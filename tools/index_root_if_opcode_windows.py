#!/usr/bin/env python3
"""Recheck priority root IFs against raw SWF and export operand-free opcode windows.

This is a private-review navigation aid, NOT a condition decompiler. Linear
predecessors may be unreachable, may belong to another branch, or may be
separated by opaque AVM1 control flow. No Push data or source strings escape.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from tools.index_swf_sprite_timeline import load_swf, iter_tags
    from tools.index_root_state_access import action_records
    from tools.index_root_conditional_edges import branch_edges
    from tools.index_root_control_flow import local_graph
except ModuleNotFoundError:
    from index_swf_sprite_timeline import load_swf, iter_tags
    from index_root_state_access import action_records
    from index_root_conditional_edges import branch_edges
    from index_root_control_flow import local_graph

HEX64 = re.compile(r'^[0-9a-f]{64}$')
HEX24 = re.compile(r'^[0-9a-f]{24}$')
# Safe operator families only. Operands, strings, identifiers, and numeric
# constants are never parsed or exported.
CLASSES = {
    0x96: 'push_opaque', 0x88: 'constant_pool_opaque',
    0x1C: 'variable_read', 0x1D: 'variable_write',
    0x4E: 'member_read', 0x4F: 'member_write',
    0x22: 'property_read', 0x23: 'property_write',
    0x0E: 'comparison', 0x0F: 'comparison', 0x13: 'comparison',
    0x29: 'comparison', 0x49: 'comparison', 0x48: 'comparison',
    0x66: 'comparison', 0x67: 'comparison', 0x68: 'comparison',
    0x10: 'boolean_logic', 0x11: 'boolean_logic', 0x12: 'boolean_logic',
    0x47: 'arithmetic', 0x0A: 'arithmetic', 0x0B: 'arithmetic',
    0x0C: 'arithmetic', 0x0D: 'arithmetic', 0x21: 'arithmetic', 0x3F: 'arithmetic', 0x50: 'arithmetic',
    0x51: 'arithmetic',
    0x99: 'branch', 0x9D: 'branch',
    0x8A: 'opaque_control', 0x8D: 'opaque_control',
    0x8F: 'opaque_control', 0x94: 'opaque_control',
    0x9B: 'opaque_control', 0x8E: 'opaque_control',
    0x3D: 'call', 0x52: 'call', 0x53: 'call',
}


def window_for_if(payload, packet, width=12):
    if type(width) is not int or not 1 <= width <= 32:
        raise ValueError('invalid opcode window width')
    records = action_records(payload)
    source = packet.get('if_source_offset')
    positions = [pos for pos, _ in records]
    if type(source) is not int or source not in positions:
        raise ValueError('IF source is not a record boundary')
    idx = positions.index(source)
    if records[idx][1] != 0x9D:
        raise ValueError('review source is not an IF opcode')
    edges = branch_edges(payload)
    graph = local_graph(payload, edges)
    matching = [e for e in edges if e['source_offset'] == source and e['opcode'] == 'if']
    successors = [s for s in graph['if_successors'] if s['if_source_offset'] == source]
    if len(matching) != 1 or len(successors) != 1:
        raise ValueError('IF edge or successor missing')
    edge, successor = matching[0], successors[0]
    if (edge['target_alignment'] != 'record_boundary'
            or packet.get('branch_target_offset') != edge['target_offset']
            or packet.get('fallthrough_offset') != successor['fallthrough_offset']
            or packet.get('if_record_reachable') is not successor['if_record_reachable']):
        raise ValueError('packet branch or reachability differs from raw SWF')
    preceding = records[max(0, idx - width):idx]
    classes = [CLASSES.get(op, 'other') for _, op in preceding]
    return {
        'review_id': packet['review_id'],
        'root_frame': packet['root_frame'],
        'action_tag_ordinal': packet['action_tag_ordinal'],
        'if_source_offset': source,
        'preceding_record_count': len(preceding),
        'preceding_opcode_classes': classes,
        'preceding_record_offsets': [pos for pos, _ in preceding],
        'comparison_opcode_count': classes.count('comparison'),
        'has_branch_or_opaque_control': any(x in ('branch', 'opaque_control') for x in classes),
        'review_status': 'unverified',
    }


def build_windows(path, packets, width=12):
    if not isinstance(packets, dict) or packets.get('schema') != 'swf-root-if-review-packets-v1':
        raise ValueError('unexpected packet schema')
    raw, data, offset = load_swf(path)
    sha = hashlib.sha256(raw).hexdigest()
    if packets.get('source_swf_sha256') != sha or not HEX64.fullmatch(sha):
        raise ValueError('source SWF fingerprint mismatch')
    if packets.get('verified_story_events') != 0:
        raise ValueError('unverified structural report required')
    selected = packets.get('manual_review_queue')
    if (not isinstance(selected, list) or not selected or len(selected) > 50
            or type(packets.get('manual_review_limit')) is not int
            or len(selected) > packets['manual_review_limit']):
        raise ValueError('invalid review queue')
    by_ordinal = {}
    seen_ids = set()
    for packet in selected:
        if not isinstance(packet, dict):
            raise ValueError('invalid review packet')
        rid, ordinal, action_sha, source = (packet.get(k) for k in
            ('review_id', 'action_tag_ordinal', 'action_sha256', 'if_source_offset'))
        if (not isinstance(rid, str) or not HEX24.fullmatch(rid) or rid in seen_ids
                or type(ordinal) is not int or ordinal < 1
                or not isinstance(action_sha, str) or not HEX64.fullmatch(action_sha)
                or type(source) is not int or source < 0
                or type(packet.get('root_frame')) is not int or packet['root_frame'] < 1
                or packet.get('review_status') != 'unverified'):
            raise ValueError('invalid review packet identity')
        expected = hashlib.sha256(f'{sha}:{ordinal}:{action_sha}:{source}'.encode('ascii')).hexdigest()[:24]
        if rid != expected:
            raise ValueError('review identity does not match SWF coordinates')
        seen_ids.add(rid)
        by_ordinal.setdefault(ordinal, []).append(packet)
    frame, ordinal, observed = 1, 0, {}
    for code, payload in iter_tags(data, offset, len(data)):
        if code == 1:
            frame += 1
        elif code == 12:
            ordinal += 1
            if ordinal not in by_ordinal:
                continue
            action_sha = hashlib.sha256(payload).hexdigest()
            for packet in by_ordinal[ordinal]:
                if packet['root_frame'] != frame or packet['action_sha256'] != action_sha:
                    raise ValueError('action fingerprint/frame mismatch')
                observed[packet['review_id']] = window_for_if(payload, packet, width)
    if len(observed) != len(selected):
        raise ValueError('review IF not found in original SWF')
    return {
        'schema': 'swf-root-if-opcode-windows-v1',
        'source_swf_sha256': sha,
        'selected_if_count': len(selected),
        'window_width': width,
        'entries': [observed[p['review_id']] for p in selected],
        'verified_story_events': 0,
        'interpretation': 'Linear preceding top-level opcode classes only, not a reconstructed IF condition, expression, execution path, story event, or rights evidence. Push operands, identifiers, scripts and media omitted.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('swf', type=Path)
    parser.add_argument('--packets', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--width', type=int, default=12)
    args = parser.parse_args()
    result = build_windows(args.swf, json.loads(args.packets.read_text(encoding='utf-8')), args.width)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Raw-SWF IF opcode windows: {result['selected_if_count']} selected; verified events: 0")


if __name__ == '__main__':
    main()
