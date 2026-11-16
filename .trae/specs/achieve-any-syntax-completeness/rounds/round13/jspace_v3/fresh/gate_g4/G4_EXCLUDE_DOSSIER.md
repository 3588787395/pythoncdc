# G4 宇宙排除案卷（36 条 a 类）

**状态：排除候选，仅供评审。`fresh/gate_g4/universe_v3.json` 未修改，权威 manifest 未写入任何 proved。**

- 分类来源：`fresh/gate_g4/g4_d3_classification.json`（88 条定性，a=36）
- 本轮重测：`D:\temp\opencode\cl_layout\g4fix\a_evidence.json`（解释器 `D:/Python/python.exe` = 3.11.7）
- 机器可读：`fresh/gate_g4/g4_exclude_candidates.json`

## 0. 判据

规则 `pattern` 里的操作码名 / IR 取值若在 CPython 3.11.7 字节码宇宙里**无法出现**，则任何 J 语料都不可能让它为真 ⇒ 不属于 completeness 分母。三分判据：

| reason_code | 判据 | 条数 |
|---|---|---|
| `opcode_name_absent_from_3_11` | `dis.opmap` 与 `dis._all_opmap` 均无该名字 | 33 |
| `opcode_never_emitted_by_dis` | 名字存在但为填充单元，`dis.get_instructions` 不产出 | 1 |
| `ir_value_has_no_producer` | IR 取值在 core/ 内 0 个生产者（只被消费） | 2 |

分母影响（**未施加**）：344 → **308**。

## 1. 族分布

| 族 | 条数 | 成员 |
|---|---|---|
| INPLACE_* | 12 | `INPLACE_ADD`, `INPLACE_POWER`, `INPLACE_RSHIFT`, `INPLACE_MULTIPLY`, `INPLACE_MODULO`, `INPLACE_AND`, `INPLACE_TRUE_DIVIDE`, `INPLACE_LSHIFT`, `INPLACE_OR`, `INPLACE_FLOOR_DIVIDE`, `INPLACE_SUBTRACT`, `INPLACE_XOR` |
| MATCH_* | 4 | `MATCH_OR`, `MATCH_VALUE`, `MATCH_AS`, `MATCH_MAPPING_KEYS` |
| POP_JUMP_IF_* | 4 | `POP_JUMP_IF_NONE`, `POP_JUMP_IF_TRUE`, `POP_JUMP_IF_FALSE`, `POP_JUMP_IF_NOT_NONE` |
| CALL_* | 3 | `CALL_FUNCTION_KW`, `CALL_METHOD`, `CALL_FUNCTION` |
| JUMP_* | 3 | `JUMP_IF_FALSE`, `JUMP_ABSOLUTE`, `JUMP_IF_TRUE` |
| FORWARD_JUMP_* | 2 | `FORWARD_JUMP_IF_TRUE`, `FORWARD_JUMP_IF_FALSE` |
| single-name | 8 | `GenExpr`, `SETUP_LOOP`, `LOAD_CONSTANT`, `RAISE`, `CACHE`, `__NESTED_FUNC__`, `UNPACK_EXTRACT`, `RETURN_CONST` |

## 2. 36 条逐条

每条：rule_id / anchor / pattern 里的名字 / 不存在证明 / 结论一句。
`after-fix` 是本轮口径修复后的状态：`guard_only` 表示**只有守卫级真值**（同守卫的别的成员满足了它），`symbol_observed=False` 表示该名字本身从未被观测到。

### 2.0 速查表

| rule_id | symbol | anchor | 判据 | after-fix |
|---|---|---|---|---|
| `RULE-014265ded990` | `GenExpr` | `core/cfg/code_generator.py:3788` | ir_value_has_no_producer | `proved`（guard-only） |
| `RULE-086b849c411a` | `CALL_FUNCTION_KW` | `core/cfg/region_ast_generator.py:4557` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-1e9aca2acbea` | `INPLACE_ADD` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-2337ddef1650` | `INPLACE_POWER` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-2397bb5fce28` | `JUMP_IF_FALSE` | `core/cfg/region_ast_generator.py:40616` | opcode_name_absent_from_3_11 | `open`（guard-only） |
| `RULE-262a0b01fd5d` | `INPLACE_RSHIFT` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-2c47b54ee0ba` | `CALL_METHOD` | `core/cfg/ast_generator_v2.py:1512` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-2f8806fa6f9b` | `INPLACE_MULTIPLY` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-3df67251fb10` | `INPLACE_MODULO` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-4cc164c4afcf` | `INPLACE_AND` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-69b3129c2626` | `JUMP_ABSOLUTE` | `core/cfg/ast_generator_v2.py:18526` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-6a468a10f3b9` | `SETUP_LOOP` | `core/cfg/region_analyzer.py:4663` | opcode_name_absent_from_3_11 | `open`（guard-only） |
| `RULE-713e86bfd48b` | `MATCH_OR` | `core/cfg/ast_generator_v2.py:2967` | opcode_name_absent_from_3_11 | `open` |
| `RULE-71f00ab8caf0` | `FORWARD_JUMP_IF_TRUE` | `core/cfg/region_analyzer.py:7160` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-72af8df090f5` | `CALL_FUNCTION` | `core/cfg/ast_generator_v2.py:1512` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-744e7a962f6d` | `LOAD_CONSTANT` | `core/cfg/ast_generator_v2.py:1062` | opcode_name_absent_from_3_11 | `open`（guard-only） |
| `RULE-75006c6546d1` | `RAISE` | `core/cfg/ast_generator_v2.py:2570` | opcode_name_absent_from_3_11 | `open` |
| `RULE-8604910886cb` | `INPLACE_TRUE_DIVIDE` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-87685c80e83d` | `CACHE` | `core/cfg/ast_generator_v2.py:2666` | opcode_never_emitted_by_dis | `proved`（guard-only） |
| `RULE-8a04c17a40dc` | `INPLACE_LSHIFT` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-8e5acd465385` | `INPLACE_OR` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-90db7684358f` | `FORWARD_JUMP_IF_FALSE` | `core/cfg/region_analyzer.py:7160` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-90eafeab8219` | `MATCH_VALUE` | `core/cfg/ast_generator_v2.py:2890` | opcode_name_absent_from_3_11 | `open` |
| `RULE-938087af729e` | `__NESTED_FUNC__` | `core/cfg/code_generator.py:4115` | ir_value_has_no_producer | `open` |
| `RULE-9432988e535a` | `INPLACE_FLOOR_DIVIDE` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-9a035d7e40e7` | `UNPACK_EXTRACT` | `core/cfg/pattern_parser.py:2190` | opcode_name_absent_from_3_11 | `open`（guard-only） |
| `RULE-9d6678631130` | `JUMP_IF_TRUE` | `core/cfg/region_ast_generator.py:40616` | opcode_name_absent_from_3_11 | `open`（guard-only） |
| `RULE-9e2d764f0456` | `RETURN_CONST` | `core/cfg/ast_generator_v2.py:1877` | opcode_name_absent_from_3_11 | `open`（guard-only） |
| `RULE-a6868eb8975c` | `POP_JUMP_IF_NONE` | `core/cfg/pattern_parser.py:748` | opcode_name_absent_from_3_11 | `open`（guard-only） |
| `RULE-bf1c204659ed` | `POP_JUMP_IF_TRUE` | `core/cfg/ast_generator_v2.py:6002` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-c911864da8dd` | `INPLACE_SUBTRACT` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-cb3db139681a` | `POP_JUMP_IF_FALSE` | `core/cfg/ast_generator_v2.py:5243` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-d88c60f60f49` | `INPLACE_XOR` | `core/cfg/region_ast_generator.py:77253` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-db1ffbe2c327` | `MATCH_AS` | `core/cfg/ast_generator_v2.py:2952` | opcode_name_absent_from_3_11 | `open` |
| `RULE-f9489f4c34b4` | `MATCH_MAPPING_KEYS` | `core/cfg/pattern_parser.py:2116` | opcode_name_absent_from_3_11 | `proved`（guard-only） |
| `RULE-f986afd96757` | `POP_JUMP_IF_NOT_NONE` | `core/cfg/pattern_parser.py:740` | opcode_name_absent_from_3_11 | `open`（guard-only） |

### RULE-014265ded990 · `GenExpr` · single-name

- **anchor**：`core/cfg/code_generator.py:3788`；pattern `node_type == 'GenExpr'`（universe kind `opcode_eq`，anchor 级 pattern_class `ast_marker_eq`）
- **修复前实测**：求值 213 次，其中真 0，到达站点运行 11
- **证明（生产者普查）**：`'GenExpr'` 出现 6 处；**生产者 0 处**；消费端（比较）：`core/cfg/code_generator.py:5871 (compare_lhs, function _get_dict_expr_precedence)`；`core/cfg/code_generator.py:6075 (compare_lhs, function _generate_awaitable)`；`core/cfg/code_generator.py:5516 (compare_rhs, function _generate_list_comp)`；`core/cfg/code_generator.py:5578 (compare_rhs, function _generate_list_comp_from_dict)`；`core/cfg/code_generator.py:3788 (compare_rhs, function _generate_expression)`；`core/cfg/code_generator.py:3863 (compare_lhs, function _generate_expression)`
- **after-fix**：status=`proved`，true=1（1/11 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：IR 取值 'GenExpr' 在 core/ 内 0 个生产者（6 处引用全部在比较/消费端），该分支永不成立：这个取值不属于本流水线的 IR 宇宙。

### RULE-086b849c411a · `CALL_FUNCTION_KW` · CALL_*

- **anchor**：`core/cfg/region_ast_generator.py:4557`；pattern `opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX', 'PRECALL')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 406 次，其中真 0，到达站点运行 34
- **证明（live probe）**：`python -c "import dis; print('CALL_FUNCTION_KW' in dis.opmap, 'CALL_FUNCTION_KW' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'CALL_FUNCTION_KW'` 出现 **25** 处（角色分布：assign_rhs 2、call_arg 3、compare_lhs 20）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/comprehension_generator.py:342 (call_arg, function try_generate_comprehension_assign)`；`core/cfg/region_analyzer.py:6356 (compare_lhs, function _identify_loop_regions)`；`core/cfg/region_analyzer.py:15334 (call_arg, function _collect_finally_body_blocks)`；`core/cfg/region_ast_generator.py:18319 (assign_rhs, function _loop_process_natural_back_edge)`；`core/cfg/region_ast_generator.py:56977 (call_arg, class RegionASTGenerator)`；`core/cfg/region_ast_generator.py:4619 (compare_lhs, function _reconstruct_decorator_chain)`
- **同守卫活成员**：`CALL`(proved, true=115)，`CALL_FUNCTION`(open, true=0)，`CALL_METHOD`(open, true=0)，`CALL_FUNCTION_EX`(proved, true=7)，`PRECALL`(proved, true=115)
- **after-fix**：status=`proved`，true=11（11/34 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 CALL_FUNCTION_KW（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（CALL、CALL_FUNCTION_EX、PRECALL）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-1e9aca2acbea · `INPLACE_ADD` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_ADD' in dis.opmap, 'INPLACE_ADD' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_ADD'` 出现 **5** 处（角色分布：call_arg 1、compare_lhs 1、dict_literal 3）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:2997 (dict_literal, function _get_binary_op)`；`core/cfg/ast_generator_v2.py:27641 (dict_literal, function _get_binary_op)`；`core/cfg/pattern_parser.py:251 (call_arg, function _collect_pattern_blocks)`；`core/cfg/region_ast_generator.py:77269 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77253 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_XOR`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_ADD（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-2337ddef1650 · `INPLACE_POWER` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_POWER' in dis.opmap, 'INPLACE_POWER' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_POWER'` 出现 **2** 处（角色分布：compare_lhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:77275 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77256 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_XOR`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_POWER（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-2397bb5fce28 · `JUMP_IF_FALSE` · JUMP_*

- **anchor**：`core/cfg/region_ast_generator.py:40616`；pattern `_instr.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE', 'JUMP_IF_FALSE', 'POP_JUMP_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE', 'JUMP_IF_TRUE', 'POP_JUMP_IF_TRUE')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 171 次，其中真 0，到达站点运行 32
- **证明（live probe）**：`python -c "import dis; print('JUMP_IF_FALSE' in dis.opmap, 'JUMP_IF_FALSE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'JUMP_IF_FALSE'` 出现 **2** 处（角色分布：compare_lhs 2）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:40617 (compare_lhs, function _generate_try)`；`core/cfg/region_ast_generator.py:43230 (compare_lhs, function _generate_handler_body_statements)`
- **同守卫活成员**：`POP_JUMP_FORWARD_IF_FALSE`(proved, true=459)，`POP_JUMP_BACKWARD_IF_FALSE`(proved, true=2)，`POP_JUMP_IF_FALSE`(open, true=0)，`POP_JUMP_FORWARD_IF_TRUE`(proved, true=41)，`POP_JUMP_BACKWARD_IF_TRUE`(proved, true=9)，`JUMP_IF_TRUE`(open, true=0)，`POP_JUMP_IF_TRUE`(open, true=0)
- **after-fix**：status=`open`，true=119（32/32 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 JUMP_IF_FALSE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（POP_JUMP_FORWARD_IF_FALSE、POP_JUMP_BACKWARD_IF_FALSE、POP_JUMP_FORWARD_IF_TRUE、POP_JUMP_BACKWARD_IF_TRUE）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-262a0b01fd5d · `INPLACE_RSHIFT` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_RSHIFT' in dis.opmap, 'INPLACE_RSHIFT' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_RSHIFT'` 出现 **2** 处（角色分布：compare_lhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:77277 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77257 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_XOR`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_RSHIFT（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-2c47b54ee0ba · `CALL_METHOD` · CALL_*

- **anchor**：`core/cfg/ast_generator_v2.py:1512`；pattern `opname in ('CALL_FUNCTION', 'CALL_METHOD')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 21873 次，其中真 0，到达站点运行 131
- **证明（live probe）**：`python -c "import dis; print('CALL_METHOD' in dis.opmap, 'CALL_METHOD' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'CALL_METHOD'` 出现 **66** 处（角色分布：assign_rhs 7、call_arg 8、compare_lhs 50、compare_rhs 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:16404 (compare_lhs, function _extract_pre_condition_statements)`；`core/cfg/ast_generator_v2.py:7388 (compare_lhs, function _generate_block_content_skip_iterator)`；`core/cfg/ast_generator_v2.py:6563 (compare_lhs, function _generate_entry_sequence)`；`core/cfg/ast_generator_v2.py:11417 (compare_lhs, function _generate_if_ast)`；`core/cfg/ast_generator_v2.py:11823 (compare_lhs, function _generate_if_ast)`；`core/cfg/ast_generator_v2.py:16372 (compare_lhs, function _extract_pre_condition_statements)`
- **同守卫活成员**：`CALL_FUNCTION`(open, true=0)
- **after-fix**：status=`proved`，true=47（46/131 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 CALL_METHOD（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（无）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-2f8806fa6f9b · `INPLACE_MULTIPLY` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_MULTIPLY' in dis.opmap, 'INPLACE_MULTIPLY' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_MULTIPLY'` 出现 **5** 处（角色分布：call_arg 1、compare_lhs 1、dict_literal 3）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:2999 (dict_literal, function _get_binary_op)`；`core/cfg/ast_generator_v2.py:27643 (dict_literal, function _get_binary_op)`；`core/cfg/pattern_parser.py:252 (call_arg, function _collect_pattern_blocks)`；`core/cfg/region_ast_generator.py:77271 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77254 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_XOR`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_MULTIPLY（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-3df67251fb10 · `INPLACE_MODULO` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_MODULO' in dis.opmap, 'INPLACE_MODULO' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_MODULO'` 出现 **2** 处（角色分布：compare_lhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:77274 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77255 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_XOR`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_MODULO（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-4cc164c4afcf · `INPLACE_AND` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_AND' in dis.opmap, 'INPLACE_AND' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_AND'` 出现 **2** 处（角色分布：compare_lhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:77278 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77257 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_XOR`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_AND（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-69b3129c2626 · `JUMP_ABSOLUTE` · JUMP_*

- **anchor**：`core/cfg/ast_generator_v2.py:18526`；pattern `instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 30153 次，其中真 0，到达站点运行 131
- **证明（live probe）**：`python -c "import dis; print('JUMP_ABSOLUTE' in dis.opmap, 'JUMP_ABSOLUTE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'JUMP_ABSOLUTE'` 出现 **422** 处（角色分布：assign_rhs 40、call_arg 28、compare_lhs 342、compare_rhs 2、other 10）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:7411 (assign_rhs, function _generate_block_content_skip_iterator)`；`core/cfg/ast_generator_v2.py:22333 (compare_lhs, function _generate_except_handler_block)`；`core/cfg/ast_generator_v2.py:22493 (compare_lhs, function _generate_generic_structure)`；`core/cfg/ast_generator_v2.py:22812 (compare_lhs, function _generate_instructions_content)`；`core/cfg/ast_generator_v2.py:7433 (compare_lhs, function _generate_block_content_skip_iterator)`；`core/cfg/ast_generator_v2.py:27558 (compare_lhs, function _get_unprocessed_blocks)`
- **同守卫活成员**：`JUMP_FORWARD`(proved, true=63)，`JUMP_BACKWARD`(proved, true=29)
- **after-fix**：status=`proved`，true=79（79/131 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 JUMP_ABSOLUTE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（JUMP_FORWARD、JUMP_BACKWARD）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-6a468a10f3b9 · `SETUP_LOOP` · single-name

- **anchor**：`core/cfg/region_analyzer.py:4663`；pattern `instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE', 'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP', 'FOR_ITER', 'SETUP_LOOP', 'GET_ITER', 'GET_AITER')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 257 次，其中真 0，到达站点运行 9
- **证明（live probe）**：`python -c "import dis; print('SETUP_LOOP' in dis.opmap, 'SETUP_LOOP' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'SETUP_LOOP'` 出现 **2** 处（角色分布：call_arg 1、compare_lhs 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/opcode_feature_detector.py:179 (call_arg, function _init_opcode_sets)`；`core/cfg/region_analyzer.py:4668 (compare_lhs, function identify_block_prefix_instructions)`
- **同守卫活成员**：`JUMP_FORWARD`(proved, true=63)，`JUMP_BACKWARD`(proved, true=29)，`JUMP_ABSOLUTE`(open, true=0)，`POP_JUMP_FORWARD_IF_FALSE`(proved, true=459)，`POP_JUMP_FORWARD_IF_TRUE`(proved, true=41)，`POP_JUMP_BACKWARD_IF_FALSE`(proved, true=2)，`POP_JUMP_BACKWARD_IF_TRUE`(proved, true=9)，`POP_JUMP_IF_FALSE`(open, true=0)，`POP_JUMP_IF_TRUE`(open, true=0)，`JUMP_IF_TRUE_OR_POP`(proved, true=8)，`JUMP_IF_FALSE_OR_POP`(proved, true=3)，`FOR_ITER`(proved, true=77)，`GET_ITER`(proved, true=77)，`GET_AITER`(proved, true=9)
- **after-fix**：status=`open`，true=10（9/9 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 SETUP_LOOP（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（JUMP_FORWARD、JUMP_BACKWARD、POP_JUMP_FORWARD_IF_FALSE、POP_JUMP_FORWARD_IF_TRUE、POP_JUMP_BACKWARD_IF_FALSE、POP_JUMP_BACKWARD_IF_TRUE、JUMP_IF_TRUE_OR_POP、JUMP_IF_FALSE_OR_POP、FOR_ITER、GET_ITER、GET_AITER）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-713e86bfd48b · `MATCH_OR` · MATCH_*

- **anchor**：`core/cfg/ast_generator_v2.py:2967`；pattern `opname == 'MATCH_OR'`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_eq`）
- **修复前实测**：求值 1584 次，其中真 0，到达站点运行 96
- **证明（live probe）**：`python -c "import dis; print('MATCH_OR' in dis.opmap, 'MATCH_OR' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'MATCH_OR'` 出现 **2** 处（角色分布：compare_rhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/astree.py:120 (dict_literal, function type_str)`；`core/cfg/ast_generator_v2.py:2967 (compare_rhs, function _process_instruction)`
- **after-fix**：status=`open`，true=0（0/96 运行），`guard_only=False`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 MATCH_OR（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（无）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-71f00ab8caf0 · `FORWARD_JUMP_IF_TRUE` · FORWARD_JUMP_*

- **anchor**：`core/cfg/region_analyzer.py:7160`；pattern `i.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE', 'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP', 'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE', 'FORWARD_JUMP_IF_TRUE', 'FORWARD_JUMP_IF_FALSE')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 979 次，其中真 0，到达站点运行 36
- **证明（live probe）**：`python -c "import dis; print('FORWARD_JUMP_IF_TRUE' in dis.opmap, 'FORWARD_JUMP_IF_TRUE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'FORWARD_JUMP_IF_TRUE'` 出现 **1** 处（角色分布：compare_lhs 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_analyzer.py:7165 (compare_lhs, function _is_while_true)`
- **同守卫活成员**：`POP_JUMP_FORWARD_IF_TRUE`(proved, true=41)，`POP_JUMP_FORWARD_IF_FALSE`(proved, true=459)，`POP_JUMP_BACKWARD_IF_TRUE`(proved, true=9)，`POP_JUMP_BACKWARD_IF_FALSE`(proved, true=2)，`JUMP_IF_TRUE_OR_POP`(proved, true=8)，`JUMP_IF_FALSE_OR_POP`(proved, true=3)，`POP_JUMP_FORWARD_IF_NONE`(proved, true=21)，`POP_JUMP_FORWARD_IF_NOT_NONE`(proved, true=13)，`POP_JUMP_BACKWARD_IF_NONE`(open, true=0)，`POP_JUMP_BACKWARD_IF_NOT_NONE`(open, true=0)，`FORWARD_JUMP_IF_FALSE`(open, true=0)
- **after-fix**：status=`proved`，true=28（28/36 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 FORWARD_JUMP_IF_TRUE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（POP_JUMP_FORWARD_IF_TRUE、POP_JUMP_FORWARD_IF_FALSE、POP_JUMP_BACKWARD_IF_TRUE、POP_JUMP_BACKWARD_IF_FALSE、JUMP_IF_TRUE_OR_POP、JUMP_IF_FALSE_OR_POP、POP_JUMP_FORWARD_IF_NONE、POP_JUMP_FORWARD_IF_NOT_NONE）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-72af8df090f5 · `CALL_FUNCTION` · CALL_*

- **anchor**：`core/cfg/ast_generator_v2.py:1512`；pattern `opname in ('CALL_FUNCTION', 'CALL_METHOD')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 18399 次，其中真 0，到达站点运行 131
- **证明（live probe）**：`python -c "import dis; print('CALL_FUNCTION' in dis.opmap, 'CALL_FUNCTION' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'CALL_FUNCTION'` 出现 **77** 处（角色分布：assign_rhs 7、call_arg 9、compare_lhs 61）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:16404 (compare_lhs, function _extract_pre_condition_statements)`；`core/cfg/ast_generator_v2.py:7387 (compare_lhs, function _generate_block_content_skip_iterator)`；`core/cfg/ast_generator_v2.py:22031 (compare_lhs, function _generate_except_handler_block)`；`core/cfg/ast_generator_v2.py:22068 (compare_lhs, function _generate_except_handler_block)`；`core/cfg/ast_generator_v2.py:6563 (compare_lhs, function _generate_entry_sequence)`；`core/cfg/ast_generator_v2.py:10711 (compare_lhs, function _generate_if_ast)`
- **同守卫活成员**：`CALL_METHOD`(open, true=0)
- **after-fix**：status=`proved`，true=47（46/131 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 CALL_FUNCTION（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（无）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-744e7a962f6d · `LOAD_CONSTANT` · single-name

- **anchor**：`core/cfg/ast_generator_v2.py:1062`；pattern `opname in ('LOAD_CONST', 'LOAD_CONSTANT')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 49826 次，其中真 0，到达站点运行 131
- **证明（live probe）**：`python -c "import dis; print('LOAD_CONSTANT' in dis.opmap, 'LOAD_CONSTANT' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'LOAD_CONSTANT'` 出现 **6** 处（角色分布：compare_lhs 6）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:1062 (compare_lhs, function _process_instruction)`；`core/cfg/ast_generator_v2.py:3179 (compare_lhs, function _load_instr_to_ast)`；`core/cfg/ast_generator_v2.py:7780 (compare_lhs, function _generate_block_content_skip_iterator)`；`core/cfg/ast_generator_v2.py:24504 (compare_lhs, function _process_instruction_sequence)`；`core/cfg/ast_generator_v2.py:24593 (compare_lhs, function _process_instruction_sequence)`；`core/cfg/ast_generator_v2.py:15433 (compare_lhs, function _generate_yield_from_ast)`
- **同守卫活成员**：`LOAD_CONST`(open, true=213)
- **after-fix**：status=`open`，true=190（131/131 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 LOAD_CONSTANT（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（无）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-75006c6546d1 · `RAISE` · single-name

- **anchor**：`core/cfg/ast_generator_v2.py:2570`；pattern `opname == 'RAISE'`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_eq`）
- **修复前实测**：求值 3473 次，其中真 0，到达站点运行 130
- **证明（live probe）**：`python -c "import dis; print('RAISE' in dis.opmap, 'RAISE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'RAISE'` 出现 **6** 处（角色分布：assign_rhs 5、compare_rhs 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:2570 (compare_rhs, function _process_instruction)`；`core/cfg/cfg_builder.py:100 (assign_rhs, class CFGBuilder)`；`core/cfg/region_ast_generator.py:53577 (assign_rhs, function _v105_try_kwarg_chain_continuation)`；`core/cfg/region_ast_generator.py:53801 (assign_rhs, function _v168_try_boolop_expr_group_tail)`；`core/cfg/region_ast_generator.py:26177 (assign_rhs, function _r2189_fold_window_guards)`；`core/cfg/region_ast_generator.py:55633 (assign_rhs, function _generate_boolop_impl)`
- **after-fix**：status=`open`，true=0（0/130 运行），`guard_only=False`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 RAISE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（无）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-8604910886cb · `INPLACE_TRUE_DIVIDE` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_TRUE_DIVIDE' in dis.opmap, 'INPLACE_TRUE_DIVIDE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_TRUE_DIVIDE'` 出现 **2** 处（角色分布：compare_lhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:77272 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77254 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_XOR`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_TRUE_DIVIDE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-87685c80e83d · `CACHE` · single-name

- **anchor**：`core/cfg/ast_generator_v2.py:2666`；pattern `opname == 'CACHE'`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_eq`）
- **修复前实测**：求值 72749 次，其中真 0，到达站点运行 131
- **证明（live probe）**：`python -c "import dis; print('CACHE' in dis.opmap, 'CACHE' in dis._all_opmap)"` ⇒ `dis.opmap=True`、`_all_opmap=True`
- **证明（dis 不产出）**：probe `def _probe(): return g   (a global load forces CACHE cells)`：raw co_code 指令名 ['CACHE', 'LOAD_GLOBAL', 'RESUME', 'RETURN_VALUE']；`dis.get_instructions` ['LOAD_GLOBAL', 'RESUME', 'RETURN_VALUE'] ⇒ `cache_in_raw=True` / `cache_emitted=False`；指令流来源 `core/cfg/cfg_builder.py:136`
- **证明（core/ 引用普查）**：`'CACHE'` 出现 **977** 处（角色分布：assign_rhs 59、call_arg 32、compare_lhs 883、compare_rhs 2、other 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:830 (compare_lhs, function _process_instruction)`；`core/cfg/ast_generator_v2.py:7451 (compare_lhs, function _generate_block_content_skip_iterator)`；`core/cfg/ast_generator_v2.py:16509 (compare_lhs, function _generate_init_block_content)`；`core/cfg/ast_generator_v2.py:21114 (compare_lhs, function _generate_pre_inner_with_code)`；`core/cfg/ast_generator_v2.py:21676 (compare_lhs, function _parse_resource_expr_from_instructions)`；`core/cfg/ast_generator_v2.py:23062 (compare_lhs, function _is_orphan_nop_statement)`
- **after-fix**：status=`proved`，true=130（130/131 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：CACHE 是填充单元：raw co_code 里存在、dis.get_instructions 从不产出；CDC 的指令流来自 dis.get_instructions（core/cfg/cfg_builder.py:136），该分支结构上不可达。

### RULE-8a04c17a40dc · `INPLACE_LSHIFT` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_LSHIFT' in dis.opmap, 'INPLACE_LSHIFT' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_LSHIFT'` 出现 **2** 处（角色分布：compare_lhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:77276 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77256 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_XOR`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_LSHIFT（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-8e5acd465385 · `INPLACE_OR` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_OR' in dis.opmap, 'INPLACE_OR' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_OR'` 出现 **2** 处（角色分布：compare_lhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:77280 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77258 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_XOR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_OR（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-90db7684358f · `FORWARD_JUMP_IF_FALSE` · FORWARD_JUMP_*

- **anchor**：`core/cfg/region_analyzer.py:7160`；pattern `i.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE', 'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP', 'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE', 'FORWARD_JUMP_IF_TRUE', 'FORWARD_JUMP_IF_FALSE')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 979 次，其中真 0，到达站点运行 36
- **证明（live probe）**：`python -c "import dis; print('FORWARD_JUMP_IF_FALSE' in dis.opmap, 'FORWARD_JUMP_IF_FALSE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'FORWARD_JUMP_IF_FALSE'` 出现 **1** 处（角色分布：compare_lhs 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_analyzer.py:7165 (compare_lhs, function _is_while_true)`
- **同守卫活成员**：`POP_JUMP_FORWARD_IF_TRUE`(proved, true=41)，`POP_JUMP_FORWARD_IF_FALSE`(proved, true=459)，`POP_JUMP_BACKWARD_IF_TRUE`(proved, true=9)，`POP_JUMP_BACKWARD_IF_FALSE`(proved, true=2)，`JUMP_IF_TRUE_OR_POP`(proved, true=8)，`JUMP_IF_FALSE_OR_POP`(proved, true=3)，`POP_JUMP_FORWARD_IF_NONE`(proved, true=21)，`POP_JUMP_FORWARD_IF_NOT_NONE`(proved, true=13)，`POP_JUMP_BACKWARD_IF_NONE`(open, true=0)，`POP_JUMP_BACKWARD_IF_NOT_NONE`(open, true=0)，`FORWARD_JUMP_IF_TRUE`(open, true=0)
- **after-fix**：status=`proved`，true=28（28/36 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 FORWARD_JUMP_IF_FALSE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（POP_JUMP_FORWARD_IF_TRUE、POP_JUMP_FORWARD_IF_FALSE、POP_JUMP_BACKWARD_IF_TRUE、POP_JUMP_BACKWARD_IF_FALSE、JUMP_IF_TRUE_OR_POP、JUMP_IF_FALSE_OR_POP、POP_JUMP_FORWARD_IF_NONE、POP_JUMP_FORWARD_IF_NOT_NONE）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-90eafeab8219 · `MATCH_VALUE` · MATCH_*

- **anchor**：`core/cfg/ast_generator_v2.py:2890`；pattern `opname == 'MATCH_VALUE'`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_eq`）
- **修复前实测**：求值 1584 次，其中真 0，到达站点运行 96
- **证明（live probe）**：`python -c "import dis; print('MATCH_VALUE' in dis.opmap, 'MATCH_VALUE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'MATCH_VALUE'` 出现 **2** 处（角色分布：compare_rhs 2）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:2890 (compare_rhs, function _process_instruction)`；`core/cfg/structured_analyzer.py:15755 (compare_rhs, function _extract_match_pattern)`
- **after-fix**：status=`open`，true=0（0/96 运行），`guard_only=False`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 MATCH_VALUE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（无）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-938087af729e · `__NESTED_FUNC__` · single-name

- **anchor**：`core/cfg/code_generator.py:4115`；pattern `name == '__NESTED_FUNC__'`（universe kind `opcode_eq`，anchor 级 pattern_class `ast_marker_eq`）
- **修复前实测**：求值 14871 次，其中真 0，到达站点运行 131
- **证明（生产者普查）**：`'__NESTED_FUNC__'` 出现 1 处；**生产者 0 处**；消费端（比较）：`core/cfg/code_generator.py:4115 (compare_rhs, function _generate_expression)`
- **after-fix**：status=`open`，true=0（0/131 运行），`guard_only=False`，`symbol_observed=False`
- **结论**：IR 取值 '__NESTED_FUNC__' 在 core/ 内 0 个生产者（1 处引用全部在比较/消费端），该分支永不成立：这个取值不属于本流水线的 IR 宇宙。

### RULE-9432988e535a · `INPLACE_FLOOR_DIVIDE` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_FLOOR_DIVIDE' in dis.opmap, 'INPLACE_FLOOR_DIVIDE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_FLOOR_DIVIDE'` 出现 **2** 处（角色分布：compare_lhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:77273 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77255 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_XOR`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_FLOOR_DIVIDE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-9a035d7e40e7 · `UNPACK_EXTRACT` · single-name

- **anchor**：`core/cfg/pattern_parser.py:2190`；pattern `instr.opname in ('MATCH_SEQUENCE', 'MATCH_CLASS', 'MATCH_MAPPING', 'MATCH_KEYS', 'MATCH_MAPPING_KEYS', 'GET_LEN', 'UNPACK_SEQUENCE', 'UNPACK_EX', 'UNPACK_EXTRACT', 'COMPARE_OP', 'IS_OP')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 283 次，其中真 0，到达站点运行 11
- **证明（live probe）**：`python -c "import dis; print('UNPACK_EXTRACT' in dis.opmap, 'UNPACK_EXTRACT' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'UNPACK_EXTRACT'` 出现 **11** 处（角色分布：assign_rhs 5、call_arg 4、compare_lhs 2）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/pattern_parser.py:1306 (assign_rhs, function _is_pattern_continuation_block)`；`core/cfg/pattern_parser.py:2012 (assign_rhs, function _is_pattern_block_for_as)`；`core/cfg/pattern_parser.py:130 (call_arg, function _collect_pattern_blocks)`；`core/cfg/pattern_parser.py:500 (assign_rhs, function _extract_case_guard_from_blocks)`；`core/cfg/pattern_parser.py:1753 (call_arg, function _extract_capture_head_store)`；`core/cfg/pattern_parser.py:2193 (compare_lhs, function _extract_sequence_pattern)`
- **同守卫活成员**：`MATCH_SEQUENCE`(proved, true=13)，`MATCH_CLASS`(proved, true=12)，`MATCH_MAPPING`(open, true=0)，`MATCH_KEYS`(open, true=0)，`MATCH_MAPPING_KEYS`(open, true=0)，`GET_LEN`(open, true=11)，`UNPACK_SEQUENCE`(proved, true=31)，`UNPACK_EX`(proved, true=4)，`COMPARE_OP`(proved, true=69)，`IS_OP`(proved, true=5)
- **after-fix**：status=`open`，true=11（11/11 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 UNPACK_EXTRACT（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（MATCH_SEQUENCE、MATCH_CLASS、UNPACK_SEQUENCE、UNPACK_EX、COMPARE_OP、IS_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-9d6678631130 · `JUMP_IF_TRUE` · JUMP_*

- **anchor**：`core/cfg/region_ast_generator.py:40616`；pattern `_instr.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE', 'JUMP_IF_FALSE', 'POP_JUMP_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE', 'JUMP_IF_TRUE', 'POP_JUMP_IF_TRUE')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 171 次，其中真 0，到达站点运行 32
- **证明（live probe）**：`python -c "import dis; print('JUMP_IF_TRUE' in dis.opmap, 'JUMP_IF_TRUE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'JUMP_IF_TRUE'` 出现 **2** 处（角色分布：compare_lhs 2）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:40619 (compare_lhs, function _generate_try)`；`core/cfg/region_ast_generator.py:43230 (compare_lhs, function _generate_handler_body_statements)`
- **同守卫活成员**：`POP_JUMP_FORWARD_IF_FALSE`(proved, true=459)，`POP_JUMP_BACKWARD_IF_FALSE`(proved, true=2)，`JUMP_IF_FALSE`(open, true=0)，`POP_JUMP_IF_FALSE`(open, true=0)，`POP_JUMP_FORWARD_IF_TRUE`(proved, true=41)，`POP_JUMP_BACKWARD_IF_TRUE`(proved, true=9)，`POP_JUMP_IF_TRUE`(open, true=0)
- **after-fix**：status=`open`，true=119（32/32 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 JUMP_IF_TRUE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（POP_JUMP_FORWARD_IF_FALSE、POP_JUMP_BACKWARD_IF_FALSE、POP_JUMP_FORWARD_IF_TRUE、POP_JUMP_BACKWARD_IF_TRUE）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-9e2d764f0456 · `RETURN_CONST` · single-name

- **anchor**：`core/cfg/ast_generator_v2.py:1877`；pattern `opname in ('RETURN_VALUE', 'RETURN_CONST')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 59342 次，其中真 0，到达站点运行 131
- **证明（live probe）**：`python -c "import dis; print('RETURN_CONST' in dis.opmap, 'RETURN_CONST' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'RETURN_CONST'` 出现 **570** 处（角色分布：assign_rhs 32、call_arg 26、compare_lhs 450、compare_rhs 59、other 3）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:23075 (assign_rhs, function _is_orphan_nop_statement)`；`core/cfg/ast_generator_v2.py:14342 (compare_lhs, function _detect_compound_condition_assignment)`；`core/cfg/ast_generator_v2.py:15119 (compare_lhs, function _detect_conditional_expression)`；`core/cfg/ast_generator_v2.py:15122 (compare_rhs, function _detect_conditional_expression)`；`core/cfg/ast_generator_v2.py:22449 (compare_lhs, function _generate_generic_structure)`；`core/cfg/ast_generator_v2.py:15267 (compare_lhs, function _generate_dict_with_ifexp)`
- **同守卫活成员**：`RETURN_VALUE`(open, true=255)
- **after-fix**：status=`open`，true=131（131/131 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 RETURN_CONST（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（无）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-a6868eb8975c · `POP_JUMP_IF_NONE` · POP_JUMP_IF_*

- **anchor**：`core/cfg/pattern_parser.py:748`；pattern `_arm_jmp.opname in ('POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1418 次，其中真 0，到达站点运行 51
- **证明（live probe）**：`python -c "import dis; print('POP_JUMP_IF_NONE' in dis.opmap, 'POP_JUMP_IF_NONE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'POP_JUMP_IF_NONE'` 出现 **28** 处（角色分布：assign_rhs 9、call_arg 9、compare_lhs 10）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/comprehension_generator.py:5958 (assign_rhs, function _b261_element_value)`；`core/cfg/comprehension_generator.py:6010 (assign_rhs, function _b261_dict_kv)`；`core/cfg/comprehension_generator.py:6203 (assign_rhs, function _b271_dict_comp_kv)`；`core/cfg/dominator_analyzer.py:31 (call_arg, module-level)`；`core/cfg/patch_detector.py:136 (call_arg, module-level)`；`core/cfg/pattern_parser.py:28 (assign_rhs, class PatternParser)`
- **同守卫活成员**：`POP_JUMP_FORWARD_IF_NONE`(proved, true=21)
- **after-fix**：status=`open`，true=200（51/51 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 POP_JUMP_IF_NONE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（POP_JUMP_FORWARD_IF_NONE）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-bf1c204659ed · `POP_JUMP_IF_TRUE` · POP_JUMP_IF_*

- **anchor**：`core/cfg/ast_generator_v2.py:6002`；pattern `instr.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 3682 次，其中真 0，到达站点运行 111
- **证明（live probe）**：`python -c "import dis; print('POP_JUMP_IF_TRUE' in dis.opmap, 'POP_JUMP_IF_TRUE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'POP_JUMP_IF_TRUE'` 出现 **101** 处（角色分布：assign_rhs 22、call_arg 13、compare_lhs 62、other 4）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:7408 (assign_rhs, function _generate_block_content_skip_iterator)`；`core/cfg/ast_generator_v2.py:9396 (compare_lhs, function _is_not_condition)`；`core/cfg/ast_generator_v2.py:10295 (compare_lhs, function _generate_if_ast)`；`core/cfg/ast_generator_v2.py:16330 (compare_lhs, function _extract_pre_condition_statements)`；`core/cfg/ast_generator_v2.py:16515 (compare_lhs, function _generate_init_block_content)`；`core/cfg/ast_generator_v2.py:18156 (compare_lhs, function _generate_while_body_from_header)`
- **同守卫活成员**：`POP_JUMP_BACKWARD_IF_TRUE`(proved, true=9)，`POP_JUMP_BACKWARD_IF_FALSE`(proved, true=2)，`POP_JUMP_FORWARD_IF_TRUE`(proved, true=41)，`POP_JUMP_FORWARD_IF_FALSE`(proved, true=459)，`POP_JUMP_IF_FALSE`(open, true=0)
- **after-fix**：status=`proved`，true=51（45/111 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 POP_JUMP_IF_TRUE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（POP_JUMP_BACKWARD_IF_TRUE、POP_JUMP_BACKWARD_IF_FALSE、POP_JUMP_FORWARD_IF_TRUE、POP_JUMP_FORWARD_IF_FALSE）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-c911864da8dd · `INPLACE_SUBTRACT` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_SUBTRACT' in dis.opmap, 'INPLACE_SUBTRACT' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_SUBTRACT'` 出现 **5** 处（角色分布：call_arg 1、compare_lhs 1、dict_literal 3）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/ast_generator_v2.py:2998 (dict_literal, function _get_binary_op)`；`core/cfg/ast_generator_v2.py:27642 (dict_literal, function _get_binary_op)`；`core/cfg/pattern_parser.py:251 (call_arg, function _collect_pattern_blocks)`；`core/cfg/region_ast_generator.py:77270 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77253 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_XOR`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_SUBTRACT（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-cb3db139681a · `POP_JUMP_IF_FALSE` · POP_JUMP_IF_*

- **anchor**：`core/cfg/ast_generator_v2.py:5243`；pattern `instructions[j].opname in ('POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_IF_FALSE')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 5246 次，其中真 0，到达站点运行 112
- **证明（live probe）**：`python -c "import dis; print('POP_JUMP_IF_FALSE' in dis.opmap, 'POP_JUMP_IF_FALSE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'POP_JUMP_IF_FALSE'` 出现 **120** 处（角色分布：assign_rhs 24、call_arg 13、compare_lhs 79、other 4）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/bytecode_matcher.py:45 (assign_rhs, class BytecodeMatcher)`；`core/bytecode_matcher.py:45 (assign_rhs, class BytecodeMatcher)`；`core/bytecode_matcher.py:45 (assign_rhs, class BytecodeMatcher)`；`core/cfg/ast_generator_v2.py:7408 (assign_rhs, function _generate_block_content_skip_iterator)`；`core/cfg/ast_generator_v2.py:5305 (compare_lhs, function _extract_comprehension_ifs)`；`core/cfg/ast_generator_v2.py:9396 (compare_lhs, function _is_not_condition)`
- **同守卫活成员**：`POP_JUMP_BACKWARD_IF_FALSE`(proved, true=2)
- **after-fix**：status=`proved`，true=712（107/112 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 POP_JUMP_IF_FALSE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（POP_JUMP_BACKWARD_IF_FALSE）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-d88c60f60f49 · `INPLACE_XOR` · INPLACE_*

- **anchor**：`core/cfg/region_ast_generator.py:77253`；pattern `instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1936 次，其中真 0，到达站点运行 13
- **证明（live probe）**：`python -c "import dis; print('INPLACE_XOR' in dis.opmap, 'INPLACE_XOR' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'INPLACE_XOR'` 出现 **2** 处（角色分布：compare_lhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/region_ast_generator.py:77279 (dict_literal, function _build_subscript_assign)`；`core/cfg/region_ast_generator.py:77258 (compare_lhs, function _build_subscript_assign)`
- **同守卫活成员**：`BINARY_OP`(proved, true=85)，`INPLACE_ADD`(open, true=0)，`INPLACE_SUBTRACT`(open, true=0)，`INPLACE_MULTIPLY`(open, true=0)，`INPLACE_TRUE_DIVIDE`(open, true=0)，`INPLACE_FLOOR_DIVIDE`(open, true=0)，`INPLACE_MODULO`(open, true=0)，`INPLACE_POWER`(open, true=0)，`INPLACE_LSHIFT`(open, true=0)，`INPLACE_RSHIFT`(open, true=0)，`INPLACE_AND`(open, true=0)，`INPLACE_OR`(open, true=0)
- **after-fix**：status=`proved`，true=6（6/13 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 INPLACE_XOR（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（BINARY_OP）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-db1ffbe2c327 · `MATCH_AS` · MATCH_*

- **anchor**：`core/cfg/ast_generator_v2.py:2952`；pattern `opname == 'MATCH_AS'`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_eq`）
- **修复前实测**：求值 1584 次，其中真 0，到达站点运行 96
- **证明（live probe）**：`python -c "import dis; print('MATCH_AS' in dis.opmap, 'MATCH_AS' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'MATCH_AS'` 出现 **2** 处（角色分布：compare_rhs 1、dict_literal 1）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/astree.py:119 (dict_literal, function type_str)`；`core/cfg/ast_generator_v2.py:2952 (compare_rhs, function _process_instruction)`
- **after-fix**：status=`open`，true=0（0/96 运行），`guard_only=False`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 MATCH_AS（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（无）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-f9489f4c34b4 · `MATCH_MAPPING_KEYS` · MATCH_*

- **anchor**：`core/cfg/pattern_parser.py:2116`；pattern `instr.opname in ('MATCH_KEYS', 'MATCH_MAPPING_KEYS', 'UNPACK_SEQUENCE')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 285 次，其中真 0，到达站点运行 12
- **证明（live probe）**：`python -c "import dis; print('MATCH_MAPPING_KEYS' in dis.opmap, 'MATCH_MAPPING_KEYS' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'MATCH_MAPPING_KEYS'` 出现 **29** 处（角色分布：assign_rhs 9、call_arg 10、compare_lhs 10）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/patch_detector.py:144 (call_arg, module-level)`；`core/cfg/pattern_parser.py:23 (assign_rhs, class PatternParser)`；`core/cfg/pattern_parser.py:46 (assign_rhs, class PatternParser)`；`core/cfg/pattern_parser.py:1117 (assign_rhs, function _find_real_match_header)`；`core/cfg/pattern_parser.py:1307 (assign_rhs, function _is_pattern_continuation_block)`；`core/cfg/pattern_parser.py:2013 (assign_rhs, function _is_pattern_block_for_as)`
- **同守卫活成员**：`MATCH_KEYS`(open, true=0)，`UNPACK_SEQUENCE`(proved, true=31)
- **after-fix**：status=`proved`，true=11（11/12 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 MATCH_MAPPING_KEYS（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（UNPACK_SEQUENCE）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

### RULE-f986afd96757 · `POP_JUMP_IF_NOT_NONE` · POP_JUMP_IF_*

- **anchor**：`core/cfg/pattern_parser.py:740`；pattern `_arm_jmp.opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE')`（universe kind `opcode_eq`，anchor 级 pattern_class `opcode_in_set`）
- **修复前实测**：求值 1480 次，其中真 0，到达站点运行 51
- **证明（live probe）**：`python -c "import dis; print('POP_JUMP_IF_NOT_NONE' in dis.opmap, 'POP_JUMP_IF_NOT_NONE' in dis._all_opmap)"` ⇒ `dis.opmap=False`、`_all_opmap=False`
- **证明（core/ 引用普查）**：`'POP_JUMP_IF_NOT_NONE'` 出现 **32** 处（角色分布：assign_rhs 9、call_arg 8、compare_lhs 15）——全部是**按名字查表/比较**的消费端（兼容名单、opname→符号映射表），不存在把它当作可产出指令名的路径；样例：`core/cfg/comprehension_generator.py:5958 (assign_rhs, function _b261_element_value)`；`core/cfg/comprehension_generator.py:6010 (assign_rhs, function _b261_dict_kv)`；`core/cfg/comprehension_generator.py:6203 (assign_rhs, function _b271_dict_comp_kv)`；`core/cfg/dominator_analyzer.py:31 (call_arg, module-level)`；`core/cfg/patch_detector.py:136 (call_arg, module-level)`；`core/cfg/pattern_parser.py:29 (assign_rhs, class PatternParser)`
- **同守卫活成员**：`POP_JUMP_FORWARD_IF_NOT_NONE`(proved, true=13)
- **after-fix**：status=`open`，true=195（51/51 运行），`guard_only=True`，`symbol_observed=False`
- **结论**：3.11.7 的 dis.opmap 与 dis._all_opmap 都没有 POP_JUMP_IF_NOT_NONE（连内部/specialized 名都不是），该名字不可能出现在 J 的指令流里；同守卫的活成员（POP_JUMP_FORWARD_IF_NOT_NONE）已被实测命中，说明该行是跨版本兼容写法，错在把兼容名建成了 3.11 规则。

## 3. 评审要点

1. 三族：33 个名字在 3.11 完全不存在（连 `dis._all_opmap` 的内部名都没有）、1 个 CACHE 填充单元、2 个 IR 取值无生产者。判据是**取值域**，与 J 语料无关。
2. 源码行本身不陈旧：`INPLACE_*`、`CALL_FUNCTION`、`POP_JUMP_IF_*` 都是跨版本兼容写法（同一守卫里还有 3.11 的活名字）；陈旧的是「把兼容名建成 3.11 规则」。
3. 口径修复（guard scope）后这 36 条里有 23 条变成 `proved`（其中 23 条是 `guard_only`：真值由同守卫的**别的成员**满足）；只看守卫级的共 31 条；这 36 条里 `symbol_observed=True` 的 **0** 条 —— 被排除的名字一次都没有被观测到。这正是排除案卷要提供的反证。
4. 建议只在评审通过后从 universe 移除（或用 `legacy_name`/`dead_branch` 标记后不计入分母）；本文件不施加任何改动。

## 4. 复现

```powershell
# 单条名字活性
D:/Python/python.exe -X utf8 -c "import dis; print('MATCH_AS' in dis.opmap, 'MATCH_AS' in dis._all_opmap)"
# 全量证据（probe + core/ 引用普查 + 上下文）
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\g4fix\g4_analyze.py
```
