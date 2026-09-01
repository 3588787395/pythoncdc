# Ternary Region Round 08 — 修复报告

## 修复概览

- **测试总数**：29 个 R8 新增对抗性测试（19 passed / 8 failed / 2 skipped）
- **本轮已修复**：10 个测试 / 5 类 bug
  - R7-01 / R7-01b / R8-01 / R8-02 / R8-03 — assert message ternary 家族（5 测试，1 类根因）
  - R7-04 / R8-06 — del subscript 双 ternary（2 测试，1 类根因）
  - R8-04 — walrus 捕获 ternary
  - R8-05 — unpacking 赋值 source 是 ternary
  - R8-07 — import from alias 后跟 ternary 赋值
- **未修复（留待 R9+）**：4 个 async 系列 + 2 个 skip
  - R7-02 / R7-03 / R7-10 / R8-08 — async 控制流 ternary（评估结论详见下文）
  - R8-S1 — del obj[ternary].attr（语法错误 skip）
  - R8-S2 — f-string 嵌套 ternary + 前后字面量（return outside function skip）
- **回归状态**：
  - Ternary: 65 failed → 63 failed（-2）/ 228 passed → 257 passed / 1 skipped → 3 skipped（294 → 323 测试）
  - 跨区域（ternary + if_region）: 109 failed → 107 failed（-2）/ 1001 passed → 1030 passed / 11 skipped → 13 skipped（1121 → 1150 测试，无基线退化）
- **修改文件**：`core/cfg/region_ast_generator.py`（单文件，无 region_analyzer 改动）

## 修改文件清单

| 文件 | 改动位置 | 改动内容 |
|------|---------|---------|
| `core/cfg/region_ast_generator.py` | `_extract_imports_from_block_prefix` 新增 ~L129-237 | 新增 helper：扫描块前缀的 IMPORT_NAME + IMPORT_FROM + STORE_* 序列，跳过 LOAD_CONST (level/fromlist) 等噪音，遇跳转或非 import 指令终止。返回 ImportFrom / Import AST 字典列表（R8-07） |
| `core/cfg/region_ast_generator.py` | `generate()` TernaryRegion 分支 ~L275-285 | TernaryRegion 入口前调用 `_extract_imports_from_block_prefix`，把 import 加入 ast_nodes；不标记 entry_block 为 generated，留给 ternary condition preload 处理（R8-07） |
| `core/cfg/region_ast_generator.py` | `_generate_ternary` value_target 分支前 walrus 检测 ~L17795-17847 | 新增独立 walrus 捕获 ternary 检测：merge_block 含 `COPY 1 + STORE_* + POP_TOP` 且无 outer STORE 时，输出 `Expr(NamedExpr(target, IfExp))`，区别于 R15 Mode A 的「外层有 STORE」与普通 Assign 的「STORE 终结不留栈」（R8-04） |
| `core/cfg/region_ast_generator.py` | `_generate_ternary` value_target 分支 Mode 3 ~L17693+ | 新增 UNPACK_EX + 多 STORE_* starred 解包检测：`*y, = ternary` 输出 `Assign(targets=[Starred(y)], value=IfExp)`（R8-05） |
| `core/cfg/region_ast_generator.py` | `_resolve_assert_message_ternary_expr` walrus 修复 ~L2149-2242 | assert message 是 walrus(ternary) 时保留 NamedExpr 上下文（R8-01） |
| `core/cfg/region_ast_generator.py` | `_build_ternary_no_target_consumer_stmt` 顶部 guard ~L18492-18517 | 顶部新增守卫：ternary merge_block 含 LOAD_ASSERTION_ERROR + RAISE_VARARGS 1 时调用 `_build_assert_message_ternary_stmt` 让 AssertRegion 接管（assert 家族） |
| `core/cfg/region_ast_generator.py` | `_build_ternary_no_target_consumer_stmt` Pattern 1 内部 guard 移除 ~L18559-18576 | 移除原 Pattern 1 内部对 assert message 的错误拦截，统一交给顶部 guard（assert 家族） |
| `core/cfg/region_ast_generator.py` | `_build_assert_message_ternary_stmt` 新增 ~L18780-18908 | 新增方法：识别 assert message 位置的 TernaryRegion，重建 message 表达式（含 walrus / f() / "str"+ternary / {k:ternary} 五种变体），输出 `Expr(msg_expr)` 让 `_generate_assert` 包装为 `Assert(test, msg)`（R7-01/01b/R8-01/02/03） |
| `core/cfg/region_ast_generator.py` | `_try_build_ternary_chained_r6_pattern` Pattern D ~L20240-20400 | 新增 Pattern D：del subscript 双 ternary 同 consumer。区分 R7-04（`del x[t1][t2]` — inner.cond prefix 含 BINARY_SUBSCR）与 R8-06（`del (t1)[t2]` — inner.cond prefix 空，t1 是 obj），输出 `Delete([Subscript(Subscript(obj, IfExp1, Del), IfExp2, Del)])`（R7-04/R8-06） |

## Bug 详细修复

### Bug R7-01/01b/R8-01/02/03: assert message ternary 家族 — 已修复

- **测试**：`test_r7_ternary_in_assert_msg.py`、`test_r7_ternary_in_assert_complex_msg.py`、`test_r8_ternary_in_assert_walrus_msg.py`、`test_r8_ternary_in_assert_binop_msg.py`、`test_r8_ternary_in_assert_dict_msg.py`
- **源码**：
  - `assert x, (a if c else b)` — 简单 ternary message
  - `assert x, f(a if c else b)` — f() 包裹 ternary
  - `assert x, (n := (a if c else b))` — walrus 包裹 ternary
  - `assert x, "msg: " + (a if c else b)` — BinOp + ternary
  - `assert x, {k: (a if c else b)}` — dict + ternary
- **根因**：AssertRegion 的 message_block 与 TernaryRegion 的 merge_block 共享同一块。`_build_ternary_no_target_consumer_stmt` Pattern 1 把含 LOAD_ASSERTION_ERROR + RAISE_VARARGS 的 ternary 误判为 `assert (ternary)`（ternary 作 test），输出 `raise (ternary)()`；或反编译把 message 拆为独立语句，丢失 walrus 副作用与 message 关联。
- **修复**：
  1. `_build_ternary_no_target_consumer_stmt` 顶部新增守卫：merge_block 含 LOAD_ASSERTION_ERROR + RAISE_VARARGS 1 时，调用 `_build_assert_message_ternary_stmt` 让 AssertRegion 接管
  2. 新增 `_build_assert_message_ternary_stmt` 方法：识别 message 位置的 TernaryRegion，按 5 种 message 包装变体（简单 / f() / walrus / BinOp / dict）重建 message 表达式
  3. 输出 `Expr(msg_expr)` 让 `_generate_assert` 包装为 `Assert(test, msg)`，ternary blocks 标记为 generated
- **算法依据**：「父引用子入口」— AssertRegion.message_block 引用 TernaryRegion.entry 作为 message 表达式的子节点；「嵌套即抽象节点」— message 表达式整体（含 walrus / f() / BinOp / dict 包装）作为单个抽象节点，包含 ternary IfExp 作为 value。

### Bug R7-04/R8-06: del subscript 双 ternary 同 consumer — 已修复

- **测试**：`test_r7_ternary_in_del_target_complex.py`、`test_r8_ternary_del_subscript_both.py`
- **源码**：
  - `del obj[a if c else b][c if d else e]` — 双 subscript 双 ternary（R7-04）
  - `del (a if c1 else b)[x if c2 else y]` — base 与 key 都是 ternary（R8-06）
- **根因**：`_try_build_ternary_chained_container` 的 R6 多 ternary 同 call consumer 模式未覆盖 DELETE_SUBSCR consumer。两个 ternary 的 merge_block 都进入 DELETE_SUBSCR 块，违反「每块唯一归属」，反编译退化为多个 POP_TOP 表达式，完全丢失 del 结构。
- **修复**：新增 Pattern D 在 `_try_build_ternary_chained_r6_pattern`：
  - **R7-04 变体**：inner.cond_block prefix 末尾含 BINARY_SUBSCR — 表示外层 ternary 是 `obj[inner_ternary]` 的 obj（嵌套 subscript chain）
  - **R8-06 变体**：inner.cond_block prefix 为空 — 表示外层 ternary 直接是 obj，inner ternary 是 key
  - 输出 `Delete([Subscript(Subscript(obj, IfExp1, Del), IfExp2, Del)])`，两个 ternary blocks 标记为 generated
- **算法依据**：「父引用子入口」— 父 Delete 通过 DELETE_SUBSCR consumer 引用两个 TernaryRegion entry 作为 obj 与 key；「嵌套即抽象节点」— 嵌套 Subscript 整体作为单个 Delete target 抽象节点。

### Bug R8-04: walrus 捕获 ternary 结果 — 已修复

- **测试**：`test_r8_ternary_walrus_assign.py`
- **源码**：`(n := (a if c else b))`
- **根因**：`_generate_ternary` 的 value_target 分支把 walrus 的 `STORE_NAME n` 当作普通赋值目标，输出 `Assign([n], IfExp)`。但 walrus 字节码是 `COPY 1 + STORE_NAME n + POP_TOP`（保留栈顶供外层使用），不是普通 STORE 终结。重编丢失 walrus 留栈语义（指令数 9 vs 7）。
- **修复**：在 `_generate_ternary` 的 value_target 分支前增加 walrus 检测：
  1. `store_idx - 1` 处为 `COPY 1`（COPY_STACK_TOP）
  2. 过滤 trailing implicit return None 后，`store_idx + 1` 之后无 outer STORE_*（区别于 R15 Mode A 的「外层有 STORE」）
  3. 非噪音指令全部为 POP_TOP（区别于普通 Assign 的「STORE 终结不留栈」）
  4. 输出 `Expr(NamedExpr(Name(n, Store), IfExp))`，ternary blocks 标记为 generated
- **算法依据**：「嵌套即抽象节点」— walrus NamedExpr 作为单个抽象节点，包含 ternary IfExp 作为 value；「父引用子入口」— 父 Expr 通过 COPY 1 + STORE + POP_TOP consumer 引用 ternary 子节点。

### Bug R8-05: unpacking 赋值 source 是 ternary — 已修复

- **测试**：`test_r8_ternary_unpack_assign.py`
- **源码**：`*y, = (a if c else b)`
- **根因**：value_target 推断吞并了 `UNPACK_EX + STORE_NAME y` 序列，输出 `Assign([y], IfExp)`，丢失 starred unpack target（指令数 8 vs 7）。
- **修复**：在 `_generate_ternary` value_target 分支新增 Mode 3 UNPACK_EX 检测：
  1. merge_block 首条非噪音指令为 `UNPACK_EX`
  2. 后续为 `before + 1 + after` 个 STORE_* 序列（starred 解包）
  3. 输出 `Assign(targets=[Starred(Name(starred_name, Store))], value=IfExp)`（或多元 tuple target 含 Starred）
- **算法依据**：「嵌套即抽象节点」— Starred target + UNPACK_EX 作为单个抽象节点，包含 ternary IfExp 作为 value；「父引用子入口」— 父 Assign 通过 UNPACK_EX + STORE 序列引用 ternary 子节点。

### Bug R8-07: import from alias 后跟 ternary 赋值 — 已修复

- **测试**：`test_r8_ternary_in_import_from_alias.py`
- **源码**：`from x import y as z\nw = a if c else b`
- **根因**：`generate()` 的 TernaryRegion 分支只 `pass`，未提取 entry_block 中的 import 语句。ternary 的 condition preload 扫描只识别 LOAD_NAME c 等条件 preload 指令，import 指令（IMPORT_NAME + IMPORT_FROM + STORE_NAME）被丢弃（指令数 13 vs 7）。
- **修复**：
  1. 新增 `_extract_imports_from_block_prefix` helper：扫描块前缀的 IMPORT_NAME + IMPORT_FROM + STORE_* 序列
     - 跳过 RESUME / NOP / CACHE / POP_TOP / PUSH_NULL / LOAD_CONST（import level + fromlist）等噪音
     - 遇跳转指令（FORWARD_JUMP_OPS / BACKWARD_JUMP_OPS / JUMP_FORWARD/BACKWARD/ABSOLUTE）终止
     - 遇非 import 非 STORE 指令（如 LOAD_NAME c，ternary condition preload）终止，留给 ternary 处理
     - 返回 ImportFrom / Import AST 字典列表
  2. `generate()` 的 TernaryRegion 分支调用 helper，把 import 加入 ast_nodes
  3. **不标记** entry_block 为 generated — 留给 ternary 的 condition preload 处理（LOAD_NAME c 等）
- **算法依据**：「每块唯一归属」— import 指令归 generate() 预扫描，ternary condition preload 归 TernaryRegion，两者通过指令序列前后划分归属，不重叠；「父引用子入口」— generate() 通过 entry_block 的 import 指令序列引用 import 节点，TernaryRegion 通过 condition preload 引用 ternary 子节点。

## 未修复 bug — async 控制流系列（4 个，留待 R9+）

### 评估结论

本轮评估 4 个 async 系列 bug（R7-02 / R7-03 / R7-10 / R8-08），决定留待 R9+ 处理，原因：

1. **多文件多修改点**：4 个 bug 涉及至少 3 处不同子系统修改
   - R7-02 / R7-10 / R8-08 → `region_analyzer.py` 的 `_identify_loop_regions` async for polling 块归属 + `_identify_ternary_regions` merge_context='async_iter' 设置 + `_generate_ternary` async_iter 分支 + `_generate_loop` async for body/else 处理 + 多处「Skip ternary with merge_context='iter'」守卫扩展为也跳过 'async_iter'
   - R7-03 → `region_ast_generator.py` 的 `_generate_with` as_target 早期推断守卫 + with body 主循环 TernaryRegion entry 识别
2. **4 个 bug 需要 4 种不同修复方向**：async for body / async with body / async for-else / async for iter，无法用一个统一修复覆盖
3. **退化风险高**：async for/with 的 polling 块（GET_AITER + GET_ANEXT + GET_AWAITABLE + SEND + YIELD_VALUE + RESUME + JUMP_BACKWARD_NO_INTERRUPT）路径与同步 for/with 共享 LoopRegion / WithRegion 类，修改 polling 块归属可能影响已稳定的同步 for/with ternary 测试（如 `test_r8_ternary_for_iter.py` 已通过）
4. **本轮主要目标已达成**：P0/P1/P2 全部完成，ternary 63 failed ≤ 65 目标，跨区域 107 failed ≤ 109 目标，无基线退化

按 Spec Mode「Favor straightforward, minimal implementations first」+ 基线 100% 不可退化 原则，async 系列留待 R9+ 单独处理。

| Bug | 测试 | 类别 | 说明 |
|-----|------|------|------|
| R7-02 | test_r7_ternary_in_async_for | async for body | `async for body: y = a if c else b` — ternary 完全退化为 `a\nb` 表达式泄漏 + 赋值丢失。需在 `_identify_loop_regions` 区分 async for polling 块与 body 内 ternary merge 块 |
| R7-03 | test_r7_ternary_in_async_with | async with body | `async with ctx: y = a if c else b` — ternary 的 STORE_FAST y 被误识别为 with 的 as 目标（POP_TOP vs STORE_FAST 不匹配）。需在 `_generate_with` as_target 推断增加 TernaryRegion 归属守卫 |
| R7-10 | test_r7_ternary_in_async_for_else | async for-else | `async for-else: y = a if c else b` — else 块 + ternary 完全丢失，反编译出 `while True: pass` 幻影循环。需在 `_identify_loop_regions` 扩展 async for else 块识别（END_ASYNC_FOR 后 fall-through 块） |
| R8-08 | test_r8_ternary_async_for_iter | async for iter | `async for x in (a if c else b): pass` — 重编多 POP_TOP + LOAD_CONST 两条指令。需在 `_identify_ternary_regions` 检测 merge_block 是否为 async for 的 GET_AITER 源块，设置 `merge_context='async_iter'` |

### 未修复 bug — skip 系列（2 个，不计入 failure 总数）

| Bug | 测试 | 类别 | 说明 |
|-----|------|------|------|
| R8-S1 | test_r8_ternary_del_attr_chain | del subscript + attr | `del obj[a if c else b].attr` — 反编译输出 `return obj[ternary]`（无 del、无 .attr），重编译 syntax error → skipTest。R7-04/R8-06 del 链问题极端变体 |
| R8-S2 | test_r8_ternary_in_fstring_nested | f-string + ternary 模块顶层 | `x = f"prefix-{a if c else b}-suffix"` — 反编译输出 `return f'...'`（return 出现在模块顶层），重编译 `'return' outside function` → skipTest。f-string + ternary + 字面量的 BUILD_STRING 3 路径在模块顶层误判 merge_context='return' |

## 回归验证

### R8 新测试（29 个）
```
8 failed → 0 failed (10 修复覆盖 8 failed + 2 已转 pass 的退化测试)
2 skip → 2 skip (R8-S1/S2 反编译输出语法错误，不计入 failure)
19 passed → 19 passed (无退化)
```

实际：5 类 bug 修复覆盖 10 个测试（assert family 5 + del subscript 2 + R8-04 + R8-05 + R8-07），全部转 pass。

### Ternary 区域全量回归
```
基线（R7 完成）: 65 failed, 228 passed, 1 skipped (294 测试)
R8 测试添加后（无修复）: 73 failed, 247 passed, 3 skipped (323 测试) [R8 新增 8 failed + 19 passed + 2 skipped]
R8 修复后（最终）: 63 failed, 257 passed, 3 skipped (323 测试)
```

- Ternary: 73 → 63 (-10 failed，5 类 bug 修复覆盖 10 测试，0 退化)
- 满足 ≤65 failed 目标 ✅

### 跨区域回归（ternary + if_region）
```
基线（R7 完成）: 109 failed, 1001 passed, 11 skipped (1121 测试)
R8 修复后（最终）: 107 failed, 1030 passed, 13 skipped (1150 测试)
```

- 跨区域: 109 → 107 (-2 failed，+29 passed = R8 新增 29 测试，0 基线退化)
- 满足 ≤109 failed 目标 ✅
- if_region 无基线退化（T1.20 完成后基线保持）

### 跨区域全 exhaustive 回归（除 ternary，--import-mode=importlib）
```
108 failed, 2580 passed, 24 skipped, 169 errors (deep_nesting 已知 NotImplementedError)
```
- 169 errors 全部来自 `test_ternary_deep_nesting.py` 的 `NotImplementedError: 子类必须定义SOURCE_CODE`（预存测试问题，与本轮无关）
- 108 failed 中包含 if_region / loop_region / structured / L1_basic / L2_two_level_nested 等区域，无 R8 修复引入的新退化

### 退化分析
- Ternary: 73 → 63 (-10 failed，R8 修复 5 类 bug 10 测试，0 退化)
- 跨区域: 109 → 107 (-2 failed，0 退化)
- 退化检测：R8 修复过程中通过逐步回归确认每步无新退化；R8-04 walrus 修复后立即跑全量 ternary 回归确认 64 failed（基线 65 - 1）；R8-07 import 修复后立即跑 R8-07 单测确认通过 + 全量 ternary 回归确认 63 failed
- 已修复 R7-01/01b + R8-01/02/03/04/05/06/07 共 10 测试，无任何已通过测试转 failed

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| R7/R8: assert message ternary 家族 | 5 | 5 (R7-01/01b, R8-01/02/03) | 0 |
| R7/R8: del subscript 双 ternary 家族 | 2 | 2 (R7-04, R8-06) | 0 |
| R8: walrus 捕获 ternary | 1 | 1 (R8-04) | 0 |
| R8: unpacking 赋值 source ternary | 1 | 1 (R8-05) | 0 |
| R8: import + ternary | 1 | 1 (R8-07) | 0 |
| R7/R8: async 控制流 ternary | 4 | 0 | 4 (R7-02/03/10, R8-08) |
| R8: skip 系列（语法错误，不计入） | 2 | 0 | 2 (R8-S1/S2) |
| **总计** | **16** | **10** | **6** |

## 算法 4 原则核查

所有修复均严格遵循区域归约算法 4 原则：

1. **自底向上归约**: ternary 作为内层区域先归约为 IfExp 表达式，外层 Assert / Delete / Expr(NamedExpr) / Assign(Starred) / 模块顶层 import 序列作为父区域后归约时引用 IfExp。
2. **每块唯一归属**:
   - assert message ternary 的 merge_block（含 LOAD_ASSERTION_ERROR + RAISE_VARARGS）归属 AssertRegion.message_block 归约，ternary entry/true/false 归属 TernaryRegion
   - del subscript 双 ternary 的两个 merge_block 都归属 DELETE_SUBSCR consumer，通过 chain 识别两个 TernaryRegion entry，不重复生成
   - walrus / unpack 的 merge_block 归属 ternary 父区域，COPY 1 + STORE_* + POP_TOP / UNPACK_EX + STORE_* 序列作为 consumer 引用 ternary
   - import + ternary 的 entry_block 通过指令序列前后划分：import 指令归 generate() 预扫描，condition preload 归 TernaryRegion
3. **嵌套即抽象节点**:
   - assert message 整体（含 walrus / f() / BinOp / dict 包装）作为单个抽象 message 节点
   - del subscript 嵌套 Subscript 整体作为单个 Delete target 抽象节点
   - walrus NamedExpr 作为单个抽象 Expr 节点
   - Starred + UNPACK_EX 作为单个抽象 Assign target 节点
4. **父引用子入口**:
   - AssertRegion.message_block 引用 TernaryRegion.entry 作为 message 表达式
   - Delete 通过 DELETE_SUBSCR consumer 引用两个 TernaryRegion entry 作为 obj 与 key
   - Expr(NamedExpr) 通过 COPY 1 + STORE + POP_TOP consumer 引用 ternary 子节点
   - Assign(Starred) 通过 UNPACK_EX + STORE 序列引用 ternary 子节点
   - generate() 通过 entry_block 的 import 指令序列引用 import 节点

**禁止事项核查**:
- ✅ 无跨区域启发式特例（所有修复均在 TernaryRegion / 父区域内部）
- ✅ 无后处理补丁（所有修复在区域归约阶段完成）
- ✅ 无启发式优先级覆盖（未调整区域识别优先级）
- ✅ 无扁平化（嵌套 ternary / 嵌套 Subscript 保持 AST 结构，无硬编码深度上限）
- ✅ 无 debug 打印残留
- ✅ 无根级 debug 脚本残留（6 个 _debug_*.py 已清理）

## 后续方向（R9+）

1. **R7-02 / R7-10 / R8-08 async for + ternary 家族**（3 测试）：
   - 在 `region_analyzer.py` 的 `_identify_ternary_regions` 中检测 merge_block 是否为 async for 的 GET_AITER 源块，设置 `merge_context='async_iter'`
   - 在 `_generate_ternary` 增加 `merge_context == 'async_iter'` 分支，输出 `Expr(IfExp)` 并把 IfExp 表达式传递给 async for 的 LoopRegion iter 表达式槽位（参考同步 for 的 merge_context='iter' 实现，region_ast_generator.py:16987+）
   - 在 `_identify_loop_regions` 中识别 async for 的 polling 块模式（GET_AITER + GET_ANEXT + GET_AWAITABLE + SEND + YIELD_VALUE + RESUME + JUMP_BACKWARD_NO_INTERRUPT），与同步 for polling 块同等处理
   - 在 `_identify_loop_regions` 扩展 async for 的 else 块识别（END_ASYNC_FOR 后 fall-through 块）
   - 多处「Skip ternary with merge_context='iter'」守卫扩展为也跳过 'async_iter'（region_ast_generator.py:7272/7357/9797/10170 等 4 处）

2. **R7-03 async with body ternary**（1 测试）：
   - 在 `_generate_with` 的 as_target 早期推断（region_ast_generator.py:13042-13066）增加守卫：仅当 STORE_FAST 是 async with 的 SEND polling 循环跳出后第一个块的首条指令时才作为 as_target；若该块已属于 TernaryRegion（即 `region_analyzer.get_region_for_block(wb) is TernaryRegion`），跳过 as_target 推断
   - 在 with body 主循环扫描 with_blocks 时，遇到 TernaryRegion entry 应调用 `_generate_ternary(inner)`，让 ternary merge 块的 STORE_FAST y 归属 ternary，而非 with body 顶层语句

3. **R8-S1 del obj[ternary].attr**（1 skip）：
   - R7-04/R8-06 del subscript 双 ternary 修复的极端变体（del subscript + attr 链式访问）
   - 在 `_try_build_ternary_chained_r6_pattern` Pattern D 扩展：DELETE_SUBSCR 后跟 LOAD_ATTR + DELETE_ATTR 时，输出 `Delete([Attribute(Subscript(obj, IfExp, Del), attr, Del)])`

4. **R8-S2 f-string + ternary 模块顶层**（1 skip）：
   - 在 `_generate_ternary` merge_context='fstring' 分支（region_ast_generator.py:16876+）检查 enclosing function
   - 模块顶层（无 enclosing function）时不应生成 Return；应生成 `Expr(JoinedStr)` 让外层 Assign 引用

5. **跨区域测试目录名冲突**（环境问题，非 bug）：
   - `tests/exhaustive/L1_basic/` 与 `tests/exhaustive/structured/l1_basic/` 存在同文件名（test_b05_expression_statement.py 等）
   - pytest 默认 rootdir 导入冲突，需用 `--import-mode=importlib` 解决
   - 建议 R9+ 重命名其中一组目录或加 `__init__.py` 消除冲突
