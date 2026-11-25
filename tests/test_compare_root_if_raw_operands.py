"""Synthetic AVM1 operand-equality tests; no original SWF content."""
import unittest

from tools.compare_root_if_raw_operands import encoded_records, compare_region


class RawOperandComparisonTests(unittest.TestCase):
    def setUp(self):
        # Two Push records with different private bytes, then two simple ops.
        self.records = encoded_records(
            b'\x96\x02\x00AB\x96\x02\x00AC\x0e\x0e\x00')

    def test_same_and_different_private_push_bytes(self):
        self.assertEqual(compare_region(self.records, [0], [0]), 'same')
        self.assertEqual(compare_region(self.records, [0], [5]), 'different')

    def test_opcode_and_length_mismatch_are_not_operand_claims(self):
        self.assertEqual(compare_region(self.records, [0], [10]), 'opcode_mismatch')
        self.assertEqual(compare_region(self.records, [0, 5], [0]), 'not_comparable')

    def test_no_encoded_operands_is_not_same(self):
        self.assertEqual(compare_region(self.records, [10], [11]),
                         'no_encoded_operands')

    def test_rejects_forged_record_offset_and_truncated_action(self):
        with self.assertRaises(ValueError):
            compare_region(self.records, [1], [0])
        with self.assertRaises(ValueError):
            encoded_records(b'\x96\x03\x00AB\x00')


if __name__ == '__main__':
    unittest.main()
