# IF 区域 Round 8 测试发现

- 测试日期：2026-07-18
- 基线：R7 已修复 11/11（git HEAD 已含 R7 修复）
- 本轮新增测试文件：33 个 `test_adv08_*.py`
- 确认错误数：**13**（全部失败；20 个通过的不计入）
- 验证方式：`ExhaustiveTestCase.verify_decompilation()` → `verify_bytecode_equivalence()`（对比原始字节码 vs 反编译后重编译字节码；过滤跳转/对齐指令）
- 约束遵守：未修改 `core/cfg/` 下任何源码，仅新增测试文件与本报告
- 运行命令：`cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv08_*.py --tb=line`

## R1-R7 已覆盖范围（本轮严格避开）

- R1：walrus+or/链式比较、await 条件/await+比较、lambda 调用条件、not+链式比较、not+BoolOp De Morgan、not+四段链式、三元条件（裸/嵌套）、CALL_FUNCTION_EX（`*args`/`**kwargs`）
- R2：walrus 下标（`d[(n := f())] > 0`）、is None/is not None BoolOp、await in BoolOp、三元 in BoolOp(and)/比较右侧/链式比较中段、not+三元
- R3：三元 wrapping（下标/属性/调用参数/is None/in/dict key/链式比较左操作数）、walrus 下标链式比较、嵌套三元链式比较、await 链式比较、walrus+await
- R4：tuple unpack、nested tuple unpack、multi-target chain rhs、chain-cmp rhs、walrus augassign、compound augassign、deep subscr assign、del nested subscr、ellipsis slice、paren-cmp false-positive、starred list cond、compound assert、lambda defaults、await rhs、yield rhs
- R5：import asname、nested lambda、setcomp multi-for、dictcomp walrus、5-level chain-cmp、ann-assign（简单 `x: int = 1`）、fstring format-spec、async with as x、async for、await list-elem、augassign attr chain（2 级 `a.b.c += 1`）
- R6：chain is/in rhs、nested ternary rhs、yield-from rhs、lambda outer/kw defaults、walrus outside comp、await call/dict/tuple/subscr、fstring conversion/debug spec
- R7：walrus 作 dict/set/list 字面量元素、import star、match or-pattern/mapping-pattern、raise ternary from、dictcomp ternary key/value、lambda walrus body、await walrus value、yieldfrom call arg、chaincmp in list、augassign attr chain4（`a.b.c.d` del）

## 失败测试列表（13 个确认错误）

| # | 测试文件 | 类名 | 失败环节 |
|---|----------|------|----------|
| 1 | test_adv08_ann_assign_complex.py | TestAdv08AnnAssignComplex | 字节码不等价（`x: List[Dict[str, int]] = {}` 退化为 `x = {}` + `__annotations__['x'] = List[Dict[str, int]]`，丢失 `SETUP_ANNOTATIONS`，19 vs 18） |
| 2 | test_adv08_ann_assign_no_value.py | TestAdv08AnnAssignNoValue | 字节码不等价（`x: int`（无值）退化为 `__annotations__['x'] = int`，丢失 `SETUP_ANNOTATIONS`，11 vs 10） |
| 3 | test_adv08_chaincmp_method_call.py | TestAdv08ChaincmpMethodCall | 反编译结果语法错误（`a.f() < b.g() < c.h()` 中段 `LOAD_METHOD` 未重建，输出 `if (a < <LOAD_METHOD> < <LOAD_METHOD>):`，5 vs 4 ops） |
| 4 | test_adv08_dict_unpack_in_call.py | TestAdv08DictUnpackInCall | 字节码不等价（`f(**a, **b)` 双 dict 解包，重编仅保留一个 `DICT_MERGE`，丢失 `**a`，16 vs 14） |
| 5 | test_adv08_dict_unpack_literal.py | TestAdv08DictUnpackLiteral | 字节码不等价（`r = {**a, **b, "k": v}` 字典字面量双解包，退化丢失 `**a`/`**b`，只剩 `{'k': v}`，16 vs 10） |
| 6 | test_adv08_lambda_with_walrus_default.py | TestAdv08LambdaWithWalrusDefault | 字节码不等价（`lambda x=(n := 1): x` walrus 默认参数退化为 `n = 1` + `lambda x: x`，13 vs 11） |
| 7 | test_adv08_multi_assign_subscr_attr.py | TestAdv08MultiAssignSubscrAttr | 字节码不等价（`a = b[k] = c.d = e` 多目标链含下标和属性目标，错位为 `a = e; b[k] = 1; c.d = None`，第 3 指令 COPY vs STORE_NAME 不匹配） |
| 8 | test_adv08_nested_walrus_subscr.py | TestAdv08NestedWalrusSubscr | 字节码不等价（`r = d[a[(n := f())]]` 嵌套 walrus 下标，退化丢失整个赋值，只剩 `n = f()`，17 vs 11） |
| 9 | test_adv08_subscr_augassign_complex_rhs.py | TestAdv08SubscrAugassignComplexRhs | 字节码不等价（`a[b] += f(c, d)` 方法调用右值丢失，变 `a[b] += 0`，21 vs 16） |
| 10 | test_adv08_tuple_unpack_attr_target.py | TestAdv08TupleUnpackAttrTarget | 字节码不等价（`a.b, c.d = e, f` tuple unpack 属性目标，错位为 `a.b = f; c.d = None`，丢失 SWAP，13 vs 12） |
| 11 | test_adv08_tuple_unpack_subscr_target.py | TestAdv08TupleUnpackSubscrTarget | 字节码不等价（`a[0], b = c, d` tuple unpack 下标目标，丢失 `b = c` 赋值，只剩 `a[0] = d`，13 vs 10） |
| 12 | test_adv08_walrus_assert_msg.py | TestAdv08WalrusAssertMsg | 字节码不等价（`assert x, (n := f())` walrus 消息退化为 dict 字面量字符串，第 4 指令 PUSH_NULL vs LOAD_CONST 不匹配） |
| 13 | test_adv08_walrus_in_format_value.py | TestAdv08WalrusInFormatValue | 字节码不等价（`s = f"{(n := x)}"` f-string 中 walrus 退化为 `n = x` 独立赋值，丢失整个 f-string 赋值，11 vs 8） |

## 本轮通过的测试（不计入错误，仅作覆盖参考）

- test_adv08_augassign_attr_3level.py（`a.b.c.d += 1`，通过）
- test_adv08_augassign_binop_rhs.py（`a += b * c + d` 复杂右值，通过）
- test_adv08_augassign_subscr_3level.py（`d[k1][k2][k3] += 1`，通过）
- test_adv08_augassign_ternary_rhs.py（`a += 1 if x else 2`，通过）
- test_adv08_attr_augassign_chain_method_rhs.py（`a.b += f(c).g(d)`，通过）
- test_adv08_del_attr_subscr_mix.py（`del a.b, c.d[e]`，通过）
- test_adv08_del_multi_targets.py（`del a, b, c`，通过）
- test_adv08_for_else_in_if.py（for-else 在 if 内，通过）
- test_adv08_global_with_augassign.py（`global g; g += 1`，通过）
- test_adv08_if_in_cond_walrus_compare.py（`(n := f()) > 0 and (n := g()) < 10`，通过）
- test_adv08_implicit_str_concat.py（`s = "a" "b" "c"` 隐式连接，通过）
- test_adv08_lambda_with_complex_default.py（`lambda x=a+b, y=c*2: x+y`，通过）
- test_adv08_multi_chain_assign.py（`a = b = c = d` 多目标链，通过）
- test_adv08_set_literal_in_cond.py（`x in {1, 2, 3}:`，通过）
- test_adv08_slice_assign.py（`a[1:3] = b` 切片目标赋值，通过）
- test_adv08_starred_call_arg.py（`f(*a, *b)`，通过）
- test_adv08_starred_in_list_literal.py（`r = [*a, *b, c]`，通过）
- test_adv08_tuple_compare_cond.py（`if (a, b) == (c, d):`，通过）
- test_adv08_while_else_in_if.py（while-else 在 if 内，通过）
- test_adv08_nested_fstring.py（`f"{f'{x}'}"` 嵌套 f-string，通过）

---

## 错误详细记录

### 错误 01 — if 体内复杂类型注解 `x: List[Dict[str, int]] = {}` 退化为 `x = {}` + `__annotations__['x'] = ...`

- 测试文件：test_adv08_ann_assign_complex.py
- 源码：
  ```python
  if c:
      x: List[Dict[str, int]] = {}
  ```
- 反编译结果：
  ```python
  if c:
      x = {}
      __annotations__['x'] = List[Dict[str, int]]
  ```
- 失败信息：指令数不匹配 19 vs 18（原始含 `SETUP_ANNOTATIONS`，重编缺 `SETUP_ANNOTATIONS`）
- 根因分析：`x: List[Dict[str, int]] = {}` 字节码为 `SETUP_ANNOTATIONS`（在 module 顶部首次出现注解时生成）+ `LOAD_NAME List; LOAD_NAME Dict; LOAD_NAME str; LOAD_NAME int; BUILD_TUPLE 2; BINARY_SUBSCR; BINARY_SUBSCR`（构造注解类型）+ `LOAD_CONST {}; STORE_NAME x; LOAD_NAME x; LOAD_CONST 'x'; STORE_SUBSCR __annotations__`。if body 的 `_generate_block_statements` 路径把 `AnnAssign` 拆成 `Assign(x, {})` + `Expr(__annotations__['x'] = annotation)`，未保留 `AnnAssign` AST 节点；而 `__annotations__['x'] = ...` 表达式语句不会触发 CPython 在函数/模块首条注解前插入 `SETUP_ANNOTATIONS` 的字节码，导致 1 个 `SETUP_ANNOTATIONS` 缺失。R5 错误 04 已修复简单 `x: int = 1`，但当时仅 `LOAD_CONST int`，未覆盖含 `BINARY_SUBSCR` 嵌套下标的复杂注解（如 `List[Dict[str, int]]`）。代码生成器 `_generate_ann_assign_dict` 已存在，但 `_build_statement`/`_build_store_statement` 路径未识别该模式以生成 `AnnAssign`。

### 错误 02 — if 体内无初始值注解 `x: int` 退化为 `__annotations__['x'] = int`

- 测试文件：test_adv08_ann_assign_no_value.py
- 源码：
  ```python
  if c:
      x: int
  ```
- 反编译结果：
  ```python
  if c:
      __annotations__['x'] = int
  ```
- 失败信息：指令数不匹配 11 vs 10（原始含 `SETUP_ANNOTATIONS`，重编缺 `SETUP_ANNOTATIONS`）
- 根因分析：与错误 01 同源。`x: int`（无值）字节码为 `SETUP_ANNOTATIONS` + `LOAD_NAME int; LOAD_CONST 'x'; STORE_SUBSCR __annotations__`。反编译器把单个 `AnnAssign`（无 value）误转为 `Assign(__annotations__['x'], int)`，导致重新编译时缺少 `SETUP_ANNOTATIONS` 注解初始化指令。R5 错误 04 已修复带初值的简单注解 `x: int = 1`，但未覆盖无初值的纯声明形式 `x: int`（无 `STORE_NAME x`）。

### 错误 03 — if 条件中段含方法调用的链式比较 `a.f() < b.g() < c.h()` 退化为语法错误

- 测试文件：test_adv08_chaincmp_method_call.py
- 源码：
  ```python
  if a.f() < b.g() < c.h():
      r = 1
  ```
- 反编译结果：
  ```python
  if (a < <LOAD_METHOD> < <LOAD_METHOD>):
      r = 1
  ```
- 失败信息：反编译结果语法错误 `invalid syntax (<unknown>, line 1)` —— `<LOAD_METHOD>` 占位符未被替换为方法调用表达式
- 根因分析：`a.f() < b.g() < c.h()` 链式比较，中段和右段是方法调用（`b.g()`、`c.h()`），字节码用 `LOAD_NAME a; LOAD_ATTR f; PRECALL; CALL`（左）、`LOAD_NAME b; LOAD_METHOD g; PRECALL; CALL`（中）、`LOAD_NAME c; LOAD_METHOD h; PRECALL; CALL`（右）+ `COMPARE_OP <`。`_build_chained_compare_from_region_data`（line 5874）假设所有 comparator 指令都是单条 `LOAD_*`，调用 `_load_instr_to_ast`（line 5899），对 `LOAD_METHOD` 返回占位符 `<LOAD_METHOD>` 字符串而非完整的方法调用表达式。`region.chained_comparator_instrs` 只保存了 `LOAD_METHOD` 一条指令，未捕获后续的 `PRECALL/CALL`，导致 comparator 退化为占位符。R5 已覆盖 `0 < a < b < c < d` 5 段链式（纯 LOAD），但每段都是简单变量；未覆盖中段含 `LOAD_METHOD + CALL` 的方法调用形式。

### 错误 04 — if 体内调用含双 dict 解包 `f(**a, **b)` 丢失一个 `DICT_MERGE`

- 测试文件：test_adv08_dict_unpack_in_call.py
- 源码：
  ```python
  if c:
      f(**a, **b)
  ```
- 反编译结果：
  ```python
  if c:
      f(*(), **b)
  ```
- 失败信息：指令数不匹配 16 vs 14（原始含 2 个 `DICT_MERGE`，重编仅 1 个 `DICT_MERGE`，丢失 `**a`）
- 根因分析：`f(**a, **b)` 字节码为 `PUSH_NULL; LOAD_NAME f; LOAD_CONST (); BUILD_MAP 0; LOAD_NAME a; DICT_MERGE 1; LOAD_NAME b; DICT_MERGE 1; CALL_FUNCTION_EX 1`。`CALL_FUNCTION_EX` 路径在 `expr_reconstructor` 中重建 kwargs 时只保留了最后一个 `DICT_MERGE` 对应的 `b`，前面的 `**a` 被丢弃，并额外生成了一个空 tuple `*()`。说明 `**kwargs1, **kwargs2` 多次 `DICT_MERGE` 的合并语义未被完整捕获。R1 已覆盖 `CALL_FUNCTION_EX`（`*args`/`**kwargs` 单个解包），R7 已覆盖 `import star`，但未覆盖「多个 `**dict` 在一次调用中合并」模式。

### 错误 05 — if 体内 dict 字面量双解包 `r = {**a, **b, "k": v}` 丢失解包项

- 测试文件：test_adv08_dict_unpack_literal.py
- 源码：
  ```python
  if c:
      r = {**a, **b, "k": v}
  ```
- 反编译结果：
  ```python
  if c:
      r = {'k': v}
  ```
- 失败信息：指令数不匹配 16 vs 10（原始含 `BUILD_MAP; LOAD_NAME a; DICT_UPDATE; LOAD_NAME b; DICT_UPDATE; LOAD_CONST 'k'; LOAD_NAME v; BUILD_MAP; DICT_UPDATE`，重编仅 `LOAD_CONST 'k'; LOAD_NAME v; BUILD_MAP`）
- 根因分析：`{**a, **b, "k": v}` 字节码使用 `BUILD_MAP 0; LOAD_NAME a; DICT_UPDATE 1; LOAD_NAME b; DICT_UPDATE 1; LOAD_CONST 'k'; LOAD_NAME v; BUILD_MAP 1; DICT_UPDATE 1` 模式（CPython 对 dict 字面量中 `**expr` 项的合并策略）。`expr_reconstructor` 处理 `BUILD_MAP` 字面量时只识别「LOAD key; LOAD value; BUILD_MAP N」的固定对，未识别 `DICT_UPDATE` 后跟其他 `DICT_UPDATE`/`BUILD_MAP` 的链式合并，导致 `**a`/`**b` 两个解包项丢失，dict 退化为 `{'k': v}`。R7 已覆盖 walrus 作 dict 字面量元素，但未覆盖 `**` 解包在 dict 字面量中（`DICT_UPDATE` 路径）。

### 错误 06 — if 体内 lambda 默认参数带 walrus `lambda x=(n := 1): x` walrus 退化为独立赋值

- 测试文件：test_adv08_lambda_with_walrus_default.py
- 源码：
  ```python
  if c:
      f = lambda x=(n := 1): x
  ```
- 反编译结果：
  ```python
  if c:
      n = 1
      f = lambda x: x
  ```
- 失败信息：指令数不匹配 13 vs 11（原始含 `COPY; STORE_NAME n; BUILD_TUPLE`（walrus 副作用 + 默认值入栈），重编缺 `COPY; STORE_NAME n`，walrus 退化为独立 `n = 1`）
- 根因分析：`lambda x=(n := 1): x` 字节码为 `LOAD_CONST 1; COPY 1; STORE_NAME n; BUILD_TUPLE 1; LOAD_CONST <code>; MAKE_FUNCTION 1`（默认值通过 `BUILD_TUPLE` 传入，walrus 的 `COPY+STORE_NAME n` 副作用在默认值构造时执行）。`_build_store_statement` 路径遇到 `COPY + STORE_NAME n` 时（无后续字面量 BUILD 操作）触发了 walrus 独立赋值分支，把 walrus 提前为 `n = 1`，并从 lambda 默认值 tuple 中移除了 walrus 表达式。R5 错误 12 已修复 `lambda` 带 `*args/**kwargs`，R6 已修复 lambda outer/kw defaults，但均未覆盖 lambda 默认参数位置出现 walrus（`COPY+STORE+BUILD_TUPLE+MAKE_FUNCTION` 模式）。

### 错误 07 — if 体内多目标赋值链含下标和属性 `a = b[k] = c.d = e` 错位

- 测试文件：test_adv08_multi_assign_subscr_attr.py
- 源码：
  ```python
  if c:
      a = b[k] = c.d = e
  ```
- 反编译结果：
  ```python
  if c:
      a = e
      b[k] = 1
      c.d = None
  ```
- 失败信息：指令 3 操作码不匹配 `COPY vs STORE_NAME`（原始第三条指令是 COPY 1，重编是 STORE_NAME，证明链式赋值 targets 顺序错位）
- 根因分析：`a = b[k] = c.d = e` 字节码为 `LOAD_NAME e; COPY 1; STORE_NAME a; COPY 1; LOAD_NAME b; LOAD_NAME k; STORE_SUBSCR; COPY 1; LOAD_NAME c; STORE_ATTR d`（COPY 链 + 各种 STORE）。`_build_store_statement` 的多目标链检测（line 16681）只识别连续相邻的 `STORE_FAST/STORE_NAME/...`，遇到 `STORE_SUBSCR` 或 `STORE_ATTR` 中断，导致链式赋值被拆成 3 个独立语句：`a = e`、`b[k] = 1`（误用 COPY 数作为索引）、`c.d = None`（缺少 LOAD 步骤）。R4 错误 03 已修复 `multi_target_chain_rhs`（纯 `STORE_NAME` 链 `a = b = c = f()`），但未覆盖链中含下标/属性 STORE 的混合目标。

### 错误 08 — if 体内嵌套 walrus 下标 `r = d[a[(n := f())]]` 丢失整个赋值

- 测试文件：test_adv08_nested_walrus_subscr.py
- 源码：
  ```python
  if c:
      r = d[a[(n := f())]]
  ```
- 反编译结果：
  ```python
  if c:
      n = f()
  ```
- 失败信息：指令数不匹配 17 vs 11（原始含 `LOAD_NAME d; LOAD_NAME a; PUSH_NULL; LOAD_NAME f; PRECALL; CALL; COPY; STORE_NAME n; BINARY_SUBSCR; BINARY_SUBSCR; STORE_NAME r`，重编仅 `LOAD_NAME f; CALL; STORE_NAME n`）
- 根因分析：`d[a[(n := f())]]` 字节码为 `LOAD_NAME d; LOAD_NAME a; PUSH_NULL; LOAD_NAME f; PRECALL; CALL; COPY 1; STORE_NAME n; BINARY_SUBSCR; BINARY_SUBSCR; STORE_NAME r`（外层 `d[...]`，内层 `a[...]`，最内层 walrus `f()`）。`_build_store_statement` 路径的 walrus 识别（line 16567-16713）检测到 `COPY + STORE_NAME n` 后，没有检测到「后续有 BUILD_MAP/BUILD_SET/BUILD_LIST/LOAD_NAME 等 literal build 路径」就提前把 walrus 提为独立 `n = f()`，丢失了 `d[...]`/`a[...]`/`r = ...` 整个赋值链。R7 错误 01/02/03 已修复 walrus 作 dict/set/list 字面量元素，但触发条件是「后续有 BUILD_MAP/BUILD_SET/BUILD_LIST」字面量构造；嵌套下标 `BINARY_SUBSCR` 不在 `_LITERAL_BUILD_OPS` 列表中，故 walrus 副作用被错误提取为独立赋值。

### 错误 09 — if 体内下标 augassign 含方法调用右值 `a[b] += f(c, d)` 方法调用丢失

- 测试文件：test_adv08_subscr_augassign_complex_rhs.py
- 源码：
  ```python
  if c:
      a[b] += f(c, d)
  ```
- 反编译结果：
  ```python
  if c:
      a[b] += 0
  ```
- 失败信息：指令数不匹配 21 vs 16（原始含 `PUSH_NULL; LOAD_NAME f; LOAD_NAME c; LOAD_NAME d; PRECALL; CALL; BINARY_OP`（方法调用作为 augassign 右值），重编缺 `PUSH_NULL/LOAD_NAME f/LOAD_NAME c/LOAD_NAME d/PRECALL/CALL` 共 5 条，右值退化为常量 0）
- 根因分析：`a[b] += f(c, d)` 字节码为 `LOAD_NAME a; LOAD_NAME b; COPY 2; COPY 2; BINARY_SUBSCR; PUSH_NULL; LOAD_NAME f; LOAD_NAME c; LOAD_NAME d; PRECALL; CALL; BINARY_OP +=; SWAP; SWAP; STORE_SUBSCR`。`_build_subscript_assign`（line 17630）的 AugAssign 重建逻辑（line 17658-17692）假设「aug_op 之后直接是 SWAP/STORE_SUBSCR」，但实际 aug_op 之前还有完整的 `f(c, d)` 调用序列，重建时把 aug_op 后的所有指令当作右值，但右值 instrs 中实际包含的是 `LOAD_CONST 0`（从某处错位补全），而不是 `f(c, d)` 调用。R4 错误 06 已修复 `compound augassign d[k1][k2] += 1`（常量右值），R6 已修复 augassign attr chain，但未覆盖方法调用作为 augassign 右值（含 `PUSH_NULL/PRECALL/CALL` 序列）。

### 错误 10 — if 体内 tuple unpack 含属性目标 `a.b, c.d = e, f` 错位

- 测试文件：test_adv08_tuple_unpack_attr_target.py
- 源码：
  ```python
  if c:
      a.b, c.d = e, f
  ```
- 反编译结果：
  ```python
  if c:
      a.b = f
      c.d = None
  ```
- 失败信息：指令数不匹配 13 vs 12（原始含 `SWAP 2; LOAD_NAME a; STORE_ATTR b; LOAD_NAME c; STORE_ATTR d`，重编缺 SWAP，且 `c.d = None` 中 None 来自错位）
- 根因分析：`a.b, c.d = e, f` 字节码为 `LOAD_NAME e; LOAD_NAME f; SWAP 2; LOAD_NAME a; STORE_ATTR b; LOAD_NAME c; STORE_ATTR d`（栈顶 [e, f]，SWAP 后 [f, e]，按顺序 STORE_ATTR）。tuple unpack 重建逻辑（_build_store_statement / _generate_block_statements）未识别 `SWAP + STORE_ATTR + LOAD_NAME + STORE_ATTR` 序列，把第一条 `STORE_ATTR` 后即当作单赋值结束，导致 `a.b` 收到 `f`（应为 `e`）、`c.d` 收到 None（应为 `f`）。R4 错误 01/02 已修复 `tuple unpack`（`a, b = c, d`，纯 STORE_NAME）和 nested tuple unpack，但未覆盖 targets 中含 `STORE_ATTR` 的属性目标。

### 错误 11 — if 体内 tuple unpack 含下标目标 `a[0], b = c, d` 丢失赋值

- 测试文件：test_adv08_tuple_unpack_subscr_target.py
- 源码：
  ```python
  if c:
      a[0], b = c, d
  ```
- 反编译结果：
  ```python
  if c:
      a[0] = d
  ```
- 失败信息：指令数不匹配 13 vs 10（原始含 `SWAP 2; LOAD_NAME a; LOAD_CONST 0; STORE_SUBSCR; STORE_NAME b`（保留 b 赋值），重编缺 `SWAP` 和 `STORE_NAME b`，丢失 `b = c` 整个赋值）
- 根因分析：`a[0], b = c, d` 字节码为 `LOAD_NAME c; LOAD_NAME d; SWAP 2; LOAD_NAME a; LOAD_CONST 0; STORE_SUBSCR; STORE_NAME b`（栈顶 [c, d]，SWAP 后 [d, c]，先 STORE_SUBSCR a[0]=d，再 STORE_NAME b=c）。反编译器遇到 `STORE_SUBSCR` 后中断 tuple unpack 重建，把后续 `STORE_NAME b` 当作独立赋值处理，但因为栈状态已错位（缺少 SWAP），`STORE_NAME b = c` 被完全丢失，只剩 `a[0] = d`。R4 错误 01/02 已修复纯 STORE_NAME 的 tuple unpack，未覆盖含 `STORE_SUBSCR` 的混合下标目标。

### 错误 12 — if 体内 assert 带 walrus 消息 `assert x, (n := f())` walrus 退化为 dict 字面量字符串

- 测试文件：test_adv08_walrus_assert_msg.py
- 源码：
  ```python
  if c:
      assert x, (n := f())
  ```
- 反编译结果：
  ```python
  if c:
      assert x, {'type': 'Name', 'id': 'f', 'ctx': 'Load', 'lineno': None}
  ```
- 失败信息：指令 4 操作码不匹配 `PUSH_NULL vs LOAD_CONST`（原始第 4 指令是 `PUSH_NULL` 准备函数调用，重编第 4 指令是 `LOAD_CONST` 加载常量字符串）
- 根因分析：`assert x, (n := f())` 字节码为 `LOAD_NAME x; COPY 1; POP_JUMP_IF_TRUE; PUSH_NULL; LOAD_NAME f; PRECALL; CALL; COPY 1; STORE_NAME n; LOAD_ASSERTION_ERROR; CALL; RAISE_VARARGS 1`。`_generate_assert`（assert 区域生成器）在重建 assert 消息时，把 walrus 表达式 `(n := f())` 当作未识别的 AST dict 字面量直接 str() 输出为 `{'type': 'Name', 'id': 'f', ...}`（占位 dict 而非 NamedExpr 节点）。说明 assert 消息路径未调用 `expr_reconstructor.reconstruct` 识别 walrus 模式，而是把内部 AST 字典 repr 直接当字符串。R7 错误 13 已覆盖 walrus 在 f-string，但未覆盖 walrus 在 assert 消息位置（`LOAD_ASSERTION_ERROR + CALL + RAISE_VARARGS 1` 路径）。

### 错误 13 — if 体内 f-string 含 walrus `s = f"{(n := x)}"` walrus 退化为独立赋值

- 测试文件：test_adv08_walrus_in_format_value.py
- 源码：
  ```python
  if c:
      s = f"{(n := x)}"
  ```
- 反编译结果：
  ```python
  if c:
      n = x
  ```
- 失败信息：指令数不匹配 11 vs 8（原始含 `LOAD_NAME x; COPY; STORE_NAME n; FORMAT_VALUE; STORE_NAME s`，重编缺 `FORMAT_VALUE` 和 `STORE_NAME s`，丢失整个 f-string 赋值）
- 根因分析：`f"{(n := x)}"` 字节码为 `LOAD_NAME x; COPY 1; STORE_NAME n; FORMAT_VALUE 0; STORE_NAME s`（walrus 的 `COPY+STORE` 副作用在 FORMAT_VALUE 之前执行）。`_build_store_statement` 的 walrus 识别路径（line 16567-16713）只识别 `_LITERAL_BUILD_OPS = ('BUILD_MAP', 'BUILD_SET', 'BUILD_LIST', 'BUILD_TUPLE', 'BUILD_CONST_KEY_MAP')` 作为「后续字面量构造」标志，未包含 `FORMAT_VALUE`（f-string 的格式化指令）。因此 walrus 被错误提取为独立 `n = x`，而 `FORMAT_VALUE + STORE_NAME s`（f-string 赋值）整段被丢弃。R7 错误 13 已覆盖 walrus 在 dict/set/list 字面量，但未覆盖 walrus 在 f-string `FORMAT_VALUE` 路径。

---

## 总结

本轮（Round 8）针对 IF 区域反编译器在 R1-R7 已修复范围之外的新错误模式进行探测，共编写 33 个候选测试，确认 13 个真实失败案例：

- **注解相关（2 个）**：复杂注解 / 无值注解 —— `AnnAssign` 退化为 `Assign + __annotations__[] =`，丢失 `SETUP_ANNOTATIONS`
- **链式比较（1 个）**：中段含方法调用的链式比较 —— `LOAD_METHOD` 占位符未替换
- **字典解包（2 个）**：调用中双 `**dict` / dict 字面量双 `**` —— 多个 `DICT_MERGE/DICT_UPDATE` 仅保留最后一个
- **walrus（5 个）**：lambda 默认参数 / 嵌套下标 / assert 消息 / f-string FORMAT_VALUE / 多目标赋值链 —— walrus 副作用被错误提取为独立赋值
- **augassign（1 个）**：下标目标 + 方法调用右值 —— `f(c, d)` 调用序列丢失
- **tuple unpack（2 个）**：含属性 / 下标目标的 tuple unpack —— `STORE_ATTR/STORE_SUBSCR` 中断 unpack 重建

主要根因集中在 `_build_store_statement` / `_generate_block_statements` 的 walrus 识别（line 16567-16713，触发条件过严，仅匹配 `_LITERAL_BUILD_OPS`）和 chain assign / tuple unpack 的目标识别（仅识别连续相邻的 `STORE_NAME/STORE_FAST`，遇 `STORE_ATTR/STORE_SUBSCR` 中断），以及 chained_compare 中 comparator 指令集对 `LOAD_METHOD + PRECALL + CALL` 序列的不支持。
