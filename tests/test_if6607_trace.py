#!/usr/bin/env python3
"""Regression tests for IF6607 private metadata shape validator.

All fixtures are synthetic; no SWF source, traces, or story semantics are included.
Run: python -m unittest discover -s tests -p 'test_if6607_trace.py'
"""
import copy
import importlib.util
import contextlib
import io
import tempfile
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
        doc["branches"]["false"]["state_delta_summary"] = "synthetic: hp 10 to 9"
        self.assertEqual(validator.validate(doc), [])

    def test_reproduced_branch_rejects_unexamined_delta(self):
        doc = fixture()
        doc["branches"]["true"].update(status="reproduced", trace_sha256=H)
        self.assertTrue(validator.validate(doc))
        doc["branches"]["true"]["state_delta_summary"] = "synthetic: inventory 0 to 1"
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

    def test_private_path_is_not_leaked_on_read_error(self):
        private_path = "/private/secret-case-6607-trace.json"
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = validator.main(["validator", private_path])
        self.assertEqual(code, 2)
        self.assertNotIn(private_path, stderr.getvalue())
        self.assertIn("invalid input", stderr.getvalue())

    def test_private_path_is_not_leaked_on_malformed_json(self):
        with tempfile.TemporaryDirectory(prefix="private-case-6607-") as directory:
            private_path = Path(directory) / "secret-trace.json"
            private_path.write_text('{"private_event": ', encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = validator.main(["validator", str(private_path)])
            self.assertEqual(code, 2)
            self.assertNotIn(str(private_path), stderr.getvalue())
            self.assertNotIn(str(private_path), stdout.getvalue())
            self.assertNotIn("private_event", stderr.getvalue())
            self.assertIn("invalid input", stderr.getvalue())

    def test_verified_reviewer_rejects_unresolved_evidence(self):
        doc = fixture()
        doc["independent_reviewer"]["status"] = "verified"
        self.assertIn("independent review cannot be verified", " ".join(validator.validate(doc)))

    def test_verified_reviewer_requires_both_branches(self):
        doc = fixture()
        doc["condition_stack"] = {"status": "resolved", "evidence_sha256": H}
        doc["branches"]["true"].update(status="reproduced", trace_sha256=H)
        doc["independent_reviewer"]["status"] = "verified"
        self.assertTrue(validator.validate(doc))
        doc["branches"]["false"].update(status="reproduced", trace_sha256="b" * 64, state_delta_summary="synthetic: flag 0 to 1")
        doc["branches"]["true"]["state_delta_summary"] = "synthetic: flag 0 to 2"
        self.assertEqual(validator.validate(doc), [])

    def test_two_reproduced_branches_require_distinct_trace_artifacts(self):
        doc = fixture()
        doc["condition_stack"] = {"status": "resolved", "evidence_sha256": H}
        for name in ("true", "false"):
            doc["branches"][name].update(
                status="reproduced", trace_sha256=H,
                state_delta_summary="synthetic: flag changed"
            )
        self.assertIn("distinct trace_sha256", " ".join(validator.validate(doc)))
        doc["branches"]["false"]["trace_sha256"] = "b" * 64
        self.assertEqual(validator.validate(doc), [])

    def test_input_is_not_mutated(self):
        doc = fixture()
        original = copy.deepcopy(doc)
        validator.validate(doc)
        self.assertEqual(doc, original)


if __name__ == "__main__":
    unittest.main()
