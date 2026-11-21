#!/usr/bin/env python3
"""Source-free DefineSprite timeline structure index. Never emit scripts or artwork."""
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

MAX_EXPANDED = 300_000_000


def load_swf(path):
    raw = Path(path).read_bytes()
    if len(raw) < 13 or raw[:3] not in (b"FWS", b"CWS"):
        raise ValueError("expected FWS or CWS")
    declared = struct.unpack_from("<I", raw, 4)[0]
    if declared < 13 or declared > MAX_EXPANDED:
        raise ValueError("invalid expanded length")
    if raw[:3] == b"CWS":
        decoder = zlib.decompressobj()
        body = decoder.decompress(raw[8:], MAX_EXPANDED - 8)
        if decoder.unconsumed_tail or not decoder.eof or decoder.unused_data:
            raise ValueError("invalid or oversized compressed stream")
        body += decoder.flush()
        data = b"FWS" + raw[3:8] + body
    else:
        data = raw
    if len(data) != declared:
        raise ValueError("SWF declared size mismatch")
    nbits = data[8] >> 3
    offset = 8 + (5 + 4 * nbits + 7) // 8 + 4
    if offset > len(data):
        raise ValueError("truncated frame header")
    return raw, data, offset


def iter_tags(data, start, end):
    offset = start
    while offset < end:
        if offset + 2 > end:
            raise ValueError("truncated tag header")
        value = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        code, length = value >> 6, value & 63
        if length == 63:
            if offset + 4 > end:
                raise ValueError("truncated extended tag header")
            length = struct.unpack_from("<I", data, offset)[0]
            offset += 4
        if length > end - offset:
            raise ValueError("tag exceeds timeline boundary")
        payload = data[offset:offset + length]
        offset += length
        yield code, payload
        if code == 0:
            if offset != end:
                raise ValueError("unexpected bytes after timeline End")
            return
    raise ValueError("timeline End tag missing")


def index_sprites(path):
    raw, data, offset = load_swf(path)
    records = {}
    init_counts = {}
    main_showframes = 0
    for code, payload in iter_tags(data, offset, len(data)):
        if code == 1:
            main_showframes += 1
        elif code == 59:
            if len(payload) < 2:
                raise ValueError("truncated DoInitAction sprite id")
            sprite_id = struct.unpack_from("<H", payload)[0]
            init_counts[sprite_id] = init_counts.get(sprite_id, 0) + 1
        elif code == 39:
            if len(payload) < 6:
                raise ValueError("truncated DefineSprite")
            sprite_id, declared_frames = struct.unpack_from("<HH", payload)
            if sprite_id in records:
                raise ValueError("duplicate DefineSprite id")
            frame = 1
            showframes = 0
            actions = 0
            labels = 0
            rows = {}
            for inner_code, inner_payload in iter_tags(payload, 4, len(payload)):
                if inner_code == 1:
                    showframes += 1
                    frame += 1
                elif inner_code in (12, 43):
                    item = rows.setdefault(frame, {"frame": frame, "action_tag_count": 0,
                                                   "frame_label_count": 0, "_digests": []})
                    if inner_code == 12:
                        actions += 1
                        item["action_tag_count"] += 1
                        item["_digests"].append(hashlib.sha256(inner_payload).digest())
                    else:
                        labels += 1
                        item["frame_label_count"] += 1
            evidence = []
            for number in sorted(rows):
                item = rows[number]
                digests = item.pop("_digests")
                if digests:
                    item["action_payload_digest"] = hashlib.sha256(b"".join(digests)).hexdigest()
                evidence.append(item)
            records[sprite_id] = {"sprite_id": sprite_id, "declared_frames": declared_frames,
                                  "observed_showframe_tags": showframes,
                                  "frame_count_matches": declared_frames == showframes,
                                  "action_tag_count": actions, "frame_label_count": labels,
                                  "evidence_frame_count": len(evidence), "evidence_frames": evidence}
    for sprite_id, count in init_counts.items():
        if sprite_id in records:
            records[sprite_id]["root_init_action_count"] = count
    return {"schema": "swf-sprite-timeline-evidence-v1",
            "source_swf_sha256": hashlib.sha256(raw).hexdigest(),
            "root_showframe_tags": main_showframes,
            "sprite_count": len(records),
            "root_init_action_tag_count": sum(init_counts.values()),
            "root_init_actions_for_defined_sprites": sum(count for sid, count in init_counts.items() if sid in records),
            "sprites_with_frame_count_mismatch": sum(not r["frame_count_matches"] for r in records.values()),
            "sprite_action_tag_count": sum(r["action_tag_count"] for r in records.values()),
            "sprite_frame_label_count": sum(r["frame_label_count"] for r in records.values()),
            "sprites": [records[k] for k in sorted(records)],
            "interpretation": "Sprite structure only. No original plot, NPC, map, or battle semantics verified."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("swf")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = index_sprites(args.swf)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Sprite timelines: {} definitions, {} actions, {} frame labels, {} init actions".format(
        report["sprite_count"], report["sprite_action_tag_count"],
        report["sprite_frame_label_count"], report["root_init_action_tag_count"]))


if __name__ == "__main__":
    main()
