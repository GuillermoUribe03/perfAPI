"""
Router con endpoints para el perfilado de funciones registradas.
"""

from typing import List

from fastapi import APIRouter, Depends

from app.models.profiling import (
    ProfileRunRequest,
    ProfileStats,
    ProfileStatsDetailed,
)
from app.services.profiler_service import (
    ProfilerService,
    ProfilingTargetRegistry,
    get_profiler_service,
    get_profiling_registry,
)

router = APIRouter(
    prefix="/profile",
    tags=["profiling"],
)


@router.get("/targets", response_model=List[str])
def list_profile_targets(
    registry: ProfilingTargetRegistry = Depends(get_profiling_registry),
) -> List[str]:
    """
    Lista los nombres de todas las funciones registradas para perfilado.
    """
    return registry.list_targets()


@router.post("/run", response_model=ProfileStats)
def run_profile(
    req: ProfileRunRequest,
    service: ProfilerService = Depends(get_profiler_service),
) -> ProfileStats:
    """
    Ejecuta un perfilado cProfile estándar sobre la función indicada en la petición.
    """
    return service.profile_target(req)


@router.post("/run_detailed", response_model=ProfileStatsDetailed)
def run_profile_detailed(
    req: ProfileRunRequest,
    service: ProfilerService = Depends(get_profiler_service),
) -> ProfileStatsDetailed:
    """
    Ejecuta un perfilado cProfile extendido sobre la función indicada,
    incluyendo muestras de uso de memoria y E/S por ejecución.
    """
    return service.profile_target_detailed(req)