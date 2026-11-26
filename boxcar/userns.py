"""
User Namespace Subsystem for Boxcar.
Manages UID and GID mapping translations for rootless and user-isolated container sandboxes.
Follows Linux kernel /proc/[pid]/uid_map specification and OCI Runtime Spec.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class IDMapping:
    container_id: int
    host_id: int
    size: int

    def to_proc_entry(self) -> str:
        """Formats mapping as a line for /proc/[pid]/uid_map or gid_map."""
        return f"{self.container_id} {self.host_id} {self.size}"

    def to_oci(self) -> Dict[str, int]:
        """Formats mapping according to OCI specification."""
        return {
            "containerID": self.container_id,
            "hostID": self.host_id,
            "size": self.size,
        }


class UserNamespaceSpec:
    """Manages container user and group namespace mapping configurations."""

    def __init__(
        self,
        uid_mappings: Optional[List[IDMapping]] = None,
        gid_mappings: Optional[List[IDMapping]] = None,
    ) -> None:
        self.uid_mappings: List[IDMapping] = uid_mappings or []
        self.gid_mappings: List[IDMapping] = gid_mappings or []

    def add_uid_mapping(self, container_id: int, host_id: int, size: int = 1) -> None:
        if container_id < 0 or host_id < 0 or size <= 0:
            raise ValueError("IDs must be non-negative and size must be positive")
        self.uid_mappings.append(IDMapping(container_id, host_id, size))

    def add_gid_mapping(self, container_id: int, host_id: int, size: int = 1) -> None:
        if container_id < 0 or host_id < 0 or size <= 0:
            raise ValueError("IDs must be non-negative and size must be positive")
        self.gid_mappings.append(IDMapping(container_id, host_id, size))

    def map_uid_to_host(self, container_uid: int) -> Optional[int]:
        for m in self.uid_mappings:
            if m.container_id <= container_uid < m.container_id + m.size:
                return m.host_id + (container_uid - m.container_id)
        return None

    def map_uid_to_container(self, host_uid: int) -> Optional[int]:
        for m in self.uid_mappings:
            if m.host_id <= host_uid < m.host_id + m.size:
                return m.container_id + (host_uid - m.host_id)
        return None

    def map_gid_to_host(self, container_gid: int) -> Optional[int]:
        for m in self.gid_mappings:
            if m.container_id <= container_gid < m.container_id + m.size:
                return m.host_id + (container_gid - m.container_id)
        return None

    def map_gid_to_container(self, host_gid: int) -> Optional[int]:
        for m in self.gid_mappings:
            if m.host_id <= host_gid < m.host_id + m.size:
                return m.container_id + (host_gid - m.host_id)
        return None

    def format_proc_uid_map(self) -> str:
        """Returns lines formatted for /proc/[pid]/uid_map."""
        return "\n".join(m.to_proc_entry() for m in self.uid_mappings)

    def format_proc_gid_map(self) -> str:
        """Returns lines formatted for /proc/[pid]/gid_map."""
        return "\n".join(m.to_proc_entry() for m in self.gid_mappings)

    def format_oci_spec(self) -> Dict[str, Any]:
        """Returns standard OCI linux namespace mapping spec."""
        return {
            "linux": {
                "uidMappings": [m.to_oci() for m in self.uid_mappings],
                "gidMappings": [m.to_oci() for m in self.gid_mappings],
            }
        }

    @classmethod
    def create_rootless_default(cls, host_uid: int = 1000, host_gid: int = 1000) -> UserNamespaceSpec:
        """Convenience constructor mapping container root (UID/GID 0) to unprivileged host user."""
        spec = cls()
        spec.add_uid_mapping(container_id=0, host_id=host_uid, size=1)
        spec.add_gid_mapping(container_id=0, host_id=host_gid, size=1)
        return spec
