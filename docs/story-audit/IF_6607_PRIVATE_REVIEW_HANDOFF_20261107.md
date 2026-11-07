# Root frame 55 / DoAction 9 / IF 6607 — private verification handoff (2026-11-07)

**Status: unverified.** This is an evidence-oriented review ticket, **not** an original-game story event, verified predicate, or HTML5 mapping. No original script text, paths, dialogue, graphics, or audio are included.

## Reproducible source coordinates

- Source: `jin.swf`; recorded SHA-256 `d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30`.
- SWF root timeline, frame **55**, DoAction index **9**.
- Candidate ID: `3d9a54e4fd91c051c87c6050`.
- `ActionIf` byte offset **6607**; branch target **6623**; fallthrough **6612**.
- Prior bounded opcode window: one comparison opcode; branch-side write hints **0**, fallthrough-side write hints **1**. These are *counts in limited windows*, not a reconstructed predicate or proven state effect.
- Nearby access hints from the earlier audit: GetVariable **6588**, SetVariable **6589**, GetVariable **6595**. Proximity alone does not establish data dependence, execution order, or variable identity.

Source evidence: [2026-11-04 frame-55 audit](ROOT_FRAME55_CANDIDATES_20261104.md), [Actions #41916211704](https://github.com/mjw3177109/newjingyong2/actions/runs/41916211704), [IF opcode windows artifact](https://github.com/mjw3177109/newjingyong2/actions/runs/41916211704/artifacts/13365201808), [state access hints artifact](https://github.com/mjw3177109/newjingyong2/actions/runs/41916211704/artifacts/13364942226), [reconciliation artifact](https://github.com/mjw3177109/newjingyong2/actions/runs/41916211704/artifacts/13363664187).

## What the current parser can and cannot establish

`tools/avm1_first_predicate.py` is a **linear, isolated AVM1 action-stream** analyzer. It can fold only certain known boolean stack operations. It does not execute the root frame's full control-flow graph, resolve runtime variables, or infer the effect of `ActionSetVariable` / `ActionStoreRegister`. Encountering state mutation before an IF yields `state_mutation_before_if` rather than an invented predicate. A literal candidate in a synthetic test is not proof about IF 6607.

The previous branch-head CI for `b1e17d7` completed successfully: [Actions #42420473773](https://github.com/mjw3177109/newjingyong2/actions/runs/42420473773). That validates the workflow, **not** the semantics of this candidate.

## Required private review, in order

1. Verify the SWF digest and FFDec Java 8 export provenance in an authorized isolated environment; retain script hash and tool version privately.
2. Extract the *actual isolated DoAction 9 action stream* with offsets; confirm 6607/6612/6623 boundaries against the same bytes. Do not feed the whole SWF or decompiled text to the isolated-stream analyzer.
3. Trace stack producer(s) of IF 6607 through control-flow joins, variable reads/writes and coercions; mark each unresolved input `unknown`. In particular investigate the 6588/6589/6595 hints without assuming a dependency.
4. Independently observe both branch-taken and fallthrough executions with controlled initial state; capture changes to variables, frame/timeline, battle or inventory **only when actually observed**.
5. Identify scene/NPC/quest/story semantics only from corroborated private source and runtime evidence. Check authorization for adaptation and distribution separately.
6. Only then populate [the source-event ledger](README.md), with stable evidence references and tests. If either branch, predicate, or effect remains unresolved, keep `verified_story_events=0` for this candidate.

## Current ledger gate

| Field | Value |
| --- | --- |
| source_event_id | none (candidate only) |
| predicate | unknown |
| taken branch effect | unknown |
| fallthrough effect | unknown |
| map / NPC / quest / battle meaning | unknown |
| private runtime attestation | absent |
| rights attestation | absent |
| html5_event_id | none |
| ready_for_html5_mapping | false |

This document adds a traceable review plan and provenance; it **does not** increase verified story-event count or claim a playable original-story route.
