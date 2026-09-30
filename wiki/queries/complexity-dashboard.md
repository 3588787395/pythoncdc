---
type: query
title: 复杂度仪表盘（Dataview）
tags:
  - code-kb
related:
  - "[[hot-modules]]"
  - "[[patch-semantic-clusters]]"
  - "[[region-reduction-stages]]"
  - "[[index]]"
created: 2026-09-29
updated: 2026-09-29
kind: query
sources:
  - wiki/modules/
  - wiki/classes/
  - wiki/patterns/
---

# 复杂度仪表盘

降复杂度的三个量化视角：**补丁密度**（哪里在堆补丁）、**god class**（哪里职责糊了）、**模式页**（每类补丁的泛化答案）。数据全部来自骨架页 frontmatter，源码改动后由 `tools/kb/gen_modules.py` / `gen_classes.py` 重算。

## 1. 模块补丁密度 TOP 15

```dataview
TABLE lines, patch_markers, method_count, round(patch_markers / lines * 1000, 1) AS "标记/千行"
FROM "wiki/modules"
WHERE kind = "module"
SORT patch_markers DESC
LIMIT 15
```

判读：前 5 行（ast_builder 三胞胎 + v2 + structured_analyzer）≈ 97% 标记量，语义分类见 [[patch-semantic-clusters]]；region 系两文件（51k/28k 行）标记/千行 ≈ 5，是算法驱动的对照组。

## 2. God class TOP 10（class_lines × method_count）

```dataview
TABLE class_lines, method_count, defined_at
FROM "wiki/classes"
WHERE kind = "class"
SORT class_lines DESC
LIMIT 10
```

判读：`RegionASTGenerator`（51,488 行 / 248 方法）与 `RegionAnalyzer`（27,175 行 / 212 方法）合计占 region 系 95%；前 10 大方法占两类的 28%，`_generate_block_statements_body` 单方法 4,022 行读 42 个实例字段——拆分优先级见 [[region-reduction-stages]]。

## 3. 缺陷模式页（修复前先查这里）

```dataview
LIST
FROM "wiki/patterns"
WHERE kind = "pattern"
SORT file.name ASC
```

判读：新 bug 的症状若与某模式页"症状/检索词"小节匹配，按该页"边界判定规则"改 region 边界，禁止 `_fix_/_patch_` 后处理（rules.md §2）。

## 4. 概念页（算法综述）

```dataview
LIST
FROM "wiki/concepts"
WHERE kind = "concept"
SORT file.name ASC
```
