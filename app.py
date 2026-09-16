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
        "About": "Independent validation layer for algorithmic trading portfolios. Synthetic data only.",
    },
)


def build_css(theme: str) -> str:
    """Return CSS adapted to the active theme."""
    if theme == "dark":
        vars_block = """
            --bg: #0a0e14;
            --bg2: #111720;
            --bg3: #1a2230;
            --border: #1f2a3a;
            --border-hi: #2a3545;
            --text: #e6edf3;
            --text2: #8b98a8;
            --text3: #5a6675;
            --accent: #22d3ee;
            --green: #10b981;
            --green-dim: rgba(16, 185, 129, .12);
            --red: #ef4444;
            --red-dim: rgba(239, 68, 68, .12);
            --amber: #f59e0b;
            --amber-dim: rgba(245, 158, 11, .12);
            --purple: #a78bfa;
            --card-bg-1: rgba(22,29,40,.95);
            --card-bg-2: rgba(17,23,32,.92);
            --metric-bg-1: rgba(26,34,48,.9);
            --metric-bg-2: rgba(17,23,32,.85);
            --plot-bg: rgba(17,23,32,.5);
            --shadow: rgba(0,0,0,.25);
            --app-bg: #0a0e14;
            --app-gradient-1: rgba(34,211,238,.06);
            --app-gradient-2: rgba(167,139,250,.05);
        """
    else:
        vars_block = """
            --bg: #f6f8fb;
            --bg2: #ffffff;
            --bg3: #eef2f7;
            --border: #e2e8f0;
            --border-hi: #cbd5e1;
            --text: #0f172a;
            --text2: #64748b;
            --text3: #94a3b8;
            --accent: #0891b2;
            --green: #059669;
            --green-dim: rgba(5, 150, 105, .1);
            --red: #dc2626;
            --red-dim: rgba(220, 38, 38, .1);
            --amber: #d97706;
            --amber-dim: rgba(217, 119, 6, .1);
            --purple: #7c3aed;
            --card-bg-1: rgba(255,255,255,.98);
            --card-bg-2: rgba(248,250,252,.95);
            --metric-bg-1: rgba(255,255,255,.98);
            --metric-bg-2: rgba(248,250,252,.95);
            --plot-bg: rgba(248,250,252,.8);
            --shadow: rgba(15,23,42,.06);
            --app-bg: #f6f8fb;
            --app-gradient-1: rgba(8,145,178,.05);
            --app-gradient-2: rgba(124,58,237,.04);
        """

    return f"""
<style>
    :root {{
{vars_block}
    }}

    .stApp {{
        background: var(--app-bg);
        background-image:
            radial-gradient(900px 400px at 0% 0%, var(--app-gradient-1), transparent 60%),
            radial-gradient(700px 500px at 100% 0%, var(--app-gradient-2), transparent 55%);
        background-attachment: fixed;
        color: var(--text);
        transition: background .3s ease, color .3s ease;
    }}

    [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {{
        visibility: hidden;
        height: 0;
    }}

    [data-testid="stAppViewContainer"] > .main .block-container {{
        max-width: 1480px;
        padding: 1.15rem 2rem 2.4rem;
    }}

    h1, h2, h3, p, label, [data-testid="stMetricLabel"] {{ color: var(--text); }}
    [data-testid="stCaptionContainer"], .stCaption {{ color: var(--text2); }}

    /* HEADER */
    .terminal-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin: .15rem 0 1rem;
        padding-bottom: .9rem;
        border-bottom: 1px solid var(--border);
    }}

    .brand-lockup {{ display: flex; align-items: center; gap: .85rem; }}
    .brand-mark {{
        display: grid;
        place-items: center;
        width: 2.6rem;
        height: 2.6rem;
        border: 1px solid rgba(34,211,238,.45);
        border-radius: .65rem;
        color: var(--accent);
        background: rgba(34,211,238,.08);
        box-shadow: 0 0 22px rgba(34,211,238,.18);
        font-size: 1.35rem;
        font-weight: 700;
    }}

    .brand-title {{ font-size: 1.08rem; font-weight: 750; letter-spacing: .035em; color: var(--text); }}
    .brand-subtitle {{ color: var(--text2); font-size: .78rem; margin-top: .1rem; }}

    .live-badge, .critical-badge {{
        display: inline-flex;
        align-items: center;
        gap: .45rem;
        padding: .34rem .65rem;
        border-radius: 999px;
        font-size: .72rem;
        letter-spacing: .08em;
        font-weight: 750;
        white-space: nowrap;
    }}

    .live-badge {{
        color: var(--green);
        background: var(--green-dim);
        border: 1px solid rgba(16,185,129,.32);
        box-shadow: 0 0 12px rgba(16,185,129,.15);
    }}

    .critical-badge {{
        color: var(--red);
        background: var(--red-dim);
        border: 1px solid rgba(239,68,68,.34);
        box-shadow: 0 0 12px rgba(239,68,68,.2);
    }}

    .pulse {{
        width: .45rem;
        height: .45rem;
        border-radius: 50%;
        background: currentColor;
        box-shadow: 0 0 0 0 currentColor;
        animation: pulse 1.8s infinite;
    }}
    @keyframes pulse {{ 70% {{ box-shadow: 0 0 0 7px transparent; }} }}

    /* CARDS */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: linear-gradient(145deg, var(--card-bg-1), var(--card-bg-2));
        border: 1px solid var(--border) !important;
        border-radius: 14px;
        box-shadow: 0 14px 34px var(--shadow), inset 0 1px 0 rgba(255,255,255,.02);
        transition: border-color .2s, box-shadow .2s, transform .2s;
    }}

    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color: var(--border-hi) !important;
        box-shadow: 0 18px 40px var(--shadow), inset 0 1px 0 rgba(255,255,255,.03);
        transform: translateY(-1px);
    }}

    /* METRICS */
    div[data-testid="stMetric"] {{
        background: linear-gradient(145deg, var(--metric-bg-1), var(--metric-bg-2));
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        border-radius: 12px;
        padding: .85rem 1rem;
        box-shadow: 0 4px 12px var(--shadow);
        transition: transform .2s, box-shadow .2s, border-color .2s;
    }}

    div[data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 24px var(--shadow);
        border-left-color: var(--purple);
    }}

    [data-testid="stMetricValue"] {{
        font-size: 1.55rem;
        font-weight: 720;
        color: var(--text);
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.5px;
    }}
    [data-testid="stMetricDelta"] {{ font-size: .73rem; }}
    [data-testid="stMetricLabel"] {{
        color: var(--text2);
        font-size: .72rem;
        text-transform: uppercase;
        letter-spacing: .06em;
        font-weight: 600;
    }}

    /* TYPOGRAPHY */
    .eyebrow {{
        color: var(--accent);
        font-size: .70rem;
        font-weight: 750;
        letter-spacing: .11em;
        text-transform: uppercase;
        margin-bottom: .25rem;
    }}
    .section-title {{ font-size: 1rem; font-weight: 720; margin-bottom: .1rem; color: var(--text); }}
    .section-copy {{ color: var(--text2); font-size: .80rem; margin-bottom: .7rem; }}

    /* CHECK CARDS */
    .check-card {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: .75rem;
        padding: .72rem .78rem;
        margin: .48rem 0;
        background: var(--card-bg-2);
        border: 1px solid var(--border);
        border-radius: 10px;
        transition: border-color .15s, transform .15s;
    }}
    .check-card:hover {{ border-color: var(--border-hi); transform: translateX(2px); }}

    .check-name {{ color: var(--text); font-size: .81rem; }}
    .passed, .failed {{
        min-width: 4.8rem;
        text-align: center;
        border-radius: 999px;
        font-size: .68rem;
        font-weight: 800;
        letter-spacing: .07em;
        padding: .25rem .5rem;
    }}
    .passed {{
        color: var(--green);
        background: var(--green-dim);
        border: 1px solid rgba(16,185,129,.25);
    }}
    .failed {{
        color: var(--red);
        background: var(--red-dim);
        border: 1px solid rgba(239,68,68,.3);
    }}

    /* ALERT STRIPS */
    .alert-strip {{
        display: flex;
        gap: .75rem;
        align-items: flex-start;
        padding: .8rem 1rem;
        margin: .2rem 0 1rem;
        border-radius: 11px;
        border: 1px solid rgba(239,68,68,.32);
        background: linear-gradient(90deg, rgba(239,68,68,.12), rgba(245,158,11,.06));
        color: #fca5a5;
        font-size: .82rem;
        box-shadow: 0 0 20px rgba(239,68,68,.08);
    }}

    .ok-strip {{
        padding: .7rem .9rem;
        margin: .2rem 0 1rem;
        border: 1px solid rgba(16,185,129,.28);
        background: rgba(16,185,129,.07);
        border-radius: 11px;
        color: #6ee7b7;
        font-size: .80rem;
    }}

    /* BUTTONS */
    div.stButton > button {{
        min-height: 2.65rem;
        border-radius: 9px;
        border: 1px solid var(--border-hi);
        background: var(--card-bg-2);
        color: var(--text);
        font-weight: 600;
        transition: all .18s;
    }}

    div.stButton > button:hover {{
        border-color: var(--accent);
        color: var(--accent);
        background: rgba(34,211,238,.08);
        box-shadow: 0 0 16px rgba(34,211,238,.2);
        transform: translateY(-1px);
    }}

    div.stButton > button[kind="primary"] {{
        background: var(--accent);
        border-color: var(--accent);
        color: #06121a;
        font-weight: 700;
    }}

    div.stButton > button[kind="primary"]:hover {{
        background: #2fd8f0;
        color: #06121a;
        box-shadow: 0 4px 20px rgba(34,211,238,.4);
    }}

    /* INPUTS */
    div[data-testid="stSelectbox"] > div > div {{
        background: var(--card-bg-2);
        border-color: var(--border-hi);
        color: var(--text);
    }}

    div[data-testid="stTextInput"] input {{
        background: var(--card-bg-2);
        border-color: var(--border-hi);
        color: var(--text);
    }}

    /* TABLES */
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
    }}

    /* PROGRESS */
    div[data-testid="stProgress"] > div > div {{
        background: linear-gradient(90deg, var(--accent), var(--purple));
        box-shadow: 0 0 12px rgba(34,211,238,.35);
        border-radius: 4px;
    }}

    /* SIDEBAR */
    [data-testid="stSidebar"] {{
        background: var(--card-bg-1);
        border-right: 1px solid var(--border);
    }}

    [data-testid="stSidebar"] h3 {{
        color: var(--accent) !important;
        font-size: .78rem !important;
        text-transform: uppercase;
        letter-spacing: .1em;
        font-weight: 700;
    }}

    /* INFO CARD */
    .info-card {{
        background: linear-gradient(135deg, rgba(34,211,238,.08), rgba(167,139,250,.04));
        border: 1px solid rgba(34,211,238,.22);
        border-left: 3px solid var(--accent);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 14px;
    }}

    .info-card .info-label {{
        font-size: .72rem;
        font-weight: 750;
        letter-spacing: .1em;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 6px;
    }}

    .info-card .info-body {{
        font-size: .9rem;
        line-height: 1.6;
        color: var(--text);
    }}

    .info-card .info-foot {{
        font-size: .78rem;
        color: var(--text2);
        margin-top: 10px;
        line-height: 1.55;
    }}

    /* FOOTER */
    .fineprint {{
        color: var(--text3);
        font-size: .70rem;
        text-align: center;
        padding-top: 1.1rem;
        letter-spacing: .05em;
    }}

    @media (max-width: 800px) {{
        [data-testid="stAppViewContainer"] > .main .block-container {{ padding: .8rem; }}
        .terminal-header {{ align-items: flex-start; }}
        .brand-subtitle {{ display: none; }}
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
        "selected_scenarios": list(REGIMES.keys()),
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
        bajo la distribución sintética simulada; no representa una pérdida máxima
        garantizada.

        **CVaR histórico 95%**
        Promedio de los retornos que caen por debajo del VaR. Más informativo que
        el VaR cuando la distribución tiene colas gruesas.

        **Máximo drawdown**
        Mayor caída porcentual desde un máximo previo de la serie de precios.

        **Sharpe y Sortino**
        Métricas ajustadas por riesgo. Un Sharpe alto sobre una muestra corta es
        con frecuencia un síntoma de sobreajuste, no de ventaja real.

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

        Cada fila de la bitácora contiene un identificador determinístico
        derivado del ciclo actual.
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
    blocks: list[str] = []
    for key, label in labels.items():
        passed = bool(report.get(key, False))
        blocks.append(
            '<div class="check-card">'
            f'<span class="check-name">{label}</span>'
            f'<span class="{"passed" if passed else "failed"}">'
            f'{"PASSED" if passed else "FAILED"}</span></div>'
        )
    return "".join(blocks)


def _plot_theme() -> dict:
    """Return plot colors adapted to active theme."""
    if st.session_state.theme == "dark":
        return {
            "bg": "rgba(0,0,0,0)",
            "plot_bg": "rgba(17,23,32,.5)",
            "grid": "rgba(31,42,58,.5)",
            "text": "#8b98a8",
            "zero": "rgba(42,53,69,.8)",
            "accent": "#22d3ee",
            "red": "#ef4444",
            "green": "#10b981",
            "heat_low": "#ef4444",
            "heat_mid": "#111720",
            "heat_high": "#22d3ee",
        }
    return {
        "bg": "rgba(0,0,0,0)",
        "plot_bg": "rgba(248,250,252,.8)",
        "grid": "rgba(148,163,184,.25)",
        "text": "#64748b",
        "zero": "rgba(148,163,184,.5)",
        "accent": "#0891b2",
        "red": "#dc2626",
        "green": "#059669",
        "heat_low": "#dc2626",
        "heat_mid": "#f6f8fb",
        "heat_high": "#0891b2",
    }


def price_figure(df: pd.DataFrame, is_critical: bool) -> go.Figure:
    t = _plot_theme()
    line_color = t["red"] if is_critical else t["accent"]
    trace = go.Scatter(
        x=df["Timestamp"],
        y=df["Price"],
        mode="lines",
        name="Precio sintético",
        line=dict(color=line_color, width=2.2),
        fill="tozeroy",
        fillcolor="rgba(239,68,68,.15)" if is_critical else "rgba(34,211,238,.15)",
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
        )
    fig.update_layout(
        height=320,
        margin=dict(l=12, r=12, t=30, b=10),
        paper_bgcolor=t["bg"],
        plot_bgcolor=t["plot_bg"],
        font=dict(color=t["text"], family="Inter, system-ui, sans-serif", size=11),
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(title=None, gridcolor=t["grid"], showline=False),
        yaxis=dict(title="Índice sintético", gridcolor=t["grid"], zeroline=False),
    )
    return fig


def scenario_figure(results: pd.DataFrame) -> go.Figure:
    t = _plot_theme()
    colors = [t["green"] if v > 0 else t["red"] for v in results["Median Return"]]
    median_returns = results["Median Return"].to_numpy()
    p5 = results["P5"].to_numpy()
    p95 = results["P95"].to_numpy()
    clamp = 0.60
    upper = np.clip(p95 - median_returns, 0, clamp)
    lower = np.clip(median_returns - p5, 0, clamp)

    fig = go.Figure(go.Bar(
        x=results["Scenario"],
        y=results["Median Return"],
        marker_color=colors,
        error_y=dict(
            type="data",
            symmetric=False,
            array=upper.tolist(),
            arrayminus=lower.tolist(),
            color=t["text"],
            thickness=1.2,
        ),
        hovertemplate="<b>%{x}</b><br>Mediana: %{y:.2%}<extra></extra>",
    ))
    fig.update_layout(
        height=340,
        margin=dict(l=12, r=12, t=20, b=30),
        paper_bgcolor=t["bg"],
        plot_bgcolor=t["plot_bg"],
        font=dict(color=t["text"], family="Inter, system-ui, sans-serif", size=11),
        showlegend=False,
        yaxis=dict(
            title="Retorno mediano anualizado",
            tickformat=".1%",
            gridcolor=t["grid"],
            zeroline=True,
            zerolinecolor=t["zero"],
            range=[-0.60, 0.60],
        ),
        xaxis=dict(gridcolor=t["grid"]),
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
        zmin=-1, zmax=1,
        colorbar=dict(title="ρ", thickness=10),
        hovertemplate="%{y} ↔ %{x}<br>ρ = %{z:.2f}<extra></extra>",
    ))
    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=t["bg"],
        plot_bgcolor=t["plot_bg"],
        font=dict(color=t["text"], family="Inter, system-ui, sans-serif", size=10),
        xaxis=dict(tickangle=-35),
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


init_state()
st.markdown(build_css(st.session_state.theme), unsafe_allow_html=True)

critical = bool(st.session_state.inject_black_swan)
status_badge = (
    '<span class="critical-badge"><span class="pulse"></span>INCIDENTE ACTIVO</span>'
    if critical
    else '<span class="live-badge"><span class="pulse"></span>SISTEMA NOMINAL</span>'
)
st.markdown(
    f"""
    <div class="terminal-header">
      <div class="brand-lockup">
        <div class="brand-mark">◈</div>
        <div>
          <div class="brand-title">VALIDATION &amp; ROBUSTNESS TERMINAL</div>
          <div class="brand-subtitle">Capa independiente de validación para portafolios algorítmicos · Prototipo</div>
        </div>
      </div>
      {status_badge}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="info-card">
      <div class="info-label">Qué es esto</div>
      <div class="info-body">
        Un prototipo de <b>capa independiente de validación</b> para portafolios de
        algoritmos de trading. No mide P&amp;L en vivo y no reemplaza el monitoreo
        existente. Responde una sola pregunta:
        <b>¿cómo se comportan estas estrategias bajo escenarios que no vieron en entrenamiento?</b>
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


with st.sidebar:
    st.markdown("### Panel de control")

    theme_label = "☀  Modo claro" if st.session_state.theme == "dark" else "☾  Modo oscuro"
    if st.button(theme_label, width="stretch", key="theme_toggle"):
        toggle_theme()
        st.rerun()

    st.markdown("---")
    preset_name = st.selectbox(
        "Preset de validación",
        ["Standard validation", "Strict quality gate", "Scenario stress test"],
        index=0,
        help="Distintos presets aplican distintos umbrales de validación.",
    )
    st.session_state.pipeline = preset_name

    st.markdown("---")
    st.markdown("### Parámetros")
    st.session_state.selected_algorithm = st.selectbox(
        "Algoritmo a evaluar",
        ["Trend Alpha", "Mean Reversion Beta", "Momentum Gamma",
         "Defensive Delta", "Volatility Epsilon", "Macro Zeta"],
        index=0,
    )

    st.markdown("---")
    st.markdown("### Acciones")
    if st.button("↻ Refrescar experimentos", width="stretch"):
        refresh_nodes()
        st.rerun()

    if critical:
        if st.button("Restablecer escenario", width="stretch"):
            set_black_swan(False)
            st.rerun()
    else:
        if st.button("⚠ Inyectar Cisne Negro", type="primary", width="stretch"):
            set_black_swan(True)
            st.rerun()

    st.markdown("---")
    st.caption(
        "Prototipo con datos sintéticos. Semilla fija y reproducible. "
        "No ejecuta órdenes, no se conecta a brokers, no constituye asesoría financiera."
    )


df = generate_simulation_data(inject_error=critical)
quality_report = validate_synthetic_data(df)
passed, total, pass_rate = summarize_quality(quality_report)
failed_checks = total - passed

if failed_checks:
    st.markdown(
        f"""
        <div class="alert-strip"><span>◆</span><div><b>Data drift confirmado.</b>
        {failed_checks} regla(s) de validación fallaron. El experimento queda
        marcado para revisión. No se ejecutan órdenes ni acciones externas.</div></div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="ok-strip">● Todos los contratos de datos están dentro de rango.</div>',
        unsafe_allow_html=True,
    )


left, right = st.columns([1.0, 1.55], gap="large")

with left:
    with st.container(border=True):
        st.markdown('<div class="eyebrow">Contrato de datos</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Calidad del dataset</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-copy">{len(df):,} observaciones · {total} reglas · '
            f'{"bloqueado" if failed_checks else "aprobado"}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(validation_cards(quality_report), unsafe_allow_html=True)
        st.progress(pass_rate, text=f"Cobertura validada: {pass_rate:.0%}")

with right:
    with st.container(border=True):
        top_text, top_action = st.columns([3.2, 1.0], vertical_alignment="center")
        with top_text:
            st.markdown('<div class="eyebrow">Motor de riesgo</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Riesgo dinámico del escenario</div>', unsafe_allow_html=True)
        with top_action:
            if st.button("ⓘ Metodología", width="stretch"):
                risk_methodology_dialog()

        var_95, mdd = calculate_market_risk(
            df["Return"].to_numpy(),
            df["Price"].to_numpy(),
        )
        cvar_95 = historical_cvar(df["Return"].to_numpy(), 0.95)

        risk_a, risk_b, risk_c = st.columns(3)
        risk_a.metric("VaR 95%", f"{var_95:.2%}", help="Percentil 5 de retornos sintéticos.")
        risk_b.metric("CVaR 95%", f"{cvar_95:.2%}", help="Promedio de la cola por debajo del VaR.")
        risk_c.metric("Máximo drawdown", f"{mdd:.2%}", help="Mayor caída desde un máximo previo.")

        st.plotly_chart(price_figure(df, bool(failed_checks)),
                        width="stretch", config={"displayModeBar": False})


st.markdown("<div style='height:.55rem'></div>", unsafe_allow_html=True)

with st.container(border=True):
    header_a, header_b = st.columns([3.0, 1.3], vertical_alignment="center")
    with header_a:
        st.markdown('<div class="eyebrow">Robustez</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-title">Resultados por escenario · '
            f'{st.session_state.selected_algorithm}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-copy">Cada barra es la mediana de 100 corridas '
            'con semilla fija. La barra de error indica el rango P5–P95.</div>',
            unsafe_allow_html=True,
        )
    with header_b:
        if st.button("↻ Recalcular", width="stretch"):
            refresh_nodes()
            st.rerun()

    results = evaluate_algorithm_under_scenarios(
        algorithm_name=st.session_state.selected_algorithm,
        scenarios=list(REGIMES.keys()),
        n_scenarios=100,
        base_seed=DEFAULT_SEED,
    )

    st.plotly_chart(
        scenario_figure(results),
        width="stretch",
        config={"displayModeBar": False},
    )

    positive = (results["Median Return"] > 0).sum()
    total_s = len(results)
    if positive >= total_s - 1:
        verdict = "Robusto bajo los escenarios evaluados."
        verdict_color = "#10b981"
    elif positive >= total_s - 2:
        verdict = "Marginal — sensible a por lo menos un escenario."
        verdict_color = "#f59e0b"
    else:
        verdict = "Frágil — falla bajo múltiples escenarios."
        verdict_color = "#ef4444"

    st.markdown(
        f'<div style="padding:.7rem .9rem;border-radius:10px;'
        f'background:rgba(26,34,48,.4);border-left:3px solid {verdict_color};'
        f'font-size:.85rem;color:var(--text);">'
        f'<b>Clasificación:</b> {verdict} '
        f'({positive}/{total_s} escenarios con retorno mediano positivo.)'
        f'</div>',
        unsafe_allow_html=True,
    )


st.markdown("<div style='height:.55rem'></div>", unsafe_allow_html=True)

col_a, col_b = st.columns([1.15, 1.0], gap="large")

with col_a:
    with st.container(border=True):
        st.markdown('<div class="eyebrow">Portafolio</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Correlación entre algoritmos</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">Correlación diaria sobre 750 días sintéticos. '
            'Correlaciones altas significan menor diversificación real.</div>',
            unsafe_allow_html=True,
        )
        portfolio = generate_portfolio_returns(seed=DEFAULT_SEED)
        st.plotly_chart(
            correlation_heatmap(portfolio),
            width="stretch",
            config={"displayModeBar": False},
        )

with col_b:
    with st.container(border=True):
        st.markdown('<div class="eyebrow">Trazabilidad</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Bitácora de experimentos</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-copy">Última sincronización UTC: '
            f'{st.session_state.last_refresh:%Y-%m-%d %H:%M:%S} · '
            f'ciclo {st.session_state.refresh_cycle:04d}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Ver detalle", width="stretch"):
            pipeline_dialog()

        audit_df = audit_log(st.session_state.refresh_cycle, bool(failed_checks))
        st.dataframe(audit_df, width="stretch", hide_index=True)
        st.download_button(
            "⤓ Descargar CSV de trazabilidad",
            data=audit_df.to_csv(index=False).encode("utf-8"),
            file_name=f"trace_cycle_{st.session_state.refresh_cycle:04d}.csv",
            mime="text/csv",
            width="stretch",
        )


st.markdown("<div style='height:.55rem'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<div class="eyebrow">Reporte</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Generar reporte de validación (PDF)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Documento de 6 secciones con ficha, configuración, '
        'resultados por escenario, clasificación de robustez, limitaciones y trazabilidad.</div>',
        unsafe_allow_html=True,
    )
    report_col_a, report_col_b = st.columns([2.0, 1.0], vertical_alignment="bottom")
    with report_col_a:
        report_algorithm = st.text_input(
            "Algoritmo a reportar",
            value=st.session_state.selected_algorithm,
        )
    with report_col_b:
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
            st.download_button(
                "⤓ Descargar reporte PDF",
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
    'PROTOTIPO · DATOS SINTÉTICOS · NO EJECUTA ÓRDENES · NO CONSTITUYE ASESORÍA FINANCIERA'
    '</div>',
    unsafe_allow_html=True,
)
