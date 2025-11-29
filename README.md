# PerfAPI – API para análisis de rendimiento de aplicaciones

PerfAPI es una API construida con **FastAPI** cuyo objetivo es analizar el rendimiento de una aplicación desde dos frentes:

1. **Métricas de sistema y procesos**: CPU, memoria y E/S (disco y red).
2. **Perfilado de funciones** de la propia aplicación (creación de perfiles), midiendo:
   - Tiempo de ejecución (CPU / cumtime por función, vía `cProfile`).
   - Uso de recursos del proceso durante la ejecución (memoria RSS y E/S).

La API está diseñada siguiendo **buenas prácticas de arquitectura** (separación por capas, SRP, SOLID básico) y con **código documentado**, para que sea fácil de entender, mantener y extender.

---

## 1. Tecnologías utilizadas

- **Python 3.x**
- **FastAPI** (framework web)
- **Uvicorn** (servidor ASGI)
- **psutil** (métricas de sistema/procesos)
- Librerías estándar de Python:
  - `cProfile`, `pstats` (perfilado)
  - `threading`, `collections.deque`, `time`, etc.

Archivo `requirements.txt` (referencia):

```txt
fastapi
uvicorn[standard]
psutil
```
---
## 2. Objetivos funcionales

La API busca cumplir con el siguiente enunciado:

Desarrollar una API que implemente diferentes mecanismos para analizar el rendimiento de una aplicación en un conjunto acotado de parámetros (CPU, memoria, dispositivos de E/S) y el análisis del uso de recursos de una función determinada de la aplicación (creación de perfiles).

En concreto, la API permite:

   - Consultar métricas de CPU, memoria, E/S de disco y E/S de red del sistema.

   - Consultar métricas detalladas de un proceso específico (por PID).

   - Mantener un histórico de métricas de sistema y obtener un resumen temporal.
     
   - Registrar funciones de la aplicación y perfilarlas:

     -   Modo estándar (tiempo/cumtime por función).
     -   Modo detallado (tiempo + uso de memoria y E/S por ejecución).

---
## 3. Estructura del proyecto

El código está organizado en una estructura por capas:

```
app/
├─ __init__.py
├─ main.py                # Punto de entrada FastAPI
├─ models/                # Modelos Pydantic (contratos de la API)
│  ├─ __init__.py
│  ├─ metrics.py          # SystemMetrics, ProcessMetrics, History, Summary
│  └─ profiling.py        # ProfileRunRequest, ProfileStats, ProfileStatsDetailed...
├─ services/              # Lógica de negocio (no conocen HTTP)
│  ├─ __init__.py
│  ├─ metrics_service.py          # Lectura de métricas de sistema y procesos
│  ├─ metrics_history_service.py  # Muestreo en background e histórico
│  └─ profiler_service.py         # Registro y perfilado de funciones
└─ routers/               # Routers FastAPI (capa de presentación)
   ├─ __init__.py
   ├─ metrics_router.py   # Endpoints /metrics/...
   ├─ profiling_router.py # Endpoints /profile/...
   └─ misc_router.py      # /health, /simulate_work, raíz "/"
```

---
## 3.1 Capas principales

- **Models (app/models)**
    
    Contienen las clases Pydantic que definen el contrato de la API:

    -   SystemMetrics, ProcessMetrics

    -   SystemMetricsHistory, SystemMetricsSummary

    -   ProfileRunRequest, ProfileStats, ResourceUsageSample, ProfileStatsDetailed


-   **Services (app/services)**

    Encapsulan la lógica de negocio:

    -   MetricsService: obtiene métricas de sistema y de procesos usando psutil.

    -   MetricsHistoryService: mantiene un histórico de métricas en memoria (deque) mediante un hilo en background.

    -   ProfilerService: ejecuta y perfila funciones registradas usando cProfile y, en modo detallado, psutil.Process.

    -   ProfilingTargetRegistry: registro de funciones perfilables.


- **Routers (app/routers)**

    Exponen la funcionalidad vía HTTP:

    - metrics_router: /metrics/system, /metrics/process/{pid}, /metrics/system/history, /metrics/system/summary.

    - profiling_router: /profile/targets, /profile/run, /profile/run_detailed.

    - misc_router: /health, /simulate_work, /.


- **main (app/main.py)**

    - Crea la instancia FastAPI.

    - Incluye los routers.

    - Registra eventos de startup/shutdown para arrancar/detener el muestreo histórico de métricas.

---
## 4. Ejecución del proyecto

1. Instalacion de dependencias.

```bash
  pip install -r requirements.txt
```

2. Levantar el servidor.

```bash
uvicorn app.main:app --reload
```
La API quedará disponible, por defecto, en:
http://127.0.0.1:8000

Documentación interactiva (Swagger):
http://127.0.0.1:8000/docs

---
## 5. Endpoints principales

### Métricas de sistema y procesos
- `GET /metrics/system`: Obtiene métricas actuales de CPU, memoria, E/S de disco y red del sistema.
- `GET /metrics/process/{pid}`: Obtiene métricas actuales de un proceso específico (por PID).
- `GET /metrics/system/history`: Obtiene el histórico de métricas de sistema.
- `GET /metrics/system/summary`: Obtiene un resumen estadístico (mín, máx, media) de las métricas de sistema en el histórico.
- `GET /metrics/process/{pid}/history`: Obtiene el histórico de métricas de un proceso específico (por PID).
- `GET /metrics/process/{pid}/summary`: Obtiene un resumen estadístico (mín, máx, media) de las métricas de un proceso específico en el histórico. 
- `GET /metrics/processes`: Lista los PIDs de los procesos actualmente monitorizados en el histórico.
- `GET /metrics/processes/summary`: Obtiene un resumen estadístico (mín, máx, media) de las métricas de todos los procesos monitorizados en el histórico.
- `GET /metrics/processes/history`: Obtiene el histórico de métricas de todos los procesos monitorizados en el histórico.

### Perfilado de funciones
- `GET /profile/targets`: Lista las funciones registradas para perfilado.
- `POST /profile/run`: Ejecuta y perfila una función registrada (modo estándar).
- `POST /profile/run_detailed`: Ejecuta y perfila una función registrada (modo detallado).
- `POST /profile/register`: Registra una función para perfilado (modo estándar).
- `POST /profile/register_detailed`: Registra una función para perfilado (modo detallado).
- `GET /profile/registered`: Lista las funciones registradas para perfilado (modo estándar).
- `GET /profile/registered_detailed`: Lista las funciones registradas para perfilado (modo detallado).
- `POST /simulate_work`: Simula trabajo en CPU y memoria (para pruebas).
- `GET /health`: Verifica el estado de la API.
- `GET /`: Página de bienvenida.

---
## 6.Registro de nuevas funciones para perfilado

Para perfilar funciones reales de tu aplicación:

1. Define tu función en Python, con firma def mi_funcion(): ... (sin parámetros).
2. Regístrala en ProfilingTargetRegistry (por ahora, en profiler_service.py):
```python
from app.services.profiler_service import _registry  # o una función de registro explícita

def mi_funcion():
    # lógica de negocio que quieres analizar
    ...

_registry.register("mi_funcion", mi_funcion)
```
3. Luego podrás perfilarla vía API:
```
  POST /profile/run
  {
    "target_name": "mi_funcion",
    "runs": 5,
    "max_seconds": 10.0
  }
```

---
## 7. Consideraciones de diseño y buenas practicas

- **Separación de responsabilidades (SRP)**

    -   Los services no saben nada de HTTP; solo exponen lógica de negocio.

    -   Los routers solo gestionan HTTP (parámetros, respuestas, códigos de error) y delegan en servicios.


- **Inversión de dependencias**

    -   Los routers obtienen instancias de servicios mediante Depends(...).

    -   Si en el futuro se desea cambiar la implementación (p. ej. persistir el histórico en una base de datos), se puede hacer sin cambiar los endpoints.


- **Seguridad**

    -   Deliberadamente no se ejecuta código arbitrario enviado por el cliente.

    -   El perfilado opera sobre un registro controlado de funciones internas.


- **Extensibilidad**

    Es sencillo:

    -   añadir nuevos tipos de métricas,

    -   extender los resúmenes históricos,

    -   registrar nuevas funciones a perfilar,

    -   agregar autenticación en el futuro.

---
## 8. Posibles mejoras futuras

-   Añadir tests unitarios para MetricsService, MetricsHistoryService y ProfilerService.

-   Implementar un mecanismo de autenticación/autorización (API key, JWT, etc.).

-   Persistir el histórico de métricas en una base de datos o solución de time-series.

-   Añadir una pequeña interfaz web o dashboard que consuma esta API.

---
