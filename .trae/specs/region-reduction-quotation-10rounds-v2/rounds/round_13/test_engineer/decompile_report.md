# R13 测试工程师反编译报告

## 1. 基线统计

| 指标 | 值 |
|------|-----|
| 总函数数 | 150 |
| 一致函数数 | 144 |
| 不一致函数数 | 6 |
| 成功率 | 96.00% |
| compile_ok | True |
| R12 基线 | 144/150 (96.00%) |
| 退化 | 无（144 == 144） |

## 2. 不一致函数清单

| 函数名 | 状态 | 详情 |
|--------|------|------|
| `<module>` | instr_diff | @idx394（co_filename 元数据差异） |
| `one_prod_to_dataframe` | instr_diff | @idx131（跳转目标归一化） |
| `build_future_fill_time` | instr_diff | @idx226（跳转目标 + listcomp） |
| `get_str_data` | len_diff | 317→269 (-48)，R12 遗留 |
| `change_his_to_backward` | instr_diff | @idx296（跳转目标归一化） |
| **`get_date_and_count`** | **len_diff** | **714→687 (-27)，R13 重点** |

## 3. get_date_and_count 差异分析（R13 重点）

### 3.1 差异概要

- **orig_len**: 714 条指令
- **new_len**: 687 条指令
- **len_diff**: -27（反编译产物少 27 条指令）
- **first_diff_idx**: 140（JUMP_FORWARD 目标偏移不同）

### 3.2 差异根因

**首处分歧**（idx 140）：
- O: `676 JUMP_FORWARD ->[710]`（原始跳到第 710 条指令，if/elif 链完整）
- N: `676 JUMP_FORWARD ->[683]`（反编译跳到第 683 条指令，if/elif 链丢失）

这是 `if candle_period == 7:` 块末尾的 JUMP_FORWARD。原始跳过后续的 `if/elif/elif...` 链到达函数尾部，反编译产物跳到较近的位置，说明 if/elif 链语句丢失。

**指令丢失位置**（idx 687-713，27 条指令）：
原始字节码末尾有 27 条指令被完全丢失，对应 `if month in (10, 11, 12): ... else: ...` 的 else 分支（`start_date = str(year) + '0' + str(month) + '01'`）。这是 while 循环后的 if/else 链的 else 分支。

### 3.3 区域结构分析

通过 `_diag_regions.py` 诊断发现：

```
LoopRegion@1222 blocks=[692, 1202, 1222, 1244, 1262, 1288, 1302, 1314] parent=678
IfRegion@692    blocks=[692, 846, 974, 992, 1018, 1032, 1044, 1052, 1124, 1202, 1244, 1262, 1288] parent=1222
```

**核心问题**：
1. **LoopRegion@1222 误吞 IfRegion@692 的 entry 块 692**：违反原则 2（每块唯一归属）
2. **LoopRegion@1222 误吞 BoolOpRegion@1202 的 entry 块 1202**：违反原则 2
3. **LoopRegion@1222 误吞 IfRegion@1314 的 entry 块 1314**（作为 else_blocks）：违反原则 2
4. **IfRegion@692 的 parent 被设为 1222**（if/elif 链在循环内部），导致 if/elif 链在 AST 生成时丢失

**根因链**：
- Block 1202（elif 条件 `count == 1 and count > 0`）的 `POP_JUMP_FORWARD_IF_FALSE` 跳到 block 1222（while 循环 condition_block）
- LoopRegion@1222 的反向链行走查到 1202 的 `p_target == _cb`（1202→1222），吸收 1202
- 但 1202 的 fall-through 是 1214（elif body），不是 1222（condition_block）
- 1202 是外层 if/elif/else 的条件块，不是 while 循环的条件链前驱
- 类似地，block 692 也被吸收（692→1202→1222 链式吸收）
- Block 1314 被 `_find_loop_else` 识别为 LoopRegion@1222 的 else_blocks（while 无 break 时 else 与 fall-through 不可区分）

### 3.4 修复尝试与退化

**尝试 1**：反向链走增加 fall-through 校验
- 判据：`p_target == _cb AND p_fall_through is _cb`（真正条件链前驱）
- 结果：LoopRegion@1222 正确只含 [1222, 1244, 1262, 1288, 1302]
- **退化**：IfRegion@1314（post-loop if/else）成为 IfRegion@692 的兄弟，AST 生成合并条件
- **len_diff**: -27 → -63（更差）

**尝试 2**：同时修复 else_blocks（无 break 时不识别 else_blocks）
- 结果：IfRegion@1314 不再被 LoopRegion 吞入，但仍为兄弟
- **退化**：同 -63（根因是 IfRegion@692 未包含 post-loop block 1314）

**退化根因**：IfRegion@692 的 else-branch 收集（`_collect_branch_blocks`）未包含 while 循环后的 block 1314。完整修复需要增强 IfRegion 的 else-branch 块收集逻辑，使其穿透嵌套 LoopRegion 收集 post-loop 代码。

## 4. 最小复现实例

| # | 文件 | 区域类型 | 违反原则 | 对应函数 |
|---|------|---------|---------|---------|
| 1 | repro_01_while_in_if_elif_else.py | Loop+IfRegion | 2,3 | get_date_and_count |
| 2 | repro_02_while_in_else_branch.py | Loop+IfRegion | 2 | get_date_and_count |
| 3 | repro_03_post_loop_if_else.py | Loop+IfRegion | 3 | get_date_and_count |
| 4 | repro_04_elif_jumps_to_while.py | IfRegion+Loop | 2 | get_date_and_count |
| 5 | repro_05_while_no_break_else.py | Loop | 1 | get_date_and_count |
| 6 | repro_06_nested_while_in_branches.py | If+2xLoop | 2,3 | get_date_and_count |
| 7 | repro_07_while_with_break.py | Loop+IfRegion | N/A (control) | control |
| 8 | repro_08_compound_while_condition.py | Loop | N/A (control) | control |
| 9 | repro_09_quarter_while_pattern.py | If+Loop+If | 2,3 | get_date_and_count |
| 10 | repro_10_while_after_if_elif.py | If+Loop | 3 | get_date_and_count |

全部 10 个实例 `py_compile` 通过。

## 5. 回归验证

| 检查项 | 结果 |
|--------|------|
| quotation.pyc 一致函数数 | 144/150 (≥144 ✓) |
| compile_ok | True |
| 既有区域测试矩阵 | 9 fail / 318 pass / 11 skip（== 基线，0 退化 ✓） |
| IMPORT_OK | True |
| 反模式新增 | 0 |
| 硬编码深度上限新增 | 0 |
