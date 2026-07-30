# R21 测试工程师报告（V3 首轮，重点攻克 get_str_data 根因 A）

## 1. 基线统计

| 指标 | V2-R20 基线 | V3-R21 基线 |
|------|------------|------------|
| 总函数数 | 150 | **150** |
| 一致函数数 | 147 | **147** |
| 不一致函数数 | 3 | 3 |
| 成功率 | 98.00% | **98.00%** |
| compile_ok | True | True |
| `<module>` | match (delegated_embeds=133) | match (delegated_embeds=133) |

R21 基线与 V2-R20 完全一致（147/150=98.00%），**无退化**。继承 V2 round_20 全部归一化逻辑：跳转目标归一化（R14 elif 链跟随 + R15 循环块旁路）、常量编码归一化（R15 set/tuple 等价）、co_filename 元数据归一化（R16）、`<module>` 传递性不一致委托（R17 方案 A 两阶段比较）。

## 2. 残留 3 个不一致函数

| 函数名 | 状态 | 详细 | 根因 |
|--------|------|------|------|
| `get_str_data` | len_diff -48 (317→269) | 字节码指令数 orig=317 new=269，反编译缺失 48 条指令 | **P0** — BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式未建模。TernaryRegion merge_block 直接进入 BUILD_CONST_KEY_MAP n + STORE_SUBSCR 时，值表达式应作为整体 dict 构造语句归约，当前被拆为独立 TernaryRegion + bare expr 导致语句丢失 |
| `change_his_to_backward` | instr_diff@296 | @idx296 `POP_JUMP_FORWARD_IF_NOT_NONE` 跳转目标 orig=330 vs new=342；@idx329 起指令完全重排 | **P2** — code_generator if/else 分支布局未对齐，真实指令重排（非语义等价跳转目标偏移），不可在 exact_match_stats.py 安全归一化 |
| `get_date_and_count` | len_diff -27 (714→687) | 字节码指令数 orig=714 new=687，反编译缺失 27 条指令 | **P1** — Loop 反向链 fall-through 吸收外层 if/elif/else 条件块 + `_find_loop_else` 在 while 无 break 时误识别 else_blocks |

### 2.1 change_his_to_backward 差异性质确认

@idx296 的 `POP_JUMP_FORWARD_IF_NOT_NONE` 跳转目标：orig=330，new=342。

经 diff_detail.txt 详细分析（@idx329 起指令完全重排）：
- orig @329: `JUMP_FORWARD`（if 分支结束，跳过 else）
- new @329: `LOAD_FAST 'preindex'`（else 分支内部不同的指令序列）

**结论**：这是真实的指令重排（不同 opcodes/结构），非语义等价跳转目标偏移。现有 `_jump_targets_equiv`（elif 链 fall-forward）和 `_loop_block_bypass`（循环块旁路）归一化均无法覆盖。在 exact_match_stats.py 中归一化会掩盖真实指令重排差异，**不可安全归一化**，需 code_generator 对齐 if/else 分支布局。

## 3. 缺陷分类（按区域类型 + 违反的算法原则）

| 缺陷 | 区域类型 | 算法原则违反 | 说明 |
|------|---------|------------|------|
| get_str_data 消费模式未建模 | TernaryRegion（表达式子区域）→ dict 构造消费 | **原则 2（每块唯一归属）**：merge_block 同时是前驱 TernaryRegion 的 merge 与后继 TernaryRegion 的 entry，前驱独占标记为 generated 导致后继 entry 被跳过；**原则 4（入口引用语义）**：dict value 表达式应作为整体 dict 构造语句归约，父区域引用 dict 构造 entry 而非展开所有值表达式子块 | `_identify_ternary_regions`（region_analyzer.py）未建模 merge_block 直接进入 BUILD_CONST_KEY_MAP n + STORE_SUBSCR 的消费模式；值表达式被拆为独立 TernaryRegion + bare expr，未作为整体 dict 构造语句归约 |
| get_date_and_count 反向链 + loop_else | LoopRegion（循环区域识别） | **原则 1（自底向上归约）**：`_identify_loop_regions` 反向链走 fall-through 吸收外层 IfRegion else-branch 块，破坏层级识别顺序；**原则 2（每块唯一归属）**：循环后语句被错误归入循环 else，块归属冲突 | A: `_identify_loop_regions` 反向链 fall-through 校验缺失；B: `_find_loop_else` 在 while 无 break 时误识别 else_blocks；前置: IfRegion else-branch 块收集穿透嵌套 LoopRegion |
| change_his_to_backward 指令重排 | code_generator（生成层 if/else 布局） | **原则 4（入口引用语义）的生成层对偶**：code_generator if/else 分支生成顺序与原始字节码不一致，跳转目标布局偏移 | code_generator if/else 分支布局未对齐原始字节码，@idx296 起真实指令重排 |

### 3.1 修复优先级与根因顺序

修复优先级：**P0（get_str_data 消费模式建模）→ P1（get_date_and_count 穿透 + 反向链 + loop_else）→ P2（change_his_to_backward 布局对齐）**

严格遵守根因修复顺序（R12/R13/R19 教训）：
- **get_str_data**：A 消费模式建模 → 边界对齐（entry 不含前驱载入块）→ B 兄弟表达式子区域收集 → C 链式共享 merge_block discard
- **get_date_and_count**：穿透缺陷 → A 反向链校验 → B loop_else 守卫

## 4. 详细 diff 参考

逐指令 diff（3 个残留不一致函数，含 offset / opcode / argval 对比，标记 `!!` 为差异行）输出至：

**`/tmp/r21_out/diff_detail.txt`**（3231 行，3 节）

由 `rounds/round_21/test_engineer/diff_detail.py` 生成，复用 R21 `exact_match_stats.py` 的 `get_instr_list` / `walk_code` / `load_orig` 归一化逻辑（跳转目标归一化 + 常量编码归一化 + `<module>` 传递性委托）。

diff 文件头摘要：
```
# R21 diff_detail — 3 个残留不一致函数逐指令 diff
# summary: total=150 matched=147 mismatched=3 success_rate=98.0% compile_ok=True
# orig PYC=/workspace/quotation.pyc
# new  SRC=/tmp/r21_decompiled.py
```

## 5. 最小复现实例（10 个，聚焦 BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式）

R21 重点针对 get_str_data 的 BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式，提取 10 个最小复现实例，覆盖该消费模式的不同侧面：

| 复现实例 | 测试的 aspect | 对应根因 |
|---------|--------------|---------|
| repro_01 | 混合三元+普通载入值的核心模式（dict 部分 value 三元、部分 LOAD） | A: 消费模式核心 |
| repro_02 | 全部 value 为三元表达式（连续三元 merge 流入 BUILD_CONST_KEY_MAP） | A: 整组三元共享消费 |
| repro_03 | 循环内 dict 构造（BUILD_CONST_KEY_MAP+STORE_SUBSCR 作为循环主体归约节点） | A: loop body consumption |
| repro_04 | 链式三元共享 merge_block（前驱 merge == 后继 entry） | C: 链式共享独占标记 |
| repro_05 | STORE_SUBSCR 下标赋值消费（data.loc[i] = {...}，get_str_data 实际形态） | A: STORE_SUBSCR 消费 |
| repro_06 | 多个三元共享同一条件变量（整组归约不遗漏中间三元） | A: 共享 cond 消费 |
| repro_07 | 嵌套三元作为 dict value（多层 then/else + merge 汇入 BUILD_CONST_KEY_MAP） | A: 嵌套三元归约 |
| repro_08 | 循环内三元引用循环变量 + 普通载入混合（归约不穿透循环边界） | A: loop + 混合 value |
| repro_09 | 三元 value 涉及方法调用/属性访问（分支内 LOAD_ATTR+CALL，merge 仍流入消费） | A: 含方法调用三元 |
| repro_10 | 综合：循环 + 链式三元 merge + 混合值 + STORE_SUBSCR（get_str_data 完整形态） | A+C: 综合模式 |

全部 10 个 repro 位于 `rounds/round_21/test_engineer/minimal_repros/repro_01.py` .. `repro_10.py`，每个文件顶部含注释说明所测试的 BUILD_CONST_KEY_MAP 消费模式 aspect。

## 6. 反编译产物

| 检查项 | 结果 |
|--------|------|
| `/tmp/r21_decompiled.py` | 已生成（继承 V2 round_20 反编译流程，未修改产物） |
| `compile(src, '<decompiled>', 'exec')` | OK (compile_ok=True) |
| `/tmp/r21_out/bc_results.json` | 已生成（summary + per-function results） |
| `/tmp/r21_out/diff_detail.txt` | 已生成（3231 行，3 节） |

## 7. 退出条件检查

| 退出条件 | 状态 | 说明 |
|---------|------|------|
| V3-E1 不一致函数数 = 0（100%） | ✗ 未达成 | 残留 3 个 |
| V3-E2 可提取新增最小复现实例 < 10 | ✗ 未达成 | 本轮提取 10 个 repro（聚焦 BUILD_CONST_KEY_MAP 消费模式），残留不一致函数 3 个但 repro 需求 ≥10 |

## 8. 对修复工程师的建议

### 8.1 get_str_data（P0，本轮重点）

优先建模 BUILD_CONST_KEY_MAP+STORE_SUBSCR 消费模式（区域识别层 `region_analyzer.py` 的 `_identify_ternary_regions`）：
- **WHEN** 三元/载入表达式的 merge_block 直接进入 `BUILD_CONST_KEY_MAP n` + `STORE_SUBSCR`
- **THEN** 这些值表达式 SHALL 作为整体 dict 构造语句归约，而非独立 TernaryRegion/bare expr
- 同步更新 `_identify_ternary_regions` docstring（6 节模板）

修复顺序严格遵守：A 消费模式建模 → 边界对齐 → B 兄弟表达式子区域收集 → C 链式共享 merge_block discard（禁止跳过 A 直接修复 B/C，R12/R19 教训：会暴露 A 导致 -48→-84 退化）。

### 8.2 change_his_to_backward（P2，defer）

code_generator if/else 分支布局对齐，属生成层重构，影响面广，需配套最小复现实例回归。本轮 defer。

### 8.3 get_date_and_count（P1，defer）

先解决 IfRegion else-branch 块收集穿透嵌套 LoopRegion（region_ast_generator.py `_process_if_blocks`），再修复 A 反向链 fall-through 校验 + B loop_else 无 break 守卫。本轮 defer。
