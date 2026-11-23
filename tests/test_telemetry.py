"""
Unit tests for Container Resource Telemetry in Boxcar.
"""

import sys
import unittest
from boxcar.runtime import ContainerRunner


class TestContainerTelemetry(unittest.TestCase):
    def setUp(self):
        self.runner = ContainerRunner(rootfs_path=".")

    def test_run_with_telemetry_success(self):
        res = self.runner.run_with_telemetry(
            [sys.executable, "-c", "print('hello from boxcar')"]
        )
        self.assertEqual(res["exit_code"], 0)
        self.assertEqual(res["status"], "success")
        self.assertIn("hello from boxcar", res["stdout"])
        self.assertGreaterEqual(res["wall_time_sec"], 0.0)
        self.assertIn("max_rss_kb", res)

    def test_run_with_telemetry_failure(self):
        res = self.runner.run_with_telemetry(
            [sys.executable, "-c", "import sys; sys.exit(42)"]
        )
        self.assertEqual(res["exit_code"], 42)
        self.assertEqual(res["status"], "failed")

    def test_run_with_telemetry_not_found(self):
        res = self.runner.run_with_telemetry(["__non_existent_binary_xyz_123__"])
        self.assertEqual(res["exit_code"], 127)
        self.assertEqual(res["status"], "not_found")


if __name__ == "__main__":
    unittest.main()
