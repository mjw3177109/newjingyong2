#!/usr/bin/env python3
"""Compare independent FFDec exports without publishing protected script content.

Uses the source-free index, review queue and frame-jump evidence JSONs.
This tests reproducibility, NOT semantic correctness of story events.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

HEX64 = re.compile(r'^[0-9a-f]{64}$')


def _sha(value):
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise ValueError('Invalid SHA-256')
    return value


def _count(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError('Invalid count')
    return value


def _index(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Expected index schema v1')
    swf = _sha(data.get('source_swf_sha256'))
    rows = data.get('entries')
    if not isinstance(rows, list) or _count(data.get('script_file_count')) != len(rows):
        raise ValueError('Index count mismatch')
    paths = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid index row')
        path, content = _sha(row.get('path_sha256')), _sha(row.get('content_sha256'))
        if path in paths:
            raise ValueError('Duplicate indexed path')
        paths[path] = content
    canonical = '\n'.join(f'{p}:{paths[p]}' for p in sorted(paths)).encode('ascii')
    return swf, paths, hashlib.sha256(canonical).hexdigest()


def _queue(data, swf, indexed):
    if not isinstance(data, dict) or data.get('schema_version') != 1 or data.get('source_swf_sha256') != swf:
        raise ValueError('Queue SWF/schema mismatch')
    if _count(data.get('indexed_script_count')) != len(indexed):
        raise ValueError('Queue index count mismatch')
    rows = data.get('candidates')
    if not isinstance(rows, list) or _count(data.get('selected_count')) != len(rows):
        raise ValueError('Queue selected count mismatch')
    selected = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid queue row')
        path, content = _sha(row.get('path_sha256')), _sha(row.get('content_sha256'))
        if path in selected or indexed.get(path) != content:
            raise ValueError('Queue candidate not in indexed export')
        cid = 'SRC-' + hashlib.sha256(f'{swf}:{path}:{content}'.encode('ascii')).hexdigest()[:20]
        if row.get('candidate_id') != cid or row.get('semantic_status') != 'unverified':
            raise ValueError('Invalid queue candidate identity')
        selected[path] = cid
    return selected


def _jumps(data, swf, indexed, selected):
    if not isinstance(data, dict) or data.get('schema_version') != 1 or data.get('source_swf_sha256') != swf:
        raise ValueError('Frame-jump SWF/schema mismatch')
    if _count(data.get('indexed_script_count')) != len(indexed) or _count(data.get('candidate_count')) != len(selected):
        raise ValueError('Frame-jump count mismatch')
    if data.get('verified_story_event_count') != 0:
        raise ValueError('Syntax report cannot verify story events')
    rows = data.get('entries')
    if not isinstance(rows, list) or len(rows) != len(selected):
        raise ValueError('Frame-jump entries mismatch')
    entries = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid frame-jump entry')
        path, content = _sha(row.get('path_sha256')), _sha(row.get('content_sha256'))
        if path in entries or indexed.get(path) != content or selected.get(path) != row.get('candidate_id'):
            raise ValueError('Frame-jump candidate identity mismatch')
        count, guards = _count(row.get('literal_jump_count')), _count(row.get('direct_guard_count'))
        if guards > count:
            raise ValueError('Guard count exceeds jump count')
        entries[path] = (count, guards)
    jumps, guards = sum(x[0] for x in entries.values()), sum(x[1] for x in entries.values())
    if _count(data.get('literal_jump_count')) != jumps or _count(data.get('direct_guard_count')) != guards:
        raise ValueError('Frame-jump total mismatch')
    return entries, jumps, guards


def compare_runs(index_a, index_b, queue_a, queue_b, jumps_a, jumps_b):
    swf_a, paths_a, digest_a = _index(index_a)
    swf_b, paths_b, digest_b = _index(index_b)
    if swf_a != swf_b:
        raise ValueError('Cannot compare different source SWF fingerprints')
    selected_a, selected_b = _queue(queue_a, swf_a, paths_a), _queue(queue_b, swf_b, paths_b)
    entry_a, count_a, guard_a = _jumps(jumps_a, swf_a, paths_a, selected_a)
    entry_b, count_b, guard_b = _jumps(jumps_b, swf_b, paths_b, selected_b)
    common = paths_a.keys() & paths_b.keys()
    selected_common = selected_a.keys() & selected_b.keys()
    stable = paths_a == paths_b and selected_a == selected_b and entry_a == entry_b
    return {
        'schema_version': 1,
        'source_swf_sha256': swf_a,
        'comparison_status': 'stable' if stable else 'divergent',
        'export_a': {'indexed_scripts': len(paths_a), 'manifest_sha256': digest_a,
                     'selected_candidates': len(selected_a), 'literal_jumps': count_a, 'simple_guards': guard_a},
        'export_b': {'indexed_scripts': len(paths_b), 'manifest_sha256': digest_b,
                     'selected_candidates': len(selected_b), 'literal_jumps': count_b, 'simple_guards': guard_b},
        'difference': {
            'paths_only_a': len(paths_a.keys() - paths_b.keys()),
            'paths_only_b': len(paths_b.keys() - paths_a.keys()),
            'common_paths_with_changed_content': sum(paths_a[p] != paths_b[p] for p in common),
            'changed_content_path_hashes': sorted(p for p in common if paths_a[p] != paths_b[p])[:20],
            'changed_content_hashes_truncated': sum(paths_a[p] != paths_b[p] for p in common) > 20,
            'selected_only_a': len(selected_a.keys() - selected_b.keys()),
            'selected_only_b': len(selected_b.keys() - selected_a.keys()),
            'common_candidates_with_changed_jump_counts': sum(entry_a[p][0] != entry_b[p][0] for p in selected_common),
            'common_candidates_with_changed_guard_counts': sum(entry_a[p][1] != entry_b[p][1] for p in selected_common),
        },
        'verified_story_event_count': 0,
        'warning': 'Stable means two exports in the same CI environment match; no original story, map, combat or event semantics are verified. No raw paths or source are published.',
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    names = ('index-a', 'index-b', 'queue-a', 'queue-b', 'jumps-a', 'jumps-b')
    for name in names:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    values = [json.loads(getattr(args, name.replace('-', '_')).read_text(encoding='utf-8')) for name in names]
    report = compare_runs(*values)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('FFDec independent-export comparison:', report['comparison_status'])
    print('Content-changed scripts:', report['difference']['common_paths_with_changed_content'])
    print('Candidate jump count differences:', report['difference']['common_candidates_with_changed_jump_counts'])
    print('Candidate guard count differences:', report['difference']['common_candidates_with_changed_guard_counts'])
    print('Candidate membership only A/B:', report['difference']['selected_only_a'], '/', report['difference']['selected_only_b'])
    print('Path membership only A/B:', report['difference']['paths_only_a'], '/', report['difference']['paths_only_b'])


if __name__ == '__main__':
    main()
