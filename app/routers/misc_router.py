"""
Router con endpoints auxiliares:
- /health: verificación de salud.
- /simulate_work: pequeña carga CPU-bound para pruebas.
- /: información básica de la API.
"""

import time

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(tags=["misc"])


class HealthResponse(BaseModel):
    status: str
    time: float


class SimulateWorkResponse(BaseModel):
    work_ms_requested: int
    work_ms_actual: int
    iterations: int


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """
    Endpoint de salud simple para verificar que la API está viva.
    """
    return HealthResponse(status="ok", time=time.time())


@router.get("/simulate_work", response_model=SimulateWorkResponse)
def simulate_work(
    work_ms: int = Query(200, ge=1, le=60_000, description="Duración aproximada de trabajo en ms."),
) -> SimulateWorkResponse:
    """
    Simula una carga de trabajo CPU-bound durante aproximadamente work_ms milisegundos.
    Útil para probar el impacto de la carga en las métricas del sistema.
    """
    t0 = time.time()
    end = t0 + (work_ms / 1000.0)
    iterations = 0

    while time.time() < end:
        iterations += 1

    t1 = time.time()
    actual_ms = int((t1 - t0) * 1000)

    return SimulateWorkResponse(
        work_ms_requested=work_ms,
        work_ms_actual=actual_ms,
        iterations=iterations,
    )


@router.get("/")
def root():
    """
    Información básica de la API y endpoints principales.
    """
    return {
        "title": "PerfAPI",
        "version": "1.0.0",
        "description": "API para métricas de rendimiento y perfilado de funciones registradas.",
        "endpoints": {
            "system_metrics": "/metrics/system",
            "process_metrics": "/metrics/process/{pid}",
            "profile_targets": "/profile/targets",
            "run_profile": "/profile/run",
            "simulate_work": "/simulate_work",
            "health": "/health",
        },
        "note": (
            "Para perfilar funciones de tu aplicación, regístralas en "
            "ProfilingTargetRegistry (por ejemplo en el arranque del servicio)."
        ),
    }