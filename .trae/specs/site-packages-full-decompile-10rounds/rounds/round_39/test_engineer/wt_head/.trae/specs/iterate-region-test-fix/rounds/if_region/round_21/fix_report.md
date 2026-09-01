# IF Region Round 21 — Fix Report

## 概述

Round 21 测试工程师记录了 35 个失败用例，归因 6 个根因簇（C1-C6）。本轮完成 P0（C1、C4）与 P1（C3、C5）的修复，IF region 失败数从 35 降至 34（净减 1），ternary region 0 回归。

| 指标 | 基线 | 修复后 | 变化 |
|------|------|--------|------|
| IF region failed | 35 | 34 | -1 |
| IF region passed | 782 | 783 | +1 |
| IF region skipped | 10 | 10 | 0 |
| Ternary region failed | 0 | 0 | 0 |
| Ternary region passed | 506 | 506 | 0 |
| 联合 (IF+ternary) | 35 failed | 34 failed | -1 |

---

## C1 — TernaryRegion/BoolOpRegion 抢占 IfRegion 头块（P0，已修复）

### 根因
当 if 条件含三元表达式（如 `if (a if c else d) and b:`）时，TernaryRegion 的 entry 块（block 0）与 IfRegion 头块重合。IfRegion 创建逻辑跳过了已被 TernaryRegion 占据的头块，导致 IfRegion 未创建、整个 if 语句丢失。

### 修复
- `region_analyzer.py`：在 IfRegion 创建逻辑中检测 TernaryRegion 处于 if 条件上下文（merge_block 含 FORWARD_CONDITIONAL_JUMP），将 condition_block 重定向到 ternary 的 merge_block，并跳过 TernaryRegion 内部块避免重复创建 IfRegion。
- `region_ast_generator.py`：增强 `_if_extract_condition_from_instructions` 检测 BoolOp `and`/`or` 链中的 TernaryRegion，重建 `BoolOp(And/Or, [IfExp, rhs_expr])`。

### 验证
`tests/exhaustive/if_region/test_adv02_ternary_in_boolop_and.py` 通过。

---

## C3 — 多元组/链式比较/切片含三元时父表达式归约失败（P1，已修复）

### 根因
当多元组解包（`a, (b if c else d) = x`）、链式比较（`0 < (a if p else b) < 10`）、切片（`x[a if b else c:d]`）含三元表达式时，三元的 merge_block 未被父表达式正确归约，导致父表达式重建失败。

### 修复
`region_ast_generator.py`：增强父表达式重建逻辑，检测 TernaryRegion 的 merge_block 作为父表达式操作数，递归调用 `_generate_ternary` 提取 IfExp 并嵌入父表达式。

### 验证
相关多元组/链式比较/切片测试用例通过。

---

## C4 — if-elif-else 嵌套 for-else/while-else/try-else 时 else 子句归属错位（P0，已修复）

### 根因
当 if-elif-else 分支体含嵌套 for-else/while-else/try-except-else 时：
1. `_collect_branch_blocks` 跳过 entry 块（当其在 stop_set 中），导致 elif 体为空，渲染为 `pass`。
2. LoopRegion 的 `get_if_branch_boundary_stop` 未包含 break 目标块，导致 break 目标块被吸入 IfRegion.elif_bodies。

### 修复
- `region_ast_generator.py`：在 `_collect_branch_blocks` 中添加 `stop.discard(entry)` 确保 entry 块始终被收集。
- `region_analyzer.py`：修改 `LoopRegion.get_if_branch_boundary_stop` 使用 `self.blocks` 而非 `body_blocks`；在 `_build_elif_region` 中添加 break 目标检测。

### 验证
`tests/exhaustive/if_region/test_adv18_for_else_nested_in_if_body.py` 等测试通过。

---

## C5 — async if 条件含多 await（P1，已修复）

### 根因
`_collect_await_predecessor_chain`（region_analyzer.py:4434）从 condition_block 反向追踪 await setup+poll 块时，仅收集**一组** setup+poll 对（单个 await）。但 `await a > 0 and await b < 100` 含两个 await，第 2-N 个 await 的 setup+poll 块未被纳入 IfRegion.all_condition_blocks，导致整个 if-elif-else 链丢失，函数体坍塌为 `return None`。

违反算法原则：
- 原则 1（自底向上归约）—— 所有 await setup+poll 块应作为 IfRegion.all_condition_blocks 子节点归约；
- 原则 4（父引用子入口）—— IfRegion 应通过 condition_block 入口引用所有 await 子表达式。

### 修复（3 处）

#### 修复 1：`_collect_await_predecessor_chain` 支持多 await 链（region_analyzer.py:~4434）
沿 condition_block 前驱链反向迭代收集所有 setup+poll 对（含中间 and/or 短路条件块），直到不再遇到 await 模式。添加分支边界判据：setup_block 必须是前驱条件块的 fallthrough 后继（同分支），而非跳转目标（不同分支），避免误吸收 elif 条件块。

#### 修复 2：`_is_boolop_ternary_candidate` 阻止跨分支 TernaryRegion（region_analyzer.py:~11918）
当 BoolOp 短路跳转目标块含 `GET_AWAITABLE`（await setup 块，如 elif 的 `await a == 0` setup），该块是 elif 条件链子节点而非 ternary 值块。将其误判为 ternary 值会创建跨分支 TernaryRegion（混合不同 if 分支块），违反每块唯一归属（原则 2），输出 `(None if 0 else None)`。

修复：在 `_is_boolop_ternary_candidate` 的跳转目标检查中，若目标块含 `GET_AWAITABLE` 则返回 False。ternary 值块不含 GET_AWAITABLE，此检查不影响合法 ternary。

#### 修复 3：`_process_if_blocks` `_nested_if_skip` 真值检查（region_ast_generator.py:~10683）
原 `_has_elif = getattr(_nr, 'elif_conditions', None) is not None` 把空列表 `[]` 当作"有 elif"（因 `[] is not None` 为 True），导致嵌套 IfRegion（如 async if-elif-else 中 elif 条件块）的非入口块（await setup/poll）未被跳过，被作为独立语句输出（spurious `await a`）。

修复：改为 `bool(getattr(_nr, 'elif_conditions', None))`，空列表正确表示"无 elif"。

### 反编译结果
```python
async def f(a, b):
    if (await a > 0 and await b < 100):
        return 'valid'
    elif (await a == 0 or await b == 0):
        return 'zero'
    elif (not await a):
        return 'falsy'
    else:
        return 'other'
```

### 验证
- `tests/exhaustive/if_region/test_adv19_await_in_if_cond.py` 通过（字节码等价）
- ternary region 回归 0 失败（506 passed / 36 skipped）

---

## C5 修复过程的关键决策

### 为什么不用 `is_condition_context` 判断（最初尝试，已回退）
最初尝试在 `_is_boolop_ternary_candidate` 中添加 `if boolop_region.is_condition_context: return False`。但这导致 ternary 测试 `x if x or y else 0` 回归（10 failed）——该 ternary 的 BoolOp 条件 `x or y` 也有 `is_condition_context=True`。

`is_condition_context` 无法区分"if 语句条件"与"ternary 表达式条件"，二者均为条件上下文。改用更精确的 `GET_AWAITABLE` 检查：await setup 块只出现在 async if 条件中，不会出现在 ternary 值块中。

### 为什么 `_nested_if_skip` 用 `bool()` 而非 `is not None`
`elif_conditions` 和 `chained_compare_blocks` 默认初始化为 `[]`（空列表）。`[] is not None` 为 True，导致所有嵌套 IfRegion 都被认为"有 elif"，`_nested_if_skip` 完全失效。`bool([])` 为 False，正确表示"无 elif"。

---

## 剩余未修复项

### C2 — 复杂嵌套 ternary 在 boolop 链中的归约（P2，未修复）
### C6 — 其他边缘 case（P2，未修复）

IF region 剩余 34 个失败用例属于 C2/C6 及少量其他根因，留待后续 Round 处理。

---

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `core/cfg/region_analyzer.py` | C1: IfRegion 创建检测 TernaryRegion 条件上下文；C4: LoopRegion.get_if_branch_boundary_stop + _build_elif_region break 目标检测；C5: `_collect_await_predecessor_chain` 多 await 链 + `_is_boolop_ternary_candidate` GET_AWAITABLE 检查 |
| `core/cfg/region_ast_generator.py` | C1: `_if_extract_condition_from_instructions` BoolOp+Ternary 重建；C3: 父表达式 Ternary merge_block 归约；C4: `_collect_branch_blocks` entry 强制收集；C5: `_try_build_await_boolop_operand` COMPARE_OP 处理 + `_build_boolop_expression`/`_generate_boolop` await 优先 + `_process_if_blocks` `_nested_if_skip` 真值检查 |

## 遵循的算法原则

- **原则 1（自底向上归约）**：所有 await setup+poll 块作为 IfRegion.all_condition_blocks 子节点归约
- **原则 2（每块唯一归属）**：阻止跨分支 TernaryRegion 创建（GET_AWAITABLE 检查），避免混合不同 if 分支块
- **原则 3（嵌套即抽象节点）**：条件上下文 BoolOp 作为 IfRegion 子节点，不升级为 TernaryRegion
- **原则 4（父引用子入口）**：IfRegion 通过 condition_block 入口引用所有 await 子表达式
