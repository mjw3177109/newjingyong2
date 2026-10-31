import copy
import unittest

from tools.reconcile_root_if_review import reconcile

SHA = 'a' * 64
RID = 'b' * 24
ACTION = 'c' * 64


def fixture():
    entry = {
        'review_id': RID,
        'source_location': {
            'root_frame': 8, 'action_tag_ordinal': 2, 'action_sha256': ACTION,
            'if_source_offset': 5, 'branch_target_offset': 12, 'fallthrough_offset': 9,
        },
        'checks': {
            'ffdec_script_sha256': None, 'condition_confirmed': False,
            'state_effects_confirmed': False, 'map_context_confirmed': False,
            'runtime_reproduced': False, 'independent_reviewed': False,
            'adaptation_rights_confirmed': False,
        },
        'review_status': 'unverified', 'html5_event_id': None,
    }
    return {
        'schema': 'swf-root-if-audit-handoff-v1',
        'source_swf_sha256': SHA, 'candidate_count': 1,
        'verified_story_events': 0, 'ready_for_html5_mapping': 0,
        'entries': [entry],
    }


def privately_reviewed(base):
    reviewed = copy.deepcopy(base)
    entry = reviewed['entries'][0]
    entry['review_status'] = 'reviewed_private'
    entry['checks'] = {
        k: ('d' * 64 if k == 'ffdec_script_sha256' else k != 'adaptation_rights_confirmed')
        for k in entry['checks']
    }
    return reviewed


class ReconciliationTests(unittest.TestCase):
    def test_baseline_has_zero_review_attestations_and_zero_events(self):
        base = fixture()
        result = reconcile(base, copy.deepcopy(base))
        self.assertEqual(result['private_review_attestations'], 0)
        self.assertEqual(result['verified_story_events'], 0)
        self.assertEqual(result['ready_for_html5_mapping'], 0)
        self.assertEqual(result, reconcile(base, copy.deepcopy(base)))

    def test_private_review_is_only_attestation_not_verified_event(self):
        base = fixture()
        reviewed = privately_reviewed(base)
        result = reconcile(base, reviewed)
        self.assertEqual(result['private_review_attestations'], 1)
        self.assertEqual(result['rights_attestations'], 0)
        self.assertEqual(result['verified_story_events'], 0)
        reviewed['entries'][0]['checks']['adaptation_rights_confirmed'] = True
        self.assertEqual(reconcile(base, reviewed)['rights_attestations'], 1)

    def test_rejects_changed_source_identity_and_coordinates(self):
        base = fixture()
        for key, value in [('source_swf_sha256', 'd' * 64), ('candidate_count', 2)]:
            changed = copy.deepcopy(base)
            changed[key] = value
            with self.assertRaises(ValueError):
                reconcile(base, changed)
        changed = copy.deepcopy(base)
        changed['entries'][0]['source_location']['root_frame'] = 99
        with self.assertRaises(ValueError):
            reconcile(base, changed)

    def test_rejects_partial_and_fake_verified_reviews(self):
        base = fixture()
        for key, value in [('condition_confirmed', True), ('ffdec_script_sha256', 'd' * 64)]:
            changed = copy.deepcopy(base)
            changed['entries'][0]['checks'][key] = value
            with self.assertRaises(ValueError):
                reconcile(base, changed)
        changed = privately_reviewed(base)
        changed['entries'][0]['checks']['independent_reviewed'] = False
        with self.assertRaises(ValueError):
            reconcile(base, changed)
        changed = privately_reviewed(base)
        changed['entries'][0]['review_status'] = 'verified'
        with self.assertRaises(ValueError):
            reconcile(base, changed)

    def test_rejects_semantic_leaks_and_premature_mapping(self):
        base = fixture()
        for key, value in [('trigger', 'guessed condition'), ('effects', 'guessed effects')]:
            changed = copy.deepcopy(base)
            changed['entries'][0][key] = value
            with self.assertRaises(ValueError):
                reconcile(base, changed)
        changed = copy.deepcopy(base)
        changed['entries'][0]['html5_event_id'] = 'EVENT_1'
        with self.assertRaises(ValueError):
            reconcile(base, changed)

    def test_rejects_bad_check_types_and_digest(self):
        base = fixture()
        for key, value in [('runtime_reproduced', 1), ('ffdec_script_sha256', 'not-sha')]:
            changed = privately_reviewed(base)
            changed['entries'][0]['checks'][key] = value
            with self.assertRaises(ValueError):
                reconcile(base, changed)
        changed = copy.deepcopy(base)
        changed['entries'][0]['checks']['extra'] = True
        with self.assertRaises(ValueError):
            reconcile(base, changed)


if __name__ == '__main__':
    unittest.main()
