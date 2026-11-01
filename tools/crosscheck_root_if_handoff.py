#!/usr/bin/env python3
"""Cross-check source-free root IF handoff and raw-SWF opcode windows.

Structural consistency only. Never imports decompiled scripts, operands, art or audio.
"""
import argparse
import json
import re
from pathlib import Path

HEX64 = re.compile(r'^[0-9a-f]{64}$')
HEX24 = re.compile(r'^[0-9a-f]{24}$')


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
        if (row.get('review_status') != 'unverified' or row.get('html5_event_id') is not None
                or not isinstance(location, dict)):
            raise ValueError('handoff contains semantic claims')
        checks = row.get('checks')
        if (not isinstance(checks, dict) or checks.get('ffdec_script_sha256') is not None
                or any(value is not False for key, value in checks.items() if key != 'ffdec_script_sha256')):
            raise ValueError('handoff contains private attestations')
        window = by_id[rid]
        for key in ('root_frame', 'action_tag_ordinal', 'if_source_offset'):
            if (type(location.get(key)) is not int or location[key] < (1 if key != 'if_source_offset' else 0)
                    or window.get(key) != location[key]):
                raise ValueError('raw SWF window/source coordinate mismatch')
        classes = window.get('straight_line_preceding_opcode_classes')
        if (not isinstance(classes, list) or len(classes) != _count(window.get('straight_line_preceding_record_count'))
                or any(not isinstance(value, str) for value in classes)):
            raise ValueError('invalid bounded opcode classes')
        incoming = _count(window.get('if_incoming_reachable_syntactic_source_count'))
        multiple = window.get('if_has_multiple_reachable_syntactic_predecessors')
        if type(multiple) is not bool or multiple != (incoming > 1):
            raise ValueError('inconsistent syntactic predecessor count')
        output.append({
            'review_id': rid,
            'root_frame': location['root_frame'],
            'action_tag_ordinal': location['action_tag_ordinal'],
            'if_source_offset': location['if_source_offset'],
            'bounded_comparison_opcode_present': 'comparison' in classes,
            'reachable_syntactic_predecessor_count': incoming,
            'multiple_reachable_syntactic_predecessors': multiple,
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
