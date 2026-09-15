"""
app.py
=======
Algorithmic Risk Monitor — MVP
Dashboard de monitoreo de rendimiento y riesgo para portafolios algorítmicos.

Aplicación de SOLO monitoreo y análisis. No envía órdenes, no se conecta a
brokers y no entrega recomendaciones de inversión. Todos los datos son ficticios.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, date

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import data_loader as dl
from src import metrics as mt
from src import risk_analysis as ra
from src import charts as ch
from src import data_quality as dq
from src import metrics_safe as ms
from src.report_generator import (
    generar_reporte_ejecutivo, generar_reporte_semanal, generar_reporte_mensual,
)

# --------------------------------------------------------------------------
# Configuración de página y carga de datos base
# --------------------------------------------------------------------------

st.set_page_config(page_title="Algorithmic Risk Monitor — MVP", layout="wide",
                    page_icon="📊")

try:
    SETTINGS = dl.load_settings()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

dl.ensure_demo_data(SETTINGS)

FMT_FECHA = SETTINGS["app"]["formato_fecha"]
DIAS_HABILES = SETTINGS["app"]["dias_habiles_anio"]
ALGO_NAMES = dl.get_algo_names(SETTINGS)
BENCH_NAME = dl.get_benchmark_name(SETTINGS)
LIMITES = SETTINGS["limites_riesgo"]

try:
    returns_full = dl.load_daily_returns()
    trades_full = dl.load_trades()
    algos_meta = dl.load_algorithms()
except FileNotFoundError as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

CAPITAL_POR_ALGO = {a["nombre"]: a["capital_asignado"] for a in SETTINGS["algoritmos"]}
DATA_META = dl.get_data_metadata()
METODOLOGIA = SETTINGS.get("metodologia", {})
DICCIONARIO_DATOS = SETTINGS.get("diccionario_datos", [])


def fmt_pct(x: float) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "s/d"
    return f"{x * 100:,.2f}%"


def fmt_usd(x: float) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "s/d"
    return f"US$ {x:,.2f}"


def fmt_fecha(d) -> str:
    if d is None:
        return "s/d"
    return pd.Timestamp(d).strftime(FMT_FECHA)


def _fmt_pct_or_nd(x) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "N/D"
    return fmt_pct(x)


def _fmt_usd(x) -> str:
    return fmt_usd(x)


def _generar_hallazgos_automaticos(returns_df: pd.DataFrame, algo_names: list) -> list:
    """Hallazgos descriptivos (NO recomendaciones) calculados a partir de los datos filtrados."""
    hallazgos = []
    if returns_df.empty or not algo_names:
        return ["No hay datos suficientes en el período seleccionado para generar hallazgos."]

    ret_acum = {a: mt.retorno_acumulado(returns_df[a]) for a in algo_names}
    vol = {a: mt.volatilidad(returns_df[a], True, DIAS_HABILES) for a in algo_names}
    mdd = {a: mt.maximo_drawdown(returns_df[a]) for a in algo_names}

    mejor_retorno = max(ret_acum, key=ret_acum.get)
    mayor_vol = max(vol, key=vol.get)
    menor_vol = min(vol, key=vol.get)
    menor_dd = max(mdd, key=mdd.get)  # mdd es negativo; "menor" caída = valor más cercano a 0

    hallazgos.append(
        f"**{mejor_retorno}** presenta el mayor retorno acumulado del período "
        f"({fmt_pct(ret_acum[mejor_retorno])})."
    )
    if mayor_vol == mejor_retorno:
        hallazgos.append(
            f"**{mejor_retorno}** también concentra la mayor volatilidad anualizada "
            f"({fmt_pct(vol[mayor_vol])}): mayor retorno acompañado de mayor riesgo."
        )
    else:
        hallazgos.append(
            f"**{mayor_vol}** presenta la mayor volatilidad anualizada del grupo ({fmt_pct(vol[mayor_vol])})."
        )
    hallazgos.append(
        f"**{menor_dd}** muestra el menor drawdown máximo del período ({fmt_pct(mdd[menor_dd])}) "
        f"y **{menor_vol}** la menor volatilidad ({fmt_pct(vol[menor_vol])})."
    )

    if len(algo_names) >= 2:
        corr = returns_df[algo_names].corr()
        corr_vals = corr.where(~np.eye(len(algo_names), dtype=bool)).abs()
        if corr_vals.notna().any().any():
            par = corr_vals.stack().idxmax()
            valor_corr = corr.loc[par[0], par[1]]
            hallazgos.append(
                f"**{par[0]}** y **{par[1]}** presentan la correlación más alta del grupo "
                f"({valor_corr:.2f}) en el período analizado."
            )

    conteo_ops = returns_df.shape[0]
    hallazgos.append(
        f"El período analizado cubre {conteo_ops} días hábiles de {fmt_fecha(returns_df['fecha'].min())} "
        f"a {fmt_fecha(returns_df['fecha'].max())}."
    )
    return hallazgos


def _generar_riesgos_principales(returns_df: pd.DataFrame, algo_names: list, limites: dict) -> list:
    """Riesgos principales a vigilar (descriptivo), basados en el estado de alerta de cada algoritmo."""
    riesgos = []
    if returns_df.empty:
        return ["No hay datos suficientes para evaluar riesgos en el período."]
    for a in algo_names:
        serie = returns_df[a]
        dd_actual_a = mt.drawdown_actual(serie)
        perdida_diaria_a = serie.iloc[-1] if len(serie) else 0.0
        detalle = ra.evaluar_estado_alerta_detallado(dd_actual_a, perdida_diaria_a, 0.0, limites)
        if detalle["estado"] != "VERDE":
            riesgos.append(f"**{a}** en estado {detalle['estado']}: {' '.join(detalle['motivos'])}")
    if not riesgos:
        riesgos.append("Ningún algoritmo supera los límites de alerta configurados en este período (todos VERDE).")
    return riesgos


def _ejemplo_alerta(returns_df: pd.DataFrame, trades_df: pd.DataFrame, algo_names: list, limites: dict):
    """Retorna el texto de un ejemplo de alerta real (el primer algoritmo no-VERDE), o None."""
    for a in algo_names:
        serie = returns_df[a]
        if serie.empty:
            continue
        dd_actual_a = mt.drawdown_actual(serie)
        perdida_diaria_a = serie.iloc[-1] if len(serie) else 0.0
        tr_a = trades_df[trades_df["algoritmo"] == a]
        exp_a = ra.exposicion_por_categoria(tr_a, "algoritmo") if not tr_a.empty else pd.DataFrame()
        conc_a = ra.concentracion_cartera(exp_a) if not exp_a.empty else 0.0
        detalle = ra.evaluar_estado_alerta_detallado(dd_actual_a, perdida_diaria_a, conc_a, limites)
        if detalle["estado"] != "VERDE":
            return f"{detalle['estado']} — {a}: " + " ".join(detalle["motivos"])
    return None


def _generar_reporte_ejecutivo_actual() -> str:
    """Genera el reporte ejecutivo de 1 página con los filtros/datos actualmente seleccionados."""
    curva_local = mt.curva_capital(portafolio_returns, capital_inicial)
    ret_acum_local = mt.retorno_acumulado(portafolio_returns)
    ret_bench_local = mt.retorno_acumulado(bench_returns)
    mdd_local = mt.maximo_drawdown(portafolio_returns)
    vol_local = mt.volatilidad(portafolio_returns, True, DIAS_HABILES)
    sharpe_local = ms.sharpe_seguro(portafolio_returns, dias_habiles=DIAS_HABILES)

    ret_por_algo = {a: mt.retorno_acumulado(returns_periodo[a]) for a in algo_sel}
    vol_por_algo = {a: mt.volatilidad(returns_periodo[a], True, DIAS_HABILES) for a in algo_sel}
    algo_mejor = max(ret_por_algo, key=ret_por_algo.get) if ret_por_algo else "s/d"
    algo_mayor_riesgo = max(vol_por_algo, key=vol_por_algo.get) if vol_por_algo else "s/d"

    alertas = []
    for a in algo_sel:
        serie_a = returns_periodo[a]
        dd_a = mt.drawdown_actual(serie_a)
        perdida_a = serie_a.iloc[-1] if len(serie_a) else 0.0
        detalle = ra.evaluar_estado_alerta_detallado(dd_a, perdida_a, 0.0, LIMITES)
        if detalle["estado"] != "VERDE":
            alertas.append({"Algoritmo": a, "Estado": detalle["estado"], "Motivo": " ".join(detalle["motivos"])})

    os.makedirs("reports", exist_ok=True)
    ruta = os.path.join("reports", f"reporte_ejecutivo_muestra_{fecha_fin.strftime('%Y%m%d')}.pdf")
    generar_reporte_ejecutivo(
        ruta_salida=ruta, periodo_inicio=fmt_fecha(fecha_inicio), periodo_fin=fmt_fecha(fecha_fin),
        capital_inicial=capital_inicial, capital_final=float(curva_local.iloc[-1]) if len(curva_local) else capital_inicial,
        retorno_pct=ret_acum_local, retorno_benchmark_pct=ret_bench_local, nombre_benchmark=BENCH_NAME,
        max_drawdown_pct=mdd_local, volatilidad_pct=vol_local,
        sharpe=sharpe_local.valor if sharpe_local.valido else None,
        algo_mejor=algo_mejor, algo_mayor_riesgo=algo_mayor_riesgo, alertas=alertas,
        dashboard_version=DATA_META.get("dashboard_version", "s/d"),
        version_datos=DATA_META.get("trades_version_datos", "s/d"),
        nombre_archivo_datos=DATA_META.get("trades_archivo", "s/d"),
    )
    return ruta


# --------------------------------------------------------------------------
# Barra lateral
# --------------------------------------------------------------------------

st.sidebar.title("⚙️ Parámetros")

fecha_min = returns_full["fecha"].min().date()
fecha_max = returns_full["fecha"].max().date()

fecha_inicio = st.sidebar.date_input("Fecha inicial", value=fecha_min,
                                      min_value=fecha_min, max_value=fecha_max)
fecha_fin = st.sidebar.date_input("Fecha final", value=fecha_max,
                                   min_value=fecha_min, max_value=fecha_max)

algo_sel = st.sidebar.multiselect("Algoritmo(s)", options=ALGO_NAMES, default=ALGO_NAMES)

mercados_disponibles = sorted(trades_full["mercado"].unique().tolist())
mercado_sel = st.sidebar.multiselect("Mercado(s)", options=mercados_disponibles,
                                      default=mercados_disponibles)

benchmark_sel = st.sidebar.selectbox("Benchmark", options=[BENCH_NAME], index=0)

capital_inicial = st.sidebar.number_input("Capital inicial (USD)",
                                           value=float(SETTINGS["app"]["capital_inicial"]),
                                           step=1000.0, min_value=1000.0)

actualizar = st.sidebar.button("🔄 Actualizar cálculos", width='stretch')
generar_pdf_btn = st.sidebar.button("📄 Generar reporte PDF", width='stretch')

st.sidebar.markdown("---")
demo_mode = st.sidebar.toggle("🎬 Demo Mode (presentación comercial)", value=True)
st.sidebar.caption(
    "Esta aplicación es únicamente de monitoreo y análisis. No envía órdenes, "
    "no se conecta a brokers y no entrega recomendaciones de inversión. "
    "Todos los datos son ficticios."
)

if fecha_inicio > fecha_fin:
    st.sidebar.error("La fecha inicial no puede ser posterior a la fecha final.")
    st.stop()

if not algo_sel:
    st.sidebar.warning("Selecciona al menos un algoritmo.")
    st.stop()

# --------------------------------------------------------------------------
# Filtrado de datos según selección
# --------------------------------------------------------------------------

mask_periodo = (returns_full["fecha"].dt.date >= fecha_inicio) & (returns_full["fecha"].dt.date <= fecha_fin)
returns_periodo = returns_full.loc[mask_periodo].reset_index(drop=True)

if returns_periodo.empty:
    st.warning("No hay datos disponibles para el período seleccionado.")
    st.stop()

# Retorno de portafolio: promedio ponderado por capital asignado entre los algoritmos seleccionados
capitales_sel = {a: CAPITAL_POR_ALGO[a] for a in algo_sel}
capital_total_sel = sum(capitales_sel.values())
pesos = {a: c / capital_total_sel for a, c in capitales_sel.items()} if capital_total_sel > 0 else {}

portafolio_returns = sum(returns_periodo[a] * pesos[a] for a in algo_sel)
portafolio_returns.name = "portafolio"

bench_returns = returns_periodo[BENCH_NAME]

trades_mask = (
    (trades_full["fecha"].dt.date >= fecha_inicio) &
    (trades_full["fecha"].dt.date <= fecha_fin) &
    (trades_full["algoritmo"].isin(algo_sel)) &
    (trades_full["mercado"].isin(mercado_sel))
)
trades_periodo = trades_full.loc[trades_mask].reset_index(drop=True)

# Reporte de calidad de datos del período seleccionado (se usa en varias pestañas)
REPORTE_CALIDAD = dq.evaluar_calidad(trades_periodo, returns_periodo, fecha_inicio, fecha_fin)

# --------------------------------------------------------------------------
# Pantalla de bienvenida / Demo Mode (portada antes de entrar al dashboard)
# --------------------------------------------------------------------------

if "entrado_dashboard" not in st.session_state:
    st.session_state["entrado_dashboard"] = False

if not st.session_state["entrado_dashboard"]:
    st.title(SETTINGS["app"]["titulo"])
    st.caption(SETTINGS["app"]["subtitulo"])

    st.markdown(
        "**¿Qué hace este sistema?** Consolida el rendimiento y riesgo de varios algoritmos "
        "de trading en un solo lugar: compara desempeño, mide drawdowns y exposición, analiza "
        "correlaciones, detecta problemas de calidad de datos y genera reportes ejecutivos "
        "periódicos. Es una herramienta de **monitoreo, control y reporte de riesgo**, no una "
        "plataforma de inversión automatizada ni un generador de recomendaciones."
    )

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Período de datos", f"{fmt_fecha(fecha_min)} – {fmt_fecha(fecha_max)}")
    b2.metric("Algoritmos monitoreados", f"{len(ALGO_NAMES)}")
    b3.metric("Estado de calidad de datos", REPORTE_CALIDAD.estado_general)
    ult_carga = DATA_META.get("trades_ultima_modificacion")
    b4.metric("Última actualización", fmt_fecha(ult_carga) if ult_carga is not None else "s/d")

    ret_acum_preview = mt.retorno_acumulado(portafolio_returns)
    mdd_preview = mt.maximo_drawdown(portafolio_returns)
    sharpe_preview = ms.sharpe_seguro(portafolio_returns, dias_habiles=DIAS_HABILES)

    k1, k2, k3 = st.columns(3)
    k1.metric("Rentabilidad acumulada (todo el período filtrado)", fmt_pct(ret_acum_preview))
    k2.metric("Máximo drawdown", fmt_pct(mdd_preview))
    k3.metric("Sharpe", sharpe_preview.texto())

    if demo_mode:
        st.markdown("---")
        st.subheader("🎬 Demo Mode — Caso de uso")
        st.markdown(
            "Esta demo usa **datos ficticios** de cinco algoritmos con perfiles de riesgo "
            "distintos, para mostrar cómo el sistema ayudaría a un gestor a supervisar su "
            "portafolio de algoritmos día a día."
        )

        st.markdown("**Tres hallazgos automáticos (descriptivos, no recomendaciones):**")
        hallazgos = _generar_hallazgos_automaticos(returns_periodo, ALGO_NAMES)
        for h in hallazgos[:3]:
            st.markdown(f"- {h}")

        st.markdown("**Principales riesgos a vigilar en este período:**")
        riesgos_demo = _generar_riesgos_principales(returns_periodo, ALGO_NAMES, LIMITES)
        for r in riesgos_demo:
            st.markdown(f"- {r}")

        st.markdown("**Ejemplo de alerta:**")
        ejemplo_alerta = _ejemplo_alerta(returns_periodo, trades_periodo, ALGO_NAMES, LIMITES)
        if ejemplo_alerta:
            st.warning(ejemplo_alerta)
        else:
            st.success("En este período no hay algoritmos en estado AMARILLO/ROJO (todos VERDE).")

        if st.button("📄 Generar reporte de muestra (ejecutivo, 1 página)"):
            ruta_muestra = _generar_reporte_ejecutivo_actual()
            with open(ruta_muestra, "rb") as f:
                st.download_button("⬇️ Descargar reporte de muestra", data=f.read(),
                                    file_name=os.path.basename(ruta_muestra), mime="application/pdf",
                                    key="descarga_muestra_landing")

    st.markdown("---")
    if st.button("➡️ Entrar al dashboard completo", type="primary", use_container_width=True):
        st.session_state["entrado_dashboard"] = True
        st.rerun()

    st.caption(SETTINGS["app"].get("pie_pagina", ""))
    st.stop()

# --------------------------------------------------------------------------
# Encabezado del dashboard completo
# --------------------------------------------------------------------------

st.title(SETTINGS["app"]["titulo"])
st.caption(SETTINGS["app"]["subtitulo"])
st.info(
    "⚠️ Aplicación de monitoreo con datos ficticios. No constituye asesoría financiera "
    "ni recomendación de inversión. Los resultados históricos no garantizan resultados futuros.",
    icon="⚠️",
)

if demo_mode:
    st.caption("🎬 Demo Mode activo — textos explicativos ampliados para audiencia no técnica.")

(tab_resumen, tab_rendimiento, tab_riesgo, tab_algoritmos, tab_operaciones,
 tab_calidad, tab_metodologia, tab_reportes) = st.tabs(
    ["📌 Resumen ejecutivo", "📈 Rendimiento", "🛡️ Riesgo", "🧩 Algoritmos", "📋 Operaciones",
     "🧪 Calidad de Datos", "📚 Metodología y Diccionario", "🧾 Reportes"]
)

# ==========================================================================
# PÁGINA 1: RESUMEN EJECUTIVO
# ==========================================================================
with tab_resumen:
    curva = mt.curva_capital(portafolio_returns, capital_inicial)
    curva_bench = mt.curva_capital(bench_returns, capital_inicial)

    ret_acum = mt.retorno_acumulado(portafolio_returns)
    ret_anual = mt.retorno_anualizado(portafolio_returns, DIAS_HABILES)
    mdd = mt.maximo_drawdown(portafolio_returns)
    dd_actual = mt.drawdown_actual(portafolio_returns)
    vol_anual = mt.volatilidad(portafolio_returns, True, DIAS_HABILES)
    sharpe_res = ms.sharpe_seguro(portafolio_returns, dias_habiles=DIAS_HABILES)
    sortino_res = ms.sortino_seguro(portafolio_returns, dias_habiles=DIAS_HABILES)
    sharpe = sharpe_res.valor if sharpe_res.valido else float("nan")
    sortino = sortino_res.valor if sortino_res.valido else float("nan")
    costos = ra.costos_totales(trades_periodo)
    resultado_periodo = curva.iloc[-1] - capital_inicial if len(curva) else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capital actual", fmt_usd(curva.iloc[-1] if len(curva) else capital_inicial))
    c2.metric("Rentabilidad acumulada", fmt_pct(ret_acum))
    c3.metric("Rentabilidad anualizada", fmt_pct(ret_anual))
    c4.metric("Resultado del período", fmt_usd(resultado_periodo))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Máximo drawdown", fmt_pct(mdd))
    c6.metric("Drawdown actual", fmt_pct(dd_actual))
    c7.metric("Volatilidad anualizada", fmt_pct(vol_anual))
    c8.metric("Sharpe ratio", sharpe_res.texto(), help=sharpe_res.motivo or None)

    c9, c10, c11, c12 = st.columns(4)
    c9.metric("Sortino ratio", sortino_res.texto(), help=sortino_res.motivo or None)
    c10.metric("Algoritmos activos", f"{len(algo_sel)}")
    c11.metric("Número de operaciones", f"{len(trades_periodo):,}")
    c12.metric("Costos acumulados", fmt_usd(costos["comisiones"] + costos["slippage"]))

    st.plotly_chart(ch.grafico_curva_capital(returns_periodo["fecha"], curva, curva_bench, BENCH_NAME),
                     width='stretch', key="curva_resumen")

    col_a, col_b = st.columns(2)
    with col_a:
        mensual = mt.retornos_mensuales(portafolio_returns, returns_periodo["fecha"])
        st.plotly_chart(ch.grafico_retornos_mensuales(mensual), width='stretch', key="mensual_resumen")

    with col_b:
        st.subheader("Estado de algoritmos")
        filas_estado = []
        for a in algo_sel:
            serie = returns_periodo[a]
            dd_a = mt.drawdown_actual(serie)
            perdida_diaria = serie.iloc[-1] if len(serie) else 0.0
            exp_df = ra.exposicion_por_categoria(trades_periodo[trades_periodo["algoritmo"] == a], "algoritmo")
            conc = ra.concentracion_cartera(exp_df) if not exp_df.empty else 0.0
            estado = ra.evaluar_estado_alerta(dd_a, perdida_diaria, conc, LIMITES)
            filas_estado.append({"Algoritmo": a, "Drawdown actual": fmt_pct(dd_a),
                                  "Estado": estado})
        df_estado = pd.DataFrame(filas_estado)

        def _color_estado(val):
            colores = {"VERDE": "background-color:#D5F5E3", "AMARILLO": "background-color:#FDEBD0",
                       "ROJO": "background-color:#FADBD8"}
            return colores.get(val, "")

        try:
            styled = df_estado.style.map(_color_estado, subset=["Estado"])
        except AttributeError:
            styled = df_estado.style.applymap(_color_estado, subset=["Estado"])
        st.dataframe(styled, width='stretch', hide_index=True)

# ==========================================================================
# PÁGINA 2: RENDIMIENTO
# ==========================================================================
with tab_rendimiento:
    st.subheader("Curva de capital acumulada")
    st.plotly_chart(ch.grafico_curva_capital(returns_periodo["fecha"], curva, curva_bench, BENCH_NAME),
                     width='stretch', key="curva_rendimiento")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Retornos diarios")
        st.plotly_chart(ch.grafico_distribucion_retornos(portafolio_returns), width='stretch', key="dist_rendimiento")
    with col2:
        st.subheader("Retornos mensuales")
        st.plotly_chart(ch.grafico_retornos_mensuales(mensual), width='stretch', key="mensual_rendimiento")

    anual_df = mt.retornos_anuales(portafolio_returns, returns_periodo["fecha"])
    st.subheader("Retornos anuales")
    st.dataframe(anual_df.assign(retorno_anual=lambda d: d["retorno_anual"].map(fmt_pct)),
                 width='stretch')

    st.subheader("Rentabilidad y contribución por algoritmo")
    atrib = ra.atribucion_rendimiento(returns_periodo, algo_sel, capitales_sel)
    st.plotly_chart(ch.grafico_contribucion_algoritmos(atrib), width='stretch', key="contribucion_algos")
    st.dataframe(
        atrib.assign(
            retorno_acumulado=lambda d: d["retorno_acumulado"].map(fmt_pct),
            resultado_usd=lambda d: d["resultado_usd"].map(fmt_usd),
            peso_capital=lambda d: d["peso_capital"].map(fmt_pct),
            contribucion_pct=lambda d: d["contribucion_pct"].map(fmt_pct),
        ),
        width='stretch', hide_index=True,
    )

    st.subheader("Comparación con benchmark")
    ret_acum_port_serie = (1 + portafolio_returns).cumprod() - 1
    ret_acum_bench_serie = (1 + bench_returns).cumprod() - 1
    st.plotly_chart(
        ch.grafico_comparacion_benchmark(returns_periodo["fecha"], ret_acum_port_serie,
                                          ret_acum_bench_serie, BENCH_NAME),
        width='stretch', key="comparacion_benchmark")

    col3, col4 = st.columns(2)
    mejores, peores = mt.mejores_peores_periodos(portafolio_returns, returns_periodo["fecha"], n=5)
    with col3:
        st.markdown("**Mejores días**")
        st.dataframe(mejores.assign(retorno=lambda d: d["retorno"].map(fmt_pct),
                                     fecha=lambda d: d["fecha"].dt.strftime(FMT_FECHA)),
                     width='stretch', hide_index=True)
    with col4:
        st.markdown("**Peores días**")
        st.dataframe(peores.assign(retorno=lambda d: d["retorno"].map(fmt_pct),
                                    fecha=lambda d: d["fecha"].dt.strftime(FMT_FECHA)),
                     width='stretch', hide_index=True)

    st.subheader("Tabla de rendimiento mensual")
    st.dataframe(mensual.assign(retorno_mensual=lambda d: d["retorno_mensual"].map(fmt_pct)),
                 width='stretch')

    st.markdown("---")
    st.subheader("Atribución de resultados")
    st.caption(
        "Atribución **aproximada** basada en el log de operaciones (bruto, costos y neto). "
        "No es una reconstrucción contable completa de posiciones abiertas/cerradas — ver "
        "'Metodología y Diccionario' para el detalle del supuesto."
    )

    atrib_instr = ra.atribucion_por_categoria(trades_periodo, "instrumento")
    atrib_mercado = ra.atribucion_por_categoria(trades_periodo, "mercado")
    atrib_periodo_df = ra.atribucion_por_periodo(trades_periodo, "ME")

    col_at1, col_at2 = st.columns(2)
    with col_at1:
        st.markdown("**Por instrumento**")
        if not atrib_instr.empty:
            st.dataframe(atrib_instr.assign(
                resultado_bruto=lambda d: d["resultado_bruto"].map(fmt_usd),
                comisiones=lambda d: d["comisiones"].map(fmt_usd),
                slippage=lambda d: d["slippage"].map(fmt_usd),
                resultado_neto=lambda d: d["resultado_neto"].map(fmt_usd),
            ), width='stretch', hide_index=True)
        else:
            st.info("Sin operaciones en el período.")
    with col_at2:
        st.markdown("**Por mercado**")
        if not atrib_mercado.empty:
            st.dataframe(atrib_mercado.assign(
                resultado_bruto=lambda d: d["resultado_bruto"].map(fmt_usd),
                comisiones=lambda d: d["comisiones"].map(fmt_usd),
                slippage=lambda d: d["slippage"].map(fmt_usd),
                resultado_neto=lambda d: d["resultado_neto"].map(fmt_usd),
            ), width='stretch', hide_index=True)
        else:
            st.info("Sin operaciones en el período.")

    st.markdown("**Por período (mensual)**")
    if not atrib_periodo_df.empty:
        st.dataframe(atrib_periodo_df.assign(resultado_neto=lambda d: d["resultado_neto"].map(fmt_usd)),
                     width='stretch', hide_index=True)

# ==========================================================================
# PÁGINA 3: RIESGO
# ==========================================================================
with tab_riesgo:
    var95_res = ms.var_seguro(portafolio_returns, 0.95)
    cvar95_res = ms.cvar_seguro(portafolio_returns, 0.95)
    calmar_res = ms.calmar_seguro(portafolio_returns, DIAS_HABILES)
    dur_max, dur_actual_dd = mt.duracion_drawdown(portafolio_returns)
    peor_dia = ra.peor_periodo(portafolio_returns, returns_periodo["fecha"], "D")
    peor_semana = ra.peor_periodo(portafolio_returns, returns_periodo["fecha"], "W")
    peor_mes = ra.peor_periodo(portafolio_returns, returns_periodo["fecha"], "ME")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Volatilidad anualizada", fmt_pct(vol_anual))
    r2.metric("Máximo drawdown", fmt_pct(mdd))
    r3.metric("Drawdown actual", fmt_pct(dd_actual))
    r4.metric("Duración máx. drawdown", f"{dur_max} días")

    r5, r6, r7, r8 = st.columns(4)
    r5.metric("Duración drawdown actual", f"{dur_actual_dd} días")
    r6.metric("Sharpe", sharpe_res.texto(), help=sharpe_res.motivo or None)
    r7.metric("Sortino", sortino_res.texto(), help=sortino_res.motivo or None)
    r8.metric("Calmar ratio", calmar_res.texto(), help=calmar_res.motivo or None)

    r9, r10, r11, r12 = st.columns(4)
    r9.metric("VaR histórico 95%", var95_res.texto("{:.2%}"), help=var95_res.motivo or None)
    r10.metric("CVaR histórico 95%", cvar95_res.texto("{:.2%}"), help=cvar95_res.motivo or None)
    r11.metric("Peor día", fmt_pct(peor_dia["valor"]))
    r12.metric("Peor semana", fmt_pct(peor_semana["valor"]))

    r13, _, _, _ = st.columns(4)
    r13.metric("Peor mes", fmt_pct(peor_mes["valor"]))

    with st.expander("ℹ️ ¿Qué significan estas métricas?"):
        st.markdown("""
- **Drawdown**: caída porcentual desde el máximo histórico de capital hasta un punto dado. Mide la peor pérdida "de punta a punta" que habría experimentado un inversionista.
- **Sharpe ratio**: retorno en exceso sobre la tasa libre de riesgo por unidad de volatilidad. **No es garantía** de resultados futuros: asume retornos aproximadamente normales y no captura riesgo de cola ni asimetría.
- **VaR (Value at Risk)**: pérdida máxima esperada con un nivel de confianza dado (ej. 95%), estimada de forma histórica. Es una estimación estadística, no un límite absoluto.
- **CVaR (Expected Shortfall)**: promedio de las pérdidas que exceden el VaR. **Limitación**: con historiales cortos, la cola de la distribución está pobremente representada.
- **Volatilidad**: desviación estándar de los retornos diarios, anualizada multiplicando por la raíz cuadrada de los días hábiles al año.
- **Correlación**: puede cambiar en el tiempo, especialmente en períodos de estrés de mercado, cuando activos normalmente descorrelacionados tienden a moverse juntos.
- **Resultados históricos**: el desempeño pasado (incluyendo backtesting) **no garantiza resultados futuros**.
        """)

    col1, col2 = st.columns(2)
    with col1:
        dd_serie = mt.drawdown_series(portafolio_returns)
        st.plotly_chart(ch.grafico_drawdown(returns_periodo["fecha"], dd_serie), width='stretch', key="drawdown_riesgo")
    with col2:
        st.plotly_chart(ch.grafico_volatilidad_movil(returns_periodo["fecha"], portafolio_returns, 30, DIAS_HABILES),
                         width='stretch', key="vol_movil_riesgo")

    col3, col4 = st.columns(2)
    with col3:
        corr_df = ra.matriz_correlacion(returns_periodo, algo_sel)
        st.plotly_chart(ch.grafico_matriz_correlacion(corr_df), width='stretch', key="matriz_correlacion")
    with col4:
        st.plotly_chart(ch.grafico_distribucion_retornos(portafolio_returns, var95_res.valor), width='stretch', key="dist_riesgo_var")

    st.subheader("Exposición")
    exp_algo = ra.exposicion_por_categoria(trades_periodo, "algoritmo")
    exp_instrumento = ra.exposicion_por_categoria(trades_periodo, "instrumento")
    exp_mercado = ra.exposicion_por_categoria(trades_periodo, "mercado")

    col5, col6, col7 = st.columns(3)
    with col5:
        st.plotly_chart(ch.grafico_exposicion(exp_algo, "algoritmo"), width='stretch', key="exp_algoritmo")
    with col6:
        st.plotly_chart(ch.grafico_exposicion(exp_instrumento, "instrumento"), width='stretch', key="exp_instrumento")
    with col7:
        st.plotly_chart(ch.grafico_exposicion(exp_mercado, "mercado"), width='stretch', key="exp_mercado")

    conc = ra.concentracion_cartera(exp_algo)
    dias_periodo_n = max(1, (fecha_fin - fecha_inicio).days)
    rotacion = ra.rotacion_estimada(trades_periodo, capital_total_sel, dias_periodo_n)

    r14, r15, r16 = st.columns(3)
    r14.metric("Concentración de cartera", fmt_pct(conc))
    r15.metric("Rotación estimada (anualizada)", f"{rotacion:,.2f}x")
    r16.metric("Comisiones + slippage", fmt_usd(costos["comisiones"] + costos["slippage"]))

    st.plotly_chart(ch.grafico_pnl_mensual(mensual, capital_inicial), width='stretch', key="pnl_mensual_riesgo")

# ==========================================================================
# PÁGINA 4: ALGORITMOS
# ==========================================================================
with tab_algoritmos:
    for a in algo_sel:
        meta = algos_meta[algos_meta["algoritmo"] == a].iloc[0]
        serie_a = returns_periodo[a]
        trades_a = trades_periodo[trades_periodo["algoritmo"] == a]

        ret_acum_a = mt.retorno_acumulado(serie_a)
        ret_anual_a = mt.retorno_anualizado(serie_a, DIAS_HABILES)
        vol_a = mt.volatilidad(serie_a, True, DIAS_HABILES)
        mdd_a = mt.maximo_drawdown(serie_a)
        dd_actual_a = mt.drawdown_actual(serie_a)
        sharpe_res_a = ms.sharpe_seguro(serie_a, dias_habiles=DIAS_HABILES)
        sortino_res_a = ms.sortino_seguro(serie_a, dias_habiles=DIAS_HABILES)
        resultados_a = trades_a["resultado_realizado"]
        tasa_a = mt.tasa_aciertos(resultados_a)
        pf_res_a = ms.profit_factor_seguro(resultados_a)
        gan_media_a = mt.ganancia_media(resultados_a)
        perd_media_a = mt.perdida_media(resultados_a)
        costo_a = trades_a["comision"].sum() + trades_a["slippage"].sum()

        exp_a_df = ra.exposicion_por_categoria(trades_a, "algoritmo")
        conc_a = ra.concentracion_cartera(exp_a_df) if not exp_a_df.empty else 0.0
        perdida_diaria_a = serie_a.iloc[-1] if len(serie_a) else 0.0
        detalle_a = ra.evaluar_estado_alerta_detallado(dd_actual_a, perdida_diaria_a, conc_a, LIMITES)
        estado_a = detalle_a["estado"]

        # Métricas rolling (30/90/252 días) y variación de N° de operaciones
        ret_30 = ra.retorno_rolling(serie_a, 30)
        ret_90 = ra.retorno_rolling(serie_a, 90)
        ret_252 = ra.retorno_rolling(serie_a, 252)
        vol_30 = ra.volatilidad_rolling_actual(serie_a, 30, DIAS_HABILES)
        vol_90 = ra.volatilidad_rolling_actual(serie_a, 90, DIAS_HABILES)
        sharpe_rolling_30 = ra.sharpe_rolling_actual(serie_a, 30, DIAS_HABILES)
        var_num_ops = ra.variacion_num_operaciones(trades_a, returns_periodo["fecha"], 30)
        capital_utilizado_a = float((trades_a["cantidad"] * trades_a["precio_ejecutado"]).sum()) if not trades_a.empty else 0.0

        emoji_estado = {"VERDE": "🟢", "AMARILLO": "🟡", "ROJO": "🔴"}[estado_a]

        with st.expander(f"{emoji_estado} {a} — {estado_a}", expanded=(len(algo_sel) <= 2)):
            st.markdown(f"*{meta['descripcion']}*")
            st.caption(f"Inicio: {meta['fecha_inicio']} · Capital asignado: {fmt_usd(meta['capital_asignado'])}")
            if estado_a != "VERDE":
                st.warning("**Motivo de la alerta:** " + " ".join(detalle_a["motivos"]))

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Rent. acumulada", fmt_pct(ret_acum_a))
            k2.metric("Rent. anualizada", fmt_pct(ret_anual_a))
            k3.metric("Volatilidad", fmt_pct(vol_a))
            k4.metric("Máx. drawdown", fmt_pct(mdd_a))

            k5, k6, k7, k8 = st.columns(4)
            k5.metric("Drawdown actual", fmt_pct(dd_actual_a))
            k6.metric("Sharpe", sharpe_res_a.texto(), help=sharpe_res_a.motivo or None)
            k7.metric("Sortino", sortino_res_a.texto(), help=sortino_res_a.motivo or None)
            k8.metric("N° operaciones", f"{len(trades_a):,}")

            k9, k10, k11, k12 = st.columns(4)
            k9.metric("Tasa de aciertos", fmt_pct(tasa_a))
            k10.metric("Profit factor", pf_res_a.texto(), help=pf_res_a.motivo or None)
            k11.metric("Ganancia media", fmt_usd(gan_media_a))
            k12.metric("Pérdida media", fmt_usd(perd_media_a))

            k13, k14, k15, k16 = st.columns(4)
            k13.metric("Costo acumulado", fmt_usd(costo_a))
            k14.metric("Capital utilizado (notional)", fmt_usd(capital_utilizado_a))
            k15.metric("Exposición actual", fmt_usd(exp_a_df["exposicion_usd"].sum() if not exp_a_df.empty else 0.0))
            k16.metric("Variación N° operaciones (30d)", fmt_pct(var_num_ops) if var_num_ops is not None else "N/D")

            st.markdown("**Ventanas móviles (rolling)**")
            k17, k18, k19, k20 = st.columns(4)
            k17.metric("Retorno rolling 30d", fmt_pct(ret_30) if ret_30 is not None else "N/D")
            k18.metric("Retorno rolling 90d", fmt_pct(ret_90) if ret_90 is not None else "N/D")
            k19.metric("Retorno rolling 252d", fmt_pct(ret_252) if ret_252 is not None else "N/D")
            k20.metric("Sharpe rolling 30d", f"{sharpe_rolling_30:,.2f}" if sharpe_rolling_30 is not None else "N/D")

            k21, k22, k23, _ = st.columns(4)
            k21.metric("Volatilidad móvil 30d", fmt_pct(vol_30) if vol_30 is not None else "N/D")
            k22.metric("Volatilidad móvil 90d", fmt_pct(vol_90) if vol_90 is not None else "N/D")
            k23.metric("Peor día (período)", fmt_pct(mt.mejores_peores_periodos(serie_a, returns_periodo['fecha'], 1)[1]['retorno'].iloc[0]) if len(serie_a) else "N/D")

            otros = [x for x in algo_sel if x != a]
            if otros:
                corr_a = returns_periodo[[a] + otros].corr()[a].drop(a)
                st.markdown("**Correlación con otros algoritmos:** " +
                            ", ".join(f"{o}: {corr_a[o]:.2f}" for o in otros))
            corr_portafolio_res = ms.correlacion_segura(
                pd.DataFrame({a: serie_a, "portafolio": portafolio_returns}), a, "portafolio")
            st.markdown(f"**Correlación con el portafolio:** {corr_portafolio_res.texto()}"
                        + (f" _{corr_portafolio_res.motivo}_" if not corr_portafolio_res.valido else ""))

            curva_a = mt.curva_capital(serie_a, meta["capital_asignado"])
            dd_serie_a = mt.drawdown_series(serie_a)
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.plotly_chart(ch.grafico_curva_capital(returns_periodo["fecha"], curva_a),
                                 width='stretch', key=f"curva_{a}")
            with col_g2:
                st.plotly_chart(ch.grafico_drawdown(returns_periodo["fecha"], dd_serie_a),
                                 width='stretch', key=f"dd_{a}")

            st.markdown("**Últimas operaciones**")
            ult = trades_a.sort_values("fecha", ascending=False).head(10)
            st.dataframe(ult.assign(fecha=lambda d: d["fecha"].dt.strftime(FMT_FECHA)),
                         width='stretch', hide_index=True)

# ==========================================================================
# PÁGINA 5: OPERACIONES
# ==========================================================================
with tab_operaciones:
    st.subheader("Operaciones filtrables")

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        filtro_algo = st.multiselect("Filtrar por algoritmo", options=algo_sel, default=algo_sel)
    with fc2:
        filtro_instr = st.multiselect("Filtrar por instrumento",
                                       options=sorted(trades_periodo["instrumento"].unique().tolist()),
                                       default=sorted(trades_periodo["instrumento"].unique().tolist()))
    with fc3:
        filtro_tipo = st.multiselect("Filtrar por tipo", options=["COMPRA", "VENTA"],
                                      default=["COMPRA", "VENTA"])
    with fc4:
        filtro_resultado = st.selectbox("Filtrar por resultado", options=["Todos", "Ganadoras", "Perdedoras"])

    fc5, fc6 = st.columns(2)
    with fc5:
        busq_fecha_ini = st.date_input("Buscar desde", value=fecha_inicio, key="busq_ini")
    with fc6:
        busq_fecha_fin = st.date_input("Buscar hasta", value=fecha_fin, key="busq_fin")

    df_ops = trades_periodo[
        trades_periodo["algoritmo"].isin(filtro_algo) &
        trades_periodo["instrumento"].isin(filtro_instr) &
        trades_periodo["lado"].isin(filtro_tipo) &
        (trades_periodo["fecha"].dt.date >= busq_fecha_ini) &
        (trades_periodo["fecha"].dt.date <= busq_fecha_fin)
    ].copy()

    if filtro_resultado == "Ganadoras":
        df_ops = df_ops[df_ops["resultado_realizado"] > 0]
    elif filtro_resultado == "Perdedoras":
        df_ops = df_ops[df_ops["resultado_realizado"] < 0]

    df_ops["resultado_neto"] = df_ops["resultado_realizado"]  # ya neto de comisión y slippage

    st.dataframe(
        df_ops.assign(fecha=lambda d: d["fecha"].dt.strftime(FMT_FECHA)),
        width='stretch', hide_index=True, height=380,
    )

    csv_bytes = df_ops.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar a CSV", data=csv_bytes, file_name="operaciones_filtradas.csv",
                        mime="text/csv")

    st.subheader("Control de calidad de datos")
    problemas = []

    nulos = trades_periodo.isnull().sum()
    nulos = nulos[nulos > 0]
    if not nulos.empty:
        problemas.append(("Valores nulos", nulos.to_dict()))

    duplicados = trades_periodo.duplicated(subset=[c for c in trades_periodo.columns if c != "trade_id"]).sum()
    if duplicados > 0:
        problemas.append(("Operaciones duplicadas", int(duplicados)))

    precios_invalidos = (trades_periodo["precio_ejecutado"] <= 0).sum()
    if precios_invalidos > 0:
        problemas.append(("Precios inválidos (<=0)", int(precios_invalidos)))

    cantidades_negativas = (trades_periodo["cantidad"] < 0).sum()
    if cantidades_negativas > 0:
        problemas.append(("Cantidades negativas", int(cantidades_negativas)))

    monedas_invalidas = (~trades_periodo["moneda"].isin(["USD"])).sum()
    if monedas_invalidas > 0:
        problemas.append(("Monedas no reconocidas", int(monedas_invalidas)))

    sin_algo = trades_periodo["algoritmo"].isnull().sum()
    if sin_algo > 0:
        problemas.append(("Operaciones sin algoritmo asociado", int(sin_algo)))

    fechas_esperadas = set(pd.bdate_range(fecha_inicio, fecha_fin).date)
    fechas_con_datos = set(returns_periodo["fecha"].dt.date)
    fechas_faltantes = fechas_esperadas - fechas_con_datos
    if fechas_faltantes:
        problemas.append(("Fechas hábiles sin datos de retorno", len(fechas_faltantes)))

    if problemas:
        for nombre, detalle in problemas:
            st.warning(f"**{nombre}**: {detalle}")
    else:
        st.success("No se detectaron problemas de calidad de datos en el período seleccionado.")

# ==========================================================================
# PÁGINA 6: CALIDAD DE DATOS ("Data Quality Monitor")
# ==========================================================================
with tab_calidad:
    st.subheader("🧪 Data Quality Monitor")
    st.caption("El dashboard no oculta errores: cada problema detectado se muestra con su "
               "cantidad, un ejemplo y una recomendación de corrección.")

    estado = REPORTE_CALIDAD.estado_general
    color_estado = {"OK": "🟢", "REVISAR": "🟡", "ERROR": "🔴"}[estado]

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Estado general", f"{color_estado} {estado}")
    q2.metric("Registros de operaciones", f"{REPORTE_CALIDAD.num_registros_trades:,}")
    q3.metric("Registros de retornos diarios", f"{REPORTE_CALIDAD.num_registros_returns:,}")
    q4.metric("Última carga", fmt_fecha(REPORTE_CALIDAD.fecha_ultima_carga))

    q5, q6, q7 = st.columns(3)
    q5.metric("Período cubierto", f"{fmt_fecha(REPORTE_CALIDAD.periodo_inicio)} – {fmt_fecha(REPORTE_CALIDAD.periodo_fin)}")
    q6.metric("Algoritmos encontrados", f"{len(REPORTE_CALIDAD.algoritmos_encontrados)}")
    q7.metric("Instrumentos encontrados", f"{len(REPORTE_CALIDAD.instrumentos_encontrados)}")

    st.markdown("**Algoritmos:** " + ", ".join(REPORTE_CALIDAD.algoritmos_encontrados))
    st.markdown("**Instrumentos:** " + ", ".join(REPORTE_CALIDAD.instrumentos_encontrados))

    st.markdown("---")
    st.subheader("Problemas detectados")
    if not REPORTE_CALIDAD.problemas:
        st.success("No se detectaron problemas de calidad de datos en el período seleccionado.")
    else:
        for p in REPORTE_CALIDAD.problemas:
            icono = "🔴" if p.severidad == "ERROR" else "🟡"
            with st.expander(f"{icono} {p.tipo} — {p.cantidad} registro(s) ({p.severidad})"):
                st.markdown(f"**Ejemplo:** {p.ejemplo}")
                st.markdown(f"**Recomendación:** {p.recomendacion}")

    st.markdown("---")
    st.caption(
        f"Archivo de operaciones: {DATA_META.get('trades_archivo')} · "
        f"Versión de datos: {DATA_META.get('trades_version_datos')} · "
        f"Última modificación: {fmt_fecha(DATA_META.get('trades_ultima_modificacion'))}"
    )

# ==========================================================================
# PÁGINA 7: METODOLOGÍA Y DICCIONARIO DE DATOS
# ==========================================================================
with tab_metodologia:
    st.subheader("📚 Assumptions & Methodology")
    st.caption("Supuestos y método de cálculo utilizados en este MVP. Un resumen de esta "
               "sección se incluye en todos los reportes PDF.")

    etiquetas_metodologia = {
        "capital_inicial": "Capital inicial",
        "moneda_base": "Moneda base",
        "benchmark": "Benchmark",
        "frecuencia_datos": "Frecuencia de datos",
        "convencion_dias": "Convención de días",
        "metodo_retornos": "Método de cálculo de retornos",
        "tratamiento_comisiones": "Tratamiento de comisiones",
        "tratamiento_slippage": "Tratamiento del slippage",
        "metodo_anualizacion": "Método de anualización",
        "metodo_var": "Método de VaR",
        "metodo_cvar": "Método de CVaR",
        "tasa_libre_riesgo": "Tasa libre de riesgo utilizada",
        "tratamiento_posiciones_abiertas": "Tratamiento de posiciones abiertas",
        "definicion_exposicion": "Definición de exposición",
        "definicion_rotacion": "Definición de rotación",
        "limitaciones_generales": "Limitaciones del modelo",
    }
    for clave, etiqueta in etiquetas_metodologia.items():
        valor = METODOLOGIA.get(clave, "s/d")
        st.markdown(f"**{etiqueta}:** {valor}")

    st.markdown("---")
    st.subheader("📖 Data Dictionary — trades.csv")
    if DICCIONARIO_DATOS:
        df_dic = pd.DataFrame(DICCIONARIO_DATOS).rename(columns={
            "campo": "Campo", "tipo": "Tipo", "descripcion": "Descripción", "unidad": "Unidad",
            "obligatorio": "Obligatorio", "ejemplo": "Ejemplo", "fuente": "Fuente",
            "tratamiento_faltantes": "Tratamiento de faltantes",
        })
        st.dataframe(df_dic, width="stretch", hide_index=True)
    else:
        st.info("Diccionario de datos no configurado.")

    st.markdown("---")
    st.subheader("Trazabilidad de KPIs")
    st.caption("Qué significa cada métrica, cómo se calcula y qué limitaciones tiene.")
    trazabilidad = {
        "Retorno acumulado": "Producto compuesto de los retornos diarios del período. Usa solo datos hasta la fecha de corte.",
        "Retorno anualizado": "Retorno acumulado llevado a base anual (252 días hábiles), geométrico.",
        "Volatilidad": "Desviación estándar de los retornos diarios, anualizada. Sensible al tamaño de la muestra.",
        "Sharpe": "Retorno en exceso / volatilidad. No garantiza calidad futura; asume retornos ~normales.",
        "Sortino": "Como el Sharpe, pero solo penaliza la volatilidad de los retornos negativos.",
        "Calmar": "Retorno anualizado / máximo drawdown. No definido si no hubo drawdown en el período.",
        "Máximo drawdown": "Mayor caída porcentual desde un máximo histórico de capital.",
        "Duración del drawdown": "Días hábiles en estado de drawdown (desde el máximo hasta la recuperación o el fin del período).",
        "VaR": "Percentil empírico de pérdida histórica; no es una pérdida máxima garantizada.",
        "CVaR": "Promedio de las pérdidas que exceden el VaR; poco confiable con historiales cortos.",
        "Profit factor": "Suma de ganancias / suma de pérdidas de las operaciones. No definido sin operaciones.",
        "Exposición": "Notional absoluto (cantidad x precio) agregado por categoría.",
        "Concentración": "Participación máxima de una categoría sobre el total de exposición.",
        "Correlación": "Coeficiente de Pearson entre series de retornos; puede cambiar en el tiempo.",
        "Rotación": "Volumen operado / capital promedio, anualizado. Aproximación simple.",
    }
    for k, v in trazabilidad.items():
        with st.expander(k):
            st.markdown(v)

# ==========================================================================
# PÁGINA 8: REPORTES
# ==========================================================================
with tab_reportes:
    st.subheader("🧾 Generación de reportes PDF")
    st.markdown(
        "Tres niveles de reporte, según la audiencia. Todos incluyen fecha/hora de "
        "generación, período, versión del dashboard, versión de los datos, archivo fuente "
        "y las advertencias obligatorias sobre datos ficticios y resultados históricos."
    )

    nivel_reporte = st.radio(
        "Tipo de reporte",
        options=["A. Ejecutivo (1 página)", "B. Semanal de riesgo", "C. Mensual detallado"],
        horizontal=False,
    )

    if nivel_reporte.startswith("A"):
        rep_inicio, rep_fin = fecha_fin, fecha_fin
    elif nivel_reporte.startswith("B"):
        rep_inicio = max(fecha_inicio, fecha_fin - pd.Timedelta(days=7))
        rep_fin = fecha_fin
    else:
        rep_inicio = max(fecha_inicio, fecha_fin - pd.Timedelta(days=30))
        rep_fin = fecha_fin

    st.caption(f"Período del reporte: {fmt_fecha(rep_inicio)} a {fmt_fecha(rep_fin)}")

    def _subset_periodo(ini, fin):
        mask_rep = (returns_periodo["fecha"].dt.date >= ini) & (returns_periodo["fecha"].dt.date <= fin)
        ret_rep = returns_periodo.loc[mask_rep].reset_index(drop=True)
        trades_rep_mask = (trades_periodo["fecha"].dt.date >= ini) & (trades_periodo["fecha"].dt.date <= fin)
        trades_rep = trades_periodo.loc[trades_rep_mask].reset_index(drop=True)
        return ret_rep, trades_rep

    def _tabla_riesgo_por_algo(ret_rep, trades_rep):
        filas = []
        alertas = []
        for a in algo_sel:
            serie_a = ret_rep[a] if a in ret_rep.columns else pd.Series(dtype=float)
            tr_a = trades_rep[trades_rep["algoritmo"] == a] if not trades_rep.empty else trades_rep
            dd_a = mt.drawdown_actual(serie_a) if len(serie_a) else 0.0
            exp_a_df = ra.exposicion_por_categoria(tr_a, "algoritmo") if not tr_a.empty else pd.DataFrame()
            conc_a = ra.concentracion_cartera(exp_a_df) if not exp_a_df.empty else 0.0
            perdida_a = serie_a.iloc[-1] if len(serie_a) else 0.0
            detalle = ra.evaluar_estado_alerta_detallado(dd_a, perdida_a, conc_a, LIMITES)
            fila = {
                "Algoritmo": a,
                "Rent. acumulada": f"{mt.retorno_acumulado(serie_a)*100:,.2f}%" if len(serie_a) else "N/D",
                "Máx. DD": f"{mt.maximo_drawdown(serie_a)*100:,.2f}%" if len(serie_a) else "N/D",
                "Sharpe": ms.sharpe_seguro(serie_a, dias_habiles=DIAS_HABILES).texto(),
                "Estado": detalle["estado"],
                "Motivo": " ".join(detalle["motivos"]),
            }
            filas.append(fila)
            if detalle["estado"] != "VERDE":
                alertas.append(fila)
        return filas, alertas

    def _generar_pdf(nivel: str, ini, fin) -> str | None:
        ret_rep, trades_rep = _subset_periodo(ini, fin)
        if ret_rep.empty:
            st.error("No hay datos suficientes para generar el reporte en ese período.")
            return None

        port_rep = sum(ret_rep[a] * pesos[a] for a in algo_sel)
        bench_rep = ret_rep[BENCH_NAME]
        curva_rep = mt.curva_capital(port_rep, capital_inicial)
        costos_rep = ra.costos_totales(trades_rep)
        tabla_algos, alertas = _tabla_riesgo_por_algo(ret_rep, trades_rep)

        version_dash = DATA_META.get("dashboard_version", "s/d")
        version_datos = DATA_META.get("trades_version_datos", "s/d")
        archivo_datos = DATA_META.get("trades_archivo", "s/d")

        os.makedirs("reports", exist_ok=True)

        if nivel == "ejecutivo":
            ret_por_algo = {a: mt.retorno_acumulado(ret_rep[a]) for a in algo_sel}
            vol_por_algo = {a: mt.volatilidad(ret_rep[a], True, DIAS_HABILES) for a in algo_sel}
            algo_mejor = max(ret_por_algo, key=ret_por_algo.get) if ret_por_algo else "s/d"
            algo_mayor_riesgo = max(vol_por_algo, key=vol_por_algo.get) if vol_por_algo else "s/d"
            ruta = os.path.join("reports", f"reporte_ejecutivo_{fin.strftime('%Y%m%d')}.pdf")
            return generar_reporte_ejecutivo(
                ruta_salida=ruta, periodo_inicio=fmt_fecha(ini), periodo_fin=fmt_fecha(fin),
                capital_inicial=capital_inicial,
                capital_final=float(curva_rep.iloc[-1]) if len(curva_rep) else capital_inicial,
                retorno_pct=mt.retorno_acumulado(port_rep), retorno_benchmark_pct=mt.retorno_acumulado(bench_rep),
                nombre_benchmark=BENCH_NAME, max_drawdown_pct=mt.maximo_drawdown(port_rep),
                volatilidad_pct=mt.volatilidad(port_rep, True, DIAS_HABILES),
                sharpe=ms.sharpe_seguro(port_rep, dias_habiles=DIAS_HABILES).valor,
                algo_mejor=algo_mejor, algo_mayor_riesgo=algo_mayor_riesgo, alertas=alertas,
                dashboard_version=version_dash, version_datos=version_datos, nombre_archivo_datos=archivo_datos,
            )

        elif nivel == "semanal":
            exp_algo = ra.exposicion_por_categoria(trades_rep, "algoritmo") if not trades_rep.empty else pd.DataFrame()
            conc = ra.concentracion_cartera(exp_algo) if not exp_algo.empty else None
            corr_relevantes = []
            if len(algo_sel) >= 2:
                corr_df = ret_rep[algo_sel].corr()
                vistos = set()
                for a in algo_sel:
                    for b in algo_sel:
                        if a != b and frozenset((a, b)) not in vistos:
                            vistos.add(frozenset((a, b)))
                            corr_relevantes.append({"Par": f"{a} / {b}", "Correlación": f"{corr_df.loc[a,b]:.2f}"})
            calidad_rep = dq.evaluar_calidad(trades_rep, ret_rep, ini, fin)
            ruta = os.path.join("reports", f"reporte_semanal_{fin.strftime('%Y%m%d')}.pdf")
            return generar_reporte_semanal(
                ruta_salida=ruta, periodo_inicio=fmt_fecha(ini), periodo_fin=fmt_fecha(fin),
                rendimiento_semanal_pct=mt.retorno_acumulado(port_rep),
                kpis_riesgo={
                    "Máximo drawdown": _fmt_pct_or_nd(mt.maximo_drawdown(port_rep)),
                    "Sharpe": ms.sharpe_seguro(port_rep, dias_habiles=DIAS_HABILES).texto(),
                    "VaR 95%": ms.var_seguro(port_rep, 0.95).texto("{:.2%}"),
                    "CVaR 95%": ms.cvar_seguro(port_rep, 0.95).texto("{:.2%}"),
                },
                tabla_riesgo_algoritmos=tabla_algos, exposicion=exp_algo.to_dict("records") if not exp_algo.empty else [],
                concentracion_pct=conc, correlaciones_relevantes=corr_relevantes, costos=costos_rep,
                resumen_calidad_datos={
                    "Estado general": calidad_rep.estado_general,
                    "Problemas detectados": len(calidad_rep.problemas),
                    "Registros de operaciones": calidad_rep.num_registros_trades,
                },
                alertas_abiertas=alertas, alertas_cerradas=[],
                comentarios_metodologicos=[
                    METODOLOGIA.get("metodo_var", ""), METODOLOGIA.get("limitaciones_generales", ""),
                ],
                dashboard_version=version_dash, version_datos=version_datos, nombre_archivo_datos=archivo_datos,
            )

        else:  # mensual
            atrib_algo = ra.atribucion_por_categoria(trades_rep, "algoritmo")
            atrib_instr = ra.atribucion_por_categoria(trades_rep, "instrumento")
            stress = ra.stress_test_simple(port_rep, float(curva_rep.iloc[-1]) if len(curva_rep) else capital_inicial)
            calidad_rep = dq.evaluar_calidad(trades_rep, ret_rep, ini, fin)
            ruta = os.path.join("reports", f"reporte_mensual_{fin.strftime('%Y%m%d')}.pdf")
            return generar_reporte_mensual(
                ruta_salida=ruta, periodo_inicio=fmt_fecha(ini), periodo_fin=fmt_fecha(fin),
                resumen_ejecutivo={
                    "Capital inicial": _fmt_usd(capital_inicial),
                    "Capital final": _fmt_usd(float(curva_rep.iloc[-1]) if len(curva_rep) else capital_inicial),
                    "Retorno del período": _fmt_pct_or_nd(mt.retorno_acumulado(port_rep)),
                },
                rendimiento_bruto_neto={
                    "Comisiones totales": _fmt_usd(costos_rep["comisiones"]),
                    "Slippage total": _fmt_usd(costos_rep["slippage"]),
                    "Resultado neto total": _fmt_usd(trades_rep["resultado_realizado"].sum() if not trades_rep.empty else 0.0),
                },
                atribucion_algoritmo=atrib_algo.to_dict("records") if not atrib_algo.empty else [],
                atribucion_instrumento=atrib_instr.to_dict("records") if not atrib_instr.empty else [],
                riesgo_absoluto={
                    "Volatilidad anualizada": _fmt_pct_or_nd(mt.volatilidad(port_rep, True, DIAS_HABILES)),
                    "Máximo drawdown": _fmt_pct_or_nd(mt.maximo_drawdown(port_rep)),
                },
                riesgo_relativo={
                    f"Retorno {BENCH_NAME}": _fmt_pct_or_nd(mt.retorno_acumulado(bench_rep)),
                    "Diferencia vs. benchmark": _fmt_pct_or_nd(mt.retorno_acumulado(port_rep) - mt.retorno_acumulado(bench_rep)),
                },
                drawdown_info={
                    "Duración máx. drawdown (días)": mt.duracion_drawdown(port_rep)[0],
                    "Duración drawdown actual (días)": mt.duracion_drawdown(port_rep)[1],
                },
                var_cvar={
                    "VaR histórico 95%": ms.var_seguro(port_rep, 0.95).texto("{:.2%}"),
                    "CVaR histórico 95%": ms.cvar_seguro(port_rep, 0.95).texto("{:.2%}"),
                },
                stress_test=stress.assign(
                    impacto_usd=lambda d: d["impacto_usd"].map(lambda v: f"US$ {v:,.2f}"),
                    capital_resultante=lambda d: d["capital_resultante"].map(lambda v: f"US$ {v:,.2f}"),
                ).to_dict("records"),
                resumen_calidad_datos={
                    "Estado general": calidad_rep.estado_general,
                    "Problemas detectados": len(calidad_rep.problemas),
                },
                cambios_parametros=[f"Capital inicial configurado: {_fmt_usd(capital_inicial)}"],
                limitaciones=[
                    METODOLOGIA.get("limitaciones_generales", ""),
                    METODOLOGIA.get("tratamiento_posiciones_abiertas", ""),
                ],
                dashboard_version=version_dash, version_datos=version_datos, nombre_archivo_datos=archivo_datos,
            )

    nivel_map = {"A": "ejecutivo", "B": "semanal", "C": "mensual"}
    nivel_actual = nivel_map[nivel_reporte[0]]

    generar_click = generar_pdf_btn or st.button("Generar reporte ahora", key="generar_reporte_tab")
    if generar_click:
        ruta_generada = _generar_pdf(nivel_actual, rep_inicio, rep_fin)
        if ruta_generada:
            st.success(f"Reporte generado: {ruta_generada}")
            with open(ruta_generada, "rb") as f:
                st.download_button("⬇️ Descargar PDF", data=f.read(),
                                    file_name=os.path.basename(ruta_generada), mime="application/pdf",
                                    key="descarga_reporte_tab")

    st.markdown("---")
    st.caption(
        "\"Este reporte tiene fines informativos y de monitoreo. Los datos son ficticios o "
        "dependen de la información cargada por el usuario. Los resultados históricos, "
        "simulados o de backtesting no garantizan resultados futuros. Este sistema no "
        "constituye asesoría financiera ni una recomendación de inversión.\""
    )

# --------------------------------------------------------------------------
# Pie de página
# --------------------------------------------------------------------------
st.markdown("---")
st.caption(SETTINGS["app"].get("pie_pagina", "MVP Demo — Datos ficticios — No constituye asesoría financiera"))
