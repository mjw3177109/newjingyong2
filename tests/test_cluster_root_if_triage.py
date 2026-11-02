"""Regression tests for source-free IF structural clusters."""
import copy
import unittest
from tools.cluster_root_if_triage import cluster_triage


def fixture(offsets=(100, 133, 166, 199), frames=None):
    frames = frames or [55] * len(offsets)
    entries = [dict(review_id=f'{i + 1:024x}', root_frame=frames[i],
                    action_tag_ordinal=9, if_source_offset=pos,
                    bounded_comparison_opcode_present=True,
                    reachable_syntactic_predecessor_count=1,
                    multiple_reachable_syntactic_predecessors=False,
                    successor_branch_write_hint_count=0,
                    successor_fallthrough_write_hint_count=1,
                    successor_arm_write_hints_differ=True,
                    review_status='unverified') for i, pos in enumerate(offsets)]
    return dict(schema='swf-root-if-handoff-window-crosscheck-v1',
                source_swf_sha256='a' * 64, matched_candidate_count=len(entries),
                entries=entries, verified_story_events=0, ready_for_html5_mapping=0,
                structural_review_triage=dict(review_target_count=len(entries),
                    review_order=[dict(rank=i + 1, review_id=e['review_id'],
                                       review_status='unverified') for i, e in enumerate(entries)]))


class RootIfClusterTests(unittest.TestCase):
    def test_same_action_repeated_stride_not_story_claim(self):
        result = cluster_triage(fixture())
        self.assertEqual(result['action_group_count'], 1)
        self.assertEqual(result['repeated_stride_run_count'], 1)
        self.assertEqual(result['repeated_stride_runs'][0]['if_offset_stride'], 33)
        self.assertEqual(result['repeated_stride_runs'][0]['candidate_count'], 4)
        self.assertEqual(result['uniform_hint_profile_stride_run_count'], 1)
        self.assertEqual(result['repeated_stride_runs'][0]['structural_hint_profiles'][0]['candidate_count'], 4)
        self.assertEqual(result['verified_story_events'], 0)
        self.assertEqual(result['ready_for_html5_mapping'], 0)

    def test_split_frames_and_nonuniform_offsets(self):
        result = cluster_triage(fixture((100, 133, 166, 201), [55, 55, 55, 56]))
        self.assertEqual(result['action_group_count'], 2)
        self.assertEqual(result['repeated_stride_run_count'], 1)
        self.assertEqual(result['repeated_stride_runs'][0]['candidate_count'], 3)
        self.assertEqual(cluster_triage(fixture((100, 133, 169, 201)))['repeated_stride_run_count'], 0)

    def test_order_independent_and_tamper_rejection(self):
        base = fixture()
        shuffled = copy.deepcopy(base)
        shuffled['entries'].reverse()
        self.assertEqual(cluster_triage(base), cluster_triage(shuffled))
        for kind in ('id', 'location', 'status', 'order', 'bool'):
            bad = copy.deepcopy(base)
            if kind == 'id':
                bad['entries'][1]['review_id'] = bad['entries'][0]['review_id']
            elif kind == 'location':
                bad['entries'][1]['if_source_offset'] = bad['entries'][0]['if_source_offset']
            elif kind == 'status':
                bad['entries'][0]['review_status'] = 'verified'
            elif kind == 'order':
                bad['structural_review_triage']['review_order'].pop()
            else:
                bad['entries'][0]['if_source_offset'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                cluster_triage(bad)

    def test_different_hints_split_same_stride_without_claiming_events(self):
        data = fixture()
        data['entries'][1]['successor_branch_write_hint_count'] = 2
        result = cluster_triage(data)
        run = result['repeated_stride_runs'][0]
        self.assertEqual(run['structural_hint_profile_count'], 2)
        self.assertEqual([p['candidate_count'] for p in run['structural_hint_profiles']], [3, 1])
        self.assertEqual(result['uniform_hint_profile_stride_run_count'], 0)
        self.assertEqual(result['verified_story_events'], 0)

    def test_invalid_hint_counts_and_flags_are_rejected(self):
        for key, value in [('successor_branch_write_hint_count', True),
                           ('successor_fallthrough_write_hint_count', -1),
                           ('reachable_syntactic_predecessor_count', '1'),
                           ('bounded_comparison_opcode_present', 1),
                           ('successor_arm_write_hints_differ', False),
                           ('multiple_reachable_syntactic_predecessors', True)]:
            bad = fixture()
            bad['entries'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                cluster_triage(bad)


if __name__ == '__main__':
    unittest.main()
