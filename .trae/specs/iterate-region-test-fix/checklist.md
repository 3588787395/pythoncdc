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
- [x] R2-F Bug return_arith: 嵌套 code object 内 `return (ternary) + 1`，BINARY_OP + RETURN_VALUE 不满足单指令块，与 R1 Bug 10/13 同类 — **R3 已修复**（Pattern 6）

## Ternary 区域 Round 03 验证

- [x] R3-04 Bug return_arith_left: `def f(): return 1 + (a if cond else 0)` — `region_ast_generator.py` `_build_ternary_no_target_consumer_stmt` 新增 Pattern 6（return wrapped），用 expr_reconstructor 重建 BINARY_OP + RETURN_VALUE 为 Return(BinOp(1, +, ternary))
  - 验证：`tests/exhaustive/ternary/test_r3_ternary_return_arith_left.py` 通过
- [x] R3-05 Bug return_arith_mul: `def f(): return (a if cond else 1) * 2` — 同 R3-04（Pattern 6 共用，BINARY_OP * 重建）
  - 验证：`tests/exhaustive/ternary/test_r3_ternary_return_arith_mul.py` 通过
- [x] R3-06 Bug return_call: `def f(): return foo(a if cond else 0)` — Pattern 6 用 `_compute_ternary_cond_preload_exprs` 提取 foo callable 加入 initial_stack，重建 Call(foo, [ternary]) + Return
  - 验证：`tests/exhaustive/ternary/test_r3_ternary_return_call.py` 通过
- [x] R3-07 Bug return_tuple: `def f(): return (a if cond else b), (c if cond else d)` — `_try_build_ternary_chained_container` 末尾新增 return 检测：innermost merge_block 以 RETURN_VALUE 结尾时返回 Return(Tuple) 而非 Expr(Tuple)
  - 验证：`tests/exhaustive/ternary/test_r3_ternary_return_tuple.py` 通过
- [x] R3-11 Bug raise_arg: `raise E(a if cond else b)` — `_build_ternary_no_target_consumer_stmt` raise 分支扩展：raise_instr.arg==1 且含 PRECALL/CALL 时，用 preload_exprs（含 E callable）重建 Call(E, [ternary])，包装为 Raise(exc=Call)
  - 验证：`tests/exhaustive/ternary/test_r3_ternary_raise_arg.py` 通过
- [x] 全量回归无退化 — Ternary 区域：58 failed → 55 failed（基线减 3 bonus）；新增 20 R3 测试后：61 failed, 133 passed, 1 skipped（无退化，POP_TOP + STORE_* 双守卫已修复两版退化）
- [x] 跨区域回归无退化 — ternary + if_region：基线 106 failed / 904 passed / 11 skipped → 106 failed / 905 passed / 11 skipped（STORE_* 守卫修复 test_adv11_augassign_subscr_ternary.py 退化后恢复基线）
- [x] 修复依归约算法 4 原则 — 所有 5 个 R3 修复 + 3 个 bonus 修复均通过「自底向上归约」「每块唯一归属」「嵌套即抽象节点」「父引用子入口」原则论证，无跨区域启发式特例、无后处理补丁、无扁平化
- [x] 修复报告已写 — `rounds/ternary_region/round_03/fix_report.md`
- [x] POP_TOP 回归保护 — Pattern 6 初版对 `func(ternary)` 顶层 Expr 语句误触发 Return 模式（退化 64 failed + 10 skipped），守卫 `merge_instrs[-1].opname != 'POP_TOP'` 修复后回归 61 failed + 1 skipped
- [x] STORE_* 回归保护 — Pattern 6 对 `if c: x[0] += a if b else c` 误触发 Return 模式（跨区域退化 11→12 skipped，test_adv11_augassign_subscr_ternary.py 因 `return x` 模块顶层非法被 skip），守卫 `not any(i.opname in STORE_OPS for i in merge_instrs)` 修复后恢复 11 skipped，该测试变 PASSED

## R3 已知限制（未修复 bug，R4+ 处理）

- [ ] R3-01/02 Bug chained_compare: ternary 在 chained compare 左端/4-term，需 chained_compare IfRegion 边界调整
- [ ] R3-03 Bug await_expr: `await (ternary)` 无 return，GET_AWAITABLE + SEND 循环消费 ternary
- [ ] R3-08 Bug try_handler: ternary 作为 except handler 异常类型，与 except 子句 COMPARE_OP 冲突
- [ ] R3-09 Bug while_cond: ternary 作为 while 条件，与 while 的 POP_JUMP_IF_FALSE 冲突
- [ ] R3-10 Bug with_as: ternary 作为 with 上下文管理器，BEFORE_WITH + STORE_NAME 消费链

## Ternary 区域 Round 07 验证

### SubTask T1.7.0: 基线确认
- [ ] 全量 ternary 回归基线 = 70 failed / 223 passed / 1 skipped
- [ ] 跨区域回归基线 = 103 failed / 975 passed / 11 skipped

### SubTask T1.7.1 (P0): R7-05/07/11 finally 块 ternary
- [ ] R7-05 `try: pass\nfinally: y = a if c else b` 反编译为 ast.Try 含 finally + body 内 IfExp 赋值，字节码等价
- [ ] R7-07 嵌套 try-finally + 内层 finally ternary + 外层 except E：内层 finally 正确归约，字节码等价
- [ ] R7-11 try-except-finally + finally ternary：finally 块内 IfExp 赋值正确归约（不再退化为 if-else 泄漏），字节码等价
- [ ] 修复依 4 原则：自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口
- [ ] ternary 回归无退化（不新增 failed）
- [ ] 跨区域回归无退化（不新增 failed）

### SubTask T1.7.2 (P1): R7-02/03/10 async 控制流 ternary
- [ ] R7-02 `async for x in ys: y = a if c else b` body 内 ternary 正确归约，字节码等价
- [ ] R7-03 `async with ctx: y = a if c else b` body 内 ternary 正确归约，as_target 不误识别（无 `as y`），字节码等价
- [ ] R7-10 `async for-else: y = a if c else b` else 块 ternary 正确归约，无幻影 while True: pass，字节码等价
- [ ] 修复依 4 原则
- [ ] ternary 回归无退化
- [ ] 跨区域回归无退化

### SubTask T1.7.3 (P2): R7-01/04/08/09 语句位置 ternary consumer
- [ ] R7-01 `assert x, (a if c else b)` message 位置 ternary 正确归约为 ast.Assert(test=x, msg=IfExp)，字节码等价
- [ ] R7-08 `assert x, f(a if c else b)` message 是 f(ternary) 调用，正确归约为 ast.Assert(test=x, msg=Call(f, [IfExp]))，字节码等价
- [ ] R7-04 `del x[a if c else b][c if d else e]` 双 subscript ternary 正确归约为 ast.Delete(Subscript(Subscript(x, t1), t2))，字节码等价
- [ ] R7-09 `del (a if c else b)[idx]` base 是 ternary，正确归约为 ast.Delete(Subscript(IfExp, idx))，字节码等价
- [ ] 修复依 4 原则
- [ ] ternary 回归无退化
- [ ] 跨区域回归无退化

### SubTask T1.7.4 (P3): R7-06 yield from + 赋值复合
- [ ] R7-06 `def g(): x = yield from (a if c else b)` ternary merge 块作为 yield from iterable 正确归约，字节码等价
- [ ] 修复依 4 原则
- [ ] ternary 回归无退化
- [ ] 跨区域回归无退化

### SubTask T1.7.5-7: 最终验证
- [ ] 全量 ternary 回归 = 70 - N failed（N = 修复成功的 bug 数），无新增退化
- [ ] 跨区域回归 ≤ 103 failed / ≥ 975 passed / 11 skipped，无新增退化
- [ ] 修复报告已写 — `rounds/ternary_region/round_07/fix_report.md`
- [ ] 所有修复均通过 4 原则论证，无跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化
- [ ] 源代码无 debug 打印残留
- [ ] 未修改任何测试文件
- [ ] 未创建根级 debug 文件
- [ ] 未 git commit
