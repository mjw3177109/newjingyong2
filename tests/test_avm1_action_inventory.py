import unittest

from tools.avm1_action_inventory import inspect_stream


class ActionInventoryTests(unittest.TestCase):
    def test_push_and_branch_offsets(self):
        data = bytes.fromhex("96040007010000009d0200000000")
        result = inspect_stream(data)
        self.assertEqual(result["pushes"], [{"offset": 0, "values": [{"type": "integer", "value": 1}]}])
        self.assertEqual(result["edges"][0]["offset"], 7)
        self.assertTrue(result["edges"][0]["branch_on_action_boundary"])

    def test_invalid_push_reports_offset(self):
        with self.assertRaisesRegex(ValueError, "ActionPush at offset 0"):
            inspect_stream(bytes.fromhex("9602000700"))

    def test_invalid_branch_target_is_reported(self):
        result = inspect_stream(bytes.fromhex("990200ffff00"))
        self.assertFalse(result["edges"][0]["branch_on_action_boundary"])

    def test_truncated_action_rejected(self):
        with self.assertRaises(ValueError):
            inspect_stream(bytes.fromhex("96040007"))


if __name__ == "__main__":
    unittest.main()
