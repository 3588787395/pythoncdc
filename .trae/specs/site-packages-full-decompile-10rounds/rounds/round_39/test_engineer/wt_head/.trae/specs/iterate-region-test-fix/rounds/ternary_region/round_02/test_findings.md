# Ternary 区域 Round 02 测试发现

> 分支: `trae/region-iteration-v2` @ `dc7bb34`
> 基线（R1 修复后）: 77 passed / 55 failed / 1 skipped (133 测试)
> R2 新增 42 测试: 32 通过 + 10 失败
> 当前全量基线: **65 failed / 109 passed / 1 skipped (175 测试)**

## 1. 测试阶段产出

新增 42 个 `test_r2_*.py` 测试文件至 `/workspace/tests/exhaustive/ternary/`，覆盖以下方向：
- set / list / tuple / dict 字面量内三元
- f-string / format / format_spec 内三元
- binop（左右操作数）/ binop chain / unary not
- subscript / attribute / attribute store / store_subscr
- slice_step / for_iter / kwarg / star_args / default_arg
- yield / yield_from / await
- triple_nested / orelse_chain / method_chain / method_call / body_is_binop / body_method_call
- walrus_in_cond / with_fstring_format_spec
- compare_right / func_call / dictcomp / listcomp

其中 **10 个失败**，归类为 5 类根因（详见 §3）。

## 2. 失败测试清单

| # | 测试 | 源码 | 反编译输出 | 根因类 |
|---|------|------|----------|--------|
| 1 | test_r2_ternary_in_is_none | `x = (a if cond else b) is None` | `x = (a if cond else b)` | R2-A |
| 2 | test_r2_ternary_in_contains | `x = (a if cond else b) in collection` | `(a if cond else b)` | R2-A |
| 3 | test_r2_ternary_in_multi_target_assign | `x = y = a if cond else b` | `x = (a if cond else b)` | R2-B |
| 4 | test_r2_ternary_in_unpacking | `a, b = (x, y) if cond else (z, w)` | `a = ((x, y) if cond else (z, w))` | R2-B |
| 5 | test_r2_ternary_in_raise | `raise (Exc1 if cond else Exc2)()` | `raise (Exc1 if cond else Exc2)` | R2-C |
| 6 | test_r2_ternary_in_multi_arg_call | `print(prefix, a if cond else b)` | `print(a if cond else b)` | R2-D |
| 7 | test_r2_ternary_in_lambda_call | `(lambda x: x * 2)(a if cond else 0)` | `(a if cond else 0)` | R2-D |
| 8 | test_r2_ternary_in_chained_compare | `x = 0 < (a if cond else 1) < 10` | `if (0 < (ternary)): pass` | R2-E |
| 9 | test_r2_ternary_in_await | `async def f(): return await (a if cond else b)` | `(a if cond else b)` | R2-F |
| 10 | test_r2_ternary_in_return_arith | `def f(): return (a if cond else 0) + 1` | `(a if cond else 0)` | R2-F |

## 3. 根因分析与字节码对比

### R2-A: ternary merge_block 中 IS_OP / CONTAINS_OP 消费指令未被识别

**影响测试**: is_none, contains

**is_none 字节码**:
```
0  RESUME
2  LOAD_NAME cond
4  POP_JUMP_FORWARD_IF_FALSE → 10
6  LOAD_NAME a
8  JUMP_FORWARD → 12
10 LOAD_NAME b
12 LOAD_CONST None           ← merge_block 起点
14 IS_OP 0                   ← 消费 ternary 结果 + None
16 STORE_NAME x              ← 消费 IS_OP 结果
18 LOAD_CONST
20 RETURN_VALUE
```

**contains 字节码**:
```
12 LOAD_NAME collection      ← merge_block 起点
14 CONTAINS_OP 0             ← 消费 ternary + collection
16 STORE_NAME x
```

**根因**:
1. `region_analyzer.py` 的 `_detect_ternary_pattern` merge_context 扫描（行 11713-11723）：CONTAINS_OP 分支未检查后续是否有 STORE_*（与 COMPARE_OP 的 [R4 Bug 7 修复] 行 11645-11659 不一致），对 `x = (ternary) in collection` 误设 `merge_context='compare'`，导致 AST 生成器走 compare 路径丢失 `in collection` 和 `x =`。
2. IS_OP 在 `region_analyzer.py` 完全未处理（NONE_CHECK_OPS 是 POP_JUMP_IF_NONE 而非 IS_OP），扫描跳过 IS_OP 落到 STORE_NAME x → merge_context='store', value_target='x'（这一步是对的）。
3. `region_ast_generator.py` `_generate_ternary` 的 has_ops 检测（行 16801-16812）未包含 IS_OP / CONTAINS_OP，导致 value_target 路径不触发 `expr_reconstructor.reconstruct`，输出 `x = (ternary)` 丢弃 IS_OP + None / CONTAINS_OP + collection。

**修复方案**:
- `region_analyzer.py` CONTAINS_OP 分支新增 STORE_* 检查（仿 COMPARE_OP Bug 7 修复）：若 CONTAINS_OP 后跟 STORE_*，跳过设置 merge_context='compare'，让扫描落入 STORE_* → merge_context='store'。
- `region_ast_generator.py` has_ops 集合新增 'IS_OP' 和 'CONTAINS_OP'，使 value_target 路径触发 expr_reconstructor.reconstruct 重建完整 Compare 表达式。

**优先级**: P0（最易修复，根因清晰）

---

### R2-B: ternary merge_block 含 COPY+多 STORE / UNPACK_SEQUENCE+多 STORE

**影响测试**: multi_target_assign, unpacking

**multi_target 字节码**:
```
12 COPY 1                   ← merge_block 起点，复制 ternary 结果
14 STORE_NAME x
16 STORE_NAME y             ← 第二个 STORE 丢失
```

**unpacking 字节码**:
```
20 UNPACK_SEQUENCE 2        ← merge_block 起点，解包 ternary 结果（tuple）
24 STORE_NAME a
26 STORE_NAME b             ← UNPACK_SEQUENCE + 第二个 STORE 丢失
```

**根因**:
- `region_analyzer.py` merge_context 扫描对 COPY / UNPACK_SEQUENCE 无专门处理，扫描落入第一个 STORE_NAME → merge_context='store', value_target='x' / value_target='a'。
- `region_ast_generator.py` _generate_ternary 的 value_target 路径（行 16898-16902）只发射 `Assign(targets=[Name(value_target)], value=ternary_expr)`，不识别 COPY+多 STORE / UNPACK_SEQUENCE+多 STORE 的多目标赋值模式。

**修复方案**:
- 在 _generate_ternary value_target 路径中，发射 Assign 前检测 merge_block 的多目标模式：
  - **COPY 1 + STORE_x + STORE_y + ...**: 收集所有 STORE_*，发射 `Assign(targets=[Name(x), Name(y), ...], value=ternary_expr)`。
  - **UNPACK_SEQUENCE N + STORE_a + STORE_b + ...**: 收集 UNPACK_SEQUENCE 后的 N 个 STORE_*，发射 `Assign(targets=[Tuple([Name(a), Name(b), ...])], value=ternary_expr)`。

**优先级**: P0（模式清晰，与现有 value_target 路径同源）

---

### R2-C: ternary body 是 CALL 表达式（`raise (Exc if cond else Exc2)()`）

**影响测试**: raise

**raise 字节码**:
```
0  RESUME
2  PUSH_NULL                 ← 调用前缀
4  LOAD_NAME cond
6  POP_JUMP_FORWARD_IF_FALSE → 12
8  LOAD_NAME Exc1
10 JUMP_FORWARD → 14
12 LOAD_NAME Exc2
14 PRECALL 0                 ← merge_block 起点，调用 Exc1/Exc2()
18 CALL 0
28 RAISE_VARARGS 1           ← 消费 CALL 结果
```

**根因**:
- merge_block: `PRECALL 0; CALL 0; RAISE_VARARGS 1`，无 STORE_* / RETURN_VALUE / GET_AWAITABLE 等，merge_context=None。
- AST 生成器走 `_build_ternary_no_target_consumer_stmt`（行 17551），raise_instr.arg==1 分支（行 17630-17632）直接返回 `Raise(exc=ternary_expr, cause=None)`，把 ternary（Exc1/Exc2 类）当作异常实例抛出，丢失了 `()` 调用。

**修复方案**:
- 在 `_build_ternary_no_target_consumer_stmt` raise_instr.arg==1 分支中，检测 merge_block 在 RAISE_VARARGS 之前是否有 PRECALL + CALL：
  - 若有，ternary 是 callable，CALL 调用它产生异常实例。重建 `exc_expr = Call(func=ternary_expr, args=[], keywords=[])`，返回 `Raise(exc=exc_expr, cause=None)`。
  - 若无（纯 `raise (ternary)`），保持现有逻辑 `Raise(exc=ternary_expr, cause=None)`。

**优先级**: P1（模式明确，但需区分 CALL 是消费 ternary 还是 ternary 内部）

---

### R2-D: ternary 作为函数调用参数（多参数 / lambda 调用）

**影响测试**: multi_arg_call, lambda_call

**multi_arg 字节码**:
```
0  RESUME
2  PUSH_NULL                 ← cond_block preload
4  LOAD_NAME print           ← 函数
6  LOAD_NAME prefix          ← 第一参数（丢失）
8  LOAD_NAME cond            ← 三元条件
10 POP_JUMP_FORWARD_IF_FALSE → 16
12 LOAD_NAME a
14 JUMP_FORWARD → 18
16 LOAD_NAME b
18 PRECALL 2                 ← merge_block，CALL argc=2
22 CALL 2
32 POP_TOP
```

**lambda_call 字节码**:
```
0  RESUME
2  PUSH_NULL
4  LOAD_CONST <lambda code>
6  MAKE_FUNCTION 0           ← cond_block preload
8  LOAD_NAME cond
10 POP_JUMP_FORWARD_IF_FALSE → 16
12 LOAD_NAME a
14 JUMP_FORWARD → 18
16 LOAD_CONST 0
18 PRECALL 1                 ← merge_block，CALL argc=1
22 CALL 1
32 POP_TOP
```

**根因**:
- **multi_arg**: `_detect_ternary_context`（region_analyzer.py 行 10987-10993）只识别 PUSH_NULL + LOAD_NAME print 作为 func_call_info，不识别后续 LOAD_NAME prefix 是预加载的第一参数。`_generate_ternary` 行 17126 `call_args = list(func_call_info.get('args', [])) + [_ternary_arg]` 未将 preload[1:]（prefix）加入 args。
- **lambda_call**: `_detect_ternary_context` 的 PUSH_NULL 路径只接受 func_i.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF')，不接受 LOAD_CONST + MAKE_FUNCTION（lambda 构造）。func_call_info=None，走 Expr(ternary) 路径丢失 lambda + 调用。

**修复方案**:
- **multi_arg**: 在 _generate_ternary func_call_info 分支中，调用 `_compute_ternary_cond_preload_exprs(region)` 获取 preload，若 preload 长度 > 1（含 func + 至少一个 arg），将 `preload[1:]` 加入 call_args（在 ternary 之前）。
- **lambda_call**: 在 `_detect_ternary_context` 中新增 MAKE_FUNCTION 模式识别：检测 cond_block preload 含 LOAD_CONST <code> + MAKE_FUNCTION，通过 code object 重建 Lambda 表达式作为 func_call_info['func']。

**优先级**: P1（multi_arg 易修复；lambda_call 涉及 code object 重建，较复杂）

---

### R2-E: ternary 在 chained compare 中间位置

**影响测试**: chained_compare

**chained_compare 字节码**:
```
0  RESUME
2  LOAD_CONST 0              ← cond_block preload（链式左端）
4  LOAD_NAME cond
6  POP_JUMP_FORWARD_IF_FALSE → 12
8  LOAD_NAME a
10 JUMP_FORWARD → 14
12 LOAD_CONST 1
14 SWAP 2                    ← merge_block 起点
16 COPY 2
18 COMPARE_OP <
24 JUMP_IF_FALSE_OR_POP → 36
26 LOAD_CONST 10
28 COMPARE_OP <
34 JUMP_FORWARD → 40
36 SWAP 2
38 POP_TOP
40 STORE_NAME x
```

**根因**:
- chained compare `0 < (ternary) < 10` 编译为 SWAP + COPY 2 + 双 COMPARE_OP + JUMP_IF_FALSE_OR_POP 的复杂序列。merge_block 含多个 COMPARE_OP 和 JUMP_IF_FALSE_OR_POP，超出当前 ternary 识别能力。
- 类似 R1 Bug 5（chained compare 在 ternary 条件中），属 chained compare 优先级问题。

**修复方案**:
- 暂列为已知限制（与 R1 Bug 5 同类），R3 优先解决。

**优先级**: P2（复杂度高，R3 处理）

---

### R2-F: 嵌套 code object 内 ternary + 算术/await

**影响测试**: await, return_arith

**return_arith 字节码**（嵌套 code object f）:
```
RESUME
LOAD_GLOBAL cond
POP_JUMP_FORWARD_IF_FALSE → ...
LOAD_GLOBAL a
JUMP_FORWARD → merge
LOAD_CONST 0
merge: BINARY_OP +           ← 消费 ternary + 1
       RETURN_VALUE           ← 消费 BINARY_OP 结果
```

**await 字节码**（嵌套 async code object f）:
```
merge: GET_AWAITABLE          ← 消费 ternary
       LOAD_CONST None
       SEND ...
       ... (polling loop)
       STORE_FAST result
       RETURN_VALUE
```

**根因**:
- 嵌套 code object 内的 ternary 识别在 R1 已知限制中（Bug 10, 13, 15, 16, 17）。
- return_arith: merge_block 是 `BINARY_OP +; RETURN_VALUE`。RETURN_VALUE 不是单指令块（行 11811 `if len(merge_non_noise) == 1` 不满足），merge_context=None。AST 生成器走 Expr(ternary) 路径，丢失 +1 和 return。
- await: async code object 的 GET_AWAITABLE + SEND 轮询循环跨多块，merge_context='await' 路径（行 11834-11872）需要 SEND 块和 STORE 块都在 merge_block.successors 中，但嵌套 code object 的块结构可能不满足。

**修复方案**:
- 暂列为已知限制（与 R1 Bug 10/13/15/16/17 同类），R3 优先解决嵌套 code object 内 ternary 重组。

**优先级**: P2（嵌套 code object 复杂度高，R3 处理）

## 4. 修复优先级

| 优先级 | Bug | 预计修复难度 | 算法 4 原则契合度 |
|--------|-----|------------|-----------------|
| P0 | is_none, contains | 易 | 嵌套即抽象节点（IS_OP/CONTAINS_OP 是 ternary 父表达式子节点） |
| P0 | multi_target, unpacking | 中 | 每块唯一归属（COPY/UNPACK_SEQUENCE + 多 STORE 同属 ternary 父赋值） |
| P1 | raise | 中 | 父引用子入口（PRECALL+CALL 在 merge_block 消费 ternary 子节点） |
| P1 | multi_arg | 中 | 父引用子入口（prefix preload + CALL 同属父 Call） |
| P1 | lambda_call | 较难 | 嵌套即抽象节点（MAKE_FUNCTION + CALL 是父 Call 的子节点） |
| P2 | chained_compare | 难 | 已知限制，R3 |
| P2 | await, return_arith | 难 | 已知限制（嵌套 code object），R3 |

## 5. R2 修复目标

R2 计划修复至少 5 个 bug，候选顺序：
1. is_none + contains（R2-A，2 个 bug，同一修复）
2. multi_target + unpacking（R2-B，2 个 bug，同类修复）
3. raise（R2-C，1 个 bug）
4. multi_arg（R2-D，1 个 bug）

预计修复 6 个 bug，剩余 4 个（lambda_call, chained_compare, await, return_arith）作为 R3 已知限制。

## 6. 算法 4 原则契合度论证

所有修复均遵循：
1. **自底向上归约**: ternary 子区域先归约，父表达式（Compare/Call/Assign）后归约。
2. **每块唯一归属**: merge_block 的消费指令（IS_OP/CONTAINS_OP/COPY/UNPACK_SEQUENCE/PRECALL+CALL）归属 ternary 父区域，不被其他区域抢占。
3. **嵌套即抽象节点**: ternary 在父表达式中是单抽象节点（IfExp），父表达式通过 merge_block 消费指令重建。
4. **父引用子入口**: 父 Assign/Call/Raise 通过 ternary 的 merge_block 入口引用 ternary 子节点。

无跨区域启发式特例、无后处理补丁、无启发式优先级覆盖、无扁平化。
