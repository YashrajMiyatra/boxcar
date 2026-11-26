"""
Boxcar: Lightweight Linux Container Runtime and OCI Image Puller.
"""

__version__ = "1.0.0"

from .registry import DockerRegistryClient
from .storage import ImageStore
from .runtime import ContainerRunner
from .health import HealthCheckConfig, HealthCheckRunner, HealthStatus
from .network import NetworkManager, NetworkConfig, VethPair
from .mount import VolumeMount, VolumeManager
from .lifecycle import LifecycleManager
from .cpu import CPUBandwidthQuota
from .memory import MemoryLimitSpec
from .env import EnvironmentInjector
from .oom import OOMScoreAdjustSpec
from .security import ReadOnlyRootfsSpec
from .seccomp import SeccompFilterSpec
from .capabilities import LinuxCapabilitiesSpec
from .sysctl import SysctlSpec
from .pids import PIDLimitSpec
from .userns import UserNamespaceSpec, IDMapping
from .apparmor import AppArmorProfileSpec, AppArmorRule
from .devices import DeviceCgroupSpec, DeviceRule

__all__ = [
    "DockerRegistryClient",
    "ImageStore",
    "ContainerRunner",
    "HealthCheckConfig",
    "HealthCheckRunner",
    "HealthStatus",
    "NetworkManager",
    "NetworkConfig",
    "VethPair",
    "VolumeMount",
    "VolumeManager",
    "LifecycleManager",
    "CPUBandwidthQuota",
    "MemoryLimitSpec",
    "EnvironmentInjector",
    "OOMScoreAdjustSpec",
    "ReadOnlyRootfsSpec",
    "SeccompFilterSpec",
    "LinuxCapabilitiesSpec",
    "SysctlSpec",
    "PIDLimitSpec",
    "UserNamespaceSpec",
    "IDMapping",
    "AppArmorProfileSpec",
    "AppArmorRule",
    "DeviceCgroupSpec",
    "DeviceRule",
]
