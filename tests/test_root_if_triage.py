"""Review triage uses only verified structural hints, never original game assets."""
import copy
import unittest

from tools.crosscheck_root_if_handoff import crosscheck, rank_structural_review_targets
from test_crosscheck_root_if_handoff import fixtures


class RootIfTriageTests(unittest.TestCase):
    def test_crosscheck_exposes_unverified_review_order(self):
        handoff, windows = fixtures()
        result = crosscheck(handoff, windows)
        triage = result['structural_review_triage']
        self.assertEqual(triage['review_target_count'], 1)
        self.assertEqual(triage['different_write_hint_count'], 0)
        self.assertEqual(triage['any_write_hint_count'], 0)
        self.assertEqual(triage['review_order'][0]['review_id'], result['entries'][0]['review_id'])
        self.assertEqual(triage['review_order'][0]['review_status'], 'unverified')
        self.assertEqual(result['verified_story_events'], 0)
        self.assertEqual(result['ready_for_html5_mapping'], 0)

    def test_write_asymmetry_ranks_first_without_semantic_claim(self):
        handoff, windows = fixtures()
        base = crosscheck(handoff, windows)['entries'][0]
        different = copy.deepcopy(base)
        different.update(review_id='1' * 24, root_frame=10,
                         successor_branch_write_hint_count=2,
                         successor_fallthrough_write_hint_count=0,
                         successor_arm_write_hints_differ=True)
        both = copy.deepcopy(base)
        both.update(review_id='2' * 24, root_frame=8,
                    successor_branch_write_hint_count=1,
                    successor_fallthrough_write_hint_count=1,
                    successor_arm_write_hints_differ=False)
        ranked = rank_structural_review_targets([base, both, different])
        self.assertEqual([x['review_id'] for x in ranked['review_order']],
                         ['1' * 24, '2' * 24, base['review_id']])
        self.assertEqual(ranked['different_write_hint_count'], 1)
        self.assertEqual(ranked['any_write_hint_count'], 2)
        self.assertTrue(all(x['review_status'] == 'unverified' for x in ranked['review_order']))
        self.assertNotIn('trigger', str(ranked))

    def test_rejects_inconsistent_or_duplicate_structural_rows(self):
        handoff, windows = fixtures()
        base = crosscheck(handoff, windows)['entries'][0]
        for change in (
            {'successor_branch_write_hint_count': True},
            {'successor_arm_write_hints_differ': True},
            {'multiple_reachable_syntactic_predecessors': True},
            {'review_status': 'verified'},
            {'root_frame': -1},
        ):
            with self.subTest(change=change):
                row = {**base, **change}
                with self.assertRaises(ValueError):
                    rank_structural_review_targets([row])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            rank_structural_review_targets([base, copy.deepcopy(base)])

    def test_deterministic_ties_ignore_input_order(self):
        handoff, windows = fixtures()
        base = crosscheck(handoff, windows)['entries'][0]
        second = copy.deepcopy(base)
        second.update(review_id='f' * 24, root_frame=base['root_frame'] + 1)
        left = rank_structural_review_targets([second, base])
        right = rank_structural_review_targets([base, second])
        self.assertEqual(left, right)


if __name__ == '__main__':
    unittest.main()
