"""Synthetic-only tests for source-free IF structural probe."""
import unittest
from tools.probe_if6607_structure import inspect_target, decode_records


class IfStructureTests(unittest.TestCase):
    def test_valid_if(self):
        # ActionIF (5 bytes), ActionNextFrame, ActionPlay, End.
        payload = bytes([0x9d, 2, 0, 1, 0, 0x04, 0x06, 0])
        row = inspect_target(payload, 0)
        self.assertEqual((row["fallthrough_offset"], row["branch_offset"]), (5, 6))
        self.assertEqual(row["verified_story_events"], 0)
        self.assertEqual(row["condition_stack_origin"], "unknown")

    def test_bad_target(self):
        with self.assertRaises(ValueError):
            inspect_target(bytes([0x9d, 2, 0, 1, 0, 0x04, 0]), 0)

    def test_not_if(self):
        with self.assertRaises(ValueError):
            inspect_target(bytes([0x04, 0]), 0)

    def test_truncated(self):
        with self.assertRaises(ValueError):
            decode_records(bytes([0x9d, 2, 0, 0]))

if __name__ == "__main__":
    unittest.main()
