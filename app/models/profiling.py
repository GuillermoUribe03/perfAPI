"""
Modelos Pydantic relacionados con el perfilado de funciones.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ProfileRunRequest(BaseModel):
    """
    Petición para ejecutar un perfilado de una función registrada.
    """
    target_name: str = Field(
        ...,
        description="Nombre de la función registrada que se desea perfilar.",
    )
    runs: int = Field(
        1,
        ge=1,
        le=100,
        description="Número de veces que se ejecutará la función durante el perfilado.",
    )
    max_seconds: float = Field(
        10.0,
        gt=0,
        description="Tiempo máximo (aproximado) para el perfilado, en segundos.",
    )


class ProfileStats(BaseModel):
    """
    Resultado de un perfilado.

    Incluye un identificador del perfilado, información del target
    y la salida en texto de pstats.
    """
    profile_id: str = Field(..., description="Identificador único del perfilado.")
    target_name: str = Field(..., description="Nombre de la función perfilada.")
    runs_executed: int = Field(..., description="Número real de ejecuciones realizadas.")
    total_seconds: float = Field(..., description="Tiempo total invertido en el perfilado.")
    stats_text: str = Field(
        ..., description="Salida de pstats con las funciones ordenadas por tiempo acumulado."
    )


class ResourceUsageSample(BaseModel):
    """
    Muestra del uso de recursos del proceso alrededor de la ejecución de una función.

    Mide memoria RSS y deltas de bytes leídos/escritos a nivel de proceso
    durante una ejecución concreta del target perfilado.
    """
    run_index: int = Field(..., description="Índice (0-based) de la ejecución dentro del perfilado.")
    mem_rss_before: int = Field(..., description="Memoria RSS antes de ejecutar la función (bytes).")
    mem_rss_after: int = Field(..., description="Memoria RSS después de ejecutar la función (bytes).")
    mem_rss_delta: int = Field(..., description="Diferencia mem_rss_after - mem_rss_before (bytes).")
    read_bytes_delta: Optional[int] = Field(
        None,
        description="Diferencia en bytes leídos por el proceso durante la ejecución, si está disponible.",
    )
    write_bytes_delta: Optional[int] = Field(
        None,
        description="Diferencia en bytes escritos por el proceso durante la ejecución, si está disponible.",
    )


class ProfileStatsDetailed(ProfileStats):
    """
    Resultado extendido de un perfilado, incluyendo muestras de uso de recursos.
    """
    resource_samples: List[ResourceUsageSample] = Field(
        ...,
        description="Lista de muestras de uso de recursos por cada ejecución del target.",
    )