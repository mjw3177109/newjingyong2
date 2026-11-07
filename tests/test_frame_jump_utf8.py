"""Regression: malformed FFDec exports must not produce silently altered syntax evidence."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_frame_jump_evidence import build_frame_jump_evidence


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FrameJumpUtf8Tests(unittest.TestCase):
    def test_invalid_utf8_is_rejected_before_syntax_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            scripts = base / "scripts"
            scripts.mkdir()
            swf = base / "jin.swf"
            swf.write_bytes(b"synthetic-swf-not-original")
            raw = b"gotoAndPlay(55);\xff"
            (scripts / "action.as").write_bytes(raw)
            swf_hash = sha(swf.read_bytes())
            path_hash = sha(b"action.as")
            content_hash = sha(raw)
            candidate = "SRC-" + sha((swf_hash + ":" + path_hash + ":" + content_hash).encode("ascii"))[:20]
            queue = {
                "schema_version": 1,
                "source_swf_sha256": swf_hash,
                "indexed_script_count": 1,
                "selected_count": 1,
                "candidates": [{
                    "path_sha256": path_hash,
                    "content_sha256": content_hash,
                    "candidate_id": candidate,
                    "semantic_status": "unverified",
                }],
            }
            with self.assertRaises(UnicodeDecodeError):
                build_frame_jump_evidence(scripts, swf, queue)


if __name__ == "__main__":
    unittest.main()
