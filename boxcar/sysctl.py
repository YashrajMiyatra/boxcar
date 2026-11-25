"""
Kernel Sysctl Configuration Subsystem for Boxcar Containers.
Configures OCI linux.sysctl key-value parameters for namespaced kernel tuning
(e.g., net.ipv4.ip_forward, net.core.somaxconn).
"""

from __future__ import annotations
from typing import Dict, Optional, Set


class SysctlSpec:
    """Manages container namespaced sysctl parameters according to OCI specification."""

    SAFE_SYSCTL_PREFIXES = (
        "net.ipv4.",
        "net.ipv6.",
        "net.core.",
        "kernel.shm",
        "kernel.msg",
        "kernel.sem",
        "fs.mqueue.",
    )

    def __init__(self, initial_params: Optional[Dict[str, str]] = None) -> None:
        self.params: Dict[str, str] = {}
        if initial_params:
            for k, v in initial_params.items():
                self.set_param(k, str(v))

    @classmethod
    def is_safe(cls, key: str) -> bool:
        """Determines if a sysctl parameter is namespaced and safe for container modification."""
        return any(key.startswith(prefix) for prefix in cls.SAFE_SYSCTL_PREFIXES)

    def set_param(self, key: str, value: str, enforce_safety: bool = True) -> None:
        """Sets a sysctl parameter, rejecting unsafe host-level parameters if enforce_safety is True."""
        key = key.strip()
        value = str(value).strip()
        if enforce_safety and not self.is_safe(key):
            raise ValueError(
                f"Sysctl '{key}' is not in a safe namespaced kernel domain (e.g. net.*, kernel.shm*)."
            )
        self.params[key] = value

    def get_param(self, key: str) -> Optional[str]:
        return self.params.get(key)

    def format_oci_spec(self) -> Dict[str, str]:
        """Formats parameters into standard OCI linux.sysctl dictionary."""
        return dict(self.params)
