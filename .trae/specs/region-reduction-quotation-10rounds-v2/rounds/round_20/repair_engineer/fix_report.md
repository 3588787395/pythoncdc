# R20 修复工程师报告（V2 最终验证与收尾轮次）

## 1. 修复目标

- **目标**: V2 10 轮迭代的最终验证与收尾。确认最终基线 147/150 (98.00%)，尝试最后的低风险修复，生成 `final_residual_v2.md`。
- **R19 基线**: 147/150 (98.00%)，残留 3 个不一致函数。
- **R20 策略**: 最终验证 + 评估 change_his_to_backward 低风险归一化可行性（若语义等价则归一化，否则确认无法安全修复）。

## 2. 最终残留缺陷定位（3 个残留函数最终状态 + 根因）

### 2.1 get_str_data — len_diff -48 (317→269)

**最终根因（三层，R18/R19 诊断确认）**:

| 根因层 | 描述 | 处置状态 |
|--------|------|---------|
| A | BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式未完整建模。TernaryRegion@1226 被误赋 `value_target='i'` | R18 **部分修复**（`value_target=None`，`container_type='dict'`，7 键捕获）；消费模式整体归约未建模 |
| B | `_process_if_blocks` 仅从 region.children 收集表达式子区域，遗漏 IfRegion@614 else_blocks 中的兄弟 TernaryRegion@844/@1226 | deferred（R19 修复因暴露 A 的消费模式缺陷导致 -48→-84 退化回退） |
| C | TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry 链式共享，前驱独占标记 merge_block 为 generated | deferred（R19 修复因暴露 A 的消费模式缺陷导致 -48→-84 退化回退） |

**关键结论**: R18 修复根因 A（value_target 检测）是必要但不充分的。完整修复需先建模 BUILD_CONST_KEY_MAP 消费模式（区域识别层），使 7 个值表达式作为整体 dict 构造语句归约，再应用 B/C 修复（生成层）。

### 2.2 change_his_to_backward — instr_diff@296 (len 578=578)

**R20 低风险归一化评估**:

@idx296 的 `POP_JUMP_FORWARD_IF_NOT_NONE` 跳转目标：orig=330，new=342。

经 `/tmp/r20_out/diff_detail.txt` 详细分析（@idx329 起指令完全重排）：
- orig @329: `JUMP_FORWARD->[490]`（if 分支结束，跳过 else）
- new @329: `LOAD_FAST 'preindex'`（else 分支内部不同的指令序列）
- @idx330-345: orig 与 new 的 opcodes 完全不同（orig: `data[predataindex:curdataindex].empty` 检查；new: `preindex != n` 检查）

**最终根因**: code_generator 的 if/else 分支布局与原始字节码不一致，属指令重排（R14 defer）。

**归一化决策**: **不可安全归一化**。理由：
1. 这是真实的指令重排（不同 opcodes/结构），非语义等价跳转目标偏移
2. 现有 `_jump_targets_equiv`（elif 链 fall-forward）和 `_loop_block_bypass`（循环块旁路）归一化均无法覆盖
3. 在 exact_match_stats.py 中归一化会掩盖真实指令重排差异，违反"不掩盖真实差异"原则
4. 完整修复需 code_generator 对齐 if/else 分支生成顺序（影响面广，R14 defer）

### 2.3 get_date_and_count — len_diff -27 (714→687)

**最终根因（双层，R13 诊断确认）**:

| 根因层 | 描述 | 处置状态 |
|--------|------|---------|
| A | `_identify_loop_regions` 反向链走 fall-through 吸收外层 if/elif/else 条件块 | deferred（R13 修复因 -27→-63 退化回退） |
| B | `_find_loop_else` 在 while 无 break 时误识别 else_blocks | deferred（R13 修复因 -27→-63 退化回退） |

**关键结论**: 完整修复需先解决 IfRegion else-branch 块收集穿透嵌套 LoopRegion（避免误吸收循环后语句），再修复反向链 fall-through 校验 + loop_else 无 break 守卫。

## 3. R20 修复尝试

### 3.1 change_his_to_backward 低风险归一化评估

**评估方法**: 分析 `/tmp/r20_out/diff_detail.txt` 中 change_his_to_backward 的 @idx296 跳转目标差异（330 vs 342）及 @idx329 起的指令序列。

**评估结论**: 差异伴随 @idx329 起的指令完全重排（不同 opcodes），属真实指令重排而非语义等价跳转目标。现有归一化（elif 链 fall-forward / 循环块旁路）无法覆盖，且在 exact_match_stats.py 中归一化会掩盖真实差异。

**决策**: 确认无法安全修复，进入最终验证。R20 不修改任何代码（core/ 与 HEAD 字节一致）。

### 3.2 算法依据（4 原则对应）

R20 不修改代码，维持 R18（HEAD commit 855b96b 后经 R19 无变更）的 4 原则合规状态：

| 原则 | 状态 | 说明 |
|------|------|------|
| 1. 自底向上归约 | ✓ | 维持 HEAD 状态 |
| 2. 每块唯一归属 | ✓ | 维持 HEAD 状态 |
| 3. 嵌套即抽象节点 | ✓ | 维持 HEAD 状态 |
| 4. 入口引用语义 | ✓ | 维持 HEAD 状态 |

## 4. 回归测试

### 4.1 一致性统计

| 指标 | R19 基线 | R20 最终 | 变化 |
|------|---------|---------|------|
| 总函数数 | 150 | 150 | — |
| 一致函数数 | 147 | **147** | — (无退化) ✓ |
| 不一致函数数 | 3 | 3 | — |
| 成功率 | 98.00% | **98.00%** | — |
| compile_ok | True | True | — |
| `<module>` | match (delegated_embeds=133) | match (delegated_embeds=133) | — |

### 4.2 既有区域测试矩阵（0 退化）

`python -m pytest tests/control_flow_matrix/ -q` 结果：**9 failed, 318 passed, 11 skipped**（与 R18/R19 基线完全一致，0 退化）。

9 个失败用例均为既有基线失败（TestL03ForElse / TestL04WhileElse / TestE03TryExceptElse / TestN11TryWhileContinue / TestXP04BoolOpInIf / TestXP07NestedTernary / TestCO09WhileIfWhileBreak / TestDEEP12 / TestDEEP16），非 R20 引入。

R20 不修改代码（`git diff HEAD -- core/` 为空），矩阵结果与 HEAD 必然一致。

### 4.3 编译与导入

| 检查项 | 结果 |
|--------|------|
| `import core.cfg.region_analyzer; import core.cfg.region_ast_generator` | IMPORT_OK ✓ |
| `compile /tmp/r20_decompiled.py` | COMPILE_OK ✓ |
| 反编译产物 src_len | 175488 (3641 lines) ✓ |
| 反编译耗时 | ~1.6s ✓ |

### 4.4 最小复现实例（G5）

10 个 repro 全部 `py_compile` 通过（覆盖 3 个残留函数根因）：
repro_01_get_str_data_const_key_map / repro_02_get_str_data_chain_shared_merge / repro_03_get_str_data_sibling_ternary / repro_04_get_str_data_ternary_boundary / repro_05_change_his_backward_if_else_reorder / repro_06_change_his_backward_jump_target / repro_07_change_his_backward_structural / repro_08_get_date_and_count_reverse_chain / repro_09_get_date_and_count_loop_else / repro_10_get_date_and_count_combined

## 5. 反模式自检

| 检查项 | 结果 |
|--------|------|
| `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法（新增） | 0 新增 ✓（core/ 与 HEAD 字节一致） |
| 既有 `_merge_block_is_loop_back_edge`（commit ec8ca39，R11 前） | 既有，非 R20 新增 ✓ |
| 硬编码深度上限（新增） | 0 新增 ✓ |
| 跨区域跨层次启发式规则 | 0 新增 ✓ |
| 后处理修正 | 0 新增 ✓ |
| 修改反编译产物文件 | 无 ✓ |

## 6. docstring 合规（G8）

R20 不修改代码，`region_ast_generator.py` / `region_analyzer.py` == HEAD。11 类 `_identify_*_regions` 识别方法 docstring 维持 V1 R8 的 6 节统一模板（11/11），**无变更**。

## 7. 算法 4 原则符合度

R20 不修改代码，当前代码 == HEAD（R18 commit 855b96b 经 R19 无变更），4 原则合规状态 == R18/R19（PASS）。

## 8. V2 退出条件检查

| 退出条件 | 状态 | 说明 |
|---------|------|------|
| V2-E1 不一致函数数 = 0（100%） | ✗ 未达成 | 残留 3 个 |
| V2-E2 可提取新增最小复现实例 < 10 | ✓ 已达成 | 残留不一致函数 3 < 10 |

V2-E2 已达成，V2-E1 未达成，输出 `final_residual_v2.md` 作为后续迭代输入。

## 9. R20 产出

### 测试工程师阶段（完成）:
- `test_engineer/decompile_report.md`（最终基线 147/150 + 3 残留函数最终状态 + 10 个最小复现实例 + 退出条件检查）
- `test_engineer/decompile_quotation.py` / `exact_match_stats.py` / `diff_detail.py`
- `test_engineer/minimal_repros/repro_01..repro_10.py`（10 个最小复现实例，覆盖 3 残留函数根因）

### 修复工程师阶段（完成）:
- `repair_engineer/fix_report.md`（本报告）
- `repair_engineer/final_residual_v2.md`（V2 10 轮迭代总结 + 残留清单 + 后续建议）

## 10. 异常说明

R20 未实现净改善（147 维持）。原因：3 个残留函数的根因均涉及区域识别层/生成层的深层结构性改动（非局部 bug 修复），风险高、影响面广：
- get_str_data 需建模 BUILD_CONST_KEY_MAP 消费模式（区域识别层功能扩展）
- change_his_to_backward 需 code_generator 对齐 if/else 分支布局（生成层重构）
- get_date_and_count 需解决 IfRegion else-branch 块收集穿透嵌套 LoopRegion（区域识别层 + 生成层）

R12/R13/R18/R19 已验证：在深层缺陷未解决前，局部修复会暴露并放大缺陷，导致退化（-48→-69/-84，-27→-63）。R20 依据"0 退化"硬约束，确认无法安全修复，维持 147 基线，输出残留清单作为后续迭代输入。
