"""Synthetic regression tests for AVM1 IF structural evidence; no SWF content."""
import struct
import unittest

from tools.probe_if6607_structure import decode_records, inspect_target


class IfStructureSyntheticTests(unittest.TestCase):
    def test_valid_branch_and_fallthrough_are_distinct_boundaries(self):
        # Push (4 bytes), IF (5 bytes), NextFrame (1 byte), End (1 byte).
        payload = bytes([0x96, 0x01, 0x00, 0x00, 0x9d, 0x02, 0x00]) + struct.pack("<h", 1) + bytes([0x04, 0x00])
        result = inspect_target(payload, target=4)
        self.assertEqual(result["fallthrough_offset"], 9)
        self.assertEqual(result["branch_offset"], 10)
        self.assertEqual(result["relative_displacement"], 1)
        self.assertEqual(result["fallthrough_opcode_hex"], "04")
        self.assertEqual(result["branch_opcode_hex"], "00")
        self.assertEqual(result["fallthrough_linear_window"], [{"offset": 9, "opcode_hex": "04"}, {"offset": 10, "opcode_hex": "00"}])
        self.assertEqual(result["branch_linear_window"], [{"offset": 10, "opcode_hex": "00"}])
        self.assertEqual(result["prior_opcode_window"][-1], {"offset": 4, "opcode_hex": "9d"})
        self.assertEqual(result["verified_story_events"], 0)
        self.assertEqual(result["condition_stack_origin"], "unknown")

    def test_branch_to_fallthrough_reports_same_successor(self):
        payload = bytes([0x9d, 0x02, 0x00, 0x00, 0x00, 0x04, 0x00])
        result = inspect_target(payload, target=0)
        self.assertEqual(result["fallthrough_offset"], result["branch_offset"])
        self.assertEqual(result["fallthrough_opcode_hex"], "04")
        self.assertEqual(result["branch_opcode_hex"], "04")
        self.assertEqual(result["fallthrough_linear_window"], result["branch_linear_window"])

    def test_successor_window_stops_at_unconditional_jump(self):
        # IF fallthrough reaches Jump; bytes after Jump are not proven executed.
        payload = bytes([0x9d, 0x02, 0x00, 0x00, 0x00,
                         0x99, 0x02, 0x00, 0x01, 0x00,
                         0x04, 0x00])
        result = inspect_target(payload, target=0)
        self.assertEqual(result["fallthrough_linear_window"],
                         [{"offset": 5, "opcode_hex": "99"}])
        self.assertEqual(result["branch_linear_window"],
                         [{"offset": 5, "opcode_hex": "99"}])

    def test_successor_window_stops_at_return(self):
        payload = bytes([0x9d, 0x02, 0x00, 0x00, 0x00, 0x3e, 0x04, 0x00])
        result = inspect_target(payload, target=0)
        self.assertEqual(result["fallthrough_linear_window"],
                         [{"offset": 5, "opcode_hex": "3e"}])

    def test_branch_into_action_body_rejected(self):
        payload = bytes([0x96, 0x01, 0x00, 0x00, 0x9d, 0x02, 0x00]) + struct.pack("<h", -8) + bytes([0x04, 0x00])
        with self.assertRaisesRegex(ValueError, "branch target not an action boundary"):
            inspect_target(payload, target=4)

    def test_missing_terminal_end_rejected(self):
        with self.assertRaisesRegex(ValueError, "terminal End"):
            decode_records(bytes([0x04]))

    def test_trailing_bytes_after_end_rejected(self):
        with self.assertRaisesRegex(ValueError, "terminal End"):
            decode_records(bytes([0x00, 0x04]))

    def test_truncated_long_action_rejected(self):
        with self.assertRaisesRegex(ValueError, "truncated action body"):
            decode_records(bytes([0x96, 0x02, 0x00, 0x01]))


if __name__ == "__main__":
    unittest.main()
