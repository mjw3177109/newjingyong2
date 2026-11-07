"""Inventory ActionPush payloads and branch edges in an isolated AVM1 stream.

This reports structural evidence only. It does not execute stack operations,
resolve variables, or infer original-game event semantics.
"""
import argparse
import json
from pathlib import Path

from tools.avm1_if_edges import inspect_actions
from tools.avm1_push_literals import decode_push_literals


def inspect_stream(data: bytes):
    edges = inspect_actions(data)
    pushes = []
    pos = 0
    while pos < len(data):
        start = pos
        opcode = data[pos]
        pos += 1
        length = 0
        if opcode >= 0x80:
            if pos + 2 > len(data):
                raise ValueError(f"truncated action length at {start}")
            length = int.from_bytes(data[pos:pos + 2], "little")
            pos += 2
        end = pos + length
        if end > len(data):
            raise ValueError(f"truncated action payload at {start}")
        if opcode == 0x96:
            try:
                values = decode_push_literals(data[pos:end])
            except ValueError as exc:
                raise ValueError(f"ActionPush at offset {start}: {exc}") from exc
            pushes.append({"offset": start, "values": values})
        pos = end
        if opcode == 0:
            break
    return {"pushes": pushes, "edges": edges}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action_stream", type=Path, help="Private raw AVM1 action stream, not SWF")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = inspect_stream(args.action_stream.read_bytes())
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.strict and any(
        not edge["branch_on_action_boundary"] or not edge["fallthrough_on_action_boundary"]
        for edge in report["edges"]
    ):
        parser.exit(1, "invalid AVM1 control-flow edge detected\n")


if __name__ == "__main__":
    main()
