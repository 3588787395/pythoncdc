# IF Round 10 测试发现

## 概述
本轮测试聚焦于 IF 区域反编译中尚未覆盖的复杂表达式场景，重点关注：
- 三元表达式（IfExp）作为各类语句的关键成分（return/yield/raise/assert/await/yield from/lambda default 等）
- f-string 中嵌套三元表达式、format spec 中包含纯表达式
- walrus 在 tuple unpack、dictcomp key 位置
- augassign 的右值为 boolop
- assert 的多条件 boolop + msg 组合
- lambda 默认参数为三元

共发现 **14 个真实失败**的反编译错误，全部通过 `python -m pytest tests/exhaustive/if_region/test_adv10_*.py` 验证。

## 错误清单（共 14 个真实失败）

### Error 1: assert_multi_cond_msg
- 测试文件: test_adv10_assert_multi_cond_msg.py
- 源码: `if c:\n    assert a > 0 and b > 0, "msg" `
- 失败信息: `AssertionError: 指令数不匹配: 17 vs 22`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_ASSERTION_ERROR', 'LOAD_CONST', 'PRECALL', 'CALL', 'RAISE_VARARGS', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_ASSERTION_ERROR', 'LOAD_CONST', 'PRECALL', 'CALL', 'RAISE_VARARGS', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_ASSERTION_ERROR', 'LOAD_CONST', 'PRECALL', 'CALL', 'RAISE_VARARGS', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  if c:
      assert (a > 0), 'msg'
      assert (b > 0), 'msg'
  ```
- 根因分析: `assert` 语句的 test 为 `BoolOp(And, [a>0, b>0])` 时，字节码会以 `JUMP_IF_FALSE_OR_POP` 串联两个比较。反编译器将该 BoolOp 误识别为 assert 的"cleanup else"模式，将原本一条 `assert (a > 0 and b > 0), "msg"` 拆分成两条独立的 assert 语句，每条都重复同样的 msg。原始字节码中只有一处 `LOAD_ASSERTION_ERROR`/`RAISE_VARARGS`，重编后却出现两处，且 boolop 语义被完全丢失（原本 `a>0 and b>0` 同时为假才触发，重编后任一为假即触发）。

### Error 2: assert_ternary
- 测试文件: test_adv10_assert_ternary.py
- 源码: `if c:\n    assert (a if cond else b)`
- 失败信息: `AssertionError: 指令数不匹配: 13 vs 10`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_ASSERTION_ERROR', 'RAISE_VARARGS', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  if c:
      (a if cond else b)
  ```
- 根因分析: `assert` 语句的 test 为三元表达式 `IfExp` 时，反编译器将整个 assert 退化为裸 `Expr` 语句。原始字节码包含 `LOAD_ASSERTION_ERROR` 与 `RAISE_VARARGS(1)` 用于在三元结果为假时抛出 `AssertionError`，但反编译器将 `RAISE_VARARGS` 替换为 `POP_TOP`，完全丢失 `assert` 关键字与 AssertionError 抛出语义。

### Error 3: augassign_boolop_rhs
- 测试文件: test_adv10_augassign_boolop_rhs.py
- 源码: `if c:\n    x += a and b`
- 失败信息: `AssertionError: 指令数不匹配: 12 vs 10`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'JUMP_IF_FALSE_OR_POP', 'LOAD_NAME', 'BINARY_OP', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'JUMP_IF_FALSE_OR_POP', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  if c:
      x = (a and b)
  ```
- 根因分析: augassign `+=` 的右值为 `BoolOp(And, [a, b])` 时，反编译器将其识别为普通赋值 `x = (a and b)`，丢失 `+=` 语义。原始字节码顺序为 `LOAD_NAME x, LOAD_NAME a, JUMP_IF_FALSE_OR_POP, LOAD_NAME b, BINARY_OP(+=), STORE_NAME x`，其中 `BINARY_OP` 操作码参数为 `in-place add`。反编译器未识别 in-place `BINARY_OP` 紧跟 `JUMP_IF_FALSE_OR_POP` 之后的模式，将 boolop 整体作为普通右值赋给 `x`，导致 `LOAD_NAME x`（augassign 的目标 load）和 `BINARY_OP(+=)` 同时丢失。

### Error 4: await_ternary
- 测试文件: test_adv10_await_ternary.py
- 源码: `async def f():\n    if c:\n        x = await (a if cond else b)`
- 失败信息: `AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 17 vs 12`
  - 原始: `['RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'GET_AWAITABLE', 'LOAD_CONST', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT', 'STORE_FAST', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  async def f():
      if c:
          (a if cond else b)
  ```
- 根因分析: `await (三元)` 表达式作赋值右值时，反编译器将 await 与三元合并结果作为裸 `Expr` 语句，丢失 `await` 关键字、`x = ` 赋值目标、`GET_AWAITABLE`/`YIELD_VALUE` 协程轮询序列、以及 `STORE_FAST x` 存储。嵌套 code object 中原本有 `GET_AWAITABLE, LOAD_CONST None, YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT, STORE_FAST x` 共 6 条指令被替换为 `POP_TOP` 一条指令。

### Error 5: dictcomp_walrus_key
- 测试文件: test_adv10_dictcomp_walrus_key.py
- 源码: `if c:\n    r = {(x := k): v for k, v in d.items()}`
- 失败信息: `AssertionError: 嵌套code object不匹配 (指令2): 指令7操作码不匹配: COPY vs LOAD_FAST`
- 反编译输出:
  ```
  if c:
      r = {k: (x := v) for k, v in d.items()}
  ```
- 根因分析: dict comprehension 中 walrus 在 **key** 位置 `{(x := k): v}` 时，反编译器将 walrus 错误地移动到 **value** 位置，并把原本的 key `k` 留在 key 位置。这导致 walrus 绑定的变量从迭代 key 变为迭代 value，语义完全错误。原始字节码在 key 计算阶段有 `COPY` 指令保留 walrus 表达式的值供后续 STORE，但反编译器错误地把它当作 value 位置的 LOAD_FAST 处理。

### Error 6: fstring_format_spec_expr
- 测试文件: test_adv10_fstring_format_spec_expr.py
- 源码: `if c:\n    x = f"{y:{width}}" `
- 失败信息: `AssertionError: 指令数不匹配: 11 vs 14`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'FORMAT_VALUE', 'FORMAT_VALUE', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'LOAD_NAME', 'FORMAT_VALUE', 'LOAD_CONST', 'BUILD_STRING', 'FORMAT_VALUE', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  if c:
      x = f"{y:f'{width}'}"
  ```
- 根因分析: f-string 的 format spec **仅由单个嵌套表达式**（无字面量后缀）构成 `f"{y:{width}}"` 时，反编译器将整个 format spec 误识别为字面字符串 `f'{width}'`，导致内层 `FORMAT_VALUE` 被替换为字面字符串拼接 `BUILD_STRING`。对比已通过的 `test_adv05_fstring_format_spec.py`（`f'{x:{width}.2f}'`，format spec 有 `.2f` 字面量后缀），可看出反编译器只在 format spec 包含字面量部分时才能正确处理嵌套表达式，纯表达式 format spec 会丢失语义。

### Error 7: fstring_ternary
- 测试文件: test_adv10_fstring_ternary.py
- 源码: `if c:\n    x = f"{a if cond else b}" `
- 失败信息: `AssertionError: 指令数不匹配: 11 vs 10`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'FORMAT_VALUE', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  if c:
      x = (a if cond else b)
  ```
- 根因分析: f-string 的 replacement field 包含三元表达式 `f"{a if cond else b}"` 时，反编译器将三元作为裸 `Expr` 赋值给 `x`，丢失 f-string 包装。原始字节码中 `FORMAT_VALUE` 指令负责将三元结果转换为字符串，反编译器误将其当作冗余指令删除，导致 `FORMAT_VALUE` 指令缺失，f-string 退化为普通表达式赋值。

### Error 8: lambda_ternary_default
- 测试文件: test_adv10_lambda_ternary_default.py
- 源码: `if c:\n    f = lambda x=(a if cond else b): x`
- 失败信息: `AssertionError: 指令8操作码不匹配: STORE_NAME vs POP_TOP`
- 反编译输出:
  ```
  if c:
      lambda x=(a if cond else b): x
  ```
- 根因分析: `f = lambda x=(a if cond else b): x` 中 lambda 的默认参数为三元表达式时，反编译器将默认值计算与 lambda 构造作为单独的 `Expr` 语句输出，丢失 `f = ` 赋值。原始字节码在 `MAKE_FUNCTION` 之后有 `STORE_NAME f` 指令保存 lambda 引用，反编译器将其替换为 `POP_TOP`，导致 lambda 表达式无法赋值给变量 `f`。

### Error 9: raise_from_ternary
- 测试文件: test_adv10_raise_from_ternary.py
- 源码: `if c:\n    raise E from (a if cond else b)`
- 失败信息: `AssertionError: 指令数不匹配: 9 vs 10`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'RAISE_VARARGS', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  if c:
      (a if cond else b)
  ```
- 根因分析: `raise E from (三元)` 中异常为简单 NAME_LOAD（非 CALL）时，反编译器将整个 raise 退化为裸 `Expr` 语句，丢失 `raise` 关键字、异常 `E` 和 `from` 子句。原始字节码以 `LOAD_NAME E` 开头、`RAISE_VARARGS(2)` 结尾（参数 2 表示同时给出 exception 和 cause），反编译器把 `RAISE_VARARGS` 替换为 `POP_TOP`，并丢弃 `LOAD_NAME E`。对比已通过的 `test_adv07_raise_ternary_from.py`（`raise E() from (a if cond else b)`，使用 `E()` 调用），可看出反编译器只在异常为 CALL 表达式时才正确处理 raise-from-ternary 模式，NAME_LOAD 异常会触发该 bug。

### Error 10: raise_ternary_value
- 测试文件: test_adv10_raise_ternary_value.py
- 源码: `if c:\n    raise E1(x) if cond else E2(y)`
- 失败信息: `AssertionError: 指令数不匹配: 16 vs 18`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_NAME', 'PRECALL', 'CALL', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_NAME', 'PRECALL', 'CALL', 'RAISE_VARARGS', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_NAME', 'PRECALL', 'CALL', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_NAME', 'PRECALL', 'CALL', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  if c:
      (E1(x) if cond else E2(y))
  ```
- 根因分析: `raise` 语句的 raised value 为三元表达式 `E1(x) if cond else E2(y)` 时，反编译器将三元作为裸 `Expr` 语句输出，丢失 `raise` 关键字。原始字节码末尾的 `RAISE_VARARGS(1)` 指令被替换为 `POP_TOP`，并多出一条 `RETURN_VALUE`（隐式 return None）。反编译器未识别三元结果应作为 `raise` 的参数，把它当作独立表达式处理。

### Error 11: ternary_method_chain
- 测试文件: test_adv10_ternary_method_chain.py
- 源码: `if c:\n    x = (a if cond else b).method()`
- 失败信息: `AssertionError: 指令数不匹配: 13 vs 10`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_METHOD', 'PRECALL', 'CALL', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  if c:
      x = (a if cond else b)
  ```
- 根因分析: 三元表达式结果上调用方法 `(a if cond else b).method()` 时，反编译器将方法调用整体丢弃，只保留三元作为赋值右值。原始字节码包含 `LOAD_METHOD method, PRECALL, CALL` 三条指令完成方法调用，反编译器未识别这些指令属于三元 merge 之后的链式调用，将它们全部丢弃，导致 `x` 拿到的是三元结果本身而非方法调用结果。

### Error 12: walrus_tuple_unpack
- 测试文件: test_adv10_walrus_tuple_unpack.py
- 源码: `if c:\n    a, b = (d := f())`
- 失败信息: `AssertionError: 指令数不匹配: 15 vs 11`
  - 原始: `['RESUME', 'LOAD_NAME', 'PUSH_NULL', 'LOAD_NAME', 'PRECALL', 'CALL', 'COPY', 'STORE_NAME', 'UNPACK_SEQUENCE', 'STORE_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'PUSH_NULL', 'LOAD_NAME', 'PRECALL', 'CALL', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  if c:
      d = f()
  ```
- 根因分析: tuple unpack `a, b = (d := f())` 中右值为 walrus 表达式时，反编译器只保留 walrus 绑定 `d = f()`，完全丢失 tuple unpack 的 `UNPACK_SEQUENCE` 和两个 `STORE_NAME a, STORE_NAME b` 指令。原始字节码使用 `COPY` 复制栈顶值同时供 walrus 存储（`STORE_NAME d`）和 unpack（`UNPACK_SEQUENCE 2, STORE_NAME a, STORE_NAME b`）使用，反编译器只识别了 walrus 部分，把后续 unpack 序列当作冗余 cleanup 丢弃。

### Error 13: yield_ternary
- 测试文件: test_adv10_yield_ternary.py
- 源码: `def f():\n    if c:\n        yield a if cond else b`
- 失败信息: `AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 14 vs 10`
  - 原始: `['RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'YIELD_VALUE', 'RESUME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  def f():
      if c:
          (a if cond else b)
  ```
- 根因分析: `yield` 语句的值为三元表达式 `yield a if cond else b` 时，反编译器将三元作为裸 `Expr` 语句输出，丢失 `yield` 关键字。原始字节码包含 `YIELD_VALUE` 指令将三元结果作为生成器输出，反编译器将其替换为 `POP_TOP`，同时丢失 `RETURN_GENERATOR` 标记指令，导致函数从生成器退化为普通函数，语义彻底错误。

### Error 14: yieldfrom_ternary
- 测试文件: test_adv10_yieldfrom_ternary.py
- 源码: `def f():\n    if c:\n        yield from (a if cond else b)`
- 失败信息: `AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 17 vs 19`
  - 原始: `['RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'GET_YIELD_FROM_ITER', 'LOAD_CONST', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'POP_TOP', 'LOAD_GLOBAL', 'GET_YIELD_FROM_ITER', 'LOAD_CONST', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- 反编译输出:
  ```
  def f():
      if c:
          (a if cond else b)
          yield from a
  ```
- 根因分析: `yield from (三元)` 语句中，反编译器将三元拆分为两个独立语句：一条裸 `Expr` 三元和一条 `yield from a`（仅使用三元的 then 分支变量 `a`）。原始字节码中 `GET_YIELD_FROM_ITER` 应作用于三元 merge 后的结果，反编译器未将三元与 yield from 关联，反而引入额外的 `LOAD_GLOBAL a` 重新加载 then 分支变量，导致指令数从 17 增至 19 且语义错误（else 分支 `b` 完全丢失）。

## 附：测试统计
- 测试文件总数: 41
- 失败 (FAILED): 14
- 通过 (PASSED): 26
- 跳过 (SKIPPED): 1 (`test_adv10_match_mapping_rest.py` — 反编译输出 `case {'k': v, **v}:` 复用变量名 `v`，重编译时触发 `multiple assignments to name 'v' in pattern` 语法错误，被框架误判为已知限制而跳过；实际为 match mapping pattern `**rest` 的捕获名被错误覆盖为已存在的 `v`，是真实 bug 但不计入失败统计)
- 错误 (ERROR): 0
- 真实错误数: **14** (≥ 10 目标已达成)

## 失败模式归类

### 类别 A: 三元表达式作语句关键字参数被丢失（10 个）
Error 2, 4, 7, 8, 9, 10, 13, 14 — `assert/yield/await/raise/lambda default/f-string value` 等场景下，当三元表达式作为这些语句的关键参数时，反编译器统一退化为裸 `Expr` 语句，丢失语句关键字与 `RAISE_VARARGS`/`YIELD_VALUE`/`FORMAT_VALUE`/`GET_AWAITABLE`/`STORE_NAME` 等关键指令。根因可能是 `_if_generate_then_branch` 中处理 TernaryRegion 时未检查 ternary merge_block 的后续指令是否属于外层语句（assert/raise/yield/await/lambda 等）。

### 类别 B: 赋值/augassign 复杂右值识别失败（2 个）
Error 3 (`x += a and b`)、Error 12 (`a, b = (d := f())`) — augassign 的右值为 BoolOp、tuple unpack 右值为 walrus 时，反编译器未识别 in-place `BINARY_OP` 与 `UNPACK_SEQUENCE` 序列，将其当作冗余 cleanup 丢弃。

### 类别 C: 表达式位置错误（1 个）
Error 5 (`{(x := k): v}`) — walrus 在 dictcomp key 位置被错误移到 value 位置，根因是 dictcomp 生成时 key/value 表达式顺序处理逻辑混乱。

### 类别 D: f-string format spec 处理边界（1 个）
Error 6 (`f"{y:{width}}"`) — format spec 仅由单个嵌套表达式构成（无字面量后缀）时，反编译器将其整体当作字面字符串处理。对比 `f'{x:{width}.2f}'`（有 `.2f` 后缀）能正确反编译，说明 format spec 解析逻辑只覆盖了"表达式 + 字面量"的组合，未覆盖纯表达式 format spec。

### 类别 E: assert 多条件拆分（1 个）
Error 1 (`assert a > 0 and b > 0, "msg"`) — assert 的 test 为 BoolOp 时被错误拆分为多条 assert，根因是 assert 生成逻辑把 BoolOp 的 `JUMP_IF_FALSE_OR_POP` 当作 assert 的 cleanup 边界，未保留 BoolOp 整体性。
