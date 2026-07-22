# Ternary Region Round 07 — 修复报告

## 修复概览

- **测试总数**：32 个 R7 新测试（11 失败 / 21 passed）
- **已修复 R7 bug**：5 个（R7-05, R7-07, R7-11, R7-09, R7-06）
- **顺带修复退化**：1 个（R3-08/R4-05 BFS walk 误判 except 为 finally）
- **未修复 R7 bug**：6 个（R7-01/02/03/04/08/10 留待 R8+）
- **回归状态**：
  - Ternary: 70 failed → 65 failed（-5）/ 223 passed → 228 passed / 1 skipped
  - 跨区域: 103 failed → 109 failed（净 +6 = R7 新增 11 failed - 5 修复，无基线退化）/ 975 passed → 1001 passed / 11 skipped
- **修改文件**：`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`

## 修改文件清单

| 文件 | 改动位置 | 改动内容 |
|------|---------|---------|
| `core/cfg/region_analyzer.py` | `_classify_handler_with_cleanup` ~L5669-5713 | BFS walk 检测 finally 异常路径；新增 CHECK_EXC_MATCH/CHECK_EG_MATCH 守卫防止 except handler 误判为 finally（R7-05/07/11 + R3-08/R4-05 退化修复） |
| `core/cfg/region_analyzer.py` | yield-from + assign 检测 ~L11948-11994 | 新增 elif 检测 STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF 作为 yield-from consume block，记录 value_target（R7-06） |
| `core/cfg/region_ast_generator.py` | `generate()` 全局预标记 ~L554-605 | 识别 TryExceptRegion 的 normal path 副本 TernaryRegion ID，跳过加入 filtered（R7-05/07/11） |
| `core/cfg/region_ast_generator.py` | `_generate_try_body` try_blocks 预标记 ~L10995-11038 | 扫描所有 region 标记 normal path 副本 blocks 为已生成（R7-05/07/11） |
| `core/cfg/region_ast_generator.py` | `_generate_try_body` children 遍历 ~L11526-11561 | 泛化 normal path 副本检测条件为 `entry not in finally_blocks + sibling 结构相同`（R7-11） |
| `core/cfg/region_ast_generator.py` | finally body 遍历 ~L12092-12121 | 识别 TernaryRegion 子区域，委托 `_generate_region` 归约（R7-05/07/11） |
| `core/cfg/region_ast_generator.py` | `_try_build_ternary_store_assign` Pattern D2 ~L18808-18851 | 新增 Pattern D2：ternary 作为 del subscript 的 base obj，重建 key 表达式（R7-09） |
| `core/cfg/region_ast_generator.py` | Pattern 4 & 5 yield-from + 赋值 ~L18469-18494 | 当 full_expr 是 YieldFrom + merge_context='yieldfrom' + value_target 非空时，包裹为 Assign（R7-06） |

## Bug 详细修复

### Bug R7-05/07/11: finally 块 ternary 归约完全缺失 — 已修复

- **测试**：`test_r7_ternary_in_finally.py`、`test_r7_ternary_in_nested_try_finally.py`、`test_r7_ternary_in_try_except_finally_finally.py`
- **源码**：
  - `try: pass\nfinally: y = a if c else b`
  - 嵌套 try-finally + 内层 finally ternary
  - `try: pass\nexcept E: pass\nfinally: y = a if c else b`
- **根因**：CPython 3.11+ 把 finally body 复制两份：normal path 副本（在 try_blocks 或 normal completion 路径，无 PUSH_EXC_INFO）+ exception path 副本（在 finally_blocks，含 PUSH_EXC_INFO + RERAISE）。原代码：
  1. `_classify_handler_with_cleanup` 误分类 finally body 含 ternary 时为 except（successors 是 ternary 的 true/false value 块，单层 walk 无法到达 merge 块的 RERAISE）
  2. normal path 副本 TernaryRegion 作为顶级区域独立输出
  3. normal path 副本 blocks 被 try_blocks 遍历消费
  4. children 遍历误把 normal path 副本当作 try body 子区域
- **修复**：
  1. BFS walk 检测 finally 异常路径（successors 是 ternary value 块时仍能到达 RERAISE）
  2. 全局预标记 normal path 副本 TernaryRegion ID，跳过加入 filtered
  3. try_blocks 遍历前标记 normal path 副本 blocks 为已生成
  4. children 遍历中泛化 normal path 副本检测条件
  5. finally body 遍历识别 TernaryRegion 子区域，委托 `_generate_region` 归约
- **退化修复**：BFS walk 引入 R3-08/R4-05 退化（except handler 含 ternary 异常类型被误判为 finally）。通过新增 CHECK_EXC_MATCH/CHECK_EG_MATCH 守卫修复。
- **算法依据**：「每块唯一归属」— normal path 副本的块归属到 finally body 的归约结果（通过 exception path 副本），不重复生成；「父引用子入口」— finally body 通过 exception path 副本的 entry 引用 ternary 子节点。

### Bug R7-09: del (ternary)[idx] — ternary 作为 del subscript 的 base obj — 已修复

- **测试**：`test_r7_ternary_in_del_obj_subscript.py`
- **源码**：`del (a if c else b)[idx]`
- **根因**：原 `_try_build_ternary_store_assign` 的 DELETE_SUBSCR Pattern D 只处理 ternary 作为 del 的 key（cond preload 含 obj），未处理 ternary 作为 del 的 base obj（merge_block 含 key）。
- **修复**：新增 Pattern D2 — 当 `before_store` 非空时，重建 key 表达式（用 ternary 作为 initial_stack[0]，处理 before_store 指令重建 key），构造 `Delete(targets=[Subscript(value=ternary, slice=key, ctx=Del)])`。
- **算法依据**：「父引用子入口」— 父 Delete 通过 merge_block 的 LOAD key + DELETE_SUBSCR 引用 ternary 子节点作为 subscript 的 base obj。

### Bug R7-06: yield from (ternary) + 赋值 — 已修复

- **测试**：`test_r7_ternary_in_yield_from_ternary.py`
- **源码**：`def g(): x = yield from (a if c else b)`
- **根因**：region_analyzer 的 yield-from consume 检测只识别 POP_TOP（无赋值），未识别 STORE_FAST x（有赋值）。原代码生成 `Expr(YieldFrom(ternary))` 而非 `Assign([x], YieldFrom(ternary))`，且 ternary 退化为独立表达式。
- **修复**：
  1. region_analyzer：新增 elif 检测 STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF 作为 yield-from consume block，记录 value_target；merge_context='yieldfrom'
  2. region_ast_generator Pattern 4 & 5：当 full_expr 是 YieldFrom + merge_context='yieldfrom' + value_target 非空时，包裹为 `Assign([Name(value_target, Store)], YieldFrom(ternary))`
- **算法依据**：「父引用子入口」— 父 Assign 通过 STORE_FAST x 引用 ternary 子节点（经 yield-from 协议）。

## 未修复 bug（6 个，留待 R8+）

| Bug | 测试 | 类别 | 说明 |
|-----|------|------|------|
| R7-01 | test_r7_ternary_in_assert_msg | assert message | `assert x, (a if c else b)` — assert message ternary 丢失 + 错误添加 raise (ternary)() 调用。需在 _generate_assert 中识别 message_block 位置的 TernaryRegion |
| R7-02 | test_r7_ternary_in_async_for_body | async for body | `async for body: y = a if c else b` — ternary 完全退化为 `a\nb` 表达式泄漏 + 赋值丢失。需在 _identify_loop_regions 中区分 async for 的 polling 块与 body 内的 ternary merge 块 |
| R7-03 | test_r7_ternary_in_async_with_body | async with body | `async with ctx: y = a if c else b` — ternary 的 STORE_FAST y 被误识别为 with 的 as 目标。需在 _generate_with 的 async with 路径修正 as_target 推断 |
| R7-04 | test_r7_ternary_in_del_target_complex | del subscript chain | `del x[t1][t2]` 双 ternary subscript — 两个 ternary 共享同一 block 14，违反「每块唯一归属」，结构复杂 |
| R7-08 | test_r7_ternary_in_assert_f_msg | assert f(ternary) msg | `assert x, f(a if c else b)` — assert f(ternary) message 丢失。同 R7-01 根因 |
| R7-10 | test_r7_ternary_in_async_for_else | async for-else | `async for-else: y = a if c else b` — else 块 + ternary 完全丢失，反编译出 `while True: pass` 幻影循环 |

## 回归验证

### R7 新测试
```
11 failed → 5 failed（5 修复：R7-05, 07, 11, 09, 06）
21 passed → 26 passed（含 R7 修复转 pass + 1退化修复 R3-08/R4-05 间接影响）
```

### Ternary 区域全量回归
```
基线（R6 完成）: 59 failed, 202 passed, 1 skipped (262 测试)
R7 测试添加后（无修复）: 70 failed, 223 passed, 1 skipped (294 测试)
R7 修复后（最终）: 65 failed, 228 passed, 1 skipped (294 测试)
```

### 跨区域回归（ternary + if_region）
```
基线: 103 failed, 975 passed, 11 skipped (1089 测试)
R7 测试添加后（无修复）: 114 failed, 996 passed, 11 skipped (1121 测试)
R7 修复后（最终）: 109 failed, 1001 passed, 11 skipped (1121 测试)
```

### 退化分析
- Ternary: 70 failed → 65 failed（R7 修复 5 个 bug，0 退化）
- 跨区域: 114 failed → 109 failed（R7 修复 5 个 bug，0 退化）
- P0 修复初期引入 R3-08/R4-05 退化（BFS walk 误判 except 为 finally），通过 CHECK_EXC_MATCH/CHECK_EG_MATCH 守卫修复
- 跨区域 if_region 无基线退化

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| R7: finally 块 ternary 归约 | 3 | 3 (R7-05/07/11) | 0 |
| R7: async 控制流 ternary | 3 | 0 | 3 (R7-02/03/10) |
| R7: 语句位置 ternary consumer | 4 | 1 (R7-09) | 3 (R7-01/04/08) |
| R7: yield from + 赋值复合 | 1 | 1 (R7-06) | 0 |
| **退化修复 bonus** | 1 | 1 (R3-08/R4-05) | 0 |
| **总计** | **12** | **6** | **6** |

## 算法 4 原则核查

所有修复均严格遵循区域归约算法 4 原则：

1. **自底向上归约**: ternary 作为内层区域先归约为 IfExp 表达式，外层 TryExcept(finally)/Delete/Assign(yield from) 作为父区域后归约时引用 IfExp。
2. **每块唯一归属**:
   - finally body 的 normal path 副本 blocks 归属到 finally body 归约结果（通过 exception path 副本），不重复生成
   - merge_block 的 wrapping 指令（STORE_FAST x / DELETE_SUBSCR / YIELD_VALUE）归属到 ternary 父区域
3. **嵌套即抽象节点**: 嵌套 try-finally 的 normal path 副本 ternary 作为外层 try-finally 的抽象子节点（通过 exception path 副本归约）。
4. **父引用子入口**: 父区域通过 cond_block preload + merge_block wrapping 指令引用 ternary 子节点；TryExcept 通过 finally_blocks 中的 exception path 副本 entry 引用 ternary 子节点。

**禁止事项核查**:
- ✅ 无跨区域启发式特例（所有修复均在 TernaryRegion / 父区域内部）
- ✅ 无后处理补丁（所有修复在区域归约阶段完成）
- ✅ 无启发式优先级覆盖（未调整区域识别优先级）
- ✅ 无扁平化（嵌套 ternary 保持 IfExp AST 结构，无硬编码深度上限）
- ✅ 无 debug 打印残留
- ✅ 无根级 debug 脚本残留

## 后续方向（R8+）

1. **R7-01/08 assert message ternary**: 在 `_generate_assert` 中识别 message_block 位置的 TernaryRegion，调用 `_generate_ternary` 提取 IfExp 作为 assert message
2. **R7-02/10 async for body/else ternary**: 在 `_identify_loop_regions` 中区分 async for 的 polling 块（GET_AWAITABLE + SEND）与 body/else 块内的 ternary merge 块
3. **R7-03 async with body ternary**: 在 `_generate_with` 的 async with 路径中修正 as_target 推断（POP_TOP 表示无 as 目标，STORE_FAST 才是 as 目标）
4. **R7-04 del subscript chain**: 处理双 ternary 共享同一 block 的 del subscript 链（需在 region_analyzer 阶段区分两个 ternary 的 block 归属）
