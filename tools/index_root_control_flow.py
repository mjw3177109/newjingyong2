#!/usr/bin/env python3
"""Source-free local AVM1 control-flow graph for reviewed root DoAction tags.

This is a syntactic, intra-action-tag graph only. It does not decode constants,
variable names, function bodies, runtime paths, or original story semantics.
"""
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

try:
    from tools.index_swf_sprite_timeline import load_swf, iter_tags
    from tools.index_root_conditional_edges import branch_edges
    from tools.index_root_state_access import action_records, build_state_access
except ModuleNotFoundError:
    from index_swf_sprite_timeline import load_swf, iter_tags
    from index_root_conditional_edges import branch_edges
    from index_root_state_access import action_records, build_state_access

OPAQUE_CONTROL = {0x8A, 0x8D, 0x8F, 0x94, 0x9B, 0x8E}
TERMINATORS = {0x3E, 0x2A}  # Return, Throw


def local_graph(payload, expected_edges=None):
    """Inspect record-boundary successors without reading operands as text."""
    records = action_records(payload)
    actual_edges = branch_edges(payload)
    if expected_edges is not None and actual_edges != expected_edges:
        raise ValueError('branch evidence mismatch')
    if any(e['target_alignment'] != 'record_boundary' for e in actual_edges):
        raise ValueError('unsafe branch target')
    edge_by_source = {e['source_offset']: e for e in actual_edges}
    if len(edge_by_source) != len(actual_edges):
        raise ValueError('duplicate branch source')
    if records:
        last, op = records[-1]
        end = last + 1 if op < 0x80 else last + 3 + struct.unpack_from('<H', payload, last + 1)[0]
    else:
        end = 0
    if end >= len(payload) or payload[end] != 0:
        raise ValueError('invalid ActionEnd boundary')
    offsets = [pos for pos, _ in records]
    successors = {}
    conditional = []
    opaque = 0
    for i, (pos, opcode) in enumerate(records):
        following = offsets[i + 1] if i + 1 < len(records) else end
        edge = edge_by_source.get(pos)
        if opcode in (0x99, 0x9D):
            if edge is None or edge['opcode'] != ('if' if opcode == 0x9D else 'jump'):
                raise ValueError('missing branch edge')
            target = edge['target_offset']
            successors[pos] = [target] if opcode == 0x99 else sorted(set([target, following]))
            if opcode == 0x9D:
                conditional.append({'if_source_offset': pos,
                                    'branch_target_offset': target,
                                    'fallthrough_offset': following,
                                    'branch_and_fallthrough_distinct': target != following})
        elif opcode in TERMINATORS:
            successors[pos] = []
        else:
            successors[pos] = [following]
        opaque += opcode in OPAQUE_CONTROL
    if len(edge_by_source) != sum(op in (0x99, 0x9D) for _, op in records):
        raise ValueError('branch record count mismatch')
    reachable = set()
    todo = [offsets[0] if offsets else end]
    while todo:
        node = todo.pop()
        if node in reachable:
            continue
        reachable.add(node)
        todo.extend(s for s in successors.get(node, []) if s not in reachable)
    return {'record_count': len(records),
            'reachable_record_count': sum(pos in reachable for pos in offsets),
            'unreachable_record_count': sum(pos not in reachable for pos in offsets),
            'action_end_reachable': end in reachable,
            'conditional_count': len(conditional),
            'jump_count': sum(op == 0x99 for _, op in records),
            'backward_branch_count': sum(e['target_offset'] <= e['source_offset'] for e in actual_edges),
            'opaque_control_opcode_count': opaque,
            'if_successors': [{**c, 'if_record_reachable': c['if_source_offset'] in reachable}
                              for c in conditional]}


def build_control_flow(path, opcodes, queue, edges, state_access):
    if state_access.get('schema') != 'swf-root-state-access-hints-v1':
        raise ValueError('unsupported state access schema')
    if build_state_access(path, opcodes, queue, edges) != state_access:
        raise ValueError('state access evidence mismatch')
    raw, data, offset = load_swf(path)
    digest = hashlib.sha256(raw).hexdigest()
    selected = {r['action_tag_ordinal']: r for r in edges['candidates']}
    results = {}
    ordinal, frame = 0, 1
    totals = Counter()
    for code, payload in iter_tags(data, offset, len(data)):
        if code == 1:
            frame += 1
        elif code == 12:
            ordinal += 1
            if ordinal not in selected:
                continue
            reference = selected[ordinal]
            if (reference['root_frame'] != frame
                    or reference['action_sha256'] != hashlib.sha256(payload).hexdigest()):
                raise ValueError('selected action fingerprint mismatch')
            graph = local_graph(payload, reference['edges'])
            totals.update({k: graph[k] for k in ('record_count', 'reachable_record_count',
                           'unreachable_record_count', 'conditional_count', 'jump_count',
                           'backward_branch_count', 'opaque_control_opcode_count')})
            results[ordinal] = {'root_frame': frame, 'action_tag_ordinal': ordinal,
                                'action_sha256': reference['action_sha256'],
                                **graph, 'review_status': 'unverified'}
    if ordinal != opcodes['root_doaction_tags'] or len(results) != len(selected):
        raise ValueError('root action count mismatch')
    ordered = [results[c['action_tag_ordinal']] for c in queue['candidates']]
    return {'schema': 'swf-root-local-control-flow-v1', 'source_swf_sha256': digest,
            'selected_action_tags': len(ordered), 'aggregate': dict(sorted(totals.items())),
            'candidates': ordered, 'verified_story_events': 0,
            'interpretation': 'Syntactic intra-tag AVM1 graph only. Opaque control opcodes, nested functions, stack values, variable semantics, runtime paths, maps and story remain unverified. No source strings or media exported.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('swf')
    for name in ('opcodes', 'queue', 'edges', 'state-access'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    reports = [json.loads(Path(getattr(args, name.replace('-', '_'))).read_text(encoding='utf-8'))
               for name in ('opcodes', 'queue', 'edges', 'state-access')]
    result = build_control_flow(args.swf, *reports)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('Root local CFG: {} selected tags, {} IF nodes, {} unreachable records, {} opaque control records; verified events: 0'.format(
        result['selected_action_tags'], result['aggregate'].get('conditional_count', 0),
        result['aggregate'].get('unreachable_record_count', 0),
        result['aggregate'].get('opaque_control_opcode_count', 0)))


if __name__ == '__main__':
    main()
