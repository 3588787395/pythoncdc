# Ternary 区域 Round 03 测试发现报告

## 测试基线
- 起点: Ternary R2 完成 (commit cba81b3)
- 基线结果: 116 passed / 58 failed / 1 skipped
- R3 新增测试: 20 个 `test_r3_*.py`
- R3 新测试结果: 9 passed / 11 failed
- 总计（含 R3 新增）: 125 passed / 69 failed / 1 skipped

## 新测试列表（共 20 个）

### R2 已知 bug 衍生变体（6 个）

| 测试 | 源码 | 类别 | 结果 |
|------|------|------|------|
| test_r3_ternary_chained_compare_left | `x = (a if cond else 1) < 10 < 100` | chained_compare (ternary 在左) | FAIL |
| test_r3_ternary_chained_compare_4way | `x = 0 < (a if cond else 1) < 10 < 100` | chained_compare (4-term) | FAIL |
| test_r3_ternary_await_assign | `async def f(): x = await (a if cond else b)` | await + assign | PASS |
| test_r3_ternary_await_expr | `async def f(): await (a if cond else b)` | await 无 return | FAIL |
| test_r3_ternary_return_arith_left | `def f(): return 1 + (a if cond else 0)` | return+arith (ternary 在右) | FAIL |
| test_r3_ternary_return_arith_mul | `def f(): return (a if cond else 1) * 2` | return+arith (乘法) | FAIL |

### R2 已知 bug 扩展场景（2 个）

| 测试 | 源码 | 类别 | 结果 |
|------|------|------|------|
| test_r3_ternary_return_call | `def f(): return foo(a if cond else 0)` | return+CALL | FAIL |
| test_r3_ternary_return_tuple | `def f(): return (a if cond else b), (c if cond else d)` | return+BUILD_TUPLE 多 ternary | FAIL |

### 全新探索场景（12 个）

| 测试 | 源码 | 类别 | 结果 |
|------|------|------|------|
| test_r3_ternary_try_handler | `try: pass\nexcept (E1 if cond else E2): pass` | except handler 类型 | FAIL |
| test_r3_ternary_while_cond | `while (a if cond else b): pass` | while 条件 | FAIL |
| test_r3_ternary_with_as | `with (ctx_a if cond else ctx_b) as x: pass` | with 上下文管理器 | FAIL |
| test_r3_ternary_decorator | `@(deco_a if cond else deco_b)\ndef f(): pass` | 装饰器 | PASS |
| test_r3_ternary_class_attr | `class A: x = a if cond else b` | 类属性 | PASS |
| test_r3_ternary_nested_func | `def outer():\n    def inner():\n        return a if cond else b\n    return inner()` | 嵌套函数 | PASS |
| test_r3_ternary_yield | `def g(): yield (a if cond else 0) + 1` | yield+arith | PASS |
| test_r3_ternary_global | `def f():\n    global x\n    x = a if cond else b` | global 赋值 | PASS |
| test_r3_ternary_aug_assign | `x += (a if cond else b)` | augmented assign | PASS |
| test_r3_ternary_raise_from | `raise E1 from (E2 if cond else E3)` | raise from | PASS |
| test_r3_ternary_raise_arg | `raise E(a if cond else b)` | raise 异常构造参数 | FAIL |
| test_r3_ternary_in_cond | `x = a if (b if c else d) else e` | 嵌套 ternary 在条件 | PASS |

## 11 个失败 Bug 详细分析

### Bug R3-01: chained_compare_left — `x = (a if cond else 1) < 10 < 100`
- **根因**: ternary 在 chained compare 左端时，merge_block 含 `SWAP / COPY 2 / COMPARE_OP / JUMP_IF_FALSE_OR_POP` 序列。merge_context 识别为 `compare` 但生成器仅发射 `Expr(IfExp)`，丢失 chained compare 后续段与赋值。
- **原始字节码（16 条）**: RESUME, LOAD_NAME cond, POP_JUMP_FORWARD_IF_FALSE, LOAD_NAME a, JUMP_FORWARD, LOAD_CONST 1, SWAP, COPY 2, COMPARE_OP, JUMP_IF_FALSE_OR_POP, LOAD_CONST 10, COMPARE_OP, SWAP, POP_TOP, STORE_NAME x, LOAD_CONST None, RETURN_VALUE
- **反编译字节码（10 条）**: RESUME, LOAD_NAME cond, LOAD_NAME a, LOAD_CONST 10, COMPARE_OP, LOAD_CONST None, RETURN_VALUE, LOAD_CONST None, RETURN_VALUE
- **反编译输出**: `if (cond): pass\nelse: a` (类似) — 丢失 chained compare 与赋值

### Bug R3-02: chained_compare_4way — `x = 0 < (a if cond else 1) < 10 < 100`
- **根因**: 同 R3-01，ternary 在 4-term chained compare 中段。需多次 COPY 2 复制 ternary 结果供后续比较段使用。
- **原始字节码（21 条）**: 含 2 次 SWAP/COPY 2/COMPARE_OP/JUMP_IF_FALSE_OR_POP
- **反编译字节码（10 条）**: 缺失全部 chained compare 段
- **反编译输出**: 丢失 chained compare 与赋值

### Bug R3-03: await_expr — `async def f(): await (a if cond else b)`
- **根因**: ternary 在 await 表达式（无 return/assign 包装）时，GET_AWAITABLE + SEND 循环消费 ternary 结果，POP_TOP 丢弃 await 结果。嵌套 code object 中 `await` 与 `POP_TOP` 丢失。
- **原始字节码（14 条）**: 含 GET_AWAITABLE/SEND/YIELD_VALUE/RESUME/JUMP_BACKWARD_NO_INTERRUPT/POP_TOP
- **反编译字节码（12 条）**: 缺 GET_AWAITABLE/SEND 等
- **反编译输出**: `async def f(): (a if cond else b)` — 丢失 `await`

### Bug R3-04: return_arith_left — `def f(): return 1 + (a if cond else 0)`
- **根因**: ternary 在 return + BINARY_OP 上下文中（ternary 在右），merge_block 不以单条 RETURN 结尾（BINARY_OP + RETURN_VALUE）。merge_context 未识别 return+arith 场景。
- **原始字节码（7 条）**: RESUME, LOAD_CONST 1, LOAD_GLOBAL cond, LOAD_GLOBAL a, LOAD_CONST 0, BINARY_OP +, RETURN_VALUE
- **反编译字节码（10 条）**: 多了 POP_TOP/LOAD_CONST/RETURN_VALUE，缺 BINARY_OP
- **反编译输出**: `def f(): (a if cond else 0)` — 丢失 `1 + ` 与 `return`

### Bug R3-05: return_arith_mul — `def f(): return (a if cond else 1) * 2`
- **根因**: 同 R3-04，BINARY_OP 是乘法。
- **反编译输出**: `def f(): (a if cond else 1)` — 丢失 `* 2` 与 `return`

### Bug R3-06: return_call — `def f(): return foo(a if cond else 0)`
- **根因**: ternary 在 return + CALL 上下文中，merge_block 含 `CALL + RETURN_VALUE`。merge_context 识别为 `compare` 但生成器仅发射 `Expr(IfExp)`，丢失 CALL 与 return。
- **原始字节码（8 条）**: RESUME, LOAD_GLOBAL cond, LOAD_GLOBAL a, LOAD_GLOBAL foo, LOAD_CONST 0, PRECALL, CALL, RETURN_VALUE
- **反编译字节码（10 条）**: 多了 POP_TOP/LOAD_CONST/RETURN_VALUE，缺 PRECALL/CALL
- **反编译输出**: `def f(): (a if cond else 0)` — 丢失 `foo(...)` 与 `return`

### Bug R3-07: return_tuple — `def f(): return (a if cond else b), (c if cond else d)`
- **根因**: 多个 ternary 作为 return tuple 元素，BUILD_TUPLE 在 merge_block 中消费两个 ternary 结果。第一个 ternary 后第二个 ternary 被忽略。
- **原始字节码（9 条）**: 含 BUILD_TUPLE + RETURN_VALUE
- **反编译字节码（11 条）**: 多了 POP_TOP/LOAD_CONST/RETURN_VALUE
- **反编译输出**: 丢失 BUILD_TUPLE 结构

### Bug R3-08: try_handler — `try: pass\nexcept (E1 if cond else E2): pass`
- **根因**: ternary 作为 except handler 的异常类型时，反编译器将 ternary 识别为 `if cond: pass\nelse: E2`（IfRegion）而非 IfExp。根本原因：except 子句的 `COMPARE_OP` 链与 ternary 的 `POP_JUMP_IF_FALSE` 冲突。
- **反编译输出**: `try:\n    pass\nexcept:\n    if cond:\n        pass\n    else:\n        E2` — 完全丢失 ternary 结构

### Bug R3-09: while_cond — `while (a if cond else b): pass`
- **根因**: ternary 作为 while 条件时，反编译器将 ternary 拆分为 if + while。根本原因：while 的 POP_JUMP_IF_FALSE 与 ternary 的 POP_JUMP_IF_FALSE 链冲突。
- **反编译输出**: `if a:\n    pass\nwhile cond and b:\n    if cond:\n        pass\n    a\n    continue` — 完全错乱

### Bug R3-10: with_as — `with (ctx_a if cond else ctx_b) as x: pass`
- **根因**: ternary 作为 with 上下文管理器时，BEFORE_WITH + STORE_NAME 消费 ternary 结果。反编译器丢失 ternary 结构，将 ctx_a 直接作为 with 上下文。
- **反编译输出**: `with (ctx_a)(cond, cond, cond, ctx_a):` 类似错乱结构

### Bug R3-11: raise_arg — `raise E(a if cond else b)`
- **根因**: ternary 作为 raise 异常构造函数参数时，CALL + RAISE_VARARGS 1 在 merge_block 中消费 ternary 结果。merge_context 识别为 call 但生成器仅发射 `Expr(IfExp)`，丢失 CALL 与 raise。
- **原始字节码（9 条）**: RESUME, LOAD_GLOBAL cond, LOAD_GLOBAL a, LOAD_GLOBAL b, LOAD_GLOBAL E, LOAD_CONST None, PRECALL, CALL, RAISE_VARARGS
- **反编译字节码（5 条）**: 缺 CALL/RAISE_VARARGS
- **反编译输出**: `(a if cond else b)` — 丢失 `E(...)` 与 `raise`

## 失败 bug 分类

### P0 — R2 已知限制衍生（3 类，6 个测试）
- **chained_compare** (R3-01, R3-02): ternary 在 chained compare 中/左
- **return_arith** (R3-04, R3-05, R3-06, R3-07): ternary 在 return + arith/call 中
- **await** (R3-03): ternary 在 await 无 return

### P1 — 嵌套 code object 内 return + 复合表达式（1 个测试）
- **return_tuple** (R3-07): 多个 ternary 在 return tuple

### P2 — 全新控制流冲突（4 个测试）
- **try_handler** (R3-08): ternary 与 except handler 类型冲突
- **while_cond** (R3-09): ternary 与 while 条件冲突
- **with_as** (R3-10): ternary 与 with 上下文管理器冲突
- **raise_arg** (R3-11): ternary 与 raise 异常构造参数

## 修复优先级（依协议：优先 R2 已知 3 个限制）

1. **R2-F return_arith** 类: R3-04, R3-05, R3-06, R3-07（4 个测试） — merge_context 增加 return+arith/call 识别
2. **R2-E chained_compare** 类: R3-01, R3-02（2 个测试） — merge_context=compare 时的链式比较段重建
3. **R2-F await** 类: R3-03（1 个测试） — await 上下文 SEND 循环节点重建
4. **R3-11 raise_arg**: return+call 类似机制，可顺带修复
5. **R3-07 return_tuple**: 多 ternary 在 return tuple，扩展 return 上下文
6. **R3-08/09/10 try_handler/while_cond/with_as**: 控制流冲突，R4 处理（不在本轮目标）

## 算法 4 原则核查

所有失败 bug 均符合「自底向上归约」「每块唯一归属」「嵌套即抽象节点」「父引用子入口」原则论证：
- ternary 作为内层区域，外层表达式（compare/return/await/raise）作为父区域引用 ternary 入口
- merge_block 的消费指令（COMPARE_OP/BINARY_OP/CALL/RETURN_VALUE/GET_AWAITABLE/RAISE_VARARGS）应归属到 ternary 父区域
- 当前反编译器将 merge_context 设为 'compare'/'return' 但生成器未发射完整父区域结构
