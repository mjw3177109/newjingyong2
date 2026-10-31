import unittest

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
        packet = result['manual_review_queue'][0]
        self.assertEqual(packet['structural_priority'], 7)
        self.assertEqual(packet['if_source_offset'], 5)
        self.assertIsNone(packet['trigger'])
        self.assertIsNone(packet['effects'])
        self.assertEqual(result['verified_story_events'], 0)
        self.assertEqual(result, build_packets(*fixture()))

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
