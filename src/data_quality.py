"""Reglas de calidad inspiradas en contratos tipo Great Expectations."""

import pandas as pd


def validate_synthetic_data(df: pd.DataFrame) -> dict[str, bool]:
    """Valida estructura, integridad, dominio de precios y drift de retornos."""
    expected_columns = ["Timestamp", "Price", "Return"]
    has_rows = len(df) > 0
    has_columns = all(column in df.columns for column in expected_columns)

    report = {
        "row_count_ok": has_rows,
        "columns_match_set": has_columns,
        "price_greater_than_zero": bool((df["Price"] > 0).all()) if has_rows and has_columns else False,
        "no_null_values": bool(not df.isnull().values.any()) if has_rows else False,
        "volatility_within_bounds": True,
    }

    # abs() es deliberado: tanto un salto positivo como un desplome severo son drift.
    if has_rows and has_columns and float(df["Return"].abs().max()) > 0.25:
        report["volatility_within_bounds"] = False
    return report