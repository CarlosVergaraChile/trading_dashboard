"""Carga y simulación reproducible de datos de mercado."""

import numpy as np
import pandas as pd


def generate_simulation_data(inject_error: bool = False) -> pd.DataFrame:
    """Simula una serie financiera; opcionalmente introduce una caída severa."""
    np.random.seed(42)
    dates = pd.date_range(start="2026-09-15 09:00", periods=50, freq="min")
    prices = np.cumsum(np.random.normal(0.5, 1.2, 50)) + 100

    if inject_error:
        prices[30:] = prices[30:] * 0.4

    returns = np.diff(prices) / prices[:-1]
    returns = np.insert(returns, 0, 0)
    return pd.DataFrame({"Timestamp": dates, "Price": prices, "Return": returns})