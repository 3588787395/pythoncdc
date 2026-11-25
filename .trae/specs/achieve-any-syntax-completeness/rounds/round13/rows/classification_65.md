# no_occ 65 条逐锚点定性（v8_b1）

(a) 纯工具路径 15 | (b) legacy 死码 19 | (c) J 未覆盖形态 31 | 合计 65


## (a) 纯工具路径

| rule_id | symbol | anchor | 外层函数(入口数) | 证据要点 |
|---|---|---|---|---|
| RULE-d53ac6879d6a | Assign | patch_detector.py:328 | -@L- (-/-) | 纯工具路径 |
| RULE-b3b3c27de3f4 | AsyncFunctionDef | objective_patch_detector.py:89 | -@L- (-/-) | 纯工具路径 |
| RULE-526c2f9c8010 | Attribute | objective_patch_detector.py:197 | -@L- (-/-) | 纯工具路径 |
| RULE-20568d2871b4 | BoolOp | objective_patch_detector.py:195 | -@L- (-/-) | 纯工具路径 |
| RULE-93efbfe2473b | Call | objective_patch_detector.py:199 | -@L- (-/-) | 纯工具路径 |
| RULE-2845ddf0b9b8 | ClassDef | objective_patch_detector.py:93 | -@L- (-/-) | 纯工具路径 |
| RULE-2b862ecf9a11 | Compare | objective_patch_detector.py:191 | -@L- (-/-) | 纯工具路径 |
| RULE-1f3252f64295 | Constant | objective_patch_detector.py:213 | -@L- (-/-) | 纯工具路径 |
| RULE-2d4b43ea95f6 | FunctionDef | objective_patch_detector.py:89 | -@L- (-/-) | 纯工具路径 |
| RULE-3d070d0913cc | If | objective_patch_detector.py:181 | -@L- (-/-) | 纯工具路径 |
| RULE-4c10258ace4e | List | patch_detector.py:425 | -@L- (-/-) | 纯工具路径 |
| RULE-b56901a142a6 | Name | objective_patch_detector.py:207 | -@L- (-/-) | 纯工具路径 |
| RULE-bd1b6b8bb350 | Set | patch_detector.py:425 | -@L- (-/-) | 纯工具路径 |
| RULE-fd29f404c20d | Subscript | objective_patch_detector.py:211 | -@L- (-/-) | 纯工具路径 |
| RULE-87d3e450c5e4 | Tuple | patch_detector.py:425 | -@L- (-/-) | 纯工具路径 |

## (b) legacy 死码（结构死/管道死）

| rule_id | symbol | anchor | 外层函数(入口数) | 证据要点 |
|---|---|---|---|---|
| RULE-eb29ec1ad01a | AnnAssign | code_generator.py:285 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-1b5b4d7115d9 | Assert | code_generator.py:378 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-eed79a22277c | Assign | code_generator.py:283 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-0b22204ea11f | AsyncFor | code_generator.py:277 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-702b6dd6ca34 | AsyncFunctionDef | code_generator.py:367 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-3b46d229d0af | AugAssign | code_generator.py:281 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-dff33ce626a7 | ClassDef | code_generator.py:369 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-8c816c79d0c7 | Delete | code_generator.py:324 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-df8d199ebe90 | Expr | code_generator.py:289 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-d712e20d2506 | FunctionDef | code_generator.py:365 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-adbedd33701f | FunctionObject | code_generator.py:4085 | _generate_expression@L3762 (35449/9051) | dict 兼容层（管道死码） |
| RULE-a99b10fa310d | Global | code_generator.py:326 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-3c8a43d55e71 | Import | code_generator.py:388 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-1601748f4b42 | ImportFrom | code_generator.py:388 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-1f2bf6bdcd1e | Module | code_generator.py:262 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-3ed21c936d06 | Nonlocal | code_generator.py:331 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-a310f7ea600b | PREP_RERAISE_STAR | ast_generator_v2.py:23481 | _process_instruction_sequence@L23097 (0/3113) | 遮蔽死分支 |
| RULE-cc118c63f579 | Pass | code_generator.py:318 | _generate_dict_node@L255 (0/0) | dict 兼容层（管道死码） |
| RULE-60fc44ca8092 | conditional_ops | basic_block.py:193 | is_conditional@L174 (0/0) | 零调用点死方法 |

## (c) J 未覆盖形态（可达但 1556 J 无该形态）

| rule_id | symbol | anchor | 外层函数(入口数) | 证据要点 |
|---|---|---|---|---|
| RULE-010c1b2cf1d7 | Break | ast_generator_v2.py:13459 | extract_elif_chain@L13416 (0/243) | elif 链形态门控 |
| RULE-6ce83d58fb8b | Continue | ast_generator_v2.py:13459 | extract_elif_chain@L13416 (0/243) | 同 RULE-010c1b2cf1d7（同一锚点行 13459 的成员规则）。 |
| RULE-681e794c6afb | For | ast_generator_v2.py:13459 | extract_elif_chain@L13416 (0/243) | 同 RULE-010c1b2cf1d7（同一锚点行 13459 的成员规则）。 |
| RULE-ae6695fa4fca | Match | ast_generator_v2.py:13459 | extract_elif_chain@L13416 (0/243) | 同 RULE-010c1b2cf1d7（同一锚点行 13459 的成员规则）。 |
| RULE-d1e1d76ee83d | PRINT_EXPR | ast_generator_v2.py:11556 | _generate_if_ast@L10211 (0/793) | if 结构形态门控 |
| RULE-cbb06f6eb54d | Try | ast_generator_v2.py:13459 | extract_elif_chain@L13416 (0/243) | 同 RULE-010c1b2cf1d7（同一锚点行 13459 的成员规则）。 |
| RULE-6048d12971c9 | While | ast_generator_v2.py:13459 | extract_elif_chain@L13416 (0/243) | 同 RULE-010c1b2cf1d7（同一锚点行 13459 的成员规则）。 |
| RULE-8fc89ce420ac | _APPEND_OPS | ast_generator_v2.py:3330 | _extract_comp_elt@L3300 (0/0) | 回退路径形态门控 |
| RULE-e950c889b956 | _BIND_STORE_OPS | region_analyzer.py:16977 | _parse_bind_unpack@L16956 (0/0) | with 绑定形态门控 |
| RULE-a6c5590d7e93 | _BIND_UNPACK_OPS | region_analyzer.py:16990 | _parse_bind_unpack@L16956 (0/0) | 同 RULE-e950c889b956（同一函数 _parse_bind_unpack；锚点 L16990 elif）。 |
| RULE-9890ff971e58 | _CHECK_OPS_r08b | region_ast_generator.py:41716 | _generate_try@L40468 (187/0) | try 结构形态门控 |
| RULE-996e7c860ca0 | _DELETE_NAME_OPS | region_ast_generator.py:65190 | _build_multi_target_del_targets@L65125 (0/0) | 三元删除目标形态门控 |
| RULE-b2e2ae122393 | _NOISE | region_analyzer.py:8235 | _is_except_break_exit@L8210 (6/0) | except-break 形态门控 |
| RULE-cd390e67679f | _STORE_CHK_R02 | region_ast_generator.py:54405 | _generate_boolop_impl@L53928 (56/0) | boolop 存储形态门控 |
| RULE-31256e3fd90e | _STORE_OPS_R2P02 | region_ast_generator.py:55971 | _build_ternary_boolop_condition@L55864 (0/0) | 三元 boolop 条件形态门控 |
| RULE-532506346aa4 | _b107_store_ops | region_ast_generator.py:76425 | _build_chained_complex_target_assign@L76354 (415/0) | 链式复杂目标赋值形态门控 |
| RULE-f3e459303717 | _b33_noise | region_ast_generator.py:14704 | _b33_await_owner_merged_stmts@L14587 (122/0) | await-owner 形态门控 |
| RULE-d7cb17e16c13 | _bounce_names | comprehension_generator.py:4064 | _b247_mixed_boolchain@L3926 (19/0) | 混合 bool 链形态门控 |
| RULE-eea05924d17d | _cmp_ops_set | region_ast_generator.py:22175 | _try_build_ternary_operand_chained_compare@L22017 (13/0) | 链式比较三元形态门控 |
| RULE-54c66455c6d9 | _cso | comprehension_generator.py:298 | try_generate_comprehension_assign@L177 (2917/0) | 推导式赋值形态门控 |
| RULE-51fbefc39b4b | _ctx_value_ops | region_ast_generator.py:46465 | _b86_complete_with_items@L46372 (124/0) | with 项补全形态门控 |
| RULE-ba395f773988 | _frame_bookkeeping | comprehension_generator.py:856 | _find_returns_pending_value_successor@L766 (1/0) | return 后继形态门控 |
| RULE-eb169da1a935 | _hb_noise_ops | region_ast_generator.py:44134 | _generate_handler_body_statements@L43187 (607/0) | handler 体形态门控 |
| RULE-9eea46812142 | _jump_ops | comprehension_generator.py:1902 | _value_chain_key_split_point@L1879 (5/1) | 值链形态门控 |
| RULE-969c990c53ef | _mt_store_ops | region_ast_generator.py:76740 | _build_multi_target_unpack@L76640 (66/0) | 多目标解包形态门控 |
| RULE-5c5d7b71d2bb | _skip_ops | region_ast_generator.py:78499 | _generate_return_ast@L78386 (0/0) | return 重建形态门控 |
| RULE-048e69dc7408 | _v105_sub_attr | region_ast_generator.py:55973 | _build_ternary_boolop_condition@L55864 (0/0) | 同 RULE-31256e3fd90e（同一函数 _build_ternary_boolop_condition；锚点 L55973 elif，前置 L55971 _STORE_OPS_R2P02 分支未命中）。 |
| RULE-e8aa239b163e | _yf_store_ops | region_ast_generator.py:7870 | _generate_loop@L7579 (444/0) | yield-from 循环形态门控 |
| RULE-a8dffc095ffd | attr | region_ast_generator.py:53333 | _build_boolop_augassign_target@L53307 (5/0) | augassign 目标形态门控 |
| RULE-26ee397f261c | skip_ops | region_ast_generator.py:78444 | _generate_return_ast@L78386 (0/0) | 同 RULE-5c5d7b71d2bb（同一函数 _generate_return_ast；锚点 L78444，位于 return_instr.opname == 'RETURN_VALUE'（L78399）之后的指令扫描内）。 |
| RULE-e255ab564575 | subscr | region_ast_generator.py:53367 | _build_boolop_augassign_target@L53307 (5/0) | 同 RULE-a8dffc095ffd（同一函数；锚点 L53367 kind == 'subscr' 分支，需 `x[i] += <boolop>` 形态）。 |
