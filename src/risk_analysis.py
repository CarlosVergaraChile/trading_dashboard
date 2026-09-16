"""Risk metrics computed from a return series.

Every function is documented with the assumption it makes. No metric
presented here guarantees anything about future performance.
"""

from __future__ import annotations

import numpy as np


def historical_var(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Historical Value at Risk at the given confidence level.

    Returns the loss threshold such that (1 - confidence) of observed
    returns fall below it. Reported as a negative number.

    Not a maximum guaranteed loss. Assumes the sample distribution is
    representative of future conditions, which it usually is not.
    """
    if returns.size == 0:
        return float("nan")
    return float(np.percentile(returns, (1 - confidence) * 100))


def historical_cvar(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Historical Conditional VaR (expected shortfall).

    Average of returns below the VaR threshold. More informative than VaR
    for tail-heavy distributions, but still a sample estimate.
    """
    if returns.size == 0:
        return float("nan")
    var = historical_var(returns, confidence)
    tail = returns[returns <= var]
    return float(tail.mean()) if tail.size else var


def max_drawdown(prices: np.ndarray) -> float:
    """Largest peak-to-trough decline of a price series, as a fraction."""
    if prices.size == 0:
        return float("nan")
    running_max = np.maximum.accumulate(prices)
    drawdowns = (prices - running_max) / running_max
    return float(drawdowns.min())


def annualized_volatility(returns: np.ndarray, periods_per_year: int = 252) -> float:
    """Annualized volatility from periodic returns.

    Assumes returns are independently distributed, which understates
    volatility when returns are autocorrelated.
    """
    if returns.size < 2:
        return float("nan")
    return float(returns.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: np.ndarray,
    risk_free: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Annualized Sharpe ratio.

    Not a guarantee of quality. A high Sharpe on a short sample is
    frequently a sign of overfitting, not of edge.
    """
    if returns.size < 2:
        return float("nan")
    excess = returns - risk_free / periods_per_year
    std = excess.std(ddof=1)
    if std == 0:
        return float("nan")
    return float(excess.mean() / std * np.sqrt(periods_per_year))


def sortino_ratio(
    returns: np.ndarray,
    risk_free: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Annualized Sortino ratio using downside deviation only."""
    if returns.size < 2:
        return float("nan")
    excess = returns - risk_free / periods_per_year
    downside = excess[excess < 0]
    if downside.size == 0:
        return float("nan")
    dd = downside.std(ddof=1)
    if dd == 0:
        return float("nan")
    return float(excess.mean() / dd * np.sqrt(periods_per_year))


def calculate_market_risk(
    returns: np.ndarray,
    prices: np.ndarray,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Convenience wrapper returning (VaR, max drawdown)."""
    return historical_var(returns, confidence), max_drawdown(prices)
