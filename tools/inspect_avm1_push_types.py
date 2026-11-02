"""Private AVM1 ActionPush type-shape comparison; never export operand values."""


def push_type_signature(payload):
    """Decode only AVM1 Push type tags, skipping private values and strings."""
    if not isinstance(payload, bytes):
        raise ValueError('Push payload must be bytes')
    position, tags = 0, []
    while position < len(payload):
        tag = payload[position]
        position += 1
        if tag == 0:  # NUL-terminated string; do not decode or expose it.
            end = payload.find(b'\x00', position)
            if end < 0:
                raise ValueError('unterminated private Push string')
            position = end + 1
        elif tag in (2, 3):  # null, undefined
            pass
        elif tag in (4, 5, 8):  # register, boolean, constant8
            position += 1
        elif tag == 9:  # constant16
            position += 2
        elif tag in (1, 7):  # float, integer
            position += 4
        elif tag == 6:  # double
            position += 8
        else:
            raise ValueError('unknown AVM1 Push type tag')
        if position > len(payload):
            raise ValueError('truncated AVM1 Push operand')
        tags.append(tag)
    return tuple(tags)


def compare_push_type_signatures(records, left_offsets, right_offsets):
    """Only return a coarse category; no types, values, offsets or hashes."""
    if len(left_offsets) != len(right_offsets):
        return 'not_comparable'
    try:
        left = [records[p] for p in left_offsets]
        right = [records[p] for p in right_offsets]
    except KeyError as exc:
        raise ValueError('window offset is not an AVM1 record boundary') from exc
    if [op for op, _ in left] != [op for op, _ in right]:
        return 'not_comparable'
    pushes = [(a, b) for (op, a), (_, b) in zip(left, right) if op == 0x96]
    if not pushes:
        return 'no_push'
    try:
        left_shapes = [push_type_signature(a) for a, _ in pushes]
        right_shapes = [push_type_signature(b) for _, b in pushes]
    except ValueError:
        return 'unparseable'
    return 'same' if left_shapes == right_shapes else 'different'
