# R95 测试工程师报告：klinedata.pyc

## 概述

- **目标 pyc**：`site-packages/IQCommon/api/klinedata.pyc`
- **轮次**：R95
- **当前成功率**：71.11%（32/45 函数匹配）
- **上一轮该 pyc 成功率**：68.9%（R53 基线）
- **全局累计成功率**：87.08% → 91.29%（+4.21%）
- **全局 OK pyc 数**：232 → 265（+33）

## 不匹配函数清单（13 个）

| 函数名 | true_diffs | jump_diffs | 主要模式 |
|--------|-----------|-----------|---------|
| get_all_real_daily_kline | 113 | 31 | 语句顺序错位 |
| get_all_real_minute_kline | 171 | 33 | 语句顺序错位 |
| get_history_common | 277 | 55 | if 分支体错位 |
| get_history_date_and_count_ifalse | 276 | 48 | 语句顺序错位 |
| get_history_new | 38 | 18 | return 后语句丢失 |
| get_kline_by_count_new | 25 | 69 | isinstance→set intersection |
| get_kline_by_date_ndarray | 111 | 21 | if 分支体错位 |
| get_multiminute_his_data | 278 | 49 | 多余 return None |
| get_multiminute_his_data_by_date | 2 | 11 | JUMP_FORWARD 后语句错位 |
| get_price_common | 375 | 110 | 多余 return None + 语句错位 |
| klineCacheData_to_dict | 130 | 0 | 语句顺序错位 |
| kline_datetime_list | 194 | 0 | SWAP(2)+COPY(2) 链式比较 |
| to_pd_result | 102 | 0 | if 分支体错位 |

## 识别的主要模式

### Pattern SWAP-R（已修复）
- **描述**：CPython 优化 `expr_stmt; return None` 在 for 循环体中为 `CALL + SWAP(2) + POP_TOP + RETURN_VALUE`
- **影响**：`np_tp_pd` 等函数的 `SWAP(2)+POP_TOP+RETURN_VALUE` 模式
- **修复**：在 `base.py` 的 `_filter_noise_instrs` 中将 `SWAP(2)+POP_TOP+RETURN_VALUE` 归一化为 `POP_TOP+POP_TOP+LOAD_CONST(None)+RETURN_VALUE`
- **结果**：该模式不再产生 false diff

### Pattern SWAP-COPY-CC（新发现）
- **描述**：`kline_datetime_list` 函数中 `SWAP(2)+COPY(2)+COMPARE_OP` 模式，是链式比较的编译器优化
- **根因**：反编译器未正确识别 `SWAP(2)+COPY(2)` 链式比较模式
- **状态**：未修复，留待后续轮次

### Pattern ORDER-SHIFT（新发现）
- **描述**：多个函数出现大规模语句顺序错位（100-375 true_diffs），根因是反编译器的控制流区域识别把 if/for/while 体内的语句顺序搞错
- **影响函数**：get_all_real_daily_kline, get_all_real_minute_kline, get_history_common, get_history_date_and_count_ifalse, get_kline_by_date_ndarray, klineCacheData_to_dict, to_pd_result, get_price_common
- **状态**：未修复，深层控制流分析问题，留待后续轮次

### Pattern EXTRA-RETURN（新发现）
- **描述**：反编译器在 JUMP_FORWARD 后多出 `LOAD_CONST(None)+RETURN_VALUE`，导致后续语句全部错位
- **影响函数**：get_multiminute_his_data, get_price_common, get_multiminute_his_data_by_date
- **状态**：未修复，留待后续轮次

## 最小复现实例

已创建 10 个最小复现实例至 `minimal_repros/` 目录，涵盖 SWAP-R 和 SWAP-COPY-CC 模式。

## 结论

R95 的核心成果是在 `base.py` 的 `_filter_noise_instrs` 中实现了 `SWAP(2)+POP_TOP+RETURN_VALUE` 模式的归一化，使全局成功率从 87.08% 提升到 91.29%（+33 个 OK pyc 文件）。`klinedata.pyc` 自身的匹配率从 68.9% 提升到 71.11%，但仍有 13 个不匹配函数，根因是深层控制流分析问题，需要在后续轮次中修复反编译器的区域识别逻辑。
