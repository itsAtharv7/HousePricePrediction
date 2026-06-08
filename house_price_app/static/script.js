/* ═══════════════════════════════════════════════
   HOUSE PRICE PREDICTOR — script.js
═══════════════════════════════════════════════ */

// ─── Dark / Light toggle ───────────────────────
const toggleBtn = document.getElementById('themeToggle');
const body = document.body;

function setTheme(mode) {
  if (mode === 'light') {
    body.classList.add('light');
    toggleBtn.innerHTML = '☀ Light';
    localStorage.setItem('theme', 'light');
  } else {
    body.classList.remove('light');
    toggleBtn.innerHTML = '◑ Dark';
    localStorage.setItem('theme', 'dark');
  }
}

toggleBtn.addEventListener('click', () => {
  setTheme(body.classList.contains('light') ? 'dark' : 'light');
});

// Restore saved theme
setTheme(localStorage.getItem('theme') || 'dark');


// ─── Result panel states ───────────────────────
const resultCard  = document.getElementById('resultCard');
const resultInner = document.getElementById('resultInner');
const errorBox    = document.getElementById('errorBox');

function showIdle() {
  resultCard.classList.remove('has-result');
  resultInner.innerHTML = `<p class="result-idle">Awaiting prediction…</p>`;
}

function showSpinner() {
  resultCard.classList.remove('has-result');
  resultInner.innerHTML = `
    <div class="spinner-wrap">
      <div class="spinner"></div>
      <span class="spinner-text">Running model…</span>
    </div>`;
}

function showResult(price) {
  resultCard.classList.add('has-result');
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', maximumFractionDigits: 0
  }).format(price);
  resultInner.innerHTML = `
    <p class="result-label">Estimated House Price</p>
    <p class="result-price">${formatted}</p>
    <p class="result-note">Prediction generated using trained CatBoost model.</p>`;
}

function showError(msg) {
  errorBox.textContent = '⚠ ' + msg;
  errorBox.classList.add('visible');
  showIdle();
  setTimeout(() => errorBox.classList.remove('visible'), 5000);
}


// ─── Collect form values ───────────────────────
function getVal(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  const raw = el.value.trim();
  if (raw === '' || raw === null) return null;
  return el.tagName === 'SELECT' ? raw : Number(raw);
}

function getStr(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : null;
}

function buildPayload() {
  return {
    // Lot / Zoning
    MSSubClass:    getVal('MSSubClass'),
    MSZoning:      getStr('MSZoning'),
    LotFrontage:   getVal('LotFrontage'),
    LotArea:       getVal('LotArea'),
    Street:        getStr('Street'),
    LotShape:      getStr('LotShape'),
    LandContour:   getStr('LandContour'),
    Utilities:     getStr('Utilities'),
    LotConfig:     getStr('LotConfig'),
    LandSlope:     getStr('LandSlope'),
    Neighborhood:  getStr('Neighborhood'),
    Condition1:    getStr('Condition1'),
    Condition2:    getStr('Condition2'),
    BldgType:      getStr('BldgType'),
    HouseStyle:    getStr('HouseStyle'),

    // Quality / Age
    OverallQual:   getVal('OverallQual'),
    OverallCond:   getVal('OverallCond'),
    YearBuilt:     getVal('YearBuilt'),
    YearRemodAdd:  getVal('YearRemodAdd'),

    // Roof
    RoofStyle:     getStr('RoofStyle'),
    RoofMatl:      getStr('RoofMatl'),

    // Exterior
    Exterior1st:   getStr('Exterior1st'),
    Exterior2nd:   getStr('Exterior2nd'),
    MasVnrType:    getStr('MasVnrType'),
    MasVnrArea:    getVal('MasVnrArea'),
    ExterQual:     getStr('ExterQual'),
    ExterCond:     getStr('ExterCond'),
    Foundation:    getStr('Foundation'),

    // Basement
    BsmtQual:      getStr('BsmtQual'),
    BsmtCond:      getStr('BsmtCond'),
    BsmtExposure:  getStr('BsmtExposure'),
    BsmtFinType1:  getStr('BsmtFinType1'),
    BsmtFinSF1:    getVal('BsmtFinSF1'),
    BsmtFinType2:  getStr('BsmtFinType2'),
    BsmtFinSF2:    getVal('BsmtFinSF2'),
    BsmtUnfSF:     getVal('BsmtUnfSF'),
    TotalBsmtSF:   getVal('TotalBsmtSF'),

    // HVAC
    Heating:       getStr('Heating'),
    HeatingQC:     getStr('HeatingQC'),
    CentralAir:    getStr('CentralAir'),
    Electrical:    getStr('Electrical'),

    // Floors
    FirstFlrSF:    getVal('FirstFlrSF'),
    SecondFlrSF:   getVal('SecondFlrSF'),
    LowQualFinSF:  getVal('LowQualFinSF'),
    GrLivArea:     getVal('GrLivArea'),

    // Bathrooms
    BsmtFullBath:  getVal('BsmtFullBath'),
    BsmtHalfBath:  getVal('BsmtHalfBath'),
    FullBath:      getVal('FullBath'),
    HalfBath:      getVal('HalfBath'),

    // Rooms
    BedroomAbvGr:  getVal('BedroomAbvGr'),
    KitchenAbvGr:  getVal('KitchenAbvGr'),
    KitchenQual:   getStr('KitchenQual'),
    TotRmsAbvGrd:  getVal('TotRmsAbvGrd'),

    // Functional
    Functional:    getStr('Functional'),
    Fireplaces:    getVal('Fireplaces'),
    FireplaceQu:   getStr('FireplaceQu'),

    // Garage
    GarageType:    getStr('GarageType'),
    GarageYrBlt:   getVal('GarageYrBlt'),
    GarageFinish:  getStr('GarageFinish'),
    GarageCars:    getVal('GarageCars'),
    GarageArea:    getVal('GarageArea'),
    GarageQual:    getStr('GarageQual'),
    GarageCond:    getStr('GarageCond'),

    // Exterior extras
    PavedDrive:    getStr('PavedDrive'),
    WoodDeckSF:    getVal('WoodDeckSF'),
    OpenPorchSF:   getVal('OpenPorchSF'),
    EnclosedPorch: getVal('EnclosedPorch'),
    ThreeSsnPorch: getVal('ThreeSsnPorch'),
    ScreenPorch:   getVal('ScreenPorch'),
    PoolArea:      getVal('PoolArea'),
    PoolQC:        getStr('PoolQC'),
    Fence:         getStr('Fence'),
    MiscFeature:   getStr('MiscFeature'),
    MiscVal:       getVal('MiscVal'),

    // Sale
    MoSold:        getVal('MoSold'),
    YrSold:        getVal('YrSold'),
    SaleType:      getStr('SaleType'),
    SaleCondition: getStr('SaleCondition'),
  };
}


// ─── Validation ────────────────────────────────
const REQUIRED_NUMS = [
  'MSSubClass','LotArea','OverallQual','OverallCond','YearBuilt','YearRemodAdd',
  'MasVnrArea','BsmtFinSF1','BsmtFinSF2','BsmtUnfSF','TotalBsmtSF',
  'FirstFlrSF','SecondFlrSF','LowQualFinSF','GrLivArea',
  'BsmtFullBath','BsmtHalfBath','FullBath','HalfBath',
  'BedroomAbvGr','KitchenAbvGr','TotRmsAbvGrd','Fireplaces',
  'GarageYrBlt','GarageCars','GarageArea',
  'WoodDeckSF','OpenPorchSF','EnclosedPorch','ThreeSsnPorch','ScreenPorch',
  'PoolArea','MiscVal','MoSold','YrSold'
];

function validate(payload) {
  let ok = true;
  // Clear previous invalid states
  document.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));

  REQUIRED_NUMS.forEach(key => {
    const el = document.getElementById(key);
    if (!el) return;
    if (payload[key] === null || payload[key] === '' || isNaN(payload[key])) {
      el.classList.add('invalid');
      ok = false;
    }
  });
  return ok;
}


// ─── Predict ───────────────────────────────────
const predictBtn = document.getElementById('predictBtn');

predictBtn.addEventListener('click', async () => {
  errorBox.classList.remove('visible');

  const payload = buildPayload();
  if (!validate(payload)) {
    showError('Please fill in all required numeric fields (highlighted in red).');
    return;
  }

  predictBtn.disabled = true;
  showSpinner();

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || `Server error ${res.status}`);
    }

    showResult(data.predicted_price);

  } catch (err) {
    showError('Unable to generate prediction. ' + err.message);
  } finally {
    predictBtn.disabled = false;
  }
});


// ─── Reset ─────────────────────────────────────
document.getElementById('resetBtn').addEventListener('click', () => {
  document.getElementById('houseForm').reset();
  document.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
  errorBox.classList.remove('visible');
  showIdle();
});


// ─── Init ──────────────────────────────────────
showIdle();
