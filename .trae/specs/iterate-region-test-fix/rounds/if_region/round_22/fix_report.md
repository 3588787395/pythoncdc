# IF Region Round 22 — Fix Report

## 概述

Round 22 测试工程师识别 10 个根因簇（C1-C10，34 测试）。本轮完成 P0 部分：
- **C2（5 测试）完全修复**：walrus+三元 if 条件 IfRegion 被丢弃
- **C3（1/3 测试）修复**：adv18_assert_in_if_body 通过；adv19/adv20_assert_chained_cmp 结构已正确（if-elif-else 不再坍塌为三元），但指令数仍有差异（深层 assert chained cmp 重建问题，留 R23+）
- C4（3 测试）代码已加 LoopRegion.blocks 守卫，但测试仍失败（深层归约问题，留 R23+）
- C7（7 测试）未修复，留 R23+

| 指标 | 基线 | 修复后 | 变化 |
|------|------|--------|------|
| IF region failed | 34 | 28 | -6 |
| IF region passed | 783 | 789 | +6 |
| IF region skipped | 10 | 10 | 0 |
| Ternary region failed | 0 | 0 | 0 |
| Ternary region passed | 506 | 506 | 0 |

---

## C2 — walrus+三元 if 条件 IfRegion 被丢弃（P0，5 测试，已修复）

### 根因
当 if 条件为 `walrus 绑定三元后再做属性/下标/方法/二元运算/比较`（如 `if (x := a if c else b).field > 0: pass`）时：
- R21-C1 的 `_ternary_if_cond_redirect` 正确把 IfRegion.condition_block 重定向到三元 merge_block
- 但 IfRegion.entry 与 TernaryRegion.entry 共享同一块
- `_generate_if`（region_ast_generator.py:6629-6641）的 `entry in generated_blocks` 检查在 TernaryRegion 先生成后把整个 IfRegion 丢弃
- 输出坍塌为 `pass`

### 修复
`region_ast_generator.py` `_generate_if`：在 `boolop_child is None` 且 `entry in generated_blocks` 时，原直接 `return []`。现增加检测：若存在 TernaryRegion 满足 `merge_block == IfRegion.condition_block` 且 `entry == IfRegion.entry`，则不返回 []，继续生成 IfRegion（通过 condition_block 引用 TernaryRegion 子节点）。

### 验证
- test_adv14_walrus_ternary_attr ✓
- test_adv14_walrus_ternary_binary_op ✓
- test_adv14_walrus_ternary_method ✓
- test_adv14_walrus_ternary_subscr ✓
- test_adv15_walrus_ternary_cond ✓

### 违反原则
- 原则 2（每块唯一归属）：IfRegion.entry 与 TernaryRegion.entry 共享，生成顺序导致 IfRegion 被丢弃
- 原则 4（父引用子入口）：IfRegion 应通过 condition_block（merge_block）引用 TernaryRegion 子节点

---

## C3 — AssertRegion 抢占 if-elif-else 头块（P0，1/3 测试修复）

### 根因
当 if-elif-else 分支体含 `assert cond, msg` 时：
- `_identify_assert_regions` 把 if 头块的 `POP_JUMP_IF_FALSE` 误识别为 AssertRegion.entry
- if-elif-else 头块被 AssertRegion 抢占
- 整 if 坍塌为链式三元 `(x < 100 if x > 0 else x < 0)`

### 修复（迭代两次）
**第一次**：在 `_can_be_ternary_header` 中加入 `isinstance(succ_region, AssertRegion)` 检查。但太宽——`assert (a if c else b), 'msg'` 中 ternary 的两个 value 块各自含 POP_JUMP_IF_TRUE（assert 检查嵌入 value），二者均被识别为独立 AssertRegion.entry，导致合法 ternary 被拒绝（ternary region 7 个测试退化）。

**第二次（最终）**：改为【恰好一个】succ 是 AssertRegion.entry 才拒绝 ternary。判据：
- if-then-assert：then 是 assert（AssertRegion.entry），else 是下一条语句（非 AssertRegion.entry）→ 恰好 1 个 → 拒绝 ternary ✓
- assert 含三元：ternary 两 value 均含 assert 检查 → 2 个 AssertRegion.entry → 允许 ternary ✓

### 验证
- test_adv18_assert_in_if_body ✓
- test_adv19_assert_chained_cmp_in_if_body ✗（结构已正确，指令数差异 50 vs 37，深层 chained cmp 重建问题）
- test_adv20_assert_chained_cmp_in_branches ✗（结构已正确，指令数差异 60 vs 39，同上）

### 违反原则
- 原则 2（每块唯一归属）：if-elif-else 头块被 AssertRegion 错误抢占
- 原则 4（父引用子入口）：AssertRegion 应作为 IfRegion.then_blocks 内的子节点

---

## C4 — if-elif-else 三分支均以 for 开头时头块被 TernaryRegion 抢占（P0，未完全修复）

### 修复尝试
在 `_can_be_ternary_header` 中扩展 LoopRegion 检查：原仅 `succ == condition_block or succ == entry`，新增 `elif succ in succ_region.blocks`（覆盖 for 循环的 GET_ITER setup 块）。

### 验证
3 测试仍失败（指令数从 44 vs 24 变为 44 vs 48，结构有变化但仍不正确）。深层归约问题：for 循环 setup 块的归属判定需要更精细的 region 边界处理。留 R23+。

---

## 剩余未修复项（留 R23+）

| 簇 | 测试数 | 优先级 | 状态 |
|----|--------|--------|------|
| C1 多三元/嵌套三元 boolop 链 | 3 | P1 | 未修 |
| C3 残留（adv19/adv20 assert chained cmp） | 2 | P0 | 结构正确，指令数差异 |
| C4 for-分支 if 头抢占 | 3 | P0 | 部分修复 |
| C5 elif 链复杂条件断裂 | 3 | P1 | 未修 |
| C6 三元在容器内归约失败 | 3 | P1 | 未修 |
| C7 if body 内嵌套 region 不透明子节点 | 7 | P0 | 未修 |
| C8 嵌套 with 平铺 | 2 | P2 | 未修 |
| C9 lambda IIFE 退化 | 1 | P2 | 未修 |
| C10 复杂表达式多块拆解 | 4 | P2 | 未修 |
| **合计** | **28** | | |

---

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `core/cfg/region_analyzer.py` | C3: `_can_be_ternary_header` 加入【恰好一个 succ 是 AssertRegion.entry】判据；C4: LoopRegion 检查扩展 `succ in succ_region.blocks` |
| `core/cfg/region_ast_generator.py` | C2: `_generate_if` entry-generated 检查增加 TernaryRegion.redirect 检测，不丢弃 IfRegion |

## 遵循的算法原则

- **原则 1（自底向上归约）**：AssertRegion 在 Phase 1 识别，TernaryRegion 候选检查时跳过 if-then-assert 头
- **原则 2（每块唯一归属）**：if-elif-else 头块不被 TernaryRegion 抢占（C3/C4）；IfRegion.entry 与 TernaryRegion.entry 共享时通过 condition_block 引用而非丢弃（C2）
- **原则 3（嵌套即抽象节点）**：AssertRegion 作为 IfRegion.then_blocks 子节点；TernaryRegion 作为 IfRegion.test 子节点
- **原则 4（父引用子入口）**：IfRegion 通过 condition_block（=TernaryRegion.merge_block）引用 ternary 子节点（C2）
