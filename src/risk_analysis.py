"""Métricas básicas de estrés y riesgo de mercado."""

import numpy as np


def calculate_market_risk(returns, prices) -> tuple[float, float]:
    """Calcula VaR histórico 95% y máximo drawdown."""
    returns_array = np.asarray(returns, dtype=float)
    prices_array = np.asarray(prices, dtype=float)
    if returns_array.size == 0 or prices_array.size == 0:
        return 0.0, 0.0

    var_95 = np.percentile(returns_array, 5)
    cumulative_max = np.maximum.accumulate(prices_array)
    drawdowns = (prices_array - cumulative_max) / cumulative_max
    max_drawdown = drawdowns.min() if drawdowns.size > 0 else 0.0
    return float(var_95), float(max_drawdown)