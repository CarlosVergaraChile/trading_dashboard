# Validation & Robustness Terminal

Prototipo de una capa independiente de validación para portafolios de
algoritmos de trading. No mide P&L en vivo. No reemplaza el monitoreo
existente. Responde una sola pregunta:

**¿Cómo se comportan estas estrategias bajo escenarios que no vieron en
entrenamiento?**

## Qué incluye

- Contrato de datos sobre el dataset sintético (5 reglas, semilla fija).
- Métricas de riesgo: VaR, CVaR, máximo drawdown, Sharpe, Sortino.
- Evaluación por escenario: 6 regímenes × 100 corridas con semilla fija.
- Matriz de correlación entre 6 algoritmos sintéticos + benchmark.
- Bitácora de experimentos con IDs determinísticos por ciclo.
- Generación de reporte PDF con ficha, resultados, limitaciones y trazabilidad.

## Qué no incluye

- Conexión a brokers.
- Ejecución de órdenes.
- Predicción de retornos.
- Recomendaciones de inversión.
- Datos reales de mercado.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
