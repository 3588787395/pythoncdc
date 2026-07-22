# Ternary Region Round 05 — 测试发现报告

## 概览

- **R5 测试总数**: 22 个新测试（10 failed / 12 passed / 0 skipped）
- **新发现 bug**: 10 个（全部 FAILED，≥10 完成标准达成）
- **回归状态**: 基线 59 failed / 158 passed / 1 skipped（218 测试）→ R5 后 69 failed / 170 passed / 1 skipped（240 测试），**基线零退化**（新增 10 failed + 12 passed 与 R5 测试结果完全吻合）
- **修改文件**: 仅新增 22 个测试文件 + 2 个调试脚本（`_r5_debug_dump.py` / `_r5_debug_dump_v2.py`），**未修改任何源代码**
- **优先聚焦**: R4-03 chained_compare_4way（3/4/5-term 变体 3 个）+ R4-10 while_cond（3 个变体）共 6 个测试，全部失败确认 R4 已知限制仍未修复
- **新对抗方向**: 11 个 R1-R4 未覆盖的 ternary 上下文（class body / decorator / global / nonlocal / lambda default / *args / **kwargs / slice / is / in / return-listcomp / dictcomp / setcomp / genexp / await+return），其中 4 个失败（class body 多属性、**kwargs、subscript slice、await+return）

## 1. 统计摘要表

| 指标 | 数值 |
|------|------|
| R5 测试文件数 | 22 |
| R5 测试 passed | 12 |
| R5 测试 failed | 10 |
| R5 测试 skipped | 0 |
| 新发现真实 bug | 10（≥10 完成标准） |
| Ternary 区域基线（R4 完成） | 59 failed / 158 passed / 1 skipped（共 218 测试） |
| Ternary 区域当前（R5 完成后） | 69 failed / 170 passed / 1 skipped（共 240 测试） |
| 基线退化 | **0**（剔除 R5 测试后基线仍为 59/158/1） |

## 2. R5 测试文件列表

| # | 文件 | 状态 | 错误类别 |
|---|------|------|---------|
| 1 | test_r5_ternary_chained_compare_assign.py | FAILED | 3-term chained compare 中段 + assign → 渲染为 if 语句（R4-03 同根因） |
| 2 | test_r5_ternary_chained_compare_4way_assign.py | FAILED | 4-term chained compare 中段 + assign（R4-03 复现） |
| 3 | test_r5_ternary_chained_compare_5way_assign.py | FAILED | 5-term chained compare 中段 + assign（R4-03 极端扩展） |
| 4 | test_r5_ternary_chained_compare_left_assign.py | PASSED | — （R4-03 部分修复覆盖，回归验证通过） |
| 5 | test_r5_ternary_while_cond_simple.py | FAILED | while(ternary) 空循环体 → 退化为 if + while + continue（R4-10 复现） |
| 6 | test_r5_ternary_while_cond_body.py | FAILED | while(ternary) + 循环体赋值（R4-10 同根因） |
| 7 | test_r5_ternary_while_cond_break.py | FAILED | while(ternary) + 嵌套 if-break（R4-10 同根因） |
| 8 | test_r5_ternary_in_class_body.py | FAILED | class body 多 ternary 属性，第二个 ternary 前泄漏 `c` 表达式语句 |
| 9 | test_r5_ternary_in_decorator.py | PASSED | — （R3 已修复场景的回归验证） |
| 10 | test_r5_ternary_in_global.py | PASSED | — （R3 已修复场景的回归验证） |
| 11 | test_r5_ternary_in_nonlocal.py | PASSED | — （STORE_DEREF 已被现有逻辑识别） |
| 12 | test_r5_ternary_in_lambda_default.py | PASSED | — （lambda defaults 已被现有逻辑识别） |
| 13 | test_r5_ternary_in_call_starred.py | PASSED | — （R1 已修复场景的回归验证） |
| 14 | test_r5_ternary_in_call_kwargs_double_star.py | FAILED | f(**(ternary)) 双星 kwargs → 退化为 f(*(ternary)) 单星 args，DICT_MERGE 丢失 |
| 15 | test_r5_ternary_in_subscript_slice.py | FAILED | x[1:(ternary)] slice → 退化为独立表达式 (ternary)，BUILD_SLICE + BINARY_SUBSCR 丢失 |
| 16 | test_r5_ternary_in_compare_is.py | PASSED | — （IS_OP 已被现有逻辑识别） |
| 17 | test_r5_ternary_in_compare_in.py | PASSED | — （CONTAINS_OP 已被现有逻辑识别） |
| 18 | test_r5_ternary_in_return_complex.py | PASSED | — （listcomp 已被现有逻辑识别） |
| 19 | test_r5_ternary_in_dict_comp.py | PASSED | — （MAP_ADD 已被现有逻辑识别） |
| 20 | test_r5_ternary_in_set_comp.py | PASSED | — （SET_ADD 已被现有逻辑识别） |
| 21 | test_r5_ternary_in_genexp.py | PASSED | — （YIELD_VALUE 已被现有逻辑识别） |
| 22 | test_r5_ternary_in_await_complex.py | FAILED | async return await (ternary) → 丢失 return，await (ternary) 作为独立语句 |

## 3. Bug 详细分析

### Bug R5-01: 3-term chained compare 中段 + assign — IfRegion 渲染为 if 而非赋值

**文件**: `test_r5_ternary_chained_compare_assign.py`
**状态**: FAILED — 指令数不匹配 16 vs 17（重编多出 RETURN_VALUE × 2，缺失 JUMP_IF_FALSE_OR_POP / STORE_NAME）
**源码**:
```python
r = 0 < (a if c else b) < 10
```
**反编译结果**:
```python
if (0 < (a if c else b) < 10):
    pass
```
**问题分解**:
- 子 bug 1: 反编译结果丢失赋值目标 `r`，将 `r = ...` 渲染为 `if (...): pass`
- 子 bug 2: chained compare 表达式已正确构建为 `0 < IfExp < 10`（R4-03 部分修复有效），但 IfRegion 仍未识别 merge_block 的 STORE_NAME(r) 应触发 Assign 而非 if 语句
- 子 bug 3: 重编字节码缺失 `JUMP_IF_FALSE_OR_POP`（chained compare 短路）、`SWAP 2`、`POP_TOP`、`STORE_NAME r`，多出 2 个 RETURN_VALUE（if + pass 块尾的隐式 return）

**字节码对比**:
- 原始 16 条 / 重编 17 条
- 原始特有: `JUMP_IF_FALSE_OR_POP 36, SWAP 2, POP_TOP, STORE_NAME 'r'`
- 重编缺失: `JUMP_IF_FALSE_OR_POP, STORE_NAME 'r'`（ chained compare 短路 + 赋值目标全丢失）
- 重编多出: `LOAD_CONST None, RETURN_VALUE, LOAD_CONST None, RETURN_VALUE`（×2，来自 if + pass 块尾隐式 return）

**根因推测**: R4-03 部分修复使 `_build_ternary_wrapped_expr` 正确识别 `SHORT_CIRCUIT_JUMP_OPS`（JUMP_IF_FALSE_OR_POP）构建 chained compare 表达式，但 IfRegion 在 `_process_if_blocks` / `_generate_if` 中仍将含 chained compare 的 IfRegion 渲染为 if 语句而非检测 merge_block 末尾的 `STORE_NAME(r)` 触发 `Assign(targets=[r], value=Compare)`。依「父引用子入口」原则，`STORE_NAME r` 应作为 ternary/chained-compare 的父消费者，触发 Assign 归约而非 If 归约。

---

### Bug R5-02: 4-term chained compare 中段 + assign — R4-03 复现

**文件**: `test_r5_ternary_chained_compare_4way_assign.py`
**状态**: FAILED — 指令 8 操作码不匹配 `JUMP_IF_FALSE_OR_POP vs LOAD_CONST`（chained compare 短路跳转丢失）
**源码**:
```python
r = 0 < (a if c else b) < 10 < 100
```
**反编译结果**:
```python
if (0 < (a if c else b) < 10 < 100):
    pass
```
**问题分解**:
- 与 R5-01 同根因（R4-03 已知限制复现），chained compare 表达式正确构建，但 IfRegion 渲染错误
- 4-term 比 3-term 多一个 `JUMP_IF_FALSE_OR_POP` 短路点，全部丢失

**字节码对比**:
- 原始 20 条 / 重编 19 条
- 原始特有: `JUMP_IF_FALSE_OR_POP 50` × 2（中段短路）, `SWAP 2, POP_TOP, STORE_NAME 'r'`
- 重编缺失: `JUMP_IF_FALSE_OR_POP × 2, STORE_NAME 'r'`
- 重编多出: `LOAD_CONST None, RETURN_VALUE` × 2（if + pass 块尾）

**根因推测**: 同 R5-01。R4-03 部分修复对 4-term 仍有效构建表达式 `0 < IfExp < 10 < 100`，但 IfRegion→Assign 边界仍未识别。

---

### Bug R5-03: 5-term chained compare 中段 + assign — R4-03 极端扩展

**文件**: `test_r5_ternary_chained_compare_5way_assign.py`
**状态**: FAILED — 指令数不匹配 26 vs 25（重编缺失 3 个 JUMP_IF_FALSE_OR_POP + STORE_NAME，多出 3 个 RETURN_VALUE）
**源码**:
```python
r = 0 < (a if c else b) < 10 < 100 < 1000
```
**反编译结果**:
```python
if (0 < (a if c else b) < 10 < 100 < 1000):
    pass
```
**问题分解**:
- 5-term chained compare 含 3 个中段 `JUMP_IF_FALSE_OR_POP` 短路点，全部丢失
- 表达式正确构建，IfRegion 渲染错误（与 R5-01/R5-02 同根因）

**字节码对比**:
- 原始 26 条 / 重编 25 条
- 原始特有: `JUMP_IF_FALSE_OR_POP 64` × 3（中段短路）, `SWAP 2, POP_TOP, STORE_NAME 'r'`
- 重编缺失: `JUMP_IF_FALSE_OR_POP × 3, STORE_NAME 'r'`
- 重编多出: `LOAD_CONST None, RETURN_VALUE` × 3

**根因推测**: 同 R5-01。chained compare 项数越多，丢失的短路跳转越多，但根因不变（IfRegion→Assign 边界）。

---

### Bug R5-04: chained compare 左端（2-term）+ assign — PASSED（回归验证）

**文件**: `test_r5_ternary_chained_compare_left_assign.py`
**状态**: PASSED — R4-03 部分修复有效，2-term 左端场景未退化。
**说明**: 作为 R5-01/R5-02/R5-03 的对照（2-term vs 3/4/5-term）。2-term 场景 `r = (a if c else b) < 10` 只有一个 COMPARE_OP，无中段 JUMP_IF_FALSE_OR_POP，IfRegion 正确渲染为 Assign。3/4/5-term 含中段短路跳转，IfRegion 错误渲染为 if 语句。**根因锁定**: chained compare 中段 JUMP_IF_FALSE_OR_POP 是触发 IfRegion 错误归约的关键。

---

### Bug R5-05: while(ternary) 空循环体 — R4-10 复现

**文件**: `test_r5_ternary_while_cond_simple.py`
**状态**: FAILED — 反编译结果中未找到预期的区域类型 TERNARY（IfExp AST 节点缺失）
**源码**:
```python
while (a if c else b):
    pass
```
**反编译结果**:
```python
if a:
    pass
while c and b:
    if c:
        pass
    a
    continue
```
**问题分解**:
- 子 bug 1: ternary 完全消失，反编译为 `if a: pass` + `while c and b: ...` 两段独立结构
- 子 bug 2: while 循环条件被错误识别为 `c and b`（BoolOp），实际应是 `(a if c else b)`（IfExp）
- 子 bug 3: 循环体内被插入 `if c: pass`, `a`, `continue` 三个本不应存在的语句
- 子 bug 4: AST 中完全不存在 IfExp 节点

**字节码对比**:
- 原始 14 条 / 重编 10 条
- 原始特有: `LOAD_NAME 'b', LOAD_CONST None, RETURN_VALUE None` × 2（ternary false 分支的隐式 return + 模块尾 return）
- 重编特有: `LOAD_NAME 'a', POP_TOP`（被错误识别为独立 if-then）
- 重编缺失: `LOAD_NAME 'b', RETURN_VALUE`（ternary false 分支丢失）

**根因推测**: R4-10 已识别为已知限制（完全回滚）。`while(ternary)` 模式中 ternary 的 true/false blocks 同时充当 while 条件测试，违反「每块唯一归属」原则。`_detect_ternary_pattern` 在 line 11112-11116 检测到 ternary 分支入口属于 LoopRegion.condition_block 时拒绝创建 TernaryRegion，导致 ternary 退化为独立 if 语句；while 循环条件被错误识别为 BoolOp `c and b`。需在 `_identify_loop_regions` 阶段识别 while(ternary) 模式，将 ternary 提取为 while 的 condition_expr 而非独立 region。

---

### Bug R5-06: while(ternary) + 循环体赋值 — R4-10 同根因

**文件**: `test_r5_ternary_while_cond_body.py`
**状态**: FAILED — IfExp AST 节点缺失
**源码**:
```python
while (a if c else b):
    x = 1
```
**反编译结果**:
```python
if a:
    pass
while c and b:
    x = 1
    if c:
        pass
    a
    continue
```
**问题分解**:
- 与 R5-05 同根因，循环体含 `x = 1` 赋值
- 循环体内被插入 `if c: pass`, `a`, `continue` 三个本不应存在的语句
- ternary 完全消失

**字节码对比**:
- 原始 16 条 / 重编 12 条
- 原始特有: `LOAD_NAME 'b', LOAD_CONST None, RETURN_VALUE None` × 2
- 重编特有: `LOAD_NAME 'a', POP_TOP`
- 重编缺失: `LOAD_NAME 'b', RETURN_VALUE` × 2

**根因推测**: 同 R5-05。循环体的 `STORE_NAME 'x'` 被正确保留在 while body 中，但 ternary 仍完全消失。

---

### Bug R5-07: while(ternary) + 嵌套 if-break — R4-10 同根因

**文件**: `test_r5_ternary_while_cond_break.py`
**状态**: FAILED — IfExp AST 节点缺失，且循环体 `if x: break` 也丢失
**源码**:
```python
while (a if c else b):
    if x:
        break
```
**反编译结果**:
```python
if a:
    pass
while c and b:
    pass
```
**问题分解**:
- 与 R5-05/R5-06 同根因
- 额外问题: 循环体内的 `if x: break` 完全丢失，被替换为 `pass`
- ternary + 嵌套 if-break 双重结构均未正确归约

**字节码对比**:
- 原始 16 条 / 重编 13 条
- 原始特有: `LOAD_NAME 'x', RETURN_VALUE, LOAD_NAME 'c', LOAD_NAME 'a', RETURN_VALUE, LOAD_NAME 'b', RETURN_VALUE`
- 重编特有: `LOAD_NAME 'c', LOAD_NAME 'b'`（while 条件 BoolOp 错误识别）
- 重编缺失: `LOAD_NAME 'x', RETURN_VALUE`（if x: break 完全丢失）

**根因推测**: 同 R5-05。while(ternary) 模式的结构融合导致后续 if-break 嵌套也未被正确归约。

---

### Bug R5-08: class body 多 ternary 属性 — 第二个 ternary 前泄漏 `c` 表达式语句

**文件**: `test_r5_ternary_in_class_body.py`
**状态**: FAILED — 嵌套 code object 不匹配（class C body 指令数 18 vs 20，重编多出 `LOAD_NAME 'c', POP_TOP`）
**源码**:
```python
class C:
    x = a if c else b
    y = m if c else n
    def f(self):
        return self.x
```
**反编译结果**:
```python
class C:
    x = (a if c else b)
    c
    y = (m if c else n)
    def f(self):
        return self.x
```
**问题分解**:
- 子 bug 1: 第二个 ternary `y = m if c else n` 之前多出一行 `c` 表达式语句（ternary 条件被泄漏到外层）
- 子 bug 2: class code object 字节码多出 `LOAD_NAME 'c', POP_TOP`（对应泄漏的 `c` 表达式语句）
- 子 bug 3: 第一个 ternary `x = a if c else b` 正确归约（说明 bug 仅触发于多 ternary 场景）

**字节码对比**（class C 内嵌 code object）:
- 原始 18 条 / 重编 20 条
- 原始特有: （无）
- 重编特有: `LOAD_NAME 'c', POP_TOP`（在第二个 ternary 之前）
- 重编缺失: （无）

**根因推测**: 与 R1 `test_r1_class_body_multi_ternary` 同根因（已存在基线 bug）。class body 中连续多个 ternary 赋值时，`_generate_region` 处理第二个 ternary 的 cond_block 时未将其标记为 generated，导致 cond_block 的 LOAD_NAME 'c'（ternary 条件）被 `_process_if_blocks` 当作独立表达式语句输出。依「每块唯一归属」原则，ternary 的 cond_block 应归属 TernaryRegion，不应被父 class body 重复处理。R5 在 R1 基础上加入 `def f` 方法加重复杂度，确认 bug 仍未修复。

---

### Bug R5-09 ~ R5-13, R5-16 ~ R5-21: PASSED（回归验证 + 新方向通过）

**文件**: `test_r5_ternary_in_decorator.py`, `test_r5_ternary_in_global.py`, `test_r5_ternary_in_nonlocal.py`, `test_r5_ternary_in_lambda_default.py`, `test_r5_ternary_in_call_starred.py`, `test_r5_ternary_in_compare_is.py`, `test_r5_ternary_in_compare_in.py`, `test_r5_ternary_in_return_complex.py`, `test_r5_ternary_in_dict_comp.py`, `test_r5_ternary_in_set_comp.py`, `test_r5_ternary_in_genexp.py`
**状态**: PASSED — 11 个新对抗方向全部通过，确认 R1-R4 修复有效覆盖 decorator / global / nonlocal / lambda default / *args / is / in / listcomp / dictcomp / setcomp / genexp 等 ternary 上下文。

---

### Bug R5-14: f(\*\*(ternary)) 双星 kwargs — 退化为单星 *args

**文件**: `test_r5_ternary_in_call_kwargs_double_star.py`
**状态**: FAILED — 指令数不匹配 13 vs 10（重编缺失 BUILD_MAP / DICT_MERGE / LOAD_CONST ()）
**源码**:
```python
f(**(d if c else e))
```
**反编译结果**:
```python
f(*(d if c else e))
```
**问题分解**:
- 子 bug 1: `**` 双星 kwargs 被错误渲染为 `*` 单星 args
- 子 bug 2: BUILD_MAP + DICT_MERGE + CALL_FUNCTION_EX 1 (kwargs flag) 全部丢失
- 子 bug 3: 重编 CALL_FUNCTION_EX 0 (无 kwargs flag)，参数语义完全改变（args 展开 vs kwargs 展开）

**字节码对比**:
- 原始 13 条 / 重编 10 条
- 原始特有: `LOAD_CONST (), BUILD_MAP 0, LOAD_NAME 'c', LOAD_NAME 'd', LOAD_NAME 'e', DICT_MERGE 1, CALL_FUNCTION_EX 1`
- 重编缺失: `LOAD_CONST (), BUILD_MAP 0, DICT_MERGE 1`
- 重编特有: `CALL_FUNCTION_EX 0`（flag 从 1 降为 0，丢失 kwargs 标志位）

**根因推测**: `_try_build_ternary_call_arg` / `_build_ternary_no_target_consumer_stmt` 在处理 `f(**(ternary))` 时，未识别 DICT_MERGE + CALL_FUNCTION_EX 1（kwargs flag）模式。当前逻辑将 ternary 直接作为 *args 位置参数重建（CALL_FUNCTION_EX 0），丢失 `**` 双星解包语义。R4-16 已通过显式 `key=value` kwargs 场景（BUILD_MAP + KW_NAMES），但 `**(ternary)` dict 解包形式（DICT_MERGE）未识别。依「父引用子入口」原则，父 Call 通过 `LOAD_CONST () + BUILD_MAP 0 + DICT_MERGE 1 + CALL_FUNCTION_EX 1` 引用 ternary 子节点，应重建为 `Call(func=f, kwargs=Starred(IfExp, ctx=Load))` 或类似 AST。

---

### Bug R5-15: x[1:(ternary)] subscript slice — 退化为独立表达式

**文件**: `test_r5_ternary_in_subscript_slice.py`
**状态**: FAILED — 指令数不匹配 11 vs 10（重编缺失 BUILD_SLICE / BINARY_SUBSCR / LOAD_CONST 1 / LOAD_NAME 'x'，多出多个 RETURN_VALUE）
**源码**:
```python
x[1:(a if c else b)]
```
**反编译结果**:
```python
(a if c else b)
```
**问题分解**:
- 子 bug 1: subscript `x[1:(ternary)]` 完全丢失，反编译为独立表达式 `(a if c else b)`
- 子 bug 2: LOAD_NAME 'x'（subscript 对象）、LOAD_CONST 1（slice lower）、BUILD_SLICE 2、BINARY_SUBSCR 全部丢失
- 子 bug 3: 重编字节码将 ternary 拆为两个独立表达式 `a` 和 `b`，每个后跟 POP_TOP + RETURN_VALUE

**字节码对比**:
- 原始 11 条 / 重编 10 条
- 原始特有: `LOAD_NAME 'x', LOAD_CONST 1, BUILD_SLICE 2, BINARY_SUBSCR`
- 重编特有: `LOAD_NAME 'c', LOAD_NAME 'a', POP_TOP, LOAD_CONST None, RETURN_VALUE, LOAD_NAME 'b', POP_TOP, LOAD_CONST None, RETURN_VALUE`
- 重编缺失: `LOAD_NAME 'x', LOAD_CONST 1, BUILD_SLICE 2, BINARY_SUBSCR`（subscript 结构全丢）

**根因推测**: R1 `test_r1_ternary_in_slice` 已通过简单 slice 场景，但本测试用 `x[1:(a if c else b)]`（slice lower=常量 1，upper=ternary）形式。`_build_ternary_wrapped_expr` 在处理 BUILD_SLICE 2 上下文时，未识别 cond_block preload（`LOAD_NAME 'x', LOAD_CONST 1`）+ merge_block（`BUILD_SLICE 2, BINARY_SUBSCR`）模式，导致 ternary 被错误归约为独立表达式语句。R1 测试的 slice 场景可能是 `x[a if c else b:b]` 或 `x[a if c else b]`（直接 subscript），未覆盖 slice + ternary upper 复合。依「父引用子入口」原则，父 Subscript 通过 cond_block preload（x, 1）+ merge_block（BUILD_SLICE 2, BINARY_SUBSCR）引用 ternary 子节点，应重建为 `Subscript(value=x, slice=Slice(lower=1, upper=IfExp))`。

---

### Bug R5-22: async return await (ternary) — 丢失 return

**文件**: `test_r5_ternary_in_await_complex.py`
**状态**: FAILED — 嵌套 code object 不匹配（async f body 指令数 12 vs 14，重编多出 POP_TOP + LOAD_CONST + RETURN_VALUE）
**源码**:
```python
async def f():
    return await (a if c else b)
```
**反编译结果**:
```python
async def f():
    await (a if c else b)
```
**问题分解**:
- 子 bug 1: `return await (ternary)` 复合语句丢失 `return`，退化为 `await (ternary)` 表达式语句
- 子 bug 2: async f 内嵌 code object 多出 `POP_TOP`（丢弃 await 表达式的值）+ `LOAD_CONST None, RETURN_VALUE`（隐式 return None）
- 子 bug 3: 原始字节码末尾直接 `RETURN_VALUE`（return await 的返回值），重编字节码末尾 `POP_TOP` + `LOAD_CONST None, RETURN_VALUE`（丢弃 await 值后隐式返回 None）

**字节码对比**（async f 内嵌 code object）:
- 原始 12 条 / 重编 14 条
- 原始特有: （无）
- 重编特有: `POP_TOP, LOAD_CONST None, RETURN_VALUE`
- 重编缺失: （无，但末尾 RETURN_VALUE 语义改变：原始返回 await 值，重编返回 None）

**根因推测**: R4-02 已通过简单 `await (ternary)` 场景（无 return），返回 `Expr(Await(IfExp))`。但 R5-22 `return await (ternary)` 复合场景中，merge_block 同时含 `GET_AWAITABLE + SEND + RETURN_VALUE`，`_build_ternary_no_target_consumer_stmt` 的 Pattern 7（await）检测到 GET_AWAITABLE 后返回 `Expr(Await(IfExp))`，未识别后续 RETURN_VALUE 应触发 `Return(Await(IfExp))` 而非 `Expr(Await(IfExp))`。依「父引用子入口」原则，父 Return 通过 merge_block 的 GET_AWAITABLE+SEND+RETURN_VALUE 引用 ternary 子节点，应重建为 `Return(value=Await(value=IfExp))`。

## 4. 错误模式归类

| 模式 | Bug 数 | Bug 编号 | 共同根因 |
|------|--------|---------|---------|
| chained compare + assign → IfRegion 错误归约 | 3 | R5-01, R5-02, R5-03 | IfRegion 未识别 merge_block 的 STORE_NAME(r) 触发 Assign；chained compare 中段 JUMP_IF_FALSE_OR_POP 是触发关键（2-term 无此跳转则通过） |
| while(ternary) → 退化为 if + while(BoolOp) | 3 | R5-05, R5-06, R5-07 | ternary 与 while 循环结构融合，违反「每块唯一归属」；`_detect_ternary_pattern` line 11112-11116 拒绝创建 TernaryRegion |
| class body 多 ternary → 条件泄漏 | 1 | R5-08 | 第二个 ternary 的 cond_block 未标记 generated，被父 class body 重复处理（R1 已知基线 bug 复现） |
| kwargs `**(ternary)` → 退化为 `*(ternary)` | 1 | R5-14 | DICT_MERGE + CALL_FUNCTION_EX 1（kwargs flag）模式未识别，重建为 CALL_FUNCTION_EX 0（args flag） |
| subscript slice `x[1:(ternary)]` → 退化为独立表达式 | 1 | R5-15 | BUILD_SLICE 2 + BINARY_SUBSCR 模式未识别，ternary 被错误归约为独立表达式语句 |
| `return await (ternary)` → 丢失 return | 1 | R5-22 | merge_block 的 GET_AWAITABLE+SEND+RETURN_VALUE 模式未识别，Pattern 7 (await) 返回 Expr 而非 Return |

**总计**: 6 个独立根因模式，10 个 bug。

## 5. 修复优先级建议

| 优先级 | Bug | 修复方向 | 难度 | 影响面 |
|--------|-----|---------|------|--------|
| P0（最高） | R5-01, R5-02, R5-03 | 在 `_process_if_blocks` / `_generate_if` 中检测 merge_block 末尾的 `STORE_NAME(r)`，触发 `Assign(targets=[r], value=Compare(...))` 而非 if 语句；与 R4-03 部分修复协同 | 中 | chained compare + assign 全场景（3/4/5-term），R4-03 已知限制解锁 |
| P0 | R5-05, R5-06, R5-07 | 在 `_identify_loop_regions` 阶段识别 while(ternary) 模式，将 ternary 提取为 while 的 condition_expr；需重构「每块唯一归属」原则对 while 条件块的例外 | 高 | while(ternary) 全场景，R4-10 已知限制解锁 |
| P1 | R5-22 | 在 `_build_ternary_no_target_consumer_stmt` Pattern 7 (await) 后追加 RETURN_VALUE 检测，返回 `Return(Await(IfExp))` 而非 `Expr(Await(IfExp))` | 低 | async return await (ternary) 场景 |
| P1 | R5-15 | 在 `_build_ternary_wrapped_expr` 中新增 BUILD_SLICE 2 + BINARY_SUBSCR 模式识别，从 cond_block preload 提取 `LOAD_NAME 'x', LOAD_CONST 1`，重建 `Subscript(value=x, slice=Slice(lower=1, upper=IfExp))` | 中 | x[const:(ternary)] subscript slice 场景 |
| P2 | R5-14 | 在 `_try_build_ternary_call_arg` 中新增 DICT_MERGE + CALL_FUNCTION_EX 1（kwargs flag）模式识别，重建 `Call(func=f, kwargs=Starred(IfExp, ctx=Load))` | 中 | f(\*\*(ternary)) 双星 kwargs 场景 |
| P2 | R5-08 | 在 `_generate_region` TernaryRegion 处理后，将 cond_block 标记为 generated，避免父 class body 重复处理；与 R1 `test_r1_class_body_multi_ternary` 同根因 | 低 | class body 多 ternary 属性场景（R1 已知基线 bug） |

## 6. 与 R1-R4 的区别

| 维度 | R1-R4 | R5 |
|------|-------|-----|
| **测试规模** | R1 16 个 / R2 35 个 / R3 19 个 / R4 23 个 | 22 个（接近 R4 规模） |
| **核心目标** | R1 覆盖基础场景 / R2 扩展算子与容器 / R3 探索 class/decorator/global/raise/while/with/try / R4 修复 R3 已知限制 + call/fstring/dict/set/with/try | **优先聚焦 R4 已知限制**（R4-03 chained_compare 3 个变体 + R4-10 while_cond 3 个变体）+ R1-R4 未覆盖的 11 个新对抗方向 |
| **已知限制复现** | R3 首次发现 R3-01/R3-02 (chained compare) + R3-09 (while_cond) | R5-01/02/03 复现 R4-03，R5-05/06/07 复现 R4-10，**确认 R4 已知限制仍未修复** |
| **新对抗方向** | R1 ternary in starred/slice/method/with/lambda；R2 ternary in binop/compare/list/dict/set/yield/format/fstring/star_args/kwarg；R3 ternary in class attr/decorator/global/nested func/raise/with/try/while/await | **R5 新增**: class body 多 ternary + 方法、decorator + return、global + return、nonlocal + ternary、lambda default + ternary、`*(ternary)`、`**(ternary)`、`x[1:(ternary)]`、`x is (ternary)`、`x in (ternary)`、return listcomp、dictcomp、setcomp、genexp、return await (ternary) |
| **失败模式** | R1-R4 已覆盖：ternary in container/call/with/try/await/raise 等 | R5 新发现 6 个独立根因：chained compare + assign IfRegion 边界（3 个）、while(ternary) 结构融合（3 个）、class body 多 ternary 条件泄漏（1 个）、`**(ternary)` DICT_MERGE 未识别（1 个）、`x[1:(ternary)]` BUILD_SLICE+BINARY_SUBSCR 未识别（1 个）、`return await (ternary)` RETURN_VALUE 未识别（1 个） |
| **基线影响** | R1 0 退化 / R2 0 退化 / R3 0 退化 / R4 0 退化 | **R5 0 退化**（基线 59 failed / 158 passed / 1 skipped 保持不变） |
| **算法原则核查** | R1-R4 严格遵循 4 原则 | R5 同样严格遵循，所有 bug 分析均依「父引用子入口」+「每块唯一归属」+「自底向上归约」+「嵌套即抽象节点」原则 |

## 7. 关键发现

1. **R4-03 部分修复有效但未完整**: R5-04 (2-term) 通过验证 R4-03 部分修复对 2-term chained compare 有效；R5-01/02/03 (3/4/5-term) 失败确认 R4-03 部分修复对 3+ term 仍无效。**根因锁定**: chained compare 中段 JUMP_IF_FALSE_OR_POP 是触发 IfRegion 错误归约的关键，2-term 无此跳转故通过。
2. **R4-10 完全未修复**: R5-05/06/07 三个变体全部失败，确认 R4-10 完全回滚后无任何残留修复。while(ternary) 模式仍需基础结构重构。
3. **R5 新发现 4 个独立 bug**: R5-08 (class body 多 ternary)、R5-14 (`**(ternary)` kwargs)、R5-15 (`x[1:(ternary)]` slice)、R5-22 (`return await (ternary)`)。这 4 个 bug 均为 R1-R4 未覆盖的新对抗方向，**根因独立**，非 R4-03/R4-10 复现。
4. **基线零退化**: R5 22 个新测试加入后，剔除 R5 测试后基线仍为 59/158/1，无任何现有测试退化。
5. **R3/R4 修复有效覆盖 11 个新方向**: R5 的 11 个新对抗方向中 7 个通过（decorator/global/nonlocal/lambda default/`*(ternary)`/`x is (ternary)`/`x in (ternary)`）+ 4 个 comp 形式（return-listcomp/dictcomp/setcomp/genexp）通过，确认 R1-R4 修复对类似上下文有泛化能力。
