from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import joblib
import pandas as pd
import numpy as np
from house_price_pipeline import HousePreprocessor, CatBoostWrapper
import house_price_pipeline

# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────
app = FastAPI(title="House Price Predictor")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load pipeline ONCE at startup
pipeline = joblib.load("house_price_pipeline_v2.joblib")
print("✅ Pipeline loaded successfully.")


# ─────────────────────────────────────────────
# Request schema  (all raw features the model expects)
# ─────────────────────────────────────────────
class HouseFeatures(BaseModel):
    # Identifiers
    Id: Optional[int] = None

    # Zoning / lot
    MSSubClass: int
    MSZoning: str
    LotFrontage: Optional[float] = None
    LotArea: int
    Street: str
    Alley: Optional[str] = None
    LotShape: str
    LandContour: str
    Utilities: str
    LotConfig: str
    LandSlope: str
    Neighborhood: str
    Condition1: str
    Condition2: str
    BldgType: str
    HouseStyle: str

    # Quality / age
    OverallQual: int
    OverallCond: int
    YearBuilt: int
    YearRemodAdd: int

    # Roof
    RoofStyle: str
    RoofMatl: str

    # Exterior
    Exterior1st: str
    Exterior2nd: str
    MasVnrType: Optional[str] = None
    MasVnrArea: Optional[float] = None
    ExterQual: str
    ExterCond: str
    Foundation: str

    # Basement
    BsmtQual: Optional[str] = None
    BsmtCond: Optional[str] = None
    BsmtExposure: Optional[str] = None
    BsmtFinType1: Optional[str] = None
    BsmtFinSF1: float
    BsmtFinType2: Optional[str] = None
    BsmtFinSF2: float
    BsmtUnfSF: float
    TotalBsmtSF: float

    # Utilities
    Heating: str
    HeatingQC: str
    CentralAir: str
    Electrical: Optional[str] = None

    # Floor areas
    FirstFlrSF: int   # 1stFlrSF
    SecondFlrSF: int  # 2ndFlrSF
    LowQualFinSF: int
    GrLivArea: int

    # Bathrooms
    BsmtFullBath: int
    BsmtHalfBath: int
    FullBath: int
    HalfBath: int

    # Rooms
    BedroomAbvGr: int
    KitchenAbvGr: int
    KitchenQual: str
    TotRmsAbvGrd: int

    # Functional
    Functional: str
    Fireplaces: int
    FireplaceQu: Optional[str] = None

    # Garage
    GarageType: Optional[str] = None
    GarageYrBlt: Optional[float] = None
    GarageFinish: Optional[str] = None
    GarageCars: int
    GarageArea: float
    GarageQual: Optional[str] = None
    GarageCond: Optional[str] = None

    # Exterior features
    PavedDrive: str
    WoodDeckSF: int
    OpenPorchSF: int
    EnclosedPorch: int
    ThreeSsnPorch: int   # 3SsnPorch
    ScreenPorch: int
    PoolArea: int
    PoolQC: Optional[str] = None
    Fence: Optional[str] = None
    MiscFeature: Optional[str] = None
    MiscVal: int

    # Sale
    MoSold: int
    YrSold: int
    SaleType: str
    SaleCondition: str


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.post("/predict")
async def predict(features: HouseFeatures):
    try:
        data = features.model_dump()

        # Rename fields that have Python-illegal names
        data["1stFlrSF"]  = data.pop("FirstFlrSF")
        data["2ndFlrSF"]  = data.pop("SecondFlrSF")
        data["3SsnPorch"] = data.pop("ThreeSsnPorch")

        df = pd.DataFrame([data])

        pred_log   = pipeline.predict(df)
        pred_price = float(np.expm1(pred_log)[0])

        return {"predicted_price": round(pred_price, 2)}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
