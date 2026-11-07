"""Decode selected AVM1 ActionPush literal types from an isolated action payload.

Structural evidence only: constant-pool indexes are unresolved, and no story
predicate or variable meaning can be inferred from literals alone.
"""
import struct


def decode_push_literals(payload: bytes):
    values = []
    pos = 0
    while pos < len(payload):
        tag = payload[pos]
        pos += 1
        if tag == 0:
            end = payload.find(b'\0', pos)
            if end < 0:
                raise ValueError('unterminated ActionPush string')
            values.append({'type': 'string', 'value': payload[pos:end].decode('utf-8', errors='replace')})
            pos = end + 1
        elif tag == 2:
            values.append({'type': 'null', 'value': None})
        elif tag == 3:
            values.append({'type': 'undefined', 'value': None})
        elif tag == 4:
            if pos >= len(payload):
                raise ValueError('truncated ActionPush register')
            values.append({'type': 'register', 'value': payload[pos]})
            pos += 1
        elif tag == 1:
            if pos + 4 > len(payload):
                raise ValueError('truncated ActionPush float')
            values.append({'type': 'float', 'value': struct.unpack_from('<f', payload, pos)[0]})
            pos += 4
        elif tag == 5:
            if pos >= len(payload):
                raise ValueError('truncated ActionPush boolean')
            values.append({'type': 'boolean', 'value': payload[pos] != 0})
            pos += 1
        elif tag in (7, 8, 9):
            size = {7: 4, 8: 1, 9: 2}[tag]
            if pos + size > len(payload):
                raise ValueError('truncated ActionPush numeric/index value')
            raw = payload[pos:pos + size]
            pos += size
            if tag == 7:
                values.append({'type': 'integer', 'value': struct.unpack('<i', raw)[0]})
            else:
                values.append({'type': 'constant_index', 'width': size * 8, 'value': int.from_bytes(raw, 'little')})
        else:
            raise ValueError(f'unsupported ActionPush type 0x{tag:02x} at offset {pos - 1}')
    return values
