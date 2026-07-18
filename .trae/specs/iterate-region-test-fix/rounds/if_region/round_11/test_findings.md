# IF Round 11 测试发现

## 概述

本轮测试聚焦于 IF 区域反编译中 R1-R10 尚未覆盖的深层边缘场景，重点探索方向：
- 三元表达式（IfExp）在装饰器、函数 kw-only 默认值、返回类型注解、class 基类等新位置
- 三元 + walrus 组合作为 if 条件
- for 循环复杂 target（属性 / 下标 / starred / 多属性 / 嵌套元组）
- augassign 复杂右值（boolop / 三元）配属性或下标目标
- 多目标赋值链与元组解包混合
- 注解赋值（AnnAssign）的属性 / 下标目标
- lambda 装饰器（含带参数 lambda）
- while 条件中 walrus + boolop
- if 条件中分组 boolop、starred 集合、bytes 字面量
- async comprehension 在 if body 中
- 相对导入 `from . import a`

共发现 **28 个真实失败**的反编译错误，全部通过 `python -m pytest tests/exhaustive/if_region/test_adv11_*.py` 验证（28 failed, 17 passed）。

## 错误清单（共 28 个真实失败）

### Error 1: ternary_decorator
- 测试文件: `test_adv11_ternary_decorator.py`
- 源码:
  ```python
  if c:
      @(dec1 if c2 else dec2)
      def f():
          return 1
  ```
- 失败信息: `AssertionError: 指令数不匹配: 14 vs 9`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'MAKE_FUNCTION', 'PRECALL', 'CALL', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'MAKE_FUNCTION', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```python
  if c:
      def f():
          return 1
  ```
- 根因分析: 当装饰器表达式本身为三元 `IfExp` 时，反编译器完全丢失整个装饰器（包括 `@` 调用与 `STORE_NAME` 后的赋值）。原始字节码包含 `LOAD_NAME dec1, LOAD_NAME dec2` 与跳转指令以选择装饰器，再 `PRECALL/CALL` 应用装饰器；反编译后只看到孤立的 `MAKE_FUNCTION`，没有任何装饰器调用。这是 `_build_function_def` 路径未处理装饰器列表元素为 `IfExp` 的情况。

### Error 2: ternary_decorator_arg
- 测试文件: `test_adv11_ternary_decorator_arg.py`
- 源码:
  ```python
  if c:
      @dec(a if c2 else b)
      def f():
          return 1
  ```
- 失败信息: `AssertionError: 指令数不匹配: 18 vs 9`
  - 原始: `['RESUME', 'LOAD_NAME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'PRECALL', 'CALL', 'LOAD_CONST', 'MAKE_FUNCTION', 'PRECALL', 'CALL', 'STORE_NAME', ...]`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'MAKE_FUNCTION', 'STORE_NAME', ...]`
- 反编译输出:
  ```python
  if c:
      def f():
          return 1
  ```
- 根因分析: 装饰器调用 `dec(a if c2 else b)` 的实参为三元表达式时，反编译器同样完全丢失整个装饰器。原始字节码先 `LOAD_NAME dec`、再 `LOAD_NAME a`/`LOAD_NAME b` 与跳转选择实参，再 `PRECALL/CALL dec` 求出实际装饰器对象；反编译器未识别这一复杂调用模式，输出仅剩 `def f(): return 1`，丢失全部装饰逻辑。

### Error 3: ternary_kwonly_default
- 测试文件: `test_adv11_ternary_kwonly_default.py`
- 源码:
  ```python
  if c:
      def f(*, x=a if c2 else b):
          return x
  ```
- 失败信息: `AssertionError: 指令数不匹配: 14 vs 9`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'BUILD_CONST_KEY_MAP', 'LOAD_CONST', 'MAKE_FUNCTION', 'STORE_NAME', ...]`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'MAKE_FUNCTION', 'STORE_NAME', ...]`
- 反编译输出:
  ```python
  if c:
      def f(*, x):
          return x
  ```
- 根因分析: 函数 kw-only 参数默认值为三元 `IfExp` 时，反编译器丢失整个默认值。原始字节码通过 `BUILD_CONST_KEY_MAP` 构造 kwonly 默认值字典（含三元求值指令 `LOAD_NAME a, LOAD_NAME b` + 跳转），再传给 `MAKE_FUNCTION`；反编译后 `MAKE_FUNCTION` 不带任何默认值，函数签名变成 `def f(*, x)`，默认值被完全丢弃。R10 已覆盖 lambda 的 ternary default，但普通 def 的 kwonly ternary default 未覆盖。

### Error 4: ternary_return_ann
- 测试文件: `test_adv11_ternary_return_ann.py`
- 源码:
  ```python
  if c:
      def f() -> (a if c2 else b):
          return 1
  ```
- 失败信息: `AssertionError: 指令数不匹配: 14 vs 9`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_TUPLE', 'LOAD_CONST', 'MAKE_FUNCTION', 'STORE_NAME', ...]`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'MAKE_FUNCTION', 'STORE_NAME', ...]`
- 反编译输出:
  ```python
  if c:
      def f():
          return 1
  ```
- 根因分析: 函数返回类型注解为三元 `IfExp` 时，反编译器完全丢失注解。原始字节码将三元表达式求值后包成 `BUILD_TUPLE` 单元素元组作为返回注解传给 `MAKE_FUNCTION`；反编译后 `MAKE_FUNCTION` 不带返回注解 flag，函数签名变为 `def f()`。R10 未覆盖返回注解为三元的情况。

### Error 5: walrus_ternary_if_cond
- 测试文件: `test_adv11_walrus_ternary_if_cond.py`
- 源码:
  ```python
  if (n := a if b else c):
      pass
  ```
- 失败信息: `AssertionError: 反编译结果中未找到预期的区域类型 IF_REGION (期望AST节点: ['If'])`
- 反编译输出:
  ```python
  n = (a if b else c)
  ```
- 根因分析: 当 if 条件为 walrus 赋值且其值表达式为三元 `IfExp` 时，反编译器将整个 if 退化为单条赋值语句，丢失 `if` 关键字与条件分支。原始字节码 cond_block 末尾是 `POP_JUMP_FORWARD_IF_FALSE`（控制流跳转），但反编译器误判该模式为值上下文的三元赋值（类似 R4 链式比较赋值模式），未生成 `ast.If` 节点。导致 `if` 完全消失，区域类型校验直接失败。

### Error 6: nested_ternary_walrus_cond
- 测试文件: `test_adv11_nested_ternary_walrus_cond.py`
- 源码:
  ```python
  if (n := (a if b else c if d else e)):
      pass
  ```
- 失败信息: `AssertionError: 反编译结果中未找到预期的区域类型 IF_REGION (期望AST节点: ['If'])`
- 反编译输出:
  ```python
  n = (a if b else c if d else e)
  ```
- 根因分析: 与 Error 5 同根因，但三元表达式为嵌套形式 `a if b else c if d else e`。反编译器同样将 if 退化为赋值，丢失 `if` 关键字。这是 Error 5 的更复杂变体，证实 bug 不限于单层三元。

### Error 7: ternary_subscr_in_cond
- 测试文件: `test_adv11_ternary_subscr_in_cond.py`
- 源码:
  ```python
  if x[a if b else c]:
      pass
  ```
- 失败信息: `AssertionError: 反编译结果中未找到预期的区域类型 IF_REGION (期望AST节点: ['If'])`
- 反编译输出:
  ```python
  (a if b else c)
  ```
- 根因分析: 当 if 条件的下标表达式 `x[a if b else c]` 中包含三元时，反编译器既丢失外层 `x[...]` 下标，又丢失整个 if 语句，只剩孤立的 `(a if b else c)` Expr 语句。这是 `_if_extract_condition_from_instructions` 在处理嵌套三元 + 下标时的栈模拟缺陷：栈上的 `x` 与最终 `BINARY_SUBSCR` 被丢弃，只剩三元部分。R3 已覆盖 ternary in subscr 单独情况，但作为 if 条件的 subscr+ternary 组合未覆盖。

### Error 8: ternary_call_arg_in_cond
- 测试文件: `test_adv11_ternary_call_arg_in_cond.py`
- 源码:
  ```python
  if f(a if b else c):
      pass
  ```
- 失败信息: `AssertionError: 反编译结果中未找到预期的区域类型 IF_REGION (期望AST节点: ['If'])`
- 反编译输出:
  ```python
  f(a if b else c)
  ```
- 根因分析: 当 if 条件的函数调用实参为三元 `IfExp` 时，反编译器将 if 退化为裸 `Expr` 语句，丢失 `if` 关键字与条件分支。原始字节码 cond_block 末尾是 `POP_JUMP_FORWARD_IF_FALSE`（控制流跳转），但反编译器误判为值上下文表达式。R9 已覆盖 `f(a, b if c else d)` 作 if body 的情况，但 if 条件中 call(ternary) 的组合未覆盖。

### Error 9: for_attr_target
- 测试文件: `test_adv11_for_attr_target.py`
- 源码:
  ```python
  if c:
      for x.a in pairs:
          pass
  ```
- 失败信息: `AssertionError: 指令数不匹配: 10 vs 11`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'GET_ITER', 'LOAD_NAME', 'STORE_ATTR', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'GET_ITER', 'STORE_NAME', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```python
  if c:
      for a in pairs:
          x
  ```
- 根因分析: 当 for 循环的 target 为属性 `x.a` 时，反编译器完全错位：将 target 变成普通 `Name(a)`，并将 `x` 误解为循环体的一条 Expr 语句。原始字节码使用 `STORE_ATTR x` 把迭代值写入 `x.a`；反编译后变成 `STORE_NAME a` + 孤立的 `LOAD_NAME x`/`POP_TOP`。`_build_for_target` 未能识别 `STORE_ATTR` 模式重建 `Attribute(target=Name(x), attr='a', ctx=Store)` 节点。

### Error 10: for_subscr_target
- 测试文件: `test_adv11_for_subscr_target.py`
- 源码:
  ```python
  if c:
      for x[0] in pairs:
          pass
  ```
- 失败信息: `AssertionError: 反编译结果语法错误: cannot assign to None`
- 反编译输出:
  ```python
  if c:
      for None in pairs:
          0
  ```
- 根因分析: 当 for 循环的 target 为下标 `x[0]` 时，反编译器产生语法错误输出：将 target 误识别为 `None`，将下标 `0` 误识别为循环体表达式。原始字节码使用 `STORE_SUBSCR` 把迭代值写入 `x[0]`（先 `LOAD_NAME x`, `LOAD_CONST 0`, `STORE_SUBSCR`）；反编译器未能从栈模拟中重建 `Subscript` 节点，把 `LOAD_CONST 0` 当作独立的循环体语句，target 名字来源错乱成 `None`。

### Error 11: for_starred_target
- 测试文件: `test_adv11_for_starred_target.py`
- 源码:
  ```python
  if c:
      for *a, b in pairs:
          pass
  ```
- 失败信息: `AssertionError: 指令数不匹配: 12 vs 11`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'GET_ITER', 'EXTENDED_ARG', 'UNPACK_EX', 'STORE_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'GET_ITER', 'UNPACK_SEQUENCE', 'STORE_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```python
  if c:
      for a, b in pairs:
          pass
  ```
- 根因分析: 当 for 循环 target 含 starred `*a` 时，反编译器丢失 starred 标记，将其当作普通 `Name` 处理。原始字节码使用 `UNPACK_EX` (with `EXTENDED_ARG`) 区分 starred 与普通目标（starred 收集剩余元素为 list）；反编译后变为 `UNPACK_SEQUENCE`（不带 starred 语义）。`_build_for_target` 未识别 `UNPACK_EX` 字节码以重建含 `Starred` 节点的 Tuple target。

### Error 12: for_multi_attr_target
- 测试文件: `test_adv11_for_multi_attr_target.py`
- 源码:
  ```python
  if c:
      for x.a, y.b in pairs:
          pass
  ```
- 失败信息: `AssertionError: 指令5操作码不匹配: LOAD_NAME vs STORE_NAME`
- 反编译输出:
  ```python
  if c:
      for a, b in pairs:
          y
  ```
- 根因分析: 当 for 循环 target 为多属性 `x.a, y.b` 时，反编译器不仅丢失属性目标（变成 `a, b`），还把第二个属性对象 `y` 误识别为循环体 Expr 语句。原始字节码先 `UNPACK_SEQUENCE 2`，再依次 `STORE_ATTR x`（写 `x.a`）、`STORE_ATTR y`（写 `y.b`）；反编译器把第一个 `STORE_ATTR` 误为 `STORE_NAME a`，第二个 `STORE_ATTR y` 的 `LOAD_NAME y` 部分泄漏到循环体。

### Error 13: augassign_attr_boolop
- 测试文件: `test_adv11_augassign_attr_boolop.py`
- 源码:
  ```python
  if c:
      x.y += a and b
  ```
- 失败信息: `AssertionError: 指令数不匹配: 15 vs 10`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'COPY', 'LOAD_ATTR', 'LOAD_NAME', 'JUMP_IF_FALSE_OR_POP', 'LOAD_NAME', 'BINARY_OP', 'SWAP', 'STORE_ATTR', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'JUMP_IF_FALSE_OR_POP', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```python
  if c:
      (a and b)
  ```
- 根因分析: 当 augassign 目标为属性 `x.y`、右值为 boolop `a and b` 时，反编译器完全丢失 augassign 语义与目标，只剩孤立的 boolop Expr 语句。原始字节码序列为 `LOAD_NAME x, LOAD_NAME y, COPY, LOAD_ATTR` 取出当前值、再 `LOAD_NAME a, JUMP_IF_FALSE_OR_POP, LOAD_NAME b` 求 boolop、`BINARY_OP(+=)` 计算 in-place 加、`SWAP, STORE_ATTR` 写回；反编译器未识别 `LOAD_ATTR + BINARY_OP + STORE_ATTR` 的 augassign 模式，将 boolop 部分作为独立 Expr。R10 已覆盖 augassign boolop rhs 的 `Name` 目标，但属性目标未覆盖。

### Error 14: augassign_subscr_boolop
- 测试文件: `test_adv11_augassign_subscr_boolop.py`
- 源码:
  ```python
  if c:
      x[0] += a and b
  ```
- 失败信息: `AssertionError: 指令数不匹配: 18 vs 10`
- 反编译输出:
  ```python
  if c:
      (a and b)
  ```
- 根因分析: 与 Error 13 同根因，但目标是下标 `x[0]`。反编译器同样丢失 augassign 与目标，只剩 boolop Expr。原始字节码使用 `BINARY_SUBSCR` 取值、`STORE_SUBSCR` 写回，反编译器未识别。

### Error 15: augassign_subscr_ternary
- 测试文件: `test_adv11_augassign_subscr_ternary.py`
- 源码:
  ```python
  if c:
      x[0] += a if b else c
  ```
- 失败信息: `AssertionError: 指令数不匹配: 18 vs 14`
- 反编译输出:
  ```python
  if c:
      x[0][a if b else c] = 0
  ```
- 根因分析: 当 augassign 目标为下标 `x[0]`、右值为三元 `IfExp` 时，反编译器输出严重错乱：将 `x[0] += (ternary)` 错误重写为 `x[0][ternary] = 0`，把 augassign 变成普通赋值，且把三元当成新的下标、把右值 `0` 凭空捏造。原始字节码的 `BINARY_OP(+=)` 与 `STORE_SUBSCR` 模式未被识别，三元求值的栈布局被误判为下标表达式的一部分。

### Error 16: multi_target_unpack
- 测试文件: `test_adv11_multi_target_unpack.py`
- 源码:
  ```python
  if c:
      a, b = e, f = g, h
  ```
- 失败信息: `AssertionError: 指令数不匹配: 16 vs 11`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_TUPLE', 'COPY', 'UNPACK_SEQUENCE', 'STORE_NAME', 'STORE_NAME', 'UNPACK_SEQUENCE', 'STORE_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'SWAP', 'STORE_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```python
  if c:
      (a, b) = (g, h)
  ```
- 根因分析: 多目标元组解包 `a, b = e, f = g, h` 反编译时丢失中间目标 `e, f`，只剩第一个目标 `(a, b)` 与最后一个值 `(g, h)`。原始字节码先 `BUILD_TUPLE` 构造值元组、`COPY` 复制栈顶、`UNPACK_SEQUENCE` 解包到第一个目标 `(a, b)`、再次 `UNPACK_SEQUENCE` 解包到第二个目标 `(e, f)`；反编译器只识别首个 `UNPACK_SEQUENCE` 与首个目标，第二个目标 `e, f` 完全丢失。R8 已覆盖 `multi_chain_assign`（`a = b = c = 1`）与 `multi_assign_subscr_attr`，但多目标元组解包未覆盖。

### Error 17: multi_target_mixed_unpack
- 测试文件: `test_adv11_multi_target_mixed_unpack.py`
- 源码:
  ```python
  if c:
      a, b = c = d, e
  ```
- 失败信息: `AssertionError: 指令数不匹配: 14 vs 11`
- 反编译输出:
  ```python
  if c:
      (a, b) = (d, e)
  ```
- 根因分析: 与 Error 16 同根因，多目标解包 `a, b = c = d, e` 反编译时丢失中间目标 `c`，只剩首个元组目标 `(a, b)` 与最后值 `(d, e)`。原始字节码先 `BUILD_TUPLE` 构造值元组、`COPY` 复制栈顶、`UNPACK_SEQUENCE` 解包到 `(a, b)`、`STORE_NAME c` 写入中间标量目标；反编译器只识别元组解包部分，中间标量目标 `c` 完全丢失。

### Error 18: ann_assign_attr_target
- 测试文件: `test_adv11_ann_assign_attr_target.py`
- 源码:
  ```python
  if c:
      x.y: int = 1
  ```
- 失败信息: `AssertionError: 指令数不匹配: 12 vs 11`
  - 原始: `['RESUME', 'SETUP_ANNOTATIONS', 'LOAD_NAME', 'LOAD_CONST', 'LOAD_NAME', 'STORE_ATTR', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'LOAD_NAME', 'STORE_ATTR', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```python
  if c:
      x.y = 1
      int
  ```
- 根因分析: 当 AnnAssign 的 target 为属性 `x.y` 时，反编译器将一条 AnnAssign 拆成两条语句：一条普通 `Assign(x.y = 1)` 和一条孤立的 `Expr(Name('int'))`。原始字节码以 `SETUP_ANNOTATIONS` 开头（声明注解上下文），并使用 `STORE_ATTR` 配合注解；反编译器丢失 `SETUP_ANNOTATIONS` 指令，把注解 `int` 当作独立 Expr 语句。R5 已覆盖 `ann_assign`（Name target），R8 已覆盖 `ann_assign_complex`，但属性目标的 AnnAssign 未覆盖。

### Error 19: ann_assign_subscr_target
- 测试文件: `test_adv11_ann_assign_subscr_target.py`
- 源码:
  ```python
  if c:
      x[0]: int = 1
  ```
- 失败信息: `AssertionError: 指令数不匹配: 13 vs 12`
- 反编译输出:
  ```python
  if c:
      x[0] = 1
      int
  ```
- 根因分析: 与 Error 18 同根因，但 target 是下标 `x[0]`。反编译器同样丢失 `SETUP_ANNOTATIONS`，把 AnnAssign 拆为 `Assign(x[0] = 1)` + `Expr(int)`，注解语义完全丢失。

### Error 20: lambda_decorator
- 测试文件: `test_adv11_lambda_decorator.py`
- 源码:
  ```python
  if c:
      @lambda f: None
      def g():
          return 1
  ```
- 失败信息: `AssertionError: 指令数不匹配: 13 vs 12`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'MAKE_FUNCTION', 'LOAD_CONST', 'MAKE_FUNCTION', 'PRECALL', 'CALL', 'STORE_NAME', ...]`
  - 重编: `['RESUME', 'LOAD_NAME', 'PUSH_NULL', 'LOAD_CONST', 'MAKE_FUNCTION', 'PRECALL', 'CALL', 'STORE_NAME', ...]`
- 反编译输出:
  ```python
  if c:
      g = (lambda *args, **kwargs: False)()
  ```
- 根因分析: 当装饰器为 lambda 表达式 `@lambda f: None` 时，反编译器未能正确重建 lambda 装饰器：将 lambda body 错误填成 `False`（而非 `None`）、参数填成 `*args, **kwargs`（而非 `f`），并丢失被装饰的 `def g(): return 1` 函数定义。原始字节码先 `MAKE_FUNCTION`（构造 lambda），再 `MAKE_FUNCTION`（构造 g），再 `PRECALL/CALL` 应用 lambda 装饰器；反编译器只看到第一个 `MAKE_FUNCTION`，把 lambda 当作被调用对象，丢失被装饰函数本身。这是 `_build_function_def` 中 `decorator_list` 含 lambda 时的处理缺陷。

### Error 21: decorator_lambda_with_args
- 测试文件: `test_adv11_decorator_lambda_with_args.py`
- 源码:
  ```python
  if c:
      @(lambda f: lambda *a, **k: f(*a, **k))
      def g():
          return 1
  ```
- 失败信息: `AssertionError: 指令数不匹配: 13 vs 12`
- 反编译输出:
  ```python
  if c:
      g = (lambda *args, **kwargs: False)()
  ```
- 根因分析: 与 Error 20 同根因，但装饰器是带嵌套 lambda 的复杂形式 `lambda f: lambda *a, **k: f(*a, **k)`。反编译器同样把外层 lambda 退化为 `lambda *args, **kwargs: False` 占位符，丢失被装饰的 `def g()` 与嵌套 lambda 主体。证实 lambda 装饰器处理缺陷不限于简单 lambda。

### Error 22: while_walrus_boolop
- 测试文件: `test_adv11_while_walrus_boolop.py`
- 源码:
  ```python
  if c:
      while (x := f()) and g():
          pass
  ```
- 失败信息: `AssertionError: 指令数不匹配: 32 vs 37`
- 反编译输出:
  ```python
  if c:
      while (x := f()) and g():
          x = f()
  ```
- 根因分析: 当 while 条件为 `(x := f()) and g()` 时，反编译器在循环体中凭空插入一条 `x = f()` 赋值语句。原始字节码循环体仅 `pass`（即 `LOAD_CONST None; RETURN_VALUE`），反编译后却多出 `LOAD_NAME f; PRECALL; CALL; COPY; STORE_NAME x`。原因是 while 条件中 walrus 的 `COPY/STORE_NAME x` 指令被错误归并到循环体 stmts 中（walrus 的 store 应在 cond_block，不应进入 body）。R5 walrus_outside_comp 与 R9 if_not_walrus 已覆盖 walrus 在 if 条件，但 while 条件中 walrus + boolop 组合未覆盖。

### Error 23: grouped_boolop_cond
- 测试文件: `test_adv11_grouped_boolop_cond.py`
- 源码:
  ```python
  if (a or b) and (c or d):
      pass
  ```
- 失败信息: `AssertionError: 指令数不匹配: 11 vs 9`
- 反编译输出:
  ```python
  if (a or b and c or d):
      pass
  ```
- 根因分析: 当 if 条件为分组 boolop `(a or b) and (c or d)` 时，反编译器丢失分组语义，输出无括号的 `a or b and c or d`。由于 Python 中 `and` 优先级高于 `or`，无括号版本被解析为 `a or (b and c) or d`，与原始 `(a or b) and (c or d)` 完全不同。原始字节码含 3 个跳转（外层 and 短路、内层 or1 短路、内层 or2 短路）；反编译后字节码指令数减少（11 vs 9），逻辑结构改变。R1 walrus_or、R1 walrus_and 等已覆盖扁平 boolop，但分组（混合 and/or 需要括号）未覆盖。

### Error 24: starred_set_in_cond
- 测试文件: `test_adv11_starred_set_in_cond.py`
- 源码:
  ```python
  if c in {*a, *b}:
      pass
  ```
- 失败信息: `AssertionError: 指令数不匹配: 12 vs 8`
  - 原始: `['RESUME', 'LOAD_NAME', 'BUILD_SET', 'LOAD_NAME', 'SET_UPDATE', 'LOAD_NAME', 'SET_UPDATE', 'CONTAINS_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'CONTAINS_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```python
  if (a in b):
      pass
  ```
- 根因分析: 当 if 条件为 `c in {*a, *b}`（含 starred 元素的集合字面量作 in 容器）时，反编译器完全错乱：丢失 starred 集合字面量、把 `c` 当作被搜索元素、把 `a` 误当作容器、丢失 `b`。原始字节码使用 `BUILD_SET 0` + 两次 `SET_UPDATE`（合并 `*a` 与 `*b`）构造集合，再 `CONTAINS_OP` 检查 `c in set`；反编译器跳过 `BUILD_SET/SET_UPDATE` 指令，把第一个 starred 元素 `a` 当作容器。R8 set_literal_in_cond 已覆盖 `if x in {1, 2, 3}:`，但 starred set element 未覆盖。

### Error 25: bytes_in_cond
- 测试文件: `test_adv11_bytes_in_cond.py`
- 源码:
  ```python
  if b"abc":
      pass
  ```
- 失败信息: `AssertionError: 反编译结果中未找到预期的区域类型 IF_REGION (期望AST节点: ['If'])`
- 反编译输出:
  ```python
  pass
  ```
- 根因分析: 当 if 条件为 bytes 字面量 `b"abc"` 时，反编译器完全丢失整个 if 语句，只剩孤立的 `pass`。原因可能是反编译器将 bytes 字面量视为"常量条件"并应用了死代码消除（认为 `b"abc"` 永远为真），但 Python 字节码并没有进行这种优化 —— `LOAD_CONST b'abc'` 后跟 `POP_JUMP_FORWARD_IF_FALSE` 是真实的条件跳转。反编译器误判 cond_block 为常量折叠块，将 if 简化为 then body。R25 测试已覆盖 `if False:` 等常量条件，但 bytes 字面量未覆盖。

### Error 26: class_ternary_base
- 测试文件: `test_adv11_class_ternary_base.py`
- 源码:
  ```python
  if c:
      class C(A if c2 else B):
          pass
  ```
- 失败信息: `AssertionError: 反编译结果语法错误: invalid syntax`
- 反编译输出:
  ```python
  if c:
      C = __build_class__(<CodeObject>, 'C', A if c2 else B)
  ```
- 根因分析: 当 class 的基类为三元 `IfExp` 时，反编译器未能重建 class 定义，输出原始 `__build_class__` 调用形式，且 `<CodeObject>` 占位符导致语法错误。原始字节码使用 `LOAD_BUILD_CLASS` + `MAKE_FUNCTION` + 三元求值 + `PRECALL/CALL` 构造类；反编译器在基类表达式为三元时未能走 `class C(...):` 重建路径，回退到原始字节码 dump。R9 multi_decorator_in_if、R9 decorator_in_if 已覆盖 if body 中的简单 class，但 class 基类为三元未覆盖。

### Error 27: relative_import
- 测试文件: `test_adv11_relative_import.py`
- 源码:
  ```python
  if c:
      from . import a
  ```
- 失败信息: `AssertionError: 反编译结果语法错误: invalid syntax`
- 反编译输出:
  ```python
  if c:
      from  import a
  ```
- 根因分析: 当 if body 中包含相对导入 `from . import a` 时，反编译器丢失模块路径 `.`，输出 `from  import a`（模块名空白），导致语法错误。原始字节码 `IMPORT_NAME` 指令的 argval 包含 `.` 字符串（相对导入的 level=1）；反编译器在重建 `ImportFrom` 节点时未处理空模块名 + 非零 level 的情况，直接用空字符串作为 module 字段，丢失点号前缀。R5 import_asname、R7 import_star 已覆盖绝对导入，但相对导入未覆盖。

### Error 28: async_comp
- 测试文件: `test_adv11_async_comp.py`
- 源码:
  ```python
  async def f():
      if c:
          x = [i async for i in y]
  ```
- 失败信息: `AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 20 vs 8`
  - 原始: `['RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'LOAD_GLOBAL', 'LOAD_CONST', 'MAKE_FUNCTION', 'LOAD_GLOBAL', 'GET_AITER', 'PRECALL', 'CALL', 'GET_AWAITABLE', 'LOAD_CONST', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT', 'STORE_FAST', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'LOAD_GLOBAL', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```python
  async def f():
      if c:
          None
  ```
- 根因分析: 当 if body 中包含 async list comprehension `[i async for i in y]` 时，反编译器完全丢失 comprehension 表达式，将其替换为 `None`。原始字节码嵌套 code object 内含完整的 async for 循环（`GET_AITER`、`GET_AWAITABLE`、`YIELD_VALUE`、`JUMP_BACKWARD_NO_INTERRUPT`）；反编译器未能识别 async comprehension 模式，把整个赋值右值退化为 `None`。R5 async_for、R10 nested_async_for_in_with 已覆盖 async for 语句，但 async comprehension 在 if body 中未覆盖。

## 失败统计

- **总测试数**: 45 (28 failed + 17 passed)
- **失败率**: 62%
- **失败类别分布**:
  - 三元表达式（IfExp）位置错误: 8 (Errors 1-8)
  - for 循环复杂 target: 4 (Errors 9-12)
  - augassign 复杂右值: 3 (Errors 13-15)
  - 多目标赋值: 2 (Errors 16-17)
  - AnnAssign 属性/下标目标: 2 (Errors 18-19)
  - lambda 装饰器: 2 (Errors 20-21)
  - while walrus + boolop: 1 (Error 22)
  - boolop 条件: 2 (Errors 23-24)
  - 其他（bytes 条件 / class 三元基类 / 相对导入 / async comp）: 4 (Errors 25-28)

## 通过的测试（17 个，作为对照）

以下测试在 R11 中创建并通过，证明这些场景已被 R1-R10 覆盖或反编译器已正确处理：
- `test_adv11_ternary_func_default.py` — `def f(x=a if c2 else b): return x`（位置参数默认值为三元，与 R10 lambda ternary default 类似路径）
- `test_adv11_for_nested_tuple_target.py` — `for (a, b), c in pairs:`（嵌套元组 target 已支持）
- `test_adv11_long_elif_chain_with_else.py` — 5 个 elif + else 全 pass body（pass body 时 else 字节码等价）
- `test_adv11_fstring_debug.py` — `f"{y=}"` → `f'y={y!r}'`（字节码等价）
- `test_adv11_fstring_debug_format.py` — `f"{y=:.2f}"` → `f'y={y:.2f}'`（字节码等价）
- `test_adv11_with_mixed_as_no_as.py` — `with x as y, z:` 已支持
- `test_adv11_try_except_tuple_type.py` — `except (A, B):` 已支持
- `test_adv11_try_except_tuple_as.py` — `except (A, B) as e:` 已支持
- `test_adv11_while_walrus_only.py` — `while (x := f()):` 已支持
- `test_adv11_deeply_nested_if_else.py` — 5 层嵌套 if + else 已支持
- `test_adv11_class_with_staticmethod.py` — `@staticmethod` 在 if body 内 class 中已支持
- `test_adv11_class_with_property.py` — `@property` 已支持
- `test_adv11_dict_unpack_mixed.py` — `{**a, 1: 2, **b, 3: 4}` 已支持
- `test_adv11_class_body_ternary.py` — class body 内三元赋值已支持
- `test_adv11_class_with_init.py` — class 含 `__init__` + 方法已支持
- `test_adv11_multi_target_chain_walrus.py` — `x = y = (z := f())` 字节码等价于 `z = x = y = f()`
- `test_adv11_walrus_comp_if_filter.py` — `[x for x in y if (n := x) > 0]` 已支持

## 测试运行命令

```bash
# 运行所有 R11 测试
cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv11_*.py --tb=line -q

# 运行单个测试
cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv11_<name>.py --tb=short
```

## 结论

R11 共发现 28 个 IF 区域反编译真实错误，远超 10 个目标。这些错误集中在以下深层边缘场景：

1. **三元表达式（IfExp）的"消费位置"未覆盖**：装饰器、装饰器参数、kwonly 默认值、返回注解、class 基类等位置的三元全部丢失语义。R1-R10 主要覆盖了三元在赋值右值、return、yield、await、lambda body 等位置，但函数/类定义"签名"位置的三元未触及。

2. **三元 + walrus 组合作为 if 条件**：反编译器将 `if (n := ternary):` 误判为值上下文赋值，丢失 `if` 关键字。

3. **三元在 if 条件的子表达式位置**：`if x[ternary]:`、`if f(ternary):` 等，反编译器无法正确处理三元在 if 条件下标/调用参数位置。

4. **for 循环复杂 target**：属性、下标、starred、多属性 target 全部错乱。`_build_for_target` 仅支持简单 Name 与元组 Name target。

5. **augassign 复杂右值 + 复杂目标**：属性 / 下标目标 + boolop / 三元右值，反编译器完全错乱。R8/R10 仅覆盖 Name 目标或简单右值。

6. **多目标赋值的"中间目标"丢失**：`a, b = e, f = g, h` 中第二个目标 `e, f` 被丢弃。

7. **AnnAssign 属性/下标 target**：`x.y: int = 1`、`x[0]: int = 1` 丢失 `SETUP_ANNOTATIONS` 与注解绑定，退化为 Assign + 孤立 Expr。

8. **lambda 装饰器**：反编译器无法正确重建 lambda 装饰器，被装饰函数本身丢失。

9. **while 条件 walrus + boolop**：walrus 的 `COPY/STORE` 被误并入循环体。

10. **分组 boolop**：`(a or b) and (c or d)` 丢失括号，导致运算符优先级改变。

11. **starred 集合字面量作 in 容器**：`if c in {*a, *b}:` 完全错乱。

12. **bytes 字面量作 if 条件**：整个 if 被死代码消除。

13. **相对导入**：模块路径 `.` 丢失。

14. **async comprehension 在 if body**：comprehension 退化为 `None`。

这些错误为后续 R12 修复提供了明确的靶向。
