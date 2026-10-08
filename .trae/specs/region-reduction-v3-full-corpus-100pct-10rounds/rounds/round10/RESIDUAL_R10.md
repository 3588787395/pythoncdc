# Round 10 残余清单（文件 × 单元 × 台账登记的机制）

> 由 `residual_report.py` 从 rounds/round10/after/ 八份分片报告直接生成，非手抄：八份不齐即拒绝出表，任何失败单元在 UNITMAP_R10 查不到即标 UNREGISTERED 并非零退出。本次 exit=0（UNREGISTERED 行数=0）。
> 同批读数：6577/6617 单元（99.3955%）、386/402 文件；本轮无代码落地，故与 round9 逐位相同。

# 封表时点 11:54:39 / label round10 / 数据源 rounds/round10/after(8 shards)
单元 6577/6617 (99.3955%)  文件 386/402  残余文件 16 个  残余单元 40 条
对照 round9：单元 6577 -> 6577  文件 386 -> 386

| 文件 | 单元读数 | 失败单元（完整 qualname） | 台账登记的机制/条款 |
|---|---|---|---|
| `IQCommon/api/klinedata.pyc` | 61/64 | `<module>.get_kline_by_count_new` | \| `klinedata.get_kline_by_count_new` \| `orig[567] JUMP_BACKWARD ANCHOR` → prod `JUMP_FORWARD ANCHOR` \| 同一位置的**回边被写成正向跳过**（方向反） \| #14（ANCHOR 子形） \| |
| `IQCommon/api/klinedata.pyc` | 61/64 | `<module>.get_multiminute_his_data` | \| `klinedata.get_multiminute_his_data` \| −1 \| 同上 \| 同上 \| |
| `IQCommon/api/klinedata.pyc` | 61/64 | `<module>.kline_datetime_list` | \| #13/#14 \| `klinedata.kline_datetime_list`、`api_base.get_history_df` \| 5→1 压形（`time_count -= 1` 与其后循环测试算术）＋ 别处 1→9 摊开 \| 具名 \| |
| `IQCommon/logger/handlers.pyc` | 29/30 | `<module>.TWHThreadController._target` | \| `handlers.TWHThreadController._target` \| **+2** \| 一对 `LOAD_CONST None/RETURN_VALUE` 未发（`orig[75:77]`） \| **#15** \| |
| `IQCommon/strategy/wizard_quant_api.pyc` | 55/58 | `<module>.filter_desicion` | \| `wizard_quant_api.filter_desicion` \| −2 \| ≤3 指令的小摊开 \| #14 邻面，派单前逐读 \| |
| `IQCommon/strategy/wizard_quant_api.pyc` | 55/58 | `<module>.get_DMI.calculate_di.<genexpr>` | \| `COPY_AMBIG`（同路径副本不唯一，**拒判**） \| 2 \| `wizard_quant_api.get_DMI.calculate_di.<genexpr>` ×2（orig 3 副本 / prod 3 副本） \| 须人工按出现次序定标后才可开票 \| |
| `IQCommon/strategy/wizard_quant_api.pyc` | 55/58 | `<module>.get_DMI.calculate_di.<genexpr>` | \| `COPY_AMBIG`（同路径副本不唯一，**拒判**） \| 2 \| `wizard_quant_api.get_DMI.calculate_di.<genexpr>` ×2（orig 3 副本 / prod 3 副本） \| 须人工按出现次序定标后才可开票 \| |
| `IQCommon/util/trade_info_utils.pyc` | 37/41 | `<module>.kill_trade_process` | \| `TRANSPOSED`（两条跳转目标**互相换位**） \| 1 \| `trade_info_utils.kill_trade_process` \| #14 \| |
| `IQCommon/util/trade_info_utils.pyc` | 37/41 | `<module>.get_trade_status` | \| `TARGET_ONLY`（**全部差都是同 opcode 仅目标不同，零内容差**） \| **8** \| `bar._history_bars`、`strategy_universe._on_clear_de_listed`、`load_daily.<module>`、`strategy.tick_worker_thread`、`trade_info_utils.get_trade_status`、`trade_live_broker.get_ipo_stocks`、`trade_live_broker.rzrq_credit_order`、`trade_live_broker._ |
| `IQCommon/util/trade_info_utils.pyc` | 37/41 | `<module>.query_trade_strategy_info` | \| `trade_info_utils.query_trade_strategy_info` \| **0** \| 两处内联（各 +1）与一处共用尾缺失（−2）相抵 ⇒ **净 0 不等于无缺陷** \| **#15** \| |
| `IQCommon/util/trade_info_utils.pyc` | 37/41 | `<module>.query_strategy_id` | \| `trade_info_utils.query_strategy_id` \| **+1** \| 一处 `JUMP_FORWARD → 共用尾` 被写成内联 `LOAD_CONST None; RETURN_VALUE`，且另一处共用尾 2 条未发 \| **#15** \| |
| `IQData/api/api_base.pyc` | 27/28 | `<module>.get_history_df` | \| #13/#14 \| `klinedata.kline_datetime_list`、`api_base.get_history_df` \| 5→1 压形（`time_count -= 1` 与其后循环测试算术）＋ 别处 1→9 摊开 \| 具名 \| |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | 43/45 | `<module>.RealQuoteData.get_real_minute_kline` | \| `real_quote.get_real_minute_kline` \| −2 \| 同上 \| 同上 \| |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | 43/45 | `<module>.RealQuoteData.get_tick_direction` | \| `real_quote.get_tick_direction` \| 11 \| **全部 −2 字节**（如 `RETURN_VALUE@1572→@1574`、`LOAD_FAST redata@1102→@1104`） \| 函数前部**多插了一条 2 字节指令**（`net = del 11/ins 12` 与之一致）⇒ **1 个缺陷**，不是 11 个 \| |
| `IQEngine/core/bar.pyc` | 84/85 | `<module>.BarData._history_bars` | \| **1** \| **#14（`TARGET_ONLY` 8 条）** \| **4 个整文件**：`bar` 84/85、`strategy_universe` 10/11、`load_daily` 26/27、`strategy` 26/27（`_history_bars`/`_on_clear_de_listed`/`<module>`/`tick_worker_thread` 各自是所在文件的**唯一**失败单元） \| 零内容差 ⇒ 一条落点判据即可，无共要件、无省略纠缠 \| |
| `IQEngine/core/strategy/strategy_universe.pyc` | 10/11 | `<module>.StrategyUniverse._on_clear_de_listed` | \| **1** \| **#14（`TARGET_ONLY` 8 条）** \| **4 个整文件**：`bar` 84/85、`strategy_universe` 10/11、`load_daily` 26/27、`strategy` 26/27（`_history_bars`/`_on_clear_de_listed`/`<module>`/`tick_worker_thread` 各自是所在文件的**唯一**失败单元） \| 零内容差 ⇒ 一条落点判据即可，无共要件、无省略纠缠 \| |
| `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` | 35/37 | `<module>.future_order` | \| 4 \| #13 次刀 \| `order_api` 35/37（`option_order`+`future_order`）、`__init__`(risk) 41/43、`real_quote` 43/45 \| 各自 del/ins 同形，且无 #16 共要件 \| |
| `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` | 35/37 | `<module>.option_order` | \| 4 \| #13 次刀 \| `order_api` 35/37（`option_order`+`future_order`）、`__init__`(risk) 41/43、`real_quote` 43/45 \| 各自 del/ins 同形，且无 #16 共要件 \| |
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | 26/27 | `<module>.Strategy.tick_worker_thread` | \| **1** \| **#14（`TARGET_ONLY` 8 条）** \| **4 个整文件**：`bar` 84/85、`strategy_universe` 10/11、`load_daily` 26/27、`strategy` 26/27（`_history_bars`/`_on_clear_de_listed`/`<module>`/`tick_worker_thread` 各自是所在文件的**唯一**失败单元） \| 零内容差 ⇒ 一条落点判据即可，无共要件、无省略纠缠 \| |
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 12/13 | `<module>.RealtimeEventSource.clock_worker` | \| #13 \| `realtime_event_source.clock_worker`(144/27) \| 一形三态：`if persist_flag is not False:` 110 条体被跳 ＋ 17 条块搬到循环后 ＋ 3 处目标差 \| 具名 \| |
| `IQEngine/plugins/plugin_system_matcher/matcher.pyc` | 16/17 | `<module>.DefaultMatcher.match` | \| 2 \| #13 P0（**在飞**） \| `matcher` 16/17 → 17/17 \| 单条被吞语句 \| |
| `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` | 41/43 | `<module>.PluginRiskCalculation._on_publish_after_trading_end` | \| #14 邻面 \| `__init__._on_publish_after_trading_end`(2/2) \| 函数内 `import`（`IMPORT_NAME`+`IMPORT_FROM` 成对消失）＋小摊开 \| 具名 \| |
| `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` | 41/43 | `<module>.PluginRiskCalculation._save_testds_to_csv` | \| `LOSS`（删多于插，**17 条逐一列全**） \| **17** \| `matcher.DefaultMatcher.match`(del25/ins15，**在飞 #13 P0**)、`__init__`(risk)`_on_publish_after_trading_end`、`__init__`(risk)`_save_testds_to_csv`、`quote.build_current_period_df`、`quote.get_real_from_zeromq`(del36/ins34)、`quote.run_individual_transform`(del84)、 |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | `<module>.TradeLiveBroker._process_order` | \| 5 \| #13＋**#16 共要件** \| `trade_live_broker` 118/128 的 `_process_order`/`_process_cancel_order`/`_trade_status_handle` \| del 471/300/18，须先应用 `RAVED_R10_B126.patch`（见 `ADJUDICATION_R10_B126_REVERTED.md` §四） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | `<module>.TradeLiveBroker._process_tick_order` | \| `TARGET_ONLY`（**全部差都是同 opcode 仅目标不同，零内容差**） \| **8** \| `bar._history_bars`、`strategy_universe._on_clear_de_listed`、`load_daily.<module>`、`strategy.tick_worker_thread`、`trade_info_utils.get_trade_status`、`trade_live_broker.get_ipo_stocks`、`trade_live_broker.rzrq_credit_order`、`trade_live_broker._ |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | `<module>.TradeLiveBroker._process_cancel_order` | \| 5 \| #13＋**#16 共要件** \| `trade_live_broker` 118/128 的 `_process_order`/`_process_cancel_order`/`_trade_status_handle` \| del 471/300/18，须先应用 `RAVED_R10_B126.patch`（见 `ADJUDICATION_R10_B126_REVERTED.md` §四） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | `<module>.TradeLiveBroker._sync_worker` | \| 未具名 \| `wizard_quant_api.filter_desicion`(−2)、`klinedata.get_multiminute_his_data`(−1)、`klinedata.get_kline_by_count_new`(0)、`quote.check_frequency`(−1)、`quote.get_individual_data`(−1)、`quote.run_tick_socket`(27/28 搬位)、`trade_live_broker._sync_worker`(178/180 链式比较腿＋搬位)、`trade_live_broker.etf_bask |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | `<module>.TradeLiveBroker._trade_status_handle` | \| 5 \| #13＋**#16 共要件** \| `trade_live_broker` 118/128 的 `_process_order`/`_process_cancel_order`/`_trade_status_handle` \| del 471/300/18，须先应用 `RAVED_R10_B126.patch`（见 `ADJUDICATION_R10_B126_REVERTED.md` §四） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | `<module>.TradeLiveBroker.etf_basket_order` | \| `MIXED`（有内容增删但净差为 0） \| **5** \| `trade_live_broker.etf_basket_order`(tgt32)、`api_base.get_history_df`(tgt14)、`klinedata.get_kline_by_count_new`、`klinedata.kline_datetime_list`(tgt25)、`trade_info_utils.query_trade_strategy_info`(**属 #15**) \| `etf_basket_order`/`get_kline_by_count_new` 主体是目标差＝**# |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | `<module>.TradeLiveBroker.etf_purchase_redemption` | \| #13 \| `trade_live_broker.etf_purchase_redemption`(11/1) \| 属性链截断 \| 半具名 \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | `<module>.TradeLiveBroker.rzrq_credit_order` | \| `TARGET_ONLY`（**全部差都是同 opcode 仅目标不同，零内容差**） \| **8** \| `bar._history_bars`、`strategy_universe._on_clear_de_listed`、`load_daily.<module>`、`strategy.tick_worker_thread`、`trade_info_utils.get_trade_status`、`trade_live_broker.get_ipo_stocks`、`trade_live_broker.rzrq_credit_order`、`trade_live_broker._ |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | `<module>.TradeLiveBroker.ipo_stocks_order` | \| `trade_live_broker.ipo_stocks_order` \| +1 \| 35 处目标差 + 1 条净少 \| #14（D 档禁按 35 记账） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | `<module>.TradeLiveBroker.get_ipo_stocks` | \| `TARGET_ONLY`（**全部差都是同 opcode 仅目标不同，零内容差**） \| **8** \| `bar._history_bars`、`strategy_universe._on_clear_de_listed`、`load_daily.<module>`、`strategy.tick_worker_thread`、`trade_info_utils.get_trade_status`、`trade_live_broker.get_ipo_stocks`、`trade_live_broker.rzrq_credit_order`、`trade_live_broker._ |
| `fly/data/quote.pyc` | 86/92 | `<module>.Quote.build_current_period_df` | \| #13 \| `quote.build_current_period_df`(12/2) \| 函数尾被吞：`tempdict['is_open'] = …` ＋ `pandas.DataFrame(tempdict, index=…)` 构造整串消失，产物只剩 `POP_TOP; LOAD_CONST None` \| 具名 \| |
| `fly/data/quote.pyc` | 86/92 | `<module>.Quote.check_frequency` | \| `quote.check_frequency` / `quote.get_individual_data` \| −1 / −1 \| 同上 \| 同上 \| |
| `fly/data/quote.pyc` | 86/92 | `<module>.Quote.get_real_from_zeromq` | \| `quote.get_real_from_zeromq` \| 31 \| 混合：部分 −2（同为位移影子），部分是**真落点差** \| 真差处读回：`@174 JUMP_FORWARD` 与 `@178 POP_JUMP_FORWARD_IF_FALSE` 应进 `POP_TOP; LOAD_CONST None; LOAD_FAST flag; BUILD_TUPLE 2; RETURN_VALUE`＝**共用尾 `return None, flag`**，产物在该块前**多插了一条 `JUMP_FORWARD@1024→1034`** 把两条入边都从返回块前跳过去 \| |
| `fly/data/quote.pyc` | 86/92 | `<module>.Quote.run_individual_transform` | \| #13 \| `quote.run_individual_transform`(71/18) \| 循环体半丢：`socket.recv()` → `message` → 空数据告警分支 → `list(...)[0]` 一串被压成 2 条（三处独立 hunk 同形） \| 具名 \| |
| `fly/data/quote.pyc` | 86/92 | `<module>.Quote.run_tick_socket` | \| `EXTRA`（插多于删） \| **7** \| `quote.check_frequency`、`quote.get_individual_data`、`quote.run_tick_socket`、`real_quote.get_tick_direction`、`real_quote.get_real_minute_kline`、`wizard_quant_api.filter_desicion`、`klinedata.get_multiminute_his_data` \| #13/#14（多为「别处 1 条摊成 9 条」的挪位形） \| |
| `fly/data/quote.pyc` | 86/92 | `<module>.Quote.get_individual_data` | \| `quote.check_frequency` / `quote.get_individual_data` \| −1 / −1 \| 同上 \| 同上 \| |
| `fly/dumpload/load_daily.pyc` | 26/27 | `<module>` | \| **1** \| **#14（`TARGET_ONLY` 8 条）** \| **4 个整文件**：`bar` 84/85、`strategy_universe` 10/11、`load_daily` 26/27、`strategy` 26/27（`_history_bars`/`_on_clear_de_listed`/`<module>`/`tick_worker_thread` 各自是所在文件的**唯一**失败单元） \| 零内容差 ⇒ 一条落点判据即可，无共要件、无省略纠缠 \| |

UNREGISTERED 行数=0（应为 0）

## 违反条款口径（按族）

| 族 | 单元数 | 违反的算法条款 | 具名宿主 |
|---|---|---|---|
| 共用返回尾未认成单一落点（#15/B127 面） | 9（跨 6 文件） | §1.2 原则2 每块唯一归属 + §1.5 C3 守卫封闭（`:51810` 的 POP_TOP 巧合支） | `_r8_b121_implicit_tail_landing_sinks:51806-51821`；实测该站点对 handlers 目标单元**不执行**（在 G4b 于 :51799 即 break），真宿主在 `_loop_generate_while`（@404 从未被请求发射） |
| 落点/换位/ANCHOR（#14 面） | 20 上下 | §1.2 原则2 与原则4（父引用子入口） | IF_ELIF_CHAIN 的臂切分与汇合挑选：`_compute_arm_level_join`、`_check_elif_chain`、`_if_generate_full_elif_chain:16140-16177` |
| 语句省略（matcher / clock_worker / order_api / genexpr） | 11 | §1.5 C3（静默豁免：登记无日志无计数无回退）| `:19324` merge 认领 ∧ `:54896-54921` 递延交接（两条独立通道，单半修法产物逐字节不变）；`MIN_INSTRS_FOR_SUBSCR_ASSIGN`（:27=3，6 处使用）属 §2 G4 计数门债 |
| 摊开 MIXED/SPREAD/COPY_AMBIG | 6 | §1.3 单向数据流（跨层反查） | 表达式重建与臂体装配；`COPY_AMBIG` 两条按 co_consts 出现次序定标后方可判 |
| try 相关两面（load_daily / get_trade_status） | 含上 | §1.2 原则2 + §1.3 | `_compute_arm_level_join:3332-3349` 越区取汇合证据；`_try_body_terminates_abnormally:11609-11610` 在 `self.regions` 未填充阶段读它（实测 n_regions=0）致 try 体尾 break 丢失 |

注：族与单元数按 UNITMAP_R10 的分类键（是否存在 ≥4 指令 hunk）给出，同批数据只按一种口径统计，不与「首个差异」口径混加。
