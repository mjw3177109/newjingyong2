#!/usr/bin/env python3
"""Source-free direct root timeline sprite placement index (not story semantics)."""
import argparse
import hashlib
import json
import struct
from collections import defaultdict
from pathlib import Path

try:
    from tools.index_swf_sprite_timeline import load_swf, iter_tags
except ModuleNotFoundError:
    from index_swf_sprite_timeline import load_swf, iter_tags


def index_placements(path):
    raw, data, start = load_swf(path)
    defined = set()
    placements = []
    root_frames = 0
    tag_counts = {"placeobject_tag_count": 0, "placeobject2_tag_count": 0, "placeobject3_unparsed_tag_count": 0}
    move_only = 0
    for code, payload in iter_tags(data, start, len(data)):
        if code == 39:
            if len(payload) < 6:
                raise ValueError("truncated DefineSprite")
            sprite_id = struct.unpack_from("<H", payload)[0]
            if sprite_id in defined:
                raise ValueError("duplicate DefineSprite id")
            defined.add(sprite_id)
        elif code == 1:
            root_frames += 1
        elif code == 4:
            if len(payload) < 4:
                raise ValueError("truncated PlaceObject")
            character_id = struct.unpack_from("<H", payload)[0]
            tag_counts["placeobject_tag_count"] += 1
            placements.append((root_frames + 1, character_id, "placeobject"))
        elif code == 26:
            if len(payload) < 3:
                raise ValueError("truncated PlaceObject2")
            tag_counts["placeobject2_tag_count"] += 1
            flags = payload[0]
            if flags & 0x02:  # HasCharacter: flags + UI16 depth + UI16 character ID
                if len(payload) < 5:
                    raise ValueError("truncated PlaceObject2 character id")
                character_id = struct.unpack_from("<H", payload, 3)[0]
                placements.append((root_frames + 1, character_id, "placeobject2"))
            else:
                move_only += 1
        elif code == 70:
            # PlaceObject3 has optional class-name fields; never guess its ID offset.
            tag_counts["placeobject3_unparsed_tag_count"] += 1

    grouped = defaultdict(lambda: {"placeobject": 0, "placeobject2": 0})
    unresolved = 0
    for frame, character_id, kind in placements:
        if character_id in defined:
            grouped[(character_id, frame)][kind] += 1
        else:
            unresolved += 1  # May be a shape or other character; not necessarily invalid.
    rows = [
        {"sprite_id": sid, "root_frame": frame, "placeobject_count": counts["placeobject"],
         "placeobject2_count": counts["placeobject2"]}
        for (sid, frame), counts in sorted(grouped.items())
    ]
    referenced = {row["sprite_id"] for row in rows}
    return {
        "schema": "swf-root-sprite-placement-evidence-v1",
        "source_swf_sha256": hashlib.sha256(raw).hexdigest(),
        "root_showframe_tags": root_frames,
        "defined_sprite_count": len(defined),
        **tag_counts,
        "placeobject2_without_character_count": move_only,
        "non_sprite_character_placement_count": unresolved,
        "direct_sprite_placement_tag_count": sum(r["placeobject_count"] + r["placeobject2_count"] for r in rows),
        "directly_referenced_sprite_count": len(referenced),
        "sprite_definitions_without_direct_root_placement": len(defined - referenced),
        "direct_root_sprite_placements": rows,
        "interpretation": "Only direct root placements using PlaceObject/PlaceObject2. "
                          "PlaceObject3 and nested sprite placements are NOT resolved; "
                          "a placement is not proof of a story event, NPC, map or visible instance."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("swf")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = index_placements(args.swf)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Root sprite placements: {} tags, {} distinct sprites, {} PlaceObject3 tags not parsed".format(
        report["direct_sprite_placement_tag_count"], report["directly_referenced_sprite_count"],
        report["placeobject3_unparsed_tag_count"]))


if __name__ == "__main__":
    main()
