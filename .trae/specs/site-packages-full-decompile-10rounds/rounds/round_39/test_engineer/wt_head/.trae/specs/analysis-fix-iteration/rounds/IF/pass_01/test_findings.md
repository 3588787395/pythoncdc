# 架构工程师分析报告 — Pass 1 / IF 区域

## 方法定位
- `_identify_conditional_regions`: region_analyzer.py L10105-L10754
- `_generate_if`: region_ast_generator.py L6588-L6646
- 关键辅助: `_detect_boolop_chain_start` (L14672), `_detect_boolop_conditional_chain` (L15185)

## 识别顺序问题
当前 analyze() Phase 2 顺序: CHAINED_COMPARE → BOOLOP → TERNARY → IF
- **BOOLOP 先于 TERNARY 不合理**：TERNARY 是叶子值表达式，可作为 BOOLOP 操作数，应先归约
- 失败用例 `test_adv02_ternary_in_boolop_or.py` (`if (a if c else d) or b:`) 根因：
  BoolOp 检测时 ternary 未识别，三元 merge_block (Block 6) 被当作 BoolOp 链起点吞并，
  违反原则 2（每块唯一归属）、原则 3（嵌套即抽象节点）、原则 4（父引用子入口）

## 4 原则合规性
- 原则 1（自底向上归约）：部分违反 — BOOLOP 先于 TERNARY
- 原则 2（每块唯一归属）：违反 — Block 6 同时归属 Ternary/BoolOp/If
- 原则 3（嵌套即抽象节点）：违反 — ternary merge_block 出现在 BoolOp op_chain
- 原则 4（入口引用语义）：部分违反 — BoolOp 应引用 ternary entry 而非 merge_block

## 反模式检查
- `_merge_block_is_loop_back_edge` (region_ast_generator.py L18311) 命中 `_merge_` 前缀
- 硬编码深度: `_find_return_through_cleanup_chain(max_depth=6)` (L13197), `_safety < 10` (L8786)
- 后处理补丁: while_boolop 后处理移除 (L1351-1379), elif_chain 后处理 (L1411-1486)
- ternary 重叠过滤遗漏 boolop_regions (L1316-1340)

## 本轮建议修复（三层防御，配套使用）
### 修复 7.1 — 收紧 `_detect_boolop_chain_start` 对 TernaryRegion 占用块的处理
位置: region_analyzer.py L14730-14733
策略: `else` 分支增加 `if isinstance(existing, TernaryRegion): return None`
理由: 强制每块唯一归属，BoolOp 不抢占 Ternary 块

### 修复 7.2 — 扩展 BoolOp 对 ternary merge_block 的 hop 逻辑
位置: region_analyzer.py `_detect_boolop_conditional_chain` L15320 附近
策略: 增加"current 是某 TernaryRegion 的 merge_block"判据，将整个 TernaryRegion 视为单操作数
理由: 统一处理 ternary 在 BoolOp 任意位置，基于区域归属判据

### 修复 7.3 — 补全 ternary 重叠过滤对 boolop_regions 的应用
位置: region_analyzer.py analyze() L1338-1339 之后
策略: 增加 `boolop_regions = [r for r in boolop_regions if not _boolop_overlaps_with_ternary(r)]`
理由: 防御性兜底，统一 match/assert/boolop 三种区域的重叠处理

## 其他问题（后续迭代处理）
- 硬编码深度上限（max_depth=6, _safety<10）
- 跨层次启发式（await 轮询三联、PUSH_EXC_INFO 指令名硬编码）
- while_boolop 后处理补丁
- `_merge_block_is_loop_back_edge` 命名
