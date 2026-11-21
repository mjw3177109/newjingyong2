#!/usr/bin/env python3
"""Create a source-free FFDec script inventory. Never publish exported source."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HINT_PATTERNS = {
    'conditional_if': re.compile(r'\bif\s*\('),
    'conditional_else': re.compile(r'\belse\b'),
    'timeline_goto': re.compile(r'\bgotoAnd(?:Play|Stop)\s*\('),
    'event_handler': re.compile(r'\bon(?:ClipEvent)?\s*\('),
    'function_decl': re.compile(r'\bfunction\b'),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def build_index(root, swf):
    root, swf = Path(root), Path(swf)
    if not root.is_dir() or not swf.is_file():
        raise ValueError('Script directory and source SWF must exist')
    entries = []
    totals = Counter()
    for path in root.rglob('*'):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        decoded = data.decode('utf-8', errors='replace')
        hints = {name: len(pattern.findall(decoded)) for name, pattern in HINT_PATTERNS.items()}
        totals.update(hints)
        suffix = path.suffix.lower()
        entries.append({
            'path_sha256': digest(rel.encode('utf-8')),
            'content_sha256': digest(data),
            'bytes': len(data),
            'lines': len(data.splitlines()),
            'extension': suffix if suffix in {'.as', '.txt'} else 'other',
            'hint_counts': hints,
        })
    entries.sort(key=lambda item: item['path_sha256'])
    return {
        'schema_version': 1,
        'source_swf_sha256': file_digest(swf),
        'script_file_count': len(entries),
        'heuristic_totals': dict(sorted(totals.items())),
        'entries': entries,
        'warning': 'Token counts are unverified syntax hints, NOT confirmed plot events, maps, variables, or battle rules.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scripts', type=Path)
    parser.add_argument('--source-swf', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build_index(args.scripts, args.source_swf)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Source-free FFDec index:', result['script_file_count'], 'files;',
          'source SWF SHA256:', result['source_swf_sha256'])


if __name__ == '__main__':
    main()
