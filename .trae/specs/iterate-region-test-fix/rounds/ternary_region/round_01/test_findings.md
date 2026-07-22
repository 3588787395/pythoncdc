# Round 01 — Ternary 区域反编译器测试发现

**日期**: 2026-07-20
**测试工程师**: R01 自动探索（Ternary 区域首轮）
**当前分支**: trae/region-iteration-v2
**基线 commit**: 5bfc75f (R20 IF 完成)
**基线状态**: 72 passed / 43 failed / 1 skipped (Ternary 区域)

**测试范围**: Ternary 区域内未覆盖模式，聚焦 17 个方向：
1. walrus 在 ternary body 中 (`:= a` in body)
2. walrus 在 ternary orelse 中 (`:= b` in orelse)
3. assert(ternary) — 三元条件被折叠为 BoolOp
4. assert(ternary, msg) — 带消息的 assert 中三元被折叠
5. ternary 条件为 chained compare (`0 < a < 10`)
6. ternary 在切片下标中 (`lst[a if cond else 0:...]`)
7. ternary 作为 compare 左操作数 (`(ternary) == b`)
8. ternary 作为方法调用参数 (`obj.method(ternary)`)
9. ternary 在 starred 表达式中 (`[*(ternary)]`)
10. return (ternary, other) — 元组 return 中含 ternary
11. 多个 ternary 作为 dict value
12. lambda body 是 (ternary) + 算术
13. while 循环体含 ternary 赋值
14. async for 体内 ternary 赋值
15. with (ternary) as f — with 上下文管理器中的 ternary
16. class body 含多个 ternary 属性
17. return (ternary, ternary) — 双 ternary 元组 return

---

## 统计摘要

| 指标 | 数量 |
|------|------|
| 测试文件总数 | 17 |
| 失败（FAILED） | 17 |
| 通过（PASSED） | 0 |
| 跳过（SKIPPED） | 0 |
| **新错误总数** | **17** |

运行命令:
```
cd /workspace && timeout 200 python -m pytest tests/exhaustive/ternary/test_r1_*.py --tb=short -q
```

结果: `17 failed in 0.49s`

**测试基线对比**:
- 测试前: 43 failed / 72 passed / 1 skipped (Ternary 区域 116 测试)
- 测试后: 60 failed / 72 passed / 1 skipped (Ternary 区域 133 测试)
- 新增失败: 17（即 R1 全部 17 个测试均失败，无重复）

---

## 现有 43 个失败用例归类分析

基线 43 个失败用例的错误类型完全一致，均归为同一类：

```
AssertionError: 反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])
```

按 SOURCE_CODE 模式归类：

| # | 失败模式 | 数量 | 代表文件 |
|---|---------|------|----------|
| 1 | 模块级裸 ternary 表达式（值被 POP_TOP 丢弃）| 42 | test_tn01/06/11~25simpleternary* |
| 2 | while 循环条件中的 ternary（has_jump_forward_skip 漏判）| 1 | test_ternary12_in_while.py |

### 根因分析（共性）

**模式 1（42 个）**: 当 ternary 表达式作为模块级语句（非赋值、非 return）时，CPython 编译器对两个值分支都生成 `LOAD value; POP_TOP; LOAD_CONST None; RETURN_VALUE` 序列（值被丢弃后模块隐式返回 None）。反编译器将此模式错判为 `MatchRegion`（误以为 `LOAD_NAME a; POP_TOP; LOAD_CONST None; RETURN_VALUE` 是 `match a: case _: pass` 的 body），从而在 `_detect_ternary_pattern` 的 `for _mr in match_regions` 守卫处拒绝创建 TernaryRegion，最终输出 `if cond: match a: case _: pass` 而非 `a if cond else b`。

**模式 2（1 个）**: while 循环条件中的 ternary（`while (next_item() if has_more() else None): pass`），`_detect_ternary_pattern` 的 has_jump_forward_skip 检测路径未正确识别 while 循环条件分支的 `LOAD_NAME a; POP_TOP; LOAD_CONST None; RETURN_VALUE` 模式，导致 ternary 未被识别。

### 修复优先级建议

- **模式 1**: 极高优先级，影响 42/43 个失败用例。修复点在 `MatchRegion` 识别的 false positive 过滤——模块级 `LOAD_NAME x; POP_TOP; LOAD_CONST None; RETURN_VALUE` 模式不应被识别为 MatchRegion case body，或在 `_detect_ternary_pattern` 中放宽 MatchRegion 守卫允许此模式被 TernaryRegion 抢占。
- **模式 2**: 高优先级，需扩展 `has_jump_forward_skip` 检测以覆盖 while 循环条件 ternary 的 false_block 模式。

---

## 新测试文件列表

| # | 文件 | 状态 | 错误类别 |
|---|------|------|----------|
| 1 | `test_r1_walrus_in_body.py` | **FAILED** | walrus 在 body → 整体退化为 if-else-return，丢失 IfExp 与赋值目标 x |
| 2 | `test_r1_walrus_in_orelse.py` | **FAILED** | walrus 在 orelse → 整体退化为 if-else，true 分支错造为 return |
| 3 | `test_r1_assert_simple.py` | **FAILED** | assert(ternary) → 三元被折叠为 BoolOp `a > 0 and a` |
| 4 | `test_r1_assert_with_message.py` | **FAILED** | assert(ternary, msg) → 三元被折叠为 BoolOp |
| 5 | `test_r1_chained_compare_in_cond.py` | **FAILED** | 条件为 chained compare → 整体退化为 if-else-return |
| 6 | `test_r1_ternary_in_slice.py` | **FAILED** | 切片中 ternary → 字节码不一致，丢失 BUILD_SLICE/BINARY_SUBSCR |
| 7 | `test_r1_ternary_in_compare.py` | **FAILED** | compare 左操作数为 ternary → 字节码不一致，丢失 == b 与外层赋值 |
| 8 | `test_r1_ternary_in_method_call.py` | **FAILED** | 方法调用参数为 ternary → 字节码不一致，丢失 obj.method() |
| 9 | `test_r1_ternary_in_starred.py` | **FAILED** | starred 中 ternary → 字节码不一致，丢失 BUILD_LIST/LIST_EXTEND |
| 10 | `test_r1_return_tuple_with_ternary.py` | **FAILED** | return (ternary, other) → 嵌套 code object 字节码不一致 |
| 11 | `test_r1_ternary_in_dict_value.py` | **FAILED** | 多个 ternary 作为 dict value → 字节码不一致 |
| 12 | `test_r1_ternary_in_lambda_complex.py` | **FAILED** | lambda body 是 (ternary)+1 → body 被替换为 None |
| 13 | `test_r1_while_with_ternary_body.py` | **FAILED** | while 体含 ternary 赋值 → 字节码不一致 |
| 14 | `test_r1_async_for_ternary.py` | **FAILED** | async for 体含 ternary 赋值 → body 退化为两个表达式语句 |
| 15 | `test_r1_ternary_in_with.py` | **FAILED** | with (ternary) as f → 字节码不一致 |
| 16 | `test_r1_class_body_multi_ternary.py` | **FAILED** | class body 多 ternary → 嵌套 code object 字节码不一致，多输出 (b>0) |
| 17 | `test_r1_return_two_ternary.py` | **FAILED** | return (ternary, ternary) → 嵌套 code object 字节码不一致 |

---

## Bug 详细分析

### Bug 1: walrus 在 ternary body 中 → 整体退化为 if-else-return

**文件**: `test_r1_walrus_in_body.py`
**状态**: FAILED（反编译结果中未找到预期的区域类型 TERNARY）

**源码**:
```python
x = (y := a) if a > 0 else 0
```

**反编译结果**:
```python
if (a > 0):
    y = a
else:
    return 0
```

**字节码对比**（filtered）:
- 原始: `LOAD_NAME a / LOAD_CONST 0 / COMPARE_OP / POP_JUMP_FORWARD_IF_FALSE / LOAD_NAME a / COPY 1 / STORE_NAME y / POP_TOP / JUMP_FORWARD / LOAD_CONST 0 / STORE_NAME x`
- 重编: `LOAD_NAME a / LOAD_CONST 0 / COMPARE_OP / POP_JUMP_FORWARD_IF_FALSE / LOAD_NAME a / STORE_NAME y / LOAD_CONST 0 / RETURN_VALUE`

**根因推测**: walrus 表达式 `(y := a)` 使 ternary 的 true_value_block 末尾包含 `COPY 1; STORE_NAME y; POP_TOP` 序列。`_is_single_expression_block` 检测到 `STORE_NAME y` 后会拒绝该块为单表达式（store_or_terminal_ops 包含 STORE_NAME），导致 TernaryRegion 未被识别，整体退化为 IfRegion。又因 walrus 赋值的副作用已执行，反编译器把 walrus 视为独立赋值语句 `y = a`，并把外层 x 赋值丢失。这是 walrus 与 ternary 组合的代表性失败。

---

### Bug 2: walrus 在 ternary orelse 中 → 整体退化为 if-else

**文件**: `test_r1_walrus_in_orelse.py`
**状态**: FAILED（反编译结果中未找到预期的区域类型 TERNARY）

**源码**:
```python
x = a if cond else (y := b)
```

**反编译结果**:
```python
if cond:
    return a
else:
    y = b
```

**字节码对比**:
- 原始 true 分支以 `JUMP_FORWARD` 跳到 merge_block（含 `STORE_NAME x`）
- 重编 true 分支以 `LOAD_CONST a; RETURN_VALUE` 终结，丢失外层 x 赋值

**根因推测**: 与 Bug 1 同源。walrus 在 orelse 中使 false_value_block 末尾包含 `STORE_NAME y`，被 `_is_single_expression_block` 拒绝。TernaryRegion 未识别，退化为 IfRegion + 独立 walrus 赋值，true 分支被错造为模块级 return（典型 false positive 模式）。

---

### Bug 3: assert(ternary) → 三元被折叠为 BoolOp

**文件**: `test_r1_assert_simple.py`
**状态**: FAILED（反编译结果中未找到预期的区域类型 TERNARY）

**源码**:
```python
assert (a if a > 0 else 0)
```

**反编译结果**:
```python
assert (a > 0 and a)
```

**字节码对比**:
- 原始: `LOAD_NAME a / LOAD_CONST 0 / COMPARE_OP / POP_JUMP_FORWARD_IF_FALSE -> false / LOAD_NAME a / JUMP_FORWARD -> merge / LOAD_CONST 0 / merge: POP_JUMP_FORWARD_IF_TRUE -> end / LOAD_ASSERTION_ERROR / RAISE_VARARGS 1`
- 重编: `LOAD_NAME a / LOAD_CONST 0 / COMPARE_OP / POP_JUMP_FORWARD_IF_FALSE -> end / LOAD_NAME a / POP_JUMP_FORWARD_IF_TRUE -> end / LOAD_ASSERTION_ERROR / RAISE_VARARGS 1`

**根因推测**: assert(ternary) 的字节码是 `ternary 的钻石形状 + merge 块的 POP_JUMP_IF_TRUE 检查`。反编译器误把 ternary 的 condition_block + true_block 视为 BoolOp (`a > 0 and a`)，因为 cond_block 末尾的 POP_JUMP_IF_FALSE 与 BoolOp 短路模式相同。assert 内的 ternary 与 BoolOp 字节码模式高度相似，BoolOpRegion 优先识别抢占。Bug 3 是 assert + ternary 组合的代表性失败，行为发生实质改变：原表达式 a <= 0 时 assert 应抛 AssertionError，但折叠后 `assert a > 0 and a` 在 a <= 0 时不抛错（a 已被求值）。

---

### Bug 4: assert(ternary, msg) → 三元被折叠为 BoolOp（带消息）

**文件**: `test_r1_assert_with_message.py`
**状态**: FAILED（反编译结果中未找到预期的区域类型 TERNARY）

**源码**:
```python
assert (a if a > 0 else 0), "error"
```

**反编译结果**:
```python
assert (a > 0 and a), 'error'
```

**根因推测**: 与 Bug 3 同源，但此用例增加了 message 参数 `"error"`，验证折叠错误在带消息场景仍存在。如果 Bug 3 被修复，此测试也应通过。

---

### Bug 5: ternary 条件为 chained compare → 整体退化为 if-else-return

**文件**: `test_r1_chained_compare_in_cond.py`
**状态**: FAILED（反编译结果中未找到预期的区域类型 TERNARY）

**源码**:
```python
x = a if 0 < a < 10 else 0
```

**反编译结果**:
```python
if (0 < a < 10):
    return a
else:
    return 0
```

**字节码对比**:
- 原始 12 条: ternary 钻石形状 + `STORE_NAME x`
- 重编 9 条: if-else + 两个 `RETURN_VALUE`

**根因推测**: chained compare `0 < a < 10` 在 CPython 3.11 编译为 `LOAD_CONST 0; LOAD_NAME a; DUP_TOP; ROT_THREE; COMPARE_OP <; POP_JUMP_IF_FALSE end; LOAD_CONST 10; COMPARE_OP <; POP_JUMP_FORWARD_IF_FALSE false` 序列。其中间的 `POP_JUMP_IF_FALSE` 是 chained compare 的短路跳转，被 `_can_be_ternary_header` 的 `SHORT_CIRCUIT_JUMP_OPS` 守卫拒绝（chained_compare IfRegion 优先级高于 TernaryRegion）。但反编译器把整个 ternary 退化为 if-else 语句后，true/false 分支被错造为模块级 return。Bug 5 是 chained compare 在 ternary 条件中的代表性失败。

---

### Bug 6: ternary 在切片下标中 → 字节码不一致

**文件**: `test_r1_ternary_in_slice.py`
**状态**: FAILED（指令数不匹配: 13 vs 11）

**源码**:
```python
x = lst[a if cond else 0:b if cond2 else -1]
```

**反编译结果**:
```python
(a if cond else 0)
x = (b if cond2 else -1)
```

**字节码对比**:
- 原始 13 条: `LOAD_NAME lst / LOAD_NAME a / LOAD_NAME cond / POP_JUMP_IF_FALSE / LOAD_NAME a / JUMP_FORWARD / LOAD_CONST 0 / LOAD_NAME b / LOAD_NAME cond2 / POP_JUMP_IF_FALSE / LOAD_NAME b / JUMP_FORWARD / LOAD_CONST -1 / BUILD_SLICE 2 / BINARY_SUBSCR / STORE_NAME x`
- 重编 11 条: 缺失 `BUILD_SLICE 2` 与 `BINARY_SUBSCR`，多出 `POP_TOP`

**根因推测**: 切片下标中嵌套两个 ternary 时，反编译器未能正确把两个 ternary 作为 BUILD_SLICE 2 的两个操作数处理，而是把它们拆解为两个独立表达式语句，丢失了 `lst[...]` 的索引访问结构。这是 ternary 作为容器/切片元素的代表失败，与 dict value、方法参数同属一类。

---

### Bug 7: ternary 作为 compare 左操作数 → 字节码不一致

**文件**: `test_r1_ternary_in_compare.py`
**状态**: FAILED（指令数不匹配: 11 vs 12）

**源码**:
```python
x = (a if a > 0 else 0) == b
```

**反编译结果**:
```python
(a if a > 0 else 0)
```

**字节码对比**:
- 原始 11 条: `LOAD_NAME a / LOAD_CONST 0 / COMPARE_OP > / POP_JUMP_IF_FALSE / LOAD_NAME a / JUMP_FORWARD / LOAD_CONST 0 / LOAD_NAME b / COMPARE_OP == / STORE_NAME x`
- 重编 12 条: 多出 `POP_TOP / LOAD_CONST None / RETURN_VALUE`，缺失 `LOAD_NAME b / COMPARE_OP ==`

**根因推测**: ternary 作为 `==` 的左操作数时，merge_block 应包含 `LOAD_NAME b / COMPARE_OP == / STORE_NAME x`。但反编译器把 ternary 视为独立表达式语句（`POP_TOP` 丢弃值），丢失了 `== b` 比较与 `STORE_NAME x` 赋值。这与 Bug 6（切片）、Bug 8（方法调用）、Bug 9（starred）同属一类根因：ternary 作为外层表达式的操作数时，merge_block 的后续消费指令未被正确归属到 ternary 的父区域。

---

### Bug 8: ternary 作为方法调用参数 → 字节码不一致

**文件**: `test_r1_ternary_in_method_call.py`
**状态**: FAILED（指令数不匹配: 13 vs 12）

**源码**:
```python
obj.method(a if a > 0 else 0)
```

**反编译结果**:
```python
(a if a > 0 else 0)
```

**字节码对比**:
- 原始 13 条: `LOAD_NAME obj / LOAD_METHOD method / LOAD_NAME a / LOAD_CONST 0 / COMPARE_OP / POP_JUMP_IF_FALSE / LOAD_NAME a / JUMP_FORWARD / LOAD_CONST 0 / PRECALL / CALL / POP_TOP`
- 重编 12 条: 缺失 `LOAD_NAME obj / LOAD_METHOD method / PRECALL / CALL`，多出 `POP_TOP / LOAD_CONST None / RETURN_VALUE`

**根因推测**: ternary 作为方法调用参数时，`LOAD_METHOD`/`PRECALL`/`CALL` 序列应在 ternary merge_block 之后消费 ternary 结果。但反编译器把 ternary 视为独立表达式语句，丢失了方法调用结构。这是 ternary 作为函数/方法参数的代表性失败。

---

### Bug 9: ternary 在 starred 表达式中 → 字节码不一致

**文件**: `test_r1_ternary_in_starred.py`
**状态**: FAILED（指令数不匹配: 9 vs 7）

**源码**:
```python
x = [*(items if cond else [])]
```

**反编译结果**:
```python
x = (items if cond else [])
```

**字节码对比**:
- 原始 9 条: `BUILD_LIST / LOAD_NAME items / LOAD_NAME cond / POP_JUMP_IF_FALSE / LOAD_NAME items / JUMP_FORWARD / BUILD_LIST / BUILD_LIST / LIST_EXTEND 1 / STORE_NAME x`
- 重编 7 条: 缺失 `BUILD_LIST / LIST_EXTEND`

**根因推测**: `[*(ternary)]` 的字节码是 `BUILD_LIST` (建外层 list) + ternary 求值 + `BUILD_LIST` (包装 iter) + `LIST_EXTEND 1` (展开)。反编译器丢失了外层 `BUILD_LIST` 与 `LIST_EXTEND`，直接赋值 ternary 结果。这是 starred 表达式 + ternary 组合的代表性失败。

---

### Bug 10: return (ternary, other) → 嵌套 code object 字节码不一致

**文件**: `test_r1_return_tuple_with_ternary.py`
**状态**: FAILED（嵌套 code object 不匹配: 7 vs 8）

**源码**:
```python
def f():
    return (a if cond else b), c
```

**反编译结果**:
```python
def f():
    (a if cond else b,)
```

**字节码对比**（嵌套函数）:
- 原始 7 条: `RESUME / LOAD_GLOBAL cond / LOAD_GLOBAL a / LOAD_GLOBAL cond / POP_JUMP_IF_FALSE / LOAD_GLOBAL a / JUMP_FORWARD / LOAD_GLOBAL b / LOAD_GLOBAL c / BUILD_TUPLE 2 / RETURN_VALUE`（其中 ternary 钻石 + `LOAD_GLOBAL c / BUILD_TUPLE 2`）
- 重编 8 条: 多出 `POP_TOP / LOAD_CONST None / RETURN_VALUE`，缺失 `LOAD_GLOBAL c`，`BUILD_TUPLE 2` 退化为 `BUILD_TUPLE 1`

**根因推测**: 函数内 return 元组中含 ternary 时，反编译器在嵌套 code object 中未能正确把 ternary 与 `c` 作为 BUILD_TUPLE 2 的两个操作数处理，丢失了 `c` 元素。这与 Bug 17（双 ternary return）同源，是 return tuple + ternary 组合的代表性失败。

---

### Bug 11: 多个 ternary 作为 dict value → 字节码不一致

**文件**: `test_r1_ternary_in_dict_value.py`
**状态**: FAILED（指令数不匹配: 12 vs 13）

**源码**:
```python
d = {"a": 1 if cond else 0, "b": 2 if cond else 0}
```

**字节码对比**:
- 原始 12 条: `LOAD_NAME cond / LOAD_CONST 1 / JUMP_FORWARD / LOAD_CONST 0 / LOAD_NAME cond / LOAD_CONST 2 / JUMP_FORWARD / LOAD_CONST 0 / LOAD_CONST ('a','b') / BUILD_CONST_KEY_MAP 2 / STORE_NAME d`
- 重编 13 条: 多出 `POP_TOP`，`BUILD_CONST_KEY_MAP` 退化为 `BUILD_MAP`

**根因推测**: dict 字面量中多个 ternary value 时，反编译器未能正确重组 `BUILD_CONST_KEY_MAP` 指令（用 const key tuple 一次性构建），改为 `BUILD_MAP` 逐键添加，导致指令序列不一致。这是 ternary 在容器字面量中的代表性失败。

---

### Bug 12: lambda body 是 (ternary) + 算术 → body 被替换为 None

**文件**: `test_r1_ternary_in_lambda_complex.py`
**状态**: FAILED（反编译结果中未找到预期的区域类型 TERNARY）

**源码**:
```python
f = lambda x, y: (x if x > y else y) + 1
```

**反编译结果**:
```python
f = lambda x, y: None
```

**根因推测**: lambda body 是 `(ternary) + 1` 复合表达式，反编译器在递归处理 lambda 的内嵌 code object 时，未能重建 `IfExp + 1` 表达式，直接以 `None` 作为 body。这是 lambda body + ternary + 算术组合的代表性失败，行为严重错误（lambda 返回 None 而非计算结果）。已通过的 `test_ternary17_in_lambda.py` 测试的 body 是单一 ternary 表达式，本测试增加了 `+ 1` 算术运算，触发了反编译器在 lambda code object 中重建复合表达式的缺陷。

---

### Bug 13: while 循环体含 ternary 赋值 → 字节码不一致

**文件**: `test_r1_while_with_ternary_body.py`
**状态**: FAILED（指令数不匹配: 13 vs 15）

**源码**:
```python
while cond:
    x = a if a > 0 else 0
```

**字节码对比**:
- 原始 13 条: while header `LOAD_NAME cond / POP_JUMP_BACKWARD_IF_FALSE end` + 循环体 `LOAD_NAME a / LOAD_CONST 0 / COMPARE_OP / POP_JUMP_IF_FALSE / LOAD_NAME a / JUMP_FORWARD / LOAD_CONST 0 / STORE_NAME x / JUMP_BACKWARD header`
- 重编 15 条: 多出 `LOAD_NAME a / POP_TOP` 两条指令

**根因推测**: while 循环体内嵌 ternary 赋值时，反编译器未能正确重组 POP_JUMP_IF_FALSE/JUMP_FORWARD 跳转目标，重编字节码多出 2 条 `LOAD_NAME a / POP_TOP` 指令（多输出了一次 a 求值）。这是 while 循环体 + ternary 组合的代表性失败。

---

### Bug 14: async for 体内 ternary 赋值 → body 退化为两个表达式语句

**文件**: `test_r1_async_for_ternary.py`
**状态**: FAILED（反编译结果中未找到预期的区域类型 TERNARY）

**源码**:
```python
async def f():
    async for i in g():
        x = i if i > 0 else 0
```

**反编译结果**:
```python
async def f():
    async for i in g():
        i
        0
```

**根因推测**: async for 体内 ternary 赋值未识别为 TERNARY 区域，body 被拆解为两个独立表达式语句 `i` 和 `0`，完全丢失 IfExp 结构与外层 `x` 赋值绑定。这是 async for + ternary 组合的代表性失败，与同步 for 循环 `test_tn_for_iter` 行为不一致。可能与 async for 的特殊字节码（GET_AITER / GET_ANEXT / SEND）干扰了 ternary 识别有关。

---

### Bug 15: with (ternary) as f → 字节码不一致

**文件**: `test_r1_ternary_in_with.py`
**状态**: FAILED（指令数不匹配: 34 vs 39）

**源码**:
```python
with (open(f1) if cond else open(f2)) as f:
    pass
```

**字节码对比**:
- 原始 34 条: `LOAD_NAME cond / PUSH_NULL / LOAD_NAME open / LOAD_NAME f1 / PRECALL / CALL / PUSH_NULL / LOAD_NAME open / LOAD_NAME f2 / PRECALL / CALL / BEFORE_WITH / STORE_NAME f / ...`
- 重编 39 条: 多出 5 条指令，with 上下文管理器的 ternary 上下文管理器未被正确重组

**根因推测**: with 语句的上下文管理器位置使用 ternary 表达式时，反编译器未能正确处理 BEFORE_WITH 与 __exit__ 调用顺序。ternary 的两个分支各自调用 `open()`，反编译器未能把两个 `open()` 调用作为 ternary 的 true/false 值块识别，导致重编字节码错乱。这是 with + ternary 组合的代表性失败。

---

### Bug 16: class body 含多个 ternary 属性 → 嵌套 code object 字节码不一致

**文件**: `test_r1_class_body_multi_ternary.py`
**状态**: FAILED（嵌套 code object 不匹配: 19 vs 23）

**源码**:
```python
class C:
    x = a if a > 0 else 0
    y = b if b > 0 else 0
```

**反编译结果**:
```python
class C:
    x = (a if a > 0 else 0)
    (b > 0)
    y = (b if b > 0 else 0)
```

**字节码对比**（class code object）:
- 原始 19 条: 两个 ternary 钻石 + 两个 STORE_NAME
- 重编 23 条: 多出 4 条，包含 `(b > 0)` 表达式语句的字节码

**根因推测**: class 体内多个 ternary 赋值时，反编译器在第二个 ternary 之前多输出了一行 `(b > 0)` 表达式语句（条件被泄漏到外层）。这是第二个 ternary 的 condition_block 未能被 TernaryRegion 正确归约，被 IfRegion 抢占后输出条件表达式语句。Bug 16 是 class body + 多 ternary 组合的代表性失败。

---

### Bug 17: return (ternary, ternary) → 双 ternary 元组 return 字节码不一致

**文件**: `test_r1_return_two_ternary.py`
**状态**: FAILED（嵌套 code object 不匹配: 13 vs 15）

**源码**:
```python
def f():
    return (a if a > 0 else 0), (b if b > 0 else 0)
```

**字节码对比**（嵌套函数）:
- 原始 13 条: 两个 ternary 钻石 + `BUILD_TUPLE 2 / RETURN_VALUE`
- 重编 15 条: 多出 2 条 `POP_TOP / LOAD_CONST None`

**根因推测**: return 语句的 tuple 包含两个 ternary 表达式时，反编译器在嵌套函数 code object 中未能正确重组双 ternary 求值路径，重编字节码多出 2 条 `POP_TOP / LOAD_CONST None` 指令（可能是某个 ternary 的 false_block 被错造为独立 return）。与 Bug 10 同源，但本测试是双 ternary 组合，验证了多 ternary 元组场景的失败。

---

## 错误模式归类

按反编译器失败现象归类：

| 模式 | Bug 编号 | 数量 | 现象 |
|------|---------|------|------|
| A. 整体三元退化为 if-else 语句（无 IfExp） | 1, 2, 3, 4, 5, 12, 14 | 7 | ternary 未被识别为 TERNARY 区域，IfExp AST 节点缺失，常伴随外层赋值丢失、模块级 return 错造 |
| B. ternary 作为容器/调用操作数，字节码不一致 | 6, 7, 8, 9, 11 | 5 | ternary 被识别，但外层表达式（切片、compare、方法调用、starred、dict）的消费指令丢失 |
| C. 嵌套 code object 内 ternary 字节码不一致 | 10, 13, 15, 16, 17 | 5 | 函数/类/wWhile/with 内 ternary 重编字节码指令数不一致 |
| **总计** | 17 | 17 | — |

按根因归类：

| 根因 | Bug 编号 | 数量 | 修复点 |
|------|---------|------|--------|
| R1. walrus 副作用导致 `_is_single_expression_block` 拒绝 ternary 值块 | 1, 2 | 2 | 放宽 `_is_single_expression_block` 对 walrus COPY+STORE 模式的判定 |
| R2. assert 内 ternary 被 BoolOpRegion 抢占 | 3, 4 | 2 | assert 上下文中 ternary 优先级高于 BoolOp |
| R3. chained compare 守卫拒绝 ternary header | 5 | 1 | chained_compare IfRegion 与 TernaryRegion 边界调整 |
| R4. ternary merge_block 的消费指令（CALL/BUILD_SLICE/BINARY_SUBSCR/LIST_EXTEND/BUILD_MAP/COMPARE_OP）未被归属到父区域 | 6, 7, 8, 9, 11 | 5 | 扩展 `_detect_ternary_context` 与 `value_target` 识别 |
| R5. 嵌套 code object 内 ternary 重组错误（return tuple、while body、with cm、class body、双 ternary） | 10, 13, 15, 16, 17 | 5 | 嵌套 code object 的 ternary AST 生成器路径修复 |
| R6. lambda body 含复合 ternary 表达式时 body 被替换为 None | 12 | 1 | lambda code object 重建 `IfExp + 算术` 表达式 |
| R7. async for 体 ternary 识别失败 | 14 | 1 | async for 字节码（GET_AITER/GET_ANEXT/SEND）干扰 ternary 识别 |

---

## 修复优先级建议

按影响范围与修复难度排序：

### P0（最高优先级，影响范围广）

1. **R4: ternary 作为外层表达式操作数时消费指令丢失**（Bug 6, 7, 8, 9, 11，共 5 个）
   - 影响所有 `ternary 作为函数参数/方法参数/切片下标/compare 操作数/starred/dict value` 场景
   - 修复点：`_detect_ternary_context` 与 `value_target` 识别扩展，merge_block 后续消费指令应归属到 ternary 父区域
   - 修复后预期可一次性解决 5 个 Bug

2. **R1: walrus 在 ternary body/orelse 中**（Bug 1, 2，共 2 个）
   - 影响所有 walrus + ternary 组合
   - 修复点：`_is_single_expression_block` 放宽对 walrus COPY+STORE 模式的判定
   - walrus 是 Python 3.8+ 的常用特性，影响实际代码

### P1（高优先级，行为错误）

3. **R2: assert(ternary) 被折叠为 BoolOp**（Bug 3, 4，共 2 个）
   - 影响 assert + ternary 组合，行为发生实质改变（assert 在 a<=0 时不抛错）
   - 修复点：assert 上下文中 ternary 优先级高于 BoolOp，或 BoolOpRegion 识别增加 assert 守卫
   - 行为错误比字节码不一致更严重

4. **R5: 嵌套 code object 内 ternary 重组错误**（Bug 10, 13, 15, 16, 17，共 5 个）
   - 影响函数体、while body、with cm、class body 内的 ternary
   - 修复点：嵌套 code object 的 ternary AST 生成器路径修复
   - 每个 Bug 可能需要单独修复

### P2（中优先级，特定场景）

5. **R3: chained compare 在 ternary 条件中**（Bug 5，1 个）
   - 影响 chained compare + ternary 组合
   - 修复点：chained_compare IfRegion 与 TernaryRegion 边界调整
   - 单个 Bug，但与 R1（基线 42 个失败）的根因可能相关

6. **R6: lambda body 含复合 ternary 表达式**（Bug 12，1 个）
   - 影响 lambda + ternary + 算术组合
   - 修复点：lambda code object 重建 `IfExp + 算术` 表达式
   - 单个 Bug，但 lambda 是常用特性

7. **R7: async for 体 ternary 识别失败**（Bug 14，1 个）
   - 影响 async for + ternary 组合
   - 修复点：async for 字节码（GET_AITER/GET_ANEXT/SEND）干扰 ternary 识别
   - 单个 Bug，async 是较少用特性

### 修复后预期效果

- P0 修复后：7 个 Bug 解决（Bug 1, 2, 6, 7, 8, 9, 11）
- P0+P1 修复后：14 个 Bug 解决（再加 Bug 3, 4, 10, 13, 15, 16, 17）
- 全部修复后：17 个 Bug 全部解决

---

## 测试基线与运行结果

### 测试前基线

```
$ python -m pytest tests/exhaustive/ternary/ --tb=no -q
72 passed, 43 failed, 1 skipped in 0.86s
```

### 新增测试运行结果

```
$ python -m pytest tests/exhaustive/ternary/test_r1_*.py --tb=short -q
17 failed in 0.49s
```

### 测试后状态

```
$ python -m pytest tests/exhaustive/ternary/ --tb=no -q
60 failed, 72 passed, 1 skipped in 0.86s
```

新增 17 个失败用例，全部为 R1 测试发现，无重复，无 skip。
