# R12 测试工程师报告 — Pattern A2（try-body if/return collapse，异常边切分）

## 1. 目标 pyc 与轮次

| 字段 | 值 |
|---|---|
| 轮次 | R12 (rcm-r12) |
| 目标 pyc | `site-packages/IQCommon/api/klinedata.pyc`（R04 残留 Pattern A2，`partial` 53.33%） |
| 缺陷模式 | Pattern A2（try-body 内 `if cond: return x / else: return y` 被异常边切分为独立块，区域分析误判为三元值分支） |
| 修复层 | 区域分析层 `core/cfg/region_analyzer.py` + 区域 AST 生成层 `core/cfg/region_ast_generator.py` |
| 累计成功率（R11 末） | 67.05%（pyc_index.json committed，293/437 函数匹配） |

## 2. 反编译产物实证（不一致清单）

### 2a. klinedata.pyc 字节码 diff（21 函数不一致）

`single` 验证结果：`partial` 53.33%（24/45 matched），21 mismatches。

| 函数 | orig | decomp | jump_diffs | true_diffs | first_diff | 模式 |
|---|---|---|---|---|---|---|
| `<module>` | 545 | 541 | 0 | 189 | NOP vs LOAD_CONST | R |
| `_all_bars_of_cache` | 250 | 253 | 39 | 187 | LOAD_CONST '20050101' vs LOAD_FAST 'start_date' | B |
| `_all_bars_of_range` | 17 | 16 | 0 | 3 | NOP vs LOAD_FAST | R |
| `get_all_real_daily_kline` | 216 | 214 | 28 | 137 | LOAD_GLOBAL 'len' vs LOAD_FAST 'list_data' | B |
| `get_all_real_minute_kline` | 305 | 306 | 37 | 191 | LOAD_GLOBAL 'range' vs LOAD_GLOBAL 'system_log' | B |
| `get_history_common` | 536 | 542 | 61 | 365 | POP_JUMP_FWD_IF_NOT_NONE vs EXTENDED_ARG | E |
| `get_history_date_and_count_ifalse` | 468 | 460 | 47 | 313 | LOAD_GLOBAL 'datetime' vs LOAD_FAST 'query_date' | B |
| `get_history_new` | 352 | 262 | 9 | 132 | EXTENDED_ARG 2 vs 1 | E |
| `get_kline_by_count` | 478 | 470 | 81 | 395 | POP_JUMP_FWD_IF_NONE vs EXTENDED_ARG | E |
| `get_kline_by_count_new` | 650 | 638 | 124 | 509 | UNPACK_SEQUENCE 2 vs STORE_FAST | C2 |
| `get_kline_by_date_ndarray` | 239 | 209 | 21 | 103 | LOAD_CONST 'data' vs LOAD_FAST 'count' | B |
| `get_kline_by_date_new` | 332 | 321 | 7 | 29 | POP_JUMP_FWD_IF_NONE 386 vs 216 | E |
| `get_kline_by_date_one` | 193 | 182 | 5 | 24 | LOAD_GLOBAL 'system_log' vs LOAD_FAST 'fields' | B |
| `get_multiminute_his_data` | 535 | 439 | 30 | 248 | EXTENDED_ARG 5 vs 3 | E |
| `get_multiminute_his_data_by_date` | 611 | 606 | 62 | 492 | LOAD_FAST vs LOAD_GLOBAL | B |
| `get_pre_date` | 193 | 182 | 43 | 117 | LOAD_GLOBAL 'len' vs LOAD_FAST 'frequency' | B |
| `get_price_common` | 594 | 605 | 95 | 471 | POP_JUMP_FWD_IF_NONE vs LOAD_FAST | E/B |
| `klineCacheData_to_dict` | 216 | 213 | 17 | 93 | LOAD_FAST 'symbol' vs NOP | B/R |
| `kline_datetime_list` | 413 | 390 | 59 | 208 | SWAP 2 vs COMPARE_OP '>' | C |
| `np_tp_pd` | 189 | 190 | 24 | 111 | SWAP 2 vs POP_TOP | C |
| `to_pd_result` | 215 | 219 | 21 | 161 | POP_JUMP_FWD_IF_NOT_NONE vs EXTENDED_ARG | E |

### 2b. 模式分布

| 模式 | 函数数 | 描述 |
|---|---|---|
| B (scope) | 9 | LOAD_GLOBAL vs LOAD_FAST（变量作用域误判） |
| E (jump renumber) | 7 | EXTENDED_ARG / POP_JUMP arg 不一致（跳转目标重编号） |
| R (NOP padding) | 3 | NOP vs LOAD_CONST/LOAD_FAST（模块级/块级 NOP 填充） |
| C (SWAP/POP) | 2 | SWAP vs COMPARE_OP/POP_TOP（栈操作坍缩） |
| C2 (tuple unpack) | 1 | UNPACK_SEQUENCE vs STORE_FAST（tuple 解包无 SWAP） |

**关键发现**：21 个不一致函数的首差（first_diff）均非 Pattern A2（try-body if/return collapse）。Pattern A2 缺陷存在于 try-body 内部的深层位置，但被更前置的模式 B/E/R/C/C2 缺陷掩盖。修复 Pattern A2 可减少 try-body 内部的 true_diffs，但无法使任何函数达到 100% 一致（因前置缺陷仍存在）。

## 3. 最小复现实例（13 个）

路径：`rounds/round_12/test_engineer/minimal_repros/`

| # | 文件 | 子模式 | pre-fix | post-fix |
|---|---|---|---|---|
| 01 | repro_01_try_if_else_return.py | A2a (try: if/else return) | DEFECT-REPRO (td=14) | NO-DEFECT ✓ |
| 02 | repro_02_try_if_elif_else_return.py | A2b (try: if/elif/else return) | DEFECT-REPRO (td=14) | NO-DEFECT ✓ |
| 03 | repro_03_try_if_elif_elif_else_return.py | A2b (3-branch) | DEFECT-REPRO (td=14) | NO-DEFECT ✓ |
| 04 | repro_04_try_if_return_else_return.py | A2c (if return / else return) | DEFECT-REPRO (td=14) | NO-DEFECT ✓ |
| 05 | repro_05_try_if_return_else_assign.py | A2a variant | NO-DEFECT | NO-DEFECT ✓ |
| 06 | repro_06_try_if_call_else_return.py | A2a (call in if) | NO-DEFECT | NO-DEFECT ✓ |
| 07 | repro_07_try_nested_if_return.py | A2a (nested if) | DEFECT-REPRO (td=15) | NO-DEFECT ✓ |
| 08 | repro_08_try_if_multi_return.py | A2c (multi return) | DEFECT-REPRO (td=15) | NO-DEFECT ✓ |
| 09 | repro_09_try_if_compare_else_return.py | A2a (compare cond) | DEFECT-REPRO (td=14) | NO-DEFECT ✓ |
| 10 | repro_10_ctrl_no_try_if_else_return.py | CTRL (no try) | NO-DEFECT | NO-DEFECT ✓ |
| 11 | repro_11_ctrl_try_if_no_return.py | CTRL (no return) | NO-DEFECT | NO-DEFECT ✓ |
| 12 | repro_12_try_if_assign_return_else.py | A2a (assign+return) | — | NO-DEFECT ✓ |
| 13 | repro_13_try_if_ternary_assign_return.py | A2c (ternary+return) | — | NO-DEFECT ✓ |

**pre-fix**: 7 DEFECT-REPRO / 4 NO-DEFECT（repro 12-13 为 post-fix 新增）
**post-fix**: 0 DEFECT-REPRO / 13 NO-DEFECT

## 4. 缺陷模式分类

### Pattern A2a: Simple condition + try-body if collapse
- **触发条件**: `try: if cond: return a / else: return b / except: ...`
- **根因**: try-body 内 `LOAD_FAST a` + `RETURN_VALUE` 被异常边切分为独立块。LOAD_FAST 块有异常边（到 handler），RETURN_VALUE 块无异常边。区域分析器将 LOAD_FAST 块误判为三元值分支的条件块，而非 return 语句体。
- **影响**: 7/13 repros（repro 01,04,07,08,09 + 05,06 NO-DEFECT）

### Pattern A2b: Multi-branch collapse
- **触发条件**: `try: if/elif/elif/else: return ...`
- **根因**: 同 A2a，但多分支 if/elif 链的每个分支都被异常边切开。
- **影响**: 2/13 repros（repro 02,03）

### Pattern A2c: Return value collapse (ternary assign + return)
- **触发条件**: `try: a = b if c else d; return a`
- **根因**: merge_block 含 STORE_FAST a + LOAD_FAST a（有异常边），后继块 RETURN_VALUE（无异常边）。LOAD_FAST a 被误判为独立 Expr 语句，而非 return 值表达式。
- **影响**: repro 13

## 5. 累计成功率与对比

| 指标 | R11 末 | R12 末 | 变化 |
|---|---|---|---|
| klinedata.pyc match rate | 53.33% (24/45) | 53.33% (24/45) | 持平 |
| klinedata.pyc status | partial | partial | 不变 |
| 累计成功率 | 67.05% (293/437) | 67.05% (293/437) | 持平 |
| DEFECT-REPRO（本轮） | 7 | 0 | -7（全部修复） |

**说明**：klinedata.pyc 的 match rate 持平，因为 21 个不一致函数的 first_diff 均为非 Pattern A2 模式（B/E/R/C/C2）。Pattern A2 修复减少了 try-body 内部的 true_diffs，但无法使任何函数从 mismatched → matched（因前置缺陷仍存在）。累计成功率因此持平。

## 6. 残留不一致清单

klinedata.pyc 残留 21 个不一致函数，按模式分布：
- Pattern B (scope): 9 函数 — LOAD_GLOBAL vs LOAD_FAST
- Pattern E (jump renumber): 7 函数 — EXTENDED_ARG / POP_JUMP arg 不一致
- Pattern R (NOP padding): 3 函数 — NOP vs LOAD_CONST/LOAD_FAST
- Pattern C (SWAP/POP): 2 函数 — SWAP vs COMPARE_OP/POP_TOP
- Pattern C2 (tuple unpack): 1 函数 — UNPACK_SEQUENCE vs STORE_FAST

跨轮残留：backtest.pyc `<module>` Pattern R / main.pyc `run` 独立模式 / graph.pyc 4 mismatch 函数 不变。

## 7. 结论

- Pattern A2 修复正确：13 个最小复现实例全部通过（7 DEFECT-REPRO → 0）。
- klinedata.pyc match rate 持平 53.33%：Pattern A2 缺陷被前置的 B/E/R/C/C2 缺陷掩盖，修复 A2 无法使函数达到 100% 一致。
- 累计成功率持平 67.05%：无退化，无新增反模式。
- 后续建议：优先修复 Pattern B（scope，9 函数）或 Pattern E（jump renumber，7 函数），因这两个模式影响面最广且为 klinedata.pyc 多数函数的 first_diff。
