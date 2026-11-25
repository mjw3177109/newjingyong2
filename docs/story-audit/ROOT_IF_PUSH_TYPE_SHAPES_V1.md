# AVM1 ActionPush 类型形状私有对照 V1（2026-11-02）

## 发现的问题

上轮 9 对相邻 IF 的原始编码比较发现后继字节不同，但尚无法区分：差异仅来自同类型的私有常量/标识符，还是 ActionPush 类型序列本身发生变化。不能因此断言剧情条件不同。

## 本轮最小实现

- 新增 `tools/inspect_avm1_push_types.py`：仅在 CI 私有内存中解析 AVM1 ActionPush 的 0–9 类型标记，跳过原始字符串、数字、寄存器索引和常量池索引，不解码或输出值。
- `tools/compare_root_if_raw_operands.py` 保留原始 SWF 重新核验、匿名 ID 和原字节相等性结论，额外输出每个可比窗口的 `*_push_type_shape_comparison`，仅允许 `same`、`different`、`no_push`、`not_comparable`、`unparseable`。
- `tests/test_inspect_avm1_push_types.py` 使用合成字节码测试 10 类 Push 类型、不同值同类型、不同类型、截断和未知类型、缺失边界及短路隐藏异常。
- CI 既有 `swf-root-if-raw-operand-equality` Artifact 自动携带新字段，无需新工作流或原始脚本发布。

## 证据边界

`same` 只代表有限窗口中 Push 的类型标记序列相同，**绝不代表变量值、条件、地图、任务或剧情效果相同**；`different` 也不能证明剧情不同。遇到不完整/未知编码返回 `unparseable`，不猜测。输出不包含原作字节、变量名、字符串、数值、类型标记列表、音视频或图像。所有原作剧情候选仍为 `unverified`，已语义核实原作剧情事件仍为 **0**。

## 下一阶段

根据真实 CI Artifact 的各窗口 Push 类型形状差异，选择优先人工复核的 IF（偏移 6607/6640 起）；在具备相应权利的隔离环境中结合 FFDec 私有脚本、时间轴和运行时观察建立剧情事件对照表。未经核验不将结构提示移植为原作事件，不合并 Draft PR，不发布受保护剧情的商业成品。
