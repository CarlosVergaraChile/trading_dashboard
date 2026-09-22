from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


DataSource = Literal["MOCK", "SYNTHETIC", "REAL"]
Mode = Literal["BACKTEST", "SYNTHETIC", "PAPER", "SHADOW"]


@dataclass(frozen=True)
class MarketBar:
    timestamp: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: DataSource
    dataset_id: str
    is_synthetic: bool


@dataclass(frozen=True)
class AlgorithmSignal:
    algorithm_id: str
    version: str
    timestamp: str
    symbol: str
    signal: float
    confidence: float
    position: float
    target_position: float
    regime: str
    source: DataSource
    mode: Mode


@dataclass(frozen=True)
class EvaluationResult:
    algorithm_id: str
    data_source: DataSource
    mode: Mode
    return_value: float
    pnl: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    win_rate: float
    turnover: float
    volatility: float
    divergence: float
    robustness_score: float

    def as_dict(self) -> dict:
        result = self.__dict__.copy()
        result["return"] = result.pop("return_value")
        return result
