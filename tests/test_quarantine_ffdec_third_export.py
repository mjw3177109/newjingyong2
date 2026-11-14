"""Source-free synthetic tests for the conditional third-export audit quarantine."""
import copy
import hashlib
import json
import unittest

from tools.quarantine_ffdec_third_export import quarantine

SWF = 'a' * 64
PATH = 'b' * 64
CONTENT = 'c' * 64


def inputs():
    row = {
        'path_sha256': PATH, 'content_sha256': CONTENT,
        'candidate_id': 'SRC-' + hashlib.sha256(f'{SWF}:{PATH}:{CONTENT}'.encode('ascii')).hexdigest()[:20],
        'literal_jump_count': 4, 'direct_guard_count': 1,
        'evidence_status': 'reproducible_syntax_unverified',
    }
    canonical = f'{PATH}:{CONTENT}:4:1'
    stable = {
        'schema_version': 1, 'scope': 'two_exports_same_ci_run_only',
        'source_swf_sha256': SWF, 'stable_candidate_count': 1,
        'stable_manifest_sha256': hashlib.sha256(canonical.encode('ascii')).hexdigest(),
        'stable_candidates': [row],
    }
    third = {'schema_version': 1, 'source_swf_sha256': SWF,
             'script_file_count': 1,
             'entries': [{'path_sha256': PATH, 'content_sha256': CONTENT}]}
    return stable, third


class ThirdExportQuarantineTests(unittest.TestCase):
    def test_matching_third_export_keeps_unverified_candidate(self):
        stable, third = inputs()
        result = quarantine(stable, third)
        self.assertEqual(result['retained_candidate_count'], 1)
        self.assertEqual(result['quarantined_candidate_count'], 0)
        self.assertEqual(result['verified_story_event_count'], 0)
        self.assertNotIn('private', json.dumps(result))

    def test_third_content_drift_quarantines_even_when_first_two_match(self):
        stable, third = inputs()
        third['entries'][0]['content_sha256'] = 'd' * 64
        result = quarantine(stable, third)
        self.assertEqual(result['retained_candidate_count'], 0)
        self.assertEqual(result['quarantined_candidates'][0]['reason'],
                         'content_changed_in_third_export')

    def test_missing_third_script_quarantines(self):
        stable, third = inputs()
        third['entries'], third['script_file_count'] = [], 0
        result = quarantine(stable, third)
        self.assertEqual(result['quarantined_candidates'][0]['reason'], 'missing_in_third_export')

    def test_rejects_cross_swf_and_tampered_manifest(self):
        stable, third = inputs()
        third['source_swf_sha256'] = 'd' * 64
        with self.assertRaisesRegex(ValueError, 'different source SWF'):
            quarantine(stable, third)
        stable, third = inputs()
        stable['stable_manifest_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'fingerprint mismatch'):
            quarantine(stable, third)

    def test_rejects_duplicate_candidate_or_forged_identity(self):
        stable, third = inputs()
        stable['stable_candidates'].append(copy.deepcopy(stable['stable_candidates'][0]))
        stable['stable_candidate_count'] = 2
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            quarantine(stable, third)
        stable, third = inputs()
        stable['stable_candidates'][0]['candidate_id'] = 'SRC-' + '0' * 20
        with self.assertRaisesRegex(ValueError, 'invalid'):
            quarantine(stable, third)

    def test_rejects_semantic_injection_and_bad_counts(self):
        stable, third = inputs()
        stable['stable_candidates'][0]['claimed_map'] = 'invented'
        with self.assertRaisesRegex(ValueError, 'fields'):
            quarantine(stable, third)
        stable, third = inputs()
        stable['stable_candidates'][0]['direct_guard_count'] = True
        with self.assertRaisesRegex(ValueError, 'invalid'):
            quarantine(stable, third)


if __name__ == '__main__':
    unittest.main()
