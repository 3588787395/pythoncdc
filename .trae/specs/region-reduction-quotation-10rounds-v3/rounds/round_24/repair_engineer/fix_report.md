# R24 修复工程师报告 — quotation.pyc 两类缺陷修复

> 修复目标：`/workspace/core/cfg/region_analyzer.py`（区域归约分析器）
> 验证目标：`/workspace/quotation.pyc`（Python 3.11）+ R24 测试工程师 8 个 minimal repro
> 基线成绩：**148 / 150 = 98.67%**（R23 持平，残留 2 个不一致函数）
> 修复后成绩：**150 / 150 = 100.00%**，`compile_ok=True`，0 个不一致函数

---

## 0. 修复结果总览

| 指标 | 基线 (R23/R24-in) | 修复后 |
|---|---|---|
| quotation.pyc 成功率 | 148/150 (98.67%) | **150/150 (100.00%)** |
| `change_his_to_backward` | instr_diff@296 | **match** |
| `get_date_and_count` | len_diff -27 | **match** |
| 8 个 minimal repro | 8/8 复现 | **8/8 match（未复现）** |
| 控制流完备性矩阵 | 318 passed / 9 failed / 11 skipped | **318 passed / 9 failed / 11 skipped（无变化）** |
| 区域生成测试（boolop/if/ternary/loop） | 见下文 | **与基线逐项一致，0 回归** |

两类缺陷均已修复，且未引入任何回归。

---

## 1. 缺陷 A — `change_his_to_backward`：IF then 分支吸收循环末尾兄弟语句

### 1.1 根因

`_identify_conditional_regions` / `_check_elif_chain` 在确定 if/elif/else 链的合并点（merge）时，使用 `_find_nearest_common_post_dominator(then_succ, else_succ)` 计算最近公共后必经节点（NCPD）。当 if 嵌套于循环内、且某分支以 break/continue/return 退出循环时，NCPD 会返回**循环出口块**（位于 LoopRegion.blocks 之外）作为 merge。但循环出口不是 if 的合并点——if 的合并点是非退出分支在循环内的汇聚块（循环末尾的兄弟语句入口）。以循环出口为 merge 会使 `_collect_branch_blocks` 越过 then 末尾的 JUMP_FORWARD，把循环末尾兄弟语句（if/elif/else 链的公共汇聚后继块）误并入 then 分支，违反「每块唯一归属」（兄弟语句应归属循环体）。

### 1.2 修复

新增循环感知合并点计算，遵循「No More Gotos」§4.2（循环区域）/§3（If 区域归约）+ 4 原则：

1. **`_find_enclosing_loop(block)`**（行 1837）：返回包含 block 的最内层 LoopRegion（无则 None）。
2. **`_is_loop_exit_block(block, loop_region)`**（行 1852）：判断块是否为循环出口块（JUMP_BACKWARD 回边 / RETURN/RAISE 终态 / JUMP_FORWARD 目标在循环外）。
3. **`_compute_in_loop_if_merge(then_succ, else_succ, loop_region, exclude)`**（行 1872）：当 NCPD 返回循环出口块时，取非退出分支末尾的 JUMP_FORWARD 目标（位于循环内、不在 exclude 中），用 BFS 可达性（不跨循环出口、不跨回边）验证其对侧分支经循环内路径可达，从而重算 if 的循环内合并点。

4. **`_identify_conditional_regions`（行 11641）** + **`_check_elif_chain`（行 12784）**：当 merge 落在循环外时，调用 `_compute_in_loop_if_merge` 重算合并点为循环内汇聚块；内层 elif 镜像同样修正，且当内层重算失败时继承外层链已修正的合并点（`inner_merge = merge_`）。

### 1.3 效果

repro_01~04（IF then 吸收循环末尾兄弟语句）全部 match；`change_his_to_backward` 由 instr_diff@296 → match。

---

## 2. 缺陷 B — `get_date_and_count`：LOOP 反向链吸收外层条件块 + loop_else

### 2.1 根因（关键定位）

`get_date_and_count` 的 `candle_period==8/15` 分支结构为：外层 `if/elif/else` 链，then 与 else 子分支均含 `while count>0:` 循环 + 循环后 `if month in (10,11,12):` 条件块，每个分支末尾 JUMP_FORWARD 到 return。

通过 `debug_repro06.py` 导出区域结构发现，根因**不在** `_find_loop_else` 的 else_blocks 边界（R5-Fix1 的「无 break 时 else 作为顺序语句」逻辑本身正确），而在 **`_detect_while_condition_boolop_chain` 的反向链回溯**：

- while 循环的 condition_block（如 repro_06 的 block@46，含 `count -= 1; while count > 0:`）是 LoopRegion 的条件块。
- `_detect_while_condition_boolop_chain` 从 condition_block **反向回溯前驱**，把外层 `elif count == 1:` 条件块（block@28）误吸收为 while 条件 boolop 链的操作数，形成 `BoolOpRegion(28, 46) merge=128`。
- 判据缺陷：前驱 block@28 的 fall-through 是 elif 体（block@40 `start='B'`，**位于循环外**），故 `cond_in_loop=False`；其跳转目标是循环条件 block@46（**在循环内**），故 `else_outside=False`。原代码仅在 `cond_in_loop and else_outside` 为真时执行额外校验，当两者皆假时**直接吸收前驱**——这正是 `elif X: <体> else: <while>` 模式（前驱的 else 分支落入循环），却被误判为 `while A and B:` 复合条件。

该误吸收级联破坏整个外层结构：
1. `elif count == 1` 守卫被并入 `count > 0` → `elif count == 1 and count > 0`；
2. else 子分支的 `count -= 1`、while 包装、回边丢失，循环体降级为裸 if/else；
3. 循环后 `if month in (10,11,12)` 被外提为多余兄弟语句。

### 2.2 修复（核心）

**`_detect_while_condition_boolop_chain`（行 16202）**：在计算 `cond_in_loop` / `else_outside` 后，新增判据——

```python
if not cond_in_loop:
    break
```

**算法依据**：「No More Gotos」§4.2 + 原则 2（每块唯一归属）+ 原则 3（嵌套即抽象节点）。while 条件 boolop 链的合法前驱，其 fall-through 必须继续求值循环条件（`cond_in_loop=True`，如 `while A and B:` 中 A 的 fall-through → B=cond_block）。当 `cond_in_loop=False` 时，前驱的 fall-through 是外层 if/elif 的 then 体（位于循环外），前驱是**外层 if/elif 条件块**——其 else 分支（跳转目标）落入循环条件。把它误吸收会把 while 条件并入外层 elif 守卫，使外层 IfRegion 消失（违反每块唯一归属）。此时必须中断回溯，让外层 if/elif 由 IfRegion 归约。

该判据是安全且完备的：合法 while-boolop 前驱的 fall-through 恒为下一条件块（在循环内），故 `cond_in_loop` 恒为真；`cond_in_loop=False` 仅出现在外层 if/elif/while 嵌套场景。

### 2.3 配套守卫（`_identify_loop_regions` 行 3192）

在 LoopRegion 条件链前驱反向吸收处保留 `_p_is_outer_elif` 守卫：当某前驱 `p` 的「非循环条件/非循环体」后继是非出口块（即外层 if/elif 的另一分支）时，判定 `p` 为外层 if/elif 条件块，不吸收并终止回溯。该守卫与 boolop 修复互补——boolop 修复阻止 while 条件在 BoolOp 识别阶段并入外层 elif；本守卫阻止外层 elif 在 LoopRegion 条件链扩展阶段被循环吞并。两者共同保证「每块唯一归属」。

### 2.4 loop_else / 循环后顺序语句处理（无需修改）

修复 boolop 误吸收后，LoopRegion 仍按原逻辑把循环后 `if month in (10,11,12)` 块归为 `else_blocks`（无 break 时）。`_generate_loop` 的 **R5-Fix1** 逻辑（行 4301）正确处理此场景：无 break时 `else_stmts` 不作为 orelse，而作为 while 之后的顺序语句返回，并标记为已生成避免父区域重复输出。即循环后条件块作为子分支内顺序语句保留在原分支内，不外提为兄弟——完全符合测试报告的修复方向。**故 `_find_loop_else` / `_generate_loop` 无需改动。**

### 2.5 效果

repro_05~08（LOOP 反向链吸收外层条件块 + loop_else）全部 match；`get_date_and_count` 由 len_diff -27 → match。

以 repro_06 为例，修复前反编译为坍塌的 `if (flag == 0) in (10, 11, 12): ... elif count == 1 and count > 0: <裸 if/else>`；修复后完整还原 `if/elif/else` + else 分支内的 `count -= 1; while count > 0: ...; if month in (10,11,12): ... else: ...`。

---

## 3. 验证

### 3.1 minimal repro（8/8 match）

```
repro_01_if_absorb_sibling_in_loop.py:           match (orig=48 new=48)
repro_02_if_absorb_sibling_while.py:             match (orig=62 new=62)
repro_03_if_absorb_sibling_elif_chain.py:        match (orig=51 new=51)
repro_04_if_absorb_sibling_minimal.py:           match (orig=41 new=41)
repro_05_loop_absorb_outer_cond_full.py:         match (orig=141 new=141)
repro_06_loop_absorb_outer_cond_else_only.py:    match (orig=81 new=81)
repro_07_loop_absorb_outer_cond_if_else.py:      match (orig=141 new=141)
repro_08_loop_absorb_outer_cond_simple_body.py:  match (orig=89 new=89)
```

验证脚本：`/workspace/.trae/specs/region-reduction-quotation-10rounds-v3/rounds/round_24/test_engineer/_run_repros.py`

### 3.2 quotation.pyc 成功率

```
[stats] orig code objects: 150
[stats] new code objects: 150
[stats] compile_ok=True
[stats] total=150 matched=150 mismatched=0 missing=0 success_rate=100.00%
[stats] mismatched functions (0):
```

反编译命令：`cd /workspace && timeout 120 python pycdc.py /workspace/quotation.pyc > /tmp/r24_decompiled.py`
统计脚本：`/workspace/.trae/specs/region-reduction-quotation-10rounds-v3/rounds/round_24/test_engineer/exact_match_stats.py`

### 3.3 回归测试（与基线逐项对比，0 回归）

| 测试矩阵 | 基线 | 修复后 |
|---|---|---|
| `tests/control_flow_matrix/` pytest | 318 passed / 9 failed / 11 skipped | 318 passed / 9 failed / 11 skipped |
| 区域生成 boolop（4 复杂度 ×300） | 1200/1200 | 1200/1200 |
| 区域生成 if（4 复杂度 ×300） | 986/986 | 986/986 |
| 区域生成 ternary（4 复杂度 ×300） | 1200/1200 | 1200/1200 |
| 区域生成 loop（4 复杂度 ×300） | 710/1136（426 预存 while/for-else ast_mismatch） | 710/1136（同基线，预存失败） |
| 区域已记录 bugs（if 区域） | 4/13（9 预存 ast_mismatch） | 4/13（同基线） |

> 回归对比方法：`git stash push core/cfg/region_analyzer.py` 后重跑各矩阵，结果与修复后**完全一致**。loop 区域的 426 个 while/for-else `ast_mismatch` 与 if 区域的 9 个 ast_mismatch 均为**预存失败**（基线即存在，与本次修复无关，属 while/for-else `else` 子句生成的已知限制，不在本轮缺陷范围）。

---

## 4. 算法原则合规性

本次修复严格遵循「No More Gotos」区域归约算法 4 原则，**未使用**任何 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法，**未硬编码**深度上限，**未引入**跨区域启发式：

| 原则 | 缺陷 A 修复 | 缺陷 B 修复 |
|---|---|---|
| ① 自底向上归约 | if 区域在循环体内归约时，合并点取循环内汇聚块（非循环出口） | while 条件 boolop 链识别时，外层 if/elif 不被内层循环条件吸收，由 IfRegion 独立归约 |
| ② 每块唯一归属 | 循环末尾兄弟语句归属循环体，不被 then 分支吸收 | 外层 elif 条件块归属 IfRegion，不被 LoopRegion 条件链 / BoolOp 吸收 |
| ③ 嵌套即抽象节点 | 内层 elif 合并点继承外层链合并点 | while 条件 boolop 不跨越外层 if/elif 边界 |
| ④ 入口引用语义 | 父循环通过 if entry 引用 IfRegion | 父 IfRegion 通过 LoopRegion entry 引用循环；循环后顺序语句由 R5-Fix1 在原分支内发射 |

---

## 5. 修改文件清单

仅修改 1 个文件：**`/workspace/core/cfg/region_analyzer.py`**（+189 行，0 删除）

| 位置 | 内容 | 缺陷 |
|---|---|---|
| 行 1837–1929 | 新增 `_find_enclosing_loop` / `_is_loop_exit_block` / `_compute_in_loop_if_merge` | A |
| 行 3192–3227 | `_identify_loop_regions` 条件链前驱吸收处 `_p_is_outer_elif` 守卫 | B（配套） |
| 行 11641–11659 | `_identify_conditional_regions` 循环感知 merge 重算 | A |
| 行 12784–12812 | `_check_elif_chain` 内层 elif 循环感知 merge 重算 | A |
| 行 16202–16213 | `_detect_while_condition_boolop_chain` `if not cond_in_loop: break` | **B（核心）** |

未修改 `region_ast_generator.py`（R5-Fix1 顺序语句逻辑本身正确）、未修改 `pycdc.py`、未修改 quotation.pyc。

---

## 6. 备注

- 未执行 `git commit` / `git push`（遵循任务约束）。
- 修复过程中创建的调试脚本（`debug_repro06.py` 等）为临时验证工具，不影响反编译器源码。
- loop 区域预存的 426 个 while/for-else `ast_mismatch` 为基线既有问题（while/for 显式 `else` 子句的 AST 等价比较限制），与本轮两类缺陷无关，留待后续轮次处理。
