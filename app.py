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
        --bg: #0a0e14;
        --bg2: #111720;
        --bg3: #1a2230;
        --bg-elev: #161d28;
        --border: #1f2a3a;
        --border-hi: #2a3545;
        --text: #e6edf3;
        --text2: #8b98a8;
        --text3: #5a6675;
        --accent: #22d3ee;
        --accent-dim: rgba(34, 211, 238, .15);
        --green: #10b981;
        --green-dim: rgba(16, 185, 129, .12);
        --red: #ef4444;
        --red-dim: rgba(239, 68, 68, .12);
        --amber: #f59e0b;
        --amber-dim: rgba(245, 158, 11, .12);
        --purple: #a78bfa;
        --purple-dim: rgba(167, 139, 250, .15);
    }

    .stApp {
        background: #0a0e14;
        background-image:
            radial-gradient(900px 400px at 0% 0%, rgba(34,211,238,.06), transparent 60%),
            radial-gradient(700px 500px at 100% 0%, rgba(167,139,250,.05), transparent 55%);
        background-attachment: fixed;
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
    [data-testid="stCaptionContainer"], .stCaption { color: var(--text2); }

    .terminal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin: .15rem 0 1rem;
        padding-bottom: .9rem;
        border-bottom: 1px solid var(--border);
    }

    .brand-lockup { display: flex; align-items: center; gap: .85rem; }
    .brand-mark {
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
    }

    .brand-title { font-size: 1.08rem; font-weight: 750; letter-spacing: .035em; color: var(--text); }
    .brand-subtitle { color: var(--text2); font-size: .78rem; margin-top: .1rem; }

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
        background: var(--green-dim);
        border: 1px solid rgba(16,185,129,.32);
        box-shadow: 0 0 12px rgba(16,185,129,.15);
    }

    .critical-badge {
        color: var(--red);
        background: var(--red-dim);
        border: 1px solid rgba(239,68,68,.34);
        box-shadow: 0 0 12px rgba(239,68,68,.2);
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
        background: linear-gradient(145deg, rgba(22,29,40,.95), rgba(17,23,32,.92));
        border: 1px solid var(--border) !important;
        border-radius: 14px;
        box-shadow: 0 14px 34px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.02);
        transition: border-color .18s, box-shadow .18s;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: var(--border-hi) !important;
        box-shadow: 0 18px 40px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.03);
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(26,34,48,.9), rgba(17,23,32,.85));
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        border-radius: 12px;
        padding: .85rem 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,.25);
        transition: transform .18s, box-shadow .18s;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,.35);
    }

    [data-testid="stMetricValue"] {
        font-size: 1.55rem;
        font-weight: 720;
        color: var(--text);
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.5px;
    }
    [data-testid="stMetricDelta"] { font-size: .73rem; }
    [data-testid="stMetricLabel"] { color: var(--text2); font-size: .72rem; text-transform: uppercase; letter-spacing: .06em; font-weight: 600; }

    .eyebrow {
        color: var(--accent);
        font-size: .70rem;
        font-weight: 750;
        letter-spacing: .11em;
        text-transform: uppercase;
        margin-bottom: .25rem;
    }

    .section-title { font-size: 1rem; font-weight: 720; margin-bottom: .1rem; color: var(--text); }
    .section-copy { color: var(--text2); font-size: .80rem; margin-bottom: .7rem; }

    .check-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: .75rem;
        padding: .72rem .78rem;
        margin: .48rem 0;
        background: rgba(26,34,48,.6);
        border: 1px solid var(--border);
        border-radius: 10px;
        transition: border-color .15s;
    }
    .check-card:hover { border-color: var(--border-hi); }

    .check-name { color: var(--text); font-size: .81rem; }
    .passed, .failed {
        min-width: 4.8rem;
        text-align: center;
        border-radius: 999px;
        font-size: .68rem;
        font-weight: 800;
        letter-spacing: .07em;
        padding: .25rem .5rem;
    }
    .passed {
        color: var(--green);
        background: var(--green-dim);
        border: 1px solid rgba(16,185,129,.25);
    }
    .failed {
        color: var(--red);
        background: var(--red-dim);
        border: 1px solid rgba(239,68,68,.3);
    }

    .alert-strip {
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
    }

    .ok-strip {
        padding: .7rem .9rem;
        margin: .2rem 0 1rem;
        border: 1px solid rgba(16,185,129,.28);
        background: rgba(16,185,129,.07);
        border-radius: 11px;
        color: #6ee7b7;
        font-size: .80rem;
    }

    div.stButton > button {
        min-height: 2.65rem;
        border-radius: 9px;
        border: 1px solid var(--border-hi);
        background: rgba(26,34,48,.7);
        color: var(--text);
        font-weight: 600;
        transition: all .18s;
    }

    div.stButton > button:hover {
        border-color: var(--accent);
        color: var(--accent);
        background: rgba(34,211,238,.08);
        box-shadow: 0 0 16px rgba(34,211,238,.2);
        transform: translateY(-1px);
    }

    div.stButton > button[kind="primary"] {
        background: var(--accent);
        border-color: var(--accent);
        color: #06121a;
        font-weight: 700;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #2fd8f0;
        color: #06121a;
        box-shadow: 0 4px 20px rgba(34,211,238,.4);
    }

    div[data-testid="stSelectbox"] > div > div {
        background: rgba(26,34,48,.7);
        border-color: var(--border-hi);
        color: var(--text);
    }

    div[data-testid="stTextInput"] input {
        background: rgba(26,34,48,.7);
        border-color: var(--border-hi);
        color: var(--text);
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
    }

    div[data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, var(--accent), var(--purple));
        box-shadow: 0 0 12px rgba(34,211,238,.35);
    }

    [data-testid="stSidebar"] {
        background: rgba(17,23,32,.95);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] h3 {
        color: var(--accent) !important;
        font-size: .78rem !important;
        text-transform: uppercase;
        letter-spacing: .1em;
        font-weight: 700;
    }

    .fineprint {
        color: var(--text3);
        font-size: .70rem;
        text-align: center;
        padding-top: 1.1rem;
        letter-spacing: .05em;
    }

    @media (max-width: 800px) {
        [data-testid="stAppViewContainer"] > .main .block-container { padding: .8rem; }
        .terminal-header { align-items: flex-start; }
        .brand-subtitle { display: none; }
    }
</style>
"""
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
