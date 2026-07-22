# Ternary Region Round 07 — 测试发现报告

## 统计摘要

| 指标 | 数值 |
|------|------|
| R7 新增测试文件 | 32（22 主任务 + 10 变体追加） |
| R7 测试结果 | 11 failed / 21 passed / 0 skipped |
| R7 真实新 bug | 11（全部为对抗性新发现） |
| 通过率 | 21 / 32 = 65.6% |
| 全量 ternary 回归 | 70 failed / 223 passed / 1 skipped（294 测试，基线 59/202/1 → +11 failed / +21 passed / 0 退化） |
| 退化 | 0 个基线测试退化 |

### 与 R1-R6 累计对比

| 轮次 | 新增测试 | passed | failed | 累计 failed | 备注 |
|------|----------|--------|--------|-------------|------|
| R1 | 14 | 5 | 9 | 9 | 基础 if-exp 场景 |
| R2 | 28 | 11 | 17 | 26 | binop / collection / format |
| R3 | 15 | 9 | 6 | 32 | decorator / class / await |
| R4 | 13 | 5 | 8 | 40 | for / del / raise / kwargs |
| R5 | 22 | 12 | 10 | 57（含 3 已知限制） | chained compare / class body / while(ternary) |
| R6 | 22 | 9 | 13 | 70（含 3 R5 已知限制 + 13 R6 新 bug；R6 修复后净 59） | while(ternary) 新角度 + try/except + 推导式 + 闭包 + 装饰器 + 注解 |
| **R7** | **32** | **21** | **11** | **70（基线 59 + R7 新增 11）** | **finally 块 + async 控制流 + 语句位置 ternary（assert msg / raise / del obj）+ yield from + 嵌套 try** |

> R6 修复 10 个 bug 后基线为 59 failed / 202 passed / 1 skipped（262 测试）。R7 在此基线上新增 32 测试：11 fail / 21 pass，全量 ternary 回归 70 failed / 223 passed / 1 skipped（294 测试），即 59 + 11 = 70 failed、202 + 21 = 223 passed，**0 退化**。

## R7 与 R1-R6 的核心区别

1. **覆盖 finally 块 + 嵌套 try 全谱系**：R6 已修复 try body 与 except handler 内的 ternary（R6-06），但 finally 块的 ternary 处理仍是空白。R7 集中暴露 3 个 finally 相关 bug：纯 try-finally + ternary in finally（R7-05）、嵌套 try-finally + 内层 finally ternary（R7-07）、try-except-finally + finally ternary（R7-11）。3 个变体退化模式各不相同（R7-05 整体 try-finally → try-except 误转，R7-07 嵌套场景同模式，R7-11 ternary 出现在 try body 前缀 + finally 退化为 if-else 泄漏），说明 finally 路径的 ternary 归约完全未实现。
2. **覆盖 async 控制流 3 个新场景**：R6 仅测 async generator yield ternary（已通过）。R7 测 async with body ternary（R7-03，`as` 目标被错认）、async for body ternary（R7-02，ternary 完全退化为表达式泄漏）、async for-else ternary（R7-10，else + ternary 完全丢失，反编译出 `while True: pass` 幻影循环）。3 个场景都暴露 async 控制流的 SEND/GET_AWAITABLE polling 与 ternary merge 块归属冲突。
3. **覆盖语句位置 ternary 4 个新角度**：R7-01（assert msg ternary，反编译为 assert + raise (ternary)()）、R7-08（assert f(ternary) msg，反编译为 raise f(ternary)(AssertionError)）、R7-09（del (ternary)[idx]，del + subscript + ternary 全部丢失）、R7-04（del x[t1][t2] 双 ternary subscript，同上）。这 4 个场景都涉及 ternary merge 块后接非常规 STORE 消费（RAISE_VARARGS / DELETE_SUBSCR / LOAD_ASSERTION_ERROR + CALL），现有 `_try_build_ternary_store_assign` 与 `_build_ternary_no_target_consumer_stmt` 都未覆盖这些 consumer 模式。
4. **覆盖 yield from + 赋值变体**：R4 已测 yield from (ternary) 无赋值（已通过）。R7-06 测 `x = yield from (ternary)` 变体：GET_YIELD_FROM_ITER + SEND 循环后的 STORE_FAST x 与 ternary merge 块的 STORE 不同，使 ternary 退化为独立表达式 + yield from 只取 true_value（`yield from a` 而非 `yield from (a if c else b)`），暴露 yield from 子句的 ternary 归约缺失。
5. **不重复 R6 已知限制**：R6 留下 3 个已知限制（R6-01/04 while(ternary) 嵌套/复杂 body、R6-16 装饰器链）。R7 不再重复 while(ternary) 简单场景，仅 R7-15（3 层嵌套函数）作为新角度。R7 装饰器相关测试（classmethod / staticmethod / property）都通过，说明 R6-16 装饰器链问题在单装饰器场景不出现。

## R7 测试文件列表

| 序号 | 文件 | 状态 | bug ID |
|------|------|------|--------|
| 1 | `test_r7_ternary_in_for_else.py` | PASSED | — |
| 2 | `test_r7_ternary_in_while_else.py` | PASSED | — |
| 3 | `test_r7_ternary_in_try_else.py` | PASSED | — |
| 4 | `test_r7_ternary_in_try_finally.py` | PASSED | — |
| 5 | `test_r7_ternary_in_finally.py` | FAILED | R7-05 |
| 6 | `test_r7_ternary_in_with_body.py` | PASSED | — |
| 7 | `test_r7_ternary_in_with_multiple.py` | PASSED | — |
| 8 | `test_r7_ternary_in_async_with.py` | FAILED | R7-03 |
| 9 | `test_r7_ternary_in_async_for.py` | FAILED | R7-02 |
| 10 | `test_r7_ternary_in_class_method.py` | PASSED | — |
| 11 | `test_r7_ternary_in_class_attr.py` | PASSED | — |
| 12 | `test_r7_ternary_in_classmethod.py` | PASSED | — |
| 13 | `test_r7_ternary_in_staticmethod.py` | PASSED | — |
| 14 | `test_r7_ternary_in_property.py` | PASSED | — |
| 15 | `test_r7_ternary_in_nested_func_3level.py` | PASSED | — |
| 16 | `test_r7_ternary_in_yield_from_ternary.py` | FAILED | R7-06 |
| 17 | `test_r7_ternary_in_raise_from_complex.py` | PASSED | — |
| 18 | `test_r7_ternary_in_assert_msg.py` | FAILED | R7-01 |
| 19 | `test_r7_ternary_in_del_target_complex.py` | FAILED | R7-04 |
| 20 | `test_r7_ternary_in_global_complex.py` | PASSED | — |
| 21 | `test_r7_ternary_in_nonlocal_complex.py` | PASSED | — |
| 22 | `test_r7_ternary_in_import_test.py` | PASSED | — |
| 23 | `test_r7_ternary_in_nested_try_finally.py` | FAILED | R7-07 |
| 24 | `test_r7_ternary_in_async_with_as.py` | PASSED | — |
| 25 | `test_r7_ternary_in_yield_from_no_assign.py` | PASSED | — |
| 26 | `test_r7_ternary_in_del_attr_subscript.py` | PASSED | — |
| 27 | `test_r7_ternary_in_assert_complex_msg.py` | FAILED | R7-08 |
| 28 | `test_r7_ternary_in_del_obj_subscript.py` | FAILED | R7-09 |
| 29 | `test_r7_ternary_in_async_for_else.py` | FAILED | R7-10 |
| 30 | `test_r7_ternary_in_raise_no_from.py` | PASSED | — |
| 31 | `test_r7_ternary_in_try_except_finally_finally.py` | FAILED | R7-11 |
| 32 | `test_r7_ternary_in_async_yield.py` | PASSED | — |

---

## Bug 详细分析（11 个真实 bug）

### Bug R7-01: `assert x, (a if c else b)` — assert message ternary 丢失 + 错误添加 raise (ternary)() 调用

- **测试**：`test_r7_ternary_in_assert_msg.py`
- **状态**：FAILED
- **源码**：
  ```python
  assert x, (a if c else b)
  ```
- **反编译结果**：
  ```python
  assert x
  raise (a if c else b)()
  ```
- **问题分解**：
  1. assert 的 message 部分（ternary）完全丢失，反编译为单独 `assert x`。
  2. ternary 被错误地保留为独立 `raise (a if c else b)()` 语句。
  3. raise 的对象错误添加 `()` 调用（应为 `raise (a if c else b)` 而非 `raise (a if c else b)()`）。
  4. 整体语义错误：原代码仅在 `not x` 时抛 AssertionError(message=ternary)，反编译为总是抛 ternary()。
- **字节码对比**：
  - **原始（12 条，过滤跳转后）**：`RESUME, LOAD_NAME x, LOAD_ASSERTION_ERROR, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, PRECALL, CALL, RAISE_VARARGS, LOAD_CONST None, RETURN_VALUE`
  - **重编（16 条）**：`RESUME, LOAD_NAME x, LOAD_ASSERTION_ERROR, RAISE_VARARGS, PUSH_NULL, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, PRECALL, CALL, RAISE_VARARGS`
  - 差异：原始 `LOAD_ASSERTION_ERROR` 后直接 ternary merge + CALL（AssertionError(ternary)）；重编先 RAISE_VARARGS（无 cause）再独立 PUSH_NULL + ternary + CALL（独立 raise ternary()），指令数 12 → 16。
- **根因推测**：`_generate_assert` 在识别 `assert test, msg` 形态时，未识别 msg 位置的 TernaryRegion。ternary merge 块的 `LOAD_ASSERTION_ERROR + CALL + RAISE_VARARGS` 序列被识别为「独立 raise 表达式」，且 `()` 调用是反编译器对 raise (ternary) 的错误包裹（误把 ternary 当作 callable）。R4 的 `test_r4_ternary_in_assert`（ternary 在 test 位置）通过，说明 assert 的 test 位置 ternary 处理正常，但 message 位置 ternary 完全未实现归约。

### Bug R7-02: `async for x in ys: y = a if c else b` — async for body 中 ternary 完全退化为表达式泄漏 + 赋值丢失

- **测试**：`test_r7_ternary_in_async_for.py`
- **状态**：FAILED
- **源码**：
  ```python
  async def f():
      async for x in ys:
          y = a if c else b
  ```
- **反编译结果**：
  ```python
  async def f():
      async for x in ys:
          a
          b
  ```
- **问题分解**：
  1. ternary 完全未被识别为 IfExp AST 节点。
  2. true_value `a` 与 false_value `b` 退化为独立表达式语句泄漏。
  3. 赋值目标 `y` 完全丢失（无 STORE_FAST）。
  4. 条件 `c` 完全丢失（无 POP_JUMP_IF_FALSE）。
- **字节码对比**（嵌套 code object f）：
  - **原始（关键部分）**：`STORE_FAST x, LOAD_GLOBAL c, POP_JUMP_FORWARD_IF_FALSE 62, LOAD_GLOBAL a, JUMP_FORWARD 74, LOAD_GLOBAL b, STORE_FAST y, JUMP_BACKWARD 20, END_ASYNC_FOR`
  - **重编（关键部分）**：`STORE_FAST x, LOAD_GLOBAL a, POP_TOP, LOAD_GLOBAL b, POP_TOP, JUMP_BACKWARD 20, END_ASYNC_FOR`
  - 差异：原始 ternary 完整 `LOAD c → POP_JUMP → LOAD a → JUMP → LOAD b → STORE_FAST y`；重编丢失 `LOAD c/POP_JUMP/STORE_FAST y`，true/false value 退化为 `LOAD a/POP_TOP + LOAD b/POP_TOP`，赋值目标 y 丢失。
- **根因推测**：`_identify_loop_regions` 处理 async for 的 SEND/GET_AWAITABLE polling 路径时，未识别 body 内 TernaryRegion（async for body 块的归属判定与同步 for 不同，可能因 SEND 指令的存在让 region_analyzer 把 ternary merge 块误判为 polling 块）。ternary 退化为 `_generate_handler_body_statements` 类似的 if-else + 泄漏表达式路径（与 R6-06 修复前同模式），但 R6-06 修复在 `_generate_try_body` 内，未覆盖 async for body 路径。

### Bug R7-03: `async with ctx: y = a if c else b` — async with body ternary 的 STORE_FAST y 被误识别为 with 的 as 目标

- **测试**：`test_r7_ternary_in_async_with.py`
- **状态**：FAILED
- **源码**：
  ```python
  async def f():
      async with ctx:
          y = a if c else b
  ```
- **反编译结果**：
  ```python
  async def f():
      async with ctx as y: y = (a if c else b)
  ```
- **问题分解**：
  1. ternary 正确归约为 IfExp AST 节点（这点与 R7-02 不同）。
  2. ternary 的赋值目标 `y` 被错误地提升为 `async with ctx as y` 的 as 目标。
  3. body 内只剩 `y = (a if c else b)` 赋值（ternary 仍存在），但语义错乱：原本 ctx 不绑定到任何变量，反编译把 ctx 绑定到 y。
- **字节码对比**（嵌套 code object f）：
  - **原始（关键部分）**：`BEFORE_ASYNC_WITH, GET_AWAITABLE, SEND, ..., POP_TOP, LOAD_GLOBAL c, POP_JUMP, LOAD_GLOBAL a, JUMP, LOAD_GLOBAL b, STORE_FAST y, LOAD_CONST None, ..., PRECALL 2, CALL 2`
  - **重编（关键部分）**：`BEFORE_ASYNC_WITH, GET_AWAITABLE, SEND, ..., STORE_FAST y, LOAD_GLOBAL c, POP_JUMP, LOAD_GLOBAL a, JUMP, LOAD_GLOBAL b, STORE_FAST y, LOAD_CONST None, ..., PRECALL 2, CALL 2`
  - 差异：原始 `SEND` 后 `POP_TOP`（无 as 目标），ternary merge 后 `STORE_FAST y`；重编 `SEND` 后直接 `STORE_FAST y`（误识别为 as 目标），ternary merge 后再 `STORE_FAST y`（body 内的赋值）。
- **根因推测**：`_generate_with` 处理 async with 时，未正确识别 `as_target`。原始字节码 `POP_TOP` 表示无 as 目标，但反编译器把后续 body 内的 `STORE_FAST y`（ternary 的赋值目标）误识别为 with 的 as 目标。这是 with region 的 `as_target` 推断 bug，与 ternary 归约本身正确性无关，但导致 with 语句语义错乱。

### Bug R7-04: `del x[a if c else b][c if d else e]` — del + 双 subscript + 双 ternary 全部丢失

- **测试**：`test_r7_ternary_in_del_target_complex.py`
- **状态**：FAILED
- **源码**：
  ```python
  del x[a if c else b][c if d else e]
  ```
- **反编译结果**：
  ```python
  (a if c else b)
  (c if d else e)
  ```
- **问题分解**：
  1. del 语句结构完全丢失（无 DELETE_SUBSCR）。
  2. 两层 subscript 链（BINARY_SUBSCR）完全丢失。
  3. 两个 ternary 都正确归约为 IfExp 表达式（这点正确），但都退化为独立表达式语句泄漏（POP_TOP）。
  4. 整体语义完全错误：原代码删除 x[t1][t2]，反编译为两个独立表达式求值。
- **字节码对比**：
  - **原始（12 条）**：`RESUME, LOAD_NAME x, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, BINARY_SUBSCR, LOAD_NAME d, LOAD_NAME c, LOAD_NAME e, DELETE_SUBSCR, LOAD_CONST None, RETURN_VALUE`
  - **重编（14 条）**：`RESUME, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, POP_TOP, LOAD_NAME d, LOAD_NAME c, POP_TOP, LOAD_CONST None, RETURN_VALUE, LOAD_NAME e, POP_TOP, LOAD_CONST None, RETURN_VALUE`
  - 差异：原始 `LOAD x → t1 → BINARY_SUBSCR → t2 → DELETE_SUBSCR` 完整 del 链；重编丢失 `LOAD x/BINARY_SUBSCR/DELETE_SUBSCR`，两个 ternary 都退化为 `LOAD → POP_TOP`，且多出重复 `LOAD_CONST None + RETURN_VALUE`（两个独立表达式各自返回）。指令数 12 → 14。
- **根因推测**：`_generate_delete` 处理 `del x[t1][t2]` 嵌套 subscript 时，未识别 subscript 索引位置的 TernaryRegion。两个 ternary 都正确归约为 IfExp 表达式（说明 ternary region 识别正确），但 del 语句的 subscript 链未被构建，导致 ternary 表达式作为独立表达式语句泄漏。R4 的 `test_r4_ternary_in_del_target`（单层 del subscript ternary）通过，说明单层 subscript 处理正常，但嵌套两层 subscript 的 ternary 处理缺失。

### Bug R7-05: `try: pass\nfinally: y = a if c else b` — try-finally 被错误反编译为 try-except + ternary 重复出现

- **测试**：`test_r7_ternary_in_finally.py`
- **状态**：FAILED
- **源码**：
  ```python
  try:
      pass
  finally:
      y = a if c else b
  ```
- **反编译结果**：
  ```python
  y = (a if c else b)
  try:
      pass
  except (a if c else b): pass
  ```
- **问题分解**：
  1. try-finally 完全被错误反编译为 try-except（无 finally 关键字）。
  2. finally 块的 ternary 赋值被提前到 try 语句之前作为独立 `y = (a if c else b)` 语句。
  3. except 的异常类型被错误地设为 ternary 表达式（应为某个异常类，但反编译把 ternary 当作异常类型）。
  4. ternary 在反编译结果中出现两次（前缀赋值 + except 类型），但原代码只出现一次。
- **字节码对比**：
  - **原始（16 条）**：`RESUME, NOP, NOP, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, STORE_NAME y, LOAD_CONST None, RETURN_VALUE, PUSH_EXC_INFO, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, STORE_NAME y, RERAISE, COPY, POP_EXCEPT, RERAISE`
  - **重编（20 条）**：`RESUME, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, STORE_NAME y, NOP, LOAD_CONST None, RETURN_VALUE, PUSH_EXC_INFO, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, CHECK_EXC_MATCH, POP_TOP, POP_EXCEPT, LOAD_CONST None, RETURN_VALUE, RERAISE, COPY, POP_EXCEPT, RERAISE`
  - 差异：原始 finally 路径 `PUSH_EXC_INFO → ternary → STORE y → RERAISE`（finally 块在异常路径执行 ternary 赋值后重新抛出）；重编 try-except 路径 `PUSH_EXC_INFO → ternary → CHECK_EXC_MATCH → POP_TOP → POP_EXCEPT → RETURN`（把 ternary 当作异常类型匹配）。指令数 16 → 20。
- **根因推测**：`_generate_try` 处理纯 try-finally（无 except handlers）时，未正确识别 finally 块的入口与异常清理路径。finally 块的 ternary 赋值被识别为「try body 前的独立语句」+ 「except handler 的异常类型表达式」。R6-06 修复仅在 `_generate_try_body` 内跳过 handler 内的 TernaryRegion，但 finally 块的 ternary 归约路径完全未实现。这是 R6-06 修复的盲区。

### Bug R7-06: `def g(): x = yield from (a if c else b)` — ternary 退化为独立表达式 + yield from 只取 true_value

- **测试**：`test_r7_ternary_in_yield_from_ternary.py`
- **状态**：FAILED
- **源码**：
  ```python
  def g():
      x = yield from (a if c else b)
  ```
- **反编译结果**：
  ```python
  def g():
      (a if c else b)
      x = yield from a
  ```
- **问题分解**：
  1. ternary 部分归约（保留 IfExp 表达式），但作为独立表达式语句泄漏（POP_TOP）。
  2. yield from 只 yield from true_value `a`，而非整个 ternary 表达式。
  3. ternary 的 false_value `b` 完全丢失（无 LOAD_GLOBAL b 在 yield from 路径）。
  4. 整体语义错误：原代码 yield from (ternary)，反编译为先求值 ternary（丢弃结果）+ yield from a。
- **字节码对比**（嵌套 code object g）：
  - **原始（14 条）**：`RETURN_GENERATOR, POP_TOP, RESUME, LOAD_GLOBAL c, LOAD_GLOBAL a, LOAD_GLOBAL b, GET_YIELD_FROM_ITER, LOAD_CONST None, YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT, STORE_FAST x, LOAD_CONST None, RETURN_VALUE`
  - **重编（16 条）**：`RETURN_GENERATOR, POP_TOP, RESUME, LOAD_GLOBAL c, LOAD_GLOBAL a, LOAD_GLOBAL b, POP_TOP, LOAD_GLOBAL a, GET_YIELD_FROM_ITER, LOAD_CONST None, YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT, STORE_FAST x, LOAD_CONST None, RETURN_VALUE`
  - 差异：原始 ternary merge 后直接 `GET_YIELD_FROM_ITER`（ternary 整体作为 yield from 的 iterable）；重编 ternary merge 后 `POP_TOP`（丢弃 ternary 结果），再独立 `LOAD_GLOBAL a + GET_YIELD_FROM_ITER`（只 yield from true_value a）。指令数 14 → 16。
- **根因推测**：`_generate_yield_from` 处理 `yield from (ternary)` 时，未识别 ternary merge 块作为 yield from 的 iterable。ternary 的 merge 块后接 `GET_YIELD_FROM_ITER` 而非 `STORE_FAST`，未触发 `_try_build_ternary_store_assign` 的归约路径；ternary 退化为独立表达式（POP_TOP），yield from 的 iterable 错误地从 ternary true_value 块的 LOAD_GLOBAL a 取值。R4 的 `test_r4_ternary_in_yield_from`（无赋值变体）通过，但 R7-06 加 `x =` 赋值后暴露 yield from + STORE_FAST x 的复合归约缺失。

### Bug R7-07: 嵌套 try-finally + 内层 finally ternary — 同 R7-05 退化模式但 RERAISE 链嵌套

- **测试**：`test_r7_ternary_in_nested_try_finally.py`
- **状态**：FAILED
- **源码**：
  ```python
  try:
      try:
          pass
      finally:
          y = a if c else b
  except E:
      pass
  ```
- **反编译结果**：
  ```python
  try:
      y = (a if c else b)
      try:
          pass
      except (a if c else b): pass
  except E: pass
  ```
- **问题分解**：
  1. 内层 try-finally 被错误反编译为 try-except（同 R7-05）。
  2. 内层 finally 块的 ternary 赋值被提前到内层 try 之前作为独立语句。
  3. 内层 except 的异常类型被错误设为 ternary 表达式。
  4. ternary 在反编译结果中出现两次（前缀赋值 + except 类型），原代码只出现一次。
  5. 外层 try-except 结构正确（E 异常类型保留）。
- **字节码对比**：
  - **原始（27 条）**：`RESUME, NOP×3, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, STORE_NAME y, LOAD_CONST None, RETURN_VALUE, PUSH_EXC_INFO, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, STORE_NAME y, RERAISE, COPY, POP_EXCEPT, RERAISE, PUSH_EXC_INFO, LOAD_NAME E, CHECK_EXC_MATCH, POP_TOP, ...`
  - **重编（31 条）**：`RESUME, NOP, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, STORE_NAME y, NOP, LOAD_CONST None, RETURN_VALUE, PUSH_EXC_INFO, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, CHECK_EXC_MATCH, POP_TOP, POP_EXCEPT, LOAD_CONST None, RETURN_VALUE, RERAISE, COPY, POP_EXCEPT, RERAISE, PUSH_EXC_INFO, LOAD_NAME E, CHECK_EXC_MATCH, POP_TOP, ...`
  - 差异：与 R7-05 同模式（内层 try-finally → try-except 误转），但叠加外层 except E 路径，RERAISE 链嵌套两层。指令数 27 → 31。
- **根因推测**：与 R7-05 同根因（`_generate_try` 处理纯 try-finally 时 finally 块归约缺失），但 R7-07 在嵌套场景下叠加外层 except E 的 RERAISE 链，证明 finally 归约缺失在嵌套 try 结构中也存在，且退化模式一致。

### Bug R7-08: `assert x, f(a if c else b)` — assert f(ternary) message 丢失 + raise f(ternary)(AssertionError) 错误嵌套调用

- **测试**：`test_r7_ternary_in_assert_complex_msg.py`
- **状态**：FAILED
- **源码**：
  ```python
  assert x, f(a if c else b)
  ```
- **反编译结果**：
  ```python
  assert x
  raise f(a if c else b)(AssertionError)
  ```
- **问题分解**：
  1. assert 的 message 部分 f(ternary) 完全丢失，反编译为单独 `assert x`。
  2. f(ternary) 被错误保留为 `raise f(a if c else b)(AssertionError)` 独立语句。
  3. raise 的对象错误嵌套调用：`f(ternary)(AssertionError)`（先调用 f(ternary) 得到 callable，再调用 (AssertionError)），完全错乱。
  4. AssertionError 被错误地作为 f(ternary) 的调用参数，而非作为 raise 的异常类。
- **字节码对比**：
  - **原始（15 条）**：`RESUME, LOAD_NAME x, LOAD_ASSERTION_ERROR, PUSH_NULL, LOAD_NAME f, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, PRECALL, CALL, PRECALL, CALL, RAISE_VARARGS, LOAD_CONST None, RETURN_VALUE`
  - **重编（16 条）**：`RESUME, LOAD_NAME x, LOAD_ASSERTION_ERROR, RAISE_VARARGS, PUSH_NULL, PUSH_NULL, LOAD_NAME f, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, PRECALL, CALL, LOAD_NAME AssertionError, PRECALL, CALL, RAISE_VARARGS`
  - 差异：原始 `LOAD_ASSERTION_ERROR + PUSH_NULL + f + ternary + CALL` 然后 `PRECALL + CALL + RAISE_VARARGS`（AssertionError(f(ternary))）；重编先 `LOAD_ASSERTION_ERROR + RAISE_VARARGS`（独立 raise AssertionError），再 `PUSH_NULL + PUSH_NULL + f + ternary + CALL + AssertionError + CALL + RAISE_VARARGS`（f(ternary)(AssertionError) 嵌套调用）。指令数 15 → 16。
- **根因推测**：与 R7-01 同根因（assert message 位置 ternary 未识别），但 R7-08 的 message 是 `f(ternary)` 调用，使反编译器的 `()` 调用错误包裹与原有的 f() 调用嵌套，产生 `f(ternary)(AssertionError)` 双重调用。证明 R7-01 的 `()` 调用错误包裹在嵌套调用场景下会放大。

### Bug R7-09: `del (a if c else b)[idx]` — del + subscript + ternary 全部丢失，ternary 退化为泄漏 + 错误分支结构

- **测试**：`test_r7_ternary_in_del_obj_subscript.py`
- **状态**：FAILED
- **源码**：
  ```python
  del (a if c else b)[idx]
  ```
- **反编译结果**：
  ```python
  (a if c else b)
  ```
- **问题分解**：
  1. del 语句结构完全丢失（无 DELETE_SUBSCR）。
  2. subscript 索引 `idx` 完全丢失（无 LOAD_NAME idx）。
  3. ternary 部分归约（保留 IfExp 表达式），但作为独立表达式语句泄漏。
  4. ternary 的 false_value `b` 路径完全脱离主控制流（重编字节码中 b 在第二个 RETURN_VALUE 之后，不可达）。
- **字节码对比**：
  - **原始（8 条）**：`RESUME, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, LOAD_NAME idx, DELETE_SUBSCR, LOAD_CONST None, RETURN_VALUE`
  - **重编（10 条）**：`RESUME, LOAD_NAME c, LOAD_NAME a, POP_TOP, LOAD_CONST None, RETURN_VALUE, LOAD_NAME b, POP_TOP, LOAD_CONST None, RETURN_VALUE`
  - 差异：原始 ternary merge 后 `LOAD idx + DELETE_SUBSCR`；重编 ternary 退化为 `LOAD c → a → POP_TOP → RETURN` + `b → POP_TOP → RETURN`（两个独立分支各自返回），完全丢失 `LOAD idx/DELETE_SUBSCR`。指令数 8 → 10。
- **根因推测**：与 R7-04 同根因（`_generate_delete` 处理 subscript 链时未识别 ternary），但 R7-09 的 ternary 在 base 对象位置（del (ternary)[idx]）而非索引位置。ternary 的 merge 块后接 `LOAD idx + DELETE_SUBSCR`，但反编译器把 ternary 退化为独立表达式 + 双 RETURN 分支结构。R7-04 的两层 subscript 索引都是 ternary 也丢失 del 结构，R7-09 证明 base 是 ternary 同样丢失 del 结构，说明 del + 任意位置 ternary 都未实现归约。

### Bug R7-10: `async for-else: y = a if c else b` — else 块 + ternary 完全丢失，反编译出 `while True: pass` 幻影循环

- **测试**：`test_r7_ternary_in_async_for_else.py`
- **状态**：FAILED
- **源码**：
  ```python
  async def f():
      async for x in ys:
          pass
      else:
          y = a if c else b
  ```
- **反编译结果**：
  ```python
  async def f():
      async for x in ys:
          while True:
              pass
  ```
- **问题分解**：
  1. async for-else 的 else 块完全丢失（无 `y = a if c else b`）。
  2. ternary 完全丢失（无 IfExp）。
  3. async for body 内反编译出 `while True: pass` 幻影循环（原 body 是 `pass`）。
  4. 赋值目标 `y` 完全丢失。
- **字节码对比**（嵌套 code object f）：
  - **原始（关键部分）**：`STORE_FAST x, JUMP_BACKWARD 20, END_ASYNC_FOR, LOAD_GLOBAL c, POP_JUMP, LOAD_GLOBAL a, JUMP, LOAD_GLOBAL b, STORE_FAST y, LOAD_CONST None, RETURN_VALUE`
  - **重编（关键部分）**：`STORE_FAST x, NOP, NOP, JUMP_BACKWARD 36, END_ASYNC_FOR, LOAD_CONST None, RETURN_VALUE`
  - 差异：原始 `END_ASYNC_FOR` 后是 else 块 `LOAD c → POP_JUMP → LOAD a → JUMP → LOAD b → STORE_FAST y → RETURN`；重编 `END_ASYNC_FOR` 后直接 `LOAD_CONST None + RETURN_VALUE`（else 块完全丢失），且 async for body 内多出 `NOP + NOP + JUMP_BACKWARD 36`（反编译出幻影 `while True: pass`）。
- **根因推测**：`_identify_loop_regions` 处理 async for-else 时，未识别 else 块的入口（END_ASYNC_FOR 后的块）。else 块的 ternary 赋值完全丢失，且 async for body 内的空 `pass` 被错误识别为 `while True: pass` 幻影循环（可能是 SEND polling 块的 JUMP_BACKWARD 被误识别为 while 循环）。R7-02（async for body ternary）也暴露 async for 处理 bug，R7-10 证明 async for-else 的 else 块归约也完全缺失。

### Bug R7-11: `try-except-finally + finally ternary` — ternary 出现在 try body 前缀 + finally 块退化为 if-else 泄漏

- **测试**：`test_r7_ternary_in_try_except_finally_finally.py`
- **状态**：FAILED
- **源码**：
  ```python
  try:
      pass
  except E:
      pass
  finally:
      y = a if c else b
  ```
- **反编译结果**：
  ```python
  try:
      y = (a if c else b)
  except E: pass
  finally:
      if c:
          a
      else:
          b
  ```
- **问题分解**：
  1. finally 块的 ternary 赋值被提前到 try body 内作为独立 `y = (a if c else b)` 语句（与 R7-05 同模式）。
  2. finally 块本身退化为 `if c: a\nelse: b`（ternary 退化为 if-else + 表达式泄漏）。
  3. ternary 在反编译结果中出现两次（try body 内的 IfExp 赋值 + finally 块内的 if-else 泄漏），原代码只出现一次。
  4. finally 块的赋值目标 `y` 完全丢失（finally 块内只有 `a`/`b` 表达式，无 `y =`）。
- **字节码对比**：
  - **原始（25 条，关键部分）**：`RESUME, NOP, JUMP_FORWARD 28, PUSH_EXC_INFO, LOAD_NAME E, CHECK_EXC_MATCH, ..., RERAISE, COPY, POP_EXCEPT, RERAISE, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, STORE_NAME y, LOAD_CONST None, RETURN_VALUE, PUSH_EXC_INFO, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, STORE_NAME y, RERAISE, ...`
  - **重编（34 条，关键部分）**：`RESUME, NOP, LOAD_NAME c, LOAD_NAME a, LOAD_NAME b, STORE_NAME y, JUMP_FORWARD 40, PUSH_EXC_INFO, LOAD_NAME E, CHECK_EXC_MATCH, ..., RERAISE, COPY, POP_EXCEPT, RERAISE, LOAD_NAME c, LOAD_NAME a, POP_TOP, LOAD_CONST None, RETURN_VALUE, LOAD_NAME b, POP_TOP, LOAD_CONST None, RETURN_VALUE, PUSH_EXC_INFO, LOAD_NAME c, LOAD_NAME a, POP_TOP, RERAISE, LOAD_NAME b, POP_TOP, RERAISE, ...`
  - 差异：原始 finally 路径 `PUSH_EXC_INFO → ternary → STORE y → RERAISE`；重编 try body 内多出 `LOAD c → ternary → STORE y`（前缀赋值），finally 块退化为 `LOAD c → a → POP_TOP → RETURN` + `b → POP_TOP → RETURN`（if-else + 泄漏），且 finally 异常路径 `LOAD c → a → POP_TOP → RERAISE + b → POP_TOP → RERAISE`（同样退化）。指令数 25 → 34。
- **根因推测**：与 R7-05/R7-07 同根因（`_generate_try` 处理 finally 块的 ternary 归约缺失），但 R7-11 是 try-except-finally 三段结构，退化模式与 R7-05（纯 try-finally）不同：R7-05 整体 try-finally → try-except 误转，R7-11 保持 try-except-finally 结构正确，但 finally 块内 ternary 退化为 if-else + 泄漏。说明 finally 路径的 ternary 归约在不同 try 结构下退化模式不同，需要分别修复。

---

## 错误模式归类

### 模式 A：finally 块 ternary 归约完全缺失（3 个 bug，最高优先级）

- **涉及 bug**：R7-05、R7-07、R7-11
- **共同特征**：finally 块包含 ternary 赋值时，反编译器完全未实现归约路径。
- **退化模式差异**：
  - R7-05（纯 try-finally）：整体 try-finally → try-except 误转，ternary 在前缀 + except 类型重复出现。
  - R7-07（嵌套 try-finally）：内层 try-finally → try-except 误转（同 R7-05），外层 except E 路径正确。
  - R7-11（try-except-finally）：try-except-finally 结构正确，但 finally 块内 ternary 退化为 if-else + 表达式泄漏，且 ternary 在 try body 前缀重复出现。
- **根因**：`_generate_try` 处理 finally 块时，未识别 finally body 内的 TernaryRegion。R6-06 修复仅覆盖 except handler 内的 ternary（通过 `handler_entry_blocks` + `except_handlers[i][2]` 预收集），未覆盖 `finally_blocks` 内的 ternary。R6-06 修复的 `_r6_06_handler_block_set` 包含 `region.finally_blocks`，但仅用于 `_generate_try_body` 跳过，未在 finally body 遍历路径中调用 `_generate_ternary` 归约。
- **修复建议**：在 `_generate_try` 的 finally body 遍历路径（与 handler body 遍历 L11715-11731 类似）中，通过 `get_entry_region_for_block` 识别 TernaryRegion 并调用 `_generate_region` 归约为 IfExp。这是 R6-06 修复的延伸，可一次性解决 3 个 finally 相关 bug。

### 模式 B：async 控制流 ternary 归约缺失（3 个 bug，高优先级）

- **涉及 bug**：R7-02（async for body）、R7-03（async with body）、R7-10（async for-else）
- **共同特征**：ternary 在 async 控制流（async for / async with）的 body / else 块中时，归约完全缺失或部分错误。
- **退化模式差异**：
  - R7-02（async for body）：ternary 完全退化为 `a\nb` 表达式泄漏 + 赋值丢失。
  - R7-03（async with body）：ternary 正确归约为 IfExp，但赋值目标 y 被误识别为 with 的 as 目标。
  - R7-10（async for-else）：else 块 + ternary 完全丢失，async for body 内反编译出 `while True: pass` 幻影循环。
- **根因**：`_identify_loop_regions` 处理 async for / async with 的 SEND/GET_AWAITABLE polling 路径时，未识别 body / else 块内的 TernaryRegion。async 控制流的 SEND 指令让 region_analyzer 把 ternary merge 块误判为 polling 块。R6-06 修复仅在同步 try 路径，未覆盖 async 控制流路径。
- **修复建议**：在 `_identify_loop_regions` 中区分 async for / async with 的 polling 块与 body 内的 ternary merge 块。R7-03 的 `as_target` 误识别需在 `_generate_with` 的 async with 路径中单独修复。

### 模式 C：语句位置 ternary consumer 未识别（4 个 bug，中优先级）

- **涉及 bug**：R7-01（assert msg）、R7-04（del 双 subscript ternary）、R7-08（assert f(ternary) msg）、R7-09（del (ternary)[idx]）
- **共同特征**：ternary merge 块后接非常规 STORE 消费（RAISE_VARARGS / DELETE_SUBSCR / LOAD_ASSERTION_ERROR + CALL），现有 `_try_build_ternary_store_assign` 与 `_build_ternary_no_target_consumer_stmt` 都未覆盖这些 consumer 模式。
- **退化模式差异**：
  - R7-01 / R7-08（assert msg）：assert message 位置 ternary 完全丢失，反编译为独立 `raise (ternary)()` 或 `raise f(ternary)(AssertionError)` 错误嵌套调用。
  - R7-04 / R7-09（del subscript）：del 语句结构 + subscript 链完全丢失，ternary 退化为独立表达式泄漏。
- **根因**：`_build_ternary_no_target_consumer_stmt` 的 consumer 识别列表未包含 `RAISE_VARARGS`（assert message 路径）与 `DELETE_SUBSCR`（del subscript 路径）。`_generate_assert` 与 `_generate_delete` 也未调用 `_generate_ternary` 归约 merge 块内的 ternary。
- **修复建议**：扩展 `_build_ternary_no_target_consumer_stmt` 的 consumer 识别列表，新增 `RAISE_VARARGS`（assert message）与 `DELETE_SUBSCR`（del subscript）模式。同时在 `_generate_assert` 与 `_generate_delete` 中调用 `_generate_ternary` 归约 merge 块内的 ternary。

### 模式 D：yield from + 赋值复合归约缺失（1 个 bug，中优先级）

- **涉及 bug**：R7-06
- **共同特征**：ternary merge 块后接 `GET_YIELD_FROM_ITER + SEND + STORE_FAST x`（yield from (ternary) + 赋值），现有归约路径未覆盖。
- **退化模式**：ternary 退化为独立表达式（POP_TOP）+ yield from 只取 true_value（`yield from a` 而非 `yield from (a if c else b)`）。
- **根因**：`_generate_yield_from` 处理 `yield from (ternary) + STORE_FAST x` 复合模式时，未识别 ternary merge 块作为 yield from 的 iterable。ternary merge 块后接 `GET_YIELD_FROM_ITER` 而非 `STORE_FAST`，未触发 `_try_build_ternary_store_assign`；`_build_ternary_no_target_consumer_stmt` 也未识别 `GET_YIELD_FROM_ITER` 作为 consumer。
- **修复建议**：在 `_generate_yield_from` 中识别 ternary merge 块作为 iterable，调用 `_generate_ternary` 归约。或在 `_build_ternary_no_target_consumer_stmt` 中新增 `GET_YIELD_FROM_ITER` consumer 模式。

---

## 修复优先级建议

| 优先级 | Bug | 修复方向 | 预期收益 |
|--------|-----|----------|----------|
| P0（最高） | R7-05 / R7-07 / R7-11 | 在 `_generate_try` 的 finally body 遍历路径中调用 `_generate_ternary` 归约（R6-06 修复延伸） | 一次性修复 3 个 finally 相关 bug，复用 R6-06 修复模式 |
| P1（高） | R7-02 / R7-10 | 在 `_identify_loop_regions` 中区分 async for 的 polling 块与 body / else 块内的 ternary merge 块 | 修复 2 个 async for 相关 bug |
| P1（高） | R7-03 | 在 `_generate_with` 的 async with 路径中修正 `as_target` 推断（POP_TOP 表示无 as 目标） | 修复 1 个 async with 相关 bug |
| P2（中） | R7-01 / R7-08 | 在 `_generate_assert` 中调用 `_generate_ternary` 归约 message 位置的 ternary；移除 `()` 调用错误包裹 | 修复 2 个 assert message 相关 bug |
| P2（中） | R7-04 / R7-09 | 在 `_generate_delete` 中识别 subscript 链内的 ternary；扩展 `_build_ternary_no_target_consumer_stmt` 新增 `DELETE_SUBSCR` consumer | 修复 2 个 del subscript 相关 bug |
| P3（中低） | R7-06 | 在 `_generate_yield_from` 中识别 ternary merge 块作为 iterable | 修复 1 个 yield from + 赋值复合 bug |

---

## 与 R1-R6 的区别

1. **覆盖 finally 块全谱系（R6 盲区）**：R6 修复了 try body 与 except handler 内的 ternary（R6-06），但 finally 块的 ternary 处理完全是空白。R7 集中暴露 3 个 finally 相关 bug（R7-05 / R7-07 / R7-11），证明 R6-06 修复的 `_r6_06_handler_block_set` 虽包含 `finally_blocks`，但仅用于 `_generate_try_body` 跳过，未在 finally body 遍历路径中调用 `_generate_ternary` 归约。
2. **覆盖 async 控制流 3 个新场景（R6 仅测 async gen yield）**：R6 的 async 测试仅 `test_r6_ternary_async_gen`（async generator yield ternary，已通过）。R7 测 async with body / async for body / async for-else 三个新场景，全部失败，证明 async 控制流的 SEND/GET_AWAITABLE polling 路径与 ternary merge 块归属冲突完全未处理。
3. **覆盖语句位置 ternary consumer 4 个新角度（R4 部分覆盖）**：R4 已测 `assert (ternary), "msg"`（ternary 在 test 位置，通过）、`raise E from (ternary)`（ternary 在 cause 位置，通过）、`del x[ternary]`（单层 subscript ternary，通过）。R7 测 4 个新角度：`assert x, (ternary)`（message 位置）、`assert x, f(ternary)`（message 是 f(ternary) 调用）、`del x[t1][t2]`（两层 subscript 都是 ternary）、`del (ternary)[idx]`（base 是 ternary）。4 个新角度全部失败，证明语句位置 ternary consumer 识别在 assert message / del 嵌套 subscript / del base 位置完全缺失。
4. **覆盖 yield from + 赋值复合变体（R4 部分覆盖）**：R4 已测 `yield from (ternary)` 无赋值（通过）。R7 测 `x = yield from (ternary)` 加赋值变体，失败，证明 yield from + STORE_FAST x 的复合归约缺失。
5. **不重复 R6 已知限制**：R6 留下 3 个已知限制（R6-01/04 while(ternary) 嵌套/复杂 body、R6-16 装饰器链）。R7 不再重复 while(ternary) 简单场景，仅 `test_r7_ternary_in_nested_func_3level.py`（3 层嵌套函数）作为新角度（通过）。R7 装饰器相关测试（classmethod / staticmethod / property / 单装饰器）都通过，说明 R6-16 装饰器链问题仅在多装饰器链场景出现，单装饰器场景不出现。
6. **R7 通过率高（65.6%）说明 R1-R6 修复有效**：R7 通过率 21/32 = 65.6%，高于 R6（9/22 = 40.9%）与 R5（12/22 = 54.5%）。说明 R6 修复（特别是 R6-06 的 try body / handler 内 ternary 归约）对 R7 的新场景有泛化效果：for-else / while-else / try-else / try-finally body / with body / with multiple / class method / class attr / classmethod / staticmethod / property / 3-level nested func / raise from complex / global / nonlocal / import / async with as / yield from no assign / del attr subscript / raise no from / async yield 等 21 个场景都通过。失败集中在 4 个全新盲区：finally 块、async for/with body、assert message、del 嵌套 subscript。

## 算法 4 原则核查（针对 R7 失败 bug）

R7 的 11 个失败 bug 都违反「每块唯一归属」原则，但违反位置不同：

1. **finally 块 ternary（R7-05 / R7-07 / R7-11）**：TernaryRegion 的块（entry + true/false/merge）应归属到 finally body（TryFinally 子节点），但被错误归属到 try body 前缀（独立语句）+ except handler（异常类型）或 finally body 内退化为 if-else。违反「每块唯一归属」+「嵌套即抽象节点」。
2. **async 控制流 ternary（R7-02 / R7-03 / R7-10）**：TernaryRegion 的块应归属到 async for body / async with body / async for-else 块，但被错误归属到 SEND polling 块（R7-02 退化为泄漏）/ with as_target（R7-03 误识别）/ 完全丢失（R7-10）。违反「每块唯一归属」+「父引用子入口」。
3. **语句位置 ternary consumer（R7-01 / R7-04 / R7-08 / R7-09）**：TernaryRegion 的 merge 块后接非常规 STORE（RAISE_VARARGS / DELETE_SUBSCR），应被识别为 assert message / del subscript 的 consumer，但被错误归约为独立 raise 表达式（R7-01 / R7-08）或独立表达式泄漏（R7-04 / R7-09）。违反「嵌套即抽象节点」+「父引用子入口」。
4. **yield from + 赋值复合（R7-06）**：TernaryRegion 的 merge 块后接 `GET_YIELD_FROM_ITER`，应被识别为 yield from 的 iterable，但被错误归约为独立表达式（POP_TOP）+ yield from 只取 true_value。违反「嵌套即抽象节点」+「父引用子入口」。
