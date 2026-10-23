# 判定空间（Judgment Space）— attack-completeness-claims / Task 1

> 目的：把上一规范「完备 128 / 破口 0 / 零能力 0 = 100%」补上可证伪性——「完备」在此被重写为**有限可枚举的判定空间**（形态 × 宿主 × 深度 × 变体）的**全覆盖**。
> 生成器：`tools/completeness/jspace_generator.py`（本表与 `judgment_space.json` 同源、可重生成）。
> 机读清单：`rounds/round1/judgment_space.json`；覆盖检查器：`tools/completeness/coverage_checker.py`；首跑基线：`rounds/round1/COVERAGE_BASELINE.md`。

> J schema v2 note: each entry now carries p_j/p_j_sha256/p_j_lines, pyc/pyc_sha256, expected_label, input_model and excluded. The `covered` field below is the legacy probe-observation status, NOT C1-C5 coverage. Use `coverage_checker.py` and `COVERAGE_C1C5.md` for covered_5tuple/probe_only/unexecuted counts.

## 0. 规模读数（本文件由生成器写出，数字与 JSON 逐项一致）

| 项 | 值 |
|---|---|
| 条目总数 | **1556** |
| 形态族数 | 39（25 行 25 + NEW 14） |
| 形态维度取值数 | 39 |
| 宿主维度取值数 | 48 |
| 深度维度取值数 | 3 |
| 变体维度取值数 | 408 |
| 其中已落到条目上的变体取值数 | 299 |
| 声明 covered（有专属见证探针） | 976 |
| 声明 uncovered | 580 |
| 其中见证探针曾判定为 success | 921 |
| 证据索引内探针路径数 | 103 |
| 可构造 (form,variant,host) 三元组总数 | 4229 |
| 其中已有观测的 | 671 |
| 其中无观测的 | 3558 |

## 1. 四个维度的定义

### 1.1 形态（form）— 文法族

形态 = **文法族**（不是 ast 节点名）。25 行沿用上一规范的行名（`REVIEW.md:19`）；其余为本规范新增（NEW），每族给出代码站点 file:line 作为「该形态在产品内被识别」的依据。

| form | 归属行 | 依据（source） | 条目数 | covered | uncovered |
|---|---|---|---|---|---|
| If | If | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:28` | 118 | 106 | 12 |
| BoolOp | BoolOp | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:29` | 85 | 73 | 12 |
| IfExp | IfExp | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:30` | 28 | 16 | 12 |
| Try | Try | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:31` | 108 | 96 | 12 |
| Raise | Raise | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:32` | 39 | 27 | 12 |
| Assert | Assert | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:33` | 46 | 34 | 12 |
| Import | Import | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:34` | 47 | 35 | 12 |
| Global | Global | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:35` | 19 | 7 | 12 |
| global_nonlocal | global_nonlocal | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:36` | 40 | 0 | 40 |
| Await | Await | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:37` | 23 | 11 | 12 |
| ListComp | ListComp | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:38` | 40 | 28 | 12 |
| await_expr | await_expr | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:39` | 21 | 9 | 12 |
| Yield | Yield | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:40` | 18 | 6 | 12 |
| Match | Match | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:41` | 37 | 25 | 12 |
| With | With | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:42` | 83 | 71 | 12 |
| match_statement | match_statement | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:43` | 60 | 48 | 12 |
| Break | Break | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:44` | 32 | 20 | 12 |
| Continue | Continue | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:45` | 35 | 23 | 12 |
| While | While | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:46` | 45 | 33 | 12 |
| Delete | Delete | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:47` | 24 | 12 | 12 |
| AugAssign | AugAssign | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:48` | 63 | 51 | 12 |
| Return | Return | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:49` | 80 | 68 | 12 |
| Slice | Slice | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:50` | 25 | 13 | 12 |
| augmented_assign | augmented_assign | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:51` | 49 | 37 | 12 |
| slice | slice | `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:52` | 32 | 20 | 12 |
| Lambda | NEW | `core/cfg/ast_converter.py:110` | 18 | 6 | 12 |
| Decorator | NEW | `core/cfg/ast_converter.py:297` | 20 | 8 | 12 |
| SetComp | NEW | `core/cfg/ast_converter.py:104` | 17 | 5 | 12 |
| DictComp | NEW | `core/cfg/ast_converter.py:105` | 23 | 11 | 12 |
| GeneratorExp | NEW | `core/cfg/ast_converter.py:106` | 21 | 9 | 12 |
| NamedExpr | NEW | `core/cfg/ast_converter.py:107` | 14 | 2 | 12 |
| JoinedStr | NEW | `core/cfg/ast_converter.py:930` | 32 | 20 | 12 |
| Starred | NEW | `core/cfg/ast_converter.py:957` | 21 | 9 | 12 |
| ExceptStar | NEW | `core/cfg/region_ast_generator.py:9707` | 96 | 0 | 96 |
| AnnAssign | NEW | `core/cfg/ast_converter.py:76` | 15 | 3 | 12 |
| AsyncFor | NEW | `core/cfg/ast_converter.py:66` | 21 | 9 | 12 |
| AsyncWith | NEW | `core/cfg/ast_converter.py:70` | 24 | 12 | 12 |
| AsyncFunctionDef | NEW | `core/cfg/ast_generator_v2.py:3696` | 25 | 13 | 12 |
| PEP604Union | NEW | `core/cfg/ast_converter.py:267` | 12 | 0 | 12 |

### 1.2 宿主（host）— 宿主上下文

host = 节点的**直接父节点** + 该节点在父节点中占据的**槽位**唯一决定（`host_of()`）。同一 ast 节点在不同槽位 = 不同宿主 = 不同判定单元。取值共 48 个：

| host | 条目数 | 最小深度 inherent | 允许深度档 |
|---|---|---|---|
| annotation-context | 5 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| assign-rhs | 60 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| async-func-body | 15 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| await-operand | 1 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| binop-operand | 8 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| boolop-operand | 24 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| call-arg | 56 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| class-body | 47 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| comprehension-for | 2 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| comprehension-if | 6 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| comprehension-scope | 21 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| condition-expr | 13 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| decorator-expr | 6 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| default-arg | 1 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| dict-literal | 1 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| elif-arm | 3 | 2 | d2 双层 / d3plus 三层及以上 |
| else-arm | 63 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| else-of-try | 19 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| except-handler | 103 | 2 | d2 双层 / d3plus 三层及以上 |
| f-string-format | 1 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| finally-body | 40 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| function-body | 180 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| generator-func-body | 2 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| if-arm | 164 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| lambda-body | 2 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| list-literal | 1 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| loop-body | 147 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| loop-else | 8 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| match-case-body | 92 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| match-guard | 8 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| match-subject | 1 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| module-level | 83 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| nested-func-body | 39 | 2 | d2 双层 / d3plus 三层及以上 |
| pattern-capture | 2 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| pattern-class | 4 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| pattern-mapping | 3 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| pattern-or | 1 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| pattern-sequence | 5 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| pattern-star | 1 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| pattern-value | 2 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| return-value-expr | 58 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| slice-bounds | 4 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| starred-operand | 1 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| subscript-index | 35 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| try-body | 115 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| tuple-literal | 6 | 0 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| with-body | 94 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |
| with-item | 3 | 1 | d1 单层 / d2 双层 / d3plus 三层及以上 |

### 1.3 深度（depth）— 深度档

**计数规则（唯一、可复算）**：

1. `REGION_TYPES` = {FunctionDef, AsyncFunctionDef, ClassDef, If, For, AsyncFor, While, With, AsyncWith, Try, TryStar, match_case, Lambda, ListComp, SetComp, DictComp, GeneratorExp} —— 即「会产生块/作用域边界」的节点。
2. 某节点的 **depth = 其 REGION_TYPES 祖先个数**（Module 不计）。
3. 深度档：`d1 单层` = depth 0 或 1；`d2 双层` = depth 2；`d3plus 三层及以上` = depth ≥ 3。
4. 宿主自身带来的必然 region 数（inherent）决定该宿主允许的深度档：宿主只允许 `depth >= inherent`（inherent=0/1 的宿主允许 d1/d2/d3plus；inherent=2 的宿主——except-handler / nested-func-body / elif-arm——只允许 d2/d3plus）。

| depth | 条目数 |
|---|---|
| d1 单层 | 720 |
| d2 双层 | 375 |
| d3plus 三层及以上 | 461 |

### 1.4 变体（variant）— 变体槽

variant = **单个 ast 节点可承载的语义变体**。这是上一规范 128 计数所折叠掉的维度，也是本规范攻击的主轴。每槽由一个**可判定的 AST 谓词**定义（谓词源码见生成器 `tools/completeness/jspace_generator.py` 的 `build_families()`），并各自要求**独立证据**。

| variant | 条目数 |
|---|---|
| if-else-arm | 24 |
| if-no-else | 24 |
| boolop-and | 20 |
| listcomp-single-for | 18 |
| try-with-handler | 18 |
| boolop-or | 17 |
| return-value | 17 |
| try-no-handler | 16 |
| with-single-item | 16 |
| aug-op-add | 15 |
| augform-target-name | 15 |
| if-elif-chain | 15 |
| ifexp-in-return | 15 |
| assert-with-msg | 14 |
| aug-op-sub | 14 |
| boolop-two-operands | 14 |
| import-plain | 14 |
| try-handler-typed | 14 |
| if-cond-boolop | 13 |
| namedexpr-in-if-cond | 13 |
| return-tuple | 13 |
| try-in-func | 13 |
| with-as-target | 13 |
| with-in-func | 13 |
| with-item-call | 13 |
| assert-plain | 12 |
| aug-target-name | 12 |
| continue-in-for | 12 |
| genexp-single-for | 12 |
| mmulti-case | 12 |
| pat-literal | 12 |
| raise-exc-call | 12 |
| return-bare | 12 |
| sliceform-in-subscript | 12 |
| try-with-finally | 12 |
| while-in-func | 12 |
| while-true | 12 |
| yield-bare | 12 |
| del-name | 11 |
| dictcomp-single-for | 11 |
| fstring-plain | 11 |
| if-in-loop | 11 |
| if-in-try | 11 |
| raise-bare | 11 |
| setcomp-single-for | 11 |
| slice-plain | 11 |
| starred-in-call | 11 |
| with-multi-item | 11 |
| af-in-async-def | 10 |
| ann-simple-name | 10 |
| augform-target-attr | 10 |
| aw-in-async-def | 10 |
| awexpr-in-if-cond | 10 |
| boolop-compare-operand | 10 |
| break-in-for | 10 |
| es-group-exception-type | 10 |
| es-multi-handler | 10 |
| es-single-handler | 10 |
| es-starred-capture | 10 |
| es-with-else | 10 |
| es-with-finally | 10 |
| global-single | 10 |
| lambda-in-assign | 10 |
| msingle-case | 10 |
| assert-in-func | 9 |
| boolop-nested | 9 |
| break-in-while | 9 |
| continue-in-while | 9 |
| es-in-func | 9 |
| es-in-loop | 9 |
| es-in-try | 9 |
| es-in-with | 9 |
| mhas-wildcard | 9 |
| min-func | 9 |
| augform-in-loop-body | 8 |
| aw-single-item | 8 |
| import-from | 8 |
| import-in-func | 8 |
| mhas-guard | 8 |
| nonlocal-in-class-in-func | 8 |
| nonlocal-in-func | 8 |
| nonlocal-in-nested-func | 8 |
| nonlocal-multiple | 8 |
| nonlocal-single | 8 |
| return-boolop | 8 |
| try-in-class-body | 8 |
| afd-at-module | 7 |
| augform-in-if-arm | 7 |
| boolop-three-plus | 7 |
| pat-capture | 7 |
| try-nested-in-try | 7 |
| try-with-else | 7 |
| af-nested-async-for | 6 |
| afd-nested | 6 |
| await-in-async-def | 6 |
| del-subscript | 6 |
| fstring-with-var | 6 |
| if-in-with | 6 |
| import-as | 6 |
| pep604-in-return-annotation | 6 |
| pep604-in-var-annotation | 6 |
| try-handler-as | 6 |
| aug-op-mul | 5 |
| await-in-async-with | 5 |
| deco-on-class | 5 |
| deco-on-function | 5 |
| deco-single | 5 |
| dictcomp-multi-for | 5 |
| fstring-embedded-expr | 5 |
| fstring-with-conversion | 5 |
| global-multiple | 5 |
| if-in-handler | 5 |
| if-in-match-case | 5 |
| lambda-as-call-arg | 5 |
| listcomp-multi-for | 5 |
| mcase-body-nested-if | 5 |
| return-in-handler | 5 |
| return-in-loop | 5 |
| return-in-match-case | 5 |
| return-in-with | 5 |
| return-ternary | 5 |
| slice-with-step | 5 |
| while-body-nested-loop | 5 |
| while-cond-boolop | 5 |
| with-body-nested-with | 5 |
| with-in-try | 5 |
| af-await-in-body | 4 |
| assert-in-loop | 4 |
| await-in-async-for | 4 |
| boolop-not-operand | 4 |
| break-in-if-arm | 4 |
| continue-in-if-arm | 4 |
| genexp-multi-for | 4 |
| listcomp-async | 4 |
| min-loop | 4 |
| pat-class | 4 |
| raise-exc-class | 4 |
| raise-in-loop | 4 |
| sliceform-in-del-target | 4 |
| starred-at-head | 4 |
| while-cond-ternary | 4 |
| with-in-loop | 4 |
| afd-in-class | 3 |
| afd-with-async-with | 3 |
| afd-with-await | 3 |
| ann-subscript-target | 3 |
| assert-in-with | 3 |
| augform-in-class-body | 3 |
| augform-in-handler | 3 |
| aw-await-in-body | 3 |
| break-in-nested-loop | 3 |
| break-target-outer | 3 |
| continue-in-nested-loop | 3 |
| continue-target-outer | 3 |
| fstring-in-assign | 3 |
| genexp-in-call-arg | 3 |
| ifexp-in-assign | 3 |
| ifexp-in-call-arg | 3 |
| import-from-as | 3 |
| import-in-handler | 3 |
| listcomp-in-assign | 3 |
| listcomp-in-call-arg | 3 |
| listcomp-in-return | 3 |
| pat-singleton | 3 |
| setcomp-multi-for | 3 |
| slice-in-assign-target | 3 |
| sliceform-in-assign-target | 3 |
| sliceform-in-return | 3 |
| sliceform-nested-subscript | 3 |
| sliceform-single-bound | 3 |
| starred-in-assign | 3 |
| try-nested-in-loop | 3 |
| yield-value | 3 |
| afd-with-async-for | 2 |
| assert-test-boolop | 2 |
| aug-rhs-ternary | 2 |
| aw-as-target | 2 |
| await-in-async-comp | 2 |
| await-in-binop | 2 |
| await-in-return | 2 |
| awexpr-in-binop | 2 |
| awexpr-in-listcomp-elt | 2 |
| awexpr-in-return | 2 |
| awexpr-in-while-cond | 2 |
| boolop-in-if-cond | 2 |
| break-in-with | 2 |
| continue-in-with | 2 |
| deco-stack | 2 |
| deco-with-args | 2 |
| del-in-loop | 2 |
| dictcomp-key-ternary | 2 |
| dictcomp-value-ternary | 2 |
| fstring-in-call-arg | 2 |
| global-with-same-name-assign | 2 |
| if-cond-compare-chain | 2 |
| ifexp-in-binop | 2 |
| ifexp-in-listcomp-elt | 2 |
| import-in-try | 2 |
| lambda-body-ternary | 2 |
| listcomp-elt-await | 2 |
| listcomp-elt-ternary | 2 |
| min-try | 2 |
| pat-mapping | 2 |
| pat-sequence | 2 |
| pat-wildcard | 2 |
| pat-with-guard | 2 |
| raise-from | 2 |
| raise-in-handler | 2 |
| raise-in-with | 2 |
| return-await | 2 |
| return-in-try-body | 2 |
| setcomp-async | 2 |
| slice-neg-bound | 2 |
| slice-ternary-bound | 2 |
| sliceform-in-call-arg | 2 |
| try-handler-tuple-type | 2 |
| try-nested-in-with | 2 |
| while-at-module | 2 |
| while-cond-compare-chain | 2 |
| while-in-try | 2 |
| with-in-match-case | 2 |
| af-in-with | 1 |
| afd-with-yield | 1 |
| ann-simple-type | 1 |
| ann-with-value | 1 |
| assert-test-call | 1 |
| assert-test-ternary | 1 |
| aug-op-bitand | 1 |
| aug-op-bitor | 1 |
| aug-op-bitxor | 1 |
| aug-op-floordiv | 1 |
| aug-op-lshift | 1 |
| aug-op-matmul | 1 |
| aug-op-mod | 1 |
| aug-op-pow | 1 |
| aug-op-rshift | 1 |
| aug-op-truediv | 1 |
| aug-rhs-attr | 1 |
| aug-rhs-call | 1 |
| aug-rhs-subscript | 1 |
| aug-target-attr | 1 |
| aug-target-subscript | 1 |
| augform-in-match-case | 1 |
| augform-in-try-body | 1 |
| augform-target-subscript | 1 |
| aw-in-loop | 1 |
| await-in-assign | 1 |
| await-in-call-arg | 1 |
| awexpr-in-assign-rhs | 1 |
| awexpr-in-boolop | 1 |
| awexpr-in-call-arg | 1 |
| boolop-await-operand | 1 |
| boolop-in-guard | 1 |
| break-in-handler | 1 |
| continue-in-handler | 1 |
| continue-in-match-case | 1 |
| deco-name-form | 1 |
| del-attribute | 1 |
| del-in-try | 1 |
| del-in-with | 1 |
| del-slice | 1 |
| del-ternary-target | 1 |
| dictcomp-async | 1 |
| dictcomp-in-assign | 1 |
| dictcomp-in-call-arg | 1 |
| genexp-elt-ternary | 1 |
| genexp-in-assign | 1 |
| global-at-module | 1 |
| global-in-func | 1 |
| if-cond-await | 1 |
| if-cond-ternary | 1 |
| ifexp-in-boolop | 1 |
| ifexp-in-lambda | 1 |
| ifexp-in-subscript | 1 |
| import-in-class-body | 1 |
| import-in-else-of-try | 1 |
| import-in-finally | 1 |
| lambda-in-return | 1 |
| mnested-match | 1 |
| namedexpr-in-loop-body | 1 |
| pat-in-nested-match | 1 |
| pat-or | 1 |
| pat-star | 1 |
| raise-in-try-body | 1 |
| raise-ternary-exc | 1 |
| return-yield | 1 |
| setcomp-elt-ternary | 1 |
| slice-expr-bound | 1 |
| slice-in-del-target | 1 |
| sliceform-full | 1 |
| sliceform-step-only | 1 |
| starred-at-mid | 1 |
| starred-at-tail | 1 |
| starred-in-tuple-literal | 1 |
| while-with-break | 1 |
| with-item-ternary | 1 |
| yield-as-arg | 1 |
| yield-in-assign | 1 |
| yield-in-boolop | 1 |

## 2. 计数规则（复算口径）

| 计数 | 规则 | 复算命令 |
|---|---|---|
| 条目总数 | `len(entries)` | `python -X utf8 tools/completeness/jspace_generator.py --out ... --md ...` |
| 族条目数 | entries 中 `form` 等于该族名的行数 | 见 §3 |
| covered | 该 (form,variant,host,depth) 在证据索引的探针源码中**被观测到** ⇒ `required_evidence[0].pyc` 命中证据索引 | `python -X utf8 tools/completeness/coverage_checker.py --space ... --evidence-root ...` |
| uncovered | 该单元无观测 ⇒ `required_evidence[0].pyc` 指向**同族锚点探针**（仓内真实存在但**从未**登记进任何 `rec1_probes_*.json`） | 同上 |
| 结构性单元选取 | 某 (form,variant,host) 在索引中零观测时登记 1 条（深度取该宿主最小档）；每族最多登记 `structural_cap`=12 条；**整族零证据时不截断** | 同上 |
| 深度档 | §1.3 的 4 条 | 同上 |

> **口径纠错声明**：上一规范台账「174 处标记」不可复现（实测 123 / 174 / 191 视正则口径而定，见 `baseline/markers.md` §5）。本空间**不使用**任何「标记数」口径；所有数字均可由 §2 的规则逐条重算。

## 3. 逐族条目数

| form | row | 条目 | covered | uncovered | 变体数 | 宿主数 |
|---|---|---|---|---|---|---|
| If | If | 118 | 106 | 12 | 13 | 15 |
| BoolOp | BoolOp | 85 | 73 | 12 | 13 | 14 |
| IfExp | IfExp | 28 | 16 | 12 | 14 | 13 |
| Try | Try | 108 | 96 | 12 | 12 | 12 |
| Raise | Raise | 39 | 27 | 12 | 10 | 10 |
| Assert | Assert | 46 | 34 | 12 | 11 | 11 |
| Import | Import | 47 | 35 | 12 | 12 | 12 |
| Global | Global | 19 | 7 | 12 | 7 | 10 |
| global_nonlocal | global_nonlocal | 40 | 0 | 40 | 5 | 8 |
| Await | Await | 23 | 11 | 12 | 12 | 11 |
| ListComp | ListComp | 40 | 28 | 12 | 14 | 12 |
| await_expr | await_expr | 21 | 9 | 12 | 9 | 10 |
| Yield | Yield | 18 | 6 | 12 | 10 | 12 |
| Match | Match | 37 | 25 | 12 | 12 | 11 |
| With | With | 83 | 71 | 12 | 10 | 11 |
| match_statement | match_statement | 60 | 48 | 12 | 10 | 10 |
| Break | Break | 32 | 20 | 12 | 10 | 10 |
| Continue | Continue | 35 | 23 | 12 | 10 | 10 |
| While | While | 45 | 33 | 12 | 11 | 11 |
| Delete | Delete | 24 | 12 | 12 | 10 | 11 |
| AugAssign | AugAssign | 63 | 51 | 12 | 20 | 12 |
| Return | Return | 80 | 68 | 12 | 13 | 13 |
| Slice | Slice | 25 | 13 | 12 | 9 | 9 |
| augmented_assign | augmented_assign | 49 | 37 | 12 | 12 | 12 |
| slice | slice | 32 | 20 | 12 | 10 | 10 |
| Lambda | NEW | 18 | 6 | 12 | 10 | 10 |
| Decorator | NEW | 20 | 8 | 12 | 8 | 5 |
| SetComp | NEW | 17 | 5 | 12 | 8 | 10 |
| DictComp | NEW | 23 | 11 | 12 | 9 | 10 |
| GeneratorExp | NEW | 21 | 9 | 12 | 8 | 10 |
| NamedExpr | NEW | 14 | 2 | 12 | 10 | 14 |
| JoinedStr | NEW | 32 | 20 | 12 | 10 | 11 |
| Starred | NEW | 21 | 9 | 12 | 9 | 10 |
| ExceptStar | NEW | 96 | 0 | 96 | 10 | 10 |
| AnnAssign | NEW | 15 | 3 | 12 | 10 | 10 |
| AsyncFor | NEW | 21 | 9 | 12 | 9 | 10 |
| AsyncWith | NEW | 24 | 12 | 12 | 10 | 11 |
| AsyncFunctionDef | NEW | 25 | 13 | 12 | 10 | 7 |
| PEP604Union | NEW | 12 | 0 | 12 | 8 | 6 |

## 4. 全量条目表

| id | form | host | depth | variant | row | required_evidence.pyc | status |
|---|---|---|---|---|---|---|---|
| JS-IF-001 | If | module-level | d1 单层 | if-no-else | If | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-IF-002 | If | function-body | d1 单层 | if-no-else | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-IF-003 | If | function-body | d2 双层 | if-no-else | If | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-IF-004 | If | function-body | d3plus 三层及以上 | if-no-else | If | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-IF-005 | If | class-body | d1 单层 | if-no-else | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-006 | If | if-arm | d2 双层 | if-no-else | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-007 | If | if-arm | d3plus 三层及以上 | if-no-else | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-IF-008 | If | elif-arm | d2 双层 | if-no-else | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-009 | If | else-arm | d2 双层 | if-no-else | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-010 | If | else-arm | d3plus 三层及以上 | if-no-else | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-011 | If | loop-body | d2 双层 | if-no-else | If | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_arg.pyc` | covered |
| JS-IF-012 | If | loop-body | d3plus 三层及以上 | if-no-else | If | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_from.pyc` | covered |
| JS-IF-013 | If | loop-else | d1 单层 | if-no-else | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-014 | If | with-body | d2 双层 | if-no-else | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-015 | If | with-body | d3plus 三层及以上 | if-no-else | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-016 | If | try-body | d2 双层 | if-no-else | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-017 | If | try-body | d3plus 三层及以上 | if-no-else | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-IF-018 | If | except-handler | d3plus 三层及以上 | if-no-else | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-019 | If | else-of-try | d3plus 三层及以上 | if-no-else | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-020 | If | finally-body | d2 双层 | if-no-else | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IF-021 | If | finally-body | d3plus 三层及以上 | if-no-else | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-IF-022 | If | match-case-body | d2 双层 | if-no-else | If | `test_repros/round10/r10_15_global_hosts.pyc` | covered |
| JS-IF-023 | If | match-case-body | d3plus 三层及以上 | if-no-else | If | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-IF-024 | If | nested-func-body | d2 双层 | if-no-else | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-025 | If | module-level | d1 单层 | if-else-arm | If | `test_repros/round2/m01_docstring_order.pyc` | covered |
| JS-IF-026 | If | function-body | d1 单层 | if-else-arm | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b75_face.pyc` | covered |
| JS-IF-027 | If | function-body | d2 双层 | if-else-arm | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-028 | If | function-body | d3plus 三层及以上 | if-else-arm | If | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-IF-029 | If | class-body | d1 单层 | if-else-arm | If | `test_repros/round2/c02_class_if.pyc` | covered |
| JS-IF-030 | If | if-arm | d1 单层 | if-else-arm | If | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-IF-031 | If | if-arm | d2 双层 | if-else-arm | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-032 | If | if-arm | d3plus 三层及以上 | if-else-arm | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-033 | If | elif-arm | d2 双层 | if-else-arm | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-034 | If | else-arm | d2 双层 | if-else-arm | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-035 | If | else-arm | d3plus 三层及以上 | if-else-arm | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-IF-036 | If | loop-body | d2 双层 | if-else-arm | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-IF-037 | If | loop-body | d3plus 三层及以上 | if-else-arm | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-038 | If | loop-else | d1 单层 | if-else-arm | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-039 | If | with-body | d3plus 三层及以上 | if-else-arm | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-040 | If | try-body | d2 双层 | if-else-arm | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-041 | If | try-body | d3plus 三层及以上 | if-else-arm | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-042 | If | except-handler | d2 双层 | if-else-arm | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IF-043 | If | except-handler | d3plus 三层及以上 | if-else-arm | If | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-IF-044 | If | else-of-try | d1 单层 | if-else-arm | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-045 | If | finally-body | d1 单层 | if-else-arm | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-046 | If | match-case-body | d2 双层 | if-else-arm | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-IF-047 | If | match-case-body | d3plus 三层及以上 | if-else-arm | If | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-IF-048 | If | nested-func-body | d2 双层 | if-else-arm | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-049 | If | module-level | d1 单层 | if-elif-chain | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-050 | If | function-body | d1 单层 | if-elif-chain | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-051 | If | function-body | d2 双层 | if-elif-chain | If | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-IF-052 | If | function-body | d3plus 三层及以上 | if-elif-chain | If | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-IF-053 | If | class-body | d1 单层 | if-elif-chain | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-054 | If | if-arm | d2 双层 | if-elif-chain | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-IF-055 | If | if-arm | d3plus 三层及以上 | if-elif-chain | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-056 | If | elif-arm | d2 双层 | if-elif-chain | If | `test_repros/round1/r1_17_elif_mixed.pyc` | uncovered |
| JS-IF-057 | If | else-arm | d2 双层 | if-elif-chain | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-058 | If | else-arm | d3plus 三层及以上 | if-elif-chain | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-059 | If | loop-body | d1 单层 | if-elif-chain | If | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-IF-060 | If | loop-body | d2 双层 | if-elif-chain | If | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-IF-061 | If | loop-body | d3plus 三层及以上 | if-elif-chain | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-062 | If | try-body | d2 双层 | if-elif-chain | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-063 | If | try-body | d3plus 三层及以上 | if-elif-chain | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-064 | If | function-body | d1 单层 | if-cond-ternary | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-IF-065 | If | function-body | d1 单层 | if-cond-boolop | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-066 | If | function-body | d2 双层 | if-cond-boolop | If | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-IF-067 | If | if-arm | d2 双层 | if-cond-boolop | If | `test_repros/round7/r7_14_boolop_deep_host.pyc` | covered |
| JS-IF-068 | If | if-arm | d3plus 三层及以上 | if-cond-boolop | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-069 | If | else-arm | d2 双层 | if-cond-boolop | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-070 | If | else-arm | d3plus 三层及以上 | if-cond-boolop | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-071 | If | loop-body | d2 双层 | if-cond-boolop | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-IF-072 | If | loop-body | d3plus 三层及以上 | if-cond-boolop | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-073 | If | with-body | d3plus 三层及以上 | if-cond-boolop | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-074 | If | try-body | d2 双层 | if-cond-boolop | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-075 | If | try-body | d3plus 三层及以上 | if-cond-boolop | If | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-IF-076 | If | match-case-body | d2 双层 | if-cond-boolop | If | `test_repros/round2/x01_if_deep_hosts.pyc` | covered |
| JS-IF-077 | If | match-case-body | d3plus 三层及以上 | if-cond-boolop | If | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-IF-078 | If | loop-body | d2 双层 | if-cond-await | If | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-IF-079 | If | function-body | d1 单层 | if-cond-compare-chain | If | `test_repros/round7/r7_14_boolop_deep_host.pyc` | covered |
| JS-IF-080 | If | loop-body | d3plus 三层及以上 | if-cond-compare-chain | If | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-IF-081 | If | if-arm | d3plus 三层及以上 | if-in-loop | If | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_assign.pyc` | covered |
| JS-IF-082 | If | else-arm | d2 双层 | if-in-loop | If | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-IF-083 | If | else-arm | d3plus 三层及以上 | if-in-loop | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-084 | If | loop-body | d1 单层 | if-in-loop | If | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-IF-085 | If | loop-body | d2 双层 | if-in-loop | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-IF-086 | If | loop-body | d3plus 三层及以上 | if-in-loop | If | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_from.pyc` | covered |
| JS-IF-087 | If | with-body | d3plus 三层及以上 | if-in-loop | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-088 | If | try-body | d3plus 三层及以上 | if-in-loop | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-IF-089 | If | except-handler | d3plus 三层及以上 | if-in-loop | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-090 | If | finally-body | d3plus 三层及以上 | if-in-loop | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-IF-091 | If | match-case-body | d3plus 三层及以上 | if-in-loop | If | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-IF-092 | If | if-arm | d3plus 三层及以上 | if-in-try | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-093 | If | else-arm | d3plus 三层及以上 | if-in-try | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-094 | If | loop-body | d3plus 三层及以上 | if-in-try | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-095 | If | with-body | d3plus 三层及以上 | if-in-try | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-096 | If | try-body | d2 双层 | if-in-try | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-097 | If | try-body | d3plus 三层及以上 | if-in-try | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-IF-098 | If | except-handler | d2 双层 | if-in-try | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IF-099 | If | except-handler | d3plus 三层及以上 | if-in-try | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-100 | If | else-of-try | d3plus 三层及以上 | if-in-try | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-101 | If | finally-body | d2 双层 | if-in-try | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IF-102 | If | finally-body | d3plus 三层及以上 | if-in-try | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-IF-103 | If | if-arm | d3plus 三层及以上 | if-in-handler | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-104 | If | else-arm | d3plus 三层及以上 | if-in-handler | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-105 | If | loop-body | d3plus 三层及以上 | if-in-handler | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-106 | If | except-handler | d2 双层 | if-in-handler | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IF-107 | If | except-handler | d3plus 三层及以上 | if-in-handler | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-108 | If | if-arm | d3plus 三层及以上 | if-in-with | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-109 | If | else-arm | d3plus 三层及以上 | if-in-with | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-110 | If | loop-body | d3plus 三层及以上 | if-in-with | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-111 | If | with-body | d2 双层 | if-in-with | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-112 | If | with-body | d3plus 三层及以上 | if-in-with | If | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IF-113 | If | match-case-body | d3plus 三层及以上 | if-in-with | If | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-IF-114 | If | if-arm | d3plus 三层及以上 | if-in-match-case | If | `test_repros/round2/x01_if_deep_hosts.pyc` | covered |
| JS-IF-115 | If | loop-body | d3plus 三层及以上 | if-in-match-case | If | `test_repros/round2/x02_for_deep_hosts.pyc` | covered |
| JS-IF-116 | If | with-body | d3plus 三层及以上 | if-in-match-case | If | `test_repros/round5/rec1_synth_g2a_with_match_cross.pyc` | covered |
| JS-IF-117 | If | match-case-body | d2 双层 | if-in-match-case | If | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-IF-118 | If | match-case-body | d3plus 三层及以上 | if-in-match-case | If | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-BOOLOP-001 | BoolOp | module-level | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-002 | BoolOp | function-body | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-003 | BoolOp | if-arm | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-004 | BoolOp | else-arm | d2 双层 | boolop-and | BoolOp | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-BOOLOP-005 | BoolOp | else-arm | d3plus 三层及以上 | boolop-and | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-006 | BoolOp | loop-body | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-007 | BoolOp | condition-expr | d1 单层 | boolop-and | BoolOp | `test_repros/round7/r7_12_boolop_nest.pyc` | covered |
| JS-BOOLOP-008 | BoolOp | condition-expr | d3plus 三层及以上 | boolop-and | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-009 | BoolOp | return-value-expr | d1 单层 | boolop-and | BoolOp | `test_repros/round3/_scratch_b98/resid.pyc` | covered |
| JS-BOOLOP-010 | BoolOp | return-value-expr | d2 双层 | boolop-and | BoolOp | `test_repros/round7/r7_12_boolop_nest.pyc` | covered |
| JS-BOOLOP-011 | BoolOp | return-value-expr | d3plus 三层及以上 | boolop-and | BoolOp | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-BOOLOP-012 | BoolOp | assign-rhs | d1 单层 | boolop-and | BoolOp | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-BOOLOP-013 | BoolOp | assign-rhs | d3plus 三层及以上 | boolop-and | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-014 | BoolOp | call-arg | d3plus 三层及以上 | boolop-and | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-015 | BoolOp | boolop-operand | d1 单层 | boolop-and | BoolOp | `test_repros/round3/_scratch_b98/resid.pyc` | covered |
| JS-BOOLOP-016 | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-and | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-017 | BoolOp | comprehension-if | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-018 | BoolOp | match-guard | d3plus 三层及以上 | boolop-and | BoolOp | `test_repros/round5/rec1_synth_b74e_guard_battery2.pyc` | covered |
| JS-BOOLOP-019 | BoolOp | except-handler | d2 双层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-020 | BoolOp | finally-body | d1 单层 | boolop-and | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-021 | BoolOp | module-level | d1 单层 | boolop-or | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-022 | BoolOp | function-body | d1 单层 | boolop-or | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-023 | BoolOp | if-arm | d1 单层 | boolop-or | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-024 | BoolOp | else-arm | d2 双层 | boolop-or | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-025 | BoolOp | else-arm | d3plus 三层及以上 | boolop-or | BoolOp | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-BOOLOP-026 | BoolOp | loop-body | d1 单层 | boolop-or | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-027 | BoolOp | condition-expr | d1 单层 | boolop-or | BoolOp | `test_repros/round7/r7_12_boolop_nest.pyc` | covered |
| JS-BOOLOP-028 | BoolOp | return-value-expr | d1 单层 | boolop-or | BoolOp | `test_repros/round3/_scratch_b98/resid.pyc` | covered |
| JS-BOOLOP-029 | BoolOp | return-value-expr | d2 双层 | boolop-or | BoolOp | `test_repros/round7/r7_14_boolop_deep_host.pyc` | covered |
| JS-BOOLOP-030 | BoolOp | return-value-expr | d3plus 三层及以上 | boolop-or | BoolOp | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-BOOLOP-031 | BoolOp | assign-rhs | d1 单层 | boolop-or | BoolOp | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-BOOLOP-032 | BoolOp | assign-rhs | d3plus 三层及以上 | boolop-or | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-033 | BoolOp | call-arg | d1 单层 | boolop-or | BoolOp | `test_repros/round1/n1_02_simple_or.pyc` | uncovered |
| JS-BOOLOP-034 | BoolOp | boolop-operand | d1 单层 | boolop-or | BoolOp | `test_repros/round3/_scratch_b98/resid.pyc` | covered |
| JS-BOOLOP-035 | BoolOp | boolop-operand | d2 双层 | boolop-or | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-036 | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-or | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-037 | BoolOp | match-guard | d3plus 三层及以上 | boolop-or | BoolOp | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-BOOLOP-038 | BoolOp | else-arm | d2 双层 | boolop-two-operands | BoolOp | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-BOOLOP-039 | BoolOp | else-arm | d3plus 三层及以上 | boolop-two-operands | BoolOp | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-BOOLOP-040 | BoolOp | condition-expr | d1 单层 | boolop-two-operands | BoolOp | `test_repros/round7/r7_12_boolop_nest.pyc` | covered |
| JS-BOOLOP-041 | BoolOp | condition-expr | d3plus 三层及以上 | boolop-two-operands | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-042 | BoolOp | return-value-expr | d1 单层 | boolop-two-operands | BoolOp | `test_repros/round3/_scratch_b98/resid.pyc` | covered |
| JS-BOOLOP-043 | BoolOp | return-value-expr | d2 双层 | boolop-two-operands | BoolOp | `test_repros/round7/r7_12_boolop_nest.pyc` | covered |
| JS-BOOLOP-044 | BoolOp | return-value-expr | d3plus 三层及以上 | boolop-two-operands | BoolOp | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-BOOLOP-045 | BoolOp | assign-rhs | d1 单层 | boolop-two-operands | BoolOp | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-BOOLOP-046 | BoolOp | assign-rhs | d3plus 三层及以上 | boolop-two-operands | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-047 | BoolOp | call-arg | d3plus 三层及以上 | boolop-two-operands | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-048 | BoolOp | boolop-operand | d1 单层 | boolop-two-operands | BoolOp | `test_repros/round3/_scratch_b98/resid.pyc` | covered |
| JS-BOOLOP-049 | BoolOp | boolop-operand | d2 双层 | boolop-two-operands | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-050 | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-two-operands | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-051 | BoolOp | match-guard | d3plus 三层及以上 | boolop-two-operands | BoolOp | `test_repros/round5/rec1_synth_b74e_guard_battery2.pyc` | covered |
| JS-BOOLOP-052 | BoolOp | else-arm | d2 双层 | boolop-three-plus | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-053 | BoolOp | else-arm | d3plus 三层及以上 | boolop-three-plus | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-054 | BoolOp | return-value-expr | d1 单层 | boolop-three-plus | BoolOp | `test_repros/round3/_scratch_b98/resid.pyc` | covered |
| JS-BOOLOP-055 | BoolOp | assign-rhs | d1 单层 | boolop-three-plus | BoolOp | `test_repros/round8/rv8_01_chain3_subscript.pyc` | covered |
| JS-BOOLOP-056 | BoolOp | assign-rhs | d3plus 三层及以上 | boolop-three-plus | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-057 | BoolOp | boolop-operand | d2 双层 | boolop-three-plus | BoolOp | `test_repros/round4/r4_or4_and2.pyc` | covered |
| JS-BOOLOP-058 | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-three-plus | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-059 | BoolOp | else-arm | d3plus 三层及以上 | boolop-nested | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-060 | BoolOp | condition-expr | d3plus 三层及以上 | boolop-nested | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-061 | BoolOp | return-value-expr | d1 单层 | boolop-nested | BoolOp | `test_repros/round3/_scratch_b98/resid.pyc` | covered |
| JS-BOOLOP-062 | BoolOp | return-value-expr | d3plus 三层及以上 | boolop-nested | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-063 | BoolOp | assign-rhs | d1 单层 | boolop-nested | BoolOp | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-BOOLOP-064 | BoolOp | assign-rhs | d3plus 三层及以上 | boolop-nested | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-065 | BoolOp | call-arg | d3plus 三层及以上 | boolop-nested | BoolOp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-BOOLOP-066 | BoolOp | boolop-operand | d1 单层 | boolop-nested | BoolOp | `test_repros/round3/_scratch_b98/resid.pyc` | covered |
| JS-BOOLOP-067 | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-nested | BoolOp | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-BOOLOP-068 | BoolOp | else-arm | d2 双层 | boolop-not-operand | BoolOp | `test_repros/round7/r7_11_boolop_mixed.pyc` | covered |
| JS-BOOLOP-069 | BoolOp | else-arm | d3plus 三层及以上 | boolop-not-operand | BoolOp | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-BOOLOP-070 | BoolOp | boolop-operand | d1 单层 | boolop-not-operand | BoolOp | `test_repros/round7/r7_11_boolop_mixed.pyc` | covered |
| JS-BOOLOP-071 | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-not-operand | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-072 | BoolOp | else-arm | d2 双层 | boolop-compare-operand | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-073 | BoolOp | else-arm | d3plus 三层及以上 | boolop-compare-operand | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-074 | BoolOp | condition-expr | d1 单层 | boolop-compare-operand | BoolOp | `test_repros/round7/r7_14_boolop_deep_host.pyc` | covered |
| JS-BOOLOP-075 | BoolOp | return-value-expr | d1 单层 | boolop-compare-operand | BoolOp | `test_repros/round7/r7_10_chain_compare_calls.pyc` | covered |
| JS-BOOLOP-076 | BoolOp | return-value-expr | d2 双层 | boolop-compare-operand | BoolOp | `test_repros/round7/r7_14_boolop_deep_host.pyc` | covered |
| JS-BOOLOP-077 | BoolOp | return-value-expr | d3plus 三层及以上 | boolop-compare-operand | BoolOp | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-BOOLOP-078 | BoolOp | boolop-operand | d1 单层 | boolop-compare-operand | BoolOp | `test_repros/round7/r7_10_chain_compare_calls.pyc` | covered |
| JS-BOOLOP-079 | BoolOp | boolop-operand | d2 双层 | boolop-compare-operand | BoolOp | `test_repros/round7/r7_14_boolop_deep_host.pyc` | covered |
| JS-BOOLOP-080 | BoolOp | boolop-operand | d3plus 三层及以上 | boolop-compare-operand | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-081 | BoolOp | match-guard | d3plus 三层及以上 | boolop-compare-operand | BoolOp | `test_repros/round5/rec1_synth_b74e_guard_battery2.pyc` | covered |
| JS-BOOLOP-082 | BoolOp | else-arm | d3plus 三层及以上 | boolop-await-operand | BoolOp | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-BOOLOP-083 | BoolOp | else-arm | d2 双层 | boolop-in-if-cond | BoolOp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BOOLOP-084 | BoolOp | else-arm | d3plus 三层及以上 | boolop-in-if-cond | BoolOp | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-BOOLOP-085 | BoolOp | match-guard | d3plus 三层及以上 | boolop-in-guard | BoolOp | `test_repros/round5/rec1_synth_b74e_guard_battery2.pyc` | covered |
| JS-IFEXP-001 | IfExp | function-body | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-002 | IfExp | module-level | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-003 | IfExp | assign-rhs | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-004 | IfExp | return-value-expr | d1 单层 | ifexp-in-return | IfExp | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-IFEXP-005 | IfExp | return-value-expr | d2 双层 | ifexp-in-return | IfExp | `test_repros/round7/r7_08_ternary_deep_host.pyc` | covered |
| JS-IFEXP-006 | IfExp | return-value-expr | d3plus 三层及以上 | ifexp-in-return | IfExp | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-IFEXP-007 | IfExp | call-arg | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-008 | IfExp | subscript-index | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-009 | IfExp | condition-expr | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-010 | IfExp | comprehension-scope | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-011 | IfExp | lambda-body | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-012 | IfExp | boolop-operand | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-013 | IfExp | binop-operand | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-014 | IfExp | if-arm | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-015 | IfExp | match-guard | d1 单层 | ifexp-in-return | IfExp | `test_repros/round3/e04_g2_ifexp_deep.pyc` | uncovered |
| JS-IFEXP-016 | IfExp | assign-rhs | d1 单层 | ifexp-in-assign | IfExp | `test_repros/round10/rv10_32_augassign_variant.pyc` | covered |
| JS-IFEXP-017 | IfExp | assign-rhs | d2 双层 | ifexp-in-assign | IfExp | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b50_face.pyc` | covered |
| JS-IFEXP-018 | IfExp | assign-rhs | d3plus 三层及以上 | ifexp-in-assign | IfExp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IFEXP-019 | IfExp | call-arg | d1 单层 | ifexp-in-call-arg | IfExp | `test_repros/round7/r7_01_ternary_args_index.pyc` | covered |
| JS-IFEXP-020 | IfExp | call-arg | d2 双层 | ifexp-in-call-arg | IfExp | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-IFEXP-021 | IfExp | call-arg | d3plus 三层及以上 | ifexp-in-call-arg | IfExp | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-IFEXP-022 | IfExp | subscript-index | d1 单层 | ifexp-in-subscript | IfExp | `test_repros/round7/r7_01_ternary_args_index.pyc` | covered |
| JS-IFEXP-023 | IfExp | lambda-body | d2 双层 | ifexp-in-lambda | IfExp | `test_repros/round7/r7_01_ternary_args_index.pyc` | covered |
| JS-IFEXP-024 | IfExp | comprehension-scope | d2 双层 | ifexp-in-listcomp-elt | IfExp | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-IFEXP-025 | IfExp | comprehension-scope | d3plus 三层及以上 | ifexp-in-listcomp-elt | IfExp | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-IFEXP-026 | IfExp | boolop-operand | d2 双层 | ifexp-in-boolop | IfExp | `test_repros/round8/r8v8rev3_b104_exprtail_battery.pyc` | covered |
| JS-IFEXP-027 | IfExp | binop-operand | d1 单层 | ifexp-in-binop | IfExp | `test_repros/round7/r7_04_ternary_binop_compare.pyc` | covered |
| JS-IFEXP-028 | IfExp | binop-operand | d2 双层 | ifexp-in-binop | IfExp | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-TRY-001 | Try | function-body | d1 单层 | try-no-handler | Try | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-TRY-002 | Try | module-level | d1 单层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-003 | Try | if-arm | d2 双层 | try-no-handler | Try | `test_repros/round9/rv9_01_b68_nonfin_tail.pyc` | covered |
| JS-TRY-004 | Try | if-arm | d3plus 三层及以上 | try-no-handler | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-TRY-005 | Try | loop-body | d2 双层 | try-no-handler | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-TRY-006 | Try | loop-body | d3plus 三层及以上 | try-no-handler | Try | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-TRY-007 | Try | with-body | d2 双层 | try-no-handler | Try | `test_repros/round8/rv8_02_with_tryfin_constret.pyc` | covered |
| JS-TRY-008 | Try | with-body | d3plus 三层及以上 | try-no-handler | Try | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-TRY-009 | Try | try-body | d2 双层 | try-no-handler | Try | `test_repros/round2/x01_if_deep_hosts.pyc` | covered |
| JS-TRY-010 | Try | try-body | d3plus 三层及以上 | try-no-handler | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-011 | Try | except-handler | d2 双层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-012 | Try | else-of-try | d1 单层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-013 | Try | finally-body | d1 单层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-014 | Try | nested-func-body | d2 双层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-015 | Try | class-body | d1 单层 | try-no-handler | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-016 | Try | match-case-body | d1 单层 | try-no-handler | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-017 | Try | function-body | d1 单层 | try-with-handler | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b50_face.pyc` | covered |
| JS-TRY-018 | Try | function-body | d2 双层 | try-with-handler | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-019 | Try | function-body | d3plus 三层及以上 | try-with-handler | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-020 | Try | module-level | d1 单层 | try-with-handler | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-021 | Try | if-arm | d2 双层 | try-with-handler | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-022 | Try | if-arm | d3plus 三层及以上 | try-with-handler | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-023 | Try | loop-body | d2 双层 | try-with-handler | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-024 | Try | loop-body | d3plus 三层及以上 | try-with-handler | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-025 | Try | with-body | d2 双层 | try-with-handler | Try | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-TRY-026 | Try | try-body | d2 双层 | try-with-handler | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-027 | Try | try-body | d3plus 三层及以上 | try-with-handler | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-028 | Try | except-handler | d2 双层 | try-with-handler | Try | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-TRY-029 | Try | except-handler | d3plus 三层及以上 | try-with-handler | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-030 | Try | else-of-try | d1 单层 | try-with-handler | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-031 | Try | finally-body | d1 单层 | try-with-handler | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-032 | Try | nested-func-body | d2 双层 | try-with-handler | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-033 | Try | class-body | d1 单层 | try-with-handler | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-034 | Try | match-case-body | d1 单层 | try-with-handler | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-035 | Try | function-body | d1 单层 | try-with-else | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-TRY-036 | Try | module-level | d1 单层 | try-with-else | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-037 | Try | if-arm | d2 双层 | try-with-else | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-038 | Try | loop-body | d3plus 三层及以上 | try-with-else | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-039 | Try | with-body | d1 单层 | try-with-else | Try | `test_repros/round2/m04_module_try.pyc` | uncovered |
| JS-TRY-040 | Try | try-body | d3plus 三层及以上 | try-with-else | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-041 | Try | class-body | d1 单层 | try-with-else | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-042 | Try | function-body | d1 单层 | try-with-finally | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b50_face.pyc` | covered |
| JS-TRY-043 | Try | function-body | d2 双层 | try-with-finally | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-044 | Try | function-body | d3plus 三层及以上 | try-with-finally | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-045 | Try | if-arm | d2 双层 | try-with-finally | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-046 | Try | if-arm | d3plus 三层及以上 | try-with-finally | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-TRY-047 | Try | loop-body | d2 双层 | try-with-finally | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-TRY-048 | Try | loop-body | d3plus 三层及以上 | try-with-finally | Try | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-TRY-049 | Try | with-body | d2 双层 | try-with-finally | Try | `test_repros/round8/rv8_02_with_tryfin_constret.pyc` | covered |
| JS-TRY-050 | Try | with-body | d3plus 三层及以上 | try-with-finally | Try | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-TRY-051 | Try | try-body | d2 双层 | try-with-finally | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-052 | Try | try-body | d3plus 三层及以上 | try-with-finally | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-053 | Try | class-body | d1 单层 | try-with-finally | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-054 | Try | function-body | d1 单层 | try-handler-typed | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b50_face.pyc` | covered |
| JS-TRY-055 | Try | function-body | d2 双层 | try-handler-typed | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-056 | Try | function-body | d3plus 三层及以上 | try-handler-typed | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-057 | Try | module-level | d1 单层 | try-handler-typed | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-058 | Try | if-arm | d2 双层 | try-handler-typed | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-059 | Try | if-arm | d3plus 三层及以上 | try-handler-typed | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-060 | Try | loop-body | d2 双层 | try-handler-typed | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-061 | Try | loop-body | d3plus 三层及以上 | try-handler-typed | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-062 | Try | with-body | d2 双层 | try-handler-typed | Try | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-TRY-063 | Try | try-body | d2 双层 | try-handler-typed | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-064 | Try | try-body | d3plus 三层及以上 | try-handler-typed | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-065 | Try | except-handler | d2 双层 | try-handler-typed | Try | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-TRY-066 | Try | except-handler | d3plus 三层及以上 | try-handler-typed | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-067 | Try | class-body | d1 单层 | try-handler-typed | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-068 | Try | function-body | d1 单层 | try-handler-as | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-TRY-069 | Try | function-body | d2 双层 | try-handler-as | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-070 | Try | function-body | d3plus 三层及以上 | try-handler-as | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-071 | Try | if-arm | d2 双层 | try-handler-as | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-072 | Try | if-arm | d3plus 三层及以上 | try-handler-as | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-073 | Try | loop-body | d3plus 三层及以上 | try-handler-as | Try | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-TRY-074 | Try | function-body | d2 双层 | try-handler-tuple-type | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-075 | Try | try-body | d3plus 三层及以上 | try-handler-tuple-type | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-076 | Try | if-arm | d3plus 三层及以上 | try-nested-in-try | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-TRY-077 | Try | loop-body | d3plus 三层及以上 | try-nested-in-try | Try | `test_repros/round2/x02_for_deep_hosts.pyc` | covered |
| JS-TRY-078 | Try | with-body | d3plus 三层及以上 | try-nested-in-try | Try | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-TRY-079 | Try | try-body | d2 双层 | try-nested-in-try | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-080 | Try | try-body | d3plus 三层及以上 | try-nested-in-try | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-081 | Try | except-handler | d2 双层 | try-nested-in-try | Try | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-TRY-082 | Try | except-handler | d3plus 三层及以上 | try-nested-in-try | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-083 | Try | if-arm | d3plus 三层及以上 | try-nested-in-loop | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-TRY-084 | Try | loop-body | d2 双层 | try-nested-in-loop | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-TRY-085 | Try | loop-body | d3plus 三层及以上 | try-nested-in-loop | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-086 | Try | with-body | d2 双层 | try-nested-in-with | Try | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-TRY-087 | Try | with-body | d3plus 三层及以上 | try-nested-in-with | Try | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-TRY-088 | Try | function-body | d1 单层 | try-in-func | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b50_face.pyc` | covered |
| JS-TRY-089 | Try | function-body | d2 双层 | try-in-func | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-090 | Try | function-body | d3plus 三层及以上 | try-in-func | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-091 | Try | if-arm | d2 双层 | try-in-func | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-092 | Try | if-arm | d3plus 三层及以上 | try-in-func | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-TRY-093 | Try | loop-body | d2 双层 | try-in-func | Try | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-TRY-094 | Try | loop-body | d3plus 三层及以上 | try-in-func | Try | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-TRY-095 | Try | with-body | d2 双层 | try-in-func | Try | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-TRY-096 | Try | with-body | d3plus 三层及以上 | try-in-func | Try | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-TRY-097 | Try | try-body | d2 双层 | try-in-func | Try | `test_repros/round2/x01_if_deep_hosts.pyc` | covered |
| JS-TRY-098 | Try | try-body | d3plus 三层及以上 | try-in-func | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-099 | Try | except-handler | d2 双层 | try-in-func | Try | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-TRY-100 | Try | except-handler | d3plus 三层及以上 | try-in-func | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-101 | Try | function-body | d2 双层 | try-in-class-body | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-102 | Try | function-body | d3plus 三层及以上 | try-in-class-body | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-103 | Try | if-arm | d3plus 三层及以上 | try-in-class-body | Try | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-TRY-104 | Try | loop-body | d3plus 三层及以上 | try-in-class-body | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-105 | Try | try-body | d2 双层 | try-in-class-body | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-TRY-106 | Try | try-body | d3plus 三层及以上 | try-in-class-body | Try | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-TRY-107 | Try | except-handler | d3plus 三层及以上 | try-in-class-body | Try | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-TRY-108 | Try | class-body | d1 单层 | try-in-class-body | Try | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-RAISE-001 | Raise | function-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-002 | Raise | module-level | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-003 | Raise | if-arm | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-004 | Raise | except-handler | d2 双层 | raise-bare | Raise | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-RAISE-005 | Raise | except-handler | d3plus 三层及以上 | raise-bare | Raise | `test_repros/round8/r8_11_deep_host_combo2.pyc` | covered |
| JS-RAISE-006 | Raise | finally-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-007 | Raise | try-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-008 | Raise | loop-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-009 | Raise | with-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-010 | Raise | match-case-body | d1 单层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-011 | Raise | nested-func-body | d2 双层 | raise-bare | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-012 | Raise | function-body | d1 单层 | raise-exc-call | Raise | `test_repros/round8/r8_09_deep_host_combo.pyc` | covered |
| JS-RAISE-013 | Raise | function-body | d2 双层 | raise-exc-call | Raise | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-RAISE-014 | Raise | module-level | d1 单层 | raise-exc-call | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-015 | Raise | if-arm | d2 双层 | raise-exc-call | Raise | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-RAISE-016 | Raise | if-arm | d3plus 三层及以上 | raise-exc-call | Raise | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-RAISE-017 | Raise | except-handler | d2 双层 | raise-exc-call | Raise | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-RAISE-018 | Raise | except-handler | d3plus 三层及以上 | raise-exc-call | Raise | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-RAISE-019 | Raise | finally-body | d1 单层 | raise-exc-call | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-020 | Raise | try-body | d3plus 三层及以上 | raise-exc-call | Raise | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-RAISE-021 | Raise | loop-body | d1 单层 | raise-exc-call | Raise | `test_repros/round2/r2_15_reraise.pyc` | uncovered |
| JS-RAISE-022 | Raise | match-case-body | d2 双层 | raise-exc-call | Raise | `test_repros/round5/rec1_synth_b61c_fusion2.pyc` | covered |
| JS-RAISE-023 | Raise | match-case-body | d3plus 三层及以上 | raise-exc-call | Raise | `test_repros/round5/rec1_synth_g3a_b61_deephost.pyc` | covered |
| JS-RAISE-024 | Raise | function-body | d2 双层 | raise-exc-class | Raise | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-RAISE-025 | Raise | if-arm | d2 双层 | raise-exc-class | Raise | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-RAISE-026 | Raise | if-arm | d3plus 三层及以上 | raise-exc-class | Raise | `test_repros/round8/r8_09_deep_host_combo.pyc` | covered |
| JS-RAISE-027 | Raise | except-handler | d2 双层 | raise-exc-class | Raise | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RAISE-028 | Raise | except-handler | d2 双层 | raise-from | Raise | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-RAISE-029 | Raise | try-body | d3plus 三层及以上 | raise-from | Raise | `test_repros/round9/n9v9_stmt_sweep.pyc` | covered |
| JS-RAISE-030 | Raise | function-body | d1 单层 | raise-ternary-exc | Raise | `test_repros/round8/r8_10_expr_cross_stmt.pyc` | covered |
| JS-RAISE-031 | Raise | except-handler | d2 双层 | raise-in-handler | Raise | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RAISE-032 | Raise | except-handler | d3plus 三层及以上 | raise-in-handler | Raise | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-RAISE-033 | Raise | try-body | d3plus 三层及以上 | raise-in-try-body | Raise | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-RAISE-034 | Raise | if-arm | d3plus 三层及以上 | raise-in-loop | Raise | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-RAISE-035 | Raise | except-handler | d3plus 三层及以上 | raise-in-loop | Raise | `test_repros/round8/r8_11_deep_host_combo2.pyc` | covered |
| JS-RAISE-036 | Raise | try-body | d3plus 三层及以上 | raise-in-loop | Raise | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-RAISE-037 | Raise | match-case-body | d3plus 三层及以上 | raise-in-loop | Raise | `test_repros/round5/rec1_synth_g3a_b61_deephost.pyc` | covered |
| JS-RAISE-038 | Raise | try-body | d3plus 三层及以上 | raise-in-with | Raise | `test_repros/round9/n9v9_stmt_sweep.pyc` | covered |
| JS-RAISE-039 | Raise | match-case-body | d3plus 三层及以上 | raise-in-with | Raise | `test_repros/round5/rec1_synth_g3b_b61_deephost.pyc` | covered |
| JS-ASSERT-001 | Assert | function-body | d1 单层 | assert-plain | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-002 | Assert | module-level | d1 单层 | assert-plain | Assert | `test_repros/round2/m01_docstring_order.pyc` | covered |
| JS-ASSERT-003 | Assert | if-arm | d3plus 三层及以上 | assert-plain | Assert | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-ASSERT-004 | Assert | else-arm | d1 单层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-005 | Assert | loop-body | d1 单层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-006 | Assert | try-body | d1 单层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-007 | Assert | except-handler | d2 双层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-008 | Assert | with-body | d1 单层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-009 | Assert | match-case-body | d2 双层 | assert-plain | Assert | `test_repros/round5/rec1_synth_b61d_assert2.pyc` | covered |
| JS-ASSERT-010 | Assert | match-case-body | d3plus 三层及以上 | assert-plain | Assert | `test_repros/round5/rec1_synth_g3a_b61_deephost.pyc` | covered |
| JS-ASSERT-011 | Assert | nested-func-body | d2 双层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-012 | Assert | finally-body | d1 单层 | assert-plain | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-013 | Assert | function-body | d1 单层 | assert-with-msg | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-014 | Assert | function-body | d2 双层 | assert-with-msg | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-015 | Assert | module-level | d1 单层 | assert-with-msg | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-016 | Assert | if-arm | d2 双层 | assert-with-msg | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-017 | Assert | if-arm | d3plus 三层及以上 | assert-with-msg | Assert | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-ASSERT-018 | Assert | else-arm | d1 单层 | assert-with-msg | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-019 | Assert | loop-body | d2 双层 | assert-with-msg | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-020 | Assert | loop-body | d3plus 三层及以上 | assert-with-msg | Assert | `test_repros/round9/n9v9_stmt_sweep.pyc` | covered |
| JS-ASSERT-021 | Assert | try-body | d1 单层 | assert-with-msg | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-022 | Assert | except-handler | d2 双层 | assert-with-msg | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-023 | Assert | with-body | d2 双层 | assert-with-msg | Assert | `test_repros/round8/r8_09_deep_host_combo.pyc` | covered |
| JS-ASSERT-024 | Assert | match-case-body | d2 双层 | assert-with-msg | Assert | `test_repros/round5/rec1_synth_b61d_assert2.pyc` | covered |
| JS-ASSERT-025 | Assert | match-case-body | d3plus 三层及以上 | assert-with-msg | Assert | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-ASSERT-026 | Assert | nested-func-body | d2 双层 | assert-with-msg | Assert | `test_repros/round1/r1_14_assert_mixed.pyc` | uncovered |
| JS-ASSERT-027 | Assert | function-body | d1 单层 | assert-test-ternary | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-028 | Assert | function-body | d1 单层 | assert-test-boolop | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-029 | Assert | module-level | d1 单层 | assert-test-boolop | Assert | `test_repros/round2/m08_module_stmts.pyc` | covered |
| JS-ASSERT-030 | Assert | function-body | d1 单层 | assert-test-call | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-031 | Assert | function-body | d1 单层 | assert-in-func | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-032 | Assert | function-body | d2 双层 | assert-in-func | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-033 | Assert | if-arm | d2 双层 | assert-in-func | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-034 | Assert | if-arm | d3plus 三层及以上 | assert-in-func | Assert | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-ASSERT-035 | Assert | loop-body | d2 双层 | assert-in-func | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-036 | Assert | loop-body | d3plus 三层及以上 | assert-in-func | Assert | `test_repros/round9/n9v9_stmt_sweep.pyc` | covered |
| JS-ASSERT-037 | Assert | with-body | d2 双层 | assert-in-func | Assert | `test_repros/round8/r8_09_deep_host_combo.pyc` | covered |
| JS-ASSERT-038 | Assert | match-case-body | d2 双层 | assert-in-func | Assert | `test_repros/round5/rec1_synth_b61d_assert2.pyc` | covered |
| JS-ASSERT-039 | Assert | match-case-body | d3plus 三层及以上 | assert-in-func | Assert | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-ASSERT-040 | Assert | if-arm | d3plus 三层及以上 | assert-in-loop | Assert | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-ASSERT-041 | Assert | loop-body | d2 双层 | assert-in-loop | Assert | `test_repros/round8/r8_07_assert_forms.pyc` | covered |
| JS-ASSERT-042 | Assert | loop-body | d3plus 三层及以上 | assert-in-loop | Assert | `test_repros/round9/n9v9_stmt_sweep.pyc` | covered |
| JS-ASSERT-043 | Assert | match-case-body | d3plus 三层及以上 | assert-in-loop | Assert | `test_repros/round5/rec1_synth_g3a_b61_deephost.pyc` | covered |
| JS-ASSERT-044 | Assert | if-arm | d3plus 三层及以上 | assert-in-with | Assert | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-ASSERT-045 | Assert | with-body | d2 双层 | assert-in-with | Assert | `test_repros/round8/r8_09_deep_host_combo.pyc` | covered |
| JS-ASSERT-046 | Assert | match-case-body | d3plus 三层及以上 | assert-in-with | Assert | `test_repros/round5/rec1_synth_g3b_b61_deephost.pyc` | covered |
| JS-IMPORT-001 | Import | module-level | d1 单层 | import-plain | Import | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IMPORT-002 | Import | function-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-003 | Import | class-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-004 | Import | try-body | d1 单层 | import-plain | Import | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-IMPORT-005 | Import | except-handler | d1 单层 | import-plain | Import | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-IMPORT-006 | Import | except-handler | d2 双层 | import-plain | Import | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-IMPORT-007 | Import | except-handler | d3plus 三层及以上 | import-plain | Import | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-IMPORT-008 | Import | else-of-try | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-009 | Import | finally-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-010 | Import | if-arm | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-011 | Import | with-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-012 | Import | loop-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-013 | Import | match-case-body | d1 单层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-014 | Import | nested-func-body | d2 双层 | import-plain | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-015 | Import | module-level | d1 单层 | import-as | Import | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-IMPORT-016 | Import | function-body | d1 单层 | import-as | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-017 | Import | class-body | d1 单层 | import-as | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-018 | Import | try-body | d1 单层 | import-as | Import | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-IMPORT-019 | Import | except-handler | d2 双层 | import-as | Import | `test_repros/round4/c4_15_star_import.pyc` | uncovered |
| JS-IMPORT-020 | Import | with-body | d3plus 三层及以上 | import-as | Import | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-IMPORT-021 | Import | module-level | d1 单层 | import-from | Import | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IMPORT-022 | Import | function-body | d1 单层 | import-from | Import | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-IMPORT-023 | Import | try-body | d2 双层 | import-from | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-024 | Import | except-handler | d2 双层 | import-from | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-025 | Import | except-handler | d3plus 三层及以上 | import-from | Import | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-IMPORT-026 | Import | else-of-try | d2 双层 | import-from | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-027 | Import | finally-body | d2 双层 | import-from | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-028 | Import | if-arm | d3plus 三层及以上 | import-from | Import | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-IMPORT-029 | Import | module-level | d1 单层 | import-from-as | Import | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-IMPORT-030 | Import | except-handler | d2 双层 | import-from-as | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-031 | Import | except-handler | d3plus 三层及以上 | import-from-as | Import | `test_repros/round10/r10_04_import_try_cross.pyc` | covered |
| JS-IMPORT-032 | Import | try-body | d1 单层 | import-in-try | Import | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-IMPORT-033 | Import | try-body | d2 双层 | import-in-try | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-034 | Import | except-handler | d1 单层 | import-in-handler | Import | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-IMPORT-035 | Import | except-handler | d2 双层 | import-in-handler | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-036 | Import | except-handler | d3plus 三层及以上 | import-in-handler | Import | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-IMPORT-037 | Import | else-of-try | d2 双层 | import-in-else-of-try | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-038 | Import | finally-body | d2 双层 | import-in-finally | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-039 | Import | function-body | d1 单层 | import-in-func | Import | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-IMPORT-040 | Import | try-body | d2 双层 | import-in-func | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-041 | Import | except-handler | d2 双层 | import-in-func | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-042 | Import | except-handler | d3plus 三层及以上 | import-in-func | Import | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-IMPORT-043 | Import | else-of-try | d2 双层 | import-in-func | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-044 | Import | finally-body | d2 双层 | import-in-func | Import | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-IMPORT-045 | Import | if-arm | d3plus 三层及以上 | import-in-func | Import | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-IMPORT-046 | Import | with-body | d3plus 三层及以上 | import-in-func | Import | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-IMPORT-047 | Import | if-arm | d3plus 三层及以上 | import-in-class-body | Import | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-GLOBAL-001 | Global | module-level | d1 单层 | global-single | Global | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b75_face.pyc` | covered |
| JS-GLOBAL-002 | Global | function-body | d1 单层 | global-single | Global | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-GLOBAL-003 | Global | class-body | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-004 | Global | nested-func-body | d2 双层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-005 | Global | if-arm | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-006 | Global | loop-body | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-007 | Global | try-body | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-008 | Global | except-handler | d2 双层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-009 | Global | with-body | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-010 | Global | match-case-body | d1 单层 | global-single | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-011 | Global | module-level | d1 单层 | global-multiple | Global | `test_repros/round10/r10_15_global_hosts.pyc` | covered |
| JS-GLOBAL-012 | Global | function-body | d1 单层 | global-multiple | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-013 | Global | class-body | d1 单层 | global-multiple | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-014 | Global | nested-func-body | d2 双层 | global-multiple | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-015 | Global | if-arm | d1 单层 | global-multiple | Global | `test_repros/round10/r10_12_global_deep.pyc` | uncovered |
| JS-GLOBAL-016 | Global | module-level | d1 单层 | global-at-module | Global | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b75_face.pyc` | covered |
| JS-GLOBAL-017 | Global | function-body | d1 单层 | global-in-func | Global | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-GLOBAL-018 | Global | module-level | d1 单层 | global-with-same-name-assign | Global | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b75_face.pyc` | covered |
| JS-GLOBAL-019 | Global | function-body | d1 单层 | global-with-same-name-assign | Global | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-NONLOCAL-001 | global_nonlocal | function-body | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-002 | global_nonlocal | nested-func-body | d2 双层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-003 | global_nonlocal | class-body | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-004 | global_nonlocal | if-arm | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-005 | global_nonlocal | loop-body | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-006 | global_nonlocal | try-body | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-007 | global_nonlocal | except-handler | d2 双层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-008 | global_nonlocal | with-body | d1 单层 | nonlocal-single | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-009 | global_nonlocal | function-body | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-010 | global_nonlocal | nested-func-body | d2 双层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-011 | global_nonlocal | class-body | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-012 | global_nonlocal | if-arm | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-013 | global_nonlocal | loop-body | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-014 | global_nonlocal | try-body | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-015 | global_nonlocal | except-handler | d2 双层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-016 | global_nonlocal | with-body | d1 单层 | nonlocal-multiple | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-017 | global_nonlocal | function-body | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-018 | global_nonlocal | nested-func-body | d2 双层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-019 | global_nonlocal | class-body | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-020 | global_nonlocal | if-arm | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-021 | global_nonlocal | loop-body | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-022 | global_nonlocal | try-body | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-023 | global_nonlocal | except-handler | d2 双层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-024 | global_nonlocal | with-body | d1 单层 | nonlocal-in-nested-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-025 | global_nonlocal | function-body | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-026 | global_nonlocal | nested-func-body | d2 双层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-027 | global_nonlocal | class-body | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-028 | global_nonlocal | if-arm | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-029 | global_nonlocal | loop-body | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-030 | global_nonlocal | try-body | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-031 | global_nonlocal | except-handler | d2 双层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-032 | global_nonlocal | with-body | d1 单层 | nonlocal-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-033 | global_nonlocal | function-body | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-034 | global_nonlocal | nested-func-body | d2 双层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-035 | global_nonlocal | class-body | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-036 | global_nonlocal | if-arm | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-037 | global_nonlocal | loop-body | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-038 | global_nonlocal | try-body | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-039 | global_nonlocal | except-handler | d2 双层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-NONLOCAL-040 | global_nonlocal | with-body | d1 单层 | nonlocal-in-class-in-func | global_nonlocal | `test_repros/round10/r10_14_nonlocal_deep.pyc` | uncovered |
| JS-AWAIT-001 | Await | async-func-body | d1 单层 | await-in-async-def | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-002 | Await | function-body | d1 单层 | await-in-async-def | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-003 | Await | comprehension-scope | d2 双层 | await-in-async-def | Await | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-AWAIT-004 | Await | comprehension-scope | d3plus 三层及以上 | await-in-async-def | Await | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-AWAIT-005 | Await | if-arm | d1 单层 | await-in-async-def | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-006 | Await | loop-body | d1 单层 | await-in-async-def | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-007 | Await | async-func-body | d1 单层 | await-in-async-with | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-008 | Await | function-body | d1 单层 | await-in-async-with | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-009 | Await | comprehension-scope | d1 单层 | await-in-async-with | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-010 | Await | if-arm | d1 单层 | await-in-async-with | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-011 | Await | loop-body | d1 单层 | await-in-async-with | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-012 | Await | async-func-body | d1 单层 | await-in-async-for | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-013 | Await | function-body | d1 单层 | await-in-async-for | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-014 | Await | comprehension-scope | d3plus 三层及以上 | await-in-async-for | Await | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-AWAIT-015 | Await | if-arm | d1 单层 | await-in-async-for | Await | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-AWAIT-016 | Await | comprehension-scope | d2 双层 | await-in-async-comp | Await | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-AWAIT-017 | Await | comprehension-scope | d3plus 三层及以上 | await-in-async-comp | Await | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-AWAIT-018 | Await | call-arg | d3plus 三层及以上 | await-in-call-arg | Await | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-AWAIT-019 | Await | return-value-expr | d2 双层 | await-in-return | Await | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-AWAIT-020 | Await | return-value-expr | d3plus 三层及以上 | await-in-return | Await | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-AWAIT-021 | Await | assign-rhs | d3plus 三层及以上 | await-in-assign | Await | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-AWAIT-022 | Await | binop-operand | d1 单层 | await-in-binop | Await | `test_repros/round4/rec1_synth_b47_ternary.pyc` | covered |
| JS-AWAIT-023 | Await | binop-operand | d3plus 三层及以上 | await-in-binop | Await | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-LISTCOMP-001 | ListComp | function-body | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-002 | ListComp | module-level | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-003 | ListComp | assign-rhs | d1 单层 | listcomp-single-for | ListComp | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-LISTCOMP-004 | ListComp | assign-rhs | d2 双层 | listcomp-single-for | ListComp | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-LISTCOMP-005 | ListComp | assign-rhs | d3plus 三层及以上 | listcomp-single-for | ListComp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-LISTCOMP-006 | ListComp | return-value-expr | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-LISTCOMP-007 | ListComp | return-value-expr | d2 双层 | listcomp-single-for | ListComp | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-LISTCOMP-008 | ListComp | return-value-expr | d3plus 三层及以上 | listcomp-single-for | ListComp | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-LISTCOMP-009 | ListComp | call-arg | d1 单层 | listcomp-single-for | ListComp | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-LISTCOMP-010 | ListComp | call-arg | d2 双层 | listcomp-single-for | ListComp | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-LISTCOMP-011 | ListComp | call-arg | d3plus 三层及以上 | listcomp-single-for | ListComp | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-LISTCOMP-012 | ListComp | comprehension-scope | d2 双层 | listcomp-single-for | ListComp | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-LISTCOMP-013 | ListComp | comprehension-if | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-014 | ListComp | comprehension-for | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-015 | ListComp | if-arm | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-016 | ListComp | loop-body | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-017 | ListComp | class-body | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-018 | ListComp | annotation-context | d1 单层 | listcomp-single-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-019 | ListComp | function-body | d1 单层 | listcomp-multi-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-020 | ListComp | module-level | d1 单层 | listcomp-multi-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-021 | ListComp | assign-rhs | d1 单层 | listcomp-multi-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-022 | ListComp | return-value-expr | d1 单层 | listcomp-multi-for | ListComp | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-LISTCOMP-023 | ListComp | call-arg | d1 单层 | listcomp-multi-for | ListComp | `test_repros/round5/probe_comp_min.pyc` | uncovered |
| JS-LISTCOMP-024 | ListComp | assign-rhs | d2 双层 | listcomp-async | ListComp | `test_repros/round4/rec1_synth_b112b_closure.pyc` | covered |
| JS-LISTCOMP-025 | ListComp | return-value-expr | d1 单层 | listcomp-async | ListComp | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-LISTCOMP-026 | ListComp | return-value-expr | d2 双层 | listcomp-async | ListComp | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-LISTCOMP-027 | ListComp | return-value-expr | d3plus 三层及以上 | listcomp-async | ListComp | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-LISTCOMP-028 | ListComp | return-value-expr | d1 单层 | listcomp-elt-ternary | ListComp | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-LISTCOMP-029 | ListComp | comprehension-scope | d2 双层 | listcomp-elt-ternary | ListComp | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-LISTCOMP-030 | ListComp | return-value-expr | d1 单层 | listcomp-elt-await | ListComp | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-LISTCOMP-031 | ListComp | return-value-expr | d3plus 三层及以上 | listcomp-elt-await | ListComp | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-LISTCOMP-032 | ListComp | call-arg | d1 单层 | listcomp-in-call-arg | ListComp | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-LISTCOMP-033 | ListComp | call-arg | d2 双层 | listcomp-in-call-arg | ListComp | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-LISTCOMP-034 | ListComp | call-arg | d3plus 三层及以上 | listcomp-in-call-arg | ListComp | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-LISTCOMP-035 | ListComp | assign-rhs | d1 单层 | listcomp-in-assign | ListComp | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-LISTCOMP-036 | ListComp | assign-rhs | d2 双层 | listcomp-in-assign | ListComp | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-LISTCOMP-037 | ListComp | assign-rhs | d3plus 三层及以上 | listcomp-in-assign | ListComp | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-LISTCOMP-038 | ListComp | return-value-expr | d1 单层 | listcomp-in-return | ListComp | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-LISTCOMP-039 | ListComp | return-value-expr | d2 双层 | listcomp-in-return | ListComp | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-LISTCOMP-040 | ListComp | return-value-expr | d3plus 三层及以上 | listcomp-in-return | ListComp | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-AWAITEXPR-001 | await_expr | condition-expr | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-002 | await_expr | return-value-expr | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-003 | await_expr | call-arg | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-004 | await_expr | assign-rhs | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-005 | await_expr | binop-operand | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-006 | await_expr | boolop-operand | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-007 | await_expr | await-operand | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-008 | await_expr | if-arm | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-009 | await_expr | comprehension-scope | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-010 | await_expr | match-guard | d1 单层 | awexpr-in-if-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-011 | await_expr | condition-expr | d1 单层 | awexpr-in-while-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-012 | await_expr | return-value-expr | d1 单层 | awexpr-in-while-cond | await_expr | `test_repros/round2/x09_funcdef_hosts.pyc` | uncovered |
| JS-AWAITEXPR-013 | await_expr | call-arg | d3plus 三层及以上 | awexpr-in-call-arg | await_expr | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-AWAITEXPR-014 | await_expr | return-value-expr | d2 双层 | awexpr-in-return | await_expr | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-AWAITEXPR-015 | await_expr | return-value-expr | d3plus 三层及以上 | awexpr-in-return | await_expr | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-AWAITEXPR-016 | await_expr | assign-rhs | d3plus 三层及以上 | awexpr-in-assign-rhs | await_expr | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-AWAITEXPR-017 | await_expr | binop-operand | d1 单层 | awexpr-in-binop | await_expr | `test_repros/round4/rec1_synth_b47_ternary.pyc` | covered |
| JS-AWAITEXPR-018 | await_expr | binop-operand | d3plus 三层及以上 | awexpr-in-binop | await_expr | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-AWAITEXPR-019 | await_expr | boolop-operand | d3plus 三层及以上 | awexpr-in-boolop | await_expr | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-AWAITEXPR-020 | await_expr | comprehension-scope | d2 双层 | awexpr-in-listcomp-elt | await_expr | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-AWAITEXPR-021 | await_expr | comprehension-scope | d3plus 三层及以上 | awexpr-in-listcomp-elt | await_expr | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-YIELD-001 | Yield | generator-func-body | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-002 | Yield | function-body | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-003 | Yield | try-body | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-004 | Yield | finally-body | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-005 | Yield | except-handler | d2 双层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-006 | Yield | loop-body | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-007 | Yield | condition-expr | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-008 | Yield | boolop-operand | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-009 | Yield | call-arg | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-010 | Yield | assign-rhs | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-011 | Yield | if-arm | d1 单层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-012 | Yield | nested-func-body | d2 双层 | yield-bare | Yield | `test_repros/round6/r6_15_yield_forms.pyc` | uncovered |
| JS-YIELD-013 | Yield | boolop-operand | d3plus 三层及以上 | yield-value | Yield | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_boolop.pyc` | covered |
| JS-YIELD-014 | Yield | call-arg | d3plus 三层及以上 | yield-value | Yield | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_arg.pyc` | covered |
| JS-YIELD-015 | Yield | assign-rhs | d3plus 三层及以上 | yield-value | Yield | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_assign.pyc` | covered |
| JS-YIELD-016 | Yield | boolop-operand | d3plus 三层及以上 | yield-in-boolop | Yield | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_boolop.pyc` | covered |
| JS-YIELD-017 | Yield | call-arg | d3plus 三层及以上 | yield-as-arg | Yield | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_arg.pyc` | covered |
| JS-YIELD-018 | Yield | assign-rhs | d3plus 三层及以上 | yield-in-assign | Yield | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_assign.pyc` | covered |
| JS-MATCHPAT-001 | Match | match-case-body | d2 双层 | pat-literal | Match | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-MATCHPAT-002 | Match | match-case-body | d3plus 三层及以上 | pat-literal | Match | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-MATCHPAT-003 | Match | pattern-value | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-004 | Match | pattern-class | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-005 | Match | pattern-sequence | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-006 | Match | pattern-mapping | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-007 | Match | pattern-capture | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-008 | Match | pattern-or | d2 双层 | pat-literal | Match | `test_repros/round5/rec1_synth_b74d_guard_depth.pyc` | covered |
| JS-MATCHPAT-009 | Match | pattern-star | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-010 | Match | match-guard | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-011 | Match | function-body | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-012 | Match | match-subject | d1 单层 | pat-literal | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-013 | Match | match-case-body | d1 单层 | pat-singleton | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-014 | Match | pattern-value | d1 单层 | pat-singleton | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-015 | Match | pattern-class | d1 单层 | pat-singleton | Match | `test_repros/round4/r4_06_match_or.pyc` | uncovered |
| JS-MATCHPAT-016 | Match | match-case-body | d2 双层 | pat-sequence | Match | `test_repros/round10/r10_15_global_hosts.pyc` | covered |
| JS-MATCHPAT-017 | Match | match-case-body | d3plus 三层及以上 | pat-sequence | Match | `test_repros/round5/rec1_synth_g2b_with_match_cross.pyc` | covered |
| JS-MATCHPAT-018 | Match | match-case-body | d2 双层 | pat-mapping | Match | `test_repros/round5/rec1_synth_b61c_fusion2.pyc` | covered |
| JS-MATCHPAT-019 | Match | match-case-body | d3plus 三层及以上 | pat-mapping | Match | `test_repros/round5/rec1_synth_g3a_b61_deephost.pyc` | covered |
| JS-MATCHPAT-020 | Match | match-case-body | d2 双层 | pat-class | Match | `test_repros/round10/r10_15_global_hosts.pyc` | covered |
| JS-MATCHPAT-021 | Match | match-case-body | d3plus 三层及以上 | pat-class | Match | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-MATCHPAT-022 | Match | pattern-sequence | d2 双层 | pat-class | Match | `test_repros/round5/rec1_synth_b74d_guard_depth.pyc` | covered |
| JS-MATCHPAT-023 | Match | pattern-capture | d2 双层 | pat-class | Match | `test_repros/round5/rec1_synth_b61c_fusion2.pyc` | covered |
| JS-MATCHPAT-024 | Match | match-case-body | d2 双层 | pat-capture | Match | `test_repros/round5/rec1_synth_b61c_fusion2.pyc` | covered |
| JS-MATCHPAT-025 | Match | pattern-class | d2 双层 | pat-capture | Match | `test_repros/round10/r10_15_global_hosts.pyc` | covered |
| JS-MATCHPAT-026 | Match | pattern-class | d3plus 三层及以上 | pat-capture | Match | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-MATCHPAT-027 | Match | pattern-sequence | d2 双层 | pat-capture | Match | `test_repros/round10/r10_15_global_hosts.pyc` | covered |
| JS-MATCHPAT-028 | Match | pattern-sequence | d3plus 三层及以上 | pat-capture | Match | `test_repros/round5/rec1_synth_g2b_with_match_cross.pyc` | covered |
| JS-MATCHPAT-029 | Match | pattern-mapping | d2 双层 | pat-capture | Match | `test_repros/round5/rec1_synth_b61c_fusion2.pyc` | covered |
| JS-MATCHPAT-030 | Match | pattern-mapping | d3plus 三层及以上 | pat-capture | Match | `test_repros/round5/rec1_synth_g3a_b61_deephost.pyc` | covered |
| JS-MATCHPAT-031 | Match | match-case-body | d2 双层 | pat-wildcard | Match | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-MATCHPAT-032 | Match | match-case-body | d3plus 三层及以上 | pat-wildcard | Match | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-MATCHPAT-033 | Match | match-case-body | d2 双层 | pat-or | Match | `test_repros/round5/rec1_synth_b74d_guard_depth.pyc` | covered |
| JS-MATCHPAT-034 | Match | pattern-sequence | d2 双层 | pat-star | Match | `test_repros/round10/r10_15_global_hosts.pyc` | covered |
| JS-MATCHPAT-035 | Match | match-case-body | d2 双层 | pat-with-guard | Match | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-MATCHPAT-036 | Match | match-case-body | d3plus 三层及以上 | pat-with-guard | Match | `test_repros/round5/rec1_synth_b122d_triple_nest.pyc` | covered |
| JS-MATCHPAT-037 | Match | match-case-body | d3plus 三层及以上 | pat-in-nested-match | Match | `test_repros/round5/rec1_synth_b122c_noguard_chain2.pyc` | covered |
| JS-WITH-001 | With | function-body | d1 单层 | with-single-item | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-002 | With | function-body | d2 双层 | with-single-item | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-003 | With | module-level | d1 单层 | with-single-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-004 | With | if-arm | d2 双层 | with-single-item | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-005 | With | if-arm | d3plus 三层及以上 | with-single-item | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-006 | With | loop-body | d2 双层 | with-single-item | With | `test_repros/round5/rec1_synth_b70a_wt_with_bc.pyc` | covered |
| JS-WITH-007 | With | loop-body | d3plus 三层及以上 | with-single-item | With | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WITH-008 | With | try-body | d2 双层 | with-single-item | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-009 | With | try-body | d3plus 三层及以上 | with-single-item | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-010 | With | except-handler | d2 双层 | with-single-item | With | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-WITH-011 | With | with-body | d3plus 三层及以上 | with-single-item | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-012 | With | with-item | d1 单层 | with-single-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-013 | With | match-case-body | d2 双层 | with-single-item | With | `test_repros/round5/rec1_synth_b93d_with_ret_case.pyc` | covered |
| JS-WITH-014 | With | match-case-body | d3plus 三层及以上 | with-single-item | With | `test_repros/round5/rec1_synth_g2a_with_match_cross.pyc` | covered |
| JS-WITH-015 | With | nested-func-body | d2 双层 | with-single-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-016 | With | else-arm | d3plus 三层及以上 | with-single-item | With | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WITH-017 | With | function-body | d1 单层 | with-multi-item | With | `test_repros/round2/x05_with_deep_hosts.pyc` | covered |
| JS-WITH-018 | With | module-level | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-019 | With | if-arm | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-020 | With | loop-body | d2 双层 | with-multi-item | With | `test_repros/round2/x05_with_deep_hosts.pyc` | covered |
| JS-WITH-021 | With | try-body | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-022 | With | except-handler | d2 双层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-023 | With | with-body | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-024 | With | with-item | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-025 | With | match-case-body | d2 双层 | with-multi-item | With | `test_repros/round5/rec1_synth_b93d_with_ret_case.pyc` | covered |
| JS-WITH-026 | With | nested-func-body | d2 双层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-027 | With | else-arm | d1 单层 | with-multi-item | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-028 | With | function-body | d1 单层 | with-as-target | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-029 | With | function-body | d2 双层 | with-as-target | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-030 | With | module-level | d1 单层 | with-as-target | With | `test_repros/round2/c05_class_with.pyc` | uncovered |
| JS-WITH-031 | With | if-arm | d2 双层 | with-as-target | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-032 | With | if-arm | d3plus 三层及以上 | with-as-target | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-033 | With | loop-body | d2 双层 | with-as-target | With | `test_repros/round2/x05_with_deep_hosts.pyc` | covered |
| JS-WITH-034 | With | loop-body | d3plus 三层及以上 | with-as-target | With | `test_repros/round2/x02_for_deep_hosts.pyc` | covered |
| JS-WITH-035 | With | try-body | d2 双层 | with-as-target | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-036 | With | try-body | d3plus 三层及以上 | with-as-target | With | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-WITH-037 | With | with-body | d3plus 三层及以上 | with-as-target | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-038 | With | match-case-body | d2 双层 | with-as-target | With | `test_repros/round5/rec1_synth_b93d_with_ret_case.pyc` | covered |
| JS-WITH-039 | With | match-case-body | d3plus 三层及以上 | with-as-target | With | `test_repros/round5/rec1_synth_g2a_with_match_cross.pyc` | covered |
| JS-WITH-040 | With | else-arm | d3plus 三层及以上 | with-as-target | With | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WITH-041 | With | if-arm | d3plus 三层及以上 | with-in-try | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-042 | With | try-body | d2 双层 | with-in-try | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-043 | With | try-body | d3plus 三层及以上 | with-in-try | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-044 | With | except-handler | d2 双层 | with-in-try | With | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-WITH-045 | With | with-body | d3plus 三层及以上 | with-in-try | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-046 | With | if-arm | d3plus 三层及以上 | with-in-loop | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-047 | With | loop-body | d2 双层 | with-in-loop | With | `test_repros/round2/x05_with_deep_hosts.pyc` | covered |
| JS-WITH-048 | With | loop-body | d3plus 三层及以上 | with-in-loop | With | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WITH-049 | With | try-body | d3plus 三层及以上 | with-in-loop | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-050 | With | function-body | d1 单层 | with-in-func | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-051 | With | function-body | d2 双层 | with-in-func | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-052 | With | if-arm | d2 双层 | with-in-func | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-053 | With | if-arm | d3plus 三层及以上 | with-in-func | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-054 | With | loop-body | d2 双层 | with-in-func | With | `test_repros/round2/x05_with_deep_hosts.pyc` | covered |
| JS-WITH-055 | With | loop-body | d3plus 三层及以上 | with-in-func | With | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WITH-056 | With | try-body | d2 双层 | with-in-func | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-057 | With | try-body | d3plus 三层及以上 | with-in-func | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-058 | With | except-handler | d2 双层 | with-in-func | With | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-WITH-059 | With | with-body | d3plus 三层及以上 | with-in-func | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-060 | With | match-case-body | d2 双层 | with-in-func | With | `test_repros/round5/rec1_synth_b93d_with_ret_case.pyc` | covered |
| JS-WITH-061 | With | match-case-body | d3plus 三层及以上 | with-in-func | With | `test_repros/round5/rec1_synth_g2a_with_match_cross.pyc` | covered |
| JS-WITH-062 | With | else-arm | d3plus 三层及以上 | with-in-func | With | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WITH-063 | With | if-arm | d3plus 三层及以上 | with-body-nested-with | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-064 | With | loop-body | d3plus 三层及以上 | with-body-nested-with | With | `test_repros/round2/x02_for_deep_hosts.pyc` | covered |
| JS-WITH-065 | With | try-body | d3plus 三层及以上 | with-body-nested-with | With | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-WITH-066 | With | with-body | d3plus 三层及以上 | with-body-nested-with | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-067 | With | match-case-body | d3plus 三层及以上 | with-body-nested-with | With | `test_repros/round5/rec1_synth_g2a_with_match_cross.pyc` | covered |
| JS-WITH-068 | With | match-case-body | d2 双层 | with-in-match-case | With | `test_repros/round5/rec1_synth_b93d_with_ret_case.pyc` | covered |
| JS-WITH-069 | With | match-case-body | d3plus 三层及以上 | with-in-match-case | With | `test_repros/round5/rec1_synth_g2a_with_match_cross.pyc` | covered |
| JS-WITH-070 | With | function-body | d1 单层 | with-item-ternary | With | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-WITH-071 | With | function-body | d1 单层 | with-item-call | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-072 | With | function-body | d2 双层 | with-item-call | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-073 | With | if-arm | d2 双层 | with-item-call | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-074 | With | if-arm | d3plus 三层及以上 | with-item-call | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-075 | With | loop-body | d2 双层 | with-item-call | With | `test_repros/round2/x05_with_deep_hosts.pyc` | covered |
| JS-WITH-076 | With | loop-body | d3plus 三层及以上 | with-item-call | With | `test_repros/round2/x02_for_deep_hosts.pyc` | covered |
| JS-WITH-077 | With | try-body | d2 双层 | with-item-call | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-078 | With | try-body | d3plus 三层及以上 | with-item-call | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-079 | With | except-handler | d2 双层 | with-item-call | With | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-WITH-080 | With | with-body | d3plus 三层及以上 | with-item-call | With | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WITH-081 | With | match-case-body | d2 双层 | with-item-call | With | `test_repros/round5/rec1_synth_b93d_with_ret_case.pyc` | covered |
| JS-WITH-082 | With | match-case-body | d3plus 三层及以上 | with-item-call | With | `test_repros/round5/rec1_synth_g2a_with_match_cross.pyc` | covered |
| JS-WITH-083 | With | else-arm | d3plus 三层及以上 | with-item-call | With | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-MATCHSTMT-001 | match_statement | module-level | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-002 | match_statement | function-body | d1 单层 | msingle-case | match_statement | `test_repros/round2/x01_if_deep_hosts.pyc` | covered |
| JS-MATCHSTMT-003 | match_statement | if-arm | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-004 | match_statement | loop-body | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-005 | match_statement | try-body | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-006 | match_statement | except-handler | d2 双层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-007 | match_statement | with-body | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-008 | match_statement | match-case-body | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-009 | match_statement | class-body | d1 单层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-010 | match_statement | nested-func-body | d2 双层 | msingle-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-011 | match_statement | module-level | d1 单层 | mmulti-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-012 | match_statement | function-body | d1 单层 | mmulti-case | match_statement | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-MATCHSTMT-013 | match_statement | if-arm | d2 双层 | mmulti-case | match_statement | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-MATCHSTMT-014 | match_statement | if-arm | d3plus 三层及以上 | mmulti-case | match_statement | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-MATCHSTMT-015 | match_statement | loop-body | d2 双层 | mmulti-case | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-016 | match_statement | try-body | d2 双层 | mmulti-case | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-017 | match_statement | except-handler | d2 双层 | mmulti-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-018 | match_statement | with-body | d2 双层 | mmulti-case | match_statement | `test_repros/round5/rec1_synth_b93c_alt3.pyc` | covered |
| JS-MATCHSTMT-019 | match_statement | with-body | d3plus 三层及以上 | mmulti-case | match_statement | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-MATCHSTMT-020 | match_statement | match-case-body | d2 双层 | mmulti-case | match_statement | `test_repros/round5/rec1_synth_b122c_noguard_chain2.pyc` | covered |
| JS-MATCHSTMT-021 | match_statement | match-case-body | d3plus 三层及以上 | mmulti-case | match_statement | `test_repros/round5/rec1_synth_b122d_triple_nest.pyc` | covered |
| JS-MATCHSTMT-022 | match_statement | class-body | d1 单层 | mmulti-case | match_statement | `test_repros/round4/c4_04_match_patterns.pyc` | uncovered |
| JS-MATCHSTMT-023 | match_statement | function-body | d1 单层 | mhas-wildcard | match_statement | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-MATCHSTMT-024 | match_statement | if-arm | d2 双层 | mhas-wildcard | match_statement | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-MATCHSTMT-025 | match_statement | if-arm | d3plus 三层及以上 | mhas-wildcard | match_statement | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-MATCHSTMT-026 | match_statement | loop-body | d2 双层 | mhas-wildcard | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-027 | match_statement | try-body | d2 双层 | mhas-wildcard | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-028 | match_statement | with-body | d2 双层 | mhas-wildcard | match_statement | `test_repros/round5/rec1_synth_g2a_with_match_cross.pyc` | covered |
| JS-MATCHSTMT-029 | match_statement | with-body | d3plus 三层及以上 | mhas-wildcard | match_statement | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-MATCHSTMT-030 | match_statement | match-case-body | d2 双层 | mhas-wildcard | match_statement | `test_repros/round5/rec1_synth_b122c_noguard_chain2.pyc` | covered |
| JS-MATCHSTMT-031 | match_statement | match-case-body | d3plus 三层及以上 | mhas-wildcard | match_statement | `test_repros/round5/rec1_synth_b122d_triple_nest.pyc` | covered |
| JS-MATCHSTMT-032 | match_statement | function-body | d1 单层 | mhas-guard | match_statement | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-MATCHSTMT-033 | match_statement | if-arm | d2 双层 | mhas-guard | match_statement | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-MATCHSTMT-034 | match_statement | loop-body | d2 双层 | mhas-guard | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-035 | match_statement | try-body | d2 双层 | mhas-guard | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-036 | match_statement | with-body | d2 双层 | mhas-guard | match_statement | `test_repros/round5/rec1_synth_b93c_alt3.pyc` | covered |
| JS-MATCHSTMT-037 | match_statement | with-body | d3plus 三层及以上 | mhas-guard | match_statement | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-MATCHSTMT-038 | match_statement | match-case-body | d2 双层 | mhas-guard | match_statement | `test_repros/round5/rec1_synth_b74e_guard_battery2.pyc` | covered |
| JS-MATCHSTMT-039 | match_statement | match-case-body | d3plus 三层及以上 | mhas-guard | match_statement | `test_repros/round5/rec1_synth_b122d_triple_nest.pyc` | covered |
| JS-MATCHSTMT-040 | match_statement | if-arm | d3plus 三层及以上 | min-loop | match_statement | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-MATCHSTMT-041 | match_statement | loop-body | d2 双层 | min-loop | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-042 | match_statement | with-body | d3plus 三层及以上 | min-loop | match_statement | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-MATCHSTMT-043 | match_statement | match-case-body | d3plus 三层及以上 | min-loop | match_statement | `test_repros/round5/rec1_synth_g5a_b122_nestnoguard.pyc` | covered |
| JS-MATCHSTMT-044 | match_statement | try-body | d2 双层 | min-try | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-045 | match_statement | with-body | d3plus 三层及以上 | min-try | match_statement | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-MATCHSTMT-046 | match_statement | function-body | d1 单层 | min-func | match_statement | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-MATCHSTMT-047 | match_statement | if-arm | d2 双层 | min-func | match_statement | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-MATCHSTMT-048 | match_statement | if-arm | d3plus 三层及以上 | min-func | match_statement | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-MATCHSTMT-049 | match_statement | loop-body | d2 双层 | min-func | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-050 | match_statement | try-body | d2 双层 | min-func | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-051 | match_statement | with-body | d2 双层 | min-func | match_statement | `test_repros/round5/rec1_synth_b93c_alt3.pyc` | covered |
| JS-MATCHSTMT-052 | match_statement | with-body | d3plus 三层及以上 | min-func | match_statement | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-MATCHSTMT-053 | match_statement | match-case-body | d2 双层 | min-func | match_statement | `test_repros/round5/rec1_synth_b122c_noguard_chain2.pyc` | covered |
| JS-MATCHSTMT-054 | match_statement | match-case-body | d3plus 三层及以上 | min-func | match_statement | `test_repros/round5/rec1_synth_b122d_triple_nest.pyc` | covered |
| JS-MATCHSTMT-055 | match_statement | function-body | d1 单层 | mcase-body-nested-if | match_statement | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-MATCHSTMT-056 | match_statement | if-arm | d2 双层 | mcase-body-nested-if | match_statement | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-MATCHSTMT-057 | match_statement | loop-body | d2 双层 | mcase-body-nested-if | match_statement | `test_repros/round5/rec1_synth_g1b_guard_depth.pyc` | covered |
| JS-MATCHSTMT-058 | match_statement | with-body | d2 双层 | mcase-body-nested-if | match_statement | `test_repros/round5/rec1_synth_g3b_b61_deephost.pyc` | covered |
| JS-MATCHSTMT-059 | match_statement | with-body | d3plus 三层及以上 | mcase-body-nested-if | match_statement | `test_repros/round5/rec1_synth_g1a_guard_depth.pyc` | covered |
| JS-MATCHSTMT-060 | match_statement | match-case-body | d3plus 三层及以上 | mnested-match | match_statement | `test_repros/round5/rec1_synth_b122d_triple_nest.pyc` | covered |
| JS-BREAK-001 | Break | loop-body | d3plus 三层及以上 | break-in-for | Break | `test_repros/round2/c13_class_misc.pyc` | covered |
| JS-BREAK-002 | Break | loop-else | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-003 | Break | try-body | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-004 | Break | except-handler | d3plus 三层及以上 | break-in-for | Break | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-BREAK-005 | Break | finally-body | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-006 | Break | with-body | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-007 | Break | match-case-body | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-008 | Break | if-arm | d3plus 三层及以上 | break-in-for | Break | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BREAK-009 | Break | function-body | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-010 | Break | module-level | d1 单层 | break-in-for | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-011 | Break | loop-body | d3plus 三层及以上 | break-in-while | Break | `test_repros/round2/c13_class_misc.pyc` | covered |
| JS-BREAK-012 | Break | loop-else | d1 单层 | break-in-while | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-013 | Break | try-body | d1 单层 | break-in-while | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-014 | Break | except-handler | d3plus 三层及以上 | break-in-while | Break | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-BREAK-015 | Break | finally-body | d1 单层 | break-in-while | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-016 | Break | with-body | d3plus 三层及以上 | break-in-while | Break | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BREAK-017 | Break | match-case-body | d1 单层 | break-in-while | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-018 | Break | if-arm | d3plus 三层及以上 | break-in-while | Break | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BREAK-019 | Break | function-body | d1 单层 | break-in-while | Break | `test_repros/round7/r7v7r_b120_break.pyc` | uncovered |
| JS-BREAK-020 | Break | except-handler | d3plus 三层及以上 | break-in-handler | Break | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-BREAK-021 | Break | with-body | d3plus 三层及以上 | break-in-with | Break | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BREAK-022 | Break | if-arm | d3plus 三层及以上 | break-in-with | Break | `test_repros/round5/rec1_synth_b70a_wt_with_bc.pyc` | covered |
| JS-BREAK-023 | Break | loop-body | d3plus 三层及以上 | break-in-if-arm | Break | `test_repros/round2/c13_class_misc.pyc` | covered |
| JS-BREAK-024 | Break | except-handler | d3plus 三层及以上 | break-in-if-arm | Break | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-BREAK-025 | Break | with-body | d3plus 三层及以上 | break-in-if-arm | Break | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BREAK-026 | Break | if-arm | d3plus 三层及以上 | break-in-if-arm | Break | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-BREAK-027 | Break | loop-body | d3plus 三层及以上 | break-target-outer | Break | `test_repros/round2/c13_class_misc.pyc` | covered |
| JS-BREAK-028 | Break | except-handler | d3plus 三层及以上 | break-target-outer | Break | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-BREAK-029 | Break | if-arm | d3plus 三层及以上 | break-target-outer | Break | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-BREAK-030 | Break | loop-body | d3plus 三层及以上 | break-in-nested-loop | Break | `test_repros/round2/c13_class_misc.pyc` | covered |
| JS-BREAK-031 | Break | except-handler | d3plus 三层及以上 | break-in-nested-loop | Break | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-BREAK-032 | Break | if-arm | d3plus 三层及以上 | break-in-nested-loop | Break | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-CONTINUE-001 | Continue | loop-body | d2 双层 | continue-in-for | Continue | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-CONTINUE-002 | Continue | loop-body | d3plus 三层及以上 | continue-in-for | Continue | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-CONTINUE-003 | Continue | loop-else | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-004 | Continue | try-body | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-005 | Continue | except-handler | d3plus 三层及以上 | continue-in-for | Continue | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-CONTINUE-006 | Continue | finally-body | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-007 | Continue | with-body | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-008 | Continue | match-case-body | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-009 | Continue | if-arm | d2 双层 | continue-in-for | Continue | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-CONTINUE-010 | Continue | if-arm | d3plus 三层及以上 | continue-in-for | Continue | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-CONTINUE-011 | Continue | function-body | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-012 | Continue | module-level | d1 单层 | continue-in-for | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-013 | Continue | loop-body | d2 双层 | continue-in-while | Continue | `test_repros/round8/r8v8rev3_b104_exprtail_battery.pyc` | covered |
| JS-CONTINUE-014 | Continue | loop-body | d3plus 三层及以上 | continue-in-while | Continue | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-CONTINUE-015 | Continue | loop-else | d1 单层 | continue-in-while | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-016 | Continue | try-body | d1 单层 | continue-in-while | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-017 | Continue | except-handler | d3plus 三层及以上 | continue-in-while | Continue | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-CONTINUE-018 | Continue | finally-body | d1 单层 | continue-in-while | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-019 | Continue | with-body | d1 单层 | continue-in-while | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-020 | Continue | match-case-body | d1 单层 | continue-in-while | Continue | `test_repros/round9/r9_02_b2_dual_continue.pyc` | uncovered |
| JS-CONTINUE-021 | Continue | if-arm | d3plus 三层及以上 | continue-in-while | Continue | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-CONTINUE-022 | Continue | except-handler | d3plus 三层及以上 | continue-in-handler | Continue | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-CONTINUE-023 | Continue | loop-body | d3plus 三层及以上 | continue-in-with | Continue | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-CONTINUE-024 | Continue | if-arm | d3plus 三层及以上 | continue-in-with | Continue | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-CONTINUE-025 | Continue | if-arm | d3plus 三层及以上 | continue-in-match-case | Continue | `test_repros/round2/x02_for_deep_hosts.pyc` | covered |
| JS-CONTINUE-026 | Continue | loop-body | d3plus 三层及以上 | continue-in-if-arm | Continue | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-CONTINUE-027 | Continue | except-handler | d3plus 三层及以上 | continue-in-if-arm | Continue | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-CONTINUE-028 | Continue | if-arm | d2 双层 | continue-in-if-arm | Continue | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-CONTINUE-029 | Continue | if-arm | d3plus 三层及以上 | continue-in-if-arm | Continue | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` | covered |
| JS-CONTINUE-030 | Continue | loop-body | d3plus 三层及以上 | continue-target-outer | Continue | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-CONTINUE-031 | Continue | except-handler | d3plus 三层及以上 | continue-target-outer | Continue | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-CONTINUE-032 | Continue | if-arm | d3plus 三层及以上 | continue-target-outer | Continue | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-CONTINUE-033 | Continue | loop-body | d3plus 三层及以上 | continue-in-nested-loop | Continue | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-CONTINUE-034 | Continue | except-handler | d3plus 三层及以上 | continue-in-nested-loop | Continue | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-CONTINUE-035 | Continue | if-arm | d3plus 三层及以上 | continue-in-nested-loop | Continue | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WHILE-001 | While | module-level | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-002 | While | function-body | d1 单层 | while-true | While | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-WHILE-003 | While | function-body | d2 双层 | while-true | While | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-WHILE-004 | While | class-body | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-005 | While | if-arm | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-006 | While | loop-body | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-007 | While | try-body | d3plus 三层及以上 | while-true | While | `test_repros/round2/x04_try_deep_hosts.pyc` | covered |
| JS-WHILE-008 | While | except-handler | d2 双层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-009 | While | with-body | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-010 | While | match-case-body | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-011 | While | nested-func-body | d2 双层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-012 | While | else-arm | d1 单层 | while-true | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-013 | While | module-level | d1 单层 | while-cond-ternary | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-014 | While | function-body | d1 单层 | while-cond-ternary | While | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-WHILE-015 | While | class-body | d1 单层 | while-cond-ternary | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-016 | While | if-arm | d1 单层 | while-cond-ternary | While | `test_repros/round1/r1_10_while_mixed.pyc` | uncovered |
| JS-WHILE-017 | While | function-body | d1 单层 | while-cond-boolop | While | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-WHILE-018 | While | if-arm | d2 双层 | while-cond-boolop | While | `test_repros/round4/r4_or4_and2.pyc` | covered |
| JS-WHILE-019 | While | if-arm | d3plus 三层及以上 | while-cond-boolop | While | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WHILE-020 | While | loop-body | d3plus 三层及以上 | while-cond-boolop | While | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WHILE-021 | While | else-arm | d3plus 三层及以上 | while-cond-boolop | While | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WHILE-022 | While | function-body | d1 单层 | while-cond-compare-chain | While | `test_repros/round8/r8v8rev3_b104_exprtail_battery.pyc` | covered |
| JS-WHILE-023 | While | loop-body | d3plus 三层及以上 | while-cond-compare-chain | While | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WHILE-024 | While | module-level | d1 单层 | while-at-module | While | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-WHILE-025 | While | loop-body | d3plus 三层及以上 | while-at-module | While | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-WHILE-026 | While | function-body | d1 单层 | while-in-func | While | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-WHILE-027 | While | function-body | d2 双层 | while-in-func | While | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-WHILE-028 | While | if-arm | d2 双层 | while-in-func | While | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WHILE-029 | While | if-arm | d3plus 三层及以上 | while-in-func | While | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WHILE-030 | While | loop-body | d2 双层 | while-in-func | While | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WHILE-031 | While | loop-body | d3plus 三层及以上 | while-in-func | While | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-WHILE-032 | While | try-body | d2 双层 | while-in-func | While | `test_repros/round2/x01_if_deep_hosts.pyc` | covered |
| JS-WHILE-033 | While | try-body | d3plus 三层及以上 | while-in-func | While | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WHILE-034 | While | with-body | d3plus 三层及以上 | while-in-func | While | `test_repros/round5/rec1_synth_b70a_wt_with_bc.pyc` | covered |
| JS-WHILE-035 | While | match-case-body | d3plus 三层及以上 | while-in-func | While | `test_repros/round5/rec1_synth_g2b_with_match_cross.pyc` | covered |
| JS-WHILE-036 | While | else-arm | d2 双层 | while-in-func | While | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-WHILE-037 | While | else-arm | d3plus 三层及以上 | while-in-func | While | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WHILE-038 | While | try-body | d2 双层 | while-in-try | While | `test_repros/round2/x01_if_deep_hosts.pyc` | covered |
| JS-WHILE-039 | While | try-body | d3plus 三层及以上 | while-in-try | While | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-WHILE-040 | While | if-arm | d3plus 三层及以上 | while-with-break | While | `test_repros/round2/c13_class_misc.pyc` | covered |
| JS-WHILE-041 | While | module-level | d1 单层 | while-body-nested-loop | While | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-WHILE-042 | While | function-body | d1 单层 | while-body-nested-loop | While | `test_repros/round5/rec1_synth_g4b_b70_whiletrue_with.pyc` | covered |
| JS-WHILE-043 | While | function-body | d2 双层 | while-body-nested-loop | While | `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | covered |
| JS-WHILE-044 | While | loop-body | d3plus 三层及以上 | while-body-nested-loop | While | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-WHILE-045 | While | else-arm | d3plus 三层及以上 | while-body-nested-loop | While | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-DELETE-001 | Delete | function-body | d1 单层 | del-name | Delete | `test_repros/round8/r8_04_delete_forms.pyc` | covered |
| JS-DELETE-002 | Delete | module-level | d1 单层 | del-name | Delete | `test_repros/round2/m01_docstring_order.pyc` | covered |
| JS-DELETE-003 | Delete | if-arm | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-004 | Delete | else-arm | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-005 | Delete | loop-body | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-006 | Delete | try-body | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-007 | Delete | except-handler | d2 双层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-008 | Delete | finally-body | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-009 | Delete | with-body | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-010 | Delete | match-case-body | d1 单层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-011 | Delete | nested-func-body | d2 双层 | del-name | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-012 | Delete | function-body | d1 单层 | del-subscript | Delete | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-DELETE-013 | Delete | module-level | d1 单层 | del-subscript | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-014 | Delete | if-arm | d3plus 三层及以上 | del-subscript | Delete | `test_repros/round5/rec1_synth_b61c_fusion2.pyc` | covered |
| JS-DELETE-015 | Delete | else-arm | d1 单层 | del-subscript | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-016 | Delete | loop-body | d1 单层 | del-subscript | Delete | `test_repros/round8/r8v8fb_b108_del_probe.pyc` | uncovered |
| JS-DELETE-017 | Delete | try-body | d3plus 三层及以上 | del-subscript | Delete | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-DELETE-018 | Delete | function-body | d1 单层 | del-slice | Delete | `test_repros/round8/r8_04_delete_forms.pyc` | covered |
| JS-DELETE-019 | Delete | function-body | d1 单层 | del-attribute | Delete | `test_repros/round8/r8_04_delete_forms.pyc` | covered |
| JS-DELETE-020 | Delete | if-arm | d3plus 三层及以上 | del-in-loop | Delete | `test_repros/round5/rec1_synth_g3a_b61_deephost.pyc` | covered |
| JS-DELETE-021 | Delete | try-body | d3plus 三层及以上 | del-in-loop | Delete | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-DELETE-022 | Delete | try-body | d3plus 三层及以上 | del-in-try | Delete | `test_repros/round2/x08_stmt_leaves.pyc` | covered |
| JS-DELETE-023 | Delete | if-arm | d3plus 三层及以上 | del-in-with | Delete | `test_repros/round5/rec1_synth_g3b_b61_deephost.pyc` | covered |
| JS-DELETE-024 | Delete | function-body | d1 单层 | del-ternary-target | Delete | `test_repros/round8/r8_10_expr_cross_stmt.pyc` | covered |
| JS-AUGASSIGN-001 | AugAssign | function-body | d1 单层 | aug-op-add | AugAssign | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b76_face.pyc` | covered |
| JS-AUGASSIGN-002 | AugAssign | module-level | d1 单层 | aug-op-add | AugAssign | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-AUGASSIGN-003 | AugAssign | if-arm | d2 双层 | aug-op-add | AugAssign | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-AUGASSIGN-004 | AugAssign | if-arm | d3plus 三层及以上 | aug-op-add | AugAssign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGASSIGN-005 | AugAssign | else-arm | d3plus 三层及以上 | aug-op-add | AugAssign | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-AUGASSIGN-006 | AugAssign | loop-body | d1 单层 | aug-op-add | AugAssign | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-AUGASSIGN-007 | AugAssign | loop-body | d2 双层 | aug-op-add | AugAssign | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-AUGASSIGN-008 | AugAssign | loop-body | d3plus 三层及以上 | aug-op-add | AugAssign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGASSIGN-009 | AugAssign | try-body | d3plus 三层及以上 | aug-op-add | AugAssign | `test_repros/round10/r10_21_fin_loopctrl.pyc` | covered |
| JS-AUGASSIGN-010 | AugAssign | except-handler | d3plus 三层及以上 | aug-op-add | AugAssign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGASSIGN-011 | AugAssign | finally-body | d3plus 三层及以上 | aug-op-add | AugAssign | `test_repros/round10/r10_21_fin_loopctrl.pyc` | covered |
| JS-AUGASSIGN-012 | AugAssign | with-body | d1 单层 | aug-op-add | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-013 | AugAssign | match-case-body | d2 双层 | aug-op-add | AugAssign | `test_repros/round5/rec1_synth_b74e_guard_battery2.pyc` | covered |
| JS-AUGASSIGN-014 | AugAssign | class-body | d1 单层 | aug-op-add | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-015 | AugAssign | nested-func-body | d2 双层 | aug-op-add | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-016 | AugAssign | function-body | d1 单层 | aug-op-sub | AugAssign | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b76_face.pyc` | covered |
| JS-AUGASSIGN-017 | AugAssign | module-level | d1 单层 | aug-op-sub | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-018 | AugAssign | if-arm | d2 双层 | aug-op-sub | AugAssign | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-AUGASSIGN-019 | AugAssign | if-arm | d3plus 三层及以上 | aug-op-sub | AugAssign | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-AUGASSIGN-020 | AugAssign | else-arm | d3plus 三层及以上 | aug-op-sub | AugAssign | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-AUGASSIGN-021 | AugAssign | loop-body | d2 双层 | aug-op-sub | AugAssign | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-AUGASSIGN-022 | AugAssign | loop-body | d3plus 三层及以上 | aug-op-sub | AugAssign | `test_repros/round2/m01_docstring_order.pyc` | covered |
| JS-AUGASSIGN-023 | AugAssign | try-body | d3plus 三层及以上 | aug-op-sub | AugAssign | `test_repros/round2/c02_class_if.pyc` | covered |
| JS-AUGASSIGN-024 | AugAssign | except-handler | d3plus 三层及以上 | aug-op-sub | AugAssign | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-AUGASSIGN-025 | AugAssign | finally-body | d3plus 三层及以上 | aug-op-sub | AugAssign | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-AUGASSIGN-026 | AugAssign | with-body | d1 单层 | aug-op-sub | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-027 | AugAssign | match-case-body | d1 单层 | aug-op-sub | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-028 | AugAssign | class-body | d1 单层 | aug-op-sub | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-029 | AugAssign | nested-func-body | d2 双层 | aug-op-sub | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-030 | AugAssign | function-body | d1 单层 | aug-op-mul | AugAssign | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b76_face.pyc` | covered |
| JS-AUGASSIGN-031 | AugAssign | module-level | d1 单层 | aug-op-mul | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-032 | AugAssign | if-arm | d1 单层 | aug-op-mul | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-033 | AugAssign | else-arm | d1 单层 | aug-op-mul | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-034 | AugAssign | loop-body | d1 单层 | aug-op-mul | AugAssign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGASSIGN-035 | AugAssign | function-body | d1 单层 | aug-op-floordiv | AugAssign | `test_repros/round10/rv10_32_augassign_variant.pyc` | covered |
| JS-AUGASSIGN-036 | AugAssign | function-body | d1 单层 | aug-op-mod | AugAssign | `test_repros/round10/rv10_32_augassign_variant.pyc` | covered |
| JS-AUGASSIGN-037 | AugAssign | function-body | d1 单层 | aug-op-pow | AugAssign | `test_repros/round8/r8_06_augassign_ops.pyc` | covered |
| JS-AUGASSIGN-038 | AugAssign | function-body | d1 单层 | aug-op-lshift | AugAssign | `test_repros/round8/r8_06_augassign_ops.pyc` | covered |
| JS-AUGASSIGN-039 | AugAssign | function-body | d1 单层 | aug-op-rshift | AugAssign | `test_repros/round10/rv10_32_augassign_variant.pyc` | covered |
| JS-AUGASSIGN-040 | AugAssign | function-body | d1 单层 | aug-op-bitor | AugAssign | `test_repros/round8/r8_06_augassign_ops.pyc` | covered |
| JS-AUGASSIGN-041 | AugAssign | function-body | d1 单层 | aug-op-bitxor | AugAssign | `test_repros/round8/r8_06_augassign_ops.pyc` | covered |
| JS-AUGASSIGN-042 | AugAssign | function-body | d1 单层 | aug-op-bitand | AugAssign | `test_repros/round8/r8_06_augassign_ops.pyc` | covered |
| JS-AUGASSIGN-043 | AugAssign | function-body | d1 单层 | aug-op-truediv | AugAssign | `test_repros/round8/r8_06_augassign_ops.pyc` | covered |
| JS-AUGASSIGN-044 | AugAssign | function-body | d1 单层 | aug-op-matmul | AugAssign | `test_repros/round8/r8_06_augassign_ops.pyc` | covered |
| JS-AUGASSIGN-045 | AugAssign | function-body | d1 单层 | aug-target-name | AugAssign | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b76_face.pyc` | covered |
| JS-AUGASSIGN-046 | AugAssign | module-level | d1 单层 | aug-target-name | AugAssign | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-AUGASSIGN-047 | AugAssign | if-arm | d2 双层 | aug-target-name | AugAssign | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-AUGASSIGN-048 | AugAssign | if-arm | d3plus 三层及以上 | aug-target-name | AugAssign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGASSIGN-049 | AugAssign | else-arm | d3plus 三层及以上 | aug-target-name | AugAssign | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-AUGASSIGN-050 | AugAssign | loop-body | d1 单层 | aug-target-name | AugAssign | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-AUGASSIGN-051 | AugAssign | loop-body | d2 双层 | aug-target-name | AugAssign | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-AUGASSIGN-052 | AugAssign | loop-body | d3plus 三层及以上 | aug-target-name | AugAssign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGASSIGN-053 | AugAssign | try-body | d3plus 三层及以上 | aug-target-name | AugAssign | `test_repros/round10/r10_21_fin_loopctrl.pyc` | covered |
| JS-AUGASSIGN-054 | AugAssign | except-handler | d3plus 三层及以上 | aug-target-name | AugAssign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGASSIGN-055 | AugAssign | finally-body | d3plus 三层及以上 | aug-target-name | AugAssign | `test_repros/round10/r10_21_fin_loopctrl.pyc` | covered |
| JS-AUGASSIGN-056 | AugAssign | match-case-body | d2 双层 | aug-target-name | AugAssign | `test_repros/round5/rec1_synth_b74e_guard_battery2.pyc` | covered |
| JS-AUGASSIGN-057 | AugAssign | function-body | d1 单层 | aug-target-attr | AugAssign | `test_repros/round10/rv10_32_augassign_variant.pyc` | covered |
| JS-AUGASSIGN-058 | AugAssign | function-body | d1 单层 | aug-target-subscript | AugAssign | `test_repros/round10/rv10_32_augassign_variant.pyc` | covered |
| JS-AUGASSIGN-059 | AugAssign | function-body | d1 单层 | aug-rhs-call | AugAssign | `test_repros/round8/r8_06_augassign_ops.pyc` | covered |
| JS-AUGASSIGN-060 | AugAssign | function-body | d1 单层 | aug-rhs-ternary | AugAssign | `test_repros/round10/rv10_32_augassign_variant.pyc` | covered |
| JS-AUGASSIGN-061 | AugAssign | loop-body | d2 双层 | aug-rhs-ternary | AugAssign | `test_repros/round7/r7_08_ternary_deep_host.pyc` | covered |
| JS-AUGASSIGN-062 | AugAssign | function-body | d1 单层 | aug-rhs-attr | AugAssign | `test_repros/round8/r8_06_augassign_ops.pyc` | covered |
| JS-AUGASSIGN-063 | AugAssign | function-body | d1 单层 | aug-rhs-subscript | AugAssign | `test_repros/round8/r8_06_augassign_ops.pyc` | covered |
| JS-RETURN-001 | Return | function-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-002 | Return | nested-func-body | d2 双层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-003 | Return | module-level | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-004 | Return | if-arm | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-005 | Return | else-arm | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-006 | Return | loop-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-007 | Return | try-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-008 | Return | except-handler | d2 双层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-009 | Return | finally-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-010 | Return | with-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-011 | Return | match-case-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-012 | Return | class-body | d1 单层 | return-bare | Return | `test_repros/round5/r5_13_comp_return.pyc` | uncovered |
| JS-RETURN-013 | Return | function-body | d1 单层 | return-value | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-RETURN-014 | Return | function-body | d2 双层 | return-value | Return | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_arg.pyc` | covered |
| JS-RETURN-015 | Return | function-body | d3plus 三层及以上 | return-value | Return | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-RETURN-016 | Return | if-arm | d2 双层 | return-value | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-RETURN-017 | Return | if-arm | d3plus 三层及以上 | return-value | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-RETURN-018 | Return | else-arm | d2 双层 | return-value | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b75_face.pyc` | covered |
| JS-RETURN-019 | Return | else-arm | d3plus 三层及以上 | return-value | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-RETURN-020 | Return | loop-body | d2 双层 | return-value | Return | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-RETURN-021 | Return | try-body | d2 双层 | return-value | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-RETURN-022 | Return | try-body | d3plus 三层及以上 | return-value | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-023 | Return | except-handler | d2 双层 | return-value | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-RETURN-024 | Return | except-handler | d3plus 三层及以上 | return-value | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-025 | Return | with-body | d2 双层 | return-value | Return | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-RETURN-026 | Return | with-body | d3plus 三层及以上 | return-value | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-027 | Return | match-case-body | d2 双层 | return-value | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-RETURN-028 | Return | match-case-body | d3plus 三层及以上 | return-value | Return | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-RETURN-029 | Return | generator-func-body | d1 单层 | return-value | Return | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_ret.pyc` | covered |
| JS-RETURN-030 | Return | function-body | d1 单层 | return-ternary | Return | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-RETURN-031 | Return | function-body | d2 双层 | return-ternary | Return | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-RETURN-032 | Return | if-arm | d3plus 三层及以上 | return-ternary | Return | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-RETURN-033 | Return | except-handler | d3plus 三层及以上 | return-ternary | Return | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-RETURN-034 | Return | match-case-body | d2 双层 | return-ternary | Return | `test_repros/round7/r7_08_ternary_deep_host.pyc` | covered |
| JS-RETURN-035 | Return | function-body | d1 单层 | return-tuple | Return | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-RETURN-036 | Return | function-body | d2 双层 | return-tuple | Return | `test_repros/round2/c04_class_try.pyc` | covered |
| JS-RETURN-037 | Return | if-arm | d2 双层 | return-tuple | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-038 | Return | if-arm | d3plus 三层及以上 | return-tuple | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-039 | Return | else-arm | d2 双层 | return-tuple | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-040 | Return | else-arm | d3plus 三层及以上 | return-tuple | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-041 | Return | try-body | d3plus 三层及以上 | return-tuple | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-042 | Return | except-handler | d2 双层 | return-tuple | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-043 | Return | except-handler | d3plus 三层及以上 | return-tuple | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-044 | Return | with-body | d2 双层 | return-tuple | Return | `test_repros/round5/rec1_synth_g2b_with_match_cross.pyc` | covered |
| JS-RETURN-045 | Return | with-body | d3plus 三层及以上 | return-tuple | Return | `test_repros/round5/rec1_synth_g2a_with_match_cross.pyc` | covered |
| JS-RETURN-046 | Return | match-case-body | d2 双层 | return-tuple | Return | `test_repros/round5/rec1_synth_b61c_fusion2.pyc` | covered |
| JS-RETURN-047 | Return | match-case-body | d3plus 三层及以上 | return-tuple | Return | `test_repros/round5/rec1_synth_g2b_with_match_cross.pyc` | covered |
| JS-RETURN-048 | Return | function-body | d1 单层 | return-boolop | Return | `test_repros/round3/_scratch_b98/resid.pyc` | covered |
| JS-RETURN-049 | Return | function-body | d3plus 三层及以上 | return-boolop | Return | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-RETURN-050 | Return | if-arm | d2 双层 | return-boolop | Return | `test_repros/round7/r7_14_boolop_deep_host.pyc` | covered |
| JS-RETURN-051 | Return | if-arm | d3plus 三层及以上 | return-boolop | Return | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-RETURN-052 | Return | else-arm | d2 双层 | return-boolop | Return | `test_repros/round7/r7_12_boolop_nest.pyc` | covered |
| JS-RETURN-053 | Return | else-arm | d3plus 三层及以上 | return-boolop | Return | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-RETURN-054 | Return | except-handler | d3plus 三层及以上 | return-boolop | Return | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-RETURN-055 | Return | match-case-body | d3plus 三层及以上 | return-boolop | Return | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-RETURN-056 | Return | if-arm | d3plus 三层及以上 | return-await | Return | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-RETURN-057 | Return | with-body | d3plus 三层及以上 | return-await | Return | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-RETURN-058 | Return | if-arm | d3plus 三层及以上 | return-yield | Return | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_ret.pyc` | covered |
| JS-RETURN-059 | Return | try-body | d2 双层 | return-in-try-body | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-RETURN-060 | Return | try-body | d3plus 三层及以上 | return-in-try-body | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-061 | Return | if-arm | d3plus 三层及以上 | return-in-handler | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-RETURN-062 | Return | else-arm | d3plus 三层及以上 | return-in-handler | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-RETURN-063 | Return | try-body | d3plus 三层及以上 | return-in-handler | Return | `test_repros/round8/r8_08_raise_forms.pyc` | covered |
| JS-RETURN-064 | Return | except-handler | d2 双层 | return-in-handler | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc` | covered |
| JS-RETURN-065 | Return | except-handler | d3plus 三层及以上 | return-in-handler | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-066 | Return | if-arm | d3plus 三层及以上 | return-in-loop | Return | `.trae/specs/attain-true-completeness/test_repros/round1/rec1_yf9_ret.pyc` | covered |
| JS-RETURN-067 | Return | else-arm | d3plus 三层及以上 | return-in-loop | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-068 | Return | loop-body | d2 双层 | return-in-loop | Return | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-RETURN-069 | Return | except-handler | d3plus 三层及以上 | return-in-loop | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-070 | Return | match-case-body | d3plus 三层及以上 | return-in-loop | Return | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-RETURN-071 | Return | if-arm | d3plus 三层及以上 | return-in-with | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-072 | Return | except-handler | d3plus 三层及以上 | return-in-with | Return | `test_repros/round9/n9v9_stmt_sweep.pyc` | covered |
| JS-RETURN-073 | Return | with-body | d2 双层 | return-in-with | Return | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-RETURN-074 | Return | with-body | d3plus 三层及以上 | return-in-with | Return | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-RETURN-075 | Return | match-case-body | d3plus 三层及以上 | return-in-with | Return | `test_repros/round5/rec1_synth_g2a_with_match_cross.pyc` | covered |
| JS-RETURN-076 | Return | if-arm | d3plus 三层及以上 | return-in-match-case | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-RETURN-077 | Return | else-arm | d3plus 三层及以上 | return-in-match-case | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-RETURN-078 | Return | with-body | d3plus 三层及以上 | return-in-match-case | Return | `test_repros/round5/rec1_synth_b93d_with_ret_case.pyc` | covered |
| JS-RETURN-079 | Return | match-case-body | d2 双层 | return-in-match-case | Return | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc` | covered |
| JS-RETURN-080 | Return | match-case-body | d3plus 三层及以上 | return-in-match-case | Return | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-SLICE-001 | Slice | subscript-index | d1 单层 | slice-plain | Slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICE-002 | Slice | subscript-index | d2 双层 | slice-plain | Slice | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-SLICE-003 | Slice | subscript-index | d3plus 三层及以上 | slice-plain | Slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICE-004 | Slice | slice-bounds | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-005 | Slice | function-body | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-006 | Slice | module-level | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-007 | Slice | assign-rhs | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-008 | Slice | if-arm | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-009 | Slice | loop-body | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-010 | Slice | try-body | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-011 | Slice | call-arg | d1 单层 | slice-plain | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-012 | Slice | subscript-index | d3plus 三层及以上 | slice-with-step | Slice | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-SLICE-013 | Slice | slice-bounds | d1 单层 | slice-with-step | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-014 | Slice | function-body | d1 单层 | slice-with-step | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-015 | Slice | module-level | d1 单层 | slice-with-step | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-016 | Slice | assign-rhs | d1 单层 | slice-with-step | Slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICE-017 | Slice | subscript-index | d1 单层 | slice-neg-bound | Slice | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-SLICE-018 | Slice | subscript-index | d3plus 三层及以上 | slice-neg-bound | Slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICE-019 | Slice | subscript-index | d3plus 三层及以上 | slice-expr-bound | Slice | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-SLICE-020 | Slice | subscript-index | d1 单层 | slice-ternary-bound | Slice | `test_repros/round7/r7_01_ternary_args_index.pyc` | covered |
| JS-SLICE-021 | Slice | subscript-index | d3plus 三层及以上 | slice-ternary-bound | Slice | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-SLICE-022 | Slice | subscript-index | d1 单层 | slice-in-del-target | Slice | `test_repros/round8/r8_04_delete_forms.pyc` | covered |
| JS-SLICE-023 | Slice | subscript-index | d1 单层 | slice-in-assign-target | Slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICE-024 | Slice | subscript-index | d2 双层 | slice-in-assign-target | Slice | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-SLICE-025 | Slice | subscript-index | d3plus 三层及以上 | slice-in-assign-target | Slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-001 | augmented_assign | function-body | d1 单层 | augform-target-name | augmented_assign | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b76_face.pyc` | covered |
| JS-AUGFORM-002 | augmented_assign | module-level | d1 单层 | augform-target-name | augmented_assign | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-AUGFORM-003 | augmented_assign | if-arm | d2 双层 | augform-target-name | augmented_assign | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-AUGFORM-004 | augmented_assign | if-arm | d3plus 三层及以上 | augform-target-name | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-005 | augmented_assign | else-arm | d3plus 三层及以上 | augform-target-name | augmented_assign | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-AUGFORM-006 | augmented_assign | loop-body | d1 单层 | augform-target-name | augmented_assign | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-AUGFORM-007 | augmented_assign | loop-body | d2 双层 | augform-target-name | augmented_assign | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-AUGFORM-008 | augmented_assign | loop-body | d3plus 三层及以上 | augform-target-name | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-009 | augmented_assign | try-body | d3plus 三层及以上 | augform-target-name | augmented_assign | `test_repros/round10/r10_21_fin_loopctrl.pyc` | covered |
| JS-AUGFORM-010 | augmented_assign | except-handler | d3plus 三层及以上 | augform-target-name | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-011 | augmented_assign | finally-body | d3plus 三层及以上 | augform-target-name | augmented_assign | `test_repros/round10/r10_21_fin_loopctrl.pyc` | covered |
| JS-AUGFORM-012 | augmented_assign | with-body | d1 单层 | augform-target-name | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-013 | augmented_assign | match-case-body | d2 双层 | augform-target-name | augmented_assign | `test_repros/round5/rec1_synth_b74e_guard_battery2.pyc` | covered |
| JS-AUGFORM-014 | augmented_assign | comprehension-scope | d1 单层 | augform-target-name | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-015 | augmented_assign | class-body | d1 单层 | augform-target-name | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-016 | augmented_assign | function-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round10/rv10_32_augassign_variant.pyc` | covered |
| JS-AUGFORM-017 | augmented_assign | module-level | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-018 | augmented_assign | if-arm | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-019 | augmented_assign | else-arm | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-020 | augmented_assign | loop-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-021 | augmented_assign | try-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-022 | augmented_assign | except-handler | d2 双层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-023 | augmented_assign | finally-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-024 | augmented_assign | with-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-025 | augmented_assign | match-case-body | d1 单层 | augform-target-attr | augmented_assign | `test_repros/round4/c4_08_augassign.pyc` | uncovered |
| JS-AUGFORM-026 | augmented_assign | function-body | d1 单层 | augform-target-subscript | augmented_assign | `test_repros/round10/rv10_32_augassign_variant.pyc` | covered |
| JS-AUGFORM-027 | augmented_assign | if-arm | d2 双层 | augform-in-if-arm | augmented_assign | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-AUGFORM-028 | augmented_assign | if-arm | d3plus 三层及以上 | augform-in-if-arm | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-029 | augmented_assign | else-arm | d3plus 三层及以上 | augform-in-if-arm | augmented_assign | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-AUGFORM-030 | augmented_assign | loop-body | d3plus 三层及以上 | augform-in-if-arm | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-031 | augmented_assign | try-body | d3plus 三层及以上 | augform-in-if-arm | augmented_assign | `test_repros/round2/c02_class_if.pyc` | covered |
| JS-AUGFORM-032 | augmented_assign | except-handler | d3plus 三层及以上 | augform-in-if-arm | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-033 | augmented_assign | finally-body | d3plus 三层及以上 | augform-in-if-arm | augmented_assign | `test_repros/round2/m02_top_ifmain.pyc` | covered |
| JS-AUGFORM-034 | augmented_assign | if-arm | d3plus 三层及以上 | augform-in-loop-body | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-035 | augmented_assign | else-arm | d3plus 三层及以上 | augform-in-loop-body | augmented_assign | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-AUGFORM-036 | augmented_assign | loop-body | d1 单层 | augform-in-loop-body | augmented_assign | `test_repros/round2/m06_module_loops.pyc` | covered |
| JS-AUGFORM-037 | augmented_assign | loop-body | d2 双层 | augform-in-loop-body | augmented_assign | `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc` | covered |
| JS-AUGFORM-038 | augmented_assign | loop-body | d3plus 三层及以上 | augform-in-loop-body | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-039 | augmented_assign | try-body | d3plus 三层及以上 | augform-in-loop-body | augmented_assign | `test_repros/round10/r10_21_fin_loopctrl.pyc` | covered |
| JS-AUGFORM-040 | augmented_assign | except-handler | d3plus 三层及以上 | augform-in-loop-body | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-041 | augmented_assign | finally-body | d3plus 三层及以上 | augform-in-loop-body | augmented_assign | `test_repros/round10/r10_21_fin_loopctrl.pyc` | covered |
| JS-AUGFORM-042 | augmented_assign | try-body | d3plus 三层及以上 | augform-in-try-body | augmented_assign | `test_repros/round10/r10_21_fin_loopctrl.pyc` | covered |
| JS-AUGFORM-043 | augmented_assign | loop-body | d3plus 三层及以上 | augform-in-handler | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-044 | augmented_assign | try-body | d3plus 三层及以上 | augform-in-handler | augmented_assign | `test_repros/round2/x10_handler_hosts.pyc` | covered |
| JS-AUGFORM-045 | augmented_assign | except-handler | d3plus 三层及以上 | augform-in-handler | augmented_assign | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-AUGFORM-046 | augmented_assign | match-case-body | d2 双层 | augform-in-match-case | augmented_assign | `test_repros/round5/rec1_synth_b74e_guard_battery2.pyc` | covered |
| JS-AUGFORM-047 | augmented_assign | if-arm | d3plus 三层及以上 | augform-in-class-body | augmented_assign | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-AUGFORM-048 | augmented_assign | loop-body | d3plus 三层及以上 | augform-in-class-body | augmented_assign | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-AUGFORM-049 | augmented_assign | try-body | d3plus 三层及以上 | augform-in-class-body | augmented_assign | `test_repros/round2/c02_class_if.pyc` | covered |
| JS-SLICEFORM-001 | slice | subscript-index | d1 单层 | sliceform-in-subscript | slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICEFORM-002 | slice | subscript-index | d2 双层 | sliceform-in-subscript | slice | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-SLICEFORM-003 | slice | subscript-index | d3plus 三层及以上 | sliceform-in-subscript | slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICEFORM-004 | slice | slice-bounds | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-005 | slice | function-body | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-006 | slice | module-level | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-007 | slice | assign-rhs | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-008 | slice | if-arm | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-009 | slice | loop-body | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-010 | slice | try-body | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-011 | slice | call-arg | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-012 | slice | return-value-expr | d1 单层 | sliceform-in-subscript | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-013 | slice | subscript-index | d1 单层 | sliceform-in-del-target | slice | `test_repros/round8/r8_04_delete_forms.pyc` | covered |
| JS-SLICEFORM-014 | slice | slice-bounds | d1 单层 | sliceform-in-del-target | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-015 | slice | function-body | d1 单层 | sliceform-in-del-target | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-016 | slice | module-level | d1 单层 | sliceform-in-del-target | slice | `test_repros/round4/c4_13_slice.pyc` | uncovered |
| JS-SLICEFORM-017 | slice | subscript-index | d1 单层 | sliceform-in-assign-target | slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICEFORM-018 | slice | subscript-index | d2 双层 | sliceform-in-assign-target | slice | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-SLICEFORM-019 | slice | subscript-index | d3plus 三层及以上 | sliceform-in-assign-target | slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICEFORM-020 | slice | subscript-index | d1 单层 | sliceform-nested-subscript | slice | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-SLICEFORM-021 | slice | subscript-index | d2 双层 | sliceform-nested-subscript | slice | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-SLICEFORM-022 | slice | subscript-index | d3plus 三层及以上 | sliceform-nested-subscript | slice | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-SLICEFORM-023 | slice | subscript-index | d3plus 三层及以上 | sliceform-step-only | slice | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-SLICEFORM-024 | slice | subscript-index | d3plus 三层及以上 | sliceform-full | slice | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-SLICEFORM-025 | slice | subscript-index | d1 单层 | sliceform-single-bound | slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICEFORM-026 | slice | subscript-index | d2 双层 | sliceform-single-bound | slice | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-SLICEFORM-027 | slice | subscript-index | d3plus 三层及以上 | sliceform-single-bound | slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICEFORM-028 | slice | subscript-index | d1 单层 | sliceform-in-call-arg | slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICEFORM-029 | slice | subscript-index | d3plus 三层及以上 | sliceform-in-call-arg | slice | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-SLICEFORM-030 | slice | subscript-index | d1 单层 | sliceform-in-return | slice | `test_repros/round7/r7_01_ternary_args_index.pyc` | covered |
| JS-SLICEFORM-031 | slice | subscript-index | d2 双层 | sliceform-in-return | slice | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-SLICEFORM-032 | slice | subscript-index | d3plus 三层及以上 | sliceform-in-return | slice | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-LAMBDA-001 | Lambda | function-body | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-002 | Lambda | module-level | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-003 | Lambda | assign-rhs | d1 单层 | lambda-in-assign | NEW | `test_repros/round7/r7_06_ternary_lambda_await.pyc` | covered |
| JS-LAMBDA-004 | Lambda | call-arg | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-005 | Lambda | return-value-expr | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-006 | Lambda | class-body | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-007 | Lambda | if-arm | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-008 | Lambda | loop-body | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-009 | Lambda | comprehension-scope | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-010 | Lambda | condition-expr | d1 单层 | lambda-in-assign | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-011 | Lambda | function-body | d1 单层 | lambda-as-call-arg | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-012 | Lambda | module-level | d1 单层 | lambda-as-call-arg | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-013 | Lambda | assign-rhs | d1 单层 | lambda-as-call-arg | NEW | `test_repros/round5/r5_11_comp_lambda.pyc` | uncovered |
| JS-LAMBDA-014 | Lambda | call-arg | d1 单层 | lambda-as-call-arg | NEW | `test_repros/round7/r7_06_ternary_lambda_await.pyc` | covered |
| JS-LAMBDA-015 | Lambda | call-arg | d3plus 三层及以上 | lambda-as-call-arg | NEW | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-LAMBDA-016 | Lambda | return-value-expr | d2 双层 | lambda-in-return | NEW | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-LAMBDA-017 | Lambda | assign-rhs | d1 单层 | lambda-body-ternary | NEW | `test_repros/round7/r7_06_ternary_lambda_await.pyc` | covered |
| JS-LAMBDA-018 | Lambda | call-arg | d1 单层 | lambda-body-ternary | NEW | `test_repros/round7/r7_06_ternary_lambda_await.pyc` | covered |
| JS-DECORATOR-001 | Decorator | decorator-expr | d1 单层 | deco-on-function | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-002 | Decorator | function-body | d1 单层 | deco-on-function | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-003 | Decorator | class-body | d1 单层 | deco-on-function | NEW | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-DECORATOR-004 | Decorator | module-level | d1 单层 | deco-on-function | NEW | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-DECORATOR-005 | Decorator | call-arg | d1 单层 | deco-on-function | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-006 | Decorator | decorator-expr | d1 单层 | deco-on-class | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-007 | Decorator | function-body | d1 单层 | deco-on-class | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-008 | Decorator | class-body | d1 单层 | deco-on-class | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-009 | Decorator | module-level | d1 单层 | deco-on-class | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-010 | Decorator | call-arg | d1 单层 | deco-on-class | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-011 | Decorator | decorator-expr | d1 单层 | deco-single | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-012 | Decorator | function-body | d1 单层 | deco-single | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-013 | Decorator | class-body | d1 单层 | deco-single | NEW | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-DECORATOR-014 | Decorator | module-level | d1 单层 | deco-single | NEW | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-DECORATOR-015 | Decorator | call-arg | d1 单层 | deco-single | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-016 | Decorator | decorator-expr | d1 单层 | deco-stack | NEW | `site-packages/fly/common/aes_encrypt.pyc` | uncovered |
| JS-DECORATOR-017 | Decorator | class-body | d1 单层 | deco-stack | NEW | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-DECORATOR-018 | Decorator | class-body | d1 单层 | deco-with-args | NEW | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-DECORATOR-019 | Decorator | module-level | d1 单层 | deco-with-args | NEW | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-DECORATOR-020 | Decorator | class-body | d1 单层 | deco-name-form | NEW | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-SETCOMP-001 | SetComp | function-body | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-002 | SetComp | module-level | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-003 | SetComp | assign-rhs | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-004 | SetComp | return-value-expr | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-SETCOMP-005 | SetComp | return-value-expr | d2 双层 | setcomp-single-for | NEW | `test_repros/round4/rec1_synth_b112b_closure.pyc` | covered |
| JS-SETCOMP-006 | SetComp | call-arg | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-007 | SetComp | comprehension-scope | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-008 | SetComp | comprehension-if | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-009 | SetComp | if-arm | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-010 | SetComp | loop-body | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-011 | SetComp | class-body | d1 单层 | setcomp-single-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-012 | SetComp | function-body | d1 单层 | setcomp-multi-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-013 | SetComp | module-level | d1 单层 | setcomp-multi-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-014 | SetComp | assign-rhs | d1 单层 | setcomp-multi-for | NEW | `test_repros/round5/r5_04_comp_cond.pyc` | uncovered |
| JS-SETCOMP-015 | SetComp | return-value-expr | d1 单层 | setcomp-async | NEW | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-SETCOMP-016 | SetComp | return-value-expr | d2 双层 | setcomp-async | NEW | `test_repros/round4/rec1_synth_b112b_closure.pyc` | covered |
| JS-SETCOMP-017 | SetComp | return-value-expr | d1 单层 | setcomp-elt-ternary | NEW | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-DICTCOMP-001 | DictComp | function-body | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-002 | DictComp | module-level | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-003 | DictComp | assign-rhs | d2 双层 | dictcomp-single-for | NEW | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-DICTCOMP-004 | DictComp | return-value-expr | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-DICTCOMP-005 | DictComp | return-value-expr | d3plus 三层及以上 | dictcomp-single-for | NEW | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-DICTCOMP-006 | DictComp | call-arg | d3plus 三层及以上 | dictcomp-single-for | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-DICTCOMP-007 | DictComp | comprehension-scope | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-008 | DictComp | comprehension-if | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-009 | DictComp | if-arm | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-010 | DictComp | loop-body | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-011 | DictComp | class-body | d1 单层 | dictcomp-single-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-012 | DictComp | function-body | d1 单层 | dictcomp-multi-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-013 | DictComp | module-level | d1 单层 | dictcomp-multi-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-014 | DictComp | assign-rhs | d1 单层 | dictcomp-multi-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-015 | DictComp | return-value-expr | d1 单层 | dictcomp-multi-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-016 | DictComp | call-arg | d1 单层 | dictcomp-multi-for | NEW | `test_repros/round5/r5_01_comp_basic.pyc` | uncovered |
| JS-DICTCOMP-017 | DictComp | return-value-expr | d1 单层 | dictcomp-async | NEW | `test_repros/round5/r5_10_comp_async.pyc` | covered |
| JS-DICTCOMP-018 | DictComp | assign-rhs | d2 双层 | dictcomp-value-ternary | NEW | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-DICTCOMP-019 | DictComp | return-value-expr | d1 单层 | dictcomp-value-ternary | NEW | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-DICTCOMP-020 | DictComp | return-value-expr | d1 单层 | dictcomp-key-ternary | NEW | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-DICTCOMP-021 | DictComp | return-value-expr | d3plus 三层及以上 | dictcomp-key-ternary | NEW | `test_repros/round3/e02_g1_b98_hosts.pyc` | covered |
| JS-DICTCOMP-022 | DictComp | call-arg | d3plus 三层及以上 | dictcomp-in-call-arg | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-DICTCOMP-023 | DictComp | assign-rhs | d2 双层 | dictcomp-in-assign | NEW | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-GENEXP-001 | GeneratorExp | function-body | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-002 | GeneratorExp | module-level | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-003 | GeneratorExp | assign-rhs | d1 单层 | genexp-single-for | NEW | `test_repros/round2/m08_module_stmts.pyc` | covered |
| JS-GENEXP-004 | GeneratorExp | return-value-expr | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-005 | GeneratorExp | call-arg | d1 单层 | genexp-single-for | NEW | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-GENEXP-006 | GeneratorExp | call-arg | d2 双层 | genexp-single-for | NEW | `test_repros/round2/c02_class_if.pyc` | covered |
| JS-GENEXP-007 | GeneratorExp | call-arg | d3plus 三层及以上 | genexp-single-for | NEW | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-GENEXP-008 | GeneratorExp | comprehension-scope | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-009 | GeneratorExp | comprehension-if | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-010 | GeneratorExp | if-arm | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-011 | GeneratorExp | loop-body | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-012 | GeneratorExp | class-body | d1 单层 | genexp-single-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-013 | GeneratorExp | function-body | d1 单层 | genexp-multi-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-014 | GeneratorExp | module-level | d1 单层 | genexp-multi-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-015 | GeneratorExp | assign-rhs | d1 单层 | genexp-multi-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-016 | GeneratorExp | return-value-expr | d1 单层 | genexp-multi-for | NEW | `test_repros/round5/r5_02_genexp.pyc` | uncovered |
| JS-GENEXP-017 | GeneratorExp | call-arg | d1 单层 | genexp-elt-ternary | NEW | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-GENEXP-018 | GeneratorExp | call-arg | d1 单层 | genexp-in-call-arg | NEW | `test_repros/round7/r7_05_ternary_comprehension.pyc` | covered |
| JS-GENEXP-019 | GeneratorExp | call-arg | d2 双层 | genexp-in-call-arg | NEW | `test_repros/round2/c02_class_if.pyc` | covered |
| JS-GENEXP-020 | GeneratorExp | call-arg | d3plus 三层及以上 | genexp-in-call-arg | NEW | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | covered |
| JS-GENEXP-021 | GeneratorExp | assign-rhs | d1 单层 | genexp-in-assign | NEW | `test_repros/round2/m08_module_stmts.pyc` | covered |
| JS-NAMEDEXPR-001 | NamedExpr | function-body | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-002 | NamedExpr | module-level | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-003 | NamedExpr | if-arm | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-004 | NamedExpr | else-arm | d3plus 三层及以上 | namedexpr-in-if-cond | NEW | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-NAMEDEXPR-005 | NamedExpr | loop-body | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-006 | NamedExpr | condition-expr | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-007 | NamedExpr | comprehension-if | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-008 | NamedExpr | comprehension-for | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-009 | NamedExpr | try-body | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-010 | NamedExpr | except-handler | d2 双层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-011 | NamedExpr | with-body | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-012 | NamedExpr | assign-rhs | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-013 | NamedExpr | call-arg | d1 单层 | namedexpr-in-if-cond | NEW | `test_repros/round4/c4_10_walrus.pyc` | uncovered |
| JS-NAMEDEXPR-014 | NamedExpr | else-arm | d3plus 三层及以上 | namedexpr-in-loop-body | NEW | `test_repros/round3/e01_g1_b98_matrix.pyc` | covered |
| JS-FSTRING-001 | JoinedStr | function-body | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-002 | JoinedStr | module-level | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-003 | JoinedStr | assign-rhs | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-004 | JoinedStr | return-value-expr | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-005 | JoinedStr | call-arg | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-006 | JoinedStr | f-string-format | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-007 | JoinedStr | if-arm | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-008 | JoinedStr | loop-body | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-009 | JoinedStr | try-body | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-010 | JoinedStr | class-body | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-011 | JoinedStr | dict-literal | d1 单层 | fstring-plain | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-012 | JoinedStr | function-body | d1 单层 | fstring-with-var | NEW | `test_repros/round3/e11_g8_fstrings.pyc` | uncovered |
| JS-FSTRING-013 | JoinedStr | assign-rhs | d1 单层 | fstring-with-var | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-014 | JoinedStr | assign-rhs | d2 双层 | fstring-with-var | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-015 | JoinedStr | assign-rhs | d3plus 三层及以上 | fstring-with-var | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-016 | JoinedStr | call-arg | d2 双层 | fstring-with-var | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-017 | JoinedStr | call-arg | d3plus 三层及以上 | fstring-with-var | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-018 | JoinedStr | assign-rhs | d1 单层 | fstring-with-conversion | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-019 | JoinedStr | assign-rhs | d2 双层 | fstring-with-conversion | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-020 | JoinedStr | assign-rhs | d3plus 三层及以上 | fstring-with-conversion | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-021 | JoinedStr | call-arg | d2 双层 | fstring-with-conversion | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-022 | JoinedStr | call-arg | d3plus 三层及以上 | fstring-with-conversion | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-023 | JoinedStr | assign-rhs | d1 单层 | fstring-embedded-expr | NEW | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-FSTRING-024 | JoinedStr | assign-rhs | d2 双层 | fstring-embedded-expr | NEW | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-FSTRING-025 | JoinedStr | assign-rhs | d3plus 三层及以上 | fstring-embedded-expr | NEW | `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | covered |
| JS-FSTRING-026 | JoinedStr | call-arg | d2 双层 | fstring-embedded-expr | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-027 | JoinedStr | call-arg | d3plus 三层及以上 | fstring-embedded-expr | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-028 | JoinedStr | call-arg | d2 双层 | fstring-in-call-arg | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-029 | JoinedStr | call-arg | d3plus 三层及以上 | fstring-in-call-arg | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-030 | JoinedStr | assign-rhs | d1 单层 | fstring-in-assign | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-031 | JoinedStr | assign-rhs | d2 双层 | fstring-in-assign | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-FSTRING-032 | JoinedStr | assign-rhs | d3plus 三层及以上 | fstring-in-assign | NEW | `site-packages/IQCommon/util/trade_info_utils.pyc` | covered |
| JS-STARRED-001 | Starred | function-body | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-002 | Starred | module-level | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-003 | Starred | call-arg | d2 双层 | starred-in-call | NEW | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-STARRED-004 | Starred | call-arg | d3plus 三层及以上 | starred-in-call | NEW | `site-packages/IQEngine/utils/scheduler.pyc` | covered |
| JS-STARRED-005 | Starred | assign-rhs | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-006 | Starred | starred-operand | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-007 | Starred | return-value-expr | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-008 | Starred | list-literal | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-009 | Starred | tuple-literal | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-010 | Starred | if-arm | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-011 | Starred | loop-body | d1 单层 | starred-in-call | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-012 | Starred | function-body | d1 单层 | starred-at-head | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-013 | Starred | module-level | d1 单层 | starred-at-head | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-014 | Starred | call-arg | d1 单层 | starred-at-head | NEW | `test_repros/round4/c4_12_star_args.pyc` | uncovered |
| JS-STARRED-015 | Starred | tuple-literal | d3plus 三层及以上 | starred-at-head | NEW | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-STARRED-016 | Starred | tuple-literal | d3plus 三层及以上 | starred-at-mid | NEW | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-STARRED-017 | Starred | tuple-literal | d3plus 三层及以上 | starred-at-tail | NEW | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-STARRED-018 | Starred | tuple-literal | d3plus 三层及以上 | starred-in-tuple-literal | NEW | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-STARRED-019 | Starred | call-arg | d2 双层 | starred-in-assign | NEW | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-STARRED-020 | Starred | call-arg | d3plus 三层及以上 | starred-in-assign | NEW | `site-packages/fly/data/quote_handler.pyc` | covered |
| JS-STARRED-021 | Starred | tuple-literal | d3plus 三层及以上 | starred-in-assign | NEW | `test_repros/round3/e07_g4_star_slice_containers.pyc` | covered |
| JS-EXCEPTSTAR-001 | ExceptStar | function-body | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-002 | ExceptStar | module-level | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-003 | ExceptStar | try-body | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-004 | ExceptStar | except-handler | d2 双层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-005 | ExceptStar | else-of-try | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-006 | ExceptStar | finally-body | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-007 | ExceptStar | if-arm | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-008 | ExceptStar | loop-body | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-009 | ExceptStar | with-body | d1 单层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-010 | ExceptStar | nested-func-body | d2 双层 | es-single-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-011 | ExceptStar | function-body | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-012 | ExceptStar | module-level | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-013 | ExceptStar | try-body | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-014 | ExceptStar | except-handler | d2 双层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-015 | ExceptStar | else-of-try | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-016 | ExceptStar | finally-body | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-017 | ExceptStar | if-arm | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-018 | ExceptStar | loop-body | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-019 | ExceptStar | with-body | d1 单层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-020 | ExceptStar | nested-func-body | d2 双层 | es-multi-handler | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-021 | ExceptStar | function-body | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-022 | ExceptStar | module-level | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-023 | ExceptStar | try-body | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-024 | ExceptStar | except-handler | d2 双层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-025 | ExceptStar | else-of-try | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-026 | ExceptStar | finally-body | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-027 | ExceptStar | if-arm | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-028 | ExceptStar | loop-body | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-029 | ExceptStar | with-body | d1 单层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-030 | ExceptStar | nested-func-body | d2 双层 | es-with-else | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-031 | ExceptStar | function-body | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-032 | ExceptStar | module-level | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-033 | ExceptStar | try-body | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-034 | ExceptStar | except-handler | d2 双层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-035 | ExceptStar | else-of-try | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-036 | ExceptStar | finally-body | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-037 | ExceptStar | if-arm | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-038 | ExceptStar | loop-body | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-039 | ExceptStar | with-body | d1 单层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-040 | ExceptStar | nested-func-body | d2 双层 | es-with-finally | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-041 | ExceptStar | function-body | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-042 | ExceptStar | module-level | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-043 | ExceptStar | try-body | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-044 | ExceptStar | except-handler | d2 双层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-045 | ExceptStar | else-of-try | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-046 | ExceptStar | finally-body | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-047 | ExceptStar | if-arm | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-048 | ExceptStar | loop-body | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-049 | ExceptStar | with-body | d1 单层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-050 | ExceptStar | nested-func-body | d2 双层 | es-group-exception-type | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-051 | ExceptStar | function-body | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-052 | ExceptStar | module-level | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-053 | ExceptStar | try-body | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-054 | ExceptStar | except-handler | d2 双层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-055 | ExceptStar | else-of-try | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-056 | ExceptStar | finally-body | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-057 | ExceptStar | if-arm | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-058 | ExceptStar | loop-body | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-059 | ExceptStar | with-body | d1 单层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-060 | ExceptStar | nested-func-body | d2 双层 | es-starred-capture | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-061 | ExceptStar | function-body | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-062 | ExceptStar | try-body | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-063 | ExceptStar | except-handler | d2 双层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-064 | ExceptStar | else-of-try | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-065 | ExceptStar | finally-body | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-066 | ExceptStar | if-arm | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-067 | ExceptStar | loop-body | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-068 | ExceptStar | with-body | d1 单层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-069 | ExceptStar | nested-func-body | d2 双层 | es-in-func | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-070 | ExceptStar | function-body | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-071 | ExceptStar | try-body | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-072 | ExceptStar | except-handler | d2 双层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-073 | ExceptStar | else-of-try | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-074 | ExceptStar | finally-body | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-075 | ExceptStar | if-arm | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-076 | ExceptStar | loop-body | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-077 | ExceptStar | with-body | d1 单层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-078 | ExceptStar | nested-func-body | d2 双层 | es-in-loop | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-079 | ExceptStar | function-body | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-080 | ExceptStar | try-body | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-081 | ExceptStar | except-handler | d2 双层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-082 | ExceptStar | else-of-try | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-083 | ExceptStar | finally-body | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-084 | ExceptStar | if-arm | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-085 | ExceptStar | loop-body | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-086 | ExceptStar | with-body | d1 单层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-087 | ExceptStar | nested-func-body | d2 双层 | es-in-try | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-088 | ExceptStar | function-body | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-089 | ExceptStar | try-body | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-090 | ExceptStar | except-handler | d2 双层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-091 | ExceptStar | else-of-try | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-092 | ExceptStar | finally-body | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-093 | ExceptStar | if-arm | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-094 | ExceptStar | loop-body | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-095 | ExceptStar | with-body | d1 单层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-EXCEPTSTAR-096 | ExceptStar | nested-func-body | d2 双层 | es-in-with | NEW | `test_repros/round4/c4_03_except_star.pyc` | uncovered |
| JS-ANNASSIGN-001 | AnnAssign | function-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-002 | AnnAssign | module-level | d1 单层 | ann-simple-name | NEW | `test_repros/round2/m08_module_stmts.pyc` | covered |
| JS-ANNASSIGN-003 | AnnAssign | class-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-004 | AnnAssign | if-arm | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-005 | AnnAssign | loop-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-006 | AnnAssign | try-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-007 | AnnAssign | except-handler | d2 双层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-008 | AnnAssign | with-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-009 | AnnAssign | match-case-body | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-010 | AnnAssign | annotation-context | d1 单层 | ann-simple-name | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-011 | AnnAssign | function-body | d1 单层 | ann-subscript-target | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-012 | AnnAssign | module-level | d1 单层 | ann-subscript-target | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-013 | AnnAssign | class-body | d1 单层 | ann-subscript-target | NEW | `test_repros/round2/c01_class_assign.pyc` | uncovered |
| JS-ANNASSIGN-014 | AnnAssign | module-level | d1 单层 | ann-with-value | NEW | `test_repros/round2/m08_module_stmts.pyc` | covered |
| JS-ANNASSIGN-015 | AnnAssign | module-level | d1 单层 | ann-simple-type | NEW | `test_repros/round2/m08_module_stmts.pyc` | covered |
| JS-ASYNCFOR-001 | AsyncFor | async-func-body | d1 单层 | af-in-async-def | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-ASYNCFOR-002 | AsyncFor | async-func-body | d2 双层 | af-in-async-def | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFOR-003 | AsyncFor | function-body | d1 单层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-004 | AsyncFor | comprehension-scope | d1 单层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-005 | AsyncFor | loop-body | d1 单层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-006 | AsyncFor | loop-else | d1 单层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-007 | AsyncFor | if-arm | d3plus 三层及以上 | af-in-async-def | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFOR-008 | AsyncFor | try-body | d1 单层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-009 | AsyncFor | with-body | d2 双层 | af-in-async-def | NEW | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-ASYNCFOR-010 | AsyncFor | nested-func-body | d2 双层 | af-in-async-def | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-011 | AsyncFor | async-func-body | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-012 | AsyncFor | function-body | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-013 | AsyncFor | comprehension-scope | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-014 | AsyncFor | loop-body | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-015 | AsyncFor | loop-else | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-016 | AsyncFor | if-arm | d1 单层 | af-nested-async-for | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFOR-017 | AsyncFor | async-func-body | d1 单层 | af-await-in-body | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-ASYNCFOR-018 | AsyncFor | async-func-body | d2 双层 | af-await-in-body | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFOR-019 | AsyncFor | if-arm | d3plus 三层及以上 | af-await-in-body | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFOR-020 | AsyncFor | with-body | d2 双层 | af-await-in-body | NEW | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-ASYNCFOR-021 | AsyncFor | with-body | d2 双层 | af-in-with | NEW | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-ASYNCWITH-001 | AsyncWith | async-func-body | d1 单层 | aw-in-async-def | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-ASYNCWITH-002 | AsyncWith | async-func-body | d2 双层 | aw-in-async-def | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCWITH-003 | AsyncWith | function-body | d1 单层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-004 | AsyncWith | with-body | d1 单层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-005 | AsyncWith | if-arm | d1 单层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-006 | AsyncWith | loop-body | d3plus 三层及以上 | aw-in-async-def | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCWITH-007 | AsyncWith | try-body | d1 单层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-008 | AsyncWith | except-handler | d2 双层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-009 | AsyncWith | match-case-body | d1 单层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-010 | AsyncWith | nested-func-body | d2 双层 | aw-in-async-def | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-011 | AsyncWith | async-func-body | d1 单层 | aw-single-item | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-ASYNCWITH-012 | AsyncWith | async-func-body | d2 双层 | aw-single-item | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCWITH-013 | AsyncWith | function-body | d1 单层 | aw-single-item | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-014 | AsyncWith | with-body | d1 单层 | aw-single-item | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-015 | AsyncWith | with-item | d1 单层 | aw-single-item | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-016 | AsyncWith | if-arm | d1 单层 | aw-single-item | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-017 | AsyncWith | loop-body | d3plus 三层及以上 | aw-single-item | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCWITH-018 | AsyncWith | try-body | d1 单层 | aw-single-item | NEW | `test_repros/round6/r6_08_async_cross.pyc` | uncovered |
| JS-ASYNCWITH-019 | AsyncWith | async-func-body | d2 双层 | aw-as-target | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCWITH-020 | AsyncWith | loop-body | d3plus 三层及以上 | aw-as-target | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCWITH-021 | AsyncWith | async-func-body | d1 单层 | aw-await-in-body | NEW | `test_repros/round3/e12b_g9_yield_split.pyc` | covered |
| JS-ASYNCWITH-022 | AsyncWith | async-func-body | d2 双层 | aw-await-in-body | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCWITH-023 | AsyncWith | loop-body | d3plus 三层及以上 | aw-await-in-body | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCWITH-024 | AsyncWith | loop-body | d3plus 三层及以上 | aw-in-loop | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFUNC-001 | AsyncFunctionDef | function-body | d1 单层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-002 | AsyncFunctionDef | module-level | d1 单层 | afd-at-module | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-ASYNCFUNC-003 | AsyncFunctionDef | class-body | d1 单层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-004 | AsyncFunctionDef | nested-func-body | d2 双层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-005 | AsyncFunctionDef | decorator-expr | d1 单层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-006 | AsyncFunctionDef | annotation-context | d1 单层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-007 | AsyncFunctionDef | default-arg | d1 单层 | afd-at-module | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-008 | AsyncFunctionDef | function-body | d1 单层 | afd-in-class | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-009 | AsyncFunctionDef | class-body | d1 单层 | afd-in-class | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-ASYNCFUNC-010 | AsyncFunctionDef | nested-func-body | d2 双层 | afd-in-class | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-011 | AsyncFunctionDef | function-body | d1 单层 | afd-nested | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFUNC-012 | AsyncFunctionDef | function-body | d2 双层 | afd-nested | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFUNC-013 | AsyncFunctionDef | module-level | d1 单层 | afd-nested | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-014 | AsyncFunctionDef | class-body | d1 单层 | afd-nested | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-015 | AsyncFunctionDef | nested-func-body | d2 双层 | afd-nested | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-016 | AsyncFunctionDef | decorator-expr | d1 单层 | afd-nested | NEW | `test_repros/round6/r6_07_async_five.pyc` | uncovered |
| JS-ASYNCFUNC-017 | AsyncFunctionDef | function-body | d1 单层 | afd-with-async-with | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFUNC-018 | AsyncFunctionDef | module-level | d1 单层 | afd-with-async-with | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-ASYNCFUNC-019 | AsyncFunctionDef | class-body | d1 单层 | afd-with-async-with | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFUNC-020 | AsyncFunctionDef | function-body | d1 单层 | afd-with-async-for | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFUNC-021 | AsyncFunctionDef | module-level | d1 单层 | afd-with-async-for | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-ASYNCFUNC-022 | AsyncFunctionDef | function-body | d1 单层 | afd-with-await | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFUNC-023 | AsyncFunctionDef | module-level | d1 单层 | afd-with-await | NEW | `test_repros/round3/e09b_g6_async_comps.pyc` | covered |
| JS-ASYNCFUNC-024 | AsyncFunctionDef | class-body | d1 单层 | afd-with-await | NEW | `test_repros/round4/c4_20_async_five.pyc` | covered |
| JS-ASYNCFUNC-025 | AsyncFunctionDef | module-level | d1 单层 | afd-with-yield | NEW | `test_repros/round4/rec1_synth_b112a_asyncgen.pyc` | covered |
| JS-PEP604-001 | PEP604Union | annotation-context | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-002 | PEP604Union | function-body | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-003 | PEP604Union | module-level | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-004 | PEP604Union | class-body | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-005 | PEP604Union | assign-rhs | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-006 | PEP604Union | return-value-expr | d1 单层 | pep604-in-var-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-007 | PEP604Union | annotation-context | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-008 | PEP604Union | function-body | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-009 | PEP604Union | module-level | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-010 | PEP604Union | class-body | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-011 | PEP604Union | assign-rhs | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |
| JS-PEP604-012 | PEP604Union | return-value-expr | d1 单层 | pep604-in-return-annotation | NEW | `core/cfg/ast_converter.py:267` | uncovered |

## 5. 与既有 25 行的双向对齐（Task 1.3）

| # | 25 行 | 空间条目数 | covered | uncovered | 归属判定 |
|---|---|---|---|---|---|
| 1 | If | 118 | 106 | 12 | 已映射 |
| 2 | BoolOp | 85 | 73 | 12 | 已映射 |
| 3 | IfExp | 28 | 16 | 12 | 已映射 |
| 4 | Try | 108 | 96 | 12 | 已映射 |
| 5 | Raise | 39 | 27 | 12 | 已映射 |
| 6 | Assert | 46 | 34 | 12 | 已映射 |
| 7 | Import | 47 | 35 | 12 | 已映射 |
| 8 | Global | 19 | 7 | 12 | 已映射 |
| 9 | global_nonlocal | 40 | 0 | 40 | 已映射 |
| 10 | Await | 23 | 11 | 12 | 已映射 |
| 11 | ListComp | 40 | 28 | 12 | 已映射 |
| 12 | await_expr | 21 | 9 | 12 | 已映射 |
| 13 | Yield | 18 | 6 | 12 | 已映射 |
| 14 | Match | 37 | 25 | 12 | 已映射 |
| 15 | With | 83 | 71 | 12 | 已映射 |
| 16 | match_statement | 60 | 48 | 12 | 已映射 |
| 17 | Break | 32 | 20 | 12 | 已映射 |
| 18 | Continue | 35 | 23 | 12 | 已映射 |
| 19 | While | 45 | 33 | 12 | 已映射 |
| 20 | Delete | 24 | 12 | 12 | 已映射 |
| 21 | AugAssign | 63 | 51 | 12 | 已映射 |
| 22 | Return | 80 | 68 | 12 | 已映射 |
| 23 | Slice | 25 | 13 | 12 | 已映射 |
| 24 | augmented_assign | 49 | 37 | 12 | 已映射 |
| 25 | slice | 32 | 20 | 12 | 已映射 |

**结论**：25 行**无一缺失**（每行在空间中至少 1 条独立条目，且每条要求独立证据）。

### 5.1 NEW 族及其立项依据

| NEW 族 | 依据（真实路径） | 立项理由 |
|---|---|---|
| Lambda | `core/cfg/ast_converter.py:110` | ast.Lambda 是独立文法族（`core/cfg/ast_converter.py:110` 有专有转换器）；上一规范 25 行无对应行。 |
| Decorator | `core/cfg/ast_converter.py:297` | 装饰器列表是函数/类的独立文法位置（`core/cfg/ast_converter.py:297` 读取 `decorator_list`），顺序与参数化形态在产物装配中单独成段；语料 `site-packages/fly/common/aes_encrypt.pyc` 含真实装饰器。 |
| SetComp | `core/cfg/ast_converter.py:104` | ast.SetComp 走 SET_ADD（与 ListComp 的 LIST_APPEND 不同），是独立文法族（`core/cfg/ast_converter.py:104`）。 |
| DictComp | `core/cfg/ast_converter.py:105` | ast.DictComp 走 MAP_ADD，是独立文法族（`core/cfg/ast_converter.py:105`）。 |
| GeneratorExp | `core/cfg/ast_converter.py:106` | ast.GeneratorExp 与 ListComp 共享代码生成路径但语义为惰性生成器（`core/cfg/ast_converter.py:106`）。 |
| NamedExpr | `core/cfg/ast_converter.py:107` | 海象表达式（:=）是 3.8+ 独立文法族（`core/cfg/ast_converter.py:107`）。 |
| JoinedStr | `core/cfg/ast_converter.py:930` | f-string 是独立文法族（`core/cfg/ast_converter.py:930` 专有 `_convert_joined_str_full`）。 |
| Starred | `core/cfg/ast_converter.py:957` | 星号展开在调用实参/解包/字面量三处语义不同（`core/cfg/ast_converter.py:957`）。 |
| ExceptStar | `core/cfg/region_ast_generator.py:9707` | 3.11 `except*` 走独立异常表语义（`core/cfg/region_ast_generator.py:9707` 同时识别 Try/TryStar；`core/cfg/patch_detector.py:194` 列出 TryStar）。 |
| AnnAssign | `core/cfg/ast_converter.py:76` | 带注解赋值是独立文法族（`core/cfg/ast_converter.py:76` 专有 `_convert_ann_assign`）。 |
| AsyncFor | `core/cfg/ast_converter.py:66` | async for 的迭代协议与同步 for 不同（`core/cfg/ast_converter.py:66`）。 |
| AsyncWith | `core/cfg/ast_converter.py:70` | async with 的退出协议与同步 with 不同（`core/cfg/ast_converter.py:70`）。 |
| AsyncFunctionDef | `core/cfg/ast_generator_v2.py:3696` | async def 的协程函数对象与普通函数不同（`core/cfg/ast_generator_v2.py:3696` 把 AsyncFor/AsyncWith 并入函数体区域集合）。 |
| PEP604Union | `core/cfg/ast_converter.py:267` | `X | Y` 联合类型在注解位生成 `types.UnionType`，与 `typing.Union` 路径不同；产品侧按 BinOp 处理（`core/cfg/ast_converter.py:267`）。**本仓语料/探针 0 个 PEP604 样本**（实测扫描 5126 个 .py 全仓无命中）⇒ 整族无见证，属最诚实的缺口。 |

## 6. 诚实缺口声明

- 本表存在 **580 个 uncovered 单元**。它们的 `required_evidence[0].pyc` 指向**同族锚点探针**（仓内真实存在，但**从未**登记进任何 `rec1_probes_*.json` 证据索引），**不**指向该单元的专属探针——因为仓内不存在这样的专属探针。覆盖检查器据此判为未覆盖。
- 未覆盖单元分两类：
  1. **结构性单元尚未可演示（structural cells not yet demonstrable）**：形态/宿主/变体组合在语言上可构造，但既有探针集里没有任何一个探针同时满足「该形态 + 该宿主 + 该深度档 + 该变体」；
  2. **整族零证据**：`global_nonlocal`（**25 行之一**，40 条）与 NEW 族 `ExceptStar`（96 条）**整族无任何见证探针**——这是本次攻击最硬的发现：上一规范把 `global_nonlocal` 判为「完备」，但其证据索引里没有任何一个探针包含 `ast.Nonlocal` 节点。
- 「covered」在本表内**只表示「该单元有专属见证探针」**，不表示「该单元的产物语义正确」——后者属语义级差分（Task 6/9 `semantic_diff.py`）与变异测试（Task 9 `mutation_test.py`）的判据，本轮不做、也不假装做了。
- **空间是「优先序化」的，不是穷尽的**：按 §2 规则，可构造的 (form,variant,host) 三元组共 4229 个，其中 671 个已有观测、**3558 个无观测**；本表按「每族最多登记 12 条结构性单元」的规则优先登记其中一部分（整族零证据者不截断）。因此「uncovered = 580」是**已登记**缺口数，真实缺口规模上界为 3558 —— 空间随证据增长而扩张（Task 3 的 L1 口径攻击负责把余量并入）。

