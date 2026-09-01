# 架构工程师分析报告 — Pass 1 / MATCH 区域

## 方法定位
- `_identify_match_regions`: region_analyzer.py L7648-L7747
- `_generate_match`: region_ast_generator.py L15266-L16054
- 关键补丁: `_detect_undetected_wildcard_match` (L16056), `_apply_or_capture_name` (L8099), `_verify_literal_match_chain` (L7590)

## 4 原则合规性
- 原则 1（自底向上归约）：部分违反 — Phase 2 后反向过滤 match_regions (L1251, L1338) + _detect_undetected_wildcard_match 跨阶段补建
- 原则 2（每块唯一归属）：基本合规 — preserves_against_nested_match 保护；但通配符 match 虚拟块创建+字段突变+except吞异常违反
- 原则 3（嵌套即抽象节点）：部分违反 — _generate_match 内对 case body 中 IfRegion/LoopRegion 重新判定块归属
- 原则 4（入口引用语义）：部分违反 — 通配符 match subject==body 同块需 case_body_start_indices 切分，破坏入口块抽象

## 反模式检查
- 无禁止前缀方法名（_merge_block_is_loop_back_edge 在 L18325 非MATCH专属）
- **硬编码上限**: `_detect_undetected_wildcard_match` 中 `len(entry_block.instructions) < 3` / `> 10` (L16076, L16079)；`len(case_blocks) > 2` (L7643)
- **后处理补丁**: _detect_undetected_wildcard_match (跨阶段补建虚拟 MatchRegion) / 通配符 match 虚拟块创建+区域字段突变+except吞异常 (L15433) / _apply_or_capture_name (从body反推模式名) / _region_overlaps_with_ternary 反向过滤 match (L1338)
- **跨区域越权**: _identify_match_regions 在 block 已属 TRY/LOOP/WITH 时开捷径创建 MatchRegion (L7704) 与 Phase 2.5 _identify_nested_match_regions 职责重复
- **指令名判据密集**: COPY+COMPARE_OP 三种模式 / NOP 前缀 / PATTERN_ONLY_OPS 14 opname / DEFINITIVE_PATTERN_OPS 重复定义
- **DRY 违背**: _collect_pattern_store_names (analyzer L7749 vs generator L16271 完全相同) / _mr_compute_case_body_start_indices vs _compute_body_block_start / MatchOr 合并逻辑两处重复
- **STORE_DEREF 缺失**: L7505 walrus 排除判据 4→3 元组，闭包内 walrus 可能误判

## 本轮建议修复（3 项，零/低风险，聚焦反模式消除）
### 修复 1 — 补全 _is_match_subject_block 的 STORE_DEREF
位置: region_analyzer.py L7505
策略: 扩展为 `('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')` 四元组，与代码库其余 40+ 处一致
理由: 零语义风险，覆盖闭包/嵌套函数 walrus 场景

### 修复 2 — 合并 _collect_pattern_store_names 重复实现
位置: region_analyzer.py L7749-L7780 与 region_ast_generator.py L16271-L16302（完全相同）
策略: 下沉到 pattern_parser 模块，analyzer 与 generator 都调用 pattern_parser.collect_pattern_store_names
理由: 零归约语义风险，纯重构，消除 DRY 违背

### 修复 3 — 移除 _verify_literal_match_chain 的硬编码 case 数阈值
位置: region_analyzer.py L7634-L7644
策略: 删除 `and len(case_blocks) > 2` 条件，保留 reload_count 单一判据；或更彻底替换为 COPY 结构判据
理由: 消除硬编码 case 数阈值；COPY 判据是结构判据（match 必生成 COPY，if-elif 不生成）比计数启发式更严格，不回归

## 其他问题（后续迭代）
- _detect_undetected_wildcard_match 跨阶段补建移除（高风险）
- _region_overlaps_with_ternary 反向过滤移除（需先在识别期拒绝 TERNARY 内部块）
- _identify_match_regions 越权捷径与 Phase 2.5 职责合并
- 通配符 match 虚拟块创建+区域字段突变+except吞异常移除
