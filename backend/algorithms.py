from __future__ import annotations

import numpy as np
import pandas as pd


class DemoAlgorithm:
    def __init__(self, algorithm_id: str, version: str = "0.1.0"):
        self.id = algorithm_id
        self.version = version

    @property
    def metadata(self) -> dict:
        return {"id": self.id, "version": self.version, "demo_only": True}

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"].astype(float)
        short = close.rolling(12, min_periods=1).mean()
        long = close.rolling(36, min_periods=1).mean()
        if self.id == "mean_reversion_beta":
            raw = -(close - close.rolling(24, min_periods=1).mean()) / close.rolling(24, min_periods=1).std().replace(0, np.nan)
        elif self.id == "momentum_gamma":
            raw = close.pct_change(20).fillna(0) * 8
        elif self.id == "volatility_epsilon":
            raw = close.pct_change().rolling(20, min_periods=2).std().rsub(.01) * 80
        else:
            raw = (short - long) / close * 30
        return raw.replace([np.inf, -np.inf], 0).fillna(0).clip(-1, 1)

    def evaluate(self, data: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        signal = self.generate_signals(data)
        returns = data["close"].pct_change().fillna(0)
        strategy = signal.shift(1).fillna(0) * returns
        return signal, strategy


ALGORITHMS = [
    DemoAlgorithm("trend_alpha"),
    DemoAlgorithm("mean_reversion_beta"),
    DemoAlgorithm("momentum_gamma"),
    DemoAlgorithm("volatility_epsilon"),
]
