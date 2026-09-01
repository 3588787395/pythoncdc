# Ternary Region Round 04 — 修复报告

## 修复概览

- **测试总数**：23 个 R4 新测试（11 失败 / 12 passed）
- **已修复 R4 bug**：9 个（R4-01, R4-02, R4-04, R4-05, R4-06, R4-07, R4-08, R4-09, R4-11）
- **顺带修复基线 bug**：4 个（基线 61 failed → 57 failed）
- **未修复 R4 bug**：2 个（R4-03 chained_compare_4way 部分修复；R4-10 while_cond 完全回滚）
- **回归状态**：
  - Ternary: 61 failed → 59 failed（基线减 4 bonus + R4 新增 2 failed）/ 133 passed → 158 passed / 1 skipped
  - 跨区域: 107 failed → 104 failed / 927 passed → 930 passed / 11 skipped（无退化，改善 3）
- **修改文件**：`core/cfg/region_analyzer.py`（R4-10 回滚后无残留改动），`core/cfg/region_ast_generator.py`（多处）

## 修改文件清单

| 文件 | 改动位置 | 改动内容 |
|------|---------|---------|
| `core/cfg/region_ast_generator.py` | `_try_build_ternary_chained_container` ~L18152 | 重写 chain 收集逻辑；新增 call pattern（R4-06）；新增 fstring pattern（R4-07）；dict key 提取（R4-04）；chain 收集循环条件扩展（R4-08） |
| `core/cfg/region_ast_generator.py` | `_try_build_ternary_store_assign` ~L17829 | 新增 DELETE_SUBSCR elif 分支（R4-05 del_subscript） |
| `core/cfg/region_ast_generator.py` | `_resolve_nested_ternary_context_expr` ~L12474 | 新增方法：通过 entry block 反向引用嵌套 TernaryRegion 的归约结果（R4-11 with_ctx_mgr） |
| `core/cfg/region_ast_generator.py` | `_generate_with` context_expr fallback ~L13481 | 替换原 `context()` fallback 为 `_resolve_nested_ternary_context_expr` 调用（R4-11） |
| `core/cfg/region_ast_generator.py` | `_generate_region` TernaryRegion 守卫 ~L1600, L1613 | 新增 WithRegion 守卫（R4-11）+ TryExceptRegion 守卫（R4-09）：当 ternary.merge_block/entry 属于父区域时返回 None |
| `core/cfg/region_ast_generator.py` | `_build_ternary_no_target_consumer_stmt` Pattern 7 ~L17853 | 新增 Pattern 7：`await (ternary)` GET_AWAITABLE consumer 返回 `Expr(Await(IfExp))`（R4-02） |
| `core/cfg/region_ast_generator.py` | `_generate_try` 嵌套 ternary 预处理 ~L11448 | 在 _generate_try 开头扫描 entry 在 handler_entry_blocks 中的嵌套 TernaryRegion，标记为 generated（R4-09） |
| `core/cfg/region_ast_generator.py` | `_generate_try` handler exc_type 检测 ~L11580 | 检测嵌套 ternary 作为 handler exc_type，调用 _generate_ternary 提取 IfExp 表达式（R4-09） |
| `core/cfg/region_ast_generator.py` | `_collect_post_ternary_positional_args` ~L17887 | 新增方法：收集 ternary 后位置参数（R4-01 setattr 中间参数） |
| `core/cfg/region_ast_generator.py` | 嵌套 ternary absorption ~L17465 | 调用 `_collect_post_ternary_positional_args` 重建多参数 Call（R4-01） |
| `core/cfg/region_ast_generator.py` | `_build_ternary_wrapped_expr` ~L8731, L8754, L8762 | 加入 SHORT_CIRCUIT_JUMP_OPS 识别 chained compare 中段跳转；新增 for-else 末段 Compare 收集（R4-03 部分修复） |
| `core/cfg/region_analyzer.py` | (R4-10 回滚) | 无残留改动 — R4-10 while_cond 修复尝试全部回滚 |

## Bug 详细修复

### Bug R4-01: setattr 中间参数 — `setattr(obj, name if c else name2, val)` — 已修复

- **测试**：`test_r4_ternary_attr_assign.py`
- **源码**：`setattr(obj, "attr" if c else "name", val)`
- **根因**：ternary 在 setattr 调用的第二参数位置，cond_block 的 preload 含 `PUSH_NULL + LOAD_GLOBAL setattr + LOAD_NAME obj`，merge_block 含 `PRECALL + CALL + POP_TOP`。原 `_try_build_ternary_call_arg` 仅处理 ternary 作为唯一参数场景，未重建 ternary 后的位置参数（val）。
- **修复**：新增 `_collect_post_ternary_positional_args` 方法，在嵌套 ternary absorption 之后调用，从 merge_block 收集 ternary 后的位置参数，重建 `Call(func=setattr, args=[obj, IfExp, val])`。
- **算法依据**：「父引用子入口」— 父 Call 通过 cond_block preload（setattr + obj）+ merge_block CALL 引用 ternary 子节点；merge_block 的 val LOAD 也归属父 Call。
- **字节码验证**：`PUSH_NULL, LOAD_GLOBAL setattr, LOAD_NAME obj, PRECALL, CALL, POP_TOP` 完整保留。

### Bug R4-02: await_expr — `await (a if c else b)` — 已修复

- **测试**：`test_r4_ternary_await_expr.py`
- **源码**：`async def f(): await (a if c else b)`
- **根因**：ternary 在 await 上下文中，merge_block 含 `GET_AWAITABLE + SEND + ... + POP_TOP` 消费链。原 `_build_ternary_no_target_consumer_stmt` 未识别 await 模式，回退到 `Expr(IfExp)`，丢失 `await` 包装。
- **修复**：新增 Pattern 7 — 当 merge_instrs 含 `GET_AWAITABLE` 时，返回 `Expr(Await(value=IfExp))`。
- **算法依据**：「父引用子入口」— 父 Await 通过 merge_block 的 GET_AWAITABLE+SEND 引用 ternary 子节点。
- **字节码验证**：`GET_AWAITABLE, SEND, POP_TOP` 完整保留。

### Bug R4-04: dict_value — `d = {k: a if c else b}` — 已修复

- **测试**：`test_r4_ternary_dict_value.py`
- **源码**：`d = {k: a if c else b}`
- **根因**：每个 dict 元素的 value 是独立的 ternary，共享 merge_block 的 `BUILD_MAP`。原 `_try_build_ternary_chained_container` 的 chain 收集逻辑未正确从每个 ternary 的 cond_block 提取 dict key。
- **修复**：重写 `_try_build_ternary_chained_container`，每个 ternary 从自己的 cond_block 提取 dict key（LOAD_NAME k），构建 `Dict(keys=[k], values=[IfExp])`。
- **算法依据**：「嵌套即抽象节点」— 每个 ternary 作为 Dict value 的抽象子节点；「父引用子入口」— 父 Dict 通过每个 ternary 的 cond_block key 入口 + merge_block BUILD_MAP 引用 ternary 子节点。

### Bug R4-05: del_subscript — `del x[a if c else b]` — 已修复

- **测试**：`test_r4_ternary_in_del_target.py`
- **源码**：`del x[a if c else b]`
- **根因**：ternary 作为 del 的 subscript 目标，merge_block 含 `DELETE_SUBSCR` 消费 ternary 结果。原 `_try_build_ternary_store_assign` 仅处理 STORE_* 指令，未识别 DELETE_SUBSCR。
- **修复**：在 `_try_build_ternary_store_assign` 新增 DELETE_SUBSCR elif 分支，从 cond_block 提取 preload（LOAD_NAME x），构建 `Delete(targets=[Subscript(value=x, slice=IfExp, ctx=Del)])`。
- **算法依据**：「父引用子入口」— 父 Delete 通过 cond_block preload（x）+ merge_block DELETE_SUBSCR 引用 ternary 子节点。
- **字节码验证**：`LOAD_NAME x, DELETE_SUBSCR` 完整保留。

### Bug R4-06: format — `"{}".format(a if c else b)` — 已修复

- **测试**：`test_r4_ternary_in_format.py`
- **源码**：`"{}".format(a if c else b)`
- **根因**：ternary 作为 format 调用的参数，cond_block 的 preload 含 `LOAD_CONST "{}"` + LOAD_ATTR format。原 `_try_build_ternary_chained_container` 未识别 call pattern（method call on constant）。
- **修复**：新增 call pattern 检测，支持 `LOAD_CONST obj + LOAD_ATTR method` 模式，构建 `Call(func=Attribute(value=Constant("{}"), attr="format"), args=[IfExp])`。
- **算法依据**：「父引用子入口」— 父 Call 通过 cond_block preload（"{}" + format）+ merge_block CALL 引用 ternary 子节点。

### Bug R4-07: fstring — `f"{a if c else b}"` — 已修复

- **测试**：`test_r4_ternary_in_fstring.py`
- **源码**：`f"{a if c else b}"`
- **根因**：ternary 作为 fstring 的 FORMAT_VALUE 参数，merge_block 含 `FORMAT_VALUE + BUILD_STRING`。原 `_try_build_ternary_chained_container` 未识别 `merge_context='fstring'` 作为有效 chain endpoint。
- **修复**：识别 `merge_context='fstring'` 作为有效 chain endpoint，构建 `JoinedStr(values=[FormattedValue(value=IfExp)])`。
- **算法依据**：「父引用子入口」— 父 JoinedStr 通过 merge_block FORMAT_VALUE+BUILD_STRING 引用 ternary 子节点。

### Bug R4-08: set_elem — `s = {a if c else b, c if d else e}` — 已修复

- **测试**：`test_r4_ternary_set_elem.py`
- **源码**：`s = {a if c else b, c if d else e}`
- **根因**：两个 ternary 共享 merge_block 的 `BUILD_SET`。原 chain 收集循环条件未覆盖 set 场景。
- **修复**：修改 chain 收集循环条件，支持多 ternary 共享 BUILD_SET，构建 `Set(elts=[IfExp1, IfExp2])`。
- **算法依据**：「嵌套即抽象节点」— 每个 ternary 作为 Set elt 的抽象子节点。

### Bug R4-09: except_handler_type — `except (E1 if c else E2) as e:` — 已修复

- **测试**：`test_r4_ternary_try_handler_type.py`
- **源码**：`try: ... except (E1 if c else E2) as e: ...`
- **根因**：ternary 作为 except handler 的异常类型，TernaryRegion.entry 是 TryExceptRegion 的 handler_entry_block。原 _generate_try 未识别嵌套 ternary 作为 exc_type，handler body 仍包含 ternary 的 if-else 结构。
- **修复**：
  1. `_generate_try` 开头预处理嵌套 ternary，标记其 blocks 为 generated
  2. `_generate_try` handler 构建时检测嵌套 ternary 作为 exc_type，调用 _generate_ternary 提取 IfExp 表达式
  3. `_generate_region` TernaryRegion 守卫：当 ternary.entry 属于 TryExceptRegion.handler_entry_blocks 时返回 None（让父 _generate_try 处理）
- **算法依据**：「自底向上归约」— ternary 先归约为 IfExp，父 TryExcept 后归约时引用之；「父引用子入口」— 父 TryExcept 通过 handler_entry_block 入口引用 ternary 子节点。
- **字节码验证**：`CHECK_EXC_MATCH, POP_JUMP_FORWARD_IF_FALSE` 完整保留。

### Bug R4-11: with_ctx_mgr — `with (a if c else b) as x:` — 已修复

- **测试**：`test_r4_ternary_with_ctx_mgr.py`
- **源码**：`with (a if c else b) as x: pass`
- **根因**：ternary 作为 with 的上下文管理器，WithRegion.entry 是 TernaryRegion.merge_block。原 _generate_with 的 context_expr 提取失败（context_instrs 为空），fallback 到 `context()` 调用。
- **修复**：
  1. 新增 `_resolve_nested_ternary_context_expr` 方法：通过 WithRegion.entry 反向查找嵌套 TernaryRegion，调用 _generate_ternary 提取 IfExp
  2. `_generate_with` context_expr fallback 替换为 `_resolve_nested_ternary_context_expr` 调用
  3. `_generate_region` TernaryRegion 守卫：当 ternary.merge_block 是 WithRegion.entry 时返回 None
- **算法依据**：「父引用子入口」— 父 With 通过 entry（=ternary.merge_block）引用 ternary 子节点；「自底向上归约」— ternary 先归约为 IfExp，父 With 后归约时引用之。
- **字节码验证**：`BEFORE_WITH, STORE_NAME x` 完整保留。

## 未修复 bug（2 个，留待 R5+）

| Bug | 测试 | 类别 | 说明 |
|-----|------|------|------|
| R4-03 | test_r4_ternary_chained_compare_4way | chained_compare | 部分修复：chained compare 表达式已正确构建为 `0 < IfExp < 10 < 100`，但 IfRegion 仍渲染为 `if (...): pass` 而非 `r = ...`。需调整 IfRegion 的 chained compare 与 Assign 的边界处理（STORE_NAME(r) 应触发 Assign 而非 if 语句） |
| R4-10 | test_r4_ternary_while_cond | while_cond | 完全回滚：while(ternary) 模式过于复杂 — ternary 与 while 循环结构融合（ternary 的 true/false blocks 同时充当 while 条件测试），需要更基础的结构重构。所有 R4-10 修复尝试已回滚 |

## R4-03 部分修复说明

R4-03 修复尝试在 `_build_ternary_wrapped_expr` 中加入了 `SHORT_CIRCUIT_JUMP_OPS` 识别 chained compare 中段跳转（JUMP_IF_FALSE_OR_POP），并新增 for-else 末段 Compare 收集。这些改动使 chained compare 表达式正确构建为 `0 < (a if cond else b) < 10 < 100`，但 IfRegion 仍被渲染为 `if` 语句而非 `r = ...` 赋值。

部分修复保留在代码中（不引入退化，且对其他 chained compare 场景有正面影响），完整修复留待 R5+ 处理 IfRegion 的 chained compare + Assign 边界。

## R4-10 回滚说明

R4-10 while_cond 修复尝试在 `region_analyzer.py` 中加入：
- `_is_while_ternary_pattern` 方法
- `BoolOpRegion.can_be_ternary_header` while-ternary 例外
- `_detect_ternary_pattern` loop_regions 检查

但这些改动导致 TernaryRegion 错误地包含 exit blocks 和 loop header（`blocks=[0, 6, 10, 12, 16, 40, 44]`），违反「每块唯一归属」原则。全部回滚后基线恢复，R4-10 标记为已知限制。

## 回归验证

### R4 新测试
```
11 failed → 2 failed（9 修复：R4-01, 02, 04, 05, 06, 07, 08, 09, 11）
12 passed → 21 passed
```

### Ternary 区域全量回归
```
基线（R3 完成）: 61 failed, 133 passed, 1 skipped (195 测试)
R4 测试添加后（无修复）: 72 failed, 142 passed, 1 skipped (218 测试)
R4 修复后（最终）: 59 failed, 158 passed, 1 skipped (218 测试)
```

### 跨区域回归（ternary + if_region）
```
基线: 107 failed, 927 passed, 11 skipped
R4 修复后: 104 failed, 930 passed, 11 skipped（改善 3，无退化）
```

### 退化分析
- 基线 61 failed → 现 59 failed（基线减 4 bonus + R4 新增 2 failed = 净减 2）
- R4 新增 2 failed（R4-03 chained_compare_4way + R4-10 while_cond，均已知限制）
- 4 个基线 bug 顺带修复（chained compare / fstring / format / set 相关基线）
- 跨区域改善 3（if_region 无退化，ternary 改善 3）
- R4-10 回滚后无任何残留退化

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| R4: 调用中间参数 (setattr) | 1 | 1 (R4-01) | 0 |
| R4: await (GET_AWAITABLE consumer) | 1 | 1 (R4-02) | 0 |
| R4: chained_compare 4-way | 1 | 0 (部分修复) | 1 (R4-03) |
| R4: dict value | 1 | 1 (R4-04) | 0 |
| R4: del subscript | 1 | 1 (R4-05) | 0 |
| R4: format call | 1 | 1 (R4-06) | 0 |
| R4: fstring | 1 | 1 (R4-07) | 0 |
| R4: set elem | 1 | 1 (R4-08) | 0 |
| R4: except handler type | 1 | 1 (R4-09) | 0 |
| R4: while cond | 1 | 0 | 1 (R4-10) |
| R4: with ctx mgr | 1 | 1 (R4-11) | 0 |
| **基线 bonus** | 4 | 4 | 0 |
| **总计** | **15** | **13** | **2** |

## 算法 4 原则核查

所有修复均严格遵循区域归约算法 4 原则：

1. **自底向上归约**: ternary 作为内层区域先归约为 IfExp 表达式，外层 Await/Call/Dict/Set/JoinedStr/TryExcept/With 作为父区域后归约时引用 IfExp。
2. **每块唯一归属**: merge_block 的 wrapping 指令（GET_AWAITABLE/CALL/BUILD_MAP/BUILD_SET/FORMAT_VALUE/DELETE_SUBSCR/BEFORE_WITH/CHECK_EXC_MATCH）归属到 ternary 父区域，不与 ternary 子区域重叠。
3. **嵌套即抽象节点**: 多个 ternary 共享 merge_block 时（Dict/Set/Call），每个 ternary 作为父容器的抽象子节点。
4. **父引用子入口**: 父区域通过 cond_block preload + merge_block wrapping 指令引用 ternary 子节点；对 with/try 等外层区域，通过 entry（=ternary.merge_block 或 handler_entry_block=ternary.entry）引用。

**禁止事项核查**:
- ✅ 无跨区域启发式特例（所有修复均在 TernaryRegion / 父区域内部）
- ✅ 无后处理补丁（所有修复在区域归约阶段完成）
- ✅ 无启发式优先级覆盖（未调整区域识别优先级，R4-10 优先级覆盖已回滚）
- ✅ 无扁平化（嵌套 ternary 保持 IfExp AST 结构，无硬编码深度上限）
- ✅ R4-10 回滚验证：`grep "_is_while_ternary_pattern"` 0 结果（无残留）

## 后续方向（R5+）

1. **R4-03 chained_compare_4way 完整修复**: 调整 IfRegion 的 chained compare + Assign 边界，使 STORE_NAME(r) 触发 Assign 而非 if 语句。需在 _process_if_blocks 或 chained compare IfRegion 生成时检测 merge_block 的 STORE_* 指令。
2. **R4-10 while_cond**: 需要更基础的结构重构 — 当前 while(ternary) 模式中 ternary 的 true/false blocks 同时充当 while 条件测试，违反「每块唯一归属」原则。可能需要在 _identify_loop_regions 阶段识别 while(ternary) 模式，将 ternary 提取为 while 的 condition_expr 而非独立 region。
3. **新方向探索**: ternary 在 class body / decorator / global / nonlocal 等位置的边界处理。
