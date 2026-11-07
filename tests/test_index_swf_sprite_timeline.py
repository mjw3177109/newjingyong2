"""Synthetic SWF fixtures only; no third-party content."""
import importlib.util
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "index_swf_sprite_timeline.py"
spec = importlib.util.spec_from_file_location("sprite_index", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def tag(code, body=b""):
    if len(body) < 63:
        return struct.pack("<H", (code << 6) | len(body)) + body
    return struct.pack("<HI", (code << 6) | 63, len(body)) + body


def swf(tags, compressed=False):
    body = b"\x08\x00" + struct.pack("<HH", 12 * 256, 1) + tags
    data = b"FWS" + bytes([8]) + struct.pack("<I", 8 + len(body)) + body
    return b"CWS" + data[3:8] + zlib.compress(body) if compressed else data


def sprite(sid, tags, frames=1):
    return tag(39, struct.pack("<HH", sid, frames) + tags)


class SpriteEvidenceTests(unittest.TestCase):
    def scan(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-name.swf"
            path.write_bytes(data)
            return mod.index_sprites(path)

    def test_sprite_frames_and_init_action_are_source_free(self):
        timeline = tag(43, b"secret-label\0") + tag(12, b"secret-code") + tag(1) + tag(0)
        root = sprite(7, timeline) + tag(59, struct.pack("<H", 7) + b"secret-init") + tag(1) + tag(0)
        report = self.scan(swf(root))
        self.assertEqual(report["sprite_count"], 1)
        self.assertEqual(report["root_showframe_tags"], 1)
        self.assertEqual(report["sprite_action_tag_count"], 1)
        self.assertEqual(report["root_init_action_tag_count"], 1)
        self.assertEqual(report["sprites"][0]["root_init_action_count"], 1)
        self.assertTrue(report["sprites"][0]["frame_count_matches"])
        self.assertEqual(report["sprites"][0]["evidence_frames"][0]["frame"], 1)
        self.assertNotIn("secret", str(report))
        self.assertNotIn("private-name", str(report))

    def test_compressed_matches_uncompressed(self):
        root = sprite(2, tag(12, b"a") + tag(1) + tag(0)) + tag(1) + tag(0)
        a, b = self.scan(swf(root)), self.scan(swf(root, compressed=True))
        self.assertEqual(a["sprites"], b["sprites"])
        self.assertNotEqual(a["source_swf_sha256"], b["source_swf_sha256"])

    def test_missing_end_and_truncated_sprite_rejected(self):
        with self.assertRaises(ValueError):
            self.scan(swf(sprite(2, tag(12, b"a") + tag(1)) + tag(1) + tag(0)))
        with self.assertRaises(ValueError):
            self.scan(swf(tag(39, b"\x01") + tag(1) + tag(0)))
        with self.assertRaises(ValueError):
            self.scan(swf(tag(1)))

    def test_duplicate_ids_and_frame_mismatch(self):
        inner = tag(1) + tag(0)
        with self.assertRaises(ValueError):
            self.scan(swf(sprite(2, inner) + sprite(2, inner) + tag(1) + tag(0)))
        report = self.scan(swf(sprite(2, inner, frames=3) + tag(1) + tag(0)))
        self.assertEqual(report["sprites_with_frame_count_mismatch"], 1)

    def test_sprite_actions_not_mixed_with_root(self):
        root = tag(12, b"root") + sprite(3, tag(12, b"inner") + tag(1) + tag(0)) + tag(1) + tag(0)
        report = self.scan(swf(root))
        self.assertEqual(report["sprite_action_tag_count"], 1)
        self.assertEqual(report["root_init_action_tag_count"], 0)


if __name__ == "__main__":
    unittest.main()
