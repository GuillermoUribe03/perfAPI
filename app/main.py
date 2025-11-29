"""
Punto de entrada de PerfAPI.

Se encarga de:
- Crear la instancia de FastAPI.
- Incluir los routers de métricas, perfilado y utilidades.
- Registrar manejadores de eventos de startup/shutdown para
  iniciar y detener el muestreo histórico de métricas.
"""

from fastapi import FastAPI

from app.routers.metrics_router import router as metrics_router
from app.routers.profiling_router import router as profiling_router
from app.routers.misc_router import router as misc_router
from app.services.metrics_history_service import metrics_history_service


def create_app() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI.

    Separar esta lógica en una función facilita las pruebas unitarias.
    """
    app = FastAPI(
        title="PerfAPI",
        version="1.1.0",
        description=(
            "API para analizar el rendimiento de aplicaciones. "
            "Permite consultar métricas de sistema/procesos, "
            "mantener un histórico de métricas y perfilar funciones "
            "registradas mediante cProfile."
        ),
    )

    # Registro de routers, agrupados por dominios
    app.include_router(metrics_router)
    app.include_router(profiling_router)
    app.include_router(misc_router)

    # Eventos de ciclo de vida: iniciar y detener el muestreo histórico
    def on_startup() -> None:
        metrics_history_service.start()

    def on_shutdown() -> None:
        metrics_history_service.stop()

    app.add_event_handler("startup", on_startup)
    app.add_event_handler("shutdown", on_shutdown)

    return app


# Instancia global utilizada por Uvicorn
app = create_app()