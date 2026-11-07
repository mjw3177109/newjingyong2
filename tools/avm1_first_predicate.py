"""Conservative linear ActionIf predicate evidence from isolated AVM1 bytes.

Stops at the first branch. Never follows paths or infers story semantics.
Supports ActionPush, boolean ActionNot, and ActionIf/ActionJump/ActionEnd before stop.
"""
from tools.avm1_action_inventory import inspect_stream
from tools.avm1_push_literals import decode_push_literals


def inspect_first_branch(data: bytes):
    inventory = inspect_stream(data)  # validates complete stream and branch boundaries
    stack = []
    pos = 0
    while pos < len(data):
        start = pos
        opcode = data[pos]
        pos += 1
        length = 0
        if opcode >= 0x80:
            if pos + 2 > len(data):
                raise ValueError("truncated action length")
            length = int.from_bytes(data[pos:pos + 2], "little")
            pos += 2
        end = pos + length
        if end > len(data):
            raise ValueError("truncated action payload")
        if opcode == 0x96:
            stack.extend(decode_push_literals(data[pos:end]))
        elif opcode == 0x12:  # ActionNot: only a known boolean is safe to fold
            if not stack:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            operand = stack.pop()
            if operand["type"] != "boolean":
                return {"status": "unknown", "reason": "unresolved_not_operand",
                        "offset": start, "operand": operand}
            stack.append({"type": "boolean", "value": not operand["value"]})
        elif opcode == 0x9D:
            edge = next(e for e in inventory["edges"] if e["offset"] == start)
            if not edge["branch_on_action_boundary"] or not edge["fallthrough_on_action_boundary"]:
                raise ValueError("invalid branch boundary")
            if not stack:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            predicate = stack.pop()
            if predicate["type"] in ("register", "constant_index"):
                return {"status": "unknown", "reason": "unresolved_push_reference",
                        "offset": start, "predicate": predicate,
                        "note": "Register/constant-pool value requires runtime context"}
            return {"status": "literal_candidate", "offset": start,
                    "predicate": predicate, "branch": edge["branch"],
                    "fallthrough": edge["fallthrough"],
                    "note": "Literal stack value only; not a verified event condition"}
        elif opcode == 0x99:
            return {"status": "unknown", "reason": "jump_before_if", "offset": start}
        elif opcode == 0:
            break
        else:
            return {"status": "unknown", "reason": "unsupported_opcode", "offset": start,
                    "opcode": opcode}
        pos = end
    return {"status": "unknown", "reason": "no_if"}
