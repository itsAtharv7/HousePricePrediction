# =============================================================================
# HOUSE PRICE PREDICTION — FINAL PIPELINE (CORRECTED)
# =============================================================================
#
# BUGS FIXED vs original notebook:
#
#  1. Row removal (Electrical == 'Mix') now handled cleanly BEFORE split,
#     and removed from transform() so predict() never drops rows silently.
#  2. OverallQual + OverallCond are now DROPPED after creating TotalHouseQuality.
#  3. drop(columns=..., axis=1) corrected to drop(columns=...) throughout.
#  4. Pipeline is actually built and fit in one clean block.
#  5. joblib load now works because HousePreprocessor is defined in a
#     standalone importable module (this file). Import it before loading.
#  6. CatBoost now receives correct cat_features list via a wrapper step.
#  7. y index mismatch fixed — row removal happens before split, not inside
#     transform(), so X and y always stay aligned.
#
# =============================================================================

import pandas as pd
import numpy as np
import joblib

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error

from catboost import CatBoostRegressor


# =============================================================================
# CUSTOM PREPROCESSOR
# =============================================================================

class HousePreprocessor(BaseEstimator, TransformerMixin):
    """
    Handles missing values, feature engineering, and log transforms.
    Row removal (Electrical == 'Mix') is NOT done here — it is done
    once before the train/test split so that y stays aligned with X.
    """

    def fit(self, X, y=None):
        # Learn the mode of Electrical from training data only
        self.electrical_mode_ = X['Electrical'].mode()[0]
        return self

    def transform(self, X):
        X = X.copy()

        # ----------------------------------------------------------------
        # MISSING VALUE HANDLING
        # ----------------------------------------------------------------

        X['LotFrontage'] = X['LotFrontage'].fillna(0)
        X['Alley']       = X['Alley'].fillna('None')

        # MasVnrType: if null but MasVnrArea > 0 → 'BrkFace', else 'None'
        mask = X['MasVnrType'].isna() & (X['MasVnrArea'] > 0)
        X.loc[mask, 'MasVnrType'] = 'BrkFace'
        X['MasVnrType'] = X['MasVnrType'].fillna('None')
        X['MasVnrArea']  = X['MasVnrArea'].fillna(0)

        basement_cols = [
            'BsmtQual', 'BsmtCond', 'BsmtExposure',
            'BsmtFinType1', 'BsmtFinType2'
        ]
        X[basement_cols] = X[basement_cols].fillna('None')

        X['GarageYrBlt'] = X['GarageYrBlt'].fillna(0)

        garage_cols = ['GarageType', 'GarageFinish', 'GarageQual', 'GarageCond']
        X[garage_cols] = X[garage_cols].fillna('None')

        # FIX: use learned mode, not df-wide mode
        X['Electrical'] = X['Electrical'].fillna(self.electrical_mode_)

        X['FireplaceQu'] = X['FireplaceQu'].fillna('None')

        high_missing = ['PoolQC', 'Fence', 'MiscFeature']
        X[high_missing] = X[high_missing].fillna('None')

        # NOTE: Electrical == 'Mix' removal is intentionally NOT here.
        # It is done once before train/test split (see training block below).
        # Doing it inside transform() would drop rows during predict() and
        # break the 1-to-1 correspondence between input rows and predictions.

        # ----------------------------------------------------------------
        # FEATURE ENGINEERING
        # ----------------------------------------------------------------

        X['TotalSF'] = X['TotalBsmtSF'] + X['1stFlrSF'] + X['2ndFlrSF']
        X = X.drop(columns=['TotalBsmtSF', '1stFlrSF', '2ndFlrSF'])

        X['TotalBathrooms'] = (
            X['FullBath'] +
            0.5 * X['HalfBath'] +
            X['BsmtFullBath'] +
            0.5 * X['BsmtHalfBath']
        )
        X = X.drop(columns=['FullBath', 'HalfBath', 'BsmtFullBath', 'BsmtHalfBath'])

        X['HouseAge'] = X['YrSold'] - X['YearBuilt']
        X = X.drop(columns=['YrSold', 'YearBuilt'])

        X['TotalPorchSF'] = (
            X['OpenPorchSF'] +
            X['EnclosedPorch'] +
            X['3SsnPorch'] +
            X['ScreenPorch'] +
            X['WoodDeckSF']
        )
        X = X.drop(columns=['OpenPorchSF', 'EnclosedPorch', '3SsnPorch',
                             'ScreenPorch', 'WoodDeckSF'])

        X['TotalBsmtFinSF'] = X['BsmtFinSF1'] + X['BsmtFinSF2']
        X = X.drop(columns=['BsmtFinSF1', 'BsmtFinSF2'])

        X['TotalRooms'] = X['TotRmsAbvGrd'] + X['BedroomAbvGr'] + X['KitchenAbvGr']
        X = X.drop(columns=['TotRmsAbvGrd', 'BedroomAbvGr', 'KitchenAbvGr'])

        X['TotalHouseQuality'] = X['OverallQual'] + X['OverallCond']
        # FIX: drop originals — they were kept in the original notebook (data leakage)
        X = X.drop(columns=['OverallQual', 'OverallCond'])

        X['HasFireplace'] = (X['Fireplaces'] > 0).astype(int)
        X = X.drop(columns=['Fireplaces'])

        X['HasPorch']  = (X['TotalPorchSF'] > 0).astype(int)
        X['HasPool']   = (X['PoolArea'] > 0).astype(int)
        X['HasGarage'] = (X['GarageArea'] > 0).astype(int)

        if 'Id' in X.columns:
            X = X.drop(columns=['Id'])

        # ----------------------------------------------------------------
        # LOG TRANSFORMS
        # ----------------------------------------------------------------

        log_cols = [
            'MiscVal', 'PoolArea', 'LotArea', 'LowQualFinSF',
            'MasVnrArea', 'TotalPorchSF', 'BsmtUnfSF', 'GrLivArea'
        ]
        for col in log_cols:
            if col in X.columns:
                X[col] = np.log1p(X[col])

        # Drop MiscVal after log transform
        if 'MiscVal' in X.columns:
            X = X.drop(columns=['MiscVal'])

        return X


# =============================================================================
# CATBOOST WRAPPER
# — detects categorical columns automatically and passes them to CatBoost
# — FIX: original notebook never passed cat_features to CatBoost at all
# =============================================================================

class CatBoostWrapper(BaseEstimator):
    """
    Wraps CatBoostRegressor to auto-detect categorical columns from
    the DataFrame passed during fit(), then uses those indices for
    cat_features. Works with joblib save/load as long as this class
    is imported in the loading session.
    """

    def __init__(
        self,
        iterations=300,
        learning_rate=0.03,
        depth=5,
        l2_leaf_reg=5,
        random_strength=2,
        bagging_temperature=0,
        loss_function='RMSE',
        eval_metric='RMSE',
        random_state=42,
        verbose=0
    ):
        self.iterations        = iterations
        self.learning_rate     = learning_rate
        self.depth             = depth
        self.l2_leaf_reg       = l2_leaf_reg
        self.random_strength   = random_strength
        self.bagging_temperature = bagging_temperature
        self.loss_function     = loss_function
        self.eval_metric       = eval_metric
        self.random_state      = random_state
        self.verbose           = verbose

    def fit(self, X, y):
        # Detect categorical columns from the DataFrame
        cat_cols = [
            col for col in X.columns
            if X[col].dtype == 'object' or str(X[col].dtype) == 'category'
        ]
        cat_indices = [X.columns.get_loc(c) for c in cat_cols]

        self.model_ = CatBoostRegressor(
            iterations          = self.iterations,
            learning_rate       = self.learning_rate,
            depth               = self.depth,
            l2_leaf_reg         = self.l2_leaf_reg,
            random_strength     = self.random_strength,
            bagging_temperature = self.bagging_temperature,
            loss_function       = self.loss_function,
            eval_metric         = self.eval_metric,
            random_state        = self.random_state,
            verbose             = self.verbose,
            cat_features        = cat_indices
        )
        self.model_.fit(X, y)
        return self

    def predict(self, X):
        return self.model_.predict(X)

    def score(self, X, y):
        from sklearn.metrics import r2_score
        return r2_score(y, self.predict(X))


# =============================================================================
# TRAINING BLOCK
# =============================================================================

if __name__ == '__main__':

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    df = pd.read_csv('data.csv')

    # FIX: remove Electrical == 'Mix' ONCE here, before split,
    # so y stays aligned with X at all times.
    df = df[df['Electrical'] != 'Mix'].reset_index(drop=True)

    y = np.log1p(df['SalePrice'])
    X = df.drop(columns='SalePrice')

    # ------------------------------------------------------------------
    # Train / test split
    # ------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ------------------------------------------------------------------
    # Build the single end-to-end pipeline
    # ------------------------------------------------------------------
    pipeline = Pipeline([
        ('preprocessor', HousePreprocessor()),
        ('model',        CatBoostWrapper())
    ])

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------
    pipeline.fit(X_train, y_train)

    # ------------------------------------------------------------------
    # Evaluate
    # ------------------------------------------------------------------
    pred      = pipeline.predict(X_test)
    r2        = r2_score(y_test, pred)
    rmse      = np.sqrt(mean_squared_error(y_test, pred))

    print(f"R²   : {r2:.4f}")
    print(f"RMSE : {rmse:.4f}  (log scale)")

    pred_actual   = np.expm1(pred)
    y_test_actual = np.expm1(y_test)
    rmse_actual   = np.sqrt(mean_squared_error(y_test_actual, pred_actual))
    print(f"RMSE : {rmse_actual:,.0f}  (actual $)")

    # ------------------------------------------------------------------
    # Save the full pipeline (one file is all you need)
    # ------------------------------------------------------------------
    joblib.dump(pipeline, 'house_price_pipeline.joblib')
    print("Pipeline saved → house_price_pipeline.joblib")


# =============================================================================
# PREDICTION ON NEW RAW CSV
# =============================================================================
#
# IMPORTANT for joblib.load():
#   The custom classes (HousePreprocessor, CatBoostWrapper) must be defined
#   in the session before you call joblib.load().
#   The easiest way: put this entire file on your PYTHONPATH, or import it:
#
#       from house_price_pipeline import HousePreprocessor, CatBoostWrapper
#       import joblib
#       pipeline = joblib.load('house_price_pipeline.joblib')
#
# That is why the original notebook kept crashing with:
#   AttributeError: Can't get attribute 'HousePreprocessor' on <module '__main__'>
# — it tried to load the file in a fresh kernel without importing the class first.
#
# Example:
#
#   from house_price_pipeline import HousePreprocessor, CatBoostWrapper
#   import joblib, pandas as pd, numpy as np
#
#   pipeline  = joblib.load('house_price_pipeline.joblib')
#   new_data  = pd.read_csv('test.csv')
#   preds_log = pipeline.predict(new_data)
#   preds     = np.expm1(preds_log)   # back to actual dollar values
#   print(preds)