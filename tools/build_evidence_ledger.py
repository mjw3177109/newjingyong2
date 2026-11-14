#!/usr/bin/env python3
"""Locate FFDec control-flow *syntax* for private review without exporting source.

Line numbers and SHA-256 digests are evidence locators, NOT verified events.
No original script paths, identifiers, literals, dialogue, or source are emitted.
"""
import argparse
from bisect import bisect_right
import json
import re
from pathlib import Path

if __package__:
    from .index_ffdec_scripts import HINT_PATTERNS, digest, file_digest
else:
    from index_ffdec_scripts import HINT_PATTERNS, digest, file_digest

HEX64 = re.compile(r'^[0-9a-f]{64}$')
CANDIDATE = re.compile(r'^SRC-[0-9a-f]{20}$')


def _sha(value):
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise ValueError('Invalid SHA-256 digest')
    return value


def _line_evidence(source, max_positions):
    """Return counts and bounded 1-based source line numbers, never source text."""
    starts = [m.start() for m in re.finditer('\n', source)]
    result = {}
    for name, pattern in HINT_PATTERNS.items():
        matches = list(pattern.finditer(source))
        locations = sorted({bisect_right(starts, match.start()) + 1 for match in matches})
        result[name] = {
            'match_count': len(matches),
            'line_numbers': locations[:max_positions],
            'line_numbers_truncated': len(locations) > max_positions,
        }
    return result


def build_evidence_ledger(root, swf, queue, max_positions=16):
    """Join a ranked source-free queue to verified local files, by exact hashes."""
    root, swf = Path(root), Path(swf)
    if root.is_symlink() or not root.is_dir() or not swf.is_file():
        raise ValueError('Valid script directory and SWF are required')
    if not isinstance(max_positions, int) or isinstance(max_positions, bool) or not 1 <= max_positions <= 64:
        raise ValueError('max_positions must be an integer in [1, 64]')
    if not isinstance(queue, dict) or queue.get('schema_version') != 1:
        raise ValueError('Expected source-free review queue v1')
    swf_sha = _sha(queue.get('source_swf_sha256'))
    if file_digest(swf) != swf_sha:
        raise ValueError('Source SWF fingerprint mismatch')
    rows = queue.get('candidates')
    if not isinstance(rows, list) or not 0 <= len(rows) <= 500 or queue.get('selected_count') != len(rows):
        raise ValueError('Queue selected_count mismatch')
    targets = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid candidate')
        path_hash = _sha(row.get('path_sha256'))
        content_hash = _sha(row.get('content_sha256'))
        cid = row.get('candidate_id')
        expected = 'SRC-' + digest((swf_sha + ':' + path_hash + ':' + content_hash).encode('ascii'))[:20]
        if not isinstance(cid, str) or CANDIDATE.fullmatch(cid) is None or cid != expected:
            raise ValueError('Candidate ID / source fingerprint mismatch')
        if row.get('semantic_status') != 'unverified' or path_hash in targets:
            raise ValueError('Duplicate or semantically pre-verified candidate')
        targets[path_hash] = (cid, content_hash)
    found = {}
    file_count = 0
    for path in root.rglob('*'):
        if path.is_symlink() or not path.is_file():
            continue
        file_count += 1
        path_hash = digest(path.relative_to(root).as_posix().encode('utf-8'))
        if path_hash not in targets:
            continue
        cid, expected_content = targets[path_hash]
        data = path.read_bytes()
        if digest(data) != expected_content:
            raise ValueError('Exported script changed since index generation')
        text = data.decode('utf-8', errors='replace')
        found[path_hash] = {
            'candidate_id': cid,
            'path_sha256': path_hash,
            'content_sha256': expected_content,
            'source_event_id': None,
            'trigger': None,
            'effects': None,
            'html5_event_id': None,
            'semantic_status': 'unverified',
            'control_flow_syntax': _line_evidence(text, max_positions),
        }
    if file_count != queue.get('indexed_script_count'):
        raise ValueError('Exported script count changed since index generation')
    if len(found) != len(targets):
        raise ValueError('One or more ranked source scripts could not be found')
    return {
        'schema_version': 1,
        'source_swf_sha256': swf_sha,
        'indexed_script_count': file_count,
        'candidate_count': len(rows),
        'reviewed_story_event_count': 0,
        'evidence_type': 'source-file SHA-256 plus decompiled syntax line positions',
        'entries': [found[row['path_sha256']] for row in rows],
        'warning': 'Locations are syntactic hints only. No original story event, condition, map, NPC, item or battle value has been verified.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scripts', type=Path)
    parser.add_argument('--source-swf', type=Path, required=True)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-positions', type=int, default=16)
    args = parser.parse_args()
    queue = json.loads(args.queue.read_text(encoding='utf-8'))
    result = build_evidence_ledger(args.scripts, args.source_swf, queue, args.max_positions)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Syntax evidence ledger:', result['candidate_count'], 'unverified candidates;',
          result['reviewed_story_event_count'], 'verified story events')


if __name__ == '__main__':
    main()
