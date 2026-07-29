# 轮 5 测试工程师报告（decompile_report.md）

> 区域归约算法驱动的 quotation.pyc 反编译迭代 — 第 5 轮测试工程师阶段
> 工作目录：`/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_05/test_engineer/`
> 算法约束：区域归约 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）

## 1. 反编译基线

| 指标 | 值 |
|---|---|
| pyc 文件 | `/workspace/quotation.pyc` |
| 反编译产物 | `/tmp/r5_decompiled.py`（只读，禁止修改） |
| 反编译路径 | `decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)`（区域归约路径） |
| compile_ok | True |
| 总函数数 | 150 |
| 一致函数数 | 141 |
| 不一致函数数 | 9 |
| 缺失函数数 | 0 |
| 成功率 | 141/150 = 94.00% |

**与 R4 基线对比**：141/150 = 94.00%，与 R1/R2/R3/R4 基线完全一致，无退化。
R5 修复 `fill_minute_or_day_blank` 的 ternary merge block 赋值丢失缺陷，diff 由 R4 的 -42 改善至 -30（恢复 3 条赋值），但函数仍未完全匹配，一致函数数维持 141。

## 2. quotation.pyc 反编译结果

- 一致函数数：141/150 = 94.00%
- compile_ok：True
- 不一致函数数：9

## 3. 9 个不一致函数清单

| # | 函数 | 状态 | orig_len | new_len | diff | 与 R4 对比 |
|---|---|---|---|---|---|---|
| 1 | `<module>` | len_diff | 1082 | 1023 | -59 | 一致 |
| 2 | `one_prod_to_dataframe` | len_diff | 444 | 455 | +11 | 一致 |
| 3 | `fill_minute_or_day_blank` | len_diff | 241 | 211 | -30 | **改善（-42→-30）** |
| 4 | `build_future_fill_time` | instr_diff | 671 | 671 | 0 | 一致（首 diff @ JUMP_FORWARD target） |
| 5 | `load_bars_from_hundsun` | len_diff | 501 | 327 | -174 | 一致 |
| 6 | `load_get_price` | len_diff | 226 | 201 | -25 | 一致 |
| 7 | `get_str_data` | len_diff | 317 | 269 | -48 | 一致 |
| 8 | `change_his_to_backward` | len_diff | 578 | 522 | -56 | 一致 |
| 9 | `get_date_and_count` | len_diff | 714 | 687 | -27 | 一致 |

**说明**：
- `build_future_fill_time` 为 instr_diff，首处不一致位于 idx=226：ORIG `JUMP_FORWARD 2660` → NEW `JUMP_FORWARD 2586`（5 处 LOAD_CONST tuple→frozenset 版本差异 + 5 处 JUMP_FORWARD 偏移）。
- `fill_minute_or_day_blank` 是 R5 唯一改善项：R4 diff=-42，R5 diff=-30，恢复 12 条指令中的 3 条赋值（source_start / source_end / dts 前置赋值）。

## 4. 缺陷分类

### 4.1 P0-A：ternary merge block 后续赋值丢失（fill_minute_or_day_blank，R5 已部分修复）

**缺陷模式**：`x = a if cond else b`（三元，merge block 含 STORE_FAST）后跟 `y = foo(); z = bar(); if len(z) > 0: ...` —— ternary STORE_* 与 if 条件之间的独立赋值（source_start=, source_end=, dts=）被丢弃。

**指令级证据**：
- ORIG `POP_JUMP_FORWARD_IF_FALSE 1206` → NEW `POP_JUMP_FORWARD_IF_FALSE 1030`（if 分支出口偏移 -176 字节，分支体被截断）
- 尾部 diverge：NEW 缺失 `pandas.DataFrame` 构造、`pandas.concat` 合并等 30 条尾部指令

**算法根因**：`region_ast_generator.py` `_if_extract_cond_instructions` 中 `_cond_block_is_ternary_merge` 标志对 cond_block（TernaryRegion.merge_block）内所有 STORE_* 生效，导致 ternary STORE_* 之后的独立赋值被跳过。

**R5 修复**：首个 STORE_* 跳过后清除 `_cond_block_is_ternary_merge = False`，后续 STORE_* 走正常 pre_stmt 提取路径。diff -42→-30，恢复 3 条赋值。

**覆盖 repro**：repro_01（精确复现）、repro_02（同类多重赋值）、repro_06（杂散字符串残留）

### 4.2 P0-B：for loop 应在 else 内部但被拉到函数体（build_future_fill_time）

**缺陷模式**：
```python
if cond: ...
else:
    if nested_cond: ...
    elif ...: ...
    else: ...
    for item in market_time: ...   # 应在 else 分支内，被拉到函数体顶层
```

**根因**：else 分支内嵌套 if-elif-else 归约后，紧随其后的 for 循环未被纳入 else 分支体，被错误提升到函数体层级。违反原则 3（嵌套即抽象节点）。

**覆盖 repro**：repro_03

### 4.3 P0-C：模块级函数发射顺序错误（`<module>`）

**缺陷模式**：模块级多个函数定义中，反编译器将部分函数发射到原始字节码的 NOP 占位位置，导致函数定义顺序错乱、尾部函数丢失（diff=-59）。

**指令级证据**：FIRST DIFF @ idx=386，ORIG `846 NOP None` → NEW `846 LOAD_CONST (None, None, ...)`；尾部 diverge，NEW 在 idx=1023 处提前结束，丢失 get_trend_data / get_reits_list / check_limit 等尾部函数定义。

**覆盖 repro**：repro_04

### 4.4 P0-D：函数体截断，分支目标过短

涉及 `load_bars_from_hundsun`(-174) / `load_get_price`(-25) / `get_str_data`(-48) / `change_his_to_backward`(-56) / `get_date_and_count`(-27)。

**缺陷模式**：
- if-then 分支内嵌套 if-else，then 分支在嵌套 if 跳转目标处被截断（load_bars_from_hundsun）
- POP_JUMP_FORWARD_IF_FALSE 目标计算过短，elif 链后续分支体截断（load_get_price）
- FOR_ITER 边界提前收敛，循环后 pandas.Panel 构造丢失（get_str_data）
- FOR_ITER 目标过短，循环后数据处理代码丢失（change_his_to_backward）
- 尾部 elif 分支体丢失（get_date_and_count）

**覆盖 repro**：repro_07（load_bars_from_hundsun）、repro_08（load_get_price）、repro_09（get_str_data）、repro_10（change_his_to_backward）

### 4.5 P0-E：额外代码生成（one_prod_to_dataframe +11）

**缺陷模式**：含 for 循环嵌套 if-elif-else 的函数，反编译器在函数尾生成重复的 return 或多余的 DataFrame 构造（diff=+11）。

**指令级证据**：FOR_ITER 目标偏移 +32 字节；尾部多出 BUILD_LIST / LIST_EXTEND / pandas.DataFrame 重复构造。

**覆盖 repro**：repro_05

## 5. minimal_repros 清单（10 个，全部 py_compile 通过）

| # | repro 文件 | 镜像函数 | 复现缺陷 | diff |
|---|---|---|---|---|
| 1 | repro_01.py | fill_minute_or_day_blank | ✓ ternary merge block 后续赋值丢失 | -30 |
| 2 | repro_02.py | fill_minute_or_day_blank 变体 | ✓ 同类多重赋值丢失 | -30 |
| 3 | repro_03.py | build_future_fill_time | ✓ for loop 被拉到函数体 | instr_diff |
| 4 | repro_04.py | `<module>` | ✓ 模块级函数发射顺序错误 | -59 |
| 5 | repro_05.py | one_prod_to_dataframe | ✓ 函数尾多余代码 +11 | +11 |
| 6 | repro_06.py | fill_minute_or_day_blank | ✓ 杂散字符串字面量 | -30 |
| 7 | repro_07.py | load_bars_from_hundsun | ✓ 函数体大幅截断 -174 | -174 |
| 8 | repro_08.py | load_get_price | ✓ if 分支目标过短 -25 | -25 |
| 9 | repro_09.py | get_str_data | ✓ 循环后 Panel 构造丢失 -48 | -48 |
| 10 | repro_10.py | change_his_to_backward | ✓ FOR_ITER 目标过短 -56 | -56 |

**汇总**：
- repro 总数：10（repro_01 ~ repro_10）
- py_compile 通过数：10/10
- 编译失败 repro 数：0
- 覆盖全部 9 个不一致函数的缺陷模式

## 6. 本轮改善与建议

1. **R5 唯一改善**：`fill_minute_or_day_blank` diff -42→-30（ternary merge block 赋值恢复）。
2. **残留**：`fill_minute_or_day_blank` 仍有 -30 差距，含 `"""1530"""` 杂散字符串与尾部 pandas.DataFrame/pandas.concat 截断。
3. **R6 建议**：修复 `fill_minute_or_day_blank` 的杂散字符串（`source_end[8:] or '1530'` 表达式重建错误）和尾部代码截断，有望将一致函数数提升至 142。

## 7. 产物清单

| 产物 | 路径 |
|---|---|
| 反编译脚本 | `test_engineer/decompile_quotation.py` |
| 一致性统计脚本 | `test_engineer/exact_match_stats.py` |
| 一致性统计结果 | `test_engineer/bc_results.json` |
| diff 详情脚本 | `test_engineer/diff_detail.py` |
| diff 详情结果 | `test_engineer/diff_detail.txt` |
| 精细分析脚本 | `test_engineer/_build_future_deep.py` |
| minimal_repros 目录 | `test_engineer/minimal_repros/`（repro_01 ~ repro_10） |
| 反编译报告 | `test_engineer/decompile_report.md`（本文件） |
