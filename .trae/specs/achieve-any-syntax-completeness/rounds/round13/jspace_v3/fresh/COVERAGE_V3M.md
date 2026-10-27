# C1-C5 判定空间覆盖报告（Task 9.3）

> checker `2.0.0`；space `.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/judgment_space_v3m_applied.json`；J schema `v3`；evidence `.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/semantic_v3m_merged.json`。

| 读数 | 值 |
|---|---:|
| J_total | 1556 |
| covered_5tuple | 1168 |
| probe_only | 0 |
| unexecuted | 0 |
| n/a | 0 |
| inconclusive | 0 |
| excluded | 388 |
| uncovered | 388 |
| semantic_failures | 0 |
| green | 1168 |
| coverage_pct | 75.06% |
| checker_version | 2.0.0 |

口径：`covered_5tuple` 必须同时有 C1 源 hash/行数、C2 pyc hash/可加载、C3 产物 hash/命令、C4 verdict/seed/exit、C5 同一记录哈希链 + judge/runner。`probe_only`、`unexecuted`、`n/a`、`inconclusive`、`excluded`、`uncovered` 全部不计入 covered。

## 逐形态族

| form | total | covered_5tuple | probe_only | unexecuted | n/a | inconclusive | excluded | uncovered |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AnnAssign | 15 | 15 | 0 | 0 | 0 | 0 | 0 | 0 |
| Assert | 46 | 46 | 0 | 0 | 0 | 0 | 0 | 0 |
| AsyncFor | 21 | 21 | 0 | 0 | 0 | 0 | 0 | 0 |
| AsyncFunctionDef | 25 | 25 | 0 | 0 | 0 | 0 | 0 | 0 |
| AsyncWith | 24 | 24 | 0 | 0 | 0 | 0 | 0 | 0 |
| AugAssign | 63 | 50 | 0 | 0 | 0 | 0 | 13 | 0 |
| Await | 23 | 23 | 0 | 0 | 0 | 0 | 0 | 0 |
| BoolOp | 85 | 65 | 0 | 0 | 0 | 0 | 20 | 0 |
| Break | 32 | 24 | 0 | 0 | 0 | 0 | 8 | 0 |
| Continue | 35 | 24 | 0 | 0 | 0 | 0 | 11 | 0 |
| Decorator | 20 | 0 | 0 | 0 | 0 | 0 | 20 | 0 |
| Delete | 24 | 23 | 0 | 0 | 0 | 0 | 1 | 0 |
| DictComp | 23 | 20 | 0 | 0 | 0 | 0 | 3 | 0 |
| ExceptStar | 96 | 96 | 0 | 0 | 0 | 0 | 0 | 0 |
| GeneratorExp | 21 | 19 | 0 | 0 | 0 | 0 | 2 | 0 |
| Global | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 0 |
| If | 118 | 60 | 0 | 0 | 0 | 0 | 58 | 0 |
| IfExp | 28 | 26 | 0 | 0 | 0 | 0 | 2 | 0 |
| Import | 47 | 28 | 0 | 0 | 0 | 0 | 19 | 0 |
| JoinedStr | 32 | 12 | 0 | 0 | 0 | 0 | 20 | 0 |
| Lambda | 18 | 16 | 0 | 0 | 0 | 0 | 2 | 0 |
| ListComp | 40 | 26 | 0 | 0 | 0 | 0 | 14 | 0 |
| Match | 37 | 37 | 0 | 0 | 0 | 0 | 0 | 0 |
| NamedExpr | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |
| PEP604Union | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 0 |
| Raise | 39 | 34 | 0 | 0 | 0 | 0 | 5 | 0 |
| Return | 80 | 57 | 0 | 0 | 0 | 0 | 23 | 0 |
| SetComp | 17 | 17 | 0 | 0 | 0 | 0 | 0 | 0 |
| Slice | 25 | 16 | 0 | 0 | 0 | 0 | 9 | 0 |
| Starred | 21 | 17 | 0 | 0 | 0 | 0 | 4 | 0 |
| Try | 108 | 48 | 0 | 0 | 0 | 0 | 60 | 0 |
| While | 45 | 27 | 0 | 0 | 0 | 0 | 18 | 0 |
| With | 83 | 40 | 0 | 0 | 0 | 0 | 43 | 0 |
| Yield | 18 | 18 | 0 | 0 | 0 | 0 | 0 | 0 |
| augmented_assign | 49 | 31 | 0 | 0 | 0 | 0 | 18 | 0 |
| await_expr | 21 | 21 | 0 | 0 | 0 | 0 | 0 | 0 |
| global_nonlocal | 40 | 40 | 0 | 0 | 0 | 0 | 0 | 0 |
| match_statement | 60 | 60 | 0 | 0 | 0 | 0 | 0 | 0 |
| slice | 32 | 17 | 0 | 0 | 0 | 0 | 15 | 0 |

## 未覆盖/未完全覆盖条目

| id | status | reason | form | host | depth | variant |
|---|---|---|---|---|---|---|
| JS-IF-003 | excluded | entry_excluded | If | function-body | d2 双层 | if-no-else |
| JS-IF-004 | excluded | entry_excluded | If | function-body | d3plus 三层及以上 | if-no-else |
| JS-IF-006 | excluded | entry_excluded | If | if-arm | d2 双层 | if-no-else |
| JS-IF-009 | excluded | entry_excluded | If | else-arm | d2 双层 | if-no-else |
| JS-IF-010 | excluded | entry_excluded | If | else-arm | d3plus 三层及以上 | if-no-else |
| JS-IF-014 | excluded | entry_excluded | If | with-body | d2 双层 | if-no-else |
| JS-IF-015 | excluded | entry_excluded | If | with-body | d3plus 三层及以上 | if-no-else |
| JS-IF-016 | excluded | entry_excluded | If | try-body | d2 双层 | if-no-else |
| JS-IF-018 | excluded | entry_excluded | If | except-handler | d3plus 三层及以上 | if-no-else |
| JS-IF-019 | excluded | entry_excluded | If | else-of-try | d3plus 三层及以上 | if-no-else |
| JS-IF-027 | excluded | entry_excluded | If | function-body | d2 双层 | if-else-arm |
| JS-IF-028 | excluded | entry_excluded | If | function-body | d3plus 三层及以上 | if-else-arm |
| JS-IF-031 | excluded | entry_excluded | If | if-arm | d2 双层 | if-else-arm |
| JS-IF-032 | excluded | entry_excluded | If | if-arm | d3plus 三层及以上 | if-else-arm |
| JS-IF-034 | excluded | entry_excluded | If | else-arm | d2 双层 | if-else-arm |
| JS-IF-037 | excluded | entry_excluded | If | loop-body | d3plus 三层及以上 | if-else-arm |
| JS-IF-039 | excluded | entry_excluded | If | with-body | d3plus 三层及以上 | if-else-arm |
| JS-IF-040 | excluded | entry_excluded | If | try-body | d2 双层 | if-else-arm |
| JS-IF-041 | excluded | entry_excluded | If | try-body | d3plus 三层及以上 | if-else-arm |
| JS-IF-050 | excluded | entry_excluded | If | function-body | d1 单层 | if-elif-chain |
| JS-IF-051 | excluded | entry_excluded | If | function-body | d2 双层 | if-elif-chain |
| JS-IF-052 | excluded | entry_excluded | If | function-body | d3plus 三层及以上 | if-elif-chain |
| JS-IF-055 | excluded | entry_excluded | If | if-arm | d3plus 三层及以上 | if-elif-chain |
| JS-IF-057 | excluded | entry_excluded | If | else-arm | d2 双层 | if-elif-chain |
| JS-IF-058 | excluded | entry_excluded | If | else-arm | d3plus 三层及以上 | if-elif-chain |
| JS-IF-060 | excluded | entry_excluded | If | loop-body | d2 双层 | if-elif-chain |
| JS-IF-061 | excluded | entry_excluded | If | loop-body | d3plus 三层及以上 | if-elif-chain |
| JS-IF-062 | excluded | entry_excluded | If | try-body | d2 双层 | if-elif-chain |
| JS-IF-063 | excluded | entry_excluded | If | try-body | d3plus 三层及以上 | if-elif-chain |
| JS-IF-065 | excluded | entry_excluded | If | function-body | d1 单层 | if-cond-boolop |
| JS-IF-066 | excluded | entry_excluded | If | function-body | d2 双层 | if-cond-boolop |
| JS-IF-068 | excluded | entry_excluded | If | if-arm | d3plus 三层及以上 | if-cond-boolop |
| JS-IF-069 | excluded | entry_excluded | If | else-arm | d2 双层 | if-cond-boolop |
| JS-IF-070 | excluded | entry_excluded | If | else-arm | d3plus 三层及以上 | if-cond-boolop |
| JS-IF-072 | excluded | entry_excluded | If | loop-body | d3plus 三层及以上 | if-cond-boolop |
| JS-IF-073 | excluded | entry_excluded | If | with-body | d3plus 三层及以上 | if-cond-boolop |
| JS-IF-074 | excluded | entry_excluded | If | try-body | d2 双层 | if-cond-boolop |
| JS-IF-075 | excluded | entry_excluded | If | try-body | d3plus 三层及以上 | if-cond-boolop |
| JS-IF-080 | excluded | entry_excluded | If | loop-body | d3plus 三层及以上 | if-cond-compare-chain |
| JS-IF-083 | excluded | entry_excluded | If | else-arm | d3plus 三层及以上 | if-in-loop |
| JS-IF-087 | excluded | entry_excluded | If | with-body | d3plus 三层及以上 | if-in-loop |
| JS-IF-089 | excluded | entry_excluded | If | except-handler | d3plus 三层及以上 | if-in-loop |
| JS-IF-092 | excluded | entry_excluded | If | if-arm | d3plus 三层及以上 | if-in-try |
| JS-IF-093 | excluded | entry_excluded | If | else-arm | d3plus 三层及以上 | if-in-try |
| JS-IF-094 | excluded | entry_excluded | If | loop-body | d3plus 三层及以上 | if-in-try |
| JS-IF-095 | excluded | entry_excluded | If | with-body | d3plus 三层及以上 | if-in-try |
| JS-IF-096 | excluded | entry_excluded | If | try-body | d2 双层 | if-in-try |
| JS-IF-099 | excluded | entry_excluded | If | except-handler | d3plus 三层及以上 | if-in-try |
| JS-IF-100 | excluded | entry_excluded | If | else-of-try | d3plus 三层及以上 | if-in-try |
| JS-IF-103 | excluded | entry_excluded | If | if-arm | d3plus 三层及以上 | if-in-handler |
| JS-IF-104 | excluded | entry_excluded | If | else-arm | d3plus 三层及以上 | if-in-handler |
| JS-IF-105 | excluded | entry_excluded | If | loop-body | d3plus 三层及以上 | if-in-handler |
| JS-IF-107 | excluded | entry_excluded | If | except-handler | d3plus 三层及以上 | if-in-handler |
| JS-IF-108 | excluded | entry_excluded | If | if-arm | d3plus 三层及以上 | if-in-with |
| JS-IF-109 | excluded | entry_excluded | If | else-arm | d3plus 三层及以上 | if-in-with |
| JS-IF-110 | excluded | entry_excluded | If | loop-body | d3plus 三层及以上 | if-in-with |
| JS-IF-111 | excluded | entry_excluded | If | with-body | d2 双层 | if-in-with |
| JS-IF-112 | excluded | entry_excluded | If | with-body | d3plus 三层及以上 | if-in-with |
| JS-BOOLOP-004 | excluded | entry_excluded | BoolOp | else-arm | d2 双层 | boolop-and |
| JS-BOOLOP-005 | excluded | entry_excluded | BoolOp | else-arm | d3plus 三层及以上 | boolop-and |
| JS-BOOLOP-011 | excluded | entry_excluded | BoolOp | return-value-expr | d3plus 三层及以上 | boolop-and |
| JS-BOOLOP-016 | excluded | entry_excluded | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-and |
| JS-BOOLOP-024 | excluded | entry_excluded | BoolOp | else-arm | d2 双层 | boolop-or |
| JS-BOOLOP-030 | excluded | entry_excluded | BoolOp | return-value-expr | d3plus 三层及以上 | boolop-or |
| JS-BOOLOP-036 | excluded | entry_excluded | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-or |
| JS-BOOLOP-038 | excluded | entry_excluded | BoolOp | else-arm | d2 双层 | boolop-two-operands |
| JS-BOOLOP-044 | excluded | entry_excluded | BoolOp | return-value-expr | d3plus 三层及以上 | boolop-two-operands |
| JS-BOOLOP-050 | excluded | entry_excluded | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-two-operands |
| JS-BOOLOP-052 | excluded | entry_excluded | BoolOp | else-arm | d2 双层 | boolop-three-plus |
| JS-BOOLOP-053 | excluded | entry_excluded | BoolOp | else-arm | d3plus 三层及以上 | boolop-three-plus |
| JS-BOOLOP-059 | excluded | entry_excluded | BoolOp | else-arm | d3plus 三层及以上 | boolop-nested |
| JS-BOOLOP-067 | excluded | entry_excluded | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-nested |
| JS-BOOLOP-071 | excluded | entry_excluded | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-not-operand |
| JS-BOOLOP-072 | excluded | entry_excluded | BoolOp | else-arm | d2 双层 | boolop-compare-operand |
| JS-BOOLOP-073 | excluded | entry_excluded | BoolOp | else-arm | d3plus 三层及以上 | boolop-compare-operand |
| JS-BOOLOP-077 | excluded | entry_excluded | BoolOp | return-value-expr | d3plus 三层及以上 | boolop-compare-operand |
| JS-BOOLOP-080 | excluded | entry_excluded | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-compare-operand |
| JS-BOOLOP-083 | excluded | entry_excluded | BoolOp | else-arm | d2 双层 | boolop-in-if-cond |
| JS-IFEXP-018 | excluded | entry_excluded | IfExp | assign-rhs | d3plus 三层及以上 | ifexp-in-assign |
| JS-IFEXP-021 | excluded | entry_excluded | IfExp | call-arg | d3plus 三层及以上 | ifexp-in-call-arg |
| JS-TRY-002 | excluded | entry_excluded | Try | module-level | d1 单层 | try-no-handler |
| JS-TRY-006 | excluded | entry_excluded | Try | loop-body | d3plus 三层及以上 | try-no-handler |
| JS-TRY-011 | excluded | entry_excluded | Try | except-handler | d2 双层 | try-no-handler |
| JS-TRY-012 | excluded | entry_excluded | Try | else-of-try | d1 单层 | try-no-handler |
| JS-TRY-013 | excluded | entry_excluded | Try | finally-body | d1 单层 | try-no-handler |
| JS-TRY-014 | excluded | entry_excluded | Try | nested-func-body | d2 双层 | try-no-handler |
| JS-TRY-016 | excluded | entry_excluded | Try | match-case-body | d1 单层 | try-no-handler |
| JS-TRY-018 | excluded | entry_excluded | Try | function-body | d2 双层 | try-with-handler |
| JS-TRY-019 | excluded | entry_excluded | Try | function-body | d3plus 三层及以上 | try-with-handler |
| JS-TRY-020 | excluded | entry_excluded | Try | module-level | d1 单层 | try-with-handler |
| JS-TRY-021 | excluded | entry_excluded | Try | if-arm | d2 双层 | try-with-handler |
| JS-TRY-022 | excluded | entry_excluded | Try | if-arm | d3plus 三层及以上 | try-with-handler |
| JS-TRY-023 | excluded | entry_excluded | Try | loop-body | d2 双层 | try-with-handler |
| JS-TRY-024 | excluded | entry_excluded | Try | loop-body | d3plus 三层及以上 | try-with-handler |
| JS-TRY-027 | excluded | entry_excluded | Try | try-body | d3plus 三层及以上 | try-with-handler |
| JS-TRY-029 | excluded | entry_excluded | Try | except-handler | d3plus 三层及以上 | try-with-handler |
| JS-TRY-030 | excluded | entry_excluded | Try | else-of-try | d1 单层 | try-with-handler |
| JS-TRY-031 | excluded | entry_excluded | Try | finally-body | d1 单层 | try-with-handler |
| JS-TRY-032 | excluded | entry_excluded | Try | nested-func-body | d2 双层 | try-with-handler |
| JS-TRY-034 | excluded | entry_excluded | Try | match-case-body | d1 单层 | try-with-handler |
| JS-TRY-036 | excluded | entry_excluded | Try | module-level | d1 单层 | try-with-else |
| JS-TRY-037 | excluded | entry_excluded | Try | if-arm | d2 双层 | try-with-else |
| JS-TRY-038 | excluded | entry_excluded | Try | loop-body | d3plus 三层及以上 | try-with-else |
| JS-TRY-039 | excluded | entry_excluded | Try | with-body | d1 单层 | try-with-else |
| JS-TRY-040 | excluded | entry_excluded | Try | try-body | d3plus 三层及以上 | try-with-else |
| JS-TRY-043 | excluded | entry_excluded | Try | function-body | d2 双层 | try-with-finally |
| JS-TRY-044 | excluded | entry_excluded | Try | function-body | d3plus 三层及以上 | try-with-finally |
| JS-TRY-045 | excluded | entry_excluded | Try | if-arm | d2 双层 | try-with-finally |
| JS-TRY-048 | excluded | entry_excluded | Try | loop-body | d3plus 三层及以上 | try-with-finally |
| JS-TRY-055 | excluded | entry_excluded | Try | function-body | d2 双层 | try-handler-typed |
| JS-TRY-056 | excluded | entry_excluded | Try | function-body | d3plus 三层及以上 | try-handler-typed |
| JS-TRY-057 | excluded | entry_excluded | Try | module-level | d1 单层 | try-handler-typed |
| JS-TRY-058 | excluded | entry_excluded | Try | if-arm | d2 双层 | try-handler-typed |
| JS-TRY-059 | excluded | entry_excluded | Try | if-arm | d3plus 三层及以上 | try-handler-typed |
| JS-TRY-060 | excluded | entry_excluded | Try | loop-body | d2 双层 | try-handler-typed |
| JS-TRY-061 | excluded | entry_excluded | Try | loop-body | d3plus 三层及以上 | try-handler-typed |
| JS-TRY-064 | excluded | entry_excluded | Try | try-body | d3plus 三层及以上 | try-handler-typed |
| JS-TRY-066 | excluded | entry_excluded | Try | except-handler | d3plus 三层及以上 | try-handler-typed |
| JS-TRY-069 | excluded | entry_excluded | Try | function-body | d2 双层 | try-handler-as |
| JS-TRY-070 | excluded | entry_excluded | Try | function-body | d3plus 三层及以上 | try-handler-as |
| JS-TRY-071 | excluded | entry_excluded | Try | if-arm | d2 双层 | try-handler-as |
| JS-TRY-072 | excluded | entry_excluded | Try | if-arm | d3plus 三层及以上 | try-handler-as |
| JS-TRY-073 | excluded | entry_excluded | Try | loop-body | d3plus 三层及以上 | try-handler-as |
| JS-TRY-074 | excluded | entry_excluded | Try | function-body | d2 双层 | try-handler-tuple-type |
| JS-TRY-075 | excluded | entry_excluded | Try | try-body | d3plus 三层及以上 | try-handler-tuple-type |
| JS-TRY-080 | excluded | entry_excluded | Try | try-body | d3plus 三层及以上 | try-nested-in-try |
| JS-TRY-082 | excluded | entry_excluded | Try | except-handler | d3plus 三层及以上 | try-nested-in-try |
| JS-TRY-085 | excluded | entry_excluded | Try | loop-body | d3plus 三层及以上 | try-nested-in-loop |
| JS-TRY-089 | excluded | entry_excluded | Try | function-body | d2 双层 | try-in-func |
| JS-TRY-090 | excluded | entry_excluded | Try | function-body | d3plus 三层及以上 | try-in-func |
| JS-TRY-091 | excluded | entry_excluded | Try | if-arm | d2 双层 | try-in-func |
| JS-TRY-094 | excluded | entry_excluded | Try | loop-body | d3plus 三层及以上 | try-in-func |
| JS-TRY-098 | excluded | entry_excluded | Try | try-body | d3plus 三层及以上 | try-in-func |
| JS-TRY-100 | excluded | entry_excluded | Try | except-handler | d3plus 三层及以上 | try-in-func |
| JS-TRY-101 | excluded | entry_excluded | Try | function-body | d2 双层 | try-in-class-body |
| JS-TRY-102 | excluded | entry_excluded | Try | function-body | d3plus 三层及以上 | try-in-class-body |
| JS-TRY-103 | excluded | entry_excluded | Try | if-arm | d3plus 三层及以上 | try-in-class-body |
| JS-TRY-104 | excluded | entry_excluded | Try | loop-body | d3plus 三层及以上 | try-in-class-body |
| JS-TRY-106 | excluded | entry_excluded | Try | try-body | d3plus 三层及以上 | try-in-class-body |
| JS-TRY-107 | excluded | entry_excluded | Try | except-handler | d3plus 三层及以上 | try-in-class-body |
| JS-RAISE-013 | excluded | entry_excluded | Raise | function-body | d2 双层 | raise-exc-call |
| JS-RAISE-015 | excluded | entry_excluded | Raise | if-arm | d2 双层 | raise-exc-call |
| JS-RAISE-024 | excluded | entry_excluded | Raise | function-body | d2 双层 | raise-exc-class |
| JS-RAISE-027 | excluded | entry_excluded | Raise | except-handler | d2 双层 | raise-exc-class |
| JS-RAISE-031 | excluded | entry_excluded | Raise | except-handler | d2 双层 | raise-in-handler |
| JS-IMPORT-001 | excluded | entry_excluded | Import | module-level | d1 单层 | import-plain |
| JS-IMPORT-004 | excluded | entry_excluded | Import | try-body | d1 单层 | import-plain |
| JS-IMPORT-005 | excluded | entry_excluded | Import | except-handler | d1 单层 | import-plain |
| JS-IMPORT-006 | excluded | entry_excluded | Import | except-handler | d2 双层 | import-plain |
| JS-IMPORT-007 | excluded | entry_excluded | Import | except-handler | d3plus 三层及以上 | import-plain |
| JS-IMPORT-015 | excluded | entry_excluded | Import | module-level | d1 单层 | import-as |
| JS-IMPORT-018 | excluded | entry_excluded | Import | try-body | d1 单层 | import-as |
| JS-IMPORT-021 | excluded | entry_excluded | Import | module-level | d1 单层 | import-from |
| JS-IMPORT-022 | excluded | entry_excluded | Import | function-body | d1 单层 | import-from |
| JS-IMPORT-025 | excluded | entry_excluded | Import | except-handler | d3plus 三层及以上 | import-from |
| JS-IMPORT-028 | excluded | entry_excluded | Import | if-arm | d3plus 三层及以上 | import-from |
| JS-IMPORT-029 | excluded | entry_excluded | Import | module-level | d1 单层 | import-from-as |
| JS-IMPORT-032 | excluded | entry_excluded | Import | try-body | d1 单层 | import-in-try |
| JS-IMPORT-034 | excluded | entry_excluded | Import | except-handler | d1 单层 | import-in-handler |
| JS-IMPORT-036 | excluded | entry_excluded | Import | except-handler | d3plus 三层及以上 | import-in-handler |
| JS-IMPORT-039 | excluded | entry_excluded | Import | function-body | d1 单层 | import-in-func |
| JS-IMPORT-042 | excluded | entry_excluded | Import | except-handler | d3plus 三层及以上 | import-in-func |
| JS-IMPORT-045 | excluded | entry_excluded | Import | if-arm | d3plus 三层及以上 | import-in-func |
| JS-IMPORT-047 | excluded | entry_excluded | Import | if-arm | d3plus 三层及以上 | import-in-class-body |
| JS-LISTCOMP-003 | excluded | entry_excluded | ListComp | assign-rhs | d1 单层 | listcomp-single-for |
| JS-LISTCOMP-004 | excluded | entry_excluded | ListComp | assign-rhs | d2 双层 | listcomp-single-for |
| JS-LISTCOMP-005 | excluded | entry_excluded | ListComp | assign-rhs | d3plus 三层及以上 | listcomp-single-for |
| JS-LISTCOMP-008 | excluded | entry_excluded | ListComp | return-value-expr | d3plus 三层及以上 | listcomp-single-for |
| JS-LISTCOMP-009 | excluded | entry_excluded | ListComp | call-arg | d1 单层 | listcomp-single-for |
| JS-LISTCOMP-010 | excluded | entry_excluded | ListComp | call-arg | d2 双层 | listcomp-single-for |
| JS-LISTCOMP-011 | excluded | entry_excluded | ListComp | call-arg | d3plus 三层及以上 | listcomp-single-for |
| JS-LISTCOMP-032 | excluded | entry_excluded | ListComp | call-arg | d1 单层 | listcomp-in-call-arg |
| JS-LISTCOMP-033 | excluded | entry_excluded | ListComp | call-arg | d2 双层 | listcomp-in-call-arg |
| JS-LISTCOMP-034 | excluded | entry_excluded | ListComp | call-arg | d3plus 三层及以上 | listcomp-in-call-arg |
| JS-LISTCOMP-035 | excluded | entry_excluded | ListComp | assign-rhs | d1 单层 | listcomp-in-assign |
| JS-LISTCOMP-036 | excluded | entry_excluded | ListComp | assign-rhs | d2 双层 | listcomp-in-assign |
| JS-LISTCOMP-037 | excluded | entry_excluded | ListComp | assign-rhs | d3plus 三层及以上 | listcomp-in-assign |
| JS-LISTCOMP-040 | excluded | entry_excluded | ListComp | return-value-expr | d3plus 三层及以上 | listcomp-in-return |
| JS-WITH-001 | excluded | entry_excluded | With | function-body | d1 单层 | with-single-item |
| JS-WITH-002 | excluded | entry_excluded | With | function-body | d2 双层 | with-single-item |
| JS-WITH-004 | excluded | entry_excluded | With | if-arm | d2 双层 | with-single-item |
| JS-WITH-005 | excluded | entry_excluded | With | if-arm | d3plus 三层及以上 | with-single-item |
| JS-WITH-007 | excluded | entry_excluded | With | loop-body | d3plus 三层及以上 | with-single-item |
| JS-WITH-008 | excluded | entry_excluded | With | try-body | d2 双层 | with-single-item |
| JS-WITH-009 | excluded | entry_excluded | With | try-body | d3plus 三层及以上 | with-single-item |
| JS-WITH-011 | excluded | entry_excluded | With | with-body | d3plus 三层及以上 | with-single-item |
| JS-WITH-016 | excluded | entry_excluded | With | else-arm | d3plus 三层及以上 | with-single-item |
| JS-WITH-028 | excluded | entry_excluded | With | function-body | d1 单层 | with-as-target |
| JS-WITH-029 | excluded | entry_excluded | With | function-body | d2 双层 | with-as-target |
| JS-WITH-031 | excluded | entry_excluded | With | if-arm | d2 双层 | with-as-target |
| JS-WITH-032 | excluded | entry_excluded | With | if-arm | d3plus 三层及以上 | with-as-target |
| JS-WITH-035 | excluded | entry_excluded | With | try-body | d2 双层 | with-as-target |
| JS-WITH-036 | excluded | entry_excluded | With | try-body | d3plus 三层及以上 | with-as-target |
| JS-WITH-037 | excluded | entry_excluded | With | with-body | d3plus 三层及以上 | with-as-target |
| JS-WITH-040 | excluded | entry_excluded | With | else-arm | d3plus 三层及以上 | with-as-target |
| JS-WITH-041 | excluded | entry_excluded | With | if-arm | d3plus 三层及以上 | with-in-try |
| JS-WITH-042 | excluded | entry_excluded | With | try-body | d2 双层 | with-in-try |
| JS-WITH-043 | excluded | entry_excluded | With | try-body | d3plus 三层及以上 | with-in-try |
| JS-WITH-045 | excluded | entry_excluded | With | with-body | d3plus 三层及以上 | with-in-try |
| JS-WITH-046 | excluded | entry_excluded | With | if-arm | d3plus 三层及以上 | with-in-loop |
| JS-WITH-048 | excluded | entry_excluded | With | loop-body | d3plus 三层及以上 | with-in-loop |
| JS-WITH-049 | excluded | entry_excluded | With | try-body | d3plus 三层及以上 | with-in-loop |
| JS-WITH-050 | excluded | entry_excluded | With | function-body | d1 单层 | with-in-func |
| JS-WITH-051 | excluded | entry_excluded | With | function-body | d2 双层 | with-in-func |
| JS-WITH-052 | excluded | entry_excluded | With | if-arm | d2 双层 | with-in-func |
| JS-WITH-053 | excluded | entry_excluded | With | if-arm | d3plus 三层及以上 | with-in-func |
| JS-WITH-055 | excluded | entry_excluded | With | loop-body | d3plus 三层及以上 | with-in-func |
| JS-WITH-056 | excluded | entry_excluded | With | try-body | d2 双层 | with-in-func |
| JS-WITH-057 | excluded | entry_excluded | With | try-body | d3plus 三层及以上 | with-in-func |
| JS-WITH-059 | excluded | entry_excluded | With | with-body | d3plus 三层及以上 | with-in-func |
| JS-WITH-062 | excluded | entry_excluded | With | else-arm | d3plus 三层及以上 | with-in-func |
| JS-WITH-063 | excluded | entry_excluded | With | if-arm | d3plus 三层及以上 | with-body-nested-with |
| JS-WITH-066 | excluded | entry_excluded | With | with-body | d3plus 三层及以上 | with-body-nested-with |
| JS-WITH-071 | excluded | entry_excluded | With | function-body | d1 单层 | with-item-call |
| JS-WITH-072 | excluded | entry_excluded | With | function-body | d2 双层 | with-item-call |
| JS-WITH-073 | excluded | entry_excluded | With | if-arm | d2 双层 | with-item-call |
| JS-WITH-074 | excluded | entry_excluded | With | if-arm | d3plus 三层及以上 | with-item-call |
| JS-WITH-077 | excluded | entry_excluded | With | try-body | d2 双层 | with-item-call |
| JS-WITH-078 | excluded | entry_excluded | With | try-body | d3plus 三层及以上 | with-item-call |
| JS-WITH-080 | excluded | entry_excluded | With | with-body | d3plus 三层及以上 | with-item-call |
| JS-WITH-083 | excluded | entry_excluded | With | else-arm | d3plus 三层及以上 | with-item-call |
| JS-BREAK-008 | excluded | entry_excluded | Break | if-arm | d3plus 三层及以上 | break-in-for |
| JS-BREAK-016 | excluded | entry_excluded | Break | with-body | d3plus 三层及以上 | break-in-while |
| JS-BREAK-018 | excluded | entry_excluded | Break | if-arm | d3plus 三层及以上 | break-in-while |
| JS-BREAK-021 | excluded | entry_excluded | Break | with-body | d3plus 三层及以上 | break-in-with |
| JS-BREAK-025 | excluded | entry_excluded | Break | with-body | d3plus 三层及以上 | break-in-if-arm |
| JS-BREAK-026 | excluded | entry_excluded | Break | if-arm | d3plus 三层及以上 | break-in-if-arm |
| JS-BREAK-029 | excluded | entry_excluded | Break | if-arm | d3plus 三层及以上 | break-target-outer |
| JS-BREAK-032 | excluded | entry_excluded | Break | if-arm | d3plus 三层及以上 | break-in-nested-loop |
| JS-CONTINUE-001 | excluded | entry_excluded | Continue | loop-body | d2 双层 | continue-in-for |
| JS-CONTINUE-002 | excluded | entry_excluded | Continue | loop-body | d3plus 三层及以上 | continue-in-for |
| JS-CONTINUE-014 | excluded | entry_excluded | Continue | loop-body | d3plus 三层及以上 | continue-in-while |
| JS-CONTINUE-021 | excluded | entry_excluded | Continue | if-arm | d3plus 三层及以上 | continue-in-while |
| JS-CONTINUE-023 | excluded | entry_excluded | Continue | loop-body | d3plus 三层及以上 | continue-in-with |
| JS-CONTINUE-024 | excluded | entry_excluded | Continue | if-arm | d3plus 三层及以上 | continue-in-with |
| JS-CONTINUE-026 | excluded | entry_excluded | Continue | loop-body | d3plus 三层及以上 | continue-in-if-arm |
| JS-CONTINUE-030 | excluded | entry_excluded | Continue | loop-body | d3plus 三层及以上 | continue-target-outer |
| JS-CONTINUE-032 | excluded | entry_excluded | Continue | if-arm | d3plus 三层及以上 | continue-target-outer |
| JS-CONTINUE-033 | excluded | entry_excluded | Continue | loop-body | d3plus 三层及以上 | continue-in-nested-loop |
| JS-CONTINUE-035 | excluded | entry_excluded | Continue | if-arm | d3plus 三层及以上 | continue-in-nested-loop |
| JS-WHILE-002 | excluded | entry_excluded | While | function-body | d1 单层 | while-true |
| JS-WHILE-003 | excluded | entry_excluded | While | function-body | d2 双层 | while-true |
| JS-WHILE-019 | excluded | entry_excluded | While | if-arm | d3plus 三层及以上 | while-cond-boolop |
| JS-WHILE-020 | excluded | entry_excluded | While | loop-body | d3plus 三层及以上 | while-cond-boolop |
| JS-WHILE-021 | excluded | entry_excluded | While | else-arm | d3plus 三层及以上 | while-cond-boolop |
| JS-WHILE-023 | excluded | entry_excluded | While | loop-body | d3plus 三层及以上 | while-cond-compare-chain |
| JS-WHILE-027 | excluded | entry_excluded | While | function-body | d2 双层 | while-in-func |
| JS-WHILE-028 | excluded | entry_excluded | While | if-arm | d2 双层 | while-in-func |
| JS-WHILE-029 | excluded | entry_excluded | While | if-arm | d3plus 三层及以上 | while-in-func |
| JS-WHILE-030 | excluded | entry_excluded | While | loop-body | d2 双层 | while-in-func |
| JS-WHILE-031 | excluded | entry_excluded | While | loop-body | d3plus 三层及以上 | while-in-func |
| JS-WHILE-033 | excluded | entry_excluded | While | try-body | d3plus 三层及以上 | while-in-func |
| JS-WHILE-036 | excluded | entry_excluded | While | else-arm | d2 双层 | while-in-func |
| JS-WHILE-037 | excluded | entry_excluded | While | else-arm | d3plus 三层及以上 | while-in-func |
| JS-WHILE-039 | excluded | entry_excluded | While | try-body | d3plus 三层及以上 | while-in-try |
| JS-WHILE-043 | excluded | entry_excluded | While | function-body | d2 双层 | while-body-nested-loop |
| JS-WHILE-044 | excluded | entry_excluded | While | loop-body | d3plus 三层及以上 | while-body-nested-loop |
| JS-WHILE-045 | excluded | entry_excluded | While | else-arm | d3plus 三层及以上 | while-body-nested-loop |
| JS-DELETE-012 | excluded | entry_excluded | Delete | function-body | d1 单层 | del-subscript |
| JS-AUGASSIGN-003 | excluded | entry_excluded | AugAssign | if-arm | d2 双层 | aug-op-add |
| JS-AUGASSIGN-004 | excluded | entry_excluded | AugAssign | if-arm | d3plus 三层及以上 | aug-op-add |
| JS-AUGASSIGN-005 | excluded | entry_excluded | AugAssign | else-arm | d3plus 三层及以上 | aug-op-add |
| JS-AUGASSIGN-007 | excluded | entry_excluded | AugAssign | loop-body | d2 双层 | aug-op-add |
| JS-AUGASSIGN-008 | excluded | entry_excluded | AugAssign | loop-body | d3plus 三层及以上 | aug-op-add |
| JS-AUGASSIGN-010 | excluded | entry_excluded | AugAssign | except-handler | d3plus 三层及以上 | aug-op-add |
| JS-AUGASSIGN-018 | excluded | entry_excluded | AugAssign | if-arm | d2 双层 | aug-op-sub |
| JS-AUGASSIGN-019 | excluded | entry_excluded | AugAssign | if-arm | d3plus 三层及以上 | aug-op-sub |
| JS-AUGASSIGN-047 | excluded | entry_excluded | AugAssign | if-arm | d2 双层 | aug-target-name |
| JS-AUGASSIGN-048 | excluded | entry_excluded | AugAssign | if-arm | d3plus 三层及以上 | aug-target-name |
| JS-AUGASSIGN-049 | excluded | entry_excluded | AugAssign | else-arm | d3plus 三层及以上 | aug-target-name |
| JS-AUGASSIGN-052 | excluded | entry_excluded | AugAssign | loop-body | d3plus 三层及以上 | aug-target-name |
| JS-AUGASSIGN-054 | excluded | entry_excluded | AugAssign | except-handler | d3plus 三层及以上 | aug-target-name |
| JS-RETURN-015 | excluded | entry_excluded | Return | function-body | d3plus 三层及以上 | return-value |
| JS-RETURN-020 | excluded | entry_excluded | Return | loop-body | d2 双层 | return-value |
| JS-RETURN-022 | excluded | entry_excluded | Return | try-body | d3plus 三层及以上 | return-value |
| JS-RETURN-024 | excluded | entry_excluded | Return | except-handler | d3plus 三层及以上 | return-value |
| JS-RETURN-026 | excluded | entry_excluded | Return | with-body | d3plus 三层及以上 | return-value |
| JS-RETURN-035 | excluded | entry_excluded | Return | function-body | d1 单层 | return-tuple |
| JS-RETURN-037 | excluded | entry_excluded | Return | if-arm | d2 双层 | return-tuple |
| JS-RETURN-038 | excluded | entry_excluded | Return | if-arm | d3plus 三层及以上 | return-tuple |
| JS-RETURN-039 | excluded | entry_excluded | Return | else-arm | d2 双层 | return-tuple |
| JS-RETURN-040 | excluded | entry_excluded | Return | else-arm | d3plus 三层及以上 | return-tuple |
| JS-RETURN-041 | excluded | entry_excluded | Return | try-body | d3plus 三层及以上 | return-tuple |
| JS-RETURN-042 | excluded | entry_excluded | Return | except-handler | d2 双层 | return-tuple |
| JS-RETURN-043 | excluded | entry_excluded | Return | except-handler | d3plus 三层及以上 | return-tuple |
| JS-RETURN-049 | excluded | entry_excluded | Return | function-body | d3plus 三层及以上 | return-boolop |
| JS-RETURN-051 | excluded | entry_excluded | Return | if-arm | d3plus 三层及以上 | return-boolop |
| JS-RETURN-053 | excluded | entry_excluded | Return | else-arm | d3plus 三层及以上 | return-boolop |
| JS-RETURN-060 | excluded | entry_excluded | Return | try-body | d3plus 三层及以上 | return-in-try-body |
| JS-RETURN-065 | excluded | entry_excluded | Return | except-handler | d3plus 三层及以上 | return-in-handler |
| JS-RETURN-067 | excluded | entry_excluded | Return | else-arm | d3plus 三层及以上 | return-in-loop |
| JS-RETURN-068 | excluded | entry_excluded | Return | loop-body | d2 双层 | return-in-loop |
| JS-RETURN-069 | excluded | entry_excluded | Return | except-handler | d3plus 三层及以上 | return-in-loop |
| JS-RETURN-071 | excluded | entry_excluded | Return | if-arm | d3plus 三层及以上 | return-in-with |
| JS-RETURN-074 | excluded | entry_excluded | Return | with-body | d3plus 三层及以上 | return-in-with |
| JS-SLICE-001 | excluded | entry_excluded | Slice | subscript-index | d1 单层 | slice-plain |
| JS-SLICE-002 | excluded | entry_excluded | Slice | subscript-index | d2 双层 | slice-plain |
| JS-SLICE-003 | excluded | entry_excluded | Slice | subscript-index | d3plus 三层及以上 | slice-plain |
| JS-SLICE-017 | excluded | entry_excluded | Slice | subscript-index | d1 单层 | slice-neg-bound |
| JS-SLICE-018 | excluded | entry_excluded | Slice | subscript-index | d3plus 三层及以上 | slice-neg-bound |
| JS-SLICE-019 | excluded | entry_excluded | Slice | subscript-index | d3plus 三层及以上 | slice-expr-bound |
| JS-SLICE-023 | excluded | entry_excluded | Slice | subscript-index | d1 单层 | slice-in-assign-target |
| JS-SLICE-024 | excluded | entry_excluded | Slice | subscript-index | d2 双层 | slice-in-assign-target |
| JS-SLICE-025 | excluded | entry_excluded | Slice | subscript-index | d3plus 三层及以上 | slice-in-assign-target |
| JS-AUGFORM-003 | excluded | entry_excluded | augmented_assign | if-arm | d2 双层 | augform-target-name |
| JS-AUGFORM-004 | excluded | entry_excluded | augmented_assign | if-arm | d3plus 三层及以上 | augform-target-name |
| JS-AUGFORM-005 | excluded | entry_excluded | augmented_assign | else-arm | d3plus 三层及以上 | augform-target-name |
| JS-AUGFORM-008 | excluded | entry_excluded | augmented_assign | loop-body | d3plus 三层及以上 | augform-target-name |
| JS-AUGFORM-010 | excluded | entry_excluded | augmented_assign | except-handler | d3plus 三层及以上 | augform-target-name |
| JS-AUGFORM-027 | excluded | entry_excluded | augmented_assign | if-arm | d2 双层 | augform-in-if-arm |
| JS-AUGFORM-028 | excluded | entry_excluded | augmented_assign | if-arm | d3plus 三层及以上 | augform-in-if-arm |
| JS-AUGFORM-029 | excluded | entry_excluded | augmented_assign | else-arm | d3plus 三层及以上 | augform-in-if-arm |
| JS-AUGFORM-030 | excluded | entry_excluded | augmented_assign | loop-body | d3plus 三层及以上 | augform-in-if-arm |
| JS-AUGFORM-032 | excluded | entry_excluded | augmented_assign | except-handler | d3plus 三层及以上 | augform-in-if-arm |
| JS-AUGFORM-034 | excluded | entry_excluded | augmented_assign | if-arm | d3plus 三层及以上 | augform-in-loop-body |
| JS-AUGFORM-035 | excluded | entry_excluded | augmented_assign | else-arm | d3plus 三层及以上 | augform-in-loop-body |
| JS-AUGFORM-038 | excluded | entry_excluded | augmented_assign | loop-body | d3plus 三层及以上 | augform-in-loop-body |
| JS-AUGFORM-040 | excluded | entry_excluded | augmented_assign | except-handler | d3plus 三层及以上 | augform-in-loop-body |
| JS-AUGFORM-043 | excluded | entry_excluded | augmented_assign | loop-body | d3plus 三层及以上 | augform-in-handler |
| JS-AUGFORM-045 | excluded | entry_excluded | augmented_assign | except-handler | d3plus 三层及以上 | augform-in-handler |
| JS-AUGFORM-047 | excluded | entry_excluded | augmented_assign | if-arm | d3plus 三层及以上 | augform-in-class-body |
| JS-AUGFORM-048 | excluded | entry_excluded | augmented_assign | loop-body | d3plus 三层及以上 | augform-in-class-body |
| JS-SLICEFORM-001 | excluded | entry_excluded | slice | subscript-index | d1 单层 | sliceform-in-subscript |
| JS-SLICEFORM-002 | excluded | entry_excluded | slice | subscript-index | d2 双层 | sliceform-in-subscript |
| JS-SLICEFORM-003 | excluded | entry_excluded | slice | subscript-index | d3plus 三层及以上 | sliceform-in-subscript |
| JS-SLICEFORM-017 | excluded | entry_excluded | slice | subscript-index | d1 单层 | sliceform-in-assign-target |
| JS-SLICEFORM-018 | excluded | entry_excluded | slice | subscript-index | d2 双层 | sliceform-in-assign-target |
| JS-SLICEFORM-019 | excluded | entry_excluded | slice | subscript-index | d3plus 三层及以上 | sliceform-in-assign-target |
| JS-SLICEFORM-020 | excluded | entry_excluded | slice | subscript-index | d1 单层 | sliceform-nested-subscript |
| JS-SLICEFORM-021 | excluded | entry_excluded | slice | subscript-index | d2 双层 | sliceform-nested-subscript |
| JS-SLICEFORM-022 | excluded | entry_excluded | slice | subscript-index | d3plus 三层及以上 | sliceform-nested-subscript |
| JS-SLICEFORM-025 | excluded | entry_excluded | slice | subscript-index | d1 单层 | sliceform-single-bound |
| JS-SLICEFORM-026 | excluded | entry_excluded | slice | subscript-index | d2 双层 | sliceform-single-bound |
| JS-SLICEFORM-027 | excluded | entry_excluded | slice | subscript-index | d3plus 三层及以上 | sliceform-single-bound |
| JS-SLICEFORM-028 | excluded | entry_excluded | slice | subscript-index | d1 单层 | sliceform-in-call-arg |
| JS-SLICEFORM-029 | excluded | entry_excluded | slice | subscript-index | d3plus 三层及以上 | sliceform-in-call-arg |
| JS-SLICEFORM-031 | excluded | entry_excluded | slice | subscript-index | d2 双层 | sliceform-in-return |
| JS-LAMBDA-015 | excluded | entry_excluded | Lambda | call-arg | d3plus 三层及以上 | lambda-as-call-arg |
| JS-LAMBDA-016 | excluded | entry_excluded | Lambda | return-value-expr | d2 双层 | lambda-in-return |
| JS-DECORATOR-001 | excluded | entry_excluded | Decorator | decorator-expr | d1 单层 | deco-on-function |
| JS-DECORATOR-002 | excluded | entry_excluded | Decorator | function-body | d1 单层 | deco-on-function |
| JS-DECORATOR-003 | excluded | entry_excluded | Decorator | class-body | d1 单层 | deco-on-function |
| JS-DECORATOR-004 | excluded | entry_excluded | Decorator | module-level | d1 单层 | deco-on-function |
| JS-DECORATOR-005 | excluded | entry_excluded | Decorator | call-arg | d1 单层 | deco-on-function |
| JS-DECORATOR-006 | excluded | entry_excluded | Decorator | decorator-expr | d1 单层 | deco-on-class |
| JS-DECORATOR-007 | excluded | entry_excluded | Decorator | function-body | d1 单层 | deco-on-class |
| JS-DECORATOR-008 | excluded | entry_excluded | Decorator | class-body | d1 单层 | deco-on-class |
| JS-DECORATOR-009 | excluded | entry_excluded | Decorator | module-level | d1 单层 | deco-on-class |
| JS-DECORATOR-010 | excluded | entry_excluded | Decorator | call-arg | d1 单层 | deco-on-class |
| JS-DECORATOR-011 | excluded | entry_excluded | Decorator | decorator-expr | d1 单层 | deco-single |
| JS-DECORATOR-012 | excluded | entry_excluded | Decorator | function-body | d1 单层 | deco-single |
| JS-DECORATOR-013 | excluded | entry_excluded | Decorator | class-body | d1 单层 | deco-single |
| JS-DECORATOR-014 | excluded | entry_excluded | Decorator | module-level | d1 单层 | deco-single |
| JS-DECORATOR-015 | excluded | entry_excluded | Decorator | call-arg | d1 单层 | deco-single |
| JS-DECORATOR-016 | excluded | entry_excluded | Decorator | decorator-expr | d1 单层 | deco-stack |
| JS-DECORATOR-017 | excluded | entry_excluded | Decorator | class-body | d1 单层 | deco-stack |
| JS-DECORATOR-018 | excluded | entry_excluded | Decorator | class-body | d1 单层 | deco-with-args |
| JS-DECORATOR-019 | excluded | entry_excluded | Decorator | module-level | d1 单层 | deco-with-args |
| JS-DECORATOR-020 | excluded | entry_excluded | Decorator | class-body | d1 单层 | deco-name-form |
| JS-DICTCOMP-003 | excluded | entry_excluded | DictComp | assign-rhs | d2 双层 | dictcomp-single-for |
| JS-DICTCOMP-018 | excluded | entry_excluded | DictComp | assign-rhs | d2 双层 | dictcomp-value-ternary |
| JS-DICTCOMP-023 | excluded | entry_excluded | DictComp | assign-rhs | d2 双层 | dictcomp-in-assign |
| JS-GENEXP-007 | excluded | entry_excluded | GeneratorExp | call-arg | d3plus 三层及以上 | genexp-single-for |
| JS-GENEXP-020 | excluded | entry_excluded | GeneratorExp | call-arg | d3plus 三层及以上 | genexp-in-call-arg |
| JS-FSTRING-013 | excluded | entry_excluded | JoinedStr | assign-rhs | d1 单层 | fstring-with-var |
| JS-FSTRING-014 | excluded | entry_excluded | JoinedStr | assign-rhs | d2 双层 | fstring-with-var |
| JS-FSTRING-015 | excluded | entry_excluded | JoinedStr | assign-rhs | d3plus 三层及以上 | fstring-with-var |
| JS-FSTRING-016 | excluded | entry_excluded | JoinedStr | call-arg | d2 双层 | fstring-with-var |
| JS-FSTRING-017 | excluded | entry_excluded | JoinedStr | call-arg | d3plus 三层及以上 | fstring-with-var |
| JS-FSTRING-018 | excluded | entry_excluded | JoinedStr | assign-rhs | d1 单层 | fstring-with-conversion |
| JS-FSTRING-019 | excluded | entry_excluded | JoinedStr | assign-rhs | d2 双层 | fstring-with-conversion |
| JS-FSTRING-020 | excluded | entry_excluded | JoinedStr | assign-rhs | d3plus 三层及以上 | fstring-with-conversion |
| JS-FSTRING-021 | excluded | entry_excluded | JoinedStr | call-arg | d2 双层 | fstring-with-conversion |
| JS-FSTRING-022 | excluded | entry_excluded | JoinedStr | call-arg | d3plus 三层及以上 | fstring-with-conversion |
| JS-FSTRING-023 | excluded | entry_excluded | JoinedStr | assign-rhs | d1 单层 | fstring-embedded-expr |
| JS-FSTRING-024 | excluded | entry_excluded | JoinedStr | assign-rhs | d2 双层 | fstring-embedded-expr |
| JS-FSTRING-025 | excluded | entry_excluded | JoinedStr | assign-rhs | d3plus 三层及以上 | fstring-embedded-expr |
| JS-FSTRING-026 | excluded | entry_excluded | JoinedStr | call-arg | d2 双层 | fstring-embedded-expr |
| JS-FSTRING-027 | excluded | entry_excluded | JoinedStr | call-arg | d3plus 三层及以上 | fstring-embedded-expr |
| JS-FSTRING-028 | excluded | entry_excluded | JoinedStr | call-arg | d2 双层 | fstring-in-call-arg |
| JS-FSTRING-029 | excluded | entry_excluded | JoinedStr | call-arg | d3plus 三层及以上 | fstring-in-call-arg |
| JS-FSTRING-030 | excluded | entry_excluded | JoinedStr | assign-rhs | d1 单层 | fstring-in-assign |
| JS-FSTRING-031 | excluded | entry_excluded | JoinedStr | assign-rhs | d2 双层 | fstring-in-assign |
| JS-FSTRING-032 | excluded | entry_excluded | JoinedStr | assign-rhs | d3plus 三层及以上 | fstring-in-assign |
| JS-STARRED-003 | excluded | entry_excluded | Starred | call-arg | d2 双层 | starred-in-call |
| JS-STARRED-004 | excluded | entry_excluded | Starred | call-arg | d3plus 三层及以上 | starred-in-call |
| JS-STARRED-019 | excluded | entry_excluded | Starred | call-arg | d2 双层 | starred-in-assign |
| JS-STARRED-020 | excluded | entry_excluded | Starred | call-arg | d3plus 三层及以上 | starred-in-assign |

## 复算

```
python -X utf8 tools/completeness/coverage_checker.py \
  --space .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/judgment_space_v3m_applied.json --evidence .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/semantic_v3m_merged.json --json .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/coverage_v3m.json
```
