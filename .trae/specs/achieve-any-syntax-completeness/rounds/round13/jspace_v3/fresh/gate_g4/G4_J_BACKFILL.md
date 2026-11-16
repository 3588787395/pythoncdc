# G4 的 J 补充清单（44 条 d 类）

**状态：可执行工作项；未写任何探针、未新增/修改 J 条目。**

- 分类来源：`fresh/gate_g4/g4_d3_classification.json`（d=44）
- 修复后状态：`fresh/gate_g4/proof_records_guardfix_after.json`
- anchor 上下文 / 现有最接近 J：`D:\temp\opencode\cl_layout\g4fix\d_context.json`
- 机器可读：`fresh/gate_g4/g4_j_backfill.json`

## 0. 一句话结论

44 条落在 **19 个不同的 J 形态**上；按形态合并后覆盖全部 44 条**最少 18 条探针**。口径修复后其中 **16 条已拿到正发生点**，仍缺正发生点的 **28 条** ⇒ 真正需要新探针的最少条数为 **16**。

## 1. 合并分析（同一 J 形态覆盖多条）

| 组 | 覆盖规则 | 修复后仍缺正发生点 | 探针数 | 为什么能合并 |
|---|---|---|---|---|
| `G1a-expression-dict-ir` | 16 | 6 | 1 | 一条源文件里的所有表达式都经 dict-IR 回退路径生成；同一条目里同时包含 dict/set/tuple/subscript/slice/f-string/boolop/unaryop/compare/attribute/await 与四种推导式即可覆盖 16 条 |
| `G1b-statement-dict-ir` | 5 | 3 | 1 | 一条生成器/循环体条目：语句级 Lambda、yield、yield from 与 for 目标（tuple 目标、占位名 <target>）、<lambda> 函数定义各出现一次 |
| `G2a-async-for` | 1 | 0 | 1 | 一条 async for 条目（async def 内的 async for 循环体） |
| `G2b-dict-set-unpack` | 2 | 1 | 1 | 一条同时含 {**a, **b} 与 {*a, *b} 的条目（MAP_ADD 与 SET_UPDATE 同源） |
| `G2c-match-mapping` | 2 | 0 | 1 | 一条 mapping pattern 的 match 条目（MATCH_MAPPING 与 MATCH_KEYS 同一 case） |
| `G2d-unary-not-pos-neg` | 3 | 3 | 1 | 一条同时出现 not x / +x / -x 的条目（三成员守卫一次满足） |
| `G2e-boolop-unary-invert` | 1 | 1 | 1 | 一条布尔链里出现 ~x 的条目（分组 boolop 构建器路径） |
| `G2f-setup-annotations` | 1 | 1 | 1 | 一条模块级注解 + 前导 import 的条目（SETUP_ANNOTATIONS 落在块前缀） |
| `G3a-comp-in-closure` | 1 | 1 | 1 | 一条函数体内捕获外层自由变量的推导式（cell/closure setup） |
| `G3b-comp-first-instr-stop` | 1 | 1 | 1 | 一条首指令落在停机集合内的推导式（FOR_ITER/LIST_APPEND 等） |
| `G3c-comp-bool-chain` | 1 | 1 | 1 | 一条推导式 if 子句里含 and/or（JUMP_IF_*_OR_POP）的条目 |
| `G3d-dictcomp-pad` | 1 | 1 | 1 | 一条 dict 推导，键值切分点前有 RESUME/NOP/CACHE/PUSH_NULL |
| `G3e-try-fin-with-machinery` | 1 | 1 | 1 | 一条 try/finally 尾部含 with/异常机制指令的条目 |
| `G3f-boolop-store-after-pin` | 1 | 1 | 1 | 一条 bool 链实现中 pin 之后仍有 STORE_* 的条目 |
| `G3g-diamond-true-polarity` | 1 | 1 | 1 | 一条 if/else 取值（diamond）且条件跳转为 POP_JUMP_*_IF_TRUE 的条目 |
| `G3h-ternary-walrus-prestore` | 1 | 1 | 1 | 一条三元表达式条件里带 walrus（先 STORE）的条目 |
| `G3i-literal-region-walrus` | 3 | 3 | 1 | 一条字面量构建 + walrus 整合指令同区的条目（_lit_skip_ops / _LITERAL_BUILD_OPS / _WALRUS_INTEGRATING_OPS 三条同点） |
| `G4-lambda-as-functiondef` | 1 | 1 | 1 | 一条 lambda 未经上游拦截、作为 FunctionDef(name='<lambda>') 进入 _generate_function_def 的条目 |
| `GX-class-body-return` | 1 | 1 | 0 | 不可构造：类体级 Return 在 CPython 语法上不存在；建议按 a 类（不可满足）处理 |
| **合计** | **44** | **28** | **18** | — |

### 1.1 修复后仍需动作的三类

- **已无需动作（12 条，口径修复后已 proved）**：`SetComp`、`ListComp`、`FormattedValue`、`DictComp`、`GeneratorExp`、`END_ASYNC_FOR`、`JoinedStr`、`MATCH_KEYS`、`MAP_ADD`、`Lambda`、`MATCH_MAPPING`、`Subscript`
- **只需反例条目（4 条，已有正发生点、缺严格负 witness）**：`Set`、`Tuple`、`Dict`、`Attribute`
- **需要新探针（28 条，仍缺正发生点）**：`YieldFrom`、`UNARY_INVERT`、`UnaryOp`、`<target>`、`_closure_setup`、`Slice`、`_pre_store_ops`、`Yield`、`_b113_stop_ops`、`<lambda>`、`_STORE_CHK_P21`、`Return`、`_pad`、`UNARY_NOT`、`Await`、`_lit_skip_ops`、`_kop_names`、`_LITERAL_BUILD_OPS`、`UNARY_POSITIVE`、`SETUP_ANNOTATIONS`、`_TRUE_POLARITY_COND_JUMP_OPS`、`BoolOp`、`Iter`、`UNARY_NEGATIVE`、`_b68_machinery`、`Compare`、`_WALRUS_INTEGRATING_OPS`、`SET_UPDATE`

合并的三个层次：

1. **同 anchor 同守卫**：`UNARY_NOT/POSITIVE/NEGATIVE` 是同一个三元组守卫的三条规则；`MATCH_MAPPING`+`MATCH_KEYS` 同一个 case；`_lit_skip_ops`+`_LITERAL_BUILD_OPS`+`_WALRUS_INTEGRATING_OPS` 同一个扫描点 ⇒ 一条 J 同时满足多条。
2. **同路径不同节点**：17 条 dict-IR 规则都是 `_generate_expression`/`_generate_dict_node` 的 dict 回退分支；一条让 region 流水线产出 dict-IR 的 J 可以在同一运行里命中多条（每条只要求本节点类型出现过一次）。
3. **不可合并**：11 条命名集合守卫各自依赖不同的扫描位置（closure setup、首指令停机集、bool 极化、pin/store 顺序、字面量区…），组间只能各给一条。

## 2. 44 条逐条

每条：rule_id / anchor / 需要的语法形态 / 现有最接近 J / 建议的新 J 形态（`expected_label.form/host/depth/variant`）/ 修复后状态。

### RULE-0453cb2cf048 · `YieldFrom` · `core/cfg/code_generator.py:456`

- **pattern**：`node_type == 'YieldFrom'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_dict_node`）：`elif node_type == 'YieldFrom':`
- **需要的语法形态**：生成器函数体里的 yield from 语句以 dict（{'type': 'YieldFrom'}）到达
- **IR 触发点**：code_generator.py:456 `elif node_type == 'YieldFrom'`（yield from 语句）
- **现有最接近 J**：`JS-FSTRING-001`（label `{"form": "JoinedStr", "variant": "fstring-plain", "host": "function-body", "depth": "d1 单层"}`；匹配依据：没有 form 命中的条目；取「在该 anchor 所在文件上求值规则数最多」的条目（31 条同文件规则）；该规则共 412 条 J 求值过）
- **建议新形态**：`form=Yield` / `host=generator-func-body` / `depth=d1 单层` / `variant=yield-from-statement`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G1b-statement-dict-ir`（组内共用 1 条探针）

### RULE-097f2c50ba6b · `UNARY_INVERT` · `core/cfg/region_ast_generator.py:51769`

- **pattern**：`inst.opname == 'UNARY_INVERT'`（anchor 级 pattern_class `opcode_eq`）
- **锚点语句**（`function _build_grouped_boolop_expression`）：`elif inst.opname == 'UNARY_INVERT':`
- **需要的语法形态**：布尔链里出现按位取反 ~x（if ~x and y: 这类分组 boolop 路径）
- **IR 触发点**：region_ast_generator.py:51769 `elif inst.opname == 'UNARY_INVERT'`
- **现有最接近 J**：`JS-BOOLOP-005`（label `{"form": "BoolOp", "variant": "boolop-and", "host": "else-arm", "depth": "d3plus 三层及以上"}`；匹配依据：form 命中 `BoolOp`（该 rule 的求值条目里 13 条是此 form）；该规则共 262 条 J 求值过）
- **建议新形态**：`form=BoolOp` / `host=condition-expr` / `depth=d2 双层` / `variant=boolop-unary-invert`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G2e-boolop-unary-invert`（组内共用 1 条探针）

### RULE-09e890625a53 · `UnaryOp` · `core/cfg/code_generator.py:3963`

- **pattern**：`node_type == 'UnaryOp'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'UnaryOp':`
- **需要的语法形态**：一元表达式 not x / -x 以 dict（{'type': 'UnaryOp'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:3963 `elif node_type == 'UnaryOp'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-BOOLOP-004`（label `{"form": "BoolOp", "variant": "boolop-and", "host": "else-arm", "depth": "d2 双层"}`；匹配依据：form 命中 `BoolOp`（该 rule 的求值条目里 20 条是此 form）；该规则共 412 条 J 求值过）
- **建议新形态**：`form=UnaryOp` / `host=assign-rhs` / `depth=d1 单层` / `variant=dict-ir-unaryop`（form 为新增词表项）
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-0c6da108567a · `<target>` · `core/cfg/code_generator.py:2116`

- **pattern**：`name == '<target>'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_for_target`）：`if name == '<target>':`
- **需要的语法形态**：for 目标是一个占位名 <target> 的 ASTName（region 归约取不到名字时的占位）
- **IR 触发点**：code_generator.py:2116 `if name == '<target>'`（_generate_for_target）
- **现有最接近 J**：`JS-WHILE-002`（label `{"form": "While", "variant": "while-true", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `While`（该 rule 的求值条目里 28 条是此 form）；该规则共 1152 条 J 求值过）
- **建议新形态**：`form=For` / `host=loop-body` / `depth=d2 双层` / `variant=for-target-placeholder`（form 为新增词表项）
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G1b-statement-dict-ir`（组内共用 1 条探针）

### RULE-1576dfcf29af · `_closure_setup` · `core/cfg/comprehension_generator.py:554`

- **pattern**：`_pw.opname in _closure_setup`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function try_generate_comprehension_assign`）：`if _pw.opname in _closure_setup:`
- **需要的语法形态**：函数体内的推导式，且该函数捕获外层自由变量（closure setup 指令序列）
- **IR 触发点**：comprehension_generator.py:554 `if _pw.opname in _closure_setup`（集合 MAKE_CELL/LOAD_CLOSURE/COPY_FREE_VARS）
- **现有最接近 J**：`JS-LISTCOMP-001`（label `{"form": "ListComp", "variant": "listcomp-single-for", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `ListComp`（该 rule 的求值条目里 29 条是此 form）；该规则共 339 条 J 求值过）
- **建议新形态**：`form=ListComp` / `host=nested-func-body` / `depth=d2 双层` / `variant=comp-in-closure`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3a-comp-in-closure`（组内共用 1 条探针）

### RULE-1ac0b3bb7543 · `SetComp` · `core/cfg/code_generator.py:3784`

- **pattern**：`node_type == 'SetComp'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'SetComp':`
- **需要的语法形态**：{x for x in it} 推导式的 IR 以 dict（{'type': 'SetComp'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:3784 `elif node_type == 'SetComp'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-LISTCOMP-003`（label `{"form": "ListComp", "variant": "listcomp-single-for", "host": "assign-rhs", "depth": "d1 单层"}`；匹配依据：form 命中 `ListComp`（该 rule 的求值条目里 14 条是此 form）；该规则共 424 条 J 求值过）
- **建议新形态**：`form=SetComp` / `host=assign-rhs` / `depth=d1 单层` / `variant=dict-ir-setcomp`
- **修复后状态**：`proved`，true=1；后续工作：`none`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-1dc9e2f98754 · `Slice` · `core/cfg/code_generator.py:3930`

- **pattern**：`node_type == 'Slice'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'Slice':`
- **需要的语法形态**：切片 a[1:2] 的 Slice 子节点以 dict 形式到达 _generate_expression
- **IR 触发点**：code_generator.py:3930 `elif node_type == 'Slice'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-SLICE-001`（label `{"form": "Slice", "variant": "slice-plain", "host": "subscript-index", "depth": "d1 单层"}`；匹配依据：form 命中 `Slice`（该 rule 的求值条目里 11 条是此 form）；该规则共 412 条 J 求值过）
- **建议新形态**：`form=Slice` / `host=slice-bounds` / `depth=d2 双层` / `variant=dict-ir-slice`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-1ebd3fdc3786 · `_pre_store_ops` · `core/cfg/region_ast_generator.py:59014`

- **pattern**：`_ri.opname in _pre_store_ops`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function _generate_ternary`）：`if _ri.opname in _pre_store_ops:`
- **需要的语法形态**：三元表达式条件里含 walrus，且 STORE_* 出现在取值表达式之前
- **IR 触发点**：region_ast_generator.py:59014 `if _ri.opname in _pre_store_ops`（frozenset STORE_FAST/NAME/GLOBAL/DEREF）
- **现有最接近 J**：`JS-IFEXP-001`（label `{"form": "IfExp", "variant": "ifexp-in-return", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `IfExp`（该 rule 的求值条目里 12 条是此 form）；该规则共 14 条 J 求值过）
- **建议新形态**：`form=IfExp` / `host=assign-rhs` / `depth=d2 双层` / `variant=ternary-walrus-prestore`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3h-ternary-walrus-prestore`（组内共用 1 条探针）

### RULE-2331b38d9765 · `ListComp` · `core/cfg/code_generator.py:3782`

- **pattern**：`node_type == 'ListComp'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'ListComp':`
- **需要的语法形态**：[x for x in it] 推导式的 IR 以 dict（{'type': 'ListComp'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:3782 `elif node_type == 'ListComp'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-LISTCOMP-003`（label `{"form": "ListComp", "variant": "listcomp-single-for", "host": "assign-rhs", "depth": "d1 单层"}`；匹配依据：form 命中 `ListComp`（该 rule 的求值条目里 14 条是此 form）；该规则共 424 条 J 求值过）
- **建议新形态**：`form=ListComp` / `host=assign-rhs` / `depth=d1 单层` / `variant=dict-ir-listcomp`
- **修复后状态**：`proved`，true=1；后续工作：`none`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-2ad1ffa97019 · `Set` · `core/cfg/code_generator.py:4047`

- **pattern**：`node_type == 'Set'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'Set':`
- **需要的语法形态**：集合字面量 {1, 2} 以 dict（{'type': 'Set'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:4047 `elif node_type == 'Set'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-FSTRING-001`（label `{"form": "JoinedStr", "variant": "fstring-plain", "host": "function-body", "depth": "d1 单层"}`；匹配依据：没有 form 命中的条目；取「在该 anchor 所在文件上求值规则数最多」的条目（31 条同文件规则）；该规则共 12 条 J 求值过）
- **建议新形态**：`form=Set` / `host=assign-rhs` / `depth=d1 单层` / `variant=dict-ir-set-literal`（form 为新增词表项）
- **修复后状态**：`open`，true=2，原因 negative_witness_missing；后续工作：`negative_witness`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-2e321a33507c · `FormattedValue` · `core/cfg/code_generator.py:3935`

- **pattern**：`node_type == 'FormattedValue'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'FormattedValue':`
- **需要的语法形态**：整个右值只是一个 FormattedValue（如 s = f'{x:>{w}}'）并以 dict 形式到达
- **IR 触发点**：code_generator.py:3935 `elif node_type == 'FormattedValue'`（顶层 FormattedValue）
- **现有最接近 J**：`JS-FSTRING-001`（label `{"form": "JoinedStr", "variant": "fstring-plain", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `JoinedStr`（该 rule 的求值条目里 32 条是此 form）；该规则共 412 条 J 求值过）
- **建议新形态**：`form=JoinedStr` / `host=assign-rhs` / `depth=d1 单层` / `variant=dict-ir-formattedvalue-toplevel`
- **修复后状态**：`proved`，true=1；后续工作：`none`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-3114624d4364 · `Yield` · `core/cfg/code_generator.py:448`

- **pattern**：`node_type == 'Yield'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_dict_node`）：`elif node_type == 'Yield':`
- **需要的语法形态**：生成器函数体里的 yield 语句以 dict（{'type': 'Yield'}）到达 _generate_dict_node
- **IR 触发点**：code_generator.py:448 `elif node_type == 'Yield'`（yield 语句）
- **现有最接近 J**：`JS-FSTRING-001`（label `{"form": "JoinedStr", "variant": "fstring-plain", "host": "function-body", "depth": "d1 单层"}`；匹配依据：没有 form 命中的条目；取「在该 anchor 所在文件上求值规则数最多」的条目（31 条同文件规则）；该规则共 412 条 J 求值过）
- **建议新形态**：`form=Yield` / `host=generator-func-body` / `depth=d1 单层` / `variant=yield-statement`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G1b-statement-dict-ir`（组内共用 1 条探针）

### RULE-33f06058607b · `DictComp` · `core/cfg/code_generator.py:3780`

- **pattern**：`node_type == 'DictComp'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`if node_type == 'DictComp':`
- **需要的语法形态**：{k: v for k, v in it} 推导式的 IR 以 dict（{'type': 'DictComp'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:3780 `if node_type == 'DictComp'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-DICTCOMP-003`（label `{"form": "DictComp", "variant": "dictcomp-single-for", "host": "assign-rhs", "depth": "d2 双层"}`；匹配依据：form 命中 `DictComp`（该 rule 的求值条目里 3 条是此 form）；该规则共 424 条 J 求值过）
- **建议新形态**：`form=DictComp` / `host=assign-rhs` / `depth=d1 单层` / `variant=dict-ir-dictcomp`
- **修复后状态**：`proved`，true=1；后续工作：`none`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-40c5ed4fe165 · `GeneratorExp` · `core/cfg/code_generator.py:3786`

- **pattern**：`node_type == 'GeneratorExp'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'GeneratorExp':`
- **需要的语法形态**：(x for x in it) 生成器表达式以 dict（{'type': 'GeneratorExp'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:3786 `elif node_type == 'GeneratorExp'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-GENEXP-007`（label `{"form": "GeneratorExp", "variant": "genexp-single-for", "host": "call-arg", "depth": "d3plus 三层及以上"}`；匹配依据：form 命中 `GeneratorExp`（该 rule 的求值条目里 2 条是此 form）；该规则共 424 条 J 求值过）
- **建议新形态**：`form=GeneratorExp` / `host=call-arg` / `depth=d1 单层` / `variant=dict-ir-genexp`
- **修复后状态**：`proved`，true=1；后续工作：`none`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-4743f0da62f0 · `_b113_stop_ops` · `core/cfg/comprehension_generator.py:2379`

- **pattern**：`first_instr.opname in _b113_stop_ops`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function _b113_extract_flat_clauses`）：`if first_instr.opname in _b113_stop_ops:`
- **需要的语法形态**：推导式的首指令本身落在停机集合内（FOR_ITER/LIST_APPEND/SET_ADD/MAP_ADD/YIELD_VALUE…）
- **IR 触发点**：comprehension_generator.py:2379 `if first_instr.opname in _b113_stop_ops`（16 成员，14 个 3.11 活操作码）
- **现有最接近 J**：`JS-LISTCOMP-001`（label `{"form": "ListComp", "variant": "listcomp-single-for", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `ListComp`（该 rule 的求值条目里 40 条是此 form）；该规则共 616 条 J 求值过）
- **建议新形态**：`form=ListComp` / `host=comprehension-scope` / `depth=d1 单层` / `variant=comp-first-in-str-in-stop-set`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3b-comp-first-instr-stop`（组内共用 1 条探针）

### RULE-4773744d80c4 · `<lambda>` · `core/cfg/code_generator.py:2396`

- **pattern**：`node.name == '<lambda>'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_function_def`）：`if node.name == '<lambda>':`
- **需要的语法形态**：lambda 的 code object 被构造为 FunctionDef(name='<lambda>') 并进入 _generate_function_def
- **IR 触发点**：code_generator.py:2396 `if node.name == '<lambda>'`
- **现有最接近 J**：`JS-LAMBDA-001`（label `{"form": "Lambda", "variant": "lambda-in-assign", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `Lambda`（该 rule 的求值条目里 18 条是此 form）；该规则共 1524 条 J 求值过）
- **建议新形态**：`form=Lambda` / `host=function-body` / `depth=d1 单层` / `variant=lambda-as-functiondef`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G4-lambda-as-functiondef`（组内共用 1 条探针）

### RULE-4982a763071c · `_STORE_CHK_P21` · `core/cfg/region_ast_generator.py:54561`

- **pattern**：`_pinstr_p21.opname in _STORE_CHK_P21`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function _generate_boolop_impl`）：`if _pinstr_p21.opname in _STORE_CHK_P21:`
- **需要的语法形态**：bool 链实现中，pin 指令串在 store 之后仍出现 STORE_*（_STORE_CHK_P21 命中）
- **IR 触发点**：region_ast_generator.py:54561 `if _pinstr_p21.opname in _STORE_CHK_P21`（6 成员）
- **现有最接近 J**：`JS-BOOLOP-008`（label `{"form": "BoolOp", "variant": "boolop-and", "host": "condition-expr", "depth": "d3plus 三层及以上"}`；匹配依据：form 命中 `BoolOp`（该 rule 的求值条目里 20 条是此 form）；该规则共 56 条 J 求值过）
- **建议新形态**：`form=BoolOp` / `host=condition-expr` / `depth=d2 双层` / `variant=boolop-store-after-pin`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3f-boolop-store-after-pin`（组内共用 1 条探针）

### RULE-4f466f58c93b · `Return` · `core/cfg/ast_converter.py:340`

- **pattern**：`node_type == 'Return'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _convert_class_def`）：`if node_type == 'Return':`
- **需要的语法形态**：类体级别出现 Return 节点（convert() 在类体列表里遇到 {'type': 'Return'}）
- **IR 触发点**：ast_converter.py:340 `if node_type == 'Return'`（类体过滤）
- **现有最接近 J**：`JS-RETURN-015`（label `{"form": "Return", "variant": "return-value", "host": "function-body", "depth": "d3plus 三层及以上"}`；匹配依据：form 命中 `Return`（该 rule 的求值条目里 31 条是此 form）；该规则共 698 条 J 求值过）
- **建议新形态**：`form=Return` / `host=class-body` / `depth=d1 单层` / `variant=class-body-return`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`GX-class-body-return`（组内共用 1 条探针）

### RULE-4fb15b673728 · `Tuple` · `core/cfg/code_generator.py:2150`

- **pattern**：`node_type == 'Tuple'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_for_target_from_dict`）：`elif node_type == 'Tuple':`
- **需要的语法形态**：for 目标以 dict-IR Tuple 形式出现（for a, b in pairs，目标来自 dict 而不是 ASTTuple）
- **IR 触发点**：code_generator.py:2150 `elif node_type == 'Tuple'`（_generate_for_target_from_dict）
- **现有最接近 J**：`JS-FSTRING-001`（label `{"form": "JoinedStr", "variant": "fstring-plain", "host": "function-body", "depth": "d1 单层"}`；匹配依据：没有 form 命中的条目；取「在该 anchor 所在文件上求值规则数最多」的条目（31 条同文件规则）；该规则共 12 条 J 求值过）
- **建议新形态**：`form=For` / `host=loop-body` / `depth=d2 双层` / `variant=for-target-tuple-dict`（form 为新增词表项）
- **修复后状态**：`open`，true=2，原因 negative_witness_missing；后续工作：`negative_witness`
- **探针组**：`G1b-statement-dict-ir`（组内共用 1 条探针）

### RULE-51cc986d9724 · `_pad` · `core/cfg/comprehension_generator.py:6219`

- **pattern**：`_ins.opname in _pad`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function _b271_dict_comp_kv`）：`if _ins.opname in _pad:`
- **需要的语法形态**：dict 推导的键值切分点前是填充指令（RESUME/NOP/CACHE/PUSH_NULL）
- **IR 触发点**：comprehension_generator.py:6219 `if _ins.opname in _pad`（4 成员）
- **现有最接近 J**：`JS-DICTCOMP-003`（label `{"form": "DictComp", "variant": "dictcomp-single-for", "host": "assign-rhs", "depth": "d2 双层"}`；匹配依据：form 命中 `DictComp`（该 rule 的求值条目里 5 条是此 form）；该规则共 39 条 J 求值过）
- **建议新形态**：`form=DictComp` / `host=assign-rhs` / `depth=d1 单层` / `variant=dictcomp-pad-before-split`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3d-dictcomp-pad`（组内共用 1 条探针）

### RULE-6cbf68b0c7ca · `END_ASYNC_FOR` · `core/cfg/ast_generator_v2.py:8409`

- **pattern**：`opname == 'END_ASYNC_FOR'`（anchor 级 pattern_class `opcode_eq`）
- **锚点语句**（`function _generate_block_content_skip_iterator`）：`elif opname == 'END_ASYNC_FOR':`
- **需要的语法形态**：async def 内的 async for 循环（END_ASYNC_FOR 收尾指令）
- **IR 触发点**：ast_generator_v2.py:8409 `elif opname == 'END_ASYNC_FOR'`
- **现有最接近 J**：`JS-ASYNCFOR-001`（label `{"form": "AsyncFor", "variant": "af-in-async-def", "host": "async-func-body", "depth": "d1 单层"}`；匹配依据：form 命中 `AsyncFor`（该 rule 的求值条目里 6 条是此 form）；该规则共 663 条 J 求值过）
- **建议新形态**：`form=AsyncFor` / `host=async-func-body` / `depth=d1 单层` / `variant=async-for-plain`
- **修复后状态**：`proved`，true=5；后续工作：`none`
- **探针组**：`G2a-async-for`（组内共用 1 条探针）

### RULE-7437333913d0 · `Dict` · `core/cfg/code_generator.py:4055`

- **pattern**：`node_type == 'Dict'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'Dict':`
- **需要的语法形态**：字典字面量 {'a': 1} 以 dict（{'type': 'Dict'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:4055 `elif node_type == 'Dict'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-FSTRING-001`（label `{"form": "JoinedStr", "variant": "fstring-plain", "host": "function-body", "depth": "d1 单层"}`；匹配依据：没有 form 命中的条目；取「在该 anchor 所在文件上求值规则数最多」的条目（31 条同文件规则）；该规则共 12 条 J 求值过）
- **建议新形态**：`form=Dict` / `host=assign-rhs` / `depth=d1 单层` / `variant=dict-ir-dict-literal`（form 为新增词表项）
- **修复后状态**：`open`，true=2，原因 negative_witness_missing；后续工作：`negative_witness`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-762ec4ca09c6 · `UNARY_NOT` · `core/cfg/ast_generator_v2.py:6571`

- **pattern**：`opname in ('UNARY_NOT', 'UNARY_POSITIVE', 'UNARY_NEGATIVE')`（anchor 级 pattern_class `opcode_in_set`）
- **锚点语句**（`function _generate_entry_sequence`）：`elif opname in ('UNARY_NOT', 'UNARY_POSITIVE', 'UNARY_NEGATIVE'):`
- **需要的语法形态**：逻辑非 not x（UNARY_NOT）
- **IR 触发点**：ast_generator_v2.py:6571 同一三成员守卫
- **现有最接近 J**：`JS-BOOLOP-005`（label `{"form": "BoolOp", "variant": "boolop-and", "host": "else-arm", "depth": "d3plus 三层及以上"}`；匹配依据：form 命中 `BoolOp`（该 rule 的求值条目里 13 条是此 form）；该规则共 274 条 J 求值过）
- **建议新形态**：`form=UnaryOp` / `host=condition-expr` / `depth=d1 单层` / `variant=unary-not`（form 为新增词表项）
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G2d-unary-not-pos-neg`（组内共用 1 条探针）

### RULE-823cae0aab30 · `JoinedStr` · `core/cfg/code_generator.py:3932`

- **pattern**：`node_type == 'JoinedStr'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'JoinedStr':`
- **需要的语法形态**：f-string 以 dict（{'type': 'JoinedStr'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:3932 `elif node_type == 'JoinedStr'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-FSTRING-001`（label `{"form": "JoinedStr", "variant": "fstring-plain", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `JoinedStr`（该 rule 的求值条目里 32 条是此 form）；该规则共 412 条 J 求值过）
- **建议新形态**：`form=JoinedStr` / `host=assign-rhs` / `depth=d1 单层` / `variant=dict-ir-joinedstr`
- **修复后状态**：`proved`，true=1；后续工作：`none`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-84fd5ec5ec83 · `Await` · `core/cfg/code_generator.py:3969`

- **pattern**：`node_type == 'Await'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'Await':`
- **需要的语法形态**：await f() 表达式以 dict（{'type': 'Await'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:3969 `elif node_type == 'Await'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-FSTRING-001`（label `{"form": "JoinedStr", "variant": "fstring-plain", "host": "function-body", "depth": "d1 单层"}`；匹配依据：没有 form 命中的条目；取「在该 anchor 所在文件上求值规则数最多」的条目（31 条同文件规则）；该规则共 412 条 J 求值过）
- **建议新形态**：`form=Await` / `host=async-func-body` / `depth=d1 单层` / `variant=dict-ir-await`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-8637d89b4417 · `Attribute` · `core/cfg/code_generator.py:4032`

- **pattern**：`node_type == 'Attribute'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'Attribute':`
- **需要的语法形态**：属性访问 a.b 以 dict（{'type': 'Attribute'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:4032 `elif node_type == 'Attribute'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-FSTRING-001`（label `{"form": "JoinedStr", "variant": "fstring-plain", "host": "function-body", "depth": "d1 单层"}`；匹配依据：没有 form 命中的条目；取「在该 anchor 所在文件上求值规则数最多」的条目（31 条同文件规则）；该规则共 12 条 J 求值过）
- **建议新形态**：`form=Attribute` / `host=assign-rhs` / `depth=d1 单层` / `variant=dict-ir-attribute`（form 为新增词表项）
- **修复后状态**：`open`，true=2，原因 negative_witness_missing；后续工作：`negative_witness`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-8b54bff8cdbb · `_lit_skip_ops` · `core/cfg/region_ast_generator.py:73913`

- **pattern**：`ri.opname in _lit_skip_ops`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function _generate_block_statements_body`）：`if ri.opname in _lit_skip_ops:`
- **需要的语法形态**：字面量区域扫描的第一个剩余指令是填充指令（RESUME/NOP/CACHE/PUSH_NULL）
- **IR 触发点**：region_ast_generator.py:73913 `if ri.opname in _lit_skip_ops`（4 成员）
- **现有最接近 J**：`JS-NAMEDEXPR-001`（label `{"form": "NamedExpr", "variant": "namedexpr-in-if-cond", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `NamedExpr`（该 rule 的求值条目里 12 条是此 form）；该规则共 12 条 J 求值过）
- **建议新形态**：`form=AnnAssign` / `host=assign-rhs` / `depth=d1 单层` / `variant=literal-region-pad-first`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3i-literal-region-walrus`（组内共用 1 条探针）

### RULE-9bedfd5ee85e · `MATCH_KEYS` · `core/cfg/ast_generator_v2.py:2930`

- **pattern**：`opname == 'MATCH_KEYS'`（anchor 级 pattern_class `opcode_eq`）
- **锚点语句**（`function _process_instruction`）：`elif opname == 'MATCH_KEYS':`
- **需要的语法形态**：同一个 mapping pattern 的键匹配（MATCH_KEYS，与 MATCH_MAPPING 同一 case）
- **IR 触发点**：ast_generator_v2.py:2930 `elif opname == 'MATCH_KEYS'`
- **现有最接近 J**：`JS-MATCHPAT-002`（label `{"form": "Match", "variant": "pat-literal", "host": "match-case-body", "depth": "d3plus 三层及以上"}`；匹配依据：form 命中 `Match`（该 rule 的求值条目里 34 条是此 form）；该规则共 1260 条 J 求值过）
- **建议新形态**：`form=Match` / `host=match-subject` / `depth=d1 单层` / `variant=match-mapping-pattern`
- **修复后状态**：`proved`，true=11；后续工作：`none`
- **探针组**：`G2c-match-mapping`（组内共用 1 条探针）

### RULE-aca0cb9d01d5 · `_kop_names` · `core/cfg/comprehension_generator.py:3977`

- **pattern**：`_ins.opname in _kop_names`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function _b247_mixed_boolchain`）：`if _ins.opname in _kop_names:`
- **需要的语法形态**：推导式 if 子句里含 and/or（JUMP_IF_FALSE_OR_POP / JUMP_IF_TRUE_OR_POP）
- **IR 触发点**：comprehension_generator.py:3977 `if _ins.opname in _kop_names`（2 成员）
- **现有最接近 J**：`JS-LISTCOMP-003`（label `{"form": "ListComp", "variant": "listcomp-single-for", "host": "assign-rhs", "depth": "d1 单层"}`；匹配依据：form 命中 `ListComp`（该 rule 的求值条目里 14 条是此 form）；该规则共 87 条 J 求值过）
- **建议新形态**：`form=BoolOp` / `host=comprehension-if` / `depth=d2 双层` / `variant=comp-bool-chain`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3c-comp-bool-chain`（组内共用 1 条探针）

### RULE-b6cb0f6833d9 · `_LITERAL_BUILD_OPS` · `core/cfg/region_ast_generator.py:73920`

- **pattern**：`ri.opname in _LITERAL_BUILD_OPS`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function _generate_block_statements_body`）：`if ri.opname in _LITERAL_BUILD_OPS:`
- **需要的语法形态**：同一区域里出现字面量构建指令（BUILD_MAP/SET/LIST/TUPLE/CONST_KEY_MAP）
- **IR 触发点**：region_ast_generator.py:73920 `if ri.opname in _LITERAL_BUILD_OPS`（5 成员）
- **现有最接近 J**：`JS-NAMEDEXPR-001`（label `{"form": "NamedExpr", "variant": "namedexpr-in-if-cond", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `NamedExpr`（该 rule 的求值条目里 12 条是此 form）；该规则共 12 条 J 求值过）
- **建议新形态**：`form=NamedExpr` / `host=assign-rhs` / `depth=d2 双层` / `variant=literal-build-with-walrus`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3i-literal-region-walrus`（组内共用 1 条探针）

### RULE-b85ddfe6b1a8 · `UNARY_POSITIVE` · `core/cfg/ast_generator_v2.py:6571`

- **pattern**：`opname in ('UNARY_NOT', 'UNARY_POSITIVE', 'UNARY_NEGATIVE')`（anchor 级 pattern_class `opcode_in_set`）
- **锚点语句**（`function _generate_entry_sequence`）：`elif opname in ('UNARY_NOT', 'UNARY_POSITIVE', 'UNARY_NEGATIVE'):`
- **需要的语法形态**：一元正号 +x（UNARY_POSITIVE）
- **IR 触发点**：ast_generator_v2.py:6571 同一三成员守卫
- **现有最接近 J**：`JS-BOOLOP-005`（label `{"form": "BoolOp", "variant": "boolop-and", "host": "else-arm", "depth": "d3plus 三层及以上"}`；匹配依据：form 命中 `BoolOp`（该 rule 的求值条目里 13 条是此 form）；该规则共 274 条 J 求值过）
- **建议新形态**：`form=UnaryOp` / `host=assign-rhs` / `depth=d1 单层` / `variant=unary-positive`（form 为新增词表项）
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G2d-unary-not-pos-neg`（组内共用 1 条探针）

### RULE-b925e75b3739 · `MAP_ADD` · `core/cfg/ast_generator_v2.py:1607`

- **pattern**：`opname == 'MAP_ADD'`（anchor 级 pattern_class `opcode_eq`）
- **锚点语句**（`function _process_instruction`）：`elif opname == 'MAP_ADD':`
- **需要的语法形态**：大字典字面量或字典合并 {**a, **b}（BUILD_MAP 0 + MAP_ADD 序列）
- **IR 触发点**：ast_generator_v2.py:1607 `elif opname == 'MAP_ADD'`
- **现有最接近 J**：`JS-DICTCOMP-001`（label `{"form": "DictComp", "variant": "dictcomp-single-for", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `DictComp`（该 rule 的求值条目里 23 条是此 form）；该规则共 1556 条 J 求值过）
- **建议新形态**：`form=Dict` / `host=dict-literal` / `depth=d1 单层` / `variant=dict-unpack-merge`（form 为新增词表项）
- **修复后状态**：`proved`，true=9；后续工作：`none`
- **探针组**：`G2b-dict-set-unpack`（组内共用 1 条探针）

### RULE-bed4750b6923 · `SETUP_ANNOTATIONS` · `core/cfg/region_ast_generator.py:940`

- **pattern**：`_instr.opname == 'SETUP_ANNOTATIONS'`（anchor 级 pattern_class `opcode_eq`）
- **锚点语句**（`function _extract_imports_from_block_prefix`）：`if _instr.opname == 'SETUP_ANNOTATIONS':`
- **需要的语法形态**：模块级带注解赋值与前导 import 同块（块前缀里出现 SETUP_ANNOTATIONS）
- **IR 触发点**：region_ast_generator.py:940 `if _instr.opname == 'SETUP_ANNOTATIONS'`
- **现有最接近 J**：`JS-ANNASSIGN-001`（label `{"form": "AnnAssign", "variant": "ann-simple-name", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `AnnAssign`（该 rule 的求值条目里 12 条是此 form）；该规则共 461 条 J 求值过）
- **建议新形态**：`form=AnnAssign` / `host=module-level` / `depth=d1 单层` / `variant=module-annotation-with-import`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G2f-setup-annotations`（组内共用 1 条探针）

### RULE-bfbc22d0d1e3 · `Lambda` · `core/cfg/code_generator.py:361`

- **pattern**：`node_type == 'Lambda'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_dict_node`）：`elif node_type == 'Lambda':`
- **需要的语法形态**：语句位置的 lambda 以 dict（{'type': 'Lambda'}）到达 _generate_dict_node
- **IR 触发点**：code_generator.py:361 `elif node_type == 'Lambda'`（语句上下文中的 lambda）
- **现有最接近 J**：`JS-LAMBDA-001`（label `{"form": "Lambda", "variant": "lambda-in-assign", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `Lambda`（该 rule 的求值条目里 14 条是此 form）；该规则共 424 条 J 求值过）
- **建议新形态**：`form=Lambda` / `host=function-body` / `depth=d1 单层` / `variant=dict-ir-stmt-lambda`
- **修复后状态**：`proved`，true=1；后续工作：`none`
- **探针组**：`G1b-statement-dict-ir`（组内共用 1 条探针）

### RULE-cf0dd620521c · `MATCH_MAPPING` · `core/cfg/ast_generator_v2.py:2917`

- **pattern**：`opname == 'MATCH_MAPPING'`（anchor 级 pattern_class `opcode_eq`）
- **锚点语句**（`function _process_instruction`）：`elif opname == 'MATCH_MAPPING':`
- **需要的语法形态**：mapping pattern 的 match：match d: case {'k': v}:
- **IR 触发点**：ast_generator_v2.py:2917 `elif opname == 'MATCH_MAPPING'`
- **现有最接近 J**：`JS-MATCHPAT-002`（label `{"form": "Match", "variant": "pat-literal", "host": "match-case-body", "depth": "d3plus 三层及以上"}`；匹配依据：form 命中 `Match`（该 rule 的求值条目里 34 条是此 form）；该规则共 1260 条 J 求值过）
- **建议新形态**：`form=Match` / `host=match-subject` / `depth=d1 单层` / `variant=match-mapping-pattern`
- **修复后状态**：`proved`，true=11；后续工作：`none`
- **探针组**：`G2c-match-mapping`（组内共用 1 条探针）

### RULE-d0e49b29cc07 · `_TRUE_POLARITY_COND_JUMP_OPS` · `core/cfg/region_ast_generator.py:56270`

- **pattern**：`_cl.opname in _TRUE_POLARITY_COND_JUMP_OPS`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function _try_build_value_diamond_return`）：`if _cl.opname in _TRUE_POLARITY_COND_JUMP_OPS:`
- **需要的语法形态**：if/else 取值（diamond），条件跳转是 POP_JUMP_*_IF_TRUE（真极性）
- **IR 触发点**：region_ast_generator.py:56270 `if _cl.opname in _TRUE_POLARITY_COND_JUMP_OPS`（3 成员）
- **现有最接近 J**：`JS-IFEXP-006`（label `{"form": "IfExp", "variant": "ifexp-in-return", "host": "return-value-expr", "depth": "d3plus 三层及以上"}`；匹配依据：form 命中 `IfExp`（该 rule 的求值条目里 1 条是此 form）；该规则共 44 条 J 求值过）
- **建议新形态**：`form=IfExp` / `host=assign-rhs` / `depth=d1 单层` / `variant=diamond-true-polarity`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3g-diamond-true-polarity`（组内共用 1 条探针）

### RULE-d2b392e7ea86 · `BoolOp` · `core/cfg/code_generator.py:3960`

- **pattern**：`node_type == 'BoolOp'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'BoolOp':`
- **需要的语法形态**：布尔表达式 a and b / a or b 以 dict（{'type': 'BoolOp'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:3960 `elif node_type == 'BoolOp'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-BOOLOP-004`（label `{"form": "BoolOp", "variant": "boolop-and", "host": "else-arm", "depth": "d2 双层"}`；匹配依据：form 命中 `BoolOp`（该 rule 的求值条目里 20 条是此 form）；该规则共 412 条 J 求值过）
- **建议新形态**：`form=BoolOp` / `host=condition-expr` / `depth=d1 单层` / `variant=dict-ir-boolop`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-d46e58a97d98 · `Iter` · `core/cfg/code_generator.py:3790`

- **pattern**：`node_type == 'Iter'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'Iter':`
- **需要的语法形态**：推导式的迭代对象被包装成 {'type': 'Iter'} 后再交给 _generate_expression
- **IR 触发点**：code_generator.py:3790 `elif node_type == 'Iter'`（推导式迭代对象包装）
- **现有最接近 J**：`JS-LISTCOMP-003`（label `{"form": "ListComp", "variant": "listcomp-single-for", "host": "assign-rhs", "depth": "d1 单层"}`；匹配依据：form 命中 `ListComp`（该 rule 的求值条目里 14 条是此 form）；该规则共 424 条 J 求值过）
- **建议新形态**：`form=ListComp` / `host=comprehension-for` / `depth=d2 双层` / `variant=dict-ir-iter-wrapper`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-da070a431a90 · `UNARY_NEGATIVE` · `core/cfg/ast_generator_v2.py:6571`

- **pattern**：`opname in ('UNARY_NOT', 'UNARY_POSITIVE', 'UNARY_NEGATIVE')`（anchor 级 pattern_class `opcode_in_set`）
- **锚点语句**（`function _generate_entry_sequence`）：`elif opname in ('UNARY_NOT', 'UNARY_POSITIVE', 'UNARY_NEGATIVE'):`
- **需要的语法形态**：一元负号 -x（UNARY_NEGATIVE）
- **IR 触发点**：ast_generator_v2.py:6571 `elif opname in ('UNARY_NOT','UNARY_POSITIVE','UNARY_NEGATIVE')`
- **现有最接近 J**：`JS-BOOLOP-005`（label `{"form": "BoolOp", "variant": "boolop-and", "host": "else-arm", "depth": "d3plus 三层及以上"}`；匹配依据：form 命中 `BoolOp`（该 rule 的求值条目里 13 条是此 form）；该规则共 274 条 J 求值过）
- **建议新形态**：`form=UnaryOp` / `host=assign-rhs` / `depth=d1 单层` / `variant=unary-negative`（form 为新增词表项）
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G2d-unary-not-pos-neg`（组内共用 1 条探针）

### RULE-e4932ccfc508 · `_b68_machinery` · `core/cfg/region_ast_generator.py:5399`

- **pattern**：`_b68_ins.opname in _b68_machinery`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function _b68_is_tryfin_tail_releasable`）：`if _b68_ins.opname in _b68_machinery:`
- **需要的语法形态**：try/finally 尾部含 with 或异常机制指令（PUSH_EXC_INFO/RERAISE/POP_EXCEPT…）
- **IR 触发点**：region_ast_generator.py:5399 `if _b68_ins.opname in _b68_machinery`（6 成员）
- **现有最接近 J**：`JS-WITH-001`（label `{"form": "With", "variant": "with-single-item", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `With`（该 rule 的求值条目里 35 条是此 form）；该规则共 300 条 J 求值过）
- **建议新形态**：`form=With` / `host=try-body` / `depth=d2 双层` / `variant=try-finally-with-machinery`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3e-try-fin-with-machinery`（组内共用 1 条探针）

### RULE-e9cd9be060c0 · `Compare` · `core/cfg/code_generator.py:3966`

- **pattern**：`node_type == 'Compare'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'Compare':`
- **需要的语法形态**：比较表达式 x < y 以 dict（{'type': 'Compare'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:3966 `elif node_type == 'Compare'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-BOOLOP-004`（label `{"form": "BoolOp", "variant": "boolop-and", "host": "else-arm", "depth": "d2 双层"}`；匹配依据：form 命中 `BoolOp`（该 rule 的求值条目里 20 条是此 form）；该规则共 412 条 J 求值过）
- **建议新形态**：`form=Compare` / `host=condition-expr` / `depth=d1 单层` / `variant=dict-ir-compare`（form 为新增词表项）
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-eb09655713ec · `_WALRUS_INTEGRATING_OPS` · `core/cfg/region_ast_generator.py:73922`

- **pattern**：`ri.opname in _WALRUS_INTEGRATING_OPS`（anchor 级 pattern_class `opcode_in_named_set`）
- **锚点语句**（`function _generate_block_statements_body`）：`if ri.opname in _WALRUS_INTEGRATING_OPS:`
- **需要的语法形态**：同一区域里出现整合类指令（BINARY_OP/COMPARE_OP/LOAD_ATTR/BINARY_SUBSCR…9 成员）
- **IR 触发点**：region_ast_generator.py:73922 `if ri.opname in _WALRUS_INTEGRATING_OPS`（9 成员）
- **现有最接近 J**：`JS-NAMEDEXPR-001`（label `{"form": "NamedExpr", "variant": "namedexpr-in-if-cond", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `NamedExpr`（该 rule 的求值条目里 12 条是此 form）；该规则共 12 条 J 求值过）
- **建议新形态**：`form=NamedExpr` / `host=if-arm` / `depth=d2 双层` / `variant=walrus-integrating-op`
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G3i-literal-region-walrus`（组内共用 1 条探针）

### RULE-f1e6481a06fe · `Subscript` · `core/cfg/code_generator.py:3910`

- **pattern**：`node_type == 'Subscript'`（anchor 级 pattern_class `ast_marker_eq`）
- **锚点语句**（`function _generate_expression`）：`elif node_type == 'Subscript':`
- **需要的语法形态**：下标表达式 a[i] 以 dict（{'type': 'Subscript'}）到达 _generate_expression
- **IR 触发点**：code_generator.py:3910 `elif node_type == 'Subscript'`（dict-IR 回退路径）
- **现有最接近 J**：`JS-SLICE-001`（label `{"form": "Slice", "variant": "slice-plain", "host": "subscript-index", "depth": "d1 单层"}`；匹配依据：form 命中 `Slice`（该 rule 的求值条目里 11 条是此 form）；该规则共 412 条 J 求值过）
- **建议新形态**：`form=Subscript` / `host=assign-rhs` / `depth=d1 单层` / `variant=dict-ir-subscript`（form 为新增词表项）
- **修复后状态**：`proved`，true=1；后续工作：`none`
- **探针组**：`G1a-expression-dict-ir`（组内共用 1 条探针）

### RULE-f6348059bc55 · `SET_UPDATE` · `core/cfg/ast_generator_v2.py:1655`

- **pattern**：`opname == 'SET_UPDATE'`（anchor 级 pattern_class `opcode_eq`）
- **锚点语句**（`function _process_instruction`）：`elif opname == 'SET_UPDATE':`
- **需要的语法形态**：集合字面量展开 {*a, *b}（BUILD_SET 0 + SET_UPDATE）
- **IR 触发点**：ast_generator_v2.py:1655 `elif opname == 'SET_UPDATE'`
- **现有最接近 J**：`JS-SETCOMP-001`（label `{"form": "SetComp", "variant": "setcomp-single-for", "host": "function-body", "depth": "d1 单层"}`；匹配依据：form 命中 `SetComp`（该 rule 的求值条目里 17 条是此 form）；该规则共 1556 条 J 求值过）
- **建议新形态**：`form=Set` / `host=assign-rhs` / `depth=d1 单层` / `variant=set-unpack`（form 为新增词表项）
- **修复后状态**：`open`，true=0，原因 predicate_false_at_site；后续工作：`positive_occurrence`
- **探针组**：`G2b-dict-set-unpack`（组内共用 1 条探针）

## 3. 两个特例

1. `RULE-4f466f58c93b`（`Return` @ `core/cfg/ast_converter.py:340`）：需要**类体级别**的 Return 节点，而 CPython 语法不允许类体写 `return`；除非解析器把某函数体误挂到类体，这条不可构造 ⇒ 建议改判 a 类，合并估计里按 0 条探针计。
2. 3 条 c 类（`RULE-6cc7b6a37fd5` SET_ADD、`RULE-b620fe7fb512` LOAD_CLASSDEREF、`RULE-ec53116b4211` List）在口径修复后**已有正发生点**，缺的是「另一条 J 让整条守卫为假」的严格负 witness ⇒ 它们要的是**反例条目**，不是新语法形态。

## 4. 复现

```powershell
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\g4fix\g4_analyze.py
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\g4fix\g4_reports.py
```
