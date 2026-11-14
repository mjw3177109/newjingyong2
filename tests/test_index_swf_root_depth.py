"""Synthetic-only root depth lifecycle tests; no original protected content."""
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.index_swf_root_depth import index_root_depth


def tag(code, payload=b""):
    return struct.pack("<H", code << 6 | len(payload)) + payload


def sprite(sid, inner=None):
    return tag(39, struct.pack("<HH", sid, 1) + (inner or tag(1) + tag(0)))


def swf(tags, compressed=False):
    body = b"\x08\x00" + struct.pack("<HH", 12 * 256, 3) + tags
    plain = b"FWS" + bytes([8]) + struct.pack("<I", len(body) + 8) + body
    return b"CWS" + plain[3:8] + zlib.compress(body) if compressed else plain


def place2(depth, sid=None, move=False):
    flags = (2 if sid is not None else 0) | (1 if move else 0)
    return tag(26, bytes([flags]) + struct.pack("<H", depth)
               + (struct.pack("<H", sid) if sid is not None else b""))


def place3(depth, sid=None, class_name=None):
    flags = 2 if sid is not None else 0
    flags2 = 8 if class_name is not None else 0
    body = bytes([flags, flags2]) + struct.pack("<H", depth)
    if class_name is not None:
        body += class_name + b"\0"
    if sid is not None:
        body += struct.pack("<H", sid)
    return tag(70, body)


class RootDepthTests(unittest.TestCase):
    def scan(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "secret.swf"
            path.write_bytes(content)
            return index_root_depth(path)

    def test_place_move_replace_remove_and_snapshot(self):
        tags = sprite(7) + sprite(8)
        tags += tag(4, struct.pack("<HH", 7, 2)) + tag(1)
        tags += place2(2, move=True) + place3(2, 8, b"secret-class") + tag(1)
        tags += tag(28, struct.pack("<H", 2)) + tag(1) + tag(0)
        r = self.scan(swf(tags))
        self.assertEqual(r["root_showframe_tags"], 3)
        self.assertEqual(r["sprite_character_assignment_tags"], 2)
        self.assertEqual(r["sprite_removal_tags"], 1)
        self.assertEqual(r["occupied_depth_assignment_tags"], 1)
        self.assertEqual(r["authored_frames_with_sprite_depths"], 2)
        self.assertEqual(r["max_sprite_depths_at_showframe"], 1)
        self.assertEqual(r["sprite_depth_transition_count"], 4)
        self.assertNotIn("secret-class", str(r))

    def test_removeobject_id_mismatch_preserves_depth(self):
        tags = sprite(7) + tag(4, struct.pack("<HH", 7, 4))
        tags += tag(5, struct.pack("<HH", 99, 4)) + tag(1)
        tags += tag(5, struct.pack("<HH", 7, 4)) + tag(1) + tag(0)
        r = self.scan(swf(tags))
        self.assertEqual(r["removeobject_character_mismatch_tags"], 1)
        self.assertEqual(r["remove_existing_depth_tags"], 1)
        self.assertEqual(r["authored_frames_with_sprite_depths"], 1)

    def test_non_sprite_depth_and_orphan_updates(self):
        tags = sprite(7) + tag(4, struct.pack("<HH", 99, 3))
        tags += place2(3, move=True) + place2(5, move=True)
        tags += place2(7, sid=7, move=True) + tag(28, struct.pack("<H", 6))
        tags += tag(1) + tag(0)
        r = self.scan(swf(tags))
        self.assertEqual(r["no_character_existing_depth_tags"], 1)
        self.assertEqual(r["no_character_missing_depth_tags"], 1)
        self.assertEqual(r["move_with_character_missing_depth_tags"], 1)
        self.assertEqual(r["remove_missing_depth_tags"], 1)
        self.assertEqual(r["max_total_depths_at_showframe"], 2)

    def test_compressed_matches_plain_and_nested_ignored(self):
        nested = tag(4, struct.pack("<HH", 7, 2)) + tag(1) + tag(0)
        tags = sprite(7) + sprite(8, nested) + place3(4, 7) + tag(1) + tag(0)
        a = self.scan(swf(tags))
        b = self.scan(swf(tags, True))
        self.assertEqual(a["sprite_depth_transitions"], b["sprite_depth_transitions"])
        self.assertEqual(a["sprite_character_assignment_tags"], 1)
        self.assertNotEqual(a["source_swf_sha256"], b["source_swf_sha256"])

    def test_truncated_and_invalid_tags_fail_closed(self):
        for bad in (tag(4, b"\x01"), tag(26, b"\x02\x03\x00"),
                    tag(70, b"\x02\x08\x01\x00\x41"),
                    tag(70, b"\x00\x08\x01\x00\x41"),
                    tag(5, b"\x01"), tag(28, b"\x01")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.scan(swf(bad + tag(1) + tag(0)))


if __name__ == "__main__":
    unittest.main()
