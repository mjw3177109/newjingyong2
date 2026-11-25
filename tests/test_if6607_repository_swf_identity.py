"""Verify private IF 6607 input identity against the actual checked-in SWF.

This test reads binary bytes only; it does not extract protected scripts or assets.
"""
import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "private_if6607_preflight", ROOT / "tools" / "private_if6607_preflight.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OriginalSWFIdentityTests(unittest.TestCase):
    def test_repository_swf_matches_private_review_gate(self):
        source = ROOT / "jin.swf"
        self.assertTrue(source.is_file(), "Original SWF missing; cannot verify review identity")
        actual = MODULE.sha256(source)
        self.assertEqual(
            actual, MODULE.EXPECTED_SWF,
            "SWF identity changed: stop IF 6607 review and re-baseline evidence",
        )

    def test_source_hash_is_sha256_hex(self):
        self.assertEqual(len(MODULE.EXPECTED_SWF), 64)
        self.assertTrue(all(ch in "0123456789abcdef" for ch in MODULE.EXPECTED_SWF))


if __name__ == "__main__":
    unittest.main()
