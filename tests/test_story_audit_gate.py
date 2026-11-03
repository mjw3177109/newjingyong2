"""Synthetic tests: no copyrighted source text or SWF content."""
import unittest
from tools.validate_story_audit import validate

H = "a" * 64


def record(**changes):
    row = dict(candidate_id="anon_001", swf_sha256=H, export_pair_id="pair_1",
               timeline_and_frame="main:55", script_sha256=H, evidence_offset="offset:9",
               trigger_summary="conditional branch", effect_summary="state transition",
               negative_path_checked=True, cross_check="independent bytecode review",
               status="verified", html5_mapping="none", rights_status="unknown")
    row.update(changes)
    return row


class AuditGateTests(unittest.TestCase):
    def test_verified_with_unknown_rights_is_not_publication(self):
        self.assertEqual(validate([record()]), [])

    def test_missing_negative_branch_blocks_verification(self):
        self.assertTrue(validate([record(negative_path_checked=False)]))

    def test_unknown_timeline_blocks_verification(self):
        self.assertTrue(validate([record(timeline_and_frame="unknown")]))

    def test_unverified_cannot_claim_mapping(self):
        self.assertTrue(validate([record(status="partial", html5_mapping="quest_1")]))

    def test_unauthorized_publication_rejected(self):
        self.assertTrue(validate([record(publication_ready=True)]))

    def test_duplicate_anonymous_ids_rejected(self):
        self.assertTrue(validate([record(), record()]))

    def test_non_string_status_rejected_without_exception(self):
        self.assertTrue(validate([record(status=[])]))
        self.assertTrue(validate([record(rights_status={})]))

    def test_publication_ready_requires_boolean(self):
        self.assertTrue(validate([record(rights_status="authorized", publication_ready="false")]))

    def test_numeric_negative_path_flag_rejected(self):
        self.assertTrue(validate([record(negative_path_checked=1)]))
        self.assertTrue(validate([record(negative_path_checked=0)]))
        self.assertTrue(validate([record(status="partial", negative_path_checked=1)]))

    def test_authorized_but_unverified_cannot_publish(self):
        self.assertTrue(validate([record(status="partial", rights_status="authorized", publication_ready=True)]))

    def test_mapping_rejects_unhashable_and_empty_values(self):
        for value in ([], {}, 1, "", "   "):
            with self.subTest(value=value):
                self.assertTrue(validate([record(html5_mapping=value)]))

    def test_verified_authorized_record_can_pass_publication_gate(self):
        self.assertEqual(validate([record(rights_status="authorized", publication_ready=True)]), [])

    def test_invalid_hash_rejected(self):
        self.assertTrue(validate([record(script_sha256="not-a-hash")]))


if __name__ == "__main__":
    unittest.main()
