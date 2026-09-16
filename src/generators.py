"""Scenario generators for robustness testing.

A scenario generator produces a synthetic return series under a named
regime. Algorithms are then evaluated against each scenario so results
can be compared across regimes rather than presented as a single curve.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REGIMES = {
    "Bullish":        {"mu":  0.0008, "sigma": 0.010, "jump_prob": 0.005},
    "Bearish":        {"mu": -0.0006, "sigma": 0.012, "jump_prob": 0.010},
    "Sideways":       {"mu":  0.0000, "sigma": 0.008, "jump_prob": 0.003},
    "High Volatility":{"mu":  0.0002, "sigma": 0.020, "jump_prob": 0.020},
    "Low Volatility": {"mu":  0.0004, "sigma": 0.005, "jump_prob": 0.001},
    "High Costs":     {"mu":  0.0004, "sigma": 0.009, "jump_prob": 0.005, "cost_drag": 0.0004},
}


def generate_scenario(
    regime: str,
    n_observations: int = 500,
    seed: int = 483920,
) -> pd.DataFrame:
    """Generate a synthetic return series under the named regime."""
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
    timestamps = pd.date_range(
        end=pd.Timestamp.now().floor("D"),
        periods=n_observations,
        freq="D",
    )

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

    The algorithm's return is modeled as a beta-adjusted response to the
    scenario return, with a small deterministic skew per algorithm name.
    This is a placeholder — the calibration happens once real data is
    available. Results are reported at the per-step level and annualized
    once, at the end, so magnitude stays interpretable.
    """
    if scenarios is None:
        scenarios = list(REGIMES.keys())

    # Deterministic character per algorithm name, in per-step units.
    name_hash = sum(ord(c) for c in algorithm_name)
    beta = 0.8 + ((name_hash % 5) / 10.0)
    skew = ((name_hash % 11) - 5) / 100000.0

    rows = []
    for scenario in scenarios:
        medians, p5s, p95s, drawdowns = [], [], [], []
        for i in range(n_scenarios):
            seed = base_seed + i * 17 + name_hash
            df = generate_scenario(scenario, n_observations=n_observations, seed=seed)

            algo_returns = beta * df["Return"].to_numpy() + skew
            algo_prices = 100.0 * np.cumprod(1.0 + algo_returns)

            medians.append(float(np.median(algo_returns)))
            p5s.append(float(np.percentile(algo_returns, 5)))
            p95s.append(float(np.percentile(algo_returns, 95)))
            peak = np.maximum.accumulate(algo_prices)
            dd = ((algo_prices - peak) / peak).min()
            drawdowns.append(float(dd))

        rows.append({
            "Scenario": scenario,
            "Median Return": float(np.median(medians)) * 252,
            "P5": float(np.median(p5s)) * 252,
            "P95": float(np.median(p95s)) * 252,
            "Max Drawdown": float(np.median(drawdowns)),
            "Probability of Loss": float(np.mean([1 if m < 0 else 0 for m in medians])),
        })

    return pd.DataFrame(rows)
