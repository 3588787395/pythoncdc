# 区域归约算法解剖（生成文档）

> 由 `tools/anatomy/extract_stages.py` 生成，**不要手改数字**。生成时刻 `2026-09-29 00:38:53`，git HEAD `78679fd0`。
> 源码变化后重跑：`python tools/anatomy/extract_stages.py`（并行迭代代理改过 region 文件时必须重跑，见 design D4）。

## 阶段模型（design D1）

区域归约 = 七个阶段，相邻阶段只通过显式数据结构传递：

| 阶段 | 名称 | 输入 | 输出 |
|---|---|---|---|
| S1 | CFG 构建 | `BasicBlock/CFGBuilder` | `BasicBlock 图 + 边集` |
| S2 | 块语义标注 | `BasicBlock -> BlockSemantics` | `BlockRole 标注后的块集` |
| S3 | 区域识别 | `BlockSemantics` | `9 类 Region 对象` |
| S4 | 区域层级装配 | `Region 对象列表` | `带 parent/children 的区域树` |
| S5 | 结构化语句生成 | `区域树` | `语句 AST` |
| S6 | 表达式重建 | `语句 AST` | `完整表达式 AST` |
| S7 | 后处理 | `完整 AST` | `可输出 AST` |

## 归属汇总（RegionAnalyzer + RegionASTGenerator）

| 阶段 | 名称 | 输入 | 输出 | 方法数 | 行数 | 占比 |
|---|---|---|---|---|---|---|
| S1 | CFG 构建 | BasicBlock/CFGBuilder | BasicBlock 图 + 边集 | 87 | 5349 | 6.9% |
| S2 | 块语义标注 | BasicBlock -> BlockSemantics | BlockRole 标注后的块集 | 15 | 833 | 1.1% |
| S3 | 区域识别 | BlockSemantics | 9 类 Region 对象 | 88 | 19983 | 25.6% |
| S4 | 区域层级装配 | Region 对象列表 | 带 parent/children 的区域树 | 8 | 525 | 0.7% |
| S5 | 结构化语句生成 | 区域树 | 语句 AST | 89 | 33179 | 42.5% |
| S6 | 表达式重建 | 语句 AST | 完整表达式 AST | 82 | 13843 | 17.7% |
| S7 | 后处理 | 完整 AST | 可输出 AST | 28 | 1784 | 2.3% |
| U | Unclassified | — | — | 63 | 2517 | 3.2% |

合计 460 个方法 / 78,013 行。Unclassified 占比 3.2%
（阈值 15%，见 spec `region-stage-model`）。

### RegionAnalyzer（`core/cfg/region_analyzer.py:1197`）

类体 27,175 行 / 212 个方法，方法合计 26,870 行（占类体 99%）

| 阶段 | 名称 | 方法数 | 行数 | 占比 |
|---|---|---|---|---|
| S1 | CFG 构建 | 70 | 4166 | 15.5% |
| S2 | 块语义标注 | 9 | 605 | 2.3% |
| S3 | 区域识别 | 77 | 19337 | 72.0% |
| S4 | 区域层级装配 | 6 | 432 | 1.6% |
| S6 | 表达式重建 | 4 | 320 | 1.2% |
| S7 | 后处理 | 18 | 1169 | 4.4% |
| U | Unclassified | 28 | 841 | 3.1% |

体长前 12 方法（外提成本参考，`self` 读/写字段数越高外提越贵）：

| 方法 | 行 | 行数 | 阶段 | 得分 | self 读/写 | 锚点 |
|---|---|---|---|---|---|---|
| `_identify_ternary_regions` | 20515 | 2898 | S3 | 12.799999999999999 | 9/8 | `core/cfg/region_analyzer.py:20515` |
| `_identify_conditional_regions` | 15981 | 2198 | S3 | 10.639999999999999 | 26/1 | `core/cfg/region_analyzer.py:15981` |
| `_build_elif_region` | 18719 | 1523 | S3 | 10.799999999999999 | 13/0 | `core/cfg/region_analyzer.py:18719` |
| `_detect_boolop_conditional_chain` | 25183 | 1506 | S3 | 8.120000000000001 | 11/0 | `core/cfg/region_analyzer.py:25183` |
| `_identify_try_except_regions` | 7603 | 1391 | S3 | 6.68 | 9/1 | `core/cfg/region_analyzer.py:7603` |
| `_identify_loop_regions` | 3782 | 837 | S3 | 7.3999999999999995 | 21/2 | `core/cfg/region_analyzer.py:3782` |
| `_find_loop_else` | 5242 | 696 | S3 | 2.88 | 13/0 | `core/cfg/region_analyzer.py:5242` |
| `analyze` | 1335 | 558 | S3 | 7.2 | 36/6 | `core/cfg/region_analyzer.py:1335` |
| `_build_basic_if_region` | 18200 | 518 | S3 | 5.76 | 9/0 | `core/cfg/region_analyzer.py:18200` |
| `_identify_boolop_regions` | 23420 | 517 | S3 | 8.48 | 8/1 | `core/cfg/region_analyzer.py:23420` |
| `_detect_break_continue` | 6055 | 513 | S3 | 2 | 5/0 | `core/cfg/region_analyzer.py:6055` |
| `_find_try_else_blocks` | 10647 | 462 | S3 | 2.1599999999999997 | 10/0 | `core/cfg/region_analyzer.py:10647` |

### RegionASTGenerator（`core/cfg/region_ast_generator.py:252`）

类体 51,488 行 / 248 个方法，方法合计 51,143 行（占类体 99%）

| 阶段 | 名称 | 方法数 | 行数 | 占比 |
|---|---|---|---|---|
| S1 | CFG 构建 | 17 | 1183 | 2.3% |
| S2 | 块语义标注 | 6 | 228 | 0.4% |
| S3 | 区域识别 | 11 | 646 | 1.3% |
| S4 | 区域层级装配 | 2 | 93 | 0.2% |
| S5 | 结构化语句生成 | 89 | 33179 | 64.9% |
| S6 | 表达式重建 | 78 | 13523 | 26.4% |
| S7 | 后处理 | 10 | 615 | 1.2% |
| U | Unclassified | 35 | 1676 | 3.3% |

体长前 12 方法（外提成本参考，`self` 读/写字段数越高外提越贵）：

| 方法 | 行 | 行数 | 阶段 | 得分 | self 读/写 | 锚点 |
|---|---|---|---|---|---|---|
| `_generate_block_statements_body` | 44955 | 4022 | S5 | 5.96 | 42/1 | `core/cfg/region_ast_generator.py:44955` |
| `_generate_ternary` | 35757 | 3639 | S5 | 8.0 | 44/0 | `core/cfg/region_ast_generator.py:35757` |
| `_process_if_blocks` | 21776 | 1696 | S5 | 9.6 | 32/1 | `core/cfg/region_ast_generator.py:21776` |
| `_loop_generate_while` | 5230 | 1561 | S5 | 10.76 | 32/0 | `core/cfg/region_ast_generator.py:5230` |
| `_generate_try` | 26128 | 1500 | S5 | 12.799999999999999 | 22/3 | `core/cfg/region_ast_generator.py:26128` |
| `_generate_boolop_impl` | 33487 | 1368 | S5 | 5.6 | 19/0 | `core/cfg/region_ast_generator.py:33487` |
| `_if_generate_normal` | 17949 | 1307 | S5 | 9.2 | 30/4 | `core/cfg/region_ast_generator.py:17949` |
| `_generate_with` | 29490 | 1300 | S5 | 10.4 | 23/0 | `core/cfg/region_ast_generator.py:29490` |
| `generate` | 672 | 1248 | S5 | 11.6 | 34/1 | `core/cfg/region_ast_generator.py:672` |
| `_if_generate_elif_chain` | 16103 | 1168 | S5 | 6.8 | 24/1 | `core/cfg/region_ast_generator.py:16103` |
| `_generate_try_body` | 24522 | 1115 | S5 | 11.6 | 12/1 | `core/cfg/region_ast_generator.py:24522` |
| `_loop_extract_self_loop_stmts` | 8516 | 997 | S6 | 3.5999999999999996 | 19/0 | `core/cfg/region_ast_generator.py:8516` |


## 冲突项（名族先验与 token 证据不一致，需人工确认）

共 97 个方法，最终归属以 token 证据为主。

| 类 | 方法 | 行 | 行数 | token 证据 | 名族先验 | 定稿阶段 |
|---|---|---|---|---|---|---|
| RegionASTGenerator | `_loop_extract_self_loop_stmts` | 8516 | 997 | S6 | S5 | S6 |
| RegionASTGenerator | `_generate_handler_body_statements` | 27789 | 990 | S6 | S5 | S6 |
| RegionASTGenerator | `_try_generate_conditional_break_or_continue` | 23627 | 823 | S6 | S5 | S6 |
| RegionAnalyzer | `_detect_break_continue` | 6055 | 513 | S1 | S3 | S3 |
| RegionASTGenerator | `_build_ternary_no_target_consumer_stmt` | 40197 | 448 | S6 | S5 | S5 |
| RegionASTGenerator | `_build_statements_from_instructions` | 28845 | 428 | S6 | S5 | S6 |
| RegionASTGenerator | `_generate_stmts_from_instrs` | 49411 | 353 | S6 | S5 | S6 |
| RegionASTGenerator | `_loop_dispatch_block` | 7398 | 324 | S5 | S7 | S5 |
| RegionASTGenerator | `_loop_handle_child_region_entry` | 11333 | 294 | S5 | S3 | S5 |
| RegionASTGenerator | `_generate_assert` | 3431 | 277 | S6 | S5 | S6 |
| RegionAnalyzer | `_detect_while_condition_boolop_chain` | 23938 | 266 | S1 | S3 | S3 |
| RegionAnalyzer | `_compute_merge_from_jump_targets` | 2203 | 248 | S4 | S7 | S7 |
| RegionASTGenerator | `_wrap_boolop_with_merge_compare` | 31849 | 243 | S6 | S7 | S6 |
| RegionASTGenerator | `_build_store_statement` | 50293 | 237 | S6 | S5 | S6 |
| RegionASTGenerator | `_generate_value_context_chain_compare_assign` | 12153 | 233 | S6 | S5 | S5 |
| RegionAnalyzer | `_classify_handler_type` | 9692 | 220 | S1 | S2 | S2 |
| RegionASTGenerator | `_loop_handle_exit_successors` | 10077 | 211 | S6 | S1 | S6 |
| RegionAnalyzer | `_detect_assert_boolop_chain` | 15133 | 208 | S1 | S3 | S3 |
| RegionASTGenerator | `_loop_handle_no_exit_successors` | 10389 | 207 | S6 | S1 | S6 |
| RegionASTGenerator | `_loop_extract_for_iter_pre_stmts` | 7138 | 187 | S6 | S5 | S6 |
| RegionASTGenerator | `_build_ternary_wrapped_expr` | 20056 | 171 | S3 | S6 | S6 |
| RegionAnalyzer | `_is_single_expression_block` | 2823 | 170 | S1 | S6 | S6 |
| RegionASTGenerator | `_try_generate_await_list_assign` | 21552 | 168 | S6 | S5 | S6 |
| RegionASTGenerator | `_try_generate_conditional_break` | 23473 | 153 | S6 | S5 | S6 |
| RegionAnalyzer | `_identify_with_regions` | 12282 | 152 | S4 | S3 | S3 |
| RegionASTGenerator | `_merge_block_is_then_exclusive` | 17406 | 150 | S5 | S7 | S7 |
| RegionASTGenerator | `_try_build_nested_ternary_as_if_cond` | 39585 | 150 | S5 | S4 | S5 |
| RegionAnalyzer | `_boolop_resolve_merge` | 24486 | 144 | S1 | S7 | S7 |
| RegionAnalyzer | `_collect_nested_literal_match` | 14321 | 141 | S3 | S4 | S3 |
| RegionAnalyzer | `_cleanup_try_else_in_loop_body` | 4685 | 138 | S2 | S7 | S7 |
| RegionAnalyzer | `_identify_chained_compare_regions` | 15495 | 136 | S4 | S3 | S3 |
| RegionASTGenerator | `_detect_if_region_as_while_loop` | 11960 | 134 | S5 | S3 | S5 |
| RegionASTGenerator | `_build_assert_message_ternary_stmt` | 40646 | 130 | S6 | S5 | S6 |
| RegionASTGenerator | `_build_effective_stmts` | 2787 | 126 | S6 | S5 | S6 |
| RegionASTGenerator | `_generate_return_ast` | 51618 | 122 | S6 | S5 | S6 |
| RegionAnalyzer | `_classify_loop_type` | 4905 | 119 | S1 | S2 | S2 |
| RegionASTGenerator | `_loop_extract_pre_stmts_from_instrs` | 11015 | 115 | S6 | S5 | S6 |
| RegionASTGenerator | `_loop_postprocess` | 11628 | 112 | S5 | S7 | S5 |
| RegionAnalyzer | `_collect_normal_exit_cleanup` | 11887 | 110 | S3 | S7 | S7 |
| RegionASTGenerator | `_detect_boolop_after_chained_compare` | 14376 | 100 | S6 | S3 | S6 |


## Unclassified 清单（需人工判定或修阶段模型）

| 类 | 方法 | 行 | 行数 | self 读/写 | 锚点 |
|---|---|---|---|---|---|
| RegionASTGenerator | `_ternary_pending_callee` | 42613 | 130 | 0/0 | `core/cfg/region_ast_generator.py:42613` |
| RegionAnalyzer | `_is_simple_match_case_block` | 13718 | 125 | 3/0 | `core/cfg/region_analyzer.py:13718` |
| RegionASTGenerator | `_extract_decorators` | 2312 | 121 | 1/0 | `core/cfg/region_ast_generator.py:2312` |
| RegionASTGenerator | `_build_assert_chained_compare` | 3761 | 121 | 4/0 | `core/cfg/region_ast_generator.py:3761` |
| RegionASTGenerator | `_process_instruction` | 49108 | 110 | 1/0 | `core/cfg/region_ast_generator.py:49108` |
| RegionASTGenerator | `_is_orphan_boundary_nop` | 44419 | 109 | 1/0 | `core/cfg/region_ast_generator.py:44419` |
| RegionASTGenerator | `_w16_split_value_groups` | 44602 | 101 | 0/0 | `core/cfg/region_ast_generator.py:44602` |
| RegionASTGenerator | `_extract_function_args` | 3065 | 90 | 1/0 | `core/cfg/region_ast_generator.py:3065` |
| RegionASTGenerator | `_build_multi_target_del_targets` | 41365 | 88 | 1/0 | `core/cfg/region_ast_generator.py:41365` |
| RegionAnalyzer | `_is_match_subject_block` | 12711 | 83 | 2/0 | `core/cfg/region_analyzer.py:12711` |
| RegionAnalyzer | `_verify_literal_match_chain` | 12853 | 66 | 2/0 | `core/cfg/region_analyzer.py:12853` |
| RegionAnalyzer | `_stack_effect` | 1244 | 60 | 0/0 | `core/cfg/region_analyzer.py:1244` |
| RegionAnalyzer | `_is_literal_default_block` | 12795 | 57 | 0/0 | `core/cfg/region_analyzer.py:12795` |
| RegionASTGenerator | `_loop_exit_is_implicit_return_none` | 44704 | 53 | 1/0 | `core/cfg/region_ast_generator.py:44704` |
| RegionASTGenerator | `_split_preload_into_siblings` | 39884 | 50 | 1/0 | `core/cfg/region_ast_generator.py:39884` |
| RegionASTGenerator | `_fstring_parts_from_segment` | 42563 | 49 | 2/0 | `core/cfg/region_ast_generator.py:42563` |
| RegionAnalyzer | `_mr_resolve_or_guard_jump` | 13302 | 48 | 3/0 | `core/cfg/region_analyzer.py:13302` |
| RegionASTGenerator | `_stack_effect` | 39983 | 48 | 0/0 | `core/cfg/region_ast_generator.py:39983` |
| RegionASTGenerator | `_condition_chain_targets_consistent` | 17358 | 47 | 1/0 | `core/cfg/region_ast_generator.py:17358` |
| RegionASTGenerator | `_compute_body_block_start` | 31769 | 46 | 0/0 | `core/cfg/region_ast_generator.py:31769` |
| RegionAnalyzer | `_w11_unprotected_else_candidate` | 10506 | 44 | 0/0 | `core/cfg/region_analyzer.py:10506` |
| RegionASTGenerator | `_extract_trapped_lhs_from_ternary` | 19520 | 43 | 0/0 | `core/cfg/region_ast_generator.py:19520` |
| RegionASTGenerator | `_extract_pre_ternary_instrs` | 19564 | 42 | 0/0 | `core/cfg/region_ast_generator.py:19564` |
| RegionAnalyzer | `_is_except_break_exit` | 6014 | 40 | 0/0 | `core/cfg/region_analyzer.py:6014` |
| RegionASTGenerator | `_build_walrus_assign` | 2746 | 40 | 2/0 | `core/cfg/region_ast_generator.py:2746` |
| RegionASTGenerator | `_w14_join_bare_return_none` | 51328 | 40 | 0/0 | `core/cfg/region_ast_generator.py:51328` |
| RegionASTGenerator | `_coalesce_compares` | 24483 | 38 | 1/0 | `core/cfg/region_ast_generator.py:24483` |
| RegionAnalyzer | `_is_implicit_default_body` | 14733 | 37 | 0/0 | `core/cfg/region_analyzer.py:14733` |
| RegionASTGenerator | `_handler_backedge_is_explicit_continue` | 20632 | 36 | 2/0 | `core/cfg/region_ast_generator.py:20632` |
| RegionAnalyzer | `_mr_collect_pattern_store_names` | 13077 | 32 | 1/0 | `core/cfg/region_analyzer.py:13077` |
| RegionASTGenerator | `_else_blocks_exit_enclosing_loop` | 16017 | 32 | 2/0 | `core/cfg/region_ast_generator.py:16017` |
| RegionASTGenerator | `_collect_pattern_store_names` | 31816 | 32 | 1/0 | `core/cfg/region_ast_generator.py:31816` |
| RegionAnalyzer | `_block_exits_loop` | 7572 | 30 | 1/0 | `core/cfg/region_analyzer.py:7572` |
| RegionASTGenerator | `_block_is_pure_back_edge_to_header` | 20444 | 30 | 2/0 | `core/cfg/region_ast_generator.py:20444` |
| RegionASTGenerator | `_r64b1_fv_conversion` | 42534 | 28 | 0/0 | `core/cfg/region_ast_generator.py:42534` |
| RegionAnalyzer | `_check_return_for_break` | 7407 | 27 | 0/0 | `core/cfg/region_analyzer.py:7407` |
| RegionAnalyzer | `_conditional_value_producing_arms` | 27161 | 27 | 0/0 | `core/cfg/region_analyzer.py:27161` |
| RegionASTGenerator | `_w14_has_following_code` | 51300 | 27 | 1/0 | `core/cfg/region_ast_generator.py:51300` |
| RegionASTGenerator | `_r23n16_blocks_have_explicit_return` | 16080 | 22 | 0/0 | `core/cfg/region_ast_generator.py:16080` |
| RegionASTGenerator | `_w14_explicit_return_flag` | 51369 | 20 | 2/0 | `core/cfg/region_ast_generator.py:51369` |
| RegionAnalyzer | `_w13_with_associated_handler` | 9512 | 17 | 1/0 | `core/cfg/region_analyzer.py:9512` |
| RegionASTGenerator | `_binary_op_arg_to_str` | 19998 | 17 | 0/0 | `core/cfg/region_ast_generator.py:19998` |
| RegionASTGenerator | `_w13_data_stream` | 25658 | 17 | 0/0 | `core/cfg/region_ast_generator.py:25658` |
| RegionAnalyzer | `_w13_data_stream` | 9467 | 16 | 0/0 | `core/cfg/region_analyzer.py:9467` |
| RegionASTGenerator | `_instruction_stack_effect` | 427 | 15 | 0/0 | `core/cfg/region_ast_generator.py:427` |
| RegionAnalyzer | `_scan_before_with_instructions` | 11998 | 14 | 2/0 | `core/cfg/region_analyzer.py:11998` |
| RegionAnalyzer | `_mr_resolve_body_entry` | 13232 | 14 | 1/0 | `core/cfg/region_analyzer.py:13232` |
| RegionAnalyzer | `_chain_compare_op_str` | 20500 | 14 | 0/0 | `core/cfg/region_analyzer.py:20500` |
| RegionAnalyzer | `_reraise_block_offsets` | 3604 | 13 | 2/1 | `core/cfg/region_analyzer.py:3604` |
| RegionAnalyzer | `_set_or_pattern_names` | 13460 | 13 | 1/0 | `core/cfg/region_analyzer.py:13460` |
| RegionAnalyzer | `_mr_bodies_are_equivalent` | 13474 | 12 | 0/0 | `core/cfg/region_analyzer.py:13474` |
| RegionAnalyzer | `_collect_consecutive_with_blocks` | 11680 | 10 | 1/0 | `core/cfg/region_analyzer.py:11680` |
| RegionAnalyzer | `_mr_find_case_jump_instruction` | 13291 | 10 | 0/0 | `core/cfg/region_analyzer.py:13291` |
| RegionASTGenerator | `_build_simple_load` | 19607 | 10 | 0/0 | `core/cfg/region_ast_generator.py:19607` |
| RegionAnalyzer | `_is_except_star_framework_block` | 12701 | 9 | 0/0 | `core/cfg/region_analyzer.py:12701` |
| RegionAnalyzer | `_is_wildcard_match_subject` | 14035 | 8 | 0/0 | `core/cfg/region_analyzer.py:14035` |
| RegionASTGenerator | `_is_implicit_return_block` | 16071 | 8 | 0/0 | `core/cfg/region_ast_generator.py:16071` |
| RegionASTGenerator | `_is_mangled_name` | 49092 | 7 | 0/0 | `core/cfg/region_ast_generator.py:49092` |
| RegionASTGenerator | `_safe_set_func_name` | 49100 | 7 | 1/0 | `core/cfg/region_ast_generator.py:49100` |
| RegionAnalyzer | `_is_back_edge_target` | 11282 | 6 | 0/0 | `core/cfg/region_analyzer.py:11282` |
| RegionAnalyzer | `_has_match_op` | 14691 | 5 | 0/0 | `core/cfg/region_analyzer.py:14691` |
| RegionAnalyzer | `_get_dominance_depth` | 3776 | 4 | 0/0 | `core/cfg/region_analyzer.py:3776` |
| RegionASTGenerator | `block_role` | 333 | 2 | 1/0 | `core/cfg/region_ast_generator.py:333` |
