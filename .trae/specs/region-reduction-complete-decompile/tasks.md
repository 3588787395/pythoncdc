# Tasks

> 目标：将 site-packages 中 47 个 partial pyc 逐个修复为 OK，10 轮迭代。
> 基线：402 个 pyc，355 OK，47 partial。累计成功率 97.07%。156 个函数字节码不一致。
> 优先级：按 match_rate 降序（先修最接近 OK 的），快速增加成功率。
> 所有命令执行 <= 300 秒。每轮 commit + push。
> 修复必须符合区域归约算法 4 原则，禁止反模式。
> 必须用相同脚本验证：scripts/pyc_batch_verify.py
> 禁止修改反编译生成的 OK.py 文件

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
- [ ] R_T7: commit + push 到 origin/main（前缀 `spr-rNN:`，<=300s）

## Round 01: IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc (0.958, 24 funcs, 23 matched)

- [ ] T1.1 测试工程师反编译 strategy.pyc，输出详细 diff
- [ ] T1.2 测试工程师提取 >=10 个最小复现实例
- [ ] T1.3 修复工程师分析根因
- [ ] T1.4 修复工程师实施修复 + 更新 docstring
- [ ] T1.5 回归测试：10+ 复现实例通过 + strategy.pyc 100% + quotation.pyc 无退化
- [ ] T1.6 生成 strategyOK.py + 更新 pyc_index.json
- [ ] T1.7 commit + push `spr-r24:`

## Round 02: fly/dumpload/load_daily.pyc (0.957, 23 funcs, 22 matched)

- [ ] T2.1-T2.7 同模板

## Round 03: IQData/plugins/plugin_system_local_finance/finance_data_source.pyc (0.944, 18 funcs, 17 matched)

- [ ] T3.1-T3.7 同模板

## Round 04: IQEngine/plugins/plugin_system_trade/function.pyc (0.944, 71 funcs, 67 matched)

- [ ] T4.1-T4.7 同模板

## Round 05: IQEngine/plugins/plugin_system_matcher/matcher.pyc (0.941, 17 funcs, 16 matched)

- [ ] T5.1-T5.7 同模板

## Round 06: IQEngine/data/asset_mixin.pyc (0.938, 16 funcs, 15 matched)

- [ ] T6.1-T6.7 同模板

## Round 07: fly/common/future_param.pyc (0.938, 16 funcs, 15 matched)

- [ ] T7.1-T7.7 同模板

## Round 08: IQCommon/manager/instance.pyc (0.938, 32 funcs, 30 matched)

- [ ] T8.1-T8.7 同模板

## Round 09: IQEngine/plugins/plugin_system_persist/__init__.pyc (0.933, 15 funcs, 14 matched)

- [ ] T9.1-T9.7 同模板

## Round 10: fly/logger.pyc (0.933, 30 funcs, 28 matched)

- [ ] T10.1-T10.7 同模板

# Task Dependencies

- 每轮内部串行：R_T1 → R_T2 → R_T3 → R_T4 → R_T5 → R_T6 → R_T7
- 跨轮串行：Round N+1 依赖 Round N 完成（至少一个 pyc 转为 OK）
- 回归测试依赖所有先前轮次：R_T5 必须验证 quotation.pyc 无退化

# Partial 文件列表（按 match_rate 降序，47 个）

1. IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc (0.958)
2. fly/dumpload/load_daily.pyc (0.957)
3. IQData/plugins/plugin_system_local_finance/finance_data_source.pyc (0.944)
4. IQEngine/plugins/plugin_system_trade/function.pyc (0.944)
5. IQEngine/plugins/plugin_system_matcher/matcher.pyc (0.941)
6. IQEngine/data/asset_mixin.pyc (0.938)
7. fly/common/future_param.pyc (0.938)
8. IQCommon/manager/instance.pyc (0.938)
9. IQEngine/plugins/plugin_system_persist/__init__.pyc (0.933)
10. fly/logger.pyc (0.933)
11. fly/common/future_contract_info.pyc (0.931)
12. fly/common/tradingday_calendar.pyc (0.929)
13. IQCommon/data/api_data.pyc (0.929)
14. IQCommon/util/fileio_utils.pyc (0.929)
15. IQEngine/plugins/plugin_system_event_source/default_event_source.pyc (0.929)
16. fly/oauthenticator/itn.pyc (0.929)
17. IQData/api/api_base.pyc (0.920)
18. IQCommon/strategy/wizard_quant_api.pyc (0.925)
19. IQCommon/data/finance.pyc (0.917)
20. IQData/utils/common_func.pyc (0.917)
21. IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc (0.917)
22. IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc (0.914)
23. fly/simtradding/flyAccount.pyc (0.913)
24. IQCommon/common/main.pyc (0.909)
25. IQCommon/strategy/hg_api.pyc (0.909)
26. IQCommon/utils.pyc (0.909)
27. fly/oauthenticator/oauth2.pyc (0.909)
28. IQCommon/util/common_func.pyc (0.905)
29. IQCommon/util/strategy_info_utils.pyc (0.893)
30. IQCommon/util/replace_utils.pyc (0.889)
31. IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc (0.889)
32. IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc (0.889)
33. IQEngine/core/execution_context.pyc (0.882)
34. IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc (0.882)
35. IQData/plugins/plugin_system_realquote/real_quote.pyc (0.886)
36. IQEngine/interface.pyc (0.876)
37. IQEngine/utils/scheduler.pyc (0.867)
38. fly/common/aes_encrypt.pyc (0.857)
39. IQEngine/plugins/plugin_system_finance/slippage.pyc (0.857)
40. IQData/modules/WEBCLIENT/web_socket_client.pyc (0.857)
41. IQCommon/api/klinedata.pyc (0.844)
42. fly/data/quote.pyc (0.827)
43. fly/data/quote_handler.pyc (0.807)
44. IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc (0.832)
45. IQCommon/util/trade_info_utils.pyc (0.800)
46. IQEngine/plugins/plugin_system_log/__init__.pyc (0.800)
47. IQEngine/plugins/plugin_system_risk_calculation/function.pyc (0.733)
