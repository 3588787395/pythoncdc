# Ternary Round 17 测试发现

## 基线
- ternary: 47 failed / 485 passed / 9 skipped
- 验证命令: `timeout 280 python -m pytest tests/exhaustive/ternary/ -q --tb=no`

## 验证后基线（新增 13 个 r17 测试后）
- 60 failed / 485 passed / 9 skipped（+13 失败，与基线差值精确匹配，确认 13 个新测试均为真实失败、无重复）

## 发现的 bug（13 个）

### Bug R17-01: ternary 作为带 args 的中间方法调用的参数（method chain with arg in middle）
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_method_chain_arg_middle.py`
- 源码: `s.replace('a', 'b').split((a if c else b))`
- 失败原因: 字节码指令数不匹配 (16 vs 11)。`_detect_ternary_context` 中 LOAD_METHOD method chain 处理仅识别 0-arg 中间调用 (PRECALL 紧跟 LOAD_METHOD)，带 args 的中间方法 `replace('a','b')` 使 obj chain 重建中断，反编译退化为 `s.replace(a if c else b)`，丢失 `'a','b'` 参数和外层 `.split()` 调用。
- 验证: FAILED `AssertionError: 指令数不匹配: 16 vs 11`
- 共性根因: 「带 args 的中间方法调用」类问题（代码注释明确说明「留待 R14+」未实现）— R17-06 / R17-08 同类。

### Bug R17-02: 同一 STORE_SUBSCR 中 subscr target 与 value 均为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_subscr_target_and_value.py`
- 源码: `x[a if c else b] = (d if e else f)`
- 失败原因: 字节码指令数不匹配 (11 vs 14)。反编译输出退化为多个独立表达式语句 `a; b; d; e; f`（每个 POP_TOP 后接 RETURN_VALUE），完全丢失 STORE_SUBSCR 语句结构，两 ternary 的归约未协调。
- 验证: FAILED `AssertionError: 指令数不匹配: 11 vs 14`

### Bug R17-03: async function return 值为 (ternary) + (await) 复合表达式
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_async_return_with_await.py`
- 源码:
  ```python
  async def f():
      return (a if c else b) + await g()
  ```
- 失败原因: 反编译结果 `async def f():\n    None` — 完全丢失 return 值。ternary merge 块需消费 BINARY_OP 后 RETURN_VALUE，await 表达式在 ternary 之外，反编译器将整个 return 退化为 `return None`。嵌套 code object 指令数严重不匹配 (16 vs 5)。
- 验证: FAILED `AssertionError: 反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`
- 共性根因: 「ternary + await 复合表达式在 async 函数中」类问题 — R17-10 同类。

### Bug R17-04: 函数调用中 *-starred 参数为 ternary 且同时含 keyword 参数
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_starred_kwarg_call.py`
- 源码: `f(*(a if c else b), key=val)`
- 失败原因: 反编译结果 `f(key=val)` — 完全丢失 starred ternary 参数。CALL 指令的 KW_NAMES 与 ternary merge 块的 BUILD_LIST/UNPACK_EX 消费链冲突，指令数不匹配 (13 vs 10)。
- 验证: FAILED `AssertionError: 反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`
- 共性根因: 「starred ternary 在容器/调用上下文中」类问题 — R17-05 / R17-09 同类。

### Bug R17-05: dict literal 含两个 **-unpacking，第二个为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_dict_double_star.py`
- 源码: `x = {**d, **(a if c else b)}`
- 失败原因: 字节码指令数不匹配 (11 vs 9)。R12 dict_merge_double_star 已覆盖单元素 `{**(a if c else b)}`，但双 `**-unpack` 中第二个为 ternary 时，cond_block preload 的 `BUILD_MAP 0` + 第一个 `DICT_UPDATE` + ternary merge 的 `DICT_UPDATE 1` 协调失败，第二个 DICT_UPDATE 被丢失。
- 验证: FAILED `AssertionError: 指令数不匹配: 11 vs 9`

### Bug R17-06: ternary 作为方法调用参数，调用结果再取属性
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_method_arg_then_attr.py`
- 源码: `obj.method(a if c else b).other`
- 失败原因: 字节码指令数不匹配 (12 vs 11)。`_try_build_ternary_merge_consumer_expr` 未处理「CALL 后再 LOAD_ATTR」的后续属性访问，反编译丢失 `.other`。
- 验证: FAILED `AssertionError: 指令数不匹配: 12 vs 11`
- 共性根因: 「ternary 在方法调用参数位置 + 后续链式访问」类问题 — R17-01 同类。

### Bug R17-07: list comprehension 中 body 表达式和 if 条件均为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_listcomp_body_and_if.py`
- 源码: `x = [(a if c else b) for x in y if (d if e else f)]`
- 失败原因: 嵌套 code object（listcomp）内指令数不匹配 (12 vs 10)。R9 listcomp_condition 测过 if 条件为 ternary，R6 listcomp_complex 测过 body 为 ternary，但两者同时存在未覆盖。两个 ternary 嵌套在 comprehension 的 code object 内，merge 块与 FOR_ITER/JUMP_BACKWARD 边界冲突，丢失 if 条件的 ternary。
- 验证: FAILED `AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 12 vs 10`

### Bug R17-08: augmented attribute assignment on ternary method chain result
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_aug_attr_on_method.py`
- 源码: `(a if c else b).method().attr += 1`
- 失败原因: 字节码指令数严重不匹配 (15 vs 10)。R16 attr_aug_assign 已测过 `(a if c else b).attr += 1`，但中间多一层 `.method()` 调用后 `LOAD_ATTR attr + LOAD + BINARY_OP + STORE_ATTR` 消费链未被 `_try_build_ternary_store_assign` 处理，反编译退化为 `(a if c else b).method()`，丢失 `.attr += 1`。
- 验证: FAILED `AssertionError: 指令数不匹配: 15 vs 10`
- 共性根因: 「ternary method chain + augmented assignment」类问题 — R17-12 同类。

### Bug R17-09: tuple literal 中间位置含 *-starred ternary
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_starred_in_tuple.py`
- 源码: `x = (1, *(a if c else b), 2)`
- 失败原因: 字节码指令数不匹配 (13 vs 12)。R2 ternary_in_starred 测过 `*y, = (a if c else b)`（unpack target），R13 starred_assign 测过同模式，但 tuple 中间 `*-starred ternary`（前后均有常量元素）未覆盖。`BUILD_LIST` + `LIST_EXTEND` + `LIST_APPEND` + `LIST_TO_TUPLE` 消费链中，前置 `LOAD_CONST 1` 被丢失。
- 验证: FAILED `AssertionError: 指令数不匹配: 13 vs 12`

### Bug R17-10: ternary 的 condition 表达式是 await
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_await_in_cond.py`
- 源码:
  ```python
  async def f():
      x = a if await g() else b
  ```
- 失败原因: 反编译结果 `async def f():\n    await g()` — 完全丢失 ternary。cond_block 末尾的 POP_JUMP_IF_FALSE 之前需要 `GET_AWAITABLE + SEND` 协程调度，R14 await_with_binop 测过 await 与 ternary body 的组合，但 await 作为 ternary condition 未覆盖。指令数不匹配 (16 vs 14)。
- 验证: FAILED `AssertionError: 反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`

### Bug R17-11: assert 的 test 表达式为 ternary.method()
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_assert_test_method.py`
- 源码: `assert (a if c else b).method()`
- 失败原因: 字节码操作码不匹配 (`LOAD_ASSERTION_ERROR` vs `LOAD_NAME`)。AssertRegion 的 `LOAD_ASSERTION_ERROR` 块与 TernaryRegion 的 merge 块（含 `LOAD_METHOD method + PRECALL + CALL`）协调失败，反编译用 `LOAD_NAME` 替代 `LOAD_ASSERTION_ERROR`，assert 结构被错误还原为 if 语句。
- 验证: FAILED `AssertionError: 指令7操作码不匹配: LOAD_ASSERTION_ERROR vs LOAD_NAME`

### Bug R17-12: augmented subscript assignment 的索引为 (ternary).method()
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_aug_subscr_with_method.py`
- 源码: `x[(a if c else b).method()] += 1`
- 失败原因: 字节码指令数严重不匹配 (18 vs 10)。R12 aug_assign_subscr 测过 `x[a if c else b] += 1`（ternary 直接作索引），R16 subscr_aug_assign 测过类似，但 `(ternary).method()` 作索引未覆盖。ternary merge 块栈顶经 `LOAD_METHOD method + PRECALL + CALL` 后作为 `BINARY_SUBSCR` 索引，再 `LOAD + BINARY_OP + STORE_SUBSCR`，反编译退化为 `(a if c else b).method()`，丢失 `x[...] += 1`。
- 验证: FAILED `AssertionError: 指令数不匹配: 18 vs 10`
- 共性根因: 「ternary method chain + augmented assignment」类问题 — R17-08 同类。

### Bug R17-13: 函数调用 keyword 参数为 lambda，lambda body 为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r17_ternary_lambda_default_in_call.py`
- 源码: `f(g=lambda: a if c else b)`
- 失败原因: 反编译结果 `f(g=(lambda *args, **kwargs: None))` — lambda body 完全退化为 `None`，丢失 ternary。lambda 的 code object 内含 ternary region，CALL 指令的 KW_NAMES 与 `MAKE_FUNCTION/KWARGS` 协调失败。嵌套 code object 指令数不匹配 (5 vs 3)。
- 验证: FAILED `AssertionError: 反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`

## 共性根因归类

1. **「带 args 的中间方法调用」类（3 个）**: R17-01, R17-06, R17-08
   - 触发: ternary 作为方法调用参数 / 方法链中间方法带 args / 方法链后接 augmented assign
   - 根因: `_detect_ternary_context` 的 LOAD_METHOD method chain 处理仅识别 0-arg 中间调用，带 args 时 obj chain 重建中断
   - 代码位置: `core/cfg/region_analyzer.py` ~L11860 `_chain_idx` 循环（注释明确「带 args 的中间方法调用留待 R14+」）

2. **「ternary + await 复合表达式在 async 函数中」类（2 个）**: R17-03, R17-10
   - 触发: ternary 与 await 在同一表达式（return 值或 condition）
   - 根因: async 函数中 `GET_AWAITABLE + SEND` 协程调度与 ternary merge 块的 POP_JUMP_IF_FALSE 边界未协调
   - 影响: 整个 ternary 完全丢失，反编译为 None 或单独的 await

3. **「starred ternary 在容器/调用上下文中」类（3 个）**: R17-04, R17-05, R17-09
   - 触发: `*(ternary)` 在 call args / dict `**` / tuple middle
   - 根因: `BUILD_<container>` + `*_UPDATE/_EXTEND`/`LIST_EXTEND`/`LIST_APPEND` 消费链与 ternary merge 块协调失败，前置/后置元素被丢失
   - 影响: 完全丢失 starred ternary 或部分元素

4. **「augmented assignment + ternary method chain」类（2 个）**: R17-08, R17-12
   - 触发: `(ternary).method().attr/subscr += ...`
   - 根因: `_try_build_ternary_store_assign` 未处理 ternary method chain 后的 `STORE_ATTR/STORE_SUBSCR` augmented assign
   - 影响: 整个 augmented assign 语句退化为方法调用表达式

5. **「嵌套 code object 内多 ternary 协调」类（1 个）**: R17-07
   - 触发: listcomp body 和 if 条件同时为 ternary
   - 根因: comprehension code object 内两个 ternary 的 merge 块与 FOR_ITER/JUMP_BACKWARD 边界冲突

6. **「assert test 表达式为 ternary.method()」类（1 个）**: R17-11
   - 触发: `assert (ternary).method()`
   - 根因: AssertRegion 的 `LOAD_ASSERTION_ERROR` 块与 TernaryRegion merge 块（含 method call）协调失败

7. **「同一语句多 ternary 协调」类（1 个）**: R17-02
   - 触发: `x[ternary] = ternary`
   - 根因: 同一 STORE_SUBSCR 中 subscr target 与 value 均为 ternary，两 ternary 归约未协调，语句结构完全破坏

8. **「lambda body 为 ternary 作为 call kwarg」类（1 个）**: R17-13
   - 触发: `f(g=lambda: ternary)`
   - 根因: lambda code object 内 ternary region 与外层 CALL 的 KW_NAMES/MAKE_FUNCTION 协调失败，lambda body 退化为 None

## 新建测试文件清单（13 个）

1. `/workspace/tests/exhaustive/ternary/test_r17_ternary_method_chain_arg_middle.py`
2. `/workspace/tests/exhaustive/ternary/test_r17_ternary_subscr_target_and_value.py`
3. `/workspace/tests/exhaustive/ternary/test_r17_ternary_async_return_with_await.py`
4. `/workspace/tests/exhaustive/ternary/test_r17_ternary_starred_kwarg_call.py`
5. `/workspace/tests/exhaustive/ternary/test_r17_ternary_dict_double_star.py`
6. `/workspace/tests/exhaustive/ternary/test_r17_ternary_method_arg_then_attr.py`
7. `/workspace/tests/exhaustive/ternary/test_r17_ternary_listcomp_body_and_if.py`
8. `/workspace/tests/exhaustive/ternary/test_r17_ternary_aug_attr_on_method.py`
9. `/workspace/tests/exhaustive/ternary/test_r17_ternary_starred_in_tuple.py`
10. `/workspace/tests/exhaustive/ternary/test_r17_ternary_await_in_cond.py`
11. `/workspace/tests/exhaustive/ternary/test_r17_ternary_assert_test_method.py`
12. `/workspace/tests/exhaustive/ternary/test_r17_ternary_aug_subscr_with_method.py`
13. `/workspace/tests/exhaustive/ternary/test_r17_ternary_lambda_default_in_call.py`

## 验证方法
- 单独运行: `timeout 60 python -m pytest tests/exhaustive/ternary/test_r17_ternary_xxx.py -v --tb=short` — 每个 test_decompile 均 FAILED
- 整体基线: `timeout 280 python -m pytest tests/exhaustive/ternary/ -q --tb=no` — 60 failed / 485 passed / 9 skipped (基线 47 + 新增 13)
- 所有测试均验证字节码完全匹配（非语义等价），使用 `verify_decompilation()` 完整流程（反编译+语法检查+区域类型+字节码等价）

## 重要说明
- 未修改任何源代码（`core/cfg/*.py`）
- 未创建根级 `_debug_*.py` 调试脚本（所有调试在 `/workspace/.trae/specs/iterate-region-test-fix/rounds/ternary_region/round_17/` 下进行，且已清理）
- 测试源码均与现有 r1-r16 测试无重复（已通过 grep 验证）
- 优先关注共性根因类问题，13 个 bug 归为 8 类根因
