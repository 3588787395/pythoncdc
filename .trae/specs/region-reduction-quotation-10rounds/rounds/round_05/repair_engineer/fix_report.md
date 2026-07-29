# 轮 5 修复工程师报告（fix_report.md）

> 区域归约算法驱动的 quotation.pyc 反编译迭代 — 第 5 轮修复工程师阶段
> 工作目录：`/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_05/repair_engineer/`
> 算法约束：区域归约 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）

## 1. 修复目标

主攻 `fill_minute_or_day_blank`（R4 diff=-42，最易改善候选），修复 ternary merge block 后续赋值丢失缺陷，力争在不退化的前提下改善该函数 diff。不允许退化（一致函数数 ≥ 141）。

## 2. 根因分析

### 2.1 缺陷函数：`fill_minute_or_day_blank`（R4 diff=-42，R5 改善至 -30）

**缺陷模式**：`x = a if cond else b`（三元，merge block 含 STORE_FAST）后跟 `y = foo(); z = bar(); if len(z) > 0: ...` —— ternary STORE_* 与 if 条件之间的独立赋值（source_start=, source_end=, dts=）被丢弃。

**算法根因**：`region_ast_generator.py` `_if_extract_cond_instructions` 中 `_cond_block_is_ternary_merge` 标志对 cond_block（TernaryRegion.merge_block）内所有 STORE_* 生效，导致 ternary STORE_* 之后的独立赋值被跳过，IfRegion 条件块内前置赋值丢失。

**违反原则**：原则 2（每块唯一归属）—— ternary 归约范围仅到其 STORE_* 为止，不延伸到同块后续指令。ternary 的 STORE_* 属于 TernaryRegion，但同块后续的 STORE_*（source_start=, source_end=, dts=）应属于 IfRegion 的 pre_stmt，不应被 ternary 标志吞并。

### 2.2 指令级证据

- ORIG `POP_JUMP_FORWARD_IF_FALSE 1206` → NEW `POP_JUMP_FORWARD_IF_FALSE 1030`（R5 修复后）：if 分支出口仍偏短，但已恢复部分尾部代码
- 尾部 diverge：NEW 仍缺失 `pandas.DataFrame` 构造、`pandas.concat` 合并等 30 条尾部指令（R4 缺失 42 条，R5 恢复 12 条中的 3 条赋值）

## 3. 修复点

**文件**：`core/cfg/region_ast_generator.py`

**位置**：`_if_extract_cond_instructions` L8849-8853

**修改内容**：第一个 STORE_* 跳过后清除 `_cond_block_is_ternary_merge = False`，使后续 STORE_* 走正常 pre_stmt 提取路径。

**修复前**（缺陷）：`_cond_block_is_ternary_merge` 标志在 ternary 的 STORE_* 命中后保持 True，对 cond_block 内全部后续 STORE_* 生效，导致 source_start= / source_end= / dts= 三条前置赋值被跳过。

**修复后**：ternary 归约范围仅到其 STORE_* 为止；首个 STORE_* 处理完毕后清除标志，后续 STORE_* 归属 IfRegion pre_stmt，正常提取。

## 4. 算法依据

**No More Gots §3.1**：基本块内顺序指令按偏序归约，ternary 归约范围仅到其 STORE_* 为止。

基本块内的顺序指令构成偏序关系：ternary 表达式的 merge block 内，ternary 的 STORE_* 是 ternary 归约的终止点；其后继指令（独立赋值）与 ternary 无数据依赖，应独立归约。归约器不应将 ternary 的归约范围延伸到同块后续无依赖指令。

## 5. 区域归约 4 原则对应

| 原则 | 对应 |
|---|---|
| 原则 1（自底向上归约） | ternary 作为底层区域先归约，其 STORE_* 为终止点 ✓ |
| 原则 2（每块唯一归属） | **核心**：第一个 STORE_* 属于 TernaryRegion，后续 STORE_* 属于 IfRegion pre_stmt ✓ |
| 原则 3（嵌套即抽象节点） | ternary 归约后作为单个抽象节点，不延伸归约范围 ✓ |
| 原则 4（入口引用语义） | IfRegion 条件块引用 ternary 抽象节点出口 ✓ |

## 6. 回归结果

### 6.1 quotation.pyc 一致性

- total=150, matched=141, mismatched=9, missing=0, success_rate=94.00%, compile_ok=True
- **无退化**：与 R4 基线 141/150 完全一致
- **改善项**：`fill_minute_or_day_blank` diff -42→-30（恢复 3 条赋值：source_start / source_end / dts 前置赋值）

### 6.2 既有区域测试矩阵（0 退化）

| 区域 | passed | failed | errors | total | 与 R4 对比 |
|---|---|---|---|---|---|
| IF | 287 | 3 | 0 | 290 | 一致（3 failures 全为 pre-existing） |
| TERNARY | 18 | 2 | 0 | 20 | 一致（2 failures 全为 pre-existing） |
| BOOLOP | 19 | 1 | 0 | 20 | 一致（1 failure 为 pre-existing） |
| TRY | 19 | 1 | 0 | 20 | 一致（1 failure 为 pre-existing） |
| LOOP | 19 | 1 | 0 | 20 | 一致（1 failure 为 pre-existing） |
| SEQ | — | — | — | — | 一致 |

**结论**：全部失败用例均为 pre-existing（与 R4 基线一致），R5 修复未引入任何新退化。

## 7. 残留不一致数

| 指标 | R4 基线 | R5 修复后 |
|---|---|---|
| 一致函数数 | 141 | 141（无退化） |
| 不一致函数数 | 9 | 9 |
| 成功率 | 94.00% | 94.00% |
| compile_ok | True | True |
| `fill_minute_or_day_blank` diff | -42 | **-30（部分改善）** |

R5 修复后 9 个不一致函数与 R4 一致：`<module>`, `one_prod_to_dataframe`, `fill_minute_or_day_blank`(部分改善), `build_future_fill_time`, `load_bars_from_hundsun`, `load_get_price`, `get_str_data`, `change_his_to_backward`, `get_date_and_count`。

## 8. 反模式自检

- `core/cfg/` 下无新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法 ✓
- 无新增硬编码深度上限 ✓
- 无跨区域跨层次启发式规则（修复仅清除标志，不引入新启发式） ✓
- 未修改 `core/cfg/` 下其他文件（仅 region_ast_generator.py L8849-8853） ✓

## 9. 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator" → COMPILE OK
```

## 10. R6 修复建议

1. **`fill_minute_or_day_blank` 杂散字符串**：修复 `source_end[8:] or '1530'` 表达式重建错误，消除杂散的 `"""1530"""` 字符串字面量。BoolOp 归约应将常量分支合并到赋值右侧，而非发射为独立表达式语句。
2. **`fill_minute_or_day_blank` 尾部代码截断**：修复 `pandas.DataFrame` 构造与 `pandas.concat` 合并的尾部代码截断（仍缺 30 条指令）。
3. **目标**：若 R6 完全修复 `fill_minute_or_day_blank`（diff -30→0），一致函数数可提升至 142。
4. **`one_prod_to_dataframe`（+11）**：R4 已分析根因（FOR_LOOP 区域抢占 BoolOp 块 + if/elif vs or 守卫缺失），R6 可继续探索。
5. **`build_future_fill_time`（instr_diff）**：frozenset 版本差异，不可修，接受。

## 11. 产物清单

| 产物 | 路径 |
|---|---|
| 修复报告 | `repair_engineer/fix_report.md`（本文件） |
| 测试工程师反编译报告 | `test_engineer/decompile_report.md` |
| 测试工程师一致性统计 | `test_engineer/bc_results.json` |
| 测试工程师 diff 详情 | `test_engineer/diff_detail.txt` |
| minimal_repros 目录 | `test_engineer/minimal_repros/`（repro_01 ~ repro_10） |

## 12. 结论

R5 修复工程师阶段针对 `fill_minute_or_day_blank` 的 ternary merge block 后续赋值丢失缺陷进行了根因分析与修复。修复点位于 `region_ast_generator.py` `_if_extract_cond_instructions` L8849-8853：首个 STORE_* 跳过后清除 `_cond_block_is_ternary_merge = False`，使后续 STORE_* 走正常 pre_stmt 提取路径。修复依据 No More Gots §3.1 基本块偏序归约原则，对应区域归约原则 2（每块唯一归属）。

回归结果：quotation.pyc 141/150 无退化，`fill_minute_or_day_blank` diff -42→-30（恢复 3 条赋值）；既有区域测试矩阵 0 退化（IF 290 tests 3 pre-existing failures, TERNARY 20 tests 2 pre-existing, BOOLOP 20 tests 1 pre-existing, TRY 20 tests 1 pre-existing, LOOP 20 tests 1 pre-existing，全部与 R4 基线一致）。残留不一致数 9（与 R4 一致，fill_minute_or_day_blank 部分改善）。R6 建议修复 `fill_minute_or_day_blank` 的杂散字符串与尾部代码截断。
