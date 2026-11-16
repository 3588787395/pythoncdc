# G3 / G4 缺口工作项清单（round13 · jspace_v3 · fresh · gate_gap）

生成：2026-11-16（只读分析）。本文件只把 G3、G4 的缺口转成**可执行工作项**；
它**没有**写入任何 `witness` / `semantic_domain` / `proof_id` / `composition` / `status`，
也没有把任何规则置 `proved`，没有改动 `core/`、`tools/`、`tests/`。

- 证据根：`fresh/g4_audit/`（342 规则读数）与
  `.trae/specs/attack-completeness-claims/rounds/round9/g3_mutation/`（30 案变异样本）。
- 机器可读产物（与本文件同目录）：`g4_empty_cov.json`（99 条全清单 + 45 簇）、
  `g4_hit_distribution.json`（243 条 witness 分布 + 单 witness 明细）、
  `g4_workitems.json`（W-* 工作项）、`g3_missed_analysis.json`（602 条 missed 明细归集）。
- 复现脚本（工作区外，只读输入）：`D:\temp\opencode\cl_layout\gap\build_g4_gap.py`、
  `build_g3_gap.py`、`build_report.py`。

## 0. 一页读数

| 支柱 | 冻结读数 | 判据来源 | 结论 |
|---|---|---|---|
| G4 规则覆盖 | 342 规则 / 243 hit / **99 empty_cov** / proved **0** / open **342** / unmapped 0 / orphan 0 | `rule_coverage_current.json`（`rule_manifest.py --check`） | FAIL，`reason=mapping_or_proof_gap` |
| G3 变异 | 30 案 × ≤25 mutants：KILLED **32** / MISSED **602** / EQUIVALENT 0 / FALSE_KILL 0 / INCONCLUSIVE 0 / **ERROR 1** | `g3_mutation/g3_sample_summary.json` | 未达 `survived==0`（`gate_report.py::gate_g3`） |

两条 FAIL 的性质不同：**G4 是「没跑到的规则 + 一条证明都没做」**（输入覆盖缺口 + 证明义务缺口）；
**G3 是「判据看不见 95% 的注入语义差」**（观测域缺口），不是变异工具坏掉。

## 1. G4 — 99 条 `empty_cov` 规则

### 1.1 按代码区域聚簇（45 簇，前 5 簇 = 41 条）

表 A：簇表。`分类` 取自 `G4_REACHABILITY_CURRENT.json`（`scope_observed_branch_unhit` /
`scope_never_observed_has_refs` / `scope_never_observed_zero_refs`），是**候选信号**，不是死代码证明。

| # | 簇（模块::作用域） | 规则数 | 分类 | 未命中的 pattern 摘要 | 要写什么探针才能触发（一句） |
|---|---|---|---|---|---|
| 1 | code_generator::CodeGenerator._generate_dict_node | 16 | scope_observed_branch_unhit | node_type == 'AsyncFor' // node_type in ('Import', 'ImportF… | 同域只命中 4 个表达式臂（Call/Lambda/Yield/YieldFrom，很可能来自 _generate_expression 的兜底调用），16 条未命中臂全是语句型 NodeType → 需要一条走「字典格式 AST 语句入口」的 J 探针（Module 的 body 里含 Import/FunctionDef/ClassDef/Global/Nonlocal/Pass/Delete/Assert/AnnAssign/AugAssign/Assign/Expr/AsyncFor/AsyncFunctionDef）。推断：region 管线当前不产出语句型 dict AST，需核实后再定探针形态。 |
| 2 | ast_generator_v2::ASTGeneratorV2._generate_if_ast | 10 | scope_never_observed_has_refs | instr.opname in ('GET_ATTR', 'GET_ITER') // prev_instr.opna… | 整函数在 131 个 J pyc 上 0 次执行（10 条同域规则全空）。补 J 输入前先确认 region 路径是否仍会调用 ASTGeneratorV2；若不会，这是「legacy 路径」，要么造驱动它的 J 输入模型，要么提交 reviewed 排除。 |
| 3 | ast_generator_v2::ASTGeneratorV2._generate_if_ast.extract_elif_chain | 6 | scope_never_observed_has_refs | node_type in ('If', 'While', 'For', 'With', 'Try', 'Match',… | 被 _generate_if_ast 调用（源码内 2 处引用），父函数都不执行 → 同属 legacy 路径问题，不是缺 elif 探针。 |
| 4 | structured_analyzer::StructuredAnalyzer._identify_with_structures | 5 | scope_never_observed_has_refs | instr.opname in ('GET_AWAITABLE', 'SEND', 'YIELD_VALUE', 'R… | 5 条都是 async 相关 opname 判定（GET_AWAITABLE/SEND/YIELD_VALUE…），函数 0 次执行 → 要一条 async with 语料的 J 条目把 StructuredAnalyzer 这条路跑到。 |
| 5 | objective_patch_detector::ObjectivePatchDetector._extract_test_pattern | 4 | scope_never_observed_has_refs | isinstance(test_node, ast.BoolOp) // isinstance(test_node, … | 4 条 isinstance 分支（Compare/BoolOp/Attribute/Call）。函数 0 次执行 → ObjectivePatchDetector 需要被「目标补丁探测」入口调用；现有 J 输入模型里没有这条入口。 |
| 6 | ast_generator_v2::ASTGeneratorV2._generate_entry_sequence | 3 | scope_observed_branch_unhit | opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'BINARY_OP… | 该函数已在 J 上执行（同域已命中 `instr.opname in ('BEFORE_WITH…`、`instr.opname in ('POP_JUMP_IF…`），只是这条分支没走到；补一条让 `opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_O…` 为真的 J 探针。 |
| 7 | ast_generator_v2::ASTGeneratorV2._remove_unreachable_code | 3 | scope_never_observed_has_refs | node_type in ('Return', 'Raise') // node_type in ('With', '… | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `node_type in ('Return', 'Raise')`、`node_type in ('With', 'AsyncWith')`。 |
| 8 | objective_patch_detector::ObjectivePatchDetector._node_signature | 3 | scope_never_observed_has_refs | isinstance(node, ast.Constant) // isinstance(node, ast.Name… | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 10 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `isinstance(node, ast.Constant)`、`isinstance(node, ast.Name)`。 |
| 9 | objective_patch_detector::ObjectivePatchDetector.analyze_file | 3 | scope_never_observed_zero_refs | isinstance(node, ast.ClassDef) // isinstance(node, (ast.Fun… | 无外部引用（死代码候选），探针无从写；需要一条 reviewed 的 universe 排除决定，而不是补探针（`isinstance(node, ast.ClassDef)`、`isinstance(node, (ast.FunctionDef, ast.AsyncF…`）。 |
| 10 | patch_detector::P2Detector._extract_opname_strings | 3 | scope_never_observed_has_refs | isinstance(node, (ast.Tuple, ast.List, ast.Set)) | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 4 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `isinstance(node, (ast.Tuple, ast.List, ast.Se…`。 |
| 11 | region_analyzer::RegionAnalyzer._is_except_break_exit | 3 | scope_never_observed_has_refs | i.opname in ('POP_TOP', 'POP_BLOCK', 'POP_EXCEPT') // i.opn… | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `i.opname in ('POP_TOP', 'POP_BLOCK', 'POP_EXC…`、`i.opname in PURE_JUMP_OPS`。 |
| 12 | ast_generator_v2::ASTGeneratorV2._generate_block_content_skip_iterator | 2 | scope_observed_branch_unhit | opname in ('PRECALL', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD… | 该函数已在 J 上执行（同域已命中 `opname == 'END_ASYNC_FOR'`、`opname == 'JUMP_BACKWARD'`），只是这条分支没走到；补一条让 `opname in ('PRECALL', 'CALL', 'CALL_FUNCTION'…`、`opname in ('YIELD_VALUE', 'YIELD')` 为真的 J 探针。 |
| 13 | region_analyzer::RegionAnalyzer._extract_with_items._parse_bind_unpack | 2 | scope_never_observed_has_refs | _ins.opname in _BIND_UNPACK_OPS // _ins.opname in _BIND_STO… | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 4 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `_ins.opname in _BIND_UNPACK_OPS`、`_ins.opname in _BIND_STORE_OPS`。 |
| 14 | region_ast_generator::RegionASTGenerator._build_boolop_augassign_target | 2 | scope_never_observed_has_refs | kind == 'attr' // kind == 'subscr' | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `kind == 'attr'`、`kind == 'subscr'`。 |
| 15 | region_ast_generator::RegionASTGenerator._generate_return_ast | 2 | scope_never_observed_has_refs | instr.opname in skip_ops // bi.opname in _skip_ops | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 36 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `instr.opname in skip_ops`、`bi.opname in _skip_ops`。 |
| 16 | region_ast_generator::RegionASTGenerator._loop_handle_header | 2 | scope_never_observed_has_refs | pre_cond_instrs[_si].opname in ('COMPARE_OP', 'IS_OP', 'IS_… | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `pre_cond_instrs[_si].opname in ('COMPARE_OP',…`。 |
| 17 | structured_analyzer::StructuredAnalyzer._identify_try_except_pre_311 | 2 | scope_never_observed_has_refs | instr.opname in {'SETUP_EXCEPT', 'SETUP_FINALLY'} | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `instr.opname in {'SETUP_EXCEPT', 'SETUP_FINAL…`。 |
| 18 | ast_generator_v2::ASTGeneratorV2._extract_function_args | 1 | scope_never_observed_has_refs | name == 'return' | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 18 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `name == 'return'`。 |
| 19 | ast_generator_v2::ASTGeneratorV2._extract_iterator_v2 | 1 | scope_never_observed_has_refs | instr.opname in ('FOR_ITER', 'FOR_ITER_RANGE') | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `instr.opname in ('FOR_ITER', 'FOR_ITER_RANGE')`。 |
| 20 | ast_generator_v2::ASTGeneratorV2._extract_with_context | 1 | scope_never_observed_zero_refs | instr.opname in ('BEFORE_WITH', 'SETUP_WITH') | 无外部引用（死代码候选），探针无从写；需要一条 reviewed 的 universe 排除决定，而不是补探针（`instr.opname in ('BEFORE_WITH', 'SETUP_WITH')`）。 |
| 21 | ast_generator_v2::ASTGeneratorV2._generate_comprehension_function | 1 | scope_observed_branch_unhit | instr.opname in ('LIST_APPEND', 'SET_ADD', 'MAP_ADD', 'DICT… | 该函数已在 J 上执行（同域已命中 `instr.opname == 'GET_AITER'`、`instr.opname in ('POP_JUMP_BA…`），只是这条分支没走到；补一条让 `instr.opname in ('LIST_APPEND', 'SET_ADD', 'M…` 为真的 J 探针。 |
| 22 | ast_generator_v2::ASTGeneratorV2._generate_inner_while_from_block | 1 | scope_never_observed_has_refs | instr.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'NOT… | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 6 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `instr.opname in ('COMPARE_OP', 'IS_OP', 'CONT…`。 |
| 23 | ast_generator_v2::ASTGeneratorV2._has_terminal_statement | 1 | scope_never_observed_has_refs | node_type in ('If',) | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 8 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `node_type in ('If',)`。 |
| 24 | ast_generator_v2::ASTGeneratorV2._process_instruction_sequence | 1 | scope_observed_branch_unhit | opname == 'PREP_RERAISE_STAR' | 该函数已在 J 上执行（同域已命中 `opname == 'IMPORT_FROM'`、`opname == 'IMPORT_NAME'`），只是这条分支没走到；补一条让 `opname == 'PREP_RERAISE_STAR'` 为真的 J 探针。 |
| 25 | ast_generator_v2::ExpressionReconstructor._extract_comp_elt | 1 | scope_never_observed_has_refs | instrs[i].opname in _APPEND_OPS | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `instrs[i].opname in _APPEND_OPS`。 |
| 26 | basic_block::BasicBlock.is_conditional | 1 | scope_never_observed_has_refs | last.opname in conditional_ops | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 20 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `last.opname in conditional_ops`。 |
| 27 | code_generator::CodeGenerator._generate_expression | 1 | scope_observed_branch_unhit | node_type == 'FunctionObject' | 该函数已在 J 上执行（同域已命中 `node_type == 'Attribute'`、`node_type == 'Await'`），只是这条分支没走到；补一条让 `node_type == 'FunctionObject'` 为真的 J 探针。 |
| 28 | comprehension_generator::ComprehensionGenerator._b247_mixed_boolchain | 1 | scope_observed_branch_unhit | _j.opname in _bounce_names | 该函数已在 J 上执行（同域已命中 `_ins.opname in _kop_names`），只是这条分支没走到；补一条让 `_j.opname in _bounce_names` 为真的 J 探针。 |
| 29 | comprehension_generator::ComprehensionGenerator._find_returns_pending_value_successor | 1 | scope_observed_branch_unhit | i.opname in _frame_bookkeeping | 该函数已在 J 上执行（同域已命中 `s_instrs[0].opname in _frame_…`、`_i.opname in _noise`），只是这条分支没走到；补一条让 `i.opname in _frame_bookkeeping` 为真的 J 探针。 |
| 30 | comprehension_generator::ComprehensionGenerator._value_chain_key_split_point | 1 | scope_never_observed_has_refs | _ins.opname in _jump_ops | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `_ins.opname in _jump_ops`。 |
| 31 | comprehension_generator::ComprehensionGenerator.try_generate_comprehension_assign | 1 | scope_observed_branch_unhit | _iii.opname in _cso | 该函数已在 J 上执行（同域已命中 `_pw.opname in _closure_setup`、`_pi.opname in _closure_setup_…`），只是这条分支没走到；补一条让 `_iii.opname in _cso` 为真的 J 探针。 |
| 32 | exception_handler::_find_handler_type_load | 1 | scope_never_observed_has_refs | last.opname in _UNCOND_JUMP_TARGET_OPS | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 4 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `last.opname in _UNCOND_JUMP_TARGET_OPS`。 |
| 33 | objective_patch_detector::ObjectivePatchDetector._check_d2_special_branches | 1 | scope_never_observed_has_refs | isinstance(child, ast.If) | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `isinstance(child, ast.If)`。 |
| 34 | patch_detector::P1Detector._is_local_region_var | 1 | scope_never_observed_has_refs | isinstance(node, ast.Assign) | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `isinstance(node, ast.Assign)`。 |
| 35 | region_ast_generator::RegionASTGenerator._b33_await_owner_merged_stmts | 1 | scope_never_observed_has_refs | i.opname in _b33_noise | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `i.opname in _b33_noise`。 |
| 36 | region_ast_generator::RegionASTGenerator._b86_complete_with_items | 1 | scope_never_observed_has_refs | _pj.opname in _ctx_value_ops | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `_pj.opname in _ctx_value_ops`。 |
| 37 | region_ast_generator::RegionASTGenerator._build_chained_complex_target_assign | 1 | scope_never_observed_has_refs | _b107_ins.opname in _b107_store_ops | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 8 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `_b107_ins.opname in _b107_store_ops`。 |
| 38 | region_ast_generator::RegionASTGenerator._build_multi_target_del_targets | 1 | scope_never_observed_has_refs | _instr.opname in _DELETE_NAME_OPS | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `_instr.opname in _DELETE_NAME_OPS`。 |
| 39 | region_ast_generator::RegionASTGenerator._build_multi_target_unpack | 1 | scope_never_observed_has_refs | _mt_instr.opname in _mt_store_ops | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 4 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `_mt_instr.opname in _mt_store_ops`。 |
| 40 | region_ast_generator::RegionASTGenerator._build_ternary_boolop_condition | 1 | scope_never_observed_has_refs | _ins.opname in _STORE_OPS_R2P02 | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 2 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `_ins.opname in _STORE_OPS_R2P02`。 |
| 41 | region_ast_generator::RegionASTGenerator._generate_boolop_impl | 1 | scope_observed_branch_unhit | _pinstr_r02.opname in _STORE_CHK_R02 | 该函数已在 J 上执行（同域已命中 `_pinstr.opname in _STORE_CHK`、`_b56_i.opname in _STORE_CHK_B…`），只是这条分支没走到；补一条让 `_pinstr_r02.opname in _STORE_CHK_R02` 为真的 J 探针。 |
| 42 | region_ast_generator::RegionASTGenerator._generate_handler_body_statements | 1 | scope_never_observed_has_refs | _hb_fi.opname in _hb_noise_ops | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 22 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `_hb_fi.opname in _hb_noise_ops`。 |
| 43 | region_ast_generator::RegionASTGenerator._generate_loop | 1 | scope_never_observed_has_refs | _si_instr.opname in _yf_store_ops | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 4 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `_si_instr.opname in _yf_store_ops`。 |
| 44 | region_ast_generator::RegionASTGenerator._generate_try | 1 | scope_observed_branch_unhit | _instr.opname in _CHECK_OPS_r08b | 该函数已在 J 上执行（同域已命中 `_instr.opname in ('POP_JUMP_F…`），只是这条分支没走到；补一条让 `_instr.opname in _CHECK_OPS_r08b` 为真的 J 探针。 |
| 45 | region_ast_generator::RegionASTGenerator._try_build_ternary_operand_chained_compare | 1 | scope_never_observed_has_refs | _i.opname in _cmp_ops_set | 该函数在 J 的 131 个 pyc 上 0 次执行（源码内 4 处引用，属未走到的现存路径）；先让入口到达它，再让它进到 `_i.opname in _cmp_ops_set`。 |

前 5 簇：`CodeGenerator._generate_dict_node` **16**、`ASTGeneratorV2._generate_if_ast` **10**、
`ASTGeneratorV2._generate_if_ast.extract_elif_chain` **6**、
`StructuredAnalyzer._identify_with_structures` **5**、
`ObjectivePatchDetector._extract_test_pattern` **4** → 合计 41/99；其余 40 簇是 1–3 条的碎簇。

### 1.2 按模块 / 按缺陷类型

| 模块 | empty_cov | branch_unhit | never_observed_has_refs | zero_refs | 簇数 |
|---|---|---|---|---|---|
| core/cfg/code_generator.py | 17 | 17 | 0 | 0 | 2 |
| core/cfg/ast_generator_v2.py | 32 | 7 | 24 | 1 | 13 |
| core/cfg/region_ast_generator.py | 17 | 2 | 15 | 0 | 14 |
| core/cfg/objective_patch_detector.py | 11 | 0 | 8 | 3 | 4 |
| core/cfg/structured_analyzer.py | 7 | 0 | 7 | 0 | 2 |
| core/cfg/region_analyzer.py | 5 | 0 | 5 | 0 | 2 |
| core/cfg/patch_detector.py | 4 | 0 | 4 | 0 | 2 |
| core/cfg/comprehension_generator.py | 4 | 3 | 1 | 0 | 4 |
| core/cfg/exception_handler.py | 1 | 0 | 1 | 0 | 1 |
| core/cfg/basic_block.py | 1 | 0 | 1 | 0 | 1 |

按缺陷类型（决定工作项种类，而不是"再写几个探针"）：

| 类型 | 规则数 | 含义 | 工作项 |
|---|---:|---|---|
| A 分支未走到（函数已跑） | 29 | 同域其它分支命中过，仅这条分派臂/条件分支没进 | 写探针（G4-W01/W03/W06） |
| B 函数 0 次执行但有源码引用 | 66 | region 管线或 J 输入根本没到达该函数（多为 legacy `ast_generator_v2` 与 `objective_patch_detector` 入口） | 补输入模型 / 或 reviewed 排除（G4-W02/W04/W05） |
| C 零引用（死代码候选） | 4 | 无外部引用，402 语料也没跑到 | 只做 reviewed 排除决定（G4-W07） |

### 1.3 为什么 99 条不能靠"再跑一遍"消失

`rule_manifest.py::check` 第 182 行：`empty_cov = sum(1 for rid, cov in coverage.items() if not cov)`，
第 190 行把它并进 FAIL 条件。也就是说 **`empty_cov` 只由"某条 J 条目执行到该 rule_id"决定**，
与 `status`、witness、proof 无关。要让 99 变 0，只有三条路：补 J 输入（探针）、
把该代码从独立规则宇宙里评审排除、或改扫描器口径（本轮不做，且改口径等于改分母）。

> 交叉证据：`G4_CURRENT.md` 记录，402 真实语料再跑一遍只补回 9/99，**90 条两个域都没跑到**；
> 所以"多跑语料"不是有效动作，必须新增能到达这些函数的输入模型。

### 1.4 99 条逐条清单

关于字段：`pattern` 来自扫描器（`isinstance_ast` 的 AST 谓词 / `opcode_eq` 的 opname 谓词），可用；
**`effect` 不可用**——`rule_manifest.generate()` 对全部 342 条硬编码 `"effect": "unclassified"`、
`preconditions/guards/invariants` 全空，所以本清单只能给 `anchor / kind / pattern / 分类`。
`effect` 本身就是一条待补的证明义务（G4-W12 的人工部分），不能用生成器占位值充数。

| # | rule_id | anchor | kind | pattern | 分类 |
|---|---|---|---|---|---|
| 1 | `RULE-1f2bf6bdcd1e` | `core/cfg/code_generator.py:257` | opcode_eq | node_type == 'Module' | observed_branch_unhit |
| 2 | `RULE-0b22204ea11f` | `core/cfg/code_generator.py:272` | opcode_eq | node_type == 'AsyncFor' | observed_branch_unhit |
| 3 | `RULE-3b46d229d0af` | `core/cfg/code_generator.py:276` | opcode_eq | node_type == 'AugAssign' | observed_branch_unhit |
| 4 | `RULE-eed79a22277c` | `core/cfg/code_generator.py:278` | opcode_eq | node_type == 'Assign' | observed_branch_unhit |
| 5 | `RULE-eb29ec1ad01a` | `core/cfg/code_generator.py:280` | opcode_eq | node_type == 'AnnAssign' | observed_branch_unhit |
| 6 | `RULE-df8d199ebe90` | `core/cfg/code_generator.py:284` | opcode_eq | node_type == 'Expr' | observed_branch_unhit |
| 7 | `RULE-cc118c63f579` | `core/cfg/code_generator.py:313` | opcode_eq | node_type == 'Pass' | observed_branch_unhit |
| 8 | `RULE-8c816c79d0c7` | `core/cfg/code_generator.py:319` | opcode_eq | node_type == 'Delete' | observed_branch_unhit |
| 9 | `RULE-a99b10fa310d` | `core/cfg/code_generator.py:321` | opcode_eq | node_type == 'Global' | observed_branch_unhit |
| 10 | `RULE-3ed21c936d06` | `core/cfg/code_generator.py:326` | opcode_eq | node_type == 'Nonlocal' | observed_branch_unhit |
| 11 | `RULE-d712e20d2506` | `core/cfg/code_generator.py:360` | opcode_eq | node_type == 'FunctionDef' | observed_branch_unhit |
| 12 | `RULE-702b6dd6ca34` | `core/cfg/code_generator.py:362` | opcode_eq | node_type == 'AsyncFunctionDef' | observed_branch_unhit |
| 13 | `RULE-dff33ce626a7` | `core/cfg/code_generator.py:364` | opcode_eq | node_type == 'ClassDef' | observed_branch_unhit |
| 14 | `RULE-1b5b4d7115d9` | `core/cfg/code_generator.py:373` | opcode_eq | node_type == 'Assert' | observed_branch_unhit |
| 15 | `RULE-1601748f4b42` | `core/cfg/code_generator.py:383` | opcode_eq | node_type in ('Import', 'ImportFrom') | observed_branch_unhit |
| 16 | `RULE-3c8a43d55e71` | `core/cfg/code_generator.py:383` | opcode_eq | node_type in ('Import', 'ImportFrom') | observed_branch_unhit |
| 17 | `RULE-5361acaaa053` | `core/cfg/ast_generator_v2.py:10462` | opcode_eq | prev_instr.opname in ('BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY… | never_observed_has_refs |
| 18 | `RULE-c7b3c96bb6c8` | `core/cfg/ast_generator_v2.py:10462` | opcode_eq | prev_instr.opname in ('BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY… | never_observed_has_refs |
| 19 | `RULE-dda45a0ced72` | `core/cfg/ast_generator_v2.py:10462` | opcode_eq | prev_instr.opname in ('BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY… | never_observed_has_refs |
| 20 | `RULE-f1bef410c01e` | `core/cfg/ast_generator_v2.py:10462` | opcode_eq | prev_instr.opname in ('BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY… | never_observed_has_refs |
| 21 | `RULE-05f8183d28bc` | `core/cfg/ast_generator_v2.py:10638` | opcode_eq | instr.opname in ('GET_ATTR', 'GET_ITER') | never_observed_has_refs |
| 22 | `RULE-b611d12faec6` | `core/cfg/ast_generator_v2.py:11541` | opcode_eq | succ_instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_KW', 'P… | never_observed_has_refs |
| 23 | `RULE-beabfd586993` | `core/cfg/ast_generator_v2.py:11541` | opcode_eq | succ_instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_KW', 'P… | never_observed_has_refs |
| 24 | `RULE-d1e1d76ee83d` | `core/cfg/ast_generator_v2.py:11541` | opcode_eq | succ_instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_KW', 'P… | never_observed_has_refs |
| 25 | `RULE-bcde89ee3e2a` | `core/cfg/ast_generator_v2.py:13166` | opcode_eq | instr.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF', 'LO… | never_observed_has_refs |
| 26 | `RULE-c56bc072e6e4` | `core/cfg/ast_generator_v2.py:13166` | opcode_eq | instr.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF', 'LO… | never_observed_has_refs |
| 27 | `RULE-010c1b2cf1d7` | `core/cfg/ast_generator_v2.py:13444` | opcode_eq | node_type in ('If', 'While', 'For', 'With', 'Try', 'Match', 'Raise', 'Retur… | never_observed_has_refs |
| 28 | `RULE-6048d12971c9` | `core/cfg/ast_generator_v2.py:13444` | opcode_eq | node_type in ('If', 'While', 'For', 'With', 'Try', 'Match', 'Raise', 'Retur… | never_observed_has_refs |
| 29 | `RULE-681e794c6afb` | `core/cfg/ast_generator_v2.py:13444` | opcode_eq | node_type in ('If', 'While', 'For', 'With', 'Try', 'Match', 'Raise', 'Retur… | never_observed_has_refs |
| 30 | `RULE-6ce83d58fb8b` | `core/cfg/ast_generator_v2.py:13444` | opcode_eq | node_type in ('If', 'While', 'For', 'With', 'Try', 'Match', 'Raise', 'Retur… | never_observed_has_refs |
| 31 | `RULE-ae6695fa4fca` | `core/cfg/ast_generator_v2.py:13444` | opcode_eq | node_type in ('If', 'While', 'For', 'With', 'Try', 'Match', 'Raise', 'Retur… | never_observed_has_refs |
| 32 | `RULE-cbb06f6eb54d` | `core/cfg/ast_generator_v2.py:13444` | opcode_eq | node_type in ('If', 'While', 'For', 'With', 'Try', 'Match', 'Raise', 'Retur… | never_observed_has_refs |
| 33 | `RULE-7f1501983cc4` | `core/cfg/structured_analyzer.py:13926` | opcode_eq | instr.opname in ('GET_AWAITABLE', 'SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BA… | never_observed_has_refs |
| 34 | `RULE-a2f801d5aefb` | `core/cfg/structured_analyzer.py:13926` | opcode_eq | instr.opname in ('GET_AWAITABLE', 'SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BA… | never_observed_has_refs |
| 35 | `RULE-c500ada1eadd` | `core/cfg/structured_analyzer.py:13926` | opcode_eq | instr.opname in ('GET_AWAITABLE', 'SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BA… | never_observed_has_refs |
| 36 | `RULE-c708889ddc61` | `core/cfg/structured_analyzer.py:13926` | opcode_eq | instr.opname in ('GET_AWAITABLE', 'SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BA… | never_observed_has_refs |
| 37 | `RULE-fac0e268c522` | `core/cfg/structured_analyzer.py:13926` | opcode_eq | instr.opname in ('GET_AWAITABLE', 'SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BA… | never_observed_has_refs |
| 38 | `RULE-2b862ecf9a11` | `core/cfg/objective_patch_detector.py:191` | isinstance_ast | isinstance(test_node, ast.Compare) | never_observed_has_refs |
| 39 | `RULE-20568d2871b4` | `core/cfg/objective_patch_detector.py:195` | isinstance_ast | isinstance(test_node, ast.BoolOp) | never_observed_has_refs |
| 40 | `RULE-526c2f9c8010` | `core/cfg/objective_patch_detector.py:197` | isinstance_ast | isinstance(test_node, ast.Attribute) | never_observed_has_refs |
| 41 | `RULE-93efbfe2473b` | `core/cfg/objective_patch_detector.py:199` | isinstance_ast | isinstance(test_node, ast.Call) | never_observed_has_refs |
| 42 | `RULE-0062e270c4a1` | `core/cfg/ast_generator_v2.py:6553` | opcode_eq | opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'BINARY_OP', 'BINARY_ADD',… | observed_branch_unhit |
| 43 | `RULE-2675d342ef0c` | `core/cfg/ast_generator_v2.py:6553` | opcode_eq | opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'BINARY_OP', 'BINARY_ADD',… | observed_branch_unhit |
| 44 | `RULE-cd714078ea23` | `core/cfg/ast_generator_v2.py:6553` | opcode_eq | opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'BINARY_OP', 'BINARY_ADD',… | observed_branch_unhit |
| 45 | `RULE-0bc203be8823` | `core/cfg/ast_generator_v2.py:3939` | opcode_eq | node_type in ('Return', 'Raise') | never_observed_has_refs |
| 46 | `RULE-42045b244e8a` | `core/cfg/ast_generator_v2.py:3950` | opcode_eq | node_type in ('With', 'AsyncWith') | never_observed_has_refs |
| 47 | `RULE-7ccfdf2f5d77` | `core/cfg/ast_generator_v2.py:3950` | opcode_eq | node_type in ('With', 'AsyncWith') | never_observed_has_refs |
| 48 | `RULE-b56901a142a6` | `core/cfg/objective_patch_detector.py:207` | isinstance_ast | isinstance(node, ast.Name) | never_observed_has_refs |
| 49 | `RULE-fd29f404c20d` | `core/cfg/objective_patch_detector.py:211` | isinstance_ast | isinstance(node, ast.Subscript) | never_observed_has_refs |
| 50 | `RULE-1f3252f64295` | `core/cfg/objective_patch_detector.py:213` | isinstance_ast | isinstance(node, ast.Constant) | never_observed_has_refs |
| 51 | `RULE-2d4b43ea95f6` | `core/cfg/objective_patch_detector.py:89` | isinstance_ast | isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) | never_observed_zero_refs |
| 52 | `RULE-b3b3c27de3f4` | `core/cfg/objective_patch_detector.py:89` | isinstance_ast | isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) | never_observed_zero_refs |
| 53 | `RULE-2845ddf0b9b8` | `core/cfg/objective_patch_detector.py:93` | isinstance_ast | isinstance(node, ast.ClassDef) | never_observed_zero_refs |
| 54 | `RULE-4c10258ace4e` | `core/cfg/patch_detector.py:425` | isinstance_ast | isinstance(node, (ast.Tuple, ast.List, ast.Set)) | never_observed_has_refs |
| 55 | `RULE-87d3e450c5e4` | `core/cfg/patch_detector.py:425` | isinstance_ast | isinstance(node, (ast.Tuple, ast.List, ast.Set)) | never_observed_has_refs |
| 56 | `RULE-bd1b6b8bb350` | `core/cfg/patch_detector.py:425` | isinstance_ast | isinstance(node, (ast.Tuple, ast.List, ast.Set)) | never_observed_has_refs |
| 57 | `RULE-b2e2ae122393` | `core/cfg/region_analyzer.py:8138` | opcode_eq | i.opname in _NOISE | never_observed_has_refs |
| 58 | `RULE-18912491428c` | `core/cfg/region_analyzer.py:8140` | opcode_eq | i.opname in ('POP_TOP', 'POP_BLOCK', 'POP_EXCEPT') | never_observed_has_refs |
| 59 | `RULE-a197991fd9e1` | `core/cfg/region_analyzer.py:8149` | opcode_eq | i.opname in PURE_JUMP_OPS | never_observed_has_refs |
| 60 | `RULE-1c8e48e5d568` | `core/cfg/ast_generator_v2.py:7372` | opcode_eq | opname in ('PRECALL', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_KW') | observed_branch_unhit |
| 61 | `RULE-9ba093d040b1` | `core/cfg/ast_generator_v2.py:8512` | opcode_eq | opname in ('YIELD_VALUE', 'YIELD') | observed_branch_unhit |
| 62 | `RULE-e950c889b956` | `core/cfg/region_analyzer.py:16774` | opcode_eq | _ins.opname in _BIND_STORE_OPS | never_observed_has_refs |
| 63 | `RULE-a6c5590d7e93` | `core/cfg/region_analyzer.py:16787` | opcode_eq | _ins.opname in _BIND_UNPACK_OPS | never_observed_has_refs |
| 64 | `RULE-a8dffc095ffd` | `core/cfg/region_ast_generator.py:49476` | opcode_eq | kind == 'attr' | never_observed_has_refs |
| 65 | `RULE-e255ab564575` | `core/cfg/region_ast_generator.py:49510` | opcode_eq | kind == 'subscr' | never_observed_has_refs |
| 66 | `RULE-26ee397f261c` | `core/cfg/region_ast_generator.py:73194` | opcode_eq | instr.opname in skip_ops | never_observed_has_refs |
| 67 | `RULE-5c5d7b71d2bb` | `core/cfg/region_ast_generator.py:73249` | opcode_eq | bi.opname in _skip_ops | never_observed_has_refs |
| 68 | `RULE-05ce2ee31a3b` | `core/cfg/region_ast_generator.py:12584` | opcode_eq | pre_cond_instrs[_si].opname in ('COMPARE_OP', 'IS_OP', 'IS_NOT', 'CONTAINS_… | never_observed_has_refs |
| 69 | `RULE-1cd90d76c906` | `core/cfg/region_ast_generator.py:12584` | opcode_eq | pre_cond_instrs[_si].opname in ('COMPARE_OP', 'IS_OP', 'IS_NOT', 'CONTAINS_… | never_observed_has_refs |
| 70 | `RULE-36dde631fda0` | `core/cfg/structured_analyzer.py:13288` | opcode_eq | instr.opname in {'SETUP_EXCEPT', 'SETUP_FINALLY'} | never_observed_has_refs |
| 71 | `RULE-36f063d106a0` | `core/cfg/structured_analyzer.py:13288` | opcode_eq | instr.opname in {'SETUP_EXCEPT', 'SETUP_FINALLY'} | never_observed_has_refs |
| 72 | `RULE-b0bb824910b4` | `core/cfg/ast_generator_v2.py:4891` | opcode_eq | name == 'return' | never_observed_has_refs |
| 73 | `RULE-cdc6b865739a` | `core/cfg/ast_generator_v2.py:26969` | opcode_eq | instr.opname in ('FOR_ITER', 'FOR_ITER_RANGE') | never_observed_has_refs |
| 74 | `RULE-85708f1fc4e5` | `core/cfg/ast_generator_v2.py:21964` | opcode_eq | instr.opname in ('BEFORE_WITH', 'SETUP_WITH') | never_observed_zero_refs |
| 75 | `RULE-a758f665e9f5` | `core/cfg/ast_generator_v2.py:5951` | opcode_eq | instr.opname in ('LIST_APPEND', 'SET_ADD', 'MAP_ADD', 'DICT_ADD', 'YIELD_VA… | observed_branch_unhit |
| 76 | `RULE-5aba44e010fc` | `core/cfg/ast_generator_v2.py:17904` | opcode_eq | instr.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'NOT') | never_observed_has_refs |
| 77 | `RULE-1fbb15a6c511` | `core/cfg/ast_generator_v2.py:3977` | opcode_eq | node_type in ('If',) | never_observed_has_refs |
| 78 | `RULE-a310f7ea600b` | `core/cfg/ast_generator_v2.py:23466` | opcode_eq | opname == 'PREP_RERAISE_STAR' | observed_branch_unhit |
| 79 | `RULE-8fc89ce420ac` | `core/cfg/ast_generator_v2.py:3315` | opcode_eq | instrs[i].opname in _APPEND_OPS | never_observed_has_refs |
| 80 | `RULE-60fc44ca8092` | `core/cfg/basic_block.py:193` | opcode_eq | last.opname in conditional_ops | never_observed_has_refs |
| 81 | `RULE-adbedd33701f` | `core/cfg/code_generator.py:3892` | opcode_eq | node_type == 'FunctionObject' | observed_branch_unhit |
| 82 | `RULE-d7cb17e16c13` | `core/cfg/comprehension_generator.py:4064` | opcode_eq | _j.opname in _bounce_names | observed_branch_unhit |
| 83 | `RULE-ba395f773988` | `core/cfg/comprehension_generator.py:856` | opcode_eq | i.opname in _frame_bookkeeping | observed_branch_unhit |
| 84 | `RULE-9eea46812142` | `core/cfg/comprehension_generator.py:1902` | opcode_eq | _ins.opname in _jump_ops | never_observed_has_refs |
| 85 | `RULE-54c66455c6d9` | `core/cfg/comprehension_generator.py:298` | opcode_eq | _iii.opname in _cso | observed_branch_unhit |
| 86 | `RULE-137de19b1304` | `core/cfg/exception_handler.py:88` | opcode_eq | last.opname in _UNCOND_JUMP_TARGET_OPS | never_observed_has_refs |
| 87 | `RULE-3d070d0913cc` | `core/cfg/objective_patch_detector.py:181` | isinstance_ast | isinstance(child, ast.If) | never_observed_has_refs |
| 88 | `RULE-d53ac6879d6a` | `core/cfg/patch_detector.py:328` | isinstance_ast | isinstance(node, ast.Assign) | never_observed_has_refs |
| 89 | `RULE-f3e459303717` | `core/cfg/region_ast_generator.py:13593` | opcode_eq | i.opname in _b33_noise | never_observed_has_refs |
| 90 | `RULE-51fbefc39b4b` | `core/cfg/region_ast_generator.py:43013` | opcode_eq | _pj.opname in _ctx_value_ops | never_observed_has_refs |
| 91 | `RULE-532506346aa4` | `core/cfg/region_ast_generator.py:71339` | opcode_eq | _b107_ins.opname in _b107_store_ops | never_observed_has_refs |
| 92 | `RULE-996e7c860ca0` | `core/cfg/region_ast_generator.py:60591` | opcode_eq | _instr.opname in _DELETE_NAME_OPS | never_observed_has_refs |
| 93 | `RULE-969c990c53ef` | `core/cfg/region_ast_generator.py:71552` | opcode_eq | _mt_instr.opname in _mt_store_ops | never_observed_has_refs |
| 94 | `RULE-31256e3fd90e` | `core/cfg/region_ast_generator.py:51407` | opcode_eq | _ins.opname in _STORE_OPS_R2P02 | never_observed_has_refs |
| 95 | `RULE-cd390e67679f` | `core/cfg/region_ast_generator.py:50092` | opcode_eq | _pinstr_r02.opname in _STORE_CHK_R02 | observed_branch_unhit |
| 96 | `RULE-eb169da1a935` | `core/cfg/region_ast_generator.py:40750` | opcode_eq | _hb_fi.opname in _hb_noise_ops | never_observed_has_refs |
| 97 | `RULE-e8aa239b163e` | `core/cfg/region_ast_generator.py:7294` | opcode_eq | _si_instr.opname in _yf_store_ops | never_observed_has_refs |
| 98 | `RULE-9890ff971e58` | `core/cfg/region_ast_generator.py:38465` | opcode_eq | _instr.opname in _CHECK_OPS_r08b | observed_branch_unhit |
| 99 | `RULE-eea05924d17d` | `core/cfg/region_ast_generator.py:20552` | opcode_eq | _i.opname in _cmp_ops_set | never_observed_has_refs |

## 2. G4 — 243 条已 hit 规则的 witness 分布

### 2.1 hit 的 J 条目数分布

| 命中 J 条目数 | 规则数 | 解读 |
|---|---|---|
| 0（empty_cov） | 99 | 从未被任何 J 条目执行过 → G4 FAIL 直接来源 |
| 1 | 2 | 唯一 witness，删掉那一条 J 条目规则就失证 |
| 2–5 | 0 | — |
| 6–20 | 13 | 中等冗余 |
| >20 | 228 | 近乎每条 J 都命中（通用分派/循环体），witness 冗余极高 |

`single_witness_rules = 2`（只有 1 条 J 命中）。全部 243 条规则里，
**228 条（93.8%）命中 >20 条 J 条目**，最大 1556（即每条 J 条目都执行它）；
分布是双峰的：要么几乎全覆盖，要么只有个位数——没有任何规则落在 2–5 条。

### 2.2 最脆弱的单 witness 规则（2 条，且都挂在同一条 J 上）

| rule_id | anchor | pattern | 唯一 J 条目 |
|---|---|---|---|
| `RULE-572fd2eb12b9` | `core/cfg/region_ast_generator.py:50850` | i.opname in _STORE_TYPES_R61_chk | `JS-BOOLOP-055` |
| `RULE-ab1d4cc5ec5e` | `core/cfg/region_ast_generator.py:50569` | _ci.opname in _STORE_TYPES_R61 | `JS-BOOLOP-055` |

两条都在 `region_ast_generator.py` 的 `_STORE_TYPES_R61*` 判定上，唯一见证都是 `JS-BOOLOP-055`。
删掉/改写这条 J 条目，这两条规则立刻回到 `empty_cov`——`G4-W13` 要求先补第二条独立 witnesses 再做证明。

### 2.3 四条证明义务：哪些能自动派生，哪些必须人工

判据就是 `tools/completeness/rule_manifest.py` 的四处布尔量（`check()` 第 160–165 行）：

| # | 判据 | 代码 | 当前实际值 | 可否自动派生 | 必须人工的部分 |
|---|---|---|---|---|---|
| 1 | `_witness_ok` | L106–116：`positive` 与 `negative` 都必须非空；若给了 jspace，**每个 witness id 必须 ∈ J 条目 id 集合** | `witnesses={"positive":[],"negative":[]}` × 342 → 全部 `witness_missing` | **positive 可自动**：直接取 `coverage[rule_id]` 的 J 条目（243 条规则各有 1–1556 条）。negative 只能自动生成**候选集**（同 form/host 下未命中该规则的条目、`counterexample_hint`），选中与语义论证须人工 | negative 的语义定义（什么叫"该规则的反例见证"）与逐条签署；99 条 empty_cov 连 positive 都没有 |
| 2 | `_domain_ok` | L119–125：`status=="proved"` 时 `semantic_domain.hosts` 与 `.depths` 都必须非空 | `{"hosts":[],"depths":[],"note":"not declared in v1"}` × 342 | **可自动派生出"已观测域"**：witness J 条目的 `expected_label.host`（48 种）与 `.depth`（3 档）就是现成值 | **声明的域**（规则在哪个 host/depth 上声称正确）是设计决定，不能由见证反推；99 条 empty 无任何 witness，只能从 spec 声明 |
| 3 | `proof_ok` | L162–163：`bool(proof.get("proof_id"))` | `proof_id=null` × 342，`counterexample_bound=null`，`review=null` | **不可自动**：`proof_id` 必须指向真实检查器产物（`isinstance_ast` 15 条 / `opcode_eq` 327 条至少要 2 族检查器 + 342 条逐规则实例化），工具只验非空、**验不了真值** | 全部人工：写检查器、跑有界反例搜索、填 `counterexample_bound`、登记 reviewer |
| 4 | `composition_ok` | L164：`bool(item.get("composition"))` | `composition=[]` × 342 | **不可自动**：没有 composition 理论可套 | 全部人工；**且这是设计级阻塞**（见 2.4） |

汇总：342 条里，**可自动落地的只有 1 的 positive 面（243 条）与 2 的"已观测域"候选**；
`negative witness`、`proof_id`、`composition` 三项没有任何一条能诚实地自动生成。
另外 `gate_report.py::gate_g4`（L122–133）直接读 coverage 的 `g4` 字段，
而 `check()` 的 PASS 条件（L190–198）同时要求 `empty_cov==0` **且** `ready==total==342`。

### 2.4 两个设计级阻塞（不解决就永远 PASS 不了，且任何"补全"都会变成造假）

1. **`composition` 非空是硬条件**，但仓库里没有 composition 语义（manifest 生成器直接写 `[]`）。
   对"原子规则"（例如某条 `opcode_eq` 分派臂），诚实的做法要么定义"单元素 composition = 自证"，
   要么把该判据改成"composition 允许为空、原子性由 proof 承担"——**这是判据变更，需要评审**，
   不能在数据里填一个假组合。
2. **negative witness 无定义**。工具只查"非空 + ∈ J"。在定义清楚前，
   任何 243 条批量填值都只是让 `_witness_ok` 变 True，不是证明。

### 2.5 因此 G4 的达成路径（量级）

- 输入侧：**99 条 empty_cov** → 29 条靠探针（可写），66+4 条要么补输入模型（legacy v2 /
  objective patch 入口），要么评审排除。探针量级：**10–20 个新 J 探针文件**（不是 99 个——
  一簇一个探针即可覆盖同域多条规则），外加 1 个"dict-AST 语句入口"驱动。
- 证明侧：**342 条 × 4 条判据**，其中 243 条可先把 1/2 自动化，**342 条 `proof_id` + 342 条
  `composition` 全部人工**；按"每族检查器 + 逐规则实例"估，至少 2 个检查器 + 342 条评审记录。

## 3. G3 — 缺口清单

### 3.1 明细是否存在：**存在**（不是"明细缺失"）

在指定的 `.trae/specs/achieve-any-syntax-completeness/rounds` 下按 `missed` 检索，
只命中 4 个 md（`round12/archive/FINAL_REPORT.md`、`GATE_REPORT_SNAPSHOT.md`、`REACHABILITY.md`、
`fresh/final_state/REPORT.md`）——即"汇总"面。但真正的明细在**另一个 spec 树**的
`.trae/specs/attack-completeness-claims/rounds/round9/g3_mutation/` 下，而且是完整的：

| 文件 | 内容 |
|---|---|
| `g3_sample_summary.json` | 30 案聚合 + 逐案 KILLED/MISSED（`sample_size=30`） |
| `case_JS-*.json` × 30 | 每案的 original.pyc / product.source / call_exprs / entrypoint |
| `mut_JS-*.json` × 30 | **逐 mutant 记录**：operator、description、lineno、status、semantic_status、diffs |

`g3_sample_summary.json` sha256 = `67ABCA0509391715FF93E0ADBB0BD1AFE6A4598CBC67C35429F7137E43348D69`。
**缺的只有两样**：(a) 生成这些文件的聚合器（`tool: "g3-sample-runner"` 未入库，仓库里找不到脚本）；
(b) 全量总体（本轮只跑了 30/1556 案）。所以"明细缺失"这个说法**不成立**，
"复跑脚本 + 全量总体缺失"才成立。

### 3.2 missed 按 case 分布（30/30 案都有 survivor，11 案被打到 25 上限）

| case | generated | selected | KILLED | MISSED | ERROR | missed_rate |
|---|---|---|---|---|---|---|
| `JS-ASYNCFOR-021` | 47 | 25 | 0 | 25 | 0 | 1.00 |
| `JS-AUGFORM-017` | 56 | 25 | 0 | 25 | 0 | 1.00 |
| `JS-AWAIT-018` | 47 | 25 | 0 | 25 | 0 | 1.00 |
| `JS-NAMEDEXPR-001` | 59 | 25 | 0 | 25 | 0 | 1.00 |
| `JS-SLICE-007` | 41 | 25 | 0 | 25 | 0 | 1.00 |
| `JS-NONLOCAL-002` | 30 | 25 | 1 | 24 | 0 | 0.96 |
| `JS-NONLOCAL-013` | 30 | 25 | 1 | 24 | 0 | 0.96 |
| `JS-NONLOCAL-033` | 30 | 25 | 1 | 24 | 0 | 0.96 |
| `JS-ASYNCFUNC-011` | 23 | 23 | 0 | 23 | 0 | 1.00 |
| `JS-ASYNCFUNC-012` | 23 | 23 | 0 | 23 | 0 | 1.00 |
| `JS-ASYNCFUNC-017` | 23 | 23 | 0 | 23 | 0 | 1.00 |
| `JS-AWAITEXPR-014` | 23 | 23 | 0 | 23 | 0 | 1.00 |
| `JS-RETURN-057` | 23 | 23 | 0 | 23 | 0 | 1.00 |
| `JS-STARRED-002` | 23 | 23 | 0 | 23 | 0 | 1.00 |
| `JS-STARRED-005` | 23 | 23 | 0 | 23 | 0 | 1.00 |
| `JS-STARRED-011` | 23 | 23 | 0 | 23 | 0 | 1.00 |
| `JS-RETURN-033` | 94 | 25 | 6 | 19 | 0 | 0.76 |
| `JS-RETURN-070` | 94 | 25 | 6 | 19 | 0 | 0.76 |
| `JS-DELETE-019` | 34 | 25 | 7 | 18 | 0 | 0.72 |
| `JS-ASYNCFOR-001` | 16 | 16 | 0 | 16 | 0 | 1.00 |
| `JS-ASYNCFUNC-023` | 16 | 16 | 0 | 16 | 0 | 1.00 |
| `JS-ASYNCWITH-011` | 16 | 16 | 0 | 16 | 0 | 1.00 |
| `JS-AWAIT-014` | 16 | 16 | 0 | 16 | 0 | 1.00 |
| `JS-LISTCOMP-026` | 16 | 16 | 0 | 16 | 0 | 1.00 |
| `JS-RETURN-025` | 16 | 16 | 0 | 16 | 0 | 1.00 |
| `JS-TRY-015` | 17 | 17 | 1 | 16 | 0 | 0.94 |
| `JS-AUGFORM-031` | 18 | 18 | 2 | 15 | 1 | 0.88 |
| `JS-BREAK-001` | 15 | 15 | 1 | 14 | 0 | 0.93 |
| `JS-WHILE-040` | 15 | 15 | 1 | 14 | 0 | 0.93 |
| `JS-MATCHSTMT-019` | 15 | 15 | 5 | 10 | 0 | 0.67 |

KILLED 只出现在 11 案（共 32 个），其余 19 案是 **0 kill**；
单案 missed 最少也有 10 个。被打到 `selected=25` 上限的 11 案：
ASYNCFOR-021、AUGFORM-017、AWAIT-018、NAMEDEXPR-001、SLICE-007、NONLOCAL-002、NONLOCAL-013、NONLOCAL-033、RETURN-033、RETURN-070、DELETE-019。**这不是"少数案拖后腿"**：19/30 案完全看不见差异。

### 3.3 missed 按 mutation operator 分布

| operator | selected | MISSED | missed 占比 |
|---|---|---|---|
| augassign | 24 | 24 | 100% |
| binop | 23 | 22 | 96% |
| boolop | 24 | 20 | 83% |
| compare | 9 | 9 | 100% |
| constant | 229 | 206 | 90% |
| if | 69 | 69 | 100% |
| return | 248 | 243 | 98% |
| unaryop | 4 | 4 | 100% |
| while | 5 | 5 | 100% |

`if`(100%)、`while`(100%)、`augassign`(100%)、`compare`(100%)、`unaryop`(100%)、`return`(98%)、
`constant`(90%) 几乎全漏；只有 `binop`(4/23 被 kill) 与 `boolop`(4/24) 偶有捕获。
**判据对"控制流取反"和"常量值变化"基本全盲**。

### 3.4 抽样 10 条：missed 到底是谁的错

| case | mutant | operator | 变更 | L | semantic_diff | diff 形态 | 归因 | 依据 |
|---|---|---|---|---|---|---|---|---|
| `JS-ASYNCFOR-001` | M0001 | if | if test -> if not test | 4 | DIFFERENT | ['metadata.code'] | 调用域未覆盖 | a_one 从未被调用（case 只执行模块体 + acm()） |
| `JS-ASYNCFUNC-011` | M0020 | return | return value -> return None | 71 | DIFFERENT | ['metadata.code'] | 调用域未覆盖 | e08_yield_from 从未被调用 |
| `JS-ASYNCFUNC-023` | M0011 | return | return value -> return None | 27 | DIFFERENT | ['metadata.code'] | 调用域未覆盖 | a_four 从未被调用 |
| `JS-AUGFORM-031` | M0017 | constant | 'new' -> 'new_mut' | 31 | EQUAL | [] | 判据盲区 | class body 已执行；CIfShallow.TAG 变了，diffs=[] |
| `JS-AWAITEXPR-014` | M0018 | return | return value -> return None | 63 | EQUAL | [] | 调用域未覆盖 | e07_async_closure 从未被调用 |
| `JS-MATCHSTMT-019` | M0009 | constant | 'o' -> 'o_mut' | 19 | EQUAL | [] | 分支不可达 | try 体不抛异常，except (TypeError,KeyError) 分支没进 |
| `JS-NONLOCAL-013` | M0009 | augassign | Mult -> FloorDiv | 14 | EQUAL | [] | 调用域未覆盖 | nl_level4 从未被调用（且 l1%3==0 才走到该行） |
| `JS-RETURN-033` | M0010 | boolop | Or -> And | 9 | DIFFERENT | ['metadata.code'] | 判据盲区 | class body 已执行；CB98.C1 只体现为 $.metadata.code.* 差异 |
| `JS-SLICE-007` | M0003 | constant | 2 -> 3 | 2 | EQUAL | [] | 调用域未覆盖 | e01_root 从未被调用 |
| `JS-STARRED-005` | M0015 | return | return value -> return None | 28 | DIFFERENT | ['metadata.code'] | 调用域未覆盖 | e06_nested 从未被调用 |

归因统计（10 条）：**调用域/分支不可达 7 条**、**判据盲区 2 条**、
**"反编译器错了但判官归一化掉" 0 条**。

关键的一条诚实说明：**这个变异实验里没有反编译器**。`mutation_test.py::run_mutations`
（L258–261）把 `mutant_case["product"] = {"source": <变异后的 .py>}`，
即"被比较的产物"是**变异源码本身**，不是反编译输出。所以这里 602 条 missed 的含义只能是
"判据看不见这次注入的语义差"，**不可能**是"反编译器确实错了被归一化"——
后一种归因需要"pyc → 反编译产物 → 判据"的回路（`fresh/semantic_products/` 里有 1556 份现成产物，
可以作为下一轮 G3 的输入），本轮没有做。

两条判据盲区的机制值得单独跟：`CIfShallow.TAG`（class body 已执行）改值后 **`diffs` 完全为空**，
而 `CB98.C1`（同样在 class body）只产生 `$.metadata.code.co_consts.v[..].code_sha` 差异 →
说明"类体里的属性"既不在 `module_values` 的可观测面里，其 code object 有时连元数据比较都没进。
这是 `semantic_diff` 观测域的具体缺口，须单独立项查（不在本轮只读范围）。

### 3.5 复跑所需的最小命令与规模

单元命令（工具自带用法，`mutation_test.py` L13–21、L313–323）：

```powershell
python -X utf8 tools/completeness/mutation_test.py `
  --case case_JS-SLICE-007.json `
  --source <该案的 product.source> `
  --max-mutants 25 --out mut_JS-SLICE-007.json
```

30 案循环（聚合器需重建，字段照 `g3_sample_summary` 的 `cases[]`/`aggregate` 抄即可）：

```powershell
Get-ChildItem .trae/specs/attack-completeness-claims/rounds/round9/g3_mutation/case_*.json |
  ForEach-Object { python -X utf8 tools/completeness/mutation_test.py --case $_.FullName `
    --max-mutants 25 --out ("...\mut_" + $_.BaseName.Replace('case_','') + ".json") }
```

规模（从 30 案实测外推）：

| 口径 | 数值 | 来源 |
|---|---:|---|
| 已生成 mutants / 已评估 | 922 / 635（21.2 案均） | 30 案实测 |
| 全量 J 空间（1556 案）按案均外推 | **≈ 33,000–48,000 mutants** | 922×1556/30 ≈ 47.8k 生成；25 上限 → 38.9k 评估 |
| 每个 mutant 的成本 | 2 次子进程（original + product）+ 1 次编译 | `semantic_diff.compare_case` |
| 单进程墙钟（按 1–3 s/mutant 估） | **≈ 10–40 h**；8 分片 2–6 h | 经验值，只有量级意义 |

**要得到 `missed=0` 的判定**（`gate_g3`：`survived==0 且 false_kill==0 且 inconclusive==0
且 errors==0 且 killed+survived>0`）：

1. **总体必须是全量而不是抽样**：1556 案 × **全部**生成的 mutants（去掉 `--max-mutants 25`
   截断；被截掉的 mutant 不算"未评估"，需要一个明确的不评估理由）。
2. 每个 survivor 必须二选一：**KILLED**（判据看见了差异）或 **EQUIVALENT + 可审计的等价证明**
   （`--equivalents`，工具只校验非空，真值得评审签）。
3. 当前 survivor 率 94.8%（602/635）→ 若照现状直接全量，需要**数万条等价证明**，
   人力上不成立；可行顺序是**先补观测域**（class-body 属性、未被调用的函数/分支、闭包返回、
   局部中间值），把 survivor 压到可人工证明的量级（≤ 数百），再全量复跑。
4. 另外必须解决 `ERROR=1`（`mut_JS-AUGFORM-031.json` M0005，`R0 product entrypoint body not
   reached` + `module_values` 全 null → 产物侧没跑起来），否则 `gate_g3` 的 `errors==0` 永远不满足。

## 4. 可执行工作项清单

| id | 支柱 | 动作 | 覆盖对象 | 验收判据 | 量级 |
|---|---|---|---|---|---|
| G4-W01 | G4 | 写一条走「字典格式 AST 语句入口」的 J 探针，覆盖 node_type 语句臂 | CodeGenerator._generate_dict_node 16 条（该模块共 17 条 empty_cov） | 这 16 条 rule_id 在重跑 trace 后 coverage 非空 | 1 个探针文件 + 1 个驱动（dict AST 语句入口），12–13 个 node_type 变体 |
| G4-W02 | G4 | 判定 legacy ASTGeneratorV2 路径的去留：造能驱动 v2 生成器的输入模型，或提交 reviewed 排除 | core/cfg/ast_generator_v2.py 32 条（其中 25 条函数 0 次执行） | 32 条要么 coverage 非空，要么有一条带证据的 universe 排除记录（含引用面分析） | 输入模型设计决定；若补探针 5–8 条 |
| G4-W03 | G4 | 对 region_ast_generator 的 15 条 0 执行规则补 async/with/try/yield 形态的 J 输入 | core/cfg/region_ast_generator.py 17 条 | 15 条 never_observed 规则的 enclosing scope 在 trace 中 scope_observed=true | 4–6 条探针（_loop_handle_header/_generate_return_ast/_build_boolop_augassign_target 等） |
| G4-W04 | G4 | 让 StructuredAnalyzer 路径被执行（async with / except pre-311 / with 结构） | core/cfg/structured_analyzer.py 7 条 | 7 条 coverage 非空 | 2–3 条探针 |
| G4-W05 | G4 | 让 ObjectivePatchDetector 入口被调用（目标补丁探测），或评审排除该探测器 | core/cfg/objective_patch_detector.py 11 条（含 3 条零引用） | 11 条要么 coverage 非空，要么排除记录在案 | 1 个入口驱动 + 2–3 条探针；零引用的 3 条另计 |
| G4-W06 | G4 | 补 with 解包 / except-break 出口 / opname 字符串提取 的 J 输入 | region_analyzer 5 + patch_detector 4 = 9 条 | 9 条 coverage 非空 | 3–4 条探针 |
| G4-W07 | G4 | 对 4 条零引用规则做 reviewed 排除决定（不删规则、不改扫描器，只改独立宇宙的收录口径） | ObjectivePatchDetector.analyze_file 3 + ASTGeneratorV2._extract_with_context 1 | 每条一条评审记录：为什么可从独立规则宇宙排除（含 402 语料也未执行的证据） | 1 次评审（4 条） |
| G4-W08 | G4 | 补 comprehension/try-handler/basic_block 条件判定的 J 输入 | comprehension_generator 4 + exception_handler 1 + basic_block 1 = 6 条 | 6 条 coverage 非空 | 2–3 条探针 |
| G4-W09 | G4 | 脚本化派生 243 条 hit 规则的 positive witness（= coverage[rule_id] 的 J id） | 243 条已 hit 规则（其中 228 条 >20 个 witness） | manifest 里 witnesses.positive 非空且每个 id ∈ J 条目 id 集合（_witness_ok 的机械面） | 1 个只读派生脚本 + 243 条记录；不写 status |
| G4-W10 | G4 | 定义 negative witness 的语义并逐条签署候选（先从同 form/host 未命中集合 + counterexample_hint 生成候选） | 243 条（99 条 empty_cov 无 positive，暂不可做） | 评审文档里写明 negative 的定义，且每条 negative 有语义理由 | 定义 1 份 + 243 条签署（人工） |
| G4-W11 | G4 | 解决 composition 判据：定义原子规则的 composition 语义，或提出判据变更评审 | 342 条全部（当前 composition=[] → check() 的 composition_ok=False） | 评审结论落文档；若改判据，需同步 rule_manifest.py（本轮禁止改） | 设计决定 1 个（阻塞项，不解决则 G4 不可能 PASS） |
| G4-W12 | G4 | 为 isinstance_ast(15) 与 opcode_eq(327) 各写一个真检查器，并为 342 条逐条建证明记录（proof_id/checker_version/counterexample_bound/review） | 342 条 | proof_id 非空且指向可复跑的检查器输出；counterexample_bound 有界且写明搜过的域 | 2 族检查器 + 342 条实例化 + 342 条评审 |
| G4-W13 | G4 | 给 2 条单 witness 规则补第二条独立 witness 再谈证明 | 2 | 两条规则的 coverage 长度 ≥2，且来自不同 J 条目（当前都只有 JS-BOOLOP-055） | 2 条（都需要新的 boolop 存储类型探针） |
| G4-W14 | G4 | 重跑 rule_universe/rule_manifest/trace/--check 并归档新的 coverage JSON（以新 SHA 为证据） | 全部 342 条 | G4 从 FAIL 变成 PASS 的唯一合法途径：empty_cov=0 且 proved=342 且 4 条判据全过 | 每轮 1 次（分钟级），但只有在前述输入/证明到位后才有意义 |
| G3-W01 | G3 | 重建 g3 聚合器（仓库里没有该脚本），把 30 案 → 全量 1556 案复跑 | 1556 案 × 全部生成 mutants（去掉 --max-mutants 截断） | 产出一份全量 mutation 报告：survived==0 且 false_kill==0 且 inconclusive==0 且 errors==0 | ≈33k–48k mutants；单进程 10–40 h，8 分片 2–6 h |
| G3-W02 | G3 | 修掉唯一 ERROR（mut_JS-AUGFORM-031 M0005：product entrypoint body not reached） | 1 个 mutant | 该案复跑后 ERROR=0；gate_g3 的 errors==0 才可能满足 | 单案复跑 |
| G3-W03 | G3 | 补 semantic_diff 观测域：class-body 属性、未被调用函数/分支、闭包返回、局部中间值 | 决定 602 survivor 中能转成 KILLED 的比例（抽样 10 条里有 2 条是纯判据盲区） | 同一批 mutants 复跑后 survivor 率显著下降，且不产生 FALSE_KILL | 产品/判据改动，需另立回合（本轮只读） |
| G3-W04 | G3 | 为真正行为等价的 survivor 写 case-relative 等价证明（--equivalents），只对有论证的 | 观测域补齐后剩余的 survivor | 每条证明有语义理由 + scope；工具不验真值，评审负责 | ≤ 数百条（若不做 W03 则是数万条，不现实） |
| G3-W05 | G3 | 补 case 调用域模型：MUT case 的 call_exprs 只覆盖模块体 + 少数构造调用，未调用函数占抽样 missed 的 7/10 | 30 案里 19 案 0 kill；全量为 1556 案 | 每案的 entrypoint/calls 能到达被变异的函数与分支，或明确记录不可达理由 | 30 案先做（≈1 天），全量随 G3-W01 |

## 5. 本轮不做 / 未解决

- 不写任何 `status: proved`、`proof_id`、`composition`、`witness`、`semantic_domain`——这些字段的
  真值不是本轮能产生的；把 342 条填成 proved 会让 `gate_g4` 变 PASS 而证据为零，属伪造。
- 不把 402 语料的 9 条补回计入 J 覆盖（不同输入域，`G4_CURRENT.md` 已明确）。
- 不宣称 G3/G4 通过，不宣称 `product_complete`。
- 未解决（需别处决策）：`composition` 判据的语义；negative witness 的定义；
  99 条中 66+4 条是"补输入"还是"评审排除"（当前只有引用计数这一候选信号，不是死代码证明）；
  `semantic_diff` 对 class-body 属性的观测缺口（3.4 的两条样本）。

## 6. 输入证据

| 文件 | sha256 |
|---|---|
| rule_universe_current.json | `F3AA931FFEA8BBEC7AB5F620C5EA1DC3A09B25C895AFE17E9655E293E9AC7C27` |
| rule_manifest_current.json | `D248D291D20ECD34F65B298FA175214A2DD2ADCA6C472CDEC9A5F047D88498FE` |
| rule_coverage_current.json | `14AD782DA0E7BEB2AE320DAE6D305BE129684423A8497EBCA81A908B322C341F` |
| rule_traces_current.json | `5917DC5F469DC6E6EE0EAE3F59CDAE7E880D0C36C0710FBE26FA890C63B1D8F8` |
| G4_REACHABILITY_CURRENT.json | `D51E54735A16D410A0F8313A4CC8B5B1BA3E4A21130A848EEEFD7572EE06DE81` |

G3 输入：`round9/g3_mutation/` 共 30 `case_*.json` + 30 `mut_*.json` +
`g3_sample_summary.json`（sha256 `67ABCA0509391715FF93E0ADBB0BD1AFE6A4598CBC67C35429F7137E43348D69`）。
