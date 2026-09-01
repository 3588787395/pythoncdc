# TERNARY 区域 Round 20 测试发现报告

## 基线

**测试命令：**
```bash
timeout 280 python -m pytest tests/exhaustive/ternary/ -q --tb=no
```

**R20 前基线（R1-R19 现有测试）：**
```
43 failed, 529 passed, 9 skipped in 5.41s
```

**R20 后基线（加入 16 个新测试后）：**
```
59 failed, 529 passed, 9 skipped in 5.56s
```

新增 16 个真实失败（43 → 59，增量 +16），全部为新发现的 TERNARY 区域反编译缺陷，与 R1-R19 现有测试无重复（已逐一比对 SOURCE_CODE 与现有测试的消费者上下文差异）。

---

## 真实失败 Bug 清单（共 16 个）

### Bug R20-01: 双 walrus + 嵌套 ternary in cond

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_walrus_in_cond.py`
- **源码：**
  ```python
  x = (n := a) if (m := b if c else d) else e
  ```
- **失败现象：** 反编译退化为 `if (m := b if c else d): pass`，丢失外层三元的 body `(n := a)` 与 orelse `e`。
- **失败指令对比：**
  - 原始 (13): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'COPY', 'STORE_NAME', 'LOAD_NAME', 'COPY', 'STORE_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (10): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'COPY', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** ternary 的条件本身是 walrus 表达式 `(m := (b if c else d))`，内含嵌套 ternary。`_detect_ternary_context` 把 cond_block 的 COPY+STORE m 误识为外层三元的 value_target，导致 walrus(嵌套ternary) 的归约吞掉了外层三元的 body/orelse 分支。外层 `_generate_ternary` 的 cond 重建与 walrus 的 COPY 消费链归属冲突。

---

### Bug R20-02: walrus(ternary) 作 subscript 赋值目标（store）

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_walrus_subscr_assign.py`
- **源码：**
  ```python
  x[(n := a if c else b)] = y
  ```
- **失败现象：** 反编译退化为 `n = (a if c else b)`，丢失外层 LOAD x / LOAD y / STORE_SUBSCR。
- **失败指令对比：**
  - 原始 (11): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'COPY', 'STORE_NAME', 'STORE_SUBSCR', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (7): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** R16 测过 `x[(n := a if c else b)]`（LOAD/BINARY_SUBSCR 消费，表达式语句），本用例是 STORE 上下文。`_try_build_ternary_store_assign` 把 walrus 的 COPY+STORE n 当成独立赋值目标，未识别 STORE_SUBSCR 是真正的消费指令，外层 LOAD x / LOAD y / STORE_SUBSCR 整条栈消费链丢失。

---

### Bug R20-03: walrus(ternary) 作属性赋值 RHS

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_walrus_attr_assign.py`
- **源码：**
  ```python
  obj.attr = (n := a if c else b)
  ```
- **失败现象：** 反编译退化为 `n = (a if c else b)` + `obj.attr = None`，walrus 的 COPY 被误识为独立 STORE。
- **失败指令对比：**
  - 原始: `[..., 'LOAD_NAME', 'LOAD_NAME', 'COPY', 'STORE_NAME', 'LOAD_NAME', 'STORE_ATTR']`
  - 重编: `[..., 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'LOAD_NAME', 'STORE_ATTR']`
  - 指令4操作码不匹配: COPY vs STORE_NAME
- **根因初步分析：** 属性赋值 `obj.attr = RHS` 的 RHS 是 walrus(ternary)。`_generate_ternary` 输出 walrus 的 STORE n 后，外层 `_try_build_ternary_store_assign` 未把 ternary merge 块栈顶关联到 STORE_ATTR 的 value 槽位，而是用 None 占位。walrus 的 COPY 与 STORE_ATTR value 的栈关联断裂。

---

### Bug R20-04: starred 展开含标量 ternary 的 list literal

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_starred_list_scalar.py`
- **源码：**
  ```python
  x = [*[a if c else b]]
  ```
- **失败现象：** 反编译退化为 `x = [a if c else b]`，丢失内层 BUILD_LIST 与 LIST_EXTEND。
- **失败指令对比：**
  - 原始 (10): `['RESUME', 'BUILD_LIST', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_LIST', 'LIST_EXTEND', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (8): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_LIST', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** R1 测过 `x = [*(items if cond else [])]`（ternary 直接产出可迭代对象，无内层 BUILD_LIST 包装）。本用例 ternary 产出标量，需 BUILD_LIST 1 包装成 `[ternary]` 再 LIST_EXTEND 展开到外层 list。`_try_build_ternary_chained_container` 只识别 ternary 直接作 LIST_EXTEND 源的情况，未处理 ternary 被 BUILD_LIST 1 包装后再 LIST_EXTEND 的双层容器结构。

---

### Bug R20-05: starred 展开含 ternary 的 list 进 tuple

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_starred_tuple_list.py`
- **源码：**
  ```python
  x = (*[a if c else b],)
  ```
- **失败现象：** 反编译退化为 `x = (a if c else b,)`，丢失 BUILD_LIST/LIST_EXTEND/LIST_TO_TUPLE。
- **失败指令对比：**
  - 原始 (11): `['RESUME', 'BUILD_LIST', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_LIST', 'LIST_EXTEND', 'LIST_TO_TUPLE', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (8): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_TUPLE', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** tuple literal `(*[ternary],)` 通过 * 展开含标量 ternary 的 list literal。`BUILD_LIST 0` + ternary merge + `BUILD_LIST 1` + `LIST_EXTEND` + `LIST_TO_TUPLE` 消费链中，`_try_build_ternary_chained_container` 未识别 LIST_TO_TUPLE 作为最终消费，且未重建内层 BUILD_LIST 包装，直接退化为 BUILD_TUPLE。

---

### Bug R20-06: dict double-star 展开含 ternary key 的 dict literal

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_dict_double_star_literal.py`
- **源码：**
  ```python
  x = {**{a if c else b: 1}}
  ```
- **失败现象：** 反编译退化为 `x = {a if c else b: 1}`，丢失外层 BUILD_MAP/DICT_UPDATE。
- **失败指令对比：**
  - 原始 (11): `['RESUME', 'BUILD_MAP', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'BUILD_MAP', 'DICT_UPDATE', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (9): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'BUILD_MAP', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** R17 测过 `x = {**d, **(a if c else b)}`（ternary 直接产出被展开的 dict，无内层 BUILD_MAP 包装）。本用例 ternary 是内层 dict 的 key：外层 `BUILD_MAP 0` + ternary merge + `LOAD_CONST 1` + `BUILD_MAP 1`（内层 dict 消费 ternary key）+ `DICT_UPDATE`（展开内层到外层）。`_try_build_ternary_chained_container` 未处理 DICT_UPDATE 作为消费指令的双层 dict 结构。

---

### Bug R20-07: starred 展开含 ternary 的 list literal 进 call *args

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_starred_call_list.py`
- **源码：**
  ```python
  f(*[a if c else b])
  ```
- **失败现象：** 反编译退化为 `f(a if c else b)`，走 PRECALL+CALL 而非 CALL_FUNCTION_EX。
- **失败指令对比：**
  - 原始: `['LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_LIST', 'CALL_FUNCTION_EX', 'POP_TOP', 'LOAD_CONST']`
  - 重编: `['LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'PRECALL', 'CALL', 'POP_TOP', 'LOAD_CONST']`
  - 指令6操作码不匹配: BUILD_LIST vs PRECALL
- **根因初步分析：** R8 测过 `f(*(a if c else b))`（ternary 直接产出可迭代对象被 unpack，无内层 BUILD_LIST 包装）。本用例 ternary 产出标量，需 BUILD_LIST 1 包装成 `[ternary]` 再 CALL_FUNCTION_EX unpack。`_try_build_ternary_merge_consumer_expr` 未识别 CALL_FUNCTION_EX 路径下 ternary 被 BUILD_LIST 包装的情况，错误地走 PRECALL+CALL 重建。

---

### Bug R20-08: pos arg 在 starred-list-ternary 前后

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_starred_call_pos_before_after.py`
- **源码：**
  ```python
  f(1, *[a if c else b], 2)
  ```
- **失败现象：** 反编译退化为 `f(1, a if c else b, 2)`，走 PRECALL+CALL。
- **失败指令对比：**
  - 原始 (17): `['RESUME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'BUILD_LIST', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_LIST', 'LIST_EXTEND', 'LOAD_CONST', 'LIST_APPEND', 'LIST_TO_TUPLE', 'CALL_FUNCTION_EX', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (13): `['RESUME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** R18 测过 `f(*(a if c else b), other)`（starred-ternary 在前，单个 pos arg 在后，且 starred 是直接 ternary 非 list）。本用例 pos arg 在 starred 前后均有，且 starred 是 list literal 含 ternary。CALL_FUNCTION_EX 路径需 `BUILD_LIST 0` + `LIST_APPEND`(pos 1) + ternary merge + `BUILD_LIST 1` + `LIST_EXTEND` + `LIST_APPEND`(pos 2) + `LIST_TO_TUPLE`。多元素 LIST_APPEND/LIST_EXTEND 交错与 ternary merge 块归属协调失败。

---

### Bug R20-09: 赋值 RHS 是两 ternary 的 boolop AND

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_boolop_and_two_assign.py`
- **源码：**
  ```python
  x = (a if c else b) and (d if e else f)
  ```
- **失败现象：** 反编译把两个 ternary 拆成独立语句 `x = (d if e else f)` + `(a if c else b)`，丢失 JUMP_IF_FALSE_OR_POP 短路与 and 结构。
- **失败指令对比：**
  - 原始 (11): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'JUMP_IF_FALSE_OR_POP', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (14): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_NAME', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** R14 测过 `assert (ternary) and (ternary)`（assert 上下文，RAISE_VARARGS 消费）。本用例是赋值上下文：`JUMP_IF_FALSE_OR_POP` 短路 + 第二个 ternary merge + `STORE_NAME x`。`_try_build_ternary_boolop_and_if` 只处理 assert/raise 上下文的 boolop，未处理赋值上下文下 BoolOp(IfExp, IfExp) 作为 STORE value 的情况，两个 ternary 被独立归约为语句。

---

### Bug R20-10: 赋值 RHS 是两 ternary 的 boolop OR

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_boolop_or_two_assign.py`
- **源码：**
  ```python
  x = (a if c else b) or (d if e else f)
  ```
- **失败现象：** 反编译把两个 ternary 拆成独立语句 `x = (d if e else f)` + `(a if c else b)`，丢失 JUMP_IF_TRUE_OR_POP 短路与 or 结构。
- **失败指令对比：**
  - 原始 (11): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'JUMP_IF_TRUE_OR_POP', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (14): `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_NAME', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** 与 R20-09 同源，OR 变体。`_try_build_ternary_boolop_and_if` 未覆盖赋值上下文下 BoolOp(Or, [IfExp, IfExp]) 作为 STORE value。

---

### Bug R20-11: yield from binop(两 ternary)

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_yield_from_binop_two.py`
- **源码：**
  ```python
  def f():
      yield from (a if c else b) + (d if e else f)
  ```
- **失败现象：** 反编译把第一个 ternary 拆成独立语句 `(a if c else b)`，yield from 只保留第二个 ternary，丢失 BINARY_OP 与第一个 ternary 的栈关联。
- **失败指令对比：**
  - 原始: `['LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'BINARY_OP', ...]`
  - 重编: `['LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'POP_TOP', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', ...]`
  - 指令6操作码不匹配: LOAD_GLOBAL vs POP_TOP
- **根因初步分析：** R7/R13 测过 `yield from (ternary)`（单一 ternary 直接作 yield from 目标）。本用例 `yield from (ternary + ternary)`：第一个 ternary merge 块栈顶 + 第二个 ternary merge 块栈顶 + BINARY_OP + GET_YIELD_FROM_ITER。`_try_build_ternary_merge_consumer_expr` 未处理 yield from 上下文下两个 ternary 通过 BINARY_OP 组合的情况，第一个 ternary 被误识为独立表达式语句（POP_TOP 丢弃）。

---

### Bug R20-12: yield from 方法调用 on ternary

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_yield_from_method_on.py`
- **源码：**
  ```python
  def f():
      yield from (a if c else b).m()
  ```
- **失败现象：** 反编译完全丢失 ternary 与方法调用，退化为 `def f(): None`。
- **失败指令对比：**
  - 原始 (17): `['RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_METHOD', 'PRECALL', 'CALL', 'GET_YIELD_FROM_ITER', 'LOAD_CONST', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (3): `['RESUME', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** yield from 的表达式是 ternary 上的方法调用 `(ternary).m()`。ternary merge 块栈顶 + LOAD_METHOD m + PRECALL + CALL + GET_YIELD_FROM_ITER + SEND 循环。`_generate_ternary` 在生成器函数（RETURN_GENERATOR 前导）上下文下完全未识别 ternary region，反编译输出空函数体。generator 的 RETURN_GENERATOR + JUMP_BACKWARD_NO_INTERRUPT 轮询结构与 ternary region 归约冲突。

---

### Bug R20-13: assert msg 是两 ternary 的 binop

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_assert_msg_binop_two.py`
- **源码：**
  ```python
  assert x, (a if c else b) + (d if e else f)
  ```
- **失败现象：** 反编译退化为 `assert x, e` + `raise (d if e else f)()`，把第二个 ternary 误识为 raise 调用。
- **失败指令对比：**
  - 原始 (15): `['RESUME', 'LOAD_NAME', 'LOAD_ASSERTION_ERROR', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BINARY_OP', 'PRECALL', 'CALL', 'RAISE_VARARGS', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (14): `['RESUME', 'LOAD_NAME', 'LOAD_ASSERTION_ERROR', 'LOAD_NAME', 'PRECALL', 'CALL', 'RAISE_VARARGS', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'PRECALL', 'CALL', 'RAISE_VARARGS']`
- **根因初步分析：** R8 测过 `assert x, "msg: " + (ternary)`（字符串 + 单 ternary）。本用例 msg 是 `ternary + ternary`（无字符串前缀）。第一个 ternary merge 块栈顶 + 第二个 ternary merge 块栈顶 + BINARY_OP + LOAD_ASSERTION_ERROR + RAISE_VARARGS。`_resolve_assert_condition_ternary_expr` 只处理单 ternary msg 或 字符串+ternary msg，未处理两个 ternary 通过 BINARY_OP 组合的 msg，第二个 ternary 被误识为独立 raise 调用。

---

### Bug R20-14: kwarg + starred-list-ternary 混合 call

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_starred_call_kwarg_star.py`
- **源码：**
  ```python
  f(x=1, *[a if c else b])
  ```
- **失败现象：** 反编译退化为 `f(a if c else b, x=1)`，走 KW_NAMES+PRECALL+CALL 而非 CALL_FUNCTION_EX。
- **失败指令对比：**
  - 原始 (14): `['RESUME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_LIST', 'LOAD_CONST', 'LOAD_CONST', 'BUILD_MAP', 'CALL_FUNCTION_EX', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编 (13): `['RESUME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'KW_NAMES', 'PRECALL', 'CALL', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** R18 测过 `f(*(ternary), other)`（starred-ternary + pos arg，无 kwarg）。本用例 kwarg + starred-list-ternary：CALL_FUNCTION_EX 路径需 BUILD_MAP（kwarg）+ BUILD_LIST（starred list 含 ternary）+ LIST_EXTEND + CALL_FUNCTION_EX。`_try_build_ternary_kwarg_call` 只处理 KW_NAMES+PRECALL+CALL 路径，未处理 CALL_FUNCTION_EX 路径下 kwarg 与 starred-list-ternary 共存的情况。

---

### Bug R20-15: ternary 作 async with 的上下文管理器表达式

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_async_with_item.py`
- **源码：**
  ```python
  async def f():
      async with (a if c else b) as x:
          pass
  ```
- **失败现象：** 反编译退化为 `async with context() as x: pass`，用占位符 context() 替换 ternary。
- **失败指令对比：**
  - 原始: `[..., LOAD_GLOBAL(c), ...]`
  - 重编: `[..., LOAD_GLOBAL(context), ...]`
  - 嵌套 code object 指令3参数不匹配: c vs context (op=LOAD_GLOBAL)
- **根因初步分析：** R7 测过 `async with ctx:` + ternary in body（ternary 在 with body 内赋值）。本用例 ternary 是 with item 本身：BEFORE_ASYNC_WITH 消费 ternary merge 块栈顶 + GET_AWAITABLE + SEND 轮询 + STORE_FAST x。`_generate_ternary` 在 async with item 上下文下未识别 ternary region，反编译器用占位符 `context()` 替换未识别的 with item 表达式。async with 的 BEFORE_ASYNC_WITH + GET_AWAITABLE + SEND 轮询与 ternary merge 块归属冲突。

---

### Bug R20-16: 函数内 try (非空 body) + except (ternary) as e

- **测试文件：** `tests/exhaustive/ternary/test_r20_ternary_except_handler_func_body.py`
- **源码：**
  ```python
  def f():
      try:
          x = 1
      except (A if c else B) as e:
          pass
  ```
- **失败现象：** 反编译额外生成 `del e` 且 except handler 字节码重排。
- **失败指令对比：**
  - 原始 (25): `['RESUME', 'LOAD_CONST', 'STORE_FAST', 'LOAD_CONST', 'RETURN_VALUE', 'PUSH_EXC_INFO', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'CHECK_EXC_MATCH', 'STORE_FAST', 'POP_EXCEPT', 'LOAD_CONST', 'STORE_FAST', 'DELETE_FAST', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'STORE_FAST', 'DELETE_FAST', 'RERAISE', 'RERAISE', 'COPY', 'POP_EXCEPT', 'RERAISE']`
  - 重编 (24): `['RESUME', 'LOAD_CONST', 'STORE_FAST', 'PUSH_EXC_INFO', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'CHECK_EXC_MATCH', 'STORE_FAST', 'POP_EXCEPT', 'LOAD_CONST', 'STORE_FAST', 'DELETE_FAST', 'LOAD_CONST', 'STORE_FAST', 'DELETE_FAST', 'RERAISE', 'RERAISE', 'COPY', 'POP_EXCEPT', 'RERAISE', 'DELETE_FAST', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因初步分析：** R14 测过模块级 `try: pass + except (ternary) as e`（空 try body，模块级，该用例通过）。本用例函数作用域（STORE_FAST/DELETE_FAST for e）+ 非空 try body（LOAD_CONST/RETURN_VALUE 在 PUSH_EXC_INFO 之前）触发：ternary merge 块的 CHECK_EXC_MATCH + STORE_FAST e + POP_EXCEPT + 清理链（RERAISE/COPY/POP_EXCEPT）与 try body 末尾 RETURN_VALUE 的归属冲突，反编译额外生成 `del e` 且 except handler 字节码重排，try body 的 RETURN_VALUE 被并入 except 路径。

---

## 共性根因分析

16 个 bug 可归为 5 类共性根因：

### 1. ternary 被容器 literal 包装后再展开（6 个：R20-04/05/06/07/08/14）

ternary 产出标量，被 `BUILD_LIST 1` / `BUILD_MAP 1` 包装成内层容器 literal，再通过 `LIST_EXTEND` / `DICT_UPDATE` / `LIST_TO_TUPLE` / `CALL_FUNCTION_EX` 展开到外层容器/call。`_try_build_ternary_chained_container` 与 `_try_build_ternary_merge_consumer_expr` 只识别 ternary 直接作展开源（无内层包装）的情况，未处理"ternary → BUILD_LIST/BUILD_MAP 包装 → EXTEND/UPDATE 展开"的双层结构。反编译丢失内层 BUILD_* 与外层 EXTEND/UPDATE，退化为单层容器或 PRECALL+CALL 路径。

### 2. walrus(ternary) 在赋值/存储上下文（3 个：R20-01/02/03）

walrus 的 COPY+STORE 与 ternary merge 块的 value_target 推断冲突。`_try_build_ternary_store_assign` 把 walrus 的 COPY+STORE 误识为独立赋值目标（subscript/attr 赋值的真正消费指令 STORE_SUBSCR/STORE_ATTR 被忽略），或把 walrus(嵌套ternary) 在 cond 中误识为外层三元的 value_target。walrus 的 COPY 栈关联与外层 STORE 消费链归属断裂。

### 3. 两 ternary 通过 boolop/binop 组合作单一值（4 个：R20-09/10/11/13）

两个 ternary merge 块的栈顶通过 `JUMP_IF_FALSE_OR_POP`/`JUMP_IF_TRUE_OR_POP`（boolop）或 `BINARY_OP`（binop）组合成单一值，再被 STORE_NAME / yield from / RAISE_VARARGS 消费。`_try_build_ternary_boolop_and_if` 只覆盖 assert/raise 上下文，未覆盖赋值上下文；`_try_build_ternary_merge_consumer_expr` 未处理 yield from / assert msg 上下文下两 ternary 通过 BINARY_OP 组合的情况。第一个 ternary 被误识为独立表达式语句（POP_TOP 丢弃或拆分）。

### 4. ternary 作 async/generator 特殊语句的 item/expr（2 个：R20-12/15）

ternary 作 async with 的 with item 表达式，或 yield from 的方法调用表达式 `(ternary).m()`。async with 的 `BEFORE_ASYNC_WITH + GET_AWAITABLE + SEND` 轮询结构与 generator 的 `RETURN_GENERATOR + JUMP_BACKWARD_NO_INTERRUPT` 轮询结构与 ternary region 归约冲突，反编译完全丢失 ternary 或用占位符 `context()` 替换。

### 5. 上下文敏感：函数作用域 + 非空 body 触发（1 个：R20-16）

模块级/空 body 上下文通过，但函数作用域（STORE_FAST/DELETE_FAST）+ 非空 body（额外 LOAD_CONST/RETURN_VALUE）触发。ternary merge 块的清理链（CHECK_EXC_MATCH/POP_EXCEPT/RERAISE）与 try body 末尾 RETURN_VALUE 的归属在函数作用域下重排失败，反编译额外生成 `del e` 且 except handler 字节码重排。

---

## 新建测试文件清单

| # | 测试文件 | Bug ID | 源码摘要 |
|---|---------|--------|---------|
| 1 | `test_r20_ternary_walrus_in_cond.py` | R20-01 | `x = (n := a) if (m := b if c else d) else e` |
| 2 | `test_r20_ternary_walrus_subscr_assign.py` | R20-02 | `x[(n := a if c else b)] = y` |
| 3 | `test_r20_ternary_walrus_attr_assign.py` | R20-03 | `obj.attr = (n := a if c else b)` |
| 4 | `test_r20_ternary_starred_list_scalar.py` | R20-04 | `x = [*[a if c else b]]` |
| 5 | `test_r20_ternary_starred_tuple_list.py` | R20-05 | `x = (*[a if c else b],)` |
| 6 | `test_r20_ternary_dict_double_star_literal.py` | R20-06 | `x = {**{a if c else b: 1}}` |
| 7 | `test_r20_ternary_starred_call_list.py` | R20-07 | `f(*[a if c else b])` |
| 8 | `test_r20_ternary_starred_call_pos_before_after.py` | R20-08 | `f(1, *[a if c else b], 2)` |
| 9 | `test_r20_ternary_boolop_and_two_assign.py` | R20-09 | `x = (a if c else b) and (d if e else f)` |
| 10 | `test_r20_ternary_boolop_or_two_assign.py` | R20-10 | `x = (a if c else b) or (d if e else f)` |
| 11 | `test_r20_ternary_yield_from_binop_two.py` | R20-11 | `def f(): yield from (a if c else b) + (d if e else f)` |
| 12 | `test_r20_ternary_yield_from_method_on.py` | R20-12 | `def f(): yield from (a if c else b).m()` |
| 13 | `test_r20_ternary_assert_msg_binop_two.py` | R20-13 | `assert x, (a if c else b) + (d if e else f)` |
| 14 | `test_r20_ternary_starred_call_kwarg_star.py` | R20-14 | `f(x=1, *[a if c else b])` |
| 15 | `test_r20_ternary_async_with_item.py` | R20-15 | `async def f(): async with (a if c else b) as x: pass` |
| 16 | `test_r20_ternary_except_handler_func_body.py` | R20-16 | `def f(): try: x = 1; except (A if c else B) as e: pass` |

探索脚本：`/workspace/.trae/specs/iterate-region-test-fix/rounds/ternary/round_20/_explore.py`

---

## 验证命令

```bash
# 单独运行 16 个新测试（预期 16 failed）
timeout 280 python -m pytest \
  tests/exhaustive/ternary/test_r20_ternary_walrus_in_cond.py \
  tests/exhaustive/ternary/test_r20_ternary_walrus_subscr_assign.py \
  tests/exhaustive/ternary/test_r20_ternary_walrus_attr_assign.py \
  tests/exhaustive/ternary/test_r20_ternary_starred_list_scalar.py \
  tests/exhaustive/ternary/test_r20_ternary_starred_tuple_list.py \
  tests/exhaustive/ternary/test_r20_ternary_dict_double_star_literal.py \
  tests/exhaustive/ternary/test_r20_ternary_starred_call_list.py \
  tests/exhaustive/ternary/test_r20_ternary_starred_call_pos_before_after.py \
  tests/exhaustive/ternary/test_r20_ternary_boolop_and_two_assign.py \
  tests/exhaustive/ternary/test_r20_ternary_boolop_or_two_assign.py \
  tests/exhaustive/ternary/test_r20_ternary_yield_from_binop_two.py \
  tests/exhaustive/ternary/test_r20_ternary_yield_from_method_on.py \
  tests/exhaustive/ternary/test_r20_ternary_assert_msg_binop_two.py \
  tests/exhaustive/ternary/test_r20_ternary_starred_call_kwarg_star.py \
  tests/exhaustive/ternary/test_r20_ternary_async_with_item.py \
  tests/exhaustive/ternary/test_r20_ternary_except_handler_func_body.py \
  -v --tb=short

# 完整 ternary 套件（预期 59 failed, 529 passed, 9 skipped）
timeout 280 python -m pytest tests/exhaustive/ternary/ -q --tb=no

# 探索脚本（批量验证候选模式）
timeout 280 python .trae/specs/iterate-region-test-fix/rounds/ternary/round_20/_explore.py
```

---

## 约束遵守说明

- 未修改任何 `core/cfg/*.py` 源代码（仅创建测试 + 探索脚本）。
- 探索脚本放在 round_20 目录内（`/workspace/.trae/specs/iterate-region-test-fix/rounds/ternary/round_20/_explore.py`），未创建根级 `_debug_*.py`。
- 所有 pytest 命令用 `timeout 280` 包裹。
- 已找到 16 个真实失败（> 10），停止测试。
- 所有测试验证字节码完全匹配（`verify_decompilation` → `verify_bytecode_equivalence`，过滤跳转指令后逐条比较操作码与参数）。
