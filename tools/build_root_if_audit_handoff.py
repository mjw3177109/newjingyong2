#!/usr/bin/env python3
"""Create a source-free, fail-closed human audit handoff for root IF candidates.

This tool cannot verify story semantics. It never reads FFDec source or assets.
The private reviewer must examine the actual script and runtime separately.
"""
import argparse
import json
import re
from pathlib import Path

HEX64 = re.compile(r'^[0-9a-f]{64}$')
HEX24 = re.compile(r'^[0-9a-f]{24}$')


def _positive(value):
    return type(value) is int and value > 0


def _offset(value):
    return type(value) is int and value >= 0


def build_handoff(report):
    if not isinstance(report, dict) or report.get('schema') != 'swf-root-if-review-packets-v1':
        raise ValueError('unexpected review packet schema')
    swf = report.get('source_swf_sha256')
    if not isinstance(swf, str) or not HEX64.fullmatch(swf):
        raise ValueError('invalid source SWF fingerprint')
    if report.get('verified_story_events') != 0:
        raise ValueError('structural packets cannot claim verified story events')
    rows = report.get('manual_review_queue')
    if not isinstance(rows, list) or not rows or not _positive(report.get('manual_review_limit')):
        raise ValueError('invalid manual review queue')
    if len(rows) > report['manual_review_limit'] or not _positive(report.get('total_if_review_packets')):
        raise ValueError('invalid review packet totals')
    if len(rows) > report['total_if_review_packets'] or not _positive(report.get('selected_action_tags')):
        raise ValueError('invalid action tag totals')

    seen = set()
    output = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('invalid review row')
        rid, action = row.get('review_id'), row.get('action_sha256')
        if (not isinstance(rid, str) or not HEX24.fullmatch(rid) or rid in seen
                or not isinstance(action, str) or not HEX64.fullmatch(action)):
            raise ValueError('invalid or duplicate review identity')
        seen.add(rid)
        if (not _positive(row.get('root_frame')) or not _positive(row.get('action_tag_ordinal'))
                or not _offset(row.get('if_source_offset'))
                or not _offset(row.get('branch_target_offset'))
                or not _offset(row.get('fallthrough_offset'))
                or type(row.get('if_record_reachable')) is not bool
                or type(row.get('same_frame_sprite_transition')) is not bool
                or not _offset(row.get('structural_priority'))):
            raise ValueError('invalid source coordinates')
        if (row.get('review_status') != 'unverified'
                or any(row.get(key) is not None for key in
                       ('trigger', 'effects', 'map_id', 'html5_event_id'))):
            raise ValueError('unreviewed structural packet contains semantic claims')
        hints = row.get('nearby_access_hints')
        if not isinstance(hints, list) or len(hints) > 8:
            raise ValueError('invalid access hint collection')
        for hint in hints:
            if (not isinstance(hint, dict) or not _offset(hint.get('offset'))
                    or hint['offset'] >= row['if_source_offset']
                    or not _positive(hint.get('records_before_if'))
                    or hint['records_before_if'] > 8
                    or hint.get('opcode') not in {
                        'get_variable', 'set_variable', 'get_member', 'set_member',
                        'get_property', 'set_property', 'define_local',
                        'define_local2', 'store_register'}):
                raise ValueError('invalid source-free access hint')
        output.append({
            'review_id': rid,
            'source_location': {'root_frame': row['root_frame'],
                                'action_tag_ordinal': row['action_tag_ordinal'],
                                'action_sha256': action,
                                'if_source_offset': row['if_source_offset'],
                                'branch_target_offset': row['branch_target_offset'],
                                'fallthrough_offset': row['fallthrough_offset']},
            'checks': {
                'ffdec_script_sha256': None,
                'condition_confirmed': False,
                'state_effects_confirmed': False,
                'map_context_confirmed': False,
                'runtime_reproduced': False,
                'independent_reviewed': False,
                'adaptation_rights_confirmed': False,
            },
            'review_status': 'unverified',
            'html5_event_id': None,
        })
    return {
        'schema': 'swf-root-if-audit-handoff-v1',
        'source_swf_sha256': swf,
        'candidate_count': len(output),
        'verified_story_events': 0,
        'ready_for_html5_mapping': 0,
        'entries': output,
        'warning': 'This is an empty private-review checklist, not FFDec semantic evidence. All checks must be performed against original source and runtime before any event is mapped.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packets', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build_handoff(json.loads(args.packets.read_text(encoding='utf-8')))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Source-free IF audit handoff:', result['candidate_count'],
          'candidates, verified story events: 0')


if __name__ == '__main__':
    main()
