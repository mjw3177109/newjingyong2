"""Synthetic AS1/2 action-record tests; no copyrighted game data."""
import unittest
from tools.index_swf_action_opcodes import inspect_actions


class ActionOpcodeTests(unittest.TestCase):
    def test_simple_conditional_jump_and_goto(self):
        # IF +0, GotoFrame(9), End
        data = bytes([0x9d, 2, 0, 0, 0, 0x81, 2, 0, 9, 0, 0])
        counts, warnings = inspect_actions(data)
        self.assertEqual((counts['if'], counts['goto_frame'], counts['records']), (1, 1, 2))
        self.assertEqual(warnings, [])

    def test_if_target_is_aligned_to_next_action(self):
        # IF offset zero points to GotoFrame at byte 5.
        data = bytes([0x9d, 2, 0, 0, 0, 0x81, 2, 0, 9, 0, 0])
        counts, warnings = inspect_actions(data)
        self.assertEqual(counts.get('branch_targets_on_record_boundary'), 1)
        self.assertEqual(counts.get('branch_targets_inside_record', 0), 0)
        self.assertEqual(warnings, [])

    def test_backward_jump_and_end_marker_are_valid_targets(self):
        # Jump at byte 3 ends at byte 8; signed -8 targets Push at byte 0.
        backward = bytes([0x96, 0, 0, 0x99, 2, 0, 0xf8, 0xff, 0])
        counts, warnings = inspect_actions(backward)
        self.assertEqual(counts.get('branch_targets_on_record_boundary'), 1)
        self.assertEqual(warnings, [])
        # A zero-offset Jump may target the terminating ActionEnd opcode.
        counts, warnings = inspect_actions(bytes([0x99, 2, 0, 0, 0, 0]))
        self.assertEqual(counts.get('branch_targets_on_record_boundary'), 1)
        self.assertEqual(warnings, [])

    def test_branch_into_middle_of_record_is_counted_not_interpreted(self):
        # Jump ends at byte 5; signed -2 targets an offset byte at index 3.
        data = bytes([0x99, 2, 0, 0xfe, 0xff, 0])
        counts, warnings = inspect_actions(data)
        self.assertEqual(counts.get('branch_targets_inside_record'), 1)
        self.assertEqual(counts.get('branch_targets_on_record_boundary', 0), 0)
        self.assertEqual(warnings, [])  # Structural anomaly, not a decode failure.

    def test_nested_function_body_is_not_interpreted(self):
        # Payload of function opcode is opaque even if it contains IF bytes.
        data = bytes([0x9b, 4, 0, 0x9d, 0, 0, 0, 0])
        counts, warnings = inspect_actions(data)
        self.assertEqual(counts.get('if', 0), 0)
        self.assertEqual(counts['define_function'], 1)
        self.assertEqual(warnings, [])

    def test_truncated_record_is_reported_not_accepted(self):
        counts, warnings = inspect_actions(bytes([0x81, 2, 0, 7]))
        self.assertEqual(counts['goto_frame'], 1)
        self.assertIn('truncated_action_payload', warnings)
        self.assertIn('missing_action_end', warnings)

    def test_out_of_bounds_branch_and_invalid_length(self):
        counts, warnings = inspect_actions(bytes([0x99, 2, 0, 0xff, 0x7f, 0]))
        self.assertEqual(counts['out_of_bounds_branch_targets'], 1)
        self.assertEqual(warnings, [])
        _, warnings2 = inspect_actions(bytes([0x81, 1, 0, 7, 0]))
        self.assertIn('invalid_fixed_action_length', warnings2)

    def test_no_leak_of_embedded_string(self):
        data = bytes([0x96, 8, 0, 0]) + b'secret\x00' + bytes([0])
        counts, warnings = inspect_actions(data)
        self.assertEqual(counts['push'], 1)
        self.assertNotIn('secret', str((counts, warnings)))
        self.assertEqual(warnings, [])


if __name__ == '__main__':
    unittest.main()
