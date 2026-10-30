"""Synthetic FFDec evidence only; no original protected source."""
import hashlib
import json
import unittest
from tools.compare_ffdec_exports import compare_runs

SWF = 'a' * 64


def fixture(content='b', jump_count=2, guard_count=1):
    path, blob = '1' * 64, content * 64
    cid = 'SRC-' + hashlib.sha256(f'{SWF}:{path}:{blob}'.encode('ascii')).hexdigest()[:20]
    index = {'schema_version': 1, 'source_swf_sha256': SWF, 'script_file_count': 1,
             'entries': [{'path_sha256': path, 'content_sha256': blob}]}
    queue = {'schema_version': 1, 'source_swf_sha256': SWF, 'indexed_script_count': 1,
             'selected_count': 1, 'candidates': [{'path_sha256': path, 'content_sha256': blob,
                                                  'candidate_id': cid, 'semantic_status': 'unverified'}]}
    jumps = {'schema_version': 1, 'source_swf_sha256': SWF, 'indexed_script_count': 1,
             'candidate_count': 1, 'literal_jump_count': jump_count, 'direct_guard_count': guard_count,
             'verified_story_event_count': 0,
             'entries': [{'path_sha256': path, 'content_sha256': blob, 'candidate_id': cid,
                          'literal_jump_count': jump_count, 'direct_guard_count': 1}]}
    return index, queue, jumps


class CompareFFDecTests(unittest.TestCase):
    def test_identical_exports_are_stable_and_source_free(self):
        i, q, j = fixture()
        r = compare_runs(i, i, q, q, j, j)
        self.assertEqual(r['comparison_status'], 'stable')
        self.assertEqual(r['difference']['common_paths_with_changed_content'], 0)
        self.assertNotIn('private.as', json.dumps(r))
        self.assertEqual(r['verified_story_event_count'], 0)

    def test_same_paths_changed_content_is_divergent(self):
        i, q, j = fixture()
        i2, q2, j2 = fixture(content='c')
        r = compare_runs(i, i2, q, q2, j, j2)
        self.assertEqual(r['comparison_status'], 'divergent')
        self.assertEqual(r['difference']['common_paths_with_changed_content'], 1)

    def test_same_content_changed_jumps_is_divergent(self):
        i, q, j = fixture()
        _, _, j2 = fixture(jump_count=3)
        r = compare_runs(i, i, q, q, j, j2)
        self.assertEqual(r['comparison_status'], 'divergent')
        self.assertEqual(r['difference']['common_candidates_with_changed_jump_counts'], 1)

    def test_same_content_changed_guards_is_divergent(self):
        i, q, j = fixture()
        _, _, j2 = fixture(guard_count=0)
        r = compare_runs(i, i, q, q, j, j2)
        self.assertEqual(r['comparison_status'], 'divergent')
        self.assertEqual(r['difference']['common_candidates_with_changed_jump_counts'], 0)
        self.assertEqual(r['difference']['common_candidates_with_changed_guard_counts'], 1)

    def test_reject_cross_swf_and_tampered_queue(self):
        i, q, j = fixture()
        i2, q2, j2 = fixture()
        i2['source_swf_sha256'] = 'c' * 64
        with self.assertRaisesRegex(ValueError, 'different source SWF'):
            compare_runs(i, i2, q, q2, j, j2)
        q2['candidates'][0]['candidate_id'] = 'SRC-' + '0' * 20
        with self.assertRaisesRegex(ValueError, 'identity'):
            compare_runs(i, i, q, q2, j, j)

    def test_reject_inconsistent_jump_totals(self):
        i, q, j = fixture()
        j2 = json.loads(json.dumps(j))
        j2['literal_jump_count'] = 999
        with self.assertRaisesRegex(ValueError, 'total mismatch'):
            compare_runs(i, i, q, q, j, j2)


if __name__ == '__main__':
    unittest.main()
