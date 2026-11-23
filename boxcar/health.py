"""
Container Healthcheck Probe Runner for Boxcar.
Supports exec probes with timeouts, consecutive retries, and status lifecycle management.
"""

from __future__ import annotations
import subprocess
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class HealthStatus(str, Enum):
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class HealthCheckConfig:
    def __init__(
        self,
        command: List[str],
        interval_sec: float = 30.0,
        timeout_sec: float = 5.0,
        retries: int = 3,
        start_period_sec: float = 0.0,
    ) -> None:
        if not command:
            raise ValueError("HealthCheck command cannot be empty")
        self.command = command
        self.interval_sec = interval_sec
        self.timeout_sec = timeout_sec
        self.retries = retries
        self.start_period_sec = start_period_sec


class HealthCheckRunner:
    def __init__(self, config: HealthCheckConfig, executor: Optional[Callable[[List[str], float], int]] = None) -> None:
        self.config = config
        self.executor = executor or self._default_exec
        self.status = HealthStatus.STARTING
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.history: List[Dict[str, Any]] = []

    def _default_exec(self, cmd: List[str], timeout: float) -> int:
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
            return res.returncode
        except subprocess.TimeoutExpired:
            return -1
        except Exception:
            return 1

    def run_probe(self) -> HealthStatus:
        """Executes a single health check probe and updates internal status."""
        start_t = time.time()
        exit_code = self.executor(self.config.command, self.config.timeout_sec)
        duration = time.time() - start_t
        success = (exit_code == 0)

        if success:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            self.status = HealthStatus.HEALTHY
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            if self.consecutive_failures >= self.config.retries:
                self.status = HealthStatus.UNHEALTHY

        self.history.append({
            "timestamp": start_t,
            "duration": duration,
            "exit_code": exit_code,
            "status": self.status.value,
        })
        return self.status
