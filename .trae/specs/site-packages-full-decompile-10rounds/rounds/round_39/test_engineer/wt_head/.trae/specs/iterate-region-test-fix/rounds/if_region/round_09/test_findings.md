# IF 区域 Round 9 测试发现

- 测试日期：2026-07-18
- 基线：R8 已修复 13/13（git HEAD 已含 R8 修复）
- 本轮新增测试文件：51 个 `test_adv09_*.py`
- 确认错误数：**16**（全部失败；35 个通过的不计入）
- 验证方式：`ExhaustiveTestCase.verify_decompilation()` → `verify_bytecode_equivalence()`（对比原始字节码 vs 反编译后重编译字节码；过滤跳转/对齐指令）
- 约束遵守：未修改 `core/cfg/` 下任何源码，仅新增测试文件与本报告
- 运行命令：`cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv09_*.py --tb=line`

## R1-R8 已覆盖范围（本轮严格避开）

- R1：walrus 各种位置、await 各种位置、链式比较、De Morgan、CALL_FUNCTION_EX、import star/multi/asname、f-string conversion/multi、ellipsis slice、lambda varargs/defaults/walrus body、match or-pattern/mapping、async with/for/multi ctx/nested
- R2-R3：walrus/await/ternary 在各种嵌套位置（boolop/chain/subscr/dict key-value-set/lambda body/await value/expr/assert msg/f-string/lambda default/nested subscr/multi-assign）
- R4-R5：chaincmp 各种 rhs/not+chain/方法调用中段、tuple unpack（基础/嵌套）、ann-assign（简单/无值）、augassign 下标+方法调用、注解复杂/无值
- R6-R7：augassign attr chain、yieldfrom call arg、dictcomp ternary key/value、walrus 作 dict/set/list 字面量元素、raise ternary from、chaincmp in list、multidim step slice、bool short circuit、starred tuple、listcomp multi if、setcomp walrus、注解(复杂/无值)、字典解包(调用/字面量)、augassign 下标+方法调用、tuple unpack(attr/subscr 目标)
- R8：multi-assign 含 subscr/attr 目标、nested walrus subscr、walrus 在 f-string、walrus 在 assert 消息、dict unpack 双解包、lambda walrus 默认值、ann-assign 复杂/无值、chaincmp 中段含方法调用

## 失败测试列表（16 个确认错误）

| # | 测试文件 | 类名 | 失败环节 |
|---|----------|------|----------|
| 1 | test_adv09_del_subscr_attr_chain.py | TestAdv09DelSubscrAttrChain | 字节码不等价（`del a[b].c` 退化为 `del b.c`，丢失外层 `a[b]` BINARY_SUBSCR，10 vs 8） |
| 2 | test_adv09_for_multi_tuple_target.py | TestAdv09ForMultiTupleTarget | 字节码不等价（`for (a, b), (c, d) in pairs` 退化为 `for a, b in pairs`，丢失嵌套 UNPACK_SEQUENCE，24 vs 20） |
| 3 | test_adv09_raise_no_arg.py | TestAdv09RaiseNoArg | 字节码不等价（`if c: raise`（在 except 中）退化为 `if c: pass; return None; raise`（raise 移出 if 体，外层多出 RAISE_VARARGS 0），20 vs 19） |
| 4 | test_adv09_ternary_dict_key_assign.py | TestAdv09TernaryAsDictKeyAndValue | 字节码不等价（`d[k if cond else m] = v` 退化为独立 Expr `(k if cond else m)`，丢失 STORE_SUBSCR 整段赋值，12 vs 10） |
| 5 | test_adv09_ternary_dict_value_assign.py | TestAdv09TernaryDictValueAssign | 字节码不等价（`d[k] = v if cond else w` 退化为 `(v if cond else w)` Expr，丢失 STORE_SUBSCR 整段赋值，12 vs 10） |
| 6 | test_adv09_ternary_kwarg.py | TestAdv09TernaryKwarg | 字节码不等价（`f(x=1 if cond else 2)` 退化为 `f(1 if cond else 2)`，丢失 `KW_NAMES`，关键字变位置参数，15 vs 14） |
| 7 | test_adv09_with_as_tuple.py | TestAdv09WithAsTuple | 字节码不等价（`with ctx as (a, b)` 退化为 `with ctx:`，丢失 `UNPACK_SEQUENCE + 2×STORE_NAME`，36 vs 34） |
| 8 | test_adv09_walrus_attr.py | TestAdv09WalrusAttr | 字节码不等价（`r = (x := f()).attr` 退化为 `x = f()`，丢失 `LOAD_ATTR + STORE_NAME r`，14 vs 11） |
| 9 | test_adv09_ternary_attr_assign.py | TestAdv09TernaryAttrAssign | 字节码不等价（`a.b = c if cond else d` 退化为 `(c if cond else d)` Expr，丢失 STORE_ATTR 整段赋值，11 vs 10） |
| 10 | test_adv09_ternary_call_arg_and_kwarg.py | TestAdv09TernaryCallArgAndKwarg | 字节码不等价（`f(a if cond else b, x=d if e else g)` 退化为 `f(a if cond else b, d if e else g)`，丢失 `KW_NAMES`，18 vs 17） |
| 11 | test_adv09_ternary_list_elem.py | TestAdv09TernaryAsListElem | 字节码不等价（`r = [a if cond else b, d if e else f]` 退化为 `(a if cond else b)\nr = [d if e else f]`，三元被拆出 list 之外，14 vs 13） |
| 12 | test_adv09_ternary_nested_kwarg.py | TestAdv09TernaryNestedKwarg | 字节码不等价（`f(x=a if cond else b, y=d if e else g)` 退化为 `f(a if cond else b, d if e else g)`，丢失两个 `KW_NAMES`，18 vs 17） |
| 13 | test_adv09_nested_func_default_walrus.py | TestAdv09NestedFuncDefaultWalrus | 字节码不等价（`def f(x=(n := 1))` 退化为 `n = 1; def f(x):`，walrus 默认参数被提取为独立赋值，13 vs 11） |
| 14 | test_adv09_lambda_call_multi_kwargs.py | TestAdv09LambdaCallWithMultiKwargs | 字节码不等价（`(lambda x, y: x + y)(x=1, y=2)` 退化为 `(lambda *args, **kwargs: None)(x=1, y=2)`，lambda 签名丢失，5 vs 3 嵌套指令） |
| 15 | test_adv09_nested_comprehension_walrus.py | TestAdv09NestedComprehensionWalrus | 字节码不等价（`[[y := x for x in a] for a in b]` 退化为 `[[True for x in a] for a in b]`，walrus `y := x` 退化为常量 True，9 vs 7 嵌套指令） |
| 16 | test_adv09_decorator_with_args_in_if.py | TestAdv09DecoratorWithArgsInIf | 字节码不等价（`@decorator(arg=1)` 退化为 `@decorator()`，丢失装饰器参数 `LOAD_CONST + KW_NAMES + PRECALL + CALL`，17 vs 15） |

## 本轮通过的测试（不计入错误，仅作覆盖参考）

- test_adv09_augassign_complex_subscr_rhs.py（`a[b] += c[d]`，通过）
- test_adv09_bool_short_circuit_mixed_cmp.py（`f() and g() > 0 or h() == 1`，通过）
- test_adv09_chain_assign_subscr.py（`a = b[k] = c`，通过）
- test_adv09_chaincmp_ternary_middle.py（`0 < (a if c else b) < 10`，通过）
- test_adv09_class_def_in_if.py（class 含 def，通过）
- test_adv09_class_def_with_base.py（class C(Base) 含基类，通过）
- test_adv09_del_attr_subscr_chain.py（`del a.b[c]`，通过）
- test_adv09_dictcomp_filter_multi.py（`{k: v for k, v in items if k > 0}`，通过）
- test_adv09_docstring_in_if.py（字符串字面量 Expr，通过）
- test_adv09_for_multi_tuple_target... wait, 已是失败
- test_adv09_genexp_as_arg.py（`sum(x for x in range(10))`，通过）
- test_adv09_global_multi.py（`global a, b, c`，通过）
- test_adv09_if_not_walrus.py（`if not (x := f()):`，通过）
- test_adv09_implicit_str_concat_mix.py（`"a" 'b' "c" 'd'`，通过）
- test_adv09_multi_ann_assign.py（多注解混合，通过）
- test_adv09_multi_assign_mixed_targets.py（`a = b.c = d[e] = f`，通过）
- test_adv09_multi_decorator_in_if.py（多装饰器叠加，通过）
- test_adv09_multi_starred_tuple.py（`(a, *b, *c, d)`，通过）
- test_adv09_nested_dict_literal.py（`{a: {b: {c: d}}}`，通过）
- test_adv09_nested_func_def.py（嵌套函数定义，通过）
- test_adv09_nonlocal_multi.py（`nonlocal x, y`，通过）
- test_adv09_pass_only.py（`if c: pass`，通过）
- test_adv09_raise_from_none.py（`raise E() from None`，通过）
- test_adv09_set_in_cond.py（`x in {1,2,3} or y in {4,5}`，通过）
- test_adv09_star_in_call_multi.py（`f(*a, *b)`，通过）
- test_adv09_starred_dict_multi.py（`{**a, k1: v1, **b, k2: v2, **c}`，通过）
- test_adv09_starred_dict_multi_call.py（`f(a, b, **c, **d)`，通过）
- test_adv09_starred_list_assign.py（`[a, *b, c, *d]`，通过）
- test_adv09_ternary_in_tuple_arg.py（`f((a if c else b))`，通过）
- test_adv09_ternary_subscr_rhs.py（`r = a[b if cond else d]`，通过）
- test_adv09_walrus_assert_msg_subscr.py（`assert x, d[(n := f())]`，通过）
- test_adv09_walrus_chain_rhs.py（`x = (y := f()) > 0`，通过）
- test_adv09_walrus_in_set_in_cond.py（`if (n := x) in {1,2,3}:`，通过）

---

## 错误详细记录

### 错误 01 — if 体内 del 嵌套下标+属性 `del a[b].c` 丢失外层下标

- 测试文件：test_adv09_del_subscr_attr_chain.py
- 源码：
  ```python
  if c:
      del a[b].c
  ```
- 反编译结果：
  ```python
  if c:
      del b.c
  ```
- 失败信息：指令数不匹配 10 vs 8（原始含 `LOAD_NAME a; LOAD_NAME b; BINARY_SUBSCR; DELETE_ATTR`，重编缺 `LOAD_NAME a; LOAD_NAME b; BINARY_SUBSCR`）
- 根因分析：`del a[b].c` 字节码为 `LOAD_NAME a; LOAD_NAME b; BINARY_SUBSCR; DELETE_ATTR c`（先求值 `a[b]` 得到对象，再 DELETE_ATTR 删除其属性 `c`）。`_build_delete_stmt`（line 17544+）处理 `DELETE_ATTR` 时假设「DELETE_ATTR 之前所有指令构成单一 attr chain」，但实际 `_build_delete_stmt` 的 `stmt_instrs` 收集只取了 DELETE_ATTR 紧邻的 LOAD_*，没识别前导的 `LOAD_NAME a + LOAD_NAME b + BINARY_SUBSCR` 序列。R6 已修复 `del a.b.c.d` 四层属性链（连续 LOAD_ATTR），R8 已修复 `del a.b, c.d[e]`（混合属性和下标），但未覆盖「`del <subscript>.<attr>` 即下标 + 属性的混合 del 目标」——前导的 BINARY_SUBSCR 不被识别为 attr chain 的一部分。

### 错误 02 — if 体内 for 多元 tuple 目标 `for (a, b), (c, d) in pairs` 丢失嵌套解包

- 测试文件：test_adv09_for_multi_tuple_target.py
- 源码：
  ```python
  if c:
      for (a, b), (c, d) in pairs:
          print(a, b, c, d)
  ```
- 反编译结果：
  ```python
  if c:
      for a, b in pairs:
          print(a, b, c, d)
  ```
- 失败信息：指令数不匹配 24 vs 20（原始含 `GET_ITER; UNPACK_SEQUENCE 2; UNPACK_SEQUENCE 2; STORE_NAME a; STORE_NAME b; UNPACK_SEQUENCE 2; STORE_NAME c; STORE_NAME d`，重编缺第二个 `UNPACK_SEQUENCE 2` 和后续两个 STORE_NAME）
- 根因分析：`for (a, b), (c, d) in pairs` 字节码为 `GET_ITER; UNPACK_SEQUENCE 2; UNPACK_SEQUENCE 2; STORE_NAME a; STORE_NAME b; UNPACK_SEQUENCE 2; STORE_NAME c; STORE_NAME d`（外层 UNPACK 2 拆出 `(a,b)` 和 `(c,d)`，每个再 UNPACK 2 拆出 4 个变量）。`_generate_for` 的 target 重建逻辑只识别一层 `UNPACK_SEQUENCE`，把 `for (a, b), (c, d) in pairs` 当作 `for a, b in pairs` 处理（只取了第一个 UNPACK 后的两个变量）。R1/R8 已修复 `with as (a, b)`（with 内单层 tuple unpack）和 `tuple unpack`（赋值中的 unpack），但未覆盖 for 循环 target 中嵌套 tuple（`(<tuple>), (<tuple>) in iter`）。

### 错误 03 — if 体内 `raise` 无参数（re-raise）退化为 pass + 提到外层

- 测试文件：test_adv09_raise_no_arg.py
- 源码：
  ```python
  def f():
      try:
          do_stuff()
      except Exception:
          if c:
              raise
  ```
- 反编译结果：
  ```python
  def f():
      try:
          do_stuff()
      except Exception:
          if c:
              pass
          return None
          raise
  ```
- 失败信息：嵌套 code object 不匹配（指令 1，20 vs 19）：原始含 `PUSH_EXC_INFO; LOAD_GLOBAL Exception; CHECK_EXC_MATCH; POP_TOP; LOAD_GLOBAL c; RAISE_VARARGS 0; POP_EXCEPT; LOAD_CONST None; RETURN_VALUE; RERAISE; COPY; POP_EXCEPT; RERAISE`，重编缺 `RAISE_VARARGS 0`（在 if body 内），多出 `return None; raise`（在外层 except body）
- 根因分析：`raise`（无参数，re-raise）字节码为 `RAISE_VARARGS 0`，在 except 上下文中。`_generate_block_statements`（line 11070）的 `RAISE_VARARGS 0` 分支确实生成了 `{'type': 'Raise', 'exc': None}`，但当 raise 出现在 if body 中时，`_process_if_blocks`（line 8653）的 `if stmts and stmts[-1].get('type') in ('Break', 'Continue', 'Return', 'Raise')` 检测到 raise 后会跳过后续块（视为终止语句），但此处 raise 之前的语句序列（包括 except 上下文）导致 raise 被错误地提升到外层 except body 中。具体来说，if body 中的 `raise` 应该是 `if c: raise`，但反编译器把它当作无 body 的 if + 后续 raise，最终把 `raise` 放到了 except body 末尾（外部）。R4 已修复 `raise X from Y`，R6/R7 已修复 raise from 复杂表达式和三元 from，但未覆盖「`raise`（无参数 re-raise）在 if body 内、且 if 位于 except body 内」这种异常控制流场景。

### 错误 04 — if 体内三元作 dict key 赋值目标 `d[k if cond else m] = v` 退化为 Expr

- 测试文件：test_adv09_ternary_dict_key_assign.py
- 源码：
  ```python
  if c:
      d[k if cond else m] = v
  ```
- 反编译结果：
  ```python
  if c:
      (k if cond else m)
  ```
- 失败信息：指令数不匹配 12 vs 10（原始含 `LOAD_NAME d; LOAD_NAME k; LOAD_NAME cond; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME m; BINARY_SUBSCR; LOAD_NAME v; STORE_SUBSCR`，重编缺 `LOAD_NAME d; BINARY_SUBSCR; STORE_SUBSCR`，整个赋值丢失，只剩三元 Expr）
- 根因分析：`d[k if cond else m] = v` 字节码为 `LOAD_NAME d; LOAD_NAME k; LOAD_NAME cond; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME m; BINARY_SUBSCR; LOAD_NAME v; STORE_SUBSCR`（先压 d 到栈底，然后求值三元 key `k if cond else m`，再 LOAD v，STORE_SUBSCR）。`_build_subscript_assign` 的处理路径假设下标是简单表达式（直接 LOAD_*），未识别下标位置的三元（`POP_JUMP_FORWARD_IF_FALSE` 控制流被当作独立 if 区域，导致三元被识别为独立 Expr 语句输出，而 d 和 v 的 LOAD 留在栈上未被消费，最终 STORE_SUBSCR 丢失）。R3 已覆盖三元 wrapping（下标位置），R7 已覆盖三元作 dictcomp key，但未覆盖三元作 STORE_SUBSCR 目标的 key（即 `d[ternary] = v` 这种赋值模式）。

### 错误 05 — if 体内三元作 dict value 赋值 `d[k] = v if cond else w` 退化为 Expr

- 测试文件：test_adv09_ternary_dict_value_assign.py
- 源码：
  ```python
  if c:
      d[k] = v if cond else w
  ```
- 反编译结果：
  ```python
  if c:
      (v if cond else w)
  ```
- 失败信息：指令数不匹配 12 vs 10（原始含 `LOAD_NAME d; LOAD_NAME k; LOAD_NAME v; LOAD_NAME cond; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME w; STORE_SUBSCR`，重编缺 `LOAD_NAME d; LOAD_NAME k; STORE_SUBSCR`）
- 根因分析：`d[k] = v if cond else w` 字节码为 `LOAD_NAME d; LOAD_NAME k; LOAD_NAME v; LOAD_NAME cond; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME w; STORE_SUBSCR`（先压 d[k] 到栈底，求值三元 value，STORE_SUBSCR）。`_build_subscript_assign` 同样未识别赋值右值位置的三元：三元被识别为独立 Expr 语句，d 和 k 的 LOAD 残留在栈上未消费，STORE_SUBSCR 整段丢失。R3 已覆盖三元 wrapping（dict key 位置）和三元作 dictcomp value，但未覆盖三元作 STORE_SUBSCR 赋值的 value（即 `d[k] = ternary` 这种赋值模式）。

### 错误 06 — if 体内三元作函数关键字参数 `f(x=1 if cond else 2)` 退化为位置参数

- 测试文件：test_adv09_ternary_kwarg.py
- 源码：
  ```python
  if c:
      f(x=1 if cond else 2)
  ```
- 反编译结果：
  ```python
  if c:
      f(1 if cond else 2)
  ```
- 失败信息：指令数不匹配 15 vs 14（原始含 `LOAD_CONST 1; LOAD_CONST 2; LOAD_CONST ('x',); KW_NAMES; PRECALL; CALL`，重编缺 `KW_NAMES`）
- 根因分析：`f(x=1 if cond else 2)` 字节码为 `PUSH_NULL; LOAD_NAME f; LOAD_CONST 1; LOAD_CONST 2; LOAD_CONST ('x',); KW_NAMES; PRECALL; CALL`（kwarg 默认值用 LOAD_CONST，关键字名通过 KW_NAMES 指令加载 tuple）。`expr_reconstructor` 重建 Call 时识别 KW_NAMES 指令后应保留 kwarg 名称，但当 kwarg 的 value 是三元（含 `POP_JUMP_FORWARD_IF_FALSE` 控制流）时，整个调用被识别为「TernaryRegion in Call」，三元被从调用中拆出作为独立 Expr，KW_NAMES 与 kwarg 名称 `x=` 关联丢失，最终关键字参数 `x=ternary` 退化为位置参数 `ternary`。R3 已覆盖 ternary call arg（三元作位置参数），R7 已覆盖 ternary call arg（chaincmp 上下文），但未覆盖三元作函数 keyword 参数（`f(k=ternary)`，含 KW_NAMES）。

### 错误 07 — if 体内 with as tuple 目标 `with ctx as (a, b)` 丢失 tuple 解包

- 测试文件：test_adv09_with_as_tuple.py
- 源码：
  ```python
  if c:
      with ctx as (a, b):
          print(a, b)
  ```
- 反编译结果：
  ```python
  if c:
      with ctx: print(a, b)
  ```
- 失败信息：指令数不匹配 36 vs 34（原始含 `BEFORE_WITH; UNPACK_SEQUENCE 2; STORE_NAME a; STORE_NAME b`，重编缺 `UNPACK_SEQUENCE 2` 和两个 STORE_NAME，目标丢失，with body 直接是 `print(a, b)`）
- 根因分析：`with ctx as (a, b)` 字节码为 `LOAD_NAME ctx; BEFORE_WITH; UNPACK_SEQUENCE 2; STORE_NAME a; STORE_NAME b`（BEFORE_WITH 把 __exit__/__enter__ 结果压栈，UNPACK_SEQUENCE 2 拆 tuple 并 STORE 到 a, b）。`_generate_with` 的 `as` 目标重建逻辑（line 11510+）只识别 `STORE_NAME`（单一目标），未识别 `UNPACK_SEQUENCE + 多个 STORE_NAME` 模式（tuple 解包目标）。结果 `UNPACK_SEQUENCE + 2×STORE_NAME` 被识别为 with body 的前置语句，被错误归类为「with body 第一个语句」而非 `withitem.optional_vars`。R5 已修复 `async with as x`（async with 单目标），R8 已修复 with 多 context（`with a as x, b as y`），但未覆盖 with 的 `as` 目标为 tuple（`with ctx as (a, b)`，含 UNPACK_SEQUENCE）。

### 错误 08 — if 体内 walrus 在属性取值 `(x := f()).attr` 退化为独立赋值

- 测试文件：test_adv09_walrus_attr.py
- 源码：
  ```python
  if c:
      r = (x := f()).attr
  ```
- 反编译结果：
  ```python
  if c:
      x = f()
  ```
- 失败信息：指令数不匹配 14 vs 11（原始含 `LOAD_NAME f; PRECALL; CALL; COPY 1; STORE_NAME x; LOAD_ATTR attr; STORE_NAME r`，重编缺 `LOAD_ATTR + STORE_NAME r`，整个赋值丢失，只剩 `x = f()`）
- 根因分析：`(x := f()).attr` 字节码为 `PUSH_NULL; LOAD_NAME f; PRECALL; CALL; COPY 1; STORE_NAME x; LOAD_ATTR attr; STORE_NAME r`（walrus 的 COPY+STORE 副作用在 LOAD_ATTR 之前执行）。`_build_store_statement` 的 walrus 识别路径（line 16567-16713）只识别 `_LITERAL_BUILD_OPS = ('BUILD_MAP', 'BUILD_SET', 'BUILD_LIST', 'BUILD_TUPLE', 'BUILD_CONST_KEY_MAP')` 作为「后续字面量构造」标志，未包含 `LOAD_ATTR`（属性访问指令）。因此 walrus 被错误提取为独立 `x = f()`，而 `LOAD_ATTR + STORE_NAME r`（属性赋值）整段被丢弃。R3 已修复 walrus attr（walrus 在 attr 上下文），R7 已修复 walrus 作 dict/set/list 字面量元素，R8 已修复 walrus 在 f-string FORMAT_VALUE，但未覆盖 walrus 后跟 LOAD_ATTR 作为普通赋值右值（`r = (walrus).attr`，非字面量构造）。

### 错误 09 — if 体内三元作属性赋值右值 `a.b = c if cond else d` 退化为 Expr

- 测试文件：test_adv09_ternary_attr_assign.py
- 源码：
  ```python
  if c:
      a.b = c if cond else d
  ```
- 反编译结果：
  ```python
  if c:
      (c if cond else d)
  ```
- 失败信息：指令数不匹配 11 vs 10（原始含 `LOAD_NAME a; LOAD_NAME c; LOAD_NAME cond; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME d; STORE_ATTR b`，重编缺 `LOAD_NAME a; STORE_ATTR b`）
- 根因分析：`a.b = c if cond else d` 字节码为 `LOAD_NAME a; LOAD_NAME c; LOAD_NAME cond; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME d; STORE_ATTR b`（先压 a 到栈底，求值三元 value，STORE_ATTR b）。`_build_attr_assign` 的处理路径假设赋值右值是简单表达式，未识别右值位置的三元：三元被识别为独立 Expr 语句输出，a 和 b 的 LOAD/STORE_ATTR 残留在栈上未消费，整个赋值丢失。R3 已修复三元 wrapping（属性取值），但未覆盖三元作 STORE_ATTR 赋值的 value（即 `a.b = ternary` 这种属性赋值模式）。

### 错误 10 — if 体内三元同时作位置参数和关键字参数 `f(a if cond else b, x=d if e else g)` 丢失关键字名

- 测试文件：test_adv09_ternary_call_arg_and_kwarg.py
- 源码：
  ```python
  if c:
      f(a if cond else b, x=d if e else g)
  ```
- 反编译结果：
  ```python
  if c:
      f(a if cond else b, d if e else g)
  ```
- 失败信息：指令数不匹配 18 vs 17（原始含 `LOAD_CONST ('x',); KW_NAMES; PRECALL; CALL`，重编缺 `KW_NAMES`）
- 根因分析：`f(a if cond else b, x=d if e else g)` 字节码为 `PUSH_NULL; LOAD_NAME f; LOAD_NAME a; LOAD_NAME cond; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME b; LOAD_NAME d; LOAD_NAME e; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME g; LOAD_CONST ('x',); KW_NAMES; PRECALL; CALL`。当 kwarg 的 value 是三元时，整个调用被识别为「TernaryRegion in Call」，KW_NAMES 与 kwarg 名称 `x=` 关联丢失，最终关键字参数 `x=ternary` 退化为位置参数 `ternary`。R3 已覆盖 ternary call arg（位置参数），但未覆盖「三元同时作位置参数和关键字参数」混合场景（含 KW_NAMES 但部分参数是三元）。

### 错误 11 — if 体内三元作 list literal 元素 `r = [a if cond else b, d if e else f]` 退化为独立 Expr + 单元素 list

- 测试文件：test_adv09_ternary_list_elem.py
- 源码：
  ```python
  if c:
      r = [a if cond else b, d if e else f]
  ```
- 反编译结果：
  ```python
  if c:
      (a if cond else b)
  r = [d if e else f]
  ```
- 失败信息：指令数不匹配 14 vs 13（原始含 `LOAD_NAME a; LOAD_NAME cond; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME b; LOAD_NAME d; LOAD_NAME e; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME f; BUILD_LIST 2; STORE_NAME r`，重编缺一个 BUILD_LIST 元素，且把 `(a if cond else b)` 拆为独立 Expr）
- 根因分析：`[a if cond else b, d if e else f]` 字节码为 `LOAD_NAME a; LOAD_NAME cond; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME b; LOAD_NAME d; LOAD_NAME e; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME f; BUILD_LIST 2; STORE_NAME r`。`_build_store_statement` 的 list literal 重建假设元素都是简单 LOAD_* 表达式，未识别 list 元素位置的三元。第一个三元被识别为独立 Expr 语句输出（`POP_JUMP_FORWARD_IF_FALSE` 控制流被当作独立 if 区域），第二个三元作为 BUILD_LIST 唯一元素。最终 list 退化为单元素 `[d if e else f]`。R7 已修复 walrus 作 list 字面量元素（`[walrus]`），但未覆盖三元作 list 字面量元素（`[ternary, ternary]`，多三元并列）。

### 错误 12 — if 体内三元作多关键字参数 `f(x=a if cond else b, y=d if e else g)` 全部丢失关键字名

- 测试文件：test_adv09_ternary_nested_kwarg.py
- 源码：
  ```python
  if c:
      f(x=a if cond else b, y=d if e else g)
  ```
- 反编译结果：
  ```python
  if c:
      f(a if cond else b, d if e else g)
  ```
- 失败信息：指令数不匹配 18 vs 17（原始含 `LOAD_CONST ('x', 'y'); KW_NAMES; PRECALL; CALL`，重编缺 `KW_NAMES`，两个 kwarg 都退化为位置参数）
- 根因分析：`f(x=a if cond else b, y=d if e else g)` 字节码为 `PUSH_NULL; LOAD_NAME f; LOAD_NAME a; LOAD_NAME cond; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME b; LOAD_NAME d; LOAD_NAME e; POP_JUMP_FORWARD_IF_FALSE; LOAD_NAME g; LOAD_CONST ('x', 'y'); KW_NAMES; PRECALL; CALL`。多个三元 kwarg 同时存在时，整个调用被识别为「TernaryRegion in Call」，KW_NAMES 与两个 kwarg 名称 `x=`/`y=` 关联全部丢失，两个关键字参数都退化为位置参数。R3 已覆盖 ternary call arg（位置参数），但未覆盖「多个三元同时作 kwarg」场景。

### 错误 13 — if 体内嵌套函数默认参数带 walrus `def f(x=(n := 1))` walrus 退化为独立赋值

- 测试文件：test_adv09_nested_func_default_walrus.py
- 源码：
  ```python
  if c:
      def f(x=(n := 1)):
          return x
  ```
- 反编译结果：
  ```python
  if c:
      n = 1
      def f(x):
          return x
  ```
- 失败信息：指令数不匹配 13 vs 11（原始含 `LOAD_CONST 1; COPY 1; STORE_NAME n; BUILD_TUPLE 1; LOAD_CONST <code>; MAKE_FUNCTION 1`，重编缺 `COPY 1; STORE_NAME n; BUILD_TUPLE 1`，walrus 被提取为独立 `n = 1`，MAKE_FUNCTION arg=0 默认值丢失）
- 根因分析：`def f(x=(n := 1))` 字节码为 `LOAD_CONST 1; COPY 1; STORE_NAME n; BUILD_TUPLE 1; LOAD_CONST <code>; MAKE_FUNCTION 1`（默认值通过 BUILD_TUPLE 传入，walrus 的 COPY+STORE_NAME n 副作用在默认值构造时执行）。`_build_store_statement` 的 walrus 识别路径（line 16567-16713）检测到 `COPY + STORE_NAME n` 时，没识别后续是 `BUILD_TUPLE + MAKE_FUNCTION`（函数默认值构造路径），就把 walrus 提前为独立 `n = 1`，并从函数默认值 tuple 中移除了 walrus 表达式。R5 已修复 lambda defaults，R6 已修复 lambda outer/kw defaults，R8 已修复 lambda with walrus default（`lambda x=(n := 1): x`），但 R8 修复仅限 lambda（`MAKE_FUNCTION` 后无 STORE_NAME），未覆盖嵌套 `def` 的 walrus 默认参数（`MAKE_FUNCTION` 后跟 `STORE_NAME f`，且 def 有独立 body code object）。

### 错误 14 — if 体内 lambda 调用含多个关键字参数 `(lambda x, y: x + y)(x=1, y=2)` 退化为无参数 lambda

- 测试文件：test_adv09_lambda_call_multi_kwargs.py
- 源码：
  ```python
  if c:
      r = (lambda x, y: x + y)(x=1, y=2)
  ```
- 反编译结果：
  ```python
  if c:
      r = (lambda *args, **kwargs: None)(x=1, y=2)
  ```
- 失败信息：嵌套 code object 不匹配（指令 3，5 vs 3）：原始 lambda body 含 `LOAD_FAST x; LOAD_FAST y; BINARY_OP +; RETURN_VALUE`，重编 lambda body 退化为 `LOAD_CONST None; RETURN_VALUE`（无参数，body 为 None）
- 根因分析：`(lambda x, y: x + y)(x=1, y=2)` 字节码为 `PUSH_NULL; LOAD_CONST <lambda_code>; LOAD_CONST (1, 2); LOAD_CONST ('x', 'y'); KW_NAMES; MAKE_FUNCTION 2; PRECALL 1; CALL 1`（lambda 用 MAKE_FUNCTION arg=2 加载默认值 + KW_NAMES）。`expr_reconstructor` 重建 lambda 时未正确解析 KW_NAMES 指令，把 lambda 的参数列表（`x, y`）丢失，重建为无参数 lambda `lambda: None`（fallback 路径），同时 lambda body 也丢失（变 `LOAD_CONST None`）。R5 已修复 lambda defaults，R6 已修复 lambda outer/kw defaults，但未覆盖「lambda 本身被调用 + 调用时使用关键字参数」场景（lambda 是 MAKE_FUNCTION 后立即 CALL，而非赋值给变量后再调用）。

### 错误 15 — if 体内嵌套推导式带 walrus `[[y := x for x in a] for a in b]` walrus 退化为常量 True

- 测试文件：test_adv09_nested_comprehension_walrus.py
- 源码：
  ```python
  if c:
      r = [[y := x for x in a] for a in b]
  ```
- 反编译结果：
  ```python
  if c:
      r = [[True for x in a] for a in b]
  ```
- 失败信息：嵌套 code object 不匹配（指令 2，9 vs 7）：原始内层 listcomp 含 `LOAD_FAST x; COPY 1; STORE_GLOBAL y; LIST_APPEND`，重编内层 listcomp 退化为 `LOAD_CONST True; LIST_APPEND`（walrus `y := x` 退化为常量 True）
- 根因分析：`[[y := x for x in a] for a in b]` 外层 listcomp 字节码为 `BUILD_LIST 0; LOAD_NAME b; GET_ITER; FOR_ITER; STORE_NAME a; LOAD_NAME a; GET_ITER; <inner listcomp>; LIST_APPEND`。内层 listcomp 字节码为 `LOAD_FAST x; COPY 1; STORE_GLOBAL y; LIST_APPEND`（walrus `y := x` 的 COPY+STORE 副作用在 LIST_APPEND 之前执行）。`ComprehensionGenerator` 重建内层 listcomp 的 element 时，未识别 `COPY + STORE` walrus 模式，把 walrus 表达式当作未知模式丢弃，回退到常量 True 作为 element。R7 已修复 setcomp walrus（`{(n := f(x)) for x in y}`，单层 setcomp），但未覆盖嵌套 listcomp 中的 walrus（外层 listcomp 内嵌套内层 listcomp，内层 element 含 walrus）。

### 错误 16 — if 体内带参数装饰器 `@decorator(arg=1)` 退化为 `@decorator()`

- 测试文件：test_adv09_decorator_with_args_in_if.py
- 源码：
  ```python
  if c:
      @decorator(arg=1)
      def f():
          return 1
  ```
- 反编译结果：
  ```python
  if c:
      @decorator()
      def f():
          return 1
  ```
- 失败信息：指令数不匹配 17 vs 15（原始含 `LOAD_CONST 1; LOAD_CONST ('arg',); KW_NAMES; PRECALL; CALL`，重编缺 `LOAD_CONST + KW_NAMES`，装饰器参数丢失）
- 根因分析：`@decorator(arg=1)` 字节码为 `LOAD_NAME decorator; LOAD_CONST 1; LOAD_CONST ('arg',); KW_NAMES; PRECALL 0; CALL 0; LOAD_CONST <code>; MAKE_FUNCTION 0; PRECALL 0; CALL 0; STORE_NAME f`。`_build_function_def` 重建装饰器调用时，未识别装饰器调用中的 KW_NAMES 指令（关键字参数），把 `decorator(arg=1)` 退化为 `decorator()`（无参数调用）。R6 已修复 decorator advanced（多装饰器、装饰器链），R8 已修复 dict unpack in call（含 KW_NAMES），但未覆盖装饰器调用本身使用关键字参数（`@deco(k=v)`，装饰器调用含 KW_NAMES）。

---

## 总结

本轮（Round 9）针对 IF 区域反编译器在 R1-R8 已修复范围之外的新错误模式进行探测，共编写 51 个候选测试，确认 16 个真实失败案例：

- **三元作赋值右值/参数（10 个）**：三元作 dict key/value 赋值、属性赋值右值、list literal 元素、函数 keyword 参数（单/多/混合位置参数），核心问题是 `POP_JUMP_FORWARD_IF_FALSE` 控制流被识别为独立 if 区域，三元被拆出作为独立 Expr，KW_NAMES 与 kwarg 名关联丢失
- **walrus 副作用（2 个）**：walrus 后跟 LOAD_ATTR 作为赋值右值、嵌套函数默认参数带 walrus，核心问题是 `_build_store_statement` 的 walrus 识别只匹配 `_LITERAL_BUILD_OPS` 不含 LOAD_ATTR/MAKE_FUNCTION
- **del 嵌套目标（1 个）**：`del a[b].c` 下标+属性混合 del 目标，`_build_delete_stmt` 未识别前导 BINARY_SUBSCR
- **for 多元 tuple 目标（1 个）**：`for (a, b), (c, d) in pairs` 嵌套 UNPACK_SEQUENCE，`_generate_for` 只识别一层 tuple 解包
- **with as tuple 目标（1 个）**：`with ctx as (a, b)` 含 UNPACK_SEQUENCE，`_generate_with` 的 as 目标识别未覆盖 tuple 解包
- **raise 无参数（1 个）**：`raise` 在 except body 的 if body 中，反编译器把 raise 提升到外层 except body 末尾

主要根因集中在三方面：(1) 三元/BoolOp 区域识别过于激进，把表达式内嵌的三元（POP_JUMP_FORWARD_IF_FALSE）当作独立 if 区域，破坏外层赋值/调用结构（10 个错误）；(2) walrus 识别的「后续字面量构造」白名单 `_LITERAL_BUILD_OPS` 不完整，未含 LOAD_ATTR/MAKE_FUNCTION/BUILD_TUPLE 等路径（2 个错误）；(3) tuple unpack / del target / with as target 在多类型混合目标场景下识别不全（3 个错误）；(4) 异常控制流（re-raise）在 if body 内被错误提升到外层 except body（1 个错误）。
