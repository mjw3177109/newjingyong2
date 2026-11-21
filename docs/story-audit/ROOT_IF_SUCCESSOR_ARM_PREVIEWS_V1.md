# 根时间轴 IF 双后继有限操作码预览 V1（2026-11-02）

## 本轮发现

此前 `swf_root_if_opcode_windows.json` 只展示 IF **之前**的无操作数操作码类别和语法前驱。即使已经核对了 IF 的分支目标与顺序后继坐标，私有审查人员仍缺少两个目标位置附近的**结构性副作用线索**，不易决定先检查哪条路径是否可能修改状态。不能因此声称恢复了剧情。

## 最小增量

更新 `tools/index_root_if_opcode_windows.py`，直接从原始 `jin.swf` 的根时间轴 DoAction 字节码，对每个优先 IF 的 `branch_target_offset` 与 `fallthrough_offset` 分别生成最多 **8 条记录**的无操作数预览：

- `successor_arm_windows.branch/fallthrough`：各自的起始字节偏移、有限记录偏移、操作码类别、写入类操作码提示计数、停止原因。
- 在遇到其他控制流入口（跳转目标）、分支、Return/Throw、不透明控制操作码、ActionEnd 或 8 条上限时停止，不跨越这些边界去猜测路径。
- 若两个后继相同，则 `successor_arms_distinct=false`；若目标就是 ActionEnd，则对应预览为空。
- 新增 `local_write` 与 `register_write` 类别，**只统计操作码**，不导出变量名、寄存器内容、Push 操作数、脚本字符串或美术音频。

现有 CI 的 `Derive operand-free IF opcode windows from original SWF` 步骤会自动运行该代码，输出仍放在原有 `swf-root-if-opcode-windows` Artifact，不增加新的源代码泄漏渠道。

## 验证与使用限制

新增 `tests/test_index_root_if_opcode_windows.py` 中的合成 AVM1 测试：两条后继分别含写操作码、遇到 Jump 立即停止、控制流汇合处停止、分支与顺序后继同为 ActionEnd 时返回空窗口。具体真实 `jin.swf` 的通过数量和测试总数以本提交后的 Actions 为准。

**关键限制：** 本报告只是从原始 SWF 中提取的线性局部字节码片段；即使某条分支窗口出现 `variable_write`，也不代表该写入实际执行、写入了哪个任务变量、对应哪张地图或触发了何种剧情。分支前的堆栈值、嵌套函数、动态跳转和运行时执行轨迹均未恢复。原作已语义核实事件仍为 **0**，`ready_for_html5_mapping` 仍为 **0**，不得将本报告当作 1:1 剧情还原证据。

## 下一步私有核验

以匿名 `review_id` 为索引，优先审查两个后继窗口写入提示不同的候选；在有权的隔离环境中结合 FFDec 私有脚本、AVM1 操作数、真实运行时记录和地图归属做人工复核。只有条件、状态变化、结果与来源坐标独立一致后，才允许将原作事件写入正式对照表。PR 保持 Draft，不修改 `main` 或商业发布策略。
