import unittest
from boxcar.memory import MemoryLimitSpec, parse_memory_string_to_bytes


class TestMemoryLimit(unittest.TestCase):
    def test_parse_memory_units(self):
        self.assertEqual(parse_memory_string_to_bytes("512m"), 512 * 1024 * 1024)
        self.assertEqual(parse_memory_string_to_bytes("2G"), 2 * 1024 * 1024 * 1024)
        self.assertEqual(parse_memory_string_to_bytes("64kb"), 64 * 1024)
        self.assertEqual(parse_memory_string_to_bytes("1048576"), 1048576)
        self.assertEqual(parse_memory_string_to_bytes("max"), -1)

    def test_memory_spec_formatting(self):
        spec = MemoryLimitSpec.from_string("256mb", "128mb")
        self.assertEqual(spec.limit_bytes, 256 * 1024 * 1024)
        self.assertEqual(spec.high_bytes, 128 * 1024 * 1024)
        self.assertEqual(spec.to_cgroup_max_spec(), str(256 * 1024 * 1024))

        spec_max = MemoryLimitSpec.from_string("max")
        self.assertEqual(spec_max.to_cgroup_max_spec(), "max")

    def test_invalid_formats(self):
        with self.assertRaises(ValueError):
            parse_memory_string_to_bytes("invalid_mem")
        with self.assertRaises(ValueError):
            parse_memory_string_to_bytes("100xyz")


if __name__ == "__main__":
    unittest.main()
