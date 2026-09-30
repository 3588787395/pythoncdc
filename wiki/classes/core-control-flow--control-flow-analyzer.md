---
type: entity
title: ControlFlowAnalyzer
tags:
  - code-kb
related:
  - "[[core-control-flow]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/control_flow.py
content_hash: 611a07e92e9dae429e01250ef1f8f8c3
class: ControlFlowAnalyzer
defined_at: core/control_flow.py:108
class_lines: 1498
method_count: 92
bases: []
sources:
  - core/control_flow.py
---

# ControlFlowAnalyzer

定义于 `core/control_flow.py:108`（类体 1498 行，92 个方法），所属模块 [[core-control-flow]]。

> 控制流分析器，基于C++版本ASTree.cpp的控制流分析算法实现

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :113
- `analyze()` :125
- `_find_block_starts()` :155
- `_get_instruction_size()` :181
- `_create_blocks()` :190
- `_infer_block_type()` :212
- `_assign_instructions_to_blocks()` :232
- `_find_block_containing_offset()` :245
- `_connect_blocks()` :252
- `_is_terminator_block()` :267
- `detect_function_calls_returns()` :276
- `_analyze_function_calls()` :305
- `_is_function_call_instruction()` :327
- `_analyze_call_target()` :343
- `_is_call_target_instruction()` :374
- `_determine_target_type()` :386
- `_analyze_call_arguments()` :399
- `_analyze_return_statements()` :416
- `_is_return_instruction()` :433
- `_analyze_return_value()` :440
- `_is_value_instruction()` :461
- `_determine_value_type()` :470
- `detect_for_while_loops()` :483
- `_detect_for_loops()` :508
- `_is_for_loop_block()` :522
- `_detect_while_loops()` :530
- `_is_while_loop_block()` :543
- `_detect_nested_loops()` :551
- `_is_block_contained_in_block()` :566
- `_calculate_loop_nesting_level()` :571
- `_is_loop_block()` :581
- `_analyze_function_entries_exits()` :585
- `_analyze_parameter_passing()` :600
- `analyze_complete_control_flow()` :620
- `_calculate_complexity_metrics()` :646
- `optimize_control_flow_analysis()` :675
- `_optimize_basic_blocks()` :713
- `_merge_redundant_blocks()` :720
- `_remove_redundant_jumps()` :737
- `_find_next_block()` :753
- `_handle_jump_instructions()` :770
- `get_block_at_offset()` :778
- `detect_conditions()` :782
- `detect_if_elif_else_structure()` :801
- `_analyze_if_block()` :830
- `_is_conditional_jump()` :863
- `_analyze_condition_branches()` :876
- `_detect_elif_chains()` :889
- `_build_elif_chain()` :897
- `_analyze_elif_block()` :915
- `_detect_else_blocks()` :936
- `_ends_with_terminator()` :948
- `_find_next_block()` :955
- `detect_loops()` :972
- `detect_for_while_loops()` :990
- `_detect_for_loops()` :1015
- `_detect_while_loops()` :1022
- `_analyze_for_loop()` :1029
- `_analyze_for_loop_structure()` :1058
- `_analyze_while_loop()` :1079
- `_analyze_while_loop_structure()` :1109
- `_find_condition_block()` :1122
- `_analyze_while_loop_body()` :1127
- `_check_for_break_continue()` :1142
- `_detect_nested_loops()` :1150
- `_is_nested_loop()` :1166
- `analyze_loop_control_flow()` :1182
- `_analyze_loop_control_flow()` :1209
- `_analyze_loop_dependence()` :1224
- `_has_control_dependency()` :1236
- `detect_exception_handling()` :1241
- `_analyze_try_block()` :1273
- `_analyze_exception_structure()` :1301
- `_analyze_finally_block()` :1310
- `_analyze_except_handlers()` :1323
- `_analyze_single_except_handler()` :1343
- `_extract_exception_types()` :1370
- `_find_next_except_handler()` :1384
- `_is_out_of_try_block()` :1393
- `_detect_except_blocks()` :1399
- `_detect_finally_blocks()` :1405
- `_detect_nested_exceptions()` :1411
- `_is_nested_exception()` :1427
- `analyze_exception_control_flow()` :1436
- `_analyze_exception_propagation()` :1473
- `detect_break_continue_jumps()` :1485
- `_analyze_break_continue_statements()` :1512
- `_analyze_jump_targets()` :1528
- `_analyze_loop_dependencies()` :1544
- `_is_jump_dependent_on_loop()` :1565
- `get_control_flow_graph()` :1580
- `print_analysis()` :1593

## 相关页面

- [[core-control-flow|core/control_flow.py]]
- [[index|Wiki Index]]
