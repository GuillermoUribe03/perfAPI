"""
Servicio para mantener un histórico de métricas de sistema.

Utiliza un hilo en background que, periódicamente, toma muestras de
SystemMetrics usando MetricsService y las almacena en memoria en una
estructura acotada (deque).
"""

from collections import deque
from threading import Event, Thread
from time import time
from typing import Deque, List, Optional
import logging

from app.models.metrics import SystemMetrics, SystemMetricsSummary
from app.services.metrics_service import MetricsService, get_metrics_service

logger = logging.getLogger(__name__)


class MetricsHistoryService:
    """
    Servicio que mantiene un histórico acotado de métricas de sistema.

    - Usa un hilo daemon que ejecuta un bucle de muestreo.
    - Almacena como máximo `max_samples` muestras.
    - Permite recuperar muestras recientes y un resumen simple.
    """

    def __init__(
        self,
        metrics_service: MetricsService,
        sampling_interval_seconds: float = 5.0,
        max_samples: int = 600,
    ) -> None:
        self._metrics_service = metrics_service
        self._sampling_interval_seconds = max(0.5, sampling_interval_seconds)
        self._samples: Deque[SystemMetrics] = deque(maxlen=max_samples)

        self._stop_event = Event()
        self._thread: Optional[Thread] = None

    def start(self) -> None:
        """
        Inicia el hilo de muestreo en background si no está ya activo.
        """
        if self._thread is not None and self._thread.is_alive():
            logger.info("MetricsHistoryService ya estaba en ejecución.")
            return

        logger.info("Iniciando MetricsHistoryService (intervalo=%.2fs)...",
                    self._sampling_interval_seconds)
        self._stop_event.clear()
        self._thread = Thread(
            target=self._run,
            name="metrics-history-sampler",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """
        Solicita la detención del hilo de muestreo.
        """
        logger.info("Deteniendo MetricsHistoryService...")
        self._stop_event.set()

    def _run(self) -> None:
        """
        Bucle principal del hilo de muestreo.
        """
        while not self._stop_event.is_set():
            try:
                metrics = self._metrics_service.get_system_metrics()
                self._samples.append(metrics)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Error tomando muestra de métricas: %s", exc)
            # Espera respetando el evento de parada
            self._stop_event.wait(self._sampling_interval_seconds)

    def get_recent_samples(self, window_seconds: float) -> List[SystemMetrics]:
        """
        Devuelve las muestras tomadas en los últimos `window_seconds` segundos.
        """
        if window_seconds <= 0:
            return []

        cutoff = time() - window_seconds
        return [sample for sample in self._samples if sample.timestamp >= cutoff]

    def get_summary(self, window_seconds: float) -> SystemMetricsSummary:
        """
        Devuelve un resumen sencillo de las métricas en la ventana indicada.

        Actualmente resume solo cpu_total_percent (promedio, máximo y mínimo),
        pero se podría extender para considerar memoria, E/S, etc.
        """
        samples = self.get_recent_samples(window_seconds)
        count = len(samples)

        if count == 0:
            return SystemMetricsSummary(
                window_seconds=window_seconds,
                sample_count=0,
                cpu_total_percent_avg=None,
                cpu_total_percent_max=None,
                cpu_total_percent_min=None,
            )

        cpu_values = [
            s.cpu_total_percent for s in samples if s.cpu_total_percent is not None
        ]

        if not cpu_values:
            avg = max_v = min_v = None
        else:
            avg = sum(cpu_values) / len(cpu_values)
            max_v = max(cpu_values)
            min_v = min(cpu_values)

        return SystemMetricsSummary(
            window_seconds=window_seconds,
            sample_count=count,
            cpu_total_percent_avg=avg,
            cpu_total_percent_max=max_v,
            cpu_total_percent_min=min_v,
        )


# Instancia global del histórico, reutilizando el MetricsService existente
metrics_history_service = MetricsHistoryService(get_metrics_service())


def get_metrics_history_service() -> MetricsHistoryService:
    """
    Función de dependencia para inyectar MetricsHistoryService en routers.
    """
    return metrics_history_service