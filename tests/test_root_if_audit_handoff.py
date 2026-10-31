import copy
import unittest

from tools.build_root_if_audit_handoff import build_handoff

SHA = 'a' * 64
ACTION = 'b' * 64


def fixture():
    return {
        'schema': 'swf-root-if-review-packets-v1',
        'source_swf_sha256': SHA,
        'selected_action_tags': 1,
        'total_if_review_packets': 1,
        'manual_review_limit': 12,
        'verified_story_events': 0,
        'manual_review_queue': [{
            'review_id': 'c' * 24,
            'root_frame': 8, 'action_tag_ordinal': 2,
            'action_sha256': ACTION, 'if_source_offset': 5,
            'branch_target_offset': 12, 'fallthrough_offset': 9,
            'if_record_reachable': True, 'same_frame_sprite_transition': True,
            'structural_priority': 7,
            'nearby_access_hints': [{'offset': 2, 'opcode': 'get_variable',
                                    'records_before_if': 1}],
            'review_status': 'unverified', 'trigger': None, 'effects': None,
            'map_id': None, 'html5_event_id': None,
        }],
    }


class AuditHandoffTests(unittest.TestCase):
    def test_generates_empty_private_review_checklist(self):
        result = build_handoff(fixture())
        self.assertEqual(result['candidate_count'], 1)
        self.assertEqual(result['verified_story_events'], 0)
        self.assertEqual(result['ready_for_html5_mapping'], 0)
        entry = result['entries'][0]
        self.assertEqual(entry['source_location']['if_source_offset'], 5)
        self.assertTrue(all(value is False or value is None
                            for value in entry['checks'].values()))
        self.assertNotIn('nearby_access_hints', entry)
        self.assertEqual(result, build_handoff(fixture()))

    def test_rejects_fake_verified_semantics(self):
        data = fixture()
        data['manual_review_queue'][0]['review_status'] = 'verified'
        with self.assertRaises(ValueError):
            build_handoff(data)
        data = fixture()
        data['manual_review_queue'][0]['trigger'] = 'guessed condition'
        with self.assertRaises(ValueError):
            build_handoff(data)

    def test_rejects_duplicate_review_id(self):
        data = fixture()
        data['manual_review_queue'].append(copy.deepcopy(data['manual_review_queue'][0]))
        data['total_if_review_packets'] = 2
        with self.assertRaises(ValueError):
            build_handoff(data)

    def test_rejects_forged_source_and_offsets(self):
        data = fixture()
        data['source_swf_sha256'] = 'not-a-hash'
        with self.assertRaises(ValueError):
            build_handoff(data)
        data = fixture()
        data['manual_review_queue'][0]['if_source_offset'] = True
        with self.assertRaises(ValueError):
            build_handoff(data)

    def test_rejects_invalid_access_hints(self):
        data = fixture()
        data['manual_review_queue'][0]['nearby_access_hints'][0]['offset'] = 8
        with self.assertRaises(ValueError):
            build_handoff(data)
        data = fixture()
        data['manual_review_queue'][0]['nearby_access_hints'][0]['opcode'] = 'source_text'
        with self.assertRaises(ValueError):
            build_handoff(data)

    def test_rejects_inconsistent_counts(self):
        data = fixture()
        data['total_if_review_packets'] = 0
        with self.assertRaises(ValueError):
            build_handoff(data)
        data = fixture()
        data['verified_story_events'] = 1
        with self.assertRaises(ValueError):
            build_handoff(data)


if __name__ == '__main__':
    unittest.main()
