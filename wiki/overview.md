---
type: overview
title: Project Overview
tags:
  - code-kb
related:
  - "[[index]]"
  - "[[ast-generation-lineages]]"
  - "[[region-reduction-stages]]"
  - "[[duplicate-code-matrix]]"
  - "[[patch-marker-hotspots]]"
  - "[[patch-semantic-clusters]]"
  - "[[complexity-dashboard]]"
  - "[[cfg-anatomy]]"
  - "[[decompile-invariant-completeness]]"
created: 2026-09-28
updated: 2026-09-29
kind: overview
file: pycdc.py
---

# Overview

pythoncdc（Python 字节码反编译器，白名单源码 60 文件 / ≈ 22 万行）的代码知识库。目录见 [[index|Wiki Index]]。

## 规模（2026-09-29）

| 分类 | 数量 | 位置 | 内容来源 |
|---|---:|---|---|
| 模块页 | 61 | `wiki/modules/` | AST 提取：行数/补丁标记/方法数/类与顶层函数行号 |
| 类页 | 68 | `wiki/classes/` | 方法 ≥8 的核心类：继承、override、方法行号清单 |
| 概念页 | 6 | `wiki/concepts/` | 三代谱系 / 七阶段模型 / 归约内部机制 / 重复矩阵 / 全图分支分布 / 语法完备性 |
| 热点页 | 2 | `wiki/hotspots/` | 补丁物理聚类（文件×窗口）+ 语义聚类（16 类） |
| 模式页 | 5 | `wiki/patterns/` | 缺陷模式：症状→区域类型→边界判据→原则→修复锚点→检索词 |
| 查询页 | 2 | `wiki/queries/` | Dataview：补丁密集清单 + 复杂度仪表盘 |

## 五条核心结论

1. **三代 AST 生成路线并存**（[[ast-generation-lineages]]）：Region 系（`pycdc.py:84` 入口，28k+52k 行）、CFG-v2 系（`UnifiedASTGenerator` + ast_builder，≈87k 行，含 29k 死副本）、自包含 `core/control_flow.py`（1,670 行零内部依赖）。三者符号零重合。
2. **区域归约 = 七阶段**（[[region-reduction-stages]]）：识别侧 25,538 行、生成侧 48,806 行；阶段归属靠"构造 vs 消费"区域对象区分；`_generate_block_statements_body` 单方法 4,022 行且读 42 个实例字段。
3. **唯一确证重复是死副本**（[[duplicate-code-matrix]]）：`parsers/ast_builder_cleaned.py` 与在用的 `ast_builder.py` 有 212 个函数体逐字相同，但全仓引用数 = 0；另有 5 对"名字像实现不同"的文件已被明确标为不可误删。
4. **缺陷模式层闭环已建立**（[[patch-semantic-clusters]] + `wiki/patterns/`）：9,098 个标记语义聚类为 16 类；if/loop/boolop 三类（2,936 个，32%）的泛化答案 = 5 张模式页（P-1~P-5，R23-R26 提炼）。新 bug 先查 patterns 区按症状命中先例，按边界判据修 region 判定，禁止 `_fix_/_patch_` 后处理。
5. **程序自身分支规模与语法完备性已量化**（[[decompile-invariant-completeness]] + [[cfg-anatomy]] + [[branch-conditions]]）：反编译器自身 60 模块 / 6,923 单元共 **60,933 个分支点**（子分支 91.2%，最深支配深度 **164** 层）；**61,289 个分支判定条件逐条入库**（7 类判定点、结构归一化、同形簇 1,903 组、相似度可查——BOM 纠正后 region_ast_generator 以 30.1% 成为最大分支巢）；**语法完备性 = 路径层 128/128 = 100% × 不变式层（嵌套无感）**：完备 **127** / 破口 **1**（BoolOp 前导操作数丢弃 B1，region_ast_generator.py:47629-47643，fix1 嫁接仅存归档 spec 未落地）/ 零能力 **0** ⇒ **99.2%**。except* 审计纠正：旧判零能力系 3.12 操作码误标，实际全链实现（code_generator.py:702）。标准含 13 条误解清单与迭代机制。
egion_ast_generator.py:47629-47643，fix1 嫁接仅存归档 spec 未落地）/ 零能力 **0** ⇒ **99.2%**。**except* 审计纠正**：旧判零能力系用 3.12 操作码 PRELOAD_RERAISE 当 3.11 检测标准，实际全链已实现（识别 
egion_analyzer.py:9731 → 发射 code_generator.py:702 except*）。标准含 13 条误解清单（循环论证/有过就算/语料口径/无限分母等）与迭代机制（fix 批落位→复审→台账→重算）。

## 维护约定

- 工具：`tools/kb/{gen_modules,gen_classes,check_stale,cluster_markers,reachability,cfg_anatomy,cfg_branch_walk,program_cfg,syntax_coverage}.py`（页面生成、stale 检查、补丁语义聚类、入口可达性、CFG 结构、语料分支枚举、程序自身分支点枚举、**语法完备占比**）、`tools/anatomy/extract_stages.py`（阶段归属与重复矩阵，产出 `docs/refactor/`）。
- 源码改动后：`python tools/kb/check_stale.py` 判 stale → 重跑生成器 → `llm_wiki_rescan_sources` 同步应用索引。
- 可视化：Obsidian Dataview 仪表盘见 [[complexity-dashboard]]；七阶段管线 + 模式页挂载见根目录 `region-reduction-pipeline.canvas`。
- 向量检索：应用端 embedding 凭据未配置时 `llm_wiki_embed_page` 返回 401，检索退化为纯关键词——模式页"检索词"小节即为该退化下的命中保障；配置后在 [[index]] 所列概念/热点/模式页上重跑 embed 即可。
- 白名单：`core/ parsers/ bytecode/ utils/ + pycdc.py + pycdas.py`（经 `raw/sources/` junction 落地）；页面链接断链必须为 0。
- 约定：页面 kebab-case 英文命名、正文中文、UTF-8 无 BOM；数字必须来自工具输出，禁止手改。
