import unittest
from boxcar.security import ReadOnlyRootfsSpec


class TestReadOnlyRootfs(unittest.TestCase):
    def test_readonly_default_tmpfs(self):
        spec = ReadOnlyRootfsSpec(readonly=True)
        # Default /tmp and /run are writable
        self.assertTrue(spec.is_writable("/tmp/foo.txt"))
        self.assertTrue(spec.is_writable("/run/app.pid"))

        # Root paths outside tmpfs are read-only
        self.assertFalse(spec.is_writable("/etc/passwd"))
        self.assertFalse(spec.is_writable("/usr/bin/python"))

    def test_writable_mount_allowlist(self):
        spec = ReadOnlyRootfsSpec(
            readonly=True,
            writable_mounts=["/var/log", "/data"],
            allow_default_tmpfs=False,
        )
        self.assertTrue(spec.is_writable("/var/log/app.log"))
        self.assertTrue(spec.is_writable("/data/db.sqlite"))
        self.assertFalse(spec.is_writable("/tmp/test"))

    def test_validate_write_attempt_raises(self):
        spec = ReadOnlyRootfsSpec(readonly=True, writable_mounts=["/data"])
        # Writing to /data should succeed
        spec.validate_write_attempt("/data/file.txt")

        # Writing to /bin should raise PermissionError
        with self.assertRaises(PermissionError):
            spec.validate_write_attempt("/bin/bash")

    def test_non_readonly_allows_all(self):
        spec = ReadOnlyRootfsSpec(readonly=False)
        self.assertTrue(spec.is_writable("/any/arbitrary/path"))


if __name__ == "__main__":
    unittest.main()
