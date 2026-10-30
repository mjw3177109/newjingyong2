"""Synthetic SWF fixtures only; no original protected scripts or graphics."""
import importlib.util
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "index_swf_timeline.py"
spec = importlib.util.spec_from_file_location("index_swf_timeline", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def tag(code, payload=b""):
    n = len(payload)
    if n < 63:
        return struct.pack("<H", (code << 6) | n) + payload
    return struct.pack("<HI", (code << 6) | 63, n) + payload

def swf(tags, compressed=False, frames=2):
    # Minimal 1-bit RECT, 12 fps, two frames.
    body = b"\\x08\\x00" + struct.pack("<HH", 12 * 256, frames) + tags
    raw = b"FWS" + bytes([8]) + struct.pack("<I", 8 + len(body)) + body
    return raw[:3].replace(b"FWS", b"CWS") + raw[3:8] + zlib.compress(body) if compressed else raw

class TimelineEvidenceTests(unittest.TestCase):
    def scan(self, payload):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "fixture.swf"
            p.write_bytes(payload)
            return mod.index_timeline(p)

    def test_main_timeline_positions_and_source_free_output(self):
        body = tag(43, b"private-scene-name\\x00") + tag(12, b"private-script-bytes")
        body += tag(1) + tag(12, b"another-script") + tag(1) + tag(0)
        report = self.scan(swf(body))
        self.assertEqual(report["observed_showframe_tags"], 2)
        self.assertTrue(report["main_timeline_frame_count_matches"])
        self.assertEqual(report["main_timeline_action_tags"], 2)
        self.assertEqual(report["main_timeline_frame_labels"], 1)
        self.assertEqual([x["frame"] for x in report["evidence_frames"]], [1, 2])
        self.assertEqual(report["evidence_frames"][0]["frame_label_count"], 1)
        self.assertNotIn("private-", str(report))
        self.assertNotIn("fixture.swf", str(report))

    def test_compressed_and_uncompressed_have_same_frame_evidence(self):
        tags = tag(12, b"abc") + tag(1) + tag(43, b"label\\x00") + tag(1) + tag(0)
        a = self.scan(swf(tags))
        b = self.scan(swf(tags, compressed=True))
        self.assertEqual(a["evidence_frames"], b["evidence_frames"])
        self.assertNotEqual(a["source_swf_sha256"], b["source_swf_sha256"])

    def test_nested_sprite_actions_not_misreported_as_main_timeline(self):
        nested = struct.pack("<HH", 5, 1) + tag(12, b"nested") + tag(1) + tag(0)
        tags = tag(39, nested) + tag(1) + tag(1) + tag(0)
        report = self.scan(swf(tags))
        self.assertEqual(report["main_timeline_action_tags"], 0)
        self.assertEqual(report["evidence_frame_count"], 0)

    def test_truncated_and_missing_end_fail_closed(self):
        with self.assertRaises(ValueError):
            self.scan(swf(tag(12, b"ok") + tag(1)))
        with self.assertRaises(ValueError):
            self.scan(swf(tag(12, b"ok") + tag(1) + tag(0))[:-2])
        with self.assertRaises(ValueError):
            self.scan(b"not a swf")

if __name__ == "__main__":
    unittest.main()
