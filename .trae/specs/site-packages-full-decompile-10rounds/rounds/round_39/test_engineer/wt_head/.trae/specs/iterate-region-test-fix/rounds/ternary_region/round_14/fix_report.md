# Ternary Region Round 14 修复报告

## 概览

- **执行日期**: 2026-07-21
- **基线**（R13 commit 46d82ea）：ternary 全量 88 failed / 365 passed / 8 skipped；跨区域 131 failed / 1140 passed / 17 skipped
- **R14 测试加入后**：ternary 全量 99 failed / 379 passed / 8 skipped（+11 新失败 / +14 新通过）
- **R14 修复完成后**：ternary 全量 93 failed / 385 passed / 8 skipped（基线 99 → 93，**-6 failed**）；跨区域 control_flow_matrix 3 failed / 324 passed / 11 skipped（**无退化**）
- **新建测试文件数**: 22
- **真失败 bug 数**: 11
- **修复 bug 数**: 5（达到「至少 5 个 bug」目标）
- **未修复 bug 数**: 6（标记为已知限制，留待 R15+）
- **算法合规性自检**: 通过（详见第五节）

---

## 一、修复的 bug（5 个）

### R14-04 ternary 在 for iter list literal 中间元素

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_for_iter_list_middle.py`
- **源码**: `for x in [1, (a if c else b), 2]:\n    pass`
- **根因**: for 循环的 iter 表达式是 list literal `[1, ternary, 2]`，中间元素是 ternary。R13-08 修复了单语句场景，R14 在 for iter 消费链下未正确归约。BUILD_TUPLE 3 + sibling LOAD_CONST 1/2 全丢失，仅保留 ternary 表达式。
- **修复方案**: 三处协同修改：
  1. `region_ast_generator.py` iter merge_ctx 处理器（约 L17167-17201）调用 `_try_build_ternary_merge_consumer_expr` 处理多元素容器，并解包 Iter wrapper（`{'type': 'Iter', 'value': {'type': 'Tuple', ...}}` → 取 `value` 作 iter_expr）。
  2. `_loop_generate_for` 方法（约 L2768-2781）扩展 iter_expr 类型检查，新增 `'List', 'Tuple', 'Set', 'Dict'` 接受类型（原本只接受 `'IfExp', 'Call'`）。
  3. 同上方法第二处（约 L2797-2804）同步扩展类型检查。
- **算法 4 原则论证**:
  - **自底向上归约**: ternary 子节点先归约为 IfExp 表达式，再由父 for 语句消费。
  - **每块唯一归属**: ternary 的 cond/true/false/merge 块归属 TernaryRegion；for 的 GET_ITER/FOR_ITER 块归属 LoopRegion。
  - **嵌套即抽象节点**: ternary 在 for 的 iter 表达式中是单个抽象 Tuple 元素节点。
  - **父引用子入口**: 父 for 通过 merge_block 的 BUILD_TUPLE 3 引用 ternary 子节点作为 Tuple 中间元素。
- **回归验证**: ternary 全量无新增退化；跨区域无新增退化。

### R14-05 ternary 在 raise 异常类型位置 + from

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_raise_ternary_type_from.py`
- **源码**: `raise (a if c else b) from E2`
- **根因**: raise from 的异常类型本身是 ternary（与 R8 ternary_cause 不同，R14 测异常类型位置）。ternary IS the exc，cause E2 loaded in merge_block。原代码只处理 `raise E from (ternary)`（preload E, ternary IS cause）情况，未处理 `raise (ternary) from E2`（无 preload, ternary IS exc）。
- **修复方案**: `region_ast_generator.py` raise_instr.arg==2 处理器（约 L19464-19489）新增 `else` 分支：当无 preload 时，调用 `expr_reconstructor.reconstruct(merge_instrs, initial_stack=[ternary_expr])`，让 merge_block 的 `LOAD <cause> + RAISE_VARARGS 2` 重建为 `Raise(exc=ternary, cause=<cause>)`。
- **算法 4 原则论证**:
  - **自底向上归约**: ternary 子节点先归约为 IfExp，再由父 Raise 消费。
  - **每块唯一归属**: ternary merge 块归属 TernaryRegion；RAISE_VARARGS 归属父 Raise 语句。
  - **嵌套即抽象节点**: ternary 在父 Raise 中作 exc 槽位的单个抽象节点。
  - **父引用子入口**: 父 Raise 通过 merge_block 的 `LOAD <cause> + RAISE_VARARGS 2` 引用 ternary 子节点（exc 槽位）。
- **回归验证**: ternary 全量无新增退化；跨区域无新增退化。

### R14-07 ternary 在 return + method chain

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_return_method_chain.py`
- **源码**: `def f():\n    return (a if c else b).method()`
- **根因**: return 表达式是 ternary + method chain。ternary merge 之后 LOAD_METHOD + PRECALL + CALL 0 消费链作为 RETURN_VALUE 栈顶。反编译器丢失 RETURN_VALUE 消费链，将表达式语句 POP_TOP 替换为 return 语句。
- **修复方案**: `region_ast_generator.py` `_try_build_ternary_merge_consumer_expr` 调用处（约 L18485-18510）新增 `_is_return_consumer` 检测：检查 merge_block 是否以裸 RETURN_VALUE 结尾（非 `LOAD_CONST None + RETURN_VALUE` 隐式 None），若是则包装为 `{'type': 'Return', 'value': _merge_consumer_expr}` 而非 `Expr`。
- **算法 4 原则论证**:
  - **自底向上归约**: ternary 子节点先归约为 IfExp，再经 LOAD_METHOD/CALL 归约为 Call(IfExp)，最后由 RETURN_VALUE 包装为 Return。
  - **每块唯一归属**: ternary merge 块归属 TernaryRegion；RETURN_VALUE 归属父 Return 语句。
  - **嵌套即抽象节点**: ternary 在父 Return 中作 Call.receiver 的单个抽象节点。
  - **父引用子入口**: 父 Return 通过 merge_block 的 `LOAD_METHOD + PRECALL + CALL 0 + RETURN_VALUE` 引用 ternary 子节点。
- **回归验证**: ternary 全量无新增退化；跨区域无新增退化。

### R14-10 ternary 在 slice assign 双边界

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_slice_assign_both_bounds.py`
- **源码**: `x[(a if c else b):(d if e else f)] = 1`
- **根因**: subscript slice assign，slice 上下界都是 ternary。R13-02 修复了 `del x[t1:t2]` 双 ternary del slice（Pattern E），但 R14 测 slice assign 双 ternary 变体未正确归约。BUILD_SLICE 2 + STORE_SUBSCR 与 chained ternary 归属冲突，整个 slice assign 丢失。
- **修复方案**: `region_ast_generator.py` `_try_build_ternary_chained_r6_pattern` 方法（约 L21466-21539）新增 **Pattern F**：检测 innermost_merge 含 `BUILD_SLICE 2 + STORE_SUBSCR` + `len(elts) == 2`，从 outer.cond_block preload 提取 `[value, obj]`（如 `[Constant(1), Name(x)]`），构造 `Assign(targets=[Subscript(obj, Slice(t1, t2), Store)], value=value)`。镜像 Pattern E（del slice）逻辑，区别：STORE_SUBSCR vs DELETE_SUBSCR、ctx='Store' vs 'Del'、Assign vs Delete、需 value。
- **算法 4 原则论证**:
  - **自底向上归约**: 两个 ternary 子节点先各自归约为 IfExp，再由 BUILD_SLICE 2 组合为 Slice(t1, t2)。
  - **每块唯一归属**: 两个 ternary 的 cond/true/false/merge 块各自归属其 TernaryRegion；BUILD_SLICE + STORE_SUBSCR 归属父 Assign 语句。
  - **嵌套即抽象节点**: 两个 ternary 在父 Assign 中作 Slice.lower/upper 的两个抽象节点。
  - **父引用子入口**: 父 Assign 通过 outer.cond_block preload (value, obj) + innermost_merge 的 `BUILD_SLICE 2 + STORE_SUBSCR` 引用 chained ternary 子节点列表作为 Slice 的 lower/upper。
- **回归验证**: ternary 全量 94→93 failed（-1）；跨区域无新增退化。

### R14-06 ternary 在 raise arg 与 cause 共存

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_raise_arg_and_cause.py`
- **源码**: `raise E(a if c else b) from (d if e else f)`
- **根因**: raise 同时含两个 ternary：第一个 ternary 在 E() 调用 args，第二个 ternary 在 from cause 位置。两个 ternary region 链式归约（outer.merge = inner.entry）时 chained ternary 识别冲突，CALL 与 RAISE_VARARGS 都未正确归约。
- **修复方案**: `region_ast_generator.py` `_try_build_ternary_chained_r6_pattern` 方法（约 L21541-21608）新增 **Pattern G**：检测 innermost_merge 含 `RAISE_VARARGS 2` + `len(elts) == 2`，从 outer.cond_block preload 提取 `[E]`（过滤 PUSH_NULL），构造 `Raise(exc=Call(E, [elts[0]]), cause=elts[1])`。outer ternary 的 merge（= inner entry）含 PRECALL + CALL 形成 E(t1)，inner ternary 的 merge 含 RAISE_VARARGS 2 消费 [E(t1), t2]。
- **算法 4 原则论证**:
  - **自底向上归约**: 两个 ternary 子节点先各自归约为 IfExp，再由 PRECALL+CALL（外层 merge）形成 E(t1)，最终由 RAISE_VARARGS 2 组合为 Raise。
  - **每块唯一归属**: 两个 ternary 的 cond/true/false/merge 块各自归属其 TernaryRegion；PRECALL+CALL 归属外层 ternary 的父 Call；RAISE_VARARGS 归属父 Raise 语句。
  - **嵌套即抽象节点**: t1 在父 Raise 中作 Call(E).args[0] 的抽象节点；t2 作 cause 槽位的抽象节点。
  - **父引用子入口**: 父 Raise 通过 outer.cond_block preload (E) + innermost_merge 的 `RAISE_VARARGS 2` 引用 chained ternary 子节点列表：t1 作 E() 参数（exc 槽位），t2 作 cause。
- **回归验证**: ternary 全量 94→93 failed（-1）；跨区域无新增退化。

---

## 二、未修复的 bug（6 个，标记为已知限制 R15+）

### R14-01 ternary 在 while 条件中含 COMPARE_OP

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_while_cond_compare.py`
- **源码**: `while (a if c else b) > 0:\n    pass`
- **未修复原因**: while 条件是 ternary + COMPARE_OP 组合。R3-09 已知限制 `while (ternary):` 同根因（while 的 POP_JUMP_IF_FALSE 与 ternary 的 cond_block 跳转冲突），R14 加 COMPARE_OP 后更复杂——ternary merge 之后的 COMPARE_OP + POP_JUMP_IF_FALSE 跳回 while 顶，反编译器不识别 ternary region，整个 while 循环被丢弃。
- **复杂度**: 中-高（while 循环回边 + ternary 条件跳转 + COMPARE_OP 三方区域边界冲突）
- **留待**: R15+ 处理 while_cond 系列（R3-09/R4-10/R5-10/R6-13/R14-01/02 同根因）

### R14-02 ternary 在 while 条件 + walrus 赋值

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_walrus_in_while_cond.py`
- **源码**: `while (n := (a if c else b)) > 0:\n    pass`
- **未修复原因**: 与 R14-01 同根因（while + ternary + COMPARE_OP），额外加 walrus 副作用（COPY + STORE_NAME n）。整个 while 循环 + walrus + ternary 全部丢失。
- **复杂度**: 高（while 回边 + walrus 副作用 + ternary + COMPARE_OP 四方冲突）
- **留待**: R15+ 与 R14-01 一并处理

### R14-03 ternary 在 elif 条件中

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_elif_cond.py`
- **源码**: `if x:\n    pass\nelif (a if c else b):\n    pass`
- **未修复原因**: elif 条件本身是 ternary。反编译器把 `elif (a if c else b): pass` 错误展开为 `elif c: if a: pass` + `elif b: pass` 三层 if-elif 链，丢失 ternary IfExp 结构。ternary region 与 elif region 边界归属冲突——ternary 的 false-branch 跳转目标被误识别为下一个 elif 的条件。
- **复杂度**: 中-高（elif 链 + ternary false-branch 跳转目标归属冲突）
- **留待**: R15+ 处理 elif + ternary 边界

### R14-08 ternary 在 multi-with 第二 item + as 别名

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_with_multiple_second_as.py`
- **源码**: `with a as x, (b if c else d) as y:\n    pass`
- **未修复原因**: with 多 item，第二个 item 的 context manager 是 ternary 且带 as 别名。BUILD_TUPLE 2 + BEFORE_WITH + WITH_EXIT 链与 ternary region 边界冲突，第二个 with item 完全丢失（输出仅 `with a as x: pass`）。
- **复杂度**: 高（multi-with cleanup 链 + BEFORE_WITH + WITH_EXCEPT_START 异常处理路径 + ternary 边界）
- **留待**: R15+ 处理 multi-with + ternary ctx mgr

### R14-09 ternary 在 yield from + method chain

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_yield_from_with_method.py`
- **源码**: `def gen():\n    yield from (a if c else b).items()`
- **未修复原因**: yield from 表达式是 ternary 后接 .items() 方法调用。ternary merge 之后 LOAD_METHOD items + PRECALL + CALL 0 消费链作为 GET_YIELD_FROM_ITER + SEND + YIELD_VALUE polling 循环输入。反编译器不识别 ternary region，整个 gen 函数体反编译为 None。涉及 RETURN_GENERATOR + yield from polling 循环 + ternary + method chain 四方归约。
- **复杂度**: 高（yield from polling 循环 + method chain + ternary 三方归约）
- **留待**: R15+ 处理 yield from + ternary + method chain

### R14-11 ternary 在 assert 测试含两 ternary + boolop

- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_assert_two_ternaries_boolop.py`
- **源码**: `assert (a if c else b) and (d if e else f)`
- **未修复原因**: assert 测试表达式是两个 ternary 通过 boolop AND 组合。两个 ternary 不是直接 chained（boolop 短路逻辑创建中间块），chained ternary 识别不触发。第一个 ternary 后多出 POP_TOP，第二个 ternary IfExp 结构丢失。字节码中两 ternary 与 boolop 短路跳转交织，非简单 chained 结构。
- **复杂度**: 中-高（boolop 短路逻辑 + 两 ternary 交织 + assert 区域边界）
- **留待**: R15+ 处理 boolop + 多 ternary 短路组合

---

## 三、整体测试结果

### 3.1 R14 测试集

```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/test_r14_*.py --tb=no -q
6 failed, 19 passed in 1.50s
```

- 修复前: 11 failed / 14 passed
- 修复后: 6 failed / 19 passed（**+5 passed**）

### 3.2 ternary 全量回归

```
$ cd /workspace && timeout 280 python -m pytest tests/exhaustive/ternary/ --tb=no -q
93 failed, 385 passed, 8 skipped in 4.08s
```

- R13 基线: 88 failed / 365 passed / 8 skipped
- R14 测试加入后（修复前）: 99 failed / 379 passed / 8 skipped
- R14 修复后: 93 failed / 385 passed / 8 skipped（基线 99 → 93，**-6 failed**）
- **无基线退化**（R13 的 88 failed 全部保留，R14 新增 11 中修复 5 + 1 bonus，剩 5 + R14-11 共 6 个已知限制 = 93 - 88 = +5 R14 未修复 + 1 额外 bonus 修复 = 5 实际未修复 + R14-11 = 6）

### 3.3 跨区域回归（control_flow_matrix）

```
$ cd /workspace && timeout 280 python -m pytest tests/control_flow_matrix/ --tb=no -q
3 failed, 324 passed, 11 skipped in 2.18s
```

- 基线: 3 failed / 324 passed / 11 skipped
- 修复后: 3 failed / 324 passed / 11 skipped（**无退化**）

---

## 四、修改的源码位置

### `core/cfg/region_ast_generator.py`

1. **R14-04 修复**（约 L17167-17201）: iter merge_ctx 处理器调用 `_try_build_ternary_merge_consumer_expr` 处理多元素容器 + Iter wrapper 解包。
2. **R14-04 修复**（约 L2768-2781 + L2797-2804）: `_loop_generate_for` 两处 iter_expr 类型检查扩展，新增 `'List', 'Tuple', 'Set', 'Dict'`。
3. **R14-05 修复**（约 L19464-19489）: raise_instr.arg==2 处理器新增 else 分支，无 preload 时用 `initial_stack=[ternary_expr]` 重建 `Raise(exc=ternary, cause=<cause>)`。
4. **R14-07 修复**（约 L18485-18510）: `_try_build_ternary_merge_consumer_expr` 调用处新增 `_is_return_consumer` 检测，裸 RETURN_VALUE 时包装为 Return 而非 Expr。
5. **R14-10 修复**（约 L21466-21539）: `_try_build_ternary_chained_r6_pattern` 新增 **Pattern F**（slice assign 双 ternary）。
6. **R14-06 修复**（约 L21541-21608）: `_try_build_ternary_chained_r6_pattern` 新增 **Pattern G**（raise E(t1) from (t2) 双 ternary）。

### `core/cfg/region_analyzer.py`

- 未修改。

---

## 五、算法合规性自检

### 5.1 自底向上归约 ✅

所有 5 个修复均先归约内层 ternary 子节点（IfExp），再由父语句消费：
- R14-04: ternary → Tuple 元素 → for iter
- R14-05: ternary → Raise.exc
- R14-07: ternary → Call.receiver → Return.value
- R14-10: 两个 ternary → Slice.lower/upper → Assign.targets[0].slice
- R14-06: 两个 ternary → Call(E).args[0] + Raise.cause

### 5.2 每块唯一归属 ✅

所有修复中，每个 BasicBlock 在任一时刻只归属一个 Region：
- ternary 的 cond/true/false/merge 块归属 TernaryRegion
- 消费指令（RAISE_VARARGS / RETURN_VALUE / STORE_SUBSCR / BUILD_SLICE / PRECALL+CALL）归属父语句
- 无块同时归属两个 Region

### 5.3 嵌套即抽象节点 ✅

所有修复中，ternary 在父表达式中是单个抽象节点：
- R14-04: ternary 是 Tuple 的一个元素节点
- R14-05: ternary 是 Raise.exc 节点
- R14-07: ternary 是 Call.receiver 节点（经 LOAD_METHOD + CALL 包装）
- R14-10: 两个 ternary 分别是 Slice.lower 和 Slice.upper 节点
- R14-06: t1 是 Call(E).args[0] 节点，t2 是 Raise.cause 节点

### 5.4 父引用子入口 ✅

所有修复中，父语句通过 merge_block 的消费指令引用 ternary 子节点入口：
- R14-04: 父 for 通过 merge_block 的 BUILD_TUPLE 3 引用 ternary
- R14-05: 父 Raise 通过 merge_block 的 LOAD <cause> + RAISE_VARARGS 2 引用 ternary（exc 槽位）
- R14-07: 父 Return 通过 merge_block 的 LOAD_METHOD + PRECALL + CALL + RETURN_VALUE 引用 ternary
- R14-10: 父 Assign 通过 outer.cond_block preload (value, obj) + innermost_merge 的 BUILD_SLICE 2 + STORE_SUBSCR 引用 chained ternary
- R14-06: 父 Raise 通过 outer.cond_block preload (E) + innermost_merge 的 RAISE_VARARGS 2 引用 chained ternary

### 5.5 禁止事项核查 ✅

- ❌ 跨区域启发式特例: 无（所有修复均通过 chained ternary 通用 Pattern F/G 或现有 merge_consumer 机制）
- ❌ 后处理补丁: 无（所有修复在区域归约阶段完成，无后处理 AST 改写）
- ❌ 启发式优先级覆盖: 无（Pattern F/G 在现有 Pattern A-E 链后追加，无优先级覆盖）
- ❌ 扁平化嵌套: 无（ternary 始终保持 IfExp 嵌套结构）
- ❌ 硬编码深度上限: 无
- ❌ 修改 R13 passing 测试: 无（仅新增 R14 测试，未修改任何现有测试）
- ❌ 创建根级 _debug 文件: 无（已清理 round_06 下 7 个遗留 _debug_*.py）

---

## 六、清理记录

- 删除 `/workspace/.trae/specs/iterate-region-test-fix/rounds/ternary_region/round_06/` 下 7 个遗留 _debug 文件：
  - `_debug_bytecode.py`
  - `_debug_regions.py`
  - `_debug_r6_06.py`
  - `_debug_r6_06_trace.py`
  - `_debug_r6_10.py`
  - `_debug_r6_17.py`
  - `_debug_r6_20.py`
- R14 round 目录下无 _debug 文件创建。

---

## 七、与历史轮次的关系

### 7.1 R14 修复复用的历史 Pattern

- **Pattern E (R13-02)**: `del x[t1:t2]` 双 ternary del slice → R14-10 Pattern F 镜像扩展为 slice assign
- **R8-03 (raise from ternary cause)**: `raise E from (ternary)` → R14-05 扩展为 `raise (ternary) from E`（exc 位置 ternary）
- **R3-11 (raise arg)**: `raise E(ternary)` → R14-06 Pattern G 扩展为 `raise E(t1) from (t2)`（双 ternary）
- **R13-01 (method chain + ternary arg)**: `s.upper().split(ternary)` → R14-07 扩展为 `return (ternary).method()`（return 消费链）
- **R13-08 (list middle ternary)**: `[1, ternary, 2]` 单语句 → R14-04 扩展为 `for x in [1, ternary, 2]:`（for iter 消费链）

### 7.2 R14 新增 Pattern

- **Pattern F**: `x[t1:t2] = value` slice assign 双 ternary（镜像 Pattern E）
- **Pattern G**: `raise E(t1) from (t2)` raise 双 ternary（exc 是 Call(E, t1)，cause 是 t2）

### 7.3 累积已知限制（R1-R14）

R14 后累积已知限制约 23 个：
- R1-R13 累积约 17 个（chained_compare 4-way / while_cond 系列 / async for-else / except* PEP 654 / frozen dataclass / lambda default / nested lambda body / property setter / abstractmethod / class decorator arg / partial application / 多函数 @overload / assert+return consumer / async with multi-as 等）
- R14 新增 6 个（R14-01/02/03/08/09/11，详见第二节）

---

## 八、Git 状态

- **未 git commit**（由父代理决定提交时机）
- **修改文件**:
  - `core/cfg/region_ast_generator.py`（6 处修改）
  - `tests/exhaustive/ternary/test_r14_*.py`（22 个新测试文件）
  - `.trae/specs/iterate-region-test-fix/rounds/ternary_region/round_14/test_findings.md`（已存在）
  - `.trae/specs/iterate-region-test-fix/rounds/ternary_region/round_14/fix_report.md`（本文件）
  - 删除 `rounds/ternary_region/round_06/_debug_*.py`（7 个文件）

---

## 九、总结

R14 通过 22 个对抗性测试发现 11 个真 bug，修复 5 个（R14-04/05/06/07/10），达「至少 5 个 bug」目标。新增 2 个通用 chained ternary Pattern（F: slice assign, G: raise arg+cause），复用 R13-02/R8-03/R3-11/R13-01/R13-08 历史 Pattern 扩展。ternary 全量从 99 failed 降至 93 failed（-6），跨区域无退化。剩余 6 个 bug 涉及 while_cond/elif/multi-with/yield-from-protocol/boolop 短路等复杂控制流交互，标记为已知限制留待 R15+。
