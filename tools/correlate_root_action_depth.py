#!/usr/bin/env python3
"""Correlate authored root action/label frames with sprite depth transitions.

Pure structural evidence; no ActionScript execution or story inference.
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

TIMELINE_SCHEMA = "swf-main-timeline-evidence-v1"
DEPTH_SCHEMA = "swf-root-depth-structural-evidence-v1"
KINDS = ("sprite_character_assigned", "sprite_character_removed", "prior_sprite_displaced")


def correlate(timeline, depth):
    if timeline.get("schema") != TIMELINE_SCHEMA or depth.get("schema") != DEPTH_SCHEMA:
        raise ValueError("unsupported evidence schema")
    sha = timeline.get("source_swf_sha256")
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError("invalid source fingerprint")
    if sha != depth.get("source_swf_sha256"):
        raise ValueError("source SWF fingerprint mismatch")
    total_frames = timeline.get("observed_showframe_tags")
    if type(total_frames) is not int or total_frames <= 0 or total_frames != depth.get("root_showframe_tags"):
        raise ValueError("root frame count mismatch")
    if timeline.get("main_timeline_frame_count_matches") is not True:
        raise ValueError("declared and observed root frame counts disagree")

    action_frames = {}
    total_actions = total_labels = 0
    for row in timeline.get("evidence_frames", []):
        frame = row.get("frame")
        actions, labels = row.get("action_tag_count"), row.get("frame_label_count")
        if (type(frame) is not int or not 1 <= frame <= total_frames or frame in action_frames
                or type(actions) is not int or actions < 0
                or type(labels) is not int or labels < 0 or actions + labels == 0):
            raise ValueError("invalid main-timeline evidence row")
        action_frames[frame] = (actions, labels)
        total_actions += actions
        total_labels += labels
    if (len(action_frames) != timeline.get("evidence_frame_count")
            or total_actions != timeline.get("main_timeline_action_tags")
            or total_labels != timeline.get("main_timeline_frame_labels")):
        raise ValueError("main-timeline evidence totals mismatch")

    grouped = defaultdict(lambda: Counter())
    transition_count = Counter()
    for row in depth.get("sprite_depth_transitions", []):
        frame, kind = row.get("root_frame"), row.get("kind")
        sid, instance_depth = row.get("sprite_id"), row.get("depth")
        if (type(frame) is not int or not 1 <= frame <= total_frames
                or kind not in KINDS or type(sid) is not int or sid <= 0
                or type(instance_depth) is not int or instance_depth < 0):
            raise ValueError("invalid depth transition")
        grouped[frame][kind] += 1
        transition_count[kind] += 1
    if (sum(transition_count.values()) != depth.get("sprite_depth_transition_count")
            or transition_count["sprite_character_assigned"] != depth.get("sprite_character_assignment_tags")
            or transition_count["sprite_character_removed"] != depth.get("sprite_removal_tags")):
        raise ValueError("depth transition totals mismatch")

    overlap = []
    for frame in sorted(action_frames.keys() & grouped.keys()):
        actions, labels = action_frames[frame]
        counts = grouped[frame]
        overlap.append({
            "root_frame": frame,
            "action_tag_count": actions,
            "frame_label_count": labels,
            "sprite_assignments": counts["sprite_character_assigned"],
            "sprite_removals": counts["sprite_character_removed"],
            "sprite_displacements": counts["prior_sprite_displaced"],
        })
    return {
        "schema": "swf-root-action-depth-correlation-v1",
        "source_swf_sha256": sha,
        "root_showframe_tags": total_frames,
        "frames_with_action_or_label": len(action_frames),
        "frames_with_sprite_transition": len(grouped),
        "frames_with_both": len(overlap),
        "frames_with_action_and_transition": sum(bool(row["action_tag_count"]) for row in overlap),
        "frames_with_label_and_transition": sum(bool(row["frame_label_count"]) for row in overlap),
        "overlap_frames": overlap,
        "interpretation": "Co-occurrence of authored SWF tags in a root frame, NOT a causal link, "
                          "runtime event, map, battle, NPC, or verified story event. No source text/assets exported.",
        "verified_story_events": 0,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--timeline", required=True)
    p.add_argument("--depth", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    timeline = json.loads(Path(a.timeline).read_text(encoding="utf-8"))
    depth = json.loads(Path(a.depth).read_text(encoding="utf-8"))
    report = correlate(timeline, depth)
    target = Path(a.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Root structural correlation: {} overlapping frames ({} action, {} label); story events verified: 0".format(
        report["frames_with_both"], report["frames_with_action_and_transition"],
        report["frames_with_label_and_transition"]))


if __name__ == "__main__":
    main()
