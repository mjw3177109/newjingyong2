#!/usr/bin/env python3
"""Diagnose two ephemeral FFDec exports without emitting paths or source bytes.

All exported script contents stay in the CI scratch directory. The JSON only
contains SHA-256 identifiers, lengths, line counts and difference locations.
No diagnosis here establishes a story event or semantic equivalence.
"""
import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from .compare_ffdec_exports import _index
else:
    from compare_ffdec_exports import _index


def sha(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root, indexed):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Invalid export directory')
    blobs = {}
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in export tree')
        if not path.is_file():
            continue
        key = sha(path.relative_to(root).as_posix().encode('utf-8'))
        if key in blobs or key not in indexed:
            raise ValueError('Export path not in validated index')
        data = path.read_bytes()
        if sha(data) != indexed[key]:
            raise ValueError('Export bytes do not match validated index')
        blobs[key] = data
    if set(blobs) != set(indexed):
        raise ValueError('Export files missing from validated index')
    return blobs


def first_difference(a, b):
    offset = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return a[:offset].count(b'\n') + 1, b[:offset].count(b'\n') + 1


def category(a, b):
    # A strict byte prefix is a useful truncation clue, not proof of truncation.
    if len(a) < len(b) and b.startswith(a):
        return 'a_exact_prefix_of_b'
    if len(b) < len(a) and a.startswith(b):
        return 'b_exact_prefix_of_a'
    if a.replace(b'\r\n', b'\n') == b.replace(b'\r\n', b'\n'):
        return 'line_endings_only'
    if b''.join(a.split()) == b''.join(b.split()):
        return 'whitespace_normalized_equal'
    return 'other_content_difference'


def diagnose(root_a, root_b, index_a, index_b, limit=20):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Invalid diagnostic sample limit')
    swf_a, paths_a, digest_a = _index(index_a)
    swf_b, paths_b, digest_b = _index(index_b)
    if swf_a != swf_b:
        raise ValueError('Cannot compare different source SWF fingerprints')
    blobs_a = snapshot(root_a, paths_a)
    blobs_b = snapshot(root_b, paths_b)
    changed = sorted(k for k in paths_a.keys() & paths_b.keys()
                     if paths_a[k] != paths_b[k])
    examples = []
    for key in changed[:limit]:
        a, b = blobs_a[key], blobs_b[key]
        line_a, line_b = first_difference(a, b)
        common_prefix = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                             min(len(a), len(b)))
        examples.append({
            'path_sha256': key,
            'bytes_a': len(a), 'bytes_b': len(b),
            'lines_a': len(a.splitlines()), 'lines_b': len(b.splitlines()),
            'first_different_line_a': line_a, 'first_different_line_b': line_b,
            'common_prefix_bytes': common_prefix,
            'difference_class': category(a, b),
        })
    return {
        'schema_version': 1,
        'source_swf_sha256': swf_a,
        'comparison_status': 'stable' if paths_a == paths_b else 'divergent',
        'manifest_sha256': {'a': digest_a, 'b': digest_b},
        'paths_only_a': len(paths_a.keys() - paths_b.keys()),
        'paths_only_b': len(paths_b.keys() - paths_a.keys()),
        'changed_content_path_count': len(changed),
        'changed_examples': examples,
        'examples_truncated': len(changed) > limit,
        'verified_story_event_count': 0,
        'warning': ('Anonymous byte-level diagnostics only. Similar bytes do not '
                    'verify plot, maps, combat values or original event semantics.'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scripts-a', type=Path, required=True)
    parser.add_argument('--scripts-b', type=Path, required=True)
    parser.add_argument('--index-a', type=Path, required=True)
    parser.add_argument('--index-b', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    index_a = json.loads(args.index_a.read_text(encoding='utf-8'))
    index_b = json.loads(args.index_b.read_text(encoding='utf-8'))
    report = diagnose(args.scripts_a, args.scripts_b, index_a, index_b, args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                        encoding='utf-8')
    print('FFDec byte-level diagnostic:', report['comparison_status'],
          'changed content paths:', report['changed_content_path_count'],
          'diagnostic examples:', len(report['changed_examples']))


if __name__ == '__main__':
    main()
