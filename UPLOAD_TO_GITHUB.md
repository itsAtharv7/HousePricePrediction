# 📤 How to Upload This Project to GitHub

Follow these steps exactly — takes about 5 minutes.

---

## Step 1 — Create a GitHub Account (if you don't have one)

Go to https://github.com and sign up. It's free.

---

## Step 2 — Create a New Repository on GitHub

1. Click the **"+"** button (top-right corner) → **"New repository"**
2. Fill in:
   - **Repository name:** `HousePricePrediction`
   - **Description:** `End-to-end house price prediction using CatBoost, FastAPI, and scikit-learn`
   - **Visibility:** Public (so recruiters can see it)
   - ✅ Do NOT check "Add a README file" (we already have one)
3. Click **"Create repository"**

---

## Step 3 — Install Git (if not installed)

Download from: https://git-scm.com/downloads

Verify it works:
```bash
git --version
```

---

## Step 4 — Configure Git (first time only)

```bash
git config --global user.name "Atharv Kathar"
git config --global user.email "your-email@example.com"
```

---

## Step 5 — Open Terminal / Command Prompt

Navigate into the project folder:
```bash
cd path\to\HousePricePrediction
```

Example on Windows:
```bash
cd C:\Users\Atharv\Downloads\HousePricePrediction
```

---

## Step 6 — Initialise Git and Push

Run these commands one by one:

```bash
git init
git add .
git commit -m "Initial commit: House Price Prediction with CatBoost + FastAPI"
git branch -M main
git remote add origin https://github.com/<your-username>/HousePricePrediction.git
git push -u origin main
```

> Replace `<your-username>` with your actual GitHub username.

---

## Step 7 — Verify

Go to `https://github.com/<your-username>/HousePricePrediction`

You should see all your files with the beautiful README displayed.

---

## ⚠️ What NOT to Upload

The `.gitignore` already handles these — they will be skipped automatically:

| File | Reason |
|---|---|
| `*.joblib` | Binary model file — too large for git |
| `data.csv` / `*.csv` | Dataset — download from Kaggle separately |
| `__pycache__/` | Compiled Python — auto-generated |
| `Raw wrok/` | Draft working files — not for public |
| `.env` | Secrets — never commit these |

---

## 💡 Pro Tips for a Better GitHub Profile

1. **Add Topics** — On your repo page → gear icon next to "About" → add tags:
   `machine-learning`, `python`, `catboost`, `fastapi`, `house-prices`, `regression`

2. **Pin the repo** — Go to your profile → "Customize your profile" → pin this repo

3. **Add a description** — Short one-liner visible on your profile

4. **Star your own repo** — Shows engagement count

---

## 🔄 Updating the Repo Later

After making changes:
```bash
git add .
git commit -m "describe what you changed"
git push
```
