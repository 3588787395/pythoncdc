# Round 20 — IF 区域反编译器测试发现

**日期**: 2026-07-20
**测试工程师**: R20 自动探索（IF 区域最后一轮）
**当前分支**: trae/region-iteration-v2
**基线 commit**: 9186044 (R19 修复后)
**基线状态**: 760 passed / 35 failed / 9 skipped

**测试范围**: IF 区域内未覆盖模式，聚焦 R1-R19 未触及的 12 个方向：
1. if body 内含 class 定义 + metaclass 关键字参数
2. async 函数 if body 内含 async generator + async for
3. if-elif-else 三分支都含属性多重 augassign
4. if-elif-else 三分支都含 for-else + break 组合
5. if body 内含 class + __slots__ + classmethod + staticmethod
6. if body 内含 while + walrus 条件 + 嵌套 if-elif-else
7. if body 内含嵌套 lambda 闭包捕获（多层闭包）
8. if-elif-else 三分支都含 assert + 链式比较 + f-string msg
9. if body 内含嵌套 try-except + raise from
10. if-elif-else 三分支都含 dictcomp/setcomp 多 for + if 过滤
11. if-elif-else 三分支都含 *args / **kwargs 混合调用
12. if-elif-else body 内含 PEP 604 union 类型注解
13. if-elif-else 三分支都含 del slice + del subscr + del attr
14. elif body 内含 match + 多 case + guard + class pattern
15. if body 内含 while + yield + 嵌套 if-elif（生成器）
16. if-elif-else body 内含 global 多变量 + del global key
17. elif body 内含多装饰器 + 嵌套函数 + nonlocal 修改
18. if-elif-else 三分支都含多元素 tuple + 嵌套结构 return
19. if-elif-else 三分支都含多重 subscr augassign
20. elif body 内含嵌套 with + try + 嵌套 if-else
21. if-elif-else 三分支都含 nonlocal 多变量 + 嵌套闭包修改
22. async 函数 if-elif-else body 含 async for + await + async with 组合
23. if-elif-else 三分支都含链式方法调用 + 链式 subscr

---

## 统计摘要

| 指标 | 数量 |
|------|------|
| 测试文件总数 | 23 |
| 失败（FAILED） | 11 |
| 通过（PASSED） | 11 |
| 跳过（SKIPPED） | 1 |
| **新错误总数（去重子 bug）** | **27** |

运行命令:
```
cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv20_*.py --tb=short -q
```

结果: `11 failed, 11 passed, 1 skipped in 2.26s`

---

## 测试文件列表

| # | 文件 | 状态 | 错误类别 |
|---|------|------|----------|
| 1 | `test_adv20_assert_chained_cmp_in_branches.py` | **FAILED** | if-elif-else 三分支都含 assert + chained cmp + f-string → 整体退化为单 ternary，丢失 assert 与 return |
| 2 | `test_adv20_async_for_with_await_in_if_body.py` | SKIPPED | async 函数 if-elif-else body 含 async for + await + async with → 重编译失败（已知限制） |
| 3 | `test_adv20_async_generator_in_if_body.py` | PASSED | — （if body 内 async generator + async for） |
| 4 | `test_adv20_augassign_attr_in_elif_body.py` | PASSED | — （if-elif-else 三分支都含属性多重 augassign） |
| 5 | `test_adv20_chained_augassign_subscr_in_branches.py` | PASSED | — （if-elif-else 三分支都含多重 subscr augassign） |
| 6 | `test_adv20_chained_method_call_in_branches.py` | PASSED | — （if-elif-else 三分支都含链式方法 + subscr） |
| 7 | `test_adv20_class_with_metaclass_in_if_body.py` | **FAILED** | if body 内 class + metaclass= → metaclass 关键字参数丢失 |
| 8 | `test_adv20_class_with_slots_in_if_body.py` | **FAILED** | if body 内 class + __slots__ + @classmethod + @staticmethod → 装饰器错位应用到 __init__ |
| 9 | `test_adv20_del_slice_in_if_body.py` | PASSED | — （if-elif-else 三分支都含 del slice/subscr/attr） |
| 10 | `test_adv20_dictcomp_complex_filter_in_branches.py` | **FAILED** | if-elif-else 三分支含 dictcomp 多 for + if → 解包错误，多 for 合并 |
| 11 | `test_adv20_for_else_break_in_each_branch.py` | **FAILED** | if-elif-else 三分支都含 for-else+break → 整体退化为 ternary，三个 for 逃出分支 |
| 12 | `test_adv20_global_del_in_if_body.py` | PASSED | — （if-elif-else body 内 global 多变量 + del） |
| 13 | `test_adv20_lambda_with_closure_in_if_body.py` | PASSED | — （if body 内嵌套 lambda 闭包捕获） |
| 14 | `test_adv20_match_with_guard_in_elif_body.py` | PASSED | — （elif body 内 match + guard + class pattern） |
| 15 | `test_adv20_multi_decorator_nested_func_in_elif.py` | PASSED | — （elif body 内多装饰器 + 嵌套函数 + nonlocal） |
| 16 | `test_adv20_nested_try_raise_from_in_if_body.py` | **FAILED** | if body 内嵌套 try + raise from → 内层 except 错位，外层 except 丢失 return |
| 17 | `test_adv20_nested_with_try_in_elif_body.py` | **FAILED** | elif body 内嵌套 with + try + if-else → 语法错误，with 块后产生 None(None,None) 垃圾 |
| 18 | `test_adv20_nonlocal_multi_in_elif_branches.py` | PASSED | — （if-elif-else 三分支都含 nonlocal 多变量） |
| 19 | `test_adv20_star_expr_in_call_in_if_body.py` | **FAILED** | if-elif-else 三分支含 *args/**kwargs → listcomp 内 dict unpacking 错译为 =Dict[k,v+1] 垃圾 |
| 20 | `test_adv20_tuple_return_in_branches.py` | **FAILED** | if-elif-else 三分支返回多元素 tuple → else 分支丢失 if-elif-else 结构，return 错译为只剩 genexp |
| 21 | `test_adv20_union_type_ann_in_if_body.py` | PASSED | — （if-elif-else body 含 PEP 604 union 类型注解） |
| 22 | `test_adv20_walrus_in_while_cond_nested_if.py` | **FAILED** | if body 内 while + walrus + 嵌套 if-elif-else → while 末尾产生游离 next 引用 |
| 23 | `test_adv20_yield_in_while_in_if_body.py` | **FAILED** | if body 内 while + yield + 嵌套 if-elif → 丢失末尾 return 语句 |

---

## Bug 详细分析

### Bug 1: if-elif-else 三分支都含 assert + 链式比较 → 整体退化为单 ternary

**文件**: `test_adv20_assert_chained_cmp_in_branches.py`
**状态**: FAILED（反编译结果中未找到预期的区域类型 IF_REGION）

**源码**:
```python
def f(flag, x):
    if flag == 'a':
        assert 0 < x < 10, f'out of range: {x}'
        return x * 2
    elif flag == 'b':
        assert 10 < x < 100, 'too small'
        return x // 2
    else:
        assert -100 < x < 0, 'must be neg'
        return -x
```

**反编译结果**:
```python
def f(flag, x):
    (0 < x if flag == 'a' else 10 < x if flag == 'b' else -100 < x)
    raise RuntimeError('must be neg')
    return (-x)
```

**问题分解（3 个子 bug）**:

#### Bug 1.1: if-elif-else 三分支整体退化为单 ternary 表达式

原始 if-elif-else 三分支被吞并，反编译产出只剩 `(0 < x if flag == 'a' else 10 < x if flag == 'b' else -100 < x)` 一个嵌套 ternary 表达式语句。三个分支的 assert + chained comparison 被错合并为 ternary 的条件表达式（assert 0 < x < 10 → 0 < x；assert 10 < x < 100 → 10 < x；assert -100 < x < 0 → -100 < x）。

#### Bug 1.2: 所有 assert 语句完全丢失

原始字节码中三个 `assert 0 < x < 10, f'...'` 等语句（包含 ASSERT_RAISE、FORMAT_VALUE、BUILD_STRING）在反编译产出中完全消失。assert 的 AssertRegion 识别被 if 区域归约干扰。

#### Bug 1.3: 前两个分支的 return 完全丢失，错译为 raise RuntimeError

原始 `return x * 2` / `return x // 2` 两个 return 语句全部消失，反编译产出中错译为 `raise RuntimeError('must be neg')`（来自 else 分支的 assert 消息），且只保留 else 分支的 `return (-x)`。

**根因推测**: 反编译器在 if-elif-else 三分支都含 assert + chained cmp + f-string msg 时，对 assert 的 AssertRegion 识别被 IfRegion 归约干扰，把每个 assert 的 chained comparison 条件错合并为 ternary 表达式，整体结构完全丢失。需要在 if-elif-else body 内含 assert + chained cmp 时保持 IfRegion 结构，禁止退化为 ternary。这是 R19 `test_adv19_assert_chained_cmp_in_if_body.py` 同类 bug 在 if-elif-else 三分支场景下的复发，说明 R19 修复未覆盖多分支场景。

---

### Bug 2: if body 内 class + metaclass= 关键字参数丢失

**文件**: `test_adv20_class_with_metaclass_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 32 vs 30）

**源码**:
```python
def f(flag):
    if flag:
        class Meta(type):
            pass
        class C(metaclass=Meta):
            def __init__(self, x):
                self.x = x
            def get(self):
                return self.x
        return C(10).get()
    return 0
```

**反编译结果**:
```python
def f(flag):
    if flag:
        class Meta(type):
            pass
        class C:                    # <-- metaclass=Meta 丢失!
            def __init__(self, x):
                self.x = x
            def get(self):
                return self.x
        return C(10).get()
    else:
        return 0
```

**字节码对比**（filtered）:
- 原始 32 条 / 重编 30 条
- 原始: `... LOAD_FAST Meta / KW_NAMES / PRECALL / CALL ...`（含 metaclass 关键字参数）
- 重编: `... PRECALL / CALL / STORE_FAST ...`（无 KW_NAMES，metaclass 丢失）

**根因推测**: 反编译器在 if body 内 class 定义含 `metaclass=` 关键字参数时，class AST 生成器没有保留 metaclass 关键字参数。`KW_NAMES` 指令是 Python 3.11+ 用于关键字参数的指令，反编译器未正确将其重建为 class 定义的 keyword 参数。R17 测试过 `class_def_in_if.py` 但未覆盖 metaclass 关键字参数场景。

---

### Bug 3: if body 内 class + __slots__ + 多装饰器 → @classmethod 错位到 __init__

**文件**: `test_adv20_class_with_slots_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 24 vs 27）

**源码**:
```python
def f(flag):
    if flag:
        class Point:
            __slots__ = ('x', 'y')
            def __init__(self, x, y):
                self.x = x
                self.y = y
            @classmethod
            def origin(cls):
                return cls(0, 0)
            @staticmethod
            def distance(p1, p2):
                return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
        return Point.distance(Point(1, 2), Point.origin())
    return 0.0
```

**反编译结果**:
```python
def f(flag):
    if flag:
        class Point:
            __slots__ = ('x', 'y')
            @classmethod
            def __init__(self, x, y):     # <-- @classmethod 错位到 __init__!
                self.x = x
                self.y = y
            @classmethod
            def origin(cls):
                return cls(0, 0)
            @staticmethod
            def distance(p1, p2):
                return (((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5)
        return Point.distance(Point(1, 2), Point.origin())
    else:
        return 0.0
```

**问题分解（2 个子 bug）**:

#### Bug 3.1: @classmethod 错位应用到 __init__（不应有装饰器）

原始 `__init__` 没有装饰器，但反编译产出中 `__init__` 错误地被 `@classmethod` 装饰。这是因为 `@classmethod` 装饰器的归属识别在 class body 多方法场景下错位，装饰器被前置到上一个方法。

#### Bug 3.2: 字节码指令数不匹配（24 vs 27，重编多 3 条）

重编指令比原始多 3 条，主要因为 @classmethod 错位导致额外的 LOAD_NAME classmethod + CALL 指令。

**根因推测**: 反编译器在 if body 内 class 含多方法 + 多装饰器（@classmethod/@staticmethod）时，装饰器的归属识别错位，把 @classmethod 错置到前一个方法 __init__ 上。R19 测过 `class_def_with_method_in_if_body.py` 但未覆盖多装饰器场景。

---

### Bug 4: if-elif-else 三分支含 dictcomp 多 for + if → 解包错误，多 for 合并

**文件**: `test_adv20_dictcomp_complex_filter_in_branches.py`
**状态**: FAILED（嵌套 code object 不匹配: 20 vs 19）

**源码**:
```python
def f(flag, data):
    if flag == 'dict':
        return {k: v * 2 for k, v in data.items() if k != 'skip' for x in [v] if x > 0}
    elif flag == 'set':
        return {x % 10 for x in data if x > 0 for y in range(x) if y % 2 == 0}
    else:
        return {x: y for x in range(5) for y in range(5) if x + y == 4}
```

**反编译结果**:
```python
def f(flag, data):
    if (flag == 'dict'):
        return {k: v * 2 for k, v, x in data.items() if k != 'skip' and x > 0}
        # <-- 错误1: for k, v, x 三元解包（应是 for k, v + for x in [v]）
        # <-- 错误2: 两个 if 合并为 and（语义改变：原是嵌套 for，新是单 for + and）
    elif (flag == 'set'):
        return {x % 10 for x in data for y in range(x) if y % 2 == 0}
        # <-- 错误3: 丢失 if x > 0 过滤
    return {y: y for x in range(5) for y in range(5) if x + y == 4}
    # <-- 错误4: else 分支丢失 if-elif-else 结构，dictcomp key 错为 y（应 x）
```

**问题分解（3 个子 bug）**:

#### Bug 4.1: dictcomp 多 for 子句被错合并为单 for + 多变量解包

原始 `{k: v * 2 for k, v in data.items() if k != 'skip' for x in [v] if x > 0}` 含两个 for 子句（外层 `for k, v in data.items()` + 内层 `for x in [v]`），反编译错合并为单 for `for k, v, x in data.items()`，将两个 for 的循环变量合并到同一个解包中，且 `[v]` 字面量构建完全丢失。

#### Bug 4.2: dictcomp 多 if 过滤被错合并为 and 表达式

原始两个独立 if 过滤（`if k != 'skip'` 和 `if x > 0`）被错合并为 `if k != 'skip' and x > 0`。虽然语义在某些情况下等价，但当 if 之间夹有 for 子句时，and 合并会改变嵌套语义。

#### Bug 4.3: else 分支 dictcomp key 错为 y（应 x）

原始 else 分支 `{x: y for x in range(5) for y in range(5) if x + y == 4}` 的 key 是 x，但反编译产出 `{y: y for x in range(5) for y in range(5) if x + y == 4}` 的 key 错为 y。

**根因推测**: 反编译器在 if-elif-else 三分支都含 dictcomp/setcomp 多 for + 多 if 过滤时，comprehension 生成器对多 for + 多 if 的嵌套结构处理错乱，把多 for 子句错合并为单 for 多变量解包。R19 `comprehension_return_in_branches.py` 测过单 for + 单 if 的 dictcomp，但未覆盖多 for + 多 if 嵌套场景。

---

### Bug 5: if-elif-else 三分支都含 for-else+break → 整体退化为 ternary，三个 for 逃出分支

**文件**: `test_adv20_for_else_break_in_each_branch.py`
**状态**: FAILED（嵌套 code object 不匹配: 指令5操作码不匹配: GET_ITER vs LOAD_FAST）

**源码**:
```python
def f(flag, items):
    if flag == 'a':
        for x in items:
            if x > 0:
                break
        else:
            return 'no_pos'
        return x
    elif flag == 'b':
        for y in items:
            if y < 0:
                break
        else:
            return 'no_neg'
        return y
    else:
        for z in items:
            if z == 0:
                break
        else:
            return 'no_zero'
        return z
```

**反编译结果**:
```python
def f(flag, items):
    (items if flag == 'a' else items if flag == 'b' else items)
    # <-- 整体退化为 ternary（三 branch 都返回 items，无意义）
    for x in items:
        if (x > 0):
            break
    else:
        return 'no_pos'
    for y in items:
        if (y < 0):
            break
    else:
        return 'no_neg'
    for z in items:
        if (z == 0):
            break
    else:
        return 'no_zero'
    return z
    # <-- 三个 for-else 逃出 if 分支，并列到函数顶层
```

**问题分解（3 个子 bug）**:

#### Bug 5.1: if-elif-else 三分支整体退化为单 ternary（值都是 items）

原始 if-elif-else 三分支被吞并，反编译产出只剩 `(items if flag == 'a' else items if flag == 'b' else items)` 一个无意义嵌套 ternary 表达式语句。三个分支的 `return x` / `return y` / `return z` 被错合并为 ternary 的值表达式（全部错为 items）。

#### Bug 5.2: 三个 for-else 循环逃出 if 分支，并列到函数顶层

原始三个 for-else 循环分别属于 if/elif/else 三个分支，反编译产出中三个 for-else 循环全部逃出 if 分支，并列到函数顶层。这破坏了 if-elif-else 的分支语义。

#### Bug 5.3: 末尾 return z 错置到函数顶层（应属于 else 分支）

原始 `return z` 属于 else 分支（for-else 的 break 路径），反编译产出中错置到函数顶层，与三个并列 for-else 同级。

**根因推测**: 反编译器在 if-elif-else 三分支都含 for-else + break 时，对 for-else 的 LoopRegion 识别与 IfRegion 归约产生冲突，把 if-elif-else 结构错合并为 ternary，三个 for-else 循环逃出 IfRegion。R18 测过 `for_else_nested_in_if_body.py`（单分支含 for-else），但未覆盖三分支都含 for-else 的场景。

---

### Bug 6: if body 内嵌套 try + raise from → 内层 except 错位，外层 except 丢失 return

**文件**: `test_adv20_nested_try_raise_from_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 54 vs 55）

**源码**:
```python
def f(flag, x):
    if flag:
        try:
            try:
                if x < 0:
                    raise ValueError('neg')
                return x
            except ValueError as e:
                raise RuntimeError('inner') from e
        except RuntimeError as e2:
            return str(e2)
    return 0
```

**反编译结果**:
```python
def f(flag, x):
    if flag:
        try:
            try:
                if (x < 0):
                    raise ValueError('neg')
                return x
            except ValueError as e: raise RuntimeError('inner') from e
            # <-- 错误1: except 块被压缩为单行，块结构丢失
        except RuntimeError as e2: str(e2)
        # <-- 错误2: 外层 except 丢失 return
    else:
        return 0
```

**问题分解（2 个子 bug）**:

#### Bug 6.1: 内层 except 块被压缩为单行（块结构丢失）

原始内层 `except ValueError as e: raise RuntimeError('inner') from e` 是一个块语句，反编译产出中被压缩为单行 `except ValueError as e: raise RuntimeError('inner') from e`。虽然语义等价，但风格不一致，且影响后续语句的归属识别。

#### Bug 6.2: 外层 except 丢失 return 语句

原始外层 `except RuntimeError as e2: return str(e2)` 含 return 语句，反编译产出中 `except RuntimeError as e2: str(e2)` 丢失 return，导致函数在该路径无返回值。

**字节码对比**: 原始 54 条 / 重编 55 条（多 1 条），主要因为外层 except 路径的 return 丢失导致重编路径不同。

**根因推测**: 反编译器在 if body 内嵌套 try-except + raise from 时，内层 except 块的单语句被错压缩为单行，外层 except 的 return 语句在嵌套 try 的归约过程中被吞并。R18 测过 `try_finally_in_if_body.py`（单层 try），但未覆盖嵌套 try + raise from 场景。

---

### Bug 7: elif body 内嵌套 with + try + if-else → 语法错误，with 块后产生 None(None,None) 垃圾

**文件**: `test_adv20_nested_with_try_in_elif_body.py`
**状态**: FAILED（反编译结果语法错误: expected 'except' or 'finally' block）

**源码**:
```python
def f(flag, path):
    if flag == 'simple':
        return 'simple'
    elif flag == 'complex':
        with open(path) as f1:
            try:
                data = f1.read()
                if data:
                    with open(path + '.bak') as f2:
                        f2.write(data)
                    return 'written'
                else:
                    return 'empty'
            except IOError as e:
                return str(e)
    else:
        return 'none'
```

**反编译结果**:
```python
def f(flag, path):
    if (flag == 'simple'):
        return 'simple'
    elif (flag == 'complex'):
        with open(path) as f1:
            try:
                data = f1.read()
                if data:
                    with open(path + '.bak') as f2: f2.write(data)
                    None(None, None)         # <-- 垃圾代码!
                    return 'written'
                else:
                    None(None, None)         # <-- 垃圾代码!
                    return 'empty'
            # <-- 丢失 except 块，try 未关闭 → 语法错误
```

**问题分解（3 个子 bug）**:

#### Bug 7.1: with 块被压缩为单行，块结构丢失

原始 `with open(path + '.bak') as f2: f2.write(data)` 是一个 with 块，反编译产出中被压缩为单行。虽然语义等价，但影响后续语句归属。

#### Bug 7.2: with 块后产生 None(None, None) 垃圾代码

原始 with 块结束后是 `return 'written'`，反编译产出中 with 块后产生 `None(None, None)` 垃圾代码。这是 with 块的 __exit__ 调用字节码未被正确归约，被错译为函数调用 `None(None, None)`。

#### Bug 7.3: try 块未关闭，丢失 except 块 → 反编译结果语法错误

原始 try 块后有 `except IOError as e: return str(e)`，反编译产出中 try 块未关闭，except 块完全丢失，导致反编译结果无法通过语法检查（`expected 'except' or 'finally' block`）。

**根因推测**: 反编译器在 elif body 内嵌套 with + try + if-else 时，内层 with 块的 __exit__ 字节码未被正确归约（产生 None(None,None) 垃圾），且外层 try 块的 except 在嵌套结构的归约过程中被吞并，导致语法错误。R17 测过 `with_try_nested_in_if.py`（单层 with + try），但未覆盖嵌套 with + try + if-else 三层组合。

---

### Bug 8: if-elif-else 三分支含 *args/**kwargs → listcomp 内 dict unpacking 错译为 =Dict[k,v+1] 垃圾

**文件**: `test_adv20_star_expr_in_call_in_if_body.py`
**状态**: FAILED（反编译结果语法错误: invalid syntax）

**源码**:
```python
def f(flag, items, extra):
    if flag == 'a':
        return sorted(*items, key=lambda x: -x, **extra)
    elif flag == 'b':
        return [f(*x, **{k: v + 1}) for x in items for k, v in extra.items()]
    else:
        return {**extra, 'sum': sum(items), 'count': len(items)}
```

**反编译结果**:
```python
def f(flag, items, extra):
    if (flag == 'a'):
        return sorted(*items, key=(lambda *args, **kwargs: None), **extra)
        # <-- 错误1: lambda x: -x 错译为 lambda *args, **kwargs: None
    elif (flag == 'b'):
        return [f(*x, =Dict[k, v + 1]) for x in items]
        # <-- 错误2: **{k: v + 1} 错译为 =Dict[k, v + 1]（无效语法）
        # <-- 错误3: 丢失 for k, v in extra.items() 子句
    return {**extra, 'sum': sum(items), 'count': len(items)}
    # <-- else 分支丢失 if-elif-else 结构
```

**问题分解（3 个子 bug）**:

#### Bug 8.1: lambda x: -x 错译为 lambda *args, **kwargs: None

原始 `lambda x: -x` 是单参数 lambda，反编译产出中错译为 `lambda *args, **kwargs: None`，参数和函数体完全丢失。

#### Bug 8.2: **{k: v + 1} 错译为 =Dict[k, v + 1]（无效语法）

原始 `**{k: v + 1}` 是 dict unpacking 在 call 中的关键字参数展开，反编译产出中错译为 `=Dict[k, v + 1]`，这是无效 Python 语法，导致反编译结果无法通过语法检查。

#### Bug 8.3: listcomp 丢失第二个 for 子句

原始 listcomp `[f(*x, **{k: v + 1}) for x in items for k, v in extra.items()]` 含两个 for 子句，反编译产出中只保留 `for x in items`，丢失 `for k, v in extra.items()` 子句。

**根因推测**: 反编译器在 if-elif-else 三分支含 *args / **kwargs 混合调用 + listcomp 内嵌 dict unpacking 时，dict unpacking 在 listcomp 上下文中的 AST 重建错乱，产生 `=Dict[k, v + 1]` 这种内部数据结构泄漏。R19 测过 `starred_call_in_if_cond.py`（if 条件含 *args），但未覆盖 listcomp 内嵌 **dict 场景。

---

### Bug 9: if-elif-else 三分支返回多元素 tuple → else 分支丢失结构，return 错译为只剩 genexp

**文件**: `test_adv20_tuple_return_in_branches.py`
**状态**: FAILED（嵌套 code object 不匹配: 62 vs 53）

**源码**:
```python
def f(flag, x):
    if flag == 'a':
        return (x, x + 1, x * 2, [x, x + 1], {'k': x})
    elif flag == 'b':
        return ((x, x + 1), (x + 2, x + 3), [x, x + 4])
    else:
        return ((), [], {}, {x, x + 1}, (x for x in range(3)))
```

**反编译结果**:
```python
def f(flag, x):
    if (flag == 'a'):
        return (x, x + 1, x * 2, [x, x + 1], {'k': x})
    elif (flag == 'b'):
        return ((x, x + 1), (x + 2, x + 3), [x, x + 4])
    return (x for x in range(3))
    # <-- else 分支丢失 if-elif-else 结构
    # <-- return 错译为只剩 genexp，丢失 (), [], {}, {x, x+1} 部分
```

**问题分解（2 个子 bug）**:

#### Bug 9.1: else 分支丢失 if-elif-else 结构（被错置到函数顶层）

原始 else 分支属于 if-elif-else 链的最后一支，反编译产出中 else 分支的 return 语句被错置到函数顶层，丢失 else 关键字和分支结构。

#### Bug 9.2: else 分支 return 错译为只剩 genexp，丢失前 4 个元素

原始 else 分支 `return ((), [], {}, {x, x + 1}, (x for x in range(3)))` 是 5 元素 tuple（含空 tuple、空 list、空 dict、set、genexp），反编译产出中错译为 `return (x for x in range(3))`，只保留最后一个 genexp 元素，前 4 个元素（(), [], {}, {x, x+1}）完全丢失。这是 tuple 字面量与 genexp 在 return 上下文中的歧义性导致的解析错误。

**字节码对比**: 原始 62 条 / 重编 53 条（少 9 条），主要因为 else 分支的 4 个字面量构建指令（BUILD_TUPLE 0 / BUILD_LIST 0 / BUILD_MAP 0 / BUILD_SET 2）全部丢失。

**根因推测**: 反编译器在 if-elif-else 三分支都返回多元素 tuple + 嵌套字面量（含 genexp）时，else 分支的 tuple 字面量与 genexp 在 return 上下文中的歧义性导致解析错误，把多元素 tuple 错译为单个 genexp。R19 测过 `comprehension_return_in_branches.py`（三分支各返回单个 comprehension），但未覆盖多元素 tuple + 嵌套字面量场景。

---

### Bug 10: if body 内 while + walrus + 嵌套 if-elif-else → while 末尾产生游离 next 引用

**文件**: `test_adv20_walrus_in_while_cond_nested_if.py`
**状态**: FAILED（嵌套 code object 不匹配: 53 vs 55）

**源码**:
```python
def f(items):
    if items:
        result = []
        it = iter(items)
        while (x := next(it, None)) is not None:
            if x > 0:
                result.append('pos')
            elif x < 0:
                result.append('neg')
            else:
                result.append('zero')
        return result
    return []
```

**反编译结果**:
```python
def f(items):
    if items:
        result = []
        it = iter(items)
        while (x := next(it, None)) is not None:
            if (x > 0):
                result.append('pos')
            elif (x < 0):
                result.append('neg')
            else:
                result.append('zero')
            next        # <-- 游离 next 引用!
        return result
    else:
        return []
```

**问题分解（2 个子 bug）**:

#### Bug 10.1: while 循环末尾产生游离 next 引用

原始 while 循环体内只有 if-elif-else 结构，反编译产出中 while 循环末尾产生游离 `next` 引用（一个独立的 Name 节点，作为表达式语句）。这是 walrus 表达式 `(x := next(it, None))` 中的 `next` 函数引用在循环归约过程中被重复生成。

#### Bug 10.2: 字节码指令数不匹配（53 vs 55，重编多 2 条）

重编指令比原始多 2 条，主要因为游离 `next` 引用产生的 LOAD_NAME next + POP_TOP 指令。

**根因推测**: 反编译器在 if body 内 while + walrus 在条件 + 嵌套 if-elif-else 时，walrus 表达式中的 `next` 函数引用在 while 循环归约过程中被重复生成，泄漏为循环末尾的游离表达式语句。R11 测过 `while_walrus_boolop.py`（while + walrus + boolop），但未覆盖 walrus 在 while 条件 + 嵌套 if-elif-else 场景。

---

### Bug 11: if body 内 while + yield + 嵌套 if-elif → 丢失末尾 return 语句

**文件**: `test_adv20_yield_in_while_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 51 vs 53）

**源码**:
```python
def f(flag, items):
    if flag:
        i = 0
        while i < len(items):
            x = items[i]
            if x > 0:
                yield x * 2
            elif x < 0:
                yield -x
            else:
                yield x
            i += 1
        return          # <-- 丢失!
    return              # <-- 丢失!
```

**反编译结果**:
```python
def f(flag, items):
    if flag:
        i = 0
        while i < len(items):
            x = items[i]
            if (x > 0):
                yield (x * 2)
            elif (x < 0):
                yield (-x)
            else:
                yield x
            i += 1
        # <-- 丢失 return!
    # <-- 丢失 return!
```

**问题分解（2 个子 bug）**:

#### Bug 11.1: if body 末尾 return 语句丢失（while 循环后的 return）

原始 if body 内 while 循环后有 `return` 语句（显式空 return），反编译产出中该 return 语句完全丢失。

#### Bug 11.2: 函数末尾 return 语句丢失（else 分支的 return）

原始 else 分支（隐式）有 `return` 语句，反编译产出中该 return 语句完全丢失。导致生成器函数在 if flag 为 False 的路径无显式 return。

**字节码对比**: 原始 51 条 / 重编 53 条（多 2 条），主要因为重编路径中 RETURN_CONST None 指令的位置和数量与原始不一致。

**根因推测**: 反编译器在生成器函数 if body 内 while + yield + 嵌套 if-elif 时，生成器函数的隐式/显式 return 语句在归约过程中被吞并。生成器函数的 RETURN_GENERATOR 指令和普通 return 的归约交互导致 return 语句丢失。R19 测过 `yield_in_elif_body.py`（elif body 内 yield），但未覆盖 if body 内 while + yield + 嵌套 if-elif 的生成器场景。

---

## 错误模式归类

### 模式 A: if-elif-else 整体退化为 ternary（2 个 bug）

- **Bug 1**: if-elif-else 三分支都含 assert + chained cmp → 退化为 ternary
- **Bug 5**: if-elif-else 三分支都含 for-else + break → 退化为 ternary

**共性**: 当 if-elif-else 三分支都含相同的复杂语句模式（assert+cmp / for-else+break）时，反编译器把 IfRegion 错合并为 TernaryRegion，三分支结构完全丢失。这是 R19 已知问题（assert_chained_cmp_in_if_body）的复发，说明 R19 修复未覆盖多分支场景。

### 模式 B: if-elif-else 三分支末位 else 分支结构丢失（2 个 bug）

- **Bug 8**: if-elif-else 三分支含 *args/**kwargs → else 分支丢失 if-elif-else 结构
- **Bug 9**: if-elif-else 三分支返回多元素 tuple → else 分支丢失 if-elif-else 结构

**共性**: 当 if-elif-else 三分支的 else 分支含复杂表达式（**dict unpacking / 多元素 tuple + genexp）时，else 分支被错置到函数顶层，丢失 else 关键字。

### 模式 C: 反编译结果产生无效语法/垃圾代码（3 个 bug）

- **Bug 7**: elif body 内嵌套 with + try + if-else → 产生 `None(None, None)` 垃圾代码
- **Bug 8**: if-elif-else 三分支含 *args/**kwargs → 产生 `=Dict[k, v + 1]` 垃圾代码
- **Bug 7**: elif body 内嵌套 with + try + if-else → try 块未关闭，语法错误

**共性**: 当 if-elif-else body 内含复杂嵌套结构（with + try / listcomp 内嵌 dict unpacking）时，反编译器内部数据结构（Dict 节点、None 调用）泄漏到输出，产生无效 Python 语法。

### 模式 D: 装饰器/metaclass 关键字参数丢失（2 个 bug）

- **Bug 2**: if body 内 class + metaclass= → metaclass 关键字参数丢失
- **Bug 3**: if body 内 class + __slots__ + 多装饰器 → @classmethod 错位到 __init__

**共性**: 当 if body 内 class 定义含 metaclass 关键字参数或多装饰器时，class AST 生成器对关键字参数和装饰器归属识别错乱。

### 模式 E: walrus/yield 在循环中产生游离引用或丢失 return（2 个 bug）

- **Bug 10**: if body 内 while + walrus + 嵌套 if-elif-else → while 末尾产生游离 next 引用
- **Bug 11**: if body 内 while + yield + 嵌套 if-elif → 丢失末尾 return 语句

**共性**: 当 if body 内 while 循环含 walrus 表达式或 yield 语句时，循环归约过程中 walrus 的函数引用泄漏为游离表达式，或 return 语句被吞并。

### 模式 F: comprehension 多 for + 多 if 嵌套结构错乱（1 个 bug）

- **Bug 4**: if-elif-else 三分支含 dictcomp 多 for + if → 多 for 合并为单 for 多变量解包

**共性**: 当 if-elif-else body 内含 comprehension 多 for + 多 if 过滤时，comprehension 生成器对多 for 嵌套结构处理错乱。

### 模式 G: 嵌套 try + raise from 块结构错位（1 个 bug）

- **Bug 6**: if body 内嵌套 try + raise from → 内层 except 错位，外层 except 丢失 return

**共性**: 当 if body 内含嵌套 try-except + raise from 时，内层 except 块被压缩为单行，外层 except 的 return 被吞并。

---

## 修复优先级建议

### P0（最高优先级，影响反编译结果可用性）

1. **Bug 7**（elif body 内嵌套 with + try + if-else → 语法错误）：反编译结果完全无法通过语法检查，影响可用性。建议优先修复 with 块 __exit__ 归约和 try 块 except 识别。
2. **Bug 8**（if-elif-else 三分支含 *args/**kwargs → 语法错误）：反编译结果完全无法通过语法检查，影响可用性。建议优先修复 listcomp 内嵌 dict unpacking 的 AST 重建。

### P1（高优先级，结构完全丢失）

3. **Bug 1**（if-elif-else 三分支都含 assert + chained cmp → 退化为 ternary）：R19 同类 bug 复发，需扩展 R19 修复到多分支场景。
4. **Bug 5**（if-elif-else 三分支都含 for-else + break → 退化为 ternary）：结构完全丢失，三个 for-else 逃出 if 分支。

### P2（中优先级，语义部分丢失）

5. **Bug 4**（if-elif-else 三分支含 dictcomp 多 for + if → 解包错误）：多 for 合并为单 for 多变量解包，语义改变。
6. **Bug 9**（if-elif-else 三分支返回多元素 tuple → else 分支丢失结构）：else 分支 return 错译为只剩 genexp。
7. **Bug 6**（if body 内嵌套 try + raise from → 内层 except 错位，外层 except 丢失 return）：外层 except 丢失 return 影响函数返回值。

### P3（中低优先级，关键字参数/装饰器丢失）

8. **Bug 2**（if body 内 class + metaclass= → metaclass 关键字参数丢失）：metaclass 关键字参数丢失，影响 class 元类型行为。
9. **Bug 3**（if body 内 class + __slots__ + 多装饰器 → @classmethod 错位到 __init__）：装饰器错位，影响方法类型。

### P4（低优先级，游离引用/return 丢失）

10. **Bug 10**（if body 内 while + walrus + 嵌套 if-elif-else → while 末尾产生游离 next 引用）：游离 next 引用不影响语义但影响代码质量。
11. **Bug 11**（if body 内 while + yield + 嵌套 if-elif → 丢失末尾 return 语句）：生成器函数末尾 return 丢失，影响生成器终止语义。

---

## 与 R19 基线对比

| 指标 | R19 基线 | R20 新增 | R20 总计（预估） |
|------|----------|----------|------------------|
| 测试文件数 | 804 (adv01-adv19) | +23 (adv20) | 827 |
| 失败（FAILED） | 35 | +11 | 46 |
| 通过（PASSED） | 760 | +11 | 771 |
| 跳过（SKIPPED） | 9 | +1 | 10 |

**新发现 11 个真实失败 + 27 个子 bug**，覆盖 7 类错误模式。R20 是 IF 区域最后一轮，发现的 bug 主要集中在：
1. if-elif-else 三分支同质复杂场景下的整体退化（Bug 1, 5）
2. else 分支结构丢失（Bug 8, 9）
3. 复杂嵌套结构（with+try / listcomp+dict unpacking）产生垃圾代码（Bug 7, 8）
4. class 高级特性（metaclass / 多装饰器）丢失（Bug 2, 3）
5. walrus/yield 在循环中的归约副作用（Bug 10, 11）
6. comprehension 多 for + 多 if 嵌套错乱（Bug 4）
7. 嵌套 try + raise from 块结构错位（Bug 6）

R20 测试覆盖了 R1-R19 未触及的 IF 区域模式，发现的 bug 为后续修复提供了明确的反编译器改进方向。
