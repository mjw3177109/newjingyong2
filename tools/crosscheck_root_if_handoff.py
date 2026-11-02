#!/usr/bin/env python3
"""Cross-check source-free root IF handoff and raw-SWF opcode windows.

Structural consistency only. Never imports decompiled scripts, operands, art or audio.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

HEX64 = re.compile(r'^[0-9a-f]{64}$')
HEX24 = re.compile(r'^[0-9a-f]{24}$')

# The source-free window producer maps AVM1 opcodes to this fixed vocabulary.
# Unknown labels must not be able to masquerade as a comparison hint.
OPCODE_CLASSES = frozenset({
    'push_opaque', 'constant_pool_opaque', 'variable_read', 'variable_write',
    'member_read', 'member_write', 'property_read', 'property_write',
    'local_write', 'register_write',
    'comparison', 'boolean_logic', 'arithmetic', 'branch',
    'opaque_control', 'call', 'other',
})


def _checked_window(row, width, if_offset):
    offsets = row.get('preceding_record_offsets')
    classes = row.get('preceding_opcode_classes')
    safe_offsets = row.get('straight_line_preceding_record_offsets')
    safe_classes = row.get('straight_line_preceding_opcode_classes')
    if (not isinstance(offsets, list) or not isinstance(classes, list)
            or not isinstance(safe_offsets, list) or not isinstance(safe_classes, list)
            or len(offsets) != len(classes)
            or len(safe_offsets) != len(safe_classes)
            or len(offsets) > width
            or len(safe_offsets) > len(offsets)
            or len(offsets) != _count(row.get('preceding_record_count'))
            or len(safe_offsets) != _count(row.get('straight_line_preceding_record_count'))):
        raise ValueError('invalid bounded opcode window lengths')
    if (any(type(pos) is not int or pos < 0 or pos >= if_offset for pos in offsets)
            or offsets != sorted(set(offsets))
            or any(type(pos) is not int for pos in safe_offsets)
            or (safe_offsets and safe_offsets != offsets[-len(safe_offsets):])):
        raise ValueError('invalid preceding opcode offsets')
    if (any(type(value) is not str or value not in OPCODE_CLASSES
            for value in classes + safe_classes)
            or (safe_classes and safe_classes != classes[-len(safe_classes):])):
        raise ValueError('invalid preceding opcode classes')
    if (_count(row.get('comparison_opcode_count')) != classes.count('comparison')
            or type(row.get('straight_line_boundary_limited')) is not bool
            or row['straight_line_boundary_limited'] != (len(safe_offsets) < len(offsets))
            or type(row.get('has_branch_or_opaque_control')) is not bool
            or row['has_branch_or_opaque_control'] != any(
                cls in ('branch', 'opaque_control') for cls in classes)):
        raise ValueError('inconsistent preceding opcode summary')
    return safe_classes



def _checked_predecessors(row, if_offset):
    """Validate operand-free incoming-edge summaries, not runtime reachability."""
    edges = row.get('if_incoming_syntactic_edges')
    unreachable_offsets = row.get('if_incoming_unreachable_syntactic_source_offsets')
    if not isinstance(edges, list) or not isinstance(unreachable_offsets, list):
        raise ValueError('missing syntactic predecessor evidence')
    pairs = []
    for edge in edges:
        if (not isinstance(edge, dict)
                or set(edge) != {'source_offset', 'edge_kind'}
                or type(edge['source_offset']) is not int or edge['source_offset'] < 0
                or edge['edge_kind'] not in ('branch', 'fallthrough')):
            raise ValueError('invalid syntactic predecessor edge')
        pairs.append((edge['source_offset'], edge['edge_kind']))
    if pairs != sorted(set(pairs)):
        raise ValueError('duplicate or unsorted syntactic predecessor edges')
    sources = {pos for pos, _ in pairs}
    if (any(type(pos) is not int or pos < 0 for pos in unreachable_offsets)
            or unreachable_offsets != sorted(set(unreachable_offsets))
            or not set(unreachable_offsets).issubset(sources)):
        raise ValueError('invalid unreachable syntactic predecessor offsets')
    total = _count(row.get('if_incoming_syntactic_source_count'))
    reachable = _count(row.get('if_incoming_reachable_syntactic_source_count'))
    unreachable = _count(row.get('if_incoming_unreachable_syntactic_source_count'))
    flags = ('if_has_multiple_syntactic_predecessors',
             'if_has_multiple_reachable_syntactic_predecessors',
             'if_has_backward_or_self_incoming_branch',
             'if_is_action_entry',
             'if_has_opaque_immediate_predecessor')
    if any(type(row.get(name)) is not bool for name in flags):
        raise ValueError('invalid syntactic predecessor flags')
    if (total != len(sources) or reachable + unreachable != total
            or unreachable != len(unreachable_offsets)
            or row['if_has_multiple_syntactic_predecessors'] != (total > 1)
            or row['if_has_multiple_reachable_syntactic_predecessors'] != (reachable > 1)
            or row['if_has_backward_or_self_incoming_branch'] != any(
                kind == 'branch' and pos >= if_offset for pos, kind in pairs)):
        raise ValueError('inconsistent syntactic predecessor summary')
    return reachable


def _checked_successor_arms(row):
    """Validate bounded operand-free successor hints before using them for triage.

    This is internal consistency only: raw-SWF provenance is checked by the
    producer, not reconstructed from the public source-free report.
    """
    limit = row.get('successor_arm_window_limit')
    if type(limit) is not int or limit != 8:
        raise ValueError('invalid successor arm window limit')
    distinct = row.get('successor_arms_distinct')
    expected_distinct = row['branch_target_offset'] != row['fallthrough_offset']
    if type(distinct) is not bool or distinct != expected_distinct:
        raise ValueError('inconsistent successor arm distinct flag')
    arms = row.get('successor_arm_windows')
    if not isinstance(arms, dict) or set(arms) != {'branch', 'fallthrough'}:
        raise ValueError('invalid successor arm windows')
    write_classes = {'variable_write', 'member_write', 'property_write',
                     'local_write', 'register_write'}
    for name, coordinate in (('branch', 'branch_target_offset'),
                             ('fallthrough', 'fallthrough_offset')):
        arm = arms[name]
        if not isinstance(arm, dict) or set(arm) != {
                'start_offset', 'record_offsets', 'opcode_classes',
                'write_opcode_hint_count', 'stop_reason'}:
            raise ValueError('invalid successor arm fields')
        start = arm['start_offset']
        offsets, classes = arm['record_offsets'], arm['opcode_classes']
        if (type(start) is not int or start != row[coordinate]
                or not isinstance(offsets, list) or not isinstance(classes, list)
                or len(offsets) != len(classes) or len(offsets) > limit
                or any(type(pos) is not int or pos < start for pos in offsets)
                or offsets != sorted(set(offsets))
                or (offsets and offsets[0] != start)
                or any(type(cls) is not str or cls not in OPCODE_CLASSES for cls in classes)):
            raise ValueError('invalid successor arm opcode window')
        reason = arm['stop_reason']
        if (type(reason) is not str or reason not in {
                'action_end', 'control_flow_join', 'window_limit',
                'branch_or_opaque_boundary'}
                or (not offsets and reason != 'action_end')
                or (reason == 'window_limit' and len(offsets) != limit)
                or (reason == 'branch_or_opaque_boundary' and not offsets)
                or (classes and classes[-1] in ('branch', 'opaque_control')
                    and reason != 'branch_or_opaque_boundary')
                or _count(arm['write_opcode_hint_count']) != sum(
                    cls in write_classes for cls in classes)):
            raise ValueError('inconsistent successor arm summary')
    if not distinct and arms['branch'] != arms['fallthrough']:
        raise ValueError('shared successor arms disagree')
    return arms


def _count(value):
    if type(value) is not int or value < 0:
        raise ValueError('invalid nonnegative count')
    return value


def crosscheck(handoff, windows):
    if not isinstance(handoff, dict) or handoff.get('schema') != 'swf-root-if-audit-handoff-v1':
        raise ValueError('invalid handoff schema')
    if not isinstance(windows, dict) or windows.get('schema') != 'swf-root-if-opcode-windows-v1':
        raise ValueError('invalid opcode windows schema')
    swf = handoff.get('source_swf_sha256')
    if not isinstance(swf, str) or not HEX64.fullmatch(swf) or windows.get('source_swf_sha256') != swf:
        raise ValueError('source SWF fingerprint mismatch')
    if (handoff.get('verified_story_events') != 0 or handoff.get('ready_for_html5_mapping') != 0
            or windows.get('verified_story_events') != 0):
        raise ValueError('unverified structural reports cannot claim story events')
    hrows, wrows = handoff.get('entries'), windows.get('entries')
    if not isinstance(hrows, list) or not isinstance(wrows, list) or not hrows:
        raise ValueError('missing structural candidates')
    if (_count(handoff.get('candidate_count')) != len(hrows)
            or _count(windows.get('selected_if_count')) != len(wrows)
            or len(hrows) != len(wrows)):
        raise ValueError('candidate count mismatch')
    if type(windows.get('window_width')) is not int or not 1 <= windows['window_width'] <= 32:
        raise ValueError('invalid window width')
    by_id = {}
    for row in wrows:
        if not isinstance(row, dict):
            raise ValueError('invalid opcode window row')
        rid = row.get('review_id')
        if not isinstance(rid, str) or not HEX24.fullmatch(rid) or rid in by_id:
            raise ValueError('invalid or duplicate opcode window identity')
        if row.get('review_status') != 'unverified':
            raise ValueError('opcode window contains semantic claims')
        by_id[rid] = row
    seen, output = set(), []
    for row in hrows:
        if not isinstance(row, dict):
            raise ValueError('invalid handoff row')
        rid, location = row.get('review_id'), row.get('source_location')
        if not isinstance(rid, str) or not HEX24.fullmatch(rid) or rid in seen or rid not in by_id:
            raise ValueError('handoff candidate identity mismatch')
        seen.add(rid)
        # Bind the anonymous review ID to the actual SWF and action bytes.
        # Otherwise a changed action hash could inherit another IF's audit.
        action_sha = location.get('action_sha256') if isinstance(location, dict) else None
        ordinal = location.get('action_tag_ordinal') if isinstance(location, dict) else None
        offset = location.get('if_source_offset') if isinstance(location, dict) else None
        if (not isinstance(action_sha, str) or not HEX64.fullmatch(action_sha)
                or type(ordinal) is not int or ordinal < 1
                or type(offset) is not int or offset < 0):
            raise ValueError('invalid action fingerprint or IF identity coordinates')
        expected_id = hashlib.sha256(
            f'{swf}:{ordinal}:{action_sha}:{offset}'.encode('ascii')).hexdigest()[:24]
        if rid != expected_id:
            raise ValueError('review identity does not match source action fingerprint')
        if (row.get('review_status') != 'unverified' or row.get('html5_event_id') is not None
                or not isinstance(location, dict)):
            raise ValueError('handoff contains semantic claims')
        checks = row.get('checks')
        # A missing checkbox must not silently mean "not reviewed": the
        # handoff schema requires an explicit, complete empty checklist.
        required_false = {
            'condition_confirmed', 'state_effects_confirmed',
            'map_context_confirmed', 'runtime_reproduced',
            'independent_reviewed', 'adaptation_rights_confirmed',
        }
        if (not isinstance(checks, dict)
                or set(checks) != required_false | {'ffdec_script_sha256'}
                or checks['ffdec_script_sha256'] is not None
                or any(checks[key] is not False for key in required_false)):
            raise ValueError('handoff contains incomplete or private attestations')
        window = by_id[rid]
        for key in ('root_frame', 'action_tag_ordinal', 'if_source_offset'):
            if (type(location.get(key)) is not int or location[key] < (1 if key != 'if_source_offset' else 0)
                    or window.get(key) != location[key]):
                raise ValueError('raw SWF window/source coordinate mismatch')
        # The review ID binds the IF source, but not its two successor offsets.
        # Require both coordinates to agree with the independent raw-SWF window.
        for key in ('branch_target_offset', 'fallthrough_offset'):
            if (type(location.get(key)) is not int or location[key] < 0
                    or type(window.get(key)) is not int or window[key] != location[key]):
                raise ValueError('raw SWF IF successor coordinate mismatch')
        classes = _checked_window(window, windows['window_width'], location['if_source_offset'])
        incoming = _checked_predecessors(window, location['if_source_offset'])
        arms = _checked_successor_arms(window)
        multiple = window['if_has_multiple_reachable_syntactic_predecessors']
        output.append({
            'review_id': rid,
            'root_frame': location['root_frame'],
            'action_tag_ordinal': location['action_tag_ordinal'],
            'if_source_offset': location['if_source_offset'],
            'bounded_comparison_opcode_present': 'comparison' in classes,
            'reachable_syntactic_predecessor_count': incoming,
            'multiple_reachable_syntactic_predecessors': multiple,
            'successor_branch_write_hint_count': arms['branch']['write_opcode_hint_count'],
            'successor_fallthrough_write_hint_count': arms['fallthrough']['write_opcode_hint_count'],
            'successor_arm_write_hints_differ': (arms['branch']['write_opcode_hint_count'] !=
                                                arms['fallthrough']['write_opcode_hint_count']),
            'review_status': 'unverified',
        })
    return {
        'schema': 'swf-root-if-handoff-window-crosscheck-v1',
        'source_swf_sha256': swf,
        'matched_candidate_count': len(output),
        'entries': output,
        'verified_story_events': 0,
        'ready_for_html5_mapping': 0,
        'warning': 'Matched structural coordinates and operand-free hints only. Neither IF predicates, runtime paths, original story events nor publication rights are verified.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--handoff', type=Path, required=True)
    parser.add_argument('--windows', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = crosscheck(json.loads(args.handoff.read_text(encoding='utf-8')),
                        json.loads(args.windows.read_text(encoding='utf-8')))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Root IF source-free handoff/window matches:', result['matched_candidate_count'],
          'verified story events:', result['verified_story_events'])


if __name__ == '__main__':
    main()