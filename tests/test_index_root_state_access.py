"""Synthetic SWF tests for source-free root AVM1 state-access hints."""
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.index_root_state_access import action_records, access_hints, build_state_access
from tools.index_swf_action_opcodes import index_root_action_opcodes
from tools.index_root_conditional_edges import build_edges


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
    return index, queue, edges


class RootStateAccessTests(unittest.TestCase):
    # ActionPush(string SECRET), GetVariable, If, SetVariable, Jump, ActionEnd.
    ACTION = bytes([0x96, 8, 0, 0, 83, 69, 67, 82, 69, 84, 0,
                    0x1c, 0x9d, 2, 0, 0, 0, 0x1d, 0x99, 2, 0, 0, 0, 0])

    def run_fixture(self, compressed=False):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fixture.swf'
            path.write_bytes(swf(self.ACTION, compressed))
            return build_state_access(path, *reports(path))

    def test_offsets_and_preceding_if_proximity(self):
        result = self.run_fixture()
        row = result['candidates'][0]
        self.assertEqual(result['total_access_opcode_records'], 2)
        self.assertEqual(result['access_opcode_counts'], {'get_variable': 1, 'set_variable': 1})
        self.assertEqual([(x['offset'], x['opcode']) for x in row['accesses']],
                         [(11, 'get_variable'), (17, 'set_variable')])
        self.assertEqual(row['if_preceding_access_hints'][0]['prior_eight_records_access_hints'],
                         [{'offset': 11, 'opcode': 'get_variable', 'records_before_if': 1}])
        self.assertEqual(result['verified_story_events'], 0)

    def test_compressed_and_does_not_leak_original_string(self):
        result = self.run_fixture(True)
        self.assertEqual(result['selected_action_tags'], 1)
        self.assertNotIn('SECRET', str(result))
        self.assertNotIn('fixture.swf', str(result))

    def test_nested_function_body_is_opaque(self):
        action = bytes([0x9b, 3, 0, 0x1d, 0x1c, 0x4f, 0])
        self.assertEqual(action_records(action), [(0, 0x9b)])
        self.assertEqual(access_hints(action, [])[0], [])

    def test_tampered_edge_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fixture.swf'
            path.write_bytes(swf(self.ACTION))
            index, queue, edges = reports(path)
            edges['candidates'][0]['edges'][0]['target_offset'] += 1
            with self.assertRaisesRegex(ValueError, 'branch edge evidence mismatch'):
                build_state_access(path, index, queue, edges)

    def test_truncated_and_invalid_end_rejected(self):
        for action in (bytes([0x96, 4, 0, 0]), bytes([0x1c]), bytes([0, 0x1d])):
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    action_records(action)


if __name__ == '__main__':
    unittest.main()
