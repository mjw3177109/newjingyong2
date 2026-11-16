#!/usr/bin/env python3
"""Regression tests for the private IF evidence structural gate (synthetic data only)."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validate_private_if_evidence.py"
spec = importlib.util.spec_from_file_location("private_if_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def fixture():
    return {
        "schema_version": 1,
        "source_swf_sha256": "a" * 64,
        "ffdec_jar_sha256": "b" * 64,
        "java_version": "1.8.0_402",
        "export_a_manifest_sha256": "c" * 64,
        "export_b_manifest_sha256": "c" * 64,
        "timeline_frame": 55,
        "doaction_index": 9,
        "if_offset": 6607,
        "fallthrough_offset": 6612,
        "jump_target_offset": 6623,
        "predicate_trace_ref": "private/predicate.json",
        "true_branch_ref": "private/true.json",
        "false_branch_ref": "private/false.json",
        "independent_review_ref": "private/review.json",
        "rights_evidence_ref": "private/rights.json",
    }

class EvidenceGateTests(unittest.TestCase):
    def test_complete_synthetic_record_is_structurally_accepted(self):
        ok, msg = gate.validate(fixture())
        self.assertTrue(ok, msg)
        self.assertIn("structural", msg)

    def test_missing_and_extra_fields_fail_closed(self):
        for mutation in ("missing", "extra"):
            with self.subTest(mutation=mutation):
                record = fixture()
                if mutation == "missing":
                    del record["predicate_trace_ref"]
                else:
                    record["unreviewed"] = "unexpected"
                self.assertFalse(gate.validate(record)[0])

    def test_invalid_digest_and_divergent_exports(self):
        for key, value in (
            ("source_swf_sha256", "A" * 64),
            ("ffdec_jar_sha256", "not-a-hash"),
            ("export_b_manifest_sha256", "d" * 64),
        ):
            with self.subTest(key=key):
                record = fixture()
                record[key] = value
                self.assertFalse(gate.validate(record)[0])

    def test_if_identity_and_boolean_offsets_rejected(self):
        for key, value in (
            ("timeline_frame", 56),
            ("doaction_index", True),
            ("if_offset", 6608),
            ("fallthrough_offset", 6623),
            ("jump_target_offset", 6612),
        ):
            with self.subTest(key=key):
                record = fixture()
                record[key] = value
                self.assertFalse(gate.validate(record)[0])

    def test_placeholder_and_multiline_references_rejected(self):
        for key, value in (
            ("predicate_trace_ref", "pending"),
            ("true_branch_ref", "unknown"),
            ("false_branch_ref", "a\nb"),
            ("true_branch_ref", "a\rb"),
            ("independent_review_ref", ""),
            ("rights_evidence_ref", "none"),
        ):
            with self.subTest(key=key):
                record = fixture()
                record[key] = value
                self.assertFalse(gate.validate(record)[0])

    def test_java8_and_safe_relative_references_required(self):
        for version in ("17.0.1", "1.7.0_80", "java 8", " 1.8.0_402"):
            with self.subTest(version=version):
                record = fixture()
                record["java_version"] = version
                self.assertFalse(gate.validate(record)[0])
        for ref in ("../secrets", "/private/trace", "https://example.com/a", "C:\\\\private", "private/../trace", "private\\\\trace", "private/trace?raw=1", "private/trace.json "):
            with self.subTest(ref=ref):
                record = fixture()
                record["predicate_trace_ref"] = ref
                self.assertFalse(gate.validate(record)[0])

    def test_digest_type_and_java_version_types_fail_closed(self):
        for key, value in (
            ("source_swf_sha256", None),
            ("ffdec_jar_sha256", 123),
            ("export_a_manifest_sha256", []),
            ("java_version", 8),
            ("predicate_trace_ref", ["private/predicate.json"]),
        ):
            with self.subTest(key=key):
                record = fixture()
                record[key] = value
                self.assertFalse(gate.validate(record)[0])

    def test_all_evidence_references_reject_unsafe_paths(self):
        keys = (
            "predicate_trace_ref", "true_branch_ref", "false_branch_ref",
            "independent_review_ref", "rights_evidence_ref",
        )
        for key in keys:
            for ref in ("../outside.json", "private/../outside.json", "/absolute.json", "https://example.org/x"):
                with self.subTest(key=key, ref=ref):
                    record = fixture()
                    record[key] = ref
                    self.assertFalse(gate.validate(record)[0])

    def test_wrong_schema_and_non_object_rejected(self):
        record = fixture()
        record["schema_version"] = 2
        self.assertFalse(gate.validate(record)[0])
        self.assertFalse(gate.validate([])[0])

if __name__ == "__main__":
    unittest.main()
