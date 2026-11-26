"""
Cgroups v2 Process and Thread (pids.max) Subsystem for Boxcar Containers.
Restricts the maximum number of concurrent tasks inside a container cgroup
to protect against fork bombs and PID space starvation.
"""

from __future__ import annotations
import os
from typing import Dict, Union, Any


class PIDLimitSpec:
    """Manages cgroup v2 pids controller settings."""

    def __init__(self, limit: Union[int, str] = 1024) -> None:
        self.limit = self._validate_limit(limit)

    @classmethod
    def _validate_limit(cls, val: Union[int, str]) -> Union[int, str]:
        if isinstance(val, str):
            if val.strip().lower() == "max":
                return "max"
            try:
                val = int(val)
            except ValueError:
                raise ValueError(f"Invalid pid limit string: '{val}' (expected positive integer or 'max')")
        if not isinstance(val, int):
            raise TypeError(f"PID limit must be int or 'max', got {type(val).__name__}")
        if val <= 0:
            raise ValueError(f"PID limit must be positive, got {val}")
        return val

    def write_to_cgroup(self, cgroup_dir: str) -> None:
        """Writes limit to pids.max inside container cgroup directory."""
        target = os.path.join(cgroup_dir, "pids.max")
        with open(target, "w") as f:
            f.write(f"{self.limit}\n")

    def format_oci_spec(self) -> Dict[str, Any]:
        """Formats into standard OCI linux.resources.pids specification."""
        limit_val = -1 if self.limit == "max" else int(self.limit)
        return {
            "pids": {
                "limit": limit_val,
            }
        }
