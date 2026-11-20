# IF 6607 / Java 8 recovery checkpoint — 2026-11-20

## Verified source and scope

- Repository: `mjw3177109/newjingyong2`; development branch `feature/html5-qstyle-foundation`; base `main` remains unchanged.
- PR: https://github.com/mjw3177109/newjingyong2/pull/1 (Draft).
- Head checked: `4e9dc585d7fdaa2cc9c4485e8b92e81058b1afbe`.
- Associated CI: https://github.com/mjw3177109/newjingyong2/actions/runs/44710600970 (run #1583, completed success).
- Four successful jobs: `html5-tests`, `browser-smoke`, `swf-inventory`, `ffdec-java8-probe`.
- `ffdec-java8-probe` job 136200991941: `actions/setup-java@v4` and private FFDec CLI export both succeeded. The preceding run's Java 8 gzip installation failure did not recur; this is **not** proof that the transient issue has been permanently fixed.
- The CI uploaded `if6607-push-type-evidence` and source-free FFDec artifacts. All protected scripts and media remain outside this document.

## Evidence boundaries

Previous real-SWF Push evidence from the earlier audited artifact: `6612` = types [8,7]; `6623` = [8]; `6629` = [7]; `6622` = SetVariable boundary. These are **static** bytecode facts only. This checkpoint independently verifies the latest CI steps executed, but does not claim to have re-extracted or compared the contents of the new Push artifact.

No source-level variable names, conditional operands, branch runtime effects, map IDs, battle values or original plot events have been semantically verified. Verified original story events: **0**.

## Next smallest meaningful change

1. Independently read the new `if6607-push-type-evidence` artifact, verify its ZIP digest and JSON schema, and compare it to the earlier audited types and adjacency.
2. In an authorized private workspace, reconstruct the AVM1 stack reaching `Less2 @6604`, `If @6607`, `Push @6612`, `SetVariable @6622`; identify constant-pool entries only privately, and confirm actual branch behavior by state-differential execution.
3. Add one source-linked event row **only after** independent semantic confirmation, then implement its HTML5 equivalent and tests. Keep PR Draft and refrain from shipping protected plot content without rights clearance.

This file is an audit checkpoint, not a claim of gameplay implementation or complete 1:1 replication.
