# Ternary Region Round 03 — 修复报告

## 修复概览

- **测试总数**: 20 个 R3 新测试（11 失败 / 9 通过）
- **已修复 R3 bug**: 5 个（R3-04, R3-05, R3-06, R3-07, R3-11）
- **顺带修复基线 bug**: 3 个（R2-F return_arith, R1 Bug 12 lambda_complex, R1 Bug 17 return_two_ternary）
- **未修复 R3 bug**: 6 个（R3-01/02/03/08/09/10，留待 R4+）
- **回归状态**: 58 failed → 55 failed（基线减 3）；新增 20 R3 测试后：61 failed / 133 passed / 1 skipped（无退化）
- **修改文件**: `core/cfg/region_ast_generator.py`（仅 1 个文件，3 处修改）

## 修改文件清单

| 文件 | 改动位置 | 改动内容 |
|------|---------|---------|
| `core/cfg/region_ast_generator.py` | `_build_ternary_no_target_consumer_stmt` ~L17679 | 新增 `_ends_with_return` 标记记录（剥离 RETURN 前的状态） |
| `core/cfg/region_ast_generator.py` | `_build_ternary_no_target_consumer_stmt` ~L17726 | 扩展 raise 模式：`raise E(ternary)` 用 preload_exprs 重建 Call(E, [ternary]) |
| `core/cfg/region_ast_generator.py` | `_build_ternary_no_target_consumer_stmt` ~L17782 | 新增 Pattern 6: `return (ternary) wrapped`（含 POP_TOP + STORE_* 双回归保护） |
| `core/cfg/region_ast_generator.py` | `_try_build_ternary_chained_container` ~L18248 | 新增 return 检测：`return (ternary1, ternary2)` chained container 返回 Return 而非 Expr |

## Bug 详细修复

### Bug R3-04: return_arith_left — `def f(): return 1 + (a if cond else 0)` — 已修复

- **测试**: `test_r3_ternary_return_arith_left.py`
- **源码**: `def f(): return 1 + (a if cond else 0)`
- **根因**: ternary 在 return + BINARY_OP 上下文中（ternary 在右），merge_block 含 `LOAD_CONST 1, BINARY_OP +, RETURN_VALUE`。merge_context 未识别 return+arith 场景，仅发射 `Expr(IfExp)`，丢失 `1 +` 与 `return`。
- **修复**: 新增 Pattern 6 — 当 merge_block 原本以 RETURN_VALUE 结尾，且剥离 RETURN 后仍有 wrapping 指令（BINARY_OP/CALL/BUILD_TUPLE 等）时，用 `expr_reconstructor.reconstruct(merge_instrs, initial_stack=[ternary_expr])` 重建完整表达式，发射 `Return(wrapped_expr)`。
- **算法依据**: 「父引用子入口」— 父 Return 通过 merge_block 的 BINARY_OP 引用 ternary 子节点。merge_block 的 wrapping 指令归属到 ternary 父区域（Return）。
- **字节码验证**: 原始 `LOAD_CONST 1, BINARY_OP +, RETURN_VALUE` 完整保留，不再多出 POP_TOP/LOAD_CONST None/RETURN_VALUE。

### Bug R3-05: return_arith_mul — `def f(): return (a if cond else 1) * 2` — 已修复

- **测试**: `test_r3_ternary_return_arith_mul.py`
- **源码**: `def f(): return (a if cond else 1) * 2`
- **根因**: 同 R3-04，BINARY_OP 是乘法。
- **修复**: 同 R3-04（Pattern 6 共用）。
- **字节码验证**: `LOAD_CONST 2, BINARY_OP *, RETURN_VALUE` 完整保留。

### Bug R3-06: return_call — `def f(): return foo(a if cond else 0)` — 已修复

- **测试**: `test_r3_ternary_return_call.py`
- **源码**: `def f(): return foo(a if cond else 0)`
- **根因**: ternary 在 return + CALL 上下文中，merge_block 含 `PRECALL, CALL, RETURN_VALUE`。cond_block 的 preload 含 `PUSH_NULL + LOAD_GLOBAL foo`（函数入口）。
- **修复**: Pattern 6 用 `_compute_ternary_cond_preload_exprs(region)` 提取 preload_exprs（含 foo callable），构造 `initial_stack = preload + [ternary_expr]`，使 expr_reconstructor 能重建 `Call(func=foo, args=[ternary])`。
- **算法依据**: 「父引用子入口」— 父 Return 通过 cond_block 的 foo 入口 + merge_block 的 CALL 引用 ternary 子节点。
- **字节码验证**: `PUSH_NULL, LOAD_GLOBAL foo, PRECALL, CALL, RETURN_VALUE` 完整保留。

### Bug R3-07: return_tuple — `def f(): return (a if cond else b), (c if cond else d)` — 已修复

- **测试**: `test_r3_ternary_return_tuple.py`
- **源码**: `def f(): return (a if cond else b), (c if cond else d)`
- **根因**: 两个 ternary 共享同一 merge_block（BUILD_TUPLE 2 + RETURN_VALUE）。内层 ternary 的 container_type='tuple'，外层 ternary 的 merge_block 是内层的 entry。`_try_build_ternary_chained_container` 正确构建了 `Tuple([ternary1, ternary2])`，但返回 `Expr(Tuple(...))` 而非 `Return(Tuple(...))`，因为未检测内层 merge_block 以 RETURN_VALUE 结尾。
- **修复**: 在 `_try_build_ternary_chained_container` 末尾（无 value_target 分支），检测 innermost ternary 的 merge_block 是否以 RETURN_VALUE/RETURN_CONST 结尾（排除 implicit return None）。若是，返回 `Return(container_info)` 而非 `Expr(container_info)`。
- **算法依据**: 「父引用子入口」— 父 Return 通过内层 ternary 的 merge_block 入口（BUILD_TUPLE + RETURN_VALUE）引用整个 chained container 子节点。「嵌套即抽象节点」— 内层 ternary 作为外层 Return 的抽象子节点。
- **字节码验证**: 原始 `BUILD_TUPLE 2, RETURN_VALUE` 完整保留，不再多出 POP_TOP/LOAD_CONST None/RETURN_VALUE。

### Bug R3-11: raise_arg — `raise E(a if cond else b)` — 已修复

- **测试**: `test_r3_ternary_raise_arg.py`
- **源码**: `raise E(a if cond else b)`
- **根因**: ternary 作为 raise 异常构造函数参数时，CALL + RAISE_VARARGS 1 在 merge_block 中消费 ternary 结果。cond_block 的 preload 含 `PUSH_NULL + LOAD_GLOBAL E`（异常类 callable）。原有 raise 模式（R2 修复）仅处理 `raise (ternary)()`（ternary 是 callable），未处理 `raise E(ternary)`（ternary 是参数）。
- **修复**: 扩展 `_build_ternary_no_target_consumer_stmt` 的 raise 分支 — 当 `raise_instr.arg == 1` 且 merge_instrs 含 PRECALL/CALL 时，用 `_compute_ternary_cond_preload_exprs(region)` 提取 preload_exprs（含 E callable），构造 `initial_stack = preload + [ternary_expr]`，使 expr_reconstructor 重建 `Call(E, [ternary])`，再包装为 `Raise(exc=Call(...))`。
- **算法依据**: 「父引用子入口」— 父 Raise 通过 cond_block 的 E 入口 + merge_block 的 CALL 引用 ternary 子节点。
- **字节码验证**: `PUSH_NULL, LOAD_GLOBAL E, PRECALL, CALL, RAISE_VARARGS` 完整保留。

## 顺带修复的基线 bug（3 个）

### Bonus-1: R2-F return_arith — `def f(): return (a if cond else 0) + 1` — 已修复

- **测试**: `test_r2_ternary_in_return_arith.py`（R2 已知限制，留待 R3 处理）
- **源码**: `def f(): return (a if cond else 0) + 1`
- **修复**: Pattern 6（同 R3-04）。
- **意义**: R2 已知 3 大限制之一（return_arith）现已解决。

### Bonus-2: R1 Bug 12 lambda_complex — `lambda: (a if cond else 0) + 1` — 已修复

- **测试**: `test_r1_ternary_in_lambda_complex.py`（R1 已知限制，P2 优先级）
- **源码**: `f = lambda: (a if cond else 0) + 1`（lambda body 含复合 ternary 表达式）
- **修复**: Pattern 6（lambda body 的 merge_block 同样含 BINARY_OP + RETURN_VALUE，Pattern 6 在嵌套 code object 内同样生效）。
- **意义**: R1 Bug 12 "lambda body 含复合 ternary 表达式时 body 被替换为 None" 现已解决。

### Bonus-3: R1 Bug 17 return_two_ternary — `return (ternary, ternary)` — 已修复

- **测试**: `test_r1_return_two_ternary.py`（R1 已知限制，P1 优先级）
- **源码**: `def f(): return (a if a > 0 else 0), (b if b > 0 else 0)`
- **修复**: chained container return 检测（同 R3-07）。
- **意义**: R1 Bug 17 "return 双 ternary 元组，嵌套 code object 内重组错误" 现已解决。

## 回归保护：POP_TOP 守卫

### 问题
Pattern 6 初版未排除 POP_TOP 结尾的 merge_block，导致顶层 `Expr(ternary)` 语句（如 `func(ternary)`，结果通过 POP_TOP 丢弃）被误编译为 `return func(ternary)`。全量回归从 58 failed 退化到 64 failed + 10 skipped（9 个测试被 skip）。

### 修复
在 Pattern 6 条件中新增 POP_TOP 守卫：
```python
if _ends_with_return and merge_instrs and merge_instrs[-1].opname != 'POP_TOP':
```
当 merge_instrs 末尾是 POP_TOP 时，ternary 结果被丢弃（顶层 Expr 语句），不应触发 Return 模式。

### 验证
守卫添加后全量回归恢复：64 failed → 61 failed，10 skipped → 1 skipped。9 个被 skip 的测试全部回到 passed/failed 正常状态。

## 回归保护：STORE_* 守卫（跨区域 if_region 退化修复）

### 问题
Pattern 6 在跨区域回归中发现对 `if c: x[0] += a if b else c` 误触发 Return 模式。该源码的 merge_block 含 `BINARY_OP +=, SWAP, STORE_SUBSCR, LOAD_CONST None, RETURN_VALUE` —— Pattern 6 看到 BINARY_OP + RETURN_VALUE 即生成 `return x`，但 RETURN_VALUE 是 implicit return None（模块顶层），且 STORE_SUBSCR 表明此为赋值上下文（AugAssign）。

跨区域回归（ternary + if_region）从基线 11 skipped 退化到 12 skipped：`test_adv11_augassign_subscr_ternary.py` 因 `return x` 在模块顶层语法非法（SyntaxError: 'return' outside function）而 skip。

### 修复
在 Pattern 6 条件中新增 STORE_* 守卫——当 merge_instrs 含任何 STORE_* 指令时，说明 merge_block 是赋值上下文（AugAssign/Assign），RETURN_VALUE 是 implicit return None，不应触发 Return 模式，应让 `_try_build_ternary_store_assign` 处理：
```python
_STORE_OPS = {'STORE_SUBSCR', 'STORE_ATTR', 'STORE_NAME',
              'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'}
_has_store = any(i.opname in _STORE_OPS for i in merge_instrs)
if not _has_store:
    # ... Pattern 6 logic ...
```

### 算法依据
「每块唯一归属」— merge_block 含 STORE_* 时，其消费指令归属 ternary 父区域（Assign/AugAssign），不归属 Return。Pattern 6 仅在 merge_block 真正消费 ternary 结果为 Return 值时触发，赋值上下文由 `_try_build_ternary_store_assign` 处理，两者互斥。

### 验证
- 守卫添加后跨区域回归恢复：12 skipped → 11 skipped（基线），`test_adv11_augassign_subscr_ternary.py` 从 skip 变为 PASSED
- Ternary 区域回归不变：61 failed / 133 passed / 1 skipped（无新退化）

## 未修复 bug（6 个，留待 R4+）

| Bug | 测试 | 类别 | 说明 |
|-----|------|------|------|
| R3-01 | test_r3_ternary_chained_compare_left | chained_compare | ternary 在 chained compare 左端，需 chained_compare IfRegion 边界调整 |
| R3-02 | test_r3_ternary_chained_compare_4way | chained_compare | 4-term chained compare，同 R3-01 |
| R3-03 | test_r3_ternary_await_expr | await | `await (ternary)` 无 return，GET_AWAITABLE + SEND 循环消费 ternary |
| R3-08 | test_r3_ternary_try_handler | except handler | ternary 作为 except handler 异常类型，与 except 子句 COMPARE_OP 冲突 |
| R3-09 | test_r3_ternary_while_cond | while cond | ternary 作为 while 条件，与 while 的 POP_JUMP_IF_FALSE 冲突 |
| R3-10 | test_r3_ternary_with_as | with ctx mgr | ternary 作为 with 上下文管理器，BEFORE_WITH + STORE_NAME 消费 ternary |

## 回归验证

### R3 新测试
```
11 failed → 6 failed（5 修复：R3-04, 05, 06, 07, 11）
9 passed → 14 passed
```

### Ternary 区域全量回归
```
基线（R2 完成）: 58 failed, 116 passed, 1 skipped (175 测试)
R3 测试添加后（无修复）: 69 failed, 125 passed, 1 skipped (195 测试)
Pattern 6 + raise 扩展后（含退化）: 64 failed, 121 passed, 10 skipped (195 测试)
POP_TOP 守卫后: 63 failed, 131 passed, 1 skipped (195 测试)
chained container return 修复后: 61 failed, 133 passed, 1 skipped (195 测试)
STORE_* 守卫后（最终）: 61 failed, 133 passed, 1 skipped (195 测试，无变化)
```

### 跨区域回归（ternary + if_region）
```
基线: 106 failed, 904 passed, 11 skipped
Pattern 6 初版（无 STORE_* 守卫）: 106 failed, 905 passed, 12 skipped（退化 +1 skip）
STORE_* 守卫后: 106 failed, 905 passed, 11 skipped（恢复基线，无退化）
```

### 退化分析
- 基线 58 failed → 现 55 failed（基线减 3，因 3 个基线 bug 顺带修复）
- R3 新增 6 failed（6 个未修复 bug）
- 总计 61 failed = 55 基线 + 6 R3 新增，无退化
- Pattern 6 初版引入的退化（POP_TOP 误触发）已通过守卫完全修复

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| R3: return + arith (ternary 在右) | 1 | 1 (R3-04) | 0 |
| R3: return + arith (ternary 在左) | 1 | 1 (R3-05) | 0 |
| R3: return + CALL | 1 | 1 (R3-06) | 0 |
| R3: return + BUILD_TUPLE 多 ternary | 1 | 1 (R3-07) | 0 |
| R3: raise E(ternary) | 1 | 1 (R3-11) | 0 |
| R3: chained_compare | 2 | 0 | 2 (R3-01, 02) |
| R3: await 无 return | 1 | 0 | 1 (R3-03) |
| R3: except handler 类型 | 1 | 0 | 1 (R3-08) |
| R3: while 条件 | 1 | 0 | 1 (R3-09) |
| R3: with 上下文管理器 | 1 | 0 | 1 (R3-10) |
| **基线 bonus**: R2 return_arith | 1 | 1 | 0 |
| **基线 bonus**: R1 lambda_complex | 1 | 1 | 0 |
| **基线 bonus**: R1 return_two_ternary | 1 | 1 | 0 |
| **总计** | **13** | **8** | **6** |

## 算法 4 原则核查

所有修复均严格遵循区域归约算法 4 原则：

1. **自底向上归约**: ternary 作为内层区域先归约，外层 Return/Raise 作为父区域后归约。
2. **每块唯一归属**: merge_block 的 wrapping 指令（BINARY_OP/CALL/BUILD_TUPLE/RETURN_VALUE）归属到 ternary 父区域（Return），不与 ternary 子区域重叠。
3. **嵌套即抽象节点**: 多个 ternary 共享 merge_block 时，内层 ternary 作为外层 Return 的抽象子节点（通过 chained container 机制）。
4. **父引用子入口**: 父 Return/Raise 通过 cond_block 的 preload 入口 + merge_block 的 wrapping 指令引用 ternary 子节点。

**禁止事项核查**:
- ✅ 无跨区域启发式特例（所有修复均在 TernaryRegion 内部）
- ✅ 无后处理补丁（所有修复在区域归约阶段完成）
- ✅ 无启发式优先级覆盖（未调整区域识别优先级）
- ✅ 无扁平化（嵌套 ternary 保持 IfExp AST 结构）

## 后续方向（R4+）

1. **R3-01/02 chained_compare**: 需调整 chained_compare IfRegion 与 TernaryRegion 的边界识别，处理 `SWAP + COPY 2 + COMPARE_OP + JUMP_IF_FALSE_OR_POP` 序列。
2. **R3-03 await_expr**: 需在嵌套 async code object 内识别 GET_AWAITABLE + SEND 轮询循环，将 await 作为父区域引用 ternary 子节点。
3. **R3-08 try_handler**: 需在 except handler 类型位置识别 ternary，处理 except 子句的 COMPARE_OP 链。
4. **R3-09 while_cond**: 需在 while 条件位置识别 ternary，处理 while 的 POP_JUMP_IF_FALSE 与 ternary 的冲突。
5. **R3-10 with_as**: 需在 with 上下文管理器位置识别 ternary，处理 BEFORE_WITH + STORE_NAME 消费链。
