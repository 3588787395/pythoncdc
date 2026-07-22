# Ternary Region Round 04 — 测试发现报告

## 概览

- **R4 测试总数**: 23 个新测试（10 failed / 12 passed / 1 skipped）
- **新发现 bug**: 11 个（10 个 FAILED + 1 个 SKIPPED，SKIPPED 是反编译输出语法非法触发的「隐性 bug」）
- **回归状态**: 基线 61 failed / 133 passed / 1 skipped（无退化），添加 23 个 R4 测试后变为 71 failed / 145 passed / 2 skipped，增量与 R4 测试结果完全吻合
- **修改文件**: 仅新增 23 个测试文件 + 1 个调试脚本（`_r4_debug_dump.py`），**未修改任何源代码**
- **基线对比**: R3 完成时 61 failed → R4 后 61 + 10 = 71 failed（基线零退化，全部新增失败均来自 R4 新测试）

## 1. 统计摘要表

| 指标 | 数值 |
|------|------|
| R4 测试文件数 | 23 |
| R4 测试 passed | 12 |
| R4 测试 failed | 10 |
| R4 测试 skipped | 1（实际为隐性 bug） |
| 新发现真实 bug | 11（≥10 完成标准） |
| Ternary 区域基线（R3 完成） | 61 failed / 133 passed / 1 skipped（共 195 测试） |
| Ternary 区域当前（R4 完成后） | 71 failed / 145 passed / 2 skipped（共 218 测试） |
| 基线退化 | **0**（剔除 R4 测试后基线仍为 61/133/1） |

## 2. R4 测试文件列表

| # | 文件 | 状态 | 错误类别 |
|---|------|------|---------|
| 1 | test_r4_ternary_attr_assign.py | FAILED | ternary 在 setattr 调用中间参数位置 — 参数丢失 |
| 2 | test_r4_ternary_await_assign.py | PASSED | — |
| 3 | test_r4_ternary_await_expr.py | FAILED | ternary 在 await 表达式（无 return）— await 结构丢失 |
| 4 | test_r4_ternary_chained_compare_4way.py | FAILED | ternary 在 4-term chained compare 中段 — 结构退化为 if |
| 5 | test_r4_ternary_chained_compare_left.py | PASSED | — |
| 6 | test_r4_ternary_dict_value.py | FAILED | dict 多 ternary value — 第一个 key 错乱 |
| 7 | test_r4_ternary_in_assert.py | PASSED | — |
| 8 | test_r4_ternary_in_call_kwargs.py | PASSED | — |
| 9 | test_r4_ternary_in_del_target.py | FAILED | ternary 作为 del subscript 索引 — del 结构丢失 |
| 10 | test_r4_ternary_in_dict_key.py | PASSED | — |
| 11 | test_r4_ternary_in_for_iter_var.py | PASSED | — |
| 12 | test_r4_ternary_in_format.py | FAILED | ternary 在 .format() 多参数 — 调用结构丢失 |
| 13 | test_r4_ternary_in_fstring.py | SKIPPED | ternary 在 f-string 多段插值 — 反编译产生非法 `return` |
| 14 | test_r4_ternary_in_lambda_call.py | PASSED | — |
| 15 | test_r4_ternary_in_print.py | PASSED | — |
| 16 | test_r4_ternary_in_raise_from.py | PASSED | — |
| 17 | test_r4_ternary_in_yield.py | PASSED | — |
| 18 | test_r4_ternary_in_yield_from.py | PASSED | — |
| 19 | test_r4_ternary_set_elem.py | FAILED | set 多 ternary 元素 — 第一个 ternary 退化为独立表达式 |
| 20 | test_r4_ternary_subscript_assign.py | PASSED | — |
| 21 | test_r4_ternary_try_handler_type.py | FAILED | ternary 作为 except handler 异常类型 — 退化为 if 语句 |
| 22 | test_r4_ternary_while_cond.py | FAILED | ternary 作为 while 条件 — 退化为 if + while + continue |
| 23 | test_r4_ternary_with_ctx_mgr.py | FAILED | ternary 作为 with 上下文管理器 — 引入未知 `context()` 调用 |

## 3. Bug 详细分析

### Bug R4-01: setattr 调用 — ternary 在中间参数位置导致末位参数丢失

**文件**: `test_r4_ternary_attr_assign.py`
**状态**: FAILED — 指令数不匹配 13 vs 12（重编缺失 `LOAD_CONST 1`）
**源码**:
```python
setattr(obj, 'a' if cond else 'b', 1)
```
**反编译结果**:
```python
setattr(obj, 'a' if cond else 'b')
```
**问题分解**:
- 子 bug 1: 反编译结果丢失了 setattr 调用的第 3 个位置参数 `1`
- 子 bug 2: PRECALL/CALL 的参数计数从 3 降为 2，但 merge_block 中 cond preload 链含 ternary 后的 `LOAD_CONST 1`
- 子 bug 3: ternary 在调用中间参数位置（第 2 参数），后跟非 ternary 参数 `1`，参数收集不完整

**字节码对比**:
- 原始 13 条 / 重编 12 条
- 原始特有: `LOAD_CONST 1, PRECALL 3, CALL 3`
- 重编缺失: `LOAD_CONST 1`（PRECALL/CALL 计数也从 3 降为 2）

**根因推测**: `_detect_ternary_context` 在 cond_block 中识别 `PUSH_NULL + LOAD_NAME setattr` 作为 call 上下文，但 `_compute_ternary_cond_preload_exprs` 提取 preload_exprs 时只覆盖到 ternary 的最后一个 LOAD 指令（`LOAD_CONST 'b'`），没有继续收集 ternary 之后的 `LOAD_CONST 1`。`_build_ternary_no_target_consumer_stmt` 在重建 Call 时 `args=[ternary]`，丢失了 ternary 之后的额外位置参数。依「父引用子入口」原则，setattr 调用的所有位置参数（obj, ternary, 1）都应通过 cond_block preload + merge_block CALL 一并重建。

### Bug R4-02: await 表达式（无 return）— await 结构丢失

**文件**: `test_r4_ternary_await_expr.py`
**状态**: FAILED — 嵌套 code object 指令数不匹配 14 vs 12
**源码**:
```python
async def f():
    await (a if cond else b)
```
**反编译结果**:
```python
async def f():
    (a if cond else b)
```
**问题分解**:
- 子 bug 1: 反编译结果丢失了 `await` 关键字，ternary 直接作为表达式语句
- 子 bug 2: 嵌套 code object 内 `GET_AWAITABLE + LOAD_CONST None + YIELD_VALUE + RESUME 3 + JUMP_BACKWARD_NO_INTERRUPT + POP_TOP` 全部丢失
- 子 bug 3: 重编字节码中 ternary 的两个分支各自走 `POP_TOP + LOAD_CONST None + RETURN_VALUE` 路径，原始则共享 `GET_AWAITABLE + YIELD_VALUE` await 循环

**字节码对比**:
- 原始 14 条 / 重编 12 条
- 原始特有: `LOAD_GLOBAL b, GET_AWAITABLE 0, LOAD_CONST None, YIELD_VALUE None, RESUME 3, JUMP_BACKWARD_NO_INTERRUPT 50, POP_TOP None`
- 重编缺失: `GET_AWAITABLE, YIELD_VALUE, JUMP_BACKWARD_NO_INTERRUPT`（await 关键指令全部丢失）

**根因推测**: R3 fix_report 已识别为 R3-03 已知限制 — `await (ternary)` 无 return/assign 时，`GET_AWAITABLE + SEND` 循环在 merge_block 中消费 ternary 结果，POP_TOP 丢弃 await 结果。`_build_ternary_no_target_consumer_stmt` 未识别 await 上下文模式（无 STORE_*/RETURN_VALUE，只有 GET_AWAITABLE + YIELD_VALUE + POP_TOP 链），导致 await 被剥离为普通表达式语句。R3 Pattern 6 仅处理 `return (ternary) wrapped`，未覆盖 `await (ternary) dropped`。

### Bug R4-03: chained compare 4 路 — ternary 在中段导致结构退化为 if

**文件**: `test_r4_ternary_chained_compare_4way.py`
**状态**: FAILED — 指令数不匹配 21 vs 10
**源码**:
```python
r = 0 < (a if cond else b) < 10 < 100
```
**反编译结果**:
```python
if (0 < (a if cond else b)):
    pass
```
**问题分解**:
- 子 bug 1: 反编译结果丢失了 chained compare 的后续段 `< 10 < 100`
- 子 bug 2: ternary 之后 merge_block 含 `SWAP, COPY 2, COMPARE_OP, JUMP_IF_FALSE_OR_POP, LOAD_CONST 10, ...` 链，反编译器误判为 if 条件
- 子 bug 3: `STORE_NAME r` 完全丢失，赋值上下文未保留

**字节码对比**:
- 原始 21 条 / 重编 10 条
- 原始特有: `SWAP 2, COPY 2, COMPARE_OP <, JUMP_IF_FALSE_OR_POP 50, LOAD_CONST 10, SWAP 2, COPY 2, COMPARE_OP <, JUMP_IF_FALSE_OR_POP 50, LOAD_CONST 100, COMPARE_OP <, SWAP 2, POP_TOP, STORE_NAME r`
- 重编缺失: chained compare 的 SWAP/COPY/JUMP_IF_FALSE_OR_POP 序列全部丢失，仅保留首个 `COMPARE_OP <`

**根因推测**: R3-01/02 已识别为已知限制 — chained compare 与 TernaryRegion 的边界识别冲突。ternary 在 chained compare 中段时，`SWAP + COPY 2 + COMPARE_OP + JUMP_IF_FALSE_OR_POP` 是 chained compare 的特征序列（COPY 2 复制 ternary 结果供后续比较段），但 `_detect_ternary_pattern` 将 `JUMP_IF_FALSE_OR_POP` 误判为 if 条件跳转，触发 IfRegion 抢占。R3 fix_report 建议「调整 chained_compare IfRegion 与 TernaryRegion 的边界识别」，R4 用变量 `b` 替代常量 `1` 排除常量折叠干扰，仍稳定复现。

### Bug R4-04: dict 多 ternary value — 第一个 key 错乱为第二个 key

**文件**: `test_r4_ternary_dict_value.py`
**状态**: FAILED — 指令 1 参数不匹配: `k` vs `k2` (op=LOAD_NAME)
**源码**:
```python
d = {k: a if cond else b, k2: c if d else e}
```
**反编译结果**:
```python
d = {k2: a if cond else b, k2: c if d else e}
```
**问题分解**:
- 子 bug 1: 第一个 dict 项的 key `k` 被错误反编译为 `k2`
- 子 bug 2: `extract_dict_key_from_block` 取错了 key — 取了 cond_block 中最后一个 LOAD_NAME（`k2`）而非与当前 ternary 配对的 key（`k`）
- 子 bug 3: 重编字节码的 dict 项顺序看起来正确，但 key 名称错乱意味着 BUILD_MAP 的 (key, value) 配对在反编译阶段已错位

**字节码对比**:
- 原始 13 条 / 重编 13 条（数量一致，但首条 LOAD_NAME argval 不同）
- 原始特有: `LOAD_NAME k, LOAD_NAME cond, LOAD_NAME a, LOAD_NAME b, LOAD_NAME k2, ...`
- 重编缺失: `LOAD_NAME k`（被替换为 `LOAD_NAME k2`）

**根因推测**: `_detect_ternary_context` 通过 `RegionAnalyzer.extract_dict_key_from_block(cond_block)` 提取 dict key，但在多个 ternary 共享或相邻的 cond_block 中，该方法线性扫描 LOAD_NAME 取最后一个，而非根据 ternary 的字节码偏移定位对应的 key。`_compute_ternary_cond_preload_exprs` 收集 preload_exprs 时也未排除后续 ternary 的 key preload，导致第一个 ternary 拿到第二个 ternary 的 key。依「每块唯一归属」原则，每个 ternary 的 cond_block 应只归属该 ternary，但多 ternary 共享 merge_block 的 BUILD_MAP 时 preload 边界识别错乱。

### Bug R4-05: del subscript 索引 — del 结构完全丢失

**文件**: `test_r4_ternary_in_del_target.py`
**状态**: FAILED — 反编译结果丢失 `del x[...]` 结构
**源码**:
```python
del x[a if cond else b]
```
**反编译结果**:
```python
(a if cond else b)
```
**问题分解**:
- 子 bug 1: 反编译结果丢失了 `del` 关键字和 subscript 对象 `x`
- 子 bug 2: 重编字节码中 `DELETE_SUBSCR` 完全消失，被 `POP_TOP` 取代
- 子 bug 3: ternary 被当作顶层独立表达式语句（`Expr(IfExp)` + POP_TOP），而非 del subscript 的索引

**字节码对比**:
- 原始 6 条 / 重编 6 条（数量一致但指令语义完全不同）
- 原始特有: `LOAD_NAME x, LOAD_NAME cond, LOAD_NAME a, LOAD_NAME b, DELETE_SUBSCR None`
- 重编缺失: `LOAD_NAME x, DELETE_SUBSCR`（被替换为 `LOAD_NAME a, POP_TOP, LOAD_NAME b, POP_TOP, LOAD_CONST None, RETURN_VALUE`）

**根因推测**: `_try_build_ternary_store_assign` 处理 `STORE_SUBSCR`（R2 已修复 subscript_assign），但 `DELETE_SUBSCR` 未纳入 store assign 模式识别。`_build_ternary_no_target_consumer_stmt` 也未识别 del 上下文 — merge_block 中只有 `DELETE_SUBSCR` + 隐式 return，没有 STORE_*/RETURN_VALUE，被默认当作独立表达式语句 POP_TOP 丢弃。依「父引用子入口」原则，`del x[ternary]` 的父 Delete 通过 cond_block 的 `LOAD_NAME x` + merge_block 的 `DELETE_SUBSCR` 引用 ternary 子节点，但反编译器未识别 DELETE_SUBSCR 作为消费指令。

### Bug R4-06: .format() 多 ternary 参数 — 调用结构丢失

**文件**: `test_r4_ternary_in_format.py`
**状态**: FAILED — 指令数不匹配 14 vs 11
**源码**:
```python
x = "{}-{}".format(a if cond else b, c if d else e)
```
**反编译结果**:
```python
(a if cond else b)
x = (c if d else e)
```
**问题分解**:
- 子 bug 1: 反编译结果丢失了 `"{}".format(...)` 调用结构
- 子 bug 2: 第一个 ternary 被当作独立表达式语句 POP_TOP，第二个 ternary 被赋给 `x`
- 子 bug 3: `LOAD_CONST '{}-{}'` + `LOAD_METHOD format` + `PRECALL` + `CALL` 链完全丢失
- 子 bug 4: 原始两条 ternary 共享 merge_block 的 BUILD 调用，反编译器把它们拆成两条独立语句

**字节码对比**:
- 原始 14 条 / 重编 11 条
- 原始特有: `LOAD_CONST '{}-{}', LOAD_METHOD format, PRECALL 2, CALL 2, STORE_NAME x`
- 重编缺失: `LOAD_CONST '{}-{}', LOAD_METHOD format, PRECALL, CALL`（format 调用链全部丢失）

**根因推测**: `_try_build_ternary_chained_container` 处理多个 ternary 共享 merge_block 的 chained container 模式（list/tuple/set/dict），但未覆盖 `LOAD_METHOD + CALL` 调用模式。第一个 ternary 的 cond_block 含 `LOAD_CONST '{}-{}', LOAD_METHOD format`（format callable preload），但 `_detect_ternary_context` 的 call 模式识别未触发（可能因 PUSH_NULL 缺失 + LOAD_METHOD 不在识别列表）。两个 ternary 被分别处理为独立语句，第一个 POP_TOP 丢弃，第二个 STORE_NAME。R3 Pattern 6 仅处理 return 上下文的 wrapped call，未覆盖普通赋值的 wrapped call。

### Bug R4-07: f-string 多 ternary 插值 — 反编译产生非法 `return`（隐性 bug）

**文件**: `test_r4_ternary_in_fstring.py`
**状态**: SKIPPED — 重编译失败 SyntaxError: `'return' outside function`（反编译输出在模块顶层出现 `return`，是隐性 bug）
**源码**:
```python
x = f"{a if cond else b}-{c if d else e}"
```
**反编译结果**:
```python
(a if cond else b)
return f'-{(c if d else e)}'
```
**问题分解**:
- 子 bug 1: 反编译结果在模块顶层出现 `return` 语句（语法非法）
- 子 bug 2: 第一个 ternary 被当作独立表达式语句 `(a if cond else b)`
- 子 bug 3: 第二个 ternary 触发 R3 Pattern 6 Return 模式（`return f'-{...}'`），但 Pattern 6 的 POP_TOP 守卫未拦截 `BUILD_STRING + STORE_NAME` 上下文
- 子 bug 4: f-string 的 `BUILD_STRING 3` 与 `STORE_NAME x` 赋值链未识别为赋值上下文

**字节码对比**:
- 原始 14 条 / 重编 0 条（重编译失败）
- 原始特有: `FORMAT_VALUE, LOAD_CONST '-', FORMAT_VALUE, BUILD_STRING 3, STORE_NAME x`
- 重编缺失: 全部（重编译失败，无法对比）

**根因推测**: R3 Pattern 6 的 POP_TOP 守卫和 STORE_* 守卫均未覆盖此场景。两个 ternary 共享 merge_block 含 `BUILD_STRING 3 + STORE_NAME x`，但反编译器把第一个 ternary 剥离为独立表达式（POP_TOP），第二个 ternary 的 merge_block 残留 `BUILD_STRING 3 + STORE_NAME x`，Pattern 6 误判 `BUILD_STRING` 为 wrapping 指令 + `RETURN_VALUE`（隐式 return None）触发 Return 模式，但 `STORE_NAME x` 已在 merge_block 中，Pattern 6 的 `_has_store` 守卫应拦截但未拦截（可能因 `BUILD_STRING` 在 `STORE_NAME` 之前，守卫检查顺序问题）。依「每块唯一归属」原则，f-string 的 `BUILD_STRING + STORE_NAME` 应归属 Assign 父区域，不归属 Return。

### Bug R4-08: set 多 ternary 元素 — 第一个 ternary 退化为独立表达式

**文件**: `test_r4_ternary_set_elem.py`
**状态**: FAILED — 指令数不匹配 14 vs 15（重编多 1 条 POP_TOP）
**源码**:
```python
s = {a if cond else b, c if d else e, f if g else h}
```
**反编译结果**:
```python
(a if cond else b)
s = {c if d else e, f if g else h}
```
**问题分解**:
- 子 bug 1: 反编译结果把第一个 ternary 剥离为独立表达式语句（POP_TOP 丢弃）
- 子 bug 2: `BUILD_SET 3` 退化为 `BUILD_SET 2`，丢失第一个元素
- 子 bug 3: 三个 ternary 共享 merge_block 的 BUILD_SET，但 chained container 模式只识别后两个

**字节码对比**:
- 原始 14 条 / 重编 15 条
- 原始特有: `LOAD_NAME cond, LOAD_NAME a, LOAD_NAME b, LOAD_NAME d, LOAD_NAME c, LOAD_NAME e, LOAD_NAME g, LOAD_NAME f, LOAD_NAME h, BUILD_SET 3`
- 重编缺失: `BUILD_SET 3`（退化为 `BUILD_SET 2`），第一个 ternary 的 `LOAD_NAME cond` 被替换为 `POP_TOP`
- 重编特有: 多出 `POP_TOP None`（第一个 ternary 被当作独立表达式丢弃）

**根因推测**: `_try_build_ternary_chained_container` 识别 set 容器模式时，从 innermost（最后）ternary 反向遍历收集元素，但 outermost（第一）ternary 的 cond_block 未被纳入 chain。可能是 chain 收集循环的终止条件过严 — 当 outermost ternary 的 entry 不直接连接到 merge_block 时（中间还有 innermost ternary 的 cond_block），chain 断裂，outermost 被单独处理为 Expr 语句。R2 `test_r2_ternary_in_set.py` 已测 2 元素 set 通过，R4 测 3 元素 set 时第一个元素丢失，说明 chained container 在 3+ 元素时 chain 边界处理有缺陷。

### Bug R4-09: except handler 异常类型 — ternary 退化为 if 语句

**文件**: `test_r4_ternary_try_handler_type.py`
**状态**: FAILED — 反编译结果未找到 IfExp 节点（退化为 if 语句）
**源码**:
```python
try:
    pass
except (E1 if cond else E2) as e:
    pass
```
**反编译结果**:
```python
try:
    e = None
    del e
except:
    if cond:
        pass
    else:
        E2
```
**问题分解**:
- 子 bug 1: 反编译结果丢失了 ternary 的 IfExp 结构，退化为 if 语句
- 子 bug 2: `except (E1 if cond else E2) as e` 退化为 `except:` 裸捕获 + handler 内 if 语句
- 子 bug 3: `E1` 完全丢失（ternary true 分支值未保留），仅保留 `E2`
- 子 bug 4: except 的 `as e` 绑定被剥离为 `e = None; del e` 显式管理

**字节码对比**:
- 原始 20 条 / 重编 20 条（数量一致但语义错乱）
- 原始特有: `CHECK_EXC_MATCH None, STORE_NAME e, POP_EXCEPT, LOAD_CONST None, STORE_NAME e, DELETE_NAME e`
- 重编缺失: `CHECK_EXC_MATCH`（裸 except 不匹配异常类型），`LOAD_NAME E1` 完全丢失

**根因推测**: R3-08 已识别为已知限制 — ternary 作为 except handler 异常类型时，`CHECK_EXC_MATCH` 在 merge_block 中消费 ternary 结果，与 except 子句的 `COMPARE_OP` 链冲突。`_detect_ternary_pattern` 未识别 except handler 上下文，ternary 的 cond_block 被误识别为顶层 if 头，except 子句被剥离为裸 `except:`，handler 内放置退化的 if-else。R4 增加 `as e` 绑定加重复杂度，仍稳定复现。

### Bug R4-10: while 条件 — ternary 退化为 if + while + continue

**文件**: `test_r4_ternary_while_cond.py`
**状态**: FAILED — 反编译结果未找到 IfExp 节点（退化为 if + while）
**源码**:
```python
while (a if cond else b):
    x = 1
```
**反编译结果**:
```python
if a:
    pass
while cond and b:
    x = 1
    if cond:
        pass
    a
    continue
```
**问题分解**:
- 子 bug 1: 反编译结果丢失了 ternary IfExp 结构
- 子 bug 2: ternary 的两个分支 `a`/`b` 被错位放置：`a` 退化为顶层 if 语句，`b` 进入 while 条件 `cond and b`
- 子 bug 3: while 循环体内出现莫名其妙的 `if cond: pass` + `a` + `continue`
- 子 bug 4: ternary 的 cond_block 与 while 的 condition_block 边界混淆

**字节码对比**:
- 原始 16 条 / 重编 13 条
- 原始特有: `LOAD_NAME cond, LOAD_NAME a, LOAD_NAME b`（ternary 三个值），`LOAD_CONST 1, STORE_NAME x`（循环体）
- 重编缺失: while 条件中 ternary 的 IfExp 结构完全丢失，循环体出现额外的 `LOAD_NAME a, POP_TOP` 和 `continue`

**根因推测**: R3-09 已识别为已知限制 — ternary 作为 while 条件时，与 while 的 `POP_JUMP_IF_FALSE` 冲突。`_detect_ternary_pattern` 中的 `has_jump_forward_skip` 路径尝试处理 ternary-in-while-condition 模式，但识别条件过严（要求 false_block 不以 POP_TOP 开头等），未触发 ternary 归约。ternary 的 cond_block 被误识别为顶层 IfRegion，while 的循环回边被错位为 `continue` 语句。R3 fix_report 建议「在 while 条件位置识别 ternary，处理 while 的 POP_JUMP_IF_FALSE 与 ternary 的冲突」，R4 用非空循环体 `x = 1` 加重复杂度，仍稳定复现且退化更严重。

### Bug R4-11: with 上下文管理器 — 引入未知 `context()` 调用

**文件**: `test_r4_ternary_with_ctx_mgr.py`
**状态**: FAILED — 指令数不匹配 26 vs 31（重编多 5 条：`POP_TOP, PUSH_NULL, LOAD_NAME context, PRECALL, CALL`）
**源码**:
```python
with (ctx_a if cond else ctx_b) as x:
    pass
```
**反编译结果**:
```python
(ctx_a if cond else ctx_b)
with context() as x: pass
```
**问题分解**:
- 子 bug 1: 反编译结果丢失了 ternary 作为 with 上下文管理器的结构
- 子 bug 2: ternary 被剥离为独立表达式语句（POP_TOP 丢弃）
- 子 bug 3: with 语句引入未知的 `context()` 函数调用（源码中无此函数）
- 子 bug 4: `BEFORE_WITH` 的消费链未识别为 with 上下文管理器位置

**字节码对比**:
- 原始 26 条 / 重编 31 条
- 原始特有: `LOAD_NAME ctx_a, LOAD_NAME ctx_b, BEFORE_WITH None, STORE_NAME x`
- 重编缺失: ternary 的 `ctx_a`/`ctx_b` 直接被 POP_TOP 丢弃
- 重编特有: `POP_TOP None, PUSH_NULL None, LOAD_NAME context, PRECALL 0, CALL 0`（凭空引入 context() 调用）

**根因推测**: R3-10 已识别为已知限制 — ternary 作为 with 上下文管理器时，`BEFORE_WITH` + `STORE_NAME` 在 merge_block 中消费 ternary 结果。`_build_ternary_no_target_consumer_stmt` 未识别 with 上下文模式，ternary 被当作独立表达式 POP_TOP 丢弃。WithRegion 的 AST 生成器在缺少上下文管理器表达式时，可能从符号表 fallback 调用一个名为 `context` 的全局函数（推测是 WithRegion 的兜底逻辑）。R3 fix_report 建议「在 with 上下文管理器位置识别 ternary，处理 BEFORE_WITH + STORE_NAME 消费链」，R4 重测仍稳定复现，且额外暴露了 `context()` 兜底调用的副作用。

## 4. 错误模式归类（按根因分组）

### 模式 A: ternary 在调用中间参数位置（参数收集不完整）— 1 个 bug
- R4-01 setattr 调用：ternary 后的位置参数 `1` 丢失

**根因**: `_compute_ternary_cond_preload_exprs` + `_build_ternary_no_target_consumer_stmt` 在 call 上下文重建 Call AST 时，args 列表只包含 ternary，未包含 ternary 之后的位置参数。

### 模式 B: ternary 在父语句消费指令未识别场景（无 STORE/RETURN）— 4 个 bug
- R4-02 await_expr: `GET_AWAITABLE + YIELD_VALUE` 未识别
- R4-05 del_target: `DELETE_SUBSCR` 未识别
- R4-09 try_handler_type: `CHECK_EXC_MATCH` 未识别
- R4-11 with_ctx_mgr: `BEFORE_WITH` 未识别

**根因**: `_build_ternary_no_target_consumer_stmt` 的 consumer 模式识别仅覆盖 STORE_*/RETURN_VALUE/RAISE_VARARGS/BUILD_*/PRECALL+CALL 等已知模式，未覆盖 `GET_AWAITABLE`、`DELETE_SUBSCR`、`CHECK_EXC_MATCH`、`BEFORE_WITH` 等 Python 特定语句的消费指令。ternary 被默认当作独立表达式语句 POP_TOP 丢弃。

### 模式 C: chained compare 边界冲突（R3 已知限制）— 1 个 bug
- R4-03 chained_compare_4way: ternary 在 chained compare 中段退化为 if

**根因**: `_detect_ternary_pattern` 将 `JUMP_IF_FALSE_OR_POP` 误判为 if 条件跳转，触发 IfRegion 抢占。chained compare 的 `SWAP + COPY 2 + COMPARE_OP + JUMP_IF_FALSE_OR_POP` 序列未被识别为 chained compare 特征。

### 模式 D: 多 ternary 共享 merge_block 的 chained container 边界缺陷 — 4 个 bug
- R4-04 dict_value: 多 key dict 的第一个 key 错乱（`extract_dict_key_from_block` 取错 key）
- R4-06 in_format: `LOAD_METHOD + CALL` chained container 未识别（第一个 ternary 被剥离为独立表达式）
- R4-07 in_fstring: `BUILD_STRING + STORE_NAME` chained container 未识别（第二个 ternary 触发 Pattern 6 Return 误判）
- R4-08 set_elem: 3 元素 set 的第一个 ternary 被剥离为独立表达式（chained container chain 边界断裂）

**根因**: `_try_build_ternary_chained_container` 的 chain 收集循环从 innermost 反向遍历，但 outermost 边界处理有缺陷 — 当 outermost ternary 的 entry 不直接连接 merge_block 时，chain 断裂。同时 `_detect_ternary_context` 的 container 类型识别仅覆盖 list/tuple/set/dict/call，未覆盖 `LOAD_METHOD + CALL`（format 调用）、`BUILD_STRING`（f-string）等扩展模式。

### 模式 E: while 条件 ternary 退化为 if + while（R3 已知限制）— 1 个 bug
- R4-10 while_cond: ternary 退化为顶层 if + while `cond and b` + 循环体 `continue`

**根因**: R3-09 已知限制 — ternary 作为 while 条件时，与 while 的 `POP_JUMP_IF_FALSE` 冲突。`_detect_ternary_pattern` 的 `has_jump_forward_skip` 路径识别条件过严，未触发 ternary 归约，ternary 的 cond_block 被误识别为 IfRegion。

## 5. 修复优先级建议

### P0 优先级（影响多场景，根因集中）
1. **模式 D: chained container chain 边界缺陷**（4 个 bug: R4-04, R4-06, R4-07, R4-08）
   - 影响: dict/set/f-string/format 多 ternary 场景全部受影响
   - 修复方向: 完善 `_try_build_ternary_chained_container` 的 chain 收集逻辑，覆盖 `LOAD_METHOD + CALL`、`BUILD_STRING + STORE_NAME` 模式；修复 `extract_dict_key_from_block` 在多 key 场景的 key 定位
   - 风险: 需要回归 R1-R3 的 chained container 测试

2. **模式 B: 父语句消费指令未识别**（4 个 bug: R4-02, R4-05, R4-09, R4-11）
   - 影响: await/del/except handler/with ctx mgr 四类语句全部受影响
   - 修复方向: 扩展 `_build_ternary_no_target_consumer_stmt` 的 consumer 模式识别，新增 `GET_AWAITABLE`、`DELETE_SUBSCR`、`CHECK_EXC_MATCH`、`BEFORE_WITH` 分支
   - 风险: 需要确保新增分支不与 IfRegion/WhileRegion/WithRegion/TryRegion 抢占

### P1 优先级（单一场景，R3 已知限制延续）
3. **模式 C: chained compare 边界冲突**（1 个 bug: R4-03）
   - 修复方向: 调整 chained_compare IfRegion 与 TernaryRegion 的边界识别，识别 `SWAP + COPY 2 + COMPARE_OP + JUMP_IF_FALSE_OR_POP` 序列为 chained compare 特征
4. **模式 E: while 条件 ternary**（1 个 bug: R4-10）
   - 修复方向: 放宽 `_detect_ternary_pattern` 的 `has_jump_forward_skip` 路径识别条件

### P2 优先级（孤立场景）
5. **模式 A: ternary 在调用中间参数位置**（1 个 bug: R4-01）
   - 修复方向: `_compute_ternary_cond_preload_exprs` 在 call 上下文下继续收集 ternary 之后的位置参数

## 6. 与 R1-R3 的区别

### 与 R1 的区别
- **R1** 关注 ternary 在常见容器/语句中的基础场景（list/tuple/dict/call/return/assert/with/lambda/compare 等），多为单 ternary + 简单容器
- **R4** 聚焦 **多 ternary 共享 merge_block 的 chained container 边界缺陷**（模式 D，4 个 bug），以及 **R3 未覆盖的父语句消费指令**（模式 B，4 个 bug）

### 与 R2 的区别
- **R2** 扩展 ternary 在更多表达式位置（attribute/binop/subscript/yield/format/fstring 等），仍以单 ternary 为主
- **R4** 测试 **多 ternary 在 dict value、set 元素、format 调用、f-string 插值等 chained container 场景**，发现 R2 已通过的 set/dict 单 ternary 场景在 3+ 元素时退化

### 与 R3 的区别
- **R3** 主要修复 `return + arith/call/tuple`、`raise E(ternary)` 等 return/raise 上下文的 ternary wrapping，引入 Pattern 6（return wrapped）
- **R4** 暴露 **Pattern 6 的 POP_TOP/STORE_* 守卫在多 ternary chained container 场景下的不足**（R4-07 f-string 第二个 ternary 触发 Pattern 6 Return 误判），以及 **R3 留下的 6 个已知限制在 R4 加重变体下仍稳定复现**（R4-02/03/09/10/11 是 R3-03/01/02/08/09/10 的变体）
- **R4 新发现的非 R3 已知限制 bug**: R4-01 setattr 中间参数、R4-04 dict 多 key 错乱、R4-05 del subscript、R4-06 format 调用、R4-07 f-string return 误判、R4-08 set 3 元素 chain 断裂 — 6 个新根因，均不在 R3 已知限制清单中

### R4 新增 bug 类别统计

| 类别 | bug 数 | 是否 R3 已知限制 |
|------|--------|-----------------|
| chained container chain 边界缺陷（模式 D） | 4 | 否（新发现） |
| 父语句消费指令未识别（模式 B） | 4 | 部分是 R3 已知限制（R3-03 await, R3-08 try, R3-10 with），R4-05 del 是新发现 |
| chained compare 边界冲突（模式 C） | 1 | 是（R3-01/02） |
| while 条件 ternary（模式 E） | 1 | 是（R3-09） |
| 调用中间参数位置（模式 A） | 1 | 否（新发现） |
| **总计** | **11** | 5 个 R3 已知 + 6 个 R4 新发现 |

## 7. 回归验证

### R4 新测试运行结果
```
23 个 R4 测试: 10 failed / 12 passed / 1 skipped（11 个真实 bug，含 1 个隐性 SKIPPED）
执行时间: 0.81s
```

### Ternary 区域全量回归（含 R4）
```
基线（R3 完成）: 61 failed, 133 passed, 1 skipped (195 测试)
R4 测试添加后（无修复）: 71 failed, 145 passed, 2 skipped (218 测试)
```

### 基线退化验证（剔除 R4 测试）
```
61 failed, 133 passed, 1 skipped (195 测试，与基线完全一致)
```

### 退化分析
- 基线 61 failed → 现 71 failed（增量 +10，全部来自 R4 新测试的 FAILED）
- 基线 133 passed → 现 145 passed（增量 +12，全部来自 R4 新测试的 PASSED）
- 基线 1 skipped → 现 2 skipped（增量 +1，来自 R4 新测试的 SKIPPED）
- **基线零退化**: 剔除 R4 测试后基线仍为 61/133/1，与 R3 完成时完全一致
- **未修改任何源代码**，所有新增失败均来自 R4 新测试发现的真实 bug

## 附录: 验证命令

```bash
# 运行所有 R4 新测试
cd /workspace && python -m pytest tests/exhaustive/ternary/test_r4_*.py --tb=short -q

# 运行全量 ternary 回归
cd /workspace && python -m pytest tests/exhaustive/ternary/ --tb=no -q

# 验证基线不退化（剔除 R4 测试）
cd /workspace && python -m pytest tests/exhaustive/ternary/ \
  --ignore=tests/exhaustive/ternary/test_r4_ternary_attr_assign.py \
  --ignore=tests/exhaustive/ternary/test_r4_ternary_await_assign.py \
  ... (忽略所有 23 个 R4 测试文件) \
  --tb=no -q
```
