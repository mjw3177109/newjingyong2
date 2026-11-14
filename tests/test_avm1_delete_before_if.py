"""Regression tests: AVM1 delete operations must not yield invented predicates."""
import unittest
from tools.avm1_first_predicate import inspect_first_branch


class DeleteBeforeIfTests(unittest.TestCase):
    def test_delete_property_before_if(self):
        # Push true, Delete, If: object mutation invalidates linear inference.
        report = inspect_first_branch(bytes.fromhex("96020005013a9d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "state_mutation_before_if")
        self.assertEqual(report["opcode"], 0x3A)

    def test_delete2_variable_before_if(self):
        report = inspect_first_branch(bytes.fromhex("96020005013b9d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "state_mutation_before_if")
        self.assertEqual(report["opcode"], 0x3B)


if __name__ == "__main__":
    unittest.main()
