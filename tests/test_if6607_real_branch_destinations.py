"""Verify actual IF 6607 branch destinations are decoded action boundaries.

Static bytecode evidence only: no assertion about runtime reachability,
variable values, NPCs, quests, or story effects.
"""
import unittest
from pathlib import Path

from tools.probe_if6607_structure import (
    decode_records, extract_root_action, inspect_target, verify_source_fingerprint,
)

EXPECTED_SHA256 = "d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30"


class RealIf6607BranchDestinationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path("jin.swf")
        if not source.is_file():
            raise unittest.SkipTest("jin.swf missing: real-byte branch tests unavailable")
        verify_source_fingerprint(source, EXPECTED_SHA256)
        cls.action = extract_root_action(source, frame=55, tag_ordinal=9)

    def test_both_destinations_match_independently_decoded_boundaries(self):
        records = decode_records(self.action)
        by_start = {start: (end, opcode) for start, end, opcode, _ in records}
        report = inspect_target(self.action, 6607)
        self.assertEqual(by_start[6607][1], 0x9D)
        self.assertEqual(report["fallthrough_offset"], by_start[6607][0])
        self.assertEqual(report["fallthrough_offset"], 6612)
        self.assertEqual(report["branch_offset"], 6623)
        self.assertEqual(report["relative_displacement"], 11)
        for offset, key in (
            (report["fallthrough_offset"], "fallthrough_opcode_hex"),
            (report["branch_offset"], "branch_opcode_hex"),
        ):
            self.assertIn(offset, by_start)
            self.assertEqual(report[key], f"{by_start[offset][1]:02x}")

    def test_linear_windows_are_not_execution_or_story_evidence(self):
        report = inspect_target(self.action, 6607)
        self.assertEqual(report["condition_stack_origin"], "unknown")
        self.assertEqual(report["true_path_effects"], "unknown")
        self.assertEqual(report["false_path_effects"], "unknown")
        self.assertEqual(report["verified_story_events"], 0)
        self.assertEqual(
            report["branch_entry_same_as_fallthrough"],
            report["branch_offset"] == report["fallthrough_offset"],
        )
        for name, start in (
            ("fallthrough_linear_window", report["fallthrough_offset"]),
            ("branch_linear_window", report["branch_offset"]),
        ):
            self.assertTrue(report[name])
            self.assertEqual(report[name][0]["offset"], start)


if __name__ == "__main__":
    unittest.main()
