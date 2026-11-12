import numpy as np
import pandas as pd
from src.quality_audit import audit_synthetic_dataset, algorithm_robustness


def sample(n=160):
    rng = np.random.default_rng(8)
    r = rng.normal(0.0002, 0.01, n)
    return pd.DataFrame({"Timestamp": pd.date_range("2025-01-01", periods=n),
                         "Price": 100 * np.cumprod(1 + r), "Return": r})


def test_schema_does_not_crash_when_missing():
    result = audit_synthetic_dataset(pd.DataFrame({"Return": [0.1]}))
    assert result["usable"] is False


def test_identical_reference_is_accepted_as_marginal_check():
    df = sample()
    result = audit_synthetic_dataset(df, df)
    assert result["usable"] is True
    assert result["metrics"]["wasserstein"] == 0


def test_invalid_prices_detected():
    df = sample()
    df.loc[0, "Price"] = -1
    assert audit_synthetic_dataset(df, df)["usable"] is False


def test_algorithm_scenario_drawdown():
    good = pd.Series([0.01] * 150)
    bad = pd.Series([-0.02] * 150)
    r = algorithm_robustness({"positivo": good, "estres": bad})
    assert r["passes_all"] is False
    assert r["evaluated"] == 2
