import unittest
import struct
from tools.avm1_push_literals import decode_push_literals


class PushLiteralTests(unittest.TestCase):
    def test_mixed_literals(self):
        payload = b'\x00quest\x00\x05\x01\x07\xfe\xff\xff\xff\x08\x03\x09\x2c\x01\x02\x03'
        self.assertEqual(decode_push_literals(payload), [
            {'type': 'string', 'value': 'quest'},
            {'type': 'boolean', 'value': True},
            {'type': 'integer', 'value': -2},
            {'type': 'constant_index', 'width': 8, 'value': 3},
            {'type': 'constant_index', 'width': 16, 'value': 300},
            {'type': 'null', 'value': None},
            {'type': 'undefined', 'value': None},
        ])

    def test_truncation_and_unsupported(self):
        for data in (b'\x00abc', b'\x05', b'\x07\x01', b'\x09\x01', b'\x06'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                decode_push_literals(data)

    def test_float_and_register(self):
        payload = b'\x01' + struct.pack('<f', 1.5) + b'\x04\x07'
        self.assertEqual(decode_push_literals(payload), [
            {'type': 'float', 'value': 1.5},
            {'type': 'register', 'value': 7},
        ])

    def test_float_and_register_truncation(self):
        for data in (b'\x01', b'\x01\x00\x00\x00', b'\x04'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                decode_push_literals(data)

    def test_double_word_order_and_truncation(self):
        # AVM1 stores the high 32-bit word first, each word little-endian.
        raw = struct.pack('<d', -12.25)
        avm1 = raw[4:8] + raw[:4]
        self.assertEqual(decode_push_literals(b'\x06' + avm1), [
            {'type': 'double', 'value': -12.25},
        ])
        for length in range(8):
            with self.subTest(length=length), self.assertRaises(ValueError):
                decode_push_literals(b'\x06' + avm1[:length])

    def test_empty_and_false(self):
        self.assertEqual(decode_push_literals(b''), [])
        self.assertEqual(decode_push_literals(b'\x05\x00'), [{'type': 'boolean', 'value': False}])


if __name__ == '__main__':
    unittest.main()
