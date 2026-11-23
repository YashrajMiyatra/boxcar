"""
Lifecycle Manager for Boxcar Containers.
Handles graceful termination with SIGTERM and timeout escalation to SIGKILL.
"""

from __future__ import annotations
import os
import signal
import time
from typing import Callable, Optional


class LifecycleManager:
    """Manages process termination signals and escalation timeouts."""

    def __init__(
        self,
        kill_fn: Optional[Callable[[int, int], None]] = None,
        is_alive_fn: Optional[Callable[[int], bool]] = None,
    ) -> None:
        self.kill_fn = kill_fn or os.kill
        self.is_alive_fn = is_alive_fn or self._default_is_alive

    def _default_is_alive(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def stop_container(
        self,
        pid: int,
        grace_period_sec: float = 10.0,
        poll_interval_sec: float = 0.1,
    ) -> str:
        """
        Sends SIGTERM to process. If process is still alive after grace_period_sec,
        escalates to SIGKILL.
        Returns: 'terminated_gracefully', 'killed_forcefully', or 'already_stopped'
        """
        if not self.is_alive_fn(pid):
            return "already_stopped"

        try:
            self.kill_fn(pid, signal.SIGTERM)
        except ProcessLookupError:
            return "already_stopped"

        start_t = time.time()
        while time.time() - start_t < grace_period_sec:
            if not self.is_alive_fn(pid):
                return "terminated_gracefully"
            time.sleep(poll_interval_sec)

        if self.is_alive_fn(pid):
            try:
                self.kill_fn(pid, signal.SIGKILL)
            except ProcessLookupError:
                return "terminated_gracefully"
            return "killed_forcefully"

        return "terminated_gracefully"
