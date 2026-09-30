---
type: concept
title: and 复合条件部分拆分（And-Chain Partial Split）
tags:
  - code-kb
related:
  - "[[region-reduction-internals]]"
  - "[[loop-absorbs-outer-condition]]"
  - "[[core-cfg-region-analyzer--if-region]]"
  - "[[core-cfg-region-ast-generator--region-ast-generator]]"
created: 2026-09-29
updated: 2026-09-29
kind: pattern
sources:
  - rules.md
  - core/cfg/region_analyzer.py
  - core/cfg/region_ast_generator.py
---

# and 复合条件部分拆分

> 模式卡 P-5：`if A and B:` 的 and 链被**部分**拆分——if 首条被拆成 `if A:` + 内层 `if B:`，而 elif 分支保留冗余 `and`，同一函数内两种形态并存。区域类型 IfRegion/BoolOpRegion；违反原则 1（自底向上归约）+ 原则 4（入口引用语义）。修复轮次 R26，方案 B：**统一不拆分任何 and**。

## 症状

1. 同一函数内 if 被拆分而 elif 未拆分，条件表达形态不一致；
2. 拆分产物改变短路求值副作用顺序（A 的副作用在 B 之前、但被拆到两个语句层级）；
3. L1 严格口径 diff 出现 `EXTENDED_ARG` ±1——对应真实 AST 形状不一致（rules.md §5.3：R26 缺陷3），不可豁免。

## 根因（违反的原则）

- **原则 1**：and 链是 BoolOpRegion，应在最内层先归约为单个表达式节点；生成侧对 if 首条做"部分拆分"是对已归约区域的二次展开（回溯修正，违反单向数据流）。
- **原则 4**：IfRegion 入口引用语义要求 `if A and B:` 的入口块引用整个 boolop 链入口；部分拆分使入口引用指向链中段。

## 边界判定规则（正确判据）

方案 B（R26 定案，rules.md §3.2.3）——**统一不拆分任何 `and` 复合条件**：

1. 'and' 链检测（识别侧 Step6，`_detect_boolop_conditional_chain`，`core/cfg/region_analyzer.py:25183`）产出 inline 链，经 `main_inline_boolop_chain` 参数存入 IfRegion（`_build_elif_region`，`core/cfg/region_analyzer.py:18719`）；
2. `generate()` 入口（`core/cfg/region_ast_generator.py:672`）：当 IfRegion.entry 是 entry_block 且存在以 entry_block 为首块的 inline_boolop_chain 时，交给 `_if_generate_normal`（`core/cfg/region_ast_generator.py:17949`）统一处理；
3. 禁止只对 if 首条拆分而 elif 保留冗余 `and` 的不对称后处理。

## 修复锚点

| 锚点 | 位置 |
|---|---|
| `generate()` 入口分发 | `core/cfg/region_ast_generator.py:672` |
| `_detect_boolop_conditional_chain`（'and' 链检测） | `core/cfg/region_analyzer.py:25183` |
| `_build_elif_region` 的 `main_inline_boolop_chain` 参数 | `core/cfg/region_analyzer.py:18719` |
| `_if_generate_normal`（统一处理） | `core/cfg/region_ast_generator.py:17949` |
| 判据来源 | rules.md §3.2.3（R26 缺陷3，方案 B） |

## 已知案例

- R26 `one_prod_to_dataframe`（quotation.pyc 迭代）：and 部分提取，EXTENDED_ARG +1 → 真实 AST 形状不一致；修复 = 方案 B 统一不拆分，见 rules.md §七。

## 检索词

`if A and B 被拆成两个 if` / `and 条件部分拆分` / `elif 保留冗余 and` / `and 链被展开` / `复合条件拆分不一致` / `EXTENDED_ARG 差异 AST 形状` / `boolop 部分提取` / `and chain partial split` / `inline boolop chain`
