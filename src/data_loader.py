"""Synthetic data generation with reproducible seeds.

Every dataset is derived from a documented seed so any experiment can be
reproduced from the audit log. No external data source is required.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_SEED = 483920


def generate_simulation_data(
    n_observations: int = 500,
    seed: int = DEFAULT_SEED,
    inject_error: bool = False,
) -> pd.DataFrame:
    """Generate a synthetic price and return series.

    Args:
        n_observations: number of observations to simulate.
        seed: random seed for reproducibility.
        inject_error: if True, injects an extreme negative shock to trigger
            drift detection. Used by the "Inject Black Swan" button.

    Returns:
        DataFrame with columns: Timestamp, Price, Return.
    """
    rng = np.random.default_rng(seed)

    # Base drift and volatility calibrated so the series looks plausible
    # for a broad-market synthetic index over the simulated horizon.
    base_return = 0.0004
    base_vol = 0.008

    # Occasional regime shifts — small probability of higher volatility.
    regime = np.ones(n_observations)
    switch_points = rng.choice(n_observations, size=max(3, n_observations // 120), replace=False)
    for point in switch_points:
        regime[point:] = rng.uniform(1.2, 2.4)

    returns = rng.normal(base_return, base_vol, n_observations) * regime

    if inject_error:
        # Inject a single severe negative shock to simulate an anomalous
        # event the validation layer should detect as drift.
        shock_index = int(n_observations * 0.78)
        returns[shock_index] = -0.31

    prices = 100.0 * np.cumprod(1.0 + returns)

    timestamps = pd.date_range(
        end=pd.Timestamp.now().floor("min"),
        periods=n_observations,
        freq="min",
    )

    return pd.DataFrame({
        "Timestamp": timestamps,
        "Price": prices,
        "Return": returns,
    })


def generate_portfolio_returns(
    n_observations: int = 750,
    n_algorithms: int = 6,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Generate daily returns for a portfolio of synthetic algorithms.

    Each algorithm has distinct statistical character so that portfolio
    analysis (correlation, robustness, attribution) has something to work
    with. This is intentionally not calibrated to any real strategy — it
    is a demo dataset.

    Args:
        n_observations: number of daily observations (~3 years).
        n_algorithms: number of algorithms to simulate.
        seed: random seed.

    Returns:
        DataFrame with one column per algorithm and a DatetimeIndex.
    """
    rng = np.random.default_rng(seed)

    # Distinct profiles: trend, mean-reversion, momentum, defensive,
    # volatility, and a residual "other" bucket.
    profiles = [
        {"name": "Trend Alpha",        "mu": 0.0006, "sigma": 0.009, "autocorr": 0.10},
        {"name": "Mean Reversion Beta","mu": 0.0003, "sigma": 0.007, "autocorr": -0.15},
        {"name": "Momentum Gamma",     "mu": 0.0009, "sigma": 0.014, "autocorr": 0.18},
        {"name": "Defensive Delta",    "mu": 0.0002, "sigma": 0.004, "autocorr": 0.02},
        {"name": "Volatility Epsilon", "mu": 0.0004, "sigma": 0.011, "autocorr": -0.05},
        {"name": "Macro Zeta",         "mu": 0.0005, "sigma": 0.010, "autocorr": 0.08},
    ][:n_algorithms]

    dates = pd.date_range(end=pd.Timestamp.now().normalize(), periods=n_observations, freq="D")
    data: dict[str, np.ndarray] = {}

    for profile in profiles:
        # Simple AR(1) to introduce autocorrelation structure.
        rho = profile["autocorr"]
        eps = rng.normal(0, profile["sigma"], n_observations)
        series = np.zeros(n_observations)
        for i in range(1, n_observations):
            series[i] = rho * series[i - 1] + eps[i]
        series += profile["mu"]
        data[profile["name"]] = series

    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"

    # Benchmark: a broad, low-vol series correlated to the aggregate.
    aggregate = df.mean(axis=1)
    benchmark = 0.6 * aggregate + 0.4 * rng.normal(0.0004, 0.008, n_observations)
    df["Global Market Index"] = benchmark

    return df
