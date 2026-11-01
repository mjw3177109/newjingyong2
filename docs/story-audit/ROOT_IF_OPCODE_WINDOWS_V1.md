# 根时间轴 IF 原始字节码上下文 V1（2026-10-31）

## 本轮目的

为已有的 12 个优先 IF 审查目标增加**直接取自 `jin.swf` 的操作码上下文**，使私有审查者能按 `review_id`、帧号、DoAction 序号和 IF 字节偏移定位证据，并快速判断是否存在比较运算、变量读取、调用或不透明控制流。此前仅有分支坐标和前八条状态访问提示，不能看出更一般的操作码类别。

## 执行

```bash
python tools/index_root_if_opcode_windows.py jin.swf \
  --packets reports/swf_root_if_review_packets.json \
  --out reports/swf_root_if_opcode_windows.json --width 12
python -m unittest discover -s tests -p 'test_*.py'
```

GitHub Actions 的 `swf-inventory` 作业将上传 `swf-root-if-opcode-windows` Artifact，包含每个目标 IF 前最多 12 条**线性字节码记录**的偏移与安全分类、比较操作码数量、是否存在分支或不透明控制流、SWF 指纹和审查 ID。对 SWF 指纹、动作 SHA-256、审查 ID、帧号、IF 字节偏移、分支目标和局部可达性进行独立复核；不一致直接拒绝。

**证据边界：** 线性前驱不等于执行路径，更不等于条件表达式。即使出现比较操作码，也不能推断比较对象、值、NPC、任务、地图、战斗机制或剧情含义。不会导出 Push 操作数、变量名、字符串、ActionScript、原始路径、音频或图像。所有条目仍是 `unverified`，`verified_story_events=0`。

## 后续

在有权利的隔离环境中，对照本次字节码类别与 FFDec 私有脚本，并以运行时证据核实触发条件、状态副作用、地图和事件效果。只有独立复核的真实事件才能加入正式剧情对照表；本次输出不能作为改编发布授权或 1:1 完成证明。
