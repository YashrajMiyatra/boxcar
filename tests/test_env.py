import os
import unittest
from boxcar.env import EnvironmentInjector


class TestEnvironmentInjector(unittest.TestCase):
    def test_key_value_injection(self):
        injector = EnvironmentInjector({"PORT": "8080"})
        injector.inject_pair("APP_ENV=production")
        self.assertEqual(injector.env["PORT"], "8080")
        self.assertEqual(injector.env["APP_ENV"], "production")

    def test_host_lookup_injection(self):
        os.environ["BOXCAR_TEST_VAR"] = "secret123"
        try:
            injector = EnvironmentInjector()
            injector.inject_pair("BOXCAR_TEST_VAR")
            self.assertEqual(injector.env["BOXCAR_TEST_VAR"], "secret123")

            injector.inject_pair("NON_EXISTENT_VAR_XYZ")
            self.assertEqual(injector.env["NON_EXISTENT_VAR_XYZ"], "")
        finally:
            del os.environ["BOXCAR_TEST_VAR"]

    def test_load_env_file(self):
        content = """
        # Comment line
        DATABASE_URL=postgres://user:pass@localhost:5432/db
        DEBUG=true

        # Another comment
        CACHE_ENABLED=1
        """
        injector = EnvironmentInjector()
        injector.load_env_file(content)
        self.assertEqual(injector.env["DATABASE_URL"], "postgres://user:pass@localhost:5432/db")
        self.assertEqual(injector.env["DEBUG"], "true")
        self.assertEqual(injector.env["CACHE_ENABLED"], "1")

    def test_to_env_list(self):
        injector = EnvironmentInjector({"B": "2", "A": "1"})
        self.assertEqual(injector.to_env_list(), ["A=1", "B=2"])


if __name__ == "__main__":
    unittest.main()
