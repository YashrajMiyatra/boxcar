"""
Linux Cgroup v2 Memory Limit Subsystem for Boxcar.
Parses human-readable memory strings (e.g. 512M, 2G) into byte quotas for memory.max and memory.high.
"""

from __future__ import annotations
import re
from typing import Optional


UNIT_MULTIPLIERS = {
    "b": 1,
    "k": 1024,
    "kb": 1024,
    "m": 1024 * 1024,
    "mb": 1024 * 1024,
    "g": 1024 * 1024 * 1024,
    "gb": 1024 * 1024 * 1024,
}


def parse_memory_string_to_bytes(spec: str) -> int:
    """Parses strings like '512m', '2GB', '65536' into integer byte values."""
    s = spec.strip().lower()
    if s == "max":
        return -1
    match = re.match(r"^(\d+)([a-z]*)$", s)
    if not match:
        raise ValueError(f"Invalid memory limit format: '{spec}'")
    val, unit = match.groups()
    num = int(val)
    if not unit:
        return num
    if unit not in UNIT_MULTIPLIERS:
        raise ValueError(f"Unknown memory unit: '{unit}'. Supported: B, K, M, G")
    return num * UNIT_MULTIPLIERS[unit]


class MemoryLimitSpec:
    """
    Manages cgroup v2 memory limits (memory.max and memory.high).
    """

    def __init__(self, limit_bytes: int, high_bytes: Optional[int] = None) -> None:
        if limit_bytes != -1 and limit_bytes <= 0:
            raise ValueError(f"Memory limit must be positive or -1 (max), got {limit_bytes}")
        self.limit_bytes = limit_bytes
        self.high_bytes = high_bytes

    def to_cgroup_max_spec(self) -> str:
        """Returns string format for cgroup v2 memory.max."""
        return "max" if self.limit_bytes == -1 else str(self.limit_bytes)

    @classmethod
    def from_string(cls, limit_str: str, high_str: Optional[str] = None) -> MemoryLimitSpec:
        limit_bytes = parse_memory_string_to_bytes(limit_str)
        high_bytes = parse_memory_string_to_bytes(high_str) if high_str else None
        return cls(limit_bytes=limit_bytes, high_bytes=high_bytes)
