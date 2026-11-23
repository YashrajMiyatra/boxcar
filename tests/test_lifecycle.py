import signal
import unittest
from boxcar.lifecycle import LifecycleManager


class TestLifecycleManager(unittest.TestCase):
    def test_graceful_termination(self):
        signals_received = []
        alive_states = [True, True, False]

        def mock_kill(pid, sig):
            signals_received.append((pid, sig))

        def mock_is_alive(pid):
            return alive_states.pop(0) if alive_states else False

        mgr = LifecycleManager(kill_fn=mock_kill, is_alive_fn=mock_is_alive)
        result = mgr.stop_container(1234, grace_period_sec=1.0, poll_interval_sec=0.01)

        self.assertEqual(result, "terminated_gracefully")
        self.assertEqual(signals_received, [(1234, signal.SIGTERM)])

    def test_forceful_escalation_to_sigkill(self):
        signals_received = []

        def mock_kill(pid, sig):
            signals_received.append((pid, sig))

        # Always remains alive
        def mock_is_alive(pid):
            return True

        mgr = LifecycleManager(kill_fn=mock_kill, is_alive_fn=mock_is_alive)
        result = mgr.stop_container(5678, grace_period_sec=0.05, poll_interval_sec=0.01)

        self.assertEqual(result, "killed_forcefully")
        self.assertEqual(signals_received, [(5678, signal.SIGTERM), (5678, signal.SIGKILL)])

    def test_already_stopped(self):
        mgr = LifecycleManager(is_alive_fn=lambda pid: False)
        result = mgr.stop_container(9999)
        self.assertEqual(result, "already_stopped")


if __name__ == "__main__":
    unittest.main()
