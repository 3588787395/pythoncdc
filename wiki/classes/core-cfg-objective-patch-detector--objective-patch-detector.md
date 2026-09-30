---
type: entity
title: ObjectivePatchDetector
tags:
  - code-kb
related:
  - "[[core-cfg-objective-patch-detector]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/objective_patch_detector.py
content_hash: 4eefe6bf5c1dd25ba051da25e9e872b1
class: ObjectivePatchDetector
defined_at: core/cfg/objective_patch_detector.py:56
class_lines: 329
method_count: 13
bases: []
sources:
  - core/cfg/objective_patch_detector.py
---

# ObjectivePatchDetector

定义于 `core/cfg/objective_patch_detector.py:56`（类体 329 行，13 个方法），所属模块 [[core-cfg-objective-patch-detector]]。

> 客观补丁检测器 - 基于代码特征而非注释

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :59
- `analyze_file()` :82
- `analyze_method()` :112
- `_infer_end_line()` :147
- `_check_d1_algorithm_basis()` :163
- `_check_d2_special_branches()` :177
- `_extract_test_pattern()` :189
- `_node_signature()` :205
- `_check_d3_postprocessing()` :217
- `_check_d4_cross_domain_access()` :246
- `_check_d5_multi_path_generation()` :290
- `_check_d6_hardcoded_references()` :326
- `generate_report()` :345

## 相关页面

- [[core-cfg-objective-patch-detector|core/cfg/objective_patch_detector.py]]
- [[index|Wiki Index]]
