# Round 15 — IF 区域反编译器测试发现

**日期**: 2026-07-18
**测试工程师**: R15 自动探索
**测试范围**: IF 区域内嵌套其他语句（三元表达式在 if 体内作赋值右值的子结构、
async with 在 if 体内、elif 测试条件为三元、walrus 绑定三元等）

---

## 统计摘要

| 指标 | 数量 |
|------|------|
| 测试文件总数 | 15 |
| 失败（FAILED） | 13 |
| 跳过（SKIPPED，反编译产出非法语法） | 2 |
| 通过（PASSED） | 0 |
| **新错误总数** | **15** |

运行命令:
```
cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv15_*.py --tb=short -q
```

结果: `13 failed, 2 skipped in 1.20s`

---

## 测试文件列表

| # | 文件 | 状态 | 错误类别 |
|---|------|------|----------|
| 1 | `test_adv15_async_with_pass.py` | SKIPPED | async with body `pass` → `break`（非法语法） |
| 2 | `test_adv15_async_with_multi_as.py` | SKIPPED | async with 多 ctx + as 绑定错乱 |
| 3 | `test_adv15_ternary_dict_value_body.py` | FAILED | 字典 value 为三元 → 字典字面量丢失 |
| 4 | `test_adv15_ternary_dict_key_body.py` | FAILED | 字典 key 为三元 → 字典字面量丢失 |
| 5 | `test_adv15_ternary_call_star_body.py` | FAILED | `f(*(三元))` → 丢失星号，CALL_FUNCTION_EX 变 CALL |
| 6 | `test_adv15_ternary_slice_in_body.py` | FAILED | 切片下/上界为三元 → 切片结构丢失 |
| 7 | `test_adv15_ternary_elif_test.py` | FAILED | elif 条件为三元 → 分解为多层 elif 链 |
| 8 | `test_adv15_complex_body_ternary.py` | FAILED | if 体内三元赋值后续语句丢失 |
| 9 | `test_adv15_ternary_in_tuple_unpack.py` | FAILED | 元组解包右值为三元 → 解包结构破坏 |
| 10 | `test_adv15_walrus_ternary_cond.py` | FAILED | walrus 绑定三元作 if 条件 → if 语句丢失 |
| 11 | `test_adv15_nested_if_ternary_body.py` | FAILED | 嵌套 if 内三元赋值 → 内层 if 提升丢失 |
| 12 | `test_adv15_ternary_each_branch.py` | FAILED | if/elif/else 每分支三元赋值 → 合并为嵌套三元 |
| 13 | `test_adv15_ternary_in_chain_compare_body.py` | FAILED | 链式比较中间操作数为三元 → 链式丢失 |
| 14 | `test_adv15_ternary_for_iter_body.py` | FAILED | for 的 iterable 为三元 → 三元重复求值 |
| 15 | `test_adv15_walrus_in_ternary_body.py` | FAILED | walrus 绑定三元后运算 → 后续运算丢失 |

---

## 详细发现

### Bug 1: async with body `pass` 被反编译为 `break`（SKIPPED — 非法语法）

**文件**: `test_adv15_async_with_pass.py`
**状态**: SKIPPED（反编译产出 `'break' outside loop` 编译错误）

**源码**:
```python
async def f():
    if c:
        async with x: pass
```

**反编译结果**:
```python
async def f():
    if c:
        async with x: break
```

**问题**: `async with` 的 body 为 `pass` 时，反编译器将 `pass` 错误还原为
`break`，导致产出非法语法（`break` 不在循环内）。`ast.parse` 能解析但
`compile` 抛出 `SyntaxError`，测试框架 `verify_bytecode_equivalence` 调用
`self.skipTest("重编译失败（可能是已知限制）")` 跳过。

**根因推测**: `async with` 的 `SETUP_ASYNC_WITH` / `POP_BLOCK` /
`WITH_EXCEPT_START` 清理路径中，`POP_TOP`（对应 `pass` body）被误识别为
`BREAK_LOOP` 或类似指令。

---

### Bug 2: async with 多上下文管理器 + as 绑定错乱（SKIPPED — 非法语法）

**文件**: `test_adv15_async_with_multi_as.py`
**状态**: SKIPPED（反编译产出 `break` + 结构错乱）

**源码**:
```python
async def f():
    if c:
        async with a as x, b as y:
            z = 1
```

**反编译结果**:
```python
async def f():
    if c:
        async with a as y:
            break
            z = 1
        async with b as x: pass
        None
```

**问题**: 多个 async with 上下文管理器被拆分为两个独立的 `async with` 语句，
as 绑定的变量名互换（`x` ↔ `y`），body 被替换为 `break`，并在末尾追加多余的
`None` 表达式。整个语句结构和变量绑定完全错乱。

**根因推测**: 多 ctx `async with` 在字节码层面是两个 `BEFORE_ASYNC_WITH` /
`SETUP_ASYNC_WITH` 序列，反编译器未能将它们合并为单个 `async with ... , ...`
语句。

---

### Bug 3: 字典字面量 value 为三元表达式 → 字典丢失

**文件**: `test_adv15_ternary_dict_value_body.py`
**状态**: FAILED（指令数不匹配: 12 vs 10）

**源码**:
```python
if c:
    d = {'k': a if x else b}
```

**反编译结果**:
```python
if c:
    (a if x else b)
```

**问题**: 字典字面量的 value 为三元表达式时，反编译器未能将三元 merge_block
归约到 `BUILD_MAP` 的 value 栈位，导致整个字典字面量丢失，仅残留三元表达式
作为独立语句（`POP_TOP`），赋值目标 `d` 也丢失。

**字节码对比**:
- 原始: `LOAD_CONST 'k'` / 三元 merge / `BUILD_MAP 1` / `STORE_NAME d`
- 重编: 三元 merge / `POP_TOP`（缺少 `BUILD_MAP` 和 `STORE_NAME`）

---

### Bug 4: 字典字面量 key 为三元表达式 → 字典丢失

**文件**: `test_adv15_ternary_dict_key_body.py`
**状态**: FAILED（指令数不匹配: 12 vs 10）

**源码**:
```python
if c:
    d = {a if x else b: 'v'}
```

**反编译结果**:
```python
if c:
    (a if x else b)
```

**问题**: 与 Bug 3 类似，但三元在 key 位置。反编译器同样未能将三元 merge
归约到 `BUILD_MAP` 的 key 栈位，字典字面量整体丢失。

---

### Bug 5: `f(*(三元))` 星号解包调用 → 丢失星号

**文件**: `test_adv15_ternary_call_star_body.py`
**状态**: FAILED（指令数不匹配: 13 vs 14）

**源码**:
```python
if c:
    f(*(a if x else b))
```

**反编译结果**:
```python
if c:
    f(a if x else b)
```

**问题**: 调用的 `*args` 参数为三元表达式时，反编译器丢失了星号解包标记。
原始字节码使用 `CALL_FUNCTION_EX`（带 `*args`），重编后变为普通
`PRECALL` / `CALL`（位置参数调用），调用语义改变。

**字节码对比**:
- 原始: `... BUILD_TUPLE 1` / `CALL_FUNCTION_EX 1`
- 重编: `... PRECALL` / `CALL`（缺少 `BUILD_TUPLE` 和 `CALL_FUNCTION_EX`）

---

### Bug 6: 切片下/上界均为三元 → 切片结构丢失

**文件**: `test_adv15_ternary_slice_in_body.py`
**状态**: FAILED（指令数不匹配: 16 vs 12）

**源码**:
```python
if c:
    x = lst[a if p else q:b if r else s]
```

**反编译结果**:
```python
if c:
    (a if p else q)
x = (b if r else s)
```

**问题**: 切片的下界和上界均为三元时，反编译器未能将两个三元 merge 归约到
`BUILD_SLICE 2` 的栈位，切片结构丢失。第一个三元变为 if 体内的独立语句，
第二个三元变为 if 体外的赋值（`x =`），`lst` 和 `BUILD_SLICE` /
`BINARY_SUBSCR` 完全消失。

---

### Bug 7: elif 测试条件为三元 → 分解为多层 elif 链

**文件**: `test_adv15_ternary_elif_test.py`
**状态**: FAILED（指令数不匹配: 13 vs 15）

**源码**:
```python
if a:
    pass
elif (b if c else d):
    pass
```

**反编译结果**:
```python
if a:
    pass
elif c:
    if b:
        pass
elif d:
    pass
```

**问题**: elif 的测试条件为三元表达式 `(b if c else d)` 时，反编译器将其
错误地分解为多层 elif 链。原始语义是三元整体作 elif 条件，反编译后变为
`elif c: if b: ... elif d: ...`，控制流结构不等价。

---

### Bug 8: if 体内三元赋值后续语句丢失

**文件**: `test_adv15_complex_body_ternary.py`
**状态**: FAILED（指令数不匹配: 16 vs 12）

**源码**:
```python
if c:
    a = 1
    b = a if x else 2
    c = b + 1
```

**反编译结果**:
```python
if c:
    a = 1
    b = (a if x else 2)
```

**问题**: if 体内有多条语句，其中一条为三元赋值时，反编译器在处理三元
merge 后丢弃了后续的 `c = b + 1` 语句。第三条语句的 `BINARY_OP` +
`STORE_NAME c` 完全从输出中消失。

---

### Bug 9: 元组解包右值为三元 → 解包结构破坏

**文件**: `test_adv15_ternary_in_tuple_unpack.py`
**状态**: FAILED（指令数不匹配: 15 vs 12）

**源码**:
```python
if c:
    a, b = (1 if x else 2), (3 if y else 4)
```

**反编译结果**:
```python
if c:
    (1 if x else 2)
a = (3 if y else 4)
```

**问题**: 元组解包赋值的右值为两个三元组成的元组时，反编译器将第一个三元
变为独立语句（`POP_TOP`），第二个三元仅赋给 `a`，`b` 的赋值丢失，元组解包
结构（`SWAP` / `STORE_NAME a` / `STORE_NAME b`）完全被破坏。

---

### Bug 10: walrus 绑定三元作 if 条件 → if 语句丢失

**文件**: `test_adv15_walrus_ternary_cond.py`
**状态**: FAILED（区域类型不匹配 — IF_REGION 中未找到 ast.If）

**源码**:
```python
if (n := (a if c else b)) > 0:
    pass
```

**反编译结果**:
```python
n = (a if c else b)
```

**问题**: if 条件中 walrus 直接绑定三元结果并参与比较时，反编译器将 if
语句整体丢弃，仅保留 `n = (a if c else b)` 作为顶层赋值语句。比较 `> 0`
和 if body 完全消失。反编译结果中不存在 `ast.If` 节点，区域类型验证失败。

**根因推测**: walrus 的 `COPY` + `STORE_NAME` 与三元 merge 的归约顺序
错误，导致 `COMPARE_OP` / `POP_JUMP_IF_FALSE` 被错误消费。

---

### Bug 11: 嵌套 if 内三元赋值 → 内层 if 提升丢失

**文件**: `test_adv15_nested_if_ternary_body.py`
**状态**: FAILED（指令2参数不匹配: `b` vs `p`）

**源码**:
```python
if a:
    if b:
        x = c if p else d
```

**反编译结果**:
```python
if a:
    x = (c if p else d)
    if b:
        pass
```

**问题**: 嵌套 if 的内层 if body 为三元赋值时，反编译器将赋值语句从内层
if body 中提升到外层 if body，导致内层 `if b` 只剩 `pass`。更严重的是，
`LOAD_NAME` 的 argval 发生错位（`b` 被误读为 `p`），表明反编译器在
归约三元 merge 时混淆了内层 if 条件和三元条件。

---

### Bug 12: if/elif/else 每分支三元赋值 → 合并为嵌套三元

**文件**: `test_adv15_ternary_each_branch.py`
**状态**: FAILED（区域类型不匹配 — IF_REGION 中未找到 ast.If）

**源码**:
```python
if a:
    x = 1 if p else 2
elif b:
    x = 3 if q else 4
else:
    x = 5 if r else 6
```

**反编译结果**:
```python
((1 if p else 2) if a else (3 if q else 4) if b else 5 if r else 6)
```

**问题**: if/elif/else 每个分支的 body 均为三元赋值时，反编译器将整个
if/elif/else 错误地合并为一个嵌套三元表达式作为顶层表达式语句。控制流
结构（`ast.If`）和赋值语义（`STORE_NAME x`）均被破坏。

---

### Bug 13: 链式比较中间操作数为三元 → 链式丢失

**文件**: `test_adv15_ternary_in_chain_compare_body.py`
**状态**: FAILED（指令数不匹配: 19 vs 10）

**源码**:
```python
if c:
    z = 0 < (a if p else b) < 10
```

**反编译结果**:
```python
if c:
    (a if p else b)
    10
```

**问题**: 链式比较的中间操作数为三元表达式时，反编译器未能将三元 merge
归约到链式比较的中间栈位。链式比较结构丢失，三元变为独立语句，`10` 也变为
独立表达式语句，`z` 的赋值完全消失。

---

### Bug 14: for 循环的 iterable 为三元 → 三元重复求值

**文件**: `test_adv15_ternary_for_iter_body.py`
**状态**: FAILED（指令数不匹配: 11 vs 15）

**源码**:
```python
if c:
    for x in (a if p else b):
        pass
```

**反编译结果**:
```python
if c:
    (a if p else b)
    for x in a if p else b:
        pass
```

**问题**: for 循环的 iterable 为三元表达式时，反编译器将三元 merge 拆出为
独立表达式语句（`POP_TOP`），同时 for 循环仍保留三元表达式作为 iterable。
这导致三元被求值两次，且第一次的求值结果被丢弃。

---

### Bug 15: walrus 绑定三元后参与运算 → 后续运算丢失

**文件**: `test_adv15_walrus_in_ternary_body.py`
**状态**: FAILED（指令数不匹配: 14 vs 10）

**源码**:
```python
if c:
    x = (y := a if p else b) + 1
```

**反编译结果**:
```python
if c:
    y = (a if p else b)
```

**问题**: 赋值右值为 walrus 绑定三元结果后参与二元运算时，反编译器在归约
walrus `COPY` + `STORE_NAME y` 与三元 merge 后，将 `+ 1` / `STORE_NAME x`
后续部分丢弃，仅保留 `y = (a if p else b)`，`x` 的赋值和加法运算完全消失。

---

## 错误模式归类

### 模式 A: 三元 merge_block 在 if 体内吞噬外层结构（11 个）

这是 R15 发现的主要错误模式。当 if 体内某条语句的子结构（字典 key/value、
切片下/上界、元组元素、链式比较操作数、for iterable、`*args` 等）包含三元
表达式时，反编译器未能将三元 merge_block 正确归约到外层构建指令
（`BUILD_MAP` / `BUILD_SLICE` / `BUILD_TUPLE` / `COMPARE_OP` 链 /
`GET_ITER` / `CALL_FUNCTION_EX`）的栈位，导致：

1. 三元 merge 被拆出为独立表达式语句（`POP_TOP`）
2. 外层构建指令和 `STORE_NAME` 丢失或错位
3. 后续语句可能被丢弃

**涉及测试**: Bug 3, 4, 5, 6, 8, 9, 13, 14, 15（9 个）

### 模式 B: 三元作 if/elif 测试条件被错误分解（2 个）

当 if 或 elif 的测试条件本身为三元表达式时，反编译器将其分解为多层
if/elif 结构或合并为嵌套三元，控制流语义不等价。

**涉及测试**: Bug 7, 12（2 个）

### 模式 C: walrus 与三元组合导致 if 语句丢失（2 个）

walrus 绑定三元结果后直接参与 if 条件比较，或三元内含 walrus 后参与运算，
反编译器在归约 walrus `COPY` + `STORE_NAME` 与三元 merge 时出错，导致
if 语句或后续运算丢失。

**涉及测试**: Bug 10, 15（2 个）

### 模式 D: 嵌套 if 内三元赋值导致结构提升（1 个）

嵌套 if 的内层 if body 为三元赋值时，赋值被提升到外层 if body，内层 if
条件与三元条件混淆。

**涉及测试**: Bug 11（1 个）

### 模式 E: async with body `pass` 被还原为 `break`（2 个）

`async with` 在 if 体内时，body 的 `pass` 被错误还原为 `break`，多 ctx
管理器的 as 绑定也会错乱。反编译产出非法语法。

**涉及测试**: Bug 1, 2（2 个）

---

## 与 R1-R14 的区别

R1-R14 主要覆盖三元表达式在 **if 条件** 中作子结构（subscr/call arg/
slice operand/container element 等）的反编译。R15 新发现集中在：

1. **三元在 if 体内（body）作赋值右值的子结构** — 此前未覆盖
2. **三元作 elif 测试条件** — 此前未覆盖
3. **walrus 直接绑定三元作 if 条件** — R14 的 `walrus_ternary_attr` 是
   walrus 绑定三元后取属性，R15 是 walrus 直接绑定三元后比较（更简单但
   反编译器反而出错）
4. **async with 在 if 体内** — R10 的 `nested_async_for_in_with` 覆盖了
   async for + async with 组合，但未覆盖 async with body 为 `pass` 的
   简单情况和多 ctx 情况
5. **嵌套 if 内三元赋值** — 此前未覆盖
6. **if/elif/else 每分支均为三元赋值** — 此前未覆盖

---

## 建议修复优先级

1. **高**: Bug 1, 2（async with `pass` → `break`）— 产出非法语法，影响面大
2. **高**: Bug 10, 12（if 语句整体丢失）— 控制流完全消失
3. **高**: Bug 11（嵌套 if 结构提升 + argval 错位）— 控制流错乱
4. **中**: Bug 3, 4, 6, 9, 13（模式 A：三元吞噬外层结构）— 赋值丢失
5. **中**: Bug 7（elif 条件三元分解）— 控制流不等价
6. **中**: Bug 8, 14, 15（后续语句丢失/三元重复求值）— 语句丢失
7. **低**: Bug 5（`*args` 丢失星号）— 调用语义改变但较少见
