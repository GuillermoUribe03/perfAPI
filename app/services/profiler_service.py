"""
Servicios relacionados con el perfilado de funciones.

Incluye:
- Registro de funciones "perfilables" (ProfilingTargetRegistry).
- Servicio de perfilado basado en cProfile (ProfilerService).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple
import cProfile
import io
import logging
import pstats
import time
import uuid

import psutil
from fastapi import HTTPException

from app.models.profiling import (
    ProfileRunRequest,
    ProfileStats,
    ProfileStatsDetailed,
    ResourceUsageSample,
)

logger = logging.getLogger(__name__)


class ProfilingTargetRegistry:
    """
    Registro de funciones que se pueden perfilar.

    La idea es que la propia aplicación registre aquí las funciones que
    tienen sentido para analizar rendimiento.
    """

    def __init__(self) -> None:
        self._targets: Dict[str, Callable[[], Any]] = {}

    def register(self, name: str, func: Callable[[], Any]) -> None:
        """
        Registra una nueva función perfilable.

        Si el nombre ya existe se sobrescribe, pero se deja constancia en logs.
        """
        if name in self._targets:
            logger.warning("La función '%s' ya estaba registrada; será sobrescrita.", name)

        self._targets[name] = func
        logger.info("Función '%s' registrada correctamente para perfilado.", name)

    def get(self, name: str) -> Callable[[], Any]:
        """
        Obtiene una función perfilable por nombre.

        Lanza HTTPException 404 si no se encuentra.
        """
        try:
            return self._targets[name]
        except KeyError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"No existe una función registrada con el nombre '{name}'.",
            ) from exc

    def list_targets(self) -> List[str]:
        """
        Lista alfabéticamente los nombres de todas las funciones registradas.
        """
        return sorted(self._targets.keys())


class ProfilerService:
    """
    Servicio responsable de ejecutar y perfilar funciones registradas.

    Encapsula cProfile y pstats para mantener la API de perfilado simple.
    """

    def __init__(self, registry: ProfilingTargetRegistry) -> None:
        self._registry = registry

    # -------------------- API pública --------------------

    def profile_target(self, req: ProfileRunRequest) -> ProfileStats:
        """
        Ejecuta un perfilado estándar (solo CPU/tiempo) sobre la función indicada.

        max_seconds se respeta de forma "suave": si la función se bloquea
        indefinidamente, este método no puede detenerla. Para timeouts duros
        habría que usar subprocesos.
        """
        target = self._registry.get(req.target_name)
        profiler = cProfile.Profile()
        profile_id = str(uuid.uuid4())

        logger.info(
            "Iniciando perfilado '%s' sobre '%s' (runs=%d, max_seconds=%.2f)...",
            profile_id,
            req.target_name,
            req.runs,
            req.max_seconds,
        )

        start = time.time()
        runs_executed = 0

        try:
            profiler.enable()
            for _ in range(req.runs):
                target()
                runs_executed += 1

                elapsed = time.time() - start
                if elapsed >= req.max_seconds:
                    logger.info(
                        "Límite de tiempo alcanzado (%.2fs) tras %d ejecuciones.",
                        req.max_seconds,
                        runs_executed,
                    )
                    break
        finally:
            profiler.disable()

        total_seconds, stats_text = self._finalize_profile(
            profiler, profile_id, req.target_name, runs_executed, start
        )

        return ProfileStats(
            profile_id=profile_id,
            target_name=req.target_name,
            runs_executed=runs_executed,
            total_seconds=total_seconds,
            stats_text=stats_text,
        )

    def profile_target_detailed(self, req: ProfileRunRequest) -> ProfileStatsDetailed:
        """
        Ejecuta un perfilado extendido, recogiendo además muestras de uso
        de memoria RSS y E/S a nivel de proceso por cada ejecución.

        max_seconds se respeta de forma "suave", igual que en profile_target().
        """
        target = self._registry.get(req.target_name)
        profiler = cProfile.Profile()
        profile_id = str(uuid.uuid4())
        proc = psutil.Process()  # Proceso actual (donde se ejecuta la función)

        logger.info(
            "Iniciando perfilado detallado '%s' sobre '%s' (runs=%d, max_seconds=%.2f)...",
            profile_id,
            req.target_name,
            req.runs,
            req.max_seconds,
        )

        start = time.time()
        runs_executed = 0
        resource_samples: List[ResourceUsageSample] = []

        try:
            profiler.enable()
            for i in range(req.runs):
                mem_before = proc.memory_info().rss
                io_before = proc.io_counters() if proc.io_counters() else None

                target()
                runs_executed += 1

                mem_after = proc.memory_info().rss
                io_after = proc.io_counters() if proc.io_counters() else None

                mem_delta = mem_after - mem_before
                read_delta = None
                write_delta = None

                if io_before and io_after:
                    read_delta = io_after.read_bytes - io_before.read_bytes
                    write_delta = io_after.write_bytes - io_before.write_bytes

                resource_samples.append(
                    ResourceUsageSample(
                        run_index=i,
                        mem_rss_before=mem_before,
                        mem_rss_after=mem_after,
                        mem_rss_delta=mem_delta,
                        read_bytes_delta=read_delta,
                        write_bytes_delta=write_delta,
                    )
                )

                elapsed = time.time() - start
                if elapsed >= req.max_seconds:
                    logger.info(
                        "Límite de tiempo alcanzado (%.2fs) tras %d ejecuciones.",
                        req.max_seconds,
                        runs_executed,
                    )
                    break
        finally:
            profiler.disable()

        total_seconds, stats_text = self._finalize_profile(
            profiler, profile_id, req.target_name, runs_executed, start
        )

        return ProfileStatsDetailed(
            profile_id=profile_id,
            target_name=req.target_name,
            runs_executed=runs_executed,
            total_seconds=total_seconds,
            stats_text=stats_text,
            resource_samples=resource_samples,
        )

    # -------------------- Helpers internos --------------------

    def _finalize_profile(
        self,
        profiler: cProfile.Profile,
        profile_id: str,
        target_name: str,
        runs_executed: int,
        start_time: float,
    ) -> Tuple[float, str]:
        """
        Genera el texto de estadísticas de cProfile y registra en logs
        el resultado global del perfilado.
        """
        total_seconds = time.time() - start_time

        buffer = io.StringIO()
        stats = pstats.Stats(profiler, stream=buffer).sort_stats("cumtime")
        stats.print_stats(40)  # Top 40 funciones
        stats_text = buffer.getvalue()

        logger.info(
            "Perfilado '%s' completado para '%s'. runs=%d, tiempo_total=%.3fs",
            profile_id,
            target_name,
            runs_executed,
            total_seconds,
        )

        return total_seconds, stats_text


# ---------------------------------------------------------------------------
# Funciones de ejemplo a perfilar
# ---------------------------------------------------------------------------

def _fibonacci_example() -> int:
    """
    Función de ejemplo que consume CPU calculando varios Fibonacci.
    """

    def fib(n: int) -> int:
        if n <= 1:
            return n
        return fib(n - 1) + fib(n - 2)

    total = 0
    for _ in range(26):
        total += fib(20)
    return total


def _io_simulation_example() -> None:
    """
    Función de ejemplo que simula pequeñas esperas de I/O.
    """
    for _ in range(5):
        time.sleep(0.05)

def _my_custom_task() -> None:
    """
    Función de ejemplo que mezcla trabajo de CPU y esperas simuladas de I/O.
    Sustituye esto por lógica real de tu aplicación cuando la tengas.
    """
    # CPU-bound simple
    total = 0
    for i in range(100_000):
        total += (i ** 2) % 97

    # I/O simulado con pequeñas pausas
    for _ in range(5):
        time.sleep(0.02)

    # Para no “optimizarla” completamente
    return total

# ---------------------------------------------------------------------------
# Instancias globales y dependencias para FastAPI
# ---------------------------------------------------------------------------

_registry = ProfilingTargetRegistry()
_profiler_service = ProfilerService(_registry)

# Registramos funciones de ejemplo; en un proyecto real aquí registrarías
# funciones propias de tu aplicación.
_registry.register("fib_example", _fibonacci_example)
_registry.register("io_example", _io_simulation_example)
_registry.register("my_custom_task", _my_custom_task)


def get_profiler_service() -> ProfilerService:
    """
    Dependencia de FastAPI para inyectar ProfilerService.
    """
    return _profiler_service


def get_profiling_registry() -> ProfilingTargetRegistry:
    """
    Dependencia de FastAPI para exponer el registro (solo lectura en routers).
    """
    return _registry