# 架构工程师分析报告 — Pass 1 / WITH 区域

## 方法定位
- `_identify_with_regions`: region_analyzer.py L7165-L7236
- `_generate_with`: region_ast_generator.py L14155-L15094（~940 行过长）
- 关键补丁: `_filter_if_blocks_in_with` (L13994), `_is_with_exit_cleanup` (L4456), `_collect_normal_exit_cleanup` (L7014)

## 4 原则合规性
- 原则 1（自底向上归约）：部分违反 — async-with SEND 循环被 LOOP 先识别为 LoopRegion，生成期 patch 掉
- 原则 2（每块唯一归属）：违反 — WITH cleanup 块同时归属 WithRegion/TryExceptRegion/IfRegion，需 save-mutate-restore
- 原则 3（嵌套即抽象节点）：违反 — _generate_with 反复遍历 self.regions 按 isinstance 筛选子区域
- 原则 4（入口引用语义）：部分违反 — async SEND LoopRegion 用 opname 集合判定而非入口引用

## 反模式检查
- 无禁止前缀方法名（变量名 _try_else_fixup/_if_blocks_fixup/_fallback 违反补丁模式但非方法名）
- 无硬编码深度上限（_is_with_exit_leading_to_break 显式注释不使用）
- **硬编码 magic number**: `+1000` (L7030), `+100` (L6883)
- **指令名判据密集**: ASYNC_WITH_SEND_LOOP_OPS 5元组重复4处 (L14323/14329/14344/14953), WITH_EXIT_INDICATOR_OPS 13 opname, _extract_with_items 23 opname 白名单
- **后处理补丁**: _filter_if_blocks_in_with / _try_else_fixup / _if_blocks_fixup / async target 三重检测
- **文档失真**: L7172 docstring "在 TRY 之后 LOOP 之前" vs 实际 TRY→LOOP→WITH

## 本轮建议修复（3 项，零/低风险，聚焦反模式消除）
### 修复 1 — 消除 `_collect_normal_exit_cleanup` 的 magic number +1000
位置: region_analyzer.py L7014-7065, 重点 L7030
策略: 将 `_collect_with_cleanup_blocks` 已计算的 exc_target（WITH_EXCEPT_START 偏移）作为参数传入，上界改为 exc_target: `body_end <= instr.offset < exc_target`
理由: exc_target 是语义上界，与 _extend_with_body_end(L6900) 一致；行为等价或更精确；消除硬编码

### 修复 2 — 抽取重复的 async-SEND-loop opname 集合为命名常量
位置: region_ast_generator.py 4 处重复 L14323/14329/14344/14953
策略: 模块级定义 `ASYNC_WITH_SEND_LOOP_OPS = frozenset({'SEND','YIELD_VALUE','RESUME','JUMP_BACKWARD_NO_INTERRUPT','NOP'})` + 谓词方法 `_is_async_with_send_loop(loop_region, with_region)`，4 处 inline 替换为调用
理由: 纯重构无行为变化，消除 DRY 违反，集中指令名判据便于后续用入口引用语义替换

### 修复 3 — 修正 `_identify_with_regions` docstring 归约顺序
位置: region_analyzer.py L7172
策略: 改为 "在 TRY、LOOP 之后，MATCH/ASSERT 之前；优先级第三档"，补注 async-with SEND 循环当前由生成期 patch 处理（待归约期消除）
理由: 零行为风险，消除 stale 文档，显式登记已知反模式

## 后续根因修复方向（不在本轮）
- 归约期归属 async-with SEND 循环（消除 4 处 patch + 三重 target 检测）
- _is_with_exit_cleanup 改为区域归属查表
- _filter_if_blocks_in_with 整方法删除（识别期排除 cleanup 块）
- _try_else_fixup/_if_blocks_fixup save-mutate-restore 模式消除
