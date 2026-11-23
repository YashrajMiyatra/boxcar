import unittest
from boxcar.cpu import CPUBandwidthQuota


class TestCPUBandwidthQuota(unittest.TestCase):
    def test_quota_calculation(self):
        quota = CPUBandwidthQuota(cpus=2.5, period_us=100_000)
        self.assertEqual(quota.quota_us, 250_000)
        self.assertEqual(quota.to_cgroup_max_spec(), "250000 100000")

    def test_from_millicores(self):
        quota = CPUBandwidthQuota.from_millicores(500)
        self.assertEqual(quota.cpus, 0.5)
        self.assertEqual(quota.quota_us, 50_000)
        self.assertEqual(quota.to_cgroup_max_spec(), "50000 100000")

    def test_parse_cpu_max(self):
        quota, period = CPUBandwidthQuota.parse_cpu_max("200000 100000")
        self.assertEqual(quota, 200_000)
        self.assertEqual(period, 100_000)

        quota_max, period_max = CPUBandwidthQuota.parse_cpu_max("max 100000")
        self.assertEqual(quota_max, -1)
        self.assertEqual(period_max, 100_000)

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            CPUBandwidthQuota(cpus=0.0)
        with self.assertRaises(ValueError):
            CPUBandwidthQuota(period_us=500)
        with self.assertRaises(ValueError):
            CPUBandwidthQuota.from_millicores(-100)


if __name__ == "__main__":
    unittest.main()
