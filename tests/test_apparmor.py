import unittest
from boxcar import AppArmorProfileSpec, AppArmorRule


class TestAppArmorProfileSpec(unittest.TestCase):
    def test_default_profile_generation(self):
        spec = AppArmorProfileSpec.create_default_profile()
        self.assertEqual(spec.name, "boxcar-default")
        self.assertEqual(spec.mode, "enforce")

        text = spec.generate_profile_text()
        self.assertIn("profile boxcar-default flags=(attach_disconnected,mediate_deleted) {", text)
        self.assertIn("deny /proc/sys/** wklx,", text)
        self.assertIn("deny /sys/** wklx,", text)

        oci = spec.format_oci_spec()
        self.assertEqual(oci["process"]["apparmorProfile"], "boxcar-default")

    def test_custom_rules_and_complain_mode(self):
        spec = AppArmorProfileSpec(name="custom-sandbox", mode="complain")
        spec.add_rule(path="/var/log/**", permissions="w", deny=False)
        spec.add_rule(path="/etc/shadow", permissions="r", deny=True)

        text = spec.generate_profile_text()
        self.assertIn("profile custom-sandbox flags=(complain,attach_disconnected,mediate_deleted) {", text)
        self.assertIn("/var/log/** w,", text)
        self.assertIn("deny /etc/shadow r,", text)

    def test_disabled_profile_oci_unconfined(self):
        spec = AppArmorProfileSpec(name="custom", mode="disabled")
        oci = spec.format_oci_spec()
        self.assertEqual(oci["process"]["apparmorProfile"], "unconfined")

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            AppArmorProfileSpec(name="test", mode="invalid_mode")
        with self.assertRaises(ValueError):
            AppArmorProfileSpec(name="", mode="enforce")
        spec = AppArmorProfileSpec()
        with self.assertRaises(ValueError):
            spec.add_rule(path="", permissions="r")


if __name__ == "__main__":
    unittest.main()
