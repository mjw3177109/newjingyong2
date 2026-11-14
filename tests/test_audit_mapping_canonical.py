"""Regression: audit mapping IDs must be canonical, without padding."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_story_audit", ROOT / "tools" / "validate_story_audit.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample():
    return {
        "candidate_id": "SRC-example",
        "swf_sha256": "a" * 64,
        "export_pair_id": None,
        "timeline_and_frame": None,
        "script_sha256": "b" * 64,
        "evidence_offset": None,
        "trigger_summary": None,
        "effect_summary": None,
        "negative_path_checked": False,
        "cross_check": None,
        "status": "unverified",
        "html5_mapping": None,
        "rights_status": "unknown",
        "rights_scope": "none",
        "rights_evidence_ref": None,
    }


class CanonicalMappingTests(unittest.TestCase):
    def test_unverified_null_mapping_is_allowed(self):
        self.assertEqual(module.validate([sample()]), [])

    def test_whitespace_padded_mapping_rejected(self):
        row = sample()
        row.update({
            "status": "verified",
            "html5_mapping": " demo_event ",
            "export_pair_id": "pair-1",
            "timeline_and_frame": "root frame 55",
            "evidence_offset": "offset 1",
            "trigger_summary": "privately checked trigger",
            "effect_summary": "privately checked effect",
            "cross_check": "independent check",
            "negative_path_checked": True,
        })
        errors = module.validate([row])
        self.assertTrue(any("html5_mapping" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
