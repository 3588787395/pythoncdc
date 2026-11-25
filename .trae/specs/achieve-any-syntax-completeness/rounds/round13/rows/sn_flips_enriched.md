# 裁决三敏感性 v8 重算：--structural-negative 翻转明细

基线 proof_records_v8_b1.json → SN proof_records_v8_b1_sn.json（shadow env，156.4s）。282/282 规则的 (predicate_evaluations, pyc_runs_reaching_site, anchors_located, anchors_declared) 完全一致；正向见证 126/126 稳定；no_occ 65 条完全一致；candidates 5413 / unmapped 499 完全一致 → SN 只作用于裁决阶段。

## 18 条 open→proved（neg_missing，selection=same_anchor_diff_pyc，structural_negative=True）

| rule_id | symbol | anchor | pattern | witness +/− | 首个负见证 | SN |
|---|---|---|---|---|---|---|
| RULE-105526e5cb57 | FOR_ITER_OPS | dominator_analyzer.py:468 | `instr.opname in FOR_ITER_OPS` | 1/1 | JS-MATCHSTMT-043 | SN |
| RULE-196b1a690257 | LOAD_NAME | ast_generator_v2.py:1103 | `opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DE` | 1/1 | JS-AUGASSIGN-006 | SN |
| RULE-37407d3cc94a | base_skip | region_ast_generator.py:7109 | `instr.opname in base_skip` | 1/1 | JS-ASSERT-001 | SN |
| RULE-440f9734bda7 | LOAD_FAST | ast_generator_v2.py:1103 | `opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DE` | 1/1 | JS-AUGASSIGN-006 | SN |
| RULE-4970d5d079cd | context_expr_ops | region_analyzer.py:9777 | `instr.opname in context_expr_ops` | 1/1 | JS-AUGASSIGN-003 | SN |
| RULE-5f8a4ca1dd8a | LOAD_GLOBAL | ast_generator_v2.py:1103 | `opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DE` | 1/1 | JS-AUGASSIGN-006 | SN |
| RULE-6b8f5b50d608 | LOAD_CLOSURE | ast_generator_v2.py:1103 | `opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DE` | 1/1 | JS-AUGASSIGN-006 | SN |
| RULE-75ad9c36dc4f | check_ops | region_analyzer.py:13382 | `instr.opname in check_ops` | 1/1 | JS-IFEXP-018 | SN |
| RULE-82b8a73502b4 | _b112_noise | region_ast_generator.py:14557 | `_i.opname in _b112_noise` | 1/1 | JS-ASYNCFUNC-025 | SN |
| RULE-85dd5276273c | _stmt_terminators | region_ast_generator.py:34022 | `i.opname in _stmt_terminators` | 1/1 | JS-IF-078 | SN |
| RULE-8f02f7727b77 | _CHECK_OPS | region_analyzer.py:13649 | `instr.opname in _CHECK_OPS` | 1/1 | JS-IFEXP-018 | SN |
| RULE-aa4f7207f477 | _pp.COND_JUMP_OPS | region_analyzer.py:2305 | `all_instrs[i].opname in _pp.COND_JUMP_OPS` | 1/1 | JS-AUGASSIGN-013 | SN |
| RULE-b8c8ba46b225 | stmt_boundary_ops | region_ast_generator.py:77619 | `bi.opname in stmt_boundary_ops` | 1/1 | JS-AUGASSIGN-003 | SN |
| RULE-baa4d7477cbf | EFFECTIVE_NOISE_OPS | region_analyzer.py:4258 | `instr.opname in EFFECTIVE_NOISE_OPS` | 1/1 | JS-AUGASSIGN-006 | SN |
| RULE-cc3bd8d61747 | _CMP_SKIP_OPS | region_ast_generator.py:20481 | `_instr.opname in _CMP_SKIP_OPS` | 1/1 | JS-DELETE-024 | SN |
| RULE-d5f661567cc1 | <module> | region_ast_generator.py:74278 | `self.cfg.name == '<module>'` | 1/1 | JS-AUGASSIGN-007 | SN |
| RULE-e2b9a18ee598 | STATEMENT_TERMINATORS | region_analyzer.py:4261 | `instr.opname in STATEMENT_TERMINATORS` | 1/1 | JS-AUGASSIGN-006 | SN |
| RULE-ee56c630c4f5 | self.RETURN_INSTRUCTIONS | cfg_builder.py:266 | `last_instr.opname in self.RETURN_INSTRUCTIONS` | 1/1 | JS-AUGASSIGN-006 | SN |

## 3 条 neg_missing→guard_only（开放内部降级，非关闭）

| rule_id | symbol | anchor | pattern | witness +/− | 首个负见证 | SN |
|---|---|---|---|---|---|---|
| RULE-00f0d5ffaaff | GET_LEN | ast_generator_v2.py:21495 | `instr.opname == 'GET_LEN'` | 1/1 | JS-ASSERT-010 | SN |
| RULE-1e003061d4c8 | LOAD_DEREF | ast_generator_v2.py:1103 | `opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DE` | 1/1 | JS-AUGASSIGN-006 | SN |
| RULE-b620fe7fb512 | LOAD_CLASSDEREF | ast_generator_v2.py:1103 | `opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DE` | 1/1 | JS-AUGASSIGN-006 | SN |

## 26 条仍为 neg_missing（需补充非见证 pyc 或采纳 SN 裁决）

| rule_id | symbol | anchor | pattern | witness +/− | 首个负见证 | SN |
|---|---|---|---|---|---|---|
| RULE-08253d92ea26 | _store_ops | region_ast_generator.py:12365 | `_instr.opname in _store_ops` | 1/0 |  |  |
| RULE-103bb62f62c8 | _frame_heads | comprehension_generator.py:840 | `s_instrs[0].opname in _frame_heads` | 1/0 |  |  |
| RULE-1dd012303932 | _STORE_CHK_B56 | region_ast_generator.py:55687 | `_b56_i.opname in _STORE_CHK_B56` | 1/0 |  |  |
| RULE-2ad1ffa97019 | Set | code_generator.py:4047 | `node_type == 'Set'` | 1/0 |  |  |
| RULE-2b6f0dcd703d | RETURN_VALUE | ast_generator_v2.py:1877 | `opname in ('RETURN_VALUE', 'RETURN_CONST')` | 1/0 |  |  |
| RULE-4f50e56b6e25 | STORE_FAST | ast_generator_v2.py:920 | `opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STOR` | 1/0 |  |  |
| RULE-4fb15b673728 | Tuple | code_generator.py:2150 | `node_type == 'Tuple'` | 1/0 |  |  |
| RULE-572fd2eb12b9 | _STORE_TYPES_R61_chk | region_ast_generator.py:55312 | `i.opname in _STORE_TYPES_R61_chk` | 1/0 |  |  |
| RULE-5949b5021f68 | STORE_DEREF | ast_generator_v2.py:920 | `opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STOR` | 1/0 |  |  |
| RULE-60c852acef19 | _STORE_CHK | region_ast_generator.py:55066 | `_pinstr.opname in _STORE_CHK` | 1/0 |  |  |
| RULE-6997aa6c7097 | STORE_SUBSCR | ast_generator_v2.py:999 | `opname == 'STORE_SUBSCR'` | 1/0 |  |  |
| RULE-7437333913d0 | Dict | code_generator.py:4055 | `node_type == 'Dict'` | 1/0 |  |  |
| RULE-840c719d57c6 | STORE_NAME | ast_generator_v2.py:920 | `opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STOR` | 1/0 |  |  |
| RULE-8637d89b4417 | Attribute | code_generator.py:4032 | `node_type == 'Attribute'` | 1/0 |  |  |
| RULE-87685c80e83d | CACHE | ast_generator_v2.py:2666 | `opname == 'CACHE'` | 1/0 |  |  |
| RULE-ab1d4cc5ec5e | _STORE_TYPES_R61 | region_ast_generator.py:54936 | `_ci.opname in _STORE_TYPES_R61` | 1/0 |  |  |
| RULE-b0bb824910b4 | return | ast_generator_v2.py:4906 | `name == 'return'` | 1/0 |  |  |
| RULE-b231086215ec | _lit_consume_ops | region_ast_generator.py:73957 | `ri.opname in _lit_consume_ops` | 1/0 |  |  |
| RULE-bfc679b49338 | self._B54_LOADISH_OPS | region_ast_generator.py:4960 | `instr.opname in self._B54_LOADISH_OPS` | 1/0 |  |  |
| RULE-c214919432c0 | Name | code_generator.py:2148 | `node_type == 'Name'` | 1/0 |  |  |
| RULE-db3c378f2dad | STORE_ATTR | ast_generator_v2.py:1038 | `opname == 'STORE_ATTR'` | 1/0 |  |  |
| RULE-e4ed34fb8c7f | _store_ops_set | region_ast_generator.py:55325 | `i.opname in _store_ops_set` | 1/0 |  |  |
| RULE-e7701666d7b5 | RESUME | ast_generator_v2.py:2662 | `opname == 'RESUME'` | 1/0 |  |  |
| RULE-e77fbe9ddbee | STORE_GLOBAL | ast_generator_v2.py:920 | `opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STOR` | 1/0 |  |  |
| RULE-ec53116b4211 | List | code_generator.py:2174 | `node_type in ('List', 'Starred')` | 1/0 |  |  |
| RULE-ed5bec7d7a05 | LOAD_CONST | ast_generator_v2.py:1062 | `opname in ('LOAD_CONST', 'LOAD_CONSTANT')` | 1/0 |  |  |
