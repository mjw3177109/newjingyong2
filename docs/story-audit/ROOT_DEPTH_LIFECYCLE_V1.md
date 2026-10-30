# 根时间轴 Depth 实例状态结构审计（v1）

## 目的与范围

新增 `tools/index_swf_root_depth.py`，在不导出原作脚本、图像、音频、文字或类名的前提下，记录原始 SWF **根时间轴**的角色 ID 放置、Depth 覆盖、移动/属性更新以及移除标签。它只模拟文件中按顺序排列的标签，**不运行 ActionScript**，不声称还原真实播放状态、NPC、地图、剧情或战斗。

## 实现与证据

运行：`python tools/index_swf_root_depth.py jin.swf --out reports/swf_root_depth_evidence.json`。

- 两次扫描：先收集根层 `DefineSprite` ID，再按顺序处理顶层标签；嵌套 `DefineSprite` 内的放置不算根层放置。
- `PlaceObject` (4)、`PlaceObject2` (26)、`PlaceObject3` (70)：仅有 CharacterId 时更新对应 Depth 的 ID。无 CharacterId 的更新不计为新放置。对 PlaceObject3 的可选 ClassName 只验证/跳过，不记录字符串。
- `RemoveObject` (5)：仅在 CharacterId 与 Depth 中记录的 ID 相符时移除；不匹配计入异常，不擅自删除。`RemoveObject2` (28) 按 Depth 移除。
- `ShowFrame` (1)：记录根时间轴作者标签序列的 Depth 占用统计。包括含精灵的帧数、同时占用的最大精灵 Depth 数；这些不等于运行时可见对象数。
- 输出包括源文件 SHA-256、标签与异常计数、数值 ID / 帧 / Depth 级别的精灵结构转换。**不输出任何 SWF 素材、脚本文本、文件内字符串或类名**。
- 对缺失 Depth、Move+Character 缺失原 Depth、RemoveObject ID 不符分别计数，不伪造匹配或推断隐藏状态。
- 5 项合成 SWF 测试覆盖放置→更新→替换→移除、旧式 RemoveObject ID 不匹配、非精灵 Depth、压缩/非压缩、嵌套隔离、异常标签拒绝。测试数据全部原创。
- GitHub Actions 的 `swf-inventory` 作业上传 `swf-root-depth-evidence` Artifact；报告数字以对应成功运行的 Artifact 为准。

## 严格限制

SWF 时间轴可以循环、跳转并由 ActionScript 动态改变显示列表。本索引不模拟 `gotoAndPlay`、`attachMovie`、动态深度操作、嵌套时间轴、遮挡或真实渲染。单个 CharacterId 也不等于角色或事件。历史 FFDec 双导出存在偶发漂移；本工具独立读取原始 SWF 结构，不代表 FFDec 漂移已解决。

**已核实的原作剧情事件：0 条。** 下一阶段需要在有权利的隔离环境中，结合稳定脚本、主/精灵时间轴和逐事件条件/效果证据核验；在授权确认前不发布受保护剧情的商业成品。
