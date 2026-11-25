"""Synthetic-only tests; no original SWF script content is embedded."""
import hashlib
import json
import unittest

from tools.build_stable_audit_set import build_stable_set

SWF = 'a' * 64


def make_export(rows):
    """rows = [(path_hash_char, content_hash_char, jumps, guards, selected), ...]."""
    entries, candidates, jump_entries = [], [], []
    for p, c, jumps, guards, selected in rows:
        path, content = p * 64, c * 64
        entries.append({'path_sha256': path, 'content_sha256': content})
        if selected:
            cid = 'SRC-' + hashlib.sha256(f'{SWF}:{path}:{content}'.encode('ascii')).hexdigest()[:20]
            candidates.append({'path_sha256': path, 'content_sha256': content,
                               'candidate_id': cid, 'semantic_status': 'unverified'})
            jump_entries.append({'path_sha256': path, 'content_sha256': content,
                                 'candidate_id': cid, 'literal_jump_count': jumps,
                                 'direct_guard_count': guards})
    idx = {'schema_version': 1, 'source_swf_sha256': SWF,
           'script_file_count': len(entries), 'entries': entries}
    queue = {'schema_version': 1, 'source_swf_sha256': SWF,
             'indexed_script_count': len(entries), 'selected_count': len(candidates),
             'candidates': candidates}
    jumps = {'schema_version': 1, 'source_swf_sha256': SWF,
             'indexed_script_count': len(entries), 'candidate_count': len(candidates),
             'literal_jump_count': sum(r['literal_jump_count'] for r in jump_entries),
             'direct_guard_count': sum(r['direct_guard_count'] for r in jump_entries),
             'verified_story_event_count': 0, 'entries': jump_entries}
    return idx, queue, jumps


def compare(a, b):
    return build_stable_set(a[0], b[0], a[1], b[1], a[2], b[2])


class StableAuditSetTests(unittest.TestCase):
    def test_identical_exports_retain_syntax_not_story(self):
        a = make_export([('1', 'b', 4, 1, True)])
        report = compare(a, a)
        self.assertEqual(report['stable_candidate_count'], 1)
        self.assertEqual(report['stable_literal_jump_count'], 4)
        self.assertEqual(report['verified_story_event_count'], 0)
        self.assertNotIn('private.as', json.dumps(report))

    def test_content_drift_excludes_candidate(self):
        a = make_export([('1', 'b', 4, 1, True)])
        b = make_export([('1', 'c', 5, 2, True)])
        report = compare(a, b)
        self.assertEqual(report['stable_candidate_count'], 0)
        self.assertEqual(report['exclusion_reason_counts'], {'script_content_changed': 1})

    def test_candidate_membership_drift_excludes_only_one(self):
        a = make_export([('1', 'b', 4, 1, True), ('2', 'c', 2, 0, False)])
        b = make_export([('1', 'b', 4, 1, True), ('2', 'c', 2, 0, True)])
        report = compare(a, b)
        self.assertEqual(report['stable_candidate_count'], 1)
        self.assertEqual(report['excluded_candidate_count'], 1)
        self.assertEqual(report['exclusion_reason_counts'], {'selected_in_one_export_only': 1})

    def test_same_content_syntax_drift_excludes_candidate(self):
        a = make_export([('1', 'b', 4, 1, True)])
        b = make_export([('1', 'b', 3, 1, True)])
        report = compare(a, b)
        self.assertEqual(report['exclusion_reason_counts'], {'syntax_counts_changed': 1})

    def test_cross_swf_or_tampered_queue_rejected(self):
        a = make_export([('1', 'b', 4, 1, True)])
        b = make_export([('1', 'b', 4, 1, True)])
        b[0]['source_swf_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'different source SWF'):
            compare(a, b)
        b = make_export([('1', 'b', 4, 1, True)])
        b[1]['candidates'][0]['candidate_id'] = 'SRC-' + '0' * 20
        with self.assertRaisesRegex(ValueError, 'identity'):
            compare(a, b)

    def test_order_independent_manifest_and_reason_counts(self):
        rows = [('1', 'b', 4, 1, True), ('2', 'c', 2, 0, True)]
        a, b = make_export(rows), make_export(list(reversed(rows)))
        x, y = compare(a, b), compare(b, a)
        self.assertEqual(x, y)
        self.assertEqual(x['stable_candidate_count'], 2)


if __name__ == '__main__':
    unittest.main()
