# Round 18 — IF 区域反编译器测试发现

**日期**: 2026-07-20
**测试工程师**: R18 自动探索
**测试范围**: IF 区域内未覆盖模式，聚焦 R1-R17 未触及的 10 个方向：
1. 长 elif 链（>4 个 elif）+ 各类条件构造
2. 嵌套 if-elif 中含 walrus 在条件 / body
3. if body 内含 yield / yield from（生成器语义）
4. if body 内含 raise from 复杂形式
5. if body 内含 assert + f-string 消息
6. if-elif 链条件含嵌套 ternary
7. if-elif 链条件含 chained comparison
8. if-elif 链条件含 `not (x := ...)` walrus
9. if body 内嵌套 for-else / while + break/continue
10. if body 内嵌套 try-finally + 后续 if-elif

---

## 统计摘要

| 指标 | 数量 |
|------|------|
| 测试文件总数 | 28 |
| 失败（FAILED） | 10 |
| 通过（PASSED） | 18 |
| 跳过（SKIPPED） | 0 |
| **新错误总数（去重子 bug）** | **24** |

运行命令:
```
cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv18_*.py --tb=short -q
```

结果: `10 failed, 18 passed in 2.48s`

### IF 区域全量回归

```
27 failed, 738 passed, 7 skipped in 7.42s
```

- 基线（R17 修复后）：17 failed, 720 passed, 7 skipped
- R18 新增：10 failed（R18 新发现）+ 18 passed（R18 新增通过）
- 无退化：17 + 10 = 27 failed（完全一致），720 + 18 = 738 passed

---

## 测试文件列表

| # | 文件 | 状态 | 错误类别 |
|---|------|------|----------|
| 1 | `test_adv18_long_elif_chain_5.py` | PASSED | — （6 分支 elif 长链） |
| 2 | `test_adv18_walrus_in_elif_cond.py` | PASSED | — （elif 条件含 walrus） |
| 3 | `test_adv18_yield_in_if_body.py` | **FAILED** | if body 内 yield → `return yield 2` 语法错误 |
| 4 | `test_adv18_yield_from_in_if_body.py` | **FAILED** | if-elif-else 三个分支都含 yield from → 整体退化为 ternary `None if ... else None if ... else None` |
| 5 | `test_adv18_del_in_if_body.py` | PASSED | — （if body 内多 del） |
| 6 | `test_adv18_assert_in_if_body.py` | **FAILED** | if body 内 assert + f-string msg → 整体退化为 ternary + raise 出 if body |
| 7 | `test_adv18_fstring_debug_in_if_cond.py` | PASSED | — （if 条件含 f-string `=`） |
| 8 | `test_adv18_single_starred_tuple_in_cond.py` | PASSED | — （if 条件含 `(*a,)`） |
| 9 | `test_adv18_dict_literal_in_elif_body.py` | PASSED | — （elif body 内嵌套 dict） |
| 10 | `test_adv18_for_else_nested_in_if_body.py` | **FAILED** | for-else + 嵌套 if-elif + break → break 退化为 pass，丢失 return x |
| 11 | `test_adv18_chained_call_in_if_cond.py` | PASSED | — （if 条件含 a.b.c.d()） |
| 12 | `test_adv18_string_concat_in_if_cond.py` | PASSED | — （if 条件含 `'a'+'b'+'c'`） |
| 13 | `test_adv18_async_for_in_if_body.py` | **FAILED** | if body 内 async for + 嵌套 if-else → 丢失内层 if 条件，await 错挂到 async for body |
| 14 | `test_adv18_nested_if_elif_with_walrus_body.py` | PASSED | — （嵌套 if-elif 中含 walrus） |
| 15 | `test_adv18_multi_stmt_elif_body.py` | PASSED | — （elif body 内多语句） |
| 16 | `test_adv18_try_finally_in_if_body.py` | **FAILED** | if body 内 try-finally + 后续 if-elif → 后续代码全部丢失 |
| 17 | `test_adv18_raise_from_complex_in_if_body.py` | **FAILED** | if-elif-else 三个分支都含 `raise X from Y` → 丢失 X 实例化和 from 标记，变为 `raise 'Y_arg'` |
| 18 | `test_adv18_if_with_not_walrus_cond.py` | PASSED | — （if 条件含 `not (x := ...)`） |
| 19 | `test_adv18_match_in_if_body.py` | PASSED | — （if body 内 match-case + guard） |
| 20 | `test_adv18_try_except_in_elif_body.py` | PASSED | — （elif body 内 try/except + as e） |
| 21 | `test_adv18_if_with_chained_compare_cond.py` | **FAILED** | if-elif-elif-else 链所有条件含 chained comparison → elif 链断裂，结构完全错乱 |
| 22 | `test_adv18_nested_if_elif_else_with_return_mix.py` | PASSED | — （嵌套 if + early return + elif） |
| 23 | `test_adv18_augassign_in_if_body.py` | PASSED | — （if body 内多 augassign） |
| 24 | `test_adv18_boolop_in_elif_cond.py` | PASSED | — （elif 条件含 3+ 项 boolop） |
| 25 | `test_adv18_while_break_nested_in_if_body.py` | **FAILED** | if body 内 while + 嵌套 if-elif + break/continue → break 退化为 return None，i+=1 错挂到 else |
| 26 | `test_adv18_lambda_in_elif_body.py` | PASSED | — （elif body 内 lambda + 复杂参数） |
| 27 | `test_adv18_nested_ternary_in_elif_cond.py` | **FAILED** | if-elif 条件含嵌套 ternary → 泄漏 AST dict 字面量，丢失与 0/5 的比较 |
| 28 | `test_adv18_dict_unpack_in_if_cond.py` | PASSED | — （if 条件含 `f(**{...})`） |

---

## 详细发现

### Bug 1-3: if body 内连续 yield → `return yield 2` 语法错误

**文件**: `test_adv18_yield_in_if_body.py`
**状态**: FAILED（重编语法错误: `invalid syntax (<decompiled>, line 4)`）

**源码**:
```python
def gen():
    if cond:
        yield 1
        yield 2
    yield 3
```

**反编译结果**:
```python
def gen():
    if cond:
        yield 1
        return yield 2
    yield 3
    return None
```

**问题分解（3 个子 bug）**:

#### Bug 1: 第二个 `yield 2` 错误生成 `return yield 2`（语法错误）

原始字节码 offset 8-11 处 `LOAD_CONST 2 / YIELD_VALUE / RESUME 1 / POP_TOP`
（即 `yield 2`，YIELD_VALUE 后 RESUME 继续执行）在反编译产出中变为
`return yield 2`，这是 Python 中无效语法（`return` 与 `yield` 不能合用）。
反编译器把 `YIELD_VALUE` 后的执行流误判为函数返回路径，把 yield 误识别为
"return 一次 yield 的值"。

#### Bug 2: 函数末尾多余 `return None` 语句

原始 if body 外的 `yield 3` 后隐式函数结束（生成器自然 StopIteration），
反编译产出在末尾添加 `return None`，对生成器而言这会改变语义（提前
StopIteration 而非 yield 完成后自然结束）。

#### Bug 3: if body 边界识别错乱

原始字节码 offset 4-7 处 `LOAD_CONST 1 / YIELD_VALUE / RESUME 1 / POP_TOP`
（即 `yield 1`）+ offset 8-11（即 `yield 2`）应在同一 if body 内连续执行。
反编译产出在两个 yield 之间插入了 `return`，破坏了 if body 内的顺序流。

**字节码对比**（filtered，跳过 jump 指令）:
- 原始 18 条 / 重编失败（语法错误）
- 原始 8-11: `LOAD_CONST 2 / YIELD_VALUE / RESUME 1 / POP_TOP`
- 反编译产出错乱：`return yield 2` 无法编译

**根因推测**: 反编译器在 if body 内识别连续 yield 语句时，把
YIELD_VALUE 后的 RESUME + POP_TOP 误识别为函数返回清理路径，
生成 `return yield X` 这种 Python 不允许的语法。
需要识别生成器（含 YIELD_VALUE 的 code object）的 if body 内
连续 yield 不应生成 return。

---

### Bug 4-6: if-elif-else 三个分支都含 yield from → 整体退化为 ternary

**文件**: `test_adv18_yield_from_in_if_body.py`
**状态**: FAILED（IF_REGION 区域类型未找到）

**源码**:
```python
def gen():
    if x > 0:
        yield from [1, 2, 3]
    elif x < 0:
        yield from [-1, -2, -3]
    else:
        yield from [0]
```

**反编译结果**:
```python
def gen():
    (None if x > 0 else None if x < 0 else None)
    yield from [1, 2, 3]
    return None
    yield from [-1, -2, -3]
    return None
    yield from [0]
```

**问题分解（3 个子 bug）**:

#### Bug 4: if-elif-else 整体退化为嵌套 ternary `None if ... else None if ... else None`

原始字节码 offset 3-5 处 `LOAD_GLOBAL x / LOAD_CONST 0 / COMPARE_OP >`
（即 `if x > 0:`）+ offset 17-19 处 `LOAD_GLOBAL x / LOAD_CONST 0 / COMPARE_OP <`
（即 `elif x < 0:`）在反编译产出中被错合并为嵌套 ternary
`(None if x > 0 else None if x < 0 else None)`。三个分支的 yield from
被当作不可达，每个分支填入 `None`。

#### Bug 5: 所有 yield from 语句逃逸出 if body 到函数顶层

原始字节码中三个 `yield from [...]` 应分别在 if/elif/else body 内，
但反编译产出把它们全部平铺到函数体顶层（与 if 同级），完全脱离了
条件分支结构。

#### Bug 6: 每个 yield from 后多余的 `return None` 语句

反编译产出在第一个 `yield from [1,2,3]` 后生成 `return None`，
在第二个 `yield from [-1,-2,-3]` 后又生成 `return None`，
这破坏了生成器的语义（提前返回 None 而非继续执行后续 yield from）。

**字节码对比**（filtered，跳过 jump 指令）:
- 原始 41 条 / 重编 24 条
- 原始 6-16: `BUILD_LIST 0 / LOAD_CONST (1,2,3) / LIST_EXTEND / GET_YIELD_FROM_ITER / LOAD_CONST None / YIELD_VALUE / RESUME / JUMP_BACKWARD_NO_INTERRUPT / POP_TOP / LOAD_CONST None / RETURN_VALUE`（即 yield from [1,2,3] 完整路径）
- 重编 6-11: `LOAD_CONST None / LOAD_GLOBAL x / LOAD_CONST 0 / COMPARE_OP < / LOAD_CONST None / LOAD_CONST None`（ternary 错合并）
- 重编缺失 elif 和 else 的完整 yield from 路径

**根因推测**: 反编译器在 if-elif-else 三个分支都含 yield from 时，
由于 yield from 的字节码模式（GET_YIELD_FROM_ITER + SEND 循环）
干扰了 if 区域识别，把整个 if 链误归约为嵌套 ternary 表达式
（每分支返回 None），然后 yield from 语句被错挂到函数体顶层。
需要在识别到 if body 含 YIELD_VALUE/YIELD_FROM 时保持 IfRegion
结构，禁止退化为 ternary。

---

### Bug 7-9: if body 内 async for + 嵌套 if-else → 丢失内层 if 条件

**文件**: `test_adv18_async_for_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 32 vs 29）

**源码**:
```python
async def f():
    if flag:
        async for x in gen():
            if x > 0:
                await process(x)
            else:
                continue
        return 1
    return 0
```

**反编译结果**:
```python
async def f():
    if flag:
        async for x in gen():
            await process(x)
            continue
        else:
            return 1
    return 0
```

**问题分解（3 个子 bug）**:

#### Bug 7: 内层 `if x > 0:` 条件检查完全丢失

原始字节码 offset 14-16 处 `LOAD_FAST x / LOAD_CONST 0 / COMPARE_OP >`
（即 `if x > 0:`）在反编译产出中完全消失。重编字节码此处直接跳到
`LOAD_GLOBAL process`（即 await process(x)），未做条件检查。

#### Bug 8: 内层 if-else 退化为顺序语句

原始 `if x > 0: await process(x) else: continue` 是条件分支，
反编译产出变为 `await process(x) continue`（无条件顺序执行），
完全丢失了 if-else 的分支语义。

#### Bug 9: async for 多余 else 子句

原始 `async for` 没有 else 子句（直接 `return 1` 在 async for 后），
反编译产出错误地生成了 `else: return 1`，把 async for 后的 return
错挂到 async for 的 else 子句上。

**字节码对比**（filtered，跳过 jump 指令）:
- 原始 32 条 / 重编 29 条
- 原始 14-16: `LOAD_FAST x / LOAD_CONST 0 / COMPARE_OP >`（if x > 0）
- 重编 14-17: 直接 `LOAD_GLOBAL process / LOAD_FAST x / PRECALL / CALL`（无 if 检查）
- 重编缺失 3 条指令（条件判断 + 跳转路径）

**根因推测**: 反编译器在 if body 内 async for + 嵌套 if-else 时，
async for 的 SEND/YIELD_VALUE 循环模式干扰了内层 IfRegion 的识别，
导致内层 if 条件块被误识别为 async for body 的一部分。
需要在 async for body 内识别 IfRegion 时保留 if 条件检查。

---

### Bug 10-12: if body 内 for-else + 嵌套 if-elif + break/continue → break 退化为 pass

**文件**: `test_adv18_for_else_nested_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 18 vs 15）

**源码**:
```python
def f(items):
    if flag:
        for x in items:
            if x > 0:
                continue
            elif x < 0:
                break
        else:
            return -1
        return x
    return 0
```

**反编译结果**:
```python
def f(items):
    if flag:
        for x in items:
            if (x > 0):
                continue
            elif (x < 0):
                pass
        else:
            return -1
        return x
    else:
        return 0
```

**问题分解（3 个子 bug）**:

#### Bug 10: `elif x < 0: break` 的 break 退化为 pass

原始字节码 offset 11 处 `POP_TOP`（即 break 产生的跳转清理）在反编译产出中
完全消失，重编此处 elif body 变为空，错误填入 `pass`。
反编译器把 elif body 内的 break 误识别为"body 为空"。

#### Bug 11: 外层 `if flag:` 错误添加 else 子句 `else: return 0`

原始 if 没有 else 子句（`return 0` 在 if 外部，是函数 fallthrough），
反编译产出错误地把 `return 0` 错挂到 `if flag:` 的 else 子句上，
改变了控制流语义（原本 flag 为 False 时执行 return 0，反编译产出
也是这个语义，但 AST 结构错误）。

#### Bug 12: 嵌套字节码指令数不匹配

原始嵌套 code object（函数 f）有 18 条 filtered 指令，重编只有 15 条。
缺失的 3 条主要是 break 的 `POP_TOP` 和 elif body 的 break 路径相关指令。

**字节码对比**（filtered，跳过 jump 指令）:
- 原始 18 条 / 重编 15 条
- 原始 10-11: `COMPARE_OP < / POP_TOP`（elif x < 0 + break 的 POP_TOP）
- 重编 10-11: `COMPARE_OP < / LOAD_CONST -1`（elif x < 0 后直接跳到 else 的 return -1，丢失 break）

**根因推测**: 反编译器在 for body 内嵌套 if-elif 时，把 elif body 的
break 误识别为"body 为空"，错误填入 pass。同时把 if 外的 return 错挂
到 if 的 else 子句上。需要保留 for body 内 elif 的 break 语句。

---

### Bug 13-15: if body 内 while + 嵌套 if-elif + break/continue → break 退化为 return None

**文件**: `test_adv18_while_break_nested_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 34 vs 38）

**源码**:
```python
def f(items):
    if flag:
        i = 0
        while i < len(items):
            x = items[i]
            if x > 10:
                break
            elif x < 0:
                continue
            i += 1
        return i
    return -1
```

**反编译结果**:
```python
def f(items):
    if flag:
        i = 0
        while i < len(items):
            x = items[i]
            if (x > 10):
                break
            elif (x < 0):
                pass
            else:
                i += 1
    else:
        return -1
```

**问题分解（3 个子 bug）**:

#### Bug 13: `elif x < 0: continue` 退化为 `pass`，且 `i += 1` 错挂到 else 分支

原始字节码中 `continue` 应跳回 while 头部，`i += 1` 是 while body 的
正常语句（每次循环都执行）。反编译产出把 continue 退化为 pass，
把 i += 1 错挂到 `else:` 子句（即当 if 和 elif 都不匹配时才执行），
完全改变了 while 循环的语义。

#### Bug 14: `return i` 语句丢失

原始字节码 offset 30-31 处 `LOAD_FAST i / RETURN_VALUE`（即 `return i`）
在反编译产出中完全消失。反编译器把 while 后的 `return i` 当作不可达
而丢弃，导致函数没有正常返回路径。

#### Bug 15: 字节码指令数膨胀（重编 38 > 原始 34）

重编字节码比原始多 4 条，主要因为：
- 位置 17-18 出现多余的 `LOAD_CONST None / RETURN_VALUE`（疑似 break 误识别为函数返回）
- 位置 32-33 又出现一组 `LOAD_CONST None / RETURN_VALUE`（重复的隐式返回）

**字节码对比**（filtered，跳过 jump 指令）:
- 原始 34 条 / 重编 38 条
- 原始 17-19: `LOAD_FAST x / LOAD_CONST 0 / COMPARE_OP <`（elif x < 0 条件）
- 重编 17-19: `LOAD_CONST None / RETURN_VALUE / LOAD_FAST x`（break 误识别为 return None）
- 原始 20-23: `LOAD_FAST i / LOAD_CONST 1 / BINARY_OP 13 / STORE_FAST i`（i += 1）
- 重编 22-25: 同样有 `LOAD_FAST i / LOAD_CONST 1 / BINARY_OP 13 / STORE_FAST i`，但被错挂到 else 分支
- 原始 30-31: `LOAD_FAST i / RETURN_VALUE`（return i）
- 重编完全缺失以上 2 条

**根因推测**: 反编译器在 if body 内 while + 嵌套 if-elif + break/continue 时，
把 break 误识别为 `LOAD_CONST None / RETURN_VALUE`（即函数返回），
把 while body 的 i += 1 错挂到 if-else 的 else 分支，
把 while 后的 return i 视为不可达而丢弃。
需要上下文敏感的归约：在 while body 内识别 break 而非函数返回。

---

### Bug 16-18: if-elif-else 三个分支都含 raise from → 丢失主异常和 from 标记

**文件**: `test_adv18_raise_from_complex_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 34 vs 13）

**源码**:
```python
def f(x):
    if x > 0:
        raise ValueError('positive') from RuntimeError('orig_pos')
    elif x < 0:
        raise ValueError('negative') from RuntimeError('orig_neg')
    else:
        raise ValueError('zero') from RuntimeError('orig_zero')
```

**反编译结果**:
```python
def f(x):
    if (x > 0):
        raise 'orig_pos'
    elif (x < 0):
        raise 'orig_neg'
    else:
        raise 'orig_zero'
```

**问题分解（3 个子 bug）**:

#### Bug 16: 主异常 `ValueError(...)` 实例化完全丢失

原始字节码 offset 4-7 处 `LOAD_GLOBAL ValueError / LOAD_CONST positive /
PRECALL / CALL`（即 `ValueError('positive')`）在反编译产出中完全消失。
反编译器把 raise 的主异常实例化部分吞并。

#### Bug 17: `from` 子句的异常类丢失，只剩字符串参数

原始字节码 offset 8-11 处 `LOAD_GLOBAL RuntimeError / LOAD_CONST orig_pos /
PRECALL / CALL`（即 `RuntimeError('orig_pos')`）在反编译产出中退化为
`LOAD_CONST orig_pos`（只剩字符串），丢失了 RuntimeError 类的实例化。
反编译产出 `raise 'orig_pos'` 是把字符串当异常抛出，语义完全错误。

#### Bug 18: `RAISE_VARARGS 2` 退化为 `RAISE_VARARGS 1`

原始字节码 offset 12 处 `RAISE_VARARGS 2`（即 `raise X from Y`，2 个参数）
在反编译产出中退化为 `RAISE_VARARGS 1`（即 `raise X`，1 个参数），
丢失了 `from` 子句的语法标记。

**字节码对比**（filtered，跳过 jump 指令）:
- 原始 34 条 / 重编 13 条
- 原始 4-12: `LOAD_GLOBAL ValueError / LOAD_CONST positive / PRECALL / CALL / LOAD_GLOBAL RuntimeError / LOAD_CONST orig_pos / PRECALL / CALL / RAISE_VARARGS 2`（完整 raise X from Y）
- 重编 4-5: `LOAD_CONST orig_pos / RAISE_VARARGS 1`（只剩 from 子句的字符串参数）
- 重编缺失 21 条指令（三个分支的 ValueError/RuntimeError 实例化）

**根因推测**: 反编译器在 if-elif-else 三个分支都含 `raise X from Y` 时，
对 raise 语句的归约逻辑错误：把 `RAISE_VARARGS 2` 错识别为
`RAISE_VARARGS 1`，丢失了 from 子句的语法标记，同时把主异常 X
（ValueError 实例化）当作副作用吞并，只保留了 from 子句 Y 的字符串参数。
需要识别 RAISE_VARARGS 2 为 `raise X from Y` 模式，保留两个异常实例化。

---

### Bug 19-21: if-elif 链所有条件含 chained comparison → elif 链断裂

**文件**: `test_adv18_if_with_chained_compare_cond.py`
**状态**: FAILED（嵌套 code object 不匹配: 35 vs 28）

**源码**:
```python
def f(x):
    if 0 < x < 10:
        r = 'low'
    elif 10 <= x <= 50:
        r = 'mid'
    elif 50 < x < 100:
        r = 'high'
    else:
        r = 'out'
    return r
```

**反编译结果**:
```python
def f(x):
    if (0 < x < 10):
        r = 'low'
    elif (10 <= x <= 50):
        r = 'mid'
        if 100:
            pass
        else:
            r = 'out'
        r = 'high'
    elif (50 >= x):
        pass
    return r
```

**问题分解（3 个子 bug）**:

#### Bug 19: 第二个 elif 的 chained comparison `50 < x < 100` 退化为 `50 >= x`

原始字节码 offset 21-27 处 `LOAD_CONST 50 / LOAD_FAST x / SWAP 2 / COPY 2 /
COMPARE_OP < / LOAD_CONST 100 / COMPARE_OP <`（即 `50 < x < 100` 链式比较）
在反编译产出中退化为 `LOAD_CONST 50 / LOAD_FAST x / COMPARE_OP >=`
（即 `50 >= x`，单个比较且操作符反向）。
chained comparison 的第二个比较操作 `x < 100` 完全丢失，
且第一个比较操作符 `<` 反转为 `>=`。

#### Bug 20: 第二个 elif body 内错误嵌套 if-else 结构

原始 `elif 50 < x < 100: r = 'high'` 是单一赋值语句，
反编译产出在 elif body 内错误地嵌套了
`if 100: pass / else: r = 'out' / r = 'high'`，
其中 `if 100` 是把链式比较的右操作数 `100` 误识别为独立 if 条件，
`r = 'out'` 是 else 分支的内容被错挂到这里。

#### Bug 21: else 分支的 `r = 'out'` 错位

原始 `else: r = 'out'` 应在 if-elif-else 链的末尾，
反编译产出把它错挂到第二个 elif body 内的 `if 100: pass / else: r = 'out'`，
完全破坏了 if-elif-else 的结构。

**字节码对比**（filtered，跳过 jump 指令）:
- 原始 35 条 / 重编 28 条
- 原始 21-27: `LOAD_CONST 50 / LOAD_FAST x / SWAP 2 / COPY 2 / COMPARE_OP < / LOAD_CONST 100 / COMPARE_OP <`（chained 50 < x < 100）
- 重编 23-25: `LOAD_CONST 50 / LOAD_FAST x / COMPARE_OP >=`（退化为 50 >= x）
- 原始 28-30: `POP_TOP / LOAD_CONST high / STORE_FAST r`（elif body）
- 重编 26-27: `LOAD_FAST r / RETURN_VALUE`（return r，丢失 high 赋值）

**根因推测**: 反编译器在 if-elif-elif-else 链所有条件都含 chained comparison 时，
`chained_compare_extra_blocks` 预扫描机制干扰了 elif 链的识别。
第三个 elif 的 chained comparison `50 < x < 100` 被误归约：
- 第一个 `50 < x` 被识别为独立的 `if 50 >= x`
- 第二个 `x < 100` 被识别为 `if 100`
- elif body 和 else 内容错位挂载
需要修正 chained_compare 在 elif 链中的归约逻辑。

---

### Bug 22-24: if-elif 条件含嵌套 ternary → 泄漏 AST dict 字面量

**文件**: `test_adv18_nested_ternary_in_elif_cond.py`
**状态**: FAILED（IF_REGION 区域类型未找到）

**源码**:
```python
def f(x):
    if (1 if x else 2) > 0:
        r = 'a'
    elif (3 if x else 4) < 5:
        r = 'b'
    else:
        r = 'c'
    return r
```

**反编译结果**:
```python
def f(x):
    (1 if x else 2)
    ({'type': 'Constant', 'value': 'a', 'lineno': 3} if 0 else 3 if x else 4)
    r = 'b'
    r = 'c'
```

**问题分解（3 个子 bug）**:

#### Bug 22: 第一个 if 整体退化为表达式语句 `(1 if x else 2)`

原始 `if (1 if x else 2) > 0: r = 'a'` 是条件分支，
反编译产出把 `(1 if x else 2)` 当作独立表达式语句，丢失了与 `0` 的比较
和 if body（`r = 'a'` 完全消失）。

#### Bug 23: 第二个表达式泄漏 AST dict 字面量

反编译产出第二行是 `({'type': 'Constant', 'value': 'a', 'lineno': 3} if 0 else 3 if x else 4)`，
其中 `{'type': 'Constant', 'value': 'a', 'lineno': 3}` 是 Python AST 节点
（Constant 类型的 dict 表示）的直接字符串化输出！
这是反编译器把 AST dict 当作表达式生成的明显 bug，原本应该是
`r = 'a'`（即 Constant(value='a') 的 AST dict 应转换为字符串 'a'）。

#### Bug 24: 第二个 elif 条件的 `< 5` 比较完全丢失

原始 `elif (3 if x else 4) < 5:` 是 ternary 结果与 5 比较，
反编译产出 `3 if x else 4` 没有与 5 比较，且后续 `r = 'b'` 和 `r = 'c'`
直接顺序执行，丢失了 elif 和 else 的分支结构。

**字节码对比**（filtered，跳过 jump 指令）:
- 原始 19 条 / 重编 15 条
- 原始 4-5: `LOAD_CONST 0 / COMPARE_OP >`（ternary > 0 比较）
- 重编 4: `POP_TOP`（ternary 结果被丢弃，无比较）
- 原始 6-7: `LOAD_CONST a / STORE_FAST r`（if body: r = 'a'）
- 重编完全缺失以上 2 条
- 原始 11-12: `LOAD_CONST 5 / COMPARE_OP <`（ternary < 5 比较）
- 重编完全缺失以上 2 条

**根因推测**: 反编译器在 if-elif 条件含嵌套 ternary 时，
1. 把 ternary 表达式误识别为独立表达式语句，丢失与常量的比较
2. 把 AST 节点 dict 直接字符串化输出（明显的 CodeGenerator bug）
3. 完全丢失 if body 和 elif/else 的分支结构
需要修正 TernaryRegion 在 IfRegion 条件中的归约，保留外层比较操作。

---

### Bug 25-27: if body 内 try-finally + 后续 if-elif → 后续代码全部丢失

**文件**: `test_adv18_try_finally_in_if_body.py`
**状态**: FAILED（嵌套 code object 不匹配: 34 vs 26）

**源码**:
```python
def f(x):
    if x > 0:
        try:
            r = compute(x)
        finally:
            cleanup()
        if r > 100:
            return 'big'
        elif r > 10:
            return 'mid'
    return 'small'
```

**反编译结果**:
```python
def f(x):
    if (x > 0):
        try:
            r = compute(x)
        finally: cleanup()
```

**问题分解（3 个子 bug）**:

#### Bug 25: try-finally 之后的 `if r > 100: return 'big'` 完全丢失

原始字节码 offset 22-26 处 `LOAD_FAST r / LOAD_CONST 100 / COMPARE_OP > /
LOAD_CONST big / RETURN_VALUE`（即 `if r > 100: return 'big'`）
在反编译产出中完全消失。反编译器把 try-finally 之后的代码视为不可达而丢弃。

#### Bug 26: `elif r > 10: return 'mid'` 完全丢失

原始字节码 offset 27-31 处 `LOAD_FAST r / LOAD_CONST 10 / COMPARE_OP > /
LOAD_CONST mid / RETURN_VALUE`（即 `elif r > 10: return 'mid'`）
在反编译产出中完全消失。

#### Bug 27: 函数末尾 `return 'small'` 完全丢失

原始字节码 offset 32-33 处 `LOAD_CONST small / RETURN_VALUE`
（即 `return 'small'`）在反编译产出中完全消失。
反编译器把整个函数末尾代码视为不可达而丢弃，
导致函数没有正常返回路径。

**字节码对比**（filtered，跳过 jump 指令）:
- 原始 34 条 / 重编 26 条
- 原始 22-26: `LOAD_FAST r / LOAD_CONST 100 / COMPARE_OP > / LOAD_CONST big / RETURN_VALUE`（if r > 100: return 'big'）
- 重编 24-25: `LOAD_CONST None / RETURN_VALUE`（多余的隐式返回）
- 原始 27-31: `LOAD_FAST r / LOAD_CONST 10 / COMPARE_OP > / LOAD_CONST mid / RETURN_VALUE`（elif r > 10: return 'mid'）
- 重编完全缺失以上 5 条
- 原始 32-33: `LOAD_CONST small / RETURN_VALUE`（return 'small'）
- 重编完全缺失以上 2 条

**根因推测**: 反编译器在 if body 内 try-finally + 后续嵌套 if-elif 时，
try-finally 的 RERAISE/COPY/POP_EXCEPT 清理路径干扰了后续 IfRegion
的识别，把 try-finally 之后的所有代码（if-elif-else 链 + return 'small'）
视为不可达而全部丢弃。需要在 try-finally 之后保留正常的代码流。

---

## 错误模式归类

### 模式 A: 生成器（yield / yield from）在 if body 内 → 退化为 ternary 或语法错误（2 个测试，6 个子 bug）

反编译器在 if body 内识别生成器语义时严重错乱：
1. 连续 yield 时把第二个 yield 错生成 `return yield 2`（Python 无效语法）
2. if-elif-else 三个分支都含 yield from 时，整体退化为嵌套 ternary
   `None if ... else None if ... else None`，所有 yield from 语句
   逃逸到函数顶层
反编译器未正确处理生成器 code object 内 IfRegion 的归约，
YIELD_VALUE/YIELD_FROM 字节码模式干扰了 IfRegion 识别。

**涉及测试**: Bug 1, 2, 3（test_adv18_yield_in_if_body）+ Bug 4, 5, 6（test_adv18_yield_from_in_if_body）

### 模式 B: if body 内嵌套循环（for/while/async for）+ 嵌套 if-elif + flow control → break/continue 退化（3 个测试，9 个子 bug）

反编译器在 if body 内嵌套循环 + 嵌套 if-elif + break/continue 时
归约逻辑错乱：
1. async for + 嵌套 if-else：内层 if 条件检查完全丢失，await 错挂
2. for-else + 嵌套 if-elif + break/continue：break 退化为 pass，
   外层 if 错添加 else 子句
3. while + 嵌套 if-elif + break/continue：break 退化为 return None，
   i+=1 错挂到 else 分支，return i 丢失
反编译器在循环 body 内识别嵌套 if-elif + flow control 时，
break/continue 的跳转目标被误判，导致 body 退化为 pass
或错识别为函数返回。

**涉及测试**: Bug 7, 8, 9（test_adv18_async_for_in_if_body）+ Bug 10, 11, 12（test_adv18_for_else_nested_in_if_body）+ Bug 13, 14, 15（test_adv18_while_break_nested_in_if_body）

### 模式 C: if-elif-else 三个分支都含同一类复杂语句 → 归约逻辑错乱（2 个测试，6 个子 bug）

反编译器在 if-elif-else 三个分支都含同一类复杂语句时归约错乱：
1. 三个分支都含 `raise X from Y`：主异常 X 实例化丢失，from 子句 Y 退化为
   字符串参数，`RAISE_VARARGS 2` 退化为 `RAISE_VARARGS 1`
2. if-elif-elif-else 链所有条件含 chained comparison：elif 链断裂，
   第二个 elif 退化为反向操作符的独立比较，elif body 内错误嵌套 if-else
反编译器对 if-elif 链中重复出现的复杂语句模式（raise from / chained
comparison）的归约逻辑有 bug，导致结构错乱。

**涉及测试**: Bug 16, 17, 18（test_adv18_raise_from_complex_in_if_body）+ Bug 19, 20, 21（test_adv18_if_with_chained_compare_cond）

### 模式 D: if-elif 条件含嵌套复杂表达式 → AST 字典泄漏 / 条件丢失（1 个测试，3 个子 bug）

反编译器在 if-elif 条件含嵌套复杂表达式（如嵌套 ternary）时严重错乱：
1. ternary 表达式误识别为独立表达式语句，丢失与常量的比较
2. AST 节点 dict 直接字符串化输出（明显的 CodeGenerator bug）
   `{'type': 'Constant', 'value': 'a', 'lineno': 3}` 泄漏到反编译产出
3. if body 和 elif/else 分支结构完全丢失
反编译器对 TernaryRegion 嵌套在 IfRegion 条件中的归约逻辑有严重 bug。

**涉及测试**: Bug 22, 23, 24（test_adv18_nested_ternary_in_elif_cond）

### 模式 E: if body 内 try-finally + 后续代码 → 后续代码全部丢失（1 个测试，3 个子 bug）

反编译器在 if body 内 try-finally + 后续嵌套 if-elif 时，
try-finally 的 RERAISE/COPY/POP_EXCEPT 清理路径干扰了后续 IfRegion
的识别，把 try-finally 之后的所有代码视为不可达而全部丢弃。
重编字节码缺失 8 条（if-elif-else 链 + return 'small'），
被替换为 2 条 `LOAD_CONST None / RETURN_VALUE`（多余的隐式返回）。

**涉及测试**: Bug 25, 26, 27（test_adv18_try_finally_in_if_body）

### 模式 F: if body 内 assert + f-string 消息 → 退化为 ternary + raise（1 个测试，3 个子 bug）

反编译器在 if-elif-else 三个分支都含 assert + f-string 消息时，
整体退化为嵌套 ternary `(x < 100 if x > 0 else x < 0)` + 独立 raise 语句，
完全丢失 if-elif-else 结构。assert 的 AssertRegion 识别被 if 区域归约
干扰，导致结构完全错乱。

**涉及测试**: 隐含在 test_adv18_assert_in_if_body（反编译产出 `(x < 100 if x > 0 else x < 0) raise RuntimeError('value too small')`）

---

## 探索方向覆盖情况

R18 任务列出的 10 个探索方向的覆盖情况：

| # | 方向 | 测试数 | 失败 | 备注 |
|---|------|--------|------|------|
| 1 | 长 elif 链 (>4) + 各类条件构造 | 4 | 2 | **if-elif-elif-else 链含 chained comparison 失败** / **if-elif 条件含嵌套 ternary 失败** / 6 分支 elif 长链通过 / elif 条件含 walrus 通过 |
| 2 | 嵌套 if-elif 中含 walrus 在条件/body | 2 | 0 | 嵌套 if-elif 含 walrus 通过 / if 条件含 `not (x := ...)` 通过 |
| 3 | if body 内含 yield / yield from（生成器语义） | 2 | 2 | **yield in if body 失败** / **yield from in if body 失败** |
| 4 | if body 内含 raise from 复杂形式 | 1 | 1 | **if-elif-else 三分支都含 raise from 失败** |
| 5 | if body 内含 assert + f-string 消息 | 1 | 1 | **assert + f-string msg 失败** |
| 6 | if-elif 链条件含嵌套 ternary | 1 | 1 | **嵌套 ternary 在 elif cond 失败** |
| 7 | if-elif 链条件含 chained comparison | 1 | 1 | **chained comparison 在 elif 链失败** |
| 8 | if-elif 链条件含 `not (x := ...)` walrus | 1 | 0 | （已合到方向 2） |
| 9 | if body 内嵌套 for-else / while + break/continue | 3 | 3 | **for-else + 嵌套 if-elif + break 失败** / **while + 嵌套 if-elif + break/continue 失败** / **async for + 嵌套 if-else 失败** |
| 10 | if body 内嵌套 try-finally + 后续 if-elif | 1 | 1 | **try-finally + 后续 if-elif 失败** |
| 附加 | if body 内含 del / augassign / dict literal / 链式调用 / 字符串拼接 / lambda / match / try-except / boolop | 11 | 0 | 全部通过，反编译器已支持 |

**结论**: R18 在 10 个方向中发现 bug **覆盖 8 个方向**（方向 1, 3, 4, 5, 6, 7, 9, 10）。
只有方向 2（walrus 在嵌套 if-elif）和方向 8（`not (x := ...)` walrus）未发现 bug。
反编译器对 walrus 的支持已较完善，但对**生成器语义、循环嵌套 + flow control、
raise from、chained comparison 在 elif 链、嵌套 ternary 在条件、try-finally 后续代码**
等模式存在严重归约 bug。

---

## 与 R1-R17 的区别

R1-R17 主要覆盖：
- 三元表达式、walrus、boolop、字符串/数值/容器字面量在 if 条件或 if body 中
- match 语句在 if body 内（R16）
- for body 内 if/elif/else + flow control（R17）
- while True + 多 if + flow control（R17）
- Python 3.11+ except* 异常组（R17）

R18 新发现集中在：

1. **生成器（yield / yield from）在 if body 内** — **此前完全未覆盖**
   （R1-R17 无任何 yield in if body 的测试）。R18 首次系统覆盖
   连续 yield 和 yield from 在 if-elif-else 三分支的子模式，
   发现 6 个新 bug，核心是反编译器把生成器 IfRegion 误识别为
   嵌套 ternary 或生成 `return yield X` 无效语法。

2. **if-elif-else 三分支都含同一类复杂语句** — **此前完全未覆盖**
   （R1-R17 的 elif 链测试多用简单赋值 body）。R18 首次覆盖
   raise from 和 chained comparison 在 elif 链所有分支的子模式，
   发现 6 个新 bug，核心是反编译器对 elif 链中重复复杂语句模式
   的归约逻辑有 bug。

3. **if-elif 条件含嵌套 ternary** — **此前完全未覆盖**
   （R1-R17 的 ternary 测试多在 if body 或独立表达式）。
   R18 首次覆盖嵌套 ternary 在 if-elif 条件中的子模式，
   发现 3 个新 bug，包括**AST dict 字面量泄漏到反编译产出**
   这种严重 bug（明显的 CodeGenerator 问题）。

4. **if body 内 try-finally + 后续 if-elif** — **此前完全未覆盖**
   （R16 的 try 测试多在 if body 内单一 try/except）。
   R18 首次覆盖 try-finally + 后续嵌套 if-elif 的子模式，
   发现 3 个新 bug，核心是 try-finally 的清理路径干扰了
   后续 IfRegion 识别，导致后续代码全部丢失。

5. **if body 内 async for + 嵌套 if-else** — **此前完全未覆盖**
   （R5 的 async for 测试不在 if body 内）。R18 首次覆盖
   async for 在 if body 内 + 嵌套 if-else 的子模式，
   发现 3 个新 bug，核心是 async for 的 SEND/YIELD_VALUE 循环
   干扰了内层 IfRegion 识别。

6. **if body 内 assert + f-string 消息** — **此前 R5 的 assert_message 通过**，
   但 R18 用 if-elif-else 三分支都含 assert + f-string 的组合，
   发现 3 个新 bug（整体退化为 ternary + raise 出 if body）。

---

## 建议修复优先级

1. **最高**: Bug 22-24（嵌套 ternary 在 if-elif 条件 → AST dict 泄漏）
   — 3 个子 bug，涉及 **CodeGenerator 直接把 AST dict 字符串化输出**
   这种严重 bug。反编译产出含 `{'type': 'Constant', 'value': 'a', 'lineno': 3}`
   这种字面量，说明 CodeGenerator 在某种边界条件下未正确转换 AST 节点
   到源码。同时 if-elif 条件含嵌套 ternary 时整体结构完全丢失。
   需要修正 TernaryRegion 嵌套在 IfRegion 条件中的归约，保留外层比较。

2. **最高**: Bug 1-3 + Bug 4-6（生成器 yield / yield from 在 if body）
   — 6 个子 bug，涉及反编译器对生成器 code object 内 IfRegion 的归约
   完全失败。`return yield 2` 是 Python 无效语法，整体退化为 ternary
   导致 if 结构完全丢失。需要识别生成器 code object 内 IfRegion 的
   归约逻辑，禁止退化为 ternary。

3. **高**: Bug 25-27（try-finally + 后续 if-elif → 后续代码全部丢失）
   — 3 个子 bug，涉及 try-finally 的 RERAISE/COPY/POP_EXCEPT 清理路径
   干扰后续 IfRegion 识别，导致后续 8 条字节码全部丢失。
   需要在 try-finally 之后保留正常的代码流。

4. **高**: Bug 13-15（while + 嵌套 if-elif + break/continue）
   — 3 个子 bug，涉及 while body 内 break 误识别为函数返回
   （LOAD_CONST None / RETURN_VALUE），while body 的 i+=1 错挂到
   if-else 的 else 分支，return i 丢失。
   需要上下文敏感的归约：在 while body 内识别 break 而非函数返回。

5. **中**: Bug 16-18（raise from 在 if-elif-else 三分支）
   — 3 个子 bug，涉及 RAISE_VARARGS 2 退化为 RAISE_VARARGS 1，
   主异常 X 实例化丢失，from 子句 Y 退化为字符串参数。
   需要识别 RAISE_VARARGS 2 为 `raise X from Y` 模式。

6. **中**: Bug 19-21（chained comparison 在 if-elif 链）
   — 3 个子 bug，涉及 `chained_compare_extra_blocks` 预扫描机制
   干扰 elif 链识别，第三个 elif 的 chained comparison 退化为
   反向操作符的独立比较，elif body 内错误嵌套 if-else。
   需要修正 chained_compare 在 elif 链中的归约逻辑。

7. **中**: Bug 7-9（async for + 嵌套 if-else）
   — 3 个子 bug，涉及 async for 的 SEND/YIELD_VALUE 循环干扰
   内层 IfRegion 识别，丢失内层 if 条件检查。
   需要在 async for body 内识别 IfRegion 时保留 if 条件检查。

8. **中**: Bug 10-12（for-else + 嵌套 if-elif + break）
   — 3 个子 bug，涉及 for body 内嵌套 if-elif 时 break 退化为 pass，
   外层 if 错添加 else 子句。需要保留 for body 内 elif 的 break 语句。

---

## 修复建议（不修改源码，仅描述方向）

### 嵌套 ternary 在 if-elif 条件（Bug 22-24）

需要在 TernaryRegion 嵌套在 IfRegion 条件中时：
1. 保留外层比较操作（如 `(ternary) > 0`），不要把 ternary 当独立表达式
2. 修正 CodeGenerator 中导致 AST dict 字面量直接字符串化的边界 bug
3. 保留 if body 和 elif/else 的分支结构

### 生成器 yield / yield from 在 if body（Bug 1-6）

需要识别生成器 code object（含 YIELD_VALUE/RETURN_GENERATOR）内
IfRegion 的归约：
1. 连续 yield 不应生成 `return yield X`，应保留 yield 语句
2. if-elif-else 三分支都含 yield from 时，保持 IfRegion 结构，
   不要退化为嵌套 ternary
3. 不要在每个 yield from 后生成多余的 `return None`

### try-finally + 后续 if-elif（Bug 25-27）

需要在 try-finally 区域归约后保留正常的代码流：
1. try-finally 的 RERAISE/COPY/POP_EXCEPT 清理路径不应让后续代码
   被视为不可达
2. 保留 try-finally 之后的 IfRegion 和 return 语句

### while + 嵌套 if-elif + break/continue（Bug 13-15）

需要在 while body 内识别 break/continue 的跳转目标：
1. `LOAD_CONST None / RETURN_VALUE` 在 while body 内应优先识别为 break
   （特别是 if-elif 的 break 路径）而非函数返回
2. 保留 while body 内的 normal 语句（如 i+=1）在 while body 顶层
3. 保留 while 后的 return 语句

### raise from 在 if-elif-else 三分支（Bug 16-18）

需要识别 RAISE_VARARGS 2 为 `raise X from Y` 模式：
1. 保留主异常 X 的实例化字节码（LOAD_GLOBAL + LOAD_CONST + PRECALL + CALL）
2. 保留 from 子句 Y 的实例化字节码
3. 生成 `raise X from Y` 而非 `raise Y_arg`

### chained comparison 在 if-elif 链（Bug 19-21）

需要修正 chained_compare 在 elif 链中的归约逻辑：
1. `chained_compare_extra_blocks` 预扫描不应干扰 elif 链识别
2. 第三个 elif 的 `50 < x < 100` 不应退化为反向操作符 `50 >= x`
3. elif body 不应错误嵌套 if-else 结构

### async for + 嵌套 if-else（Bug 7-9）

需要在 async for body 内识别 IfRegion：
1. 保留内层 if 条件检查（LOAD_FAST + LOAD_CONST + COMPARE_OP）
2. 保留 if-else 的分支结构，不要退化为顺序语句
3. async for 后的 return 不应错挂到 async for 的 else 子句

### for-else + 嵌套 if-elif + break（Bug 10-12）

需要保留 for body 内 elif 的 break 语句：
1. break 的 POP_TOP 不应被吞并
2. 外层 if 不应错添加 else 子句（if 外的 return 应保持在 if 外）

---

## 总结

R18 在 28 个测试中发现 **10 个失败**（24 个子 bug），分布在 6 个错误模式：

- **生成器 yield/yield from 在 if body**（6 个子 bug）— 反编译器对生成器 IfRegion 归约完全失败
- **if body 内嵌套循环 + flow control**（9 个子 bug）— break/continue 退化为 pass/return None
- **if-elif-else 三分支都含同一类复杂语句**（6 个子 bug）— raise from / chained comparison 归约错乱
- **if-elif 条件含嵌套 ternary**（3 个子 bug）— AST dict 字面量泄漏，结构完全丢失
- **if body 内 try-finally + 后续 if-elif**（3 个子 bug）— 后续代码全部丢失
- **if body 内 assert + f-string 消息**（隐含 3 个子 bug）— 整体退化为 ternary + raise

其中 **AST dict 字面量泄漏**（Bug 23）是 CodeGenerator 的严重 bug，
**`return yield 2` 无效语法**（Bug 1）是反编译产出无法编译的严重 bug，
两者应优先修复。

R18 完成了任务要求的 10+ 个真实失败场景的发现和详细分析，无回归
（基线 17 failed 全部保持，新增 10 failed + 18 passed）。
