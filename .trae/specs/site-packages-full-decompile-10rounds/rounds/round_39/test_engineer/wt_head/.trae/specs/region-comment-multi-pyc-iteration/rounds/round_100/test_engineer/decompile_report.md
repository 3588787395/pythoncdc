# R100 测试工程师反编译报告

## 基本信息
- **pyc 文件**: `IQCommon/api/check_strategy.pyc`
- **总函数数**: 2
- **一致函数数**: 1
- **成功率**: 50.00%
- **累计成功率**: 268/402 = 66.67% (保持不变，未新增 OK)

## 不一致函数

### check_strategy (orig=255, decomp=255, jump_diffs=14, true_diffs=44)

**第一个差异**: `[112] orig: POP_JUMP_FORWARD_IF_FALSE` vs `decomp: POP_JUMP_FORWARD_IF_TRUE`

**根因分析**:

反编译输出中 `check_strategy` 函数存在两个核心缺陷：

1. **条件取反缺陷**: 原始代码 `if pre_version < change_version <= current_version:` 被反编译为 `if not pre_version < change_version <= current_version:`，导致 `POP_JUMP_FORWARD_IF_FALSE` 变为 `POP_JUMP_FORWARD_IF_TRUE`。

2. **for-else 误识别缺陷**: 原始代码结构是：
   ```python
   for k, v in API_CHANGE_MAP.items():
       if cond:
           body
   else:
       after_for_body
   ```
   反编译输出为：
   ```python
   for k, v in API_CHANGE_MAP.items():
       if not cond:
           body
       continue
   else:
       after_for_body
   ```
   条件被取反，body 被放在 if 的 then 分支中，并添加了 `continue`。

**区域归约算法分析**:
- `_identify_conditional_regions` 在识别 if 区域时，当 if 的 then-branch 以 `continue`/`break`/`return` 结尾且 merge_block 跳回循环 header 时，可能误将条件取反
- 这是 IfRegion 在 LoopRegion 内部时的条件取反逻辑错误
- `_identify_loop_regions` 的 else_blocks 识别可能受到 if 条件取反的影响

## 最小复现实例验证 (10/10 DEFECT-REPRO)

| # | 文件 | 模式 | 状态 |
|---|------|------|------|
| 1 | repro_100_01_for_if_not_inverted.py | for-else 中 if 条件取反 | DEFECT-REPRO |
| 2 | repro_100_02_for_if_body_after.py | for-else 中 if 条件取反+后续 body | DEFECT-REPRO |
| 3 | repro_100_03_for_if_else_chain.py | for-else 中嵌套 if-else | DEFECT-REPRO |
| 4 | repro_100_04_chain_compare.py | for-else 中链式比较 | DEFECT-REPRO |
| 5 | repro_100_05_for_if_continue.py | for 中 if+continue | DEFECT-REPRO |
| 6 | repro_100_06_for_if_not_cond.py | for-else 中 if not 条件 | DEFECT-REPRO |
| 7 | repro_100_07_for_if_complex_body.py | for-else 中复杂 body | DEFECT-REPRO |
| 8 | repro_100_08_for_if_continue_else.py | for-else 中 if+continue+else | DEFECT-REPRO |
| 9 | repro_100_09_for_if_multi_stmt.py | for-else 中 if 多语句 | DEFECT-REPRO |
| 10 | repro_100_10_nested_for_if.py | 嵌套 for-else 中 if | DEFECT-REPRO |

## 模式分类

- **Pattern CI (Condition Inversion)**: 循环内 if 条件被取反 (10/10)
  - 当 IfRegion 的 then-branch 以 continue/break 结尾时，反编译器误将条件取反
  - 影响范围: 所有 `for/if/continue` 或 `for/if/break` 结构

## 建议

修复工程师应关注:
1. `region_ast_generator.py` 中 `_generate_if` 对循环内 IfRegion 的条件取反逻辑
2. `region_analyzer.py` 中 `_identify_conditional_regions` 对循环内 if 条件分支方向的判定
3. 检查 `POP_JUMP_FORWARD_IF_FALSE` → `POP_JUMP_FORWARD_IF_TRUE` 的条件取反发生位置
