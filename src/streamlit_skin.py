"""Presentation layer for the validation dashboard.

Only injects CSS and a compact header. The dashboard widgets, data, charts and
callbacks remain owned by app.py. HTML is intentionally kept as one compact
block so Streamlit does not display fragments as literal source code.
"""

from __future__ import annotations

import streamlit as st


DARK = r"""
:root{--ac-bg:#0a0e14;--ac-surface:#111720;--ac-surface2:#161d28;--ac-border:#1f2a3a;--ac-text:#e6edf3;--ac-muted:#8b98a8;--ac-accent:#22d3ee;--ac-green:#10b981;--ac-red:#ef4444;--ac-amber:#f59e0b;--ac-purple:#a78bfa;--ac-shadow:rgba(0,0,0,.3)}
"""

LIGHT = r"""
:root{--ac-bg:#f6f8fb;--ac-surface:#fff;--ac-surface2:#eef2f7;--ac-border:#e2e8f0;--ac-text:#0f172a;--ac-muted:#64748b;--ac-accent:#0891b2;--ac-green:#059669;--ac-red:#dc2626;--ac-amber:#d97706;--ac-purple:#7c3aed;--ac-shadow:rgba(15,23,42,.1)}
"""

CSS = r"""
html,body,.stApp,[data-testid="stAppViewContainer"]{background:var(--ac-bg)!important;color:var(--ac-text)!important;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important}
.stApp{background-image:radial-gradient(900px 420px at 0 0,color-mix(in srgb,var(--ac-accent) 14%,transparent),transparent 60%),radial-gradient(700px 500px at 100% 0,color-mix(in srgb,var(--ac-purple) 12%,transparent),transparent 55%);background-attachment:fixed}
[data-testid="stHeader"],[data-testid="stToolbar"],#MainMenu,footer{visibility:hidden;height:0}
[data-testid="stAppViewContainer"]>.main .block-container{max-width:1520px!important;padding:1.25rem 2.2rem 3rem!important}
*{box-sizing:border-box}
.term-header{display:flex;align-items:center;gap:18px;padding:4px 0 18px;margin-bottom:22px;border-bottom:1px solid var(--ac-border);position:relative}
.term-header:after{content:"";position:absolute;left:0;bottom:-1px;width:220px;height:1px;background:linear-gradient(90deg,var(--ac-accent),transparent)}
.brand{display:flex;align-items:center;gap:12px;flex:1}.brand-mark{width:40px;height:40px;display:grid;place-items:center;border-radius:10px;background:linear-gradient(135deg,var(--ac-accent),var(--ac-purple));color:#06121a;font-size:20px;font-weight:800;box-shadow:0 0 24px color-mix(in srgb,var(--ac-accent) 35%,transparent)}
.brand-title{font-size:15px;font-weight:800;letter-spacing:.06em;line-height:1.15;color:var(--ac-text)!important;white-space:nowrap}.brand-sub{font-size:11px;color:var(--ac-muted)!important;margin-top:3px}
.status-chip{display:inline-flex;align-items:center;gap:7px;padding:5px 12px;border-radius:999px;font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;white-space:nowrap}.status-ok{color:var(--ac-green);background:color-mix(in srgb,var(--ac-green) 12%,transparent);border:1px solid color-mix(in srgb,var(--ac-green) 30%,transparent)}.status-alert{color:var(--ac-red);background:color-mix(in srgb,var(--ac-red) 12%,transparent);border:1px solid color-mix(in srgb,var(--ac-red) 30%,transparent)}.status-dot{width:6px;height:6px;border-radius:50%;background:currentColor;box-shadow:0 0 8px currentColor}
.info-banner{padding:17px 21px;border-radius:14px;background:linear-gradient(135deg,color-mix(in srgb,var(--ac-accent) 12%,transparent),transparent 72%);border:1px solid color-mix(in srgb,var(--ac-accent) 18%,transparent);border-left:3px solid var(--ac-accent);margin-bottom:20px}.info-eyebrow,.section-eyebrow{font-size:10px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--ac-accent)!important;margin-bottom:7px}.info-body{font-size:13px;line-height:1.65;color:var(--ac-text)!important}.info-foot,.section-copy{font-size:11px;line-height:1.55;color:var(--ac-muted)!important;margin-top:8px}.section-title{font-size:15px;font-weight:750;color:var(--ac-text)!important;line-height:1.3}
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--ac-surface)!important;border:1px solid var(--ac-border)!important;border-radius:14px!important;box-shadow:0 6px 20px var(--ac-shadow)!important} [data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:color-mix(in srgb,var(--ac-accent) 35%,var(--ac-border))!important}
div[data-testid="stMetric"]{background:linear-gradient(150deg,var(--ac-surface2),var(--ac-surface))!important;border:1px solid var(--ac-border)!important;border-left:3px solid var(--ac-accent)!important;border-radius:10px!important;padding:14px 16px!important;box-shadow:0 5px 16px var(--ac-shadow)!important} [data-testid="stMetricLabel"]{color:var(--ac-muted)!important;font-size:10px!important;font-weight:800!important;text-transform:uppercase;letter-spacing:.1em}[data-testid="stMetricValue"]{color:var(--ac-text)!important;font-size:23px!important;font-weight:750!important}
div.stButton>button,div.stDownloadButton>button{min-height:39px;border-radius:7px;border:1px solid var(--ac-border);background:var(--ac-surface2);color:var(--ac-text);font-weight:650}div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:var(--ac-accent);color:var(--ac-accent);background:color-mix(in srgb,var(--ac-accent) 10%,var(--ac-surface2))}div.stButton>button[kind="primary"]{background:var(--ac-accent);border-color:var(--ac-accent);color:#06121a}
div[data-testid="stSelectbox"]>div>div,div[data-baseweb="select"]>div,div[data-testid="stTextInput"] input{background:var(--ac-surface2)!important;border-color:var(--ac-border)!important;color:var(--ac-text)!important;border-radius:7px!important}div[data-baseweb="select"] *{color:var(--ac-text)!important}
.check-row{display:flex;align-items:center;justify-content:space-between;padding:9px 12px;margin:5px 0;background:var(--ac-surface2);border:1px solid var(--ac-border);border-radius:6px;color:var(--ac-text)}.chip{min-width:68px;text-align:center;padding:3px 8px;border-radius:999px;font-size:9px;font-weight:800}.chip-pass{color:var(--ac-green);background:color-mix(in srgb,var(--ac-green) 12%,transparent);border:1px solid color-mix(in srgb,var(--ac-green) 30%,transparent)}.chip-fail{color:var(--ac-red);background:color-mix(in srgb,var(--ac-red) 12%,transparent);border:1px solid color-mix(in srgb,var(--ac-red) 30%,transparent)}
.banner{display:flex;gap:10px;padding:11px 14px;border-radius:8px;font-size:12px;margin-bottom:18px}.banner-ok{color:var(--ac-green);background:color-mix(in srgb,var(--ac-green) 10%,transparent);border:1px solid color-mix(in srgb,var(--ac-green) 25%,transparent)}.banner-alert{color:var(--ac-red);background:color-mix(in srgb,var(--ac-red) 10%,transparent);border:1px solid color-mix(in srgb,var(--ac-red) 30%,transparent)}.verdict{padding:11px 14px;border-radius:7px;background:var(--ac-surface2);border-left:3px solid var(--ac-accent);font-size:12px;color:var(--ac-text);line-height:1.55;margin-top:14px}
[data-testid="stSidebar"]{background:var(--ac-surface)!important;border-right:1px solid var(--ac-border)!important}[data-testid="stSidebar"]>div:first-child{padding:22px 18px!important}[data-testid="stSidebar"] h3{color:var(--ac-accent)!important;font-size:10px!important;text-transform:uppercase;letter-spacing:.14em;font-weight:800;margin:20px 0 10px!important}[data-testid="stSidebar"] *{color:var(--ac-text)}[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *{color:var(--ac-muted)!important;font-size:11px!important}
[data-testid="stDataFrame"]{border:1px solid var(--ac-border);border-radius:8px;overflow:hidden}div[data-testid="stProgress"]>div>div{background:var(--ac-surface2)!important}div[data-testid="stProgress"]>div>div>div{background:linear-gradient(90deg,var(--ac-accent),var(--ac-purple))!important}
.fineprint{color:var(--ac-muted)!important;font-size:10px;text-align:center;padding-top:28px;letter-spacing:.1em;font-weight:700;text-transform:uppercase}
@media(max-width:900px){[data-testid="stAppViewContainer"]>.main .block-container{padding:1rem}.brand-sub{display:none}.term-header{flex-wrap:wrap}}
"""


def apply_skin() -> None:
    """Inject presentation CSS and a safe, compact header only.

    Do not place the full dashboard HTML here: Streamlit's Markdown parser can
    expose large nested HTML blocks as literal text. The actual dashboard stays
    in app.py and remains fully functional.
    """
    theme = getattr(st.session_state, "theme", "dark")
    variables = LIGHT if theme == "light" else DARK
    st.markdown(f"<style>{variables}{CSS}</style>", unsafe_allow_html=True)
