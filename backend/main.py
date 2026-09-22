from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import numpy as np
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.algorithms import ALGORITHMS
from backend.evaluation import divergence, metric_bundle
from backend.providers import MockMarketDataProvider, SyntheticMarketDataProvider
from backend.storage import AuditStore
from src.data_loader import DEFAULT_SEED
from src.generators import REGIMES, evaluate_algorithm_under_scenarios

app = FastAPI(title="AlgoControl Research & Validation Terminal", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

mock_provider = MockMarketDataProvider()
synth_provider = SyntheticMarketDataProvider()
store = AuditStore()


def _comparison() -> list[dict]:
    real = mock_provider.latest()
    synth = synth_provider.latest()
    rows = []
    for algorithm in ALGORITHMS:
        _, real_returns = algorithm.evaluate(real)
        _, synth_returns = algorithm.evaluate(synth)
        r = metric_bundle(real_returns)
        s = metric_bundle(synth_returns)
        rows.append({"algorithm_id": algorithm.id, "version": algorithm.version, "mock": r, "synthetic": s, "divergence": divergence(r, s), "status": "NOMINAL" if divergence(r, s) < .08 else "REVIEW"})
    return rows


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "algocontrol", "orders_enabled": False}


@app.get("/api/status")
def status() -> dict:
    return {"system": "NOMINAL", "data_source": "MOCK", "synthetic_source": "SYNTHETIC", "mode": "SHADOW", "broker": "NOT CONNECTED", "live_orders": "DISABLED", "updated_at": datetime.now(timezone.utc).isoformat()}


@app.get("/api/algorithms")
def algorithms() -> list[dict]:
    return [a.metadata for a in ALGORITHMS]


@app.get("/api/market-data")
def market_data(source: str = Query("MOCK", pattern="^(MOCK|SYNTHETIC)$"), bars: int = Query(120, ge=20, le=500)) -> list[dict]:
    provider = mock_provider if source == "MOCK" else synth_provider
    return provider.latest(bars=bars).tail(bars).to_dict(orient="records")


@app.get("/api/comparison")
def comparison() -> list[dict]:
    result = _comparison()
    store.record("comparison", f"algorithms={len(result)}")
    return result


@app.get("/api/evaluations")
def evaluations() -> list[dict]:
    return _comparison()


@app.get("/api/synthetic-quality")
def synthetic_quality() -> dict:
    real = mock_provider.latest()["close"].pct_change().dropna()
    synth = synth_provider.latest()["close"].pct_change().dropna()
    checks = {
        "mean_return_gap": abs(float(real.mean() - synth.mean())),
        "volatility_gap": abs(float(real.std() - synth.std())),
        "skewness_gap": abs(float(real.skew() - synth.skew())),
        "kurtosis_gap": abs(float(real.kurt() - synth.kurt())),
        "tail_loss_gap": abs(float(real.quantile(.05) - synth.quantile(.05))),
        "autocorrelation_gap": abs(float(real.autocorr() - synth.autocorr())),
    }
    score = max(0.0, 1.0 - min(1.0, sum(checks.values()) * 4))
    return {"score": score, "checks": checks, "real_dataset": "MOCK", "synthetic_dataset": "SYNTHETIC", "seed": DEFAULT_SEED}


@app.get("/api/scenarios")
def scenarios(algorithm: str = "Trend Alpha") -> list[dict]:
    results = evaluate_algorithm_under_scenarios(algorithm_name=algorithm, scenarios=list(REGIMES), n_scenarios=30, base_seed=DEFAULT_SEED)
    return results.replace({np.nan: None}).to_dict(orient="records")


@app.get("/api/risk")
def risk() -> dict:
    first = _comparison()[0]["mock"]
    return {"var_95": first["var_95"], "cvar_95": first["cvar_95"], "max_drawdown": first["max_drawdown"], "exposure": .42, "concentration": .31, "alerts": []}


@app.get("/api/signals")
def signals() -> list[dict]:
    data = mock_provider.latest(bars=120)
    now = data.iloc[-1]["timestamp"]
    return [{"algorithm_id": a.id, "version": a.version, "timestamp": now, "symbol": "DEMO", "signal": float(a.generate_signals(data).iloc[-1]), "source": "MOCK", "mode": "SHADOW", "execution": "DISABLED"} for a in ALGORITHMS]


@app.get("/api/audit")
def audit() -> list[dict]:
    return store.latest()
