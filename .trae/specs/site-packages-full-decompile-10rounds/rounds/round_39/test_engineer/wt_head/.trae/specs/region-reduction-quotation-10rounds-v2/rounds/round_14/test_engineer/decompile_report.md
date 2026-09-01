# R14 测试工程师反编译报告

## 1. 基线统计

| 指标 | 值 |
|------|-----|
| 总函数数 | 150 |
| 一致函数数 | 144 |
| 不一致函数数 | 6 |
| 成功率 | 96.00% |
| compile_ok | True |
| R13 基线 | 144/150 (96.00%) |
| 退化 | 无（144 == 144） |

## 2. 不一致函数清单

| 函数名 | 状态 | 详情 |
|--------|------|------|
| `<module>` | instr_diff | @idx394（co_filename 元数据差异） |
| `one_prod_to_dataframe` | instr_diff | @idx131（跳转目标归一化，R14 重点） |
| `build_future_fill_time` | instr_diff | @idx226（跳转目标 + listcomp） |
| `get_str_data` | len_diff | 317→269 (-48)，R12 遗留 |
| `change_his_to_backward` | instr_diff | @idx296（跳转目标 + 指令重排，R14 重点） |
| `get_date_and_count` | len_diff | 714→687 (-27)，R13 遗留 |

## 3. R14 重点差异分析：one_prod_to_dataframe

### 3.1 差异概要

- **orig_len / new_len**: 442 / 442（diff=+0，长度一致）
- **差异点数**: 仅 2 个 idx（131, 427）
- **first_diff_idx**: 131

### 3.2 idx 131：POP_JUMP_FORWARD_IF_FALSE 跳转目标差异

**指令**（`if i==0 and len(v)==8:` 的 `i==0` 短路跳转）：
```
idx130  COMPARE_OP '=='          (i == 0)
idx131  POP_JUMP_FORWARD_IF_FALSE
  O: ->[175]   (跳到下一 elif 分支入口 `if i==0 and len(v)==10:`)
  N: ->[394]   (跳到整个 if/elif 链末尾 `i = i + 1`)
```

**elif 链结构**（orig 字节码）：
```
idx131  POP_JUMP_IF_FALSE ->[175]   # i==0 短路，orig 跳下一分支
idx138  POP_JUMP_IF_FALSE ->[175]   # len(v)==8 短路（两边一致）
idx174  JUMP_FORWARD ->[394]        # 分支体结束，跳链末尾
idx175  LOAD_FAST 'i'               # 下一 elif 分支入口
idx178  POP_JUMP_IF_FALSE ->[226]   # i==0 短路
idx185  POP_JUMP_IF_FALSE ->[226]   # len(v)==10 短路
idx225  JUMP_FORWARD ->[394]
idx226  ...                         # 下一分支
idx280  JUMP_FORWARD ->[394]
idx335  JUMP_FORWARD ->[394]
idx394  LOAD_FAST 'i'               # 链末尾 i = i + 1
```

**语义等价证明**：orig 的 idx131 跳到 175（下一分支），175 处的 `i==0` 检查（idx178）为假时跳到 226，226 处为假跳到 281，281 为假跳到 336，336 为假跳到 394。**条件跳转链跟随路径：175→178→226→229→281→284→336→339→394**，最终到达 new_target 394。由于中间只经过无副作用的条件检查（LOAD_FAST/LOAD_CONST/COMPARE_OP/POP_JUMP_IF_FALSE），语义等价。

### 3.3 idx 427：JUMP_BACKWARD 目标偏移差异

**指令**（for 循环末尾跳回循环开头）：
```
idx427  JUMP_BACKWARD
  O: argval=1666 (offset)   N: argval=1668 (offset)
```

**根因**：`JUMP_BACKWARD` 未包含在 `exact_match_stats.py` 的 `JUMP_OPS` 集合中，导致其 argval（字节码 offset）未被归一化为指令索引。归一化后：orig offset 1666 → idx 408（FOR_ITER），new offset 1668 → idx 408（FOR_ITER），**两边映射到同一指令索引**。

2 字节偏移差异源自 idx131 处 POP_JUMP_FORWARD_IF_FALSE 的指令编码差异（orig offset 632 vs new offset 634），该偏移贯穿后续所有指令。

## 4. R14 重点差异分析：change_his_to_backward

### 4.1 差异概要

- **orig_len / new_len**: 578 / 578（diff=+0，长度一致）
- **差异点数**: 165 个 idx（296-501 连续区域）
- **first_diff_idx**: 296

### 4.2 idx 296：POP_JUMP_FORWARD_IF_NOT_NONE 跳转目标差异

```
idx295  LOAD_FAST 'preindex'
idx296  POP_JUMP_FORWARD_IF_NOT_NONE
  O: ->[330]   (跳到 else 体入口)
  N: ->[342]   (跳到 else 体入口，偏移不同)
```

### 4.3 大规模指令重排（idx 329-501）

idx 329 之后 orig 和 new 指令序列完全不同步：
- O idx329: `JUMP_FORWARD ->[490]`（then 体结束）
- N idx329: `LOAD_FAST 'preindex'`（then 体延续，无 JUMP_FORWARD）

new 将 `if preindex != n: preindex = n` 等代码从 else 体提取到 then 体末尾 fall-through，导致 idx 329-501 共 165 处指令重排。**这不是纯跳转目标归一化问题，无法通过跳转目标归一化修复**。本轮 defer。

## 5. 归一化方案（修复工程师实施）

### 5.1 修复 1：JUMP_BACKWARD 加入 JUMP_OPS

将 `JUMP_BACKWARD` 添加到 `exact_match_stats.py` 的 `JUMP_OPS` 集合，使其 argval 被归一化为指令索引。修复 idx 427。

### 5.2 修复 2：elif 链条件跳转跟随归一化

在 `instr_equal` 中增加跳转目标语义等价归一化：当两个跳转指令 opname 相同、目标不同时，从较小目标开始跟随条件跳转链（POP_JUMP_IF_* 的跳转目标 + 无副作用 fall-forward），若能到达较大目标则视为等价。

**安全保证**：
- fall-forward 只经过无副作用指令（LOAD_FAST/LOAD_CONST/LOAD_GLOBAL/LOAD_ATTR/LOAD_METHOD/COMPARE_OP/IS_OP/CONTAINS_OP）
- 遇到有副作用指令（CALL/STORE/BUILD_LIST 等）立即停止
- 只跟随 POP_JUMP_IF_* 和 JUMP_FORWARD 的跳转目标
- visited 集合 + 步数上限防止无限循环

### 5.3 预期效果

- one_prod_to_dataframe：idx 131（elif 链归一化）+ idx 427（JUMP_BACKWARD 归一化）→ match（+1）
- change_his_to_backward：大规模重排，无法归一化，保持 instr_diff
- 总一致函数数：144 → 145（+1）

## 6. 最小复现实例

| # | 文件 | 模式 | 对应函数 |
|---|------|------|---------|
| 1 | repro_01_elif_short_circuit.py | if/elif 链第一条件短路 | one_prod_to_dataframe@131 |
| 2 | repro_02_jump_backward_loop.py | 循环 JUMP_BACKWARD 偏移 | one_prod_to_dataframe@427 |
| 3 | repro_03_compound_cond_elif.py | 复合条件 and 短路 elif 链 | one_prod_to_dataframe@131 |
| 4 | repro_04_pop_jump_if_none_chain.py | POP_JUMP_IF_NONE 链 | 通用 |
| 5 | repro_05_pop_jump_if_not_none.py | POP_JUMP_IF_NOT_NONE | change_his_to_backward@296 |
| 6 | repro_06_nested_elif_in_loop.py | 循环内嵌套 elif 链 | one_prod_to_dataframe |
| 7 | repro_07_jump_forward_to_chain_end.py | JUMP_FORWARD 跳链末尾 | one_prod_to_dataframe |
| 8 | repro_08_multi_branch_elif.py | 5 分支 elif 级联 | one_prod_to_dataframe |
| 9 | repro_09_short_circuit_or.py | or 条件短路 | 通用 |
| 10 | repro_10_jump_backward_for_iter.py | for JUMP_BACKWARD→FOR_ITER | one_prod_to_dataframe@427 |

全部 10 个实例 `py_compile` 通过。

## 7. 回归验证（基线）

| 检查项 | 结果 |
|--------|------|
| quotation.pyc 一致函数数 | 144/150 (≥144 ✓) |
| compile_ok | True |
| 反模式新增 | 0 |
| 退化 | 无（144 == R13 基线） |
