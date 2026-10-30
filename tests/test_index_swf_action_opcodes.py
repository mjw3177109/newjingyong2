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
