# 原始 SWF 根时间轴 IF：私有审查交接与操作码窗口交叉校验 V1

## 本轮发现

现有 `swf_root_if_audit_handoff.json` 和 `swf_root_if_opcode_windows.json` 分别生成，但缺少一个独立的、按 `review_id` 逐条检查同一 SWF 指纹、根帧、DoAction 序号与 IF 字节偏移的交接门禁。单独成功生成两个文件并不等于它们仍指向同一批 IF。

## 最小实现

新增 `tools/crosscheck_root_if_handoff.py`。从两份**不含原始脚本和操作数**的 JSON 中核对：SWF SHA-256、实际候选集合、逐条坐标、结构性未核实状态，以及窗口内有限的比较操作码/语法前驱计数。任何身份、数量或坐标不一致均失败，且不写出已核实事件。

CI 在原始 SWF 结构清点任务中运行并上传 `swf-root-if-handoff-window-crosscheck` 脱敏 Artifact。测试位于 `tests/test_crosscheck_root_if_handoff.py`，覆盖合法对齐、跨 SWF、坐标篡改、候选身份/重复、语义断言以及操作码计数异常。

## 证据边界与下一步

校验成功只能说明**结构性定位对齐**，不能还原 IF 条件表达式、确认运行时执行路径、推断剧情、地图、道具、战斗数值或授予改编权。`verified_story_events` 和 `ready_for_html5_mapping` 均固定为 **0**。后续须在有权的隔离环境中逐条审查原始 AVM1 字节码、FFDec 脚本与实际运行行为，并经独立核验后才可更新正式剧情事件对照表。
