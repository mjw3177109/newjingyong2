"""Synthetic AVM1 branch-graph regression tests; no SWF source content."""
import unittest

from tools.index_root_control_flow import local_graph


class LocalGraphRegression(unittest.TestCase):
    def test_if_two_distinct_successors(self):
        # IF at 0, next record at 5, target at 6, ActionEnd at 7.
        payload = bytes([0x9D, 2, 0, 1, 0, 0x04, 0x04, 0])
        graph = local_graph(payload)
        self.assertEqual(graph["conditional_count"], 1)
        self.assertEqual(graph["reachable_record_count"], 3)
        self.assertEqual(graph["unreachable_record_count"], 0)
        self.assertTrue(graph["action_end_reachable"])
        self.assertEqual(graph["if_successors"][0]["branch_target_offset"], 6)
        self.assertEqual(graph["if_successors"][0]["fallthrough_offset"], 5)
        self.assertTrue(graph["if_successors"][0]["branch_and_fallthrough_distinct"])

    def test_unconditional_jump_skips_record(self):
        # JUMP from 0 to 6, skipping record 5; end at 7.
        payload = bytes([0x99, 2, 0, 1, 0, 0x04, 0x04, 0])
        graph = local_graph(payload)
        self.assertEqual(graph["jump_count"], 1)
        self.assertEqual(graph["reachable_record_count"], 2)
        self.assertEqual(graph["unreachable_record_count"], 1)
        self.assertTrue(graph["action_end_reachable"])

    def test_branch_into_record_payload_is_rejected(self):
        # IF target 6 points into the second record's two-byte payload.
        payload = bytes([0x9D, 2, 0, 1, 0, 0x96, 2, 0, 0x00, 0x00, 0])
        with self.assertRaisesRegex(ValueError, "unsafe branch target"):
            local_graph(payload)


if __name__ == "__main__":
    unittest.main()
