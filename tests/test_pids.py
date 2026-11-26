import os
import tempfile
import unittest
from boxcar.pids import PIDLimitSpec


class TestPIDLimitSpec(unittest.TestCase):
    def test_valid_integer_limit(self):
        spec = PIDLimitSpec(512)
        self.assertEqual(spec.limit, 512)
        oci = spec.format_oci_spec()
        self.assertEqual(oci["pids"]["limit"], 512)

    def test_max_limit(self):
        spec = PIDLimitSpec("max")
        self.assertEqual(spec.limit, "max")
        oci = spec.format_oci_spec()
        self.assertEqual(oci["pids"]["limit"], -1)

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            PIDLimitSpec(0)
        with self.assertRaises(ValueError):
            PIDLimitSpec(-10)
        with self.assertRaises(ValueError):
            PIDLimitSpec("unlimited")

    def test_write_to_cgroup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spec = PIDLimitSpec(256)
            spec.write_to_cgroup(tmpdir)

            target = os.path.join(tmpdir, "pids.max")
            self.assertTrue(os.path.exists(target))
            with open(target) as f:
                self.assertEqual(f.read().strip(), "256")


if __name__ == "__main__":
    unittest.main()
