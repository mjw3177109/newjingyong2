#!/usr/bin/env python3
"""Compare operand-free opcode shapes for adjacent root IFs in stride clusters.

This is structural navigation only. It does not decode Push operands, prove
predicate equality, runtime execution, map identity or story semantics.
"""
import argparse
import json
import re
from pathlib import Path

try:
    from tools.index_root_if_opcode_windows import CLASSES
except ModuleNotFoundError:
    from index_root_if_opcode_windows import CLASSES

HEX24 = re.compile(r'^[0-9a-f]{24}$')
HEX64 = re.compile(r'^[0-9a-f]{64}$')
SAFE_CLASSES = frozenset(CLASSES.values()) | {'other'}
STOP_REASONS = frozenset({
    'action_end', 'control_flow_join', 'window_limit',
    'branch_or_opaque_boundary',
})


def checked_int(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('invalid structural count or coordinate')
    return value


def checked_classes(value, maximum):
    if (not isinstance(value, list) or len(value) > maximum
            or any(type(x) is not str or x not in SAFE_CLASSES for x in value)):
        raise ValueError('invalid operand-free opcode classes')
    return tuple(value)


def opcode_shape(row):
    """Return only bounded class sequences and stop/boundary indicators."""
    preceding = checked_classes(row.get('straight_line_preceding_opcode_classes'), 32)
    limited = row.get('straight_line_boundary_limited')
    arms = row.get('successor_arm_windows')
    if type(limited) is not bool or not isinstance(arms, dict) or set(arms) != {'branch', 'fallthrough'}:
        raise ValueError('invalid bounded opcode window')
    shapes = []
    for name in ('branch', 'fallthrough'):
        arm = arms[name]
        if not isinstance(arm, dict) or arm.get('stop_reason') not in STOP_REASONS:
            raise ValueError('invalid successor arm')
        shapes.append((checked_classes(arm.get('opcode_classes'), 8), arm['stop_reason']))
    return ((preceding, limited), *shapes)


def compare_shapes(clusters, windows):
    if (not isinstance(clusters, dict)
            or clusters.get('schema') != 'swf-root-if-structural-clusters-v1'
            or not isinstance(windows, dict)
            or windows.get('schema') != 'swf-root-if-opcode-windows-v1'):
        raise ValueError('unexpected input schemas')
    sha = clusters.get('source_swf_sha256')
    if (not isinstance(sha, str) or not HEX64.fullmatch(sha)
            or windows.get('source_swf_sha256') != sha
            or clusters.get('verified_story_events') != 0
            or clusters.get('ready_for_html5_mapping') != 0
            or windows.get('verified_story_events') != 0):
        raise ValueError('source identity or semantic claim mismatch')
    rows = windows.get('entries')
    runs = clusters.get('repeated_stride_runs')
    if not isinstance(rows, list) or not isinstance(runs, list):
        raise ValueError('missing IF windows or stride clusters')
    if (checked_int(windows.get('selected_if_count')) != len(rows)
            or checked_int(clusters.get('candidate_count')) != len(rows)
            or checked_int(clusters.get('repeated_stride_run_count')) != len(runs)):
        raise ValueError('candidate or cluster count mismatch')
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or row.get('review_status') != 'unverified':
            raise ValueError('invalid window review status')
        rid = row.get('review_id')
        if not isinstance(rid, str) or not HEX24.fullmatch(rid) or rid in by_id:
            raise ValueError('invalid or duplicate window review ID')
        for field, minimum in (('root_frame', 1), ('action_tag_ordinal', 1),
                               ('if_source_offset', 0)):
            checked_int(row.get(field), minimum)
        by_id[rid] = row
    groups = clusters.get('action_groups')
    if not isinstance(groups, list) or checked_int(clusters.get('action_group_count')) != len(groups):
        raise ValueError('missing action groups')
    grouped_ids = []
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get('review_ids'), list):
            raise ValueError('invalid action group')
        checked_int(group.get('root_frame'), 1)
        checked_int(group.get('action_tag_ordinal'), 1)
        if checked_int(group.get('candidate_count')) != len(group['review_ids']):
            raise ValueError('action group count mismatch')
        members = []
        for rid in group['review_ids']:
            row = by_id.get(rid)
            if (row is None or row['root_frame'] != group['root_frame']
                    or row['action_tag_ordinal'] != group['action_tag_ordinal']):
                raise ValueError('action group/window identity mismatch')
            members.append(row['if_source_offset'])
            grouped_ids.append(rid)
        if (members != sorted(set(members))
                or members[0] != group.get('first_if_source_offset')
                or members[-1] != group.get('last_if_source_offset')):
            raise ValueError('invalid action group offsets')
    if len(grouped_ids) != len(set(grouped_ids)) or set(grouped_ids) != set(by_id):
        raise ValueError('incomplete or duplicate action group coverage')

    pairs = []
    for run in runs:
        if not isinstance(run, dict) or not isinstance(run.get('review_ids'), list):
            raise ValueError('invalid stride run')
        ids = run['review_ids']
        stride = checked_int(run.get('if_offset_stride'), 1)
        if len(ids) < 3 or checked_int(run.get('candidate_count')) != len(ids):
            raise ValueError('invalid stride candidate count')
        frame = checked_int(run.get('root_frame'), 1)
        action = checked_int(run.get('action_tag_ordinal'), 1)
        members = []
        for rid in ids:
            row = by_id.get(rid)
            if row is None or row['root_frame'] != frame or row['action_tag_ordinal'] != action:
                raise ValueError('stride run/window identity mismatch')
            members.append(row)
        offsets = [row['if_source_offset'] for row in members]
        if (len(ids) != len(set(ids))
                or any(b - a != stride for a, b in zip(offsets, offsets[1:]))
                or offsets[0] != run.get('first_if_source_offset')
                or offsets[-1] != run.get('last_if_source_offset')):
            raise ValueError('stride run offsets differ from original window locations')
        for first, second in zip(members, members[1:]):
            a, b = opcode_shape(first), opcode_shape(second)
            same = [a[i] == b[i] for i in range(3)]
            pairs.append({
                'root_frame': frame,
                'action_tag_ordinal': action,
                'left_review_id': first['review_id'],
                'right_review_id': second['review_id'],
                'left_if_source_offset': first['if_source_offset'],
                'right_if_source_offset': second['if_source_offset'],
                'straight_line_predecessor_shape_equal': same[0],
                'branch_successor_shape_equal': same[1],
                'fallthrough_successor_shape_equal': same[2],
                'all_bounded_shapes_equal': all(same),
                'review_status': 'unverified',
            })
    return {
        'schema': 'swf-root-if-adjacent-opcode-shape-comparison-v1',
        'source_swf_sha256': sha,
        'stride_run_count': len(runs),
        'adjacent_pair_count': len(pairs),
        'fully_equal_pair_count': sum(p['all_bounded_shapes_equal'] for p in pairs),
        'adjacent_pairs': pairs,
        'verified_story_events': 0,
        'ready_for_html5_mapping': 0,
        'warning': 'Equal bounded opcode classes and stop reasons do not imply equal operands, conditions, state effects, runtime behavior, maps or story events. No SWF assets, scripts, identifiers or operand values are exported.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clusters', type=Path, required=True)
    parser.add_argument('--windows', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = compare_shapes(
        json.loads(args.clusters.read_text(encoding='utf-8')),
        json.loads(args.windows.read_text(encoding='utf-8')))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Adjacent IF pairs:', result['adjacent_pair_count'],
          'same bounded opcode shapes:', result['fully_equal_pair_count'],
          'verified story events: 0')


if __name__ == '__main__':
    main()
