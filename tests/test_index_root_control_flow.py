"""Synthetic SWF tests for source-free AVM1 local control-flow graphs."""
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.index_root_control_flow import local_graph, build_control_flow
from tools.index_swf_action_opcodes import index_root_action_opcodes
from tools.index_root_conditional_edges import build_edges
from tools.index_root_state_access import build_state_access


def tag(code, payload=b''):
    return struct.pack('<H', (code << 6) | len(payload)) + payload


def swf(action, compressed=False):
    body = b'\x08\x00' + struct.pack('<HH', 12 * 256, 1) + tag(12, action) + tag(1) + tag(0)
    raw = b'FWS' + bytes([8]) + struct.pack('<I', len(body) + 8) + body
    return b'CWS' + raw[3:8] + zlib.compress(body) if compressed else raw


def reports(path):
    index = index_root_action_opcodes(path)
    row = index['action_tags'][0]
    queue = {'schema': 'swf-root-conditional-review-queue-v1',
             'source_swf_sha256': index['source_swf_sha256'],
             'root_showframe_tags': 1, 'root_doaction_tags': 1,
             'selected_candidate_count': 1, 'verified_story_events': 0,
             'candidates': [{'root_frame': 1, 'action_tag_ordinal': 1,
                             'action_sha256': row['action_sha256'],
                             'conditional_opcode_count': 1, 'jump_opcode_count': 1,
                             'review_status': 'unverified'}]}
    edges = build_edges(path, index, queue)
    state = build_state_access(path, index, queue, edges)
    return index, queue, edges, state


class LocalControlFlowTests(unittest.TestCase):
    ACTION = bytes([0x9d, 2, 0, 0, 0, 0x99, 2, 0, 0, 0, 0])

    def test_conditional_and_jump_graph(self):
        result = local_graph(self.ACTION)
        self.assertEqual((result['conditional_count'], result['jump_count']), (1, 1))
        self.assertEqual(result['reachable_record_count'], 2)
        self.assertEqual(result['unreachable_record_count'], 0)
        self.assertTrue(result['action_end_reachable'])
        self.assertEqual(result['if_successors'][0]['branch_target_offset'], 5)
        self.assertFalse(result['if_successors'][0]['branch_and_fallthrough_distinct'])

    def test_if_has_two_distinct_successors(self):
        action = bytes([0x9d, 2, 0, 1, 0, 0x1d, 0])
        graph = local_graph(action)
        self.assertEqual(graph['reachable_record_count'], 2)
        self.assertTrue(graph['if_successors'][0]['branch_and_fallthrough_distinct'])
        self.assertEqual(graph['if_successors'][0]['fallthrough_offset'], 5)
        self.assertEqual(graph['if_successors'][0]['branch_target_offset'], 6)

    def test_unreachable_and_backward_branch(self):
        action = bytes([0x99, 2, 0, 1, 0, 0x1d, 0])
        self.assertEqual(local_graph(action)['unreachable_record_count'], 1)
        backward = bytes([0x1c, 0x99, 2, 0, 0xfa, 0xff, 0])
        graph = local_graph(backward)
        self.assertEqual(graph['backward_branch_count'], 1)
        self.assertFalse(graph['action_end_reachable'])

    def test_rejects_bad_boundary_and_tampered_edges(self):
        with self.assertRaisesRegex(ValueError, 'unsafe branch target'):
            local_graph(bytes([0x99, 2, 0, 0xfe, 0xff, 0]))
        with self.assertRaisesRegex(ValueError, 'branch evidence mismatch'):
            local_graph(self.ACTION, [])

    def test_real_pipeline_synthetic_compressed_and_tamper_rejection(self):
        for compressed in (False, True):
            with self.subTest(compressed=compressed), tempfile.TemporaryDirectory() as d:
                path = Path(d) / 'SECRET_fixture.swf'
                path.write_bytes(swf(self.ACTION, compressed))
                reports_tuple = reports(path)
                result = build_control_flow(path, *reports_tuple)
                self.assertEqual(result['selected_action_tags'], 1)
                self.assertEqual(result['aggregate']['conditional_count'], 1)
                self.assertEqual(result['verified_story_events'], 0)
                self.assertNotIn('SECRET', str(result))
                altered = dict(reports_tuple[3])
                altered['total_access_opcode_records'] = 99
                with self.assertRaisesRegex(ValueError, 'state access evidence mismatch'):
                    build_control_flow(path, *reports_tuple[:3], altered)


if __name__ == '__main__':
    unittest.main()
