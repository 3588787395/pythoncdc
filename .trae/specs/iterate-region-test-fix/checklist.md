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

## Ternary 区域 Round 10 验证

### SubTask T1.10.0: 基线确认
- [x] 全量 ternary 回归基线 = 66 failed / 277 passed / 5 skipped
- [x] 跨区域回归基线 = 109 failed / 1052 passed / 14 skipped
- [x] R10 新测试基线 = 15 failed / 13 passed

### SubTask T1.10.1 (P0): R9-12 @x.setter Attribute 装饰器
- [x] `@x.setter def x(self, v): ...` 反编译保留 `@x.setter`（Attribute(Name('x'), 'setter')），字节码等价
- [x] 修复依 4 原则：父 FunctionDef 通过 LOAD_ATTR setter 引用 LOAD_NAME x 子节点
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.10.2 (P0): 无参装饰器 + ternary default（R9-13/R10-03/R10-04/R10-05/R10-11）
- [x] `@abstractmethod def m(self, x=ternary): pass` 反编译保留 @abstractmethod + ternary default，字节码等价
- [x] `@classmethod def m(cls, x=ternary): pass` 反编译保留 @classmethod，字节码等价
- [x] `@staticmethod def m(x=ternary): pass` 反编译保留 @staticmethod，字节码等价
- [x] 多个 `@abstractmethod` + ternary default 共存，反编译全部保留
- [ ] `@overload def f(x: int) -> int: ...` 多次定义，反编译保留所有 @overload 装饰器 — **未修复**（R10-11 标记为已知限制，涉及三次函数定义 + annotations tuple，R10-Fix2 未覆盖多函数场景）
- [x] 修复依 4 原则：父 FunctionDef 通过 MAKE_FUNCTION 之后的 CALL 引用 FunctionObject 子节点；ternary 通过 BUILD_TUPLE defaults 引用
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.10.3 (P0): R10-01 装饰器链 @deco1 @deco2(ternary)
- [x] `@deco1 @deco2(a if c else b) def f(): pass` 反编译保留两层装饰器，字节码等价
- [x] 修复依 4 原则：每段 CALL 通过 MAKE_FUNCTION 之后的 CALL 引用下层装饰器或 FunctionObject 子节点
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.10.4 (P0): R10-02 @deco(a[ternary]) 下标参数
- [x] `@deco(a[b if c else d]) def f(): pass` 反编译保留 Subscript(a, ternary) 作装饰器参数，字节码等价
- [x] 修复依 4 原则：装饰器 Call 通过 merge_block 的 CALL 引用 ternary 子节点作为 BINARY_SUBSCR 的下标
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.10.5 (P0): R9-14 @deco(ternary) class C 类装饰器
- [x] `@deco(a if c else b) class C: pass` 反编译保留 Call(deco, [ternary]) 作类装饰器，字节码等价
- [x] 修复依 4 原则：装饰器 Call 通过 cond_block 的 deco 入口 + merge_block 的 CALL 引用 ternary 子节点
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.10.6-8 (评估/标记): P1/P2/P3 聚类
- [x] P1 聚类 G dataclass/类基础设施（R9-10/R10-06/R10-07/R10-08）评估并处理 — 评估后标记为已知限制（修复复杂度中-高，留待 R11+）
- [x] P2 聚类 H/I/J consumer/functools/kwonly（R9-15/R9-16/R10-09/R10-10/R10-12/R10-13/R10-14/R10-15）评估并处理 — R9-16/R10-13 已修复（Fix 3 bonus），其余 6 个标记为已知限制
- [x] P3 聚类 K/L except*/async with multi-as（R9-08/R7-03）标记为已知限制

### SubTask T1.10.9-12: 最终验证
- [x] 全量 ternary 回归：pre-R10 62 failed（≤66 ✓，改善 4）/ R10 新增 9 failed（已知限制）/ 总 71 failed / 300 passed / 5 skipped — 无基线退化
- [x] 跨区域回归：pre-R10 105 failed（≤109 ✓，改善 4）/ IF 43 failed（无退化）/ 775 passed / 9 skipped — 无基线退化
- [x] 修复报告已写 — `rounds/ternary_region/round_10/fix_report.md`
- [x] 所有修复均通过 4 原则论证，无跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限
- [x] 源代码无 debug 打印残留（grep print/pdb/breakpoint 仅匹配注释）
- [x] 未修改任何测试文件（git status 显示仅新增 R10 测试文件，无现有测试修改）
- [x] 未创建根级 debug 文件（`_debug_*.py` 已清理，`/tmp/dbg/` 为临时调试脚本）
- [x] 未 git commit（由父代理决定提交时机）

## Ternary 区域 Round 08 验证

### SubTask T1.8.0: 基线确认
- [x] 全量 ternary 回归基线 = 65 failed / 228 passed / 1 skipped
- [x] 跨区域回归基线 = 109 failed / 1001 passed / 11 skipped
- [x] R8 测试基线 = 8 failed / 19 passed / 2 skipped

### SubTask T1.8.1 (P0): assert message ternary 系列
- [x] R7-01 `assert x, (a if c else b)` 反编译为 ast.Assert(test=x, msg=IfExp)，字节码等价
- [x] R7-01b `assert x, f(a if c else b)` 反编译为 ast.Assert(test=x, msg=Call(f, [IfExp]))，字节码等价
- [x] R8-01 `assert x, (n := (a if c else b))` 反编译为 ast.Assert(test=x, msg=NamedExpr(n, IfExp))，字节码等价
- [x] R8-02 `assert x, "msg: " + (a if c else b)` 反编译为 ast.Assert(test=x, msg=BinOp("msg: ", +, IfExp))，字节码等价
- [x] R8-03 `assert x, {k: (a if c else b)}` 反编译为 ast.Assert(test=x, msg=Dict({k: IfExp}))，字节码等价
- [x] 修复依 4 原则：自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口
- [x] ternary 回归无退化（不新增 failed）
- [x] 跨区域回归无退化（不新增 failed）

### SubTask T1.8.2 (P0): R8-04 walrus 捕获 ternary
- [x] `(n := (a if c else b))` 反编译为 Expr(NamedExpr(n, IfExp))，字节码含 COPY+STORE+POP_TOP，等价
- [x] 修复依 4 原则
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.8.3 (P1): R7-04/R8-06 del subscript 双 ternary
- [x] R7-04 `del obj[a if c else b][c if d else e]` 反编译为 Delete([Subscript(Subscript(obj, IfExp1, Del), IfExp2, Del)])，字节码等价
- [x] R8-06 `del (a if c1 else b)[x if c2 else y]` 反编译为 Delete([Subscript(IfExp1, IfExp2, Del)])，字节码等价
- [x] 修复依 4 原则
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.8.4 (P2): R8-05 unpacking assign ternary
- [x] `*y, = (a if c else b)` 反编译为 Assign(targets=[Starred(y)], value=IfExp)，字节码含 UNPACK_EX，等价
- [x] 修复依 4 原则
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.8.5 (P2): R8-07 import 边界 ternary
- [x] `from x import y as z\nw = a if c else b` 反编译含 ImportFrom + Assign(w, IfExp)，import 不丢失，字节码等价
- [x] 修复依 4 原则
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.8.6 (评估): async 控制流 ternary 系列
- [x] R7-02/R7-03/R7-10/R8-08 评估本轮是否修复
- [x] 若未修复则记录为 R9+ 已知限制（评估结论：多文件多修改点 + 4 种不同修复方向 + 退化风险高，留待 R9+）

### SubTask T1.8.7-8: 最终验证
- [x] 全量 ternary 回归 ≤ 65 failed / ≥ 228 passed / 1 skipped，无新增退化 — 实际 63 failed / 257 passed / 3 skipped
- [x] 跨区域回归 ≤ 109 failed / ≥ 1001 passed / 11 skipped，无新增退化 — 实际 107 failed / 1030 passed / 13 skipped
- [x] 修复报告已写 — `rounds/ternary_region/round_08/fix_report.md`
- [x] 所有修复均通过 4 原则论证，无跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化
- [x] 源代码无 debug 打印残留
- [x] 未修改任何测试文件
- [x] 未创建根级 debug 文件（6 个 _debug_*.py 已清理）
- [x] 未 git commit（由父代理决定提交时机）

## Ternary 区域 Round 14 验证

### SubTask T1.14.0: 基线确认
- [x] 全量 ternary 回归基线 = 99 failed / 379 passed / 8 skipped（R13 88 + R14 新增 11）
- [x] 跨区域 control_flow_matrix 基线 = 3 failed / 324 passed / 11 skipped
- [x] R14 新测试基线 = 11 failed / 14 passed

### SubTask T1.14.1 (P1): R14-04 for iter list middle
- [x] `for x in [1, (a if c else b), 2]: pass` 反编译保留 BUILD_TUPLE 3 + 全部 list 元素 + ternary IfExp，字节码等价
- [x] 修复依 4 原则：父 for 通过 merge_block 的 BUILD_TUPLE 3 引用 ternary 子节点作 Tuple 中间元素
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.14.2 (P1): R14-05 raise ternary type from
- [x] `raise (a if c else b) from E2` 反编译为 Raise(exc=IfExp, cause=E2)，字节码等价
- [x] 修复依 4 原则：父 Raise 通过 merge_block 的 LOAD <cause> + RAISE_VARARGS 2 引用 ternary（exc 槽位）
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.14.3 (P1): R14-07 return method chain
- [x] `def f(): return (a if c else b).method()` 反编译为 Return(Call(Attribute(IfExp, 'method')))，字节码等价
- [x] 修复依 4 原则：父 Return 通过 merge_block 的 LOAD_METHOD + CALL + RETURN_VALUE 引用 ternary
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.14.4 (P1): R14-10 slice assign both bounds (Pattern F)
- [x] `x[(a if c else b):(d if e else f)] = 1` 反编译为 Assign(targets=[Subscript(x, Slice(t1, t2), Store)], value=Constant(1))，字节码等价
- [x] 修复依 4 原则：父 Assign 通过 outer.cond_block preload (value, obj) + innermost_merge 的 BUILD_SLICE 2 + STORE_SUBSCR 引用 chained ternary 作 Slice.lower/upper
- [x] ternary 回归无退化（94→93 failed）
- [x] 跨区域回归无退化

### SubTask T1.14.5 (P2): R14-06 raise arg and cause (Pattern G)
- [x] `raise E(a if c else b) from (d if e else f)` 反编译为 Raise(exc=Call(E, [t1]), cause=t2)，字节码等价
- [x] 修复依 4 原则：父 Raise 通过 outer.cond_block preload (E) + innermost_merge 的 RAISE_VARARGS 2 引用 chained ternary：t1 作 E() 参数（exc），t2 作 cause
- [x] ternary 回归无退化（94→93 failed）
- [x] 跨区域回归无退化

### SubTask T1.14.6 (评估): R14-01/02/03/08/09/11 评估
- [x] R14-01/02 while_cond + COMPARE_OP / walrus 系列 — 评估后标记为已知限制（while 回边 + ternary + COMPARE_OP 三方冲突，与 R3-09/R4-10/R5-10/R6-13 同根因，R15+ 统一处理）
- [x] R14-03 elif cond ternary — 评估后标记为已知限制（elif 链 + ternary false-branch 跳转目标归属冲突）
- [x] R14-08 multi-with second as — 评估后标记为已知限制（multi-with cleanup 链 + BEFORE_WITH + WITH_EXCEPT_START 异常处理路径复杂）
- [x] R14-09 yield from + method chain — 评估后标记为已知限制（RETURN_GENERATOR + yield from polling 循环 + method chain + ternary 四方归约）
- [x] R14-11 assert + boolop 两 ternary — 评估后标记为已知限制（boolop 短路逻辑 + 两 ternary 交织 + assert 区域边界）

### SubTask T1.14.7-10: 最终验证
- [x] 全量 ternary 回归 93 failed / 385 passed / 8 skipped（基线 99→93 -6，无基线退化）
- [x] 跨区域 control_flow_matrix 回归 3 failed / 324 passed / 11 skipped（无退化）
- [x] 修复报告已写 — `rounds/ternary_region/round_14/fix_report.md`
- [x] 所有修复均通过 4 原则论证，无跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限
- [x] 源代码无 debug 打印残留
- [x] 未修改任何 R13 passing 测试（仅新增 R14 测试）
- [x] 未创建根级 debug 文件（已清理 round_06 下 7 个遗留 _debug_*.py）
- [x] 未 git commit（由父代理决定提交时机）

## Ternary 区域 Round 15 验证

### SubTask T1.15.0: 基线确认
- [x] 全量 ternary 回归基线 = 93 failed / 385 passed / 8 skipped
- [x] 跨区域 control_flow_matrix 基线 = 3 failed / 324 passed / 11 skipped
- [x] R15 新测试基线 = 11 failed / 29 passed / 1 skipped

### SubTask T1.15.1 (P1): Cluster A — Constant obj.method(ternary) 7 bug
- [x] R15-01 `",".join((a if c else b))` 反编译保留 `Call(Constant(','), [IfExp])` 字节码等价
- [x] R15-02 `b",".join((a if c else b))` 反编译保留 `Call(Constant(b','), [IfExp])` 字节码等价
- [x] R15-03 `"{0.x}".format(a if c else b)` 反编译保留 `Call(Constant('{0.x}'), [IfExp])` 字节码等价
- [x] R15-04 `"{} {}".format((a if c else b), x)` 反编译保留 `Call(Constant('{} {}'), [IfExp, Name('x')])` 字节码等价
- [x] R15-08 `[].append((a if c else b))` 反编译保留 `Call(List([], Load), [IfExp])` 字节码等价
- [x] R15-09 `{}.get((a if c else b))` 反编译保留 `Call(Dict([], []), [IfExp])` 字节码等价
- [x] R15-10 `().count((a if c else b))` 反编译保留 `Call(Tuple([], Load), [IfExp])` 字节码等价
- [x] 修复依 4 原则：父 Call 通过 cond_block preload (obj_literal + LOAD_METHOD) 引用 ternary 子节点作 call 参数
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.15.2 (P1): Cluster B — ternary as callable 2 bug
- [x] R15-05 `(a if c else b)()` 反编译保留 `Call(IfExp(c, a, b), [])` 字节码等价
- [x] R15-06 `(a if c else b)(x, y)` 反编译保留 `Call(IfExp(c, a, b), [Name('x'), Name('y')])` 字节码等价
- [x] 修复依 4 原则：父 Call 通过 merge_block PRECALL+CALL 引用 ternary 子节点（在 func 槽位）
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.15.3 (P1): Cluster C — subscript on call result + ternary index 2 bug
- [x] R15-07 `vars()[(a if c else b)]` 反编译保留 `Subscript(Call(vars, []), IfExp, Load)` 字节码等价
- [x] R15-11 `dict()[(a if c else b)]` 反编译保留 `Subscript(Call(dict, []), IfExp, Load)` 字节码等价
- [x] 修复依 4 原则：父 Subscript 通过 cond_block preload (PUSH_NULL + callable + PRECALL + CALL 0) + merge_block (BINARY_SUBSCR) 引用 ternary 子节点
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.15.4-7: 最终验证
- [x] 全量 ternary 回归 93 failed / 425 passed / 9 skipped（基线 93/385/8，无退化 +40 passed）
- [x] 跨区域 control_flow_matrix 回归 3 failed / 324 passed / 11 skipped（无退化）
- [x] if_region 回归 43 failed / 775 passed / 9 skipped（无退化）
- [x] 修复报告已写 — `rounds/ternary_region/round_15/fix_report.md`
- [x] 所有修复均通过 4 原则论证，无跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限
- [x] 源代码无 debug 打印残留（region_analyzer.py 仅 docstring 示例含 print，region_ast_generator.py 无 debug 打印）
- [x] 未修改任何 R14 passing 测试（仅新增 R15 测试）
- [x] 未创建根级 debug 文件（_debug_r15_blocks.py + _debug_r15_explore.py 已删除）
- [x] 未 git commit（由父代理决定提交时机）

## R15 已知限制（未修复 bug）
- [ ] any_genexp skipped（与 R5 ternary_in_genexp 同嵌套 code object 机制，非新 bug，R5 已知限制延续）

## Ternary 区域 Round 20 验证（TERNARY 最后一轮）

### SubTask T1.20.0: 基线确认
- [x] 全量 ternary 回归基线（R19 commit 1d3bce5，无 R20 测试）= 43 failed / 529 passed / 9 skipped
- [x] 新增 16 个 R20 测试后基线 = 59 failed / 529 passed / 9 skipped
- [x] 跨区域回归基线 = 35 failed / 1418 passed / 13 skipped

### SubTask T1.20.1 (Cat 1): container literal starred 展开 6 bug
- [x] R20-01 `x = [*[a if c else b]]` 反编译保留 `Starred(List([IfExp]))`，BUILD_LIST+LIST_EXTEND 指令对保留，字节码等价
- [x] R20-02 `x = (*[a if c else b],)` 反编译保留 `Starred(List([IfExp]))`，字节码等价
- [x] R20-03 `x = {**{a if c else b: 1}}` 反编译保留 `Starred(Dict([IfExp],[1]))`，BUILD_MAP+DICT_UPDATE 指令对保留，字节码等价
- [x] R20-04 `f(*[a if c else b])` 反编译保留 `Call(f, [], [Starred(List([IfExp]))])`，CALL_FUNCTION_EX 保留，字节码等价
- [x] R20-05 `f(1, *[a if c else b], 2)` 反编译保留前置/后置位置参数 + Starred，字节码等价
- [x] R20-06 `f(x=1, *[a if c else b])` 反编译保留 kwarg + Starred，字节码等价
- [x] 修复依 4 原则：父 Starred 通过 LIST_EXTEND/DICT_UPDATE/CALL_FUNCTION_EX 栈效应引用 List/Dict 子节点，ternary 作 List.elts/Dict.keys 单抽象节点
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.20.2 (Cat 2): walrus store 上下文 2 bug
- [x] R20-08 `x[(n := a if c else b)] = y` 反编译保留 `Assign([Subscript(x, NamedExpr(n, IfExp))], y)`，STORE_SUBSCR 消费链保留，字节码等价
- [x] R20-09 `obj.attr = (n := a if c else b)` 反编译保留 `Assign([Attribute(obj, 'attr')], NamedExpr(n, IfExp))`，STORE_ATTR 消费链保留，字节码等价
- [x] 修复依 4 原则：父 Assign 通过 STORE_SUBSCR/STORE_ATTR 栈效应引用 NamedExpr 子节点，ternary 作 NamedExpr.value 单抽象节点
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.20.3 (Cat 3): 双 ternary boolop+binop 组合 4 bug
- [x] R20-10 `x = (a if c else b) and (d if e else f)` 反编译保留 `Assign([x], BoolOp(And, [IfExp1, IfExp2]))`，JUMP_IF_FALSE_OR_POP 消费链保留，字节码等价
- [x] R20-11 `x = (a if c else b) or (d if e else f)` 反编译保留 `Assign([x], BoolOp(Or, [IfExp1, IfExp2]))`，JUMP_IF_TRUE_OR_POP 消费链保留，字节码等价
- [x] R20-12 `assert x, (a if c else b) + (d if e else f)` 反编译保留 `Assert(x, BinOp(IfExp1, Add, IfExp2))`，BINARY_OP+RAISE_VARARGS 消费链保留，字节码等价
- [x] R20-13 `def f(): yield from (a if c else b) + (d if e else f)` 反编译保留 `Expr(YieldFrom(BinOp(IfExp1, Add, IfExp2)))`，BINARY_OP+GET_YIELD_FROM_ITER+SEND 循环保留，字节码等价
- [x] 修复依 4 原则：两个 ternary 各自独立归约为内层抽象节点，父表达式（BoolOp/BinOp/YieldFrom）通过消费指令栈效应（弹出 2 操作数）引用两个 ternary 子入口
- [x] ternary 回归无退化
- [x] 跨区域回归无退化

### SubTask T1.20.4: 回归守卫加固（关键质量保障）
- [x] 编辑 D 初版守卫过宽引入 20 个 r1-r19 回归（return/del/slice/dict/set/format/fstring/call/lambda/unpack 等场景）
- [x] 根因定位：守卫 `merge_block is not None` 在非 yield-from 双 ternary 场景误触发，输出 Expr 而非 Return/Assign
- [x] 修复：入口守卫新增 `and _second_tr.merge_extra_blocks`，精确限定为 yield-from（SEND 循环）场景
- [x] 修复后 20 个回归全部恢复，r1-r19 基线 43 failed 保持不变（经 git stash 对比验证 IDENTICAL）

### SubTask T1.20.5-8: 最终验证
- [x] 全量 ternary 回归 = 47 failed / 541 passed / 9 skipped（基线 r1-r19 43 failed 保持，+4 R20 已知限制，+12 R20 修复，0 真实回归 ✓）
- [x] 跨区域回归 = 35 failed / 1418 passed / 13 skipped（与基线 IDENTICAL，无退化 ✓）
- [x] R20 新测试 = 12 passed / 4 failed（4 已知限制）
- [x] 修复报告已写 — `rounds/ternary_region/round_20/fix_report.md`
- [x] 所有修复均通过 4 原则论证，无跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限
- [x] 源代码无 `_fix_*`/`_patch_*`/`_hack_*`/`_workaround_*`/`_temp_*` 前缀方法名
- [x] 未修改任何测试文件（git status 显示仅新增 R20 测试文件）
- [x] 未创建根级 debug 文件（`_dbg_regions.py` 在 round_20 目录内，已删除）
- [x] 所有命令 `timeout 280` 包裹

## R20 已知限制（未修复 bug）
- [ ] R20-07 walrus_in_cond: `x = (n := a) if (m := b if c else d) else e` — walrus + 嵌套 ternary + 外层 ternary 条件三层嵌套，cond_block walrus 副作用剥离与内层 ternary 归约交互复杂
- [ ] R20-14 async_with_item: `async with (a if c else b) as x: pass` — BEFORE_ASYNC_WITH + GET_AWAITABLE 消费链 + async with 清理协议渲染复杂
- [ ] R20-15 yield_from_method_on: `def f(): yield from (a if c else b).m()` — 与 R14-09 同类，单 ternary + LOAD_METHOD + CALL 消费，非双 ternary 共享块
- [ ] R20-16 except_handler_func_body: `def f(): try: x = 1 except (A if c else B) as e: pass` — ternary 已识别为 IfExp，但 except handler STORE_FAST e + DELETE_FAST e 清理序列渲染导致字节码不匹配（25 vs 24）

## TERNARY 区域 20 轮迭代完成
- R20 修复 12/16 bug（超过最低要求 10/16），4 个已知限制
- 最终 ternary 全量 = 47 failed / 541 passed / 9 skipped
- 进入下一区域（LOOP / Phase 2）
