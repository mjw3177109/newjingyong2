#!/usr/bin/env python3
"""Fail closed on incomplete private AVM1 IF evidence; never print source text."""
import argparse
import json
import re
from pathlib import Path

SHA = re.compile(r'^[0-9a-f]{64}$')
REQUIRED = {'schema_version','source_swf_sha256','ffdec_jar_sha256','java_version','export_a_manifest_sha256','export_b_manifest_sha256','timeline_frame','doaction_index','if_offset','fallthrough_offset','jump_target_offset','predicate_trace_ref','true_branch_ref','false_branch_ref','independent_review_ref','rights_evidence_ref'}

def validate(data):
    if not isinstance(data, dict) or set(data) != REQUIRED:
        return False, 'schema fields missing or unexpected'
    if data['schema_version'] != 1:
        return False, 'unsupported schema'
    for key in ('source_swf_sha256','ffdec_jar_sha256','export_a_manifest_sha256','export_b_manifest_sha256'):
        if not isinstance(data[key], str) or not SHA.fullmatch(data[key]):
            return False, f'invalid {key}'
    if data['export_a_manifest_sha256'] != data['export_b_manifest_sha256']:
        return False, 'divergent exports'
    for key, expected in {'timeline_frame':55,'doaction_index':9,'if_offset':6607,'fallthrough_offset':6612,'jump_target_offset':6623}.items():
        if type(data[key]) is not int or data[key] != expected:
            return False, f'wrong {key}'
    for key in ('java_version','predicate_trace_ref','true_branch_ref','false_branch_ref','independent_review_ref','rights_evidence_ref'):
        value = data[key]
        if not isinstance(value,str) or not (3 <= len(value) <= 160) or '\n' in value or '\r' in value or value.lower() in ('unknown','pending','none','unverified'):
            return False, f'missing or invalid {key}'
    return True, 'structural evidence gate passed; semantic truth and rights remain subject to independent human review'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence',type=Path)
    args=parser.parse_args()
    try:
        valid,message=validate(json.loads(args.evidence.read_text(encoding='utf-8')))
    except (OSError,UnicodeError,ValueError) as exc:
        valid,message=False,type(exc).__name__
    print(('PASS: ' if valid else 'FAIL: ')+message)
    raise SystemExit(0 if valid else 1)

if __name__=='__main__':
    main()
