# Tasks

> 目标：将 site-packages 中 42 个 partial + 1 个 failed pyc 逐个修复为 OK，10 轮迭代。
> 基线：402 个 pyc，359 OK，42 partial，1 failed。累计成功率 97.41%。
> 优先级：按 match_rate 降序（先修最接近 OK 的），快速增加成功率。
> 所有命令执行 <= 300 秒。每轮 commit + push。
> 修复必须符合区域归约算法 4 原则，禁止反模式。
> 必须用相同脚本验证：scripts/pyc_batch_verify.py
> 禁止修改反编译生成的 OK.py 文件
> quotation.pyc 当前 100% 匹配，每轮必须回归验证

## 通用任务模板（每轮共用）

- [ ] R_T1: 测试工程师反编译目标 pyc
  - 从 pyc_index.json 取下一个 match_rate 最高的 partial pyc
  - 执行 `python scripts/pyc_batch_verify.py single <pyc_path>`
  - 统计一致函数数与成功率
- [ ] R_T2: 测试工程师提取 >=10 个最小复现实例
  - 每个实例：最小 .py 源码 → compile → 反编译 → 字节码 diff
  - 识别涉及的区域类型与算法偏离点
- [ ] R_T3: 修复工程师分析 + 定位（依赖 R_T1/R_T2）
  - 对每个不一致定位到 `_identify_*_regions` 或 `_generate_*` 方法
  - 输出根因分析（涉及的区域类型 + 算法偏离点）
- [ ] R_T4: 修复工程师实施修复
  - 按区域归约算法 4 原则完善逻辑（禁止补丁）
  - 只修改 core/cfg/ 下源码，不修改 OK.py 文件
- [ ] R_T5: 修复工程师回归测试（<=280s）
  - 该轮 10+ 最小复现实例全部通过
  - 目标 pyc 字节码完全匹配
  - quotation.pyc 回归验证通过
  - 执行 `python scripts/pyc_batch_verify.py batch --max-count 5 --round N` 抽检无退化
- [ ] R_T6: 更新 pyc_index.json + 生成 OK.py 文件
  - 在同目录下生成同名+OK 的 .py 文件
  - pyc_index.json 中该文件状态更新为 "ok"
- [ ] R_T7: commit + push 到 origin/main（前缀 `rr43-rNN:`，<=300s）

## Round 01: IQCommon/common/main.pyc (0.970, 32/33 matched)

- [ ] T1.1 测试工程师反编译 main.pyc，输出详细 diff
- [ ] T1.2 测试工程师提取 >=10 个最小复现实例
- [ ] T1.3 修复工程师分析根因
- [ ] T1.4 修复工程师实施修复 + 更新 docstring
- [ ] T1.5 回归测试：10+ 复现实例通过 + main.pyc 100% + quotation.pyc 无退化
- [ ] T1.6 生成 mainOK.py + 更新 pyc_index.json
- [ ] T1.7 commit + push `rr43-r01:`

## Round 02: IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc (0.958, 23/24)

- [ ] T2.1-T2.7 同模板

## Round 03: IQEngine/plugins/plugin_system_trade/function.pyc (0.958, 68/71)

- [ ] T3.1-T3.7 同模板

## Round 04: fly/dumpload/load_daily.pyc (0.957, 22/23)

- [ ] T4.1-T4.7 同模板

## Round 05: IQData/plugins/plugin_system_local_finance/finance_data_source.pyc (0.944, 17/18)

- [ ] T5.1-T5.7 同模板

## Round 06: IQEngine/plugins/plugin_system_matcher/matcher.pyc (0.941, 16/17)

- [ ] T6.1-T6.7 同模板

## Round 07: IQEngine/data/asset_mixin.pyc (0.938, 15/16)

- [ ] T7.1-T7.7 同模板

## Round 08: fly/common/future_param.pyc (0.938, 15/16)

- [ ] T8.1-T8.7 同模板

## Round 09: IQEngine/plugins/plugin_system_persist/__init__.pyc (0.933, 14/15)

- [ ] T9.1-T9.7 同模板

## Round 10: fly/logger.pyc (0.933, 28/30)

- [ ] T10.1-T10.7 同模板

# Task Dependencies

- 每轮内部串行：R_T1 → R_T2 → R_T3 → R_T4 → R_T5 → R_T6 → R_T7
- 跨轮串行：Round N+1 依赖 Round N 完成（至少一个 pyc 转为 OK）
- 回归测试依赖所有先前轮次：R_T5 必须验证 quotation.pyc 无退化

# Partial 文件列表（按 match_rate 降序，42 个）

1. IQCommon/common/main.pyc (0.970, 32/33)
2. IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc (0.958, 23/24)
3. IQEngine/plugins/plugin_system_trade/function.pyc (0.958, 68/71)
4. fly/dumpload/load_daily.pyc (0.957, 22/23)
5. IQData/plugins/plugin_system_local_finance/finance_data_source.pyc (0.944, 17/18)
6. IQEngine/plugins/plugin_system_matcher/matcher.pyc (0.941, 16/17)
7. IQEngine/data/asset_mixin.pyc (0.938, 15/16)
8. fly/common/future_param.pyc (0.938, 15/16)
9. IQEngine/plugins/plugin_system_persist/__init__.pyc (0.933, 14/15)
10. fly/logger.pyc (0.933, 28/30)
11. fly/common/future_contract_info.pyc (0.931, 27/29)
12. IQCommon/data/api_data.pyc (0.929, 13/14)
13. IQCommon/util/fileio_utils.pyc (0.929, 13/14)
14. IQCommon/util/strategy_info_utils.pyc (0.929, 26/28)
15. IQEngine/plugins/plugin_system_event_source/default_event_source.pyc (0.929, 13/14)
16. IQEngine/plugins/plugin_system_finance/slippage.pyc (0.929, 13/14)
17. fly/common/tradingday_calendar.pyc (0.929, 26/28)
18. fly/oauthenticator/itn.pyc (0.929, 13/14)
19. IQCommon/strategy/wizard_quant_api.pyc (0.925, 49/53)
20. IQData/api/api_base.pyc (0.920, 23/25)
21. IQCommon/data/finance.pyc (0.917, 22/24)
22. IQData/utils/common_func.pyc (0.917, 22/24)
23. IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc (0.917, 11/12)
24. IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc (0.914, 32/35)
25. fly/simtradding/flyAccount.pyc (0.913, 21/23)
26. IQCommon/utils.pyc (0.909, 20/22)
27. fly/oauthenticator/oauth2.pyc (0.909, 10/11)
28. IQCommon/manager/instance.pyc (0.906, 29/32)
29. IQCommon/util/common_func.pyc (0.905, 19/21)
30. IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc (0.889, 16/18)
31. IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc (0.889, 16/18)
32. IQEngine/utils/scheduler.pyc (0.889, 40/45)
33. IQData/plugins/plugin_system_realquote/real_quote.pyc (0.886, 39/44)
34. IQEngine/core/execution_context.pyc (0.882, 15/17)
35. IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc (0.882, 30/34)
36. IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc (0.849, 101/119)
37. IQCommon/api/klinedata.pyc (0.844, 38/45)
38. fly/data/quote_handler.pyc (0.842, 48/57)
39. fly/data/quote.pyc (0.827, 67/81)
40. IQCommon/util/trade_info_utils.pyc (0.800, 32/40)
41. IQEngine/plugins/plugin_system_log/__init__.pyc (0.800, 8/10)
42. IQEngine/plugins/plugin_system_risk_calculation/function.pyc (0.800, 12/15)

# Failed 文件列表（1 个）

1. IQCommon/util/replace_utils.pyc (RuntimeError)
