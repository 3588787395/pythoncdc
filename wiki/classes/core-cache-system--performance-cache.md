---
type: entity
title: PerformanceCache
tags:
  - code-kb
related:
  - "[[core-cache-system]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cache_system.py
content_hash: c7d60c14d2ab800eb7d3decf2be2de78
class: PerformanceCache
defined_at: core/cache_system.py:191
class_lines: 94
method_count: 11
bases: []
sources:
  - core/cache_system.py
---

# PerformanceCache

定义于 `core/cache_system.py:191`（类体 94 行，11 个方法），所属模块 [[core-cache-system]]。

> 综合性能缓存系统

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :194
- `get_lru()` :201
- `put_lru()` :205
- `get_ttl()` :209
- `put_ttl()` :213
- `get_weak()` :217
- `put_weak()` :221
- `cache_function()` :225
- `_make_cache_key()` :244
- `cleanup()` :256
- `get_all_stats()` :277

## 相关页面

- [[core-cache-system|core/cache_system.py]]
- [[index|Wiki Index]]
