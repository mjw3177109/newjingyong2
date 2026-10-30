# 主时间轴动作/标签与精灵 Depth 变更的结构交叉索引（v1）

## 目标

在不读取或发布原始脚本文本、角色、图像、音频、帧标签字符串的前提下，交叉验证两个独立的原始 SWF 结构索引：`swf_main_timeline_evidence.json`（DoAction/FrameLabel 帧号）与 `swf_root_depth_evidence.json`（根时间轴精灵放置、替换、移除帧号）。仅输出**同一作者帧内同时存在两类标签**的数值索引，作为后续在有权利的隔离环境中人工核实的排查队列。

## 运行与验证

```bash
python tools/index_swf_timeline.py jin.swf --out reports/swf_main_timeline_evidence.json
python tools/index_swf_root_depth.py jin.swf --out reports/swf_root_depth_evidence.json
python tools/correlate_root_action_depth.py --timeline reports/swf_main_timeline_evidence.json --depth reports/swf_root_depth_evidence.json --out reports/swf_root_action_depth_correlation.json
python -m unittest discover -s tests -p 'test_*.py'
```

输入必须是对应版本的结构证据、具有相同的源 SWF SHA-256，且根帧数、动作/标签数、精灵赋值/移除数和转换总数自洽。否则直接失败，不生成貌似有效的对照。GitHub Actions 的 `swf-inventory` 作业会运行交叉索引并上传 `swf-root-action-depth-correlation` Artifact；真实数字以该次成功运行的 Artifact 为准。

## 解释边界与后续

输出的 `overlap_frames` 仅含帧号、动作标签数、帧标签数、精灵赋值/移除/替换标签数，不含原始脚本、标签文字、角色名称或资源。**同帧出现不证明动作导致了精灵变更**：Flash 时间轴可循环、跳转，脚本还可动态创建/销毁对象。本报告的 `verified_story_events` 固定为 0，不可用于宣称已复刻剧情、地图、战斗数值或真实运行流程。

下一阶段应在受控隔离环境中逐条核验：稳定 FFDec 导出候选 → 关联帧/脚本 → 原始触发条件 → 变量读写/事件效果 → 对应 HTML5 事件/测试；核实前不得写成已恢复原作剧情。商业发布前须核实相关改编与发布权利。
