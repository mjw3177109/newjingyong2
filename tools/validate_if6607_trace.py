#!/usr/bin/env python3
"""Validate private IF6607 AVM1 dual-branch trace metadata (not semantics).

Usage: python tools/validate_if6607_trace.py PRIVATE_TRACE_JSON
Keep the input private; never commit reverse-engineered source or traces.
"""
import json
import re
import sys
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = {"swf_sha256", "ffdec_version", "java_version", "export_batch",
            "frame", "doaction_index", "if_offset", "fallthrough_offset",
            "jump_offset", "condition_stack", "branches",
            "independent_reviewer", "rights_review"}

def validate(doc):
    errors = []
    if not isinstance(doc, dict):
        return ["root must be object"]
    missing = REQUIRED - doc.keys()
    if missing:
        errors.append("missing fields: " + ", ".join(sorted(missing)))
    if not SHA256.fullmatch(str(doc.get("swf_sha256", ""))):
        errors.append("swf_sha256 must be 64 lowercase hex digits")
    for field, value in (("frame", 55), ("doaction_index", 9),
                         ("if_offset", 6607), ("fallthrough_offset", 6612),
                         ("jump_offset", 6623)):
        if type(doc.get(field)) is not int or doc[field] != value:
            errors.append(f"{field} must equal {value}")
    for field in ("ffdec_version", "java_version", "export_batch"):
        if not isinstance(doc.get(field), str) or not doc[field].strip():
            errors.append(f"{field} must be nonempty")
    stack = doc.get("condition_stack")
    if (not isinstance(stack, dict) or stack.get("status") not in ("resolved", "unresolved")
            or (stack.get("status") == "resolved" and not SHA256.fullmatch(str(stack.get("evidence_sha256", ""))))
            or (stack.get("status") == "unresolved" and stack.get("evidence_sha256") not in (None, ""))):
        errors.append("condition_stack requires status and evidence_sha256")
    branches = doc.get("branches")
    if not isinstance(branches, dict) or set(branches) != {"true", "false"}:
        errors.append("branches must contain exactly true and false")
    else:
        for name in ("true", "false"):
            b = branches[name]
            if (not isinstance(b, dict)
                    or b.get("status") not in ("reproduced", "unresolved")
                    or (b.get("status") == "reproduced" and not SHA256.fullmatch(str(b.get("trace_sha256", ""))))
                    or (b.get("status") == "unresolved" and b.get("trace_sha256") not in (None, ""))
                    or not isinstance(b.get("state_delta_summary"), str)
                    or not b["state_delta_summary"].strip()):
                errors.append(f"branches.{name} requires status, trace_sha256, state_delta_summary")
    for field in ("independent_reviewer", "rights_review"):
        v = doc.get(field)
        if not isinstance(v, dict) or v.get("status") not in ("pending", "verified"):
            errors.append(f"{field} requires status pending/verified")
    return errors

def main(argv):
    if len(argv) != 2:
        print("usage: validate_if6607_trace.py PRIVATE_TRACE_JSON", file=sys.stderr)
        return 2
    try:
        doc = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    errors = validate(doc)
    if errors:
        print("INVALID metadata: " + "; ".join(errors))
        return 1
    print("Metadata shape valid; semantic verification and publication rights NOT established")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
