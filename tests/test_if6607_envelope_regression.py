"""Regression tests for IF6607 evidence envelope separation (synthetic hashes only)."""
import unittest
from tools.verify_if6607_private import validate

def h(c):
    return c * 64

def record():
    return {
        "source_swf_sha256": h("a"), "java8_version": "1.8.0",
        "ffdec_version": "test", "export_a_sha256": h("b"),
        "export_b_sha256": h("b"), "condition_stack_evidence_sha256": h("c"),
        "independent_review_sha256": h("d"), "frame": 55,
        "action_ordinal": 9, "if_offset": 6607,
        "paths": {
            "true": {"observed_successor": 6623, "before_state_sha256": h("e"),
                     "after_state_sha256": h("f"), "execution_trace_sha256": h("1"),
                     "effects_evidence_sha256": h("2")},
            "false": {"observed_successor": 6612, "before_state_sha256": h("e"),
                      "after_state_sha256": h("f"), "execution_trace_sha256": h("3"),
                      "effects_evidence_sha256": h("4")},
        },
    }

class TestEnvelope(unittest.TestCase):
    def test_distinct_path_traces_accepted(self):
        self.assertTrue(validate(record()))

    def test_same_trace_hash_for_opposite_successors_rejected(self):
        data = record()
        data["paths"]["false"]["execution_trace_sha256"] = data["paths"]["true"]["execution_trace_sha256"]
        self.assertFalse(validate(data))

    def test_wrong_successor_rejected(self):
        data = record()
        data["paths"]["false"]["observed_successor"] = 6623
        self.assertFalse(validate(data))

if __name__ == "__main__":
    unittest.main()
