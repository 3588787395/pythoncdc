# IF 区域 第 7 轮 测试发现 (round_07)

- 测试日期：2026-07-18
- 基线：if_region 1 failed (test_adv03_nested_ternary_chain 遗留，可重测但不计入本轮) / 456 passed（Round 6 已完成全部 14/14 修复并 push 到远程 trae/agent-gUeaUE，git HEAD b340f2a）
- 本轮新增测试文件：26 个 `test_adv07_*.py`
- 确认错误数：**11**（全部失败；13 个通过的不计入；另有 2 个 SKIPPED 为反编译输出语法错误，见末尾「附加发现」）
- 验证方式：`ExhaustiveTestCase.verify_decompilation()` → `verify_bytecode_equivalence()`（对比原始字节码 vs 反编译后重编译字节码；过滤跳转/对齐指令）
- 约束遵守：未修改 `core/cfg/` 下任何源码，仅新增测试文件与本报告

## Round 1-6 已覆盖范围（本轮严格避开）

- R1：walrus+or/链式比较、await 条件/await+比较、lambda 调用条件、not+链式比较、not+BoolOp De Morgan、not+四段链式、三元条件（裸/嵌套）、CALL_FUNCTION_EX（`*args`/`**kwargs`）
- R2：walrus 下标（`d[(n := f())] > 0`）、is None/is not None BoolOp、await in BoolOp、三元 in BoolOp(and)/比较右侧/链式比较中段、not+三元
- R3：三元 wrapping（下标/属性/调用参数/is None/in/dict key/链式比较左操作数）、walrus 下标链式比较、嵌套三元链式比较、await 链式比较、walrus+await（match 误判）
- R4：tuple unpack、nested tuple unpack、multi-target chain rhs、chain-cmp rhs（3 段 `0<a<10`）、walrus augassign、compound augassign（`d[k1][k2]+=1`）、deep subscr assign、del nested subscr、ellipsis slice、paren-cmp false-positive、starred list cond、compound assert、lambda defaults、await rhs、yield rhs
- R5：import asname、nested lambda、setcomp multi-for、dictcomp walrus、5-level chain-cmp、ann-assign、fstring format-spec、async with as x、async for、await list-elem、augassign attr chain
- R6：chain is/in rhs、nested ternary rhs、yield-from rhs、lambda outer/kw defaults、walrus outside comp、await call/dict/tuple/subscr、fstring conversion/debug spec
- 已知遗留（不重测）：test_adv03_nested_ternary_chain（链式比较中嵌套三元，19 vs 3）

## 失败测试列表（11 个确认错误）

| # | 测试文件 | 类名 | 失败环节 |
|---|----------|------|----------|
| 1 | test_adv07_walrus_dict_key.py | TestAdv07WalrusDictKey | 字节码不等价（`{(n := f()): v}` walrus 退化独立赋值 `n = f()`，dict 字面量变空 `{}`，COPY+STORE+BUILD_MAP 全错位） |
| 2 | test_adv07_walrus_dict_value.py | TestAdv07WalrusDictValue | 字节码不等价（`{k: (n := f())}` walrus 退化独立赋值，dict 字面量变空 `{}`，同 #1 同源） |
| 3 | test_adv07_walrus_set_elem.py | TestAdv07WalrusSetElem | 字节码不等价（`{(n := f()), m}` walrus 退化独立赋值，set 字面量丢失变单元素 `r = m`，BUILD_SET 丢失） |
| 4 | test_adv07_chaincmp_in_list.py | TestAdv07ChaincmpInList | 字节码不等价（`x in [a, b] in cc` 中段列表字面量 `[a, b]` 丢失变 `x in a in cc`，BUILD_LIST 丢失） |
| 5 | test_adv07_import_star.py | TestAdv07ImportStar | 字节码不等价（`from m import *` 退化为 `import m`，IMPORT_STAR 丢失，`('*',)` vs None） |
| 6 | test_adv07_match_or_pattern.py | TestAdv07MatchOrPattern | 字节码不等价（`match x: case 1 | 2:` 误转为 `if (x == 1): ... elif 2: ...` + 末尾多余 `match x: case 1|2: pass`，21 vs 17） |
| 7 | test_adv07_raise_ternary_from.py | TestAdv07RaiseTernaryFrom | 字节码不等价（`raise E() from (a if cond else b)` 退化为函数调用 `E(a if cond else b)`，RAISE_VARARGS 与 from 子句全丢） |
| 8 | test_adv07_dictcomp_ternary_key.py | TestAdv07DictcompTernaryKey | 嵌套 code object 不匹配（`{(k if cond else m): v for k,v in items}` 三元 key 的 else 分支 `m` 变 `v`，value `v` 变 `None`，LOAD_GLOBAL vs LOAD_FAST） |
| 9 | test_adv07_lambda_walrus_body.py | TestAdv07LambdaWalrusBody | 嵌套 code object 不匹配（`lambda x: (n := x + 1)` lambda body 走占位路径变 `lambda x: None`，walrus 与 BinOp 全丢，7 vs 3） |
| 10 | test_adv07_await_walrus_value.py | TestAdv07AwaitWalrusValue | 嵌套 code object 不匹配（`r = (n := await g())` await 提为独立语句 `await g()`，walrus 绑定 `n` 与赋值目标 `r` 全丢，17 vs 15） |
| 11 | test_adv07_yieldfrom_call_arg.py | TestAdv07YieldFromCallArg | 嵌套 code object 不匹配（`r = g((yield from h()))` 外层调用 `g()` 全丢，变 `r = yield from h()`，PRECALL/CALL 调用块丢失，18 vs 15） |

## 本轮通过的测试（不计入错误，仅作覆盖参考）

- test_adv07_attr_subscr_chain.py（`a.b[c].d[e]` 属性+下标混合链，通过）
- test_adv07_bool_short_circuit_rhs.py（`a and b or cc` 短路作赋值右值，通过）
- test_adv07_ellipsis_mixed_slice.py（`x[..., 0, ..., 1]` 多 Ellipsis 混合切片，通过）
- test_adv07_import_multi_names.py（`from m import a, b, cc` 多名导入，通过）
- test_adv07_list_slice_method_call.py（`a[1:2].count(x)` 切片+方法调用，通过）
- test_adv07_listcomp_multi_if.py（`[x for x in y if x > 0 if x < 10]` 多重 if 过滤，通过）
- test_adv07_multidim_step_slice.py（`x[1:2:3, 4:5:6]` 多维带 step 切片，通过）
- test_adv07_setcomp_walrus.py（`{(n := f(x)) for x in y}` setcomp 带 walrus，通过）
- test_adv07_starred_tuple_value.py（`(a, *b, cc)` 星号作 tuple value，通过）
- test_adv07_match_mapping_pattern.py（`case {"k": v}:` mapping 解构，通过）
- test_adv07_fstring_multi_expr.py（`f"{a + b}{c * d}{e}"` 多表达式 f-string，通过）
- test_adv07_lambda_varargs.py（`lambda *a, **k: a` 带 *args/**kwargs，通过）
- test_adv07_dictcomp_ternary_value.py（`{k: (v if cond else w) ...}` 三元作 value，通过）

---

## 错误详细记录

### 错误 01 — if 体内 walrus 作 dict 字面量 key，`{(n := f()): v}` walrus 退化独立赋值，dict 变空

- 文件：test_adv07_walrus_dict_key.py
- 源码：
  ```python
  if c:
      r = {(n := f()): v}
  ```
- 期望反编译：保留 `r = {(n := f()): v}`（walrus 作 dict key）
- 实际反编译：
  ```python
  if c:
      n = f()
      r = {}
  ```
- 失败信息：指令数不匹配 15 vs 13（原始含 `LOAD_NAME f` + `PRECALL` + `CALL` + `COPY` + `STORE_NAME n`（walrus 副作用块）+ `LOAD_NAME v` + `BUILD_MAP` + `STORE_NAME r`；重编缺 `COPY` + `STORE_NAME n`，walrus 退化为独立赋值 `n = f()`，且 `BUILD_MAP` 操作数全丢，dict 变空 `{}`）
- 根因初判：`{(n := f()): v}` walrus 作 dict key 时，字节码为 `CALL` + `COPY` + `STORE_NAME n`（walrus 副作用块，保留值在栈上作 key）+ `LOAD_NAME v` + `BUILD_MAP`。if body 区域分析对「walrus 副作用块 + BUILD_MAP」的 dict 字面量识别失败，把 walrus 的 `COPY+STORE_NAME n` 提为独立赋值 `n = f()`，丢失了 dict 字面量的 key/value 操作数，dict 退化为空 `{}`。R6 错误 04 修复了 walrus 在「无赋值目标表达式语句」(n := f())；R5 错误 04 修复了 walrus 在 dictcomp value；均未覆盖 walrus 在 dict 字面量 key 位置（BUILD_MAP 路径）。

### 错误 02 — if 体内 walrus 作 dict 字面量 value，`{k: (n := f())}` walrus 退化独立赋值，dict 变空

- 文件：test_adv07_walrus_dict_value.py
- 源码：
  ```python
  if c:
      r = {k: (n := f())}
  ```
- 期望反编译：保留 `r = {k: (n := f())}`（walrus 作 dict value）
- 实际反编译：
  ```python
  if c:
      n = f()
      r = {}
  ```
- 失败信息：指令数不匹配 15 vs 13（原始含 `LOAD_NAME k` + `LOAD_NAME f` + `PRECALL` + `CALL` + `COPY` + `STORE_NAME n`（walrus 副作用块）+ `BUILD_MAP` + `STORE_NAME r`；重编缺 `COPY` + `STORE_NAME n`，walrus 退化为独立赋值，`BUILD_MAP` 操作数全丢，dict 变空 `{}`）
- 根因初判：与错误 01 同源。`{k: (n := f())}` walrus 作 dict value 时，字节码为 `LOAD k` + `CALL` + `COPY` + `STORE_NAME n`（walrus 副作用块，保留值在栈上作 value）+ `BUILD_MAP`。if body 区域分析对「walrus 副作用块 + BUILD_MAP」的 dict 字面量识别失败，walrus 退化为独立赋值，dict 变空。与错误 01 是同源失效（walrus 在 BUILD_MAP 路径的 key/value 位置），但本例是 value 位置，错误 01 是 key 位置，确认 BUILD_MAP 路径对 walrus 的系统性盲区。

### 错误 03 — if 体内 walrus 作 set 字面量元素，`{(n := f()), m}` walrus 退化独立赋值，set 丢失变单元素

- 文件：test_adv07_walrus_set_elem.py
- 源码：
  ```python
  if c:
      r = {(n := f()), m}
  ```
- 期望反编译：保留 `r = {(n := f()), m}`（walrus 作 set 元素）
- 实际反编译：
  ```python
  if c:
      n = f()
      r = m
  ```
- 失败信息：指令数不匹配 15 vs 13（原始含 `LOAD_NAME f` + `PRECALL` + `CALL` + `COPY` + `STORE_NAME n`（walrus 副作用块）+ `LOAD_NAME m` + `BUILD_SET` + `STORE_NAME r`；重编缺 `COPY` + `STORE_NAME n` + `BUILD_SET`，walrus 退化为独立赋值，set 字面量丢失变单元素赋值 `r = m`）
- 根因初判：`{(n := f()), m}` walrus 作 set 元素时，字节码为 `CALL` + `COPY` + `STORE_NAME n`（walrus 副作用块，保留值在栈上作 set 元素）+ `LOAD_NAME m` + `BUILD_SET`。if body 区域分析对「walrus 副作用块 + BUILD_SET」的 set 字面量识别失败，把 walrus 提为独立赋值，set 字面量 `BUILD_SET` 全丢，退化为单元素赋值 `r = m`。与错误 01/02 同源（walrus 在字面量构造指令 BUILD_MAP/BUILD_SET 路径），但本例是 BUILD_SET 路径，新组合。R5/R6 修复了 walrus 在推导式 value 与表达式语句，未覆盖 walrus 在 set/dict 字面量元素位置。

### 错误 04 — if 体内链式 `in` 比较中段为列表字面量，`x in [a, b] in cc` 列表丢失变 `x in a in cc`

- 文件：test_adv07_chaincmp_in_list.py
- 源码：
  ```python
  if c:
      z = x in [a, b] in cc
  ```
- 期望反编译：保留 `z = x in [a, b] in cc`（链式 in 比较中段为列表字面量）
- 实际反编译：
  ```python
  if c:
      z = (x in a in cc)
  ```
- 失败信息：指令数不匹配 19 vs 17（原始含 `LOAD x` + `LOAD a` + `LOAD b` + `BUILD_LIST` + `SWAP` + `COPY` + `CONTAINS_OP` + `JUMP_IF_FALSE_OR_POP` + `LOAD cc` + `CONTAINS_OP` + `SWAP` + `POP_TOP` + `STORE z`；重编缺 `LOAD b` + `BUILD_LIST`，列表字面量 `[a, b]` 丢失变单元素 `a`，链式比较中段从列表坍塌为单名字）
- 根因初判：`x in [a, b] in cc` 链式比较中段是列表字面量 `[a, b]`（`BUILD_LIST`），字节码在链式比较 setup（`SWAP/COPY/CONTAINS_OP/JUMP_IF_FALSE_OR_POP`）前插入 `BUILD_LIST`。if body 区域分析对「链式比较中段含 BUILD_LIST 列表字面量」的重建失败，丢弃了 `BUILD_LIST` 与列表元素 `b`，把中段列表坍塌为单元素 `a`。R6 错误 01/02 修复了 `a is b is c` / `a in b in cc` 链式比较作赋值右值，但中段都是单名字（LOAD_NAME）；本例中段是列表字面量（BUILD_LIST），新组合（链式比较中段为字面量构造指令）。

### 错误 05 — if 体内 `from m import *`，退化为 `import m`，IMPORT_STAR 丢失

- 文件：test_adv07_import_star.py
- 源码：
  ```python
  if c:
      from m import *
  ```
- 期望反编译：保留 `from m import *`（IMPORT_STAR）
- 实际反编译：
  ```python
  if c:
      import m
  ```
- 失败信息：指令3参数不匹配：`('*',) vs None (op=LOAD_CONST)`（原始 `LOAD_CONST 0` + `LOAD_CONST None` + `IMPORT_NAME m` + `LOAD_CONST ('*',)` + `IMPORT_STAR`；重编 `LOAD_CONST 0` + `LOAD_CONST None` + `IMPORT_NAME m` + `POP_TOP`，缺 `LOAD_CONST ('*',)` + `IMPORT_STAR`，import * 退化为 `import m`）
- 根因初判：`from m import *` 字节码为 `IMPORT_NAME m` + `LOAD_CONST ('*',)` + `IMPORT_STAR`（星号导入专用指令）。if body 区域分析对 `IMPORT_STAR` 指令的识别失败，把 `from m import *` 退化为普通 `import m`（丢弃 `IMPORT_STAR` 与 `('*',)` 常量）。R5 错误 01 修复了 `from m import x as y`（IMPORT_FROM + STORE_NAME asname 路径）；R5 通过的 import_multi_names 覆盖 `from m import a, b, cc`（多 IMPORT_FROM + STORE_NAME 路径）；均未覆盖 `from m import *`（IMPORT_STAR 路径），新组合。

### 错误 06 — if 体内 match-case or 模式，`case 1 | 2:` 误转为 if-elif-else + 末尾多余 match

- 文件：test_adv07_match_or_pattern.py
- 源码：
  ```python
  if c:
      match x:
          case 1 | 2:
              r = 'low'
          case _:
              r = 'other'
  ```
- 期望反编译：保留 `match x: case 1 | 2: r = 'low' case _: r = 'other'`（or 模式）
- 实际反编译：
  ```python
  if (x == 1):
      pass
  elif 2:
      pass
  else:
      r = 'other'
  match x:
      case 1 | 2:
          pass
  ```
- 失败信息：指令数不匹配 21 vs 17（原始含 `LOAD x` + `COPY` + `LOAD_CONST 1` + `COMPARE_OP` + `COPY` + `LOAD_CONST 2` + `COMPARE_OP` + `POP_TOP`×2 + `STORE r 'low'` + `STORE r 'other'`；重编把 match 误转为 `if (x == 1): pass elif 2: pass else: r='other'` + 末尾多余 `match x: case 1|2: pass`，match body 的 `r='low'` 丢失变 pass，or 模式 `1|2` 被拆为 if-elif）
- 根因初判：`match x: case 1 | 2:` or 模式字节码为 `LOAD x` + `COPY` + `LOAD_CONST 1` + `COMPARE_OP`（匹配 1）+ `COPY` + `LOAD_CONST 2` + `COMPARE_OP`（匹配 2）+ `POP_TOP`。if body 区域分析对 match-case or 模式（`|`）的重建失败，把 or 模式 `1 | 2` 误转为 `if (x == 1): ... elif 2: ...` 的 if-elif 链，且 match body `r = 'low'` 丢失变 `pass`，末尾还泄漏了残缺的 `match x: case 1|2: pass`。R6 通过的 match_guard（`case _ if x > 0:`）与 match_destructure（`case [a, b, *rest]:`）是单模式；本例是 or 模式（`1 | 2`），新组合，揭示 or 模式重建的系统性缺陷。

### 错误 07 — if 体内 raise from 三元表达式，`raise E() from (a if cond else b)` 退化为函数调用

- 文件：test_adv07_raise_ternary_from.py
- 源码：
  ```python
  if c:
      raise E() from (a if cond else b)
  ```
- 期望反编译：保留 `raise E() from (a if cond else b)`（raise from 三元）
- 实际反编译：
  ```python
  if c:
      E(a if cond else b)
  ```
- 失败信息：指令数不匹配 12 vs 14（原始含 `LOAD E` + `PRECALL` + `CALL`（构造 E）+ `LOAD a` + `LOAD cond` + `LOAD b` + `POP_JUMP_FORWARD_IF_FALSE`（三元）+ `RAISE_VARARGS 2`（raise from）；重编缺 `RAISE_VARARGS`，raise 退化为函数调用 `E(a if cond else b)`，from 子句与 raise 语义全丢，三元变成 E 的参数）
- 根因初判：`raise E() from (a if cond else b)` 字节码为 `LOAD E` + `PRECALL` + `CALL`（构造 E 实例）+ 三元 setup（`LOAD a` + `LOAD cond` + `LOAD b` + `POP_JUMP_FORWARD_IF_FALSE`）+ `RAISE_VARARGS 2`（raise from，栈顶两项为异常和 cause）。if body 区域分析对「raise from + 三元 cause 表达式」的重建失败，把 `RAISE_VARARGS` 丢弃，把整个 raise 表达式退化为函数调用 `E(...)`，且把三元 cause `(a if cond else b)` 错误地当作 E 的参数。R6 通过的 raise_complex_from（`raise E(a, b=k) from exc`）from 子句是简单 Name；本例 from 子句是三元表达式（IfExp），新组合，揭示 raise from + 复杂 cause 表达式的重建盲区。

### 错误 08 — if 体内 dictcomp 三元作 key，`{(k if cond else m): v ...}` 三元 key/value 错位

- 文件：test_adv07_dictcomp_ternary_key.py
- 源码：
  ```python
  if c:
      r = {(k if cond else m): v for k, v in items}
  ```
- 期望反编译：保留 `{(k if cond else m): v for k, v in items}`（dictcomp 三元 key）
- 实际反编译：
  ```python
  if c:
      r = {k if cond else v: None for k, v in items}
  ```
- 失败信息：嵌套 code object 不匹配（指令2）：指令8操作码不匹配：`LOAD_GLOBAL vs LOAD_FAST`（原始 dictcomp 内层含 `LOAD_FAST k` + `LOAD_GLOBAL cond` + `LOAD_FAST m`（三元 key）+ `LOAD_FAST v`（value）+ `MAP_ADD`；重编三元 key 的 else 分支 `m` 错位为 `v`，value `v` 错位为 `None`，LOAD_GLOBAL vs LOAD_FAST 错位）
- 根因初判：`{(k if cond else m): v for k, v in items}` dictcomp 的 key 是三元表达式 `(k if cond else m)`，value 是 `v`。dictcomp 内层字节码为三元 key setup + `LOAD v` + `MAP_ADD`。if body 区域分析对「dictcomp key 位置的三元表达式」重建失败，三元 key 的 else 分支 `m` 错位为 value 变量 `v`，value `v` 错位为 `None`，导致 key/value 绑定错乱。R5 错误 04 修复了 dictcomp + walrus 在 value 位置；R6 通过的 dictcomp_with_filter（`{k: v for k,v in items if k > 0}`）key/value 都是简单名字；本例 key 是三元表达式，新组合，揭示 dictcomp key 位置三元表达式重建的盲区。

### 错误 09 — if 体内 lambda body 含 walrus，`lambda x: (n := x + 1)` lambda body 走占位路径变 None

- 文件：test_adv07_lambda_walrus_body.py
- 源码：
  ```python
  if c:
      f = lambda x: (n := x + 1)
  ```
- 期望反编译：保留 `lambda x: (n := x + 1)`（lambda body 含 walrus）
- 实际反编译：
  ```python
  if c:
      f = lambda x: None
  ```
- 失败信息：嵌套 code object 不匹配（指令2）：指令数不匹配 7 vs 3（原始内层 lambda 7 条 `RESUME/LOAD_FAST x/LOAD_CONST 1/BINARY_OP/COPY/STORE_FAST n/RETURN_VALUE`；重编 3 条 `RESUME/LOAD_CONST None/RETURN_VALUE`，walrus 与 BinOp 全丢，lambda body 走占位路径变 `None`）
- 根因初判：`lambda x: (n := x + 1)` lambda body 是 walrus 表达式 `(n := x + 1)`，内层字节码为 `LOAD_FAST x` + `LOAD_CONST 1` + `BINARY_OP` + `COPY` + `STORE_FAST n`（walrus 副作用块）+ `RETURN_VALUE`。if body 区域分析对 lambda body 中的 walrus 表达式重建失败，走「未知 lambda body」占位路径 `lambda x: None`，walrus 与 BinOp 全丢。R1 错误 03/12 修复了 lambda 调用条件中 lambda body 占位；R5 错误 02 修复了嵌套 lambda 占位；R6 通过的 lambda_comprehension_body（`lambda x: [y for y in x if y > 0]`）body 是推导式；均未覆盖 lambda body 含 walrus（NamedExpr）的情况，新组合。

### 错误 10 — if 体内 await 作 walrus 值，`r = (n := await g())` await 提为独立语句，walrus 与赋值目标全丢

- 文件：test_adv07_await_walrus_value.py
- 源码：
  ```python
  async def f():
      if c:
          r = (n := await g())
      return r
  ```
- 期望反编译：保留 `r = (n := await g())`（await 作 walrus 值）
- 实际反编译：
  ```python
  async def f():
      if c:
          await g()
      return r
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 17 vs 15（原始含 `LOAD_GLOBAL g` + `PRECALL` + `CALL` + `GET_AWAITABLE` + `YIELD_VALUE` + `RESUME` + `COPY` + `STORE_FAST n`（walrus 副作用块）+ `STORE_FAST r`（赋值目标）；重编缺 `COPY` + `STORE_FAST n` + `STORE_FAST r`，多出 `POP_TOP`，await 提为独立语句 `await g()`，walrus 绑定 `n` 与赋值目标 `r` 全丢）
- 根因初判：`r = (n := await g())` await 作 walrus 值时，字节码为 await setup（`GET_AWAITABLE/YIELD_VALUE/RESUME`）+ `COPY` + `STORE_FAST n`（walrus 副作用块，保留值在栈上）+ `STORE_FAST r`（赋值目标）。if body 区域分析对「await + walrus 副作用块 + 赋值目标」的重建失败，把 await 提为独立语句（返回值被 POP_TOP 丢弃），walrus 绑定 `n` 与赋值目标 `r` 全丢。R6 错误 08/09/10/11 修复了 await 作调用参数/dict value/tuple 元素/下标；R6 错误 04 修复了 walrus 在表达式语句；均未覆盖 await 作 walrus 值（await + COPY+STORE walrus 副作用块组合），新组合。

### 错误 11 — if 体内 yield from 作函数调用参数，`r = g((yield from h()))` 外层调用全丢

- 文件：test_adv07_yieldfrom_call_arg.py
- 源码：
  ```python
  def f():
      if c:
          r = g((yield from h()))
      return r
  ```
- 期望反编译：保留 `r = g((yield from h()))`（yield from 作调用参数）
- 实际反编译：
  ```python
  def f():
      if c:
          r = yield from h()
      return r
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 18 vs 15（原始含 `LOAD_GLOBAL g` + `LOAD_GLOBAL h` + `PRECALL` + `CALL`（h）+ `GET_YIELD_FROM_ITER` + `LOAD_CONST None` + `SEND` + `YIELD_VALUE` + `RESUME` + `JUMP_BACKWARD_NO_INTERRUPT`（yield from setup）+ `PRECALL` + `CALL`（g）+ `STORE_FAST r`；重编缺 `LOAD_GLOBAL g` + `PRECALL` + `CALL`（g），外层调用 `g(...)` 全丢，yield from 提为赋值右值 `r = yield from h()`）
- 根因初判：`g((yield from h()))` yield from 作调用参数时，字节码为 `LOAD_GLOBAL g` + yield from setup（`GET_YIELD_FROM_ITER/SEND/YIELD_VALUE/RESUME`）+ `PRECALL` + `CALL`（g）+ `STORE_FAST r`。if body 区域分析对「yield from + 外层 PRECALL/CALL」的调用参数重建失败，把外层调用 `g(...)` 全丢，yield from 提为赋值右值 `r = yield from h()`。R6 错误 07 修复了 `x = yield from g()` yield from 作赋值右值（STORE_FAST x）；R6 错误 08 修复了 await 作调用参数；均未覆盖 yield from 作调用参数（yield from + 外层 CALL 组合），新组合。

---

## 附加发现（2 个 SKIPPED — 反编译输出含语法错误，是真实缺陷但测试框架 SKIP 不计为失败）

> 说明：`verify_bytecode_equivalence` 在 `compile(decompiled)` 抛 `SyntaxError` 时调用 `self.skipTest`，故这两例标 SKIPPED 而非 FAILED。但反编译输出确实生成了非法 Python（`break` outside loop），是真实的反编译器缺陷。

### 附加 S1 — if 体内 async with 多上下文管理器，`async with a as x, b as y:` 输出 `break` outside loop

- 文件：test_adv07_async_with_multi_ctx.py
- 源码：
  ```python
  async def f():
      if c:
          async with a as x, b as y:
              r = x + y
  ```
- 实际反编译（语法错误）：
  ```python
  async def f():
      if c:
          async with a as y:
              break          # ← 'break' outside loop，SyntaxError
              r = (x + y)
          async with b as x: pass
          None
  ```
- 根因初判：`async with a as x, b as y:` 多上下文管理器字节码为两个 `BEFORE_ASYNC_WITH` + await setup + `STORE_FAST` 绑定块。if body 区域分析对多上下文 async with 的重建失败：①把多上下文拆为两个独立 `async with`；②绑定变量错位（`a as y`、`b as x` 而非 `a as x`、`b as y`）；③在第一个 async with body 内插入非法 `break`；④末尾泄漏 `None`。R5 错误 08 修复了单 `async with g() as x:`；R5 通过的 with_multi_ctx 覆盖了同步 `with a as x, b as y:`；均未覆盖 async with 多上下文管理器，新组合。

### 附加 S2 — if 体内多层嵌套 async with，`async with a: async with b:` 输出 `break` outside loop

- 文件：test_adv07_nested_async_with.py
- 源码：
  ```python
  async def f():
      if c:
          async with a:
              async with b:
                  r = x
  ```
- 实际反编译（语法错误）：
  ```python
  async def f():
      if c:
          async with a:
              break          # ← 'break' outside loop，SyntaxError
              r = x
          async with b: pass
          None
  ```
- 根因初判：`async with a: async with b:` 嵌套 async with 字节码为外层 `BEFORE_ASYNC_WITH` + await setup + 内层 `BEFORE_ASYNC_WITH` + await setup。if body 区域分析对嵌套 async with 的重建失败：①把嵌套拆为两个独立 `async with`；②外层 body 内插入非法 `break`；③末尾泄漏 `None`。R6 通过的 nested_with 覆盖了同步 `with a as x: with b as y:`；R5 错误 08 修复了单 async with as 绑定；均未覆盖嵌套 async with，新组合，与 S1 同源（async with 嵌套/多上下文重建的系统性盲区）。

---

## 根因分类汇总

| 根因类别 | 涉及错误 | 说明 |
|----------|----------|------|
| if 体内「walrus 副作用块 + 字面量构造指令（BUILD_MAP/BUILD_SET）」未识别 | 01, 02, 03 | walrus 作 dict key / dict value / set 元素，COPY+STORE 副作用块被提为独立赋值，字面量变空 / 丢失。R5/R6 修复了 walrus 在推导式 value 与表达式语句，未覆盖 walrus 在 dict/set 字面量元素位置 |
| if 体内「链式比较中段为字面量构造指令」未识别 | 04 | `x in [a, b] in cc` 中段列表字面量 BUILD_LIST 丢失变单名字。R6 修复了链式 is/in 中段为单名字，未覆盖中段为字面量 |
| if 体内「特殊导入/匹配/异常指令」未识别 | 05, 06, 07 | `IMPORT_STAR` 退化为 import / match or 模式误转为 if-elif-else + 残缺 match / raise from 三元退化为函数调用 |
| if 体内「推导式 key/value 位置复杂表达式」未识别 | 08 | dictcomp 三元作 key 导致 key/value 错位。R5 修复了 dictcomp walrus value，未覆盖 key 位置三元 |
| if 体内「lambda body 含 walrus」走占位路径 | 09 | `lambda x: (n := x + 1)` body 走 `lambda x: None` 占位。R1/R5 修复了 lambda 调用条件/嵌套 lambda 占位，未覆盖 body 含 walrus |
| if 体内「suspendable 表达式 + walrus/外层调用」组合未识别 | 10, 11 | await 作 walrus 值（await + COPY+STORE walrus 块）/ yield from 作调用参数（yield from + 外层 CALL）。R6 修复了 await 作调用参数/dict/tuple/subscr 与 yield from 作赋值右值，未覆盖 await 作 walrus 值与 yield from 作调用参数 |
| if 体内「async with 嵌套/多上下文」输出非法 `break`（SKIPPED） | S1, S2 | 多上下文 / 嵌套 async with 重建失败，输出 `break` outside loop 语法错误。R5 修复了单 async with as，未覆盖 async with 嵌套/多上下文 |

## 与 Round 1-6 的关系

- 本轮 11 个错误 + 2 个附加 SKIPPED 均为 Round 1-6 **未覆盖**的新组合，且本轮系统性地把测试焦点扩展到「if 体内字面量构造 + walrus 副作用块族 / 链式比较中段字面量族 / 特殊语句指令族 / 推导式 key 复杂表达式族 / lambda body walrus 族 / suspendable + walrus/调用组合族 / async with 嵌套族」：
  - **walrus 在字面量构造指令族（错误 01, 02, 03）**：R6 错误 04 修复了 walrus 在「无赋值目标表达式语句」(n := f())；R5 错误 04 修复了 walrus 在 dictcomp value；本轮新增 walrus 在 dict 字面量 key（错误 01）、dict 字面量 value（错误 02）、set 字面量元素（错误 03）— 揭示 walrus 副作用块（COPY+STORE）与 BUILD_MAP/BUILD_SET 字面量构造指令组合的系统性盲区
  - **链式比较中段字面量族（错误 04）**：R6 错误 01/02 修复了 `a is b is c` / `a in b in cc` 链式比较作赋值右值，中段都是单名字（LOAD_NAME）；本轮新增中段为列表字面量 `[a, b]`（BUILD_LIST）— 揭示链式比较 setup 与字面量构造指令组合的盲区
  - **特殊语句指令族（错误 05, 06, 07）**：R5 错误 01 修复了 `from m import x as y`（IMPORT_FROM + STORE_NAME asname）；本轮新增 `from m import *`（IMPORT_STAR 路径，错误 05）；R6 通过的 match_guard/match_destructure 是单模式，本轮新增 match or 模式 `case 1 | 2`（错误 06，误转为 if-elif-else）；R6 通过的 raise_complex_from 的 from 子句是简单 Name，本轮新增 raise from 三元 cause 表达式（错误 07，退化为函数调用）— 揭示 IMPORT_STAR / match or 模式 / raise from 复杂 cause 的重建盲区
  - **推导式 key 复杂表达式族（错误 08）**：R5 错误 04 修复了 dictcomp walrus value；R6 通过的 dictcomp_with_filter 的 key/value 是简单名字；本轮新增 dictcomp key 位置三元表达式 — 揭示 dictcomp key 位置复杂表达式的重建盲区
  - **lambda body walrus 族（错误 09）**：R1 错误 03/12 修复了 lambda 调用条件占位；R5 错误 02 修复了嵌套 lambda 占位；本轮新增 lambda body 含 walrus（NamedExpr）走占位 — 新组合
  - **suspendable + walrus/调用组合族（错误 10, 11）**：R6 错误 08-11 修复了 await 作调用参数/dict/tuple/subscr；R6 错误 07 修复了 yield from 作赋值右值；本轮新增 await 作 walrus 值（错误 10，await + COPY+STORE walrus 块）/ yield from 作调用参数（错误 11，yield from + 外层 CALL）— 新组合
  - **async with 嵌套族（附加 S1, S2）**：R5 错误 08 修复了单 `async with g() as x:`；R5 通过的 with_multi_ctx 覆盖同步多上下文；R6 通过的 nested_with 覆盖同步嵌套；本轮新增 async with 多上下文（S1）/ async with 嵌套（S2）— 揭示 async with 嵌套/多上下文重建输出非法 `break` 的严重缺陷

## 复现命令

```bash
# 单个
python -m pytest tests/exhaustive/if_region/test_adv07_walrus_dict_key.py -v
# 全部 adv07
python -m pytest tests/exhaustive/if_region/test_adv07_*.py -q
```

## 最终汇总运行结果

```
11 failed, 13 passed, 2 skipped
```
