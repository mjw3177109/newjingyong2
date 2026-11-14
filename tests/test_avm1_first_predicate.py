import unittest
from tools.avm1_first_predicate import inspect_first_branch


class FirstPredicateTests(unittest.TestCase):
    def test_trace_runtime_reference_is_unknown(self):
        # Push register 1; Trace may coerce an object via runtime toString.
        report = inspect_first_branch(bytes.fromhex("96020004012696020005019d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "trace_runtime_coercion_before_if")
        self.assertEqual(report["operand_type"], "register")

    def test_trace_boolean_preserves_later_literal(self):
        report = inspect_first_branch(bytes.fromhex("96020005012696020005019d0200000000"))
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_get_member_before_if_is_unknown(self):
        report = inspect_first_branch(bytes.fromhex("4e9d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "member_access_before_if")
        self.assertEqual(report["opcode"], 0x4E)

    def test_set_member_before_if_is_unknown(self):
        report = inspect_first_branch(bytes.fromhex("4f9d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "member_access_before_if")
        self.assertEqual(report["opcode"], 0x4F)

    def test_random_number_before_if_is_runtime_unknown(self):
        report = inspect_first_branch(bytes.fromhex("309d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "runtime_value_before_if")
        self.assertEqual(report["opcode"], 0x30)
        self.assertEqual(report["offset"], 0)

    def test_get_time_before_if_is_runtime_unknown(self):
        report = inspect_first_branch(bytes.fromhex("349d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "runtime_value_before_if")
        self.assertEqual(report["opcode"], 0x34)
        self.assertEqual(report["offset"], 0)

    def test_new_object_before_if_is_unknown(self):
        report = inspect_first_branch(bytes.fromhex("409d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "runtime_call_before_if")
        self.assertEqual(report["opcode"], 0x40)
        self.assertEqual(report["offset"], 0)

    def test_new_method_before_if_is_unknown(self):
        report = inspect_first_branch(bytes.fromhex("539d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "runtime_call_before_if")
        self.assertEqual(report["opcode"], 0x53)
        self.assertEqual(report["offset"], 0)

    def test_call_function_before_if_is_unknown(self):
        report = inspect_first_branch(bytes.fromhex("3d9d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "runtime_call_before_if")
        self.assertEqual(report["opcode"], 0x3D)
        self.assertEqual(report["offset"], 0)

    def test_call_method_before_if_is_unknown(self):
        report = inspect_first_branch(bytes.fromhex("529d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "runtime_call_before_if")
        self.assertEqual(report["opcode"], 0x52)
        self.assertEqual(report["offset"], 0)

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

    def test_strict_equals_known_booleans_true(self):
        report = inspect_first_branch(bytes.fromhex("96040005010501669d0200000000"))
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_strict_equals_known_booleans_false(self):
        report = inspect_first_branch(bytes.fromhex("96040005010500669d0200000000"))
        self.assertEqual(report["predicate"], {"type": "boolean", "value": False})

    def test_strict_equals_variable_is_unresolved(self):
        report = inspect_first_branch(bytes.fromhex("96040004010501669d0200000000"))
        self.assertEqual(report["reason"], "unresolved_equals_operands")

    def test_strict_equals_underflow(self):
        report = inspect_first_branch(bytes.fromhex("9602000501669d0200000000"))
        self.assertEqual(report["reason"], "stack_underflow")

    def test_duplicate_boolean_compares_equal(self):
        # Push true; duplicate it; strict-equals; conditional branch.
        report = inspect_first_branch(bytes.fromhex("96020005014c669d0200000000"))
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_duplicate_empty_stack_is_unknown(self):
        report = inspect_first_branch(bytes.fromhex("4c9d0200000000"))
        self.assertEqual(report["reason"], "stack_underflow")

    def test_duplicate_variable_remains_unresolved(self):
        report = inspect_first_branch(bytes.fromhex("96060000666c6167001c4c669d0200000000"))
        self.assertEqual(report["reason"], "unresolved_equals_operands")

    def test_stack_swap_changes_top_predicate(self):
        # Push true, false; swap so ActionIf observes true.
        report = inspect_first_branch(bytes.fromhex("960400050105004d9d0200000000"))
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_stack_swap_underflow(self):
        report = inspect_first_branch(bytes.fromhex("96020005014d9d0200000000"))
        self.assertEqual(report["reason"], "stack_underflow")

    def test_stack_swap_does_not_resolve_register(self):
        report = inspect_first_branch(bytes.fromhex("960400040105014d9d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["predicate"], {"type": "register", "value": 1})

    def test_pop_discards_top_boolean(self):
        # Push true, false; Pop false; If observes true.
        report = inspect_first_branch(bytes.fromhex("96040005010500179d0200000000"))
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_pop_underflow(self):
        report = inspect_first_branch(bytes.fromhex("179d0200000000"))
        self.assertEqual(report["reason"], "stack_underflow")

    def test_pop_unknown_reference_does_not_infer_value(self):
        # Pop an unresolved register; remaining boolean is still known.
        report = inspect_first_branch(bytes.fromhex("96040005010401179d0200000000"))
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_to_boolean_known_boolean_identity(self):
        report = inspect_first_branch(bytes.fromhex("9602000501449d0200000000"))
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_to_boolean_integer_requires_coercion(self):
        report = inspect_first_branch(bytes.fromhex("9605000701000000449d0200000000"))
        self.assertEqual(report["reason"], "unresolved_to_boolean_operand")
        self.assertEqual(report["operand"], {"type": "integer", "value": 1})

    def test_to_boolean_register_remains_unknown(self):
        report = inspect_first_branch(bytes.fromhex("9602000401449d0200000000"))
        self.assertEqual(report["reason"], "unresolved_to_boolean_operand")

    def test_to_boolean_underflow(self):
        report = inspect_first_branch(bytes.fromhex("449d0200000000"))
        self.assertEqual(report["reason"], "stack_underflow")

    def test_equals2_boolean_true(self):
        report = inspect_first_branch(bytes.fromhex("96040005010501499d0200000000"))
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_equals2_boolean_false(self):
        report = inspect_first_branch(bytes.fromhex("96040005010500499d0200000000"))
        self.assertEqual(report["predicate"], {"type": "boolean", "value": False})

    def test_equals2_register_unknown(self):
        report = inspect_first_branch(bytes.fromhex("96040004010501499d0200000000"))
        self.assertEqual(report["reason"], "unresolved_equals_operands")

    def test_equals2_underflow(self):
        report = inspect_first_branch(bytes.fromhex("9602000501499d0200000000"))
        self.assertEqual(report["reason"], "stack_underflow")

    def test_trace_discards_top_without_changing_remaining_predicate(self):
        # Push true, false; trace false; If observes true.
        report = inspect_first_branch(bytes.fromhex("96040005010500269d0200000000"))
        self.assertEqual(report["status"], "literal_candidate")
        self.assertEqual(report["predicate"], {"type": "boolean", "value": True})

    def test_trace_underflow_is_unknown(self):
        report = inspect_first_branch(bytes.fromhex("269d0200000000"))
        self.assertEqual(report["reason"], "stack_underflow")

    def test_trace_unknown_reference_is_not_resolved(self):
        # A register may coerce via runtime behavior during Trace; do not fold the later If.
        report = inspect_first_branch(bytes.fromhex("96040005010401269d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "trace_runtime_coercion_before_if")
        self.assertEqual(report["offset"], 7)
        self.assertEqual(report["operand_type"], "register")

    def test_return_before_if_is_terminal(self):
        report = inspect_first_branch(bytes.fromhex("96020005013e9d0200000000"))
        self.assertEqual(report["reason"], "terminal_before_if")
        self.assertEqual(report["opcode"], 0x3E)

    def test_throw_before_if_is_terminal(self):
        report = inspect_first_branch(bytes.fromhex("96020005012a9d0200000000"))
        self.assertEqual(report["reason"], "terminal_before_if")
        self.assertEqual(report["opcode"], 0x2A)

    def test_set_variable_before_if_is_not_a_verified_condition(self):
        # SetVariable has a side effect; do not carry earlier stack assumptions forward.
        report = inspect_first_branch(bytes.fromhex("96020005011d9d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "state_mutation_before_if")
        self.assertEqual(report["opcode"], 0x1D)

    def test_store_register_before_if_is_not_a_verified_condition(self):
        report = inspect_first_branch(bytes.fromhex("9602000501870100019d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "state_mutation_before_if")
        self.assertEqual(report["opcode"], 0x87)

    def test_define_local_before_if_is_state_mutation(self):
        # ActionDefineLocal changes the scope; no predicate is inferred across it.
        report = inspect_first_branch(bytes.fromhex("96020005013c9d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "state_mutation_before_if")
        self.assertEqual(report["opcode"], 0x3C)

    def test_define_local2_before_if_is_state_mutation(self):
        # ActionDefineLocal2 declares an undefined local; runtime state remains unknown.
        report = inspect_first_branch(bytes.fromhex("9602000501419d0200000000"))
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["reason"], "state_mutation_before_if")
        self.assertEqual(report["opcode"], 0x41)

    def test_invalid_branch_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid branch boundary"):
            inspect_first_branch(bytes.fromhex("96020005019d0200ffff00"))


if __name__ == "__main__":
    unittest.main()
