"""Synthetic structural evidence tests only; no protected game content."""
import unittest
from tools.correlate_root_action_depth import correlate

SHA = "a" * 64


def fixtures():
    timeline = {
        "schema": "swf-main-timeline-evidence-v1", "source_swf_sha256": SHA,
        "observed_showframe_tags": 3, "main_timeline_frame_count_matches": True,
        "main_timeline_action_tags": 2, "main_timeline_frame_labels": 1,
        "evidence_frame_count": 2,
        "evidence_frames": [
            {"frame": 1, "action_tag_count": 1, "frame_label_count": 1},
            {"frame": 3, "action_tag_count": 1, "frame_label_count": 0},
        ],
    }
    depth = {
        "schema": "swf-root-depth-structural-evidence-v1", "source_swf_sha256": SHA,
        "root_showframe_tags": 3, "sprite_depth_transition_count": 3,
        "sprite_character_assignment_tags": 2, "sprite_removal_tags": 1,
        "sprite_depth_transitions": [
            {"root_frame": 1, "depth": 2, "sprite_id": 7, "kind": "sprite_character_assigned"},
            {"root_frame": 2, "depth": 2, "sprite_id": 7, "kind": "sprite_character_removed"},
            {"root_frame": 3, "depth": 2, "sprite_id": 8, "kind": "sprite_character_assigned"},
        ],
    }
    return timeline, depth


class CorrelationTests(unittest.TestCase):
    def test_overlap_and_no_story_inference(self):
        a, b = fixtures()
        r = correlate(a, b)
        self.assertEqual(r["frames_with_both"], 2)
        self.assertEqual(r["frames_with_action_and_transition"], 2)
        self.assertEqual(r["frames_with_label_and_transition"], 1)
        self.assertEqual([x["root_frame"] for x in r["overlap_frames"]], [1, 3])
        self.assertEqual(r["verified_story_events"], 0)
        self.assertNotIn("sprite_id", str(r))

    def test_reject_mismatched_source_and_frame_count(self):
        for key, value in (("source_swf_sha256", "b" * 64), ("root_showframe_tags", 4)):
            with self.subTest(key=key):
                a, b = fixtures()
                b[key] = value
                with self.assertRaises(ValueError):
                    correlate(a, b)

    def test_reject_forged_totals_and_duplicate_frames(self):
        for variant in ("action", "transition", "duplicate", "declared"):
            a, b = fixtures()
            if variant == "action":
                a["main_timeline_action_tags"] += 1
            elif variant == "transition":
                b["sprite_character_assignment_tags"] += 1
            elif variant == "duplicate":
                a["evidence_frames"][1]["frame"] = 1
            else:
                a["main_timeline_frame_count_matches"] = False
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                correlate(a, b)

    def test_reject_invalid_transition_and_no_source_text(self):
        for variant in ("unknown_kind", "bad_frame", "bad_depth"):
            a, b = fixtures()
            if variant == "unknown_kind":
                b["sprite_depth_transitions"][0]["kind"] = "verified_story_event"
            elif variant == "bad_frame":
                b["sprite_depth_transitions"][0]["root_frame"] = 4
            else:
                b["sprite_depth_transitions"][0]["depth"] = -1
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                correlate(a, b)

    def test_no_overlap_is_valid(self):
        a, b = fixtures()
        a["evidence_frames"] = [{"frame": 2, "action_tag_count": 2, "frame_label_count": 1}]
        a["evidence_frame_count"] = 1
        b["sprite_depth_transitions"] = [
            {"root_frame": 1, "depth": 1, "sprite_id": 2, "kind": "sprite_character_assigned"},
            {"root_frame": 3, "depth": 1, "sprite_id": 2, "kind": "sprite_character_removed"},
        ]
        b["sprite_depth_transition_count"] = 2
        b["sprite_character_assignment_tags"] = 1
        b["sprite_removal_tags"] = 1
        self.assertEqual(correlate(a, b)["frames_with_both"], 0)


if __name__ == "__main__":
    unittest.main()
