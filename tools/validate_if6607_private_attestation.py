#!/usr/bin/env python3
"""Validate a PRIVATE IF6607 review attestation; never publish source excerpts."""
import argparse
import json
import re
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = (
    "candidate_id", "source_sha256", "export_a_sha256", "export_b_sha256",
    "offset_verified", "stack_condition_verified", "true_path_verified",
    "false_path_verified", "independent_review_verified",
    "rights_evidence_ref",
)
ALLOWED = set(REQUIRED) | {"status"}
EXPECTED_CANDIDATE = "root-f55-doaction9-if6607"

def validate(record, expected_source_sha256=None):
    errors = []
    if not isinstance(record, dict):
        return ["manifest must be an object"]
    if expected_source_sha256 is not None and (not isinstance(expected_source_sha256, str) or not SHA.fullmatch(expected_source_sha256)):
        return ["invalid expected source sha256"]
    extra = set(record) - ALLOWED
    if extra:
        errors.append("unknown fields: " + ", ".join(sorted(extra)))
    for key in REQUIRED:
        if key not in record:
            errors.append("missing " + key)
    if record.get("candidate_id") != EXPECTED_CANDIDATE:
        errors.append("candidate_id mismatch")
    for key in ("source_sha256", "export_a_sha256", "export_b_sha256"):
        if not isinstance(record.get(key), str) or not SHA.fullmatch(record[key]):
            errors.append("invalid " + key)
    if expected_source_sha256 is not None and record.get("source_sha256") != expected_source_sha256:
        errors.append("source sha256 mismatch")
    if record.get("export_a_sha256") != record.get("export_b_sha256"):
        errors.append("export hashes differ")
    for key in ("offset_verified", "stack_condition_verified", "true_path_verified",
                "false_path_verified", "independent_review_verified"):
        if record.get(key) is not True:
            errors.append("not verified: " + key)
    ref = record.get("rights_evidence_ref")
    if (not isinstance(ref, str) or len(ref) > 120 or not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", ref)
            or any(part in ("", ".", "..") for part in ref.split("/"))):
        errors.append("rights evidence reference missing or unsafe")
    if record.get("status") not in (None, "private_review_complete"):
        errors.append("invalid status")
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--expected-source-sha256", help="SHA-256 independently measured from the private source SWF")
    args = parser.parse_args()
    try:
        record = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        parser.exit(2, "cannot read JSON manifest: " + str(exc) + "\n")
    errors = validate(record, expected_source_sha256=args.expected_source_sha256)
    if errors:
        for error in errors:
            print("BLOCKED:", error)
        return 1
    print("PRIVATE_ATTESTATION_FIELDS_VALID (not proof of event semantics or rights)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
