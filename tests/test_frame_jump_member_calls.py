"""Regression tests: only direct timeline calls are counted as syntax evidence."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_frame_jump_evidence import scan_script


class FrameJumpMemberCallTests(unittest.TestCase):
    def test_member_calls_not_direct_timeline_jumps(self):
        source = 'clip.gotoAndPlay(55); this.gotoAndStop(7); _root.gotoAndPlay(8);'
        result = scan_script(source)
        self.assertEqual(result['literal_jump_count'], 0)
        self.assertEqual(result['direct_guard_count'], 0)

    def test_direct_call_still_detected(self):
        result = scan_script('gotoAndPlay(55); if (ready) gotoAndStop(7);')
        self.assertEqual(result['literal_jump_count'], 2)
        self.assertEqual(result['direct_guard_count'], 1)
        self.assertEqual([j['literal_frame'] for j in result['jumps']], [55, 7])


if __name__ == '__main__':
    unittest.main()
