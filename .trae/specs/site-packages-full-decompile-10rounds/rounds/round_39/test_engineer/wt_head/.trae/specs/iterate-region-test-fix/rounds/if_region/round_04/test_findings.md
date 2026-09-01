# IF 区域 第 4 轮 测试发现 (round_04)

- 测试日期：2026-07-18
- 基线：if_region 1 failed (test_adv03_nested_ternary_chain 遗留) / 376 passed（Round 3 已提交+推送，git HEAD 17ccc7e）
- 本轮新增测试文件：18 个 `test_adv04_*.py`
- 确认错误数：**15**（全部失败；3 个通过的不计入：walrus_const_match / elif_chain_cmp / raise_from）
- 验证方式：`ExhaustiveTestCase.verify_decompilation()` → `verify_bytecode_equivalence()`（对比原始字节码 vs 反编译后重编译字节码；过滤跳转/对齐指令）
- 约束遵守：未修改 `core/cfg/` 下任何源码，仅新增测试文件与本报告

## Round 1-3 已覆盖范围（本轮严格避开）

- R1：walrus+or/链式比较、await 条件/await+比较、lambda 调用条件、not+链式比较、not+BoolOp De Morgan、not+四段链式、三元条件（裸/嵌套）、CALL_FUNCTION_EX（`*args`/`**kwargs`）
- R2：walrus 下标（`d[(n := f())] > 0`）、is None/is not None BoolOp、await in BoolOp、三元 in BoolOp(and)/比较右侧/链式比较中段、not+三元
- R3：三元 wrapping（下标/属性/调用参数/is None/in/dict key/链式比较左操作数）、walrus 下标链式比较、嵌套三元链式比较、await 链式比较、walrus+await（match 误判）
- 已知遗留（不重测）：test_adv03_nested_ternary_chain（`if 0 < (a if (b if c else d) else e) < 10`，19 vs 3）

## 失败测试列表（15 个确认错误）

| # | 测试文件 | 类名 | 失败环节 |
|---|----------|------|----------|
| 1 | test_adv04_tuple_unpack_body.py | TestAdv04TupleUnpackBody | 字节码不等价（`a, b = d, e` 坍塌为 `a = e`，b/d 丢失） |
| 2 | test_adv04_nested_tuple_unpack.py | TestAdv04NestedTupleUnpack | 字节码不等价（嵌套元组解包整条赋值丢失变 `pass`，12 vs 6） |
| 3 | test_adv04_multi_target_chain_rhs.py | TestAdv04MultiTargetChainRhs | 字节码不等价（多目标链 `a=b=cc=d[k]` 坍塌为 `a=d[k]`，b/cc 丢失） |
| 4 | test_adv04_chain_cmp_rhs.py | TestAdv04ChainCmpRhs | 字节码不等价（链式比较作右值 `z=0<a<10` 整条赋值丢失变 `pass`，17 vs 6） |
| 5 | test_adv04_walrus_augassign.py | TestAdv04WalrusAugassign | 字节码不等价（`y += (n := f())` AugAssign 丢失变 `n = f()`，y 与 += 丢失） |
| 6 | test_adv04_compound_augassign.py | TestAdv04CompoundAugassign | 字节码不等价（`d[k1][k2] += 1` 第二层下标 [k2] 丢失变 `d[k1] += 1`） |
| 7 | test_adv04_deep_subscr_assign.py | TestAdv04DeepSubscrAssign | 字节码不等价（`d[a][b][c]=1` 严重坍塌为 `None[c]=b`，容器与多层下标丢失） |
| 8 | test_adv04_del_nested_subscr.py | TestAdv04DelNestedSubscr | 字节码不等价（`del a[b][c]` 坍塌为 `del b[c]`，容器 a 与第一层 [b] 丢失） |
| 9 | test_adv04_ellipsis_slice.py | TestAdv04EllipsisSlice | 字节码不等价（`a[..., 0]` 切片变元组下标 `a[(Ellipsis, 0)]`） |
| 10 | test_adv04_paren_cmp_chain.py | TestAdv04ParenCmpChain | 字节码不等价（`(a==b)==(c==d)` 误判为链式比较 `a==b==c==d`，语义改变，12 vs 19） |
| 11 | test_adv04_starred_list_cond.py | TestAdv04StarredListCond | 字节码不等价（`if [a, *b, c]:` 列表字面量丢失变 `if c:`，星号解包丢失，11 vs 6） |
| 12 | test_adv04_assert_chain_cmp.py | TestAdv04AssertChainCmp | 字节码不等价（`assert 0<a<10` 链式比较条件丢失变 `raise AssertionError`，16 vs 6） |
| 13 | test_adv04_lambda_defaults.py | TestAdv04LambdaDefaults | 字节码不等价（`lambda x=1, y=2` 默认值 1/2 丢失变 `lambda x, y`） |
| 14 | test_adv04_await_rhs_assign.py | TestAdv04AwaitRhsAssign | 字节码不等价（`x = await g()` 赋值目标 x 丢失变 `await g()` 独立语句） |
| 15 | test_adv04_yield_rhs_assign.py | TestAdv04YieldRhsAssign | 字节码不等价（`x = yield g()` 内部 AST dict 泄露到输出，12 vs 17，最严重） |

## 本轮通过的测试（不计入错误，仅作覆盖参考）

- test_adv04_walrus_const_match.py（`if (n := 1) > 0:`，通过 — walrus 绑定常量不触发 match 误判）
- test_adv04_elif_chain_cmp.py（`if a: ... elif 0 < b < 10: ...`，通过 — elif 链中链式比较已支持）
- test_adv04_raise_from.py（`raise E() from e`，通过 — raise-from 已支持）

---

## 错误详细记录

### 错误 01 — if 体内元组解包赋值，`a, b = d, e` 坍塌为 `a = e`

- 文件：test_adv04_tuple_unpack_body.py
- 源码：
  ```python
  if c:
      a, b = d, e
  ```
- 期望反编译：保留 `a, b = d, e`（元组解包）
- 实际反编译：
  ```python
  if c:
      a = e
  ```
- 失败信息：指令数不匹配 11 vs 8（原始含 `LOAD_NAME d` + `LOAD_NAME e` + `SWAP` + `STORE_NAME a` + `STORE_NAME b`；重编缺 `LOAD_NAME d` 与 `SWAP`，只剩单 `STORE_NAME a`，目标 `b` 与右值 `d` 全丢）
- 根因初判：if 体内元组解包赋值 `a, b = d, e` 走 `UNPACK_SEQUENCE`/`SWAP`+多 `STORE` 路径。区域分析在 if body 中识别赋值时，把 SWAP+双 STORE 的元组解包误归约为单目标赋值，丢弃了 `b` 目标与 `d` 右值。前 3 轮聚焦 if 条件，未覆盖 if 体内的元组解包。

### 错误 02 — 嵌套元组解包，整条赋值丢失变 `pass`

- 文件：test_adv04_nested_tuple_unpack.py
- 源码：
  ```python
  if c:
      (a, (b, cc)) = (1, (2, 3))
  ```
- 期望反编译：保留 `(a, (b, cc)) = (1, (2, 3))` 嵌套元组解包
- 实际反编译：
  ```python
  if c:
      pass
  ```
- 失败信息：指令数不匹配 12 vs 6（原始含 `LOAD_CONST (1,(2,3))` + `UNPACK_SEQUENCE` + `STORE a` + `UNPACK_SEQUENCE` + `STORE b` + `STORE cc`；重编仅 `RESUME/LOAD_NAME c/LOAD_CONST None/RETURN_VALUE`，整条嵌套解包坍塌为 `pass`）
- 根因初判：嵌套元组解包 `(a, (b, cc)) = (1, (2, 3))` 走两层 `UNPACK_SEQUENCE`。if body 区域分析对嵌套 UNPACK_SEQUENCE 的目标重建失败，整条赋值被丢弃输出 `pass`。比错误 01（扁平解包）更严重 — 扁平解包至少保留了部分语义，嵌套解包完全坍塌。

### 错误 03 — 多目标链带下标右值，`a = b = cc = d[k]` 坍塌为 `a = d[k]`

- 文件：test_adv04_multi_target_chain_rhs.py
- 源码：
  ```python
  if c:
      a = b = cc = d[k]
  ```
- 期望反编译：保留 `a = b = cc = d[k]` 多目标链
- 实际反编译：
  ```python
  if c:
      a = d[k]
  ```
- 失败信息：指令数不匹配 14 vs 10（原始含 `LOAD_NAME d` + `LOAD_NAME k` + `BINARY_SUBSCR` + `COPY` + `STORE a` + `COPY` + `STORE b` + `STORE cc`；重编缺 `COPY`×2 + `STORE b` + `STORE cc`，多目标链 `b`/`cc` 全丢）
- 根因初判：多目标链 `a = b = cc = d[k]` 走 `COPY`+多 `STORE` 路径。if body 区域分析对 `COPY`+多 STORE 的多目标链重建失败，只保留首目标 `a`，丢弃 `b`/`cc`。与错误 01（元组解包 SWAP+STORE）同源 — 都是「多 STORE 目标」在 if body 中被归约为单目标。

### 错误 04 — 链式比较作赋值右值，`z = 0 < a < 10` 整条丢失变 `pass`

- 文件：test_adv04_chain_cmp_rhs.py
- 源码：
  ```python
  if c:
      z = 0 < a < 10
  ```
- 期望反编译：保留 `z = 0 < a < 10`（链式比较作赋值右值）
- 实际反编译：
  ```python
  if c:
      pass
  ```
- 失败信息：指令数不匹配 17 vs 6（原始含 `LOAD_CONST 0` + `LOAD_NAME a` + `SWAP/COPY` + `COMPARE_OP` + `JUMP_IF_FALSE_OR_POP` + `LOAD_CONST 10` + `COMPARE_OP` + `SWAP` + `POP_TOP` + `STORE z`；重编仅 6 条 `RESUME/LOAD_NAME c/LOAD_CONST None/RETURN_VALUE`，整条赋值坍塌为 `pass`）
- 根因初判：链式比较 `0 < a < 10` 作赋值右值时，if body 区域分析对 `SWAP/COPY`+`COMPARE_OP`×2+`JUMP_IF_FALSE_OR_POP` 的链式比较表达式重建失败。前 3 轮的链式比较修复都集中在 if **条件**位置（`_try_build_walrus_chained_compare` 等），if **体内**作为赋值右值的链式比较未覆盖，整条赋值丢失。

### 错误 05 — walrus + AugAssign，`y += (n := f())` AugAssign 丢失变 `n = f()`

- 文件：test_adv04_walrus_augassign.py
- 源码：
  ```python
  if c:
      y += (n := f())
  ```
- 期望反编译：保留 `y += (n := f())`（AugAssign 右值为 walrus）
- 实际反编译：
  ```python
  if c:
      n = f()
  ```
- 失败信息：指令数不匹配 15 vs 11（原始含 `LOAD_NAME y` + `PUSH_NULL` + `LOAD_NAME f` + `PRECALL` + `CALL` + `COPY` + `STORE n` + `BINARY_OP` + `STORE y`；重编缺 `LOAD_NAME y` + `COPY` + `BINARY_OP` + `STORE y`，AugAssign 退化为 `n = f()` 独立赋值，目标 `y` 与 `+=` 操作丢失）
- 根因初判：AugAssign 右值为 walrus `y += (n := f())` 时，`COPY`+`STORE n` 的 walrus 求值块与 `BINARY_OP`+`STORE y` 的 AugAssign 更新块叠加。if body 区域分析把 walrus 的 `STORE n` 当作独立赋值目标，丢弃了 AugAssign 的 `LOAD y`+`BINARY_OP`+`STORE y`。前 3 轮未覆盖 walrus 在 AugAssign 右值位置。

### 错误 06 — 复合目标 AugAssign，`d[k1][k2] += 1` 第二层下标丢失

- 文件：test_adv04_compound_augassign.py
- 源码：
  ```python
  if c:
      d[k1][k2] += 1
  ```
- 期望反编译：保留 `d[k1][k2] += 1`（复合下标目标 AugAssign）
- 实际反编译：
  ```python
  if c:
      d[k1] += 1
  ```
- 失败信息：指令数不匹配 18 vs 16（原始含 `LOAD d` + `LOAD k1` + `BINARY_SUBSCR` + `LOAD k2` + `COPY/COPY` + `BINARY_SUBSCR` + `LOAD_CONST 1` + `BINARY_OP` + `SWAP/SWAP` + `STORE_SUBSCR`；重编缺 `LOAD k2` + `BINARY_SUBSCR`，第二层下标 `[k2]` 丢失，退化为 `d[k1] += 1`）
- 根因初判：复合下标目标 `d[k1][k2] += 1` 的 AugAssign 走 `COPY/COPY` 保留复合目标 + 双 `BINARY_SUBSCR`/`STORE_SUBSCR` 路径。if body 区域分析对复合下标目标的 AugAssign 重建时丢失了内层 `BINARY_SUBSCR`（[k2]），只保留外层 `[k1]`。与错误 07（多层下标赋值）同源 — 都是「多层 BINARY_SUBSCR 链」在 if body 中被截断。

### 错误 07 — 多层下标赋值，`d[a][b][c] = 1` 严重坍塌为 `None[c] = b`

- 文件：test_adv04_deep_subscr_assign.py
- 源码：
  ```python
  if c:
      d[a][b][c] = 1
  ```
- 期望反编译：保留 `d[a][b][c] = 1`（3 层下标赋值）
- 实际反编译：
  ```python
  if c:
      None[c] = b
  ```
- 失败信息：指令数不匹配 14 vs 10（原始含 `LOAD d` + `LOAD a` + `BINARY_SUBSCR` + `LOAD b` + `BINARY_SUBSCR` + `LOAD c` + `STORE_SUBSCR`；重编缺 `LOAD d` + `BINARY_SUBSCR`×2，容器 `d` 变 `None`，下标 `a`/`b` 与常量 `1` 错位为 `None[c] = b`）
- 根因初判：3 层下标赋值 `d[a][b][c] = 1` 走 `LOAD d` + 双 `BINARY_SUBSCR` + `STORE_SUBSCR` 路径。if body 区域分析对多层 `BINARY_SUBSCR` 链的赋值目标重建失败，容器 `d` 与前两层下标丢失，目标坍塌为 `None[c]`，右值 `1` 与下标 `b` 错位。这是最严重的「目标重建失败」— 不仅丢指令，还生成了语义错误的 `None[c] = b`。

### 错误 08 — del 嵌套下标，`del a[b][c]` 坍塌为 `del b[c]`

- 文件：test_adv04_del_nested_subscr.py
- 源码：
  ```python
  if c:
      del a[b][c]
  ```
- 期望反编译：保留 `del a[b][c]`（嵌套下标删除）
- 实际反编译：
  ```python
  if c:
      del b[c]
  ```
- 失败信息：指令数不匹配 11 vs 9（原始含 `LOAD a` + `LOAD b` + `BINARY_SUBSCR` + `LOAD c` + `DELETE_SUBSCR`；重编缺 `LOAD a` + `BINARY_SUBSCR`，容器 `a` 与第一层下标 `[b]` 丢失，退化为 `del b[c]`）
- 根因初判：嵌套下标删除 `del a[b][c]` 走 `LOAD a` + `BINARY_SUBSCR` + `DELETE_SUBSCR` 路径。if body 区域分析对 del 的多层下标目标重建失败，丢弃了容器 `a` 与第一层 `BINARY_SUBSCR`，把第二层容器 `b` 误当顶层容器。与错误 07（多层下标赋值 STORE_SUBSCR）同源 — 都是「多层 BINARY_SUBSCR 链」在 if body 的 del/assign 中被截断，但 del 路径（DELETE_SUBSCR）与赋值路径（STORE_SUBSCR）是独立失效。

### 错误 09 — Ellipsis 切片，`a[..., 0]` 切片变元组下标

- 文件：test_adv04_ellipsis_slice.py
- 源码：
  ```python
  if c:
      x = a[..., 0]
  ```
- 期望反编译：保留 `x = a[..., 0]`（Ellipsis 切片）
- 实际反编译：
  ```python
  if c:
      x = a[(Ellipsis, 0)]
  ```
- 失败信息：指令数不匹配 10 vs 12（原始含 `LOAD a` + `LOAD_CONST Ellipsis` + `LOAD_CONST 0` + `BUILD_SLICE` + `BINARY_SUBSCR`；重编把 `Ellipsis, 0` 当作元组下标 `a[(Ellipsis, 0)]`，多出 `BUILD_TUPLE`，缺 `BUILD_SLICE`）
- 根因初判：`a[..., 0]` 多维切片含 `Ellipsis`，字节码用 `LOAD_CONST Ellipsis` + `LOAD_CONST 0` + `BUILD_SLICE` 表达。if body 区域分析把 `BUILD_SLICE` 的操作数误识别为 `BUILD_TUPLE` 元组下标，输出 `a[(Ellipsis, 0)]` 而非 `a[..., 0]`。前 3 轮的切片测试（R3 slice_walrus `a[1:(n := f())]`）只覆盖单冒号切片，未覆盖 `Ellipsis` 多维切片。

### 错误 10 — 括号比较 false-positive 链式误判，`(a==b)==(c==d)` 变 `a==b==c==d`

- 文件：test_adv04_paren_cmp_chain.py
- 源码：
  ```python
  if (a == b) == (c == d):
      pass
  ```
- 期望反编译：保留 `if (a == b) == (c == d):`（两个独立相等比较再相等）
- 实际反编译：
  ```python
  if (a == b == c == d):
      pass
  ```
- 失败信息：指令数不匹配 12 vs 19（原始 8 条核心指令 `LOAD a/LOAD b/COMPARE_OP/LOAD c/LOAD d/COMPARE_OP/COMPARE_OP/POP_TOP`；重编 15 条 — 误判为链式比较，多出 `SWAP/COPY`×2 + `COMPARE_OP` 链式 setup，输出 `a == b == c == d` 三段链式比较）
- 根因初判：`(a == b) == (c == d)` 两个相等比较结果再相等，字节码为 `COMPARE_OP`×3 顺序执行（无 SWAP/COPY 链式 setup）。if 条件分析把连续的 `COMPARE_OP` 误判为链式比较 `a == b == c == d`，注入了 `SWAP/COPY` 链式 setup 指令。这是「链式比较归约」的 false-positive — 前几轮修复了真链式比较的重建，但未防御「括号包裹的比较结果再比较」被误判为链式。语义完全改变（`a==b==c==d` 是链式比较，与 `(a==b)==(c==d)` 布尔相等语义不同）。

### 错误 11 — 星号解包列表字面量作条件，`if [a, *b, c]:` 列表丢失变 `if c:`

- 文件：test_adv04_starred_list_cond.py
- 源码：
  ```python
  if [a, *b, c]:
      pass
  ```
- 期望反编译：保留 `if [a, *b, c]:`（含星号解包的列表字面量）
- 实际反编译：
  ```python
  if c:
      pass
  ```
- 失败信息：指令数不匹配 11 vs 6（原始含 `LOAD a` + `BUILD_LIST` + `LOAD b` + `LIST_EXTEND` + `LOAD c` + `LIST_APPEND`；重编仅 `LOAD c`，列表字面量与星号解包全丢，退化为 `if c:`）
- 根因初判：`[a, *b, c]` 含星号解包的列表字面量走 `BUILD_LIST` + `LIST_EXTEND` + `LIST_APPEND` 路径。if 条件分析对 `LIST_EXTEND`/`LIST_APPEND` 的星号解包列表字面量重建失败，丢弃了 `BUILD_LIST`/`LIST_EXTEND` 与前两个元素，只保留末元素 `c` 作为条件。前 3 轮的列表字面量测试（R3 walrus_list_lit `[(n := f())]`）只覆盖单元素无星号列表，未覆盖星号解包。

### 错误 12 — assert 链式比较条件，`assert 0 < a < 10` 变 `raise AssertionError`

- 文件：test_adv04_assert_chain_cmp.py
- 源码：
  ```python
  if c:
      assert 0 < a < 10
  ```
- 期望反编译：保留 `assert 0 < a < 10`（链式比较作 assert 条件）
- 实际反编译：
  ```python
  if c:
      raise AssertionError
  ```
- 失败信息：指令数不匹配 16 vs 6（原始含 `LOAD_CONST 0` + `LOAD_NAME a` + `SWAP/COPY` + `COMPARE_OP` + `LOAD_CONST 10` + `COMPARE_OP` + `POP_TOP` + `LOAD_ASSERTION_ERROR` + `RAISE_VARARGS`；重编缺链式比较 6 条，只剩 `LOAD_ASSERTION_ERROR` + `RAISE_VARARGS`，assert 条件丢失变裸 `raise AssertionError`）
- 根因初判：`assert 0 < a < 10` 链式比较作 assert 条件，走 `SWAP/COPY`+`COMPARE_OP`×2 + `LOAD_ASSERTION_ERROR`+`RAISE_VARARGS` 路径。if body 区域分析对 assert 的链式比较条件重建失败，丢弃了链式比较段，只保留 `raise AssertionError`。与错误 04（链式比较作赋值右值）同源 — 都是「链式比较在 if body 内非 if 条件位置」未覆盖。

### 错误 13 — lambda 默认值丢失，`lambda x=1, y=2` 变 `lambda x, y`

- 文件：test_adv04_lambda_defaults.py
- 源码：
  ```python
  if (lambda x=1, y=2: x + y)():
      pass
  ```
- 期望反编译：保留 `if (lambda x=1, y=2: x + y)():`（带默认值的 lambda 立即调用）
- 实际反编译：
  ```python
  if (lambda x, y: x + y)():
      pass
  ```
- 失败信息：指令数不匹配 11 vs 10（原始含 `LOAD_CONST (1, 2)` 元组 + `LOAD_CONST <code>` + `MAKE_FUNCTION`；重编缺 `LOAD_CONST (1, 2)`，默认值 1/2 丢失，`MAKE_FUNCTION` 无默认值参数）
- 根因初判：`lambda x=1, y=2: ...` 的默认值通过 `LOAD_CONST (1, 2)` 元组 + `MAKE_FUNCTION` 传递。if 条件中 lambda 的 `MAKE_FUNCTION` 重建时丢失了默认值元组 `LOAD_CONST (1, 2)`，输出无默认值的 `lambda x, y`。R1 的 lambda 测试（lambda_call_cond / lambda_noarg_call_cond）覆盖了无参/带参调用，但未覆盖 lambda 自身的默认值签名。

### 错误 14 — await 作赋值右值，`x = await g()` 赋值目标 x 丢失

- 文件：test_adv04_await_rhs_assign.py
- 源码：
  ```python
  async def f():
      if c:
          x = await g()
      return x
  ```
- 期望反编译：保留 `x = await g()`（await 作赋值右值）
- 实际反编译：
  ```python
  async def f():
      if c:
          await g()
      return x
  ```
- 失败信息：嵌套 code object 不匹配（指令12）：`STORE_FAST vs POP_TOP`（原始 await 后 `STORE_FAST x` 保存到赋值目标；重编 await 后 `POP_TOP` 丢弃返回值，赋值目标 `x` 丢失，await 退化为独立语句）
- 根因初判：`x = await g()` 在 async 函数 if 体内，await 表达式作赋值右值。字节码为 `GET_AWAITABLE` + `YIELD_VALUE` + `RESUME` + `STORE_FAST x`。if body 区域分析把 await 表达式当作独立语句 `await g()`，丢弃了 `STORE_FAST x` 赋值目标。前 3 轮的 await 测试（R1 await_cond / R3 await_chaincmp / await_walrus）都集中在 await 作 if **条件**，未覆盖 await 作 if **体内**赋值右值。

### 错误 15 — yield 作赋值右值，内部 AST dict 泄露到输出（最严重）

- 文件：test_adv04_yield_rhs_assign.py
- 源码：
  ```python
  def f():
      if c:
          x = yield g()
      return x
  ```
- 期望反编译：保留 `x = yield g()`（yield 作赋值右值）
- 实际反编译：
  ```python
  def f():
      if c:
          x = {'type': 'Call', 'func': {'type': 'Name', 'id': 'g', 'ctx': 'Load', 'lineno': 3}, 'args': [], 'kwargs': [], 'lineno': None}
      return x
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 12 vs 17（原始含 `RETURN_GENERATOR` + `POP_TOP` + `RESUME` + `LOAD_GLOBAL g` + `PRECALL` + `CALL` + `YIELD_VALUE` + `STORE_FAST x`；重编 17 条含 `BUILD_CONST_KEY_MAP` + `BUILD_LIST`×2 + 多个 `LOAD_CONST`，明显是把内部 AST dict 表示当作字面量构造）
- 根因初判：`x = yield g()` 在生成器函数 if 体内，yield 表达式作赋值右值。生成器函数有 `RETURN_GENERATOR` 前导。if body 区域分析对 yield 表达式的 AST 节点重建失败，**直接把内部 AST dict 表示（`{'type': 'Call', 'func': {...}, ...}`）作为字符串赋值给 x**。这是本轮最严重的失效 — 不仅丢失 yield 语义，还泄露了内部 AST 数据结构到输出源码（生成了语法上「合法」但语义完全错误的 dict 字面量）。CodeGenerator 对未正确转化的 AST 节点 dict 缺乏防御性校验，直接 `str()` 输出。

---

## 根因分类汇总

| 根因类别 | 涉及错误 | 说明 |
|----------|----------|------|
| if 体内「多 STORE 目标」被归约为单目标 | 01, 02, 03 | 元组解包（SWAP+多 STORE）/ 嵌套元组解包（双层 UNPACK_SEQUENCE）/ 多目标链（COPY+多 STORE）在 if body 中都丢失多目标 |
| if 体内「多层 BINARY_SUBSCR 链」被截断 | 06, 07, 08 | 复合下标 AugAssign / 多层下标赋值 / 嵌套下标 del 都丢失内层 BINARY_SUBSCR |
| if 体内「链式比较在非条件位置」未重建 | 04, 12 | 链式比较作赋值右值 / 作 assert 条件都坍塌，前 3 轮链式比较修复仅覆盖 if 条件位置 |
| if 条件中「链式比较归约」false-positive | 10 | `(a==b)==(c==d)` 括号比较被误判为 `a==b==c==d` 链式比较，注入 SWAP/COPY |
| if 体内「suspendable 表达式作赋值右值」目标丢失 | 14, 15 | await / yield 作赋值右值时赋值目标丢失，yield 还泄露内部 AST dict |
| if 条件中「字面量构造指令」未识别 | 09, 11, 13 | Ellipsis 切片（BUILD_SLICE 误为 BUILD_TUPLE）/ 星号解包列表（LIST_EXTEND 丢失）/ lambda 默认值（MAKE_FUNCTION 默认值元组丢失）|
| walrus 在 AugAssign 右值位置 | 05 | `y += (n := f())` AugAssign 退化为 walrus 独立赋值 |

## 与 Round 1-3 的关系

- 本轮 15 个错误均为 Round 1-3 **未覆盖**的新组合，且本轮系统性地把测试焦点从「if 条件」扩展到「if 体内语句」：
  - **if 体内赋值/解包族（错误 01-08）**：前 3 轮几乎全部聚焦 if 条件表达式，本轮首次系统测试 if body 内的复杂赋值（元组解包 / 嵌套解包 / 多目标链 / 多层下标 / 复合 AugAssign / del 嵌套下标），揭示 if body 区域分析对「多 STORE 目标」与「多层 BINARY_SUBSCR 链」的系统性盲区
  - **链式比较位置扩展（错误 04, 10, 12）**：R1-3 修复了链式比较作 if 条件；本轮新增链式比较作赋值右值（错误 04）、作 assert 条件（错误 12），以及链式比较归约的 false-positive（错误 10 `(a==b)==(c==d)`）— 既漏识别（body 内）又误识别（条件内括号比较）
  - **suspendable 表达式位置扩展（错误 14, 15）**：R1-3 修复了 await 作 if 条件；本轮新增 await/yield 作 if 体内赋值右值，且 yield 触发内部 AST dict 泄露（错误 15，最严重）
  - **字面量构造指令族（错误 09, 11, 13）**：R3 slice_walrus 只覆盖单冒号切片；本轮新增 Ellipsis 多维切片（错误 09）、星号解包列表（错误 11）、lambda 默认值（错误 13），揭示 if 条件/body 中字面量构造指令（BUILD_SLICE/LIST_EXTEND/MAKE_FUNCTION 默认值）的重建盲区
  - **walrus 位置扩展（错误 05）**：R1-3 修复了 walrus 作 if 条件；本轮新增 walrus 作 AugAssign 右值，AugAssign 退化为独立赋值

## 复现命令

```bash
# 单个
python -m pytest tests/exhaustive/if_region/test_adv04_tuple_unpack_body.py -v
# 全部 adv04
python -m pytest tests/exhaustive/if_region/test_adv04_*.py -q
```

## 最终汇总运行结果

```
15 failed, 3 passed
```
