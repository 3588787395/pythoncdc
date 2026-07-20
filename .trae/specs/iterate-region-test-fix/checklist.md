# 迭代区域测试修复 验证清单

## Ternary 区域 Round 01 验证

- [x] P0 Bug 7: ternary 作为 compare 左操作数 — `_detect_ternary_pattern` 的 `_net_stack == 1` COMPARE_OP 分支新增 STORE_* 检测，避免误设 `merge_context='compare'`
  - 验证：`tests/exhaustive/ternary/test_r1_ternary_in_compare.py` 通过
  - 源码：`x = (a if a > 0 else 0) == b`

- [x] P0 Bug 8: ternary 作为方法调用参数 — `_detect_ternary_context` 新增 LOAD_METHOD 模式识别（无 PUSH_NULL 的 `obj.method(args)` 调用）
  - 验证：`tests/exhaustive/ternary/test_r1_ternary_in_method_call.py` 通过
  - 源码：`obj.method(a if a > 0 else 0)`

- [x] P0 Bug 9: ternary 在 starred 表达式中 — 三处协同修复：
  - `region_ast_generator.py` preload 新增 BUILD_LIST/TUPLE/SET/MAP/CONST_KEY_MAP 处理
  - `region_ast_generator.py` `has_ops` 新增 LIST_EXTEND/DICT_UPDATE/SET_UPDATE/LIST_APPEND/MAP_ADD
  - `ast_generator_v2.py` LIST_EXTEND 新增对 IfExp/BoolOp 等复合表达式的 Starred 包装
  - `code_generator.py` Starred 渲染对低优先级复合表达式加括号
  - 验证：`tests/exhaustive/ternary/test_r1_ternary_in_starred.py` 通过
  - 源码：`x = [*(items if cond else [])]`

- [x] P0 Bug 1: walrus 在 ternary body 中 — `_is_single_expression_block` 新增 walrus `COPY N / STORE_*` 副作用剥离
  - 验证：`tests/exhaustive/ternary/test_r1_walrus_in_body.py` 通过
  - 源码：`x = (y := a) if a > 0 else 0`

- [x] P0 Bug 2: walrus 在 ternary orelse 中 — 同 Bug 1 修复（共用 walrus 剥离逻辑）
  - 验证：`tests/exhaustive/ternary/test_r1_walrus_in_orelse.py` 通过
  - 源码：`x = a if cond else (y := b)`

- [x] 全量回归无退化 — Ternary 区域：60 failed → 55 failed（减 5）；72 passed → 77 passed（增 5）；1 skipped 不变
- [x] 跨区域回归无退化 — ternary + if_region + control_flow_matrix：107 failed → 102 failed（减 5）；1169 passed → 1174 passed（增 5）；22 skipped 不变
- [x] 修复依归约算法 4 原则 — 所有修复均通过「嵌套即抽象节点」「每块唯一归属」原则论证，无跨区域启发式特例
- [x] 修复报告已写 — `rounds/ternary_region/round_01/fix_report.md`

## 已知限制（未修复 bug）

- [ ] Bug 3, 4 (R2): `assert(ternary)` 折叠为 BoolOp — 经验证 Python 3.11.15 中 `assert (a if a > 0 else 0)` 与 `assert (a > 0 and a)` 字节码完全等价，属根本性歧义，不可修复
- [ ] Bug 5 (R3): chained compare 在 ternary 条件中 — chained_compare IfRegion 优先级高于 TernaryRegion，需边界调整
- [ ] Bug 6 (R4): ternary 在切片下标中 — 双 ternary 喂 BUILD_SLICE 2 / BINARY_SUBSCR
- [ ] Bug 10, 13, 15, 16, 17 (R5): 嵌套 code object 内 ternary 重组错误
- [ ] Bug 11 (R4): 多个 ternary 作为 dict value — BUILD_CONST_KEY_MAP 重组
- [ ] Bug 12 (R6): lambda body 含复合 ternary 表达式 — body 被替换为 None
- [ ] Bug 14 (R7): async for 体 ternary 识别失败

## Ternary 区域 Round 02 验证

- [x] R2-A Bug is_none: `x = (a if cond else b) is None` — `region_ast_generator.py` 行 16812 `has_ops` 集合新增 'IS_OP'/'CONTAINS_OP'，触发 expr_reconstructor 重建 Compare
  - 验证：`tests/exhaustive/ternary/test_r2_ternary_in_is_none.py` 通过
- [x] R2-A Bug contains: `x = (a if cond else b) in collection` — `region_analyzer.py` 行 11730 CONTAINS_OP 分支新增 STORE_* 检查（仿 R1 Bug 7 COMPARE_OP 修复），避免误设 `merge_context='compare'`
  - 验证：`tests/exhaustive/ternary/test_r2_ternary_in_contains.py` 通过
- [x] R2-B Bug multi_target: `x = y = a if cond else b` — `region_ast_generator.py` 行 16903 value_target 路径前新增 COPY 1 + 多 STORE 模式检测，发射 Assign(targets=[x, y], is_chain_assign=True)
  - 验证：`tests/exhaustive/ternary/test_r2_ternary_in_multi_target_assign.py` 通过
- [x] R2-B Bug unpacking: `a, b = (x, y) if cond else (z, w)` — 同 multi_target，行 16903 新增 UNPACK_SEQUENCE N + N STORE 模式检测，发射 Assign(targets=[Tuple([a, b])])
  - 验证：`tests/exhaustive/ternary/test_r2_ternary_in_unpacking.py` 通过
- [x] R2-C Bug raise: `raise (Exc1 if cond else Exc2)()` — `region_ast_generator.py` 行 17721 raise_instr.arg==1 分支新增 CALL 检测，用 expr_reconstructor 重建 Raise(exc=Call(func=ternary))
  - 验证：`tests/exhaustive/ternary/test_r2_ternary_in_raise.py` 通过
- [x] R2-D Bug multi_arg: `print(prefix, a if cond else b)` — `region_ast_generator.py` 行 17196 func_call_info 分支新增 preload[1:] 作为前置参数
  - 验证：`tests/exhaustive/ternary/test_r2_ternary_in_multi_arg_call.py` 通过
- [x] R2-D Bug lambda_call: `(lambda x: x * 2)(a if cond else 0)` — `region_analyzer.py` 行 11005 `_detect_ternary_context` 新增 MAKE_FUNCTION 模式识别 + `region_ast_generator.py` 行 17230 Call 构建后调用 `_convert_lambda_function_objects` 转为 Lambda dict
  - 验证：`tests/exhaustive/ternary/test_r2_ternary_in_lambda_call.py` 通过
- [x] 全量回归无退化 — Ternary 区域：65 failed → 58 failed（减 7）；109 passed → 116 passed（增 7）；1 skipped 不变
- [x] 修复依归约算法 4 原则 — 所有 7 个修复均通过「自底向上归约」「每块唯一归属」「嵌套即抽象节点」「父引用子入口」原则论证，无跨区域启发式特例、无后处理补丁、无扁平化
- [x] 修复报告已写 — `rounds/ternary_region/round_02/fix_report.md`

## R2 已知限制（未修复 bug，R3 处理）

- [ ] R2-E Bug chained_compare: `0 < (ternary) < 10` — SWAP + COPY 2 + 双 COMPARE_OP + JUMP_IF_FALSE_OR_POP 序列，与 R1 Bug 5 同类
- [ ] R2-F Bug await: 嵌套 async code object 内 GET_AWAITABLE + SEND 轮询循环，与 R1 Bug 10/13/15/16/17 同类
- [ ] R2-F Bug return_arith: 嵌套 code object 内 `return (ternary) + 1`，BINARY_OP + RETURN_VALUE 不满足单指令块，与 R1 Bug 10/13 同类
