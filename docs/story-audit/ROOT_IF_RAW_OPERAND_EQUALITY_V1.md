# 原始 AVM1 操作数私有相等性对照 V1（2026-11-02）

## 目的

上一阶段在原始 `jin.swf` 第 55 帧 / DoAction 9 的偏移 6607–6904 发现 10 个相邻等步长 IF；9 对中 8 对有限操作码类别形状一致。但**相同类别不等于相同原始操作数**。本轮增加对原始 SWF 的只读、私有字节级对照，不发布任何 Push 值、变量名、字节摘要或解编译源码。

## 实现

- `tools/compare_root_if_raw_operands.py` 在隔离 CI 运行器中重新读取 `jin.swf`，调用 `build_windows` 重新核验原始 IF 窗口，并重新计算结构形状报告；若传入报告被篡改则直接拒绝。
- 对每组相邻 IF 的保守前驱、分支后继、顺序后继窗口，比较相同 opcode 序列中长格式 AVM1 指令的**编码 payload 字节是否完全一致**。
- 只输出 `same`、`different`、`opcode_mismatch`、`no_encoded_operands` 或 `not_comparable` 五种状态，以及匿名审核 ID 和结构坐标；不输出操作码数值、操作数、字节长度、哈希、源码或媒体。
- `tests/test_compare_root_if_raw_operands.py` 使用合成 AVM1 字节码覆盖同值、异值、opcode 不同、无编码操作数、非法记录偏移和截断记录。
- `.github/workflows/validate.yml` 的 `swf-inventory` 在既有 IF 形状对照之后运行，并上传 `swf-root-if-raw-operand-equality` 脱敏 Artifact。

## 使用

```bash
python tools/compare_root_if_raw_operands.py jin.swf \
  --packets reports/swf_root_if_review_packets.json \
  --clusters reports/swf_root_if_structural_clusters.json \
  --windows reports/swf_root_if_opcode_windows.json \
  --shapes reports/swf_root_if_adjacent_opcode_shapes.json \
  --out reports/swf_root_if_raw_operand_equality.json
python -m unittest tests.test_compare_root_if_raw_operands
```

## 证据边界与下一步

即使字节完全相同，也不证明 AVM1 栈状态、运行时变量、地图、剧情条件或实际效果相同；`no_encoded_operands` 不能视为等价证据。若 `different`，仅证明相同 opcode 序列中至少一个编码 payload 不同。所有候选仍为 `unverified`，**原作已语义核实剧情事件仍为 0**。

下一阶段以本轮 CI 的真实输出为依据，优先核实偏移 6607/6640 的差异及后续重复 IF 的编码操作数是否相同，再在有权利的隔离环境中结合 FFDec 私有脚本和运行时观察，建立有来源的剧情/事件对照表。PR 保持 Draft，禁止将这些结构证据冒充原作剧情复刻或直接商业发布。
