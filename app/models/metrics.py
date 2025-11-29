"""
Modelos Pydantic relacionados con métricas de sistema y procesos.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SystemMetrics(BaseModel):
    """
    Métricas globales del sistema.

    Incluye información de CPU, memoria, disco y red.
    Algunos campos son opcionales para permitir que el cliente
    seleccione un subconjunto de parámetros a medir.
    """
    timestamp: float = Field(..., description="Marca de tiempo UNIX (segundos).")

    cpu_total_percent: Optional[float] = Field(
        None,
        description="Uso total de CPU en porcentaje, si se ha solicitado.",
    )
    cpu_per_core_percent: Optional[List[float]] = Field(
        None,
        description="Uso de CPU por núcleo, en porcentaje, si se ha solicitado.",
    )

    memory: Optional[Dict[str, Any]] = Field(
        None,
        description="Estadísticas de memoria virtual (psutil.virtual_memory()), si se han solicitado.",
    )
    disk_io: Optional[Dict[str, Any]] = Field(
        None,
        description="Estadísticas globales de E/S de disco (psutil.disk_io_counters()), si se han solicitado.",
    )
    net_io: Optional[Dict[str, Any]] = Field(
        None,
        description="Estadísticas globales de E/S de red (psutil.net_io_counters()), si se han solicitado.",
    )


class ProcessMetrics(BaseModel):
    """
    Métricas de un proceso específico.
    """
    timestamp: float = Field(..., description="Marca de tiempo UNIX (segundos).")
    pid: int = Field(..., description="Identificador del proceso.")
    name: str = Field(..., description="Nombre del proceso.")
    cmdline: List[str] = Field(..., description="Línea de comandos que inició el proceso.")
    cpu_percent: float = Field(..., description="Uso de CPU del proceso en porcentaje.")
    memory_info: Dict[str, Any] = Field(
        ..., description="Información de memoria del proceso (psutil.Process.memory_info())."
    )
    io_counters: Optional[Dict[str, Any]] = Field(
        None,
        description="Contadores de E/S del proceso, si están disponibles "
                    "(psutil.Process.io_counters()).",
    )
    num_threads: int = Field(..., description="Número de hilos que tiene el proceso.")


class SystemMetricsHistory(BaseModel):
    """
    Colección de muestras históricas de métricas de sistema.
    """
    samples: List[SystemMetrics] = Field(
        ...,
        description="Lista ordenada cronológicamente de muestras de métricas de sistema.",
    )


class SystemMetricsSummary(BaseModel):
    """
    Resumen estadístico simple de las métricas de sistema en una ventana temporal.
    """
    window_seconds: float = Field(
        ...,
        description="Ventana de tiempo considerada para el resumen, en segundos.",
    )
    sample_count: int = Field(
        ...,
        description="Número de muestras utilizadas en el resumen.",
    )
    cpu_total_percent_avg: Optional[float] = Field(
        None,
        description="Promedio del uso total de CPU en la ventana, si hay datos.",
    )
    cpu_total_percent_max: Optional[float] = Field(
        None,
        description="Máximo uso total de CPU observado en la ventana, si hay datos.",
    )
    cpu_total_percent_min: Optional[float] = Field(
        None,
        description="Mínimo uso total de CPU observado en la ventana, si hay datos.",
    )