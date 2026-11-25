"""Audit index must be deterministic and must not leak original script text or paths."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.index_ffdec_scripts import build_index


class ScriptIndexTests(unittest.TestCase):
    def test_deterministic_and_no_source_leak(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scripts = root / 'private-scripts'
            scripts.mkdir()
            (scripts / 'secret-plot-name.as').write_text(
                'if (hiddenFlag) { gotoAndStop(12); }\nfunction secretQuest() {}\n', encoding='utf-8')
            swf = root / 'source.swf'
            swf.write_bytes(b'CWS synthetic fixture')
            a = build_index(scripts, swf)
            b = build_index(scripts, swf)
            self.assertEqual(a, b)
            self.assertEqual(a['script_file_count'], 1)
            self.assertEqual(a['heuristic_totals']['conditional_if'], 1)
            self.assertEqual(a['heuristic_totals']['timeline_goto'], 1)
            serialized = json.dumps(a)
            for forbidden in ('secret-plot-name', 'secretQuest', 'hiddenFlag', 'gotoAndStop(12)', str(root)):
                self.assertNotIn(forbidden, serialized)

    def test_empty_directory_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scripts = root / 'scripts'
            scripts.mkdir()
            swf = root / 'source.swf'
            swf.write_bytes(b'fixture')
            (scripts / 'outside.as').symlink_to(swf)
            result = build_index(scripts, swf)
            self.assertEqual(result['script_file_count'], 0)
            self.assertEqual(result['entries'], [])

    def test_missing_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                build_index(Path(temp) / 'missing', Path(temp) / 'missing.swf')


if __name__ == '__main__':
    unittest.main()
