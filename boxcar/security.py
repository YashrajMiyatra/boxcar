"""
Container Security and Read-Only Root Filesystem Subsystem for Boxcar.
Enforces immutable container root filesystems (OCI root.readonly: true)
and validates that writes are isolated to explicit volume mounts or tmpfs.
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional, Any


class ReadOnlyRootfsSpec:
    """Manages read-only rootfs enforcement and writable exception zones."""

    DEFAULT_TMPFS = ["/tmp", "/run"]

    def __init__(
        self,
        readonly: bool = True,
        writable_mounts: Optional[List[str]] = None,
        allow_default_tmpfs: bool = True,
    ) -> None:
        self.readonly = readonly
        self.writable_mounts: List[str] = [
            os.path.abspath(m) for m in (writable_mounts or [])
        ]
        if allow_default_tmpfs and self.readonly:
            for t in self.DEFAULT_TMPFS:
                if t not in self.writable_mounts:
                    self.writable_mounts.append(t)

    def is_writable(self, path: str) -> bool:
        """Determines if a target path is writable under the security policy."""
        if not self.readonly:
            return True

        norm_path = os.path.abspath(path)
        for mount in self.writable_mounts:
            if norm_path == mount or norm_path.startswith(mount.rstrip("/") + "/"):
                return True
        return False

    def validate_write_attempt(self, path: str) -> None:
        """Raises PermissionError if writing to path is forbidden."""
        if not self.is_writable(path):
            raise PermissionError(
                f"EPERM: Read-only file system. Path '{path}' is not within a writable volume or tmpfs mount."
            )

    def format_oci_spec(self) -> Dict[str, Any]:
        """Returns standard OCI root configuration."""
        return {
            "root": {
                "readonly": self.readonly,
            },
            "writableMounts": list(self.writable_mounts),
        }
