"""Validate source-free event audit records before promoting them to verified.

Input is a JSON array. This tool never reads or exports SWF script contents.
Usage: python3 tools/validate_story_audit.py path/to/private-redacted-records.json
"""
import json
import re
import sys
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
STATUSES = {"unverified", "partial", "verified", "blocked_export_drift"}
RIGHTS = {"unknown", "authorized", "restricted"}
REQUIRED = ("candidate_id", "swf_sha256", "export_pair_id", "timeline_and_frame",
            "script_sha256", "evidence_offset", "trigger_summary", "effect_summary",
            "negative_path_checked", "cross_check", "status", "html5_mapping", "rights_status")


def validate(records):
    errors = []
    if not isinstance(records, list):
        return ["root: expected JSON array"]
    seen = set()
    for i, row in enumerate(records):
        prefix = f"record[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: expected object")
            continue
        missing = [k for k in REQUIRED if k not in row]
        if missing:
            errors.append(f"{prefix}: missing fields {', '.join(missing)}")
            continue
        cid = row["candidate_id"]
        if not isinstance(cid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", cid):
            errors.append(f"{prefix}: invalid anonymous candidate_id")
        elif cid in seen:
            errors.append(f"{prefix}: duplicate candidate_id")
        else:
            seen.add(cid)
        if row["status"] not in STATUSES or row["rights_status"] not in RIGHTS:
            errors.append(f"{prefix}: invalid status or rights_status")
            continue
        for key in ("swf_sha256", "script_sha256"):
            if not isinstance(row[key], str) or not HEX64.fullmatch(row[key]):
                errors.append(f"{prefix}: invalid {key}")
        if row["negative_path_checked"] not in (True, False):
            errors.append(f"{prefix}: negative_path_checked must be boolean")
        if row["status"] == "verified":
            for key in ("export_pair_id", "timeline_and_frame", "evidence_offset",
                        "trigger_summary", "effect_summary", "cross_check"):
                if not isinstance(row[key], str) or not row[key].strip() or row[key].strip().lower() in ("unknown", "none"):
                    errors.append(f"{prefix}: verified requires {key}")
            if row["negative_path_checked"] is not True:
                errors.append(f"{prefix}: verified requires negative-path evidence")
        elif row["html5_mapping"] not in (None, "none"):
            errors.append(f"{prefix}: unverified candidate cannot claim HTML5 mapping")
        if row["rights_status"] != "authorized" and row.get("publication_ready", False):
            errors.append(f"{prefix}: publication requires separate authorization")
    return errors


def main(argv):
    if len(argv) != 2:
        print("Usage: validate_story_audit.py <redacted-json>", file=sys.stderr)
        return 2
    try:
        records = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    errors = validate(records)
    for error in errors:
        print(error, file=sys.stderr)
    print(f"Audit validation: {'FAIL' if errors else 'PASS'}; records={len(records) if isinstance(records, list) else 0}; errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
