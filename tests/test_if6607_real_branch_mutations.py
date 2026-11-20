"""Mutation regression for IF 6607: reject non-boundary jump targets.

All assertions concern bytecode structure, not story or runtime effects.
"""
import struct
import unittest
from pathlib import Path

from tools.probe_if6607_structure import (
    decode_records, extract_root_action, inspect_target, verify_source_fingerprint,
)

EXPECTED_SHA256 = "d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30"


class RealIf6607MutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path("jin.swf")
        if not source.is_file():
            raise unittest.SkipTest("jin.swf unavailable; real-byte mutation tests skipped")
        verify_source_fingerprint(source, EXPECTED_SHA256)
        cls.action = extract_root_action(source, frame=55, tag_ordinal=9)

    def test_jump_into_middle_of_push_is_rejected(self):
        records = {start: (end, opcode, body)
                   for start, end, opcode, body in decode_records(self.action)}
        self.assertEqual(records[6607][1], 0x9D)
        self.assertEqual(records[6607][0], 6612)
        self.assertEqual(records[6612][1], 0x96)
        mutated = bytearray(self.action)
        struct.pack_into("<h", mutated, records[6607][2], 1)
        with self.assertRaisesRegex(ValueError, "branch target not an action boundary"):
            inspect_target(bytes(mutated), 6607)

    def test_backward_jump_to_decoded_boundary_is_accepted(self):
        records = {start: (end, opcode, body)
                   for start, end, opcode, body in decode_records(self.action)}
        self.assertEqual(records[6604][1], 0x48)  # Less2
        mutated = bytearray(self.action)
        displacement = 6604 - records[6607][0]
        self.assertLess(displacement, 0)
        struct.pack_into("<h", mutated, records[6607][2], displacement)
        report = inspect_target(bytes(mutated), 6607)
        self.assertEqual(report["branch_offset"], 6604)
        self.assertEqual(report["relative_displacement"], displacement)
        self.assertFalse(report["branch_entry_same_as_fallthrough"])
        self.assertEqual(report["condition_stack_origin"], "unknown")
        self.assertEqual(report["verified_story_events"], 0)

    def test_backward_jump_into_instruction_body_is_rejected(self):
        records = {start: (end, opcode, body)
                   for start, end, opcode, body in decode_records(self.action)}
        mutated = bytearray(self.action)
        # Less2 at 6604 is one byte long: 6605 is itself a valid
        # instruction boundary, not an interior byte. Select an actual
        # multi-byte record in the decoded stream instead.
        candidates = [start for start, (end, _opcode, _body) in records.items()
                      if start < 6607 and end - start > 1]
        self.assertTrue(candidates, "expected a multi-byte preceding AVM1 action")
        interior = max(candidates) + 1
        self.assertNotIn(interior, records)
        struct.pack_into("<h", mutated, records[6607][2], interior - records[6607][0])
        with self.assertRaisesRegex(ValueError, "branch target not an action boundary"):
            inspect_target(bytes(mutated), 6607)

    def test_zero_displacement_is_detected_as_shared_entry(self):
        records = {start: (end, opcode, body)
                   for start, end, opcode, body in decode_records(self.action)}
        mutated = bytearray(self.action)
        struct.pack_into("<h", mutated, records[6607][2], 0)
        report = inspect_target(bytes(mutated), 6607)
        self.assertEqual(report["branch_offset"], 6612)
        self.assertTrue(report["branch_entry_same_as_fallthrough"])
        self.assertEqual(report["condition_stack_origin"], "unknown")
        self.assertEqual(report["verified_story_events"], 0)


if __name__ == "__main__":
    unittest.main()
