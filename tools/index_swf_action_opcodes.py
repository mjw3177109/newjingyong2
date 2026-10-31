#!/usr/bin/env python3
"""Source-free root DoAction bytecode structure index; no ActionScript semantics."""
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

try:
    from tools.index_swf_sprite_timeline import load_swf, iter_tags
except ModuleNotFoundError:
    from index_swf_sprite_timeline import load_swf, iter_tags

# SWF ActionScript 1/2 action-record opcodes. Nested function bodies are opaque.
TRACKED = {0x81: 'goto_frame', 0x8C: 'goto_label', 0x99: 'jump',
           0x9D: 'if', 0x8A: 'wait_for_frame', 0x9B: 'define_function',
           0x8E: 'define_function2', 0x96: 'push'}


def inspect_actions(payload):
    """Parse top-level records and classify branch target alignment, without raw bytes."""
    pos = 0
    counts = Counter()
    errors = []
    ended = False
    boundaries = set()
    destinations = []
    while pos < len(payload):
        boundaries.add(pos)
        opcode = payload[pos]
        pos += 1
        if opcode == 0:
            ended = True
            if any(payload[pos:]):
                errors.append('nonzero_bytes_after_end')
            break
        counts['records'] += 1
        if opcode in TRACKED:
            counts[TRACKED[opcode]] += 1
        if opcode >= 0x80:
            if pos + 2 > len(payload):
                errors.append('truncated_action_length')
                break
            length = struct.unpack_from('<H', payload, pos)[0]
            pos += 2
            if length > len(payload) - pos:
                errors.append('truncated_action_payload')
                break
            if opcode in (0x81, 0x99, 0x9D) and length != 2:
                errors.append('invalid_fixed_action_length')
            if opcode == 0x8A and length != 3:
                errors.append('invalid_wait_action_length')
            if opcode in (0x99, 0x9D) and length == 2:
                relative = struct.unpack_from('<h', payload, pos)[0]
                destinations.append(pos + length + relative)
            pos += length
    for destination in destinations:
        if not 0 <= destination < len(payload):
            counts['out_of_bounds_branch_targets'] += 1
        elif destination in boundaries:
            counts['branch_targets_on_record_boundary'] += 1
        else:
            counts['branch_targets_inside_record'] += 1
    if not ended:
        errors.append('missing_action_end')
    return dict(counts), sorted(set(errors))


def index_root_action_opcodes(path, timeline=None):
    raw, data, offset = load_swf(path)
    sha = hashlib.sha256(raw).hexdigest()
    frame = 1
    showframes = 0
    actions = 0
    totals = Counter()
    rows = []
    for code, payload in iter_tags(data, offset, len(data)):
        if code == 1:
            showframes += 1
            frame += 1
        elif code == 12:
            actions += 1
            counts, errors = inspect_actions(payload)
            totals.update(counts)
            rows.append({'root_frame': frame, 'tag_ordinal': actions,
                         'action_sha256': hashlib.sha256(payload).hexdigest(),
                         'opcode_counts': counts, 'parse_warnings': errors})
    if timeline is not None:
        if (timeline.get('schema') != 'swf-main-timeline-evidence-v1'
                or timeline.get('source_swf_sha256') != sha
                or timeline.get('observed_showframe_tags') != showframes
                or timeline.get('main_timeline_action_tags') != actions
                or timeline.get('main_timeline_frame_count_matches') is not True):
            raise ValueError('root timeline source or counts mismatch')
    return {'schema': 'swf-root-action-opcode-evidence-v1',
            'source_swf_sha256': sha, 'root_showframe_tags': showframes,
            'root_doaction_tags': actions, 'top_level_opcode_counts': dict(totals),
            'tags_with_parse_warnings': sum(bool(x['parse_warnings']) for x in rows),
            'action_tags': rows, 'verified_story_events': 0,
            'interpretation': 'Root DoAction top-level bytecode records only. Function bodies are opaque; no string, source code, graphics, audio, event semantics or runtime behavior exported.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('swf')
    parser.add_argument('--timeline', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    timeline = json.loads(Path(args.timeline).read_text(encoding='utf-8'))
    report = index_root_action_opcodes(args.swf, timeline)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    totals = report['top_level_opcode_counts']
    print('Root DoAction opcode index: {} tags, {} conditional records, {} parse warnings; branch targets aligned/inside/outside: {}/{}/{}; verified events: 0'.format(
        report['root_doaction_tags'], totals.get('if', 0), report['tags_with_parse_warnings'],
        totals.get('branch_targets_on_record_boundary', 0),
        totals.get('branch_targets_inside_record', 0),
        totals.get('out_of_bounds_branch_targets', 0)))


if __name__ == '__main__':
    main()
