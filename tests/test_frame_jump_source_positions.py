"""Regression tests for source positions in syntax-only FFDec jump evidence."""
import unittest

from tools.build_frame_jump_evidence import scan_script


class JumpSourcePositionTests(unittest.TestCase):
    def test_multibyte_prefix_and_multiline_positions(self):
        source = '// 中文\n  gotoAndPlay(55);\n'
        result = scan_script(source)
        self.assertEqual(result['literal_jump_count'], 1)
        jump = result['jumps'][0]
        self.assertEqual(jump['line'], 2)
        self.assertEqual(jump['column'], 3)
        self.assertEqual(jump['utf8_byte_offset'], len('// 中文\n  '.encode('utf-8')))
        self.assertEqual(jump['evidence_status'], 'syntax_only')

    def test_multiple_jumps_have_independent_offsets(self):
        source = 'gotoAndStop(1);\n // ignored gotoAndPlay(9)\n gotoAndPlay(55);'
        result = scan_script(source)
        self.assertEqual(result['literal_jump_count'], 2)
        for jump, expected in zip(result['jumps'], ('gotoAndStop(1)', 'gotoAndPlay(55)')):
            offset = source.index(expected)
            self.assertEqual(jump['utf8_byte_offset'], len(source[:offset].encode('utf-8')))
            self.assertEqual(jump['column'], offset - source.rfind('\n', 0, offset))


if __name__ == '__main__':
    unittest.main()
