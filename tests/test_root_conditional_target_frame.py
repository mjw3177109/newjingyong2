"""Regression tests for target-frame priority before capped root IF sampling."""
import unittest

from tools.build_root_conditional_review_queue import build_queue


class TargetFrameSelectionTests(unittest.TestCase):
    def fixtures(self):
        sha = "a" * 64
        rows = []
        for i, frame in enumerate((1, 2, 55), 1):
            rows.append({
                "tag_ordinal": i, "root_frame": frame,
                "action_sha256": format(i, "064x"),
                "opcode_counts": {"if": 1}, "parse_warnings": [],
            })
        opcodes = {
            "schema": "swf-root-action-opcode-evidence-v1",
            "source_swf_sha256": sha, "root_showframe_tags": 55,
            "root_doaction_tags": 3, "action_tags": rows,
            "top_level_opcode_counts": {"if": 3},
            "tags_with_parse_warnings": 0,
        }
        correlation = {
            "schema": "swf-root-action-depth-correlation-v1",
            "source_swf_sha256": sha, "root_showframe_tags": 55,
            "overlap_frames": [], "frames_with_both": 0,
            "frames_with_action_and_transition": 0,
            "frames_with_label_and_transition": 0,
        }
        return opcodes, correlation

    def test_target_precedes_global_cap(self):
        queue = build_queue(*self.fixtures(), limit=1, target_frame=55)
        self.assertEqual(queue["candidates"][0]["root_frame"], 55)
        self.assertEqual(queue["target_frame_eligible_action_tags"], 1)
        self.assertEqual(queue["target_frame_selected_action_tags"], 1)
        self.assertEqual(queue["target_frame_coverage"], "all_valid_if_tags_selected")
        self.assertEqual(queue["conditional_action_tags_without_parse_warnings"], 3)
        self.assertEqual(queue["verified_story_events"], 0)

    def test_default_sort_is_unchanged(self):
        queue = build_queue(*self.fixtures(), limit=1)
        self.assertEqual(queue["candidates"][0]["root_frame"], 1)
        self.assertEqual(queue["target_frame_coverage"], "not_requested")

    def test_no_valid_if_in_target(self):
        queue = build_queue(*self.fixtures(), limit=1, target_frame=54)
        self.assertEqual(queue["target_frame_coverage"], "no_valid_if_in_opcode_index")
        self.assertEqual(queue["target_frame_selected_action_tags"], 0)

    def test_reject_invalid_target(self):
        for frame in (0, -1, True, 57, "55"):
            with self.subTest(frame=frame), self.assertRaises(ValueError):
                build_queue(*self.fixtures(), limit=1, target_frame=frame)

    def test_partial_target_selection(self):
        opcodes, correlation = self.fixtures()
        opcodes["action_tags"][1]["root_frame"] = 55
        queue = build_queue(opcodes, correlation, limit=1, target_frame=55)
        self.assertEqual(queue["target_frame_eligible_action_tags"], 2)
        self.assertEqual(queue["target_frame_selected_action_tags"], 1)
        self.assertEqual(queue["target_frame_coverage"], "partially_selected_due_to_limit")


if __name__ == "__main__":
    unittest.main()
