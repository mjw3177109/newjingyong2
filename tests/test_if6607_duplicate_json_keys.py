"""Regression tests for duplicate-key rejection in private IF6607 attestations."""
import json
import unittest
from tools.validate_if6607_private_attestation import reject_duplicate_keys


class DuplicateKeyTests(unittest.TestCase):
    def test_rejects_duplicate_top_level_key(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON key: status"):
            json.loads('{"status":"unverified","status":"private_review_complete"}',
                       object_pairs_hook=reject_duplicate_keys)

    def test_rejects_duplicate_nested_key(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON key: source_sha256"):
            json.loads('{"nested":{"source_sha256":"a","source_sha256":"b"}}',
                       object_pairs_hook=reject_duplicate_keys)

    def test_accepts_unique_keys(self):
        self.assertEqual(json.loads('{"candidate_id":"demo","status":null}',
                                    object_pairs_hook=reject_duplicate_keys),
                         {"candidate_id": "demo", "status": None})


if __name__ == "__main__":
    unittest.main()
