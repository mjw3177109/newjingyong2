#!/usr/bin/env python3
"""Compare raw AVM1 encoded operands without exporting operand values.

Only equality categories are emitted. Equality of encoded bytes does NOT
establish equal runtime predicates, event effects, or story meaning.
"""
import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.index_swf_sprite_timeline import load_swf, iter_tags
    from tools.index_root_state_access import action_records
    from tools.index_root_if_opcode_windows import build_windows
    from tools.compare_root_if_opcode_shapes import compare_shapes
except ModuleNotFoundError:
    from index_swf_sprite_timeline import load_swf, iter_tags
    from index_root_state_access import action_records
    from index_root_if_opcode_windows import build_windows
    from compare_root_if_opcode_shapes import compare_shapes


def encoded_records(payload):
    """Return private opcode and operand bytes keyed by record boundary."""
    records = action_records(payload)
    result = {}
    for pos, opcode in records:
        if opcode >= 0x80:
            length = int.from_bytes(payload[pos + 1:pos + 3], 'little')
            result[pos] = (opcode, payload[pos + 3:pos + 3 + length])
        else:
            result[pos] = (opcode, None)
    return result


def compare_region(records, left_offsets, right_offsets):
    """Never return raw opcodes, operand bytes, digests, or constants."""
    if len(left_offsets) != len(right_offsets):
        return 'not_comparable'
    try:
        left = [records[p] for p in left_offsets]
        right = [records[p] for p in right_offsets]
    except KeyError as exc:
        raise ValueError('window offset is not an AVM1 record boundary') from exc
    if [op for op, _ in left] != [op for op, _ in right]:
        return 'opcode_mismatch'
    operands = [(a, b) for (_, a), (_, b) in zip(left, right) if a is not None]
    if not operands:
        return 'no_encoded_operands'
    return 'same' if all(a == b for a, b in operands) else 'different'


def compare_raw_operands(swf_path, packets, clusters, windows, shapes):
    """Independently attest inputs to the original SWF before comparison."""
    fresh = build_windows(swf_path, packets, windows.get('window_width', 12))
    if fresh != windows:
        raise ValueError('window report differs from independently parsed SWF')
    expected = compare_shapes(clusters, fresh)
    if expected != shapes:
        raise ValueError('shape comparison differs from independently verified inputs')
    raw, data, offset = load_swf(swf_path)
    if hashlib.sha256(raw).hexdigest() != shapes['source_swf_sha256']:
        raise ValueError('SWF fingerprint mismatch')
    wanted = {(r['root_frame'], r['action_tag_ordinal']) for r in fresh['entries']}
    payloads = {}
    frame, ordinal = 1, 0
    for code, payload in iter_tags(data, offset, len(data)):
        if code == 1:
            frame += 1
        elif code == 12:
            ordinal += 1
            key = (frame, ordinal)
            if key in wanted:
                payloads[key] = encoded_records(payload)
    if set(payloads) != wanted:
        raise ValueError('source action missing')
    by_id = {r['review_id']: r for r in fresh['entries']}
    pairs = []
    for pair in shapes['adjacent_pairs']:
        left, right = by_id[pair['left_review_id']], by_id[pair['right_review_id']]
        key = (pair['root_frame'], pair['action_tag_ordinal'])
        if (key != (left['root_frame'], left['action_tag_ordinal'])
                or key != (right['root_frame'], right['action_tag_ordinal'])):
            raise ValueError('pair/action identity mismatch')
        records = payloads[key]
        def offsets(row, region):
            if region == 'predecessor':
                return row['straight_line_preceding_record_offsets']
            return row['successor_arm_windows'][region]['record_offsets']
        result = {
            'left_review_id': left['review_id'],
            'right_review_id': right['review_id'],
            'root_frame': key[0],
            'action_tag_ordinal': key[1],
            'left_if_source_offset': left['if_source_offset'],
            'right_if_source_offset': right['if_source_offset'],
        }
        for region in ('predecessor', 'branch', 'fallthrough'):
            result[region + '_encoded_operand_comparison'] = compare_region(
                records, offsets(left, region), offsets(right, region))
        result['review_status'] = 'unverified'
        pairs.append(result)
    return {
        'schema': 'swf-root-if-raw-operand-equality-v1',
        'source_swf_sha256': shapes['source_swf_sha256'],
        'adjacent_pair_count': len(pairs),
        'adjacent_pairs': pairs,
        'verified_story_events': 0,
        'ready_for_html5_mapping': 0,
        'warning': 'Only private raw byte equality categories. Equal encoded operands do not prove equal execution, predicates, maps, state effects or story. No operand, identifier, hash, script or asset bytes exported.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('swf', type=Path)
    for name in ('packets', 'clusters', 'windows', 'shapes', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    result = compare_raw_operands(args.swf, read(args.packets),
                                  read(args.clusters), read(args.windows),
                                  read(args.shapes))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('Raw AVM1 adjacent operand comparisons:', result['adjacent_pair_count'],
          'verified story events: 0')


if __name__ == '__main__':
    main()
