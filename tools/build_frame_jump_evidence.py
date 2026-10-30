#!/usr/bin/env python3
"""Produce source-free literal timeline-jump evidence from temporary FFDec exports.

Not an ActionScript parser. Numeric jump sites and simple if-guards are syntax
evidence only; never claim verified story events or timeline scope.
"""
import argparse
import json
import re
from pathlib import Path

if __package__:
    from .index_ffdec_scripts import digest, file_digest
else:
    from index_ffdec_scripts import digest, file_digest

HEX64 = re.compile(r'^[0-9a-f]{64}$')
CANDIDATE = re.compile(r'^SRC-[0-9a-f]{20}$')
LEX = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
JUMP = re.compile(r'\bgotoAnd(?P<mode>Play|Stop)\s*\(\s*(?P<frame>\d+)\s*\)')
SIMPLE_IF = re.compile(
    r'\bif\s*\(\s*(?P<condition>[^()\n]+?)\s*\)\s*\{\s*'
    r'gotoAnd(?P<mode>Play|Stop)\s*\(\s*(?P<frame>\d+)\s*\)\s*;\s*\}',
    re.MULTILINE,
)


def mask_noncode(source):
    """Mask strings and comments without moving offsets or newline positions."""
    return LEX.sub(lambda m: ''.join('\n' if ch == '\n' else ' ' for ch in m.group()), source)


def scan_script(source, limit=32):
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 64:
        raise ValueError('limit must be in [1,64]')
    clean = mask_noncode(source)
    jumps = list(JUMP.finditer(clean))
    guarded = {}
    for m in SIMPLE_IF.finditer(clean):
        jump = JUMP.search(clean, m.start(), m.end())
        if jump is not None:
            guarded[jump.start()] = digest(m.group('condition').strip().encode('utf-8'))
    results = []
    for m in jumps[:limit]:
        results.append({
            'line': clean.count('\n', 0, m.start()) + 1,
            'mode': m.group('mode').lower(),
            'literal_frame': int(m.group('frame')),
            'direct_if_guard_sha256': guarded.get(m.start()),
            'evidence_status': 'syntax_only',
        })
    return {
        'literal_jump_count': len(jumps),
        'positions_truncated': len(jumps) > limit,
        'direct_guard_count': len(guarded),
        'jumps': results,
    }


def build_frame_jump_evidence(root, swf, queue, limit=32):
    root, swf = Path(root), Path(swf)
    if root.is_symlink() or not root.is_dir() or not swf.is_file():
        raise ValueError('Missing script directory or SWF')
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 64:
        raise ValueError('Invalid per-script limit')
    if not isinstance(queue, dict) or queue.get('schema_version') != 1:
        raise ValueError('Expected source-free review queue v1')
    swf_hash = queue.get('source_swf_sha256')
    if not isinstance(swf_hash, str) or not HEX64.fullmatch(swf_hash) or file_digest(swf) != swf_hash:
        raise ValueError('Source SWF fingerprint mismatch')
    rows = queue.get('candidates')
    if not isinstance(rows, list) or not 0 <= len(rows) <= 500 or queue.get('selected_count') != len(rows):
        raise ValueError('Invalid queue candidates')
    targets = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid candidate row')
        ph, ch, cid = row.get('path_sha256'), row.get('content_sha256'), row.get('candidate_id')
        if not isinstance(ph, str) or not HEX64.fullmatch(ph) or not isinstance(ch, str) or not HEX64.fullmatch(ch):
            raise ValueError('Invalid script digest')
        expected = 'SRC-' + digest((swf_hash + ':' + ph + ':' + ch).encode('ascii'))[:20]
        if not isinstance(cid, str) or not CANDIDATE.fullmatch(cid) or cid != expected or row.get('semantic_status') != 'unverified' or ph in targets:
            raise ValueError('Tampered or duplicate candidate')
        targets[ph] = (cid, ch)
    found = {}
    count = 0
    for path in root.rglob('*'):
        if path.is_symlink() or not path.is_file():
            continue
        count += 1
        ph = digest(path.relative_to(root).as_posix().encode('utf-8'))
        if ph not in targets:
            continue
        cid, ch = targets[ph]
        data = path.read_bytes()
        if digest(data) != ch:
            raise ValueError('Exported script fingerprint mismatch')
        found[ph] = {
            'candidate_id': cid,
            'path_sha256': ph,
            'content_sha256': ch,
            **scan_script(data.decode('utf-8', errors='replace'), limit),
        }
    if count != queue.get('indexed_script_count') or len(found) != len(targets):
        raise ValueError('Source export count or candidate membership mismatch')
    entries = [found[row['path_sha256']] for row in rows]
    return {
        'schema_version': 1,
        'source_swf_sha256': swf_hash,
        'indexed_script_count': count,
        'candidate_count': len(entries),
        'literal_jump_count': sum(x['literal_jump_count'] for x in entries),
        'direct_guard_count': sum(x['direct_guard_count'] for x in entries),
        'verified_story_event_count': 0,
        'entries': entries,
        'warning': 'Syntax-only jump targets are not confirmed frames, events, maps, battle values, or story conditions. Timeline scope is unknown.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scripts', type=Path)
    parser.add_argument('--source-swf', type=Path, required=True)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=32)
    args = parser.parse_args()
    queue = json.loads(args.queue.read_text(encoding='utf-8'))
    report = build_frame_jump_evidence(args.scripts, args.source_swf, queue, args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Literal jump syntax:', report['literal_jump_count'],
          'direct simple-if guards:', report['direct_guard_count'],
          'verified story events:', report['verified_story_event_count'])


if __name__ == '__main__':
    main()
