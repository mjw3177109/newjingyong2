#!/usr/bin/env python3
"""Source-free AVM1 Push type inventory. Never exports literal values."""
import argparse
import json
from pathlib import Path
try:
    from tools.probe_if6607_structure import decode_records, extract_root_action, verify_source_fingerprint
except ModuleNotFoundError:
    from probe_if6607_structure import decode_records, extract_root_action, verify_source_fingerprint

TYPE_WIDTH = {0: None, 1: 4, 2: 0, 3: 0, 4: 1, 5: 1, 6: 8, 7: 4, 8: 1, 9: 2}


def push_types(data):
    """Validate complete Push encoding without exposing values."""
    result = []
    index = 0
    while index < len(data):
        typ = data[index]
        index += 1
        if typ not in TYPE_WIDTH:
            raise ValueError("unsupported Push value type")
        width = TYPE_WIDTH[typ]
        if width is None:
            terminator = data.find(b"\x00", index)
            if terminator < 0:
                raise ValueError("unterminated Push string")
            index = terminator + 1
        else:
            if index + width > len(data):
                raise ValueError("truncated Push value")
            index += width
        result.append(typ)
    return result


def inventory(action, offsets=(6612, 6623, 6629)):
    records = {start: (end, op, body) for start, end, op, body in decode_records(action)}
    # This is adjacency evidence only, not proof of a variable assignment.\n    if 6622 not in records or records[6622][1] != 0x1D:\n        raise ValueError("expected SetVariable boundary missing")\n    pushes = []\n    for offset in offsets:
        if offset not in records:
            raise ValueError("expected Push boundary missing")
        end, opcode, body = records[offset]
        if opcode != 0x96 or body is None:
            raise ValueError("expected Push opcode missing")
        pushes.append({"offset": offset, "push_type_codes": push_types(action[body:end]),
                       "literal_values_exported": False, "value_count": len(push_types(action[body:end]))})
    return {"schema": "avm1-push-types-v1", "scope": "static-only", "pushes": pushes,
            "set_variable_offset": 6622, "set_variable_opcode_confirmed": True,\n            "set_variable_target": "unknown", "set_variable_value": "unknown",\n            "condition_stack_origin": "unknown", "verified_story_events": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("swf")
    parser.add_argument("--out", required=True)
    parser.add_argument("--expected-swf-sha256",
                        default="d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30")
    args = parser.parse_args()
    verify_source_fingerprint(args.swf, args.expected_swf_sha256)
    result = inventory(extract_root_action(args.swf, 55, 9))
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Push type inventory completed; no values exported")


if __name__ == "__main__":
    main()
