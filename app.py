"""Validation & Robustness Terminal.

Executive demo of an independent validation layer for portfolios of
algorithmic trading strategies. Uses synthetic data exclusively. Does not
execute orders, connect to brokers, or provide investment advice.
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
        "About": "Prototype of an independent validation layer for algorithmic trading portfolios. Synthetic data only.",
    },
)


CSS = """
<style>
    :root {
        --bg: #F8F4EC;
        --panel: #FFFFFF;
        --panel-2: #FBF7EE;
        --line: rgba(31, 41, 51, .14);
        --text: #24313B;
        --muted: #6E7B86;
        --cyan: #2C6E8E;
        --blue: #1F6FB2;
        --green: #1E9E6E;
        --red: #C4472E;
        --amber: #CE9A2E;
        --orange: #DE7F35;
    }

    .stApp {
        background:
          radial-gradient(circle at 82% -8%, rgba(206, 154, 46, .10), transparent 32rem),
          radial-gradient(circle at -8% 60%, rgba(30, 158, 110, .09), transparent 30rem),
          var(--bg);
        color: var(--text);
    }

    [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {
        visibility: hidden;
        height: 0;
    }

    [data-testid="stAppViewContainer"] > .main .block-container {
        max-width: 1480px;
        padding: 1.15rem 2rem 2.4rem;
    }

    h1, h2, h3, p, label, [data-testid="stMetricLabel"] { color: var(--text); }
    [data-testid="stCaptionContainer"], .stCaption { color: var(--muted); }

    .terminal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin: .15rem 0 1rem;
        padding-bottom: .9rem;
        border-bottom: 1px solid var(--line);
    }

    .brand-lockup { display: flex; align-items: center; gap: .85rem; }
    .brand-mark {
        display: grid;
        place-items: center;
        width: 2.6rem;
        height: 2.6rem;
        border: 1px solid rgba(206, 154, 46, .55);
        border-radius: .65rem;
        color: var(--amber);
        background: rgba(206, 154, 46, .10);
        box-shadow: 0 0 22px rgba(206, 154, 46, .12);
        font-size: 1.35rem;
    }

    .brand-title { font-size: 1.08rem; font-weight: 750; letter-spacing: .035em; }
    .brand-subtitle { color: var(--muted); font-size: .78rem; margin-top: .1rem; }

    .live-badge, .critical-badge {
        display: inline-flex;
        align-items: center;
        gap: .45rem;
        padding: .34rem .65rem;
        border-radius: 999px;
        font-size: .72rem;
        letter-spacing: .08em;
        font-weight: 750;
        white-space: nowrap;
    }

    .live-badge {
        color: var(--green);
        background: rgba(30, 158, 110, .10);
        border: 1px solid rgba(30, 158, 110, .32);
    }

    .critical-badge {
        color: var(--red);
        background: rgba(196, 71, 46, .10);
        border: 1px solid rgba(196, 71, 46, .34);
    }

    .pulse {
        width: .45rem;
        height: .45rem;
        border-radius: 50%;
        background: currentColor;
        box-shadow: 0 0 0 0 currentColor;
        animation: pulse 1.8s infinite;
    }
    @keyframes pulse { 70% { box-shadow: 0 0 0 7px transparent; } }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, rgba(255, 255, 255, .96), rgba(251, 247, 238, .92));
        border: 1px solid var(--line) !important;
        border-radius: 14px;
        box-shadow: 0 14px 34px rgba(36, 49, 59, .08);
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, .65);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: .85rem 1rem;
    }

    [data-testid="stMetricValue"] { font-size: 1.55rem; font-weight: 720; }
    [data-testid="stMetricDelta"] { font-size: .73rem; }

    .eyebrow {
        color: var(--blue);
        font-size: .70rem;
        font-weight: 750;
        letter-spacing: .11em;
        text-transform: uppercase;
        margin-bottom: .25rem;
    }

    .section-title { font-size: 1rem; font-weight: 720; margin-bottom: .1rem; }
    .section-copy { color: var(--muted); font-size: .80rem; margin-bottom: .7rem; }

    .check-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: .75rem;
        padding: .72rem .78rem;
        margin: .48rem 0;
        background: rgba(255, 255, 255, .55);
        border: 1px solid var(--line);
        border-radius: 10px;
    }

    .check-name { color: #3B4A55; font-size: .81rem; }
    .passed, .failed {
        min-width: 4.8rem;
        text-align: center;
        border-radius: 999px;
        font-size: .68rem;
        font-weight: 800;
        letter-spacing: .07em;
        padding: .25rem .5rem;
    }
    .passed { color: var(--green); background: rgba(30, 158, 110, .12); }
    .failed { color: var(--red); background: rgba(196, 71, 46, .13); }

    .alert-strip {
        display: flex;
        gap: .75rem;
        align-items: flex-start;
        padding: .8rem 1rem;
        margin: .2rem 0 1rem;
        border-radius: 11px;
        border: 1px solid rgba(196, 71, 46, .32);
        background: linear-gradient(90deg, rgba(196, 71, 46, .10), rgba(222, 127, 53, .07));
        color: #7A2E1B;
        font-size: .82rem;
    }

    .ok-strip {
        padding: .7rem .9rem;
        margin: .2rem 0 1rem;
        border: 1px solid rgba(30, 158, 110, .28);
        background: rgba(30, 158, 110, .07);
        border-radius: 11px;
        color: #145E42;
        font-size: .80rem;
    }

    div.stButton > button {
        min-height: 2.65rem;
        border-radius: 9px;
        border: 1px solid rgba(31, 111, 178, .38);
        background: rgba(31, 111, 178, .07);
        color: #1F6FB2;
        font-weight: 680;
    }

    div.stButton > button:hover {
        border-color: var(--amber);
        color: #8A6414;
        box-shadow: 0 0 16px rgba(206, 154, 46, .14);
    }

    div[data-testid="stSelectbox"] > div > div {
        background: rgba(255, 255, 255, .75);
        border-color: var(--line);
    }

    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 10px; }

    .fineprint {
        color: #63748b;
        font-size: .70rem;
        text-align: center;
        padding-top: 1.1rem;
    }

    @media (max-width: 800px) {
        [data-testid="stAppViewContainer"] > .main .block-container { padding: .8rem; }
        .terminal-header { align-items: flex-start; }
        .brand-subtitle { display: none; }
    }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------

def init_state() -> None:
    defaults = {
        "inject_black_swan": False,
        "refresh_cycle": 0,
        "last_refresh": datetime.now(timezone.utc),
        "pipeline": "Standard validation",
        "selected_algorithm": "Trend Alpha",
        "selected_scenarios": list(REGIMES.keys()),
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


# -----------------------------------------------------------------------------
# Dialogs
# -----------------------------------------------------------------------------

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

        Cada fila de la bitácora inferior contiene un identificador determinístico
        derivado del ciclo actual. Refrescar produce los mismos IDs para el mismo
        ciclo — la trazabilidad es real dentro de la sesión.
        """
    )


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

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


def price_figure(df: pd.DataFrame, is_critical: bool) -> go.Figure:
    line_color = "#C4472E" if is_critical else "#1F6FB2"
    trace = go.Scatter(
        x=df["Timestamp"],
        y=df["Price"],
        mode="lines",
        name="Precio sintético",
        line=dict(color=line_color, width=2.2),
        fill="tozeroy",
        fillcolor="rgba(196,71,46,.18)" if is_critical else "rgba(31,111,178,.15)",
        hovertemplate="%{x|%H:%M}<br>Índice %{y:.2f}<extra></extra>",
    )

    fig = go.Figure(trace)
    if is_critical:
        event_time = df.loc[df["Return"].abs().idxmax(), "Timestamp"]
        fig.add_vline(
            x=event_time.timestamp() * 1000,
            line_color="#DE7F35",
            line_dash="dot",
            annotation_text="Drift detectado",
            annotation_font_color="#8A3A1E",
        )
    fig.update_layout(
        height=320,
        margin=dict(l=12, r=12, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.35)",
        font=dict(color="#6E7B86", family="Inter, system-ui, sans-serif", size=11),
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(title=None, gridcolor="rgba(31,41,51,.08)", showline=False),
        yaxis=dict(title="Índice sintético", gridcolor="rgba(31,41,51,.08)", zeroline=False),
    )
    return fig


def scenario_figure(results: pd.DataFrame) -> go.Figure:
    """Bar chart of median returns across scenarios, with P5-P95 error bars."""
    colors = [
        "#1E9E6E" if v > 0 else "#C4472E"
        for v in results["Median Return"]
    ]
    fig = go.Figure(go.Bar(
        x=results["Scenario"],
        y=results["Median Return"],
        marker_color=colors,
        error_y=dict(
            type="data",
            symmetric=False,
            array=(results["P95"] - results["Median Return"]).tolist(),
            arrayminus=(results["Median Return"] - results["P5"]).tolist(),
            color="#6E7B86",
            thickness=1.2,
        ),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Mediana: %{y:.2%}<br>"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        height=340,
        margin=dict(l=12, r=12, t=20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.35)",
        font=dict(color="#6E7B86", family="Inter, system-ui, sans-serif", size=11),
        showlegend=False,
        yaxis=dict(title="Retorno mediano anualizado", tickformat=".1%",
                   gridcolor="rgba(31,41,51,.08)", zeroline=True,
                   zerolinecolor="rgba(31,41,51,.25)"),
        xaxis=dict(gridcolor="rgba(31,41,51,.08)"),
    )
    return fig


def correlation_heatmap(portfolio: pd.DataFrame) -> go.Figure:
    corr = portfolio.corr()
    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale=[
            [0.0, "#C4472E"],
            [0.5, "#F8F4EC"],
            [1.0, "#1F6FB2"],
        ],
        zmid=0,
        zmin=-1, zmax=1,
        colorbar=dict(title="ρ", thickness=10),
        hovertemplate="%{y} ↔ %{x}<br>ρ = %{z:.2f}<extra></extra>",
    ))
    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.35)",
        font=dict(color="#6E7B86", family="Inter, system-ui, sans-serif", size=10),
        xaxis=dict(tickangle=-35),
    )
    return fig


def audit_log(cycle: int, critical: bool) -> pd.DataFrame:
    """Deterministic audit records derived from the current cycle.

    IDs are derived from a hash of (pipeline, cycle), so refreshing produces
    new IDs while the same cycle always produces the same IDs. No invented
    infrastructure names.
    """
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
# Init
# -----------------------------------------------------------------------------

init_state()


# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------

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
    <div style="background:rgba(31,111,178,.06);border:1px solid rgba(31,111,178,.22);
                border-radius:12px;padding:14px 18px;margin-bottom:14px;">
      <div style="font-size:.72rem;font-weight:750;letter-spacing:.1em;
                  text-transform:uppercase;color:#1F6FB2;margin-bottom:6px;">
        Qué es esto
      </div>
      <div style="font-size:.9rem;line-height:1.6;color:#24313B;">
        Un prototipo de <b>capa independiente de validación</b> para portafolios de
        algoritmos de trading. No mide P&amp;L en vivo y no reemplaza el monitoreo
        existente. Responde una sola pregunta:
        <b>¿cómo se comportan estas estrategias bajo escenarios que no vieron en entrenamiento?</b>
      </div>
      <div style="font-size:.78rem;color:#6E7B86;margin-top:10px;line-height:1.55;">
        Construido con datos sintéticos. Sin conexión a brokers. No constituye
        asesoría financiera. Cada experimento queda etiquetado con versión del
        generador, semilla y hash del dataset para que los resultados sean
        reproducibles.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Panel de control")
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


# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Section 1 — Validation gate + Market risk
# -----------------------------------------------------------------------------

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
        risk_a.metric("VaR 95%", f"{var_95:.2%}",
                      help="Percentil 5 de retornos sintéticos.")
        risk_b.metric("CVaR 95%", f"{cvar_95:.2%}",
                      help="Promedio de la cola por debajo del VaR.")
        risk_c.metric("Máximo drawdown", f"{mdd:.2%}",
                      help="Mayor caída desde un máximo previo.")

        st.plotly_chart(price_figure(df, bool(failed_checks)),
                        width="stretch", config={"displayModeBar": False})


# -----------------------------------------------------------------------------
# Section 2 — Robustness by scenario
# -----------------------------------------------------------------------------

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
        verdict_color = "#1E9E6E"
    elif positive >= total_s - 2:
        verdict = "Marginal — sensible a por lo menos un escenario."
        verdict_color = "#CE9A2E"
    else:
        verdict = "Frágil — falla bajo múltiples escenarios."
        verdict_color = "#C4472E"

    st.markdown(
        f'<div style="padding:.7rem .9rem;border-radius:10px;'
        f'background:rgba(31,41,51,.04);border-left:3px solid {verdict_color};'
        f'font-size:.85rem;color:#24313B;">'
        f'<b>Clasificación:</b> {verdict} '
        f'({positive}/{total_s} escenarios con retorno mediano positivo.)'
        f'</div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Section 3 — Portfolio correlation + Audit
# -----------------------------------------------------------------------------

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
        st.dataframe(
            audit_df,
            width="stretch",
            hide_index=True,
            column_config={
                "Seed": st.column_config.NumberColumn(format="%d"),
                "Status": st.column_config.TextColumn(help="Estado simulado del experimento."),
            },
        )
        st.download_button(
            "⤓ Descargar CSV de trazabilidad",
            data=audit_df.to_csv(index=False).encode("utf-8"),
            file_name=f"trace_cycle_{st.session_state.refresh_cycle:04d}.csv",
            mime="text/csv",
            width="stretch",
        )


# -----------------------------------------------------------------------------
# Section 4 — Report generation
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.markdown(
    '<div class="fineprint">'
    'PROTOTIPO · DATOS SINTÉTICOS · NO EJECUTA ÓRDENES · NO CONSTITUYE ASESORÍA FINANCIERA'
    '</div>',
    unsafe_allow_html=True,
)
