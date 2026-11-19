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
        self.assertEqual(result["fallthrough_linear_window"], [{"offset": 9, "opcode_hex": "04"}])
        self.assertEqual(result["branch_linear_window"], [{"offset": 10, "opcode_hex": "00"}])
        self.assertEqual(result["prior_opcode_window"][-1], {"offset": 4, "opcode_hex": "9d"})
        self.assertFalse(result["branch_entry_same_as_fallthrough"])
        self.assertEqual(result["shared_linear_window_offsets"], [])
        self.assertEqual(result["verified_story_events"], 0)
        self.assertEqual(result["condition_stack_origin"], "unknown")

    def test_branch_to_fallthrough_reports_same_successor(self):
        payload = bytes([0x9d, 0x02, 0x00, 0x00, 0x00, 0x04, 0x00])
        result = inspect_target(payload, target=0)
        self.assertEqual(result["fallthrough_offset"], result["branch_offset"])
        self.assertEqual(result["fallthrough_opcode_hex"], "04")
        self.assertEqual(result["branch_opcode_hex"], "04")
        self.assertEqual(result["fallthrough_linear_window"], result["branch_linear_window"])
        self.assertTrue(result["branch_entry_same_as_fallthrough"])
        self.assertEqual(result["shared_linear_window_offsets"], [5, 6])

    def test_distinct_entries_can_share_a_later_linear_instruction(self):
        # IF false enters at 5, true enters at 6; both windows include End at 6.
        payload = bytes([0x9D, 0x02, 0, 1, 0, 0x4A, 0x00])
        result = inspect_target(payload, target=0)
        self.assertFalse(result["branch_entry_same_as_fallthrough"])
        self.assertEqual(result["shared_linear_window_offsets"], [6])
        self.assertEqual(result["condition_stack_origin"], "unknown")

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

    def test_successor_window_stops_at_conditional_skip_and_dynamic_call(self):
        # IF falls through to a WaitForFrame (skip-count action) or Call.
        # These synthetic records are structurally valid, not execution traces.
        for opcode, body in ((0x8A, bytes([1, 0, 1])), (0x8D, bytes([1])), (0x9E, b"")):
            with self.subTest(opcode=opcode):
                transfer = bytes([opcode, len(body), 0]) + body
                payload = bytes([0x9D, 0x02, 0, 0, 0]) + transfer + bytes([0x04, 0])
                result = inspect_target(payload, target=0)
                self.assertEqual(result["fallthrough_linear_window"],
                                 [{"offset": 5, "opcode_hex": f"{opcode:02x}"}])

    def test_successor_window_stops_at_timeline_navigation(self):
        # Navigation may transfer execution to another frame; do not include
        # the following action in a purported local successor window.
        cases = ((0x04, b""), (0x05, b""), (0x06, b""),
                 (0x07, b""), (0x81, bytes([1, 0])),
                 (0x8C, b"scene" + bytes([0])), (0x9F, bytes([0])))
        for opcode, body in cases:
            with self.subTest(opcode=opcode):
                action = (bytes([opcode, len(body), 0]) + body
                          if opcode >= 0x80 else bytes([opcode]))
                payload = bytes([0x9D, 0x02, 0, 0, 0]) + action + bytes([0x04, 0])
                result = inspect_target(payload, target=0)
                self.assertEqual(result["fallthrough_linear_window"],
                                 [{"offset": 5, "opcode_hex": f"{opcode:02x}"}])

    def test_successor_window_stops_at_throw(self):
        # AVM1 Throw (0x2A) transfers control to an exception handler or exits.
        payload = bytes([0x9D, 0x02, 0, 0, 0, 0x2A, 0x04, 0])
        result = inspect_target(payload, target=0)
        self.assertEqual(result["fallthrough_linear_window"],
                         [{"offset": 5, "opcode_hex": "2a"}])
        self.assertEqual(result["branch_linear_window"],
                         [{"offset": 5, "opcode_hex": "2a"}])

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
