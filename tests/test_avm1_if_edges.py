import unittest
from tools.avm1_if_edges import inspect_actions


class Avm1IfEdgesTests(unittest.TestCase):
    def test_forward_and_fallthrough(self):
        data = bytes([0x9d, 2, 0, 1, 0, 0x04, 0x04, 0])
        self.assertEqual(inspect_actions(data), [{
            'offset': 0, 'fallthrough': 5, 'branch': 6, 'kind': 'if',
            'branch_on_action_boundary': True,
            'fallthrough_on_action_boundary': True}])

    def test_signed_backward_displacement(self):
        data = bytes([0x04, 0x9d, 2, 0, 0xfa, 0xff, 0])
        self.assertEqual(inspect_actions(data)[0]['branch'], 0)

    def test_truncated_length_and_payload(self):
        for data in (bytes([0x9d]), bytes([0x9d, 2, 0, 1])):
            with self.subTest(data=data), self.assertRaises(ValueError):
                inspect_actions(data)

    def test_wrong_if_payload_length(self):
        with self.assertRaises(ValueError):
            inspect_actions(bytes([0x9d, 1, 0, 0, 0]))

    def test_branch_to_terminal_end_of_stream(self):
        # IF at 0: fallthrough is ActionEnd at 5; jump exits after it at 6.
        data = bytes([0x9d, 2, 0, 1, 0, 0])
        edge = inspect_actions(data)[0]
        self.assertEqual(edge['branch'], len(data))
        self.assertTrue(edge['branch_on_action_boundary'])
        self.assertTrue(edge['fallthrough_on_action_boundary'])

    def test_branch_past_stream_is_not_boundary(self):
        data = bytes([0x9d, 2, 0, 2, 0, 0])
        self.assertFalse(inspect_actions(data)[0]['branch_on_action_boundary'])

    def test_end_marker_does_not_validate_trailing_bytes(self):
        data = bytes([0x9d, 2, 0, 1, 0, 0, 0x04])
        self.assertFalse(inspect_actions(data)[0]['branch_on_action_boundary'])

    def test_unconditional_jump_forward_and_backward(self):
        forward = bytes([0x99, 2, 0, 1, 0, 0x04, 0])
        edge = inspect_actions(forward)[0]
        self.assertEqual((edge['kind'], edge['branch']), ('jump', 6))
        self.assertTrue(edge['branch_on_action_boundary'])
        backward = bytes([0x04, 0x99, 2, 0, 0xfa, 0xff, 0])
        self.assertEqual(inspect_actions(backward)[0]['branch'], 0)

    def test_unconditional_jump_invalid_payload_and_target(self):
        with self.assertRaises(ValueError):
            inspect_actions(bytes([0x99, 1, 0, 0, 0]))
        edge = inspect_actions(bytes([0x99, 2, 0, 0xfe, 0xff, 0]))[0]
        self.assertFalse(edge['branch_on_action_boundary'])

    def test_non_boundary_target(self):
        # IF at 0 ends at 5; -2 targets byte 3 inside its operand.
        data = bytes([0x9d, 2, 0, 0xfe, 0xff, 0x04, 0])
        self.assertFalse(inspect_actions(data)[0]['branch_on_action_boundary'])


if __name__ == '__main__':
    unittest.main()
