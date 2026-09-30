---
type: entity
title: CFGASTConverter
tags:
  - code-kb
related:
  - "[[core-cfg-ast-converter]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/ast_converter.py
content_hash: 76e96d6383af1bd0550ae12d6b0eaad0
class: CFGASTConverter
defined_at: core/cfg/ast_converter.py:34
class_lines: 1775
method_count: 83
bases: []
sources:
  - core/cfg/ast_converter.py
---

# CFGASTConverter

定义于 `core/cfg/ast_converter.py:34`（类体 1775 行，83 个方法），所属模块 [[core-cfg-ast-converter]]。

> CFG AST到项目AST的转换器

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :42
- `convert()` :105
- `convert_body()` :156
- `_convert_module()` :190
- `_create_const_placeholder()` :204
- `_convert_function_def()` :243
- `_convert_class_def()` :297
- `_convert_if()` :345
- `_convert_for()` :478
- `_convert_async_for()` :507
- `_convert_while()` :536
- `_convert_try()` :556
- `_convert_with()` :589
- `_convert_async_with()` :608
- `_convert_return()` :626
- `_convert_yield()` :643
- `_convert_yield_from()` :651
- `_convert_yield_expr()` :659
- `_convert_starred_full()` :667
- `_convert_iter_full()` :676
- `_convert_assign()` :687
- `_convert_aug_assign()` :717
- `_convert_ann_assign()` :737
- `_convert_assert()` :763
- `_convert_expr_stmt()` :779
- `_convert_pass()` :788
- `_convert_break()` :792
- `_convert_continue()` :796
- `_convert_delete()` :800
- `_convert_import()` :822
- `_convert_import_from()` :843
- `_convert_global()` :865
- `_convert_nonlocal()` :873
- `_convert_block()` :881
- `_convert_sequence()` :885
- `_convert_expression()` :891
- `_convert_constant_full()` :1050
- `_convert_name_full()` :1055
- `_convert_binop_full()` :1060
- `_convert_augassign_full()` :1089
- `_convert_unaryop_full()` :1124
- `_convert_boolop_full()` :1143
- `_convert_compare_full()` :1171
- `_convert_call_full()` :1234
- `_convert_attribute_full()` :1272
- `_convert_subscript_full()` :1284
- `_convert_list_full()` :1293
- `_convert_tuple_full()` :1301
- `_convert_dict_full()` :1309
- `_convert_set_full()` :1323
- `_convert_ifexp_full()` :1331
- `_convert_joined_str_full()` :1345
- `_convert_formatted_value_full()` :1365
- `_convert_except_handler()` :1394
- `_convert_with_item()` :1424
- `_convert_arguments()` :1440
- `_convert_constant_expr()` :1480
- `_convert_name_expr()` :1484
- `_convert_binop_expr()` :1488
- `_convert_unaryop_expr()` :1493
- `_convert_compare_expr()` :1498
- `_convert_call_expr()` :1503
- `_convert_attribute_expr()` :1508
- `_convert_subscript_expr()` :1513
- `_convert_list_expr()` :1518
- `_convert_tuple_expr()` :1522
- `_convert_dict_expr()` :1526
- `_convert_set_expr()` :1530
- `_convert_named_expr()` :1534
- `_convert_named_expr_full()` :1540
- `_convert_await_expr()` :1546
- `_convert_await_expr_full()` :1551
- `_convert_raise_expr()` :1556
- `_convert_list_comp_expr()` :1570
- `_convert_set_comp_expr()` :1576
- `_convert_dict_comp_expr()` :1582
- `_convert_generator_exp_expr()` :1589
- `_convert_lambda_expr()` :1596
- `_convert_match()` :1625
- `_convert_case()` :1641
- `_convert_match_pattern()` :1668
- `_convert_slice_full()` :1790
- `_convert_comprehensions()` :1797

## 相关页面

- [[core-cfg-ast-converter|core/cfg/ast_converter.py]]
- [[index|Wiki Index]]
