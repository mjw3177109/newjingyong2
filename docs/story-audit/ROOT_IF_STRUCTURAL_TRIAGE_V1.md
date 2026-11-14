# 根时间轴 IF 双后继结构差异审核排序 V1（2026-11-02）

## 本轮发现

原有 `swf_root_if_handoff_window_crosscheck.json` 已能列出每个优先 IF 两条后继的有限写入操作码提示，但人工审查仍需逐条寻找差异。报告没有稳定的审核顺序，容易反复检查没有结构差异的候选。

## 最小实现

- `tools/crosscheck_root_if_handoff.py` 新增 `rank_structural_review_targets`，在**现有交叉校验完成之后**生成 `structural_review_triage`，不改变原始 `entries` 顺序或格式。
- 排序优先级依次为：双后继写入提示数量不同、至少一侧出现写入提示、IF 前安全窗口含比较操作码、存在语法可达前驱、写入提示数量差值，最后按帧/Action/偏移/匿名 ID 稳定排序。
- 输出匿名审核 ID、帧/Action/IF 偏移、双后继写入操作码数量和统计总数。每条均保留 `review_status=unverified`；不输出操作数、变量名、脚本、图像或音频。
- 复用既有 GitHub Actions `swf-inventory` 流程和 `swf-root-if-handoff-window-crosscheck` Artifact，不新增网络接口或私有材料上传。CI 仍先用原始 `jin.swf` 重新生成窗口和交接表，拒绝不匹配报告。
- 新增 4 项合成数据回归测试：单候选集成、差异优先、伪造/重复拒绝、同分排序确定性。

## 证据边界

排序是**有限操作码类别的人工审查优先级**，不是剧情语义识别。两个窗口写入提示相同不代表效果相同；零提示不代表无副作用；语法可达不代表运行时执行。12 个优先 IF 的实际差异数量必须从本提交后真实 Actions Artifact 读取，不得预填。

目前已语义核实原作剧情事件仍为 **0**，`ready_for_html5_mapping=0`。完整原作剧情、地图、数值及改编发布权利均未得到本轮确认。

## 下一步

下载本轮 CI 生成的脱敏交叉核验报告，优先按 `structural_review_triage.review_order` 审核双后继差异候选。在有权的隔离环境中逐条结合 FFDec 私有脚本、AVM1 操作数、地图上下文和运行时结果交叉核实；只有证据完整才写入正式剧情/事件对照表。
