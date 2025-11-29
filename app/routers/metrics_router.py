"""
Router con endpoints relacionados con métricas de rendimiento
del sistema y de procesos concretos.
"""

from fastapi import APIRouter, Depends, Query

from app.models.metrics import (
    SystemMetrics,
    ProcessMetrics,
    SystemMetricsHistory,
    SystemMetricsSummary,
)
from app.services.metrics_service import MetricsService, get_metrics_service
from app.services.metrics_history_service import (
    MetricsHistoryService,
    get_metrics_history_service,
)

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
)


@router.get("/system", response_model=SystemMetrics)
def read_system_metrics(
    include_cpu: bool = Query(
        True,
        description="Incluir métricas de CPU (total y por núcleo).",
    ),
    include_memory: bool = Query(
        True,
        description="Incluir métricas de memoria virtual.",
    ),
    include_disk_io: bool = Query(
        True,
        description="Incluir métricas de E/S de disco.",
    ),
    include_net_io: bool = Query(
        True,
        description="Incluir métricas de E/S de red.",
    ),
    cpu_interval: float = Query(
        0.3,
        ge=0.0,
        le=5.0,
        description="Intervalo en segundos para muestrear CPU. 0.0 usa la ventana previa.",
    ),
    service: MetricsService = Depends(get_metrics_service),
) -> SystemMetrics:
    """
    Devuelve un snapshot de las métricas globales del sistema.

    El cliente puede seleccionar qué parámetros incluir, dentro de un
    conjunto acotado (CPU, memoria, E/S) y ajustar el intervalo de muestreo
    de la CPU.
    """
    return service.get_system_metrics(
        include_cpu=include_cpu,
        include_memory=include_memory,
        include_disk_io=include_disk_io,
        include_net_io=include_net_io,
        cpu_interval=cpu_interval,
    )


@router.get("/process/{pid}", response_model=ProcessMetrics)
def read_process_metrics(
    pid: int,
    service: MetricsService = Depends(get_metrics_service),
) -> ProcessMetrics:
    """
    Devuelve métricas detalladas de un proceso específico identificado por su PID.
    """
    return service.get_process_metrics(pid)


@router.get("/system/history", response_model=SystemMetricsHistory)
def read_system_metrics_history(
    window_seconds: float = Query(
        60.0,
        ge=1.0,
        le=3600.0,
        description="Ventana de tiempo a considerar hacia atrás, en segundos.",
    ),
    history_service: MetricsHistoryService = Depends(get_metrics_history_service),
) -> SystemMetricsHistory:
    """
    Devuelve el histórico de métricas de sistema en la ventana de tiempo indicada.
    """
    samples = history_service.get_recent_samples(window_seconds)
    return SystemMetricsHistory(samples=samples)


@router.get("/system/summary", response_model=SystemMetricsSummary)
def read_system_metrics_summary(
    window_seconds: float = Query(
        300.0,
        ge=1.0,
        le=3600.0,
        description="Ventana de tiempo a considerar hacia atrás, en segundos.",
    ),
    history_service: MetricsHistoryService = Depends(get_metrics_history_service),
) -> SystemMetricsSummary:
    """
    Devuelve un resumen estadístico simple de las métricas de sistema
    (actualmente CPU total) en la ventana indicada.
    """
    return history_service.get_summary(window_seconds)