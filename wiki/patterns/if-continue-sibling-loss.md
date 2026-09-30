---
type: concept
title: if-continue 兄弟丢失（If-Continue Sibling Loss）
tags:
  - code-kb
related:
  - "[[region-reduction-internals]]"
  - "[[if-absorbs-loop-sibling]]"
  - "[[core-cfg-region-analyzer--if-region]]"
  - "[[core-cfg-region-ast-generator--region-ast-generator]]"
created: 2026-09-29
updated: 2026-09-29
kind: pattern
sources:
  - rules.md
  - core/cfg/region_ast_generator.py
  - core/cfg/region_analyzer.py
---

# if-continue 兄弟丢失

> 模式卡 P-1：循环体内 `if cond: ... continue` 的 continue 节点丢失，或 `[inner_if, Continue]` 被条件合并逻辑误吞并为 `if A and B:`。区域类型 IfRegion；违反原则 2（每块唯一归属）+ 原则 4（入口引用语义）。修复轮次 R23。

## 症状

反编译产物中出现以下任一表现：

1. 源码里的 `if cond: continue` 在产物中丢失 continue，控制流语义改变（少一次跳回循环头）；
2. 嵌套 if + 显式 continue 被合并成单个 `if A and B:`——两分支均指向回边时，合并器把"或语义"的兄弟结构误判为"与语义"的复合条件；
3. 字节码 diff 显示产物重编译后 `JUMP_BACKWARD` 数量少于原 pyc。

最小特征：`IfRegion.merge_block` 恰好是当前循环的回边块（纯 `JUMP_BACKWARD`），且 if 无 else 分支——两分支都无条件 continue。

## 根因（违反的原则）

- **原则 4（入口引用语义）**：continue 的入口引用语义（Continue 节点引用回边 entry）未显式表达，条件合并逻辑把"两分支均→回边"误读为短路 and 链。
- **原则 2（每块唯一归属）**：回边块既被 IfRegion 消费又留在循环体序列中重复处理，导致语句丢失或重复。

## 边界判定规则（正确判据）

`_if_generate_normal`（`core/cfg/region_ast_generator.py:17949`）中，以下 4 条**全部满足**才触发显式 Continue 兄弟节点生成：

1. `_current_loop is not None`（处于循环上下文）；
2. `merge == back_edge_block`（IfRegion 的 merge 就是循环回边块）；
3. 回边块仅含 `JUMP_BACKWARD`（纯 continue 回边，无其他语句）；
4. `not else_stmts`（无 else，两分支均→回边）。

触发后：生成显式 `Continue` 兄弟节点，并标记回边块已生成（`generated_blocks`/`generated_offsets`），阻止后续条件合并把 `[inner_if, Continue]` 吞并为 `if A and B:`。

## 修复锚点

| 锚点 | 位置 |
|---|---|
| `_if_generate_normal` 判据实现 | `core/cfg/region_ast_generator.py:17949` |
| 语句体生成（兄弟序列装配处） | `core/cfg/region_ast_generator.py:44955`（`_generate_block_statements_body`） |
| 判据来源 | rules.md §3.2.2（R23 修复） |

## 已知案例

- R23 `get_str_data`（quotation.pyc 迭代）：if-continue 兄弟丢失，按上述 4 判据修复，见 rules.md §七。

## 检索词

`continue 丢失` / `continue 丢失` / `if continue 被合并` / `if A and B 误合并` / `两分支都 continue` / `回边块被吞并` / `JUMP_BACKWARD 少了` / `if-continue sibling` / `merge 是回边` / `back_edge`
