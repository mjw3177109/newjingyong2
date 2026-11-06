"""Synthetic tests: no copyrighted source text or SWF content."""
import unittest
from tools.validate_story_audit import validate

H = "a" * 64


def record(**changes):
    row = dict(candidate_id="anon_001", swf_sha256=H, export_pair_id="pair_1",
               timeline_and_frame="main:55", script_sha256=H, evidence_offset="offset:9",
               trigger_summary="conditional branch", effect_summary="state transition",
               negative_path_checked=True, cross_check="independent bytecode review",
               status="verified", html5_mapping="none", rights_status="unknown",
               rights_scope="none", rights_evidence_ref=None)
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
        self.assertTrue(validate([record(status="partial", rights_status="authorized",
                                         rights_scope="adaptation_and_distribution",
                                         rights_evidence_ref="rights-doc:license-2026",
                                         publication_ready=True)]))

    def test_mapping_rejects_unhashable_and_empty_values(self):
        for value in ([], {}, 1, "", "   "):
            with self.subTest(value=value):
                self.assertTrue(validate([record(html5_mapping=value)]))

    def test_verified_authorized_record_can_pass_publication_gate(self):
        self.assertEqual(validate([record(
            rights_status="authorized",
            rights_scope="adaptation_and_distribution",
            rights_evidence_ref="rights-doc:license-2026",
            publication_ready=True,
            html5_mapping="quest_1"
        )]), [])

    def test_publication_requires_concrete_html5_mapping(self):
        for mapping in (None, "none", "unknown", " NONE "):
            with self.subTest(mapping=mapping):
                self.assertTrue(validate([record(
                    rights_status="authorized",
                    rights_scope="adaptation_and_distribution",
                    rights_evidence_ref="rights-doc:license-2026",
                    publication_ready=True,
                    html5_mapping=mapping
                )]))

    def test_partial_record_rejects_structured_evidence_fields(self):
        for key in ("export_pair_id", "timeline_and_frame", "evidence_offset",
                    "trigger_summary", "effect_summary", "cross_check"):
            with self.subTest(field=key):
                self.assertTrue(validate([record(status="partial", **{key: {"unexpected": "object"}})]))
                self.assertTrue(validate([record(status="unverified", **{key: [1, 2]})]))

    def test_partial_record_allows_null_evidence_pending_review(self):
        self.assertEqual(validate([record(status="partial", trigger_summary=None,
                                          effect_summary=None, cross_check=None)]), [])

    def test_verified_rejects_placeholder_evidence(self):
        for field in ("export_pair_id", "timeline_and_frame", "evidence_offset",
                      "trigger_summary", "effect_summary", "cross_check"):
            for placeholder in ("n/a", "TBD", "pending", "not checked"):
                with self.subTest(field=field, placeholder=placeholder):
                    self.assertTrue(validate([record(**{field: placeholder})]))

    def test_publication_rejects_placeholder_mapping(self):
        for mapping in ("tbd", "pending", "n/a", "todo"):
            with self.subTest(mapping=mapping):
                self.assertTrue(validate([record(
                    rights_status="authorized",
                    rights_scope="adaptation_and_distribution",
                    rights_evidence_ref="rights-doc:license-2026",
                    publication_ready=True,
                    html5_mapping=mapping
                )]))

    def test_invalid_hash_rejected(self):
        self.assertTrue(validate([record(script_sha256="not-a-hash")]))

    def test_authorized_rights_require_evidence_reference(self):
        self.assertTrue(validate([record(
            rights_status="authorized",
            rights_scope="adaptation_and_distribution",
            rights_evidence_ref=None
        )]))

    def test_analysis_only_rights_cannot_publish(self):
        self.assertTrue(validate([record(
            rights_status="authorized",
            rights_scope="analysis_only",
            rights_evidence_ref="rights-doc:analysis-only",
            publication_ready=True,
            html5_mapping="quest_1"
        )]))

    def test_restricted_rights_cannot_claim_adaptation_scope(self):
        self.assertTrue(validate([record(
            rights_status="restricted",
            rights_scope="adaptation_and_distribution",
            rights_evidence_ref="rights-doc:restricted"
        )]))

    def test_unknown_rights_cannot_claim_scope_or_evidence(self):
        self.assertTrue(validate([record(
            rights_status="unknown",
            rights_scope="adaptation_only",
            rights_evidence_ref="rights-doc:unknown"
        )]))

    def test_unknown_fields_reject_possible_source_material(self):
        for key in ("source_text", "raw_actionscript", "dialogue", "source_path", "media_url"):
            with self.subTest(field=key):
                self.assertTrue(validate([record(**{key: "must not enter public ledger"})]))

    def test_evidence_summaries_are_bounded_and_single_line(self):
        self.assertTrue(validate([record(trigger_summary="x" * 241)]))
        self.assertTrue(validate([record(effect_summary="line one\nline two")]))

    def test_mapping_rejects_multiline_and_oversized_or_source_like_values(self):
        for mapping in ("quest_1\nraw script", "x" * 101, "script/path",
                        "quest 1", "https://example.test/source", "事件原文"):
            with self.subTest(mapping=mapping):
                self.assertTrue(validate([record(html5_mapping=mapping)]))

    def test_public_evidence_rejects_control_characters(self):
        for value in ("safe\tunsafe", "safe\x1b[31m", "safe\x7funsafe", "safe\x01unsafe"):
            with self.subTest(value=repr(value)):
                self.assertTrue(validate([record(trigger_summary=value)]))
                self.assertTrue(validate([record(rights_status="authorized",
                                                 rights_scope="adaptation_and_distribution",
                                                 rights_evidence_ref=value)]))

    def test_safe_mapping_identifier_remains_valid(self):
        self.assertEqual(validate([record(html5_mapping="quest_trial-1")]), [])

    def test_noncanonical_none_mapping_is_rejected_before_verification(self):
        for mapping in (" NONE ", "None", "NONE", " none"):
            with self.subTest(mapping=mapping):
                self.assertTrue(validate([record(status="partial", html5_mapping=mapping)]))
        self.assertEqual(validate([record(status="partial", html5_mapping="none")]), [])


if __name__ == "__main__":
    unittest.main()
