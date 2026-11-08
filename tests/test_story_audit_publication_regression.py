"""Regression tests for source-free audit publication gates.

All fixtures are synthetic; no SWF source, story text, or assets are used.
"""
import unittest

from tools.validate_story_audit import validate


def record(candidate="candidate_1"):
    return {
        "candidate_id": candidate,
        "swf_sha256": "a" * 64,
        "export_pair_id": "synthetic-pair",
        "timeline_and_frame": "synthetic-frame",
        "script_sha256": "b" * 64,
        "evidence_offset": "synthetic-offset",
        "trigger_summary": "Synthetic trigger checked",
        "effect_summary": "Synthetic effect checked",
        "negative_path_checked": True,
        "cross_check": "Synthetic independent review",
        "status": "verified",
        "html5_mapping": "syntheticEvent",
        "rights_status": "authorized",
        "rights_scope": "adaptation_and_distribution",
        "rights_evidence_ref": "synthetic-license-ref",
        "publication_ready": True,
    }


class PublicationGateRegressionTests(unittest.TestCase):
    def test_synthetic_complete_record_passes_format_gate_only(self):
        self.assertEqual(validate([record()]), [])

    def test_duplicate_publication_mapping_is_rejected(self):
        errors = validate([record("candidate_1"), record("candidate_2")])
        self.assertTrue(any("duplicate publication HTML5 mapping" in e for e in errors), errors)

    def test_analysis_only_rights_cannot_publish(self):
        item = record()
        item["rights_scope"] = "analysis_only"
        errors = validate([item])
        self.assertTrue(any("publication requires adaptation_and_distribution" in e for e in errors), errors)

    def test_unverified_candidate_cannot_publish(self):
        item = record()
        item["status"] = "unverified"
        errors = validate([item])
        self.assertTrue(any("publication requires verified evidence" in e for e in errors), errors)

    def test_same_export_pair_cannot_mix_different_swf_sources(self):
        first = record("candidate_1")
        second = record("candidate_2")
        second["html5_mapping"] = "syntheticEvent2"
        second["swf_sha256"] = "c" * 64
        errors = validate([first, second])
        self.assertTrue(any("conflicting SWF digests" in e for e in errors), errors)

    def test_same_export_pair_allows_same_swf_source(self):
        first = record("candidate_1")
        second = record("candidate_2")
        second["html5_mapping"] = "syntheticEvent2"
        self.assertEqual(validate([first, second]), [])

    def test_raw_source_field_is_rejected(self):
        item = record()
        item["raw_actionscript"] = "synthetic source placeholder"
        errors = validate([item])
        self.assertTrue(any("unexpected fields" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
