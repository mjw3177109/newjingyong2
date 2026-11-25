"""Synthetic root opcode/correlation queue tests; no original game source."""
import unittest
from tools.build_root_conditional_review_queue import build_queue

SHA = "a" * 64


def fixture():
    rows = [
        {"root_frame": 1, "tag_ordinal": 1, "action_sha256": "b" * 64,
         "opcode_counts": {"records": 2, "if": 1, "jump": 1}, "parse_warnings": []},
        {"root_frame": 2, "tag_ordinal": 2, "action_sha256": "c" * 64,
         "opcode_counts": {"records": 3, "if": 2, "jump": 1}, "parse_warnings": []},
        {"root_frame": 3, "tag_ordinal": 3, "action_sha256": "d" * 64,
         "opcode_counts": {"records": 1, "if": 1}, "parse_warnings": ["missing_action_end"]},
    ]
    opcode = {"schema": "swf-root-action-opcode-evidence-v1", "source_swf_sha256": SHA,
              "root_showframe_tags": 4, "root_doaction_tags": 3,
              "top_level_opcode_counts": {"records": 6, "if": 4, "jump": 2},
              "tags_with_parse_warnings": 1, "action_tags": rows}
    correlation = {"schema": "swf-root-action-depth-correlation-v1",
                   "source_swf_sha256": SHA, "root_showframe_tags": 4,
                   "frames_with_both": 1, "frames_with_action_and_transition": 1,
                   "frames_with_label_and_transition": 0,
                   "overlap_frames": [{"root_frame": 1, "action_tag_count": 1,
                                      "frame_label_count": 0, "sprite_assignments": 1,
                                      "sprite_removals": 0, "sprite_displacements": 0}]}
    return opcode, correlation


class ConditionalReviewTests(unittest.TestCase):
    def test_prioritizes_overlap_not_maximum_if_count(self):
        result = build_queue(*fixture())
        self.assertEqual(result["conditional_action_tags_without_parse_warnings"], 2)
        self.assertEqual([r["root_frame"] for r in result["candidates"]], [1, 2])
        self.assertTrue(result["candidates"][0]["same_frame_sprite_transition"])
        self.assertEqual(result["verified_story_events"], 0)

    def test_limit_and_invalid_limits(self):
        a, b = fixture()
        self.assertEqual(build_queue(a, b, 1)["selected_candidate_count"], 1)
        for n in (0, 101, True):
            with self.subTest(limit=n), self.assertRaises(ValueError):
                build_queue(a, b, n)

    def test_rejects_cross_swf_and_forged_action_count(self):
        a, b = fixture()
        b["source_swf_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            build_queue(a, b)
        a, b = fixture()
        b["overlap_frames"][0]["action_tag_count"] = 2
        with self.assertRaisesRegex(ValueError, "disagree"):
            build_queue(a, b)

    def test_rejects_tampered_opcode_aggregate_and_ordinals(self):
        a, b = fixture()
        a["top_level_opcode_counts"]["if"] = 99
        with self.assertRaisesRegex(ValueError, "totals"):
            build_queue(a, b)
        a, b = fixture()
        a["action_tags"][0]["tag_ordinal"] = 3
        with self.assertRaisesRegex(ValueError, "action evidence"):
            build_queue(a, b)

    def test_excludes_malformed_action_and_does_not_leak_names(self):
        a, b = fixture()
        result = build_queue(a, b)
        self.assertEqual(result["selected_candidate_count"], 2)
        self.assertNotIn("missing_action_end", str(result))
        self.assertNotIn("script_path", str(result))
        self.assertTrue(all(c["review_status"] == "unverified" for c in result["candidates"]))


if __name__ == "__main__":
    unittest.main()
