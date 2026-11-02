"""Synthetic SWF placement fixtures only; never use original game assets."""
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.index_swf_sprite_placements import index_placements


def tag(code, payload=b""):
    if len(payload) < 63:
        return struct.pack("<H", code << 6 | len(payload)) + payload
    return struct.pack("<HI", code << 6 | 63, len(payload)) + payload


def sprite(sid, inner=None):
    if inner is None:
        inner = tag(1) + tag(0)
    return tag(39, struct.pack("<HH", sid, 1) + inner)


def swf(tags, compressed=False):
    body = b"\x08\x00" + struct.pack("<HH", 12 * 256, 2) + tags
    data = b"FWS" + bytes([8]) + struct.pack("<I", len(body) + 8) + body
    return b"CWS" + data[3:8] + zlib.compress(body) if compressed else data


def place2(sid=None):
    return tag(26, bytes([2 if sid is not None else 1]) + struct.pack("<H", 3)
               + (struct.pack("<H", sid) if sid is not None else b""))


def place3(sid=None, class_name=None, image=False):
    flags1 = 0x02 if sid is not None else 0
    flags2 = (0x08 if class_name is not None else 0) | (0x10 if image else 0)
    body = bytes([flags1, flags2]) + struct.pack("<H", 3)
    if class_name is not None or (image and sid is not None):
        body += (class_name or b"image-class") + bytes([0])
    if sid is not None:
        body += struct.pack("<H", sid)
    return tag(70, body)


class RootPlacementTests(unittest.TestCase):
    def scan(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "private-asset.swf"
            path.write_bytes(data)
            return index_placements(path)

    def test_direct_root_placements_and_source_free(self):
        root = sprite(7) + sprite(8)
        root += tag(4, struct.pack("<HH", 7, 1)) + place2(8) + tag(1)
        root += place2(None) + tag(4, struct.pack("<HH", 99, 2)) + tag(1) + tag(0)
        report = self.scan(swf(root))
        self.assertEqual(report["root_showframe_tags"], 2)
        self.assertEqual(report["defined_sprite_count"], 2)
        self.assertEqual(report["direct_sprite_placement_tag_count"], 2)
        self.assertEqual(report["directly_referenced_sprite_count"], 2)
        self.assertEqual(report["non_sprite_character_placement_count"], 1)
        self.assertEqual(report["placeobject2_without_character_count"], 1)
        self.assertEqual([(r["sprite_id"], r["root_frame"]) for r in report["direct_root_sprite_placements"]],
                         [(7, 1), (8, 1)])
        self.assertNotIn("private-asset", str(report))

    def test_compressed_and_uncompressed_same_placements(self):
        root = sprite(4) + place2(4) + tag(1) + tag(1) + tag(0)
        a, b = self.scan(swf(root)), self.scan(swf(root, compressed=True))
        self.assertEqual(a["direct_root_sprite_placements"], b["direct_root_sprite_placements"])
        self.assertNotEqual(a["source_swf_sha256"], b["source_swf_sha256"])

    def test_nested_sprite_placement_not_assigned_to_root(self):
        nested = tag(4, struct.pack("<HH", 5, 1)) + tag(1) + tag(0)
        root = sprite(5) + sprite(6, nested) + tag(1) + tag(1) + tag(0)
        report = self.scan(swf(root))
        self.assertEqual(report["direct_sprite_placement_tag_count"], 0)
        self.assertEqual(report["sprite_definitions_without_direct_root_placement"], 2)

    def test_placeobject3_without_character_is_not_placement(self):
        root = sprite(3) + place3(class_name=b"secret-class-name") + tag(1) + tag(1) + tag(0)
        report = self.scan(swf(root))
        self.assertEqual(report["placeobject3_tag_count"], 1)
        self.assertEqual(report["placeobject3_without_character_count"], 1)
        self.assertEqual(report["direct_sprite_placement_tag_count"], 0)
        self.assertNotIn("secret", str(report))

    def test_placeobject3_plain_character_and_class_name(self):
        root = sprite(3) + sprite(4) + place3(3) + place3(4, b"private-class") + tag(1) + tag(1) + tag(0)
        report = self.scan(swf(root))
        self.assertEqual(report["direct_sprite_placement_tag_count"], 2)
        self.assertEqual(report["directly_referenced_sprite_count"], 2)
        self.assertEqual([(r["sprite_id"], r["placeobject3_count"]) for r in report["direct_root_sprite_placements"]],
                         [(3, 1), (4, 1)])
        self.assertNotIn("private-class", str(report))

    def test_placeobject3_image_class_name_and_compression(self):
        root = sprite(7) + place3(7, image=True) + tag(1) + tag(1) + tag(0)
        a, b = self.scan(swf(root)), self.scan(swf(root, compressed=True))
        self.assertEqual(a["direct_root_sprite_placements"], b["direct_root_sprite_placements"])
        self.assertEqual(a["direct_sprite_placement_tag_count"], 1)
        self.assertNotIn("image-class", str(a))

    def test_placeobject3_non_sprite_character_and_move_only(self):
        root = sprite(7) + place3(99) + place3() + tag(1) + tag(1) + tag(0)
        report = self.scan(swf(root))
        self.assertEqual(report["non_sprite_character_placement_count"], 1)
        self.assertEqual(report["placeobject3_without_character_count"], 1)
        self.assertEqual(report["direct_sprite_placement_tag_count"], 0)

    def test_placeobject3_truncated_fields_fail_closed(self):
        malformed = (b"", b"\\x02\\x00\\x01", b"\\x02\\x00\\x01\\x00\\x07",
                     b"\\x02\\x08\\x01\\x00\\x41\\x42",
                     b"\\x02\\x08\\x01\\x00\\x41\\x00\\x01")
        for payload in malformed:
            with self.subTest(length=len(payload)):
                with self.assertRaises(ValueError):
                    self.scan(swf(tag(70, payload) + tag(1) + tag(1) + tag(0)))

    def test_malformed_tags_fail_closed(self):
        for bad in (tag(4, b"\x01"), tag(26, b"\x02\x01\x00"),
                    tag(39, b"\x01"), tag(1)):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.scan(swf(bad + tag(1) + tag(1) + tag(0)) if bad != tag(1)
                              else swf(tag(1) + tag(1)))


if __name__ == "__main__":
    unittest.main()
