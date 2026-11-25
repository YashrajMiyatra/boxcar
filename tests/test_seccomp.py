import unittest
from boxcar.seccomp import SeccompFilterSpec


class TestSeccompFilter(unittest.TestCase):
    def test_default_blocked_syscalls(self):
        spec = SeccompFilterSpec(default_action="SCMP_ACT_ALLOW")
        # reboot and swapon should be blocked by default with ERRNO
        self.assertEqual(spec.evaluate("reboot"), "SCMP_ACT_ERRNO")
        self.assertEqual(spec.evaluate("swapon"), "SCMP_ACT_ERRNO")
        # standard syscalls fall back to default ALLOW
        self.assertEqual(spec.evaluate("read"), "SCMP_ACT_ALLOW")
        self.assertEqual(spec.evaluate("write"), "SCMP_ACT_ALLOW")

    def test_custom_override(self):
        spec = SeccompFilterSpec(default_action="SCMP_ACT_ALLOW")
        spec.block_syscall("ptrace", action="SCMP_ACT_KILL")
        self.assertEqual(spec.evaluate("ptrace"), "SCMP_ACT_KILL")

        spec.allow_syscall("reboot")
        self.assertEqual(spec.evaluate("reboot"), "SCMP_ACT_ALLOW")

    def test_invalid_action(self):
        with self.assertRaises(ValueError):
            SeccompFilterSpec(default_action="SCMP_ACT_INVALID")

    def test_format_oci_spec(self):
        spec = SeccompFilterSpec()
        oci = spec.format_oci_spec()
        self.assertEqual(oci["defaultAction"], "SCMP_ACT_ALLOW")
        self.assertIn("SCMP_ARCH_X86_64", oci["architectures"])
        self.assertTrue(len(oci["syscalls"]) > 0)


if __name__ == "__main__":
    unittest.main()
