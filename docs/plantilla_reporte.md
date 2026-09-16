# Plantilla del reporte de validación

Este documento describe la estructura del PDF que se entrega al cliente.
La plantilla se llena con datos reales del algoritmo evaluado.

## Página 1 — Portada

VALIDACIÓN ALGORÍTMICA · REPORTE

Algoritmo: [nombre del algoritmo]
Versión: [vX.X]
Tipo: [tendencia / reversión / momentum / defensivo]
Mercado: [instrumentos]
Período evaluado: [fecha inicio — fecha fin]

Evaluado por: Carlos Vergara
Aprobado por: [nombre]
Fecha de emisión: [DD-MM-AAAA]

Documento confidencial. Resultados bajo escenarios sintéticos.
No constituye asesoría financiera.


## Página 2 — Ficha del algoritmo

Descripción del algoritmo, tipo de estrategia, activos que opera, horizonte
temporal, quién lo construyó, cuándo entró en operación.

## Página 3 — Configuración del experimento

| Parámetro | Valor |
|---|---|
| Semilla | XXXXXX |
| Generador | RegimeSim vX.X |
| Número de escenarios | XXX |
| Supuestos de costo | comisión X.XX%, slippage X.XX% |
| Benchmark | Global Market Index |
| Aprobado por | — |

## Páginas 4–7 — Resultados por escenario

Distribución de resultados bajo cada régimen evaluado. Tabla con mediana,
P5, P25, P75, P95, probabilidad de pérdida, máximo drawdown.

## Páginas 8–10 — Robustez y sensibilidad

Matriz algoritmo × escenario. Identificación de escenarios críticos.
Análisis de sensibilidad a volatilidad, correlación, cambios de régimen.

## Páginas 11–12 — Sobreajuste

PBO, Deflated Sharpe Ratio, walk-forward efficiency. Clasificación:
robusto, marginal, sobreajustado.

## Página 13 — Limitaciones

Lista explícita. No es un descargo de responsabilidad. Es una sección técnica
que documenta qué no se probó y bajo qué condiciones se recomienda re-evaluar.

## Página 14 — Trazabilidad

Semilla, hash del dataset, versiones, fechas, aprobadores.

## Página 15 — Glosario

Definiciones breves de los términos técnicos usados.
