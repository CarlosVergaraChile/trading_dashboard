from __future__ import annotations

import numpy as np
import pandas as pd

from src.risk_analysis import historical_cvar, historical_var, max_drawdown, sharpe_ratio, sortino_ratio, annualized_volatility


def metric_bundle(returns: pd.Series) -> dict[str, float]:
    values = returns.to_numpy(dtype=float)
    prices = 100 * np.cumprod(1 + values)
    annual = float(values.mean() * 252)
    dd = max_drawdown(prices)
    sharpe = sharpe_ratio(values)
    sortino = sortino_ratio(values)
    result = {
        "return": annual,
        "pnl": float(prices[-1] - 100),
        "sharpe": float(np.nan_to_num(sharpe)),
        "sortino": float(np.nan_to_num(sortino)),
        "calmar": float(np.nan_to_num(annual / abs(dd))) if dd else 0.0,
        "max_drawdown": float(dd),
        "var_95": historical_var(values),
        "cvar_95": historical_cvar(values),
        "win_rate": float((values > 0).mean()),
        "turnover": float(np.abs(np.diff(values, prepend=0)).mean()),
        "volatility": annualized_volatility(values),
    }
    return {k: float(np.nan_to_num(v)) for k, v in result.items()}


def divergence(a: dict, b: dict) -> float:
    scale = max(abs(a["sharpe"]), abs(b["sharpe"]), 1.0)
    return float(min(1.0, abs(a["sharpe"] - b["sharpe"]) / scale))
