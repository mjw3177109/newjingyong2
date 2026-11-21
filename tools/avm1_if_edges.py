"""Inspect AVM1 ActionIf (0x9D) and ActionJump (0x99) edges from an isolated action byte stream.

No SWF content is printed. Offsets are relative to the supplied action stream.
This is structural analysis only; it does not establish predicate or story semantics.
"""
import argparse
import json
import struct
from pathlib import Path


def inspect_actions(data: bytes):
    pos = 0
    boundaries = set()
    edges = []
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
        boundaries.add(start)
        if opcode in (0x9D, 0x99):
            if length != 2:
                name = "ActionIf" if opcode == 0x9D else "ActionJump"
                raise ValueError(f"invalid {name} payload at {start}")
            displacement = struct.unpack_from('<h', data, pos)[0]
            target = end + displacement
            edges.append({"offset": start, "fallthrough": end, "branch": target, "kind": "if" if opcode == 0x9D else "jump"})
        pos = end
        if opcode == 0:
            if pos != len(data):
                raise ValueError(f"trailing bytes after ActionEnd at {start}")
            break
    # The byte immediately after the final action is a valid terminal exit.
    # A branch to that offset must not be mislabeled as an invalid instruction.
    if pos == len(data):
        boundaries.add(pos)
    for edge in edges:
        edge["branch_on_action_boundary"] = edge["branch"] in boundaries
        edge["fallthrough_on_action_boundary"] = edge["fallthrough"] in boundaries
    return edges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action_stream', type=Path, help='Private raw AVM1 action stream (not a complete SWF)')
    parser.add_argument('--strict', action='store_true', help='Fail if a branch or fallthrough is not an action boundary')
    args = parser.parse_args()
    edges = inspect_actions(args.action_stream.read_bytes())
    print(json.dumps(edges, indent=2))
    if args.strict and any(not e['branch_on_action_boundary'] or not e['fallthrough_on_action_boundary'] for e in edges):
        parser.exit(1, 'invalid AVM1 control-flow edge detected\n')


if __name__ == '__main__':
    main()
