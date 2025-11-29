"""
Servicio responsable de obtener métricas del sistema y de procesos.

Encapsula psutil para que el resto de la aplicación no dependa
directamente de esta librería (principio de inversión de dependencias).
"""

from time import time

import psutil
from fastapi import HTTPException

from app.models.metrics import SystemMetrics, ProcessMetrics


class MetricsService:
    """
    Proporciona operaciones de lectura de métricas.

    Esta clase no sabe nada de HTTP ni de FastAPI, solo de "negocio".
    """

    def get_system_metrics(
        self,
        include_cpu: bool = True,
        include_memory: bool = True,
        include_disk_io: bool = True,
        include_net_io: bool = True,
        cpu_interval: float = 0.3,
    ) -> SystemMetrics:
        """
        Devuelve un snapshot de las métricas globales del sistema.

        Los parámetros permiten seleccionar un subconjunto acotado de métricas
        a calcular, para reducir coste y alinearse con lo que el cliente necesita.
        """
        timestamp = time()

        cpu_total = None
        cpu_per_core = None
        memory = None
        disk_io = None
        net_io = None

        # CPU
        if include_cpu:
            # psutil.cpu_percent con intervalo para obtener una medida reciente
            interval = max(0.0, cpu_interval)
            cpu_total = psutil.cpu_percent(interval=interval)
            # Segundo muestreo: por núcleo, reutilizando la ventana de referencia
            cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)

        # Memoria
        if include_memory:
            memory = psutil.virtual_memory()._asdict()

        # Disco
        if include_disk_io:
            disk_io = psutil.disk_io_counters()._asdict()

        # Red
        if include_net_io:
            net_io = psutil.net_io_counters()._asdict()

        return SystemMetrics(
            timestamp=timestamp,
            cpu_total_percent=cpu_total,
            cpu_per_core_percent=cpu_per_core,
            memory=memory,
            disk_io=disk_io,
            net_io=net_io,
        )

    def get_process_metrics(self, pid: int) -> ProcessMetrics:
        """
        Devuelve métricas detalladas de un proceso específico.

        Lanza HTTPException 404 si el PID no existe.
        """
        if not psutil.pid_exists(pid):
            raise HTTPException(status_code=404, detail=f"PID {pid} no encontrado")

        timestamp = time()
        proc = psutil.Process(pid)

        cpu_usage = proc.cpu_percent(interval=0.2)
        memory_info = proc.memory_info()._asdict()
        io_counters = proc.io_counters()._asdict() if proc.io_counters() else None

        return ProcessMetrics(
            timestamp=timestamp,
            pid=pid,
            name=proc.name(),
            cmdline=proc.cmdline(),
            cpu_percent=cpu_usage,
            memory_info=memory_info,
            io_counters=io_counters,
            num_threads=proc.num_threads(),
        )


# Instancia "singleton" sencilla y función de dependencia para FastAPI
_metrics_service = MetricsService()


def get_metrics_service() -> MetricsService:
    """
    Función usada por FastAPI para inyectar MetricsService
    mediante Depends().
    """
    return _metrics_service