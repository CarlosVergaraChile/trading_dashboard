# AlgoControl — integración de auditoría de datos y algoritmos

## Decisión
Mantener `trading_dashboard` como candidato a repositorio principal de AlgoControl. `trading` aporta una interfaz de gobierno cuantitativo y demostración de drift, que debe compararse y trasladarse por módulos, **no fusionarse en bloque**.

## Lo que existe en el código
- `src/data_quality.py`: controles básicos y contraste KS/Wasserstein con series históricas.
- `src/generators.py`: regímenes sintéticos (alcista, bajista, lateral, volatilidad, costos).
- `backend/algorithms.py`: cuatro algoritmos DEMO, generadores de señales; no son estrategias clientes verificadas.
- `backend/evaluation.py`: métricas Sharpe, Sortino, VaR, CVaR, drawdown y una política ilustrativa CONTINUE/RETRAIN/STOP.
- `tests/test_poc.py`: pruebas de concepto, incluida ausencia de endpoint de órdenes.
- Nuevo `src/quality_audit.py`: contrato separado y explícito de calidad sintética y evaluación por régimen, con límites metodológicos.
- Nuevas pruebas `tests/test_quality_audit.py`.

## Antes de afirmar calidad de los datos sintéticos
1. Especificar datos de referencia y trazabilidad temporal.
2. Evaluar distribución marginal y dependencia temporal, autocorrelación, colas y extremos.
3. Determinar cobertura de regímenes y sensibilidad.
4. Separar datos de calibración y evaluación para evitar leakage.
5. Hacer análisis de escenarios que incluya latencia, costos, slippage y fallas de proveedor.

## Antes de afirmar calidad del algoritmo
1. Definir claramente la estrategia y comparar contra una línea base.
2. Backtest fuera de muestra y walk-forward.
3. Variaciones por mercado, régimen y tamaño de muestra.
4. Costos, drawdown, riesgos de cola y robustez ante perturbaciones.
5. Mostrar intervalos e incertidumbre, no solo métricas puntuales.

## Seguridad y alcance
- Producto de **evaluación y validación** de estrategias, no ejecución de transacciones.
- Sin órdenes de compra/venta; no enlazar a brokers ni prometer rentabilidad.
- Los nombres de algoritmos de demostración son solo ejemplos.
- Este commit NO altera el endpoint activo ni despliega la aplicación.
- Validar mediante `pytest tests/test_quality_audit.py` en entorno con dependencias instaladas.
