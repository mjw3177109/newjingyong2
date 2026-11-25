"""Cross-check independently decoded IF 6607 reports on the same real SWF.

Only structural assertions; no story semantics or protected literals exported.
"""
import hashlib
import unittest
from pathlib import Path

from tools.probe_if6607_structure import (
    extract_root_action, inspect_target, verify_source_fingerprint,
)
from tools.probe_if6607_stack_boundary import predecessor_audit

SWF_SHA256 = "d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30"


class RealIf6607CrossReportTests(unittest.TestCase):
    def test_branch_and_predecessor_reports_share_action_identity(self):
        source = Path("jin.swf")
        if not source.is_file():
            self.skipTest("jin.swf missing; real SWF cross-check not executed")
        verify_source_fingerprint(source, SWF_SHA256)
        action = extract_root_action(source, 55, 9)
        branch = inspect_target(action, 6607)
        predecessor = predecessor_audit(action, 6607, 6622)

        self.assertEqual(branch["action_sha256"], hashlib.sha256(action).hexdigest())
        self.assertEqual(branch["if_offset"], predecessor["if_offset"])
        self.assertEqual(branch["fallthrough_offset"], branch["if_offset"] + 5)
        self.assertNotEqual(branch["branch_offset"], branch["if_offset"])
        self.assertEqual(predecessor["set_variable_offset"], 6622)
        for record in predecessor["if_immediate_predecessors"]:
            self.assertLess(record["offset"], branch["if_offset"])
            self.assertIn(
                record,
                branch["prior_opcode_window"],
                "immediate predecessor must appear in bounded preceding opcode window",
            )
        self.assertEqual(branch["condition_stack_origin"], "unknown")
        self.assertEqual(predecessor["condition_stack_origin"], "unknown")
        self.assertEqual(branch["verified_story_events"], 0)
        self.assertEqual(predecessor["verified_story_events"], 0)


if __name__ == "__main__":
    unittest.main()
