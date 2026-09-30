---
type: concept
title: 三代 AST 生成谱系（AST Generation Lineages）
tags:
  - code-kb
related:
  - "[[core-cfg-region-ast-generator]]"
  - "[[parsers-ast-builder-unified]]"
  - "[[core-control-flow]]"
created: 2026-09-28
updated: 2026-09-29
kind: concept
sources:
  - pycdc.py
  - core/cfg/region_ast_generator.py
  - core/cfg/region_analyzer.py
  - core/cfg/ast_generator_v2.py
  - parsers/ast_builder.py
  - parsers/ast_builder_cleaned.py
  - parsers/ast_builder_unified.py
  - core/control_flow.py
---

# 三代 AST 生成谱系

pythoncdc 内部并存**三条互不共享代码的 AST 生成路线**，全部从 `pycdc.py` 的入口分发，函数名零重合。

## 路线 1：Region 系（区域归约）

- 入口：`pycdc.py:71` `if use_region:` → `pycdc.py:84` `from core.cfg.region_ast_generator import RegionASTGenerator` → `pycdc.py:89` 实例化。
- 主体：`[[core-cfg-region-ast-generator]]`（`core/cfg/region_ast_generator.py`，51,751 行 / 3.1MB）+ `core/cfg/region_analyzer.py`（28,371 行）+ `core/cfg/structured_analyzer.py`（16,098 行 / 约 949KB）。
- 特征：先做 CFG，再按结构化模式（if/loop/try）把 basic block 归约成语句树；失败路径见 `pycdc.py:105-117` 的三段错误处理（syntax error / failed / exception）。

## 路线 2：CFG-v2 系（`UnifiedASTGenerator` + ast_builder 三胞胎）

- 入口：`pycdc.py:121` `if use_cfg or cfg_hybrid:` → `pycdc.py:126` `UnifiedASTGenerator(verbose=verbose, use_cfg=True)`。
- 主体：`core/cfg/ast_generator_v2.py`（26,879 行）+ `parsers/` 下的三胞胎：
  - `[[parsers-ast-builder]]` 30,264 行（CFG 向）
  - `parsers/ast_builder_cleaned.py` 29,479 行（清理版，与前者差 785 行）
  - `[[parsers-ast-builder-unified]]` 185 行，仅定义 `BuilderMode{CFG,TRADITIONAL,HYBRID}` 与 `UnifiedASTBuilder` 门面
- 代码复用点：`pycdc.py:493-496` 注释"重建AST - 使用 parsers.ast_builder.ASTBuilder"，属 v2 路线在 region 失败后的回退链。

## 路线 3：自包含 `core/control_flow.py`

- 入口：`pycdc.py:18` `from core.control_flow import ControlFlowAnalyzer`。
- 主体：`[[core-control-flow]]` 1,670 行 / 64KB，**零内部 import**（仅 typing/dataclasses/enum/collections，函数内 `import time` 也是标准库）——仓库内唯一完全自包含的分析器。
- 定位：轻量 CFG 分析，为 region/v2 路线之外的快速路径服务。

## 谱系对比

| 维度 | Region 系 | CFG-v2 系 | 自包含系 |
|------|-----------|-----------|----------|
| 触发参数 | `use_region` | `use_cfg` / `cfg_hybrid` | 常驻（`decompile` 前置） |
| 代码量 | ~80k 行（generator 51,751 + analyzer 28,371） | ~87k 行（v2 26,879 + 三胞胎 60k，含 29,479 死副本） | 1,670 行 |
| 依赖方向 | 依赖 core/cfg/* | 依赖 core/cfg/* + parsers/* | 无内部依赖 |
| 与另两路的符号重合 | 0 | 0 | 0 |

## 对重构的含义

- 归约算法若要通用化，收敛点在**区域归约（Region 系）与结构化分析（structured_analyzer）**；v2 的 `ast_builder` 三胞胎是最大的重复源（两份 ~30k 行近似代码）。
- `ast_builder_unified.py` 已经给出门面雏形（`BuilderMode.HYBRID`），可作为三胞胎收敛的落点。
- `core/control_flow.py` 的零依赖特性可作为归约算法接口化的参照（纯数据结构 + 分析函数）。
