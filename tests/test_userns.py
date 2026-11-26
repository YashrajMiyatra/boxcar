import unittest
from boxcar import UserNamespaceSpec, IDMapping


class TestUserNamespace(unittest.TestCase):
    def test_rootless_default_mapping(self):
        spec = UserNamespaceSpec.create_rootless_default(host_uid=1001, host_gid=1002)
        # Inside container root (UID 0) maps to host 1001
        self.assertEqual(spec.map_uid_to_host(0), 1001)
        self.assertEqual(spec.map_uid_to_container(1001), 0)

        # Inside container GID 0 maps to host 1002
        self.assertEqual(spec.map_gid_to_host(0), 1002)
        self.assertEqual(spec.map_gid_to_container(1002), 0)

        # Unmapped ID returns None
        self.assertIsNone(spec.map_uid_to_host(1))
        self.assertIsNone(spec.map_uid_to_container(1000))

    def test_multi_range_mapping(self):
        spec = UserNamespaceSpec()
        # Map root to 1000
        spec.add_uid_mapping(container_id=0, host_id=1000, size=1)
        # Map container UIDs 1000-1999 to host 100000-100999
        spec.add_uid_mapping(container_id=1000, host_id=100000, size=1000)

        self.assertEqual(spec.map_uid_to_host(0), 1000)
        self.assertEqual(spec.map_uid_to_host(1000), 100000)
        self.assertEqual(spec.map_uid_to_host(1500), 100500)
        self.assertEqual(spec.map_uid_to_host(1999), 100999)
        self.assertIsNone(spec.map_uid_to_host(2000))

        # Reverse mapping
        self.assertEqual(spec.map_uid_to_container(100000), 1000)
        self.assertEqual(spec.map_uid_to_container(100500), 1500)

    def test_proc_format(self):
        spec = UserNamespaceSpec()
        spec.add_uid_mapping(container_id=0, host_id=1000, size=1)
        spec.add_gid_mapping(container_id=0, host_id=1000, size=1)

        self.assertEqual(spec.format_proc_uid_map(), "0 1000 1")
        self.assertEqual(spec.format_proc_gid_map(), "0 1000 1")

    def test_oci_spec_format(self):
        spec = UserNamespaceSpec.create_rootless_default(host_uid=1000, host_gid=1000)
        oci = spec.format_oci_spec()
        self.assertIn("linux", oci)
        self.assertEqual(
            oci["linux"]["uidMappings"],
            [{"containerID": 0, "hostID": 1000, "size": 1}],
        )
        self.assertEqual(
            oci["linux"]["gidMappings"],
            [{"containerID": 0, "hostID": 1000, "size": 1}],
        )

    def test_invalid_mapping_args(self):
        spec = UserNamespaceSpec()
        with self.assertRaises(ValueError):
            spec.add_uid_mapping(container_id=-1, host_id=1000, size=1)
        with self.assertRaises(ValueError):
            spec.add_uid_mapping(container_id=0, host_id=-1, size=1)
        with self.assertRaises(ValueError):
            spec.add_uid_mapping(container_id=0, host_id=1000, size=0)


if __name__ == "__main__":
    unittest.main()
