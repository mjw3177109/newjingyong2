"""Synthetic source-free checks: no original SWF content or story claims."""
import copy
import unittest
from tools.crosscheck_root_if_handoff import crosscheck


def fixtures():
    rid = 'a' * 24
    handoff = {
        'schema': 'swf-root-if-audit-handoff-v1', 'source_swf_sha256': 'b' * 64,
        'candidate_count': 1, 'verified_story_events': 0, 'ready_for_html5_mapping': 0,
        'entries': [{'review_id': rid, 'source_location': {
            'root_frame': 9, 'action_tag_ordinal': 2, 'if_source_offset': 15,
            'action_sha256': 'c' * 64, 'branch_target_offset': 20, 'fallthrough_offset': 20},
            'checks': {'ffdec_script_sha256': None, 'condition_confirmed': False,
                       'state_effects_confirmed': False, 'map_context_confirmed': False,
                       'runtime_reproduced': False, 'independent_reviewed': False,
                       'adaptation_rights_confirmed': False},
            'review_status': 'unverified', 'html5_event_id': None}],
    }
    windows = {
        'schema': 'swf-root-if-opcode-windows-v1', 'source_swf_sha256': 'b' * 64,
        'selected_if_count': 1, 'window_width': 12, 'verified_story_events': 0,
        'entries': [{'review_id': rid, 'root_frame': 9, 'action_tag_ordinal': 2,
                     'if_source_offset': 15, 'review_status': 'unverified',
                     'straight_line_preceding_record_count': 2,
                     'straight_line_preceding_opcode_classes': ['push_opaque', 'comparison'],
                     'if_incoming_reachable_syntactic_source_count': 1,
                     'if_has_multiple_reachable_syntactic_predecessors': False}],
    }
    return handoff, windows


class CrosscheckTests(unittest.TestCase):
    def test_matching_handoff_reports_only_source_free_hints(self):
        h, w = fixtures()
        result = crosscheck(h, w)
        self.assertEqual(result['matched_candidate_count'], 1)
        self.assertTrue(result['entries'][0]['bounded_comparison_opcode_present'])
        self.assertEqual(result['verified_story_events'], 0)
        self.assertNotIn('condition_confirmed', str(result))

    def test_rejects_cross_swf_and_coordinate_drift(self):
        h, w = fixtures()
        w['source_swf_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            crosscheck(h, w)
        h, w = fixtures()
        w['entries'][0]['if_source_offset'] = 16
        with self.assertRaisesRegex(ValueError, 'coordinate'):
            crosscheck(h, w)

    def test_rejects_missing_or_duplicate_review_identity(self):
        h, w = fixtures()
        w['entries'][0]['review_id'] = 'e' * 24
        with self.assertRaisesRegex(ValueError, 'identity'):
            crosscheck(h, w)
        h, w = fixtures()
        w['entries'].append(copy.deepcopy(w['entries'][0]))
        w['selected_if_count'] = 2
        h['entries'].append(copy.deepcopy(h['entries'][0]))
        h['candidate_count'] = 2
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            crosscheck(h, w)

    def test_rejects_unverified_claims_and_private_checkboxes(self):
        h, w = fixtures()
        w['verified_story_events'] = 1
        with self.assertRaisesRegex(ValueError, 'story events'):
            crosscheck(h, w)
        h, w = fixtures()
        h['entries'][0]['checks']['condition_confirmed'] = True
        with self.assertRaisesRegex(ValueError, 'attestations'):
            crosscheck(h, w)

    def test_rejects_inconsistent_opcode_and_predecessor_counts(self):
        h, w = fixtures()
        w['entries'][0]['straight_line_preceding_record_count'] = 3
        with self.assertRaisesRegex(ValueError, 'opcode'):
            crosscheck(h, w)
        h, w = fixtures()
        w['entries'][0]['if_has_multiple_reachable_syntactic_predecessors'] = True
        with self.assertRaisesRegex(ValueError, 'predecessor'):
            crosscheck(h, w)


if __name__ == '__main__':
    unittest.main()
