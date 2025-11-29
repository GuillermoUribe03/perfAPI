"""
Routers de FastAPI agrupados por dominio:
- metrics_router: métricas de sistema y procesos.
- profiling_router: perfilado de funciones registradas.
- misc_router: endpoints auxiliares (/health, /simulate_work, /).
"""

from .metrics_router import router as metrics_router
from .profiling_router import router as profiling_router
from .misc_router import router as misc_router

__all__ = [
    "metrics_router",
    "profiling_router",
    "misc_router",
]