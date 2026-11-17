#!/usr/bin/env python3
"""Private IF 6607 review input gate. Does not parse or publish protected content."""
import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED_SWF = "d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30"

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def preflight(swf, jar, java_version, ffdec_version):
    if not swf.is_file() or not jar.is_file():
        raise ValueError("Required local SWF or FFDec jar missing")
    swf_hash = sha256(swf)
    if swf_hash != EXPECTED_SWF:
        raise ValueError("SWF SHA-256 differs from audited candidate; stop and re-baseline")
    if not java_version.strip() or not ffdec_version.strip():
        raise ValueError("Java and FFDec versions must be recorded")
    if not re.search(r"(?i)(?:\b1\.8(?:[._\s]|$)|\b(?:java|openjdk|jdk)\s*(?:version\s*)?[\x22\x27]?8(?:[.\s\x22\x27]|$))", java_version):
        raise ValueError("Java 8 required for reproducible FFDec review")
    return {
        "candidate": "root-frame55-doaction9-if6607",
        "source_sha256": swf_hash,
        "ffdec_jar_sha256": sha256(jar),
        "java_version": java_version.strip(),
        "ffdec_version": ffdec_version.strip(),
        "branch_target": 6623,
        "fallthrough": 6612,
        "condition_stack": "unknown",
        "true_branch_effect": "unknown",
        "false_branch_effect": "unknown",
        "semantic_review": "unverified",
        "ready_for_html5_mapping": False,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swf", type=Path, required=True)
    parser.add_argument("--ffdec-jar", type=Path, required=True)
    parser.add_argument("--java-version", required=True)
    parser.add_argument("--ffdec-version", required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="Private local JSON destination; do not commit")
    args = parser.parse_args()
    result = preflight(args.swf, args.ffdec_jar, args.java_version, args.ffdec_version)
    if args.output.exists():
        raise ValueError("Refusing to overwrite an existing review manifest")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print("Private input preflight passed; semantics remain unverified.")

if __name__ == "__main__":
    main()
