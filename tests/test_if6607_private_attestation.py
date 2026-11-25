import unittest

from tools.validate_if6607_private_attestation import validate

H = "a" * 64

def valid():
    return {
        "candidate_id": "root-f55-doaction9-if6607",
        "source_sha256": H,
        "export_a_sha256": H,
        "export_b_sha256": H,
        "offset_verified": True,
        "stack_condition_verified": True,
        "true_path_verified": True,
        "false_path_verified": True,
        "independent_review_verified": True,
        "rights_evidence_ref": "private/rights-001",
    }

class IF6607AttestationTests(unittest.TestCase):
    def test_complete_fields(self):
        self.assertEqual(validate(valid()), [])

    def test_missing_true_path(self):
        data = valid()
        data["true_path_verified"] = False
        self.assertTrue(validate(data))

    def test_export_drift(self):
        data = valid()
        data["export_b_sha256"] = "b" * 64
        self.assertIn("export hashes differ", validate(data))

    def test_unknown_source_text_rejected(self):
        data = valid()
        data["raw_actionscript"] = "DO NOT PUBLISH"
        self.assertTrue(any("unknown fields" in x for x in validate(data)))

    def test_missing_rights(self):
        data = valid()
        data["rights_evidence_ref"] = ""
        self.assertTrue(validate(data))

    def test_not_object(self):
        self.assertTrue(validate([]))

if __name__ == "__main__":
    unittest.main()
