import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

# 1. Configuración de página estilo Terminal Institucional (Modo Oscuro Forzado)
st.set_page_config(
    page_title="Quantum & MLOps Governance Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inyección de CSS para imitar la interfaz ejecutiva de HealthEye Pro
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    div.stButton > button:first-child {
        background-color: #2563eb; color: white; font-weight: bold; border-radius: 8px; width: 100%; border: none; padding: 10px;
    }
    div.stButton > button:first-child:hover { background-color: #1d4ed8; color: white; }
    .status-box { padding: 12px; border-radius: 8px; margin-bottom: 10px; font-family: monospace; }
    .status-passed { background-color: #065f46; color: #34d399; border: 1px solid #047857; }
    .status-error { background-color: #991b1b; color: #f87171; border: 1px solid #b91c1c; }
    </style>
""", unsafe_allowed_html=True)

# 2. Inicializador de Estado de la Demo
if "nodos_activos" not in st.session_state:
    st.session_state.nodos_activos = True
if "error_simulado" not in st.session_state:
    st.session_state.error_simulado = False

# HEADER CORPORATIVO (Estilo HealthEye Pro)
st.title("📊 QUANTUM & MLOPS GOVERNANCE TERMINAL")
st.caption("DECISION INTELLIGENCE & INFRASTRUCTURE MONITOR · v2.0 · PILOT PROTOTYPE")
st.markdown("---")

# FILA DE BOTONES DE CONTROL DE OPERACIONES (Botonera interactiva)
col_b1, col_b2, col_b3, col_b4 = st.columns(4)

with col_b1:
    if st.button("↺ REFRESCAR NODOS"):
        with st.spinner("Sincronizando con granjas en Alemania..."):
            time.sleep(1)
        st.session_state.nodos_activos = True
        st.success("Nodos remotos sincronizados con éxito.")

with col_b2:
    if st.button("🚨 INYECTAR CISNE NEGRO (TEST ERROR)"):
        st.session_state.error_simulado = True

with col_b3:
    if st.button("🟢 RESTABLECER SISTEMA"):
        st.session_state.error_simulado = False

with col_b4:
    contexto = st.selectbox(
        "Configuración del Pipeline",
        ["Granja Servidores Frankfurt (HFT)", "Nodo Santiago - Modelos Predictivos", "Test Dataset Sintético CFA"]
    )

st.markdown("###")

# LÓGICA DE SIMULACIÓN DE DATOS
np.random.seed(42)
dates = pd.date_range(start="2026-09-15 09:00", periods=50, freq="min")
prices = np.cumsum(np.random.normal(0.5, 1.2, 50)) + 100

# Forzar una distorsión masiva si el usuario inyecta el error
if st.session_state.error_simulado:
    prices[30:] = prices[30:] * 0.4  

returns = np.diff(prices) / prices[:-1]
returns = np.insert(returns, 0, 0)

df_data = pd.DataFrame({"Timestamp": dates, "Price": prices, "Return": returns})

# EVALUACIÓN DE CALIDAD DE DATOS (Great Expectations)
is_row_count_ok = len(df_data) > 0
is_columns_ok = all(col in df_data.columns for col in ["Timestamp", "Price", "Return"])
is_price_positive = (df_data["Price"] > 0).all()
is_no_nulls = not df_data.isnull().values.any()
is_volatility_ok = float(df_data["Return"].max()) < 0.25 if not st.session_state.error_simulado else False

# 3. CUADRO DE MANDOS: METRICAS Y ALERTAS
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 🛡️ Gobernanza MLOps (Great Expectations)")
    
    if is_row_count_ok:
        st.markdown("<div class='status-box status-passed'>✔ ROW_COUNT_OK : PASSED</div>", unsafe_allowed_html=True)
    else:
        st.markdown("<div class='status-box status-error'>❌ ROW_COUNT_OK : FAILED</div>", unsafe_allowed_html=True)
        
    if is_columns_ok:
        st.markdown("<div class='status-box status-passed'>✔ COLUMNS_MATCH_SET : PASSED</div>", unsafe_allowed_html=True)
    else:
        st.markdown("<div class='status-box status-error'>❌ COLUMNS_MATCH_SET : FAILED</div>", unsafe_allowed_html=True)

    if is_price_positive:
        st.markdown("<div class='status-box status-passed'>✔ PRICE_GREATER_THAN_ZERO : PASSED</div>", unsafe_allowed_html=True)
    else:
        st.markdown("<div class='status-box status-error'>❌ CRITICAL: NEGATIVE PRICES DETECTED</div>", unsafe_allowed_html=True)

    if is_no_nulls:
        st.markdown("<div class='status-box status-passed'>✔ NO_NULL_VALUES : PASSED</div>", unsafe_allowed_html=True)
    else:
        st.markdown("<div class='status-box status-error'>❌ DATA_INTEGRITY_NULLS_FOUND</div>", unsafe_allowed_html=True)

    if is_volatility_ok:
        st.markdown("<div class='status-box status-passed'>✔ VOLATILITY_WITHIN_BOUNDS : PASSED</div>", unsafe_allowed_html=True)
    else:
        st.markdown("<div class='status-box status-error'>🚨 ALERT: SYNTHETIC DATA DRIFT DETECTED</div>", unsafe_allowed_html=True)

with col_right:
    st.markdown("### 📊 Análisis de Riesgo & Decision KPIs")
    
    var_95 = np.percentile(returns, 5)
    max_dd = (df_data["Price"] / df_data["Price"].cummax() - 1).min()
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Value at Risk (VaR 95%)", f"{var_95:.4f}", delta="Estable" if not st.session_state.error_simulado else "Riesgo Crítico", delta_color="inverse")
    with col_m2:
        st.metric("Max Drawdown Extremo", f"{max_dd:.2%}", delta="Bajo control" if not st.session_state.error_simulado else "Alerta de Liquidación", delta_color="inverse")
        
    if st.session_state.error_simulado:
        st.error("⚠️ CRITICAL ALERT: Los datos sintéticos generados rompen las restricciones de mercado histórico. El pipeline ha bloqueado la inyección automática en las granjas de servidores de producción.")
    else:
        st.info("ℹ️ INFO: Servidores operando con normalidad. Simulaciones distribuidas bajo arquitectura limpia.")

st.markdown("---")

# 4. GRÁFICOS CUANTITATIVOS INTERACTIVOS (Plotly con sombreado)
st.markdown("### 📈 Visualización Temporal e Historial de Escenarios")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_data["Timestamp"], 
    y=df_data["Price"], 
    mode='lines',
    name='Trayectoria de Precios',
    line=dict(color='#2563eb' if not st.session_state.error_simulado else '#dc2626', width=3),
    fill='tozeroy',
    fillcolor='rgba(37, 99, 235, 0.1)' if not st.session_state.error_simulado else 'rgba(220, 38, 38, 0.1)'
))

fig.update_layout(
    template="plotly_dark",
    margin=dict(l=20, r=20, t=20, b=20),
    height=400,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=True, gridcolor='#374151'),
    yaxis=dict(showgrid=True, gridcolor='#374151')
)

st.plotly_chart(fig, use_container_width=True)

# 5. REGISTRO DE INFRAESTRUCTURA REMOTA (Corregido con lista explícita)
st.markdown("### 🗂️ Registro de Experimentos e Infraestructura Remota")
grid_df = pd.DataFrame({
    "ID Experimento": ["EXP-2026-004", "EXP-2026-003", "EXP-2026-002"],
    "Nodo Servidor": ["Frankfurt-HFT-01", "Santiago-Core-02", "Frankfurt-HFT-02"],
    "Versión Código": ["v1.4-de (Optimizado C++)", "v1.2-cl (Python AI)", "v1.4-de (Optimizado C++)"],
    "Semilla (Seed)":,
    "Estado del Dataset": ["Aprobado" if not st.session_state.error_simulado else "BLOQUEADO", "Aprobado", "Aprobado"]
})
st.table(grid_df)
