# 封表时点 03:08:14 / label round39 / 数据源 rounds/round39/after(8 shards)
单元 6615/6617 (99.9698%)  文件 400/402  残余文件 2 个  残余单元 2 条
对照 round38：单元 6614 -> 6615  文件 400 -> 400

| 文件 | 单元读数 | 失败单元（完整 qualname） | 台账登记的机制/条款 |
|---|---|---|---|
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 12/13 | `<module>.RealtimeEventSource.clock_worker` | \| realtime_event_source `clock_worker` \| −3/8（基 3d4f27de6d80ab6e） \| 已复原内容但错位约 1k 偏移 \| r63a \| |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 127/128 | `<module>.TradeLiveBroker._sync_worker` | \| trade_live_broker `_sync_worker` \| −3/5 \| 独占 continue 臂应先发（极性 @2 实测翻转） \| r62a \| |

UNREGISTERED 行数=0（应为 0）
