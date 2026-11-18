"""Synthetic-only tests for source-free IF structural probe."""
import unittest
import hashlib
import tempfile
from pathlib import Path
from tools.probe_if6607_structure import inspect_target, decode_records, verify_source_fingerprint


class IfStructureTests(unittest.TestCase):
    def test_source_fingerprint_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.swf"
            path.write_bytes(b"synthetic source only")
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(verify_source_fingerprint(path, expected.upper()), expected)
            with self.assertRaisesRegex(ValueError, "does not match"):
                verify_source_fingerprint(path, "0" * 64)

    def test_valid_if(self):
        # ActionIF (5 bytes), ActionNextFrame, ActionPlay, End.
        payload = bytes([0x9d, 2, 0, 1, 0, 0x04, 0x06, 0])
        row = inspect_target(payload, 0)
        self.assertEqual((row["fallthrough_offset"], row["branch_offset"]), (5, 6))
        self.assertEqual(row["verified_story_events"], 0)
        self.assertEqual(row["condition_stack_origin"], "unknown")

    def test_backward_if_to_action_boundary(self):
        # Backward IF edges are legal AVM1 control flow and must not be rejected.
        payload = bytes([0x04, 0x9d, 2, 0, 0xfa, 0xff, 0])
        row = inspect_target(payload, 1)
        self.assertEqual((row["fallthrough_offset"], row["branch_offset"]), (6, 0))
        self.assertEqual(row["relative_displacement"], -6)

    def test_branch_into_operand_is_rejected(self):
        # Offset 3 is inside the IF operand, not an instruction boundary.
        payload = bytes([0x9d, 2, 0, 0xfe, 0xff, 0x04, 0])
        with self.assertRaises(ValueError):
            inspect_target(payload, 0)

    def test_bad_target(self):
        with self.assertRaises(ValueError):
            inspect_target(bytes([0x9d, 2, 0, 2, 0, 0x04, 0]), 0)

    def test_not_if(self):
        with self.assertRaises(ValueError):
            inspect_target(bytes([0x04, 0]), 0)

    def test_truncated(self):
        with self.assertRaises(ValueError):
            decode_records(bytes([0x9d, 2, 0, 0]))

if __name__ == "__main__":
    unittest.main()
