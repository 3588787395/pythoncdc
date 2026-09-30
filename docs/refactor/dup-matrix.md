# 重复矩阵（生成文档）

> 由 `tools/anatomy/extract_stages.py` 生成。生成时刻 `2026-09-29 00:38:53`，git HEAD `78679fd0`。
> 判据（spec `dup-triage`）：同名数 / 同体数 / 函数体 AST 哈希三件套；行数量级相似**不作为**重复判据。

## 全量文件对（同名 ≥ 3）

| 文件 A | 文件 B | A 函数数 | B 函数数 | 同名 | 同体 | 结论 | AST 哈希样本 |
|---|---|---|---|---|---|---|---|
| `parsers/ast_builder.py` | `parsers/ast_builder_cleaned.py` | 247 | 245 | 245 | 212 | 合并/删除候选 | 002e36593f, 01a994c736, 01d7898a1d |
| `core/ast_nodes.py` | `core/astree.py` | 154 | 43 | 10 | 3 | 不同构，保留 | 0664d20daa, 33ecc149f8, 4e2d817b49 |
| `core/control_flow.py` | `bytecode/pyc_disasm.py` | 96 | 11 | 4 | 2 | 不同构，保留 | 05209c95e8, 2a61c73986 |
| `core/pyc_objects.py` | `core/PycObject.py` | 51 | 29 | 16 | 1 | 不同构，保留 | 8571215ea2 |
| `core/ast_nodes.py` | `core/pyc_objects.py` | 154 | 51 | 11 | 1 | 不同构，保留 | cb9ae75333 |
| `bytecode/python311_support.py` | `bytecode/python312_plus.py` | 23 | 11 | 4 | 1 | 不同构，保留 | d47aeab037 |
| `core/fast_stack.py` | `utils/stack.py` | 37 | 29 | 9 | 0 | 不同构，保留 | — |
| `core/ast_nodes.py` | `core/cfg/basic_block.py` | 154 | 30 | 8 | 0 | 不同构，保留 | — |
| `core/cfg/code_generator.py` | `core/cfg/region_ast_generator.py` | 126 | 256 | 7 | 0 | 不同构，保留 | — |
| `core/ast_nodes.py` | `core/PycObject.py` | 154 | 29 | 6 | 0 | 不同构，保留 | — |
| `core/astree.py` | `bytecode/bytecode_ops.py` | 43 | 28 | 6 | 0 | 不同构，保留 | — |
| `core/cfg/basic_block.py` | `core/control_flow.py` | 30 | 96 | 6 | 0 | 不同构，保留 | — |
| `core/cfg/basic_block.py` | `core/pyc_objects.py` | 30 | 51 | 6 | 0 | 不同构，保留 | — |
| `core/ast_nodes.py` | `core/fast_stack.py` | 154 | 37 | 5 | 0 | 不同构，保留 | — |
| `core/cfg/basic_block.py` | `core/cfg/cfg_builder.py` | 30 | 30 | 5 | 0 | 不同构，保留 | — |
| `core/cfg/basic_block.py` | `core/PycObject.py` | 30 | 29 | 5 | 0 | 不同构，保留 | — |
| `core/cfg/code_generator.py` | `parsers/code_generator.py` | 126 | 149 | 5 | 0 | 不同构，保留 | — |
| `core/fast_stack.py` | `core/pyc_objects.py` | 37 | 51 | 5 | 0 | 不同构，保留 | — |
| `parsers/enhanced_class_handler.py` | `parsers/enhanced_decorator_handler.py` | 7 | 6 | 5 | 0 | 不同构，保留 | — |
| `core/ast_nodes.py` | `core/cfg/cfg_builder.py` | 154 | 30 | 4 | 0 | 不同构，保留 | — |
| `core/cache_system.py` | `core/cfg/cfg_optimizer.py` | 24 | 15 | 4 | 0 | 不同构，保留 | — |
| `core/cfg/ast_generator_v2.py` | `core/cfg/region_ast_generator.py` | 111 | 256 | 4 | 0 | 不同构，保留 | — |
| `core/cfg/basic_block.py` | `core/cfg/dominator_analyzer.py` | 30 | 27 | 4 | 0 | 不同构，保留 | — |
| `core/cfg/basic_block.py` | `core/fast_stack.py` | 30 | 37 | 4 | 0 | 不同构，保留 | — |
| `core/cfg/patch_detector.py` | `core/cfg/patch_detector_enhanced.py` | 34 | 20 | 4 | 0 | 不同构，保留 | — |
| `core/cfg/region_ast_generator.py` | `parsers/ast_builder.py` | 256 | 247 | 4 | 0 | 不同构，保留 | — |
| `core/cfg/region_ast_generator.py` | `parsers/ast_builder_cleaned.py` | 256 | 245 | 4 | 0 | 不同构，保留 | — |
| `core/cfg/structured_analyzer.py` | `parsers/ast_builder.py` | 101 | 247 | 4 | 0 | 不同构，保留 | — |
| `core/cfg/structured_analyzer.py` | `parsers/ast_builder_cleaned.py` | 101 | 245 | 4 | 0 | 不同构，保留 | — |
| `core/control_flow.py` | `parsers/ast_builder.py` | 96 | 247 | 4 | 0 | 不同构，保留 | — |
| `core/control_flow.py` | `parsers/ast_builder_cleaned.py` | 96 | 245 | 4 | 0 | 不同构，保留 | — |
| `core/pyc_stream.py` | `core/PycObject.py` | 25 | 29 | 4 | 0 | 不同构，保留 | — |
| `core/ast_nodes.py` | `core/cfg/region_analyzer.py` | 154 | 240 | 3 | 0 | 不同构，保留 | — |
| `core/ast_nodes.py` | `core/control_flow.py` | 154 | 96 | 3 | 0 | 不同构，保留 | — |
| `core/ast_nodes.py` | `bytecode/pyc_disasm.py` | 154 | 11 | 3 | 0 | 不同构，保留 | — |
| `core/cache_system.py` | `core/fast_stack.py` | 24 | 37 | 3 | 0 | 不同构，保留 | — |
| `core/cache_system.py` | `core/pyc_objects.py` | 24 | 51 | 3 | 0 | 不同构，保留 | — |
| `core/cache_system.py` | `utils/stack.py` | 24 | 29 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/ast_generator_v2.py` | `parsers/ast_builder.py` | 111 | 247 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/ast_generator_v2.py` | `parsers/ast_builder_cleaned.py` | 111 | 245 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/basic_block.py` | `core/cfg/opcode_feature_detector.py` | 30 | 102 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/cfg_builder.py` | `core/control_flow.py` | 30 | 96 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/cfg_builder.py` | `core/fast_stack.py` | 30 | 37 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/cfg_builder.py` | `core/pyc_objects.py` | 30 | 51 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/objective_patch_detector.py` | `core/cfg/patch_detector_enhanced.py` | 14 | 20 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/opcode_feature_detector.py` | `core/control_flow.py` | 102 | 96 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/opcode_feature_detector.py` | `bytecode/pyc_disasm.py` | 102 | 11 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/region_analyzer.py` | `core/cfg/region_ast_generator.py` | 240 | 256 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/region_analyzer.py` | `core/cfg/structured_analyzer.py` | 240 | 101 | 3 | 0 | 不同构，保留 | — |
| `core/cfg/structured_analyzer.py` | `core/control_flow.py` | 101 | 96 | 3 | 0 | 不同构，保留 | — |
| `core/control_flow.py` | `core/fast_stack.py` | 96 | 37 | 3 | 0 | 不同构，保留 | — |
| `core/control_flow.py` | `core/pyc_objects.py` | 96 | 51 | 3 | 0 | 不同构，保留 | — |
| `core/control_flow.py` | `core/PycObject.py` | 96 | 29 | 3 | 0 | 不同构，保留 | — |
| `core/fast_stack.py` | `core/PycObject.py` | 37 | 29 | 3 | 0 | 不同构，保留 | — |
| `core/pyc_objects.py` | `core/pyc_stream.py` | 51 | 25 | 3 | 0 | 不同构，保留 | — |
| `core/pyc_objects.py` | `bytecode/unified_analyzer.py` | 51 | 17 | 3 | 0 | 不同构，保留 | — |
| `core/pyc_stream.py` | `bytecode/unified_analyzer.py` | 25 | 17 | 3 | 0 | 不同构，保留 | — |
| `core/PycObject.py` | `bytecode/unified_analyzer.py` | 29 | 17 | 3 | 0 | 不同构，保留 | — |
| `parsers/enhanced_class_handler.py` | `bytecode/python311_support.py` | 7 | 23 | 3 | 0 | 不同构，保留 | — |
| `parsers/enhanced_decorator_handler.py` | `bytecode/python311_support.py` | 6 | 23 | 3 | 0 | 不同构，保留 | — |
| `utils/bytecode_comparator.py` | `utils/bytecode_comparator_cfg.py` | 5 | 12 | 3 | 0 | 不同构，保留 | — |
| `pycdc.py` | `pycdas.py` | 5 | 5 | 3 | 0 | 不同构，保留 | — |

## 差异函数明细（需逐个判定保留哪一侧）

### `parsers/ast_builder.py` ↔ `parsers/ast_builder_cleaned.py`：33 个同名不同体函数

`__init__`、`_before_with`、`_build_expression_from_instructions`、`_call_function`、`_check_if_finally_block`、`_convert_cfg_node`、`_copy`、`_create_class_from_code`、`_create_class_from_python_code`、`_create_function_from_code`、`_create_function_from_python_code`、`_emit`、`_is_try_except_pattern`、`_jump_forward`、`_load_closure`、`_load_const`、`_make_function`、`_parse_comprehension_element`、`_pop_jump_forward_if_false`、`_pop_jump_forward_if_true`、`_pop_jump_if_false`、`_pop_top`、`_process_instruction`、`_process_module_level_functions`、`_push_exc_info`、`_return_value`、`_setup_with`、`_store_attr`、`_store_fast`、`_store_name`、`_swap`、`_yield_value`、`build_from_code`


## 净减行数折算（design D5）

净减行数只对「合并/删除」结论成立；阶段化搬移不计入净减行数。
