
---

## `docs/metodologia.md`

```markdown
# Validación independiente para sistemas algorítmicos

*Capa de robustez y trazabilidad sobre portafolios de trading*

## Por qué existe esta capa

Los sistemas algorítmicos bien construidos ya tienen backtest, control de
riesgo y monitoreo en vivo. Lo que suele faltar es una capa independiente
que responda tres preguntas que el equipo que construye el algoritmo, por
definición, no puede responder con distancia:

1. **¿El algoritmo funciona por su lógica o por coincidencia?** El backtest
   sobre datos históricos responde a una sola trayectoria del pasado. Un
   algoritmo puede ajustarse a esa trayectoria sin capturar ninguna
   regularidad real.

2. **¿Qué tan sensible es a los supuestos de los datos de entrenamiento?**
   Con datos sintéticos, esta pregunta es central: el algoritmo puede ser
   robusto bajo un generador y frágil bajo otro, y el resultado del backtest
   no lo muestra.

3. **¿Cómo se documenta esto de manera que sobreviva una revisión externa?**
   Familia, socios, inversionistas o reguladores pedirán evidencia trazable
   de que la evaluación no se hizo en el mismo conjunto de datos con el que
   se construyó el algoritmo.

Esta capa no reemplaza el trabajo del equipo. Lo hace auditable.

## Qué valida exactamente

Para cada algoritmo, sobre un conjunto de escenarios definidos en conjunto
con el cliente:

| Dimensión | Pregunta que responde | Método |
|---|---|---|
| Sobreajuste | ¿El resultado es producto de la lógica o de la curva? | PBO, Deflated Sharpe Ratio |
| Robustez entre escenarios | ¿El algoritmo funciona bajo regímenes distintos? | Distribución de resultados sobre múltiples escenarios sintéticos, con semilla fija |
| Sensibilidad a supuestos | ¿Qué parámetros del generador cambian el resultado? | Análisis de sensibilidad sobre volatilidad, correlación, colas, cambios de régimen |
| Fallas por costos | ¿A qué múltiplo de costos muere el edge? | Cost stress test a 1×, 2×, 3×, 5× comisión y slippage |
| Comportamiento fuera de muestra | ¿El modelo generaliza? | Walk-forward analysis con ventanas desplazadas |
| Calidad de los datos | ¿Los datos de entrada pasan un contrato explícito? | Validación de esquema, integridad, frescura, rangos, unicidad |
| Trazabilidad | ¿Se puede reproducir cada resultado? | Registro de semilla, versión de generador, hash del dataset y versión del algoritmo |

## Qué no hace esta capa

- No predice retornos.
- No recomienda comprar o vender.
- No conecta brokers ni ejecuta órdenes.
- No reemplaza el monitoreo en vivo del portafolio.
- No certifica que un algoritmo sea seguro ni rentable.

Evalúa **robustez metodológica**, no desempeño futuro.

## Cómo se ve un reporte

Cada algoritmo evaluado produce un documento de aproximadamente 15 páginas
con esta estructura:

1. **Ficha del algoritmo** — nombre, versión, tipo, mercado, activos,
   horizonte, fecha de evaluación, aprobadores.
2. **Configuración del experimento** — generador, semilla, número de
   escenarios, supuestos de costos, benchmark.
3. **Distribución de resultados** — retorno mediano, percentiles, probabilidad
   de pérdida, peor y mejor escenario.
4. **Robustez por escenario** — matriz algoritmo × régimen.
5. **Sensibilidad** — cómo cambia el resultado al variar supuestos críticos.
6. **Sobreajuste** — PBO, Deflated Sharpe, walk-forward.
7. **Stress tests** — escenarios adversos.
8. **Calidad de datos** — contrato aplicado, problemas detectados.
9. **Limitaciones explícitas** — qué no se probó, qué supuestos son fuertes.
10. **Trazabilidad** — semilla, hash, versiones, aprobadores.

Cada reporte concluye con una clasificación **prudente** entre:

- Robusto bajo los escenarios evaluados.
- Sensible a costos.
- Sensible a cambios de régimen.
- Insuficientemente validado.

Nunca concluye "rentable," "seguro" ni "listo para producción."

## Cómo se entrega

- El reporte en PDF.
- Los resultados crudos en CSV.
- El código de las funciones de cálculo, versionado, para que un tercero
  pueda reproducir los números.
- Los supuestos y definiciones documentados en un anexo metodológico.

## Cómo se empieza

El primer paso no es un contrato. Es una sesión de trabajo con el dueño del
portafolio para definir: qué escenarios importan, qué algoritmo evaluar
primero, qué datos existen y en qué formato.

De ahí sale una propuesta de alcance concreto.

---

*Carlos Vergara · Consultoría Estratégica*
*carlosvergarachile@uchile.cl*
