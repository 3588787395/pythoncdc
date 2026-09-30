---
type: concept
title: 分支判定条件库：逐条件跟踪 + 相似度比较
tags:
  - code-kb
related:
  - "[[cfg-anatomy]]"
  - "[[decompile-invariant-completeness]]"
  - "[[decompile-invariant-completeness]]"
created: 2026-09-29
updated: 2026-09-29
kind: concept
sources:
  - tools/kb/branch_conditions.py
  - docs/refactor/branch-conditions.json
---

# 分支判定条件库

**知识库必须能跟踪每一分支判断条件，并能比较相似度。** 本页是这项能力的规范与读数：程序自身（60 模块，与 [[cfg-anatomy]] 同白名单）**每一分支判定点**的条件表达式被逐条入库，可按**结构归一化**比较相似度、查询同形条件、聚簇重复形态。

工具：`tools/kb/branch_conditions.py` → `docs/refactor/branch-conditions.json`。数字来自该 JSON，**禁止手改**。

## 1. 判定点分类（7 类，与完备性标准的分支形态对齐）

| 类别 | 语法位置 | 计数 |
|---|---|---:|
| IF_TEST | `ast.If.test`（if/elif 链逐条件） | 30,996 |
| BOOLOP_OPERAND | `ast.BoolOp.values[i]`（and/or 短路链**逐操作数**） | 26,358 |
| IFEXP_TEST | `ast.IfExp.test`（三元） | 2,124 |
| COMP_IF | `ast.comprehension.ifs[j]`（推导式 if 子句） | 1,302 |
| WHILE_TEST | `ast.While.test` | 509 |
| MATCH_GUARD | `ast.match_case.guard` | **0** |
| ASSERT_TEST | `ast.Assert.test` | **0** |
| **合计** | | **61,289** |

- **MATCH_GUARD=0、ASSERT_TEST=0 是真实读数**：程序自身不使用 match 语句与 assert 语句（精确 grep 交叉核实：仅有的"assert"字样全在 docstring/注释）。这**不影响**完备性结论——[[decompile-invariant-completeness]] 测的是"能处理什么语法"，不是"程序自己用了什么语法"。
- for 的 `FOR_ITER` 与异常表边**没有源级条件表达式**，不进条件库（由 [[cfg-anatomy]] 的字节码分支点覆盖）。
- **粒度区分**：本库是 **AST 级条件表达式**（61,289 条）；[[cfg-anatomy]] 是**字节码 CFG 级分支点**（60,933 个）。两个口径互补，前者可查"条件长什么样、与谁同形"，后者可查"控制流嵌在哪、多深"。

## 2. 每条记录的字段

| 字段 | 含义 |
|---|---|
| `m` / `q` | 模块路径 / 完整 qualname（含 `<locals>`） |
| `k` | 判定点类别（7 类之一） |
| `L` / `E` | 起止行 |
| `c` | 条件原文（`ast.unparse`） |
| `n` | **结构归一化文本**：`Name→N, Attribute→A, Constant→C, arg→N`——消除变量名/常量字面差异，保留结构 |
| `h` | 结构哈希 = sha1(归一化 AST dump)[:12]——**同形同哈希** |
| `t` | 文本哈希 = sha1(去空白原文)[:12]——逐字重复 |
| `d` | 判定嵌套深度（外层判定构造数） |
| `op` | 仅 BOOLOP_OPERAND：'and'/'or' |

## 3. 读数（2026-09-29）

| 项 | 值 |
|---|---:|
| 判定点 | **61,289** |
| 唯一结构哈希 | 4,618 |
| 结构重复记录 | 58,574（1,903 组同形簇） |
| 最深判定嵌套 | 143 层 |
| 最大模块 | `core/cfg/region_ast_generator.py` 18,687 条 |

**同形条件簇 top 形态**：`N`（单变量真值，9,097 处）、`N(N, N)`（两参调用，2,739）、`N(N, 'C')`（hasattr 族，2,543）、`not N`（2,320）、`N is not None` 族（1,849）——判别式代码的典型词汇。

## 4. 相似度比较

**查询模式**（`similar "<expr>" [--top-k N] [--kind K] [--module M]`）：
- 结构哈希全等 → 记 1.0（`[结构全等]`）
- 否则 `score = SequenceMatcher(None, 归一化query, 归一化记录).ratio()`，长度差 >50% 预过滤
- 实测：`"inner_merge != merge_"` → 25,267 候选中结构全等族（`asname != name`、`v1 != v2`…）；`"opcode in python311_opcodes and not isinstance(v, str)"` → 0.923 命中 `block in try_region.blocks and not self._w11_unprotected_else_candidate(...)` 等**同形族**

**聚簇模式**（`dupes [--min-size N]`）：按结构哈希分组，输出组大小/归一化形态/模块分布。

## 5. 缺陷工作流用法（为什么需要它）

1. **同形定位**：缺陷出现在某分支条件处 → 查该条件的结构哈希 → **全程序同形条件清单**即候选同类缺陷面（B1 类教训：`_cjb_skip_inline_if` 的丢弃模式作用于某类条件形状，同形条件全部是回归目标）。
2. **修复批验收**：fix 批落位后，对目标形态族跑 similar → 同形簇作为定向回归集，替代"等语料撞上"。
3. **模式页联动**：[[if-continue-sibling-loss]] 等缺陷模式的触发条件可在此库中查同形分布，量化"该模式还可能藏在哪"。
4. **复杂度证据**：最深判定嵌套 143 层、单模块 18,687 条条件——与 [[cfg-anatomy]] 的 164 层支配深度互证。

## 检索词

分支判定条件 / 判定点 61,289 / BOOLOP_OPERAND 逐操作数 / 结构归一化 / 结构哈希 / 同形条件簇 / 相似度查询 / SequenceMatcher / MATCH_GUARD 零读数 / ASSERT_TEST 零读数 / region_ast_generator 18,687 / 判定嵌套 143 / 同形定位 / 定向回归集 / branch condition tracking / similarity
