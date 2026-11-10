#!/usr/bin/env python3
"""Check private IF6607 evidence envelope completeness, not authenticity."""
import argparse
import json
import re
from pathlib import Path

HASH = re.compile(r'^[0-9a-f]{64}$')
EXPECTED_SWF_SHA256 = 'd762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30'
REQUIRED = ('source_swf_sha256', 'java8_version', 'ffdec_version',
            'export_a_sha256', 'export_b_sha256',
            'condition_stack_evidence_sha256', 'independent_review_sha256')
PATH_HASHES = ('before_state_sha256', 'after_state_sha256',
               'execution_trace_sha256', 'effects_evidence_sha256')


def validate(record):
    if not isinstance(record, dict):
        return False
    if any(not isinstance(record.get(k), str) or not record[k].strip()
           for k in REQUIRED):
        return False
    for k in ('source_swf_sha256', 'export_a_sha256', 'export_b_sha256',
              'condition_stack_evidence_sha256', 'independent_review_sha256'):
        if not HASH.fullmatch(record[k]):
            return False
    if record['source_swf_sha256'] != EXPECTED_SWF_SHA256:
        return False
    if (record['export_a_sha256'] != record['export_b_sha256']
            and not HASH.fullmatch(str(record.get('export_drift_review_sha256', '')))):
        return False
    if any(type(record.get(k)) is not int or record[k] != expected
           for k, expected in (('frame', 55), ('action_ordinal', 9),
                               ('if_offset', 6607))):
        return False
    paths = record.get('paths')
    if not isinstance(paths, dict) or set(paths) != {'true', 'false'}:
        return False
    for name, successor in (('true', 6623), ('false', 6612)):
        path = paths[name]
        if (not isinstance(path, dict)
                or type(path.get('observed_successor')) is not int
                or path['observed_successor'] != successor):
            return False
        if any(not HASH.fullmatch(str(path.get(k, ''))) for k in PATH_HASHES):
            return False
    if paths['true']['execution_trace_sha256'] == paths['false']['execution_trace_sha256']:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_json', type=Path)
    args = parser.parse_args()
    try:
        valid = validate(json.loads(args.private_json.read_text(encoding='utf-8')))
    except (OSError, ValueError, UnicodeError):
        valid = False
    print('IF6607 envelope: complete (NOT independently verified)' if valid
          else 'IF6607 envelope: incomplete or invalid')
    raise SystemExit(0 if valid else 1)


if __name__ == '__main__':
    main()
