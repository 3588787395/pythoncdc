---
type: entity
title: PatternParser
tags:
  - code-kb
related:
  - "[[core-cfg-pattern-parser]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/pattern_parser.py
content_hash: 73a35a26a8b249ba9e1067e703fbf1cf
class: PatternParser
defined_at: core/cfg/pattern_parser.py:15
class_lines: 1797
method_count: 22
bases: []
sources:
  - core/cfg/pattern_parser.py
---

# PatternParser

定义于 `core/cfg/pattern_parser.py:15`（类体 1797 行，22 个方法），所属模块 [[core-cfg-pattern-parser]]。

> Match Pattern解析器 - 职责：从字节码构建pattern AST节点

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :41
- `parse_case_pattern()` :47
- `parse_case_guard()` :66
- `collect_pattern_blocks()` :78
- `_collect_pattern_blocks()` :93
- `_extract_case_guard_from_blocks()` :305
- `_find_real_match_header()` :549
- `_collect_all_pattern_instrs()` :584
- `_is_pattern_continuation_block()` :644
- `_extract_case_pattern()` :681
- `_has_as_binding_copy()` :816
- `_find_as_binding()` :840
- `_find_last_store_on_success_path()` :936
- `_is_pattern_block_for_as()` :991
- `_find_store_in_successors()` :1043
- `_collect_pattern_bindings_from_successor()` :1066
- `_extract_sequence_pattern()` :1097
- `_extract_starred_sequence_pattern()` :1282
- `_count_class_pattern_instrs()` :1383
- `_extract_class_pattern()` :1457
- `_extract_or_or_literal_pattern()` :1599
- `_extract_mapping_pattern()` :1700

## 相关页面

- [[core-cfg-pattern-parser|core/cfg/pattern_parser.py]]
- [[index|Wiki Index]]
