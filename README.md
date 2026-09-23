# AirPrice India — National Airfare Monitoring System
### SIH26056 | Ministry of Civil Aviation | DGCA

> **[🚀 Live Demo → airprice-india.streamlit.app](https://share.streamlit.io)**

---

## What is this?
Real-time airfare index & surveillance system for Indian domestic routes.
Tracks fares across IndiGo, Air India, Akasa Air, SpiceJet and more —
computes a CPI-style inflation index per route, detects anomalies, and
forecasts 30-day fare trends.

## Pages
| Page | Description |
|---|---|
| 🏠 Overview | Route inflation map (India) + KPIs + CPI status |
| ✈️ Airlines | Fare comparison, market share |
| 🗺️ Routes & CPI | CPI ranking + daily fare trend charts |
| 📊 Analytics | Distribution, booking window, 3D scatter |
| 🚨 Anomalies | Z-score price spike / drop alerts |
| 📈 Forecast | 30-day CPI forecast cone |

## Run locally
`ash
pip install -r requirements.txt
streamlit run app.py
`

## Deploy to Streamlit Cloud (free)
1. Push this folder to a GitHub repo
2. Go to https://share.streamlit.io → **New app**
3. Select your repo, set **Main file path** = pp.py
4. Click **Deploy** — get a free shareable link in ~2 minutes

## Tech Stack
Python · Streamlit · Plotly · pydeck · SQLAlchemy · scikit-learn
