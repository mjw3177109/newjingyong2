"""Synthetic SWF tests for source-free root conditional edges."""
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.index_root_conditional_edges import branch_edges, build_edges
from tools.index_swf_action_opcodes import index_root_action_opcodes


def tag(code, payload=b""):
    return struct.pack("<H", (code << 6) | len(payload)) + payload


def swf(action, compressed=False):
    tags = tag(12, action) + tag(1) + tag(0)
    body = b"\x08\x00" + struct.pack("<HH", 12 * 256, 1) + tags
    raw = b"FWS" + bytes([8]) + struct.pack("<I", 8 + len(body)) + body
    return b"CWS" + raw[3:8] + zlib.compress(body) if compressed else raw


def queue_for(index):
    row = index["action_tags"][0]
    return {"schema": "swf-root-conditional-review-queue-v1",
            "source_swf_sha256": index["source_swf_sha256"],
            "root_showframe_tags": 1, "root_doaction_tags": 1,
            "selected_candidate_count": 1, "verified_story_events": 0,
            "candidates": [{"root_frame": 1, "action_tag_ordinal": 1,
                            "action_sha256": row["action_sha256"],
                            "conditional_opcode_count": 1, "jump_opcode_count": 1,
                            "review_status": "unverified"}]}


class RootConditionalEdgesTests(unittest.TestCase):
    ACTION = bytes([0x9d, 2, 0, 0, 0, 0x99, 2, 0, 0, 0, 0])

    def run_fixture(self, compressed=False):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "fixture.swf"
            path.write_bytes(swf(self.ACTION, compressed))
            index = index_root_action_opcodes(path)
            return build_edges(path, index, queue_for(index))

    def test_forward_conditional_and_jump_to_end(self):
        result = self.run_fixture()
        self.assertEqual((result["if_edges"], result["jump_edges"], result["invalid_target_edges"]), (1, 1, 0))
        self.assertEqual([(e["source_offset"], e["target_offset"]) for e in result["candidates"][0]["edges"]], [(0, 5), (5, 10)])
        self.assertEqual(result["verified_story_events"], 0)

    def test_compressed_swf_and_source_free(self):
        result = self.run_fixture(True)
        self.assertEqual(result["total_branch_edges"], 2)
        self.assertNotIn("fixture.swf", str(result))
        self.assertNotIn("ActionScript", str(result))

    def test_backward_and_misaligned_branch_are_classified(self):
        backward = bytes([0x96, 0, 0, 0x9d, 2, 0, 0xf8, 0xff, 0])
        edges = branch_edges(backward)
        self.assertEqual(edges[0]["target_offset"], 0)
        self.assertEqual(edges[0]["target_alignment"], "record_boundary")
        self.assertEqual(edges[0]["direction"], "backward_or_self")
        self.assertEqual(branch_edges(bytes([0x99, 2, 0, 0xfe, 0xff, 0]))[0]["target_alignment"], "inside_record")

    def test_rejects_mismatched_hash_and_forged_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "fixture.swf"
            path.write_bytes(swf(self.ACTION))
            index = index_root_action_opcodes(path)
            queue = queue_for(index)
            queue["source_swf_sha256"] = "f" * 64
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                build_edges(path, index, queue)
            queue = queue_for(index)
            queue["candidates"][0]["conditional_opcode_count"] = 99
            with self.assertRaisesRegex(ValueError, "mismatch"):
                build_edges(path, index, queue)

    def test_rejects_truncated_and_missing_end(self):
        with self.assertRaises(ValueError):
            branch_edges(bytes([0x9d, 2, 0, 0]))
        with self.assertRaises(ValueError):
            branch_edges(bytes([0x9d, 2, 0, 0, 0]))


if __name__ == "__main__":
    unittest.main()
