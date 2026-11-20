#!/usr/bin/env python3
"""Source-free AVM1 immediate-predecessor audit; no stack semantics inferred."""
import argparse
import json
from pathlib import Path
try:
    from tools.probe_if6607_structure import decode_records, extract_root_action, verify_source_fingerprint
except ModuleNotFoundError:
    from probe_if6607_structure import decode_records, extract_root_action, verify_source_fingerprint


def predecessor_audit(action, if_offset=6607, set_variable_offset=6622):
    records = decode_records(action)
    by_start = {start: (end, opcode) for start, end, opcode, _ in records}
    if by_start.get(if_offset, (None, None))[1] != 0x9D:
        raise ValueError("expected If instruction boundary missing")
    if by_start.get(set_variable_offset, (None, None))[1] != 0x1D:
        raise ValueError("expected SetVariable instruction boundary missing")

    def predecessors(target):
        return [{"offset": start, "opcode_hex": f"{opcode:02x}"}
                for start, end, opcode, _ in records if end == target]

    if_predecessors = predecessors(if_offset)
    set_predecessors = predecessors(set_variable_offset)
    return {
        "schema": "avm1-predecessor-boundary-v1",
        "scope": "static-only",
        "if_offset": if_offset,
        "if_immediate_predecessors": if_predecessors,
        "if_preceded_by_less2": any(p["opcode_hex"] == "48" for p in if_predecessors),
        "set_variable_offset": set_variable_offset,
        "set_variable_immediate_predecessors": set_predecessors,
        "set_variable_preceded_by_push": any(p["opcode_hex"] == "96" for p in set_predecessors),
        "condition_stack_origin": "unknown",
        "assignment_stack_origin": "unknown",
        "runtime_reachability": "unknown",
        "verified_story_events": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("swf")
    parser.add_argument("--out", required=True)
    parser.add_argument("--expected-swf-sha256", default="d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30")
    args = parser.parse_args()
    verify_source_fingerprint(args.swf, args.expected_swf_sha256)
    result = predecessor_audit(extract_root_action(args.swf, 55, 9))
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Instruction predecessor boundaries checked; runtime semantics remain unknown")


if __name__ == "__main__":
    main()
