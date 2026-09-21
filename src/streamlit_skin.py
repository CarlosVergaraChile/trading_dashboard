"""Reusable premium Streamlit trading-desk skin.

Presentation only: it adds a visual shell and CSS, without changing widgets,
callbacks, session state, data, or business logic.
"""

from __future__ import annotations

import streamlit as st


CSS = r"""
<style>
:root {
  --ac-bg:#070b12; --ac-panel:#0d141e; --ac-panel-2:#111b27;
  --ac-line:rgba(148,163,184,.16); --ac-cyan:#22d3ee;
  --ac-green:#10b981; --ac-red:#fb7185; --ac-amber:#f59e0b;
  --ac-purple:#a78bfa; --ac-text:#e6edf3; --ac-muted:#8292a7;
}
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background:var(--ac-bg)!important; color:var(--ac-text)!important;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;
}
.stApp { background:
  radial-gradient(900px 420px at -5% -8%,rgba(34,211,238,.16),transparent 58%),
  radial-gradient(820px 520px at 105% 0%,rgba(167,139,250,.13),transparent 54%),
  var(--ac-bg)!important; }
[data-testid="stHeader"],[data-testid="stToolbar"],#MainMenu,footer{visibility:hidden;height:0}
[data-testid="stAppViewContainer"]>.main .block-container{
  max-width:1660px!important; padding:1.2rem 2.2rem 3rem!important;
}

/* Real visual shell: this is intentionally structural, not just recoloring. */
.ac-shell{
  display:flex; align-items:center; gap:14px; min-height:68px;
  margin:-1.2rem -2.2rem 18px; padding:12px 2.2rem;
  background:linear-gradient(180deg,rgba(8,15,23,.98),rgba(8,15,23,.82));
  border-bottom:1px solid rgba(34,211,238,.32);
  box-shadow:0 12px 34px rgba(0,0,0,.28);
}
.ac-logo{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;
  background:linear-gradient(135deg,var(--ac-cyan),var(--ac-purple));color:#06121a;
  font-size:20px;font-weight:900;box-shadow:0 0 24px rgba(34,211,238,.4)}
.ac-brand{flex:1;min-width:0}.ac-title{font-size:14px;font-weight:800;letter-spacing:.14em;
  white-space:nowrap}.ac-sub{font-size:10px;color:var(--ac-muted);margin-top:3px}
.ac-nav{display:flex;gap:6px;align-items:center;white-space:nowrap;overflow:auto}
.ac-nav span{padding:7px 10px;border:1px solid transparent;border-radius:8px;color:var(--ac-muted);
  font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.ac-nav .active{color:var(--ac-cyan);background:rgba(34,211,238,.1);border-color:rgba(34,211,238,.25)}
.ac-status{padding:6px 10px;border-radius:999px;color:var(--ac-green);background:rgba(16,185,129,.1);
  border:1px solid rgba(16,185,129,.3);font-size:10px;font-weight:800;letter-spacing:.1em}
.ac-status i{display:inline-block;width:6px;height:6px;border-radius:50%;background:currentColor;margin-right:6px;box-shadow:0 0 8px currentColor}

/* Suppress the old duplicate header; the shell above replaces it. */
.term-header{display:none!important}
[data-testid="stVerticalBlockBorderWrapper"]{
  background:linear-gradient(145deg,rgba(17,27,39,.98),rgba(9,16,25,.94))!important;
  border:1px solid var(--ac-line)!important;border-radius:16px!important;
  box-shadow:0 12px 30px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.025)!important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:rgba(34,211,238,.35)!important;transform:translateY(-1px)}
.info-banner{border-radius:16px!important;background:linear-gradient(110deg,rgba(34,211,238,.13),rgba(167,139,250,.08) 65%,rgba(13,20,30,.8))!important;box-shadow:0 10px 34px rgba(0,0,0,.2)!important}
div[data-testid="stMetric"]{min-height:136px!important;padding:18px!important;border-left:3px solid var(--ac-cyan)!important;border-radius:14px!important;background:linear-gradient(145deg,rgba(17,27,39,.98),rgba(10,18,28,.92))!important;box-shadow:0 10px 26px rgba(0,0,0,.24)!important}
[data-testid="stMetricValue"]{font-size:28px!important;line-height:1.2!important}
[data-testid="stMetricLabel"]{letter-spacing:.14em!important}
div.stButton>button,div.stDownloadButton>button{border-radius:9px!important;min-height:38px!important;border:1px solid rgba(148,163,184,.24)!important;background:linear-gradient(180deg,rgba(27,42,58,.95),rgba(13,23,34,.95))!important}
div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:var(--ac-cyan)!important;box-shadow:0 0 0 3px rgba(34,211,238,.08)!important}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#09111b,#070c13)!important;border-right:1px solid rgba(34,211,238,.18)!important}
[data-testid="stSidebar"]>div:first-child{padding:24px 17px!important}
[data-testid="stDataFrame"]{border:1px solid var(--ac-line)!important;border-radius:10px!important}
[data-testid="stPlotlyChart"]{border-radius:12px;overflow:hidden;background:rgba(6,12,19,.32)}
@media(max-width:900px){[data-testid="stAppViewContainer"]>.main .block-container{padding:.8rem 1rem 2rem!important}.ac-shell{margin:-.8rem -1rem 16px;padding:10px 1rem;flex-wrap:wrap}.ac-nav{order:3;width:100%}.ac-title{font-size:12px}.ac-sub{display:none}}
</style>
"""


def skin_css() -> str:
    return CSS


def apply_skin() -> None:
    """Apply the skin and render its visible terminal shell."""
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ac-shell">
          <div class="ac-logo">◈</div>
          <div class="ac-brand">
            <div class="ac-title">ALGO CONTROL <span style="color:var(--ac-cyan)">/</span> VALIDATION DESK</div>
            <div class="ac-sub">Synthetic-data monitoring · independent robustness terminal</div>
          </div>
          <div class="ac-nav">
            <span class="active">Overview</span><span>Risk</span><span>Robustness</span><span>Audit</span>
          </div>
          <div class="ac-status"><i></i>LIVE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
