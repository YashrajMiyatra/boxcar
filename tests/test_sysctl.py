import unittest
from boxcar.sysctl import SysctlSpec


class TestSysctlSpec(unittest.TestCase):
    def test_safe_sysctl_params(self):
        spec = SysctlSpec()
        spec.set_param("net.ipv4.ip_forward", "1")
        spec.set_param("net.core.somaxconn", "1024")
        spec.set_param("kernel.shmmax", "67108864")

        self.assertEqual(spec.get_param("net.ipv4.ip_forward"), "1")
        self.assertEqual(spec.get_param("net.core.somaxconn"), "1024")

    def test_unsafe_sysctl_rejection(self):
        spec = SysctlSpec()
        # Modifying host kernel hostname or vm settings without safety override should fail
        with self.assertRaises(ValueError):
            spec.set_param("kernel.hostname", "rogue-host")

        with self.assertRaises(ValueError):
            spec.set_param("vm.max_map_count", "262144")

    def test_format_oci_spec(self):
        spec = SysctlSpec({"net.ipv4.tcp_syncookies": "1"})
        oci = spec.format_oci_spec()
        self.assertEqual(oci, {"net.ipv4.tcp_syncookies": "1"})


if __name__ == "__main__":
    unittest.main()
