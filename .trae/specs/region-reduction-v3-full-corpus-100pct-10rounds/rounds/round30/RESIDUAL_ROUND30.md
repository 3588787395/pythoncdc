# 封表时点 02:39:36 / label round30 / 数据源 rounds/round30/after(8 shards)
单元 6603/6617 (99.7884%)  文件 396/402  残余文件 6 个  残余单元 14 条
对照 round29：单元 6600 -> 6603  文件 393 -> 396

| 文件 | 单元读数 | 失败单元（完整 qualname） | 台账登记的机制/条款 |
|---|---|---|---|
| `IQCommon/logger/handlers.pyc` | 29/30 | `<module>.TWHThreadController._target` | \| `handlers.TWHThreadController._target` \| **+2** \| 一对 `LOAD_CONST None/RETURN_VALUE` 未发（`orig[75:77]`） \| **#15** \| |
| `IQCommon/util/trade_info_utils.pyc` | 38/41 | `<module>.kill_trade_process` | \| `TRANSPOSED`（两条跳转目标**互相换位**） \| 1 \| `trade_info_utils.kill_trade_process` \| #14 \| |
| `IQCommon/util/trade_info_utils.pyc` | 38/41 | `<module>.query_trade_strategy_info` | \| `trade_info_utils.query_trade_strategy_info` \| **0** \| 两处内联（各 +1）与一处共用尾缺失（−2）相抵 ⇒ **净 0 不等于无缺陷** \| **#15** \| |
| `IQCommon/util/trade_info_utils.pyc` | 38/41 | `<module>.query_strategy_id` | \| `trade_info_utils.query_strategy_id` \| **+1** \| 一处 `JUMP_FORWARD → 共用尾` 被写成内联 `LOAD_CONST None; RETURN_VALUE`，且另一处共用尾 2 条未发 \| **#15** \| |
| `IQData/api/api_base.pyc` | 27/28 | `<module>.get_history_df` | \| #13/#14 \| `klinedata.kline_datetime_list`、`api_base.get_history_df` \| 5→1 压形（`time_count -= 1` 与其后循环测试算术）＋ 别处 1→9 摊开 \| 具名 \| |
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 12/13 | `<module>.RealtimeEventSource.clock_worker` | \| #13 \| `realtime_event_source.clock_worker`(144/27) \| 一形三态：`if persist_flag is not False:` 110 条体被跳 ＋ 17 条块搬到循环后 ＋ 3 处目标差 \| 具名 \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 121/128 | `<module>.TradeLiveBroker._process_order` | \| 5 \| #13＋**#16 共要件** \| `trade_live_broker` 118/128 的 `_process_order`/`_process_cancel_order`/`_trade_status_handle` \| del 471/300/18，须先应用 `RAVED_R10_B126.patch`（见 `ADJUDICATION_R10_B126_REVERTED.md` §四） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 121/128 | `<module>.TradeLiveBroker._process_cancel_order` | \| 5 \| #13＋**#16 共要件** \| `trade_live_broker` 118/128 的 `_process_order`/`_process_cancel_order`/`_trade_status_handle` \| del 471/300/18，须先应用 `RAVED_R10_B126.patch`（见 `ADJUDICATION_R10_B126_REVERTED.md` §四） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 121/128 | `<module>.TradeLiveBroker._sync_worker` | \| 未具名 \| `wizard_quant_api.filter_desicion`(−2)、`klinedata.get_multiminute_his_data`(−1)、`klinedata.get_kline_by_count_new`(0)、`quote.check_frequency`(−1)、`quote.get_individual_data`(−1)、`quote.run_tick_socket`(27/28 搬位)、`trade_live_broker._sync_worker`(178/180 链式比较腿＋搬位)、`trade_live_broker.etf_bask |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 121/128 | `<module>.TradeLiveBroker._trade_status_handle` | \| 5 \| #13＋**#16 共要件** \| `trade_live_broker` 118/128 的 `_process_order`/`_process_cancel_order`/`_trade_status_handle` \| del 471/300/18，须先应用 `RAVED_R10_B126.patch`（见 `ADJUDICATION_R10_B126_REVERTED.md` §四） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 121/128 | `<module>.TradeLiveBroker.etf_purchase_redemption` | \| #13 \| `trade_live_broker.etf_purchase_redemption`(11/1) \| 属性链截断 \| 半具名 \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 121/128 | `<module>.TradeLiveBroker.ipo_stocks_order` | \| `trade_live_broker.ipo_stocks_order` \| +1 \| 35 处目标差 + 1 条净少 \| #14（D 档禁按 35 记账） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 121/128 | `<module>.TradeLiveBroker.get_ipo_stocks` | \| `TARGET_ONLY`（**全部差都是同 opcode 仅目标不同，零内容差**） \| **8** \| `bar._history_bars`、`strategy_universe._on_clear_de_listed`、`load_daily.<module>`、`strategy.tick_worker_thread`、`trade_info_utils.get_trade_status`、`trade_live_broker.get_ipo_stocks`、`trade_live_broker.rzrq_credit_order`、`trade_live_broker._ |
| `fly/data/quote.pyc` | 91/92 | `<module>.Quote.run_individual_transform` | \| #13 \| `quote.run_individual_transform`(71/18) \| 循环体半丢：`socket.recv()` → `message` → 空数据告警分支 → `list(...)[0]` 一串被压成 2 条（三处独立 hunk 同形） \| 具名 \| |

UNREGISTERED 行数=0（应为 0）
