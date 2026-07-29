# Round 4 测试工程师报告（decompile_report.md）

> 区域归约算法驱动的 quotation.pyc 反编译迭代 — 第 4 轮测试工程师阶段
> 工作目录：`/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_04/test_engineer/`
> 算法约束：区域归约 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）

## 1. 反编译基线

| 指标 | 值 |
|---|---|
| pyc 文件 | `/workspace/quotation.pyc` |
| 反编译产物 | `/tmp/r4_decompiled.py`（只读，禁止修改） |
| 反编译路径 | `decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)`（区域归约路径） |
| compile_ok | True |
| 总函数数 | 150 |
| 一致函数数 | 141 |
| 不一致函数数 | 9 |
| 缺失函数数 | 0 |
| 成功率 | 94.00% |

**与 R3 基线对比**：141/150 = 94.00%，与 R1/R2/R3 基线完全一致，无退化。

## 2. 9 个不一致函数清单（按接近匹配程度排序）

| # | 函数 | 状态 | orig_len | new_len | diff | 根因 | 可修复性 |
|---|---|---|---|---|---|---|---|
| 1 | `one_prod_to_dataframe` | len_diff | 444 | 455 | +11 | `if i == 0 and len(v) == N:` elif 链分裂为两个 if 结构 | 中（高风险） |
| 2 | `build_future_fill_time` | instr_diff | 671 | 671 | 0 | 5 处 LOAD_CONST tuple→frozenset（版本差异）+ 5 处 JUMP_FORWARD 偏移 | **不可修** |
| 3 | `get_date_and_count` | len_diff | 714 | 687 | -27 | 尾部 elif 分支体（`str(year)+str(month)+'01'`）丢失 | 低 |
| 4 | `load_get_price` | len_diff | 226 | 201 | -25 | 长 or 链 + 前导嵌套 if，R3 修复未触达 | 低 |
| 5 | `fill_minute_or_day_blank` | len_diff | 241 | 199 | -42 | else 分支（numpy.array + pandas.concat）丢失 | 低 |
| 6 | `get_str_data` | len_diff | 317 | 269 | -48 | 循环后 `pandas.Panel(...)` 构造边界丢失 | 低 |
| 7 | `change_his_to_backward` | len_diff | 578 | 522 | -56 | FOR_ITER 边界提前收敛 + 循环后 if/None 丢失 | 低 |
| 8 | `<module>` | len_diff | 1082 | 1023 | -59 | 模块级 NOP 占位区段后 10 个函数定义丢失 | 低 |
| 9 | `load_bars_from_hundsun` | len_diff | 501 | 327 | -174 | 长 or 链 + try/except + `if len(data)>0` 包裹层 | 低 |

## 3. 缺陷分类

### 3.1 P0-A：`one_prod_to_dataframe` elif 链分裂（+11，最易 +1 候选）

**缺陷模式**：`if i == 0 and len(v) == N:` 复合条件 elif 链被拆分为两个独立 if 结构。

**指令级证据**：
- 首处分歧 idx=97：`FOR_ITER 1650` → `FOR_ITER 1682`（跳转目标偏移 +32 字节，由 11 条多余指令导致）
- 关键分歧 idx=231：`POP_JUMP_FORWARD_IF_FALSE 1202`（orig，跳向下一个 elif）→ `POP_JUMP_FORWARD_IF_FALSE 1166`（new，跳过当前 elif 链）
- idx=232：orig `LOAD_GLOBAL len`（开始 `len(v)==11` 条件）→ new `LOAD_FAST index`（直接进入 body，条件丢失）

**反编译产物源码**：
```python
if i == 0:                              # 拆分点 1：外层 if
    if len(v) == 8:                      # 内层 if
        index.append(...)
    elif i == 0 and len(v) == 10:        # 冗余 `i == 0 and`
        index.append(...)
    elif i == 0:                          # 丢失 `len(v) == 11`
        index.append(...)
    elif i == 0:                          # 丢失 `len(v) == 12`
        index.append(...)
    elif i == 0:                          # 丢失 `len(v) == 14`
        index.append(...)
if len(v) == 11:                          # 拆分点 2：第二个 if 链
    pass                                  # body 丢失
elif i == 0 and len(v) == 12:
    pass                                  # body 丢失
elif i == 0 and len(v) == 14:
    pass                                  # body 丢失
```

**算法根因**：`_identify_conditional_regions` 在处理 `A and B` 复合条件的 elif 链时，将 `A`（`i == 0`）提取为外层 if 条件，破坏 elif 链连续性。违反原则 4（入口引用语义）—— elif 链的每个分支条件块应共享同一 exit 入口。

**覆盖 repro**：repro_01（+11，精确复现）、repro_11（+11，精确复现）、repro_13、repro_14

### 3.2 P0-B：`build_future_fill_time` frozenset 版本差异（不可修）

**缺陷模式**：5 处 `LOAD_CONST tuple` → `LOAD_CONST frozenset`，5 处 `JUMP_FORWARD 2660` → `JUMP_FORWARD 2586`。

**根因**：原始 pyc 编译自旧版 Python，集合字面量 `{'14:30:00', ...}` 常量存储为 tuple；Python 3.11.15 编译时存储为 frozenset。这是编译器版本差异，非算法缺陷。JUMP_FORWARD 偏移 74 字节是 frozenset 差异的派生后果（常量索引变化触发不同 EXTENDED_ARG 前缀）。

**结论**：不可通过算法修复。即使反编译器输出与原始源码完全一致的集合字面量，Python 3.11.15 编译器仍会生成 `LOAD_CONST frozenset(...)`。

### 3.3 P1：长 or 链 + 嵌套 if 包裹（load_bars_from_hundsun / load_get_price）

**缺陷模式**：R3 修复的 `_detect_boolop_conditional_chain` and(or-chain) 入口引用语义判定在精简 repro 上有效，但原始函数的 CFG 更复杂（前导嵌套 if + try/except + `if len(data)>0` 包裹层），未触发相同代码路径。

**覆盖 repro**：repro_05（+2，接近匹配）、repro_06（-33）

### 3.4 P2：循环边界 + 循环后构造丢失（change_his / get_str_data / fill_minute）

**缺陷模式**：FOR_ITER 边界提前收敛 + 循环后 `pandas.Panel(...)` / `pandas.concat(...)` 构造丢失。

**覆盖 repro**：repro_08（-3，接近匹配）、repro_15

### 3.5 P3：模块级 NOP 占位（`<module>`）

**缺陷模式**：模块级 NOP 占位区段后 10 个函数定义丢失。原始 pyc 含连续 NOP 指令（可能是字节码对齐或调试信息占位），反编译器未能正确归约。

## 4. minimal_repros 清单（15 个，10 个复现缺陷）

| # | repro 文件 | 镜像函数 | 复现缺陷 | diff |
|---|---|---|---|---|
| 1 | repro_01_one_prod_elif_chain_split.py | one_prod_to_dataframe | ✓ | +11 |
| 2 | repro_02_one_prod_elif_with_outer_if.py | one_prod 变体 | ✓ | -194 |
| 3 | repro_03_build_future_frozenset_set_literal.py | build_future_fill_time | ✗（版本差异需原始 pyc） | 0 |
| 4 | repro_04_get_date_and_count_tail_elif_str_concat.py | get_date_and_count | ✗（简化过度） | 0 |
| 5 | repro_05_load_get_price_long_or_with_nested_if.py | load_get_price | ✓ | +2 |
| 6 | repro_06_load_bars_long_or_try_except_wrapper.py | load_bars_from_hundsun | ✓ | -33 |
| 7 | repro_07_fill_minute_else_numpy_concat.py | fill_minute_or_day_blank | ✗（简化过度） | 0 |
| 8 | repro_08_get_str_data_post_loop_panel_construct.py | get_str_data | ✓ | -3 |
| 9 | repro_09_change_his_for_iter_boundary_post_loop.py | change_his_to_backward | ✗（简化过度） | 0 |
| 10 | repro_10_module_nop_placeholder_func_defs.py | `<module>` | ✗（简化过度） | 0 |
| 11 | repro_11_one_prod_elif_in_elif_time_index.py | one_prod 变体 | ✓ | +11 |
| 12 | repro_12_build_future_listcomp_in_loop_with_set.py | build_future 变体 | ✓ | -16 |
| 13 | repro_13_one_prod_elif_3_branches.py | one_prod 最小化 | ✓ | +11 |
| 14 | repro_14_one_prod_elif_with_str_assign_prefix.py | one_prod 变体 | ✓ | +11 |
| 15 | repro_15_get_str_data_nested_for_post_construct.py | get_str_data 变体 | ✓ | -3 |

**汇总**：
- repro 总数：15
- 复现缺陷 repro 数：10（repro_01/02/05/06/08/11/12/13/14/15）
- 全部匹配 repro 数：5
- 编译失败 repro 数：0

## 5. 本轮修复建议

1. **主攻 `one_prod_to_dataframe`（+11 → 0）**：修复 `_identify_conditional_regions` 的 elif 链识别逻辑，使 `A and B` 复合条件的 elif 链保持整体归约。repro_01/11/13/14 均精确复现 +11 diff，可作为回归测试集。
2. **接受 `build_future_fill_time` 不可修**：frozenset 版本差异。
3. **确保无退化**：修复必须通过既有区域测试矩阵 0 退化 + quotation.pyc 一致数 ≥ 141。
4. **若 one_prod 修复导致退化**：立即回滚，保持 141 无退化，留待 R5。

## 6. 产物清单

| 产物 | 路径 |
|---|---|
| 反编译脚本 | `test_engineer/decompile_quotation.py` |
| 一致性统计脚本 | `test_engineer/exact_match_stats.py` |
| 一致性统计结果 | `test_engineer/bc_results.json` |
| diff 详情脚本 | `test_engineer/diff_detail.py` |
| diff 详情结果 | `test_engineer/diff_detail.txt` |
| 最接近修复分析 | `test_engineer/closest_targets.md` |
| 精细分析脚本 | `test_engineer/_analyze_closest.py` |
| minimal_repros 目录 | `test_engineer/minimal_repros/` |
| repro 验证汇总 | `test_engineer/minimal_repros/repro_verify_summary.txt` |
| repro 验证 JSON | `test_engineer/minimal_repros/repro_verify_summary.json` |
| 反编译报告 | `test_engineer/decompile_report.md`（本文件） |
