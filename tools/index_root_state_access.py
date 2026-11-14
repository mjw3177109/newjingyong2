#!/usr/bin/env python3
"""Source-free AVM1 data-access opcode hints near selected root IF branches.

This does not decode identifiers, Push operands, conditions, or function bodies.
"""
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

try:
    from tools.index_swf_sprite_timeline import load_swf, iter_tags
    from tools.index_swf_action_opcodes import inspect_actions
    from tools.index_root_conditional_edges import branch_edges
except ModuleNotFoundError:
    from index_swf_sprite_timeline import load_swf, iter_tags
    from index_swf_action_opcodes import inspect_actions
    from index_root_conditional_edges import branch_edges

ACCESS_OPCODES = {
    0x1C: 'get_variable', 0x1D: 'set_variable',
    0x4E: 'get_member', 0x4F: 'set_member',
    0x22: 'get_property', 0x23: 'set_property',
    0x3C: 'define_local', 0x41: 'define_local2',
    0x87: 'store_register',
}


def action_records(payload):
    """Return only (byte offset, numeric opcode); never export operands."""
    pos, records, ended = 0, [], False
    while pos < len(payload):
        start = pos
        opcode = payload[pos]
        pos += 1
        if opcode == 0:
            ended = True
            if any(payload[pos:]):
                raise ValueError('nonzero bytes after ActionEnd')
            break
        records.append((start, opcode))
        if opcode >= 0x80:
            if pos + 2 > len(payload):
                raise ValueError('truncated action length')
            length = struct.unpack_from('<H', payload, pos)[0]
            pos += 2
            if length > len(payload) - pos:
                raise ValueError('truncated action payload')
            pos += length
    if not ended:
        raise ValueError('missing ActionEnd')
    return records


def access_hints(payload, edges):
    records = action_records(payload)
    access = [{'offset': pos, 'opcode': ACCESS_OPCODES[op]}
              for pos, op in records if op in ACCESS_OPCODES]
    by_position = {pos: idx for idx, (pos, _) in enumerate(records)}
    if_context = []
    for edge in edges:
        if edge['opcode'] != 'if':
            continue
        idx = by_position.get(edge['source_offset'])
        if idx is None or records[idx][1] != 0x9D:
            raise ValueError('IF edge does not match opcode boundary')
        preceding = [
            {'offset': pos, 'opcode': ACCESS_OPCODES[op], 'records_before_if': idx - j}
            for j, (pos, op) in enumerate(records[max(0, idx - 8):idx], start=max(0, idx - 8))
            if op in ACCESS_OPCODES
        ]
        if_context.append({'if_source_offset': edge['source_offset'],
                           'prior_eight_records_access_hints': preceding})
    return access, if_context


def build_state_access(path, opcodes, queue, edges):
    if (opcodes.get('schema') != 'swf-root-action-opcode-evidence-v1'
            or queue.get('schema') != 'swf-root-conditional-review-queue-v1'
            or edges.get('schema') != 'swf-root-conditional-edges-v1'):
        raise ValueError('unsupported evidence schema')
    raw, data, offset = load_swf(path)
    sha = hashlib.sha256(raw).hexdigest()
    if any(report.get('source_swf_sha256') != sha for report in (opcodes, queue, edges)):
        raise ValueError('source SWF fingerprint mismatch')
    rows = opcodes.get('action_tags')
    selected = queue.get('candidates')
    edge_rows = edges.get('candidates')
    if (not isinstance(rows, list) or not isinstance(selected, list)
            or not isinstance(edge_rows, list)
            or len(rows) != opcodes.get('root_doaction_tags')
            or len(selected) != queue.get('selected_candidate_count')
            or len(selected) != edges.get('selected_action_tags')
            or len(edge_rows) != len(selected)
            or len(selected) > 100
            or queue.get('verified_story_events') != 0
            or edges.get('verified_story_events') != 0):
        raise ValueError('invalid selection metadata')
    selected_by_ordinal = {}
    for candidate, edge_row in zip(selected, edge_rows):
        ordinal = candidate.get('action_tag_ordinal')
        if (type(ordinal) is not int or not 1 <= ordinal <= len(rows)
                or ordinal in selected_by_ordinal
                or candidate.get('review_status') != 'unverified'
                or edge_row.get('review_status') != 'unverified'
                or edge_row.get('action_tag_ordinal') != ordinal
                or edge_row.get('root_frame') != candidate.get('root_frame')
                or edge_row.get('action_sha256') != candidate.get('action_sha256')):
            raise ValueError('invalid candidate/edge alignment')
        selected_by_ordinal[ordinal] = (candidate, edge_row)
    frame, ordinal, frames = 1, 0, 0
    output = {}
    totals = Counter()
    for code, payload in iter_tags(data, offset, len(data)):
        if code == 1:
            frame += 1
            frames += 1
        elif code == 12:
            ordinal += 1
            if ordinal > len(rows):
                raise ValueError('extra root action tag')
            source = rows[ordinal - 1]
            digest = hashlib.sha256(payload).hexdigest()
            if (source.get('tag_ordinal') != ordinal or source.get('root_frame') != frame
                    or source.get('action_sha256') != digest):
                raise ValueError('opcode index and original SWF mismatch')
            if ordinal not in selected_by_ordinal:
                continue
            candidate, edge_row = selected_by_ordinal[ordinal]
            counts, warnings = inspect_actions(payload)
            if (warnings or source.get('parse_warnings') != []
                    or counts != source.get('opcode_counts')
                    or candidate.get('root_frame') != frame
                    or candidate.get('action_sha256') != digest
                    or candidate.get('conditional_opcode_count') != counts.get('if', 0)
                    or candidate.get('jump_opcode_count') != counts.get('jump', 0)
                    or counts.get('if', 0) < 1):
                raise ValueError('candidate opcode evidence mismatch')
            actual_edges = branch_edges(payload)
            if actual_edges != edge_row.get('edges'):
                raise ValueError('branch edge evidence mismatch')
            access, context = access_hints(payload, actual_edges)
            totals.update(a['opcode'] for a in access)
            output[ordinal] = {'root_frame': frame, 'action_tag_ordinal': ordinal,
                               'action_sha256': digest, 'accesses': access,
                               'if_preceding_access_hints': context,
                               'review_status': 'unverified'}
    if (ordinal != len(rows) or frames != opcodes.get('root_showframe_tags')
            or frames != queue.get('root_showframe_tags')
            or ordinal != queue.get('root_doaction_tags')
            or len(output) != len(selected)):
        raise ValueError('root timeline count mismatch')
    result_rows = [output[c['action_tag_ordinal']] for c in selected]
    return {'schema': 'swf-root-state-access-hints-v1', 'source_swf_sha256': sha,
            'selected_action_tags': len(result_rows),
            'access_opcode_counts': dict(sorted(totals.items())),
            'total_access_opcode_records': sum(totals.values()),
            'candidates': result_rows, 'verified_story_events': 0,
            'interpretation': 'Only top-level AVM1 opcode locations and preceding-eight-record proximity hints; no variable identifiers, stack/branch semantics, nested functions, runtime behavior, story or media exported.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('swf')
    parser.add_argument('--opcodes', required=True)
    parser.add_argument('--queue', required=True)
    parser.add_argument('--edges', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    reports = [json.loads(Path(p).read_text(encoding='utf-8'))
               for p in (args.opcodes, args.queue, args.edges)]
    result = build_state_access(args.swf, *reports)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('Root state access hints: {} selected tags, {} opcode records, verified events: 0'.format(
        result['selected_action_tags'], result['total_access_opcode_records']))


if __name__ == '__main__':
    main()
