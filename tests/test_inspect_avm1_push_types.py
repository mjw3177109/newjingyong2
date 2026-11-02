"""Synthetic ActionPush type-shape tests; no original SWF data."""
import unittest
from tools.inspect_avm1_push_types import push_type_signature, compare_push_type_signatures


class PushTypesTests(unittest.TestCase):
    def test_private_string_values_have_same_type_shape(self):
        records = {0: (0x96, b'\x00A\x00'), 6: (0x96, b'\x00B\x00')}
        self.assertEqual(compare_push_type_signatures(records, [0], [6]), 'same')

    def test_same_length_different_push_types(self):
        records = {0: (0x96, b'\x05\x01'), 5: (0x96, b'\x04\x01')}
        self.assertEqual(compare_push_type_signatures(records, [0], [5]), 'different')

    def test_all_supported_push_tags(self):
        payload = (b'\x00a\x00\x01' + b'\x00'*4 + b'\x02\x03\x04\x00'
                   + b'\x05\x01\x06' + b'\x00'*8 + b'\x07'
                   + b'\x00'*4 + b'\x08\x00\x09\x00\x00')
        self.assertEqual(push_type_signature(payload), tuple(range(10)))

    def test_malformed_push_fails_closed(self):
        records = {0: (0x96, b'\x07\x01'), 5: (0x96, b'\x07\x02')}
        self.assertEqual(compare_push_type_signatures(records, [0], [5]), 'unparseable')
        with self.assertRaises(ValueError):
            push_type_signature(b'\x00no-terminator')
        with self.assertRaises(ValueError):
            push_type_signature(b'\x0a')

    def test_nonpush_and_misaligned_regions(self):
        records = {0: (0x0e, None), 1: (0x0e, None), 2: (0x96, b'\x02')}
        self.assertEqual(compare_push_type_signatures(records, [0], [1]), 'no_push')
        self.assertEqual(compare_push_type_signatures(records, [0], [2]), 'not_comparable')
        self.assertEqual(compare_push_type_signatures(records, [0, 1], [1]), 'not_comparable')
        with self.assertRaises(ValueError):
            compare_push_type_signatures(records, [999], [1])

    def test_later_malformed_push_is_not_hidden_by_first_difference(self):
        records = {0: (0x96, b'\x02'), 2: (0x96, b'\x03'),
                   4: (0x96, b'\x07\x01'), 6: (0x96, b'\x02')}
        self.assertEqual(compare_push_type_signatures(records, [0, 4], [2, 6]), 'unparseable')


if __name__ == '__main__':
    unittest.main()
