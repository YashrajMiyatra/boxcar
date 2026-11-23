"""
Unit tests for Boxcar NetworkManager, VethPair allocation, and NetworkConfig validation.
"""

import unittest
from boxcar.network import NetworkManager, NetworkConfig, VethPair


class TestNetworkManager(unittest.TestCase):
    def setUp(self):
        self.mgr = NetworkManager(bridge="boxcar0", base_subnet="172.19.0.0/16")

    def test_veth_pair_naming_under_kernel_limit(self):
        veth = self.mgr.allocate_veth_pair("c_abcd1234efgh5678")
        self.assertEqual(veth.host_ifname, "veth_c_abcd12")
        self.assertEqual(veth.peer_ifname, "ceth_c_abcd12")
        self.assertLessEqual(len(veth.host_ifname), 15)  # Linux IFNAMSIZ limit
        self.assertLessEqual(len(veth.peer_ifname), 15)

        cmd = veth.to_ip_link_args()
        self.assertEqual(cmd, ["ip", "link", "add", "veth_c_abcd12", "type", "veth", "peer", "name", "ceth_c_abcd12"])

    def test_ip_assignment_and_release(self):
        cfg = self.mgr.assign_ip("cont_01", host_index=2)
        self.assertEqual(cfg.gateway, "172.19.0.1")
        self.assertEqual(cfg.ip_address, "172.19.0.2/16")
        self.assertEqual(cfg.bridge, "boxcar0")

        # Release
        self.assertTrue(self.mgr.release_ip("cont_01"))
        self.assertFalse(self.mgr.release_ip("nonexistent"))

    def test_invalid_host_index(self):
        with self.assertRaises(ValueError):
            self.mgr.assign_ip("bad_cont", host_index=1)  # Gateway collision


if __name__ == "__main__":
    unittest.main()
