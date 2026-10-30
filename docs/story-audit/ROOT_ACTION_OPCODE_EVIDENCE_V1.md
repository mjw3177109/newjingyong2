# 根时间轴 DoAction 指令结构审计 v1

新增 `tools/index_swf_action_opcodes.py`，在不公开 ActionScript 源码、字符串、素材的前提下，对 `jin.swf` 根时间轴 `DoAction` 标签进行 AS1/AS2 顶层指令记录解析。统计 `If`、`Jump`、`GotoFrame`、`GotoLabel`、`WaitForFrame`、`DefineFunction` 等指令，记录帧号、动作标签序号、SHA-256 与有限错误类别。**函数定义体不递归解析**，条件真假、变量读写、跳转目标所属时间轴、剧情语义均未验证。

```bash
python tools/index_swf_timeline.py jin.swf --out reports/swf_main_timeline_evidence.json
python tools/index_swf_action_opcodes.py jin.swf --timeline reports/swf_main_timeline_evidence.json --out reports/swf_root_action_opcode_evidence.json
python -m unittest discover -s tests -p 'test_*.py'
```

工具对源 SWF 指纹、根时间轴 ShowFrame 和 DoAction 总数进行独立交叉校验；解析错误记录为 `parse_warnings`，不能视作已成功解析的逻辑。GitHub Actions 上传仅包含数字、帧号、SHA-256 和预定义错误类别的 `swf-root-action-opcode-evidence` Artifact。此报告不包含 ActionScript 原文、标签名称、素材或音频。`verified_story_events` 恒为 0。

下一步应在有权利的隔离环境中针对少量带条件分支的动作帧复核脚本的具体条件、变量写入、运行时跳转及对应地图/任务/战斗效果。语义核实前不得计入已复刻剧情，商业发布前须核实改编和发布权利。
