---
type: entity
title: SourceEquivalenceChecker
tags:
  - code-kb
related:
  - "[[utils-source-equivalence-checker]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: utils/source_equivalence_checker.py
content_hash: 5be87d57e81153f52af925f5f0de97f8
class: SourceEquivalenceChecker
defined_at: utils/source_equivalence_checker.py:18
class_lines: 2167
method_count: 60
bases: []
sources:
  - utils/source_equivalence_checker.py
---

# SourceEquivalenceChecker

定义于 `utils/source_equivalence_checker.py:18`（类体 2167 行，60 个方法），所属模块 [[utils-source-equivalence-checker]]。

> 源代码等效性检查器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :21
- `enable_semantic_analysis()` :42
- `enable_strict_mode()` :46
- `normalize_variable_names()` :50
- `analyze_variable_usage()` :54
- `_extract_variable_usage()` :90
- `_traverse_ast()` :99
- `_get_variable_usage_pattern()` :122
- `analyze_control_flow()` :133
- `_extract_control_flow()` :165
- `_traverse_control_flow()` :178
- `_extract_name()` :215
- `_extract_expression()` :226
- `_extract_operator()` :251
- `calculate_complexity_metrics()` :274
- `_calculate_ast_complexity()` :294
- `_calculate_ast_complexity_recursive()` :310
- `compute_semantic_hash()` :341
- `_compute_ast_hash()` :357
- `_extract_ast_structure()` :365
- `_should_include_attribute()` :390
- `generate_detailed_report()` :412
- `compare_source_files()` :504
- `compare_source_strings()` :523
- `_safe_parse_ast()` :578
- `_basic_text_comparison()` :594
- `_calculate_text_similarity()` :618
- `_normalize_text()` :636
- `_compare_asts()` :663
- `_compare_module_nodes()` :691
- `_compare_nodes()` :723
- `_compare_generic_nodes()` :784
- `_compare_assign_nodes()` :884
- `_compare_function_nodes()` :924
- `_compare_class_nodes()` :999
- `_compare_if_nodes()` :1058
- `_compare_for_nodes()` :1119
- `_compare_while_nodes()` :1188
- `_compare_try_nodes()` :1249
- `_compare_import_nodes()` :1388
- `_compare_importfrom_nodes()` :1436
- `_compare_expr_nodes()` :1507
- `_compare_return_nodes()` :1520
- `_compare_break_nodes()` :1546
- `_compare_continue_nodes()` :1559
- `_compare_with_nodes()` :1572
- `_compare_expression_nodes()` :1641
- `_compare_constant_nodes()` :1693
- `_compare_name_nodes()` :1716
- `_compare_attribute_nodes()` :1739
- `_compare_call_nodes()` :1770
- `_compare_binop_nodes()` :1835
- `_compare_unaryop_nodes()` :1874
- `_compare_boolop_nodes()` :1905
- `_compare_compare_nodes()` :1945
- `_compare_subscript_nodes()` :2002
- `_compare_list_nodes()` :2033
- `_compare_tuple_nodes()` :2068
- `_compare_dict_nodes()` :2103
- `_compare_set_nodes()` :2151

## 相关页面

- [[utils-source-equivalence-checker|utils/source_equivalence_checker.py]]
- [[index|Wiki Index]]
