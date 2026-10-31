# 根时间轴 IF 私有语义审查交接单 V1（2026-10-31）

在既有 12 个优先 IF 结构审查任务包之后，新增逐条人工审查交接单，便于在合法授权的隔离环境里对照 FFDec 脚本和原始运行时。

生成命令：

    python tools/build_root_if_audit_handoff.py --packets reports/swf_root_if_review_packets.json --out reports/swf_root_if_audit_handoff.json
    python -m unittest discover -s tests -p 'test_*.py'

每条交接单包含匿名 review_id、原始帧号、DoAction 序号、动作 SHA-256、IF/分支偏移，以及七项尚未完成的核验门禁：FFDec 脚本哈希、条件、状态副作用、地图上下文、运行时复现、独立复核和改编发布权。

工具严格校验 SWF 指纹、任务数量、ID 唯一性、偏移和未核实状态；对伪造已核实事件或提前填写剧情语义直接失败。交接单不含脚本原文、变量名、台词、地图图像、音频或原作美术。

2026-10-31 增量安全修复：交接单不再只检查 `review_id` 是否为 24 位十六进制字符串，而是根据 `SHA256(SWF哈希:DoAction序号:动作哈希:IF偏移)` 重新计算前 24 位，拒绝将其他 IF 的审查身份套用到本条记录。还会根据静态可达性、同帧精灵变化、附近状态访问提示、真假分支是否不同重新计算结构优先级（权重 8/4/2/1），拒绝伪造优先级。新增四项回归测试覆盖 ID 篡改、偏移变更、SWF 指纹变更、优先级篡改。此处只校验结构证据链，不构成剧情语义或版权授权证明。

输出 verified_story_events=0、ready_for_html5_mapping=0。它是审查入口而非剧情语义证据；FFDec 历史偶发导出漂移也未解决。

下一阶段：按 12 个 review_id 逐条对照私有 FFDec 脚本，核实触发条件、状态变化、地图归属与运行时效果，并进行独立复核；取得相关改编发布权前不商业发布受保护剧情。
