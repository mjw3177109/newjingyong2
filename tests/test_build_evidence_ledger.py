"""Synthetic scripts only; no original copyrighted source content."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.build_evidence_ledger import build_evidence_ledger
from tools.index_ffdec_scripts import build_index
from tools.build_review_queue import build_review_queue


class EvidenceLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'scripts'
        self.root.mkdir()
        self.swf = Path(self.tmp.name) / 'dummy.swf'
        self.swf.write_bytes(b'FAKE_TEST_SFW_NOT_ORIGINAL')
        self.script = self.root / 'private_scene_hero.as'
        self.script.write_text('on(release) {\n if(secretQuestFlag) {\n gotoAndPlay(42);\n }\n}\n', encoding='utf-8')

    def queue(self):
        return build_review_queue(build_index(self.root, self.swf))

    def test_locators_are_grounded_and_source_free(self):
        queue = self.queue()
        ledger = build_evidence_ledger(self.root, self.swf, queue)
        self.assertEqual(ledger['candidate_count'], 1)
        self.assertEqual(ledger['reviewed_story_event_count'], 0)
        row = ledger['entries'][0]
        self.assertEqual(row['control_flow_syntax']['event_handler']['line_numbers'], [1])
        self.assertEqual(row['control_flow_syntax']['conditional_if']['line_numbers'], [2])
        self.assertEqual(row['control_flow_syntax']['timeline_goto']['line_numbers'], [3])
        self.assertIsNone(row['source_event_id'])
        exported = json.dumps(ledger)
        for private in ('private_scene_hero', 'secretQuestFlag', 'release', 'FAKE_TEST_SFW'):
            self.assertNotIn(private, exported)

    def test_rejects_stale_script_content_and_missing_file(self):
        queue = self.queue()
        self.script.write_text('if(changedFlag) {}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'changed'):
            build_evidence_ledger(self.root, self.swf, queue)
        self.script.unlink()
        with self.assertRaises(ValueError):
            build_evidence_ledger(self.root, self.swf, queue)

    def test_rejects_tampered_queue_and_wrong_swf(self):
        queue = self.queue()
        bad = json.loads(json.dumps(queue))
        bad['candidates'][0]['candidate_id'] = 'SRC-' + '0' * 20
        with self.assertRaises(ValueError):
            build_evidence_ledger(self.root, self.swf, bad)
        self.swf.write_bytes(b'CHANGED')
        with self.assertRaisesRegex(ValueError, 'SWF fingerprint'):
            build_evidence_ledger(self.root, self.swf, queue)

    def test_bounded_locations_and_empty_queue(self):
        self.script.write_text('\n'.join('if(flag){}' for _ in range(10)), encoding='utf-8')
        result = build_evidence_ledger(self.root, self.swf, self.queue(), max_positions=3)
        info = result['entries'][0]['control_flow_syntax']['conditional_if']
        self.assertEqual(info['match_count'], 10)
        self.assertEqual(info['line_numbers'], [1, 2, 3])
        self.assertTrue(info['line_numbers_truncated'])
        with self.assertRaises(ValueError):
            build_evidence_ledger(self.root, self.swf, self.queue(), max_positions=0)
        self.script.write_text('var x = 1;', encoding='utf-8')
        empty = build_evidence_ledger(self.root, self.swf, self.queue())
        self.assertEqual(empty['candidate_count'], 0)
        self.assertEqual(empty['entries'], [])


if __name__ == '__main__':
    unittest.main()
