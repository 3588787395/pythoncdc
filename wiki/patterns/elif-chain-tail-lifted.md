---
type: concept
title: elif 链尾随语句外提（Elif-Chain Tail Lifted）
tags:
  - code-kb
related:
  - "[[region-reduction-internals]]"
  - "[[if-absorbs-loop-sibling]]"
  - "[[core-cfg-region-analyzer--if-region]]"
created: 2026-09-29
updated: 2026-09-29
kind: pattern
sources:
  - rules.md
  - core/cfg/region_analyzer.py
  - core/cfg/region_ast_generator.py
---

# elif 链尾随语句外提

> 模式卡 P-4：else 体内的尾随循环（及其他语句）被错误外提到 if/elif/else 链之后——elif 链构建时内外 merge 不一致未被阻止。区域类型 IfRegion；违反原则 2 + 原则 3。修复轮次 R25。**高危信号**：此类边界错误会造成 `JUMP_FORWARD` 跳错目标，产物运行直接 NameError。

## 症状

1. else 分支体末尾的 for/while 循环出现在 if/elif/else 链**之后**（被外提为兄弟语句）；
2. 产物语义变化：尾随循环从"仅 else 时执行"变成"总是执行"；
3. L1 严格口径 diff 出现多个 `JUMP_FORWARD` 目标不一致 + NOP 增减——**不可豁免为对齐偏移**，须按本模式核查（rules.md §5.3：R25 缺陷2 即 5 个 JUMP_FORWARD 跳错目标 → 真实 NameError）。

## 根因（违反的原则）

`_check_elif_chain` 构建链时未校验**内层 merge 与外层 merge 的一致性**：

- 内层 if 的汇聚点（`inner_merge`）≠ 外层链的汇聚点（`merge_`）时，内层 if 并不是真正的 elif——它的 else 分支还有后续语句要继续执行；
- 强行建链后，else 边界判定把 else 体内所有语句（含尾部循环）切给了外层，违反原则 2（else-region 边界应包含其体内所有语句）、原则 3（内层区域作为抽象节点的边界被外层重划）。

## 边界判定规则（正确判据）

- **判据**：`_check_elif_chain`（`core/cfg/region_analyzer.py:18876`）中 `inner_merge ≠ merge_` 时**阻止 elif 链构建**，尾随语句保留在 else 体内；
- **else-region 边界包含其体内所有语句**（含尾部 for 循环），不得把 else 体内尾随循环外提到 if/elif/else 之后（rules.md §3.2.1）；
- 生成侧 `_generate_if` 的 orelse 守卫：else 列表装配时校验块归属，越界块退回语句序列。

## 修复锚点

| 锚点 | 位置 |
|---|---|
| `_build_elif_region`（链构建主体） | `core/cfg/region_analyzer.py:18719` |
| `_check_elif_chain`（inner_merge ≠ merge_ 判据） | `core/cfg/region_analyzer.py:18876` |
| `_generate_if` orelse 守卫（生成侧） | `core/cfg/region_ast_generator.py`（`_process_if_blocks` :21776 邻域） |
| 判据来源 | rules.md §3.2.1（R25 缺陷2） |

## 已知案例

- R25 `build_future_fill_time`（quotation.pyc 迭代）：else 块尾部 for 被提升，5 个 JUMP_FORWARD 跳错目标 → 真实 NameError；修复 = `inner_merge ≠ merge_` 阻断 + orelse 守卫，见 rules.md §七。

## 检索词

`else 体内循环被外提` / `尾随循环跑到 if 之后` / `else 尾部 for 提升` / `elif 链构建错误` / `inner_merge 不等于 merge` / `else 边界少收语句` / `JUMP_FORWARD 跳错目标 NameError` / `NOP 增减真实缺陷` / `elif chain tail lifted`
