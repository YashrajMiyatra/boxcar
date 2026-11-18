import os
import tempfile
import unittest
from boxcar.runtime import ContainerRunner


class TestRuntime(unittest.TestCase):
    def setUp(self):
        self.temp_rootfs = tempfile.mkdtemp()
        self.runner = ContainerRunner(self.temp_rootfs)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_rootfs)

    def test_run_command_sandbox(self):
        # Runs a basic command in the sandbox environment
        code = self.runner.run(["echo", "Container Sandbox Active"])
        self.assertEqual(code, 0)

    def test_run_with_env_vars(self):
        # Verifies custom environment variables are injected into container environment
        code = self.runner.run(
            ["python3", "-c", "import os; assert os.environ.get('MY_CONTAINER_VAR') == 'boxcar_ok'"],
            env_vars={"MY_CONTAINER_VAR": "boxcar_ok"},
        )
        self.assertEqual(code, 0)

    def test_run_command_failure(self):
        code = self.runner.run(["python3", "-c", "import sys; sys.exit(42)"])
        self.assertEqual(code, 42)


if __name__ == "__main__":
    unittest.main()
