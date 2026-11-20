import unittest
from tools.probe_if6607_stack_boundary import predecessor_audit


class PredecessorBoundaryTests(unittest.TestCase):
    def test_immediate_predecessors(self):
        # Less2, If(+0), Push(string), SetVariable, End.
        action = b"\x48\x9d\x02\x00\x00\x00\x96\x03\x00\x00X\x00\x1d\x00"
        result = predecessor_audit(action, if_offset=1, set_variable_offset=12)
        self.assertTrue(result["if_preceded_by_less2"])
        self.assertTrue(result["set_variable_preceded_by_push"])
        self.assertEqual(result["verified_story_events"], 0)
        self.assertEqual(result["runtime_reachability"], "unknown")
        self.assertNotIn("X", str(result))

    def test_separated_predecessors(self):
        action = b"\x48\x17\x9d\x02\x00\x00\x00\x96\x03\x00\x00X\x00\x17\x1d\x00"
        result = predecessor_audit(action, if_offset=2, set_variable_offset=14)
        self.assertFalse(result["if_preceded_by_less2"])
        self.assertFalse(result["set_variable_preceded_by_push"])

    def test_reject_wrong_boundaries(self):
        action = b"\x48\x9d\x02\x00\x00\x00\x96\x03\x00\x00X\x00\x1d\x00"
        with self.assertRaisesRegex(ValueError, "If"):
            predecessor_audit(action, if_offset=0, set_variable_offset=12)
        with self.assertRaisesRegex(ValueError, "SetVariable"):
            predecessor_audit(action, if_offset=1, set_variable_offset=13)


if __name__ == "__main__":
    unittest.main()
