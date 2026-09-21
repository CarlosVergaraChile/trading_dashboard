"""Validation & Robustness Terminal.

Independent validation layer for algorithmic trading portfolios.
Synthetic data only. No broker connection. No investment advice.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import (
    generate_simulation_data,
    generate_portfolio_returns,
    DEFAULT_SEED,
)
from src.data_quality import validate_synthetic_data, summarize_quality
from src.risk_analysis import (
    historical_var,
    historical_cvar,
    max_drawdown,
    annualized_volatility,
    sharpe_ratio,
    sortino_ratio,
    calculate_market_risk,
)
from src.generators import REGIMES, evaluate_algorithm_under_scenarios
from src.report_generator import generate_validation_report


st.set_page_config(
    page_title="Validation & Robustness Terminal",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a Bug": None,
        "About": "Independent validation layer for algorithmic trading portfolios.",
    },
)


def build_css(theme: str) -> str:
    if theme == "dark":
        v = """
            --bg: #070d16;
            --bg-2: #0d1722;
            --bg-3: #111d2b;
            --surface: rgba(13, 23, 34, 0.88);
            --surface-2: rgba(17, 29, 43, 0.96);
            --surface-3: rgba(21, 35, 52, 0.96);
            --border: rgba(148,163,184,.15);
            --border-hi: rgba(96,165,250,.34);
            --text: #e5edf7;
            --text-2: #9fb2c8;
            --text-3: #73839a;
            --accent: #22d3ee;
            --accent-2: #67e8f9;
            --accent-soft: rgba(34,211,238,.14);
            --accent-glow: rgba(34,211,238,.4);
            --green: #10b981;
            --green-soft: rgba(16,185,129,.12);
            --green-glow: rgba(16,185,129,.35);
            --red: #f87171;
            --red-soft: rgba(248,113,113,.12);
            --red-glow: rgba(248,113,113,.35);
            --amber: #f59e0b;
            --amber-soft: rgba(245,158,11,.12);
            --purple: #a78bfa;
            --purple-soft: rgba(167,139,250,.12);
            --shadow-sm: 0 1px 2px rgba(2,6,23,.45);
            --shadow-md: 0 8px 24px rgba(2,6,23,.5);
            --shadow-lg: 0 18px 50px rgba(2,6,23,.62);
            --plot-bg: rgba(7,13,22,.7);
            --plot-grid: rgba(148,163,184,.08);
            --heat-low: #f87171;
            --heat-mid: #1b2330;
            --heat-high: #22d3ee;
            --input-bg: rgba(17,29,43,.96);
            --input-border: rgba(148,163,184,.25);
            --select-text: #e5edf7;
            --header-bg: rgba(8, 15, 22, 0.7);
        """
    else:
        v = """
            --bg: #f3f5f9;
            --bg-2: #f8fafc;
            --bg-3: #edf3f9;
            --surface: rgba(255,255,255,.9);
            --surface-2: rgba(255,255,255,.95);
            --surface-3: rgba(248,250,252,.98);
            --border: rgba(15,23,42,.08);
            --border-hi: rgba(8,145,178,.28);
            --text: #0f172a;
            --text-2: #52657a;
            --text-3: #7b8ea5;
            --accent: #0891b2;
            --accent-2: #22d3ee;
            --accent-soft: rgba(8,145,178,.1);
            --accent-glow: rgba(8,145,178,.2);
            --green: #059669;
            --green-soft: rgba(5,150,105,.1);
            --green-glow: rgba(5,150,105,.18);
            --red: #dc2626;
            --red-soft: rgba(220,38,38,.09);
            --red-glow: rgba(220,38,38,.15);
            --amber: #d97706;
            --amber-soft: rgba(217,119,6,.1);
            --purple: #7c3aed;
            --purple-soft: rgba(124,58,237,.08);
            --shadow-sm: 0 1px 2px rgba(15,23,42,.05);
            --shadow-md: 0 8px 22px rgba(15,23,42,.08);
            --shadow-lg: 0 18px 40px rgba(15,23,42,.12);
            --plot-bg: rgba(255,255,255,.8);
            --plot-grid: rgba(15,23,42,.05);
            --heat-low: #dc2626;
            --heat-mid: #f8fafc;
            --heat-high: #0891b2;
            --input-bg: rgba(255,255,255,.96);
            --input-border: rgba(15,23,42,.12);
            --select-text: #0f172a;
            --header-bg: rgba(255,255,255,.78);
        """

    return f"""
<style>
    :root {{
{v}
        --r: 12px;
        --r-lg: 18px;
        --r-sm: 8px;
    }}

    html, body, .stApp, [data-testid="stAppViewContainer"] {{
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', system-ui, sans-serif !important;
        font-feature-settings: 'cv02','cv03','cv04','cv11','tnum';
    }}

    .stApp {{
        background-image:
            radial-gradient(1100px 500px at 0% -10%, rgba(34,211,238,.12), transparent 52%),
            radial-gradient(700px 420px at 100% 8%, rgba(167,139,250,.12), transparent 48%),
            linear-gradient(180deg, rgba(7,13,22,0.18), transparent 400px);
        background-attachment: fixed;
    }}

    [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {{
        visibility: hidden;
        height: 0;
    }}

    [data-testid="stAppViewContainer"] > .main .block-container {{
        max-width: 1520px;
        padding: 1.2rem 2rem 2.5rem;
    }}

    * {{ box-sizing: border-box; }}
    h1, h2, h3, h4, h5, p, label, span, div {{ color: var(--text); }}
    .tnum {{ font-variant-numeric: tabular-nums; }}

    .term-header {{
        display: flex;
        align-items: center;
        gap: 18px;
        padding: 10px 18px 18px;
        margin: 0 -2rem 20px;
        background: rgba(7,13,22,0.08);
        border-bottom: 1px solid var(--border);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        position: sticky;
        top: 0;
        z-index: 10;
    }}

    .brand {{
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;
        min-width: 0;
    }}

    .brand-mark {{
        width: 42px;
        height: 42px;
        display: grid;
        place-items: center;
        border-radius: 12px;
        background: linear-gradient(135deg, var(--accent), var(--purple));
        color: #08141a;
        font-size: 20px;
        font-weight: 800;
        box-shadow: 0 0 20px var(--accent-glow);
        flex-shrink: 0;
    }}

    .brand-title {{
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        line-height: 1.2;
        color: var(--text);
        white-space: nowrap;
    }}

    .brand-sub {{
        font-size: 11.5px;
        color: var(--text-2);
        margin-top: 3px;
        line-height: 1.3;
    }}

    .status-chip {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 10.5px;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        white-space: nowrap;
        border: 1px solid transparent;
    }}

    .status-ok {{
        color: var(--green);
        background: var(--green-soft);
        border-color: var(--green-glow);
        box-shadow: inset 0 0 12px rgba(16,185,129,.06);
    }}

    .status-alert {{
        color: var(--red);
        background: var(--red-soft);
        border-color: var(--red-glow);
        box-shadow: 0 0 18px rgba(248,113,113,.12);
        animation: alertPulse 1.8s ease-in-out infinite;
    }}

    .status-dot {{
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
        box-shadow: 0 0 8px currentColor;
        animation: dotPulse 2s ease-in-out infinite;
    }}

    @keyframes alertPulse {{
        0%, 100% {{ box-shadow: 0 0 12px rgba(248,113,113,.12); }}
        50% {{ box-shadow: 0 0 24px rgba(248,113,113,.25), 0 0 36px rgba(248,113,113,.12); }}
    }}

    @keyframes dotPulse {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.5; transform: scale(0.8); }}
    }}

    .info-banner {{
        position: relative;
        padding: 18px 20px 16px;
        border-radius: var(--r-lg);
        background: linear-gradient(135deg, rgba(34,211,238,.09), rgba(167,139,250,.06));
        border: 1px solid rgba(34,211,238,.16);
        border-left: 3px solid var(--accent);
        margin: 14px 0 18px;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }}

    .info-banner::before {{
        content: '';
        position: absolute;
        top: -70px;
        right: -70px;
        width: 180px;
        height: 180px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(34,211,238,.18), transparent 70%);
        pointer-events: none;
    }}

    .info-eyebrow {{
        position: relative;
        z-index: 1;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 8px;
    }}

    .info-body, .info-foot {{
        position: relative;
        z-index: 1;
        font-size: 13px;
        line-height: 1.65;
        color: var(--text);
    }}

    .info-foot {{
        font-size: 11.5px;
        color: var(--text-2);
        margin-top: 10px;
    }}

    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r-lg) !important;
        box-shadow: var(--shadow-sm);
        transition: box-shadow 0.2s, border-color 0.2s, transform 0.2s;
    }}

    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color: var(--border-hi) !important;
        box-shadow: var(--shadow-md);
    }}

    div[data-testid="stMetric"] {{
        background: linear-gradient(160deg, var(--surface-2), var(--surface));
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        border-radius: var(--r);
        padding: 14px 16px;
        box-shadow: var(--shadow-sm);
        position: relative;
        overflow: hidden;
        min-height: 126px;
    }}

    div[data-testid="stMetric"]::after {{
        content: '';
        position: absolute;
        top: -30px;
        right: -24px;
        width: 130px;
        height: 130px;
        border-radius: 50%;
        background: radial-gradient(circle, var(--accent-soft), transparent 70%);
        opacity: 0.7;
        pointer-events: none;
    }}

    div[data-testid="stMetricLabel"] {{
        color: var(--text-2) !important;
        font-size: 10.5px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 6px !important;
    }}

    [data-testid="stMetricValue"] {{
        color: var(--text) !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        letter-spacing: -0.03em;
        font-variant-numeric: tabular-nums;
    }}

    [data-testid="stMetricDelta"] {{
        font-size: 11px !important;
        font-weight: 600 !important;
        font-variant-numeric: tabular-nums;
    }}

    .section-eyebrow {{
        display: inline-block;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 8px;
    }}

    .section-title {{
        font-size: 15px;
        font-weight: 800;
        color: var(--text);
        letter-spacing: -0.02em;
        line-height: 1.3;
        margin-bottom: 6px;
    }}

    .section-copy {{
        font-size: 12px;
        color: var(--text-2);
        line-height: 1.6;
    }}

    .check-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 10px 12px;
        margin: 7px 0;
        border-radius: var(--r-sm);
        background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(148,163,184,0.02));
        border: 1px solid var(--border);
        font-size: 12.5px;
        color: var(--text);
    }}

    .chip {{
        min-width: 76px;
        text-align: center;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 9.5px;
        font-weight: 800;
        letter-spacing: 0.09em;
    }}

    .chip-pass {{
        color: var(--green);
        background: var(--green-soft);
        border: 1px solid var(--green-glow);
    }}

    .chip-fail {{
        color: var(--red);
        background: var(--red-soft);
        border: 1px solid var(--red-glow);
    }}

    .banner {{
        display: flex;
        gap: 12px;
        align-items: flex-start;
        padding: 12px 14px;
        border-radius: var(--r);
        font-size: 12.5px;
        line-height: 1.55;
        margin: 0 0 18px;
    }}

    .banner-ok {{
        color: var(--green);
        background: var(--green-soft);
        border: 1px solid var(--green-glow);
    }}

    .banner-alert {{
        color: var(--red);
        background: linear-gradient(90deg, var(--red-soft), var(--amber-soft));
        border: 1px solid var(--red-glow);
    }}

    .verdict {{
        padding: 12px 14px;
        border-radius: var(--r);
        background: var(--surface-2);
        border-left: 3px solid var(--accent);
        font-size: 12.5px;
        color: var(--text);
        line-height: 1.55;
        margin-top: 16px;
        box-shadow: var(--shadow-sm);
    }}

    div.stButton > button {{
        min-height: 40px;
        border-radius: 10px;
        border: 1px solid var(--border-hi);
        background: rgba(17,29,43,0.7);
        color: var(--text);
        font-weight: 700;
        font-size: 12.5px;
        transition: all 0.18s ease;
    }}

    div.stButton > button:hover {{
        border-color: var(--accent);
        color: var(--accent);
        background: var(--accent-soft);
        transform: translateY(-1px);
    }}

    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        border-color: transparent;
        color: #08141a;
        box-shadow: 0 0 18px var(--accent-glow);
    }}

    div.stButton > button[kind="primary"]:hover {{
        box-shadow: 0 0 26px var(--accent-glow), 0 0 50px var(--accent-soft);
        color: #08141a;
    }}

    div[data-testid="stSelectbox"] > div > div,
    div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        border-color: var(--input-border) !important;
        color: var(--select-text) !important;
        border-radius: var(--r-sm) !important;
        min-height: 40px;
    }}

    div[data-testid="stSelectbox"] * ,
    div[data-baseweb="select"] * {{
        color: var(--select-text) !important;
    }}

    div[data-testid="stTextInput"] input {{
        background-color: var(--input-bg) !important;
        border-color: var(--input-border) !important;
        color: var(--select-text) !important;
        border-radius: var(--r-sm) !important;
        min-height: 40px;
    }}

    div[data-testid="stProgress"] > div > div > div {{
        background: linear-gradient(90deg, var(--accent), var(--purple)) !important;
        box-shadow: 0 0 12px var(--accent-glow);
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid var(--border);
        border-radius: var(--r);
        overflow: hidden;
    }}

    [data-testid="stSidebar"] {{
        background: rgba(7,13,22,0.9) !important;
        border-right: 1px solid var(--border);
    }}

    [data-testid="stSidebar"] > div:first-child {{
        padding: 22px 18px;
    }}

    [data-testid="stSidebar"] h3 {{
        color: var(--accent) !important;
        font-size: 10px !important;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-weight: 800;
    }}

    [data-testid="stSidebar"] * {{
        color: var(--text);
    }}

    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {{
        color: var(--text-3) !important;
        font-size: 11px !important;
        line-height: 1.55;
    }}

    hr {{
        margin: 18px 0 !important;
        border-color: var(--border) !important;
    }}

    .fineprint {{
        color: var(--text-3);
        font-size: 10px;
        text-align: center;
        padding-top: 32px;
        letter-spacing: 0.1em;
        font-weight: 700;
        text-transform: uppercase;
    }}

    @media (max-width: 900px) {{
        [data-testid="stAppViewContainer"] > .main .block-container {{
            padding: 1rem 1rem 2rem;
        }}
        .brand-sub {{ display: none; }}
        .term-header {{ flex-wrap: wrap; margin: 0 -1rem 18px; padding-inline: 12px; }}
    }}
</style>
"""


def init_state() -> None:
    defaults = {
        "inject_black_swan": False,
        "refresh_cycle": 0,
        "last_refresh": datetime.now(timezone.utc),
        "pipeline": "Standard validation",
        "selected_algorithm": "Trend Alpha",
        "theme": "dark",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_black_swan(active: bool) -> None:
    st.session_state.inject_black_swan = active
    st.session_state.last_refresh = datetime.now(timezone.utc)


def refresh_nodes() -> None:
    st.session_state.refresh_cycle += 1
    st.session_state.last_refresh = datetime.now(timezone.utc)


def toggle_theme() -> None:
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"


@st.dialog("Metodología de riesgo")
def risk_methodology_dialog() -> None:
    st.markdown(
        """
        **VaR histórico 95%**  
        Percentil 5 de los retornos observados. Resume una pérdida diaria de cola
        bajo la distribución sintética simulada. No representa una pérdida máxima
        garantizada.

        **CVaR histórico 95%**  
        Promedio de los retornos que caen por debajo del VaR. Más informativo que
        el VaR cuando la distribución tiene colas gruesas.

        **Máximo drawdown**  
        Mayor caída porcentual desde un máximo previo de la serie de precios.

        **Sharpe y Sortino**  
        Métricas ajustadas por riesgo. Un Sharpe alto sobre una muestra corta
        frecuentemente es síntoma de sobreajuste, no de ventaja real.

        La demo usa semilla fija y reproducible. Ninguna métrica constituye
        recomendación de inversión.
        """
    )


@st.dialog("Trazabilidad del experimento")
def pipeline_dialog() -> None:
    st.markdown(
        f"""
        **Preset de validación:** {st.session_state.pipeline}  
        **Ciclo de ejecución:** {st.session_state.refresh_cycle:04d}  
        **Datos:** sintéticos, semilla fija y reproducible  
        **Última sincronización UTC:** {st.session_state.last_refresh:%Y-%m-%d %H:%M:%S}

        Cada fila de la bitácora contiene un identificador determinístico derivado
        del ciclo actual. Refrescar produce los mismos IDs para el mismo ciclo.
        """
    )


def validation_cards(report: dict[str, bool]) -> str:
    labels = {
        "row_count_ok": "Dataset no vacío",
        "columns_match_set": "Esquema contractual",
        "price_greater_than_zero": "Precios > 0",
        "no_null_values": "Integridad / nulos",
        "volatility_within_bounds": "Drift de volatilidad",
    }
    rows = []
    for key, label in labels.items():
        ok = bool(report.get(key, False))
        chip_cls = "chip-pass" if ok else "chip-fail"
        chip_txt = "PASSED" if ok else "FAILED"
        rows.append(
            f'<div class="check-row">'
            f'<span>{label}</span>'
            f'<span class="chip {chip_cls}">{chip_txt}</span>'
            f'</div>'
        )
    return "".join(rows)


def _plot_theme() -> dict:
    if st.session_state.theme == "dark":
        return {
            "bg": "rgba(0,0,0,0)",
            "plot_bg": "rgba(15,20,28,.6)",
            "grid": "rgba(148,163,184,.08)",
            "text": "#94a3b8",
            "zero": "rgba(148,163,184,.25)",
            "accent": "#22d3ee",
            "red": "#f43f5e",
            "green": "#10b981",
            "heat_low": "#f43f5e",
            "heat_mid": "#131a24",
            "heat_high": "#22d3ee",
        }
    return {
        "bg": "rgba(0,0,0,0)",
        "plot_bg": "rgba(250,248,243,.9)",
        "grid": "rgba(28,43,58,.06)",
        "text": "#55657a",
        "zero": "rgba(28,43,58,.2)",
        "accent": "#0891b2",
        "red": "#dc2626",
        "green": "#059669",
        "heat_low": "#dc2626",
        "heat_mid": "#faf8f3",
        "heat_high": "#0891b2",
    }


def price_figure(df: pd.DataFrame, is_critical: bool) -> go.Figure:
    t = _plot_theme()
    line_color = t["red"] if is_critical else t["accent"]
    fill_color = "rgba(244,63,94,.12)" if is_critical else "rgba(34,211,238,.1)"
    trace = go.Scatter(
        x=df["Timestamp"],
        y=df["Price"],
        mode="lines",
        name="Precio sintético",
        line=dict(color=line_color, width=2),
        fill="tozeroy",
        fillcolor=fill_color,
        hovertemplate="%{x|%H:%M}<br>Índice %{y:.2f}<extra></extra>",
    )
    fig = go.Figure(trace)
    if is_critical:
        event_time = df.loc[df["Return"].abs().idxmax(), "Timestamp"]
        fig.add_vline(
            x=event_time.timestamp() * 1000,
            line_color=t["accent"],
            line_dash="dot",
            annotation_text="Drift detectado",
            annotation_font_color=t["accent"],
            annotation_font_size=10,
        )
    fig.update_layout(
        height=300,
        margin=dict(l=8, r=8, t=24, b=8),
        paper_bgcolor=t["bg"],
        plot_bgcolor=t["plot_bg"],
        font=dict(color=t["text"], family="Inter, system-ui, sans-serif", size=11),
        showlegend=False,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=t["plot_bg"],
            bordercolor=t["accent"],
            font=dict(color=t["text"], size=11),
        ),
        xaxis=dict(title=None, gridcolor=t["grid"], showline=False, zeroline=False),
        yaxis=dict(title=None, gridcolor=t["grid"], zeroline=False),
    )
    return fig


def scenario_figure(results: pd.DataFrame) -> go.Figure:
    t = _plot_theme()
    colors = [t["green"] if v > 0 else t["red"] for v in results["Median Return"]]
    median_returns = results["Median Return"].to_numpy()
    p5 = results["P5"].to_numpy()
    p95 = results["P95"].to_numpy()
    clamp = 0.6
    upper = np.clip(p95 - median_returns, 0, clamp)
    lower = np.clip(median_returns - p5, 0, clamp)

    fig = go.Figure(go.Bar(
        x=results["Scenario"],
        y=results["Median Return"],
        marker=dict(
            color=colors,
            line=dict(width=0),
        ),
        error_y=dict(
            type="data",
            symmetric=False,
            array=upper.tolist(),
            arrayminus=lower.tolist(),
            color=t["text"],
            thickness=1,
            width=4,
        ),
        hovertemplate="<b>%{x}</b><br>Retorno mediano: %{y:.2%}<extra></extra>",
    ))
    fig.update_layout(
        height=320,
        margin=dict(l=8, r=8, t=20, b=32),
        paper_bgcolor=t["bg"],
        plot_bgcolor=t["plot_bg"],
        font=dict(color=t["text"], family="Inter, system-ui, sans-serif", size=11),
        showlegend=False,
        bargap=0.4,
        hoverlabel=dict(
            bgcolor=t["plot_bg"],
            bordercolor=t["accent"],
            font=dict(color=t["text"], size=11),
        ),
        yaxis=dict(
            title=None,
            tickformat=".0%",
            gridcolor=t["grid"],
            zeroline=True,
            zerolinecolor=t["zero"],
            range=[-0.6, 0.6],
        ),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
    )
    return fig


def correlation_heatmap(portfolio: pd.DataFrame) -> go.Figure:
    t = _plot_theme()
    corr = portfolio.corr()
    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale=[
            [0.0, t["heat_low"]],
            [0.5, t["heat_mid"]],
            [1.0, t["heat_high"]],
        ],
        zmid=0,
        zmin=-1,
        zmax=1,
        colorbar=dict(
            title=dict(text="ρ", font=dict(size=10, color=t["text"])),
            thickness=8,
            len=0.7,
            tickfont=dict(size=9, color=t["text"]),
        ),
        hovertemplate="%{y} ↔ %{x}<br>ρ = %{z:.2f}<extra></extra>",
        xgap=2,
        ygap=2,
    ))
    fig.update_layout(
        height=360,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor=t["bg"],
        plot_bgcolor=t["bg"],
        font=dict(color=t["text"], family="Inter, system-ui, sans-serif", size=10),
        xaxis=dict(tickangle=-35, side="bottom"),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def audit_log(cycle: int, critical: bool) -> pd.DataFrame:
    def _id(prefix: str, n: int) -> str:
        h = hashlib.sha1(f"{prefix}-{n}-{cycle}".encode()).hexdigest()[:6]
        return f"{prefix}-{h}"
    statuses = ["DRIFT" if critical else "VALIDATED", "VALIDATED", "SHADOW"]
    return pd.DataFrame({
        "Experiment ID": [_id("exp", 1), _id("exp", 2), _id("exp", 3)],
        "Pipeline": ["market-sim", "risk-core", "quality-gate"],
        "Generator": ["RegimeSim v0.3", "RegimeSim v0.3", "RegimeSim v0.3"],
        "Seed": [DEFAULT_SEED, DEFAULT_SEED + 11, DEFAULT_SEED + 23],
        "Dataset hash": [
            hashlib.sha1(f"ds1-{cycle}".encode()).hexdigest()[:8],
            hashlib.sha1(f"ds2-{cycle}".encode()).hexdigest()[:8],
            hashlib.sha1(f"ds3-{cycle}".encode()).hexdigest()[:8],
        ],
        "Status": statuses,
    })


# -----------------------------------------------------------------------------
# APP
# -----------------------------------------------------------------------------

init_state()
st.markdown(build_css(st.session_state.theme), unsafe_allow_html=True)

critical = bool(st.session_state.inject_black_swan)
status_html = (
    '<span class="status-chip status-alert"><span class="status-dot"></span>INCIDENTE ACTIVO</span>'
    if critical
    else '<span class="status-chip status-ok"><span class="status-dot"></span>SISTEMA NOMINAL</span>'
)

st.markdown(
    f"""
    <div class="term-header">
      <div class="brand">
        <div class="brand-mark">◈</div>
        <div>
          <div class="brand-title">VALIDATION &amp; ROBUSTNESS TERMINAL</div>
          <div class="brand-sub">Capa independiente de validación para portafolios algorítmicos · Prototipo</div>
        </div>
      </div>
      {status_html}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="info-banner">
      <div class="info-eyebrow">Qué es esto</div>
      <div class="info-body">
        Un prototipo de <b>capa independiente de validación</b> para portafolios de
        algoritmos de trading. No mide P&amp;L en vivo y no reemplaza el monitoreo
        existente. Responde una sola pregunta:
        <b>¿cómo se comportan estas estrategias bajo escenarios que no vieron en
        entrenamiento?</b>
      </div>
      <div class="info-foot">
        Construido con datos sintéticos. Sin conexión a brokers. No constituye
        asesoría financiera. Cada experimento queda etiquetado con versión del
        generador, semilla y hash del dataset para que los resultados sean
        reproducibles.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# SIDEBAR
with st.sidebar:
    theme_icon = "☀" if st.session_state.theme == "dark" else "☾"
    theme_label = f"{theme_icon}  Modo {'claro' if st.session_state.theme == 'dark' else 'oscuro'}"
    if st.button(theme_label, width="stretch", key="theme_btn"):
        toggle_theme()
        st.rerun()

    st.markdown("### Validación")
    preset_name = st.selectbox(
        "Preset",
        ["Standard validation", "Strict quality gate", "Scenario stress test"],
        index=0,
        help="Distintos presets aplican distintos umbrales.",
    )
    st.session_state.pipeline = preset_name

    st.markdown("### Algoritmo")
    st.session_state.selected_algorithm = st.selectbox(
        "Algoritmo a evaluar",
        ["Trend Alpha", "Mean Reversion Beta", "Momentum Gamma",
         "Defensive Delta", "Volatility Epsilon", "Macro Zeta"],
        index=0,
    )

    st.markdown("### Acciones")
    if st.button("↻  Refrescar experimentos", width="stretch"):
        refresh_nodes()
        st.rerun()

    if critical:
        if st.button("Restablecer escenario", width="stretch"):
            set_black_swan(False)
            st.rerun()
    else:
        if st.button("⚠  Inyectar Cisne Negro", type="primary", width="stretch"):
            set_black_swan(True)
            st.rerun()

    st.markdown("---")
    st.caption(
        "Prototipo con datos sintéticos. Semilla fija y reproducible. "
        "No ejecuta órdenes, no se conecta a brokers, no constituye asesoría financiera."
    )


# DATA
df = generate_simulation_data(inject_error=critical)
quality_report = validate_synthetic_data(df)
passed, total, pass_rate = summarize_quality(quality_report)
failed_checks = total - passed

if failed_checks:
    st.markdown(
        f"""
        <div class="banner banner-alert">
          <span>◆</span>
          <div><strong>Data drift confirmado.</strong>
          {failed_checks} regla(s) de validación fallaron. El experimento queda marcado
          para revisión. No se ejecutan órdenes ni acciones externas.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="banner banner-ok"><span>●</span>'
        '<div>Todos los contratos de datos están dentro de rango.</div></div>',
        unsafe_allow_html=True,
    )


# SECTION 1 — VALIDATION + RISK
left, right = st.columns([1, 1.5], gap="medium")

with left:
    with st.container(border=True):
        st.markdown('<div class="section-eyebrow">Contrato de datos</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Calidad del dataset</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-copy">{len(df):,} observaciones · {total} reglas · '
            f'{"bloqueado" if failed_checks else "aprobado"}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(validation_cards(quality_report), unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.progress(pass_rate, text=f"Cobertura validada: {pass_rate:.0%}")

with right:
    with st.container(border=True):
        top_a, top_b = st.columns([3.5, 1], vertical_alignment="center")
        with top_a:
            st.markdown('<div class="section-eyebrow">Motor de riesgo</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Riesgo dinámico del escenario</div>', unsafe_allow_html=True)
        with top_b:
            if st.button("ⓘ  Metodología", width="stretch"):
                risk_methodology_dialog()

        var_95, mdd = calculate_market_risk(
            df["Return"].to_numpy(),
            df["Price"].to_numpy(),
        )
        cvar_95 = historical_cvar(df["Return"].to_numpy(), 0.95)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("VaR 95%", f"{var_95:.2%}", help="Percentil 5 de retornos sintéticos.")
        c2.metric("CVaR 95%", f"{cvar_95:.2%}", help="Promedio de la cola por debajo del VaR.")
        c3.metric("Máximo drawdown", f"{mdd:.2%}", help="Mayor caída desde un máximo previo.")

        st.plotly_chart(
            price_figure(df, bool(failed_checks)),
            use_container_width=True,
            config={"displayModeBar": False},
        )


# SECTION 2 — ROBUSTNESS
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    h_a, h_b = st.columns([3, 1], vertical_alignment="center")
    with h_a:
        st.markdown('<div class="section-eyebrow">Robustez</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-title">Resultados por escenario · '
            f'{st.session_state.selected_algorithm}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-copy">Cada barra es la mediana de 100 corridas con '
            'semilla fija. La barra de error indica el rango P5–P95.</div>',
            unsafe_allow_html=True,
        )
    with h_b:
        if st.button("↻  Recalcular", width="stretch"):
            refresh_nodes()
            st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    results = evaluate_algorithm_under_scenarios(
        algorithm_name=st.session_state.selected_algorithm,
        scenarios=list(REGIMES.keys()),
        n_scenarios=100,
        base_seed=DEFAULT_SEED,
    )

    st.plotly_chart(
        scenario_figure(results),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    positive = (results["Median Return"] > 0).sum()
    total_s = len(results)
    if positive >= total_s - 1:
        verdict_text = "Robusto bajo los escenarios evaluados."
        verdict_color = "var(--green)"
    elif positive >= total_s - 2:
        verdict_text = "Marginal — sensible a por lo menos un escenario."
        verdict_color = "var(--amber)"
    else:
        verdict_text = "Frágil — falla bajo múltiples escenarios."
        verdict_color = "var(--red)"

    st.markdown(
        f'<div class="verdict" style="border-left-color:{verdict_color};">'
        f'<strong>Clasificación:</strong> {verdict_text} '
        f'({positive}/{total_s} escenarios con retorno mediano positivo.)'
        f'</div>',
        unsafe_allow_html=True,
    )


# SECTION 3 — PORTFOLIO + AUDIT
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

col_a, col_b = st.columns([1.15, 1], gap="medium")

with col_a:
    with st.container(border=True):
        st.markdown('<div class="section-eyebrow">Portafolio</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Correlación entre algoritmos</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">Correlación diaria sobre 750 días sintéticos. '
            'Correlaciones altas significan menor diversificación real.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        portfolio = generate_portfolio_returns(seed=DEFAULT_SEED)
        st.plotly_chart(
            correlation_heatmap(portfolio),
            use_container_width=True,
            config={"displayModeBar": False},
        )

with col_b:
    with st.container(border=True):
        st.markdown('<div class="section-eyebrow">Trazabilidad</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Bitácora de experimentos</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-copy">Última sincronización UTC: '
            f'{st.session_state.last_refresh:%Y-%m-%d %H:%M:%S} · '
            f'ciclo {st.session_state.refresh_cycle:04d}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.button("Ver detalle", width="stretch"):
            pipeline_dialog()

        audit_df = audit_log(st.session_state.refresh_cycle, bool(failed_checks))
        st.dataframe(
            audit_df,
            use_container_width=True,
            hide_index=True,
            height=180,
        )
        st.download_button(
            "⤓  Descargar CSV de trazabilidad",
            data=audit_df.to_csv(index=False).encode("utf-8"),
            file_name=f"trace_cycle_{st.session_state.refresh_cycle:04d}.csv",
            mime="text/csv",
            width="stretch",
        )


# SECTION 4 — REPORT
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<div class="section-eyebrow">Reporte</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Generar reporte de validación (PDF)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Documento de 6 secciones con ficha, configuración, '
        'resultados por escenario, clasificación de robustez, limitaciones y trazabilidad.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    r_a, r_b = st.columns([2, 1], vertical_alignment="bottom")
    with r_a:
        report_algorithm = st.text_input(
            "Algoritmo a reportar",
            value=st.session_state.selected_algorithm,
        )
    with r_b:
        generate_clicked = st.button("Generar PDF", type="primary", width="stretch")

    if generate_clicked:
        try:
            pdf_bytes = generate_validation_report(
                algorithm_name=report_algorithm,
                algorithm_version="v1.0",
                results=results,
                dataset_seed=DEFAULT_SEED,
                generator_version="RegimeSim v0.3",
                approved_by="—",
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.download_button(
                "⤓  Descargar reporte PDF",
                data=pdf_bytes,
                file_name=f"validation_report_{report_algorithm.replace(' ', '_')}.pdf",
                mime="application/pdf",
                width="stretch",
            )
            st.success("Reporte generado. Descargar arriba.")
        except Exception as e:
            st.error(f"Error generando el reporte: {e}")


st.markdown(
    '<div class="fineprint">'
    'Prototipo · Datos sintéticos · No ejecuta órdenes · No constituye asesoría financiera'
    '</div>',
    unsafe_allow_html=True,
)
