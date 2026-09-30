---
type: concept
title: 区域归约七阶段模型（Region Reduction Stage Model）
tags:
  - code-kb
related:
  - "[[ast-generation-lineages]]"
  - "[[duplicate-code-matrix]]"
  - "[[core-cfg-region-ast-generator--region-ast-generator]]"
  - "[[core-cfg-region-analyzer--region-analyzer]]"
created: 2026-09-29
updated: 2026-09-29
kind: concept
sources:
  - core/cfg/region_analyzer.py
  - core/cfg/region_ast_generator.py
---

# 区域归约七阶段模型

区域归约（region reduction）= CFG → 区域对象树 → 语句 AST 的七阶段管线。识别侧由 [[core-cfg-region-analyzer--region-analyzer|RegionAnalyzer]]（`core/cfg/region_analyzer.py:1197`，27,175 行 / 212 方法，所属模块 [[core-cfg-region-analyzer]]）实现 S1–S4；生成侧由 [[core-cfg-region-ast-generator--region-ast-generator|RegionASTGenerator]]（`core/cfg/region_ast_generator.py:252`，51,488 行 / 248 方法，所属模块 [[core-cfg-region-ast-generator]]）实现 S5–S7。两条生成路线的谱系位置见 [[ast-generation-lineages]]。

## 阶段表

| 阶段 | 名称 | 输入 | 输出 |
|---|---|---|---|
| S1 | CFG 构建 | `BasicBlock` 图 | 边集 + 基本块 |
| S2 | 块语义标注 | `BasicBlock` | `BlockSemantics` + `BlockRole` 标注 |
| S3 | 区域识别 | `BlockSemantics` | 9 类 `Region` 对象（`IfRegion`/`LoopRegion`/`TryExceptRegion`/`WithRegion`/`MatchRegion`/`AssertRegion`/`BoolOpRegion`/`TernaryRegion`/`Region`） |
| S4 | 区域层级装配 | `Region` 对象列表 | 带 `parent`/`children` 的区域树 |
| S5 | 结构化语句生成 | 区域树 | 语句 AST（`ASTIf`/`ASTWhile`/`ASTFor`/`ASTTry`/`ASTWith`/`ASTMatch`） |
| S6 | 表达式重建 | 语句 AST | 完整表达式 AST（`ExpressionReconstructor`） |
| S7 | 后处理 | 完整 AST | 可输出 AST |

## 归属实测（460 方法 / 77,880 行）

| 阶段 | 方法数 | 行数 | 占比 |
|---|---:|---:|---:|
| S1 | 87 | 5,349 | 6.7% |
| S2 | 15 | 833 | 1.0% |
| S3 | 88 | 19,983 | 25.0% |
| S4 | 8 | 525 | 0.7% |
| S5 | 89 | 33,179 | 41.6% |
| S6 | 82 | 13,843 | 17.3% |
| S7 | 28 | 1,784 | 2.2% |
| Unclassified | 63 | 2,517 | 3.2% |

识别侧（S1–S4）25,538 行；生成侧（S5–S7）48,806 行（占 `RegionASTGenerator` 的 95%）。

## 阶段归属的判定规则（关键）

区分**构造**与**消费**是判定阶段归属的唯一可靠信号：

- `IfRegion(...)` 这类**构造**调用 → 识别侧 S3 证据（`new:IfRegion`）
- 仅作为 `isinstance`/注解/属性**读取** → 生成侧 S5 证据（`use:IfRegion`）
- 例外情况：`_loop_generate_while`（`core/cfg/region_ast_generator.py:5230`）只读 `LoopRegion` → S5；`_identify_loop_regions`（`core/cfg/region_analyzer.py:3782`）构造 `LoopRegion` → S3

## 最大的 10 个方法（占两个 god class 的 28%）

| 方法 | 类 | 行数 | 阶段 | self 读/写 | 锚点 |
|---|---|---:|---|---:|---|
| `_generate_block_statements_body` | RegionASTGenerator | 4,022 | S5 | 42/1 | `core/cfg/region_ast_generator.py:44955` |
| `_generate_ternary` | RegionASTGenerator | 3,639 | S5 | 44/0 | `core/cfg/region_ast_generator.py:35757` |
| `_identify_ternary_regions` | RegionAnalyzer | 2,898 | S3 | 9/8 | `core/cfg/region_analyzer.py:20515` |
| `_identify_conditional_regions` | RegionAnalyzer | 2,198 | S3 | 26/1 | `core/cfg/region_analyzer.py:15981` |
| `_process_if_blocks` | RegionASTGenerator | 1,696 | S5 | 32/1 | `core/cfg/region_ast_generator.py:21776` |
| `_loop_generate_while` | RegionASTGenerator | 1,561 | S5 | 32/0 | `core/cfg/region_ast_generator.py:5230` |
| `_build_elif_region` | RegionAnalyzer | 1,523 | S3 | 13/0 | `core/cfg/region_analyzer.py:18719` |
| `_detect_boolop_conditional_chain` | RegionAnalyzer | 1,506 | S3 | 11/0 | `core/cfg/region_analyzer.py:25183` |
| `_generate_try` | RegionASTGenerator | 1,500 | S5 | 22/3 | `core/cfg/region_ast_generator.py:26128` |
| `_identify_try_except_regions` | RegionAnalyzer | 1,391 | S3 | 9/1 | `core/cfg/region_analyzer.py:7603` |

前三个生成侧方法（`_generate_block_statements_body`/`_generate_ternary`/`_process_if_blocks`）各读 32–44 个实例字段——职责边界已糊在 god class 内部，是"该拆"的量化信号。

## 复现方式

`python tools/anatomy/extract_stages.py` → 重算归属表与 `docs/refactor/anatomy-evidence.json`（含每方法的 token 证据、`self` 读写、方法体 AST 哈希）。阶段归属为静态推断（97 个方法存在"名族先验 vs token 证据"冲突，已单列待人工确认），**不可当作搬移指令**。
