"""
Servicios de dominio de PerfAPI.

Aquí se reexportan los servicios principales y funciones de dependencia
para FastAPI.
"""

from .metrics_service import MetricsService, get_metrics_service
from .metrics_history_service import (
    MetricsHistoryService,
    metrics_history_service,
    get_metrics_history_service,
)
from .profiler_service import (
    ProfilingTargetRegistry,
    ProfilerService,
    get_profiler_service,
    get_profiling_registry,
)

__all__ = [
    "MetricsService",
    "get_metrics_service",
    "MetricsHistoryService",
    "metrics_history_service",
    "get_metrics_history_service",
    "ProfilingTargetRegistry",
    "ProfilerService",
    "get_profiler_service",
    "get_profiling_registry",
]