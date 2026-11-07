# 原始 IF 相邻操作码形状对照 V1（2026-11-02）

## 本轮目的与证据

前轮从 `jin.swf` 直接提取的 12 个优先 IF 位于根时间轴第 55 帧 / DoAction 9。其中偏移 6607–6904 的 10 个候选每隔 33 字节出现一次，并共享四项有限窗口统计提示。**相同计数不能证明它们的操作码排列相同**，更不能证明条件表达式相同。

新增 `tools/compare_root_if_opcode_shapes.py`，读取原始 SWF 校验链生成的 `swf_root_if_opcode_windows.json` 和 `swf_root_if_structural_clusters.json`，逐一比较等步长簇中相邻 IF 的：

- 保守直线前驱操作码类别序列与边界截断标志；
- 分支后继最多 8 条操作码类别及停止原因；
- 顺序后继最多 8 条操作码类别及停止原因。

结果仅输出匿名 ID、帧/Action/IF 偏移、三项相等标志与总相等标志，不包含 Push 操作数、常量、变量名、源码、音频、美术或原始脚本路径。校验 SWF SHA-256、候选覆盖、组别、排序、33 字节等步长等结构，不接受不认识的操作码类别或已核实剧情声明。

## 执行与验收

```bash
python tools/compare_root_if_opcode_shapes.py \
  --clusters reports/swf_root_if_structural_clusters.json \
  --windows reports/swf_root_if_opcode_windows.json \
  --out reports/swf_root_if_adjacent_opcode_shapes.json
python -m unittest tests.test_compare_root_if_opcode_shapes
```

GitHub Actions 的 `swf-inventory` 作业先重新解析原始 `jin.swf`、对原始 IF 证据重新核验，再执行本工具并上传 `swf-root-if-adjacent-opcode-shapes` Artifact。测试覆盖一致与不同的前驱/后继形状、顺序独立、无连续簇、坐标/来源/类别/状态篡改。

**解释限制：** 即使相邻 IF 的三组有限操作码类别序列完全一致，AVM1 Push 操作数、变量名、常量、运行时栈值及跳转目标仍可能不同；不同类别序列也不能证明不同剧情。当前原作剧情事件的语义核实数量为 **0**，不能据此映射到 HTML5 剧情表或宣称完成 1:1 复刻。

## 原始 SWF 实测结果（2026-11-02）

本轮 [Push Actions #41518235489](https://github.com/mjw3177109/newjingyong2/actions/runs/41518235489) 的四项作业全部成功；[PR Actions #41518243902](https://github.com/mjw3177109/newjingyong2/actions/runs/41518243902) 成功。Python 审计测试 **198/198**，HTML5 测试仍按既有门禁执行。新增的 `swf-root-if-adjacent-opcode-shapes` Artifact 由原始 `jin.swf` 审计链实际生成，源 SWF SHA-256 为 `d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30`。

- 10 个等步长 IF 构成 **9 组相邻对照**，其中 **8 组**的有限操作码形状完全一致。
- **6607 → 6640**：保守直线前驱操作码类别形状不同；两个后继的有限操作码形状均相同。匿名审核 ID 分别为 `3d9a54e4fd91c051c87c6050` 与 `c129bb397ede9b1ad08adc07`。
- **6640 → 6904** 的后续 8 组相邻对照：三部分有限形状均相同。
- Java 8 + FFDec 两次导出成功，首次文件数 4,560，第二次退出码 0；日志指纹仍不同，不能由此断言历史漂移问题根治。

这些是操作码类别形状的**结构性结果**，不代表已核实某个剧情事件。已语义核实原作剧情事件仍为 **0**，也没有将其映射到 HTML5 玩法。

## 下一步

读取真实 CI Artifact，先比较偏移 6607/6640，再按形状差异定位最值得在有权利的隔离环境中逐条核实的 AVM1 条件、FFDec 私有脚本和运行时结果。只有具备可复核的条件、状态效果、地图归属、运行时证据及权利确认，才将事件登记为原作已核实条目。PR 继续保持 Draft，不发布含第三方受保护剧情的商业成品。
