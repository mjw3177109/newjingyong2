"""Synthetic, non-protected FFDec export drift tests."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.diagnose_ffdec_drift import diagnose

SWF = 'a' * 64


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fixture(root, files, swf=SWF):
    entries = []
    for name, data in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        entries.append({'path_sha256': sha(name.encode('utf-8')),
                        'content_sha256': sha(data),
                        'bytes': len(data), 'lines': len(data.splitlines())})
    return {'schema_version': 1, 'source_swf_sha256': swf,
            'script_file_count': len(entries), 'entries': entries}


class FFDecDriftDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.a = Path(self.temp.name) / 'a'
        self.b = Path(self.temp.name) / 'b'
        self.a.mkdir()
        self.b.mkdir()

    def test_identical_exports_are_stable_and_source_free(self):
        files = {'secret/hero.as': b'if (x) {\n gotoAndPlay(2);\n}\n'}
        a, b = fixture(self.a, files), fixture(self.b, files)
        result = diagnose(self.a, self.b, a, b)
        self.assertEqual(result['comparison_status'], 'stable')
        self.assertEqual(result['changed_content_path_count'], 0)
        self.assertEqual(result['verified_story_event_count'], 0)
        self.assertNotIn('hero.as', json.dumps(result))
        self.assertNotIn('gotoAndPlay', json.dumps(result))

    def test_content_change_is_reported_without_source(self):
        a = fixture(self.a, {'private/script.as': b'one\nsecret AAA\n'})
        b = fixture(self.b, {'private/script.as': b'one\nsecret BBB\n'})
        result = diagnose(self.a, self.b, a, b)
        self.assertEqual(result['comparison_status'], 'divergent')
        self.assertEqual(result['changed_content_path_count'], 1)
        self.assertEqual(result['changed_examples'][0]['first_different_line_a'], 2)
        self.assertEqual(result['changed_examples'][0]['difference_class'], 'other_content_difference')
        self.assertNotIn('secret', json.dumps(result))
        self.assertNotIn('private', json.dumps(result))

    def test_classify_crlf_and_whitespace_drift(self):
        a = fixture(self.a, {'a.as': b'foo\r\nbar\r\n', 'b.as': b'x = 1;\n'})
        b = fixture(self.b, {'a.as': b'foo\nbar\n', 'b.as': b'x=1;\n'})
        result = diagnose(self.a, self.b, a, b)
        classes = {r['difference_class'] for r in result['changed_examples']}
        self.assertEqual(classes, {'line_endings_only', 'whitespace_normalized_equal'})

    def test_exact_prefix_a_of_b_is_only_a_diagnostic_clue(self):
        a = fixture(self.a, {'private/script.as': b'header\\n'})
        b = fixture(self.b, {'private/script.as': b'header\\nbody\\n'})
        result = diagnose(self.a, self.b, a, b)
        example = result['changed_examples'][0]
        self.assertEqual(example['difference_class'], 'a_exact_prefix_of_b')
        self.assertEqual(example['common_prefix_bytes'], 7)
        self.assertEqual(result['verified_story_event_count'], 0)
        self.assertNotIn('header', json.dumps(result))
        self.assertNotIn('private/', json.dumps(result))

    def test_exact_prefix_b_of_a_and_nonprefix(self):
        a = fixture(self.a, {'private/script.as': b'header\\nbody\\n'})
        b = fixture(self.b, {'private/script.as': b'header\\n'})
        result = diagnose(self.a, self.b, a, b)
        self.assertEqual(result['changed_examples'][0]['difference_class'],
                         'b_exact_prefix_of_a')
        self.assertEqual(result['changed_examples'][0]['common_prefix_bytes'], 7)

    def test_reject_tampered_index(self):
        a = fixture(self.a, {'a.as': b'first'})
        b = fixture(self.b, {'a.as': b'first'})
        b['entries'][0]['content_sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'Export bytes'):
            diagnose(self.a, self.b, a, b)

    def test_reject_different_swf(self):
        a = fixture(self.a, {'a.as': b'x'})
        b = fixture(self.b, {'a.as': b'x'}, swf='c' * 64)
        with self.assertRaisesRegex(ValueError, 'different source SWF'):
            diagnose(self.a, self.b, a, b)

    def test_reject_symlink_and_invalid_limit(self):
        a = fixture(self.a, {'a.as': b'x'})
        b = fixture(self.b, {'a.as': b'x'})
        with self.assertRaises(ValueError):
            diagnose(self.a, self.b, a, b, limit=0)
        (self.a / 'escape.as').symlink_to(self.a / 'a.as')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            diagnose(self.a, self.b, a, b)

    def test_limit_truncates_examples_not_counts(self):
        files_a = {f'script{i}.as': b'x' for i in range(3)}
        files_b = {f'script{i}.as': b'y' for i in range(3)}
        a, b = fixture(self.a, files_a), fixture(self.b, files_b)
        result = diagnose(self.a, self.b, a, b, limit=1)
        self.assertEqual(result['changed_content_path_count'], 3)
        self.assertEqual(len(result['changed_examples']), 1)
        self.assertTrue(result['examples_truncated'])


if __name__ == '__main__':
    unittest.main()
