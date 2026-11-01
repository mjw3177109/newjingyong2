"""Source-free synthetic tests for comparing FFDec indexes across CI runs."""
import hashlib
import json
import unittest

from tools.compare_ffdec_run_baselines import compare_baselines

SWF = 'a' * 64


def fixture(files, swf=SWF):
    rows = [{'path_sha256': hashlib.sha256(path.encode()).hexdigest(),
             'content_sha256': hashlib.sha256(content.encode()).hexdigest()}
            for path, content in files.items()]
    return {'schema_version': 1, 'source_swf_sha256': swf,
            'script_file_count': len(rows), 'entries': rows}


class CrossRunBaselineTests(unittest.TestCase):
    def test_matching_indexes_are_not_story_verification(self):
        a = fixture({'private/one.as': 'A'})
        result = compare_baselines(a, a)
        self.assertEqual(result['comparison_status'], 'matching_indexes')
        self.assertEqual(result['verified_story_event_count'], 0)
        self.assertEqual(result['changed_path_examples'], [])

    def test_changed_content_and_membership_are_distinguished(self):
        a = fixture({'private/one.as': 'A', 'private/old.as': 'X'})
        b = fixture({'private/one.as': 'B', 'private/new.as': 'Y'})
        result = compare_baselines(a, b)
        self.assertEqual(result['comparison_status'], 'divergent_indexes')
        self.assertEqual(result['common_paths_with_changed_content'], 1)
        self.assertEqual((result['paths_only_a'], result['paths_only_b']), (1, 1))
        self.assertEqual({e['difference_kind'] for e in result['changed_path_examples']},
                         {'content', 'only_a', 'only_b'})
        payload = json.dumps(result)
        self.assertNotIn('private/', payload)
        self.assertNotIn('one.as', payload)
        self.assertNotIn('old.as', payload)

    def test_example_limit_does_not_truncate_counts(self):
        a = fixture({f'private/{i}.as': 'A' for i in range(5)})
        b = fixture({f'private/{i}.as': 'B' for i in range(5)})
        result = compare_baselines(a, b, limit=1)
        self.assertEqual(result['common_paths_with_changed_content'], 5)
        self.assertEqual(len(result['changed_path_examples']), 1)
        self.assertTrue(result['examples_truncated'])

    def test_rejects_unrelated_swf_or_tampered_index(self):
        a = fixture({'private/one.as': 'A'})
        with self.assertRaisesRegex(ValueError, 'different source SWF'):
            compare_baselines(a, fixture({'private/one.as': 'A'}, swf='b' * 64))
        bad = json.loads(json.dumps(a))
        bad['entries'][0]['content_sha256'] = 'invalid'
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            compare_baselines(a, bad)

    def test_rejects_invalid_limit_and_duplicate_paths(self):
        a = fixture({'private/one.as': 'A'})
        for value in (True, 0, -1, 101, '20'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                compare_baselines(a, a, limit=value)
        bad = json.loads(json.dumps(a))
        bad['entries'].append(dict(bad['entries'][0]))
        bad['script_file_count'] = 2
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            compare_baselines(a, bad)


if __name__ == '__main__':
    unittest.main()
