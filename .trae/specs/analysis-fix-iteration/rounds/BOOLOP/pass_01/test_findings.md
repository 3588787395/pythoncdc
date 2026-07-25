# 架构工程师分析报告 — Pass 1 / BOOLOP 区域

## 方法定位
- `_identify_boolop_regions`: region_analyzer.py L13655-L14275（420 行，200+ 行注释）
- `_detect_boolop_conditional_chain`: region_analyzer.py L15143-L15779（636 行，最复杂）
- `_generate_boolop`: region_ast_generator.py L17437-L18309（872 行过长）
- `_build_boolop_expression`: region_ast_generator.py L16977-L17342

## 识别顺序
- Phase 2: CHAINED_COMPARE → BOOLOP → TERNARY → IF
- BOOLOP→TERNARY 已知反模式（违反原则 1），衍生 5 处协调补丁（_boolop_overlaps_with_ternary 后过滤 / _is_boolop_ternary_candidate / Edit A hop / Edit H merge / Fix 7.1 占用检查）。本轮不调换顺序（高风险）。

## 4 原则合规性
- 原则 1（自底向上归约）：违反 — BOOLOP→TERNARY 顺序 + 5 处后处理补丁
- 原则 2（每块唯一归属）：基本合规 — claimed 集合 + loop_condition_blocks 例外 + 双角色 merge_block 结构判据
- 原则 3（嵌套即抽象节点）：合规 — BoolOp 通过 entry 引用 ternary/chained-compare 子区域（Fix 7.1 + hop 逻辑）
- 原则 4（入口引用语义）：合规 — 父 IfRegion/LoopRegion 引用 BoolOpRegion.entry / prefix_block

## 反模式检查
- 无禁止前缀方法名（_merge_* 均为 merge_block 语义方法，_temp_region 是局部变量）
- **硬编码深度上限**: `_walk_count < 5` (L15505) — _is_scenario_b_ternary 检测
- **后处理补丁 5 处**: _detect_boolop_after_chained_compare (生成期绕过归约) / guard_idx 修剪 (L14053+L14179 重复) / value block 扩展 (L14248) / _while_boolop_data 事后删除 IfRegion (L1396) / _boolop_overlaps_with_ternary 事后过滤 (L1360)
- **跨区域跨层次启发式**: guard_idx 修剪（BOOLOP↔LOOP 变量名分析）
- **实例驱动判据**: _is_not_ternary_boolop_pattern 重复实现 exit 等价比较 (L11619-11624)，未委托 _is_equivalent_exit_block
- **子串匹配判据散布 6+ 处**: `'FALSE' in opname` 等，需 _normalize_none_check_op_types 后处理修正

## 本轮建议修复（3 项，聚焦反模式消除）
### 修复 1 — 消除硬编码深度上限 `_walk_count < 5`
位置: region_analyzer.py L15505
策略: 删除 `_walk_count < 5` 与 `_walk_count += 1` (L15537)，仅保留 `_visited_ft` 集合判别
理由: _visited_ft 已防环，<5 多余且漏检深度更大的合法 ternary 模式；极低风险

### 修复 2 — 统一 guard_idx 修剪逻辑，移至区域创建期
位置: region_analyzer.py L14053-L14130（主循环修剪）与 L14179-L14214（while 条件重识别后修剪）重复实现
策略: 抽取为 `_trim_boolop_guard_prefix(region, loop_region)` 辅助方法，在 _create_boolop_region_from_chain (L14931) 创建期一次性调用
理由: 消除后处理补丁 + 减约 100 行重复代码；变量名启发式收敛到单一调用点

### 修复 3 — _is_not_ternary_boolop_pattern 委托 _is_equivalent_exit_block
位置: region_analyzer.py L11619-L11624
策略: 将实例驱动 exit 等价比较替换为 `self._is_equivalent_exit_block(fv_exit_bo, tv_exit_bo)`；若 helper 不够则扩展其内部规则
理由: 消除实例驱动判据，统一等价判别入口

## 其他问题（后续迭代）
- BOOLOP→TERNARY 顺序调换（高风险，影响全流水线）
- _detect_boolop_after_chained_compare 生成期后处理移除
- 子串匹配 'FALSE' in opname 统一替换为结构判据
