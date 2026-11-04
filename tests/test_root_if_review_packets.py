import copy
import unittest
from pathlib import Path

from tools.build_root_if_review_packets import build_packets

SHA = 'a' * 64
ACT = 'b' * 64


def fixture():
    candidate = {'root_frame': 8, 'action_tag_ordinal': 2, 'action_sha256': ACT,
                 'conditional_opcode_count': 1, 'jump_opcode_count': 1,
                 'same_frame_sprite_transition': True, 'review_status': 'unverified'}
    shared = {'root_frame': 8, 'action_tag_ordinal': 2,
              'action_sha256': ACT, 'review_status': 'unverified'}
    queue = {'schema': 'swf-root-conditional-review-queue-v1',
             'source_swf_sha256': SHA, 'verified_story_events': 0,
             'selected_candidate_count': 1, 'candidates': [candidate]}
    edges = {'schema': 'swf-root-conditional-edges-v1',
             'source_swf_sha256': SHA, 'verified_story_events': 0,
             'selected_action_tags': 1, 'if_edges': 1, 'total_branch_edges': 2,
             'candidates': [{**shared, 'edges': [
                 {'opcode': 'if', 'source_offset': 5, 'target_offset': 12,
                  'target_alignment': 'record_boundary'},
                 {'opcode': 'jump', 'source_offset': 9, 'target_offset': 20,
                  'target_alignment': 'record_boundary'}]}]}
    access = {'schema': 'swf-root-state-access-hints-v1',
              'source_swf_sha256': SHA, 'verified_story_events': 0,
              'selected_action_tags': 1, 'candidates': [{**shared,
              'if_preceding_access_hints': [{'if_source_offset': 5,
              'prior_eight_records_access_hints': [{'offset': 2, 'opcode': 'get_variable',
              'records_before_if': 1}]}]}]}
    cfg = {'schema': 'swf-root-local-control-flow-v1',
           'source_swf_sha256': SHA, 'verified_story_events': 0,
           'selected_action_tags': 1, 'candidates': [{**shared, 'conditional_count': 1,
           'jump_count': 1, 'if_successors': [{'if_source_offset': 5,
           'branch_target_offset': 12, 'fallthrough_offset': 9,
           'branch_and_fallthrough_distinct': True, 'if_record_reachable': True}]}]}
    return [queue, edges, access, cfg]


class ReviewPacketsTests(unittest.TestCase):
    def test_builds_source_free_target_without_claiming_story(self):
        result = build_packets(*fixture())
        self.assertEqual(result['total_if_review_packets'], 1)
        self.assertIsNone(result['target_frame_action_tags_in_sample'])
        self.assertEqual(result['target_frame_coverage'], 'not_requested')
        packet = result['manual_review_queue'][0]
        self.assertEqual(packet['structural_priority'], 15)
        self.assertEqual(result['syntactically_reachable_if_count'], 1)
        self.assertEqual(result['syntactically_unreachable_if_count'], 0)
        self.assertEqual(result['selected_syntactically_reachable_count'], 1)
        self.assertEqual(packet['if_source_offset'], 5)
        self.assertIsNone(packet['trigger'])
        self.assertIsNone(packet['effects'])
        self.assertEqual(result['verified_story_events'], 0)
        self.assertEqual(result, build_packets(*fixture()))

    def test_unreachable_if_has_lower_priority_and_is_not_verified(self):
        rows = fixture()
        rows[3]['candidates'][0]['if_successors'][0]['if_record_reachable'] = False
        result = build_packets(*rows)
        packet = result['manual_review_queue'][0]
        self.assertFalse(packet['if_record_reachable'])
        self.assertEqual(packet['structural_priority'], 7)
        self.assertEqual(result['syntactically_reachable_if_count'], 0)
        self.assertEqual(result['syntactically_unreachable_if_count'], 1)
        self.assertEqual(result['selected_syntactically_reachable_count'], 0)
        self.assertEqual(result['verified_story_events'], 0)

    def test_reachable_if_wins_limited_queue_over_unreachable_high_score(self):
        rows = fixture()
        # The first IF has every optional hint, but is syntactically unreachable.
        rows[3]['candidates'][0]['if_successors'][0]['if_record_reachable'] = False
        for report in rows:
            second = copy.deepcopy(report['candidates'][0])
            second['action_tag_ordinal'] = 3
            second['root_frame'] = 9
            second['action_sha256'] = 'c' * 64
            if 'same_frame_sprite_transition' in second:
                second['same_frame_sprite_transition'] = False
            if 'if_successors' in second:
                second['if_successors'][0]['if_record_reachable'] = True
            report['candidates'].append(second)
        rows[0]['selected_candidate_count'] = 2
        for report in rows[1:]:
            report['selected_action_tags'] = 2
        rows[1]['if_edges'] = 2
        rows[1]['total_branch_edges'] = 4
        result = build_packets(*rows, limit=1)
        self.assertEqual(result['total_if_review_packets'], 2)
        self.assertEqual(result['syntactically_unreachable_if_count'], 1)
        self.assertEqual(result['syntactically_reachable_if_count'], 1)
        self.assertEqual(result['manual_review_queue'][0]['action_tag_ordinal'], 3)
        self.assertEqual(result['selected_syntactically_reachable_count'], 1)
        self.assertEqual(result['verified_story_events'], 0)

    def test_target_frame_filters_queue_but_keeps_global_counts(self):
        rows = fixture()
        for report in rows:
            second = copy.deepcopy(report['candidates'][0])
            second['root_frame'] = 55
            second['action_tag_ordinal'] = 9
            second['action_sha256'] = 'c' * 64
            report['candidates'].append(second)
        rows[0]['selected_candidate_count'] = 2
        for report in rows[1:]:
            report['selected_action_tags'] = 2
        rows[1]['if_edges'] = 2
        rows[1]['total_branch_edges'] = 4
        result = build_packets(*rows, target_frame=55)
        self.assertEqual(result['total_if_review_packets'], 2)
        self.assertEqual(result['target_frame_if_count'], 1)
        self.assertEqual(result['target_frame_action_tags_in_sample'], 1)
        self.assertEqual(result['target_frame_coverage'], 'present_in_capped_sample_not_exhaustive')
        self.assertEqual(result['target_frame'], 55)
        self.assertEqual(result['manual_review_queue'][0]['root_frame'], 55)
        self.assertEqual(result['verified_story_events'], 0)
        empty = build_packets(*rows, target_frame=56)
        self.assertEqual(empty['target_frame_if_count'], 0)
        self.assertEqual(empty['target_frame_action_tags_in_sample'], 0)
        self.assertEqual(empty['target_frame_coverage'], 'absent_from_capped_sample')
        self.assertEqual(empty['manual_review_queue'], [])
        self.assertEqual(empty['total_if_review_packets'], 2)

    def test_frame55_queue_limit_covers_all_thirteen_if_candidates(self):
        rows = fixture()
        # Model the real SWF report: thirteen IFs in frame 55 / one action tag.
        # Each synthetic action has one IF and one Jump so all four evidence
        # inputs remain aligned while the packet cap is exercised.
        for index in range(1, 13):
            delta = index * 20
            for report in rows:
                candidate = copy.deepcopy(report['candidates'][0])
                candidate['root_frame'] = 55
                candidate['action_tag_ordinal'] = index + 2
                candidate['action_sha256'] = f'{index + 1:064x}'
                if 'edges' in candidate:
                    for edge in candidate['edges']:
                        edge['source_offset'] += delta
                        edge['target_offset'] += delta
                if 'if_preceding_access_hints' in candidate:
                    for hint in candidate['if_preceding_access_hints']:
                        hint['if_source_offset'] += delta
                        for access_hint in hint['prior_eight_records_access_hints']:
                            access_hint['offset'] += delta
                if 'if_successors' in candidate:
                    for successor in candidate['if_successors']:
                        successor['if_source_offset'] += delta
                        successor['branch_target_offset'] += delta
                        successor['fallthrough_offset'] += delta
                report['candidates'].append(candidate)

        rows[0]['selected_candidate_count'] = 13
        for report in rows[1:]:
            report['selected_action_tags'] = 13
        rows[1]['if_edges'] = 13
        rows[1]['total_branch_edges'] = 26

        complete = build_packets(*rows, limit=50, target_frame=55)
        self.assertEqual(complete['target_frame_if_count'], 13)
        self.assertEqual(complete['target_frame_action_tags_in_sample'], 13)
        self.assertEqual(len(complete['manual_review_queue']), 13)
        self.assertEqual(complete['manual_review_limit'], 50)
        self.assertEqual(complete['verified_story_events'], 0)

        truncated = build_packets(*rows, limit=12, target_frame=55)
        self.assertEqual(truncated['target_frame_if_count'], 13)
        self.assertEqual(len(truncated['manual_review_queue']), 12)
        self.assertEqual(truncated['verified_story_events'], 0)

    def test_ci_workflow_keeps_review_limit_above_frame55_if_count(self):
        workflow = Path('.github/workflows/validate.yml').read_text(encoding='utf-8')
        self.assertIn('build_root_if_review_packets.py', workflow)
        self.assertIn('--limit 50 --target-frame 55', workflow)

    def test_rejects_invalid_target_frame(self):
        for invalid in (0, -1, True, '55'):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    build_packets(*fixture(), target_frame=invalid)

    def test_rejects_source_mismatch(self):
        rows = fixture()
        rows[3]['source_swf_sha256'] = 'c' * 64
        with self.assertRaises(ValueError):
            build_packets(*rows)

    def test_rejects_misaligned_target(self):
        rows = fixture()
        rows[3]['candidates'][0]['if_successors'][0]['branch_target_offset'] = 13
        with self.assertRaises(ValueError):
            build_packets(*rows)

    def test_rejects_invalid_nearby_hint(self):
        rows = fixture()
        rows[2]['candidates'][0]['if_preceding_access_hints'][0]['prior_eight_records_access_hints'][0]['opcode'] = 'raw_source'
        with self.assertRaises(ValueError):
            build_packets(*rows)

    def test_rejects_forged_verified_events(self):
        rows = fixture()
        rows[1]['verified_story_events'] = 1
        with self.assertRaises(ValueError):
            build_packets(*rows)

    def test_rejects_bad_count_and_limit(self):
        rows = fixture()
        rows[1]['if_edges'] = 2
        with self.assertRaises(ValueError):
            build_packets(*rows)
        with self.assertRaises(ValueError):
            build_packets(*fixture(), limit=0)

    def test_rejects_invalid_opcode_and_candidate_status(self):
        rows = fixture()
        rows[1]['candidates'][0]['edges'][0]['opcode'] = 'script_text'
        with self.assertRaises(ValueError):
            build_packets(*rows)
        rows = fixture()
        rows[0]['candidates'][0]['review_status'] = 'verified'
        with self.assertRaises(ValueError):
            build_packets(*rows)


if __name__ == '__main__':
    unittest.main()
