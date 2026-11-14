"""Negative tests for the private IF6607 evidence schema (synthetic only)."""
import unittest

from tools.validate_if6607_private_attestation import validate


def sample():
    return {
        "candidate_id": "root-f55-doaction9-if6607",
        "source_sha256": "a" * 64,
        "export_a_sha256": "b" * 64,
        "export_b_sha256": "b" * 64,
        "offset_verified": True,
        "stack_condition_verified": True,
        "true_path_verified": True,
        "false_path_verified": True,
        "independent_review_verified": True,
        "rights_evidence_ref": "private/review-001",
    }


class IF6607PrivateEvidenceEdgeCases(unittest.TestCase):
    def test_wrong_candidate_rejected(self):
        record = sample()
        record["candidate_id"] = "root-f55-doaction9-if6608"
        self.assertIn("candidate_id mismatch", validate(record))

    def test_invalid_source_hash_rejected(self):
        record = sample()
        record["source_sha256"] = "NOT_A_SHA256"
        self.assertIn("invalid source_sha256", validate(record))

    def test_missing_independent_review_rejected(self):
        record = sample()
        record["independent_review_verified"] = 1
        self.assertIn("not verified: independent_review_verified", validate(record))

    def test_invalid_status_rejected(self):
        record = sample()
        record["status"] = "published"
        self.assertIn("invalid status", validate(record))

    def test_rights_reference_traversal_rejected(self):
        for ref in ("../../private", "private/../secret", "private/./secret", "private//secret"):
            with self.subTest(ref=ref):
                record = sample()
                record["rights_evidence_ref"] = ref
                self.assertIn("rights evidence reference missing or unsafe", validate(record))

    def test_absolute_and_url_rights_references_rejected(self):
        for ref in ("/private/review", "https://example.com/proof", "C:/private/review", "private\\\\review", "private/review?token=abc"):
            with self.subTest(ref=ref):
                record = sample()
                record["rights_evidence_ref"] = ref
                self.assertIn("rights evidence reference missing or unsafe", validate(record))

    def test_relative_rights_reference_remains_valid(self):
        record = sample()
        record["rights_evidence_ref"] = "private/review-001"
        self.assertEqual([], validate(record))

    def test_unsafe_rights_reference_rejected(self):
        record = sample()
        record["rights_evidence_ref"] = "../../private rights\nsource"
        self.assertIn("rights evidence reference missing or unsafe", validate(record))


if __name__ == "__main__":
    unittest.main()
