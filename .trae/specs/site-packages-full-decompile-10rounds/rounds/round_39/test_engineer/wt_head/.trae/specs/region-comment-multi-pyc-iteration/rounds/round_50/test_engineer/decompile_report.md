# Round 50 测试工程师报告

## 目标文件
- **路径**: `F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
- **函数数**: 119
- **匹配率**: 76/119 = 63.87%
- **不匹配函数数**: 43

## 主要缺陷模式

### 模式 A: LOAD_METHOD vs LOAD_FAST（2 函数，影响最大）
- `_process_cancel_order`: 228 true_diffs, first_diff `LOAD_METHOD(acquire)` → `LOAD_FAST(order)`
- `_process_order`: 361 true_diffs, first_diff `LOAD_METHOD(acquire)` → `LOAD_FAST(self)`
- 根因：方法调用检测错误，将 `lock.acquire()` 误识别为变量访问

### 模式 B: LOAD_FAST vs LOAD_GLOBAL（变量作用域）
- `_sync_worker`: 232 true_diffs
- `fund_transfer`: 51 true_diffs
- 根因：变量作用域识别错误

### 模式 C: STORE_ATTR vs LOAD_FAST（属性赋值丢失）
- `_trade_status_handle`: 86 true_diffs
- 根因：属性赋值语句被误识别为表达式

### 模式 D: extra RETURN_VALUE（多余返回语句）
- `_process_tick_order`: 1 true_diff, extra_in_decomp

## 当前状态
- 累计匹配率：87.12% (5765/6617)
- OK: 232, Partial: 170, Failed: 0

## 结论
`trade_live_broker.pyc` 的缺陷涉及深层算法问题（方法调用检测、变量作用域、属性赋值识别），需要深入的 `region_ast_generator.py` 和 `code_generator.py` 修复。建议留待后续专门轮次处理。
