---
type: concept
title: 程序自身控制流图的全部分支点（含所有子分支）
tags:
  - code-kb
related:
  - "[[decompile-invariant-completeness]]"
  - "[[branch-conditions]]"
  - "[[region-reduction-stages]]"
  - "[[region-reduction-internals]]"
  - "[[duplicate-code-matrix]]"
  - "[[core-cfg-region-analyzer]]"
  - "[[core-cfg-region-ast-generator]]"
created: 2026-09-29
updated: 2026-09-29
kind: concept
sources:
  - core/cfg/region_analyzer.py
  - core/cfg/region_ast_generator.py
  - core/cfg/ast_generator_v2.py
  - parsers/ast_builder.py
  - docs/refactor/program-cfg.json
---

# 程序自身控制流图的全部分支点

分析对象 = **反编译器程序自身**：`core/ parsers/ bytecode/ utils/ + pycdc.py + pycdas.py`，共 **60 个模块 / 6,923 个 code object**。把每个模块编译成字节码 → 建 CFG → 枚举**图上每一个分支点**（决策节点），按**支配深度**展开**所有层级的所有子分支**。

**口径**：分支点 = 块尾指令使控制流转为 ≥2 路径（条件跳转 / `FOR_ITER` / 短路跳转）。支配深度 = 支配该分支点的分支点数量（0 = 顶层，N = 嵌在 N 层分支内）。统计单位是**分支点实例**，不是"某函数是否含某形态"——一个 500 行、嵌套 20 层的函数贡献它内部**每一个**分支点。

工具：`tools/kb/program_cfg.py` → `docs/refactor/program-cfg.json`。数字全部来自该 JSON，**禁止手改**（约定见 [[overview]]）。

> **⚠️ 2026-09-29 BOM 读数纠正（重要）**：`core/cfg/region_ast_generator.py` 带 UTF-8 BOM（G0 保护特性"BOM efbbbf 保持"），旧工具用裸 `utf-8` 读 → `compile()` SyntaxError → **最大模块（51,751 行）整个从旧读数里缺失**（旧 fail=1 被静默计入）。改 `utf-8-sig` 后修复。另：`parsers/ast_builder_cleaned.py` 已删除（用户决定区），其 8,941 分支点随之出清。**旧读数 51,518 作废，以下全部为新口径**。逐条件级的新维度见 [[branch-conditions]]。

## 1. 总量：程序自身 60,933 个分支点

| 项 | 值 |
|---|---:|
| 模块 | 60 |
| code object | 6,923 |
| **分支点总计** | **60,933** |
| 顶层分支点（深度 0） | 5,351（8.8%） |
| **子分支（深度 ≥1）** | **55,582（91.2%）** |
| 最深支配深度 | **164** 层（`parsers/ast_builder.py :: ASTBuilder._process_instruction`） |
| 每 code object 平均 | 8.80 |

- **子分支占 91.2%**：程序自身的分支 overwhelmingly 嵌套——几乎所有决策都在别的分支臂内。
- **最深 164 层**：单个函数内的分支嵌套深度远超语料 pyc（语料最深 32 层）。这是"程序比被反编译的代码复杂得多"的直接证据：反编译器自身的控制流嵌套比它要处理的输入还深。
- 每 code object 平均 8.80 个分支点，是高决策密度的程序。

## 2. 分支点形态分布（程序自身）

| 形态 | 分支点数 | 占比 | 对应语言形态 |
|---|---:|---:|---|
| if（条件跳转头） | 47,113 | 77.3% | if/elif/比较/守卫 |
| for_iter（`FOR_ITER`） | 9,555 | 15.7% | for 迭代 |
| boolop（短路跳转） | 2,003 | 3.3% | and / or |
| while_backward（回向条件跳转） | 1,809 | 3.0% | while |
| exc_branch（异常检查头） | 453 | 0.7% | try/except |

- **if 独占 77%**：程序的决策逻辑几乎全是条件分支——这与"程序要做大量形态判别（这是什么结构、这个块归谁）"一致。
- for 迭代 9,555 vs while 1,809：程序本身也偏好 for。

## 3. 分支嵌套深度分布（所有子分支层级）

| 支配深度 | 分支点数 | 占比 |
|---:|---:|---:|
| 0（顶层） | 5,351 | 8.8% |
| 1 | 3,993 | 6.6% |
| 2 | 2,810 | 4.6% |
| 3 | 2,606 | 4.3% |
| 4–10 | 14,573 | 23.9% |
| 11–19 | 12,551 | 20.6% |
| 20 | 1,059 | 1.7% |
| 21–30 | ~4,000 | ~6.6% |
| 31–50 | ~2,050 | ~3.4% |
| **≥60（含最深 164）** | **1,322** | **2.2%** |

- 深度每层只衰减 ~7%（从深度 1 的 3,993 到深度 19 的 1,110），**衰减极慢**——与语料 pyc（深度 1 占 17% 后迅速衰减）截然不同。
- **深度 ≥60 的分支点仍有 1,322 个**（clamp 桶，最深 164）：存在极端深嵌套的巨型函数，它们的控制流复杂度是数量级级别的。

## 4. 分支点最集中的模块（程序自身）

| 模块 | 分支点 | 占程序 |
|---|---:|---:|
| **`core/cfg/region_ast_generator.py`** | **18,356** | **30.1%** |
| `core/cfg/region_analyzer.py` | 10,131 | 16.6% |
| `parsers/ast_builder.py` | 9,226 | 15.1% |
| `core/cfg/ast_generator_v2.py` | 7,929 | 13.0% |
| `core/cfg/structured_analyzer.py` | 4,358 | 7.2% |
| `parsers/code_generator.py` | 2,715 | 4.5% |
| `core/cfg/code_generator.py` | 1,622 | 2.7% |
| `core/ast_nodes.py` | 1,452 | 2.4% |
| `core/cfg/pattern_parser.py` | 696 | 1.1% |
| `core/cfg/comprehension_generator.py` | 578 | 0.9% |

- **前 5 个模块占程序分支点的 82.1%（50,000/60,933）**：复杂度高度集中。
- **`region_ast_generator` 独占 30.1%、是最大分支巢**——旧读数里它整个缺失（BOM bug），"复杂度集中在 region_analyzer"的旧叙事是错的：**生成侧（region_ast_generator）比识别侧（region_analyzer）分支还多 80%**。
- `region_analyzer`（区域识别）+ `region_ast_generator`/`ast_generator_v2`（AST 生成）构成决策主战场；识别、生成、AST 重建三条管线都是巨型分支巢。

## 5. 关键结论

1. **程序自身 60,933 分支点，91.2% 是子分支**：反编译器自身的控制流几乎全是嵌套分支，不是平铺决策。
2. **最深 164 层**（`ast_builder._process_instruction`）：程序内部的分支嵌套深度远超它要处理的输入 pyc（语料最深 32 层）⇒ **"反编译器比它反编译的代码更复杂"**（见 [[overview]] 结论 2、[[region-reduction-stages]]）。
3. **复杂度集中在 5 个模块（82.1%）**，且 **`region_ast_generator` 是单一最大巢（30.1%）**——B1 破口（前导操作数丢弃 `:47629-47643`）恰好坐落其中。
4. **深度衰减极慢**（每层约 -7%），深分支长尾厚（≥60 层仍 1,322 个）——这些巨型嵌套函数是块归属/剪枝缺陷的高发区，与 [[region-reduction-internals]] 的"每块唯一归属"在深嵌套下的复杂度吻合。

## 6. 附：被反编译语料的分支规模（对照）

同样方法跑 `site-packages` 1,720 pyc（`tools/kb/cfg_branch_walk.py`）：56,026 分支点、77.9% 子分支、最深 32 层。程序自身（91.2% 子分支、164 层）比语料**嵌套更深、决策更密**——反编译器是"以复杂性换通用性"的结构。

## 检索词

程序自身控制流 / 分支点 / 子分支 / 支配深度 164 / 60,933 / region_ast_generator 30.1% 最大分支巢 / BOM 纠正 / utf-8-sig / ast_builder_cleaned 出清 / 复杂度集中 82.1% / 深度衰减 / 程序比输入复杂 / program CFG / branch point / dominance depth
