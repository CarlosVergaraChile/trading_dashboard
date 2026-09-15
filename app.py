import streamlit as st
import pandas as pd
from src.data_loader import load_trades, load_algorithms, load_settings
from src.data_quality import DataQualityEngine
from src.risk_analysis import calculate_var, calculate_drawdown
from src.charts import plot_price_evolution

st.set_page_config(layout="wide", page_title="Quantum & MLOps Governance")
st.title("🎛️ Torre de Control Cuantitativa & Gobernanza MLOps")

st.sidebar.header("🖥️ Granjas de Servidores e Infraestructura")
try:
    algos = load_algorithms()
    for idx, row in algos.iterrows():
        st.sidebar.metric(label=f"{row['algorithm_id']} ({row['version']})", value=row['server_node'], delta=f"Semilla: {row['seed']}")
except Exception as e:
    st.sidebar.write("Modo local activo.")

try:
    settings = load_settings()
    df_trades = load_trades()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🛡️ Calidad de Datos Sintéticos (Great Expectations)")
        dq = DataQualityEngine(max_ret=0.50, min_ret=-0.50)
        dq_results = dq.validate_dataset(df_trades)
        for metric, passed in dq_results.items():
            if passed: st.success(f"✔ {metric.upper()}: PASSED")
            else: st.error(f"❌ {metric.upper()}: FAILED")
                
    with col2:
        st.subheader("📊 Análisis de Riesgo Avanzado")
        var_95 = calculate_var(df_trades['return'], confidence=0.95)
        max_dd = calculate_drawdown(df_trades['price'])
        st.metric(label="Value at Risk (VaR 95%)", value=f"{var_95:.4f}")
        st.metric(label="Max Drawdown Extremo", value=f"{max_dd:.4f}")
        
    st.subheader("📈 Visualización Temporal")
    st.plotly_chart(plot_price_evolution(df_trades), use_container_width=True)
except Exception as e:
    st.write("Carga los archivos de datos para iniciar la simulación.")
