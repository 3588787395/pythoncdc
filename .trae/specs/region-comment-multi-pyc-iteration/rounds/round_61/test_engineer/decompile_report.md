# 测试工程师报告 - Round 61

## 目标文件
- **pyc路径**: `site-packages/IQCommon/api/klinedata.pyc`
- **反编译输出**: `site-packages/IQCommon/api/klinedataOK.py`
- **源代码长度**: 91,131 字符

## 字节码一致性结果
- **匹配率**: 62.22%
- **匹配函数数**: 28 / 45
- **不匹配函数数**: 17

## 不匹配函数清单

| 函数名 | 差异数 | 首个差异 |
|--------|--------|----------|
| get_kline_by_count_new | 430 | UNPACK_SEQUENCE→STORE_FAST (参数解包错误) |
| get_all_real_minute_kline | 171 | LOAD_GLOBAL copy→LOAD_GLOBAL range |
| get_history_common | 277 | LOAD_FAST fields→BUILD_LIST 1 |
| get_history_date_and_count_ifalse | 276 | LOAD_GLOBAL datetime→LOAD_FAST query_date |
| get_all_real_daily_kline | 113 | LOAD_GLOBAL copy→LOAD_FAST symbol |
| get_kline_by_date_ndarray | 111 | LOAD_GLOBAL api_get_from_zeromq→LOAD_FAST redata |
| get_kline_by_count | 21 | LOAD_GLOBAL system_log→LOAD_FAST fields |
| get_kline_by_date_new | 24 | LOAD_GLOBAL system_log→LOAD_FAST fields |
| get_kline_by_date_one | 21 | LOAD_GLOBAL system_log→LOAD_FAST fields |
| get_history_new | 38 | LOAD_FAST real_data_len→LOAD_GLOBAL len |

## 分析结论

**当前状态**: 部分一致 (28/45 = 62.22%)

**主要问题模式**:

### Pattern P1: 参数解包错误 (get_kline_by_count_new, 430 diffs)
- **症状**: UNPACK_SEQUENCE 2 变成 STORE_FAST start_000300
- **根因**: 可能是 `try-except` 嵌套导致参数解包丢失
- **影响**: 函数参数列表被错误归约

### Pattern P2: 赋值语句顺序错位 (多个函数)
- **症状**: LOAD_FAST fields → BUILD_LIST 或 LOAD_GLOBAL system_log 误识别
- **根因**: try/except 结构导致语句边界判定错误
- **影响**: 属性访问和日志调用位置错误

### Pattern P3: 控制流边界扩张
- **症状**: 多达 277 个 true_diffs (get_history_common)
- **根因**: 区域边界 BFS 过度扩张，吸收了外层语句
- **影响**: 大量语句顺序和结构错误

**下一步行动**:
- 创建 12 个最小复现实例（覆盖 Pattern P1/P2/P3）
- 定位到 `_identify_with_regions` 或 `_identify_conditional_regions` 的边界判定逻辑

## 与上一轮对比
- 上一轮 (R60): 全局匹配率 89.07%, 0 failed
- 本轮 (R61): 本文件匹配率 62.22%, 17 个不匹配函数
- 变化: 本轮为首次针对 klinedata.pyc 的专门分析

## 备注
- klinedata.pyc 有 64 个 code objects，但 bytecode_diff 只报告了 45 个函数
- 可能存在嵌套 code objects（如推导式、类定义）需要单独分析