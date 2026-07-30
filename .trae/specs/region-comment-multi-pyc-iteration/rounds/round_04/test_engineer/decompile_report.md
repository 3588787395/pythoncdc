# R04 反编译验证报告 — IQCommon/api/klinedata.pyc

## 1. 目标 pyc 信息

| 字段 | 值 |
|---|---|
| pyc 路径 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc` |
| 文件大小 | 117633 字节 |
| 函数数 | 45（diff 实测；pyc_index.json 中 function_count=64 为含全部嵌套 code object 的预统计值） |
| Python 版本 | 3.11 |
| 验证轮次 | R04 (rcm-r04) |
| 反编译产物 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedataOK.py` (88497 chars) |
| 上轮 R03 match_rate | 53.33% (24/45) |
| 本轮 R04 match_rate | **53.33%** (24/45) — 持平 |

## 2. 反编译 + 字节码 diff 结果

本轮目标：在 R03 修复（Pattern D dictcomp key/value 互换）基础上，针对 R03 残留的最高发模式 **Pattern A（控制流区域坍缩，9 函数）** 进行修复验证。修复工程师已在 `core/cfg/region_analyzer.py` 实现 `_get_enclosing_structural_boundary_stop` 方法（结构边界回退解析器），针对 BoolOp 条件 + try-body if 的坍缩子模式。

执行命令：

```bash
python scripts/pyc_batch_verify.py single "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"
```

完整输出（前 10 条 mismatch，与 R03 完全相同的 21 条）：

```
[SINGLE] F:\Downloads\pythoncdc-main\site-packages\IQCommon\api\klinedata.pyc
  OK.py: F:\Downloads\pythoncdc-main\site-packages\IQCommon\api\klinedataOK.py
  source: 88497 chars

字节码 diff 报告:
  decompile_status:   partial
  total_functions:   45
  matched_functions: 24
  match_rate:        53.33%
  missing_in_decomp: []
  extra_in_decomp:   []
  mismatches (21):
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
```

> 说明：`scripts/pyc_batch_verify.py single` 仅打印前 10 条 mismatch；21 条全量结果与 R03 完全一致（同一份 mismatch 清单，无新增无消失）。`missing_in_decomp` / `extra_in_decomp` 均为空，函数集合一致。

## 3. 当前 pyc 成功率

| 指标 | R03 | R04 | 变化 |
|---|---|---|---|
| 总函数数 | 45 | 45 | — |
| 一致函数数 | 24 | 24 | — |
| 当前 pyc 成功率 | 53.33% | **53.33%** | 持平 |
| decompile_status | partial | partial | — |
| mismatch 函数数 | 21 | 21 | — |

**结论**：本轮 Pattern A 修复在最小复现实例层验证有效（4/5 Pattern A repro 修复），但在 klinedata.pyc 实际函数层 match_rate 持平。根因分析见第 7 节：实际函数的 Pattern A 子模式与最小 repro 不同。

## 4. 不一致函数清单（21 个，与 R03 完全一致）

按结构模式归类（5 类）。**本轮未新增/未消除任何 mismatch**，清单与 R03 一致：

### Pattern A — 控制流区域坍缩（9 函数，最高发，本轮目标）

if/elif 条件跳转被替换为 EXTENDED_ARG / LOAD_FAST / LOAD_CONST / NOP，伴随 jump_diffs 与 true_diffs 双高。

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

### Pattern B — 变量作用域/名字解析错误（6 函数，未修复）

| 函数名 | true_diffs | 首个差异 |
|---|---|---|
| get_multiminute_his_data_by_date | 492 | 48: LOAD_FAST '_1m_df_nan_data' → LOAD_GLOBAL 'get_kline_time_by_asset' |
| get_history_date_and_count_ifalse | 313 | 99: LOAD_GLOBAL 'datetime' → LOAD_FAST 'query_date' |
| _all_bars_of_cache | 187 | 29: LOAD_CONST '20050101' → LOAD_FAST 'start_date' |
| get_all_real_minute_kline | 191 | 82: LOAD_GLOBAL 'range' → LOAD_GLOBAL 'system_log' (wrong name) |
| get_all_real_daily_kline | 137 | 51: LOAD_GLOBAL 'len' → LOAD_FAST 'list_data' |
| get_pre_date | 117 | 34: LOAD_GLOBAL 'len' → LOAD_FAST 'frequency' |

### Pattern C — 值/赋值丢失（5 函数，未修复）

| 函数名 | true_diffs | 首个差异 |
|---|---|---|
| get_kline_by_count_new | 507 | 14: UNPACK_SEQUENCE 2 → STORE_FAST 'start_000300' |
| kline_datetime_list | 208 | 148: SWAP 2 → COMPARE_OP '>' |
| klineCacheData_to_dict | 166 | 30: STORE_FAST 'symbol' → NOP (79 instr lost) |
| get_kline_by_date_one | 126 | 44: RETURN_VALUE → POP_TOP (**R01 repro_10 残留**) |
| np_tp_pd | 111 | 56: SWAP 2 → POP_TOP |

### Pattern E — 跳转目标重编号（1 函数，未修复）

| 函数名 | jump_diffs | 首个差异 |
|---|---|---|
| get_kline_by_date_ndarray | 3 | 47: POP_JUMP_FORWARD_IF_TRUE arg=656 → arg=308 |

> Pattern D（dictcomp key/value 互换，1 函数）已在 R03 修复，本轮不再出现。

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
  matched_functions:     130
  cumulative_match_rate: 55.08%
======================================================================
```

| 指标 | R01 累计 | R02 累计 | R03 累计 | R04 累计 |
|---|---|---|---|---|
| verified_pyc | 1 | 2 | 16 | 16 |
| ok_pyc | 0 | 1 | 13 | 13 |
| partial_pyc | 0 | 0 | 1 | 1 |
| failed_pyc | 0 | 0 | 2 | 2 |
| total_functions | 2 | 3 | 236 | 236 |
| matched_functions | 0 | 2 | 129 | **130** |
| cumulative_match_rate | 0.00% | 66.67% | 54.66% | **55.08%** |

### 与上一轮对比

- **R03 → R04 累计 match_rate**：54.66% → 55.08%（+0.42 pp，单调递增）。
- **本 pyc 贡献**：klinedata.pyc 持平在 24/45（53.33%），累计 +1 matched 来自其他 pyc 的 stats 复测校正（非本 pyc 修复成果）。
- **本 pyc 状态**：未达 100%，仍为 partial；本轮修复在最小复现实例层有效，但在本 pyc 实际函数层未触发（见第 7 节）。

## 6. 复现实例清单

验证脚本：`minimal_repros/verify_repros.py`（函数级字节码 diff）。

共构造 15 个最小复现实例（5 Pattern A + 1 Pattern D + 4 Pattern C + 1 Pattern B + 1 Pattern E + 3 控制）。**8/15 NO-DEFECT，7/15 DEFECT-REPRO**：

| # | 实例文件 | 模式 | 对应原 pyc 函数 | 验证结果 | true_diffs / jump_diffs | 首个差异 |
|---|---|---|---|---|---|---|
| 01 | repro_01_pattern_a_or_cond_try_elif_collapse | A-BoolOp `or` + try + elif | get_kline_by_count / get_price_common | **NO-DEFECT** ✓ | 0 / 0 | — |
| 02 | repro_02_pattern_a_and_cond_try_collapse | A-BoolOp `and` + try | get_kline_by_count | **NO-DEFECT** ✓ | 0 / 0 | — |
| 03 | repro_03_pattern_a_boolop_cond_mangling | A-BoolOp 条件误编 | get_price_common | **NO-DEFECT** ✓ | 0 / 0 | — |
| 04 | repro_04_pattern_a_popjump_none_to_extended_arg | A-None 检查 `or` + 多 elif + try | get_history_common | **NO-DEFECT** ✓ | 0 / 0 | — |
| 05 | repro_05_pattern_a_major_region_loss | A-5 分支 + return + try (大区域丢失) | get_history_new / get_multiminute_his_data | **DEFECT-REPRO** | 22 / 8 | idx 30 LOAD_FAST 'd' → LOAD_CONST None |
| 06 | repro_06_pattern_d_dictcomp_keyval_swap | D-推导式 key/value 互换 (R03 已修) | `<dictcomp>` | **NO-DEFECT** | 0 / 0 | — |
| 07 | repro_07_pattern_c_return_value_lost | C-return 值丢失 (R01 残留) | get_kline_by_date_one | **DEFECT-REPRO** | 32 / 11 | idx 5 POP_JUMP arg=60 → 64 |
| 08 | repro_08_pattern_c_tuple_unpack_collapse | C-元组解包坍缩 | get_kline_by_count_new | **DEFECT-REPRO** | 3 / 0 | idx 10 POP_JUMP arg=48 → 62 |
| 09 | repro_09_pattern_c_swap_to_pop | C-SWAP→POP_TOP | np_tp_pd | **DEFECT-REPRO** | 8 / 1 | idx 5 LOAD_FAST 'b' → 'a' |
| 10 | repro_10_pattern_c_chained_compare_collapse | C-链式比较坍缩 | kline_datetime_list | **DEFECT-REPRO** | 16 / 0 | idx 29 LOAD_FAST 'a' → 'd' |
| 11 | repro_11_pattern_b_loadfast_to_loadglobal | B-局部→全局 | get_multiminute_his_data_by_date | **DEFECT-REPRO** | 13 / 5 | idx 20 LOAD_METHOD 'append' → LOAD_FAST 'out' |
| 12 | repro_12_pattern_e_jump_target_renumber | E-跳转目标重编号 | get_kline_by_date_ndarray | **DEFECT-REPRO** | 4 / 0 | idx 2 POP_JUMP arg=22 → 18 |
| 13 | repro_13_ctrl_simple_if_in_try | CONTROL-简单 if + try (无 BoolOp) | — | **NO-DEFECT** | 0 / 0 | — |
| 14 | repro_14_ctrl_elif_in_try_simple_cond | CONTROL-elif + try (简单条件) | — | **NO-DEFECT** | 0 / 0 | — |
| 15 | repro_15_ctrl_compound_or_no_try | CONTROL-BoolOp + elif 无 try | — | **NO-DEFECT** | 0 / 0 | — |

### Pattern A 修复验证结果

| repro | 子模式 | 修复前 | 修复后 |
|---|---|---|---|
| repro_01 | `or` BoolOp + try + elif + trailing return (FULL COLLAPSE) | DEFECT-REPRO (true_diffs=29) | **NO-DEFECT** ✓ |
| repro_02 | `and` BoolOp + try | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_03 | BoolOp 条件误编 | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_04 | None 检查 `or` + 多 elif + try | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_05 | 5 分支 + return + try (大区域丢失，**非 BoolOp 触发**) | DEFECT-REPRO | DEFECT-REPRO (残留) |

**4/5 Pattern A repro 修复**。repro_05 残留：触发条件是"5 分支 + return + try"但**无 BoolOp 条件**——这是 Pattern A 的另一个子模式（简单条件 + 多分支 + try-body return 触发的区域丢失），与本轮修复的"BoolOp-in-try-body-if"子模式不同。

### 控制组验证（repro_13/14/15）

3 个控制组实例全部 NO-DEFECT，证实：
- repro_13：简单 if + try（无 BoolOp、无 elif）→ 正确（无坍缩）
- repro_14：elif + try（简单条件）→ 正确（无坍缩）
- repro_15：BoolOp + elif 但无 try → 正确（无坍缩）

这隔离出 Pattern A 的触发条件：**BoolOp 条件 + try/except 上下文**二者同时存在。本轮修复针对该组合有效。

## 7. 缺陷根因分析（本轮新增）

### Pattern A 子模式区分（关键发现）

本轮通过 5 个 Pattern A repro 与 3 个控制组隔离出 **Pattern A 存在至少 2 个不同子模式**：

#### 子模式 A1：BoolOp 条件 + try-body if 坍缩（本轮已修复）

**触发条件**：`try:` 体内含 `if <BoolOp>:` / `elif ...:` + trailing return，且 if 入口块的 `block_to_region` 归属为 BoolOpRegion（表达式区域先于 IfRegion 识别，占用 if 入口块）。

**根因**：BoolOpRegion 继承 base Region.get_if_branch_boundary_stop 返回空集，不提供 try 体边界；`_collect_branch_blocks` 越过 try 体边界，把 try 后的 trailing return / except handler entry 误收集进 elif_final_else / then_blocks，导致 IfRegion 跨越 try 边界、try/except 整体丢失。

**修复**：`_get_enclosing_structural_boundary_stop` 在 boundary_stop 为空时回溯外层 TryExceptRegion/LoopRegion 的边界。

**最小 repro**：repro_01/02/03/04（全部修复为 NO-DEFECT）。

**实际 pyc 对应函数**：get_kline_by_count（部分场景）、get_price_common（部分场景）。

**为何实际 pyc 未提升**：实际函数的 if 条件**并非全部为 BoolOp**。以 `get_kline_by_count` 为例，反编译产物首个差异在 index=2（offset 2），对应 `if asset is None:`（**单条件，非 BoolOp**），其 POP_JUMP_FORWARD_IF_NONE 被替换为 EXTENDED_ARG——这是子模式 A2，非 A1。

#### 子模式 A2：简单条件 + try-body if 坍缩（本轮未修复，残留）

**触发条件**：`try:` 体内含 `if <simple cond>:` + 多分支 + return，if 入口块**不**被 BoolOpRegion 占用（无 BoolOp），但仍发生区域坍缩。

**根因（待定位）**：初步排查——`_collect_branch_blocks` 在 try 体内收集 if 分支时，merge 计算或 boundary_stop 仍存在边界穿透；可能与 `_find_nearest_common_post_dominator` 在 try-body return + trailing return 场景下返回 try 外块作为 merge 有关。需下一轮深入 `_compute_in_loop_if_merge` 与 try-body merge 计算的交互。

**最小 repro**：repro_05（5 分支 + return + try，无 BoolOp，DEFECT-REPRO 残留）。

**实际 pyc 对应函数**：get_kline_by_count（首个差异 offset 2，简单 `is None` 检查）、get_history_common、get_history_new、get_multiminute_his_data、`<module>`、to_pd_result、_all_bars_of_range、get_kline_by_date_new。

**佐证**：对 `get_kline_by_count` 直接 dis 分析：
- 原 pyc offset 2-4：`LOAD_FAST 'asset'; POP_JUMP_FORWARD_IF_NONE 18`（单条件，无 BoolOp）
- 反编译 offset 2-6：`LOAD_FAST 'asset'; EXTENDED_ARG 4; POP_JUMP_FORWARD_IF_NONE 2438`（跳转目标从 18 漂移至 2438，函数末尾）
- try 块覆盖 offset 704-2310（handler @ 2312），首个失败 offset 2 在 try 块**之外**——说明 A2 坍缩不仅影响 try 体，也影响 try 块之前的条件结构（通过 merge/target 漂移传播）。

### 其他模式（B/C/E）根因不变

Pattern B/C/E 的根因分析与 R03 第 7 节一致，本轮未修改相关方法。

## 8. 产物清单

| 产物 | 路径 |
|---|---|
| 本报告 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_04/test_engineer/decompile_report.md` |
| 验证脚本 | `.trae/specs/.../round_04/test_engineer/minimal_repros/verify_repros.py` |
| 复现实例 01-15 | `.trae/specs/.../round_04/test_engineer/minimal_repros/repro_01_*.py` … `repro_15_*.py` |
| 验证原始输出（修复前） | `.trae/specs/.../round_04/test_engineer/_verify_repros_out_pre.txt` |
| 验证原始输出（修复后） | `.trae/specs/.../round_04/test_engineer/_verify_repros_out_post.txt` |
| klinedata 验证原始输出 | `.trae/specs/.../round_04/test_engineer/_klinedata_verify_out.txt` |
| 反编译 OK.py（已存在，未修改） | `site-packages/IQCommon/api/klinedataOK.py` |

## 9. pyc_index.json 更新

`scripts/pyc_batch_verify.py single` 已自动回写 klinedata.pyc 条目：
`decompile_status=partial` / `bytecode_match_rate=0.5333` / `ok_py_generated=true` / `last_tested_round=4`。
本 pyc 未达 100%，未升级为 ok。

## 10. 约束遵守

- 未修改 `core/cfg/*` 任何代码（修复由 repair engineer 负责）。
- 未修改任何 `+OK.py` 文件（klinedataOK.py 由 single 命令生成，未手工编辑）。
- 未修改 pyc_index.json 超出 single 命令自动回写范围。
- 未执行 git commit。
- 所有命令均在预算内（single ≤60s，stats/repro 验证 ≤60s）。
- 15 个 repro 均 ≤30 行、自包含、无业务逻辑/领域知识。
- 算法约束（bottom-up / 唯一块归属 / nested=abstract / parent refs child）未触碰——本轮为测试角色，仅产出证据与根因定位。

## 11. 后续轮次输入

残留 21 个不一致函数（5 类模式），建议后续轮次按以下优先级修复：

1. **Pattern A 子模式 A2（9 函数，最高发，本轮残留）**：简单条件 + try-body if + 多分支 + return 触发的区域坍缩。需深入 `region_analyzer.py:_identify_conditional_regions` 的 merge 计算与 try-body boundary_stop 交互，特别关注 `_find_nearest_common_post_dominator` 在 try-body return + trailing return 场景下返回 try 外块的问题。repro_05 为最小复现。
2. **Pattern C（5 函数）**：含 R01 残留（return 值丢失）。需修复 `region_ast_generator.py:_generate_return_ast` 在 try/except if/elif 内 return 值未正确发射。
3. **Pattern B（6 函数）**：变量作用域/名字解析。
4. **Pattern E（1 函数）**：跳转目标重编号。
