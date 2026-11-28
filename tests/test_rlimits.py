import unittest
from boxcar import RlimitsSpec, RlimitEntry


class TestRlimitsSpec(unittest.TestCase):
    def test_default_container_limits(self):
        spec = RlimitsSpec.default_container_limits()
        nofile = spec.get_limit("RLIMIT_NOFILE")
        self.assertIsNotNone(nofile)
        self.assertEqual(nofile.soft, 1024)
        self.assertEqual(nofile.hard, 2048)

        core = spec.get_limit("RLIMIT_CORE")
        self.assertIsNotNone(core)
        self.assertEqual(core.soft, 0)
        self.assertEqual(core.hard, 0)

    def test_set_and_remove_limit(self):
        spec = RlimitsSpec()
        spec.set_limit("RLIMIT_MEMLOCK", 65536, 65536)
        self.assertIsNotNone(spec.get_limit("RLIMIT_MEMLOCK"))

        removed = spec.remove_limit("RLIMIT_MEMLOCK")
        self.assertTrue(removed)
        self.assertIsNone(spec.get_limit("RLIMIT_MEMLOCK"))

    def test_to_and_from_oci(self):
        spec = RlimitsSpec()
        spec.set_limit("RLIMIT_CPU", 10, 20)
        spec.set_limit("RLIMIT_AS", 1048576, 2097152)

        oci_list = spec.to_oci()
        self.assertEqual(len(oci_list), 2)

        reconstructed = RlimitsSpec.from_oci(oci_list)
        cpu = reconstructed.get_limit("RLIMIT_CPU")
        self.assertIsNotNone(cpu)
        self.assertEqual(cpu.soft, 10)
        self.assertEqual(cpu.hard, 20)

    def test_validation_errors(self):
        # Invalid type
        with self.assertRaises(ValueError):
            RlimitEntry("RLIMIT_INVALID", 100, 200)

        # Soft > Hard
        with self.assertRaises(ValueError):
            RlimitEntry("RLIMIT_NOFILE", 5000, 1000)

        # Negative value
        with self.assertRaises(ValueError):
            RlimitEntry("RLIMIT_NPROC", -1, 100)


if __name__ == "__main__":
    unittest.main()
