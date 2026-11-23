"""
Unit tests for Boxcar VolumeMount and VolumeManager path resolution.
"""

import os
import tempfile
import unittest
from boxcar.mount import VolumeMount, VolumeManager


class TestVolumeMounts(unittest.TestCase):
    def test_volume_mount_flags(self):
        m_rw = VolumeMount("/host/dir", "/data", readonly=False)
        self.assertEqual(m_rw.to_mount_flags(), ["bind"])
        self.assertEqual(m_rw.container_path, "/data")

        m_ro = VolumeMount("/host/dir", "/data", readonly=True)
        self.assertEqual(m_ro.to_mount_flags(), ["bind", "ro"])

    def test_volume_manager_resolution(self):
        with tempfile.TemporaryDirectory() as host_dir, tempfile.TemporaryDirectory() as rootfs_dir:
            mgr = VolumeManager(rootfs_path=rootfs_dir)
            mount = mgr.add_mount(host_path=host_dir, container_path="/app/config", readonly=True)

            resolved = mgr.resolve_target_path(mount)
            expected = os.path.join(rootfs_dir, "app/config")
            self.assertEqual(resolved, expected)
            self.assertEqual(len(mgr.list_mounts()), 1)

    def test_missing_host_path_raises(self):
        mgr = VolumeManager(rootfs_path="/tmp")
        with self.assertRaises(FileNotFoundError):
            mgr.add_mount(host_path="/nonexistent/host/directory", container_path="/data")


if __name__ == "__main__":
    unittest.main()
