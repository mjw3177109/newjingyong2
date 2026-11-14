"""Synthetic-only tests: no protected SWF scripts or private logs used."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.summarize_ffdec_logs import MAX_LOG_BYTES, fingerprint, summarize


class FFDecLogFingerprintTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def log(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return path

    def test_equal_logs_are_fingerprinted_without_raw_text(self):
        raw = b'Private path /tmp/scratch/secret.as\nWarning: synthetic issue\n'
        a = self.log('a.log', raw)
        b = self.log('b.log', raw)
        result = summarize(a, b)
        self.assertEqual(result['byte_identical_pattern'], 'a_b_equal')
        self.assertEqual(result['observations']['a']['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['observations']['a']['line_count'], 2)
        self.assertEqual(result['observations']['a']['warning_marker_lines'], 1)
        self.assertNotIn('secret.as', json.dumps(result))
        self.assertFalse(result['raw_log_content_exported'])

    def test_different_logs_and_heuristic_markers(self):
        a = self.log('a.log', b'error: sample\nexception: sample\n')
        b = self.log('b.log', b'completed\n')
        result = summarize(a, b)
        self.assertEqual(result['byte_identical_pattern'], 'a_b_different')
        self.assertEqual(result['observations']['a']['error_marker_lines'], 2)
        self.assertEqual(result['observations']['b']['error_marker_lines'], 0)

    def test_three_run_equality_patterns_do_not_pick_authority(self):
        a = self.log('a.log', b'A')
        b = self.log('b.log', b'B')
        c = self.log('c.log', b'A')
        self.assertEqual(summarize(a, b, c)['byte_identical_pattern'], 'a_c_equal')
        c.write_bytes(b'C')
        self.assertEqual(summarize(a, b, c)['byte_identical_pattern'], 'all_distinct')
        b.write_bytes(b'A')
        c.write_bytes(b'A')
        self.assertEqual(summarize(a, b, c)['byte_identical_pattern'], 'all_equal')

    def test_rejects_symlink_and_non_file(self):
        a = self.log('a.log', b'A')
        alias = self.root / 'alias.log'
        alias.symlink_to(a)
        with self.assertRaises(ValueError):
            fingerprint(alias)
        with self.assertRaises(ValueError):
            fingerprint(self.root)
        with self.assertRaises(ValueError):
            fingerprint(self.root / 'missing.log')

    def test_rejects_oversized_log(self):
        a = self.root / 'oversized.log'
        with a.open('wb') as stream:
            stream.truncate(MAX_LOG_BYTES + 1)
        with self.assertRaises(ValueError):
            fingerprint(a)


if __name__ == '__main__':
    unittest.main()
