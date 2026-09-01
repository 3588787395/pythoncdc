# Ternary Region Round 8 — Test Findings

## 概要

- **测试轮次**: Round 8 (R8)
- **测试时间**: 2026-07-20
- **测试文件目录**: `/workspace/tests/exhaustive/ternary/`
- **新建 R8 测试文件数**: 29
- **R8 真 failure 数**: 8
- **R7 已知限制仍 failure 数**: 6 (R7-01/01b/02/03/04/10)
- **R8 skip 数（反编译输出语法错误，不计入 failure）**: 2
- **累计确认 bug 数**: **14**（超过 10 个停止阈值）

测试命令：
```
cd /workspace && python -m pytest tests/exhaustive/ternary/test_r8_*.py --tb=no -q
# 8 failed, 19 passed, 2 skipped, 1 warning in 1.15s

cd /workspace && python -m pytest tests/exhaustive/ternary/test_r7_ternary_in_assert_msg.py \
  tests/exhaustive/ternary/test_r7_ternary_in_assert_complex_msg.py \
  tests/exhaustive/ternary/test_r7_ternary_in_async_for.py \
  tests/exhaustive/ternary/test_r7_ternary_in_async_with.py \
  tests/exhaustive/ternary/test_r7_ternary_in_async_for_else.py \
  tests/exhaustive/ternary/test_r7_ternary_in_del_target_complex.py \
  --tb=no -q
# 6 failed, 2 passed in 0.72s
```

---

## R7 已知限制回归确认（6 个，仍失败）

### R7-01: assert message ternary（简单变体）

| 项 | 值 |
|---|---|
| 测试文件 | `test_r7_ternary_in_assert_msg.py` |
| 源码 | `assert x, (a if c else b)` |
| 期望 | 反编译 + 重编译字节码与原始一致 |
| 实际 failure | `AssertionError: 指令3操作码不匹配: LOAD_NAME vs RAISE_VARARGS` |

**根因分析**：
- `_generate_assert`（`core/cfg/region_ast_generator.py:1676`）处理 `region.message_block` 时（行 1815-1852），把 message 块整体当作普通 message 表达式重建。但 message 块本身就是 TernaryRegion 的 entry/merge，message_block 的 LOAD_ASSERTION_ERROR + RAISE_VARARGS 与 ternary merge 共享同一块，导致 ternary 子区域未被父 AssertRegion 通过 message_block 入口引用。
- `_build_ternary_no_target_consumer_stmt`（`region_ast_generator.py:18340`）Pattern 1（行 18407-18423）只处理 `assert (ternary)`（ternary 作 test），未处理 `assert x, (ternary)`（ternary 作 msg）。后者被 Pattern 2 raise（行 18426）误匹配，输出 `raise (ternary)()`。
- 违反原则 3「嵌套区域在父区域中作为单个抽象节点」+ 原则 4「父区域 then/else 列表引用子区域入口」：AssertRegion 的 message_block 应引用 TernaryRegion 入口作为子节点。

**修复方向**：
1. 在 `_generate_assert` 处理 message_block 时，先检查 `region.message_block` 是否为某 TernaryRegion 的 entry 或 merge_block；若是，调用 `_generate_ternary(inner_ternary_region)` 获取 IfExp 作为 msg，并把 TernaryRegion.blocks 标记为 generated。
2. 或在 `_build_ternary_no_target_consumer_stmt` Pattern 1 增加检测：ternary 的 merge_block 含 LOAD_ASSERTION_ERROR + RAISE_VARARGS 时，如果 ternary 的 condition_block 不含 POP_JUMP_IF_TRUE→exit 跳过 raise 路径，说明 ternary 是 message 而非 test，应跳过 Pattern 1，让 AssertRegion 接管。

### R7-01b: assert message ternary（f(ternary) 变体）

| 项 | 值 |
|---|---|
| 测试文件 | `test_r7_ternary_in_assert_complex_msg.py` |
| 源码 | `assert x, f(a if c else b)` |
| 实际 failure | `指令数不匹配: 15 vs 16` |

根因同 R7-01，仅 ternary 外层多一层 f() 调用，反编译输出 `assert x; raise (ternary)()` 形式，调用嵌套层级错乱。

### R7-02: async for body ternary

| 项 | 值 |
|---|---|
| 测试文件 | `test_r7_ternary_in_async_for.py` |
| 源码 | `async def f():\n    async for x in ys:\n        y = a if c else b` |
| 期望 | 反编译结果含 IfExp AST 节点 |
| 实际 | 反编译输出 `async def f():\n    async for x in ys:\n        a\n        b`（IfExp 完全丢失，退化为两个表达式语句） |

**根因分析**：
- `_identify_loop_regions` 与 async for 的 polling 块（GET_AITER + GET_ANEXT + GET_AWAITABLE + SEND + YIELD_VALUE + RESUME + JUMP_BACKWARD_NO_INTERRUPT）路径冲突。
- async for 的 polling 循环被识别为 LoopRegion，其 body 块（含 ternary entry）归属到 LoopRegion，但 ternary 的 true/false/merge 块未在 LoopRegion.body 中正确归约。
- `_generate_with`（`region_ast_generator.py:12931`）行 13092-13098 有针对 async with 的 polling 块特殊处理，但 `_identify_loop_regions` 对 async for 的 polling 块缺少等价处理。
- 违反原则 2「每块在任意层级只属于一个区域」：ternary entry 块同时被 LoopRegion 与 TernaryRegion 声称归属。

**修复方向**：
1. 在 `_identify_loop_regions` 中识别 async for 的 polling 块模式（含 SEND + YIELD_VALUE + JUMP_BACKWARD_NO_INTERRUPT 且 header 块含 GET_AITER/GET_ANEXT/GET_AWAITABLE），将其与同步 for 的 polling 块同等处理。
2. 在 `_generate_region` 处理 LoopRegion body 时，对 async for 的 body 块（即 ternary entry 所在块）调用 `_generate_ternary`，把 ternary merge 块作为 IfExp 赋值语句输出，而不是退化为两个表达式。

### R7-03: async with body ternary

| 项 | 值 |
|---|---|
| 测试文件 | `test_r7_ternary_in_async_with.py` |
| 源码 | `async def f():\n    async with ctx:\n        y = a if c else b` |
| 实际 failure | `嵌套code object不匹配 (指令1): 指令10操作码不匹配: POP_TOP vs STORE_FAST` |

**根因分析**：
- `_generate_with` 行 13042-13066 有针对 `region.is_async and region.target is None` 的早期 as_target 检测，但当 ternary 在 body 内时，STORE_FAST x（as 绑定）与 STORE_FAST y（ternary merge）都被 WithRegion 误推断为 as_target。
- 违反原则 4「父区域 then/else 列表引用子区域入口，不是子区域所有块」：WithRegion 应只引用 TernaryRegion entry，不应吞并 TernaryRegion merge 块的 STORE_FAST y。

**修复方向**：
1. 在 `_generate_with` 的 as_target 早期检测（行 13042-13066）增加守卫：仅当 STORE_FAST 是 async with 的 SEND polling 循环跳出后第一个块的首条指令时才作为 as_target；若该块已属于 TernaryRegion（即 `region_analyzer.get_region_for_block(wb) is TernaryRegion`），跳过 as_target 推断。
2. 在 with body 主循环（行 13067+）扫描 with_blocks 时，遇到 TernaryRegion entry 应调用 `_generate_ternary(inner)`，让 ternary merge 块的 STORE_FAST y 归属 ternary，而非 with body 顶层语句。

### R7-04: del subscript chain（双 ternary 同块）

| 项 | 值 |
|---|---|
| 测试文件 | `test_r7_ternary_in_del_target_complex.py` |
| 源码 | `del obj[a if c else b][c if d else e]` |
| 实际 failure | `指令数不匹配: 12 vs 14`，重编退化为多个 POP_TOP 表达式 |

**根因分析**：
- `_try_build_ternary_store_assign`（`region_ast_generator.py:18627`）Pattern D（行 18835+）处理 `del d[ternary]` 单 ternary key 变体，但未覆盖双层 subscript + 双 ternary 的栈顺序（DELETE_SUBSCR 弹 [obj, key]，但 obj 本身已是 subscript 表达式含 ternary）。
- 两个 ternary 的 merge_block 都进入 DELETE_SUBSCR 块，违反原则 2「每块唯一归属」+ 原则 3「嵌套即抽象节点」。
- 反编译输出退化为 `LOAD_NAME; POP_TOP; LOAD_NAME; POP_TOP` 形式，完全丢失 del 结构。

**修复方向**：
1. 在 `_try_build_ternary_store_assign` Pattern D 增加 chain 检测：当 DELETE_SUBSCR 的 obj 操作数本身是另一个 TernaryRegion（即 merge_block 链式），调用 `_try_build_ternary_chained_container`（`region_ast_generator.py:19056`）的 R6 多 ternary 同 consumer 模式扩展逻辑。
2. 反编译输出应为 `Delete([Subscript(Subscript(obj, IfExp1, Del), IfExp2, Del)])`，遵循原则 4 让父 Delete 引用两个 TernaryRegion entry。

### R7-10: async for-else

| 项 | 值 |
|---|---|
| 测试文件 | `test_r7_ternary_in_async_for_else.py` |
| 源码 | `async def f():\n    async for x in ys:\n        pass\n    else:\n        y = a if c else b` |
| 实际 | 反编译输出 `async def f():\n    async for x in ys:\n        while True:\n            pass`（else 块丢失，ternary 丢失，body 退化为 while True） |

**根因分析**：
- async for-else 的 else 块入口（END_ASYNC_FOR 后的 JUMP_FORWARD 目标）未被识别为 LoopRegion.else_blocks。
- else 块内的 ternary merge 块的 STORE_FAST y 与 while True 占位结构冲突，违反原则 4。

**修复方向**：
1. 在 `_identify_loop_regions` 中扩展 async for 的 else 块识别：扫描 END_ASYNC_FOR 后的 fall-through 块作为 else 入口。
2. 把 else 块内的 ternary 通过 `_generate_ternary` 重建为 IfExp 赋值。

---

## R8 新增对抗性测试 — 真失败（8 个）

### R8-01: assert message 是 walrus(ternary)

| 项 | 值 |
|---|---|
| 测试文件 | `test_r8_ternary_in_assert_walrus_msg.py` |
| 源码 | `assert x, (n := (a if c else b))` |
| 实际反编译输出 | `assert x\nn = (a if c else b)` |
| 实际 failure | `指令数不匹配: 13 vs 10`（原始 13 条，重编 10 条 — 丢失 walrus 副作用 + 丢失 message） |

**根因分析**：
- 同 R7-01 的根因（AssertRegion.message_block 未识别 TernaryRegion），但变体为 walrus 包装。
- 反编译把 walrus 拆为独立 Assign，丢失 walrus 的 NamedExpr 上下文与 assert message 的关联。
- 字节码层 walrus 的 COPY + STORE n + PRECALL + CALL + RAISE_VARARGS 路径在 `_generate_assert`（行 1815-1852）的 message_block 重建中被丢弃。
- `_build_ternary_no_target_consumer_stmt` Pattern 1（行 18407-18423）未识别此模式：ternary merge_block 含 walrus COPY+STORE 时应跳过 Pattern 1。

**修复方向**：同 R7-01，扩展 `_generate_assert` 让 message_block 识别 TernaryRegion 入口；同时在 message 表达式重建中保留 walrus COPY+STORE 模式（参考行 1818-1828 的 walrus in assert message 注释，但实现未覆盖 ternary 包装情况）。

### R8-02: assert message 是 "str" + ternary

| 项 | 值 |
|---|---|
| 测试文件 | `test_r8_ternary_in_assert_binop_msg.py` |
| 源码 | `assert x, "msg: " + (a if c else b)` |
| 实际反编译输出 | `assert x\nraise ('msg: ' + (a if c else b))()` |
| 实际 failure | `指令3操作码不匹配: LOAD_CONST vs RAISE_VARARGS` |

**根因分析**：
- 同 R7-01 根因。message 是 BINARY_OP 包装 ternary，反编译把 message 误识别为 `raise (msg)()` 调用。
- 反编译输出 `raise ('msg: ' + (ternary))()` 是非法 raise 语法（raise 不能对 BinOp 调用），重编译可能 syntax error 或字节码不匹配。

**修复方向**：同 R7-01。

### R8-03: assert message 是 dict 含 ternary

| 项 | 值 |
|---|---|
| 测试文件 | `test_r8_ternary_in_assert_dict_msg.py` |
| 源码 | `assert x, {k: (a if c else b)}` |
| 实际反编译输出 | `assert x\nraise {k: a if c else b}()` |
| 实际 failure | `指令3操作码不匹配: LOAD_NAME vs RAISE_VARARGS` |

**根因分析**：同 R8-02，message 是 dict（BUILD_MAP）含 ternary value，反编译误识别为 `raise {dict}()` 调用。

**修复方向**：同 R7-01。

### R8-04: walrus 捕获 ternary 结果

| 项 | 值 |
|---|---|
| 测试文件 | `test_r8_ternary_walrus_assign.py` |
| 源码 | `(n := (a if c else b))` |
| 实际反编译输出 | `n = (a if c else b)` |
| 实际 failure | `指令数不匹配: 9 vs 7`（原始 9 条含 COPY+STORE+POP_TOP，重编 7 条仅 STORE — 丢失 walrus 留栈语义） |

**根因分析**：
- `_generate_ternary`（`region_ast_generator.py:16433`）行 16983 `elif region.value_target and not str(region.value_target).startswith('__'):` 分支：value_target 推断把 walrus 的 STORE_NAME n 当作普通赋值目标，输出 Assign([n], IfExp)。
- 但 walrus `(n := ternary)` 的字节码是 COPY 1 + STORE_NAME n + POP_TOP（保留栈顶供外层使用），不是普通 STORE 终结。
- `_try_build_ternary_store_assign`（行 18627）也未识别 walrus 模式。
- 违反原则 3「嵌套即抽象节点」：walrus NamedExpr 应作为单个抽象节点，包含 ternary IfExp 作为 value。

**修复方向**：
1. 在 `_generate_ternary` 的 value_target 分支前增加 walrus 检测：merge_block 含 `COPY 1 + STORE_NAME n + POP_TOP`（COPY 1 = COPY_STACK_TOP）时，输出 `Expr(NamedExpr(n, IfExp))` 而非 `Assign([n], IfExp)`。
2. 区分 walrus（COPY+STORE+POP_TOP，留栈）与普通 Assign（STORE 终结，不留栈）。

### R8-05: unpacking 赋值 source 是 ternary

| 项 | 值 |
|---|---|
| 测试文件 | `test_r8_ternary_unpack_assign.py` |
| 源码 | `*y, = (a if c else b)` |
| 实际反编译输出 | `y = (a if c else b)` |
| 实际 failure | `指令数不匹配: 8 vs 7`（原始 8 条含 UNPACK_EX，重编 7 条无 UNPACK_EX — 丢失 starred unpack） |

**根因分析**：
- 同 R8-04，value_target 推断吞并了 UNPACK_EX + STORE_NAME y 模式。
- `_try_build_ternary_store_assign` Pattern A（行 18703+）处理 STORE_SUBSCR / STORE_ATTR，未处理 UNPACK_EX + STORE 序列。
- 反编译输出丢失 starred target `*y,`。

**修复方向**：
1. 在 `_generate_ternary` 的 value_target 分支增加 UNPACK_EX 检测：merge_block 含 UNPACK_EX 时，输出 `Assign(targets=[Starred(y)], value=IfExp)`。
2. 或扩展 `_try_build_ternary_store_assign` 增加 Pattern E：UNPACK_EX + STORE_* 序列。

### R8-06: del obj[ternary] 双 ternary 同块（base 与 key 都是 ternary）

| 项 | 值 |
|---|---|
| 测试文件 | `test_r8_ternary_del_subscript_both.py` |
| 源码 | `del (a if c1 else b)[x if c2 else y]` |
| 实际反编译输出 | `(a if c1 else b)\n(x if c2 else y)` |
| 实际 failure | `指令数不匹配: 10 vs 14`（完全丢失 del + subscript 结构，两个 ternary 退化为独立表达式语句） |

**根因分析**：
- 同 R7-04 根因，但更严重：两个 ternary 都没有 merge_block 与 DELETE_SUBSCR 关联，因为 DELETE_SUBSCR 需要弹 [obj, key]，两个 ternary 的栈输出都被各自退化为表达式。
- `_build_ternary_no_target_consumer_stmt`（行 18340）未识别「两个 ternary 同 consumer」的 del 模式。
- `_try_build_ternary_chained_container`（行 19056）的 R6 模式（行 19121+）处理多 ternary 同 call consumer，但未覆盖 DELETE_SUBSCR consumer。

**修复方向**：
1. 扩展 `_try_build_ternary_chained_container` 增加 del subscript 模式：当 innermost merge_block 含 DELETE_SUBSCR，且 chain 中两个 ternary 分别作为 obj 与 key，输出 `Delete([Subscript(IfExp1, IfExp2, Del)])`。
2. 遵循原则 4：父 Delete 引用两个 TernaryRegion entry 作为 obj 与 key。

### R8-07: import from alias 后跟 ternary 赋值

| 项 | 值 |
|---|---|
| 测试文件 | `test_r8_ternary_in_import_from_alias.py` |
| 源码 | `from x import y as z\nw = a if c else b` |
| 实际反编译输出 | `w = (a if c else b)` |
| 实际 failure | `指令数不匹配: 13 vs 7`（import 语句完全丢失，从 13 条指令退化为 7 条） |

**根因分析**：
- `generate()`（`region_ast_generator.py:129`）的 entry_block 预扫描（行 188-296）处理 IMPORT_NAME + IMPORT_FROM + STORE_NAME 序列生成 `_pre_stmts`，但当 entry_block 后续含 ternary 时，预扫描终止条件（`if _instr.opname in FORWARD_JUMP_OPS...: break`）可能误把 import 指令吞入 ternary condition preload。
- 具体行 188-268 的 import 处理后设置 `_import_pending_store = True`，但若 import 块与 ternary entry 块共享（或 import 后立即是 ternary POP_JUMP），import store 被吞入 ternary condition preload 扫描。
- 违反原则 2「每块唯一归属」+ 原则 4「父区域引用子入口」。

**修复方向**：
1. 在 `generate()` entry_block 预扫描的 import 处理后，强制把 import 指令范围标记为 generated，避免 ternary condition preload 扫描时再次消费。
2. 或在 `_generate_ternary` 的 cond_block preload 扫描（行 17005+）增加守卫：跳过 IMPORT_NAME / IMPORT_FROM / LOAD_CONST 0（import level）序列。

### R8-08: async for iter 表达式是 ternary

| 项 | 值 |
|---|---|
| 测试文件 | `test_r8_ternary_async_for_iter.py` |
| 源码 | `async def f():\n    async for x in (a if c else b):\n        pass` |
| 实际反编译输出 | `async def f():\n    (a if c else b)\n    async for x in None:\n        continue` |
| 实际 failure | `嵌套code object不匹配 (指令1): 指令数不匹配: 16 vs 18` |

**根因分析**：
- ternary merge_block 的 STORE 临时变量应作为 GET_AITER 的源，但被退化为独立表达式 `(a if c else b)`，async for 的 iter 槽位变为 None。
- `_generate_ternary` 的 merge_context='iter' 分支（行 16785-16787）处理同步 for 的 iter 变体，但 async for 的 GET_AITER + GET_ANEXT + SEND polling 路径未覆盖。
- 同步 for 的 R8-iter 测试 (`test_r8_ternary_for_iter.py`) 通过，async for 失败 — 说明 async for 的 polling 块归属处理与 ternary 归约未解耦。
- 违反原则 2：ternary merge 块同时被 ternary（作为 Expr 输出）与 async for LoopRegion（作为 iter 源）声称归属。

**修复方向**：
1. 扩展 `_identify_ternary_regions` 在识别 ternary 后检测 merge_block 是否为 async for 的 GET_AITER 源块；若是，设置 `merge_context='async_iter'`。
2. 在 `_generate_ternary` 增加 `merge_context == 'async_iter'` 分支，输出 `Expr(IfExp)` 并把 IfExp 表达式传递给 async for 的 LoopRegion iter 表达式槽位（参考同步 for 的 merge_context='iter' 实现，行 16785）。

---

## R8 新增测试 — 反编译输出语法错误（skip，2 个，不计入 failure 总数）

### R8-S1: del obj[ternary].attr

| 项 | 值 |
|---|---|
| 测试文件 | `test_r8_ternary_del_attr_chain.py` |
| 源码 | `del obj[a if c else b].attr` |
| 实际反编译输出 | `return obj[a if c else b]`（包裹后 try 块无 except，重编译 syntax error） |
| skip 原因 | `verify_bytecode_equivalence` 的 `compile(decompiled)` 抛 SyntaxError → `skipTest("重编译失败")` |

**根因分析**：del subscript + attr 链式访问完全错乱，反编译输出 `return obj[ternary]` 退化为返回语句（无 del、无 .attr）。这是 R7-04 del 链问题的极端变体。

**修复方向**：同 R7-04 / R8-06。

### R8-S2: f-string 嵌套 ternary + 前后字面量

| 项 | 值 |
|---|---|
| 测试文件 | `test_r8_ternary_in_fstring_nested.py` |
| 源码 | `x = f"prefix-{a if c else b}-suffix"` |
| 实际反编译输出 | `return f'prefix-{(a if c else b)}'`（return 出现在模块顶层，重编译 syntax error） |
| skip 原因 | `'return' outside function` |

**根因分析**：f-string + ternary + 字面量的 BUILD_STRING 3 路径在模块顶层被退化为 return 语句（merge_context 误判为 'return'）。这是 f-string ternary 处理的边界 bug。

**修复方向**：检查 `_generate_ternary` 的 merge_context='fstring' 分支（行 16876+）在模块顶层（无 enclosing function）时不应生成 Return；应生成 Expr(JoinedStr)。

---

## R8 新增测试 — 通过（19 个，记录用于回归基线）

下列 19 个 R8 测试通过，作为未来回归基线（这些上下文已正确处理 ternary）：

| 测试文件 | 源码 | 说明 |
|---|---|---|
| test_r8_ternary_3level_nested_func.py | 3 层嵌套函数 + 最内层 ternary 赋值 | 已稳定 |
| test_r8_ternary_ann_assign.py | `y: int = (a if c else b)` | AnnAssign + ternary 已支持 |
| test_r8_ternary_async_with_as_body.py | `async with ctx as x: y = a if c else b` | 与 R7-03 不同源码但通过 |
| test_r8_ternary_aug_assign_subscr.py | `d[k] += (a if c else b)` | subscr augassign + ternary 已支持 |
| test_r8_ternary_chained_compare_complex.py | `x = 0 < (a if c else b) < 10` | 链式比较中间操作数 ternary 已支持 |
| test_r8_ternary_for_iter.py | `for x in (a if c else b): pass` | 同步 for iter 是 ternary 已支持 |
| test_r8_ternary_in_async_gen.py | `async def g(): yield a if c else b` | async gen + yield ternary 已支持 |
| test_r8_ternary_in_class_body_assign.py | 类体 ternary 赋值 + 方法定义 | 已稳定 |
| test_r8_ternary_in_decorator_with_args.py | `@deco(a if c else b) def f(): pass` | 装饰器带 ternary 参数已支持 |
| test_r8_ternary_in_fstring_format_spec.py | `x = f"{val:{a if c else b}}"` | f-string format_spec 是 ternary 已支持 |
| test_r8_ternary_in_global_then_assign.py | `def f(): global x; x = a if c else b` | global + ternary 已稳定 |
| test_r8_ternary_in_lambda_comprehension.py | `lambda items: [x if c else y for x in items]` | lambda + listcomp + ternary 已支持 |
| test_r8_ternary_in_nonlocal_then_assign.py | 嵌套函数 nonlocal + ternary | 已稳定 |
| test_r8_ternary_in_try_except_finally.py | try-except-finally + ternary in finally | 已稳定 |
| test_r8_ternary_multi_same_consumer.py | `f(a if c1 else b, d if c2 else e)` | 多 ternary 同 call consumer 已支持 |
| test_r8_ternary_nested_with_body.py | 嵌套 with + ternary 赋值 | 已稳定 |
| test_r8_ternary_raise_from_ternary_cause.py | `raise E from (a if c else b)` | raise from + ternary cause 已支持 |
| test_r8_ternary_starred_call.py | `f(*(a if c else b))` | call starred ternary 已支持 |
| test_r8_ternary_yield_from_assign.py | `x = yield from (a if c else b)` | yield from + ternary + 赋值已支持 |

---

## 累计 bug 统计

| 轮次 | bug 数 | 说明 |
|---|---|---|
| R1-R6 | 已修复 | 历史 bug 不计入本轮 |
| R7 已知限制仍失败 | 6 | R7-01/01b/02/03/04/10 |
| R8 新增真失败 | 8 | R8-01/02/03/04/05/06/07/08 |
| R8 skip（输出语法错误，不计入） | 2 | R8-S1/S2 |
| **累计确认 bug 数** | **14** | 超过 10 个停止阈值 |

---

## 整体修复优先级建议

按影响面 + 修复难度排序：

### P0（影响核心 ternary 归约语义，应优先修复）

1. **R7-01 / R8-01/02/03 (assert message ternary 家族)** — 5 个测试失败（R7-01 + R7-01b + R8-01 + R8-02 + R8-03）
   - 根因：`_generate_assert` message_block 未识别 TernaryRegion 入口
   - 修复点：`core/cfg/region_ast_generator.py:1815-1852` 的 message_block 处理 + `:18407-18423` Pattern 1 守卫

2. **R8-04 / R8-05 (walrus/unpack + ternary)** — 2 个测试失败
   - 根因：`_generate_ternary` value_target 推断吞并 walrus COPY+STORE 与 UNPACK_EX 模式
   - 修复点：`core/cfg/region_ast_generator.py:16983` value_target 分支前增加 walrus/UNPACK_EX 检测

3. **R7-04 / R8-06 / R8-S1 (del + ternary 家族)** — 3 个测试失败 + 1 skip
   - 根因：`_try_build_ternary_store_assign` Pattern D + `_try_build_ternary_chained_container` 未覆盖多 ternary 同 DELETE_SUBSCR consumer
   - 修复点：`core/cfg/region_ast_generator.py:18835` Pattern D 扩展 + `:19056` chained container 增加 del 模式

### P1（影响 async 控制流 + ternary）

4. **R7-02 / R7-10 / R8-08 (async for + ternary 家族)** — 3 个测试失败
   - 根因：`_identify_loop_regions` 未正确处理 async for polling 块与 ternary entry/merge 归属
   - 修复点：`core/cfg/region_analyzer.py` 的 `_identify_loop_regions` + async for else 块识别

5. **R7-03 (async with body ternary)** — 1 个测试失败
   - 根因：`_generate_with` as_target 早期推断吞并 ternary merge 的 STORE_FAST
   - 修复点：`core/cfg/region_ast_generator.py:13042-13066` as_target 守卫

### P2（影响模块顶层 ternary 输出格式）

6. **R8-07 (import + ternary)** — 1 个测试失败
   - 根因：`generate()` entry_block 预扫描的 import 处理未阻止 ternary condition preload 吞并
   - 修复点：`core/cfg/region_ast_generator.py:188-296` import 处理后强制 generated 标记

7. **R8-S2 (f-string + ternary 模块顶层)** — 1 skip
   - 根因：`_generate_ternary` merge_context='fstring' 分支在模块顶层误生成 Return
   - 修复点：`core/cfg/region_ast_generator.py:16876-16981` fstring 分支检查 enclosing function

---

## 修复方向必须遵守区域归约算法 4 原则

1. **自底向上归约**：先识别最内层 TernaryRegion，再让父区域（AssertRegion / WithRegion / LoopRegion / Delete 等）引用之
2. **每块唯一归属**：ternary entry/true/false/merge 块只归属 TernaryRegion，父区域不直接吞并这些块的指令
3. **嵌套即抽象节点**：walrus NamedExpr、UNPACK_EX starred、del subscript chain 应作为单个抽象节点，包含 ternary IfExp 作为 value/target
4. **父引用子入口**：AssertRegion.message_block 引用 TernaryRegion.entry；WithRegion body 引用 TernaryRegion.entry；Delete 引用 TernaryRegion.entry 作为 obj/key

所有修复点都在 `_generate_assert` / `_generate_ternary` / `_try_build_ternary_store_assign` / `_try_build_ternary_chained_container` / `_generate_with` / `_identify_loop_regions` 范围内，符合「父区域通过 consumer 指令（RAISE_VARARGS / DELETE_SUBSCR / STORE_SUBSCR / STORE_FAST / GET_AITER 等）引用子区域入口」的设计。

---

## 测试文件清单

### R8 新建测试文件（29 个）

位于 `/workspace/tests/exhaustive/ternary/`：

**失败（8 个）**：
- test_r8_ternary_async_for_iter.py
- test_r8_ternary_del_subscript_both.py
- test_r8_ternary_in_assert_binop_msg.py
- test_r8_ternary_in_assert_dict_msg.py
- test_r8_ternary_in_assert_walrus_msg.py
- test_r8_ternary_in_import_from_alias.py
- test_r8_ternary_unpack_assign.py
- test_r8_ternary_walrus_assign.py

**skip（2 个，反编译输出语法错误）**：
- test_r8_ternary_del_attr_chain.py
- test_r8_ternary_in_fstring_nested.py

**通过（19 个，回归基线）**：
- test_r8_ternary_3level_nested_func.py
- test_r8_ternary_ann_assign.py
- test_r8_ternary_async_with_as_body.py
- test_r8_ternary_aug_assign_subscr.py
- test_r8_ternary_chained_compare_complex.py
- test_r8_ternary_for_iter.py
- test_r8_ternary_in_async_gen.py
- test_r8_ternary_in_class_body_assign.py
- test_r8_ternary_in_decorator_with_args.py
- test_r8_ternary_in_fstring_format_spec.py
- test_r8_ternary_in_global_then_assign.py
- test_r8_ternary_in_lambda_comprehension.py
- test_r8_ternary_in_nonlocal_then_assign.py
- test_r8_ternary_in_try_except_finally.py
- test_r8_ternary_multi_same_consumer.py
- test_r8_ternary_nested_with_body.py
- test_r8_ternary_raise_from_ternary_cause.py
- test_r8_ternary_starred_call.py
- test_r8_ternary_yield_from_assign.py
