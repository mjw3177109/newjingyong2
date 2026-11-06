import unittest
from tools.avm1_if_edges import inspect_actions


class Avm1IfEdgesTests(unittest.TestCase):
    def test_forward_and_fallthrough(self):
        data = bytes([0x9d, 2, 0, 1, 0, 0x04, 0x04, 0])
        self.assertEqual(inspect_actions(data), [{
            'offset': 0, 'fallthrough': 5, 'branch': 6,
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

    def test_non_boundary_target(self):
        data = bytes([0x9d, 2, 0, 2, 0, 0x04, 0])
        self.assertFalse(inspect_actions(data)[0]['branch_on_action_boundary'])


if __name__ == '__main__':
    unittest.main()
