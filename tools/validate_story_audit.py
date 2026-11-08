"""Validate source-free event audit records before promoting them to verified.

Input is a JSON array. This tool never reads or exports SWF script contents.
Usage: python3 tools/validate_story_audit.py path/to/private-redacted-records.json
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
STATUSES = {"unverified", "partial", "verified", "blocked_export_drift"}
RIGHTS = {"unknown", "authorized", "restricted"}
RIGHTS_SCOPES = {"none", "analysis_only", "adaptation_only", "distribution_only",
                 "adaptation_and_distribution"}
PLACEHOLDERS = {"unknown", "none", "n/a", "na", "tbd", "todo", "pending",
                "not checked", "not verified"}
REQUIRED = ("candidate_id", "swf_sha256", "export_pair_id", "timeline_and_frame",
            "script_sha256", "evidence_offset", "trigger_summary", "effect_summary",
            "negative_path_checked", "cross_check", "status", "html5_mapping",
            "rights_status", "rights_scope", "rights_evidence_ref")
ALLOWED = set(REQUIRED) | {"publication_ready"}
TEXT_LIMITS = {
    "export_pair_id": 100,
    "timeline_and_frame": 160,
    "evidence_offset": 160,
    "trigger_summary": 240,
    "effect_summary": 240,
    "cross_check": 240,
    "rights_evidence_ref": 240,
}


def _usable_text(value):
    return (isinstance(value, str) and bool(value.strip())
            and len(value) <= 240 and not any(unicodedata.category(ch) in {"Cc", "Cf", "Zl", "Zp"} for ch in value))


def _is_placeholder(value):
    return isinstance(value, str) and value.strip().lower() in PLACEHOLDERS


def validate(records):
    errors = []
    if not isinstance(records, list):
        return ["root: expected JSON array"]
    seen = set()
    published_mappings = set()
    export_pair_sources = {}
    for i, row in enumerate(records):
        prefix = f"record[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: expected object")
            continue
        extra = sorted(str(key) for key in set(row) - ALLOWED)
        if extra:
            errors.append(f"{prefix}: unexpected fields {', '.join(extra)}")
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
        if (not isinstance(row["status"], str) or row["status"] not in STATUSES
                or not isinstance(row["rights_status"], str)
                or row["rights_status"] not in RIGHTS):
            errors.append(f"{prefix}: invalid status or rights_status")
            continue
        pair = row["export_pair_id"]
        swf_digest = row["swf_sha256"]
        if (isinstance(pair, str) and pair.strip() and isinstance(swf_digest, str)
                and HEX64.fullmatch(swf_digest)):
            prior = export_pair_sources.setdefault(pair, swf_digest.lower())
            if prior != swf_digest.lower():
                errors.append(f"{prefix}: export_pair_id refers to conflicting SWF digests")
        for key in ("swf_sha256", "script_sha256"):
            if not isinstance(row[key], str) or not HEX64.fullmatch(row[key]):
                errors.append(f"{prefix}: invalid {key}")
        if not isinstance(row["negative_path_checked"], bool):
            errors.append(f"{prefix}: negative_path_checked must be boolean")
        mapping = row["html5_mapping"]
        if not (mapping is None or (isinstance(mapping, str) and
                re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,99}", mapping))):
            errors.append(f"{prefix}: html5_mapping must be null or a short safe event ID")
        for key, limit in TEXT_LIMITS.items():
            value = row[key]
            if value is not None and (
                not isinstance(value, str) or not value.strip()
                or len(value) > limit or any(unicodedata.category(ch) in {"Cc", "Cf", "Zl", "Zp"} for ch in value)
            ):
                errors.append(f"{prefix}: {key} must be a short single-line string or null")
        if (not isinstance(row["rights_scope"], str)
                or row["rights_scope"] not in RIGHTS_SCOPES):
            errors.append(f"{prefix}: invalid rights_scope")
        if row["rights_status"] == "unknown":
            if row["rights_scope"] != "none" or row["rights_evidence_ref"] is not None:
                errors.append(f"{prefix}: unknown rights require scope none and no evidence reference")
        elif row["rights_status"] == "restricted":
            if (isinstance(row["rights_scope"], str)
                    and row["rights_scope"] not in {"none", "analysis_only"}):
                errors.append(f"{prefix}: restricted rights cannot claim adaptation or distribution scope")
        elif row["rights_status"] == "authorized":
            if not _usable_text(row["rights_evidence_ref"]) or _is_placeholder(row["rights_evidence_ref"]):
                errors.append(f"{prefix}: authorized rights require a concrete rights_evidence_ref")
            if row["rights_scope"] == "none":
                errors.append(f"{prefix}: authorized rights require an explicit rights_scope")
        for key in ("export_pair_id", "timeline_and_frame", "evidence_offset",
                    "trigger_summary", "effect_summary", "cross_check"):
            if row[key] is not None and not isinstance(row[key], str):
                errors.append(f"{prefix}: {key} must be string or null")
        if row["status"] == "verified":
            for key in ("export_pair_id", "timeline_and_frame", "evidence_offset",
                        "trigger_summary", "effect_summary", "cross_check"):
                if not isinstance(row[key], str) or not row[key].strip() or _is_placeholder(row[key]):
                    errors.append(f"{prefix}: verified requires {key}")
            if row["negative_path_checked"] is not True:
                errors.append(f"{prefix}: verified requires negative-path evidence")
        else:
            mapping = row["html5_mapping"]
            if not (mapping is None or
                    (isinstance(mapping, str) and mapping == "none")):
                errors.append(f"{prefix}: unverified candidate cannot claim HTML5 mapping")
        if "publication_ready" in row and not isinstance(row["publication_ready"], bool):
            errors.append(f"{prefix}: publication_ready must be boolean")
        if row.get("publication_ready") is True:
            if isinstance(mapping, str) and mapping not in PLACEHOLDERS and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,99}", mapping):
                if mapping in published_mappings:
                    errors.append(f"{prefix}: duplicate publication HTML5 mapping")
                published_mappings.add(mapping)
            if row["rights_status"] != "authorized":
                errors.append(f"{prefix}: publication requires separate authorization")
            if row["rights_scope"] != "adaptation_and_distribution":
                errors.append(f"{prefix}: publication requires adaptation_and_distribution scope")
            if not _usable_text(row["rights_evidence_ref"]) or _is_placeholder(row["rights_evidence_ref"]):
                errors.append(f"{prefix}: publication requires a concrete rights evidence reference")
            if row["status"] != "verified":
                errors.append(f"{prefix}: publication requires verified evidence")
            if not isinstance(row["html5_mapping"], str) or row["html5_mapping"].strip().lower() in (PLACEHOLDERS | {""}):
                errors.append(f"{prefix}: publication requires a concrete HTML5 mapping")
    return errors


def _reject_duplicate_keys(pairs):
    """Reject ambiguous JSON objects instead of silently keeping the last value."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main(argv):
    if len(argv) != 2:
        print("Usage: validate_story_audit.py <redacted-json>", file=sys.stderr)
        return 2
    try:
        records = json.loads(Path(argv[1]).read_text(encoding="utf-8"),
                             object_pairs_hook=_reject_duplicate_keys)
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
