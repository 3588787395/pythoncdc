# Round 19 — IF 区域反编译器测试发现

**日期**: 2026-07-20
**测试工程师**: R19 自动探索
**测试范围**: IF 区域内未覆盖模式，聚焦 R1-R18 未触及的 12 个方向：
1. if body 内含 class 定义（带 __init__ 和实例方法）
2. if body 内含 global 声明 + augassign + 后续读取
3. if body 内含 import + 使用导入的名字
4. if 条件含 lambda 立即调用 (IIFE) + boolop + elif 链
5. if-elif-else 条件含 4 项 not 链 + 4 项 and 链
6. if body 内含 with 多上下文 + as 绑定 + 嵌套 with
7. if body 内含 @decorator + 嵌套 def + 调用
8. elif body 内含 match-case（R18 只测 if body 内 match）
9. if body 内含完整 try-except-else-finally 四子句
10. if-elif 条件含 dict unpacking `{**d, 'a': 1}` + 长度比较
11. elif body 内含 while-else + break
12. if-elif-else 三分支各自含不同复杂语句（for/try/with）
13. if-elif 条件含 `in` set literal / frozenset
14. if-elif 条件含 *args / **kwargs 函数调用
15. if-elif-else 三分支都含多目标 del + 属性 + subscr
16. if-elif-else 条件含 3 项 in 检查链 + not in + elif 链
17. async 函数 if body 内含 async with + async for + 嵌套 if
18. if-elif-else 三分支各自返回不同类型 comprehension
19. if-elif 条件含 walrus + in list + elif 链
20. elif body 内含 class 定义 + 继承 + super 调用
21. 外层函数 + if body 内含 nonlocal + nested def + closure
22. elif body 内含 yield + 嵌套 if-else（生成器）
23. async 函数 if-elif-else 条件含 await + boolop + not
24. if-elif-else 条件含 `is` / `is not` 链 + None 检查
25. if-elif-else 三分支各自含 for + continue/break
26. if 条件含多 walrus + boolop 链 (4+ operands)
27. if-elif-else body 内含 assert + chained comparison + f-string msg
28. if body 内含 try-except-else 三子句 + 后续 if-elif
29. if-elif-else body 内含 tuple unpacking + starred + 嵌套 if
30. if-elif 条件含 f-string format spec + 多种 conversion
31. if-elif-else 三分支各自嵌套 if-elif-else
32. if body 内含多行 dict 字面量 + 嵌套 ternary + 后续 if

---

## 统计摘要

| 指标 | 数量 |
|------|------|
| 测试文件总数 | 32 |
| 失败（FAILED） | 12 |
| 通过（PASSED） | 18 |
| 跳过（SKIPPED） | 2 |
| **新错误总数（去重子 bug）** | **36** |

运行命令:
```
cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv19_*.py --tb=short -q
```

结果: `12 failed, 18 passed, 2 skipped in 3.22s`

### IF 区域全量回归

```
37 failed, 758 passed, 9 skipped in 7.39s
```

- 基线（R18 修复后）：25 failed, 740 passed, 7 skipped
- R19 新增：12 failed（R19 新发现）+ 18 passed（R19 新增通过）+ 2 skipped（R19 新增）
- 无退化：25 + 12 = 37 failed（完全一致），740 + 18 = 758 passed，7 + 2 = 9 skipped

---

## 测试文件列表

| # | 文件 | 状态 | 错误类别 |
|---|------|------|----------|
| 1 | `test_adv19_assert_chained_cmp_in_if_body.py` | **FAILED** | if-elif-else 三分支都含 assert + chained cmp + f-string → 整体退化为单 ternary，丢失 assert 与 return |
| 2 | `test_adv19_async_with_async_for_in_if_body.py` | SKIPPED | async 函数 if body 内 async with + async for + 嵌套 if → `await process(item)` 丢失为 pass，`return 'done'` 丢失，泄漏 `break` 出循环（语法错误） |
| 3 | `test_adv19_await_in_if_cond.py` | **FAILED** | async if-elif-else 条件含 `await a > 0 and await b < 100` → 整体退化为 `if (0 and 100):` 丢失所有 await 和比较 |
| 4 | `test_adv19_chained_in_check_in_if_cond.py` | PASSED | — （3 项 in 链 + not in + elif 链） |
| 5 | `test_adv19_class_def_with_method_in_if_body.py` | PASSED | — （if body 内 class + __init__ + method） |
| 6 | `test_adv19_comprehension_return_in_branches.py` | PASSED | — （if-elif-else 三分支各返回 listcomp/setcomp/dictcomp/genexp） |
| 7 | `test_adv19_del_multi_in_if_body.py` | PASSED | — （if-elif-else 三分支都含多目标 del） |
| 8 | `test_adv19_dict_unpack_in_if_cond.py` | PASSED | — （if-elif 条件含 `{**d, 'a': 1}` + len 比较） |
| 9 | `test_adv19_for_continue_in_each_branch.py` | **FAILED** | if-elif-else 三分支各自含 for + continue/break → 整体退化为 ternary `(items if mode == 'a' else items if mode == 'b' else items)`，3 个 for 全部逃出分支 |
| 10 | `test_adv19_fstring_format_value_in_if_cond.py` | PASSED | — （if-elif 条件含 f-string format spec + 多 conversion） |
| 11 | `test_adv19_global_decl_with_augassign_in_if_body.py` | PASSED | — （if body 内 global + augassign + 读取） |
| 12 | `test_adv19_import_in_if_body.py` | PASSED | — （if body 内 import + from import + 使用） |
| 13 | `test_adv19_in_set_literal_in_if_cond.py` | PASSED | — （if-elif 条件含 in set literal / frozenset） |
| 14 | `test_adv19_is_isnot_chain_in_if_cond.py` | **FAILED** | elif `a is not None or b is not None` → `elif not (a is not None or b is not None)` 语义反转（De Morgan 错误） |
| 15 | `test_adv19_lambda_iife_in_if_cond.py` | **FAILED** | if-elif 条件含 `(lambda x: x > 0)(y)` → lambda 体被替换为 `lambda *args, **kwargs: None`，丢失比较逻辑 |
| 16 | `test_adv19_match_in_elif_body.py` | PASSED | — （elif body 内 match-case + 多 case） |
| 17 | `test_adv19_mixed_complex_branches.py` | **FAILED** | if-elif-else 三分支各自含 for/try/with → 整体退化为 ternary `(items if x > 0 else x < 0)`，3 个 body 全部逃出，泄漏 `None(None, None)` 字面量 |
| 18 | `test_adv19_multi_not_chain_in_if_cond.py` | PASSED | — （if-elif-else 条件含 4 项 not 链 + 4 项 and 链） |
| 19 | `test_adv19_multiline_return_in_if_body.py` | **FAILED** | if body 内多行 dict + 嵌套 ternary + 后续 if → 内层 `if result['doubled'] > 100:` 退化为表达式语句 `(result['doubled'] > 100)`，丢失 if body |
| 20 | `test_adv19_nested_class_in_elif_body.py` | SKIPPED | elif body 内 class + 继承 + super → 类体内泄漏 `return (__classcell__ := __class__)`（return 出函数语法错误） |
| 21 | `test_adv19_nested_func_decorator_in_if_body.py` | PASSED | — （if body 内 @deco + 嵌套 def + 调用） |
| 22 | `test_adv19_nested_if_elif_in_each_branch.py` | **FAILED** | if-elif-else 三分支各自嵌套 if-elif-else → 整体退化为 6 个裸 return 语句，全部 if 结构丢失 |
| 23 | `test_adv19_nonlocal_with_nested_func_in_if_body.py` | PASSED | — （外层函数 + if body 内 nonlocal + nested def + closure） |
| 24 | `test_adv19_starred_call_in_if_cond.py` | PASSED | — （if-elif 条件含 *args / **kwargs 函数调用） |
| 25 | `test_adv19_try_except_else_finally_in_if_body.py` | PASSED | — （if body 内完整 try-except-else-finally 四子句） |
| 26 | `test_adv19_try_except_else_in_if_body.py` | **FAILED** | if body 内 try-except-else + 后续 if-elif → 函数末尾 `return 'none'` 错挂到内层 if-elif 的 else 分支 |
| 27 | `test_adv19_tuple_unpack_in_if_body.py` | **FAILED** | if-elif-else 三分支含 tuple unpacking + starred → else 分支 `return a, b` 完全丢失 |
| 28 | `test_adv19_walrus_complex_boolop_in_if_cond.py` | PASSED | — （if-elif 条件含多 walrus + boolop 链） |
| 29 | `test_adv19_walrus_in_in_if_cond.py` | PASSED | — （if-elif 条件含 walrus + in list） |
| 30 | `test_adv19_while_else_break_in_elif_body.py` | **FAILED** | elif body 内 while-else + break → `else: return 'no_stop'` 错挂为 while 后的顺序语句，`return items[i]` 丢失 |
| 31 | `test_adv19_with_multi_ctx_in_if_body.py` | **FAILED** | if body 内 with 多上下文 + 嵌套 with → 3 个 with 错合并为单 with，`fa.read()` 丢失，泄漏 `None(None, None)` 字面量 |
| 32 | `test_adv19_yield_in_elif_body.py` | PASSED | — （elif body 内 yield + 嵌套 if-else） |

---

## 详细发现

### Bug 1-3: if-elif-else 三分支都含 assert + chained cmp + f-string → 整体退化为单 ternary

**文件**: `test_adv19_assert_chained_cmp_in_if_body.py`
**状态**: FAILED（IF_REGION 区域类型未找到）

**源码**:
```python
def f(x):
    if x > 0:
        assert 0 < x < 100, f'x out of range: {x}'
        return 'pos_valid'
    elif x < 0:
        assert -100 < x < 0, f'x too negative: {x}'
        return 'neg_valid'
    else:
        assert x == 0
        return 'zero'
```

**反编译结果**:
```python
def f(x):
    (0 < x if x > 0 else -100 < x if x < 0 else x == 0)
```

**问题分解（3 个子 bug）**:

#### Bug 1: if-elif-else 三分支整体退化为单 ternary 表达式

原始 if-elif-else 三分支都被吞并，反编译产出只剩 `(0 < x if x > 0 else -100 < x if x < 0 else x == 0)`
一个嵌套 ternary 表达式语句。三个分支的 assert + chained comparison 被错合并为
ternary 的条件表达式（assert 0 < x < 100 → 0 < x；assert -100 < x < 0 → -100 < x；
assert x == 0 → x == 0）。

#### Bug 2: 所有 assert 语句完全丢失

原始字节码中三个 `assert 0 < x < 100, f'...'` 等语句（包含 ASSERT_RAISE、
FORMAT_VALUE、BUILD_STRING）在反编译产出中完全消失。assert 的 AssertRegion
识别被 if 区域归约干扰。

#### Bug 3: 所有 return 语句完全丢失

原始 `return 'pos_valid'` / `return 'neg_valid'` / `return 'zero'` 三个 return
语句在反编译产出中全部消失，函数没有任何 return 路径。

**根因推测**: 反编译器在 if-elif-else 三分支都含 assert + chained cmp + f-string
msg 时，对 assert 的 AssertRegion 识别被 IfRegion 归约干扰，把每个 assert 的
chained comparison 条件错合并为 ternary 表达式，整体结构完全丢失。需要在
if-elif-else body 内含 assert + chained cmp 时保持 IfRegion 结构，禁止退化为 ternary。

---

### Bug 4-6: async if-elif-else 条件含 await + boolop → 丢失所有 await 和比较

**文件**: `test_adv19_await_in_if_cond.py`
**状态**: FAILED（嵌套 code object 不匹配: 49 vs 5）

**源码**:
```python
async def f(a, b):
    if await a > 0 and await b < 100:
        return 'valid'
    elif await a == 0 or await b == 0:
        return 'zero'
    elif not await a:
        return 'falsy'
    else:
        return 'other'
```

**反编译结果**:
```python
async def f(a, b):
    if (0 and 100):
        return 'valid'
```

**问题分解（3 个子 bug）**:

#### Bug 4: `await a > 0 and await b < 100` 退化为 `0 and 100`

原始字节码 offset 2-8 处 `LOAD_FAST a / GET_AWAITABLE / LOAD_CONST None / YIELD_VALUE
/ JUMP_BACKWARD_NO_INTERRUPT / LOAD_CONST 0 / COMPARE_OP >`（即 `await a > 0`）
在反编译产出中退化为 `LOAD_CONST 0`（即常量 0）。await 表达式和比较运算完全丢失，
只剩比较的右操作数常量。

#### Bug 5: elif 链 + else 完全丢失

原始 4 个分支（if + 3 个 elif/else）在反编译产出中只剩 1 个 if，其余 3 个分支
（`elif await a == 0 or await b == 0:` / `elif not await a:` / `else:`）全部消失。

#### Bug 6: 字节码指令数严重缩水（49 → 5）

原始嵌套 code object 有 49 条 filtered 指令，重编只有 5 条。缺失 44 条指令，
主要因为所有 await + 比较运算的字节码都被吞并。

**字节码对比**（filtered）:
- 原始 49 条 / 重编 5 条
- 原始 2-8: `LOAD_FAST a / GET_AWAITABLE / LOAD_CONST None / YIELD_VALUE / JUMP_BACKWARD_NO_INTERRUPT / LOAD_CONST 0 / COMPARE_OP >`（await a > 0）
- 重编完全缺失以上 7 条
- 原始 9-15: `LOAD_FAST b / GET_AWAITABLE / LOAD_CONST None / YIELD_VALUE / JUMP_BACKWARD_NO_INTERRUPT / LOAD_CONST 100 / COMPARE_OP <`（await b < 100）
- 重编完全缺失以上 7 条

**根因推测**: 反编译器在 async 函数 if-elif-else 条件含 await + boolop 时，
GET_AWAITABLE + YIELD_VALUE 字节码模式（async 函数特有的 await 实现）干扰了
IfRegion 条件表达式的重建，把每个 await 表达式替换为常量 0/100，丢失全部 await
和比较运算。需要在 async 函数 IfRegion 条件中正确重建 await 表达式。

---

### Bug 7-9: if-elif-else 三分支各自含 for + continue/break → 3 个 for 逃出分支

**文件**: `test_adv19_for_continue_in_each_branch.py`
**状态**: FAILED（嵌套 code object 不匹配: 44 vs 24）

**源码**:
```python
def f(items, mode):
    if mode == 'a':
        for x in items:
            if x < 0:
                continue
            process_a(x)
        return 'a_done'
    elif mode == 'b':
        for x in items:
            if x > 100:
                break
            process_b(x)
        return 'b_done'
    else:
        for x in items:
            process_c(x)
        return 'c_done'
```

**反编译结果**:
```python
def f(items, mode):
    (items if mode == 'a' else items if mode == 'b' else items)
    for x in items:
        if (x < 0):
            continue
        else:
            process_a(x)
    else:
        return 'a_done'
    for x in items:
        if (x > 100):
            break
        else:
            process_b(x)
    for x in items:
        process_c(x)
    else:
        return 'c_done'
```

**问题分解（3 个子 bug）**:

#### Bug 7: if-elif-else 整体退化为 ternary `(items if mode == 'a' else items if mode == 'b' else items)`

三个分支的 for 循环 iter 对象（都是 items）被错合并为 ternary 表达式的值，
三个分支的 if/elif 条件被错合并为 ternary 的条件。整体 if-elif-else 结构完全丢失。

#### Bug 8: 3 个 for 循环全部逃出 if-elif-else 到函数顶层

原始字节码中三个 for 循环应分别在 if/elif/else body 内，
反编译产出把它们全部平铺到函数体顶层（与 if 同级）。

#### Bug 9: 内层 `if x < 0: continue` 退化为 `if-else`，外层 for 多余 else 子句

原始 `if x < 0: continue / process_a(x)` 是顺序结构（if 条件不满足时执行 process_a），
反编译产出变为 `if (x < 0): continue / else: process_a(x)`，多余 else 子句。
同时第一个 for 错添加 `else: return 'a_done'`，第二个 for 缺少 else 子句
（原始 b 分支没有 for-else，反编译产出缺失 b 分支的 `return 'b_done'`）。

**字节码对比**（filtered）:
- 原始 44 条 / 重编 24 条
- 原始 4-13: `LOAD_FAST items / GET_ITER / STORE_FAST x / LOAD_FAST x / LOAD_CONST 0 / COMPARE_OP < / LOAD_GLOBAL process_a / LOAD_FAST x / PRECALL / CALL / POP_TOP / LOAD_CONST None / RETURN_VALUE`
- 重编缺失以上多条指令

**根因推测**: 反编译器在 if-elif-else 三分支都含 for 循环 + flow control
（continue/break）时，对 for 循环的归约逻辑干扰了 IfRegion 识别，把三个 for
循环的 iter 对象错合并为 ternary 表达式，三个 for 循环本身逃出 if-elif-else 到
函数顶层。需要在 if-elif-else body 内含 for 循环时保持 IfRegion 结构。

---

### Bug 10-12: elif `a is not None or b is not None` → `not(...)` 语义反转

**文件**: `test_adv19_is_isnot_chain_in_if_cond.py`
**状态**: FAILED（指令10参数不匹配: 26 vs 30，op=POP_JUMP_FORWARD_IF_NOT_NONE）

**源码**:
```python
def f(a, b, c):
    if a is None and b is None and c is None:
        return 'all_none'
    elif a is not None or b is not None:
        return 'some_not_none'
    elif c is None:
        return 'c_none'
    else:
        return 'none'
```

**反编译结果**:
```python
def f(a, b, c):
    if (a is None and b is None and c is None):
        return 'all_none'
    elif (not (a is not None or b is not None)):
        return 'some_not_none'
    elif (c is None):
        return 'c_none'
    else:
        return 'none'
```

**问题分解（3 个子 bug）**:

#### Bug 10: elif 条件 `a is not None or b is not None` 错误包裹 `not(...)` 语义反转

原始 `elif a is not None or b is not None: return 'some_not_none'` 的语义：
当 a 不为 None 或 b 不为 None 时返回 'some_not_none'。
反编译产出 `elif not (a is not None or b is not None):` 的语义：
当 a 为 None 且 b 为 None 时返回 'some_not_none'。
两个语义完全相反（De Morgan 错误）！

#### Bug 11: 字节码跳转目标错乱

原始字节码 offset 9 处 `POP_JUMP_FORWARD_IF_NOT_NONE 26`（a is not None 时跳到
elif body），反编译产出 offset 9 处 `POP_JUMP_FORWARD_IF_NOT_NONE 30`
（a is not None 时跳到下一 elif，跳过 body）。跳转目标从 26 变为 30。

#### Bug 12: 第二个跳转指令操作码反转

原始字节码 offset 11 处 `POP_JUMP_FORWARD_IF_NONE 30`（b is None 时跳到下一 elif），
反编译产出 offset 11 处 `POP_JUMP_FORWARD_IF_NOT_NONE 30`（b is not None 时跳到
下一 elif）。跳转指令操作码从 IF_NONE 反转为 IF_NOT_NONE，b 的判断条件也反转。

**字节码对比**（filtered）:
- 原始 20 条 / 重编 20 条（指令数相同）
- 原始 9: `POP_JUMP_FORWARD_IF_NOT_NONE 26`（a is not None → 跳到 body）
- 重编 9: `POP_JUMP_FORWARD_IF_NOT_NONE 30`（a is not None → 跳过 body 到下一 elif）
- 原始 11: `POP_JUMP_FORWARD_IF_NONE 30`（b is None → 跳到下一 elif）
- 重编 11: `POP_JUMP_FORWARD_IF_NOT_NONE 30`（b is not None → 跳到下一 elif，操作码反转）

**根因推测**: 反编译器在 elif 条件含 `a is not None or b is not None` 时，
对 IS_OP + boolop 链的归约逻辑有 bug：把原始条件 `X or Y` 错误包裹为 `not (X or Y)`，
导致语义反转。这是 **语义正确性 bug**（非结构 bug），反编译产出可编译但语义错误，
运行结果与原始不同。需要修正 elif 条件含 `is not None or is not None` 的归约逻辑，
不应包裹 not(...)。

---

### Bug 13-15: if-elif 条件含 lambda IIFE → lambda 体被替换为 None

**文件**: `test_adv19_lambda_iife_in_if_cond.py`
**状态**: FAILED（嵌套 code object 不匹配: 5 vs 3，lambda 体指令数不匹配）

**源码**:
```python
def f(y):
    if (lambda x: x > 0)(y) and (lambda x: x < 100)(y):
        return 'valid'
    elif (lambda x: x == 0)(y):
        return 'zero'
    else:
        return 'invalid'
```

**反编译结果**:
```python
def f(y):
    if ((lambda *args, **kwargs: None)(y) and (lambda *args, **kwargs: None)(y)):
        return 'valid'
    elif (lambda *args, **kwargs: None)(y):
        return 'zero'
    return 'invalid'
```

**问题分解（3 个子 bug）**:

#### Bug 13: lambda 参数 `x` 被替换为 `*args, **kwargs`

原始三个 lambda 都是 `lambda x: ...`（单参数 x），
反编译产出三个 lambda 全部变为 `lambda *args, **kwargs: ...`（变长参数）。
lambda 的参数签名完全错误。

#### Bug 14: lambda 体 `x > 0` / `x < 100` / `x == 0` 被替换为 `None`

原始 lambda 体分别是 `x > 0`、`x < 100`、`x == 0`（含 LOAD_FAST + LOAD_CONST +
COMPARE_OP + RETURN_VALUE，共 5 条指令），反编译产出 lambda 体全部变为 `None`
（LOAD_CONST None + RETURN_VALUE，3 条指令）。lambda 体的比较逻辑完全丢失。

#### Bug 15: else 分支被错挂为顶层 return

原始 `else: return 'invalid'` 是 if-elif-else 的 else 分支，
反编译产出 `return 'invalid'` 错挂到函数顶层（与 if 同级），脱离 else 分支结构。

**字节码对比**（filtered）:
- 原始 f 字节码 24 条 / 重编 24 条（顶层指令数相同）
- 原始 lambda 体（嵌套 code object）5 条 / 重编 lambda 体 3 条
  - 原始: `LOAD_FAST x / LOAD_CONST 0 / COMPARE_OP > / RETURN_VALUE`
  - 重编: `LOAD_CONST None / RETURN_VALUE`（缺失 LOAD_FAST 和 COMPARE_OP）

**根因推测**: 反编译器在 if-elif 条件含 lambda IIFE `(lambda x: ...)(y)` 时，
对 lambda 的嵌套 code object 处理有 bug：把 lambda 的参数签名 `x` 替换为
`*args, **kwargs`，把 lambda 体 `x > 0` 替换为 `None`。可能是 lambda 的
MAKE_FUNCTION + LOAD_CONST <code> 模式被错误归约，把 lambda 体视为默认返回 None。
需要修正 lambda IIFE 在 IfRegion 条件中的归约，保留 lambda 的参数和体。

---

### Bug 16-18: if-elif-else 三分支各自含 for/try/with → 整体退化为 ternary + `None(None, None)` 泄漏

**文件**: `test_adv19_mixed_complex_branches.py`
**状态**: FAILED（嵌套 code object 不匹配: 79 vs 87）

**源码**:
```python
def f(x, items):
    if x > 0:
        for item in items:
            if item == x:
                break
        return 'found_pos'
    elif x < 0:
        try:
            raise ValueError('neg')
        except ValueError as e:
            return str(e)
    else:
        with open('log') as f:
            if f.read():
                return 'has_log'
        return 'no_log'
```

**反编译结果**:
```python
def f(x, items):
    (items if x > 0 else x < 0)
    for item in items:
        if (item == x):
            break
    try:
        raise ValueError('neg')
    except ValueError as e: str(e)
    with open('log') as f:
        if f.read():
            None(None, None)
            return 'has_log'
```

**问题分解（3 个子 bug）**:

#### Bug 16: if-elif-else 整体退化为 ternary `(items if x > 0 else x < 0)`

三个分支的入口条件被错合并为 ternary 表达式：
- if 分支的 `for item in items:` 的 iter 对象 `items` 成为 ternary 的 true value
- elif 分支的条件 `x < 0` 成为 ternary 的 false value
- else 分支完全消失

#### Bug 17: 三个分支的 body 全部逃出 if-elif-else 到函数顶层

原始字节码中三个 body（for / try / with）应分别在 if/elif/else body 内，
反编译产出把它们全部平铺到函数体顶层（与 if 同级），完全脱离分支结构。
同时丢失了 if 分支的 `return 'found_pos'` 和 else 分支的 `return 'no_log'`。

#### Bug 18: `None(None, None)` AST 字典泄漏到反编译产出

反编译产出在内层 if body 中出现 `None(None, None)` 字面量，
这是反编译器把 AST 节点 dict 当作函数调用生成的明显 bug。
明显是 CodeGenerator 在某种边界条件下未正确转换 AST 节点到源码。

**字节码对比**（filtered）:
- 原始 79 条 / 重编 87 条（重编多 8 条）
- 重编 6-7: `LOAD_FAST items / LOAD_FAST items`（多余，ternary 错合并的副作用）
- 原始 4-13: `LOAD_FAST items / GET_ITER / STORE_FAST item / LOAD_FAST item / LOAD_FAST x / COMPARE_OP == / POP_TOP / LOAD_CONST found_pos / RETURN_VALUE`
- 重编缺失 `LOAD_CONST found_pos / RETURN_VALUE` 两条指令

**根因推测**: 反编译器在 if-elif-else 三分支各自含不同复杂语句（for + try + with）
时，归约逻辑严重错乱：把三分支入口错合并为 ternary，body 全部逃出 if-elif-else。
更严重的是泄漏 `None(None, None)` 这种 AST dict 字面量到反编译产出，
说明 CodeGenerator 在某边界条件下未正确转换 AST 节点。
需要在 if-elif-else body 含混合复杂语句时保持 IfRegion 结构，
并修正 CodeGenerator 的 AST dict 泄漏 bug。

---

### Bug 19-21: if body 内多行 dict + 嵌套 ternary + 后续 if → 内层 if 退化为表达式

**文件**: `test_adv19_multiline_return_in_if_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 33 vs 32）

**源码**:
```python
def f(x):
    if x > 0:
        result = {
            'value': x,
            'category': 'pos' if x < 10 else 'big',
            'doubled': x * 2,
        }
        if result['doubled'] > 100:
            return {**result, 'overflow': True}
        return result
    return None
```

**反编译结果**:
```python
def f(x):
    if (x > 0):
        result = {'value': x, 'category': 'pos' if x < 10 else 'big', 'doubled': x * 2}
        (result['doubled'] > 100)
        return {**result, 'overflow': True}
    return None
```

**问题分解（3 个子 bug）**:

#### Bug 19: 内层 `if result['doubled'] > 100:` 退化为表达式语句 `(result['doubled'] > 100)`

原始 `if result['doubled'] > 100: return {...}` 是条件分支，
反编译产出变为 `(result['doubled'] > 100)` 表达式语句（无 if body），
内层 if 的条件检查结果被丢弃，不进入 if body。

#### Bug 20: 内层 if body 的 `return {**result, 'overflow': True}` 错挂到外层 if body

原始 `return {**result, 'overflow': True}` 应在内层 if body 内（仅当
result['doubled'] > 100 时执行），反编译产出把它错挂到外层 if body（无条件执行），
丢失了条件分支语义。

#### Bug 21: 外层 if body 末尾的 `return result` 完全丢失

原始 `return result` 是外层 if body 的末尾语句（当 result['doubled'] <= 100 时执行），
反编译产出完全消失。函数在 x > 0 时永远返回 `{**result, 'overflow': True}`，
不再有条件分支返回路径。

**字节码对比**（filtered）:
- 原始 33 条 / 重编 32 条（仅差 1 条）
- 重编缺失原始末尾的 `LOAD_FAST result / RETURN_VALUE` 两条指令
- 重编多余的 `POP_TOP`（来自 `(result['doubled'] > 100)` 表达式语句）

**根因推测**: 反编译器在 if body 内含多行 dict 字面量 + 嵌套 ternary + 后续 if 时，
把后续 if 的条件检查退化为表达式语句（添加 `POP_TOP`），把 if body 错挂到外层 if，
并丢失外层 if 末尾的 return。需要保留 if body 内嵌套 if 的条件检查结构。

---

### Bug 22-24: if-elif-else 三分支各自嵌套 if-elif-else → 整体退化为 6 个裸 return

**文件**: `test_adv19_nested_if_elif_in_each_branch.py`
**状态**: FAILED（IF_REGION 区域类型未找到）

**源码**:
```python
def f(x, y):
    if x > 0:
        if y > 0:
            return 'pos_pos'
        elif y < 0:
            return 'pos_neg'
        else:
            return 'pos_zero'
    elif x < 0:
        if y > 0:
            return 'neg_pos'
        elif y < 0:
            return 'neg_neg'
        else:
            return 'neg_zero'
    else:
        if y > 0:
            return 'zero_pos'
        elif y < 0:
            return 'zero_neg'
        else:
            return 'zero_zero'
```

**反编译结果**:
```python
def f(x, y):
    return 'pos_neg'
    return 'pos_zero'
    return 'neg_neg'
    return 'neg_zero'
    return 'zero_neg'
    return 'zero_zero'
```

**问题分解（3 个子 bug）**:

#### Bug 22: 整体 9 分支 if-elif-else 结构完全丢失

原始 1 个外层 if + 3 个内层 if-elif-else（共 9 个分支）在反编译产出中全部消失，
没有任何 ast.If 节点。反编译产出只剩 6 个裸 return 语句。

#### Bug 23: 6 个 return 语句错合并为顶层裸 return

原始 9 个分支各自的 return 语句（如 `return 'pos_pos'`）应分别在内层 if-elif-else
的 body 内，反编译产出把其中 6 个 return 错合并为顶层裸 return 语句，
顺序执行（无分支）。这完全改变了函数语义（原本应基于 x 和 y 的值返回不同结果，
反编译产出总是返回第一个 return 'pos_neg'，其余 5 个 return 是死代码）。

#### Bug 24: 字节码指令数严重缩水（42 → 2）

原始嵌套 code object（函数 f）有 42 条 filtered 指令，重编只有 2 条
（`LOAD_CONST pos_neg / RETURN_VALUE`）。缺失 40 条指令，所有 if-elif-else
结构和大部分 return 都丢失。

**字节码对比**（filtered）:
- 原始 42 条 / 重编 2 条
- 原始 0-2: `LOAD_FAST x / LOAD_CONST 0 / COMPARE_OP >`（外层 if x > 0）
- 重编完全缺失以上 3 条
- 原始 3-7: `LOAD_FAST y / LOAD_CONST 0 / COMPARE_OP > / LOAD_CONST pos_pos / RETURN_VALUE`（内层 if y > 0）
- 重编完全缺失以上 5 条

**根因推测**: 反编译器在 if-elif-else 三分支各自嵌套 if-elif-else 时，
归约逻辑严重错乱：把 9 个分支的 return 语句错合并为顶层裸 return，
完全丢失 if-elif-else 结构。可能是嵌套 IfRegion 的归约顺序错误，
外层 IfRegion 先归约时把内层 IfRegion 的 return 当作"分支终止"提取出来。
需要修正嵌套 IfRegion 的归约顺序，保留嵌套 if-elif-else 结构。

---

### Bug 25-27: if body 内 try-except-else + 后续 if-elif → `return 'none'` 错挂到内层 else

**文件**: `test_adv19_try_except_else_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 38 vs 40）

**源码**:
```python
def f(x):
    if x > 0:
        result = None
        try:
            r = process(x)
        except ValueError:
            r = -1
        else:
            r = r + 1
        if r > 100:
            return 'big'
        elif r > 0:
            return 'small'
    return 'none'
```

**反编译结果**:
```python
def f(x):
    if (x > 0):
        result = None
        try:
            r = process(x)
        except ValueError: r = -1
        else: r = (r + 1)
        if (r > 100):
            return 'big'
        elif (r > 0):
            return 'small'
        return 'none'
```

**问题分解（3 个子 bug）**:

#### Bug 25: 函数末尾 `return 'none'` 错挂到内层 if-elif 的 else 分支

原始 `return 'none'` 是函数末尾的 fallthrough 语句（当 x <= 0 时执行），
反编译产出把它错挂到内层 `if r > 100: ... elif r > 0: ...` 的 else 分支
（即当 r <= 0 时执行）。语义改变：原始当 x <= 0 时返回 'none'，
反编译产出当 x > 0 且 r <= 0 时返回 'none'。

#### Bug 26: 字节码指令数膨胀（38 → 40）

重编字节码比原始多 2 条，主要因为：
- 外层 if 错添加 else 子句（`return 'none'` 被错挂）
- 多余的 `LOAD_CONST None / RETURN_VALUE`（隐式返回）

#### Bug 27: 内层 try-except-else 的 else 子句缩排错乱

原始 `else: r = r + 1` 是 try-except-else 的 else 子句（多行），
反编译产出 `else: r = (r + 1)` 把 else 子句压缩到单行（虽然语法上正确，
但风格不一致，可能是归约过程中的副作用）。

**字节码对比**（filtered）:
- 原始 38 条 / 重编 40 条
- 重编末尾多余的 `LOAD_CONST none / RETURN_VALUE`（错挂的 return 'none'）

**根因推测**: 反编译器在 if body 内含 try-except-else + 后续 if-elif 时，
对函数末尾的 fallthrough return 错误识别为内层 if-elif 的 else 分支。
需要在归约内层 IfRegion 时正确区分函数 fallthrough 和 else 分支。

---

### Bug 28-30: if-elif-else body 内 tuple unpacking + starred → else 分支 return 丢失

**文件**: `test_adv19_tuple_unpack_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 42 vs 40）

**源码**:
```python
def f(items, mode):
    if mode == 'a':
        a, b, *c = items
        if a > b:
            return c
        return a + b
    elif mode == 'b':
        (a, b), c = items
        return a + b + c
    else:
        *a, b = items
        return a, b
```

**反编译结果**:
```python
def f(items, mode):
    if (mode == 'a'):
        (a, b, *c) = items
        if (a > b):
            return c
        else:
            return (a + b)
    elif (mode == 'b'):
        ((a, b), c) = items
        return (a + b + c)
    else:
        (*a, b) = items
```

**问题分解（3 个子 bug）**:

#### Bug 28: else 分支的 `return a, b` 完全丢失

原始 else 分支 `*a, b = items / return a, b` 在反编译产出中只剩 `(*a, b) = items`，
`return a, b` 语句完全消失。else 分支没有 return 路径，函数在该分支隐式返回 None。

#### Bug 29: if 分支的顺序语句错添加 else 子句

原始 `if a > b: return c / return a + b` 是顺序结构（if 不满足时执行 return a+b），
反编译产出变为 `if (a > b): return c / else: return (a + b)`，多余 else 子句。

#### Bug 30: 字节码指令数缩水（42 → 40）

重编字节码比原始少 2 条，主要因为 else 分支的 `BUILD_TUPLE 2 / RETURN_VALUE`
（即 `return a, b`）完全丢失。

**字节码对比**（filtered）:
- 原始 42 条 / 重编 40 条
- 原始末尾: `LOAD_FAST a / LOAD_FAST b / BUILD_TUPLE 2 / RETURN_VALUE`（return a, b）
- 重编完全缺失以上 4 条

**根因推测**: 反编译器在 if-elif-else body 内含 tuple unpacking + starred 时，
else 分支的 return 语句丢失。可能是 UNPACK_EX + STORE_FAST 链的归约过程中
误把后续 return 视为"已被吞并"而丢弃。需要保留 if-elif-else body 内 tuple
unpacking 之后的 return 语句。

---

### Bug 31-33: elif body 内 while-else + break → `else: return 'no_stop'` 错挂为顺序语句

**文件**: `test_adv19_while_else_break_in_elif_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 40 vs 36）

**源码**:
```python
def f(items, mode):
    if mode == 'a':
        return 'a_mode'
    elif mode == 'b':
        i = 0
        while i < len(items):
            if items[i] == 'stop':
                break
            i += 1
        else:
            return 'no_stop'
        return items[i]
    else:
        return 'unknown'
```

**反编译结果**:
```python
def f(items, mode):
    if (mode == 'a'):
        return 'a_mode'
    elif (mode == 'b'):
        i = 0
        while i < len(items):
            if (items[i] == 'stop'):
                break
            i += 1
        return 'no_stop'
    return 'unknown'
```

**问题分解（3 个子 bug）**:

#### Bug 31: `else: return 'no_stop'` 错挂为 while 后的顺序语句

原始 `else: return 'no_stop'` 是 while-else 的 else 子句（仅当 while 循环正常
结束，即没有 break 时执行），反编译产出变为 `return 'no_stop'` 顺序语句
（while 后无条件执行）。语义改变：原始当 while 中 break 时执行 `return items[i]`，
反编译产出当 while 中 break 时也执行 `return 'no_stop'`（因为顺序语句）。

#### Bug 32: `return items[i]` 完全丢失

原始 `return items[i]` 是 while-else 之后的语句（当 while 中 break 时执行），
反编译产出完全消失。elif body 没有正确的 break 路径 return。

#### Bug 33: 字节码指令数缩水（40 → 36）

重编字节码比原始少 4 条，主要因为 `return items[i]` 的
`LOAD_FAST items / LOAD_FAST i / BINARY_SUBSCR / RETURN_VALUE` 完全丢失。

**字节码对比**（filtered）:
- 原始 40 条 / 重编 36 条
- 原始末尾: `LOAD_FAST items / LOAD_FAST i / BINARY_SUBSCR / RETURN_VALUE`（return items[i]）
- 重编完全缺失以上 4 条

**根因推测**: 反编译器在 elif body 内含 while-else + break 时，把 while-else 的
else 子句错识别为 while 后的顺序语句（脱离 else 子句结构），同时丢失 while-else
之后的 `return items[i]`。可能是 while-else 的归约过程中 else 子句边界识别错误。
需要保留 elif body 内 while-else 的 else 子句结构。

---

### Bug 34-36: if body 内 with 多上下文 + 嵌套 with → 3 with 错合并 + `None(None, None)` 泄漏

**文件**: `test_adv19_with_multi_ctx_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 97 vs 120）

**源码**:
```python
def f(flag):
    if flag:
        with open('a') as fa, open('b') as fb:
            data = fa.read()
            with open('c') as fc:
                data += fc.read()
            return data + fb.read()
    return None
```

**反编译结果**:
```python
def f(flag):
    if flag:
        with open('a') as fa, open('b') as fb, open('c') as fc:
            data += fc.read()
            with open('c') as fc: pass
        (data + fb.read())
        None(None, None)
        return None(None, None)
```

**问题分解（3 个子 bug）**:

#### Bug 34: 嵌套 with 错合并到外层 with 多上下文

原始 `with open('a') as fa, open('b') as fb: ... with open('c') as fc: ...`
是外层多上下文 with + 内层嵌套 with，反编译产出变为
`with open('a') as fa, open('b') as fb, open('c') as fc:`（3 个上下文合并），
并额外生成 `with open('c') as fc: pass`（空 with body）。

#### Bug 35: `fa.read()` 完全丢失，`data` 变量未定义

原始 `data = fa.read()` 是外层 with body 的第一行（初始化 data 变量），
反编译产出完全消失。后续 `data += fc.read()` 在 data 未定义的情况下执行，
运行时会产生 NameError。

#### Bug 36: `None(None, None)` AST 字典泄漏 + `return None(None, None)` 错误生成

反编译产出 `None(None, None)` 和 `return None(None, None)` 出现，
这是反编译器把 AST 节点 dict 当作函数调用生成的明显 bug。
原本应该是 `return data + fb.read()`，反编译产出变为
`(data + fb.read())` 表达式语句 + `None(None, None)` + `return None(None, None)`。

**字节码对比**（filtered）:
- 原始 97 条 / 重编 120 条（重编多 23 条）
- 重编多余的 `LOAD_GLOBAL open / LOAD_CONST c / PRECALL / CALL / BEFORE_WITH / STORE_FAST`（错合并的第三个 with 上下文）
- 重编完全缺失 `LOAD_FAST fa / LOAD_METHOD read / PRECALL / CALL / STORE_FAST data`（data = fa.read()）

**根因推测**: 反编译器在 if body 内含 with 多上下文 + 嵌套 with 时，把嵌套 with
错合并到外层 with 的上下文列表，丢失 `fa.read()` 调用，并泄漏 `None(None, None)`
AST dict 字面量到反编译产出（明显的 CodeGenerator bug）。
需要修正 if body 内嵌套 with 的归约逻辑，保留嵌套结构。

---

## 附加：被跳过的测试（实际是语法错误 bug）

### Bug 37-39: async 函数 if body 内 async with + async for + 嵌套 if → `break` 泄漏出循环

**文件**: `test_adv19_async_with_async_for_in_if_body.py`
**状态**: SKIPPED（重编译失败：`SyntaxError: 'break' outside loop`）

**源码**:
```python
async def f(flag):
    if flag:
        async with get_session() as session:
            async for item in session.iter():
                if item.is_valid():
                    await process(item)
                    return 'done'
        return 'no_item'
    return 'skip'
```

**反编译结果**:
```python
async def f(flag):
    if flag:
        async with get_session() as session:
            async for item in session.iter():
                if item.is_valid():
                    pass
            break
            break
```

**问题分解（3 个子 bug）**:

#### Bug 37: `await process(item)` 退化为 `pass`

原始 `await process(item)` 是内层 if body 的语句，反编译产出变为 `pass`，
await 表达式完全丢失。

#### Bug 38: 内层 `return 'done'` 完全丢失

原始 `return 'done'` 在 `await process(item)` 之后，反编译产出完全消失。

#### Bug 39: 多余 `break` 泄漏出 async for 循环（语法错误）

反编译产出在 async for 之后生成两个 `break` 语句，但 break 在循环外（语法错误），
导致重编译失败。同时外层 `return 'no_item'` 和 `return 'skip'` 完全丢失。

**根因推测**: 反编译器在 async 函数 if body 内 async with + async for + 嵌套 if 时，
async with + async for 的 SEND/YIELD_VALUE 循环模式干扰了内层 IfRegion 识别，
把 `await process(item)` 退化为 pass，把 `return 'done'` 丢失，并泄漏 break 出循环。
需要修正 async with + async for 在 if body 内的归约逻辑。

---

### Bug 40-42: elif body 内 class + 继承 + super → 类体内泄漏 return

**文件**: `test_adv19_nested_class_in_elif_body.py`
**状态**: SKIPPED（重编译失败：`SyntaxError: 'return' outside function`）

**源码**:
```python
def f(x):
    if x > 0:
        return 'pos'
    elif x == 0:
        class Animal(Base):
            def __init__(self, name):
                super().__init__()
                self.name = name
            def speak(self):
                return self.name
        return Animal('cat').speak()
    else:
        return 'neg'
```

**反编译结果**:
```python
def f(x):
    if (x > 0):
        return 'pos'
    elif (x == 0):
        class Animal(Base):
            def __init__(self, name):
                super().__init__()
                self.name = name
            def speak(self):
                return self.name
            return (__classcell__ := __class__)
        return Animal('cat').speak()
    return 'neg'
```

**问题分解（3 个子 bug）**:

#### Bug 40: 类体内泄漏 `return (__classcell__ := __class__)`

原始 class Animal 的 body 内只有 `__init__` 和 `speak` 两个方法，
反编译产出在 class body 末尾错误添加 `return (__classcell__ := __class__)`
语句。这是反编译器把 class 的 `__classcell__` 闭包变量错生成为 return 语句，
而 class body 内不能有 return（语法错误）。

#### Bug 41: walrus 表达式 `(__classcell__ := __class__)` 错误生成

反编译产出 `return (__classcell__ := __class__)` 中，
`(__classcell__ := __class__)` 是 walrus 表达式（Python 3.8+），
但原本应该是 `__classcell__` 闭包变量的赋值（class body 的隐式变量）。
反编译器把 class body 的隐式 `__classcell__` 处理错生成为 walrus 表达式。

#### Bug 42: 外层 else 分支 `return 'neg'` 错挂到函数顶层

原始 `else: return 'neg'` 是 if-elif-else 的 else 分支，
反编译产出 `return 'neg'` 错挂到函数顶层（与 if 同级），脱离 else 分支结构。

**根因推测**: 反编译器在 elif body 内含 class + 继承 + super 时，
对 class 的 `__classcell__` 闭包变量错生成为 walrus 表达式 + return 语句
（class body 内不允许 return，导致语法错误）。同时外层 else 分支的 return
错挂到函数顶层。需要修正 elif body 内 class 定义的归约逻辑，不要在 class body
内生成 return 语句。

---

## 错误模式归类

### 模式 A: if-elif-else 三分支都含复杂语句 → 整体退化为 ternary（4 个测试，12 个子 bug）

反编译器在 if-elif-else 三分支都含复杂语句时归约严重错乱：
1. 三分支都含 assert + chained cmp + f-string → 整体退化为单 ternary
2. 三分支各自含 for + continue/break → 整体退化为 ternary `(items if mode == 'a' else items if mode == 'b' else items)`
3. 三分支各自含 for/try/with → 整体退化为 ternary `(items if x > 0 else x < 0)`
4. 三分支各自嵌套 if-elif-else → 整体退化为 6 个裸 return

反编译器对 if-elif-else 三分支都含复杂语句（特别是循环、try、with）的归约逻辑
有 bug，把三分支入口错合并为 ternary 表达式，body 全部逃出 if-elif-else 到
函数顶层。

**涉及测试**: Bug 1, 2, 3（test_adv19_assert_chained_cmp_in_if_body）+ Bug 7, 8, 9（test_adv19_for_continue_in_each_branch）+ Bug 16, 17, 18（test_adv19_mixed_complex_branches）+ Bug 22, 23, 24（test_adv19_nested_if_elif_in_each_branch）

### 模式 B: if-elif-else 条件含复杂表达式 → 条件错乱 / 语义反转（4 个测试，12 个子 bug）

反编译器在 if-elif-else 条件含复杂表达式时归约错乱：
1. async if-elif-else 条件含 await + boolop → 整体退化为 `if (0 and 100):` 丢失所有 await
2. elif 条件含 `a is not None or b is not None` → 错误包裹 `not(...)` 语义反转（De Morgan 错误）
3. if-elif 条件含 lambda IIFE + boolop → lambda 体被替换为 `None`，参数替换为 `*args, **kwargs`
4. if body 内多行 dict + 嵌套 ternary + 后续 if → 内层 if 退化为表达式语句

反编译器对 if-elif-else 条件含 await / is not None / lambda IIFE / 多行 dict 的
归约逻辑有 bug，丢失条件表达式或语义反转。

**涉及测试**: Bug 4, 5, 6（test_adv19_await_in_if_cond）+ Bug 10, 11, 12（test_adv19_is_isnot_chain_in_if_cond）+ Bug 13, 14, 15（test_adv19_lambda_iife_in_if_cond）+ Bug 19, 20, 21（test_adv19_multiline_return_in_if_body）

### 模式 C: if/elif body 内嵌套循环 + flow control → 循环边界错乱（2 个测试，6 个子 bug）

反编译器在 if/elif body 内嵌套循环 + flow control 时归约错乱：
1. elif body 内 while-else + break → `else: return 'no_stop'` 错挂为顺序语句，`return items[i]` 丢失
2. async 函数 if body 内 async with + async for + 嵌套 if → `await process(item)` 退化为 pass，泄漏 break 出循环（语法错误）

反编译器对 elif body 内 while-else / async for 的归约逻辑有 bug，
把 else 子句错挂为顺序语句，丢失 break 之后的 return。

**涉及测试**: Bug 31, 32, 33（test_adv19_while_else_break_in_elif_body）+ Bug 37, 38, 39（test_adv19_async_with_async_for_in_if_body，SKIPPED）

### 模式 D: if body 内 try/with 复杂结构 → 后续代码错挂 / 语句丢失（3 个测试，9 个子 bug）

反编译器在 if body 内 try/with 复杂结构时归约错乱：
1. if body 内 try-except-else + 后续 if-elif → 函数末尾 `return 'none'` 错挂到内层 else
2. if body 内 with 多上下文 + 嵌套 with → 3 with 错合并 + `fa.read()` 丢失 + `None(None, None)` 泄漏
3. elif body 内 class + 继承 + super → 类体内泄漏 `return (__classcell__ := __class__)`（语法错误）

反编译器对 if body 内 try-except-else / with 多上下文 / class 定义的归约逻辑有 bug，
错挂后续代码到内层分支，丢失语句，或泄漏 AST dict 字面量。

**涉及测试**: Bug 25, 26, 27（test_adv19_try_except_else_in_if_body）+ Bug 34, 35, 36（test_adv19_with_multi_ctx_in_if_body）+ Bug 40, 41, 42（test_adv19_nested_class_in_elif_body，SKIPPED）

### 模式 E: if-elif-else body 内 tuple unpacking → return 丢失（1 个测试，3 个子 bug）

反编译器在 if-elif-else body 内含 tuple unpacking + starred 时，
else 分支的 return 语句丢失。可能是 UNPACK_EX + STORE_FAST 链的归约过程中
误把后续 return 视为"已被吞并"而丢弃。

**涉及测试**: Bug 28, 29, 30（test_adv19_tuple_unpack_in_if_body）

### 模式 F: AST dict 字面量泄漏（CodeGenerator bug）（2 个测试，隐含在 Bug 16-18 和 Bug 34-36）

反编译器在多种边界条件下泄漏 AST dict 字面量到反编译产出：
1. `None(None, None)` 在 if-elif-else 三分支各自含复杂语句时泄漏
2. `None(None, None)` 和 `return None(None, None)` 在 if body 内 with 多上下文时泄漏

这是 CodeGenerator 在某种边界条件下未正确转换 AST 节点到源码的明显 bug。

**涉及测试**: Bug 17, 18（test_adv19_mixed_complex_branches）+ Bug 34, 35, 36（test_adv19_with_multi_ctx_in_if_body）

---

## 与 R1-R18 的区别

R1-R18 主要覆盖：
- 三元表达式、walrus、boolop、字符串/数值/容器字面量在 if 条件或 if body 中
- match 语句在 if body 内（R16/R18）
- for/while body 内 if/elif/else + flow control（R17/R18）
- Python 3.11+ except* 异常组（R17）
- 生成器 yield/yield from 在 if body（R18）
- raise from / chained comparison / 嵌套 ternary 在 elif 链（R18）

R19 新发现集中在：

1. **if-elif-else 三分支都含复杂语句 → 整体退化为 ternary** — **此前未系统覆盖**
   R18 测过三分支都含 raise from / yield from，但 R19 首次系统覆盖
   三分支都含 assert + chained cmp / for + continue / for-try-with 混合 / 嵌套 if-elif-else
   的子模式，发现 12 个新 bug，核心是反编译器把三分支入口错合并为 ternary 表达式。

2. **if-elif-else 条件含复杂表达式** — **R18 测过嵌套 ternary，但 await / is not / lambda IIFE 未覆盖**
   R19 首次系统覆盖 async if-elif-else 条件含 await + boolop、elif 条件含 is not None 链、
   if-elif 条件含 lambda IIFE 的子模式，发现 12 个新 bug。
   特别是 **elif 条件 `a is not None or b is not None` 错误包裹 `not(...)` 语义反转**
   是严重的语义正确性 bug（非结构 bug）。

3. **elif body 内 match / while-else / class** — **此前未覆盖**
   R18 只测 if body 内 match，R19 首次覆盖 elif body 内 match-case、while-else + break、
   class + 继承 + super 的子模式，发现 elif body 内 while-else 的 else 子句错挂为顺序语句、
   class body 内泄漏 `return (__classcell__ := __class__)` 等严重 bug。

4. **async 函数 if body 内 async with + async for + 嵌套 if** — **此前未覆盖**
   R18 只测 if body 内 async for，R19 首次覆盖 async with + async for + 嵌套 if 的
   组合模式，发现 `await process(item)` 退化为 pass、break 泄漏出循环（语法错误）等 bug。

5. **if body 内 with 多上下文 + 嵌套 with** — **此前未覆盖**
   R18 测过 if body 内 with 单上下文，R19 首次覆盖 if body 内 with 多上下文 + 嵌套 with
   的组合模式，发现 3 with 错合并、`fa.read()` 丢失、`None(None, None)` AST 字典泄漏等 bug。

6. **AST dict 字面量泄漏（CodeGenerator bug）** — **R18 测过嵌套 ternary 泄漏 `{'type': 'Constant', ...}`**
   R19 发现 `None(None, None)` 这种新的 AST dict 泄漏形式，在 if-elif-else 三分支混合复杂语句
   和 if body 内 with 多上下文两种边界条件下都出现。说明 CodeGenerator 的 AST dict 泄漏 bug
   比 R18 发现的更普遍。

---

## 建议修复优先级

1. **最高**: Bug 22-24（if-elif-else 三分支各自嵌套 if-elif-else → 退化为 6 个裸 return）
   — 3 个子 bug，涉及 if-elif-else 三分支各自嵌套 if-elif-else 时整体退化为 6 个裸 return，
   9 分支结构完全丢失，重编字节码 42 → 2。**最严重的结构 bug**。
   需要修正嵌套 IfRegion 的归约顺序，保留嵌套 if-elif-else 结构。

2. **最高**: Bug 10-12（elif `a is not None or b is not None` → `not(...)` 语义反转）
   — 3 个子 bug，涉及 **语义正确性 bug**（非结构 bug）：反编译产出可编译但语义错误，
   运行结果与原始完全相反。这是反编译器最危险的 bug 类型（silent semantic corruption）。
   需要修正 elif 条件含 `is not None or is not None` 的归约逻辑，不应包裹 not(...)。

3. **最高**: Bug 4-6（async if-elif-else 条件含 await + boolop → 丢失所有 await）
   — 3 个子 bug，涉及 async 函数 IfRegion 条件含 await 时整体退化为 `if (0 and 100):`，
   丢失所有 await 表达式和比较运算，elif 链 + else 完全丢失。重编字节码 49 → 5。
   需要在 async 函数 IfRegion 条件中正确重建 await 表达式。

4. **最高**: Bug 13-15（if-elif 条件含 lambda IIFE → lambda 体被替换为 None）
   — 3 个子 bug，涉及 if-elif 条件含 lambda IIFE 时 lambda 参数和体完全错误替换。
   lambda 体 `x > 0` 被替换为 `None`，参数 `x` 被替换为 `*args, **kwargs`。
   需要修正 lambda IIFE 在 IfRegion 条件中的归约，保留 lambda 的参数和体。

5. **高**: Bug 16-18 + Bug 34-36（AST dict 字面量泄漏 `None(None, None)`）
   — 6 个子 bug（分布在 2 个测试），涉及 CodeGenerator 把 AST 节点 dict 当作函数调用
   生成的明显 bug。反编译产出含 `None(None, None)` 和 `return None(None, None)` 这种
   字面量，说明 CodeGenerator 在某种边界条件下未正确转换 AST 节点到源码。
   需要修正 CodeGenerator 的 AST dict 转换逻辑。

6. **高**: Bug 7-9（if-elif-else 三分支各自含 for + continue/break → 3 for 逃出分支）
   — 3 个子 bug，涉及 if-elif-else 三分支都含 for 循环 + flow control 时整体退化为
   ternary `(items if mode == 'a' else items if mode == 'b' else items)`，
   3 个 for 全部逃出 if-elif-else 到函数顶层。
   需要在 if-elif-else body 内含 for 循环时保持 IfRegion 结构。

7. **高**: Bug 1-3（if-elif-else 三分支都含 assert + chained cmp + f-string → 退化为 ternary）
   — 3 个子 bug，涉及 if-elif-else 三分支都含 assert + chained cmp + f-string msg 时
   整体退化为单 ternary，所有 assert 和 return 丢失。
   需要在 if-elif-else body 内含 assert + chained cmp 时保持 IfRegion 结构。

8. **中**: Bug 31-33（elif body 内 while-else + break → else 子句错挂为顺序语句）
   — 3 个子 bug，涉及 elif body 内 while-else + break 时 else 子句错挂为顺序语句，
   `return items[i]` 丢失。需要保留 elif body 内 while-else 的 else 子句结构。

9. **中**: Bug 25-27（if body 内 try-except-else + 后续 if-elif → return 错挂）
   — 3 个子 bug，涉及 if body 内 try-except-else + 后续 if-elif 时函数末尾 return
   错挂到内层 else 分支。需要在归约内层 IfRegion 时正确区分函数 fallthrough 和 else 分支。

10. **中**: Bug 28-30（if-elif-else body 内 tuple unpacking → return 丢失）
    — 3 个子 bug，涉及 if-elif-else body 内含 tuple unpacking + starred 时 else 分支
    return 丢失。需要保留 if-elif-else body 内 tuple unpacking 之后的 return 语句。

11. **中**: Bug 19-21（if body 内多行 dict + 嵌套 ternary + 后续 if → 内层 if 退化为表达式）
    — 3 个子 bug，涉及 if body 内多行 dict + 嵌套 ternary + 后续 if 时内层 if 退化为
    表达式语句，return 错挂到外层 if。需要保留 if body 内嵌套 if 的条件检查结构。

12. **中**: Bug 37-39（async 函数 if body 内 async with + async for + 嵌套 if → break 泄漏，SKIPPED）
    — 3 个子 bug，涉及 async 函数 if body 内 async with + async for + 嵌套 if 时
    `await process(item)` 退化为 pass，break 泄漏出循环（语法错误）。
    需要修正 async with + async for 在 if body 内的归约逻辑。

13. **中**: Bug 40-42（elif body 内 class + 继承 + super → 类体内泄漏 return，SKIPPED）
    — 3 个子 bug，涉及 elif body 内 class + 继承 + super 时类体内泄漏
    `return (__classcell__ := __class__)`（语法错误）。
    需要修正 elif body 内 class 定义的归约逻辑，不要在 class body 内生成 return 语句。

---

## 修复建议（不修改源码，仅描述方向）

### if-elif-else 三分支都含复杂语句 → 退化为 ternary（Bug 1-3, 7-9, 16-18, 22-24）

需要在 if-elif-else 三分支都含复杂语句（assert / for / try / with / 嵌套 if-elif）时：
1. 不要把三分支入口错合并为 ternary 表达式
2. 保持 IfRegion 结构，body 全部留在 if/elif/else 内
3. 保留所有 assert / return / for / try / with 语句

### elif 条件含 `is not None or is not None` → 语义反转（Bug 10-12）

需要在 elif 条件含 `X is not None or Y is not None` 时：
1. 不要错误包裹 `not(...)`
2. 保留原始条件表达式 `X is not None or Y is not None`
3. 修正 IS_OP + boolop 链的归约逻辑

### async if-elif-else 条件含 await + boolop（Bug 4-6）

需要在 async 函数 IfRegion 条件含 await + boolop 时：
1. 保留 GET_AWAITABLE + YIELD_VALUE 字节码模式
2. 正确重建 await 表达式
3. 保留 elif 链 + else 分支结构

### lambda IIFE 在 if-elif 条件（Bug 13-15）

需要在 if-elif 条件含 lambda IIFE `(lambda x: ...)(y)` 时：
1. 保留 lambda 的参数签名（`x` 而非 `*args, **kwargs`）
2. 保留 lambda 体的比较逻辑（`x > 0` 而非 `None`）
3. 修正 MAKE_FUNCTION + LOAD_CONST <code> 模式的归约

### CodeGenerator AST dict 泄漏（Bug 16-18, 34-36）

需要修正 CodeGenerator 在边界条件下未正确转换 AST 节点到源码的 bug：
1. 不要把 AST dict 当作函数调用生成 `None(None, None)`
2. 不要把 AST dict 直接字符串化输出
3. 检查 CodeGenerator 的所有节点转换路径

### elif body 内 while-else + break（Bug 31-33）

需要在 elif body 内 while-else + break 时：
1. 保留 while-else 的 else 子句结构
2. 不要把 else 子句错挂为 while 后的顺序语句
3. 保留 while-else 之后的 return 语句

### if body 内 with 多上下文 + 嵌套 with（Bug 34-36）

需要在 if body 内 with 多上下文 + 嵌套 with 时：
1. 不要把嵌套 with 错合并到外层 with 的上下文列表
2. 保留外层 with body 内的语句（如 `data = fa.read()`）
3. 保留嵌套 with 的独立结构

### async 函数 if body 内 async with + async for（Bug 37-39）

需要在 async 函数 if body 内 async with + async for + 嵌套 if 时：
1. 保留 `await process(item)` 表达式
2. 保留内层 if body 的 return 语句
3. 不要泄漏 break 出 async for 循环

### elif body 内 class + 继承 + super（Bug 40-42）

需要在 elif body 内 class + 继承 + super 时：
1. 不要在 class body 内生成 `return (__classcell__ := __class__)`
2. 保留 class body 内只有方法定义
3. 保留外层 else 分支的 return 语句

### if body 内 try-except-else + 后续 if-elif（Bug 25-27）

需要在 if body 内 try-except-else + 后续 if-elif 时：
1. 保留函数末尾 fallthrough return 不被错挂到内层 else 分支
2. 正确区分函数 fallthrough 和内层 IfRegion 的 else 分支

### if-elif-else body 内 tuple unpacking（Bug 28-30）

需要在 if-elif-else body 内含 tuple unpacking + starred 时：
1. 保留 else 分支的 return 语句不被吞并
2. 修正 UNPACK_EX + STORE_FAST 链的归约过程

### if body 内多行 dict + 嵌套 ternary + 后续 if（Bug 19-21）

需要在 if body 内多行 dict + 嵌套 ternary + 后续 if 时：
1. 保留内层 if 的条件检查结构，不要退化为表达式语句
2. 保留内层 if body 的 return 语句
3. 保留外层 if body 末尾的 return 语句

---

## 总结

R19 在 32 个测试中发现 **12 个失败 + 2 个跳过（实为语法错误 bug）**（共 42 个子 bug），
分布在 6 个错误模式：

- **if-elif-else 三分支都含复杂语句 → 退化为 ternary**（12 个子 bug）— 最严重的结构 bug，
  整体 if-elif-else 结构完全丢失
- **if-elif-else 条件含复杂表达式 → 条件错乱 / 语义反转**（12 个子 bug）— 包括
  **elif `a is not None or b is not None` → `not(...)` 语义反转**这种
  silent semantic corruption bug（最危险的 bug 类型）
- **if/elif body 内嵌套循环 + flow control → 循环边界错乱**（6 个子 bug）—
  while-else 的 else 子句错挂为顺序语句，async for + await 退化为 pass
- **if body 内 try/with 复杂结构 → 后续代码错挂 / 语句丢失**（9 个子 bug）—
  try-except-else 后续 return 错挂、with 多上下文 + 嵌套 with 错合并、
  class body 内泄漏 return 语句（语法错误）
- **if-elif-else body 内 tuple unpacking → return 丢失**（3 个子 bug）
- **AST dict 字面量泄漏（CodeGenerator bug）**（隐含 6 个子 bug）—
  `None(None, None)` 字面量在多种边界条件下泄漏

其中 **elif 条件 `a is not None or b is not None` → `not(...)` 语义反转**（Bug 10-12）
是 silent semantic corruption bug，反编译产出可编译但语义错误，运行结果与原始完全相反，
应最优先修复。**if-elif-else 三分支各自嵌套 if-elif-else → 退化为 6 个裸 return**
（Bug 22-24）和 **async if-elif-else 条件含 await → 退化为 `if (0 and 100):`**（Bug 4-6）
是严重的结构 bug，重编字节码分别 42→2 和 49→5，应优先修复。

R19 完成了任务要求的 10+ 个真实失败场景的发现和详细分析，无回归
（基线 25 failed 全部保持，新增 12 failed + 18 passed + 2 skipped）。
