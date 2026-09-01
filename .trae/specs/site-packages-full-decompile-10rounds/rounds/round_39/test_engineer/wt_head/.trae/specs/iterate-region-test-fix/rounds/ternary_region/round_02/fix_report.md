# Ternary Region Round 02 — 修复报告

## 修复概览

- **测试总数**: 10 个（R2 测试工程师发现，全部 FAILED）
- **已修复**: 7 个 bug（is_none, contains, multi_target, unpacking, raise, multi_arg, lambda_call）
- **已知限制**: 3 个 bug 未修复（chained_compare, await, return_arith — 均与 R1 已知限制同类）
- **回归状态**: Ternary 区域 65 failed → 58 failed（减 7），109 passed → 116 passed（增 7），1 skipped 不变，无退化

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `core/cfg/region_analyzer.py` | `_detect_ternary_pattern` merge_context 扫描：CONTAINS_OP 分支新增 STORE_* 检测（行 11730+）；新增 IS_OP 分支（行 11763+）；`_detect_ternary_context`：新增 MAKE_FUNCTION (lambda) 调用模式识别（行 11005+） |
| `core/cfg/region_ast_generator.py` | `_generate_ternary` `has_ops` 集合新增 IS_OP/CONTAINS_OP（行 16812）；value_target 路径前新增多目标/解包赋值检测（行 16903+）；`_build_ternary_no_target_consumer_stmt` raise 分支新增 CALL 检测（行 17721+）；func_call_info 分支新增 preload[1:] 作为前置参数（行 17196+）；func_call_info Call 构建后调用 `_convert_lambda_function_objects`（行 17230+） |

## Bug 详细修复

### Bug is_none: `x = (a if cond else b) is None` — 已修复

- **测试**: `test_r2_ternary_in_is_none.py`
- **源码**: `x = (a if cond else b) is None`
- **缺陷输出**: `x = (a if cond else b)`（丢失 `is None` 与 `x =`）
- **根因**:
  1. `region_analyzer.py` `_detect_ternary_pattern` merge_context 扫描完全未处理 IS_OP（NONE_CHECK_OPS 是 POP_JUMP_IF_NONE 而非 IS_OP），扫描跳过 IS_OP 落到 STORE_NAME x → `merge_context='store', value_target='x'`（这一步正确）。
  2. `region_ast_generator.py` `_generate_ternary` 的 `has_ops` 检测未包含 IS_OP，导致 value_target 路径不触发 `expr_reconstructor.reconstruct`，输出 `x = (ternary)` 丢弃 IS_OP + None。
- **修复**:
  - `region_ast_generator.py` 行 16812：`has_ops` 集合新增 `'IS_OP'` 与 `'CONTAINS_OP'`，使 value_target 路径触发 expr_reconstructor 重建完整 Compare 表达式。
- **算法依据**: 「嵌套即抽象节点」— IS_OP 是 ternary 父表达式（Compare）的算子，ternary 是其左操作数子节点；「父引用子入口」— 父 Compare 通过 merge_block 的 IS_OP + LOAD_CONST None 引用 ternary 入口。

### Bug contains: `x = (a if cond else b) in collection` — 已修复

- **测试**: `test_r2_ternary_in_contains.py`
- **源码**: `x = (a if cond else b) in collection`
- **缺陷输出**: `(a if cond else b)`（丢失 `in collection` 与 `x =`）
- **根因**:
  1. `region_analyzer.py` `_detect_ternary_pattern` merge_context 扫描的 CONTAINS_OP 分支（与 R1 Bug 7 修复中 COMPARE_OP 分支不一致）未检查后续是否有 STORE_*。对 `x = (ternary) in collection` 误设 `merge_context='compare'`，导致 AST 生成器走 compare 路径丢失 `in collection` 和 `x =`。
- **修复**:
  - `region_analyzer.py` 行 11730：CONTAINS_OP 分支新增 STORE_* 检查（仿 R1 Bug 7 COMPARE_OP 修复）——若 CONTAINS_OP 后跟 STORE_*，跳过设置 `merge_context='compare'`，让扫描落入 STORE_* → `merge_context='store'`。
  - `region_ast_generator.py` 行 16812：`has_ops` 集合新增 `'CONTAINS_OP'`（与 is_none 共用）。
- **算法依据**: 「父引用子入口」— 父 Compare 通过 merge_block 的 CONTAINS_OP + LOAD_NAME collection 引用 ternary 入口；「每块唯一归属」— CONTAINS_OP + STORE_* 同属 ternary 父赋值区域。

### Bug multi_target: `x = y = a if cond else b` — 已修复

- **测试**: `test_r2_ternary_in_multi_target_assign.py`
- **源码**: `x = y = a if cond else b`
- **缺陷输出**: `x = (a if cond else b)`（丢失 `y =`）
- **根因**:
  - `region_ast_generator.py` `_generate_ternary` 的 value_target 路径只发射 `Assign(targets=[Name(value_target)], value=ternary_expr)`，不识别 `COPY 1 + STORE_x + STORE_y` 的多目标赋值模式。
- **修复**:
  - `region_ast_generator.py` 行 16903：value_target 路径前新增模式 1 检测——若 merge_block 含 `COPY 1` + ≥2 个 STORE_*，收集所有 STORE_* 目标，发射 `Assign(targets=[Name(x), Name(y), ...], value=ternary_expr, is_chain_assign=True)`。`is_chain_assign=True` 标志让 CodeGenerator 用 ` = ` 连接 targets（而非 `, `）。
- **字节码验证**: `x = y = ternary` 编译为 `COPY 1; STORE x; STORE y`（链式赋值），而 `x, y = ternary` 编译为 `UNPACK_SEQUENCE 2; STORE x; STORE y`（解包赋值）— 两者字节码不同。
- **算法依据**: 「每块唯一归属」— COPY + 多 STORE 同属 ternary 父赋值区域；「父引用子入口」— 父 Assign 通过 COPY + 多 STORE 引用 ternary 入口。

### Bug unpacking: `a, b = (x, y) if cond else (z, w)` — 已修复

- **测试**: `test_r2_ternary_in_unpacking.py`
- **源码**: `a, b = (x, y) if cond else (z, w)`
- **缺陷输出**: `a = ((x, y) if cond else (z, w))`（丢失 `b` 与解包）
- **根因**:
  - 同 multi_target，value_target 路径不识别 `UNPACK_SEQUENCE N + N 个 STORE_*` 的解包赋值模式。
- **修复**:
  - `region_ast_generator.py` 行 16903：value_target 路径前新增模式 2 检测——若 merge_block 含 `UNPACK_SEQUENCE N` + N 个 STORE_*，收集 N 个 STORE_* 目标，发射 `Assign(targets=[Tuple(elts=[Name(a), Name(b), ...], ctx='Store')], value=ternary_expr)`。
- **算法依据**: 「每块唯一归属」— UNPACK_SEQUENCE + N STORE 同属 ternary 父赋值区域；「父引用子入口」— 父 Assign 通过 UNPACK_SEQUENCE 引用 ternary 入口。

### Bug raise: `raise (Exc1 if cond else Exc2)()` — 已修复

- **测试**: `test_r2_ternary_in_raise.py`
- **源码**: `raise (Exc1 if cond else Exc2)()`
- **缺陷输出**: `raise (Exc1 if cond else Exc2)`（丢失 `()` 调用）
- **根因**:
  - merge_block: `PRECALL 0; CALL 0; RAISE_VARARGS 1`，无 STORE_*/RETURN_VALUE 等，`merge_context=None`。AST 生成器走 `_build_ternary_no_target_consumer_stmt` 的 raise_instr.arg==1 分支直接返回 `Raise(exc=ternary_expr, cause=None)`，把 ternary（Exc1/Exc2 类）当作异常实例抛出，丢失了 `()` 调用。
- **修复**:
  - `region_ast_generator.py` 行 17721：raise_instr.arg==1 分支中，检测 merge_block 在 RAISE_VARARGS 之前是否有 PRECALL + CALL。若有，ternary 是 callable，CALL 调用它产生异常实例——用 `expr_reconstructor.reconstruct(merge_instrs, initial_stack=[ternary_expr])` 重建完整 `Raise(exc=Call(func=ternary_expr, args=[], keywords=[]))`。若无（纯 `raise (ternary)`），保持现有逻辑。
- **算法依据**: 「父引用子入口」— 父 Raise 通过 merge_block 的 PRECALL+CALL+RAISE_VARARGS 引用 ternary 入口；「嵌套即抽象节点」— ternary（Exc1/Exc2 类选择）是父 Call(func=ternary) 的 func 子节点。

### Bug multi_arg: `print(prefix, a if cond else b)` — 已修复

- **测试**: `test_r2_ternary_in_multi_arg_call.py`
- **源码**: `print(prefix, a if cond else b)`
- **缺陷输出**: `print(a if cond else b)`（丢失 `prefix` 参数）
- **根因**:
  - `_detect_ternary_context` 只识别 PUSH_NULL + LOAD_NAME print 作为 func_call_info，不识别后续 LOAD_NAME prefix 是预加载的第一参数。`_generate_ternary` 的 `call_args = list(func_call_info.get('args', [])) + [_ternary_arg]` 未将 preload[1:]（prefix）加入 args。
- **修复**:
  - `region_ast_generator.py` 行 17196：func_call_info 分支中，调用 `_compute_ternary_cond_preload_exprs(region)` 获取 preload 表达式列表。若 preload 长度 > 1（含 func + 至少一个 arg），将 `preload[1:]` 加入 call_args（在 ternary 之前）。
- **算法依据**: 「父引用子入口」— 父 Call 通过 cond_block preload（func + 前置 args）+ merge_block CALL 引用 ternary 入口；「嵌套即抽象节点」— ternary 是父 Call 的最后一个位置参数子节点。

### Bug lambda_call: `(lambda x: x * 2)(a if cond else 0)` — 已修复

- **测试**: `test_r2_ternary_in_lambda_call.py`
- **源码**: `(lambda x: x * 2)(a if cond else 0)`
- **缺陷输出**: `(a if cond else 0)`（丢失 lambda 与调用）
- **根因**:
  1. `region_analyzer.py` `_detect_ternary_context` 的 PUSH_NULL 路径只接受 `func_i.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF')`，不接受 LOAD_CONST + MAKE_FUNCTION（lambda 构造）。func_call_info=None，走 `Expr(ternary)` 路径丢失 lambda + 调用。
  2. 即便 func_call_info 设置成功，`func_call_info['func']` 是 FunctionObject dict（不是 Lambda dict），CodeGenerator 会将其渲染为占位符 `lambda *args, **kwargs: None`，丢失真实 body。
- **修复**（2 处协同）:
  1. `region_analyzer.py` 行 11005：`_detect_ternary_context` 新增 MAKE_FUNCTION 模式识别——检测 cond_block preload 含 `LOAD_CONST <code>` + `MAKE_FUNCTION`，用 `{'type': 'FunctionObject', 'code': <code>}` 作为 func_call_info['func']。
  2. `region_ast_generator.py` 行 17230：func_call_info 分支构建 Call dict 后，调用 `_convert_lambda_function_objects(call_expr)` 递归将 FunctionObject（co_name=='<lambda>'）转为 Lambda dict（由 `_build_function_def` 反编译 lambda code object 重建 args + body）。
- **算法依据**: 「嵌套即抽象节点」— lambda 是父 Call 的 func 子节点；「父引用子入口」— 父 Call 通过 cond_block 的 PUSH_NULL+LOAD_CONST+MAKE_FUNCTION + merge_block 的 PRECALL+CALL 引用 ternary 入口；「自底向上归约」— lambda code object 先被递归反编译为 Lambda dict，再作为 Call 的 func。

## 未修复 bug（已知限制）

| Bug | 测试 | 优先级 | 说明 |
|-----|------|--------|------|
| chained_compare | test_r2_ternary_in_chained_compare | P2 | `0 < (ternary) < 10` 编译为 SWAP + COPY 2 + 双 COMPARE_OP + JUMP_IF_FALSE_OR_POP 复杂序列，与 R1 Bug 5（chained compare 在 ternary 条件中）同类，chained_compare IfRegion 优先级问题，R3 处理 |
| await | test_r2_ternary_in_await | P2 | 嵌套 async code object 内 GET_AWAITABLE + SEND 轮询循环跨多块，与 R1 Bug 10/13/15/16/17（嵌套 code object 内 ternary 重组）同类，R3 处理 |
| return_arith | test_r2_ternary_in_return_arith | P2 | 嵌套 code object 内 `return (ternary) + 1` 的 BINARY_OP + RETURN_VALUE 不满足 `len(merge_non_noise)==1`，与 R1 Bug 10/13 同类，R3 处理 |

## 回归验证

### R2 新测试
```
10 failed → 3 failed（7 修复：is_none, contains, multi_target, unpacking, raise, multi_arg, lambda_call）
```

### Ternary 区域全量回归
```
65 failed, 109 passed, 1 skipped → 58 failed, 116 passed, 1 skipped
```

### 退化分析
- Ternary 区域：减 7 failed，增 7 passed，无退化
- 7 个修复均新增 passing 测试，未引入任何新 failing 测试
- 已验证预存在失败（test_tn25ternarynone_*.py 等）非本次修复引入

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| R2-A: IS_OP / CONTAINS_OP 消费指令未识别 | 2 | 2 (is_none, contains) | 0 |
| R2-B: 多目标 / 解包赋值未识别 | 2 | 2 (multi_target, unpacking) | 0 |
| R2-C: raise + CALL 表达式 | 1 | 1 (raise) | 0 |
| R2-D: 函数调用多参数 / lambda 调用 | 2 | 2 (multi_arg, lambda_call) | 0 |
| R2-E: chained compare 中间位置 | 1 | 0 | 1 (R3) |
| R2-F: 嵌套 code object 内 ternary + 算术/await | 2 | 0 | 2 (R3) |
| **合计** | **10** | **7** | **3** |

## 算法原则遵循性

所有 7 个修复均严格遵循区域归约算法 4 原则：

1. **自底向上归约**: ternary 子区域先归约（识别 IfExp），父表达式（Compare/Call/Assign/Raise）后归约。lambda_call 中 lambda code object 先递归反编译为 Lambda dict，再作为父 Call 的 func 子节点。
2. **每块唯一归属**: merge_block 的消费指令（IS_OP/CONTAINS_OP/COPY/UNPACK_SEQUENCE/PRECALL+CALL+RAISE_VARARGS/MAKE_FUNCTION+PRECALL+CALL）归属 ternary 父区域，不被其他区域抢占。
3. **嵌套即抽象节点**: ternary 在父表达式中是单抽象节点（IfExp）；lambda 在父 Call 中是 func 子节点；Starred/Tuple/Compare 等通过父表达式重建。
4. **父引用子入口**: 父 Assign/Call/Raise/Compare 通过 ternary 的 merge_block 入口或 cond_block preload 引用 ternary 子节点。

**禁止项核查**: 无跨区域启发式特例、无后处理补丁、无启发式优先级覆盖、无破坏嵌套的扁平化。

- IS_OP/CONTAINS_OP 修复仅扩展 `has_ops` 集合 + 仿照已有 COMPARE_OP 修复的 STORE_* 检查，未引入新特例。
- multi_target/unpacking 修复在 value_target 路径前新增模式检测，与现有 store 路径同构。
- raise 修复复用 `expr_reconstructor.reconstruct`，未引入新表达式重建逻辑。
- multi_arg 修复复用 `_compute_ternary_cond_preload_exprs`，未引入新 preload 计算。
- lambda_call 修复复用 `_convert_lambda_function_objects`（已有的 FunctionObject→Lambda 转换器），未引入新转换逻辑。

## 下一阶段计划（R3）

1. **P2 R2-E**: chained_compare — 需处理 SWAP + COPY 2 + 双 COMPARE_OP + JUMP_IF_FALSE_OR_POP 序列，与 R1 Bug 5 合并解决。
2. **P2 R2-F**: await + return_arith — 需处理嵌套 code object 内 ternary + 算术/await，与 R1 Bug 10/13/15/16/17 合并解决。
3. **R1 遗留已知限制**: Bug 3, 4 (assert 字节码歧义，不可修复)；Bug 6, 11 (双 ternary 喂同一消费指令)；Bug 12 (lambda body 含复合 ternary)；Bug 14 (async for 体 ternary)。
