# Round 3 测试工程师报告 — quotation.pyc 反编译一致性

> 区域归约算法驱动的 quotation.pyc 反编译迭代 — 第 3 轮测试阶段
> 工作目录：`/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_03/test_engineer/`
> 反编译路径：`decompile_pyc('/workspace/quotation.pyc', use_cfg=False, cfg_hybrid=False)`（区域归约，11 个 `_identify_*_regions`）
> 反编译产物：`/tmp/r3_decompiled.py`（只读，禁止修改）
> 基线：R2 后 141/150 (94%)，9 个不一致函数；本轮复现基线无退化。

## 1. 一致性统计

| 指标 | 值 |
|---|---|
| pyc | `/workspace/quotation.pyc` |
| 反编译产物 | `/tmp/r3_decompiled.py` |
| compile_ok | **True** |
| orig code objects | 150 |
| new code objects | 150 |
| total | 150 |
| **matched** | **141** |
| mismatched | 9 |
| missing | 0 |
| **success_rate** | **94.00%** |

**结论**：141/150 一致，与 R2 基线完全一致，无退化。9 个不一致函数与 R2 相同（清单见 §3）。
统计脚本：`exact_match_stats.py`，结果：`bc_results.json`。

## 2. 9 个不一致函数 diff 摘要

数据来源：`diff_detail.txt`（每个函数标注首处不一致 + 前后 10 条指令上下文 + 末尾发散区段）。

| # | 函数 | 状态 | orig_len | new_len | diff | 首处不一致 |
|---|---|---|---|---|---|---|
| 1 | `<module>` | len_diff | 1082 | 1023 | -59 | idx=386 orig=`NOP` vs new=`LOAD_CONST (None,×7)`；模块级 NOP 占位区段后尾部 ~9 个函数定义（check_arg 包装）整体丢失 |
| 2 | `one_prod_to_dataframe` | len_diff | 444 | 455 | +11 | idx=97 `FOR_ITER 1650→1682`；尾部 spurious `pandas.DataFrame(df,columns,index)`+RETURN 重发 |
| 3 | `fill_minute_or_day_blank` | len_diff | 241 | 199 | -42 | idx=4 `POP_JUMP_FORWARD_IF_FALSE 1206→1006`；else 分支（numpy.array+DataFrame+concat）丢失 |
| 4 | `build_future_fill_time` | instr_diff | 671 | 671 | 0 | idx=226 `JUMP_FORWARD 2660→2586`（偏移 74 字节）；listcomp 归约后父分支跳转目标不同步 |
| 5 | `load_bars_from_hundsun` | len_diff | 501 | 327 | -174 | idx=17 `POP_JUMP_FORWARD_IF_FALSE 1120→540`；长 or 链 `is_utc=='0' and (typet==1 or ... or typet==13)` 分支体折叠为 pass |
| 6 | `load_get_price` | len_diff | 226 | 201 | -25 | idx=50 `POP_JUMP_FORWARD_IF_FALSE 500→428`；长 or 链 if 条件+分支体折叠，跳过 or 链测试直入体 |
| 7 | `get_str_data` | len_diff | 317 | 269 | -48 | idx=9 `FOR_ITER 1546→1234`；循环后半段+循环后 `pandas.Panel(...)` 构造整体丢失 |
| 8 | `change_his_to_backward` | len_diff | 578 | 522 | -56 | idx=276 `FOR_ITER 2594→2294`；循环体尾段（STORE_SUBSCR+append）+ 循环后 if/None 重赋值丢失 |
| 9 | `get_date_and_count` | len_diff | 714 | 687 | -27 | idx=140 `JUMP_FORWARD 3046→2946`；while 体尾段 if/else 字符串拼接丢失 |

## 3. 缺陷分类（按区域归约算法维度）

### 3.1 Loop 类（FOR_ITER / while 边界提前收敛）— 3 函数
- **`change_his_to_backward` (-56)**：`for n in indexlist:` 的 FOR_ITER 目标 2594 被收敛为 2294（提前 300 字节）。循环体尾段（`data.loc[predataindex, (fields)] = ...` STORE_SUBSCR + `tmpdata.append(...)` + `tmpdata = tmpdata`）与循环后 `if tmpdata is not None: data = tmpdata` 整体丢失。
- **`get_str_data` (-48)**：`for stock, stock_df in rdata.items():` 的 FOR_ITER 目标 1546 被收敛为 1234（提前 312 字节）。循环后半段（`time_index.append` / `order_data[stock] = data`）+ 循环后 `pandas.Panel(order_data, minor_axis=[...])` 构造整体丢失。
- **`get_date_and_count` (-27)**：while 循环 JUMP_FORWARD 3046→2946（提前 100 字节）。while 体尾段 `if/else`（`str(year)+'01'` / `str(year)+'0'+str(month)+'01'` 字符串拼接）整体丢失。

**共性根因**：Loop 区域的循环体结束边界（FOR_ITER jump target / while 退出跳转目标）被提前收敛，导致循环体尾段 + 循环后语句被切掉。涉及 `_identify_loop_regions`（循环体边界判定）与 `_generate_loop`（循环体语句生成）。

### 3.2 BoolOp 类（长 or 链分支体仍 pass）— 2 函数
- **`load_bars_from_hundsun` (-174)**：`if is_utc == '0' and (typet == 1 or typet == 2 or ... or typet == 13):` 长 or 链条件 + `elif typet == 6:` 兜底。or 链 if 分支体（`tz_localize('Asia/Shanghai').tz_convert('UTC')`）折叠为 pass，整个 if/elif 块及其后续 tz 转换逻辑丢失。
- **`load_get_price` (-25)**：`if typet == 1 or typet == 2 or typet == 3 or typet == 4:` 长 or 链 if 条件被折叠，直接跳入 `tz_convert` 体，丢失 or 链测试与 `elif typet in (7,8,9,15):` 分支。

**共性根因**：BoolOp 长 or 链（≥4 个 or 操作数）作为 if 条件时，条件链块归约后分支体入口被误判为空（pass）。涉及 `_identify_boolop_regions`（or 链边界）与 `_identify_conditional_regions` / `_generate_conditional`（分支体入口引用语义）。

### 3.3 listcomp 类（跳转目标偏移）— 1 函数
- **`build_future_fill_time` (instr_diff)**：listcomp `[item.strftime(' %H:%M:%S') for item in trade_times]` 归约后，父分支 `JUMP_FORWARD 2660→2586`（偏移 74 字节）。listcomp 区域归约消耗的指令宽度未同步到父 if/elif 分支的跳转目标计算，导致跳转目标偏移。

**根因**：listcomp 区域作为子抽象节点归约后，父区域跳转目标未按入口引用语义同步。涉及 listcomp 区域识别（`_identify_*_regions` 中 listcomp 分支 / `comprehension_generator`）与父 Conditional 跳转目标计算。

### 3.4 Sequence 类（模块级 NOP 占位）— 1 函数
- **`<module>` (-59)**：模块级存在 NOP 占位区段（offsets 846-858，被剥离函数残留）。反编译器正确折叠 NOP，但其后 ~9 个 check_arg 包装的函数定义（get_trend_data / get_reits_list / check_limit / check_jq_code / trans_jq_code / get_current_kline_count / filter_stock_by_status / get_trading_day_by_date / get_dominant_contract）整体丢失。

**根因**：模块级 Sequence 区域在遇到 NOP 占位区段后，尾部边界被误判，截断了后续函数定义区段。涉及 `_identify_sequence_regions`（模块级序列边界）。

### 3.5 Conditional 类（尾部 spurious / else 分支丢失）— 2 函数
- **`one_prod_to_dataframe` (+11)**：尾部 `if data_type is None: ... else: columns=[...]` + `return pandas.DataFrame(...)` 中，else 分支的 columns 赋值 + return 被重复发射一次（spurious 重发）。
- **`fill_minute_or_day_blank` (-42)**：`POP_JUMP_FORWARD_IF_FALSE 1206→1006`，else 分支（`numpy.array` + `pandas.DataFrame` + `pandas.concat`）整体丢失。R2 已收窄 +12 指令（前序赋值恢复），但 else 分支体仍未恢复。

**根因**：Conditional if/else 分支体入口引用语义在尾部 return / else 场景下未正确归约。涉及 `_identify_conditional_regions`（else 分支边界）与 `_generate_conditional`（尾部 return 发射）。

## 4. minimal_repros 清单（12 个，全部复现缺陷）

验证脚本：`minimal_repros/verify_repro.py` + `run_verify_summary.py`，结果：`minimal_repros/repro_verify_summary.txt` / `.json`。
**12/12 复现缺陷**（编译→反编译→字节码比较，任一 code object 不一致即复现）。

| # | repro 文件 | 覆盖函数 | 缺陷类型 | total/matched | 说明 |
|---|---|---|---|---|---|
| 1 | `repro_01_for_iter_target_early.py` | change_his_to_backward | Loop | 2/0 | FOR_ITER 目标提前收敛 + 循环后 if/None |
| 2 | `repro_02_post_loop_panel_construct.py` | get_str_data | Loop | 2/0 | 循环后 pandas.Panel 构造边界 |
| 3 | `repro_03_long_or_chain_body_pass.py` | load_bars_from_hundsun | BoolOp | 2/0 | 长 or 链分支体仍 pass |
| 4 | `repro_04_long_or_chain_if_and_body.py` | load_get_price | BoolOp | 2/0 | 长 or 链 if-and 分支体折叠 |
| 5 | `repro_05_listcomp_jump_target_nested_for.py` | build_future_fill_time | listcomp | 3/1 | listcomp + 嵌套 for 跳转目标偏移 |
| 6 | `repro_06_long_or_chain_first_cond.py` | load_bars (变体) | BoolOp | 2/0 | 长 or 链作为首条件 |
| 7 | `repro_07_long_or_chain_else_branch.py` | load_bars (变体) | BoolOp | 2/0 | 长 or 链 + else 分支体 |
| 8 | `repro_08_for_iter_while_subscr_post.py` | change_his/get_date | Loop | 2/0 | for+while+STORE_SUBSCR+循环后 if/None |
| 9 | `repro_09_for_loop_body_tail_subscr.py` | change_his (变体) | Loop | 2/0 | 循环体尾段 STORE_SUBSCR+append |
| 10 | `repro_10_long_or_chain_elif_tz.py` | load_bars (变体) | BoolOp | 2/0 | 长 or 链 + elif tz_localize |
| 11 | `repro_11_listcomp_not_guard_two_branch.py` | build_future_fill_time | listcomp | 3/1 | listcomp + `if not` 守卫 + 两分支 |
| 12 | `repro_12_for_loop_tail_post_construct.py` | get_str_data (变体) | Loop | 2/0 | 单层 for 尾段 + 循环后构造 |

> 注：模块级 NOP 占位（`<module>`）与尾部 spurious return（`one_prod_to_dataframe`）的失败模式依赖原始 pyc 的特定结构（NOP 占位区段、复杂 if/else+return 交互），无法用 py_compile 生成的最小 repro 稳定复现，本轮以原始 quotation.pyc 的 diff_detail 为根因证据。

## 5. 给修复工程师的根因建议（定位到 `_identify_*_regions` / `_generate_*` 方法）

按「最大化提升一致函数数且不退化」优先级排序：

### P0-A：FOR_ITER / while 循环体结束边界提前收敛（潜在 +3 函数：change_his_to_backward / get_str_data / get_date_and_count）
- **定位**：`core/cfg/region_analyzer.py` 的 `_identify_loop_regions`（循环体结束边界判定）+ `core/cfg/region_ast_generator.py` 的 `_generate_loop`（循环体语句生成）。
- **现象**：循环体结束边界（FOR_ITER jump target / while 退出跳转）被提前收敛，循环体尾段（STORE_SUBSCR + append + 重赋值）+ 循环后语句（if/None 重赋值、构造器调用）被切掉。
- **算法依据**：原则 ①自底向上归约 —— 循环体应归约到 FOR_ITER jump target 指向的下一条指令（循环出口），而非更早的中间跳转目标；原则 ④入口引用语义 —— 循环体出口由 FOR_ITER 的 jump target 唯一确定，循环后语句入口紧接循环出口。
- **建议**：检查 `_identify_loop_regions` 是否把循环体内的中间跳转目标（如 `JUMP_BACKWARD` 回边、`continue` 跳转）误判为循环体结束。循环体结束应以 FOR_ITER 的 jump target（出口）为准，循环后语句从出口开始归约。
- **覆盖 repro**：repro_01 / 02 / 08 / 09 / 12。

### P0-B：长 or 链分支体仍 pass（潜在 +2 函数：load_bars_from_hundsun / load_get_price）
- **定位**：`core/cfg/region_analyzer.py` 的 `_identify_boolop_regions`（or 链边界）+ `_identify_conditional_regions`（分支体入口）+ `core/cfg/region_ast_generator.py` 的 `_generate_conditional` / `_generate_boolop`。
- **现象**：`if a and (x==1 or x==2 or ... or x==13):` 长 or 链（≥4 个 or 操作数）条件归约后，分支体入口被误判为空（pass），整个 if 分支体丢失。
- **算法依据**：原则 ②每块唯一归属 —— or 链条件块归属 BoolOp 区域，分支体归属 Conditional then 块，两者不混淆；原则 ④入口引用语义 —— Conditional then 入口从 or 链条件链最后一个 `POP_JUMP_FORWARD_IF_FALSE` 之后开始。
- **建议**：检查 `_identify_boolop_regions` 对长 or 链（≥4 操作数）的边界判定是否吞并了 then 块首指令；`_identify_conditional_regions` 的 then 入口应从 BoolOp 链结束后的第一条指令开始。
- **覆盖 repro**：repro_03 / 04 / 06 / 07 / 10。

### P0-C：listcomp 跳转目标偏移（潜在 +1 函数：build_future_fill_time）
- **定位**：listcomp 区域识别（`_identify_*_regions` 中 listcomp 分支 / `comprehension_generator.py`）+ 父 Conditional 跳转目标计算（`_identify_conditional_regions` / `_generate_conditional`）。
- **现象**：listcomp 作为 if 分支首语句归约后，父 if/elif 的 `JUMP_FORWARD` 跳转目标偏移 74 字节（listcomp 区域消耗的指令宽度未同步）。
- **算法依据**：原则 ③嵌套即抽象节点 —— listcomp 作为子抽象节点归约后，父区域将其视为单个节点；原则 ④入口引用语义 —— 父 then/else 引用子 listcomp entry，跳转目标应按归约后宽度同步。
- **建议**：检查 listcomp 区域归约后，父 Conditional 的 JUMP_FORWARD 目标是否按归约后指令宽度重算（而非沿用原始偏移）。
- **覆盖 repro**：repro_05 / 11。

### P1：模块级 NOP 占位 + 尾部 spurious return（依赖原始 pyc 结构，本轮 best-effort）
- **`<module>`**：`_identify_sequence_regions` 模块级序列在 NOP 占位区段后尾部边界误判。
- **`one_prod_to_dataframe`**：`_generate_conditional` 尾部 if/else + return 的 else 分支重复发射。
- **`fill_minute_or_day_blank`**：`_identify_conditional_regions` else 分支（numpy.array+concat）边界。

## 6. 约束遵守声明
- ✅ 反编译走区域归约路径（`use_cfg=False, cfg_hybrid=False`）
- ✅ 所有命令 ≤ 300 秒（最长为 repro 验证 ~30s）
- ✅ 禁止修改 `/tmp/r3_decompiled.py` 及反编译产物
- ✅ 12 个 repro 全部可独立 py_compile 且字节码不一致（12/12 复现缺陷）
- ✅ 一致函数数 141/150 与 R2 基线一致，无退化
