#!/usr/bin/env python3
"""Index only main-timeline SWF action/label tag locations; never export source text or assets."""
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

MAX_EXPANDED = 300_000_000

def index_timeline(path):
    raw = Path(path).read_bytes()
    if len(raw) < 13 or raw[:3] not in (b"FWS", b"CWS"):
        raise ValueError("expected a complete FWS or CWS file")
    declared = struct.unpack_from("<I", raw, 4)[0]
    if declared > MAX_EXPANDED:
        raise ValueError("declared SWF exceeds safety limit")
    if raw[:3] == b"CWS":
        inflater = zlib.decompressobj()
        expanded = inflater.decompress(raw[8:], MAX_EXPANDED - 7)
        if inflater.unconsumed_tail or not inflater.eof:
            raise ValueError("compressed SWF incomplete or too large")
        expanded += inflater.flush()
        data = raw[:8] + expanded
    else:
        data = raw
    if len(data) > MAX_EXPANDED or len(data) != declared:
        raise ValueError("SWF length does not match header or exceeds limit")
    nbits = data[8] >> 3
    rect_size = (5 + 4 * nbits + 7) // 8
    header = 8 + rect_size
    if header + 4 > len(data):
        raise ValueError("truncated frame header")
    expected_frames = struct.unpack_from("<H", data, header + 2)[0]
    offset = header + 4
    frame = 1
    showframes = 0
    action_total = 0
    label_total = 0
    evidence = {}
    saw_end = False
    while offset < len(data):
        if offset + 2 > len(data):
            raise ValueError("truncated tag header")
        tag_header = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        code, size = tag_header >> 6, tag_header & 63
        if size == 63:
            if offset + 4 > len(data):
                raise ValueError("truncated extended tag header")
            size = struct.unpack_from("<I", data, offset)[0]
            offset += 4
        if size > len(data) - offset:
            raise ValueError("tag exceeds file boundary")
        payload = data[offset:offset + size]
        offset += size
        if code == 0:
            saw_end = True
            break
        if code == 1:
            showframes += 1
            frame += 1
        elif code in (12, 43):
            item = evidence.setdefault(frame, {"frame": frame, "action_tag_count": 0,
                                                "frame_label_count": 0, "_hashes": []})
            if code == 12:
                action_total += 1
                item["action_tag_count"] += 1
                item["_hashes"].append(hashlib.sha256(payload).digest())
            else:
                label_total += 1
                item["frame_label_count"] += 1
    if not saw_end:
        raise ValueError("SWF End tag missing")
    rows = []
    for number in sorted(evidence):
        item = evidence[number]
        digests = item.pop("_hashes")
        if digests:
            item["action_payload_digest"] = hashlib.sha256(b"".join(digests)).hexdigest()
        rows.append(item)
    return {
        "schema": "swf-main-timeline-evidence-v1",
        "source_swf_sha256": hashlib.sha256(raw).hexdigest(),
        "declared_main_frames": expected_frames,
        "observed_showframe_tags": showframes,
        "main_timeline_frame_count_matches": expected_frames == showframes,
        "main_timeline_action_tags": action_total,
        "main_timeline_frame_labels": label_total,
        "evidence_frame_count": len(rows),
        "evidence_frames": rows,
        "interpretation": "Structural tag positions only; no story event, map, NPC, or battle semantics verified.",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("swf")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = index_timeline(args.swf)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Main timeline: {} ShowFrame, {} DoAction, {} FrameLabel, {} evidence frames".format(
        result["observed_showframe_tags"], result["main_timeline_action_tags"],
        result["main_timeline_frame_labels"], result["evidence_frame_count"]))

if __name__ == "__main__":
    main()
