# Round 2 测试工程师反编译报告

> 区域归约算法驱动的 quotation.pyc 反编译迭代 — 第 2 轮测试阶段
> 工作目录：`/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_02/test_engineer/`
> 反编译路径：`decompile_pyc(pyc, use_cfg=False, cfg_hybrid=False)`（内部 `use_region=True`，调用 `core/cfg/region_analyzer.py` 的 11 个 `_identify_*_regions` 方法）
> R1 已修复 `_detect_boolop_conditional_chain`（长 and→or 混合 BoolOp 链首边界）与 `_process_if_blocks`（嵌套 if_skip 不再过早标记 generated_blocks）

## 1. 总体结果

| 指标 | 值 |
|---|---|
| pyc 文件 | `/workspace/quotation.pyc`（Python 3.11） |
| 反编译产物 | `/tmp/r2_decompiled.py`（只读，chmod 444） |
| 反编译耗时 | 1.51 秒 |
| 产物长度 | 174008 字符 / 3628 行 |
| **compile_ok** | **True** |
| 总函数数（含 `<module>` / listcomp / lambda） | **150** |
| **一致函数数** | **141** |
| 不一致函数数 | 9 |
| 缺失函数数 | 0 |
| **成功率** | **94.00%** |

**无退化确认**：本轮 matched=141 与 R1 基线完全一致（R1 commit rr-r01 / 21507b7），9 个不一致函数及其 diff 数值均与 R1 一致，R1 修复未引入任何退化。本轮 9 个不一致函数中 `load_bars_from_hundsun` 已从 R0 的 -150 变为 -174（R1 修复了 if/elif 结构首边界，但内层 or 链分支体仍 pass，结构修正后暴露出更深层的分支体丢失），其余 8 个 diff 数值与 R1 完全相同。

产物文件清单：
- `decompile_quotation.py` — 反编译脚本
- `exact_match_stats.py` — 字节码一致性统计脚本
- `diff_detail.py` — 按函数输出不一致指令 diff 脚本
- `bc_results.json` — 字节码一致性统计结果（150 函数逐条状态）
- `diff_detail.txt` — 9 个不一致函数的完整指令 diff（98097 字符 / 856 行）
- `minimal_repros/` — 21 个最小复现实例（**13 个复现缺陷**）
- `minimal_repros/repro_verify_summary.txt` — repro 验证摘要
- `minimal_repros/repro_verify_summary.json` — repro 验证结果（机器可读）
- `minimal_repros/verify_repro.py` — 单 repro 验证辅助脚本
- `minimal_repros/run_verify_summary.py` — 批量验证脚本

## 2. 9 个不一致函数清单与 diff 摘要

下表按"丢失/多余指令数"排序。`len_diff` 表示指令数不一致；`instr_diff` 表示指令数一致但某条指令的 argval（含跳转目标）不同。

| # | 函数名 | 状态 | orig→new | 差值 | 首处不一致位置 | 缺陷分类 |
|---|---|---|---|---|---|---|
| 1 | `load_bars_from_hundsun` | len_diff | 501→327 | -174 | idx=17 `POP_JUMP_FORWARD_IF_FALSE 1120→540`（if/elif 结构已正确，内层 or 链分支体仍 pass） | Conditional + BoolOp（长 or 链分支体丢失） |
| 2 | `<module>` | len_diff | 1082→1023 | -59 | idx=386 `NOP None` vs `LOAD_CONST`（模块级 NOP 占位区段后 10 个函数定义丢失） | Sequence / Module-level |
| 3 | `change_his_to_backward` | len_diff | 578→522 | -56 | idx=276 `FOR_ITER 2594→2294`（for 循环体边界提前） | Loop（for 复杂体 + 尾部 if/None） |
| 4 | `fill_minute_or_day_blank` | len_diff | 241→187 | -54 | idx=4 `POP_JUMP_FORWARD_IF_FALSE 1206→946`（if/else 的 else 分支丢失 + 三元与前序方法调用合并） | Ternary + Conditional（else 分支 + 三元/BoolOp 混合） |
| 5 | `get_str_data` | len_diff | 317→264 | -53 | idx=9 `FOR_ITER 1546→1214`（for 循环体 + 循环后 Panel 构造丢失） | Loop（for + 嵌套 for + 循环后语句） |
| 6 | `get_date_and_count` | len_diff | 714→687 | -27 | idx=140 `JUMP_FORWARD 3046→2946`（尾部 elif 含 while + if/in + 字符串拼接丢失） | Conditional（尾部 elif 算术/字符串分支） |
| 7 | `load_get_price` | len_diff | 226→201 | -25 | 尾部 `get_str_data` 调用 + `isinstance(stocks, str)` 分支字节码不一致 | Conditional + Sequence（顺序 if 重赋值 + 尾部 isinstance） |
| 8 | `one_prod_to_dataframe` | len_diff | 444→455 | **+11** | idx=97 `FOR_ITER 1650→1682`（尾部多出 spurious `return pandas.DataFrame(...)` 构造） | Sequence（尾部 spurious 重发） |
| 9 | `build_future_fill_time` | instr_diff | 671→671 | 0 | idx=226 `JUMP_FORWARD 2660→2586`（跳转目标偏移 74 字节，含 listcomp） | listcomp + Loop（嵌套 for + listcomp 跳转目标计算） |

### 各函数 diff 细节

**`load_bars_from_hundsun`（-174）**：R1 修复了 if/elif 结构首边界（长 and→or 混合 BoolOp 链），`if typet == 6:` 与 `if isinstance(stocks, str):` 结构已正确识别。但内层 `if is_utc == '0' and (typet==1 or typet==2 or ... typet==13):` 长 or 链的分支体（`panel.major_axis = panel.major_axis.tz_localize('Asia/Shanghai').tz_convert('UTC')` + `elif typet == 6:` 的 `tz_localize(pytz.utc)`）仍被折叠为 pass，尾部 `pandas.concat([retpanel, panel])` 也丢失。ORIG idx=17 跳转目标 1120，NEW 收敛为 540。

**`<module>`（-59）**：模块级在 `api_get_financial` 之后存在 NOP 占位区段（offset 846-858，`check_arg` 装饰器产生的死代码填充），反编译器在 NOP 占位区段处提前终止 Sequence 归约，丢失 `get_kline` / `get_holiday_online` / `get_reits_list` / `check_limit` / `check_jq_code` / `trans_jq_code` / `get_current_kline_count` / `filter_stock_by_status` / `get_trading_day_by_date` / `get_dominant_contract` 共 10 个函数定义。ORIG idx=386 是 `NOP None`，NEW 是 `LOAD_CONST (None,None,...)`。

**`change_his_to_backward`（-56）**：`for n in indexlist:` 的 `FOR_ITER` 目标 2594 被收敛为 2294，循环体尾段（`series.loc[preindex, 'exer_backward_a']` float 算术、`data.loc[predataindex, (fields)] = ... * factor`、`tmpdata.append(data[predataindex:])`）+ 循环后 `POP_JUMP_FORWARD_IF_NONE tmpdata` + `data = tmpdata` 重赋值 + `return data` 丢失，反编译产物提前 `return data`。

**`fill_minute_or_day_blank`（-54）**：`if nowend >= nowstart:` 的 else 分支（含 `numpy.array([numpy.nan] * len(dts))` + `pandas.DataFrame` + `pandas.concat`）整体丢失，`POP_JUMP_FORWARD_IF_FALSE` 目标 1206 收敛为 946。同时三元 `suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix` 与前序 `code = stocks.split('.')[0]` 合并，产生错误源码 `suffix = stocks.split('T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix)`，丢失 `code` 赋值。

**`get_str_data`（-56→-53）**：`for stock, stock_df in rdata.items():` 的 `FOR_ITER` 目标 1546 收敛为 1214。循环体内 `data.loc[i] = {'open':..., 'close':..., ...}`（`BUILD_CONST_KEY_MAP 7` + `STORE_SUBSCR`）被丢弃，反编译产物把该赋值退化为裸表达式（`numpy.nan if ... else stock_df.ix[...]['volume'].sum()`）。循环后 `pandas.Panel(order_data, minor_axis=[...])` 构造在源码层保留但字节码仍少 53 条（subscript 赋值丢失）。

**`get_date_and_count`（-27）**：`elif candle_period == 8:` 分支含 `query_date = datetime.strftime(...)` 重赋值 + 嵌套 `if len(...)==0:` / `elif count==1` / else + `while count > 0:` 循环 + 尾部 `if month in (10,11,12): start_date = str(year)+str(month)+'01' else: start_date = str(year)+'0'+str(month)+'01'`。`JUMP_FORWARD` 3046 收敛为 2946，尾部 if/in 元组判定 + 字符串拼接 + `return (start_date, query_date)` 丢失。

**`load_get_price`（-25）**：连续 4 个 `if typet == N: _typet = N; typet = 6` 重赋值后，`if len(panel.major_axis) != 0:` 内嵌 `is_utc == '0'` / `typet == 1 or ... or typet == 13` 分支，尾部 `if _typet in (7,8,9,15): panel = get_str_data(...)` + `if isinstance(stocks, str): rdata = panel[stocks] else: rdata = panel` + `return rdata`。反编译产物源码层看似完整，但重编译后字节码少 25 条（顺序 if 重赋值 + panel.major_axis 属性赋值的归约产生等价源码但不同字节码布局）。

**`one_prod_to_dataframe`（+11）**：尾部正确 `return pandas.DataFrame(df, columns=columns, index=index)` 之后，反编译器多发出 11 条 spurious 指令：`BUILD_LIST` / `LIST_EXTEND` / `STORE_FAST 'columns'` / `LOAD_GLOBAL 'pandas'` / `LOAD_ATTR 'DataFrame'` / `LOAD_FAST 'df'` / `LOAD_FAST 'columns'` / `LOAD_FAST 'index'` / `KW_NAMES` / `PRECALL 3` / `CALL 3` / `RETURN_VALUE`，即重复发射了尾部 return 语句。`FOR_ITER` 目标 1650→1682（+32 字节）。

**`build_future_fill_time`（instr_diff）**：指令数完全相同（671），唯一差异是 idx=226 `JUMP_FORWARD` 跳转目标 2660→2586（偏移 74 字节）。该函数含 3 个 listcomp 子 code object（`[item.strftime(' %H:%M:%S') for item in trade_times]`）+ 多个 `elif typet == N:` 分支 + 嵌套 for `for today in trade_days: for item in trade_times: total_dts.append(today + item)`。listcomp 归约后父区域跳转目标偏移量未同步更新。

## 3. 缺陷分类汇总（按区域类型）

本轮重点聚焦 R1 未覆盖的 **Loop / Ternary / Sequence / listcomp** 缺陷（R1 已覆盖 BoolOp + 嵌套 if）。

| 区域类型 | 不一致函数数 | 占比 | 主要缺陷模式 |
|---|---|---|---|
| **Loop**（for） | 4 | 44% | `FOR_ITER` 目标提前收敛、循环体内 `data.loc[i]={dict}` STORE_SUBSCR 丢失、循环后语句/构造丢失 |
| **Conditional**（if/elif/else） | 5 | 56% | else 分支丢失、尾部 elif 含 while+if/in 丢失、长 or 链分支体仍 pass |
| **Ternary**（三元） | 1 | 11% | 三元与前序 `stocks.split('.')` 方法调用合并、三元条件含 and 短路误归约 |
| **Sequence**（序列/模块级） | 3 | 33% | 模块级 NOP 占位区段后函数定义丢失、尾部 spurious return 重发、顺序 if 重赋值产生不等价字节码 |
| **listcomp** | 1 | 11% | listcomp 归约后父区域 JUMP_FORWARD 跳转目标偏移 74 字节 |
| **BoolOp**（and/or 短路） | 2 | 22% | 长 or 链分支体折叠为 pass（R1 修了首边界，分支体仍未恢复） |
| **TryExcept / With / Match** | 0 | 0% | 无 |

> 注：一个函数可能归入多个区域类型（如 `load_bars_from_hundsun` 同时是 Conditional + BoolOp，`fill_minute_or_day_blank` 同时是 Ternary + Conditional）。

**核心结论**：R1 修复 BoolOp 链首边界 + 嵌套 if_skip 后，残留缺陷集中在：
1. **Loop 循环体边界**（4 函数）：`FOR_ITER` 目标提前收敛，循环体内 subscript 字典赋值（`BUILD_CONST_KEY_MAP` + `STORE_SUBSCR`）丢失，循环后语句丢失。
2. **Ternary 与前序语句归约交互**（1 函数）：三元表达式侵入前序 `STORE_FAST`/方法调用，丢失前序赋值。
3. **Sequence 尾部 / 模块级**（3 函数）：NOP 占位区段终止归约、尾部 spurious 重发、顺序 if 重赋值字节码不等价。
4. **listcomp 跳转目标重算**（1 函数）：listcomp 归约后父循环 `JUMP_FORWARD` 偏移未同步。
5. **Conditional 尾部分支**（5 函数）：else/elif 尾部含 while+if/in+字符串拼接时丢失。

## 4. minimal repro 清单（≥10 个）

共编写 21 个 repro，全部 `py_compile` 通过，其中 **13 个复现缺陷**（反编译后字节码不一致）。8 个未复现的 repro 文档化为"反编译器在隔离上下文能正确处理"的对照样本。验证摘要见 `minimal_repros/repro_verify_summary.txt`。

### 复现缺陷的 repro（13 个）

| 编号 | 文件名 | 复现的缺陷 | 对应原始函数 | 区域类型 | 验证结果 |
|---|---|---|---|---|---|
| 01 | `repro_01_for_loc_subscr_assign_lost.py` | for 内 `data.loc[i]={dict}`（BUILD_CONST_KEY_MAP+STORE_SUBSCR）丢失 | get_str_data | Loop | total=2 matched=0；`get_str_data` len_diff 106→95 |
| 02 | `repro_02_for_post_loop_panel_construct.py` | for 循环体 + 循环后 `pandas.Panel(...)` 构造边界 | get_str_data | Loop | total=2 matched=0；`get_str_data` len_diff 107→104 |
| 03 | `repro_03_for_iter_target_early.py` | for `FOR_ITER` 目标提前收敛 + 循环后 if/None 丢失 | change_his_to_backward | Loop | total=2 matched=0；`change_his_to_backward` len_diff 98→81 |
| 05 | `repro_05_for_method_chain_append.py` | for 内 replace/float/.loc 方法链 + append 边界 | change_his_to_backward | Loop | total=2 matched=0；len_diff 84→74 |
| 06 | `repro_06_ternary_merged_with_call.py` | 三元与前序 `stocks.split('.')` 方法调用合并 | fill_minute_or_day_blank | Ternary | total=2 matched=0；`fill_blank` len_diff 72→68 |
| 08 | `repro_08_ternary_and_short_circuit.py` | 三元条件含 and 短路 + 切片误归约 | fill_minute_or_day_blank | Ternary | total=2 matched=0；`parse_suffix` len_diff 29→21 |
| 09 | `repro_09_nested_for_listcomp_jump_target.py` | 多 elif + listcomp + 嵌套 for append 跳转目标 | build_future_fill_time | listcomp+Loop | total=3 matched=1；`build_future_fill_time` len_diff 137→139 |
| 15 | `repro_15_long_or_chain_body_pass.py` | 长 or 链 `is_utc=='0' and (typet==1 or ...)` 分支体仍 pass | load_bars_from_hundsun | Conditional+BoolOp | total=2 matched=0；len_diff 94→64 |
| 16 | `repro_16_nested_for_dict_subscr_post_loop.py` | 嵌套 for + 字典 subscript 赋值 + 循环后构造 | get_str_data | Loop | total=3 matched=1；`get_str_data` len_diff 104→92 |
| 17 | `repro_17_ternary_in_dict_method_chain.py` | 三元 + and 短路 + dict 构造 + 方法链 | fill_minute_or_day_blank | Ternary | total=2 matched=0；`fill_blank` len_diff 122→118 |
| 19 | `repro_19_for_while_loc_subscr_append.py` | for + 嵌套 while + .loc subscript + append | change_his_to_backward | Loop | total=2 matched=0；instr_diff `STORE_FAST 'n'` vs `POP_TOP` |
| 20 | `repro_20_ternary_in_return_and_or.py` | 三元作为 return 值 + and/or 短路 | fill_minute_or_day_blank | Ternary | total=2 matched=0；`fill_blank` len_diff 37→34 |
| 21 | `repro_21_for_continue_dict_subscr_assign.py` | for + continue + 字典 subscript 赋值 | get_str_data | Loop | total=3 matched=1；`get_str_data` len_diff 81→69 |

### 未复现缺陷的 repro（8 个，仍 py_compile 通过，作为对照样本）

| 编号 | 文件名 | 目标缺陷 | 说明 |
|---|---|---|---|
| 04 | `repro_04_for_tail_if_none_reassign.py` | for + 尾部 if/None 重赋值 | 反编译匹配（结构过简未触发，需循环体更复杂） |
| 07 | `repro_07_if_else_ternary_branch_lost.py` | if/else + 三元混合 | 反编译匹配（else 分支过简未触发） |
| 10 | `repro_10_for_append_listcomp.py` | for + append + listcomp | 反编译匹配（listcomp 过简未触发跳转目标偏移） |
| 11 | `repro_11_module_func_defs_lost.py` | 模块级函数定义丢失 | 反编译匹配（需 NOP 占位区段 + 大规模函数序列才触发） |
| 12 | `repro_12_tail_spurious_return.py` | 尾部 spurious return 重发 | 反编译匹配（需嵌套 for + try/except 完整上下文） |
| 13 | `repro_13_elif_tail_string_concat.py` | 尾部 elif + while + 字符串拼接 | 反编译匹配（需完整 get_date_and_count 字节码布局） |
| 14 | `repro_14_seq_if_reassign_isinstance_tail.py` | 顺序 if 重赋值 + isinstance 尾部 | 反编译匹配（需 panel.major_axis 属性赋值上下文） |
| 18 | `repro_18_for_elif_append_tail_spurious.py` | for + if/elif + append + 尾部 spurious | 反编译匹配（需 try/except + f-string 完整上下文） |

> **观察**：Sequence/Module（`<module>`、`one_prod_to_dataframe`）与 Conditional 尾部（`get_date_and_count`、`load_get_price`）的缺陷难以用最小 repro 复现——这些缺陷依赖完整函数的字节码布局（NOP 占位区段、精确的跳转偏移、属性赋值上下文）。相反，**Loop 循环体边界** 与 **Ternary 与前序语句交互** 两类缺陷可在 10-40 行内稳定复现（13 个复现 repro 中 Loop 占 7、Ternary 占 4），表明这两类是区域归约算法的系统性边界缺陷，而非布局相关偶发问题。

## 5. 给修复工程师的根因建议

### 5.1 优先级 P0：Loop 循环体边界 + subscript 赋值丢失（影响 4 个函数，7 个 repro 复现）

**症状**：`get_str_data`(-53)、`change_his_to_backward`(-56)、`load_bars_from_hundsun`(-174) 的 `FOR_ITER` 目标提前收敛；循环体内 `data.loc[i] = {'open':..., ...}`（`BUILD_CONST_KEY_MAP` + `STORE_SUBSCR`）被丢弃退化为裸表达式；循环后 `pandas.Panel(...)` 构造 / `POP_JUMP_FORWARD_IF_NONE` 重赋值丢失。

**根因定位**：
- `_identify_loop_regions`（`core/cfg/region_analyzer.py:2801`）— 检查 `FOR_ITER` 的 loop end 边界判定。当前在循环体含嵌套 for / `BUILD_CONST_KEY_MAP`+`STORE_SUBSCR` 字典赋值 / 连续 `.loc` subscript 方法链时，把 loop end 提前收敛（repro_03 `FOR_ITER 2594→2294`、repro_01/repro_21 `STORE_SUBSCR` 丢失）。
- `_generate_loop`（`core/cfg/region_ast_generator.py:2776`）— 检查循环体 block 列表 + 循环后剩余 block 的发射顺序，确认 `STORE_SUBSCR`（`data.loc[i] = {dict}`）未被误判为表达式语句。
- `_generate_block_statements`（`core/cfg/region_ast_generator.py:27843`）— 检查 `BUILD_CONST_KEY_MAP` + `STORE_SUBSCR` 组合是否被正确识别为赋值而非丢弃。

**repro 验证**：repro_01、repro_02、repro_03、repro_05、repro_16、repro_19、repro_21 全部复现（7 个）。

**算法 4 原则对应**：违反"每块唯一归属"——循环体尾段 block 未被 loop 区域认领；违反"入口引用语义"——`STORE_SUBSCR` 的 entry 未被正确归约为赋值目标。

### 5.2 优先级 P0：Ternary 与前序语句归约交互（影响 1 个函数，4 个 repro 复现）

**症状**：`fill_minute_or_day_blank`(-54) 中 `suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix` 三元与前序 `code = stocks.split('.')[0]` 合并，产生 `suffix = stocks.split('T.' + suffix if ...)`，丢失 `code` 赋值；else 分支（numpy.array + pandas.concat）整体丢失。

**根因定位**：
- `_identify_ternary_regions`（`core/cfg/region_analyzer.py:12893`）— 检查三元表达式的 entry block 判定是否侵入了前序 `STORE_FAST 'code'` 语句。当前疑似把前序 `code = stocks.split('.')[0]` 的 `STORE_FAST` 误并入三元的 value 路径。
- `_generate_ternary`（`core/cfg/region_ast_generator.py:21021`）— 检查三元节点发射是否误纳入前置 `STORE_FAST`，导致 `stocks.split(...)` 的参数被替换为三元表达式。
- 与 `_identify_boolop_regions`（`region_analyzer.py:15189`）的交互：三元条件含 `and` 短路时，BoolOp 归约可能把 `and` 的右操作数 `code[:1] == 'T'` 误并入三元，进一步干扰前序 `code` 赋值的归属。

**repro 验证**：repro_06、repro_08、repro_17、repro_20 全部复现（4 个）。

### 5.3 优先级 P0：Conditional 尾部分支 + 长 or 链分支体（影响 5 个函数）

**症状**：
- `load_bars_from_hundsun`(-174)：R1 修复了 if/elif 结构首边界，但内层 `is_utc=='0' and (typet==1 or ... or typet==13)` 长 or 链的分支体（tz_localize/tz_convert）仍 pass。
- `get_date_and_count`(-27)：`elif == 8` 尾部含 while + if/in 元组 + 字符串拼接丢失。
- `fill_minute_or_day_blank`(-54)：else 分支丢失。

**根因定位**：
- `_identify_conditional_regions`（`core/cfg/region_analyzer.py:10765`）— 检查 else/elif 尾部 block 在含 while 循环 + `if x in (tuple)` + 字符串拼接时是否被正确纳入 then/else 列表。
- `_generate_elif_else_chain`（`core/cfg/region_ast_generator.py:5701`）— 检查 elif 链尾部分支（含嵌套 while）的 block 发射完整性。
- `_identify_boolop_regions`（`region_analyzer.py:15189`）— R1 修了长 or 链首边界，但 or 链分支体（then 列表）仍为空，需检查 `_detect_boolop_conditional_chain` 修复后 then block 列表的填充逻辑。

**repro 验证**：repro_15 复现（长 or 链分支体 pass）。`get_date_and_count`/`load_get_price` 尾部缺陷因依赖完整字节码布局未在最小 repro 复现，建议修复工程师直接用 `diff_detail.txt` 中这两个函数的完整指令 diff 验证。

### 5.4 优先级 P1：Sequence 模块级 NOP 占位 + 尾部 spurious 重发（影响 3 个函数）

**症状**：
- `<module>`(-59)：模块级 `check_arg` 装饰器产生的 NOP 占位区段（offset 846-858）后，10 个函数定义丢失。
- `one_prod_to_dataframe`(+11)：尾部正确 return 后多发出 11 条 spurious `return pandas.DataFrame(...)`。
- `load_get_price`(-25)：顺序 if 重赋值 + panel.major_axis 属性赋值产生等价源码但不等价字节码。

**根因定位**：
- `_identify_sequence_regions`（`core/cfg/region_analyzer.py:17863`）— 检查模块级 / 函数级 Sequence 区域在遇到 NOP 占位区段（`check_arg` 装饰器死代码）时是否提前终止（`<module>`）；检查 for 循环后 `return pandas.DataFrame(...)` 是否被重复发射（`one_prod_to_dataframe`）。
- `_generate_basic_region`（`core/cfg/region_ast_generator.py:27770`）— 检查尾部 return 语句是否被重复发射（one_prod_to_dataframe +11）。
- 模块级：检查 `<module>` 的 Sequence 区域在 NOP 占位区段后是否继续归约后续 `MAKE_FUNCTION`/`STORE_NAME` block。

**repro 验证**：repro_11/repro_12/repro_13/repro_14/repro_18 未在最小 repro 复现（需完整字节码布局），建议修复工程师直接用 `diff_detail.txt` 中 `<module>` idx=386 NOP 占位区段 + `one_prod_to_dataframe` 尾部 +11 spurious 验证。

### 5.5 优先级 P1：listcomp + 嵌套 for 跳转目标重算（影响 1 个函数，1 个 repro 复现）

**症状**：`build_future_fill_time` 指令数完全相同（671），唯一差异 idx=226 `JUMP_FORWARD` 2660→2586（偏移 74 字节）。函数含 3 个 listcomp + 多 elif + 嵌套 for append。

**根因定位**：
- `_identify_loop_regions`（`region_analyzer.py:2801`）嵌套 for 归约后，父区域 `JUMP_FORWARD` 目标未同步更新。
- listcomp 作为子 code object 归约后，父区域的跳转目标偏移量计算未考虑 listcomp 体积变化。
- 检查 `_generate_if`（`region_ast_generator.py:7105`）的跳转目标重算逻辑，确认 `if not typet == 5:` 的 `JUMP_FORWARD` 在内层 elif + listcomp 归约后是否重算。

**repro 验证**：repro_09 复现（`build_future_fill_time` len_diff 137→139，listcomp + 嵌套 for append 触发跳转目标偏移）。

### 5.6 修复优先级建议

1. **P0-1**：`_identify_loop_regions` 的 `FOR_ITER` 边界 + `BUILD_CONST_KEY_MAP`+`STORE_SUBSCR` 字典赋值识别（覆盖 4 个函数，7 个 repro 复现，预计提升 +4~8%）
2. **P0-2**：`_identify_ternary_regions` + `_generate_ternary` 与前序 `STORE_FAST`/方法调用交互（覆盖 1 个函数，4 个 repro 复现，预计提升 +1~3%）
3. **P0-3**：`_identify_conditional_regions` 尾部 elif/else 含 while+if/in+字符串拼接 + `_identify_boolop_regions` 长 or 链分支体填充（覆盖 5 个函数）
4. **P1-1**：`_identify_sequence_regions` 模块级 NOP 占位 + 尾部 spurious 重发（覆盖 3 个函数）
5. **P1-2**：listcomp + 嵌套 for `JUMP_FORWARD` 跳转目标重算（覆盖 1 个函数，instr_diff 类型）

**关键提示**：P0-1（Loop）有 7 个稳定复现的最小 repro，是本轮最高 ROI 修复点；P0-2（Ternary）有 4 个稳定复现 repro。建议修复工程师优先用 repro_01/repro_03/repro_06/repro_08 作为回归测试用例。P1 类（Sequence/listcomp）的缺陷依赖完整字节码布局，最小 repro 难以复现，建议直接用 `diff_detail.txt` 的完整指令 diff 验证。

## 6. 约束遵守声明

- ✅ 所有命令 ≤300 秒（最长命令为反编译 1.51s + 批量验证 ~30s，远低于上限）
- ✅ `/tmp/r2_decompiled.py` 已 `chmod 444`，未修改反编译产物
- ✅ 未修改 `core/cfg/` 下任何源码（仅分析）
- ✅ 工作目录为 `/workspace`，所有产物写入指定 round_02/test_engineer 目录
- ✅ 报告用中文撰写
- ✅ 21 个 repro 全部 `py_compile` 通过，其中 13 个复现缺陷（≥10 要求达成）
