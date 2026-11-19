#!/usr/bin/env python3
"""Inspect one root DoAction IF structurally; never export SWF source or literals."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

try:
    from tools.index_swf_sprite_timeline import load_swf, iter_tags
except ModuleNotFoundError:
    from index_swf_sprite_timeline import load_swf, iter_tags


def decode_records(payload):
    records = []
    offset = 0
    while offset < len(payload):
        start = offset
        op = payload[offset]
        offset += 1
        if op == 0:
            records.append((start, offset, op, None))
            break
        size = 0
        if op >= 0x80:
            if offset + 2 > len(payload):
                raise ValueError("truncated action length")
            size = struct.unpack_from("<H", payload, offset)[0]
            offset += 2
            if offset + size > len(payload):
                raise ValueError("truncated action body")
        body = offset
        offset += size
        records.append((start, offset, op, body if op >= 0x80 else None))
    if not records or records[-1][2] != 0 or records[-1][1] != len(payload):
        raise ValueError("action stream must end with a single terminal End action")
    return records


def inspect_target(payload, target=6607):
    records = decode_records(payload)
    by_offset = {r[0]: r for r in records}
    if target not in by_offset:
        raise ValueError("target not an action boundary")
    start, end, opcode, body = by_offset[target]
    if opcode != 0x9D or end - start != 5:
        raise ValueError("target not a five-byte AVM1 IF")
    displacement = struct.unpack_from("<h", payload, body)[0]
    branch = end + displacement
    if end not in by_offset:
        raise ValueError("fallthrough not an action boundary")
    if branch not in by_offset:
        raise ValueError("branch target not an action boundary")
    index = next(i for i, r in enumerate(records) if r[0] == target)
    window = records[max(0, index - 12):index + 1]
    # Opcode-only window: no operands, source strings, paths or decoded script.
    return {
        "schema": "avm1-if-structure-v1",
        "action_sha256": hashlib.sha256(payload).hexdigest(),
        "if_offset": target,
        "fallthrough_offset": end,
        "branch_offset": branch,
        "relative_displacement": displacement,
        "prior_opcode_window": [{"offset": r[0], "opcode_hex": f"{r[2]:02x}"} for r in window],
        "condition_stack_origin": "unknown",
        "true_path_effects": "unknown",
        "false_path_effects": "unknown",
        "verified_story_events": 0,
    }


def extract_root_action(path, frame=55, tag_ordinal=9):
    _, data, start = load_swf(path)
    current_frame = 1
    ordinal = 0
    for code, payload in iter_tags(data, start, len(data)):
        if code == 1:
            current_frame += 1
        elif code == 12:
            ordinal += 1
            if ordinal == tag_ordinal:
                if current_frame != frame:
                    raise ValueError("root action ordinal does not match expected frame")
                return payload
    raise ValueError("root action not found")


def verify_source_fingerprint(path, expected_sha256):
    """Fail closed if the input SWF differs from the audited original."""
    actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual.lower() != expected_sha256.lower():
        raise ValueError("SWF SHA-256 does not match audited source")
    return actual


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("swf")
    parser.add_argument("--out", required=True)
    parser.add_argument("--expected-swf-sha256", default="d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30")
    parser.add_argument("--frame", type=int, default=55)
    parser.add_argument("--action", type=int, default=9)
    parser.add_argument("--offset", type=int, default=6607)
    args = parser.parse_args()
    source_hash = verify_source_fingerprint(args.swf, args.expected_swf_sha256)
    report = inspect_target(extract_root_action(args.swf, args.frame, args.action), args.offset)
    report["root_frame"] = args.frame
    report["root_doaction_tag_ordinal"] = args.action
    report["source_swf_sha256"] = source_hash
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("IF structure checked; condition and both effects remain unknown")


if __name__ == "__main__":
    main()
