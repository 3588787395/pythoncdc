# 判定空间覆盖基线（Coverage Baseline）— attack-completeness-claims / Task 1

> 工具：`tools/completeness/coverage_checker.py`；判定空间：`.trae/specs/attack-completeness-claims/rounds/round1/judgment_space.json`。
> 证据索引根：`.trae/specs/attain-true-completeness/rounds`（扫描到 405 份 `rec1_probes_*.json` stamp，237 条探针记录，103 个探针路径）。
> 覆盖口径：条目 `required_evidence[].pyc` 命中证据索引 ⇒ covered；否则 uncovered。

## 0. 总读数

| 项 | 值 |
|---|---|
| 判定空间条目总数 | **1556** |
| covered（有专属见证探针） | **976** |
| uncovered（无专属见证探针） | **580** |
| 覆盖率 | 62.72% |
| 形态族数 | 39 |
| 清单声明与实测状态不一致 | 0 |

> **这就是本次攻击的首个读数**：上一规范以「完备 128 / 破口 0 / 零能力 0 = 100%」结案，而按**判定空间口径**，当前仅 976/1556 个单元有专属见证探针（62.72%），**580 个单元无任何专属证据**。「100%」是折叠口径的读数，不是判定空间口径的读数。

## 1. 逐形态族覆盖

| form | row | 条目 | covered | uncovered | 覆盖率 |
|---|---|---|---|---|---|
| AnnAssign | NEW | 15 | 3 | 12 | 20.00% |
| Assert | Assert | 46 | 34 | 12 | 73.91% |
| AsyncFor | NEW | 21 | 9 | 12 | 42.86% |
| AsyncFunctionDef | NEW | 25 | 13 | 12 | 52.00% |
| AsyncWith | NEW | 24 | 12 | 12 | 50.00% |
| AugAssign | AugAssign | 63 | 51 | 12 | 80.95% |
| Await | Await | 23 | 11 | 12 | 47.83% |
| BoolOp | BoolOp | 85 | 73 | 12 | 85.88% |
| Break | Break | 32 | 20 | 12 | 62.50% |
| Continue | Continue | 35 | 23 | 12 | 65.71% |
| Decorator | NEW | 20 | 8 | 12 | 40.00% |
| Delete | Delete | 24 | 12 | 12 | 50.00% |
| DictComp | NEW | 23 | 11 | 12 | 47.83% |
| ExceptStar | NEW | 96 | 0 | 96 | 0.00% |
| GeneratorExp | NEW | 21 | 9 | 12 | 42.86% |
| Global | Global | 19 | 7 | 12 | 36.84% |
| If | If | 118 | 106 | 12 | 89.83% |
| IfExp | IfExp | 28 | 16 | 12 | 57.14% |
| Import | Import | 47 | 35 | 12 | 74.47% |
| JoinedStr | NEW | 32 | 20 | 12 | 62.50% |
| Lambda | NEW | 18 | 6 | 12 | 33.33% |
| ListComp | ListComp | 40 | 28 | 12 | 70.00% |
| Match | Match | 37 | 25 | 12 | 67.57% |
| NamedExpr | NEW | 14 | 2 | 12 | 14.29% |
| PEP604Union | NEW | 12 | 0 | 12 | 0.00% |
| Raise | Raise | 39 | 27 | 12 | 69.23% |
| Return | Return | 80 | 68 | 12 | 85.00% |
| SetComp | NEW | 17 | 5 | 12 | 29.41% |
| Slice | Slice | 25 | 13 | 12 | 52.00% |
| Starred | NEW | 21 | 9 | 12 | 42.86% |
| Try | Try | 108 | 96 | 12 | 88.89% |
| While | While | 45 | 33 | 12 | 73.33% |
| With | With | 83 | 71 | 12 | 85.54% |
| Yield | Yield | 18 | 6 | 12 | 33.33% |
| augmented_assign | augmented_assign | 49 | 37 | 12 | 75.51% |
| await_expr | await_expr | 21 | 9 | 12 | 42.86% |
| global_nonlocal | global_nonlocal | 40 | 0 | 40 | 0.00% |
| match_statement | match_statement | 60 | 48 | 12 | 80.00% |
| slice | slice | 32 | 20 | 12 | 62.50% |

### 1.1 最差形态族（uncovered 绝对数前 10）

| form | 条目 | covered | uncovered |
|---|---|---|---|
| ExceptStar | 96 | 0 | 96 |
| global_nonlocal | 40 | 0 | 40 |
| If | 118 | 106 | 12 |
| Try | 108 | 96 | 12 |
| BoolOp | 85 | 73 | 12 |
| With | 83 | 71 | 12 |
| Return | 80 | 68 | 12 |
| AugAssign | 63 | 51 | 12 |
| match_statement | 60 | 48 | 12 |
| augmented_assign | 49 | 37 | 12 |

## 2. 未覆盖单元清单

共 **580** 条。`required_evidence.pyc` 列给出该单元所引用的**同族锚点探针**（仓内真实存在，但从未登记进 `rec1_probes_*.json` 证据索引）。

| id | form | host | depth | variant | row | 锚点探针 |
|---|---|---|---|---|---|---|
| JS-IF-005 | If | class-body | d1 单层 | if-no-else | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-008 | If | elif-arm | d2 双层 | if-no-else | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-013 | If | loop-else | d1 单层 | if-no-else | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-024 | If | nested-func-body | d2 双层 | if-no-else | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-033 | If | elif-arm | d2 双层 | if-else-arm | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-038 | If | loop-else | d1 单层 | if-else-arm | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-044 | If | else-of-try | d1 单层 | if-else-arm | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-045 | If | finally-body | d1 单层 | if-else-arm | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-048 | If | nested-func-body | d2 双层 | if-else-arm | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-049 | If | module-level | d1 单层 | if-elif-chain | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-053 | If | class-body | d1 单层 | if-elif-chain | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-IF-056 | If | elif-arm | d2 双层 | if-elif-chain | If | `test_repros/round1/r1_17_elif_mixed.pyc` |
| JS-BOOLOP-001 | BoolOp | module-level | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-002 | BoolOp | function-body | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-003 | BoolOp | if-arm | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-006 | BoolOp | loop-body | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-017 | BoolOp | comprehension-if | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-019 | BoolOp | except-handler | d2 双层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-020 | BoolOp | finally-body | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-021 | BoolOp | module-level | d1 单层 | boolop-or | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-022 | BoolOp | function-body | d1 单层 | boolop-or | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-023 | BoolOp | if-arm | d1 单层 | boolop-or | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-026 | BoolOp | loop-body | d1 单层 | boolop-or | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-BOOLOP-033 | BoolOp | call-arg | d1 单层 | boolop-or | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` |
| JS-IFEXP-001 | IfExp | function-body | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-002 | IfExp | module-level | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-003 | IfExp | assign-rhs | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-007 | IfExp | call-arg | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-008 | IfExp | subscript-index | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-009 | IfExp | condition-expr | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-010 | IfExp | comprehension-scope | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-011 | IfExp | lambda-body | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-012 | IfExp | boolop-operand | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-013 | IfExp | binop-operand | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-014 | IfExp | if-arm | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-IFEXP-015 | IfExp | match-guard | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` |
| JS-TRY-002 | Try | module-level | d1 单层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-011 | Try | except-handler | d2 双层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-012 | Try | else-of-try | d1 单层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-013 | Try | finally-body | d1 单层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-014 | Try | nested-func-body | d2 双层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-016 | Try | match-case-body | d1 单层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-030 | Try | else-of-try | d1 单层 | try-with-handler | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-031 | Try | finally-body | d1 单层 | try-with-handler | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-032 | Try | nested-func-body | d2 双层 | try-with-handler | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-034 | Try | match-case-body | d1 单层 | try-with-handler | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-036 | Try | module-level | d1 单层 | try-with-else | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-TRY-039 | Try | with-body | d1 单层 | try-with-else | Try | `test_repros/round2/m04_module_try.pyc` |
| JS-RAISE-001 | Raise | function-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-002 | Raise | module-level | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-003 | Raise | if-arm | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-006 | Raise | finally-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-007 | Raise | try-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-008 | Raise | loop-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-009 | Raise | with-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-010 | Raise | match-case-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-011 | Raise | nested-func-body | d2 双层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-014 | Raise | module-level | d1 单层 | raise-exc-call | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-019 | Raise | finally-body | d1 单层 | raise-exc-call | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-RAISE-021 | Raise | loop-body | d1 单层 | raise-exc-call | Raise | `test_repros/round2/r2_15_reraise.pyc` |
| JS-ASSERT-004 | Assert | else-arm | d1 单层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-005 | Assert | loop-body | d1 单层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-006 | Assert | try-body | d1 单层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-007 | Assert | except-handler | d2 双层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-008 | Assert | with-body | d1 单层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-011 | Assert | nested-func-body | d2 双层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-012 | Assert | finally-body | d1 单层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-015 | Assert | module-level | d1 单层 | assert-with-msg | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-018 | Assert | else-arm | d1 单层 | assert-with-msg | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-021 | Assert | try-body | d1 单层 | assert-with-msg | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-022 | Assert | except-handler | d2 双层 | assert-with-msg | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-ASSERT-026 | Assert | nested-func-body | d2 双层 | assert-with-msg | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` |
| JS-IMPORT-002 | Import | function-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-003 | Import | class-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-008 | Import | else-of-try | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-009 | Import | finally-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-010 | Import | if-arm | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-011 | Import | with-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-012 | Import | loop-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-013 | Import | match-case-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-014 | Import | nested-func-body | d2 双层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-016 | Import | function-body | d1 单层 | import-as | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-017 | Import | class-body | d1 单层 | import-as | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-IMPORT-019 | Import | except-handler | d2 双层 | import-as | Import | `test_repros/round4/c4_15_star_import.pyc` |
| JS-GLOBAL-003 | Global | class-body | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-004 | Global | nested-func-body | d2 双层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-005 | Global | if-arm | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-006 | Global | loop-body | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-007 | Global | try-body | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-008 | Global | except-handler | d2 双层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-009 | Global | with-body | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-010 | Global | match-case-body | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-012 | Global | function-body | d1 单层 | global-multiple | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-013 | Global | class-body | d1 单层 | global-multiple | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-014 | Global | nested-func-body | d2 双层 | global-multiple | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-GLOBAL-015 | Global | if-arm | d1 单层 | global-multiple | Global | `test_repros/round10/r10_12_global_deep.pyc` |
| JS-NONLOCAL-001 | global_nonlocal | function-body | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-002 | global_nonlocal | nested-func-body | d2 双层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-003 | global_nonlocal | class-body | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-004 | global_nonlocal | if-arm | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-005 | global_nonlocal | loop-body | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-006 | global_nonlocal | try-body | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-007 | global_nonlocal | except-handler | d2 双层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-008 | global_nonlocal | with-body | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-009 | global_nonlocal | function-body | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-010 | global_nonlocal | nested-func-body | d2 双层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-011 | global_nonlocal | class-body | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-012 | global_nonlocal | if-arm | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-013 | global_nonlocal | loop-body | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-014 | global_nonlocal | try-body | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-015 | global_nonlocal | except-handler | d2 双层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-016 | global_nonlocal | with-body | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-017 | global_nonlocal | function-body | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-018 | global_nonlocal | nested-func-body | d2 双层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-019 | global_nonlocal | class-body | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-020 | global_nonlocal | if-arm | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-021 | global_nonlocal | loop-body | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-022 | global_nonlocal | try-body | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-023 | global_nonlocal | except-handler | d2 双层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-024 | global_nonlocal | with-body | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-025 | global_nonlocal | function-body | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-026 | global_nonlocal | nested-func-body | d2 双层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-027 | global_nonlocal | class-body | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-028 | global_nonlocal | if-arm | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-029 | global_nonlocal | loop-body | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-030 | global_nonlocal | try-body | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-031 | global_nonlocal | except-handler | d2 双层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-032 | global_nonlocal | with-body | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-033 | global_nonlocal | function-body | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-034 | global_nonlocal | nested-func-body | d2 双层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-035 | global_nonlocal | class-body | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-036 | global_nonlocal | if-arm | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-037 | global_nonlocal | loop-body | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-038 | global_nonlocal | try-body | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-039 | global_nonlocal | except-handler | d2 双层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-NONLOCAL-040 | global_nonlocal | with-body | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` |
| JS-AWAIT-001 | Await | async-func-body | d1 单层 | await-in-async-def | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-002 | Await | function-body | d1 单层 | await-in-async-def | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-005 | Await | if-arm | d1 单层 | await-in-async-def | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-006 | Await | loop-body | d1 单层 | await-in-async-def | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-007 | Await | async-func-body | d1 单层 | await-in-async-with | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-008 | Await | function-body | d1 单层 | await-in-async-with | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-009 | Await | comprehension-scope | d1 单层 | await-in-async-with | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-010 | Await | if-arm | d1 单层 | await-in-async-with | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-011 | Await | loop-body | d1 单层 | await-in-async-with | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-012 | Await | async-func-body | d1 单层 | await-in-async-for | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-013 | Await | function-body | d1 单层 | await-in-async-for | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-AWAIT-015 | Await | if-arm | d1 单层 | await-in-async-for | Await | `test_repros/round6/r6_07_async_five.pyc` |
| JS-LISTCOMP-001 | ListComp | function-body | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-002 | ListComp | module-level | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-013 | ListComp | comprehension-if | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-014 | ListComp | comprehension-for | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-015 | ListComp | if-arm | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-016 | ListComp | loop-body | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-017 | ListComp | class-body | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-018 | ListComp | annotation-context | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-019 | ListComp | function-body | d1 单层 | listcomp-multi-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-020 | ListComp | module-level | d1 单层 | listcomp-multi-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-021 | ListComp | assign-rhs | d1 单层 | listcomp-multi-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-LISTCOMP-023 | ListComp | call-arg | d1 单层 | listcomp-multi-for | ListComp | `test_repros/round5/probe_comp_min.pyc` |
| JS-AWAITEXPR-001 | await_expr | condition-expr | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-002 | await_expr | return-value-expr | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-003 | await_expr | call-arg | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-004 | await_expr | assign-rhs | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-005 | await_expr | binop-operand | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-006 | await_expr | boolop-operand | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-007 | await_expr | await-operand | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-008 | await_expr | if-arm | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-009 | await_expr | comprehension-scope | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-010 | await_expr | match-guard | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-011 | await_expr | condition-expr | d1 单层 | awexpr-in-while-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-AWAITEXPR-012 | await_expr | return-value-expr | d1 单层 | awexpr-in-while-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` |
| JS-YIELD-001 | Yield | generator-func-body | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-002 | Yield | function-body | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-003 | Yield | try-body | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-004 | Yield | finally-body | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-005 | Yield | except-handler | d2 双层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-006 | Yield | loop-body | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-007 | Yield | condition-expr | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-008 | Yield | boolop-operand | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-009 | Yield | call-arg | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-010 | Yield | assign-rhs | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-011 | Yield | if-arm | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-YIELD-012 | Yield | nested-func-body | d2 双层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` |
| JS-MATCHPAT-003 | Match | pattern-value | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-004 | Match | pattern-class | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-005 | Match | pattern-sequence | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-006 | Match | pattern-mapping | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-007 | Match | pattern-capture | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-009 | Match | pattern-star | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-010 | Match | match-guard | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-011 | Match | function-body | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-012 | Match | match-subject | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-013 | Match | match-case-body | d1 单层 | pat-singleton | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-014 | Match | pattern-value | d1 单层 | pat-singleton | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-MATCHPAT-015 | Match | pattern-class | d1 单层 | pat-singleton | Match | `test_repros/round4/r4_06_match_or.pyc` |
| JS-WITH-003 | With | module-level | d1 单层 | with-single-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-012 | With | with-item | d1 单层 | with-single-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-015 | With | nested-func-body | d2 双层 | with-single-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-018 | With | module-level | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-019 | With | if-arm | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-021 | With | try-body | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-022 | With | except-handler | d2 双层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-023 | With | with-body | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-024 | With | with-item | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-026 | With | nested-func-body | d2 双层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-027 | With | else-arm | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` |
| JS-WITH-030 | With | module-level | d1 单层 | with-as-target | With | `test_repros/round2/c05_class_with.pyc` |
| JS-MATCHSTMT-001 | match_statement | module-level | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-003 | match_statement | if-arm | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-004 | match_statement | loop-body | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-005 | match_statement | try-body | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-006 | match_statement | except-handler | d2 双层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-007 | match_statement | with-body | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-008 | match_statement | match-case-body | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-009 | match_statement | class-body | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-010 | match_statement | nested-func-body | d2 双层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-011 | match_statement | module-level | d1 单层 | mmulti-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-017 | match_statement | except-handler | d2 双层 | mmulti-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-MATCHSTMT-022 | match_statement | class-body | d1 单层 | mmulti-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` |
| JS-BREAK-002 | Break | loop-else | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-003 | Break | try-body | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-005 | Break | finally-body | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-006 | Break | with-body | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-007 | Break | match-case-body | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-009 | Break | function-body | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-010 | Break | module-level | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-012 | Break | loop-else | d1 单层 | break-in-while | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-013 | Break | try-body | d1 单层 | break-in-while | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-015 | Break | finally-body | d1 单层 | break-in-while | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-017 | Break | match-case-body | d1 单层 | break-in-while | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-BREAK-019 | Break | function-body | d1 单层 | break-in-while | Break | `test_repros/round7/r7v7r_b120_break.pyc` |
| JS-CONTINUE-003 | Continue | loop-else | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-004 | Continue | try-body | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-006 | Continue | finally-body | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-007 | Continue | with-body | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-008 | Continue | match-case-body | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-011 | Continue | function-body | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-012 | Continue | module-level | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-015 | Continue | loop-else | d1 单层 | continue-in-while | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-016 | Continue | try-body | d1 单层 | continue-in-while | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-018 | Continue | finally-body | d1 单层 | continue-in-while | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-019 | Continue | with-body | d1 单层 | continue-in-while | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-CONTINUE-020 | Continue | match-case-body | d1 单层 | continue-in-while | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` |
| JS-WHILE-001 | While | module-level | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-004 | While | class-body | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-005 | While | if-arm | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-006 | While | loop-body | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-008 | While | except-handler | d2 双层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-009 | While | with-body | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-010 | While | match-case-body | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-011 | While | nested-func-body | d2 双层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-012 | While | else-arm | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-013 | While | module-level | d1 单层 | while-cond-ternary | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-015 | While | class-body | d1 单层 | while-cond-ternary | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-WHILE-016 | While | if-arm | d1 单层 | while-cond-ternary | While | `test_repros/round1/r1_10_while_mixed.pyc` |
| JS-DELETE-003 | Delete | if-arm | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-004 | Delete | else-arm | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-005 | Delete | loop-body | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-006 | Delete | try-body | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-007 | Delete | except-handler | d2 双层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-008 | Delete | finally-body | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-009 | Delete | with-body | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-010 | Delete | match-case-body | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-011 | Delete | nested-func-body | d2 双层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-013 | Delete | module-level | d1 单层 | del-subscript | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-015 | Delete | else-arm | d1 单层 | del-subscript | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-DELETE-016 | Delete | loop-body | d1 单层 | del-subscript | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` |
| JS-AUGASSIGN-012 | AugAssign | with-body | d1 单层 | aug-op-add | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-014 | AugAssign | class-body | d1 单层 | aug-op-add | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-015 | AugAssign | nested-func-body | d2 双层 | aug-op-add | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-017 | AugAssign | module-level | d1 单层 | aug-op-sub | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-026 | AugAssign | with-body | d1 单层 | aug-op-sub | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-027 | AugAssign | match-case-body | d1 单层 | aug-op-sub | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-028 | AugAssign | class-body | d1 单层 | aug-op-sub | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-029 | AugAssign | nested-func-body | d2 双层 | aug-op-sub | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-031 | AugAssign | module-level | d1 单层 | aug-op-mul | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-032 | AugAssign | if-arm | d1 单层 | aug-op-mul | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-033 | AugAssign | else-arm | d1 单层 | aug-op-mul | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGASSIGN-034 | AugAssign | loop-body | d1 单层 | aug-op-mul | AugAssign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-RETURN-001 | Return | function-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-002 | Return | nested-func-body | d2 双层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-003 | Return | module-level | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-004 | Return | if-arm | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-005 | Return | else-arm | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-006 | Return | loop-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-007 | Return | try-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-008 | Return | except-handler | d2 双层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-009 | Return | finally-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-010 | Return | with-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-011 | Return | match-case-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-RETURN-012 | Return | class-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` |
| JS-SLICE-004 | Slice | slice-bounds | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-005 | Slice | function-body | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-006 | Slice | module-level | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-007 | Slice | assign-rhs | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-008 | Slice | if-arm | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-009 | Slice | loop-body | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-010 | Slice | try-body | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-011 | Slice | call-arg | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-013 | Slice | slice-bounds | d1 单层 | slice-with-step | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-014 | Slice | function-body | d1 单层 | slice-with-step | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-015 | Slice | module-level | d1 单层 | slice-with-step | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICE-016 | Slice | assign-rhs | d1 单层 | slice-with-step | Slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-AUGFORM-012 | augmented_assign | with-body | d1 单层 | augform-target-name | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-014 | augmented_assign | comprehension-scope | d1 单层 | augform-target-name | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-015 | augmented_assign | class-body | d1 单层 | augform-target-name | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-017 | augmented_assign | module-level | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-018 | augmented_assign | if-arm | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-019 | augmented_assign | else-arm | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-020 | augmented_assign | loop-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-021 | augmented_assign | try-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-022 | augmented_assign | except-handler | d2 双层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-023 | augmented_assign | finally-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-024 | augmented_assign | with-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-AUGFORM-025 | augmented_assign | match-case-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` |
| JS-SLICEFORM-004 | slice | slice-bounds | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-005 | slice | function-body | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-006 | slice | module-level | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-007 | slice | assign-rhs | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-008 | slice | if-arm | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-009 | slice | loop-body | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-010 | slice | try-body | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-011 | slice | call-arg | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-012 | slice | return-value-expr | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-014 | slice | slice-bounds | d1 单层 | sliceform-in-del-target | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-015 | slice | function-body | d1 单层 | sliceform-in-del-target | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-SLICEFORM-016 | slice | module-level | d1 单层 | sliceform-in-del-target | slice | `test_repros/round4/c4_13_slice.pyc` |
| JS-LAMBDA-001 | Lambda | function-body | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-002 | Lambda | module-level | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-004 | Lambda | call-arg | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-005 | Lambda | return-value-expr | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-006 | Lambda | class-body | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-007 | Lambda | if-arm | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-008 | Lambda | loop-body | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-009 | Lambda | comprehension-scope | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-010 | Lambda | condition-expr | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-011 | Lambda | function-body | d1 单层 | lambda-as-call-arg | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-012 | Lambda | module-level | d1 单层 | lambda-as-call-arg | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-LAMBDA-013 | Lambda | assign-rhs | d1 单层 | lambda-as-call-arg | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` |
| JS-DECORATOR-001 | Decorator | decorator-expr | d1 单层 | deco-on-function | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-002 | Decorator | function-body | d1 单层 | deco-on-function | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-005 | Decorator | call-arg | d1 单层 | deco-on-function | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-006 | Decorator | decorator-expr | d1 单层 | deco-on-class | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-007 | Decorator | function-body | d1 单层 | deco-on-class | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-008 | Decorator | class-body | d1 单层 | deco-on-class | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-009 | Decorator | module-level | d1 单层 | deco-on-class | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-010 | Decorator | call-arg | d1 单层 | deco-on-class | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-011 | Decorator | decorator-expr | d1 单层 | deco-single | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-012 | Decorator | function-body | d1 单层 | deco-single | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-015 | Decorator | call-arg | d1 单层 | deco-single | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-DECORATOR-016 | Decorator | decorator-expr | d1 单层 | deco-stack | NEW | `site-packages/fly/common/aes_encrypt.pyc` |
| JS-SETCOMP-001 | SetComp | function-body | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-002 | SetComp | module-level | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-003 | SetComp | assign-rhs | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-006 | SetComp | call-arg | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-007 | SetComp | comprehension-scope | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-008 | SetComp | comprehension-if | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-009 | SetComp | if-arm | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-010 | SetComp | loop-body | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-011 | SetComp | class-body | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-012 | SetComp | function-body | d1 单层 | setcomp-multi-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-013 | SetComp | module-level | d1 单层 | setcomp-multi-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-SETCOMP-014 | SetComp | assign-rhs | d1 单层 | setcomp-multi-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` |
| JS-DICTCOMP-001 | DictComp | function-body | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-002 | DictComp | module-level | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-007 | DictComp | comprehension-scope | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-008 | DictComp | comprehension-if | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-009 | DictComp | if-arm | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-010 | DictComp | loop-body | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-011 | DictComp | class-body | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-012 | DictComp | function-body | d1 单层 | dictcomp-multi-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-013 | DictComp | module-level | d1 单层 | dictcomp-multi-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-014 | DictComp | assign-rhs | d1 单层 | dictcomp-multi-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-015 | DictComp | return-value-expr | d1 单层 | dictcomp-multi-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-DICTCOMP-016 | DictComp | call-arg | d1 单层 | dictcomp-multi-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` |
| JS-GENEXP-001 | GeneratorExp | function-body | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-002 | GeneratorExp | module-level | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-004 | GeneratorExp | return-value-expr | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-008 | GeneratorExp | comprehension-scope | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-009 | GeneratorExp | comprehension-if | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-010 | GeneratorExp | if-arm | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-011 | GeneratorExp | loop-body | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-012 | GeneratorExp | class-body | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-013 | GeneratorExp | function-body | d1 单层 | genexp-multi-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-014 | GeneratorExp | module-level | d1 单层 | genexp-multi-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-015 | GeneratorExp | assign-rhs | d1 单层 | genexp-multi-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-GENEXP-016 | GeneratorExp | return-value-expr | d1 单层 | genexp-multi-for | NEW | `test_repros/round5/r5_02_genexp.pyc` |
| JS-NAMEDEXPR-001 | NamedExpr | function-body | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-002 | NamedExpr | module-level | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-003 | NamedExpr | if-arm | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-005 | NamedExpr | loop-body | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-006 | NamedExpr | condition-expr | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-007 | NamedExpr | comprehension-if | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-008 | NamedExpr | comprehension-for | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-009 | NamedExpr | try-body | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-010 | NamedExpr | except-handler | d2 双层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-011 | NamedExpr | with-body | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-012 | NamedExpr | assign-rhs | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-NAMEDEXPR-013 | NamedExpr | call-arg | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` |
| JS-FSTRING-001 | JoinedStr | function-body | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-002 | JoinedStr | module-level | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-003 | JoinedStr | assign-rhs | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-004 | JoinedStr | return-value-expr | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-005 | JoinedStr | call-arg | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-006 | JoinedStr | f-string-format | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-007 | JoinedStr | if-arm | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-008 | JoinedStr | loop-body | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-009 | JoinedStr | try-body | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-010 | JoinedStr | class-body | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-011 | JoinedStr | dict-literal | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-FSTRING-012 | JoinedStr | function-body | d1 单层 | fstring-with-var | NEW | `test_repros/round3/e11_g8_fstrings.pyc` |
| JS-STARRED-001 | Starred | function-body | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-002 | Starred | module-level | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-005 | Starred | assign-rhs | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-006 | Starred | starred-operand | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-007 | Starred | return-value-expr | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-008 | Starred | list-literal | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-009 | Starred | tuple-literal | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-010 | Starred | if-arm | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-011 | Starred | loop-body | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-012 | Starred | function-body | d1 单层 | starred-at-head | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-013 | Starred | module-level | d1 单层 | starred-at-head | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-STARRED-014 | Starred | call-arg | d1 单层 | starred-at-head | NEW | `test_repros/round4/c4_12_star_args.pyc` |
| JS-EXCEPTSTAR-001 | ExceptStar | function-body | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-002 | ExceptStar | module-level | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-003 | ExceptStar | try-body | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-004 | ExceptStar | except-handler | d2 双层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-005 | ExceptStar | else-of-try | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-006 | ExceptStar | finally-body | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-007 | ExceptStar | if-arm | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-008 | ExceptStar | loop-body | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-009 | ExceptStar | with-body | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-010 | ExceptStar | nested-func-body | d2 双层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-011 | ExceptStar | function-body | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-012 | ExceptStar | module-level | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-013 | ExceptStar | try-body | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-014 | ExceptStar | except-handler | d2 双层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-015 | ExceptStar | else-of-try | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-016 | ExceptStar | finally-body | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-017 | ExceptStar | if-arm | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-018 | ExceptStar | loop-body | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-019 | ExceptStar | with-body | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-020 | ExceptStar | nested-func-body | d2 双层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-021 | ExceptStar | function-body | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-022 | ExceptStar | module-level | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-023 | ExceptStar | try-body | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-024 | ExceptStar | except-handler | d2 双层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-025 | ExceptStar | else-of-try | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-026 | ExceptStar | finally-body | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-027 | ExceptStar | if-arm | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-028 | ExceptStar | loop-body | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-029 | ExceptStar | with-body | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-030 | ExceptStar | nested-func-body | d2 双层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-031 | ExceptStar | function-body | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-032 | ExceptStar | module-level | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-033 | ExceptStar | try-body | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-034 | ExceptStar | except-handler | d2 双层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-035 | ExceptStar | else-of-try | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-036 | ExceptStar | finally-body | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-037 | ExceptStar | if-arm | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-038 | ExceptStar | loop-body | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-039 | ExceptStar | with-body | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-040 | ExceptStar | nested-func-body | d2 双层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-041 | ExceptStar | function-body | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-042 | ExceptStar | module-level | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-043 | ExceptStar | try-body | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-044 | ExceptStar | except-handler | d2 双层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-045 | ExceptStar | else-of-try | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-046 | ExceptStar | finally-body | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-047 | ExceptStar | if-arm | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-048 | ExceptStar | loop-body | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-049 | ExceptStar | with-body | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-050 | ExceptStar | nested-func-body | d2 双层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-051 | ExceptStar | function-body | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-052 | ExceptStar | module-level | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-053 | ExceptStar | try-body | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-054 | ExceptStar | except-handler | d2 双层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-055 | ExceptStar | else-of-try | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-056 | ExceptStar | finally-body | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-057 | ExceptStar | if-arm | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-058 | ExceptStar | loop-body | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-059 | ExceptStar | with-body | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-060 | ExceptStar | nested-func-body | d2 双层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-061 | ExceptStar | function-body | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-062 | ExceptStar | try-body | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-063 | ExceptStar | except-handler | d2 双层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-064 | ExceptStar | else-of-try | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-065 | ExceptStar | finally-body | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-066 | ExceptStar | if-arm | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-067 | ExceptStar | loop-body | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-068 | ExceptStar | with-body | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-069 | ExceptStar | nested-func-body | d2 双层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-070 | ExceptStar | function-body | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-071 | ExceptStar | try-body | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-072 | ExceptStar | except-handler | d2 双层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-073 | ExceptStar | else-of-try | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-074 | ExceptStar | finally-body | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-075 | ExceptStar | if-arm | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-076 | ExceptStar | loop-body | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-077 | ExceptStar | with-body | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-078 | ExceptStar | nested-func-body | d2 双层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-079 | ExceptStar | function-body | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-080 | ExceptStar | try-body | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-081 | ExceptStar | except-handler | d2 双层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-082 | ExceptStar | else-of-try | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-083 | ExceptStar | finally-body | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-084 | ExceptStar | if-arm | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-085 | ExceptStar | loop-body | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-086 | ExceptStar | with-body | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-087 | ExceptStar | nested-func-body | d2 双层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-088 | ExceptStar | function-body | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-089 | ExceptStar | try-body | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-090 | ExceptStar | except-handler | d2 双层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-091 | ExceptStar | else-of-try | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-092 | ExceptStar | finally-body | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-093 | ExceptStar | if-arm | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-094 | ExceptStar | loop-body | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-095 | ExceptStar | with-body | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-EXCEPTSTAR-096 | ExceptStar | nested-func-body | d2 双层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` |
| JS-ANNASSIGN-001 | AnnAssign | function-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-003 | AnnAssign | class-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-004 | AnnAssign | if-arm | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-005 | AnnAssign | loop-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-006 | AnnAssign | try-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-007 | AnnAssign | except-handler | d2 双层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-008 | AnnAssign | with-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-009 | AnnAssign | match-case-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-010 | AnnAssign | annotation-context | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-011 | AnnAssign | function-body | d1 单层 | ann-subscript-target | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-012 | AnnAssign | module-level | d1 单层 | ann-subscript-target | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ANNASSIGN-013 | AnnAssign | class-body | d1 单层 | ann-subscript-target | NEW | `test_repros/round2/c01_class_assign.pyc` |
| JS-ASYNCFOR-003 | AsyncFor | function-body | d1 单层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-004 | AsyncFor | comprehension-scope | d1 单层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-005 | AsyncFor | loop-body | d1 单层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-006 | AsyncFor | loop-else | d1 单层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-008 | AsyncFor | try-body | d1 单层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-010 | AsyncFor | nested-func-body | d2 双层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-011 | AsyncFor | async-func-body | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-012 | AsyncFor | function-body | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-013 | AsyncFor | comprehension-scope | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-014 | AsyncFor | loop-body | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-015 | AsyncFor | loop-else | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFOR-016 | AsyncFor | if-arm | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCWITH-003 | AsyncWith | function-body | d1 单层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-004 | AsyncWith | with-body | d1 单层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-005 | AsyncWith | if-arm | d1 单层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-007 | AsyncWith | try-body | d1 单层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-008 | AsyncWith | except-handler | d2 双层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-009 | AsyncWith | match-case-body | d1 单层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-010 | AsyncWith | nested-func-body | d2 双层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-013 | AsyncWith | function-body | d1 单层 | aw-single-item | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-014 | AsyncWith | with-body | d1 单层 | aw-single-item | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-015 | AsyncWith | with-item | d1 单层 | aw-single-item | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-016 | AsyncWith | if-arm | d1 单层 | aw-single-item | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCWITH-018 | AsyncWith | try-body | d1 单层 | aw-single-item | NEW | `test_repros/round6/r6_08_async_cross.pyc` |
| JS-ASYNCFUNC-001 | AsyncFunctionDef | function-body | d1 单层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-003 | AsyncFunctionDef | class-body | d1 单层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-004 | AsyncFunctionDef | nested-func-body | d2 双层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-005 | AsyncFunctionDef | decorator-expr | d1 单层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-006 | AsyncFunctionDef | annotation-context | d1 单层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-007 | AsyncFunctionDef | default-arg | d1 单层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-008 | AsyncFunctionDef | function-body | d1 单层 | afd-in-class | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-010 | AsyncFunctionDef | nested-func-body | d2 双层 | afd-in-class | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-013 | AsyncFunctionDef | module-level | d1 单层 | afd-nested | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-014 | AsyncFunctionDef | class-body | d1 单层 | afd-nested | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-015 | AsyncFunctionDef | nested-func-body | d2 双层 | afd-nested | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-ASYNCFUNC-016 | AsyncFunctionDef | decorator-expr | d1 单层 | afd-nested | NEW | `test_repros/round6/r6_07_async_five.pyc` |
| JS-PEP604-001 | PEP604Union | annotation-context | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-002 | PEP604Union | function-body | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-003 | PEP604Union | module-level | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-004 | PEP604Union | class-body | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-005 | PEP604Union | assign-rhs | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-006 | PEP604Union | return-value-expr | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-007 | PEP604Union | annotation-context | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-008 | PEP604Union | function-body | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-009 | PEP604Union | module-level | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-010 | PEP604Union | class-body | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-011 | PEP604Union | assign-rhs | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` |
| JS-PEP604-012 | PEP604Union | return-value-expr | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` |

## 3. 复算方式

```
python -X utf8 tools/completeness/coverage_checker.py \
    --space .trae/specs/attack-completeness-claims/rounds/round1/judgment_space.json \
    --evidence-root .trae/specs/attain-true-completeness/rounds \
    --out .trae/specs/attack-completeness-claims/rounds/round1/COVERAGE_BASELINE.md --json .trae/specs/attack-completeness-claims/rounds/round1/coverage_baseline.json
```

- 退出码：`uncovered > 0` ⇒ **1**（门禁不放行）；`--allow-uncovered` ⇒ 0。
- 索引构建：递归扫描 `--evidence-root` 下 `rec1_probes_*.json`；每条 stamp 的 `pyc_src_rel` 归一化为仓根相对路径（非 `.trae/`/`site-packages/`/`test_repros/` 开头的按规范目录前缀补齐）。
- 路径匹配：原样 → 规范目录前缀补齐 → 仅取 .pyc 基名（索引内基名唯一时生效）。

