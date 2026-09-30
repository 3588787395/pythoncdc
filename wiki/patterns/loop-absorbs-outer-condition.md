---
type: concept
title: Loop 吸收外层条件（Loop Absorbs Outer Condition）
tags:
  - code-kb
related:
  - "[[region-reduction-internals]]"
  - "[[and-chain-partial-split]]"
  - "[[if-absorbs-loop-sibling]]"
  - "[[core-cfg-region-analyzer--loop-region]]"
created: 2026-09-29
updated: 2026-09-29
kind: pattern
sources:
  - rules.md
  - core/cfg/region_analyzer.py
---

# Loop 吸收外层条件

> 模式卡 P-3：`while A and B:` 的复合条件链被 LoopRegion 反向吞并——前驱若是外层 if/elif 条件块（`cond_in_loop=False`），循环把它错认成自己的条件链，导致外层条件消失或 while 条件并入外层 elif。区域类型 LoopRegion；违反原则 2 + 原则 3。修复轮次 R24B。

## 症状

1. `while A and B:` 被拆成"外层 if + 内层 while"或外层条件直接消失；
2. 外层 if/elif/while 嵌套场景中，循环条件被并入外层 elif；
3. 语义漂移：产物重编译后条件求值次数与原 pyc 不同（短路链被拉直）。

## 根因（违反的原则）

`_detect_while_condition_boolop_chain` 反向链回溯时**未区分条件块是否在循环内**：

- 合法 while-boolop 前驱的 fall-through **恒为下一条件块**（条件块都在循环内，`cond_in_loop` 恒真）；
- `cond_in_loop=False` 只出现在外层 if/elif/while 嵌套场景——此时前驱是**外层**条件块，属外层 IfRegion 的资产。循环若吸收它，即违反原则 2（外层块被内层区域抢走）、原则 3（外层条件未作为父区域抽象节点）。

## 边界判定规则（正确判据）

`_detect_while_condition_boolop_chain`（`core/cfg/region_analyzer.py:23938`）：

- **判据**：`if not cond_in_loop: break`——回溯链上遇到不在循环体内的条件块立即终止；
- 循环后的顺序语句：后继块仍位于外层 if/elif/else 同一子分支内（未被外层分支的 `JUMP_FORWARD to return` 截断）时，作为循环后子分支内顺序语句保留，**不得外提为兄弟、不得把 while 条件并入外层 elif**（rules.md §3.3.2）。

## 修复锚点

| 锚点 | 位置 |
|---|---|
| `_detect_while_condition_boolop_chain` | `core/cfg/region_analyzer.py:23938` |
| `_identify_loop_regions`（LoopRegion 构造侧） | `core/cfg/region_analyzer.py:3782` |
| `_loop_generate_while`（生成侧 while） | `core/cfg/region_ast_generator.py:5230` |
| 判据来源 | rules.md §3.3.1（R24 缺陷B） |

## 已知案例

- R24B `get_date_and_count`（quotation.pyc 迭代）：LOOP 吸收外层条件，修复为 `if not cond_in_loop: break` 终止回溯，见 rules.md §七。

## 检索词

`while 条件被拆开` / `while A and B 被拆成 if + while` / `循环吞掉外层 elif` / `外层条件消失` / `boolop 链反向回溯越界` / `cond_in_loop` / `while 复合条件并入外层` / `loop absorbs outer condition` / `while-boolop 链`
