import unittest
from boxcar import DeviceCgroupSpec, DeviceRule


class TestDeviceCgroup(unittest.TestCase):
    def test_default_device_permissions(self):
        spec = DeviceCgroupSpec.create_default_devices()

        # /dev/null (c 1:3) is allowed rwm
        self.assertTrue(spec.is_allowed("c", 1, 3, "rwm"))
        self.assertTrue(spec.is_allowed("c", 1, 3, "r"))
        self.assertTrue(spec.is_allowed("c", 1, 3, "w"))

        # /dev/urandom (c 1:9) allows rm, but NOT write
        self.assertTrue(spec.is_allowed("c", 1, 9, "r"))
        self.assertFalse(spec.is_allowed("c", 1, 9, "w"))

        # Arbitrary block device /dev/sda (b 8:0) is denied
        self.assertFalse(spec.is_allowed("b", 8, 0, "r"))

    def test_cgroup_lines_and_oci(self):
        spec = DeviceCgroupSpec()
        spec.add_rule(device_type="c", major=1, minor=3, access="rwm", allow=True)
        spec.add_rule(device_type="b", major=8, minor=0, access="r", allow=False)

        allows = spec.format_cgroup_allow_lines()
        self.assertEqual(allows, ["c 1:3 rwm"])

        denies = spec.format_cgroup_deny_lines()
        self.assertEqual(denies, ["b 8:0 r"])

        oci = spec.format_oci_spec()
        self.assertEqual(len(oci["linux"]["resources"]["devices"]), 2)
        self.assertTrue(oci["linux"]["resources"]["devices"][0]["allow"])
        self.assertEqual(oci["linux"]["resources"]["devices"][0]["major"], 1)

    def test_wildcard_rule(self):
        spec = DeviceCgroupSpec(default_allow=False)
        # Allow all char devices major 4
        spec.add_rule(device_type="c", major=4, minor=None, access="r", allow=True)

        self.assertTrue(spec.is_allowed("c", 4, 1, "r"))
        self.assertTrue(spec.is_allowed("c", 4, 99, "r"))
        self.assertFalse(spec.is_allowed("c", 5, 1, "r"))

    def test_invalid_arguments(self):
        spec = DeviceCgroupSpec()
        with self.assertRaises(ValueError):
            spec.add_rule(device_type="x", major=1, minor=1)
        with self.assertRaises(ValueError):
            spec.add_rule(device_type="c", major=1, minor=1, access="xyz")


if __name__ == "__main__":
    unittest.main()
