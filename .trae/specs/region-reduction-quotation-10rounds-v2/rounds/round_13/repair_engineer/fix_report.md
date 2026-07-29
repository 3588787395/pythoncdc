# R13 修复工程师报告

## 1. 修复目标

- **目标函数**: `get_date_and_count`（len_diff -27，while 循环 if/elif 链丢失）
- **R12 基线**: 144/150 (96.00%)
- **修复方向**: LoopRegion 反向链走吸收外层 if/elif/else 条件块 + while 无 break 时 else_blocks 误识别

## 2. 根因分析

### 2.1 缺陷定位

**文件**: `/workspace/core/cfg/region_analyzer.py`
**方法**: `_identify_loop_regions`（反向链走，~line 3079-3121）+ `_find_loop_else`（else_blocks 识别，~line 3939-3957）

**缺陷 1：反向链走吸收外层 if/elif/else 条件块**

Block 1202（elif 条件 `count == 1 and count > 0`）的 `POP_JUMP_FORWARD_IF_FALSE` 目标是 block 1222（while 循环 condition_block）。反向链走判据 `p_target == _cb` 成立，吸收 block 1202。

但 block 1202 的 fall-through 是 block 1214（elif body），不是 block 1222。真正的条件链前驱（如 `while (a or b) and c:` 的较早操作数）其 fall-through 流向 _cb（链中下一操作数）。外层 if/elif/else 条件块其 fall-through 流向自己的 then 体（独立块，非 _cb）。

**违反原则**: 原则 2（每块唯一归属）— block 1202 同时属于 LoopRegion@1222 和 IfRegion@692；原则 3（嵌套即抽象节点）— IfRegion@692 的 parent 被设为 LoopRegion@1222。

**缺陷 2：while 无 break 时 else_blocks 误识别**

`_find_loop_else` 在 while 循环无 break 时仍识别 else_blocks。在 Python 3.11+（无 SETUP_LOOP/POP_BLOCK），`while: ... else: ...` 无 break 与 `while: ... ` 后接普通代码字节码不可区分。Block 1314（post-loop if/else）被误识别为 LoopRegion@1222 的 else_blocks。

**违反原则**: 原则 1（自底向上归约）— else_blocks 识别基于后必经节点分析，但在无 break 时无法区分 else 与 fall-through；原则 2（每块唯一归属）— block 1314 同时属于 LoopRegion@1222（else）和 IfRegion@1314（entry）。

### 2.2 修复方案

**方案 A（反向链走 fall-through 校验）**：
在反向链走的吸收判据中，将 `p_target == _cb` 改为 `p_target == _cb AND p_fall_through is _cb`。p 的 fall-through 是 p 的非跳转后继（FORWARD_CONDITIONAL_JUMP 块恰好两个后继：跳转目标 p_target 与 fall-through）。真正条件链前驱 fall-through 是 _cb；外层 if/elif/else 条件块 fall-through 是自己的 then 体。

**方案 B（无 break 时不识别 else_blocks）**：
在 `_find_loop_else` 中，当 while 循环无 break 目标时，设 `else_blocks = None`。遵循自底向上归约：每个区域由自身结构边界识别，而非对后续代码的启发式判断。

## 3. 修复尝试与退化

### 3.1 尝试 A+B（同时修复两个缺陷）

**修改**：
1. `region_analyzer.py` line ~3097：增加 `_p_fall_through` 和 `_is_true_cond_chain_pred` 校验
2. `region_analyzer.py` line ~3939：无 break 时 `else_blocks = None`
3. 更新 `_identify_loop_regions` Step 9 docstring + `_find_loop_else` docstring

**结果**：
- LoopRegion@1222 正确只含 [1222, 1244, 1262, 1288, 1302] ✓
- IfRegion@692 parent 正确为 678 ✓
- **退化**：IfRegion@1314 成为 IfRegion@692 的兄弟（parent=678），AST 生成合并条件
- **len_diff**: -27 → -63（更差）
- **退化根因**：IfRegion@692 的 else-branch 块收集未包含 while 循环后的 block 1314

### 3.2 尝试 A only（仅修复反向链走）

**修改**：仅方案 A，不修改 else_blocks

**结果**：
- **len_diff**: -63（同 A+B，退化根因相同）

### 3.3 回退

所有修改已回退。代码恢复到 R12 基线状态（144/150，get_date_and_count -27）。

## 4. 完整修复需要的额外工作

完整修复需要解决 **IfRegion else-branch 块收集穿透嵌套 LoopRegion** 的问题：

1. **IfRegion@692 的 else-branch 收集**：`_collect_branch_blocks(1222, 3046, else_stop)` 应 BFS 从 block 1222 到 merge block 3046，收集包括 block 1314 在内的所有块。当前实现可能因 `boundary_stop` 或 `block_to_region` 过滤阻止了 BFS 到达 block 1314。

2. **IfRegion@1314 的 parent 赋值**：在 `_build_region_hierarchy` 中，IfRegion@1314 的 parent 应为 IfRegion@692（在 else-branch 内），而非 IfRegion@678（兄弟）。这需要 IfRegion@692 的 blocks 包含 block 1314。

3. **AST 生成**：`_generate_if` / `_if_generate_elif_chain` 需要正确处理 else-branch 内嵌套 LoopRegion + post-loop IfRegion 的场景。

这些修改涉及 IfRegion 识别、区域层级构建、AST 生成三个阶段，需要协同修改，风险较高。deferred 到后续轮次。

## 5. 算法 4 原则符合度

| 原则 | 状态 | 说明 |
|------|------|------|
| 1. 自底向上归约 | ✓ | 修复方案基于区域自身结构识别，不跨层引用 |
| 2. 每块唯一归属 | ✓ | 修复方案消除 block 1202/1314 的双重归属 |
| 3. 嵌套即抽象节点 | ✓ | 修复方案恢复 IfRegion@692 作为 LoopRegion@1222 的父节点 |
| 4. 入口引用语义 | ✓ | 未修改入口引用逻辑 |

## 6. 反模式自检

| 检查项 | 结果 |
|--------|------|
| `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法 | 0 新增 |
| 硬编码深度上限 | 0 新增 |
| 跨区域跨层次启发式规则 | 0 新增 |
| 后处理修正 | 0 新增 |

## 7. 回归结果

| 检查项 | 结果 |
|--------|------|
| quotation.pyc 一致函数数 | 144/150 (≥144 ✓) |
| compile_ok | True |
| 既有区域测试矩阵 | 9 fail / 318 pass / 11 skip（== 基线，0 退化 ✓） |
| IMPORT_OK | True |
| 10 个 repro py_compile | 全部通过 ✓ |

## 8. 残留不一致数

6 个不一致函数（== R12 基线，无退化）：
- `get_date_and_count`: -27（R13 分析完成，修复因退化回退，deferred）
- `get_str_data`: -48（R12 deferred）
- `one_prod_to_dataframe` / `build_future_fill_time` / `change_his_to_backward`: 跳转目标归一化
- `<module>`: co_filename 元数据
