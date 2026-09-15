"""Quantum & MLOps Governance Terminal.

Demo ejecutiva de monitoreo cuantitativo. Usa exclusivamente datos sintéticos,
no ejecuta órdenes y no constituye asesoría financiera.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import generate_simulation_data
from src.data_quality import validate_synthetic_data
from src.risk_analysis import calculate_market_risk


st.set_page_config(
    page_title="Quantum & MLOps Governance Terminal",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get help": None,
        "Report a Bug": None,
        "About": "Demo con datos sintéticos. No ejecuta órdenes ni recomienda inversiones.",
    },
)


CSS = """
<style>
    :root {
        --bg: #07101f;
        --panel: #0d182b;
        --panel-2: #111f35;
        --line: rgba(148, 163, 184, .18);
        --text: #e8eef7;
        --muted: #8797ad;
        --cyan: #22d3ee;
        --blue: #5b8cff;
        --green: #35d399;
        --red: #ff5c70;
        --amber: #f8c15c;
    }

    .stApp {
        background:
          radial-gradient(circle at 78% -10%, rgba(38, 100, 190, .17), transparent 31rem),
          radial-gradient(circle at -10% 55%, rgba(20, 184, 166, .08), transparent 28rem),
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
        border: 1px solid rgba(34, 211, 238, .55);
        border-radius: .65rem;
        color: var(--cyan);
        background: rgba(34, 211, 238, .08);
        box-shadow: 0 0 25px rgba(34, 211, 238, .10);
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
        background: rgba(53, 211, 153, .09);
        border: 1px solid rgba(53, 211, 153, .28);
    }

    .critical-badge {
        color: var(--red);
        background: rgba(255, 92, 112, .09);
        border: 1px solid rgba(255, 92, 112, .30);
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
        background: linear-gradient(145deg, rgba(17, 31, 53, .88), rgba(10, 21, 38, .88));
        border: 1px solid var(--line) !important;
        border-radius: 14px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, .17);
    }

    div[data-testid="stMetric"] {
        background: rgba(7, 16, 31, .46);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: .85rem 1rem;
    }

    [data-testid="stMetricValue"] { font-size: 1.55rem; font-weight: 720; }
    [data-testid="stMetricDelta"] { font-size: .73rem; }

    .eyebrow {
        color: var(--cyan);
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
        background: rgba(7, 16, 31, .47);
        border: 1px solid var(--line);
        border-radius: 10px;
    }

    .check-name { color: #c8d4e4; font-size: .81rem; }
    .passed, .failed {
        min-width: 4.8rem;
        text-align: center;
        border-radius: 999px;
        font-size: .68rem;
        font-weight: 800;
        letter-spacing: .07em;
        padding: .25rem .5rem;
    }
    .passed { color: var(--green); background: rgba(53, 211, 153, .10); }
    .failed { color: var(--red); background: rgba(255, 92, 112, .12); }

    .alert-strip {
        display: flex;
        gap: .75rem;
        align-items: flex-start;
        padding: .8rem 1rem;
        margin: .2rem 0 1rem;
        border-radius: 11px;
        border: 1px solid rgba(255, 92, 112, .35);
        background: linear-gradient(90deg, rgba(116, 22, 39, .34), rgba(54, 20, 34, .18));
        color: #ffdbe0;
        font-size: .82rem;
    }

    .ok-strip {
        padding: .7rem .9rem;
        margin: .2rem 0 1rem;
        border: 1px solid rgba(53, 211, 153, .24);
        background: rgba(53, 211, 153, .06);
        border-radius: 11px;
        color: #bbf7db;
        font-size: .80rem;
    }

    div.stButton > button {
        min-height: 2.65rem;
        border-radius: 9px;
        border: 1px solid rgba(91, 140, 255, .35);
        background: rgba(91, 140, 255, .08);
        color: #dce7ff;
        font-weight: 680;
    }

    div.stButton > button:hover {
        border-color: var(--cyan);
        color: white;
        box-shadow: 0 0 20px rgba(34, 211, 238, .10);
    }

    div[data-testid="stSelectbox"] > div > div {
        background: rgba(7, 16, 31, .62);
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


def init_state() -> None:
    defaults = {
        "inject_black_swan": False,
        "refresh_cycle": 0,
        "last_refresh": datetime.now(timezone.utc),
        "pipeline": "Risk Core · Production Candidate",
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


@st.dialog("Metodología de riesgo")
def risk_methodology_dialog() -> None:
    st.markdown(
        """
        **VaR histórico 95%**  
        Percentil 5 de los retornos observados. Resume una pérdida diaria de cola bajo
        la distribución sintética simulada; no representa una pérdida máxima garantizada.

        **Máximo drawdown**  
        Mayor caída porcentual desde un máximo previo de la serie de precios.

        La demo usa 50 observaciones por minuto y una semilla reproducible. Ninguna
        métrica constituye recomendación de inversión.
        """
    )


@st.dialog("Trazabilidad del pipeline")
def pipeline_dialog() -> None:
    st.markdown(
        f"""
        **Configuración:** {st.session_state.pipeline}  
        **Ciclo de ejecución:** {st.session_state.refresh_cycle:04d}  
        **Datos:** sintéticos, semilla fija y reproducible  
        **Última sincronización UTC:** {st.session_state.last_refresh:%Y-%m-%d %H:%M:%S}

        La tabla inferior conserva el identificador de experimento, nodo, versión de
        código y semilla utilizados en cada ejecución simulada.
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


def price_figure(df: pd.DataFrame, is_critical: bool) -> go.Figure:
    line_color = "#ff5c70" if is_critical else "#22d3ee"
    gradient = (
        [[0.0, "rgba(255,92,112,0.02)"], [1.0, "rgba(255,92,112,0.46)"]]
        if is_critical
        else [[0.0, "rgba(34,211,238,0.02)"], [1.0, "rgba(34,211,238,0.42)"]]
    )
    trace_kwargs = dict(
        x=df["Timestamp"],
        y=df["Price"],
        mode="lines",
        name="Synthetic price",
        line=dict(color=line_color, width=2.2),
        fill="tozeroy",
        hovertemplate="%{x|%H:%M}<br>Índice %{y:.2f}<extra></extra>",
    )
    try:
        trace = go.Scatter(**trace_kwargs, fillgradient=dict(type="vertical", colorscale=gradient))
    except ValueError:
        trace = go.Scatter(**trace_kwargs, fillcolor="rgba(255,92,112,.20)" if is_critical else "rgba(34,211,238,.18)")

    fig = go.Figure(trace)
    if is_critical:
        event_time = df.loc[df["Return"].abs().idxmax(), "Timestamp"]
        fig.add_vline(
            x=event_time.timestamp() * 1000,
            line_color="#ff9cab",
            line_dash="dot",
            annotation_text="Drift detectado",
            annotation_font_color="#ffbdc6",
        )
    fig.update_layout(
        height=345,
        margin=dict(l=12, r=12, t=35, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(7,16,31,.35)",
        font=dict(color="#8797ad", family="Inter, system-ui, sans-serif", size=11),
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(title=None, gridcolor="rgba(148,163,184,.10)", showline=False),
        yaxis=dict(title="Índice sintético", gridcolor="rgba(148,163,184,.10)", zeroline=False),
    )
    return fig


def audit_log(cycle: int, critical: bool) -> pd.DataFrame:
    suffix = f"{cycle % 100:02d}"
    statuses = ["DRIFT" if critical else "VALIDATED", "VALIDATED", "SHADOW"]
    return pd.DataFrame(
        {
            "Experiment ID": [f"exp-QM-{suffix}A", f"exp-RK-{suffix}B", f"exp-DQ-{suffix}C"],
            "Nodo remoto": ["Frankfurt-Node-4", "Santiago-Node-1", "Frankfurt-DR-2"],
            "Pipeline": ["market-sim", "risk-core", "quality-gate"],
            "Versión": ["v2.4.1", "v1.9.7", "v3.1.0-rc"],
            "Semilla (Seed)": [483920, 102948, 573920],
            "Estado": statuses,
        }
    )


init_state()

critical = bool(st.session_state.inject_black_swan)
status_badge = (
    '<span class="critical-badge"><span class="pulse"></span>INCIDENTE ACTIVO</span>'
    if critical
    else '<span class="live-badge"><span class="pulse"></span>SYSTEM NOMINAL</span>'
)
st.markdown(
    f"""
    <div class="terminal-header">
      <div class="brand-lockup">
        <div class="brand-mark">◈</div>
        <div>
          <div class="brand-title">QUANTUM &amp; MLOPS GOVERNANCE TERMINAL</div>
          <div class="brand-subtitle">Decision intelligence · Model observability · Remote execution audit</div>
        </div>
      </div>
      {status_badge}
    </div>
    """,
    unsafe_allow_html=True,
)


control_a, control_b, control_c = st.columns([1.7, 1.2, 1.2], vertical_alignment="bottom")
with control_a:
    st.session_state.pipeline = st.selectbox(
        "Configuración del pipeline",
        [
            "Risk Core · Production Candidate",
            "Data Quality · Strict Gate",
            "Stress Lab · Scenario Replay",
        ],
        index=[
            "Risk Core · Production Candidate",
            "Data Quality · Strict Gate",
            "Stress Lab · Scenario Replay",
        ].index(st.session_state.pipeline),
    )
with control_b:
    st.button("↻  Refrescar nodos", on_click=refresh_nodes, width="stretch")
with control_c:
    if critical:
        st.button("Restablecer escenario", on_click=set_black_swan, args=(False,), width="stretch")
    else:
        st.button("⚠  Inyectar Cisne Negro", on_click=set_black_swan, args=(True,), type="primary", width="stretch")


df = generate_simulation_data(inject_error=critical)
quality_report = validate_synthetic_data(df)

# Una anomalía negativa severa también es drift. Esta salvaguarda hace compatible
# la interfaz con versiones antiguas del validador que solo inspeccionaban max().
if not df.empty and float(df["Return"].abs().max()) > 0.25:
    quality_report["volatility_within_bounds"] = False

var_95, max_drawdown = calculate_market_risk(df["Return"].to_numpy(), df["Price"].to_numpy())
failed_checks = sum(not value for value in quality_report.values())

if failed_checks:
    st.markdown(
        f"""
        <div class="alert-strip"><span>◆</span><div><b>Synthetic Data Drift confirmado.</b>
        {failed_checks} regla(s) de gobierno fallaron. El pipeline quedó marcado para revisión;
        no se ejecutan órdenes ni acciones externas en esta demo.</div></div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="ok-strip">● Todos los contratos de datos y límites de observabilidad están dentro de rango.</div>',
        unsafe_allow_html=True,
    )


left, right = st.columns([1.0, 1.55], gap="large")
with left:
    with st.container(border=True):
        st.markdown('<div class="eyebrow">Governance gate</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Calidad de datos sintéticos</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-copy">{len(df):,} observaciones · contrato de 5 reglas · '
            f'{"bloqueado" if failed_checks else "aprobado"}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(validation_cards(quality_report), unsafe_allow_html=True)

        pass_rate = (len(quality_report) - failed_checks) / max(len(quality_report), 1)
        st.progress(pass_rate, text=f"Cobertura validada: {pass_rate:.0%}")

with right:
    with st.container(border=True):
        top_text, top_action = st.columns([3.2, 1.0], vertical_alignment="center")
        with top_text:
            st.markdown('<div class="eyebrow">Market risk engine</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Riesgo dinámico del escenario</div>', unsafe_allow_html=True)
        with top_action:
            if st.button("ⓘ Metodología", width="stretch"):
                risk_methodology_dialog()

        risk_a, risk_b, risk_c = st.columns(3)
        risk_a.metric("VaR histórico · 95%", f"{var_95:.2%}", help="Percentil 5 de retornos sintéticos.")
        risk_b.metric("Máximo drawdown", f"{max_drawdown:.2%}", help="Mayor caída desde un máximo previo.")
        risk_c.metric(
            "Retorno extremo",
            f"{df['Return'].abs().max():.2%}",
            delta="DRIFT" if failed_checks else "NORMAL",
            delta_color="inverse" if failed_checks else "normal",
        )

        st.plotly_chart(price_figure(df, bool(failed_checks)), width="stretch", config={"displayModeBar": False})


st.markdown("<div style='height:.55rem'></div>", unsafe_allow_html=True)
with st.container(border=True):
    title_col, action_col = st.columns([4.5, 1.0], vertical_alignment="center")
    with title_col:
        st.markdown('<div class="eyebrow">Remote infrastructure</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Bitácora de auditoría de experimentos</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-copy">Última sincronización UTC: '
            f'{st.session_state.last_refresh:%Y-%m-%d %H:%M:%S} · ciclo {st.session_state.refresh_cycle:04d}</div>',
            unsafe_allow_html=True,
        )
    with action_col:
        if st.button("Ver trazabilidad", width="stretch"):
            pipeline_dialog()

    audit_df = audit_log(st.session_state.refresh_cycle, bool(failed_checks))
    st.dataframe(
        audit_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Semilla (Seed)": st.column_config.NumberColumn(format="%d"),
            "Estado": st.column_config.TextColumn(help="Estado simulado del experimento."),
        },
    )
    st.download_button(
        "Descargar evidencia CSV",
        data=audit_df.to_csv(index=False).encode("utf-8"),
        file_name=f"mlops_audit_cycle_{st.session_state.refresh_cycle:04d}.csv",
        mime="text/csv",
    )


st.markdown(
    '<div class="fineprint">DEMO · DATOS 100% SINTÉTICOS · NO EJECUTA ÓRDENES · NO CONSTITUYE ASESORÍA FINANCIERA</div>',
    unsafe_allow_html=True,
)
