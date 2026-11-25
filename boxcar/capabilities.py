"""
Linux Capabilities Security Subsystem for Boxcar Containers.
Configures OCI process.capabilities (bounding, effective, inheritable, permitted, ambient)
to enforce least-privilege security boundaries.
"""

from __future__ import annotations
from typing import Dict, List, Set, Any


class LinuxCapabilitiesSpec:
    """Manages container process capability bounding and effective sets."""

    DEFAULT_CAPABILITIES = [
        "CAP_CHOWN",
        "CAP_DAC_OVERRIDE",
        "CAP_FOWNER",
        "CAP_FSETID",
        "CAP_KILL",
        "CAP_SETGID",
        "CAP_SETUID",
        "CAP_SETPCAP",
        "CAP_NET_BIND_SERVICE",
        "CAP_NET_RAW",
        "CAP_SYS_CHROOT",
        "CAP_MKNOD",
        "CAP_AUDIT_WRITE",
        "CAP_SETFCAP",
    ]

    DANGEROUS_CAPABILITIES = {
        "CAP_SYS_ADMIN",
        "CAP_SYS_BOOT",
        "CAP_SYS_MODULE",
        "CAP_SYS_RAWIO",
        "CAP_SYS_PTRACE",
        "CAP_SYS_TIME",
    }

    def __init__(self, base_caps: List[str] = None) -> None:
        self.caps: Set[str] = set(base_caps if base_caps is not None else self.DEFAULT_CAPABILITIES)

    def add(self, *cap_names: str) -> None:
        """Adds capabilities to the container spec."""
        for c in cap_names:
            c = c.upper()
            if not c.startswith("CAP_"):
                c = f"CAP_{c}"
            self.caps.add(c)

    def drop(self, *cap_names: str) -> None:
        """Drops capabilities from the container spec."""
        for c in cap_names:
            c = c.upper()
            if not c.startswith("CAP_"):
                c = f"CAP_{c}"
            self.caps.discard(c)

    def drop_all(self) -> None:
        """Drops all capabilities (maximum isolation)."""
        self.caps.clear()

    def has_capability(self, cap: str) -> bool:
        c = cap.upper()
        if not c.startswith("CAP_"):
            c = f"CAP_{c}"
        return c in self.caps

    def format_oci_spec(self) -> Dict[str, List[str]]:
        """Formats into OCI process.capabilities specification."""
        sorted_caps = sorted(list(self.caps))
        return {
            "bounding": list(sorted_caps),
            "effective": list(sorted_caps),
            "inheritable": list(sorted_caps),
            "permitted": list(sorted_caps),
            "ambient": list(sorted_caps),
        }
