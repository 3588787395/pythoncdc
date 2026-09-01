# 架构工程师分析报告 — Pass 1 / TERNARY 区域

## 方法定位
- `_identify_ternary_regions`: region_analyzer.py L11455-L13645（含 _detect_ternary_pattern ~1600 行过长）
- `_generate_ternary`: region_ast_generator.py L18310-L21200+（~3000 行过长）
- `_is_fused_ternary_false_value_block`: region_analyzer.py L14298-L14408（跨 LOOP↔TERNARY）

## 识别顺序
- Phase 2: CHAINED_COMPARE → BOOLOP → TERNARY → IF
- BOOLOP→TERNARY 已知反模式（衍生 5 处协调补丁 Fix 7.1-7.5），本轮不调换
- TERNARY→IF 顺序衍生 R19 Bug 22-24 修复（提前判别 if-elif-else 条件头）
- TERNARY→CHAINED_COMPARE 顺序衍生 Phase 7 方案 D（从 chained_compare_blocks 重建值块）

## 4 原则合规性
- 原则 1（自底向上归约）：违反 — BOOLOP→TERNARY 顺序 + 3 处提前判别其他 Pass 区域
- 原则 2（每块唯一归属）：基本合规但有 4 处后处理补丁（_loop_to_remove / _region_overlaps_with_ternary / to_remove / 解除 LoopRegion 块映射）
- 原则 3（嵌套即抽象节点）：合规 — TernaryRegion 是叶子值区域，父通过 entry 引用
- 原则 4（入口引用语义）：合规 — 父区域引用 condition_block（TernaryRegion.entry）

## 反模式检查
- 无禁止前缀方法名（_merge_block_is_loop_back_edge 是 merge_block 语义）
- 无硬编码深度上限（_visited_ft/_visited 集合防环）
- **实例驱动判据散布 10+ 处**: 子串匹配 'FALSE' in opname / RETURN_VALUE/RETURN_CONST 6处 / CALL+POP_TOP / 纯跳转 opname 列表 5处重复
- **后处理补丁 5+ 处**: _loop_to_remove / _region_overlaps_with_ternary / to_remove / _try_create_ternary_region 重复创建路径 / _is_fused_ternary_false_value_block 跨 LOOP
- **跨区域跨层次启发式 6 处**: TERNARY↔CHAINED_COMPARE / TERNARY↔LOOP / TERNARY↔MATCH

## 本轮建议修复（3 项，含失败用例修复尝试）
### 修复 1 — 抽取 _is_value_block_nested_if_header 局部 helper，消除 R19 Bug 22-24 修复 3 处重复
位置: region_analyzer.py L12291-L12356
策略: 在 _detect_ternary_pattern 内嵌套定义 _is_value_block_nested_if_header(vb)，基于 block_to_region[vb] 是 IfRegion 且 entry==vb 的结构判据，替换 3 处实例驱动重复实现
理由: 极低风险，消除实例驱动判据+重复代码，升级为 IfRegion 归属结构判据

### 修复 2 — 抽取 RETURN_TERMINATOR_OPS / PURE_JUMP_OPS 模块级常量 + 统一 helper
位置: region_analyzer.py L12144-L12161 + 5 处纯跳转列表重复 (L12270/L12491/L12583/L12620/L14395)
策略: 模块级定义 RETURN_TERMINATOR_OPS = frozenset({'RETURN_VALUE','RETURN_CONST'}) 与 PURE_JUMP_OPS = frozenset({'JUMP_FORWARD','JUMP_ABSOLUTE','JUMP_BACKWARD','JUMP_BACKWARD_NO_INTERRUPT'})，6处 RETURN 检查与 5 处纯跳转列表替换为常量引用
理由: 极低风险纯重构，消除重复字面量，集中维护

### 修复 3 — _is_call_without_value_used 增加 IfRegion 抢占判据（中风险，可能修复失败用例）
位置: region_analyzer.py L12165-L12178（_is_call_without_value_used 定义），调用点 L12202/L12381
策略: 在 has_call_pop 返回 True 时，额外检查 blk 是否已被 IfRegion 占用（block_to_region[blk] 是 IfRegion 且 entry==blk）；若未被 IfRegion 占用（即 print() 在 ternary 表达式上下文中作为值被消费），则允许 ternary 创建
理由: 将实例驱动 CALL+POP_TOP 判据升级为基于 IfRegion 归属的结构判据；可能修复 print(ternary) 类失败用例
注意: 必须验证 if x>0: print() else: print() 类语句仍正确识别为 IfRegion；若 IfRegion 仅在 Phase 3 识别则本修复可能引入回归，需回退

## 其他问题（后续迭代）
- BOOLOP→TERNARY 顺序调换（高风险）
- to_remove 后处理补丁消除（需识别期通过 claimed 集合预判）
- _is_fused_ternary_false_value_block 跨 LOOP↔TERNARY 启发式重构
- _detect_ternary_pattern / _generate_ternary 函数拆分（可维护性）
