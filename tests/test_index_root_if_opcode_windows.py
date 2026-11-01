import copy
import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from tools.index_root_if_opcode_windows import window_for_if, build_windows, CLASSES
from tools.index_root_conditional_edges import branch_edges
from tools.index_root_control_flow import local_graph


def action_payload():
    # Push(null), Equals, If(+0) -> ActionEnd. The push operand is deliberately
    # never returned by the indexer.
    return b'\x96\x01\x00\x02\x0e\x9d\x02\x00\x00\x00\x00'


def tiny_swf(action):
    def tag(code, payload=b''):
        return struct.pack('<H', (code << 6) | len(payload)) + payload
    # FWS, RECT nbits=1 (2 bytes), frame rate and count, DoAction, ShowFrame, End.
    body = b'\x08\x00\x00\x0c\x01\x00' + tag(12, action) + tag(1) + tag(0)
    return b'FWS\x08' + struct.pack('<I', 8 + len(body)) + body


def packets_for(raw, action):
    swf_sha = hashlib.sha256(raw).hexdigest()
    action_sha = hashlib.sha256(action).hexdigest()
    rid = hashlib.sha256(f'{swf_sha}:1:{action_sha}:5'.encode('ascii')).hexdigest()[:24]
    packet = {
        'review_id': rid, 'root_frame': 1, 'action_tag_ordinal': 1,
        'action_sha256': action_sha, 'if_source_offset': 5,
        'branch_target_offset': 10, 'fallthrough_offset': 10,
        'if_record_reachable': True, 'review_status': 'unverified',
    }
    report = {
        'schema': 'swf-root-if-review-packets-v1',
        'source_swf_sha256': swf_sha, 'verified_story_events': 0,
        'manual_review_limit': 12, 'manual_review_queue': [packet],
    }
    return report


def packet_for_if(action, source):
    edges = branch_edges(action)
    edge = next(e for e in edges if e['source_offset'] == source and e['opcode'] == 'if')
    succ = next(s for s in local_graph(action, edges)['if_successors']
                if s['if_source_offset'] == source)
    return {'review_id': 'a' * 24, 'root_frame': 1, 'action_tag_ordinal': 1,
            'if_source_offset': source, 'branch_target_offset': edge['target_offset'],
            'fallthrough_offset': succ['fallthrough_offset'],
            'if_record_reachable': succ['if_record_reachable']}


class IfOpcodeWindowTests(unittest.TestCase):
    def test_linear_window_has_no_push_operand_or_semantic_claim(self):
        packet = packets_for(tiny_swf(action_payload()), action_payload())['manual_review_queue'][0]
        result = window_for_if(action_payload(), packet)
        self.assertEqual(result['preceding_opcode_classes'], ['push_opaque', 'comparison'])
        self.assertEqual(result['preceding_record_offsets'], [0, 4])
        self.assertEqual(result['comparison_opcode_count'], 1)
        self.assertEqual(result['straight_line_preceding_record_offsets'], [0, 4])
        self.assertFalse(result['straight_line_boundary_limited'])
        self.assertFalse(result['has_branch_or_opaque_control'])
        self.assertNotIn('trigger', result)
        self.assertNotIn('condition', result)

    def test_jump_target_starts_new_straight_line_suffix(self):
        # Jump at offset 4 lands on comparison at 13; the preceding Push at 9
        # is not a straight-line predecessor of the IF at 14.
        action = (b'\\x96\\x01\\x00\\x02' + b'\\x99\\x02\\x00\\x04\\x00'
                  + b'\\x96\\x01\\x00\\x02' + b'\\x0e'
                  + b'\\x9d\\x02\\x00\\x00\\x00' + b'\\x00')
        result = window_for_if(action, packet_for_if(action, 14))
        self.assertEqual(result['preceding_record_offsets'], [0, 4, 9, 13])
        self.assertEqual(result['straight_line_preceding_record_offsets'], [13])
        self.assertEqual(result['straight_line_preceding_opcode_classes'], ['comparison'])
        self.assertTrue(result['straight_line_boundary_limited'])

    def test_opaque_control_bounds_preceding_suffix(self):
        # WaitForFrame has opaque control behavior; never stitch the earlier
        # Push into a putative condition across that opcode.
        action = (b'\\x96\\x01\\x00\\x02' + b'\\x8a\\x03\\x00\\x00\\x00\\x00'
                  + b'\\x96\\x01\\x00\\x02' + b'\\x0e'
                  + b'\\x9d\\x02\\x00\\x00\\x00' + b'\\x00')
        result = window_for_if(action, packet_for_if(action, 15))
        self.assertEqual(result['preceding_record_offsets'], [0, 4, 10, 14])
        self.assertEqual(result['straight_line_preceding_record_offsets'], [10, 14])
        self.assertTrue(result['straight_line_boundary_limited'])

    def test_if_at_branch_target_has_empty_straight_line_predecessors(self):
        action = (b'\\x99\\x02\\x00\\x04\\x00' + b'\\x96\\x01\\x00\\x02'
                  + b'\\x9d\\x02\\x00\\x00\\x00' + b'\\x00')
        result = window_for_if(action, packet_for_if(action, 9))
        self.assertEqual(result['preceding_record_offsets'], [0, 5])
        self.assertEqual(result['straight_line_preceding_record_offsets'], [])
        self.assertTrue(result['straight_line_boundary_limited'])

    def test_avm1_operator_family_classification(self):
        # AVM1 And is 0x10; StringAdd is 0x21. Neither is comparison.
        self.assertEqual(CLASSES[0x10], 'boolean_logic')
        self.assertEqual(CLASSES[0x13], 'comparison')
        self.assertEqual(CLASSES[0x21], 'arithmetic')
        self.assertEqual(CLASSES[0x48], 'comparison')
        self.assertEqual(CLASSES[0x49], 'comparison')

    def test_rejects_mismatched_target_reachability_and_non_if(self):
        packet = packets_for(tiny_swf(action_payload()), action_payload())['manual_review_queue'][0]
        for field, value in [('branch_target_offset', 4), ('fallthrough_offset', 4),
                             ('if_record_reachable', False), ('if_source_offset', 4)]:
            changed = {**packet, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                window_for_if(action_payload(), changed)

    def test_rejects_bad_window_width_and_malformed_bytecode(self):
        packet = packets_for(tiny_swf(action_payload()), action_payload())['manual_review_queue'][0]
        for width in (0, 33, True, '12'):
            with self.subTest(width=width), self.assertRaises(ValueError):
                window_for_if(action_payload(), packet, width)
        with self.assertRaises(ValueError):
            window_for_if(action_payload()[:-1], packet)

    def test_real_swf_header_path_and_review_identity(self):
        action = action_payload()
        raw = tiny_swf(action)
        report = packets_for(raw, action)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'mini.swf'
            path.write_bytes(raw)
            result = build_windows(path, report)
            self.assertEqual(result['selected_if_count'], 1)
            self.assertEqual(result['verified_story_events'], 0)
            self.assertEqual(result['entries'][0]['review_id'], report['manual_review_queue'][0]['review_id'])
            changed = copy.deepcopy(report)
            changed['manual_review_queue'][0]['review_id'] = '0' * 24
            with self.assertRaisesRegex(ValueError, 'review identity'):
                build_windows(path, changed)

    def test_rejects_different_source_and_fake_verified_event(self):
        action = action_payload()
        raw = tiny_swf(action)
        report = packets_for(raw, action)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'mini.swf'
            path.write_bytes(raw)
            for key, value in [('source_swf_sha256', 'f' * 64), ('verified_story_events', 1)]:
                changed = copy.deepcopy(report)
                changed[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    build_windows(path, changed)
            changed = copy.deepcopy(report)
            changed['manual_review_queue'][0]['action_sha256'] = 'b' * 64
            with self.assertRaises(ValueError):
                build_windows(path, changed)


if __name__ == '__main__':
    unittest.main()
