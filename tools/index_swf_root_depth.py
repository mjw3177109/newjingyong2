#!/usr/bin/env python3
"""Index root timeline display-list depth assignments, not rendered frames or story."""
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

try:
    from tools.index_swf_sprite_timeline import load_swf, iter_tags
    from tools.index_swf_sprite_placements import placeobject3_character_id
except ModuleNotFoundError:
    from index_swf_sprite_timeline import load_swf, iter_tags
    from index_swf_sprite_placements import placeobject3_character_id


def index_root_depth(path):
    raw, data, offset = load_swf(path)
    # Definitions may follow placements. Collect before classifying references.
    defined = set()
    for code, payload in iter_tags(data, offset, len(data)):
        if code == 39:
            if len(payload) < 6:
                raise ValueError("truncated DefineSprite")
            sid = struct.unpack_from("<H", payload)[0]
            if sid in defined:
                raise ValueError("duplicate DefineSprite id")
            defined.add(sid)

    depth_state = {}  # depth -> character id; non-sprites retained privately for correct removals
    counters = Counter()
    frame = 1
    sprite_occupied_frames = 0
    max_sprite_depths = 0
    max_occupied_depths = 0
    sprite_transitions = []

    def assign(depth, character_id, kind):
        previous = depth_state.get(depth)
        if previous is not None:
            counters["occupied_depth_assignment_tags"] += 1
        if previous in defined:
            sprite_transitions.append({"root_frame": frame, "depth": depth,
                                       "sprite_id": previous, "kind": "prior_sprite_displaced"})
        depth_state[depth] = character_id
        if character_id in defined:
            sprite_transitions.append({"root_frame": frame, "depth": depth,
                                       "sprite_id": character_id, "kind": "sprite_character_assigned"})
            counters["sprite_character_assignment_tags"] += 1
        counters[kind + "_character_assignment_tags"] += 1

    for code, payload in iter_tags(data, offset, len(data)):
        if code == 1:  # ShowFrame is an authored snapshot, not runtime animation.
            counters["root_showframe_tags"] += 1
            occupied = len(depth_state)
            sprites = sum(character in defined for character in depth_state.values())
            max_sprite_depths = max(max_sprite_depths, sprites)
            max_occupied_depths = max(max_occupied_depths, occupied)
            if sprites:
                sprite_occupied_frames += 1
            frame += 1
        elif code == 4:
            if len(payload) < 4:
                raise ValueError("truncated PlaceObject")
            character, depth = struct.unpack_from("<HH", payload)
            counters["placeobject_tags"] += 1
            assign(depth, character, "placeobject")
        elif code in (26, 70):
            if len(payload) < (3 if code == 26 else 4):
                raise ValueError("truncated PlaceObject2/3")
            flags = payload[0]
            depth = struct.unpack_from("<H", payload, 1 if code == 26 else 2)[0]
            kind = "placeobject2" if code == 26 else "placeobject3"
            counters[kind + "_tags"] += 1
            parsed3 = placeobject3_character_id(payload) if code == 70 else None
            if flags & 0x02:
                if code == 26:
                    if len(payload) < 5:
                        raise ValueError("truncated PlaceObject2 character id")
                    character = struct.unpack_from("<H", payload, 3)[0]
                else:
                    character = parsed3
                if flags & 0x01 and depth not in depth_state:
                    counters["move_with_character_missing_depth_tags"] += 1
                assign(depth, character, kind)
            elif depth in depth_state:
                counters["no_character_existing_depth_tags"] += 1
            else:
                counters["no_character_missing_depth_tags"] += 1
        elif code in (5, 28):
            expected = None
            if code == 5:
                if len(payload) < 4:
                    raise ValueError("truncated RemoveObject")
                expected, depth = struct.unpack_from("<HH", payload)
                counters["removeobject_tags"] += 1
            else:
                if len(payload) < 2:
                    raise ValueError("truncated RemoveObject2")
                depth = struct.unpack_from("<H", payload)[0]
                counters["removeobject2_tags"] += 1
            existing = depth_state.get(depth)
            if existing is None:
                counters["remove_missing_depth_tags"] += 1
            elif expected is not None and expected != existing:
                counters["removeobject_character_mismatch_tags"] += 1
                # Fail closed: do not erase an unmatched instance.
            else:
                if existing in defined:
                    sprite_transitions.append({"root_frame": frame, "depth": depth,
                                               "sprite_id": existing, "kind": "sprite_character_removed"})
                    counters["sprite_removal_tags"] += 1
                del depth_state[depth]
                counters["remove_existing_depth_tags"] += 1

    return {
        "schema": "swf-root-depth-structural-evidence-v1",
        "source_swf_sha256": hashlib.sha256(raw).hexdigest(),
        "defined_sprite_count": len(defined),
        **{key: counters[key] for key in (
            "root_showframe_tags", "placeobject_tags", "placeobject2_tags", "placeobject3_tags",
            "removeobject_tags", "removeobject2_tags", "placeobject_character_assignment_tags",
            "placeobject2_character_assignment_tags", "placeobject3_character_assignment_tags",
            "sprite_character_assignment_tags", "sprite_removal_tags", "occupied_depth_assignment_tags",
            "move_with_character_missing_depth_tags", "no_character_existing_depth_tags",
            "no_character_missing_depth_tags", "remove_missing_depth_tags",
            "removeobject_character_mismatch_tags", "remove_existing_depth_tags")},
        "authored_frames_with_sprite_depths": sprite_occupied_frames,
        "max_sprite_depths_at_showframe": max_sprite_depths,
        "max_total_depths_at_showframe": max_occupied_depths,
        "sprite_depth_transition_count": len(sprite_transitions),
        "sprite_depth_transitions": sprite_transitions,
        "interpretation": "Root SWF authored depth state only; not actual runtime display list, visibility, "
                          "nested sprite instances, scripts, maps, NPCs or verified story events. "
                          "Character IDs and depth values are structural identifiers, not asset exports."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("swf")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = index_root_depth(args.swf)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Root depth: {} frames, {} sprite assignments, {} sprite removals, {} mismatched removes".format(
        report["root_showframe_tags"], report["sprite_character_assignment_tags"],
        report["sprite_removal_tags"], report["removeobject_character_mismatch_tags"]))


if __name__ == "__main__":
    main()
