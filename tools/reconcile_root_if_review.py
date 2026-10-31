#!/usr/bin/env python3
"""Reconcile private IF review attestations without publishing story or script content.

The result counts reviewer ATTESTATIONS, not independently verified story events.
Source scripts, semantic text, original art and audio are never emitted.
"""
import argparse
import json
import re
from pathlib import Path

SCHEMA = 'swf-root-if-audit-handoff-v1'
CHECKS = {
    'ffdec_script_sha256',
    'condition_confirmed',
    'state_effects_confirmed',
    'map_context_confirmed',
    'runtime_reproduced',
    'independent_reviewed',
    'adaptation_rights_confirmed',
}
REQUIRED_PRIVATE = CHECKS - {'ffdec_script_sha256', 'adaptation_rights_confirmed'}
HEX64 = re.compile(r'^[0-9a-f]{64}$')
HEX24 = re.compile(r'^[0-9a-f]{24}$')


def reconcile(handoff, reviewed):
    """Fail closed if source identity changes or private assertions are incomplete."""
    for report in (handoff, reviewed):
        if not isinstance(report, dict) or report.get('schema') != SCHEMA:
            raise ValueError('invalid handoff schema')
        if not isinstance(report.get('source_swf_sha256'), str) or not HEX64.fullmatch(report['source_swf_sha256']):
            raise ValueError('invalid SWF fingerprint')
        if report.get('verified_story_events') != 0 or report.get('ready_for_html5_mapping') != 0:
            raise ValueError('unverified handoff cannot claim verified events or mappings')
        rows = report.get('entries')
        if not isinstance(rows, list) or not rows or type(report.get('candidate_count')) is not int or len(rows) != report['candidate_count']:
            raise ValueError('invalid entry count')
    if (handoff['source_swf_sha256'] != reviewed['source_swf_sha256']
            or handoff['candidate_count'] != reviewed['candidate_count']):
        raise ValueError('source or candidate count changed')

    def index(report):
        result = {}
        for entry in report['entries']:
            if not isinstance(entry, dict) or set(entry) != {
                    'review_id', 'source_location', 'checks', 'review_status', 'html5_event_id'}:
                raise ValueError('unexpected review entry fields')
            rid = entry['review_id']
            if not isinstance(rid, str) or not HEX24.fullmatch(rid) or rid in result:
                raise ValueError('invalid or duplicate review ID')
            if not isinstance(entry['source_location'], dict) or not isinstance(entry['checks'], dict) or set(entry['checks']) != CHECKS:
                raise ValueError('invalid review evidence structure')
            if entry['html5_event_id'] is not None:
                raise ValueError('review handoff cannot authorize HTML5 event mapping')
            result[rid] = entry
        return result

    originals, updates = index(handoff), index(reviewed)
    if originals.keys() != updates.keys():
        raise ValueError('review candidate set changed')
    result = []
    for rid, baseline in originals.items():
        entry = updates[rid]
        if entry['source_location'] != baseline['source_location']:
            raise ValueError('immutable SWF source coordinates changed')
        if baseline['review_status'] != 'unverified' or baseline['html5_event_id'] is not None or any(
                value is not (None if key == 'ffdec_script_sha256' else False)
                for key, value in baseline['checks'].items()):
            raise ValueError('baseline is not a blank unverified handoff')
        checks = entry['checks']
        digest = checks['ffdec_script_sha256']
        if digest is not None and (not isinstance(digest, str) or not HEX64.fullmatch(digest)):
            raise ValueError('invalid private script digest')
        if any(type(checks[key]) is not bool for key in CHECKS - {'ffdec_script_sha256'}):
            raise ValueError('review checks must be boolean')
        status = entry['review_status']
        if status == 'unverified':
            if digest is not None or any(checks[k] for k in CHECKS - {'ffdec_script_sha256'}):
                raise ValueError('unverified candidate has partial private attestations')
        elif status == 'reviewed_private':
            if digest is None or not all(checks[k] for k in REQUIRED_PRIVATE):
                raise ValueError('private review missing independent/runtime/semantic checks')
        else:
            raise ValueError('unrecognized or prematurely verified review status')
        result.append({
            'review_id': rid,
            'status': status,
            'rights_attested': status == 'reviewed_private' and checks['adaptation_rights_confirmed'],
        })
    private_count = sum(e['status'] == 'reviewed_private' for e in result)
    return {
        'schema': 'swf-root-if-private-review-reconciliation-v1',
        'source_swf_sha256': handoff['source_swf_sha256'],
        'candidate_count': len(result),
        'private_review_attestations': private_count,
        'rights_attestations': sum(e['rights_attested'] for e in result),
        'verified_story_events': 0,
        'ready_for_html5_mapping': 0,
        'entries': result,
        'warning': 'Private-review checkboxes are attestations only, not independent semantic proof or publication rights. No original story events are verified or mapped by this tool.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--handoff', type=Path, required=True)
    parser.add_argument('--reviewed', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = reconcile(json.loads(args.handoff.read_text(encoding='utf-8')),
                       json.loads(args.reviewed.read_text(encoding='utf-8')))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Private review attestations:', result['private_review_attestations'],
          'verified story events:', result['verified_story_events'])


if __name__ == '__main__':
    main()
