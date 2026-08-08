# R57 测试工程师反编译报告

## 测试目标
验证 R56 修复（TRY-NO-HANDLER）对全部 pyc 文件的影响，更新所有文件状态。

## 基线状态（R56 修复前）
- OK: 249, Partial: 150, Pending: 1, Failed: 2
- 累计匹配率: 5815/6617 = 87.88%

## 当前状态（R56 修复后）
- OK: 249, Partial: 153, Pending: 0, Failed: 0
- 累计匹配率: 5905/6617 = 89.24%
- 改善: +90 匹配函数, 0 failed（从 2 → 0）

## 已验证文件
1. `real_quote.pyc`: failed 0% → partial 68.18% (30/44, +30)
2. `trade_info_utils.pyc`: failed 0% → partial 52.50% (21/40, +21)
3. `klinedata.pyc`: failed 0% → partial 62.22% (28/45, +28)
4. `strategy_info_utils.pyc`: failed 0% → partial 79% (24/30, +24)
5. `trade_live_broker.pyc`: failed 0% → partial 70% (90/128, +90)

注意：3-5 的 failed 状态是由后台批量验证（R56 修复前启动）错误标记的。

## 常见失败模式分析

### Pattern 1: JUMP_IF_TRUE_OR_POP 表达式赋值坍缩（最高影响）
- 影响：trade.pyc create_trade（68 → 16 条指令，函数体坍缩）
- 根因：`x or y` 后跟 `LOAD_FAST(obj) + STORE_ATTR(attr)` 被误处理为独立表达式
- 应为：`obj.attr = x or y`
- 实际：`x or y`（表达式语句）+ 后续语句丢失

### Pattern 2: LOAD_GLOBAL vs LOAD_FAST 变量名混淆
- 影响：klinedata.pyc 多个函数
- 根因：表达式重建时变量作用域解析错误
- 示例：`LOAD_GLOBAL(system_log)` → `LOAD_FAST(fields)`

### Pattern 3: PUSH_EXC_INFO try-except 结构重建不完整
- 影响：trade_info_utils.pyc 多个函数
- 根因：try-except handler body 语句顺序错乱

### Pattern 4: UNPACK_SEQUENCE vs STORE_FAST 元组解包问题
- 影响：klinedata.pyc get_kline_by_count_new
- 根因：元组解包被误处理为单独赋值

## 最小复现实例
本轮聚焦于批量状态更新，复现实例归档至 `minimal_repros/`。

## 累计成功率
- 87.88% → 89.24%（+1.36 pp，+90 匹配函数）
- 0 failed（从 2 → 0）
