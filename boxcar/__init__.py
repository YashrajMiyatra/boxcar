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
]
