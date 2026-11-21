# IF 6607 repeated real-SWF Push evidence — 2026-11-20

## Independently checked artifact

- Repository: `mjw3177109/newjingyong2`; branch `feature/html5-qstyle-foundation`; PR #1 remains Draft.
- Workflow: https://github.com/mjw3177109/newjingyong2/actions/runs/44710600970 (run #1583; head `4e9dc585d7fdaa2cc9c4485e8b92e81058b1afbe`).
- Artifact ID: `14616437855`, `if6607-push-type-evidence`.
- Downloaded ZIP SHA-256 independently recomputed: `d67dfde18563c3e1b08a9ffb3794a83d52d4e1fc35195c6adbae7a3fccb70dcd`. This equals GitHub's artifact digest.
- ZIP contains one file: `if6607_push_types.json`. JSON was extracted and read, not inferred merely from a green CI job.
- Schema: `avm1-push-types-v1`; scope: `static-only`.

## Verified fields

| Offset | Opcode | Push type codes | Value count |
| --- | --- | --- | --- |
| 6612 | Push | [8, 7] | 2 |
| 6622 | SetVariable | boundary confirmed | — |
| 6623 | Push | [8] | 1 |
| 6629 | Push | [7] | 1 |

The artifact reports `push_ends_at_set_variable=[6612]`. Type 8 denotes an AVM1 constant-pool index; type 7 denotes a 32-bit integer. All three Push records explicitly say `literal_values_exported=false`.

These values match the previously independently examined artifact `14613391581` as recorded in `IF6607_REAL_PUSH_EVIDENCE_20261120.md`; this is repeatability of **static structural fields**, not runtime equivalence or proof of an original plot event.

## Explicit unknowns and gate

`set_variable_target`, `set_variable_value`, and `condition_stack_origin` remain `unknown`; `verified_story_events=0`. Push adjacency does not by itself prove the runtime stack value reaching SetVariable, nor the meaning of Less2 @6604 / If @6607. Do not add a story-event mapping or claim original plot fidelity from these fields.

Next: privately trace stack producers/consumers across the branch and verify both branch outcomes against original execution, retaining only non-protected offsets/hashes in public reports. Independently confirm source provenance before mapping a verified event into HTML5. Keep main untouched and PR Draft; no third-party assets or protected script text should be published.
