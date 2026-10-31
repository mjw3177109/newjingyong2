#!/usr/bin/env python3
"""Build source-free per-IF review packets from upstream SWF evidence reports.

All inputs are generated against the original SWF by the CI pipeline.
This script never reads ActionScript text, identifiers, media, or operands.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMAS = {
    'queue': 'swf-root-conditional-review-queue-v1',
    'edges': 'swf-root-conditional-edges-v1',
    'access': 'swf-root-state-access-hints-v1',
    'cfg': 'swf-root-local-control-flow-v1',
}
ACCESS_NAMES = {
    'get_variable', 'set_variable', 'get_member', 'set_member',
    'get_property', 'set_property', 'define_local', 'define_local2',
    'store_register',
}


def _integer(value, minimum=0):
    return type(value) is int and value >= minimum


def build_packets(queue, edges, access, cfg, limit=12):
    sources = {'queue': queue, 'edges': edges, 'access': access, 'cfg': cfg}
    sha = queue.get('source_swf_sha256')
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha):
        raise ValueError('invalid SWF fingerprint')
    if not _integer(limit, 1) or limit > 50:
        raise ValueError('invalid review limit')
    candidates = queue.get('candidates')
    if (not isinstance(candidates, list) or len(candidates) > 100
            or len(candidates) != queue.get('selected_candidate_count')):
        raise ValueError('invalid queue size')
    for name, report in sources.items():
        if (report.get('schema') != SCHEMAS[name]
                or report.get('source_swf_sha256') != sha
                or report.get('verified_story_events') != 0):
            raise ValueError('schema, fingerprint or status mismatch: ' + name)
        if name != 'queue' and (not isinstance(report.get('candidates'), list)
                or report.get('selected_action_tags') != len(candidates)
                or len(report['candidates']) != len(candidates)):
            raise ValueError('candidate count mismatch: ' + name)

    packets, seen_tags, seen_ids = [], set(), set()
    for i, candidate in enumerate(candidates):
        erow, arow, crow = (sources[k]['candidates'][i] for k in ('edges', 'access', 'cfg'))
        ordinal, frame, action_sha = (candidate.get(k) for k in
                                      ('action_tag_ordinal', 'root_frame', 'action_sha256'))
        if (not _integer(ordinal, 1) or ordinal in seen_tags or not _integer(frame, 1)
                or not isinstance(action_sha, str)
                or not re.fullmatch(r'[0-9a-f]{64}', action_sha)
                or type(candidate.get('same_frame_sprite_transition')) is not bool
                or candidate.get('review_status') != 'unverified'):
            raise ValueError('invalid queue candidate')
        seen_tags.add(ordinal)
        for row in (erow, arow, crow):
            if (row.get('action_tag_ordinal') != ordinal or row.get('root_frame') != frame
                    or row.get('action_sha256') != action_sha
                    or row.get('review_status') != 'unverified'):
                raise ValueError('unaligned evidence row')
        if (not isinstance(erow.get('edges'), list)
                or not isinstance(arow.get('if_preceding_access_hints'), list)
                or not isinstance(crow.get('if_successors'), list)):
            raise ValueError('missing branch evidence')
        if any(e.get('opcode') not in ('if', 'jump') or
               e.get('target_alignment') != 'record_boundary' or
               not _integer(e.get('source_offset')) or
               not _integer(e.get('target_offset')) for e in erow['edges']):
            raise ValueError('invalid branch edge')
        if_edges = [e for e in erow['edges'] if e['opcode'] == 'if']
        jump_edges = [e for e in erow['edges'] if e['opcode'] == 'jump']
        if (len(if_edges) != candidate.get('conditional_opcode_count')
                or len(jump_edges) != candidate.get('jump_opcode_count')
                or len(if_edges) != crow.get('conditional_count')
                or len(jump_edges) != crow.get('jump_count')
                or len(if_edges) != len(crow['if_successors'])
                or len(if_edges) != len(arow['if_preceding_access_hints'])):
            raise ValueError('IF/Jump count mismatch')
        seen_offsets = set()
        for edge, successor, hint in zip(if_edges, crow['if_successors'],
                                          arow['if_preceding_access_hints']):
            source, target = edge['source_offset'], edge['target_offset']
            fallthrough = successor.get('fallthrough_offset')
            if (source in seen_offsets or not _integer(fallthrough)
                    or successor.get('if_source_offset') != source
                    or successor.get('branch_target_offset') != target
                    or successor.get('branch_and_fallthrough_distinct') != (target != fallthrough)
                    or type(successor.get('if_record_reachable')) is not bool
                    or hint.get('if_source_offset') != source):
                raise ValueError('branch/CFG alignment mismatch')
            seen_offsets.add(source)
            nearby = hint.get('prior_eight_records_access_hints')
            if not isinstance(nearby, list) or len(nearby) > 8:
                raise ValueError('invalid access hints')
            sanitized = []
            for item in nearby:
                if (not isinstance(item, dict) or not _integer(item.get('offset'))
                        or item['offset'] >= source
                        or not _integer(item.get('records_before_if'), 1)
                        or item['records_before_if'] > 8
                        or item.get('opcode') not in ACCESS_NAMES):
                    raise ValueError('invalid access hint')
                sanitized.append({'offset': item['offset'], 'opcode': item['opcode'],
                                  'records_before_if': item['records_before_if']})
            identity = f'{sha}:{ordinal}:{action_sha}:{source}'
            packet_id = hashlib.sha256(identity.encode('ascii')).hexdigest()[:24]
            if packet_id in seen_ids:
                raise ValueError('duplicate review packet')
            seen_ids.add(packet_id)
            priority = (4 if candidate['same_frame_sprite_transition'] else 0)
            priority += (2 if sanitized else 0) + (1 if target != fallthrough else 0)
            packets.append({
                'review_id': packet_id, 'root_frame': frame,
                'action_tag_ordinal': ordinal, 'action_sha256': action_sha,
                'if_source_offset': source, 'branch_target_offset': target,
                'fallthrough_offset': fallthrough,
                'if_record_reachable': successor['if_record_reachable'],
                'same_frame_sprite_transition': candidate['same_frame_sprite_transition'],
                'nearby_access_hints': sanitized, 'structural_priority': priority,
                'review_status': 'unverified', 'trigger': None, 'effects': None,
                'map_id': None, 'html5_event_id': None,
            })
    if (len(packets) != edges.get('if_edges')
            or sum(len(r['edges']) for r in edges['candidates']) != edges.get('total_branch_edges')):
        raise ValueError('aggregate branch count mismatch')
    ordered = sorted(packets, key=lambda r: (-r['structural_priority'],
                    r['root_frame'], r['action_tag_ordinal'], r['if_source_offset']))
    return {
        'schema': 'swf-root-if-review-packets-v1', 'source_swf_sha256': sha,
        'selected_action_tags': len(candidates), 'total_if_review_packets': len(packets),
        'manual_review_limit': limit, 'manual_review_queue': ordered[:limit],
        'verified_story_events': 0,
        'interpretation': 'Structural review targets only. Null semantics are intentional; no original story, map, runtime behavior or rights verified.',
    }


def main():
    parser = argparse.ArgumentParser()
    for name in SCHEMAS:
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--limit', type=int, default=12)
    args = parser.parse_args()
    reports = [json.loads(Path(getattr(args, name)).read_text(encoding='utf-8'))
               for name in SCHEMAS]
    result = build_packets(*reports, limit=args.limit)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Root IF review: {result['total_if_review_packets']} structural IFs, "
          f"{len(result['manual_review_queue'])} prioritized, verified events: 0")


if __name__ == '__main__':
    main()
