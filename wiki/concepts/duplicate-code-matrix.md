---
type: concept
title: 重复代码矩阵（Duplicate Code Matrix）
tags:
  - code-kb
related:
  - "[[region-reduction-stages]]"
  - "[[patch-marker-hotspots]]"
  - "[[parsers-ast-builder]]"
  - "[[parsers-ast-builder-cleaned]]"
created: 2026-09-29
updated: 2026-09-29
kind: concept
sources:
  - parsers/ast_builder.py
  - parsers/ast_builder_cleaned.py
  - core/cfg/code_generator.py
  - parsers/code_generator.py
  - core/control_flow.py
  - core/cfg/cfg_builder.py
  - core/fast_stack.py
  - utils/stack.py
---

# 重复代码矩阵

白名单 61 个源文件两两比对（判据：同名函数数 / 函数体 AST 逐字相同数 / AST 哈希样本；**行数量级相似不作判据**）。共 62 个文件对达到"同名 ≥ 3"，其中**同体 ≥ 10 的只有一对**。

## 唯一确证的重复：ast_builder 双胞胎

| 文件 | 行数 | 字节 | 函数数 | 同名 | 同体 |
|---|---:|---:|---:|---:|---:|
| `parsers/ast_builder.py`（在用） | 30,264 | 1,748,549 | 255 | 245 | **212** |
| `parsers/ast_builder_cleaned.py` | 29,479 | 1,705,502 | 253 | 245 | **212** |

- **两者 212 个函数体 AST 逐字相同**，仅 33 个函数体存在差异。
- 引用扫描结论：`ast_builder_cleaned` 在白名单 61 文件、`tests/`（4,057 个 .py）、`scripts/`、`tools/` 中**引用数 = 0**。
- 在用入口（均指向 `ast_builder.py`）：
  - `pycdc.py:494` `from parsers.ast_builder import ASTBuilder`
  - `parsers/code_generator.py:1474` 同上
  - `parsers/unified_generator.py:343` 同上
- **结论**：`ast_builder_cleaned.py` 是零引用死副本（1.7MB / 29,479 行编译单元），删除不改变任何行为。

## 判定"不同构、保留"的文件对（防误删）

| 文件 A | 文件 B | 同名 | 同体 | 结论 |
|---|---|---:|---:|---|
| `core/cfg/code_generator.py`（127 方法） | `parsers/code_generator.py`（146 方法） | 5 | 0 | 不同构，两份并存 |
| `core/control_flow.py`（92 方法） | `core/cfg/cfg_builder.py`（28 方法） | 3 | 0 | 不同构 |
| `core/fast_stack.py` | `utils/stack.py` | 9 | 0 | 不同构 |
| `core/pyc_objects.py` | `core/PycObject.py` | 16 | 1 | 不同构 |
| `core/ast_nodes.py` | `core/astree.py` | 10 | 3 | 不同构（AST 节点定义 vs 树结构） |

这 5 对是"名字像但实现不同"的典型，误删会直接破坏反编译能力。

## 补丁标记与重复的关系

见 [[patch-marker-hotspots]]：9,098 个补丁标记中 97% 集中在 5 个文件（ast_builder 三胞胎 + `core/cfg/ast_generator_v2.py` + `core/cfg/structured_analyzer.py`）。**补丁密度最高的三兄弟恰好也是重复最严重的一对**——`ast_builder` 与其 cleaned 副本在维护中各自长出补丁，属于典型的"双份演进"债务。

## 复现方式

`python tools/anatomy/extract_stages.py` 重新生成比对结果（同名/同体/AST 哈希样本写入 `docs/refactor/anatomy-evidence.json` 与 `docs/refactor/dup-matrix.md`）。
