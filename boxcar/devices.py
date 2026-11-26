"""
Device Cgroup Subsystem for Boxcar.
Manages character and block device whitelisting and access control for Linux container sandboxes
complying with OCI Runtime Spec linux.resources.devices and cgroup v2 device controllers.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class DeviceRule:
    device_type: str  # 'c', 'b', 'a'
    major: Optional[int]
    minor: Optional[int]
    access: str  # subset of 'rwm'
    allow: bool = True

    def to_cgroup_line(self) -> str:
        maj = str(self.major) if self.major is not None and self.major >= 0 else "*"
        min_ = str(self.minor) if self.minor is not None and self.minor >= 0 else "*"
        return f"{self.device_type} {maj}:{min_} {self.access}"

    def to_oci(self) -> Dict[str, Any]:
        oci: Dict[str, Any] = {
            "allow": self.allow,
            "type": self.device_type,
            "access": self.access,
        }
        if self.major is not None and self.major >= 0:
            oci["major"] = self.major
        if self.minor is not None and self.minor >= 0:
            oci["minor"] = self.minor
        return oci


class DeviceCgroupSpec:
    """Manages container device access permissions and cgroup rules."""

    def __init__(self, default_allow: bool = False) -> None:
        self.default_allow = default_allow
        self.rules: List[DeviceRule] = []

    def add_rule(
        self,
        device_type: str,
        major: Optional[int],
        minor: Optional[int],
        access: str = "rwm",
        allow: bool = True,
    ) -> None:
        if device_type not in ("c", "b", "a"):
            raise ValueError(f"Invalid device type '{device_type}', must be 'c', 'b', or 'a'")
        for char in access:
            if char not in "rwm":
                raise ValueError(f"Invalid access mode '{char}', must be subset of 'rwm'")
        self.rules.append(DeviceRule(device_type, major, minor, access, allow))

    def is_allowed(self, device_type: str, major: int, minor: int, access_mode: str) -> bool:
        """Evaluates whether an access operation on a device is permitted."""
        for rule in reversed(self.rules):
            type_match = rule.device_type in ("a", device_type)
            maj_match = rule.major is None or rule.major < 0 or rule.major == major
            min_match = rule.minor is None or rule.minor < 0 or rule.minor == minor
            if type_match and maj_match and min_match:
                if all(c in rule.access for c in access_mode):
                    return rule.allow
        return self.default_allow

    def format_cgroup_allow_lines(self) -> List[str]:
        return [r.to_cgroup_line() for r in self.rules if r.allow]

    def format_cgroup_deny_lines(self) -> List[str]:
        return [r.to_cgroup_line() for r in self.rules if not r.allow]

    def format_oci_spec(self) -> Dict[str, Any]:
        return {
            "linux": {
                "resources": {
                    "devices": [r.to_oci() for r in self.rules]
                }
            }
        }

    @classmethod
    def create_default_devices(cls) -> DeviceCgroupSpec:
        """Creates standard secure default device permissions (/dev/null, zero, full, random, urandom, tty)."""
        spec = cls(default_allow=False)
        # Deny all first
        spec.add_rule(device_type="a", major=None, minor=None, access="rwm", allow=False)
        # /dev/null (c 1:3)
        spec.add_rule(device_type="c", major=1, minor=3, access="rwm", allow=True)
        # /dev/zero (c 1:5)
        spec.add_rule(device_type="c", major=1, minor=5, access="rwm", allow=True)
        # /dev/full (c 1:7)
        spec.add_rule(device_type="c", major=1, minor=7, access="rwm", allow=True)
        # /dev/random (c 1:8)
        spec.add_rule(device_type="c", major=1, minor=8, access="rm", allow=True)
        # /dev/urandom (c 1:9)
        spec.add_rule(device_type="c", major=1, minor=9, access="rm", allow=True)
        # /dev/tty (c 5:0)
        spec.add_rule(device_type="c", major=5, minor=0, access="rwm", allow=True)
        return spec
