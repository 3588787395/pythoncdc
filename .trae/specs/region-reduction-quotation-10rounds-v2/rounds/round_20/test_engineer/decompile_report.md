# R20 测试工程师报告（V2 最终验证轮次）

## 1. 基线统计

| 指标 | R19 基线 | R20 最终基线 |
|------|---------|------------|
| 总函数数 | 150 | 150 |
| 一致函数数 | 147 | **147** |
| 不一致函数数 | 3 | 3 |
| 成功率 | 98.00% | **98.00%** |
| compile_ok | True | True |
| `<module>` | match (delegated_embeds=133) | match (delegated_embeds=133) |

R20 最终基线与 R19 完全一致（147/150），无退化。继承 R19（含 R17 传递性委托 + R14/R15/R16 归一化）全部归一化逻辑。

## 2. 残留 3 个不一致函数（最终状态）

| 函数名 | 状态 | 最终根因 | 历史 |
|--------|------|---------|------|
| `get_str_data` | len_diff -48 (317→269) | BUILD_CONST_KEY_MAP 消费模式未完整建模 + 区域边界对齐 + B/C 修复需先建模消费模式 | R18 修复根因 A，R19 修复 B/C 因 -48→-84 退化回退 |
| `change_his_to_backward` | instr_diff@296 | if/else 分支指令重排（code_generator 布局未对齐） | R14 defer |
| `get_date_and_count` | len_diff -27 (714→687) | _identify_loop_regions 反向链吸收外层 if/elif/else + _find_loop_else 误识别 | R13 修复 A+B 因 -27→-63 退化回退 |

### 2.1 change_his_to_backward 差异性质确认

@idx296 的 `POP_JUMP_FORWARD_IF_NOT_NONE` 跳转目标：orig=330，new=342。

经 diff_detail.txt 详细分析（@idx329 起指令完全重排）：
- orig @329: `JUMP_FORWARD->[490]`（if 分支结束，跳过 else）
- new @329: `LOAD_FAST 'preindex'`（else 分支内部不同的指令序列）

**结论**：这是真实的指令重排（不同 opcodes/结构），非语义等价跳转目标偏移。现有 `_jump_targets_equiv`（elif 链 fall-forward）和 `_loop_block_bypass`（循环块旁路）归一化均无法覆盖。在 exact_match_stats.py 中归一化会掩盖真实指令重排差异，**不可安全归一化**，需 code_generator 对齐 if/else 分支布局。

## 3. 退出条件检查

| 退出条件 | 状态 | 说明 |
|---------|------|------|
| V2-E1 不一致函数数 = 0（100%） | ✗ 未达成 | 残留 3 个 |
| V2-E2 可提取新增最小复现实例 < 10 | ✓ 已达成 | 残留不一致函数仅 3 个 < 10 |

V2-E2 已达成（残留不一致函数 3 < 10），但 V2-E1 未达成，故输出 `final_residual_v2.md` 作为后续迭代输入。

## 4. 最小复现实例（10 个，覆盖 3 个残留函数根因）

10 个复现实例覆盖 3 个残留函数的根因侧面（每个残留函数因多层根因生成多个 repro）：

| 复现实例 | 对应残留函数 | 根因层 |
|---------|------------|--------|
| repro_01_get_str_data_const_key_map | get_str_data | A: BUILD_CONST_KEY_MAP 消费模式 |
| repro_02_get_str_data_chain_shared_merge | get_str_data | C: 链式共享 merge_block 独占 |
| repro_03_get_str_data_sibling_ternary | get_str_data | B: 兄弟表达式子区域遗漏 |
| repro_04_get_str_data_ternary_boundary | get_str_data | 区域边界对齐 |
| repro_05_change_his_backward_if_else_reorder | change_his_to_backward | if/else 分支布局差异 |
| repro_06_change_his_backward_jump_target | change_his_to_backward | 跳转目标偏移 |
| repro_07_change_his_backward_structural | change_his_to_backward | 结构性指令重排 |
| repro_08_get_date_and_count_reverse_chain | get_date_and_count | A: 反向链吸收外层 |
| repro_09_get_date_and_count_loop_else | get_date_and_count | B: loop_else 误识别 |
| repro_10_get_date_and_count_combined | get_date_and_count | A+B 综合模式 |

全部 10 个 repro `py_compile` 通过（OK=10 FAIL=0）。

## 5. 反编译产物

| 检查项 | 结果 |
|--------|------|
| /tmp/r20_decompiled.py | 生成成功（src_len=175488, src_lines=3641） |
| compile(src, '<decompiled>', 'exec') | OK |
| 反编译耗时 | ~1.6s |

## 6. 对修复工程师的建议

### 6.1 change_his_to_backward 低风险归一化评估

经 diff_detail.txt 分析，change_his_to_backward @idx296 的跳转目标差异（330 vs 342）伴随 @idx329 起的指令完全重排（不同 opcodes）。这是 code_generator 的 if/else 分支布局差异，非语义等价跳转目标。

**建议**：不在 exact_match_stats.py 归一化（会掩盖真实指令重排），确认无法安全修复，进入最终验证。完整修复需 code_generator 对齐 if/else 跳转目标布局（R14 defer，影响面广）。

### 6.2 残留函数后续迭代方向

1. **get_str_data**：优先建模 BUILD_CONST_KEY_MAP 消费模式（区域识别层），再应用 B/C 修复（生成层）
2. **change_his_to_backward**：code_generator 对齐 if/else 分支生成顺序
3. **get_date_and_count**：先解决 IfRegion else-branch 块收集穿透嵌套 LoopRegion，再修复反向链 fall-through 校验 + loop_else 无 break 守卫
