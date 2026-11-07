"""Only invented fixtures; no original SWF source is committed."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.build_frame_jump_evidence import scan_script, build_frame_jump_evidence
from tools.build_review_queue import build_review_queue
from tools.index_ffdec_scripts import build_index


class FrameJumpEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'scripts'
        self.root.mkdir()
        self.swf = Path(self.tmp.name) / 'fixture.swf'
        self.swf.write_bytes(b'INVENTED_TEST_SWF')
        self.script = self.root / 'private.as'
        self.script.write_text('if (demoFlag == 1) { gotoAndPlay(42); }\n'
                               'gotoAndStop(7);\n', encoding='utf-8')

    def queue(self):
        return build_review_queue(build_index(self.root, self.swf))

    def test_exact_literal_jump_and_direct_guard(self):
        result = scan_script(self.script.read_text(encoding='utf-8'))
        self.assertEqual(result['literal_jump_count'], 2)
        self.assertEqual(result['direct_guard_count'], 1)
        self.assertEqual(result['jumps'][0]['line'], 1)
        self.assertEqual(result['jumps'][0]['mode'], 'play')
        self.assertEqual(result['jumps'][0]['literal_frame'], 42)
        self.assertRegex(result['jumps'][0]['direct_if_guard_sha256'], r'^[0-9a-f]{64}$')
        self.assertIsNone(result['jumps'][1]['direct_if_guard_sha256'])

    def test_comments_and_literals_are_not_code(self):
        source = '// gotoAndPlay(12)\n"gotoAndStop(13)";\n'
        source += '/* gotoAndPlay(14)\n if(x){gotoAndStop(15);} */\n'
        source += 'if(flag) { trace("gotoAndPlay(16)"); }\ngotoAndStop(17);'
        result = scan_script(source)
        self.assertEqual(result['literal_jump_count'], 1)
        self.assertEqual(result['jumps'][0]['literal_frame'], 17)
        self.assertEqual(result['jumps'][0]['line'], 6)

    def test_conservative_guard_and_limit(self):
        source = 'if(flag) { trace(1); gotoAndPlay(3); }\n'
        source += 'if(flag) { gotoAndPlay(variable); }\n'
        source += 'gotoAndStop(9);\n'
        result = scan_script(source, 1)
        self.assertEqual(result['literal_jump_count'], 2)
        self.assertTrue(result['positions_truncated'])
        self.assertIsNone(result['jumps'][0]['direct_if_guard_sha256'])
        with self.assertRaises(ValueError):
            scan_script(source, 0)

    def test_source_free_report_and_tamper_detection(self):
        report = build_frame_jump_evidence(self.root, self.swf, self.queue())
        self.assertEqual(report['literal_jump_count'], 2)
        self.assertEqual(report['verified_story_event_count'], 0)
        exported = json.dumps(report)
        for secret in ('demoFlag', 'private.as', 'INVENTED_TEST_SWF'):
            self.assertNotIn(secret, exported)
        queue = self.queue()
        self.script.write_text('gotoAndPlay(999);', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            build_frame_jump_evidence(self.root, self.swf, queue)
        self.script.unlink()
        with self.assertRaises(ValueError):
            build_frame_jump_evidence(self.root, self.swf, queue)


if __name__ == '__main__':
    unittest.main()
