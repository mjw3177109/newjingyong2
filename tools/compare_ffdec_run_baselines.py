#!/usr/bin/env python3
"""Compare source-free FFDec indexes from separate CI runs.

This identifies cross-run drift in anonymous scripts, not a canonical export,
root cause, or verified story event. Never reads decompiled source or assets.
"""
import argparse
import json
from pathlib import Path

if __package__:
    from .compare_ffdec_exports import _index
else:
    from compare_ffdec_exports import _index


def compare_baselines(index_a, index_b, limit=20):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Invalid example limit')
    swf_a, paths_a, manifest_a = _index(index_a)
    swf_b, paths_b, manifest_b = _index(index_b)
    if swf_a != swf_b:
        raise ValueError('Cannot compare different source SWF fingerprints')
    common = paths_a.keys() & paths_b.keys()
    changed = sorted(path for path in common if paths_a[path] != paths_b[path])
    only_a = sorted(paths_a.keys() - paths_b.keys())
    only_b = sorted(paths_b.keys() - paths_a.keys())
    # Anonymous paths only. No FFDec source, original path or original strings.
    examples = [{'path_sha256': path, 'difference_kind': 'content'} for path in changed[:limit]]
    examples += [{'path_sha256': path, 'difference_kind': 'only_a'} for path in only_a[:max(0, limit - len(examples))]]
    examples += [{'path_sha256': path, 'difference_kind': 'only_b'} for path in only_b[:max(0, limit - len(examples))]]
    total = len(changed) + len(only_a) + len(only_b)
    return {
        'schema_version': 1,
        'source_swf_sha256': swf_a,
        'comparison_scope': 'two_independent_ci_run_indexes',
        'comparison_status': 'matching_indexes' if not total else 'divergent_indexes',
        'manifest_sha256': {'a': manifest_a, 'b': manifest_b},
        'script_counts': {'a': len(paths_a), 'b': len(paths_b)},
        'common_path_count': len(common),
        'common_paths_with_changed_content': len(changed),
        'paths_only_a': len(only_a),
        'paths_only_b': len(only_b),
        'changed_path_examples': examples,
        'examples_truncated': total > len(examples),
        'verified_story_event_count': 0,
        'warning': ('Cross-run index equality is not proof of deterministic FFDec, '
                    'script semantic correctness, or any recovered story event. '
                    'Different source revisions or tool versions may affect results. '
                    'No original paths, scripts or media are included.'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index-a', type=Path, required=True)
    parser.add_argument('--index-b', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    report = compare_baselines(
        json.loads(args.index_a.read_text(encoding='utf-8')),
        json.loads(args.index_b.read_text(encoding='utf-8')),
        limit=args.limit,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Cross-run FFDec index comparison:', report['comparison_status'],
          'changed common scripts:', report['common_paths_with_changed_content'],
          'verified story events:', report['verified_story_event_count'])


if __name__ == '__main__':
    main()
