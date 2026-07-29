# Round 1 测试工程师反编译报告

> 区域归约算法驱动的 quotation.pyc 反编译迭代 — 第 1 轮测试阶段
> 工作目录：`/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_01/test_engineer/`
> 反编译路径：`decompile_pyc(pyc, use_cfg=False, cfg_hybrid=False)`（内部 `use_region=True`，调用 `core/cfg/region_analyzer.py` 的 11 个 `_identify_*_regions` 方法）

## 1. 总体结果

| 指标 | 值 |
|---|---|
| pyc 文件 | `/workspace/quotation.pyc`（Python 3.11） |
| 反编译产物 | `/tmp/r1_decompiled.py`（只读，chmod 444） |
| 反编译耗时 | 1.52 秒 |
| 产物长度 | 174015 字符 / 3625 行 |
| **compile_ok** | **True** |
| 总函数数（含 `<module>` / listcomp / lambda） | **150** |
| **一致函数数** | **141** |
| 不一致函数数 | 9 |
| 缺失函数数 | 0 |
| **成功率** | **94.00%** |

**基线复现确认**：本轮结果与预备阶段基线完全一致（total=150, matched=141, mismatched=9, missing=0, success_rate=94.00%, compile_ok=True）。9 个不一致函数及各自 diff 数值均与 `baseline/baseline_diff.json` 一致。

产物文件清单：
- `decompile_quotation.py` — 反编译脚本
- `exact_match_stats.py` — 字节码一致性统计脚本
- `diff_detail.py` — 按函数输出不一致指令 diff 脚本
- `bc_results.json` — 字节码一致性统计结果（150 函数逐条状态）
- `diff_detail.txt` — 9 个不一致函数的完整指令 diff（93957 字符 / 824 行）
- `minimal_repros/` — 15 个最小复现实例（10 个复现缺陷）
- `minimal_repros/repro_verify_summary.txt` — repro 验证摘要
- `minimal_repros/repro_verify_summary.json` — repro 验证结果（机器可读）
- `_orig_funcs_dump.txt` — 9 个不一致函数原始字节码 dump（辅助分析）

## 2. 9 个不一致函数清单与 diff 摘要

下表按"丢失/多余指令数"排序。`len_diff` 表示指令数不一致；`instr_diff` 表示指令数一致但某条指令的 argval（含跳转目标）不同。

| # | 函数名 | 状态 | orig→new | 差值 | 首处不一致位置 | 缺陷分类 |
|---|---|---|---|---|---|---|
| 1 | `load_bars_from_hundsun` | len_diff | 501→351 | -150 | idx=17 `POP_JUMP_FORWARD_IF_FALSE 1120→540`（if 分支目标过早收敛） | Conditional（长 if/elif 链 + BoolOp or 链折叠） |
| 2 | `<module>` | len_diff | 1082→1023 | -59 | idx=386 `NOP None` vs `LOAD_CONST`（模块级连续函数定义丢失） | Sequence / Module-level |
| 3 | `change_his_to_backward` | len_diff | 578→522 | -56 | idx=276 `FOR_ITER 2594→2294`（for 循环体边界提前） | Loop（for 复杂体 + 尾部 if/None） |
| 4 | `fill_minute_or_day_blank` | len_diff | 241→187 | -54 | idx=4 `POP_JUMP_FORWARD_IF_FALSE 1206→946`（if/else 的 else 分支丢失） | Conditional（else 分支 + Ternary/BoolOp 混合） |
| 5 | `get_str_data` | len_diff | 317→264 | -53 | idx=9 `FOR_ITER 1546→1214`（for 循环体 + 循环后 Panel 构造丢失） | Loop（for + 嵌套 for + 循环后语句） |
| 6 | `get_date_and_count` | len_diff | 714→687 | -27 | idx=140 `JUMP_FORWARD 3046→2946`（尾部 elif 分支丢失） | Conditional（if/elif 尾部算术分支） |
| 7 | `load_get_price` | len_diff | 226→207 | -19 | idx=50 `POP_JUMP_FORWARD_IF_FALSE 500→346`（if 内嵌 or 链 + 尾部 isinstance 丢失） | Conditional + BoolOp（长 or 链） |
| 8 | `one_prod_to_dataframe` | len_diff | 444→455 | **+11** | idx=97 `FOR_ITER 1650→1682`（尾部多出 spurious DataFrame 构造） | Sequence（尾部 spurious 重发） |
| 9 | `build_future_fill_time` | instr_diff | 671→671 | 0 | idx=226 `JUMP_FORWARD 2660→2586`（跳转目标偏移 74 字节，含 listcomp） | Loop/Conditional（嵌套 for + listcomp + 跳转目标计算） |

### 各函数 diff 细节

**`<module>`（-59）**：模块级在 `api_get_financial` 之后丢失 `get_kline`、`get_holiday_online`、`get_reits_list`、`check_limit`、`check_jq_code`、`trans_jq_code`、`get_current_kline_count`、`filter_stock_by_status`、`get_trading_day_by_date`、`get_dominant_contract` 共 10 个函数定义。原始字节码在该位置是 `NOP`（占位），反编译产物直接跳过。

**`one_prod_to_dataframe`（+11）**：尾部多出 `BUILD_LIST / LIST_EXTEND / STORE_FAST 'columns' / LOAD_GLOBAL 'pandas' / LOAD_ATTR 'DataFrame' / ... / RETURN_VALUE` 共 11 条，疑似 `_generate_basic_region` 或 `_generate_block_statements` 在 for 循环后重复发射了尾部 `return pandas.DataFrame(...)` 语句。

**`fill_minute_or_day_blank`（-54）**：`if nowend >= nowstart:` 的 else 分支（含 `numpy.array([numpy.nan] * len(dts))` + `pandas.DataFrame` + `pandas.concat`）整体丢失。else 分支含 `and/or` 混合短路三元表达式 `suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix`，反编译器把三元与前置 `stocks.split('.')` 方法调用合并，产生错误源码。

**`build_future_fill_time`（instr_diff）**：指令数完全相同（671），唯一差异是 `JUMP_FORWARD` 跳转目标 2660→2586（偏移 74 字节）。该函数含 3 个 listcomp 子 code object + 嵌套 for 循环 + if/elif 链，跳转目标计算在 listcomp 归约后未同步更新。

**`load_bars_from_hundsun`（-150）**：函数体严重截断。原始含 `if typet == 6: ...` + `if is_utc == '0' and (typet==1 or typet==2 or ... typet==13):` 长 or 链，每个分支含 `tz_localize('Asia/Shanghai').tz_convert('UTC')` 方法调用链。反编译器把长 or 链折叠为单 `if ...: pass`，丢失全部 tz 转换分支。

**`load_get_price`（-19）**：连续 4 个 `if typet == N: _typet = N; typet = 6` 重赋值语句后，`if len(panel.major_axis) != 0:` 内嵌 `if is_utc == '0' and typet == 1 or ...` 长 or 链，尾部 `isinstance(stocks, str)` 分支丢失。

**`get_str_data`（-53）**：`for stock, stock_df in rdata.items():` 循环体（含嵌套 for + `data.loc[i] = {...}` + `order_data[stock] = data`）+ 循环后 `pandas.Panel(order_data, items=[...])` 构造整体丢失。

**`change_his_to_backward`（-56）**：`for n in indexlist:` 循环体（含 `replace` / `float` / `loc` / `BINARY_SUBSCR` / `append`）+ 循环后 `POP_JUMP_FORWARD_IF_NONE` + 尾部 `tmpdata` 赋值丢失。

**`get_date_and_count`（-27）**：`if candle_period == 7: ... elif candle_period == 8: ...` 链中，尾部 `elif` 分支（含 `str(year) + '0' + str(month) + '01'` 字符串拼接）丢失。

## 3. 缺陷分类汇总（按区域类型）

| 区域类型 | 不一致函数数 | 占比 | 主要缺陷模式 |
|---|---|---|---|
| **Conditional**（if/elif/else） | 5 | 56% | else 分支丢失、长 elif 链截断、尾部 elif 丢失、or 链折叠 |
| **Loop**（for） | 4 | 44% | 循环体截断、循环后语句丢失、嵌套 for 边界错误 |
| **BoolOp**（and/or 短路） | 3 | 33% | 长 or 链折叠为单 if、and/or 混合三元表达式错误归约 |
| **Ternary**（三元） | 2 | 22% | 三元表达式与前置方法调用合并、三元作为函数参数错误 |
| **Sequence**（序列/模块级） | 2 | 22% | 模块级函数定义丢失、尾部 spurious 重发 |
| **TryExcept** | 0 | 0% | （one_prod_to_dataframe 的 try/except 本身未错，错在尾部 Sequence 重发） |
| **With / Match / Assert / ChainedCompare** | 0 | 0% | 无 |

> 注：一个函数可能归入多个区域类型（如 `load_bars_from_hundsun` 同时是 Conditional + BoolOp）。

**核心结论**：94% 的不一致集中在 **Conditional（if/elif/else）** 与 **Loop（for）** 两类区域的归约边界处理，尤其涉及：
1. 长 `elif` 链 / 长 `or` 链的尾部归约
2. for 循环体与循环后语句的边界判定
3. 三元/BoolOp 表达式与周围语句的归约交互

## 4. minimal repro 清单（≥10 个）

共编写 15 个 repro，全部 `py_compile` 通过，其中 **10 个复现缺陷**（反编译后字节码不一致）。验证摘要见 `minimal_repros/repro_verify_summary.txt`。

### 复现缺陷的 repro（10 个）

| 编号 | 文件名 | 复现的缺陷 | 对应原始函数 | 验证结果 |
|---|---|---|---|---|
| 01 | `repro_01_if_else_complex_branch.py` | 三元 + and 短路赋值，else 分支截断 | fill_minute_or_day_blank | total=2 matched=0；`fill_blank` len_diff 88→65 |
| 03 | `repro_03_for_body_truncation.py` | for + 嵌套 for + 循环后构造丢失 | get_str_data | total=2 matched=0；`get_str_data` len_diff 77→74 |
| 04 | `repro_04_nested_for_jump_target.py` | 嵌套 for + listcomp + if/elif 跳转目标 | build_future_fill_time | total=3 matched=0；`build_future_fill_time` listcomp instr_diff |
| 06 | `repro_06_if_reassign_or_chain.py` | 顺序 if 重赋值 + 长 or 链 + 尾部 isinstance 丢失 | load_get_price | total=2 matched=0；`load_get_price` len_diff 107→95 |
| 07 | `repro_07_for_complex_body_tail.py` | for 循环复杂体 + 尾部 if/None 丢失 | change_his_to_backward | total=2 matched=0；instr_diff `STORE_FAST` vs `POP_TOP` |
| 09 | `repro_09_long_elif_method_chain.py` | 长 if/elif + 方法调用链 + or 链折叠 | load_bars_from_hundsun | total=2 matched=0；`convert` len_diff 91→90 |
| 10 | `repro_10_ternary_in_arg.py` | 三元/and/or 作为函数参数错误归约 | fill_minute_or_day_blank | total=2 matched=0；`parse_source` len_diff 78→47 |
| 12 | `repro_12_nested_if_for_break.py` | 嵌套 if + for + break + 尾部 if/else 丢失 | change_his_to_backward | total=2 matched=0；`filter_data` len_diff 35→34 |
| 13 | `repro_13_and_or_short_circuit.py` | and/or 短路 + 字符串切片拼接 | fill_minute_or_day_blank | total=2 matched=0；`parse_endpoints` len_diff 55→39 |
| 14 | `repro_14_for_method_chain_tail_if.py` | for + 方法调用链 + 尾部 if 分支丢失 | get_str_data | total=2 matched=0；`get_str_data` len_diff 90→87 |

### 未复现缺陷的 repro（5 个，仍 py_compile 通过）

| 编号 | 文件名 | 目标缺陷 | 说明 |
|---|---|---|---|
| 02 | `repro_02_long_elif_chain.py` | try/except + for + spurious 尾部 | 反编译匹配（try/except 结构未触发） |
| 05 | `repro_05_module_many_funcs.py` | 模块级函数定义丢失 | 反编译匹配（函数过简未触发） |
| 08 | `repro_08_elif_nested_arithmetic.py` | if/elif + 嵌套算术 | 反编译匹配（算术过简未触发） |
| 11 | `repro_11_for_subscript_assign.py` | for + subscript 赋值 | 反编译匹配（结构过简未触发） |
| 15 | `repro_15_nested_if_for_concat.py` | 嵌套 if + concat | 反编译匹配（结构过简未触发） |

## 5. 给修复工程师的根因建议

### 5.1 优先级 P0：Conditional 区域尾部归约（影响 5 个函数）

**症状**：`load_bars_from_hundsun`(-150)、`fill_minute_or_day_blank`(-54)、`load_get_price`(-19)、`get_date_and_count`(-27) 均表现为 `if/elif/else` 链的尾部或 else 分支在反编译后丢失。

**根因定位**：
- `_identify_conditional_regions`（`core/cfg/region_analyzer.py:10765`）— 检查 `elif` 链 / `else` 分支的尾部 block 是否被正确纳入 then/else 列表。当前疑似在遇到长 `elif` 链（≥4 分支）或 else 分支含复杂表达式时，提前终止归约。
- `_generate_if`（`core/cfg/region_ast_generator.py:7105`）— 检查 else 分支的 block 列表发射是否完整。
- `_generate_elif_else_chain`（`core/cfg/region_ast_generator.py:5701`）— 检查 elif 链的尾部分支处理。

**repro 验证**：repro_01（else 分支截断）、repro_06（尾部 isinstance 丢失）、repro_09（长 elif + 方法链）。

**算法 4 原则对应**：
- 违反"每块唯一归属"——尾部 block 未被任何区域认领，导致丢失。
- 违反"入口引用语义"——else 分支 entry 未被父区域 then/else 列表引用。

### 5.2 优先级 P0：BoolOp 长 or 链归约（影响 3 个函数）

**症状**：`load_bars_from_hundsun`、`load_get_price` 中 `is_utc == '0' and typet == 1 or typet == 2 or ... typet == 13` 长 or 链被折叠为单 `if ...: pass`，丢失所有分支体。

**根因定位**：
- `_identify_boolop_regions`（`core/cfg/region_analyzer.py:15189`）— 检查长 or 链（≥5 个 `==` 比较）的归约是否把整个 BoolOp 误判为单一条件，导致后续 Conditional 区域的 then/else 列表为空。
- `_generate_boolop`（`core/cfg/region_ast_generator.py:20009`）— 检查 BoolOp 节点发射是否保留了短路语义。

**repro 验证**：repro_06、repro_09、repro_13（and/or 短路）。

### 5.3 优先级 P0：Loop 区域循环体边界（影响 4 个函数）

**症状**：`get_str_data`(-53)、`change_his_to_backward`(-56)、`load_bars_from_hundsun`(-150) 的 `FOR_ITER` 目标提前收敛，循环体后半 + 循环后语句丢失。

**根因定位**：
- `_identify_loop_regions`（`core/cfg/region_analyzer.py:2801`）— 检查 `FOR_ITER` 的 loop end 边界判定。当前疑似在循环体含嵌套 for / 复杂 subscript 赋值时，把 loop end 提前。
- `_generate_loop`（`core/cfg/region_ast_generator.py:2776`）— 检查循环体 block 列表 + 循环后语句的发射顺序。
- `_generate_block_statements`（`core/cfg/region_ast_generator.py:27807`）— 检查循环后剩余 block 是否被遗漏。

**repro 验证**：repro_03、repro_07、repro_14。

### 5.4 优先级 P1：Ternary 与周围语句归约交互（影响 2 个函数）

**症状**：`fill_minute_or_day_blank` 中 `suffix = 'T.' + suffix if cond and code[:1] == 'T' else suffix` 三元表达式与前置 `stocks.split('.')` 方法调用合并，产生错误源码。

**根因定位**：
- `_identify_ternary_regions`（`core/cfg/region_analyzer.py:12893`）— 检查三元表达式的 entry block 判定是否侵入了前置语句。
- `_generate_ternary`（`core/cfg/region_ast_generator.py:20985`）— 检查三元节点发射是否误纳入前置 `STORE_FAST`。
- 与 `_identify_boolop_regions` 的交互：三元条件含 `and` 短路时，BoolOp 归约可能把 `and` 的右操作数误并入三元。

**repro 验证**：repro_01、repro_10、repro_13。

### 5.5 优先级 P1：Sequence / 模块级尾部 spurious 重发（影响 2 个函数）

**症状**：`one_prod_to_dataframe`(+11) 尾部多出 11 条 `pandas.DataFrame(...)` 构造指令；`<module>`(-59) 丢失 10 个函数定义。

**根因定位**：
- `_identify_sequence_regions`（`core/cfg/region_analyzer.py:17821`）— 检查模块级 / 函数级尾部 block 的序列归约是否重复发射或遗漏。
- `_generate_basic_region`（`core/cfg/region_ast_generator.py:27734`）— 检查尾部 return 语句是否被重复发射（one_prod_to_dataframe）。
- 模块级：检查 `<module>` 的 Sequence 区域在遇到连续 `MAKE_FUNCTION / STORE_NAME` 时是否提前终止（<module> -59）。

**repro 验证**：repro_05（未复现，需更接近原始的连续 `@decorator + def` 模式触发）。

### 5.6 优先级 P1：嵌套 for + listcomp 跳转目标计算（影响 1 个函数）

**症状**：`build_future_fill_time` 指令数完全相同，唯一差异是 `JUMP_FORWARD` 目标 2660→2586（偏移 74 字节）。该函数含 3 个 listcomp + 嵌套 for + if/elif。

**根因定位**：
- `_identify_loop_regions` 嵌套 for 归约后，父区域 `JUMP_FORWARD` 目标未同步更新。
- listcomp 作为子 code object 归约后，父区域的跳转目标偏移量计算未考虑 listcomp 体积变化。
- 检查 `_generate_if`（`core/cfg/region_ast_generator.py:7105`）的跳转目标重算逻辑。

**repro 验证**：repro_04（listcomp 内 `POP_JUMP_BACKWARD_IF_NONE` → `POP_JUMP_BACKWARD_IF_FALSE`，复现 listcomp 归约差异）。

### 5.7 修复优先级建议

1. **P0-1**：`_identify_conditional_regions` 的 else/elif 尾部归约（覆盖 5 个函数，预计提升 +5~10%）
2. **P0-2**：`_identify_boolop_regions` 长 or 链归约（覆盖 3 个函数，与 P0-1 协同）
3. **P0-3**：`_identify_loop_regions` 循环体边界（覆盖 4 个函数，预计提升 +4~8%）
4. **P1-1**：`_identify_ternary_regions` + `_generate_ternary` 与前置语句交互（覆盖 2 个函数）
5. **P1-2**：`_identify_sequence_regions` 模块级 + 尾部 spurious（覆盖 2 个函数）
6. **P1-3**：嵌套 for + listcomp 跳转目标重算（覆盖 1 个函数，instr_diff 类型）

## 6. 约束遵守声明

- ✅ 所有命令 ≤300 秒（最长命令为反编译 1.52s，远低于上限）
- ✅ `/tmp/r1_decompiled.py` 已 `chmod 444`，未修改反编译产物
- ✅ 未修改 `core/cfg/` 下任何源码（仅分析）
- ✅ 工作目录为 `/workspace`，所有产物写入指定目录
- ✅ 报告用中文撰写
- ✅ 10 个 minimal repro 全部 `py_compile` 通过且验证为字节码不一致
