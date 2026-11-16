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


if __name__ == "__main__":
    unittest.main()
