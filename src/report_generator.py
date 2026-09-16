"""Generates a PDF validation report from a set of results.

Uses ReportLab. The output is a document, not a chart dump — sections,
methodology notes, and an explicit limitations page are mandatory.
"""

from __future__ import annotations

from io import BytesIO
from datetime import datetime

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontSize=20, leading=24,
                                 textColor=colors.HexColor("#24313B"), spaceAfter=6),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontSize=11,
                                    textColor=colors.HexColor("#6E7B86"), spaceAfter=18),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=14, leading=18,
                              textColor=colors.HexColor("#1F6FB2"), spaceBefore=14, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=11.5, leading=15,
                              textColor=colors.HexColor("#24313B"), spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=10, leading=14,
                                textColor=colors.HexColor("#24313B"), spaceAfter=6),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontSize=8.5, leading=11,
                                 textColor=colors.HexColor("#6E7B86"), spaceAfter=4),
    }


def _table_from_df(df: pd.DataFrame, styles: dict) -> Table:
    data = [list(df.columns)] + df.astype(str).values.tolist()
    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#24313B")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DCE4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def generate_validation_report(
    algorithm_name: str,
    algorithm_version: str,
    results: pd.DataFrame,
    dataset_seed: int,
    generator_version: str = "RegimeSim v0.3",
    approved_by: str = "—",
) -> bytes:
    """Build a validation report PDF and return the bytes.

    Args:
        algorithm_name: name of the algorithm being evaluated.
        algorithm_version: version string.
        results: DataFrame from evaluate_algorithm_under_scenarios.
        dataset_seed: seed used for the underlying scenario generation.
        generator_version: name of the synthetic data generator.
        approved_by: name of the person who approved the report.

    Returns:
        PDF file contents as bytes.
    """
    buffer = BytesIO()
    styles = _styles()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"Validation Report — {algorithm_name}",
    )

    story = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Cover
    story.append(Paragraph("Validation Report", styles["title"]))
    story.append(Paragraph(
        f"{algorithm_name} · {algorithm_version} · issued {now}",
        styles["subtitle"],
    ))

    # 1. Algorithm card
    story.append(Paragraph("1. Algorithm", styles["h1"]))
    story.append(Paragraph(
        f"<b>{algorithm_name}</b> (version {algorithm_version}). "
        "Evaluated under the scenario suite documented in section 4. "
        "This report presents robustness evidence, not a performance forecast.",
        styles["body"],
    ))

    # 2. Experiment configuration
    story.append(Paragraph("2. Experiment Configuration", styles["h1"]))
    config = pd.DataFrame([
        ["Dataset seed", str(dataset_seed)],
        ["Generator", generator_version],
        ["Number of scenarios", str(len(results))],
        ["Evaluation performed by", "Carlos Vergara"],
        ["Approved by", approved_by],
        ["Report issued at", now],
    ], columns=["Parameter", "Value"])
    story.append(_table_from_df(config, styles))
    story.append(Spacer(1, 8))

    # 3. Results
    story.append(Paragraph("3. Results by Scenario", styles["h1"]))
    formatted = results.copy()
    for col in ["Median Return", "P5", "P95", "Max Drawdown", "Probability of Loss"]:
        if col in formatted.columns:
            if col == "Probability of Loss":
                formatted[col] = formatted[col].map(lambda v: f"{v:.1%}")
            else:
                formatted[col] = formatted[col].map(lambda v: f"{v:+.2%}")
    story.append(_table_from_df(formatted, styles))
    story.append(Spacer(1, 8))

    # 4. Robustness classification
    story.append(Paragraph("4. Robustness Classification", styles["h1"]))
    positive_scenarios = (results["Median Return"] > 0).sum()
    total_scenarios = len(results)
    if positive_scenarios >= total_scenarios - 1:
        verdict = "Robust under the scenarios evaluated."
    elif positive_scenarios >= total_scenarios - 2:
        verdict = "Marginal — sensitive to at least one scenario."
    else:
        verdict = "Fragile — fails under multiple scenarios."

    story.append(Paragraph(
        f"Across {total_scenarios} scenarios, {positive_scenarios} showed a positive median return. "
        f"<b>Classification: {verdict}</b>",
        styles["body"],
    ))

    failing = results[results["Median Return"] <= 0]["Scenario"].tolist()
    if failing:
        story.append(Paragraph(
            f"Failing scenarios: {', '.join(failing)}. "
            "These are the regimes under which the algorithm's behavior diverges from the design assumption.",
            styles["body"],
        ))

    # 5. Limitations
    story.append(PageBreak())
    story.append(Paragraph("5. Limitations", styles["h1"]))
    limitations = [
        "Results are derived from synthetic scenarios, not from observed market data.",
        "The scenario generator encodes assumptions about volatility, correlation, and regime switching. "
        "These assumptions are documented in the methodology annex and are not validated against a large sample of real data.",
        "No broker execution is simulated. Slippage and partial fills are represented as a fixed cost drag.",
        "The algorithm's behavior is approximated as a beta-adjusted response to the scenario returns. "
        "A real algorithm's behavior would depend on its internal signal logic, position sizing, and risk controls.",
        "This report does not certify that the algorithm will be profitable, safe, or suitable for any specific purpose.",
    ]
    for item in limitations:
        story.append(Paragraph(f"• {item}", styles["body"]))

    # 6. Traceability
    story.append(Paragraph("6. Traceability", styles["h1"]))
    trace = pd.DataFrame([
        ["Seed", str(dataset_seed)],
        ["Generator version", generator_version],
        ["Algorithm version", algorithm_version],
        ["Scenarios evaluated", str(total_scenarios)],
        ["Report version", "1.0"],
        ["Issued", now],
    ], columns=["Field", "Value"])
    story.append(_table_from_df(trace, styles))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Confidential document. Synthetic-data evaluation. Not investment advice.",
        styles["small"],
    ))

    doc.build(story)
    return buffer.getvalue()
