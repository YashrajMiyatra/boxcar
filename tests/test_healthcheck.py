"""
Unit tests for Boxcar HealthCheck runner and status transitions.
"""

import unittest
from boxcar.health import HealthCheckConfig, HealthCheckRunner, HealthStatus


class TestHealthCheck(unittest.TestCase):
    def test_validation(self):
        with self.assertRaises(ValueError):
            HealthCheckConfig(command=[])

    def test_successful_probe_transitions_to_healthy(self):
        config = HealthCheckConfig(command=["true"], timeout_sec=1.0, retries=2)
        runner = HealthCheckRunner(config, executor=lambda cmd, t: 0)
        self.assertEqual(runner.status, HealthStatus.STARTING)

        status = runner.run_probe()
        self.assertEqual(status, HealthStatus.HEALTHY)
        self.assertEqual(runner.consecutive_successes, 1)
        self.assertEqual(runner.consecutive_failures, 0)
        self.assertEqual(len(runner.history), 1)

    def test_retry_threshold_before_unhealthy(self):
        config = HealthCheckConfig(command=["curl", "localhost"], timeout_sec=1.0, retries=3)
        # Mock executor that always fails
        runner = HealthCheckRunner(config, executor=lambda cmd, t: 1)

        # Probe 1: fails, but retries not exceeded -> stays STARTING
        status = runner.run_probe()
        self.assertEqual(status, HealthStatus.STARTING)
        self.assertEqual(runner.consecutive_failures, 1)

        # Probe 2: fails
        status = runner.run_probe()
        self.assertEqual(status, HealthStatus.STARTING)
        self.assertEqual(runner.consecutive_failures, 2)

        # Probe 3: threshold reached -> UNHEALTHY
        status = runner.run_probe()
        self.assertEqual(status, HealthStatus.UNHEALTHY)
        self.assertEqual(runner.consecutive_failures, 3)

    def test_recovery_from_unhealthy(self):
        config = HealthCheckConfig(command=["check"], retries=1)
        runner = HealthCheckRunner(config, executor=lambda cmd, t: 1)
        runner.run_probe()
        self.assertEqual(runner.status, HealthStatus.UNHEALTHY)

        # Service recovers
        runner.executor = lambda cmd, t: 0
        runner.run_probe()
        self.assertEqual(runner.status, HealthStatus.HEALTHY)


if __name__ == "__main__":
    unittest.main()
