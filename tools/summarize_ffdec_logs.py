#!/usr/bin/env python3
"""Fingerprint private FFDec CLI logs without publishing their contents.

Log fingerprints are diagnostics only: a changed digest is not proof of a
failed export, and identical logs do not prove bytecode or story equivalence.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

MAX_LOG_BYTES = 8 * 1024 * 1024
_MARKERS = {
    'error_marker_lines': re.compile(rb'\berror\b|\bexception\b', re.IGNORECASE),
    'warning_marker_lines': re.compile(rb'\bwarn(?:ing)?\b', re.IGNORECASE),
}


def fingerprint(path):
    """Read only a regular, bounded log; return anonymous aggregate metadata."""
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError('FFDec log must be a regular, non-symlink file')
    if p.stat().st_size > MAX_LOG_BYTES:
        raise ValueError('FFDec log exceeds diagnostic size limit')
    data = p.read_bytes()
    if len(data) > MAX_LOG_BYTES:
        raise ValueError('FFDec log changed beyond diagnostic size limit')
    lines = data.splitlines()
    result = {
        'sha256': hashlib.sha256(data).hexdigest(),
        'byte_count': len(data),
        'line_count': len(lines),
    }
    for name, pattern in _MARKERS.items():
        result[name] = sum(bool(pattern.search(line)) for line in lines)
    return result


def _pattern(digests):
    if len(digests) == 2:
        return 'a_b_equal' if digests[0] == digests[1] else 'a_b_different'
    a, b, c = digests
    if a == b == c:
        return 'all_equal'
    if a == b:
        return 'a_b_equal'
    if a == c:
        return 'a_c_equal'
    if b == c:
        return 'b_c_equal'
    return 'all_distinct'


def summarize(log_a, log_b, log_c=None):
    logs = {'a': fingerprint(log_a), 'b': fingerprint(log_b)}
    if log_c is not None:
        logs['c'] = fingerprint(log_c)
    return {
        'schema': 'ffdec-log-fingerprints-v1',
        'observations': logs,
        'byte_identical_pattern': _pattern([v['sha256'] for v in logs.values()]),
        'raw_log_content_exported': False,
        'interpretation': 'Diagnostics only; marker counts are heuristic, not verified errors or story evidence.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log-a', required=True, type=Path)
    parser.add_argument('--log-b', required=True, type=Path)
    parser.add_argument('--log-c', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    result = summarize(args.log_a, args.log_b, args.log_c)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('FFDec log fingerprints:', result['byte_identical_pattern'],
          '; raw log content retained in private scratch only')


if __name__ == '__main__':
    main()
