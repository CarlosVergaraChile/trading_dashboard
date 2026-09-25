"""Validation contracts for synthetic datasets.

Each rule is independent, inspectable, and returns a boolean. The result
is a dictionary that the dashboard renders as pass/fail cards.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
import yfinance as yf
from scipy import stats

REQUIRED_COLUMNS = {"Timestamp", "Price", "Return"}
DEFAULT_REFERENCE_SYMBOL = "SPY"
DEFAULT_REFERENCE_PERIOD = "2y"


@lru_cache(maxsize=8)
def download_reference_returns(
    symbol: str = DEFAULT_REFERENCE_SYMBOL,
    period: str = DEFAULT_REFERENCE_PERIOD,
) -> pd.Series:
    """Download daily reference returns from Yahoo Finance.

    Yahoo Finance is an external data source, so an unavailable network must
    not crash the local Streamlit demo. Callers can also provide a preloaded
    series to keep tests deterministic and avoid a network request.
    """
    try:
        prices = yf.download(
            symbol,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=10,
        )
        if prices.empty or "Close" not in prices:
            return pd.Series(dtype=float, name="Return")
        close = prices["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        return (
            close.astype(float)
            .pct_change()
            .replace([float("inf"), -float("inf")], pd.NA)
            .dropna()
        )
    except Exception:
        return pd.Series(dtype=float, name="Return")


def distribution_report(
    synthetic_returns: pd.Series,
    reference_returns: pd.Series,
    ks_alpha: float = 0.05,
    wasserstein_max: float = 0.01,
) -> dict[str, float | bool]:
    """Compare return distributions using KS and Wasserstein statistics."""
    synthetic = pd.to_numeric(synthetic_returns, errors="coerce").dropna().to_numpy(dtype=float)
    reference = pd.to_numeric(reference_returns, errors="coerce").dropna().to_numpy(dtype=float)
    if synthetic.size < 2 or reference.size < 2:
        return {
            "reference_data_available": False,
            "ks_p_value": float("nan"),
            "ks_test_passed": False,
            "wasserstein_distance": float("nan"),
            "wasserstein_within_bounds": False,
        }

    ks_result = stats.ks_2samp(synthetic, reference, alternative="two-sided", mode="auto")
    distance = float(stats.wasserstein_distance(synthetic, reference))
    return {
        "reference_data_available": True,
        "ks_p_value": float(ks_result.pvalue),
        "ks_test_passed": bool(ks_result.pvalue >= ks_alpha),
        "wasserstein_distance": distance,
        "wasserstein_within_bounds": bool(distance <= wasserstein_max),
    }


def validate_synthetic_data(
    df: pd.DataFrame,
    reference_returns: pd.Series | None = None,
    symbol: str = DEFAULT_REFERENCE_SYMBOL,
    period: str = DEFAULT_REFERENCE_PERIOD,
) -> dict[str, bool]:
    """Run the standard validation contract on a synthetic dataset.

    Returns a dict mapping rule name -> pass/fail. Every key is present
    even when the DataFrame is empty, so the UI never has to guard.
    """
    if df is None or df.empty:
        return {
            "row_count_ok": False,
            "columns_match_set": False,
            "price_greater_than_zero": False,
            "no_null_values": False,
            "reference_data_available": False,
            "ks_test_passed": False,
            "wasserstein_within_bounds": False,
        }

    report: dict[str, bool] = {}

    report["row_count_ok"] = len(df) >= 50
    report["columns_match_set"] = REQUIRED_COLUMNS.issubset(set(df.columns))
    report["price_greater_than_zero"] = bool((df["Price"] > 0).all())
    report["no_null_values"] = bool(not df[list(REQUIRED_COLUMNS)].isnull().any().any())

    if reference_returns is None:
        reference_returns = download_reference_returns(symbol=symbol, period=period)
    distribution = distribution_report(df["Return"], reference_returns)
    report.update({
        "reference_data_available": bool(distribution["reference_data_available"]),
        "ks_test_passed": bool(distribution["ks_test_passed"]),
        "wasserstein_within_bounds": bool(distribution["wasserstein_within_bounds"]),
    })

    return report


def summarize_quality(report: dict[str, bool]) -> tuple[int, int, float]:
    """Return (passed, total, pass_rate) for a validation report."""
    total = len(report)
    passed = sum(1 for v in report.values() if v)
    return passed, total, passed / total if total else 0.0
