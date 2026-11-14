"""Synthetic AVM1 predicate safety tests; never infer original story semantics."""
import unittest

from tools.avm1_first_predicate import inspect_first_branch


def push_boolean(value):
    return bytes([0x96, 0x02, 0x00, 0x05, int(value)])


def action_if():
    # Conditional jump with zero displacement; both successors are stream end.
    return bytes([0x9D, 0x02, 0x00, 0x00, 0x00])


class PredicateSafetyRegression(unittest.TestCase):
    def test_known_boolean_not_is_only_literal_candidate(self):
        result = inspect_first_branch(push_boolean(True) + bytes([0x12]) + action_if())
        self.assertEqual(result["status"], "literal_candidate")
        self.assertEqual(result["predicate"], {"type": "boolean", "value": False})

    def test_runtime_state_mutation_blocks_literal_inference(self):
        # Even a known literal cannot be carried across SetVariable.
        payload = push_boolean(True) + bytes([0x1D]) + action_if()
        result = inspect_first_branch(payload)
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reason"], "state_mutation_before_if")

    def test_runtime_variable_is_not_treated_as_known_boolean(self):
        # Push string "flag", then GetVariable and If.
        payload = bytes([0x96, 0x06, 0x00, 0x00]) + b"flag\x00" + bytes([0x1C]) + action_if()
        result = inspect_first_branch(payload)
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reason"], "unresolved_push_reference")
        self.assertEqual(result["predicate"]["type"], "variable_reference")


if __name__ == "__main__":
    unittest.main()
