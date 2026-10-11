# 封表时点 15:38:46 / label round33 / 数据源 rounds/round33/after(8 shards)
单元 6609/6617 (99.8791%)  文件 399/402  残余文件 3 个  残余单元 8 条
对照 round32：单元 6608 -> 6609  文件 398 -> 399

| 文件 | 单元读数 | 失败单元（完整 qualname） | 台账登记的机制/条款 |
|---|---|---|---|
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 12/13 | `<module>.RealtimeEventSource.clock_worker` | \| #13 \| `realtime_event_source.clock_worker`(144/27) \| 一形三态：`if persist_flag is not False:` 110 条体被跳 ＋ 17 条块搬到循环后 ＋ 3 处目标差 \| 具名 \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 122/128 | `<module>.TradeLiveBroker._process_order` | \| 5 \| #13＋**#16 共要件** \| `trade_live_broker` 118/128 的 `_process_order`/`_process_cancel_order`/`_process_status_handle` \| del 471/300/18，须先应用 `RAVED_R10_B126.patch`（见 `ADJUDICATION_R10_B126_REVERTED.md` §四） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 122/128 | `<module>.TradeLiveBroker._process_cancel_order` | \| 5 \| #13＋**#16 共要件** \| `trade_live_broker` 118/128 的 `_process_order`/`_process_cancel_order`/`_process_status_handle` \| del 471/300/18，须先应用 `RAVED_R10_B126.patch`（见 `ADJUDICATION_R10_B126_REVERTED.md` §四） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 122/128 | `<module>.TradeLiveBroker._sync_worker` | \| 未具名 \| `wizard_quant_api.filter_desicion`(−2)、`klinedata.get_multiminute_his_data`(−1)、`klinedata.get_kline_by_count_new`(0)、`quote.check_frequency`(−1)、`quote.get_individual_data`(−1)、`quote.run_tick_socket`(27/28 搬位)、`trade_live_broker._sync_worker`(178/180 链式比较腿＋搬位)、`trade_live_broker.etf_bask |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 122/128 | `<module>.TradeLiveBroker._trade_status_handle` | \| 5 \| #13＋**#16 共要件** \| `trade_live_broker` 118/128 的 `_process_order`/`_process_cancel_order`/`_process_status_handle` \| del 471/300/18，须先应用 `RAVED_R10_B126.patch`（见 `ADJUDICATION_R10_B126_REVERTED.md` §四） \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 122/128 | `<module>.TradeLiveBroker.etf_purchase_redemption` | \| #13 \| `trade_live_broker.etf_purchase_redemption`(11/1) \| 属性链截断 \| 半具名 \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 122/128 | `<module>.TradeLiveBroker.ipo_stocks_order` | \| `trade_live_broker.ipo_stocks_order` \| +1 \| 35 处目标差 + 1 条净少 \| #14（D 档禁按 35 记账） \| |
| `fly/data/quote.pyc` | 91/92 | `<module>.Quote.run_individual_transform` | \| #13 \| `quote.run_individual_transform`(71/18) \| 循环体半丢：`socket.recv()` → `message` → 空数据告警分支 → `list(...)[0]` 一串被压成 2 条（三处独立 hunk 同形） \| 具名 \| |

UNREGISTERED 行数=0（应为 0）
