"""Real SWF regression: fail closed on a changed source; never print operands.

Unlike synthetic tests, this checks the exact audited DoAction against jin.swf.
If the binary is not shipped in a checkout, skip rather than invent evidence.
"""
import unittest
from pathlib import Path

from tools.probe_if6607_structure import extract_root_action, verify_source_fingerprint
from tools.probe_if6607_push_types import inventory

ROOT = Path(__file__).resolve().parents[1]
SWF = ROOT / "jin.swf"
EXPECTED_SHA256 = "d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30"


class RealIf6607PushIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(SWF.is_file(), "audited jin.swf absent; real-source test not executed")
    def test_real_push_boundaries_and_source_free_report(self):
        verify_source_fingerprint(SWF, EXPECTED_SHA256)
        action = extract_root_action(SWF, frame=55, tag_ordinal=9)
        report = inventory(action)
        self.assertEqual([item["offset"] for item in report["pushes"]], [6612, 6623, 6629])
        self.assertEqual(report["set_variable_offset"], 6622)
        self.assertTrue(report["set_variable_opcode_confirmed"])
        self.assertEqual(report["verified_story_events"], 0)
        self.assertEqual(report["set_variable_target"], "unknown")
        self.assertEqual(report["set_variable_value"], "unknown")
        self.assertEqual(report["condition_stack_origin"], "unknown")
        for item in report["pushes"]:
            self.assertFalse(item["literal_values_exported"])
            self.assertEqual(len(item["push_type_codes"]), item["value_count"])
            self.assertTrue(all(code in range(10) for code in item["push_type_codes"]))


if __name__ == "__main__":
    unittest.main()
