#!/usr/bin/env python3
"""Regression tests for IF6607 private metadata shape validator.

All fixtures are synthetic; no SWF source, traces, or story semantics are included.
Run: python -m unittest discover -s tests -p 'test_if6607_trace.py'
"""
import copy
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validate_if6607_trace.py"
spec = importlib.util.spec_from_file_location("if6607_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

H = "a" * 64


def fixture():
    return {
        "swf_sha256": H,
        "ffdec_version": "synthetic-test-version",
        "java_version": "synthetic-test-version",
        "export_batch": "synthetic-test-batch",
        "frame": 55,
        "doaction_index": 9,
        "if_offset": 6607,
        "fallthrough_offset": 6612,
        "jump_offset": 6623,
        "condition_stack": {"status": "unresolved", "evidence_sha256": None},
        "branches": {
            "true": {"status": "unresolved", "trace_sha256": None, "state_delta_summary": "not examined"},
            "false": {"status": "unresolved", "trace_sha256": None, "state_delta_summary": "not examined"},
        },
        "independent_reviewer": {"status": "pending"},
        "rights_review": {"status": "pending"},
    }


class TraceMetadataTests(unittest.TestCase):
    def test_synthetic_unresolved_metadata_is_valid_shape_only(self):
        self.assertEqual(validator.validate(fixture()), [])

    def test_unresolved_cannot_claim_trace_hash(self):
        doc = fixture()
        doc["branches"]["true"]["trace_sha256"] = H
        self.assertTrue(validator.validate(doc))

    def test_unresolved_false_branch_rejects_hash(self):
        doc = fixture()
        doc["branches"]["false"]["trace_sha256"] = H
        self.assertTrue(validator.validate(doc))

    def test_resolved_requires_evidence_hash(self):
        doc = fixture()
        doc["condition_stack"]["status"] = "resolved"
        self.assertTrue(validator.validate(doc))
        doc["condition_stack"]["evidence_sha256"] = H
        self.assertEqual(validator.validate(doc), [])

    def test_reproduced_requires_trace_hash(self):
        doc = fixture()
        doc["branches"]["false"]["status"] = "reproduced"
        self.assertTrue(validator.validate(doc))
        doc["branches"]["false"]["trace_sha256"] = H
        self.assertEqual(validator.validate(doc), [])

    def test_non_object_root(self):
        self.assertTrue(validator.validate([]))

    def test_missing_required_field(self):
        doc = fixture()
        del doc["rights_review"]
        self.assertTrue(validator.validate(doc))

    def test_invalid_swf_hash(self):
        doc = fixture()
        doc["swf_sha256"] = "NOT-A-SHA"
        self.assertTrue(validator.validate(doc))

    def test_boolean_is_not_integer_offset(self):
        doc = fixture()
        doc["frame"] = True
        self.assertTrue(validator.validate(doc))

    def test_wrong_branch_names(self):
        doc = fixture()
        doc["branches"]["other"] = doc["branches"].pop("false")
        self.assertTrue(validator.validate(doc))

    def test_invalid_branch_payload(self):
        doc = fixture()
        doc["branches"]["true"] = None
        self.assertTrue(validator.validate(doc))

    def test_empty_delta_summary(self):
        doc = fixture()
        doc["branches"]["false"]["state_delta_summary"] = "  "
        self.assertTrue(validator.validate(doc))

    def test_invalid_reviewer_status(self):
        doc = fixture()
        doc["independent_reviewer"]["status"] = "approved"
        self.assertTrue(validator.validate(doc))

    def test_input_is_not_mutated(self):
        doc = fixture()
        original = copy.deepcopy(doc)
        validator.validate(doc)
        self.assertEqual(doc, original)


if __name__ == "__main__":
    unittest.main()
