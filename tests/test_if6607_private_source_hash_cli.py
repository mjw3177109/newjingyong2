"""CLI regression tests for independent private SWF hashing; uses synthetic bytes only."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "validate_if6607_private_attestation.py"

class PrivateSourceHashCLITests(unittest.TestCase):
    def test_local_source_hash_match_and_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "synthetic.swf"
            source.write_bytes(b"synthetic-test-data-not-a-real-swf")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            record = {
                "candidate_id": "root-f55-doaction9-if6607",
                "source_sha256": digest,
                "export_a_sha256": "a" * 64,
                "export_b_sha256": "a" * 64,
                "offset_verified": True,
                "stack_condition_verified": True,
                "true_path_verified": True,
                "false_path_verified": True,
                "independent_review_verified": True,
                "rights_evidence_ref": "private/rights-001",
            }
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(record), encoding="utf-8")
            def run(*args):
                return subprocess.run([sys.executable, str(TOOL), str(manifest), *args],
                                      capture_output=True, text=True, check=False)
            self.assertEqual(run("--source-swf", str(source)).returncode, 0)
            record["source_sha256"] = "b" * 64
            manifest.write_text(json.dumps(record), encoding="utf-8")
            mismatch = run("--source-swf", str(source))
            self.assertEqual(mismatch.returncode, 1)
            self.assertIn("source sha256 mismatch", mismatch.stdout)
            self.assertNotEqual(run("--source-swf", str(root / "missing.swf")).returncode, 0)
            self.assertNotEqual(run("--source-swf", str(source),
                                    "--expected-source-sha256", digest).returncode, 0)

if __name__ == "__main__":
    unittest.main()
