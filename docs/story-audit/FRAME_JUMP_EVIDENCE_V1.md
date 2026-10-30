# FFDec 字面帧跳转证据 v1（2026-10-30）

## 目的与范围

本阶段只检查同一轮 Java 8 + FFDec 临时导出的前 100 个匿名脚本候选，检测 gotoAndPlay(N) / gotoAndStop(N) 中 N 为十进制整数字面量的调用，并记录 1 起始行号、play/stop 模式及数字。新脚本先将字符串与注释遮蔽，避免将注释和台词误判为跳转。

仅在 `if (简单条件) { gotoAndPlay(整数); }` 这种**单语句花括号结构**里，生成条件表达式的 SHA-256 匿名指纹。不能据此断言条件实际生效、目标帧属于主时间轴、剧情发生、任务已完成、地图已识别。

## 证据与隐私

- 输入 `jin.swf` SHA-256、匿名审查队列、FFDec 同批次导出文件；核验 SWF、候选 ID、文件哈希和总文件数，不匹配则拒绝输出。
- 输出 `reports/ffdec_frame_jump_evidence.json`，包含候选 ID、匿名路径/内容哈希、字面帧跳转次数、行号、模式、字面帧参数、简单 if 条件哈希和截断标记。
- 仅输出脱敏 JSON Artifact；原始 ActionScript、路径、角色名、对话、美术和音频不公开上传。
- 不支持动态帧参数、嵌套括号复杂条件、动态脚本注入或完整 ActionScript 语义；漏报是预期行为。正则表达式匹配结果不是 CFG/AST。

## 验收及后续

运行 `python -m unittest discover -s tests -p 'test_*.py'`，新增四项合成脚本测试。真实数量以 GitHub Actions 的 `ffdec-java8-probe` 日志为准，不预设跳转数量。

下一步在有权利的隔离环境中把匿名候选与真实脚本上下文、精灵时间轴、原始 SWF 帧标签交叉核对。只有经过语义核验、记录来源和触发/效果证据后，才能新增正式剧情事件对照表行；当前 verified_story_event_count = 0。
