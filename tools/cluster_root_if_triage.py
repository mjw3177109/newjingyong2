#!/usr/bin/env python3
"""Source-free grouping of IFs by action and repeated byte-offset stride.

These patterns are navigation hints, never evidence of story semantics.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

HEX24 = re.compile(r'^[0-9a-f]{24}$')
HEX64 = re.compile(r'^[0-9a-f]{64}$')


def checked_int(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('invalid structural coordinate or count')
    return value


def cluster_triage(report):
    if not isinstance(report, dict) or report.get('schema') != 'swf-root-if-handoff-window-crosscheck-v1':
        raise ValueError('invalid crosscheck schema')
    sha = report.get('source_swf_sha256')
    if not isinstance(sha, str) or not HEX64.fullmatch(sha):
        raise ValueError('invalid SWF fingerprint')
    if report.get('verified_story_events') != 0 or report.get('ready_for_html5_mapping') != 0:
        raise ValueError('semantic claims are forbidden')
    entries, triage = report.get('entries'), report.get('structural_review_triage')
    if not isinstance(entries, list) or not entries or not isinstance(triage, dict):
        raise ValueError('missing IF review data')
    if checked_int(report.get('matched_candidate_count')) != len(entries):
        raise ValueError('candidate count mismatch')
    order = triage.get('review_order')
    if not isinstance(order, list) or len(order) != len(entries) or checked_int(triage.get('review_target_count')) != len(entries):
        raise ValueError('triage count mismatch')
    grouped, seen_ids, seen_locations = defaultdict(list), set(), set()
    for row in entries:
        if not isinstance(row, dict) or row.get('review_status') != 'unverified':
            raise ValueError('invalid IF row')
        rid = row.get('review_id')
        if not isinstance(rid, str) or not HEX24.fullmatch(rid) or rid in seen_ids:
            raise ValueError('invalid or duplicate review ID')
        frame = checked_int(row.get('root_frame'), 1)
        action = checked_int(row.get('action_tag_ordinal'), 1)
        offset = checked_int(row.get('if_source_offset'))
        if (frame, action, offset) in seen_locations:
            raise ValueError('duplicate IF source location')
        seen_ids.add(rid)
        seen_locations.add((frame, action, offset))
        grouped[(frame, action)].append((offset, rid))
    order_ids = []
    for rank, row in enumerate(order, 1):
        if not isinstance(row, dict) or row.get('review_status') != 'unverified' or row.get('rank') != rank:
            raise ValueError('invalid review order')
        rid = row.get('review_id')
        if rid not in seen_ids or rid in order_ids:
            raise ValueError('triage review ID mismatch')
        order_ids.append(rid)
    if set(order_ids) != seen_ids:
        raise ValueError('incomplete review order')
    groups, runs = [], []
    for (frame, action), members in sorted(grouped.items()):
        members.sort()
        groups.append({
            'root_frame': frame, 'action_tag_ordinal': action,
            'candidate_count': len(members),
            'first_if_source_offset': members[0][0],
            'last_if_source_offset': members[-1][0],
            'review_ids': [rid for _, rid in members],
            'review_status': 'unverified',
        })
        i = 0
        while i + 2 < len(members):
            stride = members[i + 1][0] - members[i][0]
            j = i + 2
            while j < len(members) and members[j][0] - members[j - 1][0] == stride:
                j += 1
            if j - i >= 3:
                segment = members[i:j]
                runs.append({
                    'root_frame': frame, 'action_tag_ordinal': action,
                    'if_offset_stride': stride, 'candidate_count': len(segment),
                    'first_if_source_offset': segment[0][0],
                    'last_if_source_offset': segment[-1][0],
                    'review_ids': [rid for _, rid in segment],
                    'review_status': 'unverified',
                })
                i = j - 1
            else:
                i += 1
    return {
        'schema': 'swf-root-if-structural-clusters-v1',
        'source_swf_sha256': sha,
        'candidate_count': len(entries), 'action_group_count': len(groups),
        'action_groups': groups, 'repeated_stride_run_count': len(runs),
        'repeated_stride_runs': runs,
        'verified_story_events': 0, 'ready_for_html5_mapping': 0,
        'warning': 'Same action and repeated IF byte-offset stride are navigation hints only; no shared predicate, story event, runtime effect, map or rights are verified.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--crosscheck', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = cluster_triage(json.loads(args.crosscheck.read_text(encoding='utf-8')))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('IFs:', result['candidate_count'], 'action groups:', result['action_group_count'],
          'stride runs:', result['repeated_stride_run_count'], 'verified story events: 0')


if __name__ == '__main__':
    main()
