# 根时间轴 IF 私有语义审查交接单 V1（2026-10-31）

在既有 12 个优先 IF 结构审查任务包之后，新增逐条人工审查交接单，便于在合法授权的隔离环境里对照 FFDec 脚本和原始运行时。

生成命令：

    python tools/build_root_if_audit_handoff.py --packets reports/swf_root_if_review_packets.json --out reports/swf_root_if_audit_handoff.json
    python -m unittest discover -s tests -p 'test_*.py'

每条交接单包含匿名 review_id、原始帧号、DoAction 序号、动作 SHA-256、IF/分支偏移，以及七项尚未完成的核验门禁：FFDec 脚本哈希、条件、状态副作用、地图上下文、运行时复现、独立复核和改编发布权。

工具严格校验 SWF 指纹、任务数量、ID 唯一性、偏移和未核实状态；对伪造已核实事件或提前填写剧情语义直接失败。交接单不含脚本原文、变量名、台词、地图图像、音频或原作美术。

输出 verified_story_events=0、ready_for_html5_mapping=0。它是审查入口而非剧情语义证据；FFDec 历史偶发导出漂移也未解决。

下一阶段：按 12 个 review_id 逐条对照私有 FFDec 脚本，核实触发条件、状态变化、地图归属与运行时效果，并进行独立复核；取得相关改编发布权前不商业发布受保护剧情。
