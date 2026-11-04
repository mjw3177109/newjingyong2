#!/usr/bin/env python3
"""Prioritize source-free root conditional bytecode evidence for manual review.

Structural correlation only: no ActionScript execution or story interpretation.
"""
import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

OPCODE_SCHEMA = "swf-root-action-opcode-evidence-v1"
CORRELATION_SCHEMA = "swf-root-action-depth-correlation-v1"
COUNT_FIELDS = ("if", "jump", "goto_frame", "goto_label", "define_function", "define_function2")


def _nonnegative(value):
    return type(value) is int and value >= 0


def build_queue(opcodes, correlation, limit=50, target_frame=None):
    if opcodes.get("schema") != OPCODE_SCHEMA or correlation.get("schema") != CORRELATION_SCHEMA:
        raise ValueError("unsupported evidence schema")
    sha = opcodes.get("source_swf_sha256")
    if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{64}", sha) is None:
        raise ValueError("invalid source fingerprint")
    if sha != correlation.get("source_swf_sha256"):
        raise ValueError("source SWF fingerprint mismatch")
    frames = opcodes.get("root_showframe_tags")
    count = opcodes.get("root_doaction_tags")
    if (type(frames) is not int or frames <= 0
            or type(count) is not int or count < 0
            or frames != correlation.get("root_showframe_tags")
            or type(limit) is not int or not 1 <= limit <= 100):
        raise ValueError("invalid root counts or review limit")
    if target_frame is not None and (type(target_frame) is not int or not 1 <= target_frame <= frames + 1):
        raise ValueError("invalid target frame")
    rows = opcodes.get("action_tags")
    totals = opcodes.get("top_level_opcode_counts")
    if not isinstance(rows, list) or len(rows) != count or not isinstance(totals, dict):
        raise ValueError("invalid opcode index")
    by_frame = defaultdict(int)
    aggregate = Counter()
    warning_tags = 0
    for ordinal, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError("invalid action row")
        frame = row.get("root_frame")
        digest = row.get("action_sha256")
        counts = row.get("opcode_counts")
        warnings = row.get("parse_warnings")
        if (row.get("tag_ordinal") != ordinal or type(frame) is not int
                or not 1 <= frame <= frames + 1
                or not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None
                or not isinstance(counts, dict) or not isinstance(warnings, list)
                or any(not isinstance(k, str) or not _nonnegative(v) for k, v in counts.items())
                or any(not isinstance(w, str) for w in warnings)):
            raise ValueError("invalid action evidence")
        by_frame[frame] += 1
        aggregate.update(counts)
        warning_tags += bool(warnings)
    if (dict(aggregate) != totals
            or warning_tags != opcodes.get("tags_with_parse_warnings")):
        raise ValueError("opcode totals or warning count mismatch")
    overlap = correlation.get("overlap_frames")
    if not isinstance(overlap, list) or len(overlap) != correlation.get("frames_with_both"):
        raise ValueError("invalid correlation rows")
    overlap_by_frame = {}
    for row in overlap:
        if not isinstance(row, dict):
            raise ValueError("invalid correlation row")
        frame = row.get("root_frame")
        if (type(frame) is not int or not 1 <= frame <= frames or frame in overlap_by_frame
                or any(not _nonnegative(row.get(key)) for key in
                       ("action_tag_count", "frame_label_count", "sprite_assignments",
                        "sprite_removals", "sprite_displacements"))
                or row["action_tag_count"] + row["frame_label_count"] == 0
                or row["sprite_assignments"] + row["sprite_removals"] + row["sprite_displacements"] == 0
                or row["action_tag_count"] != by_frame.get(frame, 0)):
            raise ValueError("correlation and opcode action counts disagree")
        overlap_by_frame[frame] = row
    if (sum(bool(row["action_tag_count"]) for row in overlap) != correlation.get("frames_with_action_and_transition")
            or sum(bool(row["frame_label_count"]) for row in overlap) != correlation.get("frames_with_label_and_transition")):
        raise ValueError("correlation aggregate mismatch")
    candidates = []
    target_if_with_warnings = 0
    for row in rows:
        counts = row["opcode_counts"]
        conditional = counts.get("if", 0)
        if target_frame is not None and row["root_frame"] == target_frame and conditional and row["parse_warnings"]:
            target_if_with_warnings += 1
        if not conditional or row["parse_warnings"]:
            continue
        frame = row["root_frame"]
        shared = overlap_by_frame.get(frame)
        candidates.append({
            "root_frame": frame,
            "action_tag_ordinal": row["tag_ordinal"],
            "action_sha256": row["action_sha256"],
            "conditional_opcode_count": conditional,
            "jump_opcode_count": counts.get("jump", 0),
            "same_frame_sprite_transition": shared is not None,
            "same_frame_sprite_assignments": shared["sprite_assignments"] if shared else 0,
            "same_frame_sprite_removals": shared["sprite_removals"] if shared else 0,
            "review_status": "unverified",
        })
    candidates.sort(key=lambda x: (-(int(target_frame is not None and x["root_frame"] == target_frame)),
                                   -int(x["same_frame_sprite_transition"]),
                                   -x["conditional_opcode_count"], -x["jump_opcode_count"],
                                   x["root_frame"], x["action_tag_ordinal"]))
    target_total_action_tags = (None if target_frame is None else by_frame.get(target_frame, 0))
    target_candidates = (None if target_frame is None else
                         sum(c["root_frame"] == target_frame for c in candidates))
    target_selected = (None if target_frame is None else
                       sum(c["root_frame"] == target_frame for c in candidates[:limit]))
    return {
        "schema": "swf-root-conditional-review-queue-v1",
        "target_frame": target_frame,
        "target_frame_total_action_tags": target_total_action_tags,
        "target_frame_eligible_action_tags": target_candidates,
        "target_frame_selected_action_tags": target_selected,
        "target_frame_if_tags_excluded_by_parse_warnings": (None if target_frame is None else target_if_with_warnings),
        "target_frame_parse_integrity": ("not_requested" if target_frame is None else
                                         "contains_parse_warnings" if target_if_with_warnings else
                                         "no_parse_warnings_in_target_if_tags"),
        "target_frame_coverage": ("not_requested" if target_frame is None else
                                  "no_action_tags_in_opcode_index" if target_total_action_tags == 0 else
                                  "only_parse_warning_if_tags" if target_candidates == 0 and target_if_with_warnings else
                                  "no_valid_if_in_opcode_index" if target_candidates == 0 else
                                  "all_valid_if_tags_selected" if target_selected == target_candidates else
                                  "partially_selected_due_to_limit"),
        "source_swf_sha256": sha,
        "root_showframe_tags": frames,
        "root_doaction_tags": count,
        "conditional_action_tags_without_parse_warnings": len(candidates),
        "selected_candidate_count": min(limit, len(candidates)),
        "review_limit": limit,
        "candidates": candidates[:limit],
        "verified_story_events": 0,
        "interpretation": "Bytecode IF and sprite transitions in the same authored root frame are review hints only, not verified conditions, causal effects, gameplay, or story events. No raw script, names, art, or audio exported.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--opcodes", required=True)
    parser.add_argument("--correlation", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--target-frame", type=int, default=None,
                        help="Prioritize this root frame before the global 100-tag cap; structural evidence only")
    args = parser.parse_args()
    opcodes = json.loads(Path(args.opcodes).read_text(encoding="utf-8"))
    correlation = json.loads(Path(args.correlation).read_text(encoding="utf-8"))
    result = build_queue(opcodes, correlation, args.limit, target_frame=args.target_frame)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Conditional review queue: {} valid conditional tags, {} selected; verified events: 0".format(
        result["conditional_action_tags_without_parse_warnings"], result["selected_candidate_count"]))


if __name__ == "__main__":
    main()
