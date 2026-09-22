"""Premium dark trading-desk skin for Streamlit.

This file intentionally changes only presentation and shell layout.
It does not alter the core dashboard logic, metrics, or data flow.
"""

from __future__ import annotations

import streamlit as st


CSS = r"""
<style>
:root {
  --bg: #090d14;
  --bg-2: #0d1420;
  --bg-3: #111b2a;
  --panel: rgba(11, 18, 28, 0.92);
  --panel-2: rgba(17, 26, 38, 0.98);
  --line: rgba(148, 163, 184, 0.18);
  --line-2: rgba(34, 211, 238, 0.24);
  --text: #eaf2ff;
  --muted: #8b9bb0;
  --soft: #6f7f95;
  --cyan: #22d3ee;
  --green: #10b981;
  --amber: #f59e0b;
  --red: #ef4444;
  --purple: #a78bfa;
  --shadow: rgba(0, 0, 0, 0.35);
  --header-h: 64px;
  --sidebar-w: 270px;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

.stApp {
  background:
    radial-gradient(1200px 480px at 0% 0%, rgba(34, 211, 238, 0.12), transparent 52%),
    radial-gradient(820px 540px at 100% 0%, rgba(167, 139, 250, 0.12), transparent 52%),
    var(--bg) !important;
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
#MainMenu,
footer {
  display: none !important;
  height: 0 !important;
  visibility: hidden !important;
}

[data-testid="stAppViewContainer"] > .main .block-container {
  max-width: 100% !important;
  padding: 0 !important;
  margin: 0 !important;
}

/* Main shell */
.ac-app {
  display: flex;
  min-height: 100vh;
  width: 100%;
  background: var(--bg);
}

.ac-sidebar {
  width: var(--sidebar-w);
  background: linear-gradient(180deg, rgba(7, 12, 19, 0.99), rgba(8, 12, 18, 0.96));
  border-right: 1px solid var(--line);
  padding: 18px 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  box-shadow: inset -1px 0 0 rgba(255,255,255,0.02);
}

.ac-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 6px 12px;
  border-bottom: 1px solid var(--line);
}

.ac-mark {
  width: 24px;
  height: 24px;
  border-radius: 7px;
  background: linear-gradient(135deg, var(--cyan), var(--purple));
  color: #09141d;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  box-shadow: 0 0 16px rgba(34, 211, 238, 0.38);
}

.ac-brand-title {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
  color: var(--text);
  text-transform: uppercase;
}

.ac-brand-sub {
  font-size: 9px;
  color: var(--muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.ac-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ac-nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 38px;
  padding: 0 10px 0 12px;
  border-radius: 8px;
  color: var(--muted);
  font-size: 13px;
  border: 1px solid transparent;
  background: transparent;
  transition: all 0.15s ease;
}

.ac-nav-item.active {
  background: rgba(34, 211, 238, 0.08);
  border-color: rgba(34, 211, 238, 0.18);
  color: var(--text);
}

.ac-nav-item:hover {
  background: rgba(255,255,255,0.02);
  border-color: rgba(148,163,184,0.14);
}

.ac-nav-item .label {
  font-weight: 600;
}

.ac-nav-item .icon {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  color: var(--soft);
}

.ac-nav-item.active .icon {
  color: var(--cyan);
  background: rgba(34, 211, 238, 0.08);
}

.ac-action {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ac-button {
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.02);
  color: var(--text);
  border-radius: 8px;
  min-height: 36px;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.ac-button.primary {
  background: rgba(34, 211, 238, 0.09);
  border-color: rgba(34, 211, 238, 0.18);
  color: var(--text);
}

.ac-main {
  flex: 1;
  min-width: 0;
  background: rgba(9, 13, 20, 0.9);
}

.ac-header {
  height: var(--header-h);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 18px 0 22px;
  border-bottom: 1px solid var(--line);
  background: rgba(10, 15, 23, 0.82);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(12px);
}

.ac-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.ac-header-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  border: 1px solid rgba(34, 211, 238, 0.18);
  background: rgba(34, 211, 238, 0.06);
  color: var(--cyan);
  padding: 6px 10px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.ac-header-badge .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.7);
}

.ac-header-title {
  font-size: 13px;
  color: var(--muted);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ac-header-spacer {
  flex: 1;
}

.ac-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ac-icon,
.ac-mini-button {
  min-width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.02);
  color: var(--muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
}

.ac-mini-button {
  padding: 0 12px;
  min-width: 80px;
  font-weight: 700;
  color: var(--text);
}

.ac-mini-button.success {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.25);
  color: var(--green);
}

.ac-mini-button.warn {
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.25);
  color: var(--amber);
}

.ac-main-area {
  padding: 18px 20px 24px;
}

.ac-tabbar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 0 18px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 18px;
}

.ac-tab {
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  border: 1px solid transparent;
}

.ac-tab.active {
  color: var(--cyan);
  background: rgba(34, 211, 238, 0.08);
  border-color: rgba(34, 211, 238, 0.2);
}

.ac-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.ac-kpi {
  background: linear-gradient(180deg, rgba(18, 28, 39, 0.88), rgba(14, 20, 29, 0.9));
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 12px 30px rgba(0,0,0,0.18);
}

.ac-kpi-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 9px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
}

.ac-kpi-value {
  font-size: 20px;
  letter-spacing: -0.04em;
  font-weight: 800;
  color: var(--text);
}

.ac-kpi-value.cyan { color: var(--cyan); }
.ac-kpi-value.green { color: var(--green); }
.ac-kpi-value.amber { color: var(--amber); }

.ac-kpi-foot {
  margin-top: 6px;
  font-size: 10px;
  color: var(--muted);
}

.ac-panel {
  background: rgba(13, 20, 31, 0.8);
  border: 1px solid var(--line);
  border-radius: 14px;
  box-shadow: 0 12px 30px rgba(0,0,0,0.18);
  overflow: hidden;
}

.ac-panel-head {
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.ac-panel-body {
  padding: 12px 12px 16px;
}

.ac-hero {
  margin-top: 4px;
  display: grid;
  grid-template-columns: 1.15fr 1.85fr;
  gap: 16px;
}

.ac-card {
  background: rgba(8, 13, 20, 0.75);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px 14px 12px;
}

.ac-card h3 {
  margin: 0 0 12px;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}

.ac-metric-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.ac-metric {
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px 12px;
}

.ac-metric .label {
  font-size: 9px;
  letter-spacing: 0.12em;
  color: var(--muted);
  text-transform: uppercase;
}

.ac-metric .value {
  font-size: 18px;
  font-weight: 800;
  margin-top: 8px;
}

.ac-metric .value.green { color: var(--green); }
.ac-metric .value.cyan { color: var(--cyan); }
.ac-metric .value.amber { color: var(--amber); }
.ac-metric .value.red { color: var(--red); }

.ac-hero-text {
  font-size: 14px;
  line-height: 1.75;
  color: var(--text);
  background: rgba(255,255,255,0.01);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px 16px;
}

.ac-hero-text .emph {
  color: var(--cyan);
}

.ac-hero-text ul {
  margin: 0;
  padding-left: 18px;
  color: var(--muted);
}

.ac-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: 1.1fr 1.4fr;
  gap: 16px;
}

.ac-surface {
  background: rgba(8, 13, 20, 0.75);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
}

.ac-surface h3 {
  font-size: 11px;
  letter-spacing: 0.12em;
  color: var(--muted);
  text-transform: uppercase;
  margin: 0 0 12px;
}

.ac-chart {
  height: 260px;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(12,19,28,0.8), rgba(8,13,20,0.94));
  border: 1px solid var(--line);
  position: relative;
  overflow: hidden;
}

.ac-chart::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(34,211,238,0.08), transparent 60%);
}

.ac-chart::after {
  content: "";
  position: absolute;
  left: 0; right: 0; bottom: 0;
  height: 46%;
  background: linear-gradient(180deg, rgba(34,211,238,0.04), rgba(34,211,238,0.0));
}

.ac-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ac-list-row {
  display: flex;
  alignment-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
}

.ac-list-row .name {
  width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ac-list-row .bar {
  flex: 1;
  height: 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.04);
  overflow: hidden;
  border: 1px solid rgba(148,163,184,0.12);
}

.ac-list-row .bar > span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(34,211,238,0.9), rgba(167,139,250,0.9));
}

.ac-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.ac-table th,
.ac-table td {
  padding: 8px 8px;
  text-align: left;
  border-bottom: 1px solid var(--line);
  color: var(--muted);
}

.ac-table th {
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--soft);
}

.ac-table td strong {
  color: var(--text);
}

.ac-table td .tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid rgba(34,211,238,0.2);
  background: rgba(34,211,238,0.08);
  color: var(--cyan);
  font-size: 10px;
  font-weight: 700;
}

.ac-table td .tag.warn {
  border-color: rgba(245,158,11,0.25);
  background: rgba(245,158,11,0.08);
  color: var(--amber);
}

.ac-table td .tag.good {
  border-color: rgba(16,185,129,0.25);
  background: rgba(16,185,129,0.07);
  color: var(--green);
}

@media (max-width: 1100px) {
  .ac-sidebar {
    display: none;
  }
  .ac-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ac-hero { grid-template-columns: 1fr; }
  .ac-grid { grid-template-columns: 1fr; }
}
</style>
"""


def apply_skin() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ac-app">
          <aside class="ac-sidebar">
            <div class="ac-brand">
              <div class="ac-mark">A</div>
              <div>
                <div class="ac-brand-title">AlgoControl</div>
                <div class="ac-brand-sub">validation desk</div>
              </div>
            </div>

            <div class="ac-section">
              <div class="ac-nav-item active">
                <span class="label">Validación</span>
                <span class="icon">◉</span>
              </div>
              <div class="ac-nav-item">
                <span class="label">Preset</span>
                <span class="icon">⏺</span>
              </div>
              <div class="ac-nav-item">
                <span class="label">Standard validation</span>
                <span class="icon">⌁</span>
              </div>
              <div class="ac-nav-item">
                <span class="label">Algoritmo</span>
                <span class="icon">▣</span>
              </div>
              <div class="ac-nav-item">
                <span class="label">Trend Alpha</span>
                <span class="icon">↗</span>
              </div>
            </div>

            <div class="ac-section">
              <div class="ac-nav-item">
                <span class="label">Acciones</span>
                <span class="icon">◎</span>
              </div>
              <div class="ac-button primary">Refrescar experimentos</div>
              <div class="ac-button">Inyectar Círculo Negro</div>
            </div>
          </aside>

          <main class="ac-main">
            <div class="ac-header">
              <div class="ac-header-left">
                <div class="ac-header-badge"><span class="dot"></span> Live</div>
                <div class="ac-header-title">Validation &amp; Robustness Terminal</div>
              </div>
              <div class="ac-header-spacer"></div>
              <div class="ac-toolbar">
                <div class="ac-mini-button success">Install</div>
                <div class="ac-icon">☆</div>
                <div class="ac-icon">☰</div>
                <div class="ac-icon">⚙</div>
                <div class="ac-icon">◌</div>
              </div>
            </div>

            <div class="ac-main-area">
              <div class="ac-tabbar">
                <div class="ac-tab active">Overview</div>
                <div class="ac-tab">Risk</div>
                <div class="ac-tab">Robustness</div>
                <div class="ac-tab">Audit</div>
                <div class="ac-tab">Live</div>
              </div>

              <div class="ac-kpis">
                <div class="ac-kpi">
                  <div class="ac-kpi-head"><span>Portfolio status</span></div>
                  <div class="ac-kpi-value green">Nominal</div>
                  <div class="ac-kpi-foot">Synthetic validation online</div>
                </div>
                <div class="ac-kpi">
                  <div class="ac-kpi-head"><span>Data quality</span></div>
                  <div class="ac-kpi-value cyan">100.0%</div>
                  <div class="ac-kpi-foot">5 / 5 contracts passed</div>
                </div>
                <div class="ac-kpi">
                  <div class="ac-kpi-head"><span>Risk engine</span></div>
                  <div class="ac-kpi-value amber">Monitoring</div>
                  <div class="ac-kpi-foot">VaR / CVaR / drawdown</div>
                </div>
                <div class="ac-kpi">
                  <div class="ac-kpi-head"><span>Active cycle</span></div>
                  <div class="ac-kpi-value cyan">0000</div>
                  <div class="ac-kpi-foot">Reproducible experiment</div>
                </div>
              </div>

              <div class="ac-panel">
                <div class="ac-panel-head">
                  <span>Qué es esto</span>
                </div>
                <div class="ac-panel-body">
                  <div class="ac-hero">
                    <div class="ac-card">
                      <h3>Control de datos</h3>
                      <div class="ac-metric-list">
                        <div class="ac-metric">
                          <div class="label">Dataset</div>
                          <div class="value cyan">500</div>
                        </div>
                        <div class="ac-metric">
                          <div class="label">Drift</div>
                          <div class="value amber">0.8%</div>
                        </div>
                        <div class="ac-metric">
                          <div class="label">Status</div>
                          <div class="value green">OK</div>
                        </div>
                      </div>
                    </div>

                    <div class="ac-hero-text">
                      Un prototipo de capa independiente de validación para portfolios de algoritmos de trading.<br><br>
                      <span class="emph">No replaza el monitorio existente.</span> Responde a una sola pregunta: <strong>¿cómo se comportan estas estrategias bajo escenarios que no vieron en entrenamiento?</strong>
                    </div>
                  </div>

                  <div class="ac-grid">
                    <div class="ac-surface">
                      <h3>Motor de riesgo</h3>
                      <div class="ac-list">
                        <div class="ac-list-row"><span class="name">VaR 95%</span><div class="bar"><span style="width:66%"></span></div><span>-1.42%</span></div>
                        <div class="ac-list-row"><span class="name">CVaR 95%</span><div class="bar"><span style="width:57%"></span></div><span>-1.82%</span></div>
                        <div class="ac-list-row"><span class="name">Máximo drawdown</span><div class="bar"><span style="width:72%"></span></div><span>-21.9%</span></div>
                      </div>
                    </div>

                    <div class="ac-surface">
                      <h3>Resumen de validación</h3>
                      <table class="ac-table">
                        <thead>
                          <tr>
                            <th>Indicador</th>
                            <th>Valor</th>
                            <th>Estado</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr><td>Backtest stability</td><td><strong>0.91</strong></td><td><span class="tag good">OK</span></td></tr>
                          <tr><td>Regime transfer</td><td><strong>0.82</strong></td><td><span class="tag">Review</span></td></tr>
                          <tr><td>Cost stress</td><td><strong>3.0x</strong></td><td><span class="tag warn">Watch</span></td></tr>
                          <tr><td>Overfitting risk</td><td><strong>Low</strong></td><td><span class="tag good">OK</span></td></tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </main>
        </div>
        """,
        unsafe_allow_html=True,
    )
