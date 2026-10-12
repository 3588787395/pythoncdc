# 封表时点 12:24:15 / label round38 / 数据源 rounds/round38/after(8 shards)
单元 6614/6617 (99.9547%)  文件 400/402  残余文件 2 个  残余单元 3 条
对照 round37：单元 6613 -> 6614  文件 400 -> 400

| 文件 | 单元读数 | 失败单元（完整 qualname） | 台账登记的机制/条款 |
|---|---|---|---|
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 12/13 | `<module>.RealtimeEventSource.clock_worker` | \| realtime_event_source `clock_worker` \| −3/8（基 3d4f27de6d80ab6e） \| 已复原内容但错位约 1k 偏移 \| r63a \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 126/128 | `<module>.TradeLiveBroker._process_order` | \| trade_live_broker `_process_order` \| −68/14 \| 三元被当语句发（臂是裸串→docstring 丢弃）＋ f-string 语句真丢失（type_str 死存储） \| r64a \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 126/128 | `<module>.TradeLiveBroker._sync_worker` | \| trade_live_broker `_sync_worker` \| −3/5 \| 独占 continue 臂应先发（极性 @2 实测翻转） \| r62a \| |

UNREGISTERED 行数=0（应为 0）
