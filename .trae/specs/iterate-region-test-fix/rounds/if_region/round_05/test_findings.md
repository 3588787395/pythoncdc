# IF 区域 第 5 轮 测试发现 (round_05)

- 测试日期：2026-07-18
- 基线：if_region 1 failed (test_adv03_nested_ternary_chain 遗留，可重测但不计入本轮) / 394 passed（Round 4 已完成 15/15 修复并 push 到远程 trae/agent-gUeaUE，git HEAD a3e4d41）
- 本轮新增测试文件：24 个 `test_adv05_*.py`
- 确认错误数：**11**（全部失败；13 个通过的不计入）
- 验证方式：`ExhaustiveTestCase.verify_decompilation()` → `verify_bytecode_equivalence()`（对比原始字节码 vs 反编译后重编译字节码；过滤跳转/对齐指令）
- 约束遵守：未修改 `core/cfg/` 下任何源码，仅新增测试文件与本报告

## Round 1-4 已覆盖范围（本轮严格避开）

- R1：walrus+or/链式比较、await 条件/await+比较、lambda 调用条件、not+链式比较、not+BoolOp De Morgan、not+四段链式、三元条件（裸/嵌套）、CALL_FUNCTION_EX（`*args`/`**kwargs`）
- R2：walrus 下标（`d[(n := f())] > 0`）、is None/is not None BoolOp、await in BoolOp、三元 in BoolOp(and)/比较右侧/链式比较中段、not+三元
- R3：三元 wrapping（下标/属性/调用参数/is None/in/dict key/链式比较左操作数）、walrus 下标链式比较、嵌套三元链式比较、await 链式比较、walrus+await（match 误判）
- R4：tuple unpack、nested tuple unpack、multi-target chain rhs、chain-cmp rhs（3 段 `0<a<10`）、walrus augassign、compound augassign（`d[k1][k2]+=1`）、deep subscr assign、del nested subscr、ellipsis slice、paren-cmp false-positive、starred list cond、compound assert、lambda defaults、await rhs、yield rhs
- 已知遗留（不重测）：test_adv03_nested_ternary_chain（链式比较中嵌套三元，19 vs 3）

## 失败测试列表（11 个确认错误）

| # | 测试文件 | 类名 | 失败环节 |
|---|----------|------|----------|
| 1 | test_adv05_import_asname.py | TestAdv05ImportAsname | 字节码不等价（`from m import x as y` 退化为 `from m import x`，asname y 丢失） |
| 2 | test_adv05_nested_lambda.py | TestAdv05NestedLambda | 嵌套 code object 不匹配（内层 lambda 走占位路径 `lambda *args, **kwargs: None`，闭包信息丢失） |
| 3 | test_adv05_setcomp_multi_for.py | TestAdv05SetcompMultiFor | 嵌套 code object 不匹配（多 for 子句被误为元组解包 `for x, y in a`，第二个 GET_ITER 丢失） |
| 4 | test_adv05_dictcomp_walrus.py | TestAdv05DictcompWalrus | 嵌套 code object 不匹配（dictcomp 内 walrus `(v := f(k))` 丢失变 `f(k)`，COPY+STORE_GLOBAL 丢失） |
| 5 | test_adv05_chaincmp_5_levels.py | TestAdv05Chaincmp5Levels | 反编译结果语法错误（5 段链式比较 `0<a<b<c<d` 作赋值右值，幽灵表达式 + `<copy_placeholder_2>` 占位符泄漏） |
| 6 | test_adv05_ann_assign.py | TestAdv05AnnAssign | 字节码不等价（注解赋值 `x: int = 1` 缺 `SETUP_ANNOTATIONS` 前导，注解被改为 `__annotations__['x']=int` 独立语句） |
| 7 | test_adv05_fstring_format_spec.py | TestAdv05FstringFormatSpec | 字节码不等价（f-string 嵌套格式说明符 `f'{x:{width}.2f}'` 被误判为 dict 字面量 `{x:f'{width}.2f'}`，FORMAT_VALUE 退化为 BUILD_MAP） |
| 8 | test_adv05_async_with.py | TestAdv05AsyncWith | 嵌套 code object 不匹配（`async with g() as x:` 中 `as x` 绑定丢失，STORE_FAST 变 POP_TOP） |
| 9 | test_adv05_async_for.py | TestAdv05AsyncFor | 嵌套 code object 不匹配（`async for x in g()` 结构坍塌，GET_AITER 变 POP_TOP，g() 提为独立语句 + `async for x in None: while True: pass`） |
| 10 | test_adv05_await_list_elem.py | TestAdv05AwaitListElem | 嵌套 code object 不匹配（`r = [await g(), await h()]` 列表字面量与 await 元素全丢，退化为 `await g(); await h(); r = []`） |
| 11 | test_adv05_augassign_attr_chain.py | TestAdv05AugassignAttrChain | 字节码不等价（`a.b.c += 1` 中间属性 `b` 丢失变 `a.c += 1`，LOAD_ATTR b 丢失） |

## 本轮通过的测试（不计入错误，仅作覆盖参考）

- test_adv05_try_finally_no_except.py（if 体内 try-finally 无 except，通过）
- test_adv05_del_attr_chain.py（`del a.b.c`，通过 — STORE_ATTR 链 del 已支持）
- test_adv05_global_decl.py（if 体内 global 声明，通过）
- test_adv05_nonlocal_decl.py（if 体内 nonlocal 声明，通过）
- test_adv05_with_multi_ctx.py（`with a as x, b as y:` 多上下文，通过）
- test_adv05_listcomp_if_filter.py（`[x for x in s if x > 0]`，通过）
- test_adv05_starred_assign.py（`a, *b = d`，通过 — UNPACK_EX 已支持）
- test_adv05_paren_tuple_assign.py（`(a, b) = (1, 2)`，通过）
- test_adv05_complex_literal.py（`z = 1 + 2j`，通过）
- test_adv05_lambda_posonly.py（`(lambda x, /: x+1)(5) > 3`，通过）
- test_adv05_assert_message.py（`assert x > 0, 'positive'`，通过）
- test_adv05_ellipsis_expr.py（`x = ...`，通过）
- test_adv05_nested_list_literal.py（`r = [[a, b], [c, d]]`，通过）

---

## 错误详细记录

### 错误 01 — if 体内 `from m import x as y`，asname y 丢失变 `from m import x`

- 文件：test_adv05_import_asname.py
- 源码：
  ```python
  if c:
      from m import x as y
  ```
- 期望反编译：保留 `from m import x as y`（IMPORT_FROM + STORE_NAME y）
- 实际反编译：
  ```python
  if c:
      from m import x
  ```
- 失败信息：指令6参数不匹配：`y vs x (op=STORE_NAME)`（原始 `IMPORT_FROM x` + `STORE_NAME y`；重编 `STORE_NAME x`，asname 丢失）
- 根因初判：`from m import x as y` 字节码为 `IMPORT_NAME m` + `IMPORT_FROM x` + `STORE_NAME y` + `POP_TOP`。if body 区域分析识别 `IMPORT_FROM` 时，把 `IMPORT_FROM` 的参数 `x` 直接当作 STORE 目标，丢失了真正的 STORE_NAME 目标 `y`。`_build_statement` 对 IMPORT_FROM 后接 STORE_NAME 的 asname 模式重建缺失。前 4 轮未覆盖 import-from asname 在 if body 中。

### 错误 02 — if 体内嵌套 lambda，内层 lambda 走占位路径

- 文件：test_adv05_nested_lambda.py
- 源码：
  ```python
  if c:
      f = lambda x: (lambda y: x + y)
  ```
- 期望反编译：保留嵌套 lambda `lambda x: (lambda y: x + y)`，内层 lambda 捕获外层 x
- 实际反编译：
  ```python
  if c:
      f = lambda x: (lambda *args, **kwargs: None)
  ```
- 失败信息：嵌套 code object 不匹配（指令2）：指令数不匹配 7 vs 4（原始内层 lambda 7 条 `MAKE_CELL/RESUME/LOAD_CLOSURE/BUILD_TUPLE/LOAD_CONST/MAKE_FUNCTION/RETURN_VALUE`；重编 4 条 `RESUME/LOAD_CONST/MAKE_FUNCTION/RETURN_VALUE`，闭包与代码对象全丢）
- 根因初判：嵌套 lambda `lambda y: x + y` 捕获外层 x，字节码走 `MAKE_CELL` + `LOAD_CLOSURE` + `BUILD_TUPLE` 闭包路径。if body 区域分析对嵌套 lambda code object 的反编译走了「未知 lambda」占位路径 `lambda *args, **kwargs: None`，丢失原始形参 y 与函数体 `x + y`，且未处理闭包绑定。与 R1 错误 03/12（lambda 调用条件中 lambda 体被占位）同源 — 都是 lambda code object 走占位路径，但本例是 if body 中嵌套 lambda（外层 lambda 正确，内层 lambda 占位）。R4 错误 13 修复了 lambda 默认值在 if 条件中；未覆盖嵌套 lambda 在 if body 中。

### 错误 03 — if 体内 setcomp 多 for 子句，第二 for 退化为元组解包

- 文件：test_adv05_setcomp_multi_for.py
- 源码：
  ```python
  if c:
      r = {x + y for x in a for y in b}
  ```
- 期望反编译：保留 `{x + y for x in a for y in b}`（两个 for 子句）
- 实际反编译：
  ```python
  if c:
      r = {x + y for x, y in a}
  ```
- 失败信息：嵌套 code object 不匹配（指令2）：指令数不匹配 12 vs 11（原始含 `GET_ITER` + `STORE_FAST y` 第二个 for 子句；重编改为 `UNPACK_SEQUENCE` + `STORE_FAST y`，第二个 `GET_ITER` 丢失，把两个 for 子句误判为元组解包 `for x, y in a`）
- 根因初判：setcomp 多 for 子句 `{x+y for x in a for y in b}` 的字节码含两个独立的 `GET_ITER` + `FOR_ITER` 块。if body 区域分析对 setcomp 第二个 `GET_ITER`（针对源 b）的识别失败，把它与前一个 `STORE_FAST x` 组合误判为 `UNPACK_SEQUENCE`（元组解包 `x, y`），导致第二个迭代源 b 丢失，整体退化为 `for x, y in a`。前 4 轮未覆盖 setcomp 多 for 子句在 if body 中。

### 错误 04 — if 体内 dictcomp + walrus，walrus 丢失变裸调用

- 文件：test_adv05_dictcomp_walrus.py
- 源码：
  ```python
  if c:
      r = {k: (v := f(k)) for k in s}
  ```
- 期望反编译：保留 `{k: (v := f(k)) for k in s}`（dictcomp 内 walrus 绑定）
- 实际反编译：
  ```python
  if c:
      r = {k: f(k) for k in s}
  ```
- 失败信息：嵌套 code object 不匹配（指令2）：指令数不匹配 13 vs 11（原始含 `COPY` + `STORE_GLOBAL v` walrus 绑定块；重编缺这两条，walrus 退化为普通调用）
- 根因初判：dictcomp 中 walrus `(v := f(k))` 作 value，字节码在 `CALL` 后插入 `COPY` + `STORE_GLOBAL v`（walrus 副作用块）+ `MAP_ADD`。if body 区域分析对 dictcomp 内 walrus 求值块的识别失败，丢弃了 `COPY` + `STORE_GLOBAL v`，walrus 退化为普通调用 `f(k)`。R1-3 修复了 walrus 在 if 条件 / 下标 / 切片 / 链式比较等位置；R4 修复了 walrus 在 AugAssign 右值；均未覆盖 walrus 在推导式（dictcomp）value 位置。

### 错误 05 — if 体内 5 段链式比较作赋值右值，幽灵表达式 + 占位符泄漏

- 文件：test_adv05_chaincmp_5_levels.py
- 源码：
  ```python
  if c:
      z = 0 < a < b < c < d
  ```
- 期望反编译：保留 `z = 0 < a < b < c < d`（5 段链式比较作赋值右值）
- 实际反编译：
  ```python
  if c:
      (b < <copy_placeholder_2> and c < <copy_placeholder_2> and d)
      z = (0 < a < b < c < d)
  ```
- 失败信息：反编译结果语法错误：invalid syntax（`<copy_placeholder_2>` 不是合法标识符）
- 根因初判：5 段链式比较 `0 < a < b < c < d` 作赋值右值时，字节码含 4 次 `COMPARE_OP` + `JUMP_IF_FALSE_OR_POP` + 多个 `COPY`。if body 区域分析对 5 段（含 4 个 comparator）链式比较的中间操作数（COPY 暂存）重建失败，把中间 COPY 暂存变量当作独立表达式语句输出（含内部占位符 `<copy_placeholder_2>`），同时正确生成了 `z = (0 < a < b < c < d)` 赋值。这导致反编译结果出现「幽灵表达式」+ 内部占位符泄漏，语法错误无法编译。R1 错误 11 的 `<copy_placeholder_2>` 泄漏发生在 4 段链式 + `not` 的 if **条件**位置；R4 错误 04 的 3 段链式比较作赋值右值整条丢失变 `pass`。本例是 5 段链式 + 无 not + 赋值右值，新的失效模式（幽灵表达式 + 正确赋值并存）。

### 错误 06 — if 体内注解赋值 `x: int = 1`，SETUP_ANNOTATIONS 前导丢失

- 文件：test_adv05_ann_assign.py
- 源码：
  ```python
  if c:
      x: int = 1
  ```
- 期望反编译：保留 `x: int = 1`（带注解的赋值）
- 实际反编译：
  ```python
  if c:
      x = 1
      __annotations__['x'] = int
  ```
- 失败信息：指令数不匹配 13 vs 12（原始含 `SETUP_ANNOTATIONS` 前导；重编缺这条，注解被改为 `__annotations__['x'] = int` 独立语句）
- 根因初判：带注解的赋值 `x: int = 1` 字节码为 `SETUP_ANNOTATIONS` + `LOAD_NAME c` + `POP_JUMP_FORWARD_IF_FALSE` + `LOAD_CONST 1` + `STORE_NAME x` + `LOAD_NAME int` + `LOAD_NAME __annotations__` + `LOAD_CONST 'x'` + `STORE_SUBSCR`。`SETUP_ANNOTATIONS` 是模块/函数级前导指令（在 if 之前）。if body 区域分析对 `SETUP_ANNOTATIONS` 的处理失败 — 把注解的 `STORE_SUBSCR __annotations__['x']` 误判为独立赋值语句输出，且丢失了 `SETUP_ANNOTATIONS` 前导。R4 错误 09 修复了 Ellipsis 切片（BUILD_SLICE）；R4 错误 13 修复了 lambda defaults；均未覆盖 AnnAssign 在 if body 中。

### 错误 07 — if 体内 f-string 嵌套格式说明符，被误判为 dict 字面量

- 文件：test_adv05_fstring_format_spec.py
- 源码：
  ```python
  if c:
      s = f'{x:{width}.2f}'
  ```
- 期望反编译：保留 `f'{x:{width}.2f}'`（f-string 嵌套格式说明符）
- 实际反编译：
  ```python
  if c:
      s = {x:f'{width}.2f'}
  ```
- 失败信息：指令7操作码不匹配：`FORMAT_VALUE vs BUILD_MAP`（原始 `LOAD_NAME x` + `LOAD_NAME width` + `FORMAT_VALUE 0`（无格式） + `LOAD_CONST '.2f'` + `BUILD_STRING 2` + `FORMAT_VALUE 4`（with format）+ `STORE_NAME s`；重编 `BUILD_MAP`，f-string 退化为 dict 字面量 `{x: f'{width}.2f'}`）
- 根因初判：f-string `f'{x:{width}.2f}'` 含嵌套格式说明符 `{width}.2f`，字节码为 `LOAD x` + `LOAD width` + `FORMAT_VALUE 0`（把 width 格式化为字符串） + `LOAD_CONST '.2f'` + `BUILD_STRING 2`（拼接成 `{width}.2f` 格式说明符字符串）+ `FORMAT_VALUE 4`（用格式说明符格式化 x）。if body 区域分析对 `FORMAT_VALUE` + `BUILD_STRING` + `FORMAT_VALUE` 嵌套 f-string 序列的识别失败，把它误判为 `BUILD_MAP`（dict 字面量 `{x: f'{width}.2f'}`）。前 4 轮未覆盖 f-string 嵌套格式说明符在 if body 中。

### 错误 08 — if 体内 async with `as x` 绑定丢失

- 文件：test_adv05_async_with.py
- 源码：
  ```python
  async def f():
      if c:
          async with g() as x:
              y = x
  ```
- 期望反编译：保留 `async with g() as x:`（async with 带绑定）
- 实际反编译：
  ```python
  async def f():
      if c:
          async with g(): y = x
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令13操作码不匹配：`STORE_FAST vs POP_TOP`（原始 `BEFORE_ASYNC_WITH` + `GET_AWAITABLE` + `SEND/YIELD` + `STORE_FAST x`（as x 绑定）；重编 `STORE_FAST x` 退化为 `POP_TOP`，as x 绑定丢失）
- 根因初判：`async with g() as x:` 字节码在 `BEFORE_ASYNC_WITH` + await setup（`GET_AWAITABLE/SEND/YIELD/RESUME`）+ `STORE_FAST x`（as x 绑定）。if body 区域分析对 async with 的 `as x` 绑定识别失败，把 `STORE_FAST x` 退化为 `POP_TOP`（丢弃 await 返回的上下文管理器 `__aenter__` 结果）。async with 与 sync with 的字节码差异在于 `BEFORE_ASYNC_WITH` + await setup，本例揭示 async with 在 if body 中 `as` 绑定的丢失。R1/R3 修复了 await 作 if 条件；R4 修复了 await 作 if body 赋值右值；均未覆盖 async with 在 if body 中。

### 错误 09 — if 体内 async for 结构坍塌，迭代源退化为 None

- 文件：test_adv05_async_for.py
- 源码：
  ```python
  async def f():
      if c:
          async for x in g():
              y = x
  ```
- 期望反编译：保留 `async for x in g(): y = x`（async for 循环）
- 实际反编译：
  ```python
  async def f():
      if c:
          g()
          async for x in None:
              while True:
                  pass
              y = x
              continue
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令7操作码不匹配：`GET_AITER vs POP_TOP`（原始 `LOAD_GLOBAL g` + `PRECALL` + `CALL` + `GET_AITER` + `GET_ANEXT` + `LOAD_CONST` + `SEND` + `YIELD_VALUE` + `RESUME` + `STORE_FAST x`（async for setup）；重编 `g()` 提为独立语句，`GET_AITER` 退化为 `POP_TOP`，迭代源 `g()` 退化为 `None`，循环体还混入 `while True: pass`）
- 根因初判：`async for x in g():` 字节码为 `LOAD_GLOBAL g` + `PRECALL` + `CALL` + `GET_AITER` + `GET_ANEXT` + `SEND` + `YIELD_VALUE` + `RESUME` + `STORE_FAST x`（async for setup）。if body 区域分析对 async for 的 `GET_AITER/GET_ANEXT` 序列识别失败，把 `g()` 提为独立语句（其返回值被 `POP_TOP` 丢弃），`GET_AITER` 退化为 `POP_TOP`，迭代源退化为 `None`，循环体还混入 `while True: pass`。这是最严重的失效之一 — 不仅丢失 async for 语义，还生成了语义完全不同的 `async for x in None:` （这在 Python 中会抛 TypeError）。前 4 轮未覆盖 async for 在 if body 中。

### 错误 10 — if 体内 await 作列表元素，列表字面量与 await 全丢

- 文件：test_adv05_await_list_elem.py
- 源码：
  ```python
  async def f():
      if c:
          r = [await g(), await h()]
  ```
- 期望反编译：保留 `r = [await g(), await h()]`（列表字面量含多个 await 元素）
- 实际反编译：
  ```python
  async def f():
      if c:
          await g()
          await h()
          r = []
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 26 vs 28（原始含 `RETURN_GENERATOR/POP_TOP/RESUME` + 完整 `LOAD_GLOBAL g/PRECALL/CALL/GET_AWAITABLE/YIELD_VALUE` ×2 + `BUILD_LIST 2` + `STORE_FAST r`；重编多出 `POP_TOP`，列表字面量 `BUILD_LIST 2` 与 await 元素绑定全丢，await 退化为独立语句 `await g(); await h()`，赋值目标 r 变空列表 `[]`）
- 根因初判：`[await g(), await h()]` 列表字面量含两个 await 元素，字节码为 await setup（`GET_AWAITABLE/YIELD_VALUE`）×2 + `BUILD_LIST 2`。if body 区域分析对「await 元素 + BUILD_LIST」的列表字面量识别失败，把两个 await 提为独立语句（返回值被 POP_TOP 丢弃），列表字面量退化为空 `[]`。R1/R3 修复了 await 作 if 条件 / await in BoolOp / await in chained cmp；R4 修复了 await 作 if body 赋值右值；均未覆盖 await 作列表字面量元素在 if body 中。

### 错误 11 — if 体内 `a.b.c += 1`，中间属性 b 丢失

- 文件：test_adv05_augassign_attr_chain.py
- 源码：
  ```python
  if c:
      a.b.c += 1
  ```
- 期望反编译：保留 `a.b.c += 1`（多层属性链 AugAssign）
- 实际反编译：
  ```python
  if c:
      a.c += 1
  ```
- 失败信息：指令数不匹配 14 vs 13（原始含 `LOAD_NAME a` + `LOAD_ATTR b` + `COPY` + `LOAD_ATTR c` + `LOAD_CONST 1` + `BINARY_OP` + `SWAP` + `STORE_ATTR c`；重编缺 `LOAD_ATTR b`，中间属性 `b` 丢失，退化为 `a.c += 1`）
- 根因初判：`a.b.c += 1` 多层属性链 AugAssign 字节码为 `LOAD_NAME a` + `LOAD_ATTR b`（取 a.b）+ `COPY 1`（保留 a.b 用于 STORE_ATTR）+ `LOAD_ATTR c`（取 a.b.c）+ `LOAD_CONST 1` + `BINARY_OP +=` + `SWAP 2` + `STORE_ATTR c`（写回 a.b.c）。if body 区域分析对多层 `LOAD_ATTR` 链的 AugAssign 目标重建失败，丢弃了中间 `LOAD_ATTR b`，把 `a.b.c` 截断为 `a.c`。与 R4 错误 06/07/08（多层 BINARY_SUBSCR 链在 if body 中被截断）同源 — 都是「多层属性/下标访问链」在 if body 中被截断，但本例是属性链（LOAD_ATTR），R4 是下标链（BINARY_SUBSCR）。R4 错误 06 修复了 `d[k1][k2] += 1` 复合下标 AugAssign；未覆盖 `a.b.c += 1` 多层属性 AugAssign。

---

## 根因分类汇总

| 根因类别 | 涉及错误 | 说明 |
|----------|----------|------|
| if 体内「多层属性访问链」被截断 | 11 | `a.b.c += 1` 中间 LOAD_ATTR b 丢失，与 R4 多层 BINARY_SUBSCR 链截断同源，但本例是属性链 |
| if 体内「async 语义」整体未重建 | 8, 9, 10 | async with as 绑定丢失 / async for 结构坍塌 / await 作列表元素丢失 — R1-4 修复了 await 作条件/BoolOp/链式比较/rhs 赋值，未覆盖 async with / async for / await 作列表元素 |
| if 体内「推导式」 walrus 与多 for 子句未识别 | 3, 4 | setcomp 多 for 退化为元组解包 / dictcomp walrus 丢失 — R1-3 修复了 walrus 在条件/下标/切片/链式比较，R4 修复了 walrus 在 AugAssign；均未覆盖 walrus 在推导式 |
| if 体内「lambda code object」嵌套走占位路径 | 2 | 嵌套 lambda 内层走 `lambda *args, **kwargs: None` 占位，闭包信息全丢 — R1 修复了 lambda 调用条件占位，R4 修复了 lambda 默认值；未覆盖嵌套 lambda |
| if 体内「5 段链式比较」占位符泄漏 | 5 | 5 段链式比较作赋值右值产生幽灵表达式 + `<copy_placeholder_2>` 泄漏 — R1 错误 11 是 4 段 + not 在条件；R4 错误 04 是 3 段 rhs；本例是 5 段 + 无 not + rhs，新组合 |
| if 体内「特殊前导指令」未识别 | 1, 6 | `IMPORT_FROM x + STORE_NAME y` 误把 IMPORT_FROM 参数当 STORE 目标 / `SETUP_ANNOTATIONS` 前导丢失导致注解退化为 `__annotations__['x']=int` 独立语句 |
| if 体内「f-string 嵌套格式说明符」误判为 dict 字面量 | 7 | `FORMAT_VALUE + BUILD_STRING + FORMAT_VALUE` 嵌套序列误判为 `BUILD_MAP` dict 字面量 `{x: f'{width}.2f'}` |

## 与 Round 1-4 的关系

- 本轮 11 个错误均为 Round 1-4 **未覆盖**的新组合，且本轮系统性地把测试焦点从「if 条件 + if body 赋值族」扩展到「if body 内的特殊语句类型与构造指令族」：
  - **if 体内 async 语义族（错误 08, 09, 10）**：R1-4 修复了 await 作 if 条件 / await in BoolOp / await in 链式比较 / await 作 if body 赋值右值；本轮新增 async with `as` 绑定丢失（错误 08）、async for 结构坍塌（错误 09）、await 作列表元素丢失（错误 10）— 揭示 if body 区域分析对 async 上下文（BEFORE_ASYNC_WITH / GET_AITER / GET_ANEXT / await 元素 + BUILD_LIST）的系统性盲区
  - **if 体内推导式族（错误 03, 04）**：R1-3 修复了 walrus 在条件/下标/切片/链式比较；R4 修复了 walrus 在 AugAssign 右值；本轮新增 setcomp 多 for 子句（错误 03）、dictcomp + walrus（错误 04）— 揭示 if body 中推导式的多 for 子句与 walrus 在 value 位置的盲区
  - **if 体内属性/下标访问链扩展（错误 11）**：R4 修复了多层 BINARY_SUBSCR 链（`d[k1][k2] += 1` 复合下标 AugAssign / `d[a][b][c]=1` 多层下标赋值 / `del a[b][c]` 嵌套下标删除）；本轮新增多层 LOAD_ATTR 链（`a.b.c += 1` 多层属性 AugAssign）— 同源失效，但属性链与下标链是独立路径
  - **if 体内链式比较段数扩展（错误 05）**：R1 错误 11 是 4 段 + not 在条件；R4 错误 04 是 3 段 rhs 整条坍塌为 pass；本轮新增 5 段 + 无 not + rhs 的幽灵表达式 + 占位符泄漏模式 — 新失效模式（既生成正确赋值又额外泄漏幽灵表达式）
  - **if 体内 lambda 嵌套扩展（错误 02）**：R1 错误 03/12 是单层 lambda 调用条件走占位；R4 错误 13 修复了 lambda 默认值在 if 条件；本轮新增嵌套 lambda（外层正确、内层占位）在 if body — 新组合
  - **if 体内特殊前导/绑定指令族（错误 01, 06）**：R1-4 未覆盖 `IMPORT_FROM x + STORE_NAME y`（asname）与 `SETUP_ANNOTATIONS`（注解前导）— 揭示 if body 中 import-from asname 与 AnnAssign 的盲区
  - **if 体内 f-string 嵌套格式说明符（错误 07）**：R1-4 未触及 f-string 在 if body 中的反编译 — 揭示 `FORMAT_VALUE + BUILD_STRING + FORMAT_VALUE` 嵌套序列被误判为 `BUILD_MAP` dict 字面量的盲区

## 复现命令

```bash
# 单个
python -m pytest tests/exhaustive/if_region/test_adv05_import_asname.py -v
# 全部 adv05
python -m pytest tests/exhaustive/if_region/test_adv05_*.py -q
```

## 最终汇总运行结果

```
11 failed, 13 passed
```
