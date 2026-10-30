#!/usr/bin/env python3
"""Select only reproducible, source-free syntax candidates from two FFDec exports.

This is a two-export consistency filter, not a plot/event verification step.
No decompiled source, original path or protected media is emitted.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from tools.compare_ffdec_exports import _index, _jumps, _queue


def build_stable_set(index_a, index_b, queue_a, queue_b, jumps_a, jumps_b):
    swf_a, paths_a, digest_a = _index(index_a)
    swf_b, paths_b, digest_b = _index(index_b)
    if swf_a != swf_b:
        raise ValueError('Cannot compare different source SWF fingerprints')
    selected_a = _queue(queue_a, swf_a, paths_a)
    selected_b = _queue(queue_b, swf_b, paths_b)
    syntax_a, _, _ = _jumps(jumps_a, swf_a, paths_a, selected_a)
    syntax_b, _, _ = _jumps(jumps_b, swf_b, paths_b, selected_b)

    stable, excluded, reasons = [], [], Counter()
    for path in sorted(set(selected_a) | set(selected_b)):
        if path not in selected_a or path not in selected_b:
            reason = 'selected_in_one_export_only'
        elif paths_a[path] != paths_b[path]:
            reason = 'script_content_changed'
        elif syntax_a[path] != syntax_b[path]:
            reason = 'syntax_counts_changed'
        else:
            stable.append({
                'path_sha256': path,
                'content_sha256': paths_a[path],
                'candidate_id': selected_a[path],
                'literal_jump_count': syntax_a[path][0],
                'direct_guard_count': syntax_a[path][1],
                'evidence_status': 'reproducible_syntax_unverified',
            })
            continue
        reasons[reason] += 1
        excluded.append({'path_sha256': path, 'reason': reason})

    canonical = '\n'.join(
        f"{r['path_sha256']}:{r['content_sha256']}:{r['literal_jump_count']}:{r['direct_guard_count']}"
        for r in stable
    ).encode('ascii')
    return {
        'schema_version': 1,
        'source_swf_sha256': swf_a,
        'scope': 'two_exports_same_ci_run_only',
        'export_manifest_sha256': {'a': digest_a, 'b': digest_b},
        'selected_count': {'a': len(selected_a), 'b': len(selected_b)},
        'stable_candidate_count': len(stable),
        'excluded_candidate_count': len(excluded),
        'exclusion_reason_counts': dict(sorted(reasons.items())),
        'stable_literal_jump_count': sum(r['literal_jump_count'] for r in stable),
        'stable_direct_guard_count': sum(r['direct_guard_count'] for r in stable),
        'stable_manifest_sha256': hashlib.sha256(canonical).hexdigest(),
        'stable_candidates': stable,
        'excluded_candidates': excluded,
        'verified_story_event_count': 0,
        'warning': 'Only two-export syntax agreement, not cross-run stability or story semantics. No original events, maps, combat values or narrative conditions have been verified.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    names = ('index-a', 'index-b', 'queue-a', 'queue-b', 'jumps-a', 'jumps-b')
    for name in names:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    values = [json.loads(getattr(args, name.replace('-', '_')).read_text(encoding='utf-8')) for name in names]
    report = build_stable_set(*values)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Reproducible syntax candidates:', report['stable_candidate_count'],
          'excluded:', report['excluded_candidate_count'],
          'stable literal jumps:', report['stable_literal_jump_count'],
          'verified story events:', report['verified_story_event_count'])


if __name__ == '__main__':
    main()
