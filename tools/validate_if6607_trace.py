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
    unknown = doc.keys() - REQUIRED
    if unknown:
        errors.append("unexpected top-level fields")
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
    if isinstance(stack, dict) and set(stack) != {"status", "evidence_sha256"}:
        errors.append("condition_stack has unexpected fields")
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
            if isinstance(b, dict) and set(b) != {"status", "trace_sha256", "state_delta_summary"}:
                errors.append(f"branches.{name} has unexpected fields")
            if (not isinstance(b, dict)
                    or b.get("status") not in ("reproduced", "unresolved")
                    or (b.get("status") == "reproduced" and not SHA256.fullmatch(str(b.get("trace_sha256", ""))))
                    or (b.get("status") == "unresolved" and b.get("trace_sha256") not in (None, ""))
                    or not isinstance(b.get("state_delta_summary"), str)
                    or not b["state_delta_summary"].strip()
                    or len(b["state_delta_summary"]) > 160
                    or any(ord(ch) < 32 or ord(ch) == 127 for ch in b["state_delta_summary"])
                    or (b.get("status") == "reproduced" and b["state_delta_summary"].strip().lower() in ("not examined", "unresolved", "unknown", "pending"))):
                errors.append(f"branches.{name} requires status, trace_sha256, state_delta_summary")
    # Two distinct branch executions must not reuse one trace artifact as proof.
    if isinstance(branches, dict) and all(
        isinstance(branches.get(name), dict) and branches[name].get("status") == "reproduced"
        for name in ("true", "false")
    ):
        true_hash = branches["true"].get("trace_sha256")
        false_hash = branches["false"].get("trace_sha256")
        if isinstance(true_hash, str) and SHA256.fullmatch(true_hash) and true_hash == false_hash:
            errors.append("true and false branches must have distinct trace_sha256")
    for field in ("independent_reviewer", "rights_review"):
        v = doc.get(field)
        if isinstance(v, dict) and set(v) != {"status"}:
            errors.append(f"{field} has unexpected fields")
        if not isinstance(v, dict) or v.get("status") not in ("pending", "verified"):
            errors.append(f"{field} requires status pending/verified")
    reviewer = doc.get("independent_reviewer")
    if isinstance(reviewer, dict) and reviewer.get("status") == "verified":
        if not isinstance(stack, dict) or stack.get("status") != "resolved" or not isinstance(branches, dict) or any(not isinstance(branches.get(name), dict) or branches[name].get("status") != "reproduced" for name in ("true", "false")):
            errors.append("independent review cannot be verified while condition or branches are unresolved")
    return errors

def main(argv):
    if len(argv) != 2:
        print("usage: validate_if6607_trace.py PRIVATE_TRACE_JSON", file=sys.stderr)
        return 2
    try:
        doc = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        # Never echo private trace paths or parser excerpts into CI logs.
        print("invalid input: cannot read or parse private trace JSON", file=sys.stderr)
        return 2
    errors = validate(doc)
    if errors:
        print("INVALID metadata: " + "; ".join(errors))
        return 1
    print("Metadata shape valid; semantic verification and publication rights NOT established")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
