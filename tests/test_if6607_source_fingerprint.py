"""Synthetic tests for independently pinned source fingerprint checks."""
import unittest
from tools.validate_if6607_private_attestation import validate

SOURCE = "d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30"

def record():
    return {
        "candidate_id": "root-f55-doaction9-if6607",
        "source_sha256": SOURCE,
        "export_a_sha256": "a" * 64,
        "export_b_sha256": "a" * 64,
        "offset_verified": True,
        "stack_condition_verified": True,
        "true_path_verified": True,
        "false_path_verified": True,
        "independent_review_verified": True,
        "rights_evidence_ref": "private/review-001",
    }

class SourceFingerprintTests(unittest.TestCase):
    def test_matching_independent_fingerprint(self):
        self.assertEqual([], validate(record(), expected_source_sha256=SOURCE))

    def test_changed_source_blocked(self):
        self.assertIn("source sha256 mismatch", validate(record(), expected_source_sha256="b" * 64))

    def test_invalid_expected_fingerprint_blocked(self):
        self.assertIn("invalid expected source sha256", validate(record(), expected_source_sha256="bad"))

if __name__ == "__main__":
    unittest.main()
