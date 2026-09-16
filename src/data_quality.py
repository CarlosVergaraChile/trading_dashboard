"""Validation contracts for synthetic datasets.

Each rule is independent, inspectable, and returns a boolean. The result
is a dictionary that the dashboard renders as pass/fail cards.
"""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {"Timestamp", "Price", "Return"}


def validate_synthetic_data(df: pd.DataFrame) -> dict[str, bool]:
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
            "volatility_within_bounds": False,
        }

    report: dict[str, bool] = {}

    report["row_count_ok"] = len(df) >= 50
    report["columns_match_set"] = REQUIRED_COLUMNS.issubset(set(df.columns))
    report["price_greater_than_zero"] = bool((df["Price"] > 0).all())
    report["no_null_values"] = bool(not df[list(REQUIRED_COLUMNS)].isnull().any().any())

    # Volatility bound: absolute return should stay below a threshold that
    # would be implausible for the synthetic generator's stated calibration.
    # The threshold is generous because the demo injects a black swan at -31%.
    max_abs_return = float(df["Return"].abs().max()) if "Return" in df else 0.0
    report["volatility_within_bounds"] = max_abs_return < 0.20

    return report


def summarize_quality(report: dict[str, bool]) -> tuple[int, int, float]:
    """Return (passed, total, pass_rate) for a validation report."""
    total = len(report)
    passed = sum(1 for v in report.values() if v)
    return passed, total, passed / total if total else 0.0
