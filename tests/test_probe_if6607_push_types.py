import unittest
from tools.probe_if6607_push_types import push_types, inventory


class PushTypeTests(unittest.TestCase):
    def test_supported_types(self):
        self.assertEqual(push_types(b"\x00abc\x00\x01\x00\x00\x80?\x02\x05\x01\x08\x03"), [0, 1, 2, 5, 8])

    def test_reject_malformed(self):
        for payload in (b"\x00abc", b"\x01\x00", b"\x09\x00", b"\xff"):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                push_types(payload)

    def test_no_literal_leakage(self):
        action = b"\x96\x03\x00\x00A\x00\x96\x03\x00\x00B\x00\x96\x03\x00\x00C\x00\x1d\x00"
        report = inventory(action, (0, 6, 12))
        self.assertEqual([x["push_type_codes"] for x in report["pushes"]], [[0], [0], [0]])
        self.assertNotIn('"A"', str(report))
        self.assertEqual(report["verified_story_events"], 0)\n        self.assertTrue(report["set_variable_opcode_confirmed"])\n        self.assertEqual(report["set_variable_target"], "unknown")\n        self.assertEqual([x["value_count"] for x in report["pushes"]], [1, 1, 1])\n\n    def test_requires_set_variable_boundary(self):\n        action = b"\x96\x03\x00\x00A\x00\x96\x03\x00\x00B\x00\x96\x03\x00\x00C\x00\x00"\n        with self.assertRaisesRegex(ValueError, "SetVariable"):\n            inventory(action, (0, 6, 12))


if __name__ == "__main__":
    unittest.main()
