# AlgoControl - Trading Algorithm Dashboard 📈

Una plataforma avanzada de analítica y visualización diseñada para la **evaluación robusta de algoritmos de trading**. Este dashboard permite monitorear métricas clave de rendimiento, analizar la calidad de los datos y simular escenarios mediante la generación de datos sintéticos, optimizando la toma de decisiones estratégicas sobre portafolios de ETFs, acciones y divisas.

---

## 🚀 Características Principales

*   **Evaluación de Algoritmos:** Análisis enfocado estrictamente en la consistencia y el rendimiento de los modelos (Métricas Sharpe, Equity, y estado del algoritmo), diferenciándose de las herramientas tradicionales de portafolio.
*   **Simulación con Datos Sintéticos:** Capacidad avanzada para modelar escenarios y validar estrategias en entornos controlados mediante la generación de datos artificiales de alta fidelidad.
*   **Análisis de Riesgo y Calidad:** Módulos integrados para la auditoría de calidad de datos (`data_quality.py`) y gestión de riesgo adaptativa (`risk_analysis.py`).
*   **Interfaz de Alta Fidelidad:** Diseño optimizado en React (con soporte para cambio de temas claro/oscuro y skins alternativas) y backend escalable.

---

## 🛠️ Estructura del Proyecto

El repositorio mantiene una arquitectura limpia y modular para separar la lógica de evaluación, los datos y la interfaz de usuario:

| Componente / Archivo | Descripción |
| :--- | :--- |
| **`src/App.jsx`** | Interfaz principal y lógica de presentación visual (React). |
| **`backend/evaluation.py`** | Motor de cálculo para métricas de rendimiento y estadísticas profundas. |
| **`backend/algorithms.py`** | Definición y control de los algoritmos de trading integrados. |
| **`src/data_quality.py`** | Módulo de validación y control de calidad de las fuentes de datos. |
| **`src/risk_analysis.py`** | Análisis estadístico de riesgo y simulaciones de mercado. |
| **`src/generators.py`** | Motor de generación de datos sintéticos para pruebas de estrés. |

---

## 🔧 Requisitos e Instalación

Para ejecutar el entorno de desarrollo local, asegúrate de contar con los módulos definidos en las dependencias del sistema:

1. **Instalación de dependencias del Backend (Python):**
   ```bash
   pip install -r requirements.txt
   ```
   *Nota: Incluye bibliotecas clave como `yfinance` y `pandas` para el procesamiento de datos.*

2. **Ejecución de Pruebas de Concepto:**
   ```bash
   pytest tests/test_poc.py
   ```

---

## 📊 Flujo de Trabajo (CI/CD)

El proyecto cuenta con scripts de automatización para el despliegue rápido y la sincronización de cambios:
*   Integración y despliegue continuo vinculados mediante scripts de automatización local hacia repositorios **GitLab** y plataformas en la nube.
*   Control de ejecución directo desde los directorios locales definidos para el proyecto.

---

## ✒️ Autor

* **Carlos Vergara** - *Desarrollo e Integración* - [carlosvergarachile](https://github.com/carlosvergarachile)
