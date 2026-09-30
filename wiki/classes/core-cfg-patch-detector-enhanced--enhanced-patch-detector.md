---
type: entity
title: EnhancedPatchDetector
tags:
  - code-kb
related:
  - "[[core-cfg-patch-detector-enhanced]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/patch_detector_enhanced.py
content_hash: d3b6b9fdc36d6068590f14a9607ad7e7
class: EnhancedPatchDetector
defined_at: core/cfg/patch_detector_enhanced.py:116
class_lines: 583
method_count: 18
bases: []
sources:
  - core/cfg/patch_detector_enhanced.py
---

# EnhancedPatchDetector

定义于 `core/cfg/patch_detector_enhanced.py:116`（类体 583 行，18 个方法），所属模块 [[core-cfg-patch-detector-enhanced]]。

> 增强版补丁检测器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :161
- `detect()` :166
- `_analyze_file()` :219
- `_analyze_class()` :226
- `_analyze_method()` :233
- `_check_method_name_violations()` :271
- `_check_complexity_violations()` :288
- `_analyze_if_elif_chains()` :337
- `_check_responsibility_violations()` :366
- `_check_hardcoded_violations()` :399
- `_check_post_processing_violations()` :421
- `_calculate_score()` :439
- `_determine_quality_gate()` :451
- `_generate_recommendations()` :462
- `generate_report()` :497
- `_generate_text_report()` :516
- `_generate_json_report()` :591
- `_generate_html_report()` :601

## 相关页面

- [[core-cfg-patch-detector-enhanced|core/cfg/patch_detector_enhanced.py]]
- [[index|Wiki Index]]
