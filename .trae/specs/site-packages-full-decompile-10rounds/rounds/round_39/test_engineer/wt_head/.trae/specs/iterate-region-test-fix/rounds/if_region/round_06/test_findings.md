# IF 区域 第 6 轮 测试发现 (round_06)

- 测试日期：2026-07-18
- 基线：if_region 1 failed (test_adv03_nested_ternary_chain 遗留，可重测但不计入本轮) / 418 passed（Round 5 已完成全部 11/11 修复并 push 到远程 trae/agent-gUeaUE，git HEAD fb8d930）
- 本轮新增测试文件：38 个 `test_adv06_*.py`
- 确认错误数：**14**（全部失败；24 个通过的不计入）
- 验证方式：`ExhaustiveTestCase.verify_decompilation()` → `verify_bytecode_equivalence()`（对比原始字节码 vs 反编译后重编译字节码；过滤跳转/对齐指令）
- 约束遵守：未修改 `core/cfg/` 下任何源码，仅新增测试文件与本报告

## Round 1-5 已覆盖范围（本轮严格避开）

- R1：walrus+or/链式比较、await 条件/await+比较、lambda 调用条件、not+链式比较、not+BoolOp De Morgan、not+四段链式、三元条件（裸/嵌套）、CALL_FUNCTION_EX（`*args`/`**kwargs`）
- R2：walrus 下标（`d[(n := f())] > 0`）、is None/is not None BoolOp、await in BoolOp、三元 in BoolOp(and)/比较右侧/链式比较中段、not+三元
- R3：三元 wrapping（下标/属性/调用参数/is None/in/dict key/链式比较左操作数）、walrus 下标链式比较、嵌套三元链式比较、await 链式比较、walrus+await（match 误判）
- R4：tuple unpack、nested tuple unpack、multi-target chain rhs、chain-cmp rhs、walrus augassign、compound augassign、deep subscr assign、del nested subscr、ellipsis slice、paren-cmp false-positive、starred list cond、compound assert、lambda defaults、await rhs、yield rhs
- R5：import asname、nested lambda、setcomp multi-for、dictcomp walrus、5-level chain-cmp、ann-assign、fstring format-spec、async with as x、async for、await list-elem、augassign attr chain
- 已知遗留（不重测）：test_adv03_nested_ternary_chain（链式比较中嵌套三元，19 vs 3）

## 失败测试列表（14 个确认错误）

| # | 测试文件 | 类名 | 失败环节 |
|---|----------|------|----------|
| 1 | test_adv06_chaincmp_is_chain.py | TestAdv06ChaincmpIsChain | 字节码不等价（`a is b is c` 整条赋值丢失变 `pass`，17 vs 6） |
| 2 | test_adv06_chaincmp_in_chain.py | TestAdv06ChaincmpInChain | 字节码不等价（`a in b in c` 整条赋值丢失变 `pass`，17 vs 6） |
| 3 | test_adv06_nested_ternary_body.py | TestAdv06NestedTernaryBody | 字节码不等价（多层嵌套三元 `a if b else cc if d else e` 内层 `cc if d else e` 坍塌为 `d`，12 vs 10） |
| 4 | test_adv06_walrus_outside_comp.py | TestAdv06WalrusOutsideComp | 字节码不等价（`(n := f())` walrus 在表达式语句中 `COPY` 丢失变 `n = f()`，24 vs 20） |
| 5 | test_adv06_lambda_outer_default.py | TestAdv06LambdaOuterDefault | 字节码不等价（`lambda x=a, y=b` 默认值 `a/b` 丢失变 `lambda x, y`，BUILD_TUPLE 丢失，12 vs 9） |
| 6 | test_adv06_lambda_kw_default.py | TestAdv06LambdaKwDefault | 字节码不等价（`lambda x, *, y=10` kw-only 默认 `10` 丢失变 `lambda x, *, y`，BUILD_CONST_KEY_MAP 丢失，12 vs 9） |
| 7 | test_adv06_yield_from_rhs.py | TestAdv06YieldFromRhs | 字节码不等价（`x = yield from g()` 赋值目标 x 丢失变 `yield from g()` 独立语句，STORE_FAST→POP_TOP） |
| 8 | test_adv06_await_call_arg.py | TestAdv06AwaitCallArg | 嵌套 code object 不匹配（`h(await g(), x)` 调用结构坍塌，剩 `await g()` 独立语句，21 vs 17） |
| 9 | test_adv06_await_dict_elem.py | TestAdv06AwaitDictElem | 嵌套 code object 不匹配（`{k: await g(), m: await h()}` dict 字面量与 await 元素全丢，退化为 `await g(); await h(); r = {}`，k vs g LOAD_GLOBAL 错位） |
| 10 | test_adv06_await_tuple_elem.py | TestAdv06AwaitTupleElem | 嵌套 code object 不匹配（`(await g(), await h())` tuple 字面量丢失变 `await g(); await h(); r = ()`，26 vs 28） |
| 11 | test_adv06_await_in_subscr.py | TestAdv06AwaitInSubscr | 嵌套 code object 不匹配（`d[await g()]` BINARY_SUBSCR 丢失变 `await g()` 独立语句，19 vs 17） |
| 12 | test_adv06_assert_fstring_msg.py | TestAdv06AssertFstringMsg | 反编译结果语法错误（assert + f-string `!r` 转换被替换为 U+0002 控制字符，输出 `f'msg {y}: {z\x02}'`） |
| 13 | test_adv06_fstring_conversion.py | TestAdv06FstringConversion | 反编译结果语法错误（f-string `!r`/`!s`/`!a` 转换被替换为 U+0002/U+0001 控制字符，输出 `f'{x\x02} {y\x01} {z\x01}'`） |
| 14 | test_adv06_fstring_debug_spec.py | TestAdv06FstringDebugSpec | 反编译结果语法错误（f-string debug `f"{x=}"` 转换被替换为 U+0002 控制字符，输出 `f'x={x\x02} y={y\x02}'`） |

## 本轮通过的测试（不计入错误，仅作覆盖参考）

- test_adv06_lambda_comprehension_body.py（`lambda x: [y for y in x if y > 0]`，通过）
- test_adv06_multidim_slice.py（`x[1:2, 3:4]` 多维切片，通过）
- test_adv06_step_slice.py（`x[1:10:2]` step 切片，通过）
- test_adv06_reversed_slice.py（`x[::-1]` reversed 切片，通过）
- test_adv06_frozenset_literal.py（`r = {1, 2, 3}` set 字面量，通过）
- test_adv06_genexp_nested.py（`sum(x for x in y if x > 0)`，通过）
- test_adv06_setcomp_nested.py（`{x + 1 for x in a if x > 0}`，通过）
- test_adv06_genexp_walrus.py（`list((n := x) for x in a)`，通过）
- test_adv06_dictcomp_with_filter.py（`{k: v for k, v in items if k > 0}`，通过）
- test_adv06_none_coalescing.py（`x if x is not None else y`，通过）
- test_adv06_complex_number_op.py（`1j * x + 2j`，通过）
- test_adv06_long_int_op.py（`10**100 + x`，通过）
- test_adv06_ellipsis_is.py（`x is ...`，通过）
- test_adv06_bytes_format.py（`b'%s:%d' % (s, n)`，通过）
- test_adv06_del_attr_chain4.py（`del a.b.c.d` 四层属性 del，通过）
- test_adv06_ternary_lambda_body.py（`lambda x: a if x > 0 else b`，通过）
- test_adv06_starred_call_in_body.py（`f(*args, **kwargs)` 体内调用，通过）
- test_adv06_raise_complex_from.py（`raise E(a, b=k) from exc`，通过）
- test_adv06_nested_with.py（`with a as x: with b as y:`，通过）
- test_adv06_try_finally_nested.py（try-finally 嵌套 try-except，通过）
- test_adv06_augassign_subscr.py（`a[b] += 1`，通过）
- test_adv06_multitarget_ann_assign.py（`x: list = [1, 2, 3]`，通过）
- test_adv06_match_guard.py（`match x: case _ if x > 0:`，通过）
- test_adv06_match_destructure.py（`case [a, b, *rest]:`，通过）

---

## 错误详细记录

### 错误 01 — if 体内链式 `is` 比较作赋值右值，`a is b is c` 整条丢失变 `pass`

- 文件：test_adv06_chaincmp_is_chain.py
- 源码：
  ```python
  if c:
      z = a is b is c
  ```
- 期望反编译：保留 `z = a is b is c`（链式 is 比较作赋值右值）
- 实际反编译：
  ```python
  if c:
      pass
  ```
- 失败信息：指令数不匹配 17 vs 6（原始含 `LOAD_NAME a` + `LOAD_NAME b` + `LOAD_NAME c` + `SWAP` + `COPY` + `IS_OP` + `JUMP_IF_FALSE_OR_POP` + `LOAD_NAME c` + `IS_OP` + `SWAP` + `POP_TOP` + `STORE_NAME z`；重编仅 `RESUME/LOAD_NAME c/LOAD_CONST None/RETURN_VALUE`，整条赋值坍塌为 `pass`）
- 根因初判：链式 `is` 比较 `a is b is c` 字节码含 `IS_OP`×2 + `JUMP_IF_FALSE_OR_POP` + `SWAP/COPY` 链式 setup。if body 区域分析对 `IS_OP` 链式比较（而非 `COMPARE_OP`）的重建失败，整条赋值坍塌为 `pass`。前 5 轮的链式比较测试都基于 `COMPARE_OP`（`<`/`>`/`==` 等），未覆盖 `IS_OP`（`is`/`is not`）链式比较作赋值右值。R5 错误 05 修复了 5 段 `COMPARE_OP` 链式比较；本例是 2 段 `IS_OP` 链式比较，新失效模式（IS_OP 链式比较在 if body 中未识别）。

### 错误 02 — if 体内链式 `in` 比较作赋值右值，`a in b in c` 整条丢失变 `pass`

- 文件：test_adv06_chaincmp_in_chain.py
- 源码：
  ```python
  if c:
      z = a in b in c
  ```
- 期望反编译：保留 `z = a in b in c`（链式 in 比较作赋值右值）
- 实际反编译：
  ```python
  if c:
      pass
  ```
- 失败信息：指令数不匹配 17 vs 6（原始含 `LOAD_NAME a` + `LOAD_NAME b` + `LOAD_NAME c` + `SWAP` + `COPY` + `CONTAINS_OP` + `JUMP_IF_FALSE_OR_POP` + `LOAD_NAME c` + `CONTAINS_OP` + `SWAP` + `POP_TOP` + `STORE_NAME z`；重编仅 `RESUME/LOAD_NAME c/LOAD_CONST None/RETURN_VALUE`，整条赋值坍塌为 `pass`）
- 根因初判：与错误 01 同源，但字节码用 `CONTAINS_OP`（`in`/`not in`）。if body 区域分析对 `CONTAINS_OP` 链式比较的重建失败，整条赋值坍塌为 `pass`。前 5 轮的链式比较测试都基于 `COMPARE_OP`，未覆盖 `CONTAINS_OP` 链式比较作赋值右值。

### 错误 03 — if 体内多层嵌套三元作赋值右值，内层三元坍塌

- 文件：test_adv06_nested_ternary_body.py
- 源码：
  ```python
  if c:
      z = a if b else cc if d else e
  ```
- 期望反编译：保留 `z = a if b else cc if d else e`（多层嵌套三元作赋值右值）
- 实际反编译：
  ```python
  if c:
      z = (a if b else d)
  ```
- 失败信息：指令数不匹配 12 vs 10（原始含 6 个 `LOAD_NAME`（a/b/cc/d/e + 条件变量）；重编仅 4 个 `LOAD_NAME`，内层三元 `cc if d else e` 坍塌为 `d`，`cc` 与 `e` 全丢）
- 根因初判：多层嵌套三元 `a if b else cc if d else e` 作赋值右值时，字节码为外层 `POP_JUMP_FORWARD_IF_FALSE` + 内层 `POP_JUMP_FORWARD_IF_FALSE` 嵌套。if body 区域分析对多层 IfExp 嵌套重建时，把内层三元的 `body` (cc) 与 `orelse` (e) 都丢弃，只保留内层的 `test` (d)，输出 `a if b else d`。R1 错误 09 修复了嵌套三元作 if 条件（裸 if）；R3 错误 07 是嵌套三元在链式比较中段（遗留）；本轮新增嵌套三元在 if body 作赋值右值，新组合。

### 错误 04 — if 体内 walrus 在表达式语句中，`COPY` 丢失变普通赋值

- 文件：test_adv06_walrus_outside_comp.py
- 源码：
  ```python
  if c:
      (n := f())
      (m := g())
      r = n + m
  ```
- 期望反编译：保留 `(n := f())`、`(m := g())`（walrus 在表达式语句中）
- 实际反编译：
  ```python
  if c:
      n = f()
      m = g()
      r = (n + m)
  ```
- 失败信息：指令数不匹配 24 vs 20（原始含 `PUSH_NULL` + `LOAD_NAME f` + `PRECALL` + `CALL` + `COPY` + `STORE_NAME n` + `POP_TOP`（walrus 求值块 + 丢弃返回值）；重编缺 `COPY`，walrus 退化为普通赋值 `n = f()`，且无 `POP_TOP` 丢弃返回值）
- 根因初判：walrus 在表达式语句中 `(n := f())`（其返回值被 POP_TOP 丢弃）字节码为 `CALL` + `COPY` + `STORE_NAME n` + `POP_TOP`。if body 区域分析对 walrus 在「无赋值目标位置」的求值块识别失败，丢弃 `COPY`，把 walrus 退化为普通赋值 `n = f()`，同时丢失了 `POP_TOP`（丢弃返回值）。前 5 轮的 walrus 测试覆盖了 walrus 在条件/下标/切片/链式比较/AugAssign/推导式 value 位置，均未覆盖 walrus 在「无赋值目标的表达式语句」位置。R1-5 修复的 walrus 都是「有显式赋值目标」或「条件内部」位置；本例是「无赋值目标」的纯副作用 walrus 表达式语句。

### 错误 05 — if 体内 lambda 默认参数引用外部变量，`BUILD_TUPLE` 丢失

- 文件：test_adv06_lambda_outer_default.py
- 源码：
  ```python
  if c:
      f = lambda x=a, y=b: x + y
  ```
- 期望反编译：保留 `lambda x=a, y=b: x + y`（默认值引用外部变量）
- 实际反编译：
  ```python
  if c:
      f = lambda x, y: x + y
  ```
- 失败信息：指令数不匹配 12 vs 9（原始含 `LOAD_NAME a` + `LOAD_NAME b` + `BUILD_TUPLE` + `LOAD_CONST <code>` + `MAKE_FUNCTION`；重编缺 `LOAD_NAME a/b` 与 `BUILD_TUPLE`，默认值丢失，`MAKE_FUNCTION` 无默认值参数）
- 根因初判：`lambda x=a, y=b: x + y` 默认值通过 `LOAD_NAME a` + `LOAD_NAME b` + `BUILD_TUPLE` + `MAKE_FUNCTION` 传递。if body 区域分析对 lambda 的 `MAKE_FUNCTION` 重建时丢失了默认值元组（`BUILD_TUPLE`），输出无默认值的 `lambda x, y`。R4 错误 13 修复了 lambda 默认值在 if **条件**位置（`if (lambda x=1, y=2: x + y)():`），但默认值是常量 `1/2`，走 `LOAD_CONST (1, 2)` 元组路径；本例默认值是外部变量 `a/b`，走 `LOAD_NAME` + `BUILD_TUPLE` 路径，新组合。

### 错误 06 — if 体内 lambda kw-only 默认值，`BUILD_CONST_KEY_MAP` 丢失

- 文件：test_adv06_lambda_kw_default.py
- 源码：
  ```python
  if c:
      f = lambda x, *, y=10: x + y
  ```
- 期望反编译：保留 `lambda x, *, y=10: x + y`（kw-only 默认值）
- 实际反编译：
  ```python
  if c:
      f = lambda x, *, y: x + y
  ```
- 失败信息：指令数不匹配 12 vs 9（原始含 `LOAD_CONST 10` + `LOAD_CONST ('y',)` + `BUILD_CONST_KEY_MAP` + `LOAD_CONST <code>` + `MAKE_FUNCTION`；重编缺 `LOAD_CONST 10` + `LOAD_CONST ('y',)` + `BUILD_CONST_KEY_MAP`，kw-only 默认值 `10` 丢失）
- 根因初判：`lambda x, *, y=10: x + y` 的 kw-only 默认值通过 `LOAD_CONST 10` + `LOAD_CONST ('y',)` + `BUILD_CONST_KEY_MAP` + `MAKE_FUNCTION` 传递。if body 区域分析对 lambda 的 `MAKE_FUNCTION` 重建时丢失了 `BUILD_CONST_KEY_MAP` 块（kw-only 默认值），输出无默认值的 `lambda x, *, y`。R4 错误 13 是普通默认值 `LOAD_CONST (1, 2)` 元组；本例是 kw-only 默认值 `BUILD_CONST_KEY_MAP` 路径，新组合。

### 错误 07 — if 体内 `yield from` 作赋值右值，赋值目标 x 丢失

- 文件：test_adv06_yield_from_rhs.py
- 源码：
  ```python
  def f():
      if c:
          x = yield from g()
      return x
  ```
- 期望反编译：保留 `x = yield from g()`（yield from 作赋值右值）
- 实际反编译：
  ```python
  def f():
      if c:
          yield from g()
      return x
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令12操作码不匹配：`STORE_FAST vs POP_TOP`（原始 yield from 后 `STORE_FAST x` 保存到赋值目标；重编 yield from 后 `POP_TOP` 丢弃返回值，赋值目标 `x` 丢失，yield from 退化为独立语句）
- 根因初判：`x = yield from g()` 在生成器函数 if 体内，yield from 表达式作赋值右值。字节码为 `GET_YIELD_FROM_ITER` + `LOAD_CONST None` + `SEND` + `YIELD_VALUE` + `RESUME` + `STORE_FAST x`。if body 区域分析把 yield from 表达式当作独立语句 `yield from g()`，丢弃了 `STORE_FAST x` 赋值目标。R4 错误 14/15 修复了 await / yield 作赋值右值；本轮新增 yield from 作赋值右值，新组合（yield from 走 `GET_YIELD_FROM_ITER/SEND` 路径，与 yield 的 `YIELD_VALUE` 路径不同）。

### 错误 08 — if 体内 await 作函数调用参数，调用结构坍塌

- 文件：test_adv06_await_call_arg.py
- 源码：
  ```python
  async def f():
      if c:
          r = h(await g(), x)
  ```
- 期望反编译：保留 `r = h(await g(), x)`（await 作调用参数）
- 实际反编译：
  ```python
  async def f():
      if c:
          await g()
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 21 vs 17（原始含 `LOAD_GLOBAL h` + `PUSH_NULL` + `LOAD_GLOBAL g` + `PRECALL` + `CALL` + `GET_AWAITABLE` + `YIELD_VALUE` + `RESUME` + `LOAD_FAST x` + `PRECALL` + `CALL` + `STORE_FAST r`；重编多出 `POP_TOP`，调用 `h(...)` 与赋值目标 `r` 全丢，await 退化为独立语句）
- 根因初判：`h(await g(), x)` await 作调用参数时，字节码在 `CALL`（g）后插入 `GET_AWAITABLE` + `YIELD_VALUE` + `RESUME`（await setup），再 `LOAD_FAST x` + `CALL`（h）。if body 区域分析对「await 元素 + PRECALL/CALL」的调用参数重建失败，把 await 提为独立语句（返回值被 POP_TOP 丢弃），外层调用 `h(...)` 与赋值目标 `r` 全丢。R5 错误 10 修复了 `r = [await g(), await h()]` await 作列表元素；本轮新增 await 作函数调用参数，新组合。

### 错误 09 — if 体内 await 作 dict 字面量 value，dict 字面量与 await 全丢

- 文件：test_adv06_await_dict_elem.py
- 源码：
  ```python
  async def f():
      if c:
          r = {k: await g(), m: await h()}
  ```
- 期望反编译：保留 `r = {k: await g(), m: await h()}`（dict 字面量含多个 await value）
- 实际反编译：
  ```python
  async def f():
      if c:
          await g()
          await h()
          r = {}
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令4参数不匹配：`k vs g (op=LOAD_GLOBAL)`（原始 `LOAD_GLOBAL k` + `LOAD_GLOBAL g` + `PRECALL` + `CALL` + `GET_AWAITABLE` + `YIELD_VALUE` + `RESUME` + `BUILD_MAP`；重编 `LOAD_GLOBAL g` + `POP_TOP`，dict 字面量 `BUILD_MAP` 与 await 元素绑定全丢，退化为 `await g(); await h(); r = {}`）
- 根因初判：`{k: await g(), m: await h()}` dict 字面量含两个 await value，字节码为 await setup（`GET_AWAITABLE/YIELD_VALUE`）×2 + `BUILD_MAP`。if body 区域分析对「await value + BUILD_MAP」的 dict 字面量识别失败，把两个 await 提为独立语句（返回值被 POP_TOP 丢弃），dict 字面量退化为空 `{}`。R5 错误 10 修复了 await 作列表元素；本轮新增 await 作 dict 字面量 value，新组合（dict 走 `BUILD_MAP` 路径，list 走 `BUILD_LIST` 路径）。

### 错误 10 — if 体内 await 作 tuple 字面量元素，tuple 字面量丢失变空 tuple

- 文件：test_adv06_await_tuple_elem.py
- 源码：
  ```python
  async def f():
      if c:
          r = (await g(), await h())
  ```
- 期望反编译：保留 `r = (await g(), await h())`（tuple 字面量含多个 await 元素）
- 实际反编译：
  ```python
  async def f():
      if c:
          await g()
          await h()
          r = ()
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 26 vs 28（原始含 `RETURN_GENERATOR/POP_TOP/RESUME` + 完整 `LOAD_GLOBAL g/PRECALL/CALL/GET_AWAITABLE/YIELD_VALUE` ×2 + `BUILD_TUPLE 2` + `STORE_FAST r`；重编多出 `POP_TOP`，tuple 字面量 `BUILD_TUPLE 2` 与 await 元素绑定全丢，await 退化为独立语句 `await g(); await h()`，赋值目标 r 变空 tuple `()`）
- 根因初判：`(await g(), await h())` tuple 字面量含两个 await 元素，字节码为 await setup ×2 + `BUILD_TUPLE 2`。if body 区域分析对「await 元素 + BUILD_TUPLE」的 tuple 字面量识别失败，把两个 await 提为独立语句（返回值被 POP_TOP 丢弃），tuple 字面量退化为空 `()`。R5 错误 10 修复了 await 作列表元素；本轮新增 await 作 tuple 字面量元素，新组合（tuple 走 `BUILD_TUPLE` 路径，list 走 `BUILD_LIST` 路径）。

### 错误 11 — if 体内 await 作下标，`BINARY_SUBSCR` 丢失

- 文件：test_adv06_await_in_subscr.py
- 源码：
  ```python
  async def f():
      if c:
          r = d[await g()]
  ```
- 期望反编译：保留 `r = d[await g()]`（await 作下标）
- 实际反编译：
  ```python
  async def f():
      if c:
          await g()
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 19 vs 17（原始含 `LOAD_GLOBAL d` + `LOAD_GLOBAL g` + `PRECALL` + `CALL` + `GET_AWAITABLE` + `YIELD_VALUE` + `RESUME` + `BINARY_SUBSCR` + `STORE_FAST r`；重编多出 `POP_TOP`，`BINARY_SUBSCR` 与 `STORE_FAST r` 全丢，await 退化为独立语句）
- 根因初判：`d[await g()]` await 作下标时，字节码在 `CALL`（g）后插入 `GET_AWAITABLE` + `YIELD_VALUE` + `RESUME`（await setup），再 `BINARY_SUBSCR`（取下标）+ `STORE_FAST r`。if body 区域分析对「await + BINARY_SUBSCR」的下标表达式重建失败，把 await 提为独立语句（返回值被 POP_TOP 丢弃），容器 `d`、`BINARY_SUBSCR` 与赋值目标 `r` 全丢。R5 错误 10 修复了 await 作列表元素；R3 错误 02 修复了三元作下标；本轮新增 await 作下标，新组合。

### 错误 12 — if 体内 assert + f-string 带 `!r` 转换，转换符被替换为 U+0002 控制字符

- 文件：test_adv06_assert_fstring_msg.py
- 源码：
  ```python
  if c:
      assert x > 0, f"msg {y}: {z!r}"
  ```
- 期望反编译：保留 `assert x > 0, f"msg {y}: {z!r}"`（f-string 带 `!r` 转换）
- 实际反编译：
  ```python
  if c:
      assert (x > 0), f'msg {y}: {z\x02}'
  ```
- 失败信息：反编译结果语法错误：invalid non-printable character U+0002 (<unknown>, line 2)（`!r` 转换被替换为 U+0002 (STX) 控制字符，输出 `f'msg {y}: {z\x02}'`）
- 根因初判：f-string `{z!r}` 中 `!r` 是 `FORMAT_VALUE` 指令的 flags 参数（Python 3.11 中 `FORMAT_VALUE` 用 flags 区分 conversion：0=无 / 1=(!s) / 2=(!r) / 3=(!a) / 4=带格式说明符）。if body 区域分析对 assert message 中 f-string 的 `FORMAT_VALUE` flags 解码失败，把 flags=2（`!r`）当作字符 `\x02` (STX) 直接拼接到 f-string 模板字符串中。前 5 轮未覆盖 f-string 带 conversion（`!r`/`!s`/`!a`）在 if body 中。R5 错误 07 是 f-string 嵌套格式说明符（误判为 dict）；本例是 f-string 转换说明符（`!r`）被替换为控制字符，新失效模式。

### 错误 13 — if 体内 f-string 带 `!r`/`!s`/`!a` 转换，转换符被替换为 U+0002/U+0001 控制字符

- 文件：test_adv06_fstring_conversion.py
- 源码：
  ```python
  if c:
      s = f"{x!r} {y!s} {z!a}"
  ```
- 期望反编译：保留 `f"{x!r} {y!s} {z!a}"`（f-string 带多种 conversion）
- 实际反编译：
  ```python
  if c:
      s = f'{x\x02} {y\x01} {z\x01}'
  ```
- 失败信息：反编译结果语法错误：invalid non-printable character U+0002 (<unknown>, line 2)（`!r` → `\x02`，`!s` → `\x01`，`!a` → `\x01`，conversion 被替换为控制字符）
- 根因初判：与错误 12 同源。f-string `{x!r}` / `{y!s}` / `{z!a}` 中 conversion 由 `FORMAT_VALUE` 的 flags 参数编码（1=(!s) / 2=(!r) / 3=(!a)）。if body 区域分析对 f-string 的 `FORMAT_VALUE` flags 解码失败，把 flags 当作字符直接拼接到模板字符串中：`!r` (flags=2) → `\x02`，`!s` (flags=1) → `\x01`，`!a` (flags=3) → `\x01`（注意 `!a` 应为 `\x03` 但实际是 `\x01`，说明解码逻辑还有 off-by-one 错误）。本例进一步揭示 conversion 解码的系统性缺陷。

### 错误 14 — if 体内 f-string debug spec `f"{x=}"`，转换符被替换为 U+0002 控制字符

- 文件：test_adv06_fstring_debug_spec.py
- 源码：
  ```python
  if c:
      s = f"{x=} {y=}"
  ```
- 期望反编译：保留 `f"{x=} {y=}"`（f-string debug spec）
- 实际反编译：
  ```python
  if c:
      s = f'x={x\x02} y={y\x02}'
  ```
- 失败信息：反编译结果语法错误：invalid non-printable character U+0002 (<unknown>, line 2)（debug spec `=` 被替换为 `\x02` 控制字符，输出 `f'x={x\x02} y={y\x02}'`）
- 根因初判：f-string `{x=}` debug spec 在 Python 3.8+ 启用，字节码为 `LOAD_NAME x` + `FORMAT_VALUE 4`（带格式说明符，且模板字符串中含 `x=` 前缀）+ `BUILD_STRING`。if body 区域分析对 `FORMAT_VALUE 4`（带 `=` debug spec）的解码失败，把 `=` debug 标志当作 `\x02` 控制字符拼接到 f-string 模板字符串中。debug spec 在 Python 3.11 字节码中通过 `FORMAT_VALUE` flags=4 + 模板字符串 `x=` 前缀组合实现，与前 5 轮的普通 f-string（flags=0）和格式说明符 f-string（flags=4 但无 `=` debug）不同，新组合。

---

## 根因分类汇总

| 根因类别 | 涉及错误 | 说明 |
|----------|----------|------|
| if 体内「IS_OP/CONTAINS_OP 链式比较」未识别 | 01, 02 | `a is b is c` / `a in b in c` 作赋值右值整条坍塌为 `pass`，前 5 轮链式比较仅覆盖 `COMPARE_OP`，未覆盖 `IS_OP`/`CONTAINS_OP` 链式比较 |
| if 体内「多层嵌套三元作赋值右值」内层坍塌 | 03 | `a if b else cc if d else e` 内层三元 `cc if d else e` 坍塌为 `d`，前 5 轮嵌套三元覆盖 if 条件 / 链式比较中段，未覆盖 if body 赋值右值 |
| if 体内「walrus 在无赋值目标表达式语句」退化为普通赋值 | 04 | `(n := f())` 表达式语句 `COPY` 丢失变 `n = f()`，前 5 轮 walrus 均为「有显式赋值目标」或「条件内部」位置 |
| if 体内「lambda MAKE_FUNCTION 默认值」丢失（外部变量 / kw-only） | 05, 06 | `lambda x=a, y=b`（BUILD_TUPLE 丢失）/ `lambda x, *, y=10`（BUILD_CONST_KEY_MAP 丢失），R4 错误 13 仅修复常量默认值（LOAD_CONST 元组），未覆盖外部变量 / kw-only 路径 |
| if 体内「suspendable 表达式作赋值右值」目标丢失（yield from / await） | 07, 08, 09, 10, 11 | `yield from g()` / `h(await g(), x)` / `{k: await g()}` / `(await g(),)` / `d[await g()]` 赋值目标与外层结构全丢；R4 修复 await/yield rhs；R5 修复 await 列表元素；本轮新增 yield from rhs + await 调用参数/dict/tuple/subscr |
| if 体内「f-string FORMAT_VALUE flags」解码失败 | 12, 13, 14 | `!r`/`!s`/`!a` conversion 与 `=` debug spec 被替换为 U+0002/U+0001 控制字符；R5 错误 07 是 f-string 嵌套格式说明符（误判为 dict）；本轮是 conversion/debug spec 解码缺陷 |

## 与 Round 1-5 的关系

- 本轮 14 个错误均为 Round 1-5 **未覆盖**的新组合，且本轮系统性地把测试焦点扩展到「if 体内的链式运算符扩展族 / 嵌套深度族 / walrus 位置扩展族 / lambda 默认值路径族 / suspendable 表达式位置扩展族 / f-string flags 解码族」：
  - **链式运算符扩展族（错误 01, 02）**：R1-5 修复了 `COMPARE_OP`（`<`/`>`/`==`）链式比较；本轮新增 `IS_OP`（`is`）链式比较（错误 01）、`CONTAINS_OP`（`in`）链式比较（错误 02）— 揭示 if body 中链式比较归约只覆盖 COMPARE_OP，未识别 IS_OP/CONTAINS_OP 链式 setup
  - **嵌套深度扩展族（错误 03）**：R1 错误 09 是嵌套三元作 if 条件；R3 错误 07 是嵌套三元在链式比较中段（遗留）；本轮新增嵌套三元在 if body 作赋值右值（错误 03）— 内层三元坍塌为 test，新组合
  - **walrus 位置扩展族（错误 04）**：R1-3 修复 walrus 在条件/下标/切片/链式比较；R4 修复 walrus 在 AugAssign 右值；R5 修复 walrus 在推导式 value；本轮新增 walrus 在「无赋值目标表达式语句」(错误 04) — `COPY` 丢失变普通赋值，新组合
  - **lambda 默认值路径扩展族（错误 05, 06）**：R4 错误 13 修复 lambda 常量默认值（LOAD_CONST 元组）；本轮新增 lambda 外部变量默认值（`BUILD_TUPLE` 路径，错误 05）、lambda kw-only 默认值（`BUILD_CONST_KEY_MAP` 路径，错误 06）— 揭示 MAKE_FUNCTION 重建的多路径盲区
  - **suspendable 表达式位置扩展族（错误 07, 08, 09, 10, 11）**：R4 修复 await/yield 作赋值右值；R5 修复 await 作列表元素；本轮新增 yield from 作赋值右值（错误 07）、await 作调用参数（错误 08）、await 作 dict value（错误 09）、await 作 tuple 元素（错误 10）、await 作下标（错误 11）— 揭示 if body 中 await/yield from 在「多种外层表达式包裹」下的系统性盲区
  - **f-string flags 解码族（错误 12, 13, 14）**：R5 错误 07 是 f-string 嵌套格式说明符（误判为 dict）；本轮新增 f-string `!r`/`!s`/`!a` conversion（错误 12, 13）、f-string `=` debug spec（错误 14）— 揭示 `FORMAT_VALUE` flags 解码为控制字符的系统性缺陷

## 复现命令

```bash
# 单个
python -m pytest tests/exhaustive/if_region/test_adv06_chaincmp_is_chain.py -v
# 全部 adv06
python -m pytest tests/exhaustive/if_region/test_adv06_*.py -q
```

## 最终汇总运行结果

```
14 failed, 24 passed
```
