"""
POSIX Resource Limits Subsystem for Boxcar.
Manages process resource limits (rlimits) for container processes
complying with the OCI Runtime Specification process.rlimits schema.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


VALID_RLIMIT_TYPES = {
    "RLIMIT_CPU",
    "RLIMIT_FSIZE",
    "RLIMIT_DATA",
    "RLIMIT_STACK",
    "RLIMIT_CORE",
    "RLIMIT_RSS",
    "RLIMIT_NPROC",
    "RLIMIT_NOFILE",
    "RLIMIT_MEMLOCK",
    "RLIMIT_AS",
    "RLIMIT_LOCKS",
    "RLIMIT_SIGPENDING",
    "RLIMIT_MSGQUEUE",
    "RLIMIT_NICE",
    "RLIMIT_RTPRIO",
    "RLIMIT_RTTIME",
}


@dataclass
class RlimitEntry:
    limit_type: str
    soft: int
    hard: int

    def __post_init__(self) -> None:
        if self.limit_type not in VALID_RLIMIT_TYPES:
            raise ValueError(f"Invalid rlimit type: '{self.limit_type}'")
        if self.soft < 0 or self.hard < 0:
            raise ValueError("soft and hard limits must be non-negative integers")
        if self.soft > self.hard:
            raise ValueError(f"soft limit ({self.soft}) cannot exceed hard limit ({self.hard})")

    def to_oci(self) -> Dict[str, Any]:
        return {
            "type": self.limit_type,
            "soft": self.soft,
            "hard": self.hard,
        }


class RlimitsSpec:
    """Manages process resource limits for container sandboxes according to OCI specification."""

    def __init__(self) -> None:
        self.limits: Dict[str, RlimitEntry] = {}

    def set_limit(self, limit_type: str, soft: int, hard: int) -> None:
        entry = RlimitEntry(limit_type, soft, hard)
        self.limits[limit_type] = entry

    def get_limit(self, limit_type: str) -> Optional[RlimitEntry]:
        return self.limits.get(limit_type)

    def remove_limit(self, limit_type: str) -> bool:
        if limit_type in self.limits:
            del self.limits[limit_type]
            return True
        return False

    def to_oci(self) -> List[Dict[str, Any]]:
        return [entry.to_oci() for entry in self.limits.values()]

    @classmethod
    def from_oci(cls, oci_list: List[Dict[str, Any]]) -> RlimitsSpec:
        spec = cls()
        for item in oci_list:
            spec.set_limit(item["type"], item["soft"], item["hard"])
        return spec

    @classmethod
    def default_container_limits(cls) -> RlimitsSpec:
        """Returns standard recommended container isolation limits."""
        spec = cls()
        spec.set_limit("RLIMIT_NOFILE", 1024, 2048)
        spec.set_limit("RLIMIT_NPROC", 1024, 2048)
        spec.set_limit("RLIMIT_CORE", 0, 0)
        return spec
