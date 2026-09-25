from __future__ import annotations

import numpy as np
import pandas as pd
import quantstats as qs

from src.risk_analysis import historical_cvar, historical_var, max_drawdown, sharpe_ratio, sortino_ratio, annualized_volatility

MAX_DRAWDOWN_STOP_THRESHOLD = -0.15
CVaR_RETRAIN_THRESHOLD = -0.03


def metric_bundle(returns: pd.Series) -> dict[str, float]:
    series = pd.Series(returns, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
    values = series.to_numpy(dtype=float)
    if values.size == 0:
        return {key: 0.0 for key in (
            "return", "pnl", "sharpe", "sortino", "calmar", "max_drawdown",
            "var_95", "cvar_95", "win_rate", "turnover", "volatility",
        )}
    prices = 100 * np.cumprod(1 + values)
    annual = float(values.mean() * 252)
    dd = max_drawdown(prices)
    # QuantStats is the source of truth for the recommendation metrics; the
    # local implementations remain a fallback for unusual/short inputs.
    sharpe = qs.stats.sharpe(series, rf=0.0, periods=252, annualize=True)
    sortino = qs.stats.sortino(series, rf=0.0, periods=252, annualize=True)
    cvar = qs.stats.cvar(series, confidence=0.95)
    sharpe = sharpe if pd.notna(sharpe) else sharpe_ratio(values)
    sortino = sortino if pd.notna(sortino) else sortino_ratio(values)
    cvar = cvar if pd.notna(cvar) else historical_cvar(values)
    result = {
        "return": annual,
        "pnl": float(prices[-1] - 100),
        "sharpe": float(np.nan_to_num(sharpe)),
        "sortino": float(np.nan_to_num(sortino)),
        "calmar": float(np.nan_to_num(annual / abs(dd))) if dd else 0.0,
        "max_drawdown": float(dd),
        "var_95": historical_var(values),
        "cvar_95": float(cvar),
        "win_rate": float((values > 0).mean()),
        "turnover": float(np.abs(np.diff(values, prepend=0)).mean()),
        "volatility": annualized_volatility(values),
    }
    return {k: float(np.nan_to_num(v)) for k, v in result.items()}


def divergence(a: dict, b: dict) -> float:
    scale = max(abs(a["sharpe"]), abs(b["sharpe"]), 1.0)
    return float(min(1.0, abs(a["sharpe"] - b["sharpe"]) / scale))


def daily_recommendation(metrics: dict[str, float]) -> str:
    """Return the daily action based on drawdown and tail-loss thresholds.

    ``STOP`` has priority because breaching the portfolio drawdown limit is
    the strongest protection signal. A CVaR breach requests ``RETRAIN``;
    otherwise the strategy can ``CONTINUE`` under the current evidence.
    """
    if float(metrics.get("max_drawdown", 0.0)) <= MAX_DRAWDOWN_STOP_THRESHOLD:
        return "STOP"
    if float(metrics.get("cvar_95", 0.0)) <= CVaR_RETRAIN_THRESHOLD:
        return "RETRAIN"
    return "CONTINUE"
