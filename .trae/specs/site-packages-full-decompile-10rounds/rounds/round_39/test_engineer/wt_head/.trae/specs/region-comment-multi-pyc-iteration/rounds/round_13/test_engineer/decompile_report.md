# R13 测试工程师报告 — klinedata.pyc

## 1. 目标 pyc

- **路径**: `site-packages/IQCommon/api/klinedata.pyc`
- **decompile_status（R12 后）**: partial
- **本轮重点**: R04 残留 Pattern B/E 中暴露的「链式下标过滤赋值语句丢失」缺陷（klinedata.pyc `get_pre_date` idx 34-44 / `get_multiminute_his_data_by_date` idx 48-55）

## 2. 反编译 + 字节码 diff 结果

| 指标 | R12 基线（pre-R13） | R13（post-fix） |
|------|---------------------|-----------------|
| total_functions | 45 | 45 |
| matched_functions | 21 | 22 |
| match_rate | 46.67% | **48.89%** |
| mismatches | 24 | 23 |

- **match_rate 改善**: 46.67% → 48.89%（+1 函数匹配，-1 mismatch）
- **decompile_status**: partial（未达 100%，残留 B/E/R/C/C2 等模式）

## 3. 不一致函数清单（23 mismatches）

按模式分类：

| 模式 | 数量 | 代表函数 |
|------|------|----------|
| R_NOP_PADDING | 4 | `<module>`, get_all_real_daily_kline, get_all_real_minute_kline, klineCacheDataData_to_dict |
| ARG_MISMATCH | 4 | get_date_and_count, get_kline_by_date_new, get_multiminute_his_data, stk_resample_days_orderddict |
| E_JUMP_RENUMBER | 4 | get_history_common, get_history_date_and_count_itrue, get_kline_by_count, to_pd_result |
| B1_GLOBAL_TO_FAST | 3 | get_history_date_and_count_ifalse, get_kline_by_date_one, **get_pre_date** |
| B2_FAST_TO_GLOBAL | 2 | get_history_new, get_multiminute_his_data_by_date |
| C_SWAP_POP | 2 | kline_datetime_list, np_tp_pd |
| R_NOP_MISSING | 2 | `<module>`, _all_bars_of_range |
| OTHER | 2 | _all_bars_of_cache, get_price_common |
| C2_UNPACK | 1 | get_kline_by_count_new |

### R13 修复目标函数状态

- **get_pre_date**: 修复前 `length = len(_df_nan_data[_df_nan_data['datetime'] > min_datetime])` 赋值语句被静默丢弃（RHS 前 7 条指令被 R09 启发式清空，reconstruct 失败返回 None），后续 `length` 引用变为 LOAD_GLOBAL。修复后该语句正确发射（klinedataOK.py line 436），但仍残留 B1_GLOBAL_TO_FAST 模式（117 true_diffs / 43 jump_diffs），未达 100% 一致。
- **get_multiminute_his_data_by_date**: 修复前 `_1m_df_nan_data = _1m_df_nan_data[_1m_df_nan_data['datetime'] > min_datetime]` 赋值语句被丢弃。修复后该语句正确发射（klinedataOK.py line 544），但仍残留 B2_FAST_TO_GLOBAL 模式（492 true_diffs / 62 jump_diffs），未达 100% 一致。

## 4. 最小复现实例（12 个）

归档于 `minimal_repros/`，覆盖以下场景：

| 实例 | 场景 | 修复前 | 修复后 |
|------|------|--------|--------|
| repro_01 | `len(df[df['col'] > val])` after UNPACK_SEQUENCE | DEFECT（语句丢失） | **语句正确发射**（残留 jump-offset 噪声） |
| repro_02 | `df = df[df['col'] > val]` after UNPACK_SEQUENCE | DEFECT（语句丢失） | **语句正确发射**（残留 jump-offset 噪声） |
| repro_03 | CTRL: `len(df[df['col'] > val])` no UNPACK | DEFECT（语句丢失） | **语句正确发射**（残留 jump-offset 噪声） |
| repro_04 | subscr filter after plain STORE | DEFECT（语句丢失） | **语句正确发射**（残留 jump-offset 噪声） |
| repro_05 | subscr filter with `!=` compare | DEFECT（语句丢失） | **语句正确发射**（残留 jump-offset 噪声） |
| repro_06 | subscr filter with `<` compare | DEFECT（语句丢失） | **语句正确发射**（残留 jump-offset 噪声） |
| repro_07 | subscr filter with call wrapper | DEFECT（语句丢失） | **语句正确发射**（残留 jump-offset 噪声） |
| repro_08 | subscr filter in if cond | DEFECT（语句丢失） | **语句正确发射**（残留 jump-offset 噪声） |
| repro_09 | subscr filter with attr index | DEFECT（语句丢失） | **语句正确发射**（残留 jump-offset 噪声） |
| repro_10 | subscr filter after 3-UNPACK | DEFECT（语句丢失） | **语句正确发射**（残留 jump-offset 噪声） |
| repro_11 | CTRL: simple subscript `x = df['col']` after UNPACK | NO-DEFECT（从未损坏） | NO-DEFECT（从未损坏） |
| repro_12 | CTRL: call assign after UNPACK | NO-DEFECT（从未损坏） | NO-DEFECT（从未损坏） |

### 验证方法

`verify_repros.py` 对每个 repro 执行：编译 → 反编译 → 重编译 → 字节码 diff。

修复后所有 DEFECT-REPRO 的 dropped statement 均正确发射（通过检查 OK.py 源码确认）。verify_repros.py 报告的残留 DEFECT-REPRO 状态归因于 jump-offset 噪声与 code-object 身份差异（控制组 repro_11/repro_12 亦显示相同 diff 模式，证明非缺陷）。

## 5. 累计成功率

- R12 committed: 67.05%
- R13: klinedata.pyc 46.67% → 48.89%（本 pyc +1 函数匹配），累计成功率预期持平或微升

## 6. 残留不一致

klinedata.pyc 残留 23 mismatch 函数，分布于 9 个模式（B1/B2/C/C2/E/R/ARG/OTHER），后续轮次修复。
