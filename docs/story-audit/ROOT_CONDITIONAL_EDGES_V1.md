# 原始根时间轴条件分支边界证据 v1

新增 `tools/index_root_conditional_edges.py`，从原始 `jin.swf` 的根时间轴 DoAction 标签中，对已有的前 50 条脱敏条件审查候选重新校验 SWF SHA-256、帧号、动作标签序号、动作 SHA-256、指令计数及解析警告。只在交叉核验成功时输出顶层 `If`/`Jump` 的源字节偏移、目标字节偏移、方向与是否命中动作记录边界。

输出 `reports/swf_root_conditional_edges.json`，CI Artifact 名为 `swf-root-conditional-edges`。它不包含原始字节码、反编译脚本、原作字符串、场景/人物名称、图像或音频；仍将所有条目标记为 `unverified`，已核实剧情事件固定为 **0**。

本工具**不能**证明 If 条件表达式的含义、变量副作用、地图归属、运行时可达性、NPC 对话或战斗结果；嵌套函数体仍不解析。即使边界全部有效，也不能当作剧情完成度或 1:1 复刻证据。FFDec 的历史间歇性导出漂移独立存在。

在隔离且有合法审查权限的环境中，下一步可利用 `root_frame`、`action_tag_ordinal`、`action_sha256`、`source_offset` 定位候选，并对照 FFDec 私有脚本人工核实条件、写入及实际效果。仅经过独立证据复核的事件才能登记到 `docs/story-audit/README.md`。未经相关改编及发布授权，不公开原作受保护剧情的商业成品。
