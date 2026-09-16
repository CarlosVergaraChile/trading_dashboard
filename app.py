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

    [data-testid="stDataFrame"] { border: 1px solid var
