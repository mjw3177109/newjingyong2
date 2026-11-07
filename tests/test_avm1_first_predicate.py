import unittest
from tools.avm1_first_predicate import inspect_first_branch


class FirstPredicateTests(unittest.TestCase):
    def test_literal_candidate(self):
        data = bytes.fromhex("96020005019d0200000000")
        report = inspect_first_branch(data)
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})
        self.assertEqual(report["offset"], 5)

    def test_underflow(self):
        self.assertEqual(inspect_first_branch(bytes.fromhex("9d0200000000"))["reason"], "stack_underflow")

    def test_unknown_opcode_not_guessed(self):
        data = bytes.fromhex("96020005010a9d0200000000")
        self.assertEqual(inspect_first_branch(data)["reason"], "unsupported_opcode")

    def test_jump_not_followed(self):
        data = bytes.fromhex("99020000009d0200000000")
        self.assertEqual(inspect_first_branch(data)["reason"], "jump_before_if")

    def test_invalid_branch_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid branch boundary"):
            inspect_first_branch(bytes.fromhex("96020005019d0200ffff00"))


if __name__ == "__main__":
    unittest.main()
