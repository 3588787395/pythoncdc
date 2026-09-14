# Tasks

> 目标：将 site-packages 中 58 个 partial pyc 逐个修复为 OK，10 轮迭代。
> 基线：402 个 pyc，344 OK，58 partial。成功率 85.6%。317 个函数字节码不一致。
> 优先级：按 match_rate 降序（先修最接近 OK 的），快速增加成功率。
> 所有命令执行 <= 300 秒。每轮 commit + push。
> 修复必须符合区域归约算法 4 原则，禁止反模式。

## 通用任务模板（每轮共用）

- [ ] R_T1: 测试工程师反编译目标 pyc
  - 从 pyc_index.json 取下一个 match_rate 最高的 partial pyc
  - 执行反编译 + 逐函数字节码 diff
  - 统计一致函数数与成功率
  - 归档至 `rounds/round_NN/test_engineer/decompile_report.md`
- [ ] R_T2: 测试工程师提取 >=10 个最小复现实例
  - 每个实例：最小 .py 源码 → compile → 反编译 → 字节码 diff
  - 识别涉及的区域类型与算法偏离点
  - 归档至 `rounds/round_NN/test_engineer/minimal_repros/`
- [ ] R_T3: 修复工程师分析 + 定位（依赖 R_T1/R_T2）
  - 对每个不一致定位到 `_identify_*_regions` 或 `_generate_*` 方法
  - 输出根因分析（涉及的区域类型 + 算法偏离点）
- [ ] R_T4: 修复工程师实施修复
  - 按区域归约算法 4 原则完善逻辑（禁止补丁）
  - 同步更新方法 docstring（6 节 / 4 节模板）
- [ ] R_T5: 修复工程师回归测试（<=280s）
  - 该轮 10+ 最小复现实例全部通过
  - 目标 pyc 字节码完全匹配
  - quotation.pyc 回归验证通过
- [ ] R_T6: 更新 pyc_index.json + 生成 OK.py 文件
  - 在同目录下生成同名+OK 的 .py 文件
  - pyc_index.json 中该文件状态更新为 "ok"
- [ ] R_T7: commit + push 到 origin/main（前缀 `spr-rNN:`，<=300s）

## Round 01: IQCommon/strategy/jq_trans_module.pyc (0.971, 35 funcs, 34 matched)

- [ ] T1.1 测试工程师反编译 jq_trans_module.pyc，输出 decompile_report.md
- [ ] T1.2 测试工程师提取 >=10 个最小复现实例（trans_code, replace_args 等不一致函数）
- [ ] T1.3 修复工程师分析根因（推测：elif 链 / for-in-try 边界）
- [ ] T1.4 修复工程师实施修复 + 更新 docstring
- [ ] T1.5 回归测试：10+ 复现实例通过 + jq_trans_module.pyc 100% + quotation.pyc 无退化
- [ ] T1.6 生成 jq_trans_moduleOK.py + 更新 pyc_index.json
- [ ] T1.7 commit + push `spr-r01:`

## Round 02: fly/common/flytools.pyc (0.969, 65 funcs, 63 matched)

- [ ] T2.1 测试工程师反编译 flytools.pyc，输出 decompile_report.md
- [ ] T2.2 测试工程师提取 >=10 个最小复现实例
- [ ] T2.3 修复工程师分析根因 + 实施修复
- [ ] T2.4 回归测试：10+ 复现实例 + flytools.pyc 100% + quotation.pyc 无退化 + R01 无退化
- [ ] T2.5 生成 flytoolsOK.py + 更新 pyc_index.json
- [ ] T2.6 commit + push `spr-r02:`

## Round 03: IQData/plugins/plugin_system_db_tools/db_base.pyc (0.967, 30 funcs, 29 matched)

- [ ] T3.1-T3.6 同模板

## Round 04: IQEngine/plugins/plugin_system_trade/function.pyc (0.944, 71 funcs, 67 matched)

- [ ] T4.1-T4.6 同模板

## Round 05: IQEngine/core/strategy/strategy.pyc (0.947, 19 funcs, 18 matched)

- [ ] T5.1-T5.6 同模板

## Round 06: IQEngine/plugins/plugin_system_matcher/matcher.pyc (0.941, 17 funcs, 16 matched)

- [ ] T6.1-T6.6 同模板

## Round 07: IQCommon/common/main.pyc (0.879, 33 funcs, 29 matched)

- [ ] T7.1-T7.6 同模板

## Round 08: IQEngine/interface.pyc (0.876, 105 funcs, 92 matched)

- [ ] T8.1-T8.6 同模板

## Round 09: fly/data/quote.pyc (0.778, 81 funcs, 63 matched)

- [ ] T9.1-T9.6 同模板

## Round 10: IQCommon/util/replace_utils.pyc (0.667, 9 funcs, 6 matched)

- [ ] T10.1-T10.6 同模板

# Task Dependencies

- 每轮内部串行：R_T1 → R_T2 → R_T3 → R_T4 → R_T5 → R_T6 → R_T7
- 跨轮串行：Round N+1 依赖 Round N 完成（至少一个 pyc 转为 OK）
- 回归测试依赖所有先前轮次：R_T5 必须验证所有已 OK 的 pyc 无退化

# Partial 文件列表（按 match_rate 降序，58 个）

1. IQCommon/strategy/jq_trans_module.pyc (0.971)
2. fly/common/flytools.pyc (0.969)
3. IQData/plugins/plugin_system_db_tools/db_base.pyc (0.967)
4. IQEngine/plugins/plugin_system_trade/function.pyc (0.944)
5. IQEngine/core/strategy/strategy.pyc (0.947)
6. fly/event/event_engine.pyc (0.947)
7. IQEngine/plugins/plugin_system_matcher/matcher.pyc (0.941)
8. fly/common/future_param.pyc (0.938)
9. IQEngine/plugins/plugin_system_persist/__init__.pyc (0.933)
10. fly/logger.pyc (0.933)
11. IQEngine/core/strategy/strategy_universe.pyc (0.909)
12. fly/oauthenticator/oauth2.pyc (0.909)
13. IQEngine/core/executor.pyc (0.900)
14. IQCommon/util/common_func.pyc (0.905)
15. IQCommon/strategy/wizard_quant_api.pyc (0.906)
16. IQCommon/manager/instance.pyc (0.906)
17. fly/dumpload/load_daily.pyc (0.913)
18. IQCommon/data/finance.pyc (0.917)
19. IQData/utils/common_func.pyc (0.917)
20. IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc (0.917)
21. IQData/api/api_base.pyc (0.920)
22. IQCommon/data/api_data.pyc (0.929)
23. IQEngine/plugins/plugin_system_finance/slippage.pyc (0.929)
24. fly/oauthenticator/itn.pyc (0.929)
25. fly/common/future_contract_info.pyc (0.931)
26. IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc (0.889)
27. IQData/plugins/plugin_system_client_db/client_db.pyc (0.889)
28. IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc (0.886)
29. IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc (0.882)
30. IQEngine/core/execution_context.pyc (0.882)
31. IQCommon/common/main.pyc (0.879)
32. IQEngine/interface.pyc (0.876)
33. IQEngine/data/asset_mixin.pyc (0.875)
34. IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc (0.875)
35. IQEngine/plugins/plugin_fly_data/quote/get_stock_status.pyc (0.875)
36. IQCommon/util/cgroup_utils.pyc (0.875)
37. IQEngine/utils/scheduler.pyc (0.867)
38. IQCommon/utils.pyc (0.864)
39. fly/common/aes_encrypt.pyc (0.857)
40. IQEngine/plugins/plugin_system_event_source/default_event_source.pyc (0.857)
41. IQData/modules/WEBCLIENT/web_socket_client.pyc (0.857)
42. IQCommon/util/strategy_info_utils.pyc (0.857)
43. IQCommon/util/fileio_utils.pyc (0.857)
44. fly/common/common.pyc (0.833)
45. IQEngine/plugins/plugin_system_debug/__init__.pyc (0.833)
46. IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc (0.833)
47. fly/simtradding/flyAccount.pyc (0.826)
48. IQCommon/strategy/hg_api.pyc (0.818)
49. IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc (0.807)
50. fly/data/quote_handler.pyc (0.807)
51. IQEngine/plugins/plugin_system_log/__init__.pyc (0.800)
52. IQData/entry.pyc (0.800)
53. fly/data/quote.pyc (0.778)
54. IQData/plugins/plugin_system_realquote/real_quote.pyc (0.773)
55. IQData/plugins/plugin_system_db_tools/api_db.pyc (0.750)
56. IQEngine/plugins/plugin_system_risk_calculation/function.pyc (0.733)
57. IQCommon/api/klinedata.pyc (0.733)
58. IQData/plugins/plugin_system_local_finance/finance_data_source.pyc (0.722)
59. IQCommon/util/trade_info_utils.pyc (0.675)
60. IQCommon/util/replace_utils.pyc (0.667)
