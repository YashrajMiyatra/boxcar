import unittest
from boxcar.capabilities import LinuxCapabilitiesSpec


class TestLinuxCapabilities(unittest.TestCase):
    def test_default_capabilities(self):
        spec = LinuxCapabilitiesSpec()
        self.assertTrue(spec.has_capability("CAP_CHOWN"))
        self.assertTrue(spec.has_capability("net_bind_service"))
        self.assertFalse(spec.has_capability("CAP_SYS_ADMIN"))

    def test_add_and_drop(self):
        spec = LinuxCapabilitiesSpec()
        spec.add("sys_admin")
        self.assertTrue(spec.has_capability("CAP_SYS_ADMIN"))

        spec.drop("CHOWN")
        self.assertFalse(spec.has_capability("CAP_CHOWN"))

    def test_drop_all(self):
        spec = LinuxCapabilitiesSpec()
        spec.drop_all()
        self.assertFalse(spec.has_capability("CAP_KILL"))
        oci = spec.format_oci_spec()
        self.assertEqual(oci["effective"], [])

    def test_format_oci_spec(self):
        spec = LinuxCapabilitiesSpec(["CAP_KILL", "CAP_CHOWN"])
        oci = spec.format_oci_spec()
        self.assertEqual(sorted(oci["bounding"]), ["CAP_CHOWN", "CAP_KILL"])
        self.assertEqual(sorted(oci["effective"]), ["CAP_CHOWN", "CAP_KILL"])


if __name__ == "__main__":
    unittest.main()
