"""Scenario generators for robustness testing.

A scenario generator produces a synthetic return series under a named
regime. Algorithms are then evaluated against each scenario so results
can be compared across regimes rather than presented as a single curve.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REGIMES = {
    "Bullish":       {"mu":  0.0008, "sigma": 0.010, "jump_prob": 0.005},
    "Bearish":       {"mu": -0.0006, "sigma": 0.012, "jump_prob": 0.010},
    "Sideways":      {"mu":  0.0000, "sigma": 0.008, "jump_prob": 0.003},
    "High Volatility":{"mu": 0.0002, "sigma": 0.020, "jump_prob": 0.020},
    "Low Volatility":{"mu":  0.0004, "sigma": 0.005, "jump_prob": 0.001},
    "High Costs":    {"mu":  0.0004, "sigma": 0.009, "jump_prob": 0.005, "cost_drag": 0.0004},
}


def generate_scenario(
    regime: str,
    n_observations: int = 500,
    seed: int = 483920,
) -> pd.DataFrame:
    """Generate a synthetic return series under the named regime.

    Args:
        regime: key from REGIMES.
        n_observations: number of observations.
        seed: random seed for reproducibility.

    Returns:
        DataFrame with columns: Timestamp, Return, Price.
    """
    if regime not in REGIMES:
        raise ValueError(f"Unknown regime: {regime}. Valid: {list(REGIMES)}")

    params = REGIMES[regime]
    rng = np.random.default_rng(seed)

    returns = rng.normal(params["mu"], params["sigma"], n_observations)

    # Occasional jumps to introduce fat tails.
    jumps = rng.random(n_observations) < params["jump_prob"]
    if jumps.any():
        jump_sizes = rng.normal(0, params["sigma"] * 6, jumps.sum())
        returns[jumps] += jump_sizes

    # Cost drag reduces realized returns by a fixed amount per step.
    cost_drag = params.get("cost_drag", 0.0)
    returns = returns - cost_drag

    prices = 100.0 * np.cumprod(1.0 + returns)
    timestamps = pd.date_range(end=pd.Timestamp.now().floor("D"), periods=n_observations, freq="D")

    return pd.DataFrame({
        "Timestamp": timestamps,
        "Return": returns,
        "Price": prices,
        "Regime": regime,
    })


def evaluate_algorithm_under_scenarios(
    algorithm_name: str,
    scenarios: list[str] | None = None,
    n_scenarios: int = 100,
    n_observations: int = 500,
    base_seed: int = 483920,
) -> pd.DataFrame:
    """Evaluate a named algorithm under multiple scenarios.

    In this prototype, the algorithm's return is a synthetic function of
    the scenario's return plus a deterministic offset derived from the
    algorithm name. This is not a real strategy — it is a placeholder
    for the calibration that happens once real data is available.

    Returns a DataFrame with one row per scenario and columns:
        Scenario, Median Return, P5, P95, Max Drawdown, Probability of Loss.
    """
    if scenarios is None:
        scenarios = list(REGIMES.keys())

    # Deterministic character per algorithm name, so results are stable
    # across runs for the same algorithm and seed.
    name_hash = sum(ord(c) for c in algorithm_name)
    skew = ((name_hash % 11) - 5) / 1000.0
    beta = 0.8 + ((name_hash % 5) / 10.0)

    rows = []
    for scenario in scenarios:
        medians, p5s, p95s, drawdowns = [], [], [], []
        for i in range(n_scenarios):
            seed = base_seed + i * 17 + name_hash
            df = generate_scenario(scenario, n_observations=n_observations, seed=seed)

            # Algorithm return is a beta-adjusted version of the scenario
            # return plus a small skew, minus costs applied at the algo level.
            algo_returns = beta * df["Return"].to_numpy() + skew

            # Realized price series from the algorithm's perspective.
            algo_prices = 100.0 * np.cumprod(1.0 + algo_returns)

            medians.append(float(np.median(algo_returns)) * 252)
            p5s.append(float(np.percentile(algo_returns, 5)) * 252)
            p95s.append(float(np.percentile(algo_returns, 95)) * 252)
            peak = np.maximum.accumulate(algo_prices)
            dd = ((algo_prices - peak) / peak).min()
            drawdowns.append(float(dd))

        rows.append({
            "Scenario": scenario,
            "Median Return": float(np.median(medians)),
            "P5": float(np.median(p5s)),
            "P95": float(np.median(p95s)),
            "Max Drawdown": float(np.median(drawdowns)),
            "Probability of Loss": float(np.mean([1 if m < 0 else 0 for m in medians])),
        })

    return pd.DataFrame(rows)
