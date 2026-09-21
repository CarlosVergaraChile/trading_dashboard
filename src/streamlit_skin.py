"""Reusable premium skin for Streamlit dashboards.

Usage in any Streamlit app:

    from src.streamlit_skin import apply_skin
    apply_skin()

The current dashboard also installs this skin automatically through src.__init__.
The skin is presentation-only: it does not add widgets, alter state, or change
application behavior.
"""

from __future__ import annotations

import streamlit as st


CSS = r"""
<style>
/* AlgoControl / Streamlit Trading Desk skin */
:root {
  --ac-bg: #070b12;
  --ac-panel: #0d141e;
  --ac-panel-2: #111b27;
  --ac-line: rgba(148,163,184,.14);
  --ac-line-strong: rgba(34,211,238,.34);
  --ac-text: #e6edf3;
  --ac-muted: #8292a7;
  --ac-cyan: #22d3ee;
  --ac-green: #10b981;
  --ac-red: #fb7185;
  --ac-amber: #f59e0b;
  --ac-purple: #a78bfa;
}

/* Full trading-terminal canvas */
.stApp {
  background:
    radial-gradient(900px 420px at -5% -8%, rgba(34,211,238,.16), transparent 58%),
    radial-gradient(820px 520px at 105% 0%, rgba(167,139,250,.13), transparent 54%),
    var(--ac-bg) !important;
}
[data-testid="stAppViewContainer"] > .main .block-container {
  max-width: 1660px !important;
  padding: 1rem 2.2rem 3.5rem !important;
}

/* Header becomes a command-center masthead */
.term-header {
  min-height: 76px;
  margin: -1rem -2.2rem 18px !important;
  padding: 14px 2.2rem 13px !important;
  background: linear-gradient(180deg, rgba(8,15,23,.96), rgba(8,15,23,.72)) !important;
  border-bottom: 1px solid var(--ac-line-strong) !important;
  box-shadow: 0 10px 34px rgba(0,0,0,.22);
}
.brand-mark {
  width: 46px !important; height: 46px !important; border-radius: 14px !important;
  background: linear-gradient(135deg, var(--ac-cyan), var(--ac-purple)) !important;
  box-shadow: 0 0 28px rgba(34,211,238,.34) !important;
}
.brand-title { letter-spacing: .16em !important; font-size: 14px !important; }
.status-chip { box-shadow: inset 0 0 14px rgba(255,255,255,.035), 0 0 16px rgba(34,211,238,.06) !important; }

/* Convert Streamlit containers into distinct desk panels */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: linear-gradient(145deg, rgba(17,27,39,.96), rgba(9,16,25,.92)) !important;
  border: 1px solid var(--ac-line) !important;
  border-radius: 16px !important;
  box-shadow: 0 12px 30px rgba(0,0,0,.2), inset 0 1px 0 rgba(255,255,255,.025) !important;
  padding-top: 3px;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: var(--ac-line-strong) !important;
  transform: translateY(-1px);
}
.info-banner {
  border-radius: 16px !important;
  background: linear-gradient(110deg, rgba(34,211,238,.13), rgba(167,139,250,.08) 65%, rgba(13,20,30,.75)) !important;
  box-shadow: 0 10px 34px rgba(0,0,0,.2), inset 0 1px 0 rgba(255,255,255,.04) !important;
}

/* Metrics read like a portfolio strip */
div[data-testid="stMetric"] {
  min-height: 136px !important;
  padding: 18px 18px !important;
  border-left: 3px solid var(--ac-cyan) !important;
  border-radius: 14px !important;
  background: linear-gradient(145deg, rgba(17,27,39,.98), rgba(10,18,28,.9)) !important;
  box-shadow: 0 10px 26px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.025) !important;
}
[data-testid="stMetricLabel"] { letter-spacing: .16em !important; }
[data-testid="stMetricValue"] { font-size: 28px !important; line-height: 1.2 !important; }
[data-testid="stMetricDelta"] { margin-top: 8px !important; }

/* Streamlit controls get a compact terminal treatment */
div.stButton > button, div.stDownloadButton > button {
  border-radius: 9px !important;
  min-height: 38px !important;
  border: 1px solid rgba(148,163,184,.22) !important;
  background: linear-gradient(180deg, rgba(27,42,58,.92), rgba(13,23,34,.92)) !important;
  letter-spacing: .02em;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
  border-color: var(--ac-cyan) !important;
  box-shadow: 0 0 0 3px rgba(34,211,238,.08), 0 0 18px rgba(34,211,238,.13) !important;
}

/* Sidebar becomes the persistent control rail */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #09111b 0%, #070c13 100%) !important;
  border-right: 1px solid rgba(34,211,238,.16) !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 24px 17px !important; }
[data-testid="stSidebar"] h3 {
  padding-top: 12px; border-top: 1px solid var(--ac-line);
  letter-spacing: .18em !important;
}

/* Tables/charts sit inside quieter analytical surfaces */
[data-testid="stDataFrame"] {
  border: 1px solid var(--ac-line) !important;
  border-radius: 10px !important;
  background: rgba(7,13,20,.5) !important;
}
[data-testid="stPlotlyChart"] {
  border-radius: 12px;
  overflow: hidden;
  background: rgba(6,12,19,.28);
}

/* Mobile keeps the terminal readable */
@media (max-width: 900px) {
  [data-testid="stAppViewContainer"] > .main .block-container { padding: .8rem 1rem 2rem !important; }
  .term-header { margin-left: -1rem !important; margin-right: -1rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
  .brand-title { white-space: normal !important; font-size: 12px !important; }
  [data-testid="stMetricValue"] { font-size: 23px !important; }
}
</style>
"""


def skin_css() -> str:
    """Return the CSS payload so it can be composed with an app's own theme."""
    return CSS


def apply_skin() -> None:
    """Apply the skin explicitly in any Streamlit application."""
    st.markdown(CSS, unsafe_allow_html=True)
