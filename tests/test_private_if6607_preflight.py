"""Synthetic-only tests for private IF 6607 input gate; no protected SWF content."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "private_if6607_preflight", ROOT / "tools" / "private_if6607_preflight.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrivateIF6607PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.swf = root / "synthetic.swf"
        self.jar = root / "synthetic.jar"
        self.swf.write_bytes(b"synthetic SWF fixture, not an original game")
        self.jar.write_bytes(b"synthetic FFDec jar fixture")
        self.swf_hash = hashlib.sha256(self.swf.read_bytes()).hexdigest()

    def test_valid_synthetic_inputs_never_claim_semantic_verification(self):
        with patch.object(MODULE, "EXPECTED_SWF", self.swf_hash):
            result = MODULE.preflight(self.swf, self.jar, "Java 8", "FFDec test")
        self.assertEqual(result["source_sha256"], self.swf_hash)
        self.assertEqual(result["ffdec_jar_sha256"],
                         hashlib.sha256(self.jar.read_bytes()).hexdigest())
        self.assertEqual(result["condition_stack"], "unknown")
        self.assertEqual(result["true_branch_effect"], "unknown")
        self.assertEqual(result["false_branch_effect"], "unknown")
        self.assertEqual(result["semantic_review"], "unverified")
        self.assertIs(result["ready_for_html5_mapping"], False)

    def test_rejects_wrong_swf_fingerprint(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            MODULE.preflight(self.swf, self.jar, "Java 8", "FFDec test")

    def test_rejects_missing_inputs(self):
        with patch.object(MODULE, "EXPECTED_SWF", self.swf_hash):
            for missing in (self.swf, self.jar):
                with self.subTest(missing=missing.name):
                    with self.assertRaisesRegex(ValueError, "missing"):
                        MODULE.preflight(missing.with_name("absent"), self.jar
                                         if missing == self.swf else missing.with_name("absent"),
                                         "Java 8", "FFDec test")

    def test_requires_java_8_for_legacy_ffdec(self):
        with patch.object(MODULE, "EXPECTED_SWF", self.swf_hash):
            for version in ("Java 17", "openjdk version \"21.0.2\"", "Java 18"):
                with self.subTest(version=version):
                    with self.assertRaisesRegex(ValueError, "Java 8"):
                        MODULE.preflight(self.swf, self.jar, version, "FFDec test")
            for version in ("Java 8", "openjdk version \"1.8.0_402\""):
                with self.subTest(version=version):
                    self.assertEqual(MODULE.preflight(self.swf, self.jar, version, "FFDec test")["semantic_review"], "unverified")

    def test_rejects_ambiguous_or_embedded_java_version(self):
        with patch.object(MODULE, "EXPECTED_SWF", self.swf_hash):
            for version in ("Java 8 compatibility; runtime Java 21",
                            "Java 17 (Java 8 supported)",
                            "openjdk version \"21.0.2\"; Java 8",
                            "Java 8; unknown runtime"):
                with self.subTest(version=version):
                    with self.assertRaisesRegex(ValueError, "Java 8"):
                        MODULE.preflight(self.swf, self.jar, version, "FFDec test")

    def test_rejects_blank_version_metadata(self):
        with patch.object(MODULE, "EXPECTED_SWF", self.swf_hash):
            for java, ffdec in (("", "FFDec"), ("Java 8", "  ")):
                with self.subTest(java=java, ffdec=ffdec):
                    with self.assertRaisesRegex(ValueError, "versions"):
                        MODULE.preflight(self.swf, self.jar, java, ffdec)


if __name__ == "__main__":
    unittest.main()
