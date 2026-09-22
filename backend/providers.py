from __future__ import annotations

import hashlib
from typing import Protocol

import numpy as np
import pandas as pd

from src.data_loader import DEFAULT_SEED, generate_simulation_data


class MarketDataProvider(Protocol):
    source: str

    def latest(self, symbol: str = "DEMO", bars: int = 500) -> pd.DataFrame:
        ...


def _ohlcv(df: pd.DataFrame, source: str, symbol: str, seed: int) -> pd.DataFrame:
    close = df["Price"].astype(float)
    rng = np.random.default_rng(seed)
    out = pd.DataFrame({
        "timestamp": pd.to_datetime(df["Timestamp"]).dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "symbol": symbol,
        "open": close.shift(1).fillna(close.iloc[0]),
        "high": close * (1 + np.abs(rng.normal(0, .002, len(close)))),
        "low": close * (1 - np.abs(rng.normal(0, .002, len(close)))),
        "close": close,
        "volume": rng.lognormal(10, .25, len(close)),
        "source": source,
        "is_synthetic": source == "SYNTHETIC",
    })
    dataset = hashlib.sha256(out.to_csv(index=False).encode()).hexdigest()[:12]
    out["dataset_id"] = f"{source.lower()}-{dataset}"
    return out


class MockMarketDataProvider:
    source = "MOCK"

    def __init__(self, seed: int = DEFAULT_SEED):
        self.seed = seed

    def latest(self, symbol: str = "DEMO", bars: int = 500) -> pd.DataFrame:
        return _ohlcv(generate_simulation_data(bars, self.seed), self.source, symbol, self.seed + 1)


class SyntheticMarketDataProvider:
    source = "SYNTHETIC"

    def __init__(self, seed: int = DEFAULT_SEED + 101):
        self.seed = seed

    def latest(self, symbol: str = "DEMO", bars: int = 500) -> pd.DataFrame:
        return _ohlcv(generate_simulation_data(bars, self.seed), self.source, symbol, self.seed + 1)
