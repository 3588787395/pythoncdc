---
type: entity
title: OpcodeFeatureDetector
tags:
  - code-kb
related:
  - "[[core-cfg-opcode-feature-detector]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/cfg/opcode_feature_detector.py
content_hash: 31717d3055eeb3a41bc58648a1654ff5
class: OpcodeFeatureDetector
defined_at: core/cfg/opcode_feature_detector.py:40
class_lines: 647
method_count: 100
bases: []
sources:
  - core/cfg/opcode_feature_detector.py
---

# OpcodeFeatureDetector

定义于 `core/cfg/opcode_feature_detector.py:40`（类体 647 行，100 个方法），所属模块 [[core-cfg-opcode-feature-detector]]。

> 操作码特征检测器 - 替代所有硬编码操作码名称

## 继承与 override

- 无基类（模块内独立定义）

## 方法清单

- `__init__()` :64
- `_get_opcode()` :84
- `_init_opcode_sets()` :103
- `is_conditional_jump()` :182
- `is_unconditional_jump()` :197
- `is_loop_header_opcode()` :208
- `is_for_iter()` :219
- `is_get_anext()` :230
- `is_iterator_setup_opcode()` :241
- `is_send()` :253
- `is_yield_value()` :264
- `is_jump_backward_no_interrupt()` :275
- `is_get_yield_from_iter()` :286
- `is_short_circuit_jump()` :297
- `is_exception_related()` :310
- `is_setup_instruction()` :321
- `get_opcode_category()` :334
- `is_python311_plus()` :360
- `get_opcode_name()` :373
- `get_all_opcodes_in_category()` :392
- `_get_opname()` :411
- `_is_opname()` :415
- `_is_opname_in()` :419
- `_opname_startswith()` :423
- `is_store_instruction()` :428
- `is_store_fast()` :432
- `is_store_name()` :435
- `is_store_global()` :438
- `is_store_deref()` :441
- `is_store_subscr()` :444
- `is_store_attr()` :447
- `is_any_store()` :450
- `is_load_instruction()` :455
- `is_load_const()` :459
- `is_load_fast()` :462
- `is_load_name()` :465
- `is_load_global()` :468
- `is_load_deref()` :471
- `is_load_attr()` :474
- `is_load_method()` :477
- `is_load_assertion_error()` :480
- `is_any_load()` :483
- `is_return_instruction()` :489
- `is_return_value()` :493
- `is_return_const()` :496
- `is_return_generator()` :499
- `is_jump_forward()` :502
- `is_jump_backward()` :505
- `is_jump_absolute()` :508
- `is_build_list()` :511
- `is_build_tuple()` :514
- `is_build_set()` :517
- `is_build_map()` :520
- `is_build_string()` :523
- `is_any_build()` :526
- `is_pop_top()` :531
- `is_nop()` :534
- `is_resume()` :537
- `is_cache()` :540
- `is_copy()` :543
- `is_swap()` :546
- `is_compare_op()` :549
- `is_is_op()` :552
- `is_contains_op()` :555
- `is_any_compare()` :558
- `is_call()` :562
- `is_call_function()` :565
- `is_call_method()` :568
- `is_precall()` :571
- `is_any_call()` :574
- `is_pop_except()` :578
- `is_push_exc_info()` :581
- `is_reraise()` :584
- `is_raise_varargs()` :587
- `is_end_async_for()` :590
- `is_check_exc_match()` :593
- `is_with_except_start()` :596
- `is_exception_handling()` :599
- `is_import_name()` :606
- `is_import_from()` :609
- `is_make_function()` :612
- `is_unpack_sequence()` :615
- `is_unpack_ex()` :618
- `is_delete_subscr()` :621
- `is_delete_attr()` :624
- `is_delete_name()` :627
- `is_delete_global()` :630
- `is_get_iter()` :633
- `is_get_aiter()` :636
- `is_before_with()` :639
- `is_before_async_with()` :642
- `is_push_null()` :645
- `is_noise_instruction()` :648
- `is_debug_or_noise()` :652
- `has_for_iter_in_opname()` :656
- `is_loop_back_jump()` :661
- `is_forward_jump()` :665
- `is_backward_jump()` :671
- `is_terminator()` :678
- `__repr__()` :684

## 相关页面

- [[core-cfg-opcode-feature-detector|core/cfg/opcode_feature_detector.py]]
- [[index|Wiki Index]]
