"""Synthetic, source-free tests for adjacent IF opcode-shape comparison."""
import copy
import unittest

from tools.compare_root_if_opcode_shapes import compare_shapes


def fixture():
    ids = [f'{i + 1:024x}' for i in range(4)]
    offsets = [100, 133, 166, 199]
    rows = []
    for rid, offset in zip(ids, offsets):
        rows.append({
            'review_id': rid, 'root_frame': 55, 'action_tag_ordinal': 9,
            'if_source_offset': offset, 'review_status': 'unverified',
            'straight_line_preceding_opcode_classes': ['push_opaque', 'comparison'],
            'straight_line_boundary_limited': False,
            'successor_arm_windows': {
                'branch': {'opcode_classes': ['other', 'branch'],
                           'stop_reason': 'branch_or_opaque_boundary'},
                'fallthrough': {'opcode_classes': ['push_opaque', 'variable_write'],
                                'stop_reason': 'window_limit'},
            },
        })
    clusters = {
        'schema': 'swf-root-if-structural-clusters-v1',
        'source_swf_sha256': 'a' * 64,
        'candidate_count': 4,
        'action_group_count': 1,
        'action_groups': [{
            'root_frame': 55, 'action_tag_ordinal': 9,
            'candidate_count': 4, 'first_if_source_offset': 100,
            'last_if_source_offset': 199, 'review_ids': ids,
        }],
        'repeated_stride_run_count': 1,
        'repeated_stride_runs': [{
            'root_frame': 55, 'action_tag_ordinal': 9,
            'if_offset_stride': 33, 'candidate_count': 4,
            'first_if_source_offset': 100, 'last_if_source_offset': 199,
            'review_ids': ids,
        }],
        'verified_story_events': 0, 'ready_for_html5_mapping': 0,
    }
    windows = {
        'schema': 'swf-root-if-opcode-windows-v1',
        'source_swf_sha256': 'a' * 64,
        'selected_if_count': 4, 'entries': rows,
        'verified_story_events': 0,
    }
    return clusters, windows


class AdjacentOpcodeShapeTests(unittest.TestCase):
    def test_equal_shapes_are_not_semantic_claims(self):
        clusters, windows = fixture()
        result = compare_shapes(clusters, windows)
        self.assertEqual(result['adjacent_pair_count'], 3)
        self.assertEqual(result['fully_equal_pair_count'], 3)
        self.assertTrue(all(p['all_bounded_shapes_equal'] for p in result['adjacent_pairs']))
        self.assertEqual(result['verified_story_events'], 0)
        self.assertEqual(result['ready_for_html5_mapping'], 0)
        self.assertNotIn('push_operand', str(result))

    def test_distinguishes_predecessor_and_successor_shapes(self):
        clusters, windows = fixture()
        windows['entries'][1]['straight_line_preceding_opcode_classes'] = ['variable_read', 'comparison']
        windows['entries'][2]['successor_arm_windows']['branch']['opcode_classes'] = ['branch']
        result = compare_shapes(clusters, windows)
        self.assertEqual(result['fully_equal_pair_count'], 0)
        self.assertFalse(result['adjacent_pairs'][0]['straight_line_predecessor_shape_equal'])
        self.assertFalse(result['adjacent_pairs'][1]['branch_successor_shape_equal'])
        self.assertTrue(result['adjacent_pairs'][2]['straight_line_predecessor_shape_equal'])

    def test_input_order_independent_and_no_runs(self):
        clusters, windows = fixture()
        original = compare_shapes(clusters, windows)
        windows['entries'].reverse()
        self.assertEqual(original, compare_shapes(clusters, windows))
        clusters['repeated_stride_runs'] = []
        clusters['repeated_stride_run_count'] = 0
        result = compare_shapes(clusters, windows)
        self.assertEqual(result['adjacent_pair_count'], 0)

    def test_rejects_tampered_provenance_and_coordinates(self):
        for kind in ('sha', 'duplicate', 'stride', 'group', 'status',
                     'operand', 'bool', 'story', 'unknown_class'):
            clusters, windows = fixture()
            if kind == 'sha':
                windows['source_swf_sha256'] = 'b' * 64
            elif kind == 'duplicate':
                windows['entries'][1]['review_id'] = windows['entries'][0]['review_id']
            elif kind == 'stride':
                clusters['repeated_stride_runs'][0]['if_offset_stride'] = 34
            elif kind == 'group':
                clusters['action_groups'][0]['review_ids'].pop()
            elif kind == 'status':
                windows['entries'][0]['review_status'] = 'verified'
            elif kind == 'operand':
                windows['entries'][0]['successor_arm_windows']['branch']['opcode_classes'] = ['secret_name']
            elif kind == 'bool':
                windows['entries'][0]['if_source_offset'] = True
            elif kind == 'story':
                clusters['verified_story_events'] = 1
            else:
                windows['entries'][0]['straight_line_preceding_opcode_classes'] = ['ActionPush:hello']
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                compare_shapes(clusters, windows)


if __name__ == '__main__':
    unittest.main()
