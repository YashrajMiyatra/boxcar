"""
Volume and Host Bind-Mount Manager for Boxcar Container Runtime.
Mounts host directories and files into container rootfs with permission modes.
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional


class VolumeMount:
    def __init__(self, host_path: str, container_path: str, readonly: bool = False) -> None:
        self.host_path = os.path.abspath(host_path)
        self.container_path = "/" + container_path.lstrip("/")
        self.readonly = readonly

    def to_mount_flags(self) -> List[str]:
        """Returns mount syscall option flags for bind mount."""
        flags = ["bind"]
        if self.readonly:
            flags.append("ro")
        return flags

    def __repr__(self) -> str:
        mode = "ro" if self.readonly else "rw"
        return f"VolumeMount({self.host_path}:{self.container_path}:{mode})"


class VolumeManager:
    """Manages volume validation and container rootfs path resolution."""

    def __init__(self, rootfs_path: str) -> None:
        self.rootfs = os.path.abspath(rootfs_path)
        self._mounts: List[VolumeMount] = []

    def add_mount(self, host_path: str, container_path: str, readonly: bool = False) -> VolumeMount:
        if not os.path.exists(host_path):
            raise FileNotFoundError(f"Host path does not exist: {host_path}")

        mount = VolumeMount(host_path, container_path, readonly)
        self._mounts.append(mount)
        return mount

    def resolve_target_path(self, mount: VolumeMount) -> str:
        """Returns the absolute path of the mount target inside the host rootfs mount tree."""
        rel_target = mount.container_path.lstrip("/")
        return os.path.join(self.rootfs, rel_target)

    def list_mounts(self) -> List[VolumeMount]:
        return list(self._mounts)
