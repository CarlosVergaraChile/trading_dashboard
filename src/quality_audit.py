"""Evaluación auditable de datos sintéticos y estrategias (sin órdenes reales).

Módulo independiente para integrar en dashboard y API. No atribuye calidad
a partir de un único estadístico ni confunde una simulación con rendimiento real.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, wasserstein_distance


@dataclass(frozen=True)
class QualityCheck:
    name: str
    passed: bool
    detail: str


def audit_synthetic_dataset(
    synthetic: pd.DataFrame,
    reference: pd.DataFrame | None = None,
    *,
    min_rows: int = 100,
    wasserstein_limit: float = 0.01,
) -> dict:
    """Audita estructura, datos y semejanza marginal; no certifica realismo."""
    checks: list[QualityCheck] = []
    required = {"Timestamp", "Price", "Return"}
    present = required.issubset(synthetic.columns)
    checks.append(QualityCheck("schema", present, "Columnas: Timestamp, Price, Return"))
    if not present:
        return {"usable": False, "checks": [asdict(c) for c in checks], "metrics": {}}
    n = len(synthetic)
    checks.append(QualityCheck("sample_size", n >= min_rows, f"{n} filas; mínimo {min_rows}"))
    prices = pd.to_numeric(synthetic["Price"], errors="coerce")
    returns = pd.to_numeric(synthetic["Return"], errors="coerce")
    timestamps = pd.to_datetime(synthetic["Timestamp"], errors="coerce", utc=True)
    complete = bool(prices.notna().all() and returns.notna().all() and timestamps.notna().all())
    checks.append(QualityCheck("completeness", complete, "Sin valores faltantes o inválidos"))
    positive = bool((prices > 0).all())
    checks.append(QualityCheck("positive_prices", positive, "Precios estrictamente positivos"))
    finite = bool(np.isfinite(prices.to_numpy()).all() and np.isfinite(returns.to_numpy()).all())
    checks.append(QualityCheck("finite_values", finite, "Sin infinitos"))
    unique_ordered = bool(timestamps.is_unique and timestamps.is_monotonic_increasing)
    checks.append(QualityCheck("timestamps", unique_ordered, "Fechas únicas y ordenadas"))
    metrics: dict[str, float | None] = {"ks_pvalue": None, "wasserstein": None}
    if reference is not None and "Return" in reference and complete and finite:
        base = pd.to_numeric(reference["Return"], errors="coerce").dropna()
        syn = returns.dropna()
        if len(base) >= min_rows and len(syn) >= min_rows:
            p = float(ks_2samp(syn, base).pvalue)
            w = float(wasserstein_distance(syn, base))
            metrics = {"ks_pvalue": p, "wasserstein": w}
            checks.append(QualityCheck("distribution_ks", p >= 0.05, f"p={p:.4f}; no rechazo no demuestra equivalencia"))
            checks.append(QualityCheck("distribution_wasserstein", w <= wasserstein_limit, f"distancia={w:.6f}"))
        else:
            checks.append(QualityCheck("reference_sample", False, "Referencia insuficiente"))
    else:
        checks.append(QualityCheck("reference", False, "Sin comparación de distribución contra referencia"))
    return {"usable": all(c.passed for c in checks), "checks": [asdict(c) for c in checks], "metrics": metrics,
            "limitations": "No verifica colas extremas, dependencia temporal, filtraciones ni robustez fuera de muestra."}


def algorithm_robustness(
    scenario_returns: Mapping[str, pd.Series],
    *,
    max_allowed_drawdown: float = 0.20,
) -> dict:
    """Resume rendimientos por régimen. Las series deben provenir de backtests legítimos.

    No sustituye controles de leakage, costos, slippage, train/test ni walk-forward.
    """
    rows = []
    for scenario, values in scenario_returns.items():
        x = pd.to_numeric(pd.Series(values), errors="coerce").dropna().astype(float)
        if x.empty or not np.isfinite(x.to_numpy()).all() or (x <= -1).any():
            rows.append({"scenario": scenario, "valid": False, "reason": "retornos inválidos"})
            continue
        equity = (1 + x).cumprod()
        drawdown = equity / equity.cummax() - 1
        rows.append({"scenario": scenario, "valid": True,
                     "total_return": float(equity.iloc[-1] - 1),
                     "max_drawdown": float(drawdown.min()),
                     "passes_drawdown": bool(drawdown.min() >= -max_allowed_drawdown)})
    valid = [r for r in rows if r.get("valid")]
    return {"scenarios": rows, "evaluated": len(valid),
            "passes_all": bool(valid) and len(valid) == len(rows) and all(r["passes_drawdown"] for r in valid),
            "limitations": "Resultados de simulación no predicen rendimiento futuro."}
