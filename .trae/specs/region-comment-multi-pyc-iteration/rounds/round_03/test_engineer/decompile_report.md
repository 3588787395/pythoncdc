# R03 反编译验证报告 — IQCommon/api/klinedata.pyc

## 1. 目标 pyc 信息

| 字段 | 值 |
|---|---|
| pyc 路径 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc` |
| 文件大小 | 117633 字节 |
| 函数数 | 45（diff 实测；pyc_index.json 中 function_count=64 为含全部嵌套 code object 的预统计值） |
| Python 版本 | 3.11 |
| 验证轮次 | R03 (rcm-r03) |
| 反编译产物 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedataOK.py` (88495 chars) |

## 2. 反编译 + 字节码 diff 结果

执行命令（使用本轮修复后的工具ing：decompile_status 逻辑 + code-object 身份噪声过滤）：

```bash
python scripts/pyc_batch_verify.py single "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"
```

完整输出：

```
[SINGLE] F:\Downloads\pythoncdc-main\site-packages\IQCommon\api\klinedata.pyc
  OK.py: F:\Downloads\pythoncdc-main\site-packages\IQCommon\api\klinedataOK.py
  source: 88495 chars

字节码 diff 报告:
  decompile_status:   partial
  total_functions:   45
  matched_functions: 23
  match_rate:        51.11%
  missing_in_decomp: []
  extra_in_decomp:   []
  mismatches (22):
    - <dictcomp>: orig=12 decomp=12 jump_diffs=0 true_diffs=1
      first_diff: {'index': 7, 'orig_op': 'LOAD_FAST', 'decomp_op': 'LOAD_FAST', 'orig_arg': 'date', 'decomp_arg': 'idx'}
    - <module>: orig=545 decomp=541 jump_diffs=0 true_diffs=189
      first_diff: {'index': 344, 'orig_op': 'NOP', 'decomp_op': 'LOAD_CONST', 'orig_arg': None, 'decomp_arg': (None, None, False, None, None, None)}
    - _all_bars_of_cache: orig=250 decomp=253 jump_diffs=39 true_diffs=187
      first_diff: {'index': 29, 'orig_op': 'LOAD_CONST', 'decomp_op': 'LOAD_FAST', 'orig_arg': '20050101', 'decomp_arg': 'start_date'}
    - _all_bars_of_range: orig=17 decomp=16 jump_diffs=0 true_diffs=3
      first_diff: {'index': 14, 'orig_op': 'NOP', 'decomp_op': 'LOAD_FAST', 'orig_arg': None, 'decomp_arg': 'data_array'}
    - get_all_real_daily_kline: orig=216 decomp=214 jump_diffs=28 true_diffs=137
      first_diff: {'index': 51, 'orig_op': 'LOAD_GLOBAL', 'decomp_op': 'LOAD_FAST', 'orig_arg': 'len', 'decomp_arg': 'list_data'}
    - get_all_real_minute_kline: orig=305 decomp=306 jump_diffs=37 true_diffs=191
      first_diff: {'index': 82, 'orig_op': 'LOAD_GLOBAL', 'decomp_op': 'LOAD_GLOBAL', 'orig_arg': 'range', 'decomp_arg': 'system_log'}
    - get_history_common: orig=536 decomp=543 jump_diffs=62 true_diffs=367
      first_diff: {'index': 111, 'orig_op': 'POP_JUMP_FORWARD_IF_NOT_NONE', 'decomp_op': 'EXTENDED_ARG', 'orig_arg': 760, 'decomp_arg': 3}
    - get_history_date_and_count_ifalse: orig=468 decomp=460 jump_diffs=47 true_diffs=313
      first_diff: {'index': 99, 'orig_op': 'LOAD_GLOBAL', 'decomp_op': 'LOAD_FAST', 'orig_arg': 'datetime', 'decomp_arg': 'query_date'}
    - get_history_new: orig=352 decomp=262 jump_diffs=9 true_diffs=132
      first_diff: {'index': 65, 'orig_op': 'EXTENDED_ARG', 'decomp_op': 'EXTENDED_ARG', 'orig_arg': 2, 'decomp_arg': 1}
    - get_kline_by_count: orig=478 decomp=478 jump_diffs=80 true_diffs=392
      first_diff: {'index': 2, 'orig_op': 'POP_JUMP_FORWARD_IF_NONE', 'decomp_op': 'EXTENDED_ARG', 'orig_arg': 18, 'decomp_arg': 4}
    - get_kline_by_count_new: orig=650 decomp=640 jump_diffs=125 true_diffs=507
      first_diff: {'index': 14, 'orig_op': 'UNPACK_SEQUENCE', 'decomp_op': 'STORE_FAST', 'orig_arg': 2, 'decomp_arg': 'start_000300'}
    - get_kline_by_date_ndarray: orig=239 decomp=239 jump_diffs=3 true_diffs=0
      first_diff: {'index': 47, 'orig_op': 'POP_JUMP_FORWARD_IF_TRUE', 'decomp_op': 'POP_JUMP_FORWARD_IF_TRUE', 'orig_arg': 656, 'decomp_arg': 308}
    - get_kline_by_date_new: orig=332 decomp=322 jump_diffs=16 true_diffs=43
      first_diff: {'index': 38, 'orig_op': 'POP_JUMP_FORWARD_IF_NONE', 'decomp_op': 'POP_JUMP_FORWARD_IF_NONE', 'orig_arg': 386, 'decomp_arg': 216}
    - get_kline_by_date_one: orig=193 decomp=188 jump_diffs=22 true_diffs=126
      first_diff: {'index': 44, 'orig_op': 'RETURN_VALUE', 'decomp_op': 'POP_TOP', 'orig_arg': None, 'decomp_arg': None}
    - get_multiminute_his_data: orig=535 decomp=439 jump_diffs=30 true_diffs=248
      first_diff: {'index': 18, 'orig_op': 'EXTENDED_ARG', 'decomp_op': 'EXTENDED_ARG', 'orig_arg': 5, 'decomp_arg': 3}
    - get_multiminute_his_data_by_date: orig=611 decomp=606 jump_diffs=62 true_diffs=492
      first_diff: {'index': 48, 'orig_op': 'LOAD_FAST', 'decomp_op': 'LOAD_GLOBAL', 'orig_arg': '_1m_df_nan_data', 'decomp_arg': 'get_kline_time_by_asset'}
    - get_pre_date: orig=193 decomp=182 jump_diffs=43 true_diffs=117
      first_diff: {'index': 34, 'orig_op': 'LOAD_GLOBAL', 'decomp_op': 'LOAD_FAST', 'orig_arg': 'len', 'decomp_arg': 'frequency'}
    - get_price_common: orig=594 decomp=605 jump_diffs=94 true_diffs=472
      first_diff: {'index': 28, 'orig_op': 'POP_JUMP_FORWARD_IF_NONE', 'decomp_op': 'LOAD_FAST', 'orig_arg': 174, 'decomp_arg': 'start_date'}
    - klineCacheData_to_dict: orig=216 decomp=137 jump_diffs=22 true_diffs=166
      first_diff: {'index': 30, 'orig_op': 'STORE_FAST', 'decomp_op': 'NOP', 'orig_arg': 'symbol', 'decomp_arg': None}
    - kline_datetime_list: orig=413 decomp=390 jump_diffs=59 true_diffs=208
      first_diff: {'index': 148, 'orig_op': 'SWAP', 'decomp_op': 'COMPARE_OP', 'orig_arg': 2, 'decomp_arg': '>'}
    - np_tp_pd: orig=189 decomp=190 jump_diffs=24 true_diffs=111
      first_diff: {'index': 56, 'orig_op': 'SWAP', 'decomp_op': 'POP_TOP', 'orig_arg': 2, 'decomp_arg': None}
    - to_pd_result: orig=215 decomp=219 jump_diffs=21 true_diffs=161
      first_diff: {'index': 35, 'orig_op': 'POP_JUMP_FORWARD_IF_NOT_NONE', 'decomp_op': 'EXTENDED_ARG', 'orig_arg': 648, 'decomp_arg': 1}
```

> 说明：`scripts/pyc_batch_verify.py single` 仅打印前 10 条 mismatch；上述 22 条全量结果由直接调用 `bytecode_diff()` 并序列化为 `_diff_full.json` 取得（已随报告留存）。`missing_in_decomp` / `extra_in_decomp` 均为空，说明函数集合一致，差异纯为函数体内部字节码。

## 3. 当前 pyc 成功率

| 指标 | 值 |
|---|---|
| 总函数数 | 45 |
| 一致函数数 | 23 |
| 当前 pyc 成功率 | **51.11%** |
| decompile_status | partial |

## 4. 不一致函数清单

按结构模式归类（5 类，共 22 个不一致函数）：

### Pattern A — 控制流区域坍缩（POP_JUMP_\* → EXTENDED_ARG/LOAD_FAST/LOAD_CONST/NOP）

if/elif 条件跳转被替换为非跳转指令（EXTENDED_ARG/LOAD_FAST/LOAD_CONST/NOP），伴随大量 true_diffs 与 jump_diffs；部分函数指令数大幅减少（区域整体丢失）。这是本 pyc 最高发模式。

| 函数名 | orig | decomp | jump_diffs | true_diffs | 首个差异 (index / orig → decomp) |
|---|---|---|---|---|---|
| get_price_common | 594 | 605 | 94 | 472 | 28: POP_JUMP_FORWARD_IF_NONE → LOAD_FAST 'start_date' |
| get_kline_by_count | 478 | 478 | 80 | 392 | 2: POP_JUMP_FORWARD_IF_NONE → EXTENDED_ARG |
| get_history_common | 536 | 543 | 62 | 367 | 111: POP_JUMP_FORWARD_IF_NOT_NONE → EXTENDED_ARG |
| get_multiminute_his_data | 535 | 439 | 30 | 248 | 18: EXTENDED_ARG arg=5 → arg=3 (96 instr lost) |
| get_history_new | 352 | 262 | 9 | 132 | 65: EXTENDED_ARG arg=2 → arg=1 (90 instr lost) |
| `<module>` | 545 | 541 | 0 | 189 | 344: NOP → LOAD_CONST tuple |
| get_kline_by_date_new | 332 | 322 | 16 | 43 | 38: POP_JUMP_FORWARD_IF_NONE arg=386 → arg=216 |
| to_pd_result | 215 | 219 | 21 | 161 | 35: POP_JUMP_FORWARD_IF_NOT_NONE → EXTENDED_ARG |
| _all_bars_of_range | 17 | 16 | 0 | 3 | 14: NOP → LOAD_FAST 'data_array' |

### Pattern B — 变量作用域/名字解析错误（LOAD_GLOBAL ↔ LOAD_FAST / 名字错配）

builtin/global 名字被解析为 LOAD_FAST（局部），或局部变量被解析为 LOAD_GLOBAL，或取了无关 global 名字。

| 函数名 | orig | decomp | jump_diffs | true_diffs | 首个差异 (index / orig → decomp) |
|---|---|---|---|---|---|
| get_multiminute_his_data_by_date | 611 | 606 | 62 | 492 | 48: LOAD_FAST '_1m_df_nan_data' → LOAD_GLOBAL 'get_kline_time_by_asset' |
| get_history_date_and_count_ifalse | 468 | 460 | 47 | 313 | 99: LOAD_GLOBAL 'datetime' → LOAD_FAST 'query_date' |
| _all_bars_of_cache | 250 | 253 | 39 | 187 | 29: LOAD_CONST '20050101' → LOAD_FAST 'start_date' |
| get_all_real_minute_kline | 305 | 306 | 37 | 191 | 82: LOAD_GLOBAL 'range' → LOAD_GLOBAL 'system_log' (wrong name) |
| get_all_real_daily_kline | 216 | 214 | 28 | 137 | 51: LOAD_GLOBAL 'len' → LOAD_FAST 'list_data' |
| get_pre_date | 193 | 182 | 43 | 117 | 34: LOAD_GLOBAL 'len' → LOAD_FAST 'frequency' |

### Pattern C — 值/赋值丢失（STORE_FAST→NOP / SWAP→POP_TOP / RETURN_VALUE→POP_TOP / UNPACK_SEQUENCE→STORE_FAST）

赋值目标、元组解包、return 值或 SWAP 操作数被丢弃（→ NOP / POP_TOP / 单 STORE_FAST）。

| 函数名 | orig | decomp | jump_diffs | true_diffs | 首个差异 (index / orig → decomp) |
|---|---|---|---|---|---|
| get_kline_by_count_new | 650 | 640 | 125 | 507 | 14: UNPACK_SEQUENCE 2 → STORE_FAST 'start_000300' |
| kline_datetime_list | 413 | 390 | 59 | 208 | 148: SWAP 2 → COMPARE_OP '>' |
| klineCacheData_to_dict | 216 | 137 | 22 | 166 | 30: STORE_FAST 'symbol' → NOP (79 instr lost) |
| get_kline_by_date_one | 193 | 188 | 22 | 126 | 44: RETURN_VALUE → POP_TOP (**R01 repro_10 残留**) |
| np_tp_pd | 189 | 190 | 24 | 111 | 56: SWAP 2 → POP_TOP |

### Pattern D — 推导式变量名错配（dictcomp key/value 互换）

| 函数名 | orig | decomp | jump_diffs | true_diffs | 首个差异 (index / orig → decomp) |
|---|---|---|---|---|---|
| `<dictcomp>` | 12 | 12 | 0 | 1 | 7: LOAD_FAST 'date' → LOAD_FAST 'idx' (key/value 互换) |

### Pattern E — 跳转目标重编号（仅 jump_diffs，true_diffs=0）

| 函数名 | orig | decomp | jump_diffs | true_diffs | 首个差异 (index / orig → decomp) |
|---|---|---|---|---|---|
| get_kline_by_date_ndarray | 239 | 239 | 3 | 0 | 47: POP_JUMP_FORWARD_IF_TRUE arg=656 → arg=308 (仅跳转目标偏移不同) |

## 5. 累计成功率（跨所有已验证 pyc）

执行命令：`python scripts/pyc_batch_verify.py stats`

```
======================================================================
累计统计:
  total_pyc:             402
  verified_pyc:          16
  ok_pyc:                13
  partial_pyc:           1
  failed_pyc:            2
  total_functions:       236
  matched_functions:     129
  cumulative_match_rate: 54.66%
======================================================================
```

| 指标 | R01 累计 | R02 累计 | R03 累计 |
|---|---|---|---|
| verified_pyc | 1 | 2 | 16 |
| ok_pyc | 0 | 1 | 13 |
| partial_pyc | 0 | 0 | 1 |
| failed_pyc | 0 | 0 | 2 |
| total_functions | 2 | 3 | 236 |
| matched_functions | 0 | 2 | 129 |
| cumulative_match_rate | 0.00% | 66.67% | **54.66%** |

### 与上一轮对比

- **R02 → R03 累计 match rate**：66.67% → 54.66%（−12.01 pp）。
- **下降原因（非回归）**：R02 累计仅基于 2 个极简 `__init__.pyc`（3 个函数），样本过小导致虚高。R03 新增 14 个已验证 pyc（含本目标 klinedata.pyc 及 base_api/check_strategy/gtn_api/wrapper/arg_checker/config/const/api_data/asset_storage 等），函数样本从 3 扩至 236，其中多数为含 try/except + if/elif 复杂结构的真实业务 pyc，暴露了大量 R01 修复未覆盖的缺陷模式（见第 4/7 节）。
- **本 pyc 贡献**：新增 45 个函数（236 中的 45），其中 23 个一致；本 pyc 单 pyc 成功率 51.11% 是当前 partial_pyc 的唯一来源（其余 13 个标 ok 中部分为旧工具ing 误标 status=ok 但 rate<1.0 的陈旧条目，待后续轮次以修复后工具ing 复测校正）。
- **新增 ok_pyc**：本轮未新增真正 100% 一致的 pyc（klinedata 为 partial）。

### 已验证 pyc 明细（last_tested_round=3）

| # | pyc 路径 | 函数数 | match_rate | status | 轮次 |
|---|---|---|---|---|---|
| 1 | `IQCommon/__init__.pyc` | 2 | 1.00 | ok | R03 |
| 2 | `IQCommon/api/__init__.pyc` | 1 | 1.00 | ok | R02 |
| 3 | `IQCommon/api/base_api.pyc` | 2 | 0.50 | ok* | R03 |
| 4 | `IQCommon/api/check_strategy.pyc` | 2 | 0.00 | ok* | R03 |
| 5 | `IQCommon/api/gtn_api.pyc` | 5 | 0.40 | ok* | R03 |
| 6 | `IQCommon/api/klinedata.pyc` | 64 | 0.5111 | **partial** | **R03** |
| 7 | `IQCommon/api/wrapper.pyc` | 4 | 0.00 | ok* | R03 |
| 8 | `IQCommon/arg_checker.pyc` | 49 | 0.7021 | ok* | R03 |
| 9 | `IQCommon/backtest/backtest.pyc` | 2 | 0.00 | failed | R03 |
| 10 | `IQCommon/common/__init__.pyc` | 1 | 1.00 | ok | R03 |
| 11 | `IQCommon/common/config.pyc` | 2 | 0.50 | ok* | R03 |
| 12 | `IQCommon/common/main.pyc` | 34 | 0.00 | failed | R03 |
| 13 | `IQCommon/const.pyc` | 44 | 0.8864 | ok* | R03 |
| 14 | `IQCommon/data/__init__.pyc` | 1 | 1.00 | ok | R03 |
| 15 | `IQCommon/data/api_data.pyc` | 15 | 0.5714 | ok* | R03 |
| 16 | `IQCommon/data/asset_storage.pyc` | 8 | 0.625 | ok* | R03 |

> `ok*` = 旧工具ing 批量跑遗留的 status 误标（rate<1.0 却标 ok），decompile_status 分类逻辑本轮已修复但陈旧条目尚未以新逻辑复跑校正。cumulative_match_rate 按 `round(fc*rate)` 计算，不受 status 误标影响。

## 6. 复现实例清单

验证脚本：`minimal_repros/verify_repros.py`（函数级字节码 diff，已过滤模块级 code-object 身份噪声）。

共构造 14 个最小复现实例，**10/14 触发缺陷（DEFECT-REPRO），4/14 未触发（NO-DEFECT）**：

| # | 实例文件 | 模式 | 对应原 pyc 函数 | 验证结果 | true_diffs / jump_diffs | 首个差异 |
|---|---|---|---|---|---|---|
| 01 | repro_01_dictcomp_keyval_swap | D-推导式 key/value 互换 | `<dictcomp>` | **DEFECT-REPRO** | 1 / 0 | idx 7 LOAD_FAST 'date' → 'idx' |
| 02 | repro_02_module_ifelif_collapse | A-模块级 if/elif 坍缩 | `<module>` | NO-DEFECT | 0 / 0 | — |
| 03 | repro_03_default_const_to_local | B-常量→局部 (if not a>b + elif) | _all_bars_of_cache | **DEFECT-REPRO** | 0 / 1 | idx 4 POP_JUMP arg=78 → 26 |
| 04 | repro_04_global_builtin_to_local | B-全局 builtin→局部 (len) | get_pre_date | NO-DEFECT | 0 / 0 | — |
| 05 | repro_05_wrong_global_name | B-错误全局名 (range) | get_all_real_minute_kline | NO-DEFECT | 0 / 0 | — |
| 06 | repro_06_popjump_none_to_extended_arg | A-None 检查 + try/except + return | get_kline_by_count / get_price_common | **DEFECT-REPRO** | 35 / 6 | idx 1 NOP → LOAD_FAST 'x' |
| 07 | repro_07_return_value_lost_in_conditional | C-return 值丢失 (try/except if/elif) | get_kline_by_date_one (**R01 repro_10 残留**) | **DEFECT-REPRO** | 32 / 11 | idx 5 POP_JUMP arg=60 → 64 |
| 08 | repro_08_tuple_unpack_collapse | C-元组解包坍缩 | get_kline_by_count_new | **DEFECT-REPRO** | 3 / 0 | idx 10 POP_JUMP arg=48 → 62 |
| 09 | repro_09_store_to_nop_assign_lost | C-赋值丢失 (STORE_FAST→NOP) | klineCacheData_to_dict | NO-DEFECT | 0 / 0 | — |
| 10 | repro_10_swap_to_pop_value_dropped | C-SWAP→POP_TOP (元组交换) | np_tp_pd | **DEFECT-REPRO** | 8 / 1 | idx 5 LOAD_FAST 'b' → 'a' |
| 11 | repro_11_chained_compare_collapse | C-链式比较坍缩 (SWAP→COMPARE_OP) | kline_datetime_list | **DEFECT-REPRO** | 16 / 0 | idx 29 LOAD_FAST 'a' → 'd' |
| 12 | repro_12_major_region_loss_extended_arg | A-try 体大区域丢失 (5 分支+return) | get_history_new / get_multiminute_his_data | **DEFECT-REPRO** | 22 / 8 | idx 30 LOAD_FAST 'd' → LOAD_CONST |
| 13 | repro_13_loadfast_to_loadglobal_scope | B-局部→全局 (LOAD_FAST→LOAD_GLOBAL) | get_multiminute_his_data_by_date | **DEFECT-REPRO** | 13 / 5 | idx 20 LOAD_METHOD 'append' → LOAD_FAST 'out' |
| 14 | repro_14_jump_target_renumber | E-跳转目标重编号 | get_kline_by_date_ndarray / _new | **DEFECT-REPRO** | 4 / 0 | idx 2 POP_JUMP arg=22 → 18 |

### R01 残留缺陷在本 pyc 的复现情况

- **R01 repro_10（except return 值丢失 → None）**：**是，已复现**。`get_kline_by_date_one` 在 try 体 if/elif 中 `return history_data`，反编译产物将 RETURN_VALUE 降级为 POP_TOP（first_diff index 44），函数实际返回 None 而非 history_data。repro_07 以最小用例复现该残留（true_diffs=32）。**结论：R01 修复未覆盖 try 体 if/elif 内含 return 的场景。**
- **R01 repro_12（elif BoolOp 链拆分）**：**部分出现**。`get_kline_by_count` / `get_price_common` 的 `if x is None or y is None`（BoolOp `or`）+ elif 链触发 POP_JUMP_FORWARD_IF_NONE → EXTENDED_ARG 坍缩（Pattern A）。这不是 clean 的"BoolOp 链拆分"，而是 BoolOp 条件 + elif + try/except 组合下的区域坍缩；repro_06 复现该组合（true_diffs=35）。

### NO-DEFECT 说明

repro_02/04/05/09 未触发：这些模式在原 pyc 中依赖更大函数体（更多局部变量 / 更长 elif 链 / 特定全局名集合）才暴露；当前最小用例（≤30 行）不足以独立触发，需后续在更大上下文中复现。已保留用例与 NO-DEFECT footer 供后续轮次扩展。

## 7. 缺陷根因分析

按模式指向 `core/cfg/` 下可疑方法（本轮仅分析，不修改——修复由 repair engineer 负责）：

### Pattern A — 控制流区域坍缩（9 函数，最高发）

**现象**：if/elif 条件跳转（POP_JUMP_FORWARD_IF_NONE / _IF_NOT_NONE / _IF_TRUE）被替换为 EXTENDED_ARG / LOAD_FAST / LOAD_CONST / NOP，伴随 jump_diffs 与 true_diffs 双高；get_history_new / get_multiminute_his_data 指令数减少 90+，说明 try 体或 elif 体整体丢失。

**可疑根因方法**：
- `core/cfg/region_analyzer.py:_identify_conditional_regions` (L11035) — if/elif 区域识别在 try/except 上下文或复合 BoolOp 条件下未能正确归属条件块；条件块被 try-region pass 或前置 pass 提前消费，导致 elif 链入口跳转指令丢失。
- `core/cfg/region_ast_generator.py:_generate_elif_else_chain` (L5830) 与 `_generate_if` (L7234) — elif 链生成阶段对已 analyzed 的条件块跳过，未输出跳转指令，回退为 EXTENDED_ARG 占位。
- `core/cfg/exception_handler.py:identify_try_except_simplified` (R01 已定位) — try_body 块归属与 if-region pass 冲突，try 体内 elif 链被吞。

**佐证**：repro_06（None 检查 + try/except + return）与 repro_12（5 分支 + try/except + return）均触发，first_diff 为 NOP→LOAD_FAST / LOAD_FAST→LOAD_CONST，与原 pyc get_price_common / get_history_new 签名一致。

### Pattern B — 变量作用域/名字解析错误（6 函数）

**现象**：builtin/global（`len`/`range`/`datetime`）被发射为 LOAD_FAST（局部），或局部变量被发射为 LOAD_GLOBAL，或取了无关 global 名字（`range`→`system_log`）；常量字面量（`'20050101'`）被发射为 LOAD_FAST。

**可疑根因方法**：
- `core/cfg/region_ast_generator.py` 在 `_generate_if` / `_generate_elif_else_chain` (L7234 / L5830) 内的名字分类逻辑——对条件体内引用的 builtin/global 名字误判为局部（co_varnames），或反之；常量字面量在 `if a < '20050101'` 比较中被误解析为变量引用。
- `core/cfg/code_generator.py` 名字解析（LOAD_GLOBAL vs LOAD_FAST 判定）在 elif 链 + try/except 复合上下文中误分类。

**佐证**：repro_03（`if not a > b:` + `elif a < '20050101'`）触发跳转目标偏移差异；repro_13（局部 `_1m_df_nan_data` 在循环+if 中）触发 LOAD_METHOD→LOAD_FAST。

### Pattern C — 值/赋值丢失（5 函数，含 R01 残留）

**现象**：STORE_FAST→NOP（赋值目标丢失）、SWAP→POP_TOP（交换操作数丢弃）、RETURN_VALUE→POP_TOP（return 值丢失）、UNPACK_SEQUENCE→STORE_FAST（元组解包仅存一目标）。

**可疑根因方法**：
- `core/cfg/region_ast_generator.py:_generate_return_ast` (L32944) — try/except if/elif 内 return 值未正确发射（RETURN_VALUE 降级为 POP_TOP），即 R01 repro_10 残留。
- `core/cfg/region_ast_generator.py:_generate_try_body` (L14601) — try 体内赋值/元组解包语句在块被标记 analyzed 后跳过，STORE_FAST 退化为 NOP，UNPACK_SEQUENCE 退化为单 STORE_FAST。
- `core/cfg/exception_handler.py` try_body 块归属（同 Pattern A）。

**佐证**：repro_07（return 值丢失，true_diffs=32）、repro_08（元组解包坍缩）、repro_10（SWAP→POP_TOP）、repro_11（链式比较 SWAP→COMPARE_OP）均触发。

### Pattern D — 推导式 key/value 互换（1 函数）

**现象**：`{date: idx for idx, date in pairs}` 反编译为 `{idx: idx ...}`，key/value 互换，first_diff index 7 LOAD_FAST 'date' → 'idx'。

**可疑根因方法**：
- `core/cfg/comprehension_generator.py` — dict comprehension 生成阶段 key/value 表达式顺序错配，MAP_ADD 前两个 LOAD_FAST 取了同一迭代变量。

**佐证**：repro_01 以纯推导式最小用例 1:1 复现（true_diffs=1，first_diff 与原 pyc 完全一致）。

### Pattern E — 跳转目标重编号（1 函数）

**现象**：`get_kline_by_date_ndarray` true_diffs=0、仅 jump_diffs=3，POP_JUMP_FORWARD_IF_TRUE 操作码一致但跳转目标偏移不同（656 → 308）。

**可疑根因方法**：
- `core/cfg/region_ast_generator.py:_generate_if` / `_generate_elif_else_chain` (L7234 / L5830) — 跳转目标偏移计算在条件块指令数变化后未同步重算，或区域边界 NOP 插入/删除导致后续跳转目标漂移。

**佐证**：repro_14（复合 None 检查 + 嵌套 if + return）触发 POP_JUMP arg=22 → 18（true_diffs=4）。

## 8. 产物清单

| 产物 | 路径 |
|---|---|
| 本报告 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_03/test_engineer/decompile_report.md` |
| 验证脚本 | `.trae/specs/.../round_03/test_engineer/minimal_repros/verify_repros.py` |
| 复现实例 01-14 | `.trae/specs/.../round_03/test_engineer/minimal_repros/repro_01_*.py` … `repro_14_*.py` |
| 全量 diff JSON（佐证） | `.trae/specs/.../round_03/test_engineer/_diff_full.json` |
| 验证原始输出（佐证） | `.trae/specs/.../round_03/test_engineer/_verify_repros_out3.txt` |
| 反编译 OK.py（已存在，未修改） | `site-packages/IQCommon/api/klinedataOK.py` |

## 9. pyc_index.json 更新

`scripts/pyc_batch_verify.py single` 已自动回写 klinedata.pyc 条目：
`decompile_status=partial` / `bytecode_match_rate=0.5111` / `ok_py_generated=true` / `last_tested_round=3`。
本 pyc 未达 100%，未升级为 ok。未手工修改 pyc_index.json。

## 10. 约束遵守

- 未修改 `core/cfg/*` 任何代码（修复由 repair engineer 负责）。
- 未修改任何 `+OK.py` 文件（klinedataOK.py 由 single 命令生成，未手工编辑）。
- 未修改 pyc_index.json 超出 single 命令自动回写范围。
- 未执行 git commit。
- 所有命令均在预算内（single ≤60s，stats/repro 验证 ≤60s）。
- 14 个 repro 均 ≤30 行、自包含、无业务逻辑/领域知识。
- 算法约束（bottom-up / 唯一块归属 / nested=abstract / parent refs child）未触碰——本轮为测试角色，仅产出证据与根因定位。
