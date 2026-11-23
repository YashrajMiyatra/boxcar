"""
Network Namespace and Virtual Ethernet (veth) Interface Manager for Boxcar.
Configures container network bridge attachment and private IPv4 allocation.
"""

from __future__ import annotations
import ipaddress
import re
from typing import Dict, List, Optional, Tuple


class NetworkConfig:
    def __init__(
        self,
        ip_address: str,
        gateway: str = "172.19.0.1",
        bridge: str = "boxcar0",
        subnet: str = "172.19.0.0/16",
    ) -> None:
        self.ip_address = str(ipaddress.IPv4Interface(ip_address))
        self.gateway = str(ipaddress.IPv4Address(gateway))
        self.bridge = bridge
        self.subnet = str(ipaddress.IPv4Network(subnet))

    def __repr__(self) -> str:
        return f"NetworkConfig(ip={self.ip_address}, gw={self.gateway}, br={self.bridge})"


class VethPair:
    def __init__(self, host_ifname: str, peer_ifname: str) -> None:
        self.host_ifname = host_ifname
        self.peer_ifname = peer_ifname

    def to_ip_link_args(self) -> List[str]:
        """Returns iproute2 command arguments to allocate the veth pair."""
        return ["ip", "link", "add", self.host_ifname, "type", "veth", "peer", "name", self.peer_ifname]


class NetworkManager:
    """Manages container network allocation and interface generation."""

    def __init__(self, bridge: str = "boxcar0", base_subnet: str = "172.19.0.0/16") -> None:
        self.bridge = bridge
        self.network = ipaddress.IPv4Network(base_subnet)
        self._allocated_ips: Dict[str, str] = {}

    def allocate_veth_pair(self, container_id: str) -> VethPair:
        """Generates deterministic, unique veth pair interface names (max 15 chars for Linux kernel)."""
        short_id = container_id[:8]
        host_if = f"veth_{short_id}"
        peer_if = f"ceth_{short_id}"
        return VethPair(host_ifname=host_if, peer_ifname=peer_if)

    def assign_ip(self, container_id: str, host_index: int) -> NetworkConfig:
        """Assigns an IPv4 address from the subnet to the given container."""
        # host 1 is gateway
        gateway_ip = str(self.network[1])
        container_ip = str(self.network[host_index])
        if host_index <= 1 or host_index >= self.network.num_addresses - 1:
            raise ValueError(f"Invalid host index {host_index} for subnet {self.network}")

        config = NetworkConfig(
            ip_address=f"{container_ip}/{self.network.prefixlen}",
            gateway=gateway_ip,
            bridge=self.bridge,
            subnet=str(self.network),
        )
        self._allocated_ips[container_id] = container_ip
        return config

    def release_ip(self, container_id: str) -> bool:
        if container_id in self._allocated_ips:
            del self._allocated_ips[container_id]
            return True
        return False
