---
type: concept
title: IF 吸收循环后兄弟语句（If Absorbs Loop Sibling）
tags:
  - code-kb
related:
  - "[[region-reduction-internals]]"
  - "[[if-continue-sibling-loss]]"
  - "[[loop-absorbs-outer-condition]]"
  - "[[core-cfg-region-analyzer--if-region]]"
created: 2026-09-29
updated: 2026-09-29
kind: pattern
sources:
  - rules.md
  - core/cfg/region_analyzer.py
---

# IF 吸收循环后兄弟语句

> 模式卡 P-2：循环体内 if/elif/else 链把**公共汇聚后继块**（本应保留为循环体兄弟语句）并入 then/else 分支；或外层 IfRegion 把循环后的顺序语句吸进分支体。区域类型 IfRegion；违反原则 2（每块唯一归属）+ 原则 3（嵌套即抽象节点）。修复轮次 R24A。

## 症状

1. 循环体末尾的 if/elif/else 链之后还有语句，产物中这些语句消失或被塞进某个分支体内；
2. 循环正常退出后的语句出现在循环体内部（语句被"搬进"了循环）；
3. 字节码 diff：`JUMP_FORWARD` 目标偏移，循环体边界块集合与原 pyc 不一致。

## 根因（违反的原则）

- **原则 2**：then/else 边界判定未止于分支末尾的 `JUMP_FORWARD` 跳转点，多吞了汇聚块——同一块被 if 分支和循环体序列争抢。
- **原则 3**：嵌套循环/if 在父区域中应作为单个抽象节点，边界错判导致父区域展开子区域内部块。

## 边界判定规则（正确判据）

- **then-region 边界止于 then 分支末尾的 `JUMP_FORWARD` 跳转点**（rules.md §3.2.1）；
- 循环体内 if/elif/else 链的**公共汇聚后继块保留为循环体兄弟语句**，不得并入 then 分支；
- merge 重算必须**循环感知**：在循环上下文中重新计算 IfRegion 的 merge，防止把循环出口后的块当作 if 的汇聚。

## 修复锚点

| 锚点 | 位置 |
|---|---|
| `_identify_conditional_regions`（merge 判定主体） | `core/cfg/region_analyzer.py:15981` |
| `_process_if_blocks`（生成侧 if 块处理） | `core/cfg/region_ast_generator.py:21776` |
| 判据来源 | rules.md §3.2.1（R24 缺陷A） |

## 已知案例

- R24A `change_his_to_backward`（quotation.pyc 迭代）：IF 吸收循环后兄弟，修复为循环感知 merge 重算，见 rules.md §七。

## 检索词

`循环后语句被吞进循环` / `循环体末尾语句丢失` / `if 吸收兄弟` / `兄弟语句被并入分支` / `汇聚块被 else 吃掉` / `then 边界多吞` / `JUMP_FORWARD 跳错目标` / `if absorbs sibling` / `循环感知 merge`
