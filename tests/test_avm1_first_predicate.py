import unittest
from tools.avm1_first_predicate import inspect_first_branch


class FirstPredicateTests(unittest.TestCase):
    def test_literal_candidate(self):
        data = bytes.fromhex("96020005019d0200000000")
        report = inspect_first_branch(data)
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})
        self.assertEqual(report["offset"], 5)

    def test_register_reference_is_not_literal(self):
        report = inspect_first_branch(bytes.fromhex("96020004019d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "unresolved_push_reference")
        self.assertEqual(report["predicate"], {"type": "register", "value": 1})

    def test_constant_pool_index_is_not_literal(self):
        report = inspect_first_branch(bytes.fromhex("96020008029d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "unresolved_push_reference")
        self.assertEqual(report["predicate"], {"type": "constant_index", "width": 8, "value": 2})

    def test_boolean_not_before_if(self):
        report = inspect_first_branch(bytes.fromhex("9602000501129d0200000000"))
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": False})

    def test_double_not_restores_boolean(self):
        report = inspect_first_branch(bytes.fromhex("960200050112129d0200000000"))
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_not_register_is_unknown(self):
        report = inspect_first_branch(bytes.fromhex("9602000401129d0200000000"))
        self.assertEqual(report["reason"], "unresolved_not_operand")

    def test_not_underflow(self):
        report = inspect_first_branch(bytes.fromhex("129d0200000000"))
        self.assertEqual(report["reason"], "stack_underflow")

    def test_underflow(self):
        self.assertEqual(inspect_first_branch(bytes.fromhex("9d0200000000"))["reason"], "stack_underflow")

    def test_unknown_opcode_not_guessed(self):
        data = bytes.fromhex("96020005010a9d0200000000")
        self.assertEqual(inspect_first_branch(data)["reason"], "unsupported_opcode")

    def test_jump_not_followed(self):
        data = bytes.fromhex("99020000009d0200000000")
        self.assertEqual(inspect_first_branch(data)["reason"], "jump_before_if")

    def test_boolean_equals_true(self):
        data = bytes.fromhex("960400050105010e9d0200000000")
        report = inspect_first_branch(data)
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_boolean_equals_false(self):
        data = bytes.fromhex("960400050105000e9d0200000000")
        report = inspect_first_branch(data)
        self.assertEqual(report["predicate"], {"type": "boolean", "value": False})

    def test_equals_register_remains_unknown(self):
        data = bytes.fromhex("960400040105010e9d0200000000")
        report = inspect_first_branch(data)
        self.assertEqual(report["reason"], "unresolved_equals_operands")

    def test_equals_stack_underflow(self):
        data = bytes.fromhex("96020005010e9d0200000000")
        report = inspect_first_branch(data)
        self.assertEqual(report["reason"], "stack_underflow")

    def test_boolean_and_true(self):
        report = inspect_first_branch(bytes.fromhex("96040005010501109d0200000000"))
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_boolean_and_false(self):
        report = inspect_first_branch(bytes.fromhex("96040005010500109d0200000000"))
        self.assertEqual(report["predicate"], {"type": "boolean", "value": False})

    def test_boolean_or_true(self):
        report = inspect_first_branch(bytes.fromhex("96040005000501119d0200000000"))
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_boolean_or_false(self):
        report = inspect_first_branch(bytes.fromhex("96040005000500119d0200000000"))
        self.assertEqual(report["predicate"], {"type": "boolean", "value": False})

    def test_logical_register_is_unknown(self):
        report = inspect_first_branch(bytes.fromhex("96040004010501109d0200000000"))
        self.assertEqual(report["reason"], "unresolved_logical_operands")

    def test_logical_underflow(self):
        report = inspect_first_branch(bytes.fromhex("9602000501119d0200000000"))
        self.assertEqual(report["reason"], "stack_underflow")

    def test_get_variable_is_symbolic_not_verified(self):
        # Push "flag", GetVariable, If (zero relative jump).
        report = inspect_first_branch(bytes.fromhex("96060000666c6167001c9d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "unresolved_push_reference")
        self.assertEqual(report["predicate"], {"type": "variable_reference", "name": "flag"})

    def test_get_variable_stack_underflow(self):
        report = inspect_first_branch(bytes.fromhex("1c9d0200000000"))
        self.assertEqual(report["reason"], "stack_underflow")

    def test_get_variable_unknown_name(self):
        report = inspect_first_branch(bytes.fromhex("96020004011c9d0200000000"))
        self.assertEqual(report["reason"], "unresolved_variable_name")

    def test_get_variable_not_is_unresolved(self):
        report = inspect_first_branch(bytes.fromhex("96060000666c6167001c129d0200000000"))
        self.assertEqual(report["reason"], "unresolved_not_operand")

    def test_integer_if_requires_coercion(self):
        # AVM1 integer 1 is truthy, but this conservative tracer does not model coercion.
        report = inspect_first_branch(bytes.fromhex("96050007010000009d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "unresolved_push_reference")
        self.assertEqual(report["predicate"], {"type": "integer", "value": 1})

    def test_string_if_requires_coercion(self):
        report = inspect_first_branch(bytes.fromhex("9603000061009d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["predicate"], {"type": "string", "value": "a"})

    def test_invalid_branch_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid branch boundary"):
            inspect_first_branch(bytes.fromhex("96020005019d0200ffff00"))


if __name__ == "__main__":
    unittest.main()
