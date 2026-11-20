"""Regression checks for IF 6607 predecessor flags against actual SWF bytes.

These assertions verify only opcode boundaries, never story semantics.
"""
import unittest
from pathlib import Path

from tools.probe_if6607_stack_boundary import predecessor_audit
from tools.probe_if6607_structure import extract_root_action, verify_source_fingerprint

EXPECTED_SHA256 = "d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30"


class RealPredecessorFlagConsistencyTests(unittest.TestCase):
    def test_real_swf_flags_match_immediate_opcode(self):
        source = Path("jin.swf")
        if not source.is_file():
            self.skipTest("jin.swf not available; real-byte verification not performed")
        verify_source_fingerprint(source, EXPECTED_SHA256)
        report = predecessor_audit(extract_root_action(source, 55, 9))
        before_if = report["if_immediate_predecessors"]
        before_set = report["set_variable_immediate_predecessors"]
        self.assertEqual(report["if_preceded_by_less2"],
                         any(p["opcode_hex"] == "48" for p in before_if))
        self.assertEqual(report["if_preceded_by_not"],
                         any(p["opcode_hex"] == "12" for p in before_if))
        self.assertEqual(report["set_variable_preceded_by_push"],
                         any(p["opcode_hex"] == "96" for p in before_set))
        self.assertLessEqual(len(before_if), 1)
        self.assertLessEqual(len(before_set), 1)
        self.assertFalse(report["if_preceded_by_less2"] and report["if_preceded_by_not"])
        self.assertEqual(report["condition_stack_origin"], "unknown")
        self.assertEqual(report["runtime_reachability"], "unknown")
        self.assertEqual(report["verified_story_events"], 0)


if __name__ == "__main__":
    unittest.main()
