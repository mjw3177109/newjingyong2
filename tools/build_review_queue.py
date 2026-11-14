#!/usr/bin/env python3
"""Prioritize source-free FFDec script *review candidates*, never plot claims.

The input is the SHA-256-only index produced by index_ffdec_scripts.py.
This tool cannot infer characters, quests, maps, battle rules or event semantics.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

HEX64 = re.compile(r'^[0-9a-f]{64}$')
WEIGHTS = {
    'conditional_if': 2,
    'conditional_else': 1,
    'timeline_goto': 6,
    'event_handler': 5,
    'function_decl': 1,
}
CONTROL_SIGNALS = ('conditional_if', 'timeline_goto', 'event_handler')


def _sha(value):
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise ValueError('Expected a SHA-256 hex digest')
    return value


def build_review_queue(index, limit=100):
    """Return a deterministic, source-free queue; every candidate is UNVERIFIED."""
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500:
        raise ValueError('limit must be an integer in [1, 500]')
    if not isinstance(index, dict) or index.get('schema_version') != 1:
        raise ValueError('Expected FFDec source-free index schema v1')
    swf = _sha(index.get('source_swf_sha256'))
    entries = index.get('entries')
    if not isinstance(entries, list) or index.get('script_file_count') != len(entries):
        raise ValueError('Index file count mismatch')
    seen = set()
    candidates = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Invalid index entry')
        path_hash = _sha(entry.get('path_sha256'))
        content_hash = _sha(entry.get('content_sha256'))
        if path_hash in seen:
            raise ValueError('Duplicate source path hash')
        seen.add(path_hash)
        hints = entry.get('hint_counts')
        if not isinstance(hints, dict):
            raise ValueError('Missing hint counts')
        counts = {}
        for name in WEIGHTS:
            value = hints.get(name, 0)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError('Invalid heuristic count')
            counts[name] = value
        if not any(counts[name] for name in CONTROL_SIGNALS):
            continue
        score = sum(counts[name] * WEIGHTS[name] for name in WEIGHTS)
        candidate_id = hashlib.sha256(
            (swf + ':' + path_hash + ':' + content_hash).encode('ascii')
        ).hexdigest()[:20]
        candidates.append({
            'candidate_id': 'SRC-' + candidate_id,
            'path_sha256': path_hash,
            'content_sha256': content_hash,
            'review_score': score,
            'hint_counts': counts,
            'semantic_status': 'unverified',
        })
    candidates.sort(key=lambda row: (-row['review_score'], row['path_sha256']))
    # Explicitly omit raw source paths, source text and all unknown index keys.
    return {
        'schema_version': 1,
        'source_swf_sha256': swf,
        'indexed_script_count': len(entries),
        'control_signal_candidate_count': len(candidates),
        'selected_count': min(limit, len(candidates)),
        'selection_rule': 'heuristic control-flow token counts; NOT verified plot events',
        'candidates': candidates[:limit],
        'warning': 'Review candidates are NOT confirmed story events, conditions, maps, NPCs, or battle values.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('index', type=Path, help='source-free FFDec index JSON')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    result = build_review_queue(json.loads(args.index.read_text(encoding='utf-8')), args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Source-free review queue:', result['selected_count'],
          'selected of', result['control_signal_candidate_count'], 'candidates')


if __name__ == '__main__':
    main()
