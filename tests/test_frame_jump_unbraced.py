"""Regression coverage for simple braced and unbraced ActionScript jump guards."""
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_frame_jump_evidence import scan_script


class UnbracedFrameJumpTests(unittest.TestCase):
    def test_unbraced_if_guard_is_hashed(self):
        result = scan_script("if (questReady) gotoAndPlay(55);")
        self.assertEqual(result["literal_jump_count"], 1)
        self.assertEqual(result["direct_guard_count"], 1)
        self.assertEqual(result["jumps"][0]["direct_if_guard_sha256"],
                         hashlib.sha256(b"questReady").hexdigest())
        self.assertEqual(result["jumps"][0]["evidence_status"], "syntax_only")

    def test_braced_and_unbraced_are_both_detected(self):
        result = scan_script("if (a) { gotoAndStop(2); }\nif (b) gotoAndPlay(3);")
        self.assertEqual(result["literal_jump_count"], 2)
        self.assertEqual(result["direct_guard_count"], 2)

    def test_comments_and_strings_do_not_create_guards(self):
        result = scan_script('// if (a) gotoAndPlay(55);\n"if (b) gotoAndStop(3);"')
        self.assertEqual(result["literal_jump_count"], 0)
        self.assertEqual(result["direct_guard_count"], 0)

    def test_plain_jump_has_no_guard(self):
        result = scan_script("gotoAndPlay(55);")
        self.assertIsNone(result["jumps"][0]["direct_if_guard_sha256"])


if __name__ == "__main__":
    unittest.main()
