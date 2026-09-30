# Project Purpose

## Goal

从反编译器代码（core/ parsers/ bytecode/ utils/ 入口共约 22 万行）生成可查询、可视化的知识库，用于**降低程序复杂度、提升区域归约算法的通用性**——以代码为唯一事实源，不采信现有文档的声明。

## Key Questions

1. 三代 AST 生成谱系（region 系 / v2 系 / 自包含 control_flow）中哪套从入口 `pycdc.py` 真正可达？哪些是可删除的死代码？
2. 8,954 个补丁标记聚类后剩几类？每类的泛化算法应长什么样（对照 rules.md 四大原则）？
3. 三胞胎 ast_builder（plain/cleaned/unified）与双份 code_generator 差异何在，如何收敛为单一实现？
4. 新 bug 属于哪个已有模式？修复前先查 wiki，按泛化方案改 region 边界判定，禁止 `_fix_/_patch_` 式后处理。

## Scope

**In scope:**
- core/、parsers/、bytecode/、utils/、pycdc.py、pycdas.py（sources 白名单）
- 四类知识页：modules（模块骨架）/ classes（类与 override 矩阵）/ concepts（算法综述）/ hotspots（补丁热点）

**Out of scope:**
- tests/、test_repros/、.trae/、scripts/、tools/、docs/（噪声与声明，不 ingest）
- 本项目只建知识库；重构由知识库产出的清单驱动，另行变更实施

## Thesis

> 三代并存 + 补丁堆积的根因是"修复绕过算法"；知识库把每一类补丁收敛为一条泛化原则，并在修复前可被检索到，使复杂度单调下降。

（按证据持续更新）
