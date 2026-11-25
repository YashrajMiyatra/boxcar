import os
import tempfile
import unittest
from boxcar.oom import OOMScoreAdjustSpec


class TestOOMScoreAdjust(unittest.TestCase):
    def test_valid_scores(self):
        spec0 = OOMScoreAdjustSpec(0)
        self.assertEqual(spec0.score, 0)
        self.assertEqual(spec0.format_oci_spec(), {"oomScoreAdj": 0})

        spec_min = OOMScoreAdjustSpec(-1000)
        self.assertEqual(spec_min.score, -1000)

        spec_max = OOMScoreAdjustSpec(1000)
        self.assertEqual(spec_max.score, 1000)

    def test_out_of_bounds(self):
        with self.assertRaises(ValueError):
            OOMScoreAdjustSpec(-1001)

        with self.assertRaises(ValueError):
            OOMScoreAdjustSpec(1001)

    def test_invalid_type(self):
        with self.assertRaises(TypeError):
            OOMScoreAdjustSpec("high")

    def test_write_to_proc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_dir = os.path.join(tmpdir, "1234")
            os.makedirs(pid_dir, exist_ok=True)

            spec = OOMScoreAdjustSpec(500)
            spec.write_to_proc(1234, proc_root=tmpdir)

            proc_file = os.path.join(pid_dir, "oom_score_adj")
            self.assertTrue(os.path.exists(proc_file))
            with open(proc_file, "r") as f:
                content = f.read().strip()
            self.assertEqual(content, "500")


if __name__ == "__main__":
    unittest.main()
