---
type: query
title: 补丁密集模块（Dataview）
tags:
  - code-kb
related:
  - "[[patch-marker-hotspots]]"
  - "[[index]]"
created: 2026-09-28
updated: 2026-09-28
kind: query
sources:
  - wiki/modules/
---

# 补丁密集模块查询

spec `code-kb-pages` Dataview 验收查询：

```dataview
TABLE lines, patch_markers, method_count
FROM "wiki/modules"
WHERE kind = "module" AND patch_markers > 100
SORT patch_markers DESC
```

预期：10 行（与 [[patch-marker-hotspots]] 的热点清单一致）。
