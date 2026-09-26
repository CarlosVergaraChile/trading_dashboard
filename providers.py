from __future__ import annotations
import logging
from typing import Any, Dict
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

VIX_TICKER = "^VIX"
HY_SPREAD_SERIES = "BAMLH0A0HYM2"
FRED_HY_SPREAD_URL = f"https://stlouisfed.org{HY_SPREAD_SERIES}"

DEFAULT_VIX = 16.50
DEFAULT_CREDIT_SPREAD = 3.80

def _fetch_vix() -> dict[str, Any]:
    try:
        data = yf.download(VIX_TICKER, period="10d", progress=False)
        if not data.empty and "Close" in data.columns:
            val = data["Close"].dropna().iloc[-1]
            return {"value": float(val), "fallback_used": False}
    except Exception as e:
        logger.warning(f"Error fetching VIX: {e}")
    return {"value": DEFAULT_VIX, "fallback_used": True}

def _fetch_credit_spread() -> dict[str, Any]:
    try:
        data = pd.read_csv(FRED_HY_SPREAD_URL)
        if not data.empty and HY_SPREAD_SERIES in data.columns:
            clean_data = data[data[HY_SPREAD_SERIES] != "."]
            if not clean_data.empty:
                val = clean_data[HY_SPREAD_SERIES].iloc[-1]
                return {"value": float(val), "fallback_used": False}
    except Exception as e:
        logger.warning(f"Error fetching Credit Spread: {e}")
    return {"value": DEFAULT_CREDIT_SPREAD, "fallback_used": True}

def fetch_macro_regime_indicators() -> dict[str, Any]:
    vix_res = _fetch_vix()
    spread_res = _fetch_credit_spread()
    vix_fb = vix_res["fallback_used"]
    spread_fb = spread_res["fallback_used"]
    return {
        "vix": round(float(vix_res["value"]), 2),
        "credit_spread": round(float(spread_res["value"]), 2),
        "vix_fallback_used": vix_fb,
        "credit_spread_fallback_used": spread_fb,
        "fallback_used": (vix_fb or spread_fb)
    }

def calculate_dynamic_risk_multipliers(vix: float, credit_spread: float, fallback_used: bool) -> dict[str, Any]:
    if fallback_used:
        return {"multiplier": 0.85, "regime": "Datos Degradados - Precaución", "color": "orange"}
    if vix > 25.0 and credit_spread > 5.0:
        return {"multiplier": 0.70, "regime": "Alto Estrés Macro", "color": "red"}
    elif vix > 25.0:
        return {"multiplier": 0.85, "regime": "Volatilidad Elevada", "color": "orange"}
    return {"multiplier": 1.00, "regime": "Régimen Estable", "color": "green"}
