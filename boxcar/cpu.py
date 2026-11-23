"""
Linux Cgroup v2 CPU Bandwidth and Quota Subsystem for Boxcar.
Calculates cpu.max quotas and periods based on millicores or fractional CPUs.
"""

from __future__ import annotations
from typing import Tuple


DEFAULT_PERIOD_US = 100_000  # 100ms in microseconds (standard Linux cgroup v2 default)


class CPUBandwidthQuota:
    """
    Manages CPU quota calculation and validation for container cgroups.
    cpu.max format in cgroup v2: "<quota> <period>"
    """

    def __init__(self, cpus: float = 1.0, period_us: int = DEFAULT_PERIOD_US) -> None:
        if cpus <= 0:
            raise ValueError(f"CPU count must be strictly positive, got {cpus}")
        if period_us < 1000 or period_us > 1_000_000:
            raise ValueError(f"Period must be in [1000, 1000000] microseconds, got {period_us}")
        self.cpus = float(cpus)
        self.period_us = int(period_us)

    @property
    def quota_us(self) -> int:
        """Returns quota in microseconds allocated per period."""
        return int(self.cpus * self.period_us)

    def to_cgroup_max_spec(self) -> str:
        """Returns string format for cgroup v2 cpu.max interface."""
        return f"{self.quota_us} {self.period_us}"

    @classmethod
    def from_millicores(cls, millicores: int, period_us: int = DEFAULT_PERIOD_US) -> CPUBandwidthQuota:
        """Constructs CPU quota from millicores (e.g. 500m -> 0.5 CPU)."""
        if millicores <= 0:
            raise ValueError(f"Millicores must be strictly positive, got {millicores}")
        return cls(cpus=millicores / 1000.0, period_us=period_us)

    @classmethod
    def parse_cpu_max(cls, raw: str) -> Tuple[int, int]:
        """Parses a raw cpu.max cgroup file content like '200000 100000' or 'max 100000'."""
        parts = raw.strip().split()
        if len(parts) != 2:
            raise ValueError(f"Invalid cpu.max format: '{raw}'")
        quota_str, period_str = parts
        period = int(period_str)
        quota = -1 if quota_str == "max" else int(quota_str)
        return quota, period
