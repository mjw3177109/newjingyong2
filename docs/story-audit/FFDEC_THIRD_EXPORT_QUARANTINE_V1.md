# FFDec 第三次导出候选隔离（v1）

当同一 CI 作业内 A/B 导出不一致、触发第三次 C 导出时，原有 `ffdec_stable_audit_set.json` 仅保证 A/B 所选候选的一致性；不能保证它们在 C 中仍相同。新增 `tools/quarantine_ffdec_third_export.py` 对 A/B 候选与 C 的匿名路径、内容 SHA-256 逐一核对。

- C 缺失路径：`missing_in_third_export`；C 同路径内容变化：`content_changed_in_third_export`；其余保留为 `three_export_content_agreement_unverified`。
- 输入须为同一 SWF，校验 A/B 候选清单哈希、候选 ID 与字段结构；拒绝篡改或语义注入。
- 仅在第三次导出实际发生时产生 `ffdec_third_export_quarantine.json` Artifact；没有第三次导出时不生成，不能假称已做三次复核。
- 输出仅含匿名哈希、数量、状态，不包含反编译源码、原路径、台词、图像或音频。三次内容一致也**不等于** FFDec 权威输出、跨 CI 稳定、已核实剧情或改编授权。原作已语义核实剧情事件仍为 **0**。

合成回归：`python -m unittest discover -s tests -p 'test_*.py'`。真实 FFDec 漂移条件下的 CI 分支仍需观察。
