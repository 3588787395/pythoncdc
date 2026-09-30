---
type: synthesis
title: 补丁标记热点（Patch Marker Hotspots）
tags:
  - code-kb
related:
  - "[[index]]"
  - "[[ast-generation-lineages]]"
created: 2026-09-28
updated: 2026-09-28
kind: hotspot
sources:
  - parsers/ast_builder.py
  - parsers/ast_builder_cleaned.py
  - core/cfg/ast_generator_v2.py
  - core/cfg/structured_analyzer.py
  - core/ast_nodes.py
  - parsers/code_generator.py
  - core/cfg/region_ast_generator.py
  - core/cfg/code_generator.py
  - core/cfg/region_analyzer.py
  - core/cfg/exception_handler.py
---

# 补丁标记热点

按 `patch_markers > 100` 从模块骨架页筛出的 **10 个补丁密集模块**（白名单 61 文件合计 9,098 个标记；本页口径见文末定义）。

## 热点模块清单（与 Dataview 查询等价）

查询：`WHERE kind = "module" AND patch_markers > 100`

| 模块 | patch_markers | lines | 补丁密度 |
|---|---:|---:|---:|
| [[parsers-ast-builder\|parsers/ast_builder.py]] | 2261 | 30264 | 0.07 |
| [[parsers-ast-builder-cleaned\|parsers/ast_builder_cleaned.py]] | 2209 | 29479 | 0.07 |
| [[core-cfg-ast-generator-v2\|core/cfg/ast_generator_v2.py]] | 1889 | 26879 | 0.07 |
| [[core-cfg-structured-analyzer\|core/cfg/structured_analyzer.py]] | 1360 | 16098 | 0.08 |
| [[core-ast-nodes\|core/ast_nodes.py]] | 260 | 7076 | 0.04 |
| [[parsers-code-generator\|parsers/code_generator.py]] | 254 | 8746 | 0.03 |
| [[core-cfg-region-ast-generator\|core/cfg/region_ast_generator.py]] | 247 | 51751 | 0.00 |
| [[core-cfg-code-generator\|core/cfg/code_generator.py]] | 231 | 5970 | 0.04 |
| [[core-cfg-region-analyzer\|core/cfg/region_analyzer.py]] | 133 | 28371 | 0.00 |
| [[core-cfg-exception-handler\|core/cfg/exception_handler.py]] | 115 | 1538 | 0.07 |

## 聚类：100 行窗口 Top-3（标记最密集的源码区段）

| 模块 | 窗口1 | 窗口2 | 窗口3 |
|---|---|---|---|
| parsers/ast_builder.py | L24501-24600 (21) | L26501-26600 (19) | L3801-3900 (19) |
| parsers/ast_builder_cleaned.py | L23701-23800 (20) | L26901-27000 (19) | L25801-25900 (19) |
| core/cfg/ast_generator_v2.py | L2701-2800 (24) | L21901-22000 (21) | L25501-25600 (17) |
| core/cfg/structured_analyzer.py | L201-300 (25) | L7901-8000 (24) | L11901-12000 (21) |
| core/ast_nodes.py | L2701-2800 (13) | L3501-3600 (11) | L3301-3400 (11) |
| parsers/code_generator.py | L1901-2000 (11) | L3001-3100 (9) | L2301-2400 (9) |
| core/cfg/region_ast_generator.py | L29701-29800 (4) | L28901-29000 (4) | L18401-18500 (4) |
| core/cfg/code_generator.py | L4301-4400 (13) | L2501-2600 (11) | L2101-2200 (11) |
| core/cfg/region_analyzer.py | L1201-1300 (6) | L26301-26400 (4) | L25701-25800 (4) |
| core/cfg/exception_handler.py | L701-800 (13) | L601-700 (12) | L301-400 (12) |

## 结论（供重构优先级参考）

- **ast_builder 三胞胎 + ast_generator_v2 + structured_analyzer 五者占 8,788 / 9,098 ≈ 97% 的标记量**——与 [[ast-generation-lineages]] 的收敛判断一致：三胞胎去重与区域归约通用化是降复杂度的最大杠杆。
- region 系文件（51k / 28k 行）标记密度低（≈0.005），补丁散布；exception_handler 密度高但体量小，属局部热点。

## 标记口径

`patch_markers` = 匹配 `#.*(修复|补丁|临时|workaround|hack|兼容|hardcode|硬编码)` 或 `def _(fix|merge|patch|fallback|hack|workaround|temp)_*` 的行数，由生成器 `gen_modules.py` 按当前源码计算写入各模块页 frontmatter（区别于 `.quality_baseline.json` 的 2026-04 旧口径）。
