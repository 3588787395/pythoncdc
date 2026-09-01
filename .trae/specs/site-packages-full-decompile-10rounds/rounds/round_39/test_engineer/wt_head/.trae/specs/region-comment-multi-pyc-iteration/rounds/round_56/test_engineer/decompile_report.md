# R56 测试工程师反编译报告

## 测试目标
取 2 个 failed pyc 文件（最高优先级）：
1. `site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc` — failed, 0% match rate
2. `site-packages/IQCommon/util/trade_info_utils.pyc` — failed, 0% match rate

## 基线状态
- 总计 402 个 pyc 文件
- OK: 249, Partial: 150, Pending: 1, Failed: 2
- 累计匹配率: 5815/6617 = 87.88%

## 诊断结果

### 根因：Pattern TRY-NO-HANDLER
两个 failed 文件都是相同的 SyntaxError：`expected 'except' or 'finally' block`

**real_quote.pyc** (line 263):
```python
for f in list(sub_fields):
    for i in range(len(data_dict['datetime'])):
        try:
            kline_ndarray[f][i] = data_dict[f][i]
        else:  # ← for-else, but try: has no except:
```

**trade_info_utils.pyc** (line 258):
```python
try:
    os.unlink(sim_trading_lock_path)
    app_log.warning(...)
else:  # ← if-else, but try: has no except:
```

### 根因分析
- 异常表正确识别了 try 范围
- 但所有 handler entry 块被嵌套区域或 block_to_region 归属守卫消费
- `_generate_try` 方法在 `handlers = []` 时仍构造 `{'type': 'Try', 'handlers': []}` AST 节点
- 代码生成器输出 `try:` 但不生成 `except:` 或 `finally:` → SyntaxError

## 最小复现实例
12 个最小复现实例已归档至 `minimal_repros/`，覆盖以下模式：
1. try inside for loop with for-else
2. try inside nested for with outer for-else
3. try inside if-elif inside for-else
4. try inside if inside for-else
5. try with except + else inside for-else
6. nested try inside for inside try-except
7. try inside for with break
8. try inside for inside try (real_quote pattern)
9. try with multiple except inside for-else
10. try-finally inside for-else
11. try in if inside for (trade_info pattern)
12. deeply nested try in for in for-else

注意：简单复现实例未触发缺陷（均 NO-DEFECT），因为缺陷需要更复杂的嵌套结构使 handler entry 被消费。缺陷仅在真实 pyc 文件的复杂嵌套上下文中触发。

## 当前 pyc 成功率
- real_quote.pyc: failed 0% → partial 68.18% (30/44)
- trade_info_utils.pyc: failed 0% → partial 52.50% (21/40)
- 两个 failed 文件均消除 SyntaxError，变为 partial

## 累计成功率
预期：87.88% → ~89%+（两个 failed 变为 partial，0 failed）
