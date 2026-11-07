# 根时间轴 AVM1 状态访问指令审查提示 v1

`tools/index_root_state_access.py` 针对已选定的根时间轴 `DoAction` 条件审查队列，重新读取原始 `jin.swf`，校验 SWF SHA-256、动作标签帧号/序号/哈希、顶层指令计数，并与前一阶段的字节级 IF/Jump 边证据逐条比对。任何不一致均拒绝生成报告。

工具只记录顶层 AVM1 `GetVariable`、`SetVariable`、`GetMember`、`SetMember`、`GetProperty`、`SetProperty`、`DefineLocal`、`DefineLocal2` 和 `StoreRegister` 的**指令类别与字节偏移**，以及每条 IF 前 8 条动作记录内的状态访问指令位置与记录距离。这可帮助在有权利的隔离环境中优先核查条件附近的读写线索。

输出：`reports/swf_root_state_access_hints.json`，CI Artifact：`swf-root-state-access-hints`。不解析或导出变量名、字符串、Push 常量、ActionScript 源码、函数体、原作美术、音频。指令位置并不代表栈值归属；前 8 条动作记录只是**线性邻近关系**，不能推断 IF 的条件依赖、分支实际执行路径、变量修改、NPC、地图、战斗数值或剧情事件。

所有候选继续标记 `unverified`，`verified_story_events` 为 **0**。只有在隔离环境结合 FFDec 私有脚本、原始时间轴、条件/副作用/结果的多重证据完成语义复核后，才能登记正式原作事件。FFDec 双导出曾出现间歇性漂移，不能将单次反编译结果视为稳定真值。PR 保持 Draft，未经相关改编/发布权利确认，不公开受保护剧情的商业成品。
