"""Conservative linear ActionIf predicate evidence from isolated AVM1 bytes.

Stops at the first branch. Never follows paths or infers story semantics.
Supports ActionPush, ActionPop, stack operations, conservative boolean operations, and branches.
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
        elif opcode == 0x26:  # ActionTrace: consumes one value; does not change remaining stack
            if not stack:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            stack.pop()
        elif opcode == 0x17:  # ActionPop: discard top entry without inferring its value
            if not stack:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            stack.pop()
        elif opcode == 0x1C:  # ActionGetVariable: preserve name, never assume runtime value
            if not stack:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            name = stack.pop()
            if name["type"] != "string":
                return {"status": "unknown", "reason": "unresolved_variable_name",
                        "offset": start, "operand": name}
            stack.append({"type": "variable_reference", "name": name["value"]})
        elif opcode == 0x4C:  # ActionPushDuplicate: duplicate top stack entry
            if not stack:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            stack.append(stack[-1].copy())
        elif opcode == 0x4D:  # ActionStackSwap: exchange the top two entries
            if len(stack) < 2:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            stack[-1], stack[-2] = stack[-2], stack[-1]
        elif opcode == 0x44:  # ActionToBoolean: identity only for known booleans
            if not stack:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            operand = stack.pop()
            if operand["type"] != "boolean":
                return {"status": "unknown", "reason": "unresolved_to_boolean_operand",
                        "offset": start, "operand": operand}
            stack.append(operand)
        elif opcode == 0x12:  # ActionNot: only a known boolean is safe to fold
            if not stack:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            operand = stack.pop()
            if operand["type"] != "boolean":
                return {"status": "unknown", "reason": "unresolved_not_operand",
                        "offset": start, "operand": operand}
            stack.append({"type": "boolean", "value": not operand["value"]})
        elif opcode in (0x10, 0x11):  # ActionAnd / ActionOr: known booleans only
            if len(stack) < 2:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            right, left = stack.pop(), stack.pop()
            if left["type"] != "boolean" or right["type"] != "boolean":
                return {"status": "unknown", "reason": "unresolved_logical_operands",
                        "offset": start, "left": left, "right": right}
            result = (left["value"] and right["value"]) if opcode == 0x10 else (left["value"] or right["value"])
            stack.append({"type": "boolean", "value": result})
        elif opcode in (0x0E, 0x49, 0x66):  # Equals / Equals2 / StrictEquals: known booleans only
            if len(stack) < 2:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            right, left = stack.pop(), stack.pop()
            if left["type"] != "boolean" or right["type"] != "boolean":
                return {"status": "unknown", "reason": "unresolved_equals_operands",
                        "offset": start, "left": left, "right": right}
            stack.append({"type": "boolean", "value": left["value"] == right["value"]})
        elif opcode == 0x9D:
            edge = next(e for e in inventory["edges"] if e["offset"] == start)
            if not edge["branch_on_action_boundary"] or not edge["fallthrough_on_action_boundary"]:
                raise ValueError("invalid branch boundary")
            if not stack:
                return {"status": "unknown", "reason": "stack_underflow", "offset": start}
            predicate = stack.pop()
            if predicate["type"] != "boolean":
                return {"status": "unknown", "reason": "unresolved_push_reference",
                        "offset": start, "predicate": predicate,
                        "note": "Only known boolean literals are folded; other values require AVM1 coercion or runtime context"}
            return {"status": "literal_candidate", "offset": start,
                    "predicate": predicate, "branch": edge["branch"],
                    "fallthrough": edge["fallthrough"],
                    "note": "Literal stack value only; not a verified event condition"}
        elif opcode in (0x1D, 0x87, 0x3C, 0x41):  # SetVariable / StoreRegister / DefineLocal / DefineLocal2 mutate runtime state
            return {"status": "unknown", "reason": "state_mutation_before_if", "offset": start,
                    "opcode": opcode,
                    "note": "Cannot infer branch predicates across state changes without runtime context"}
        elif opcode in (0x3E, 0x2A):  # Return / Throw terminate linear execution before any later If
            return {"status": "unknown", "reason": "terminal_before_if", "offset": start,
                    "opcode": opcode}
        elif opcode == 0x99:
            return {"status": "unknown", "reason": "jump_before_if", "offset": start}
        elif opcode == 0:
            break
        else:
            return {"status": "unknown", "reason": "unsupported_opcode", "offset": start,
                    "opcode": opcode}
        pos = end
    return {"status": "unknown", "reason": "no_if"}
