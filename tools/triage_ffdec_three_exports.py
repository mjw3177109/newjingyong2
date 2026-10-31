#!/usr/bin/env python3
"""Triage three ephemeral FFDec exports using anonymous content fingerprints.

This records repeatability patterns, NOT the cause of drift or story semantics.
Only hashed path identities and aggregate counts may leave the scratch directory.
"""
import argparse
import json
from pathlib import Path

if __package__:
    from .compare_ffdec_exports import _index
else:
    from compare_ffdec_exports import _index


def triage(index_a, index_b, index_c, limit=20):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Invalid triage sample limit')
    parsed = [_index(index) for index in (index_a, index_b, index_c)]
    swfs = {item[0] for item in parsed}
    if len(swfs) != 1:
        raise ValueError('Cannot triage different source SWF fingerprints')
    paths = [item[1] for item in parsed]
    manifests = [item[2] for item in parsed]
    a, b, c = paths
    equal_ab, equal_ac, equal_bc = a == b, a == c, b == c
    if equal_ab and equal_ac:
        pattern, outlier = 'all_equal', None
    elif equal_ab:
        pattern, outlier = 'a_b_equal', 'c'
    elif equal_ac:
        pattern, outlier = 'a_c_equal', 'b'
    elif equal_bc:
        pattern, outlier = 'b_c_equal', 'a'
    else:
        pattern, outlier = 'all_distinct', None

    union = set(a) | set(b) | set(c)
    differing = sorted(p for p in union if len({x.get(p) for x in paths}) > 1)
    membership = sum(len({p in x for x in paths}) > 1 for p in union)
    content = sum(all(p in x for x in paths)
                  and len({x[p] for x in paths}) > 1 for p in union)
    return {
        'schema_version': 1,
        'source_swf_sha256': parsed[0][0],
        'export_manifests': dict(zip('abc', manifests)),
        'export_script_counts': dict(zip('abc', (len(x) for x in paths))),
        'whole_export_pattern': pattern,
        'observed_outlier': outlier,
        'paths_in_union': len(union),
        'paths_with_membership_difference': membership,
        'common_paths_with_content_difference': content,
        'paths_with_any_difference': len(differing),
        'changed_path_sha256_examples': differing[:limit],
        'examples_truncated': len(differing) > limit,
        'verified_story_event_count': 0,
        'warning': ('An exact repeated pair is an observation, not a canonical '
                    'export or root-cause diagnosis. Three matching exports '
                    'would not prove deterministic FFDec or story semantics. '
                    'No decompiled source, original paths or media included.'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for label in 'abc':
        parser.add_argument('--index-' + label, type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    indexes = [json.loads(getattr(args, 'index_' + label).read_text(encoding='utf-8'))
               for label in 'abc']
    report = triage(*indexes, limit=args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                        encoding='utf-8')
    print('Three-export FFDec triage:', report['whole_export_pattern'],
          'differing paths:', report['paths_with_any_difference'],
          'verified story events:', report['verified_story_event_count'])


if __name__ == '__main__':
    main()
