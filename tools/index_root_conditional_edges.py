#!/usr/bin/env python3
"""Source-free top-level AVM1 branch edges for selected root DoAction tags."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

try:
    from tools.index_swf_sprite_timeline import load_swf, iter_tags
    from tools.index_swf_action_opcodes import inspect_actions
except ModuleNotFoundError:
    from index_swf_sprite_timeline import load_swf, iter_tags
    from index_swf_action_opcodes import inspect_actions


def branch_edges(payload):
    """Only structural offsets; never decode operands, names or script text."""
    pos, boundaries, branches, ended = 0, set(), [], False
    while pos < len(payload):
        start = pos
        boundaries.add(start)
        opcode = payload[pos]
        pos += 1
        if opcode == 0:
            ended = True
            if any(payload[pos:]):
                raise ValueError("nonzero bytes after ActionEnd")
            break
        if opcode < 0x80:
            continue
        if pos + 2 > len(payload):
            raise ValueError("truncated action length")
        length = struct.unpack_from("<H", payload, pos)[0]
        pos += 2
        if length > len(payload) - pos:
            raise ValueError("truncated action payload")
        if opcode in (0x99, 0x9D):
            if length != 2:
                raise ValueError("invalid branch payload length")
            delta = struct.unpack_from("<h", payload, pos)[0]
            branches.append((start, pos + length + delta, "if" if opcode == 0x9D else "jump"))
        pos += length
    if not ended:
        raise ValueError("missing ActionEnd")
    edges = []
    for source, target, kind in branches:
        alignment = ("out_of_bounds" if target < 0 or target >= len(payload)
                     else "record_boundary" if target in boundaries else "inside_record")
        edges.append({"opcode": kind, "source_offset": source, "target_offset": target,
                      "target_alignment": alignment,
                      "direction": "forward" if target > source else "backward_or_self"})
    return edges


def build_edges(path, opcodes, queue):
    if (opcodes.get("schema") != "swf-root-action-opcode-evidence-v1"
            or queue.get("schema") != "swf-root-conditional-review-queue-v1"):
        raise ValueError("unsupported evidence schema")
    raw, data, offset = load_swf(path)
    sha = hashlib.sha256(raw).hexdigest()
    if opcodes.get("source_swf_sha256") != sha or queue.get("source_swf_sha256") != sha:
        raise ValueError("source fingerprint mismatch")
    rows, selected = opcodes.get("action_tags"), queue.get("candidates")
    if (not isinstance(rows, list) or not isinstance(selected, list)
            or len(selected) != queue.get("selected_candidate_count")
            or len(selected) > 100 or queue.get("verified_story_events") != 0):
        raise ValueError("invalid evidence selection")
    selected_by_ordinal = {}
    for candidate in selected:
        if not isinstance(candidate, dict):
            raise ValueError("invalid candidate")
        ordinal = candidate.get("action_tag_ordinal")
        if (type(ordinal) is not int or ordinal < 1 or ordinal > len(rows)
                or ordinal in selected_by_ordinal or candidate.get("review_status") != "unverified"):
            raise ValueError("invalid candidate ordinal or status")
        selected_by_ordinal[ordinal] = candidate
    ordinal, frame, frames = 0, 1, 0
    result_rows = []
    for code, payload in iter_tags(data, offset, len(data)):
        if code == 1:
            frames += 1
            frame += 1
        elif code == 12:
            ordinal += 1
            if ordinal > len(rows):
                raise ValueError("extra root action tag")
            source = rows[ordinal - 1]
            digest = hashlib.sha256(payload).hexdigest()
            if (source.get("tag_ordinal") != ordinal or source.get("root_frame") != frame
                    or source.get("action_sha256") != digest):
                raise ValueError("opcode index and SWF action mismatch")
            if ordinal not in selected_by_ordinal:
                continue
            candidate = selected_by_ordinal[ordinal]
            counts, warnings = inspect_actions(payload)
            if (warnings or source.get("parse_warnings") != []
                    or source.get("opcode_counts") != counts
                    or candidate.get("root_frame") != frame
                    or candidate.get("action_sha256") != digest
                    or candidate.get("conditional_opcode_count") != counts.get("if", 0)
                    or candidate.get("jump_opcode_count") != counts.get("jump", 0)
                    or counts.get("if", 0) < 1):
                raise ValueError("selected action evidence mismatch")
            edges = branch_edges(payload)
            if (sum(e["opcode"] == "if" for e in edges) != counts.get("if", 0)
                    or sum(e["opcode"] == "jump" for e in edges) != counts.get("jump", 0)):
                raise ValueError("branch count mismatch")
            result_rows.append({"root_frame": frame, "action_tag_ordinal": ordinal,
                                "action_sha256": digest, "edges": edges,
                                "review_status": "unverified"})
    if (ordinal != len(rows) or ordinal != opcodes.get("root_doaction_tags")
            or frames != opcodes.get("root_showframe_tags")
            or frames != queue.get("root_showframe_tags")
            or ordinal != queue.get("root_doaction_tags")
            or len(result_rows) != len(selected)):
        raise ValueError("root timeline or selection count mismatch")
    order = {c["action_tag_ordinal"]: i for i, c in enumerate(selected)}
    result_rows.sort(key=lambda r: order[r["action_tag_ordinal"]])
    edges = [edge for row in result_rows for edge in row["edges"]]
    return {"schema": "swf-root-conditional-edges-v1", "source_swf_sha256": sha,
            "selected_action_tags": len(result_rows), "total_branch_edges": len(edges),
            "if_edges": sum(e["opcode"] == "if" for e in edges),
            "jump_edges": sum(e["opcode"] == "jump" for e in edges),
            "invalid_target_edges": sum(e["target_alignment"] != "record_boundary" for e in edges),
            "candidates": result_rows, "verified_story_events": 0,
            "interpretation": "Root top-level byte offsets only. No nested functions, runtime, variable, map, battle, or plot semantics verified; no script or media exported."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("swf")
    parser.add_argument("--opcodes", required=True)
    parser.add_argument("--queue", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    opcodes = json.loads(Path(args.opcodes).read_text(encoding="utf-8"))
    queue = json.loads(Path(args.queue).read_text(encoding="utf-8"))
    result = build_edges(args.swf, opcodes, queue)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Conditional edge evidence: {} selected actions, {} IF edges, {} Jump edges, {} invalid targets; verified events: 0".format(
        result["selected_action_tags"], result["if_edges"], result["jump_edges"], result["invalid_target_edges"]))


if __name__ == "__main__":
    main()
