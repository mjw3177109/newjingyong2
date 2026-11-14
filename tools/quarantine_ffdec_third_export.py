#!/usr/bin/env python3
"""Quarantine two-export audit candidates contradicted by a third FFDec export.

Only anonymous hashes leave the private runner. This does not verify story events.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

if __package__:
    from .compare_ffdec_exports import _index
else:
    from compare_ffdec_exports import _index

HEX64 = re.compile(r'^[0-9a-f]{64}$')


def quarantine(stable_report, third_index):
    if not isinstance(stable_report, dict) or stable_report.get('schema_version') != 1:
        raise ValueError('invalid two-export audit report')
    if stable_report.get('scope') != 'two_exports_same_ci_run_only':
        raise ValueError('invalid two-export audit scope')
    swf, paths_c, manifest_c = _index(third_index)
    if stable_report.get('source_swf_sha256') != swf:
        raise ValueError('third export uses different source SWF')
    rows = stable_report.get('stable_candidates')
    if (not isinstance(rows, list) or type(stable_report.get('stable_candidate_count')) is not int
            or stable_report['stable_candidate_count'] != len(rows)):
        raise ValueError('invalid stable candidate count')
    seen = set()
    canonical = []
    retained, quarantined = [], []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
                'path_sha256', 'content_sha256', 'candidate_id',
                'literal_jump_count', 'direct_guard_count', 'evidence_status'}:
            raise ValueError('invalid candidate fields')
        path, content = row['path_sha256'], row['content_sha256']
        if (not isinstance(path, str) or not HEX64.fullmatch(path)
                or not isinstance(content, str) or not HEX64.fullmatch(content)
                or path in seen or row['evidence_status'] != 'reproducible_syntax_unverified'
                or type(row['literal_jump_count']) is not int or row['literal_jump_count'] < 0
                or type(row['direct_guard_count']) is not int or row['direct_guard_count'] < 0
                or row['direct_guard_count'] > row['literal_jump_count']
                or not isinstance(row['candidate_id'], str)
                or row['candidate_id'] != 'SRC-' + hashlib.sha256(
                    f'{swf}:{path}:{content}'.encode('ascii')).hexdigest()[:20]):
            raise ValueError('invalid or duplicate stable candidate')
        seen.add(path)
        canonical.append(f"{path}:{content}:{row['literal_jump_count']}:{row['direct_guard_count']}")
        if path not in paths_c:
            quarantined.append({'path_sha256': path, 'reason': 'missing_in_third_export'})
        elif paths_c[path] != content:
            quarantined.append({'path_sha256': path, 'reason': 'content_changed_in_third_export'})
        else:
            retained.append({'path_sha256': path, 'content_sha256': content,
                             'candidate_id': row['candidate_id'],
                             'evidence_status': 'three_export_content_agreement_unverified'})
    expected = hashlib.sha256('\n'.join(canonical).encode('ascii')).hexdigest()
    if stable_report.get('stable_manifest_sha256') != expected:
        raise ValueError('two-export stable manifest fingerprint mismatch')
    return {
        'schema_version': 1,
        'source_swf_sha256': swf,
        'scope': 'three_exports_same_ci_run_content_only',
        'third_export_manifest_sha256': manifest_c,
        'two_export_candidate_count': len(rows),
        'retained_candidate_count': len(retained),
        'quarantined_candidate_count': len(quarantined),
        'retained_candidates': retained,
        'quarantined_candidates': quarantined,
        'verified_story_event_count': 0,
        'warning': 'Three matching content hashes are not a canonical FFDec export, cross-run stability, semantic verification, or publication rights.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stable-set', type=Path, required=True)
    parser.add_argument('--index-c', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = quarantine(json.loads(args.stable_set.read_text(encoding='utf-8')),
                        json.loads(args.index_c.read_text(encoding='utf-8')))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Third-export content agreement:', result['retained_candidate_count'],
          'quarantined:', result['quarantined_candidate_count'],
          'verified story events:', result['verified_story_event_count'])


if __name__ == '__main__':
    main()
