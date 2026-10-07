# Round 10 起点路由：40 个残余单元按**一条链**重取（新字节口径，含配对缺陷订正）

**订正声明（先于数据）**：本节首版把 3 条单元误标为 `NORMALIZER_BLIND`，根因是我自己又踩了一次
**按名字尾段配对**的老坑——`handlers.pyc` 里有两个 `_target`
（`TWHThreadController._target` 失败、`TWHThreadRotatingFileHandler._target` 通过），
最佳匹配在**错的孪生体**上取到 `ratio=1.000`，于是把真有差的单元判成「看不见」。
现改为**按完整 qualname 路径配对**（`/` + unit 的点换斜杠），同名多实例只在**同路径副本**之间取最佳匹配并标 `AMBIG×n`。
订正后 `handlers._target` 读数 `net=+2 / 17 hunks` ⇒ **#15 的前提（缺 `LOAD_CONST`+`RETURN_VALUE`）成立**，
先前那条「#15 的差在我仪器之外」的结论作废。

口径写明，防再次桶间漂移：
- 基线报告＝`rounds/round9/after/shard*_report.json`（本轮封表读数，40 失败单元／16 文件）；
- 产物读**盘上现字节**（Round 9 落地代码重生成，`bad=0`），输入 `.pyc` 读盘（输入从不被重写）；
- 序列归一化**解析跳转目标**（相对跳转归一到其后第一条保留指令的 `opname@offset`），剔 `NOP/CACHE/EXTENDED_ARG`，
  非跳转指令带 `argrepr`（常量身份在比较面内）；
- 判定链**首中即止**（仪器 `D:/Temp/r9main/route10.py`，原表 `D:/Temp/r9main/route10b.txt`）：
  1 `NORMALIZER_BLIND` 序列已等 → 2 `REORDER` opcode 多重集相等(`net=0`) →
  3 `LOSS_COLLAPSE` 存在 `orig≥3 → prod≤1` 的 hunk → 4 `LANDED_TARGET` 存在 **1→1 同 opcode 仅目标不同** 的孤立 hunk →
  5 `LOSS` 净少 → 6 `EXTRA` 其余。

## 一、类计数（40 单元，互斥完备）

| 类 | 单元数 | 归属 |
|---|---|---|
| `LOSS_COLLAPSE` | **14** | #13（省略族，含「5 指令语句压成 1 条」新形） |
| `LANDED_TARGET` | **14** | #14 落点面 + #15（`handlers._target` 在此列） |
| `REORDER` | **9** | #14 的**纯重排**面＝它的可翻正上界 |
| `NORMALIZER_BLIND` | **3** | 真实盲区 1 条 + 同路径歧义 2 条（见 §三） |
| 合计 | 40 | — |

⇒ **#14 的纯重排上限＝9**（Round 9 落掉 2 条，另有 3 条带内容差不再算纯重排）；排产按 9 记账，不按 14/35。

## 二、逐单元名单

**REORDER（9，`net=0`）** `trade_info_utils.get_trade_status`(1 hunk)、`trade_info_utils.kill_trade_process`(3)、
`bar.BarData._history_bars`(1)、`strategy_universe.StrategyUniverse._on_clear_de_listed`(1)、
`strategy.Strategy.tick_worker_thread`(4)、`trade_live_broker.etf_basket_order`(39)、
`trade_live_broker.get_ipo_stocks`(1)、`trade_live_broker.rzrq_credit_order`(1)、`load_daily.<module>`(20)。

**LANDED_TARGET（14）** `klinedata.get_kline_by_count_new`、`klinedata.get_multiminute_his_data`、
`wizard_quant_api.filter_desicion`、`trade_info_utils.query_strategy_id`、`trade_info_utils.query_trade_strategy_info`、
`real_quote.get_real_minute_kline`、`real_quote.get_tick_direction`、
`plugin_system_risk_calculation._on_publish_after_trading_end`、`trade_live_broker.ipo_stocks_order`、
`quote.build_current_period_df`、`quote.check_frequency`、`quote.get_individual_data`、
`quote.get_real_from_zeromq`、**`handlers.TWHThreadController._target`**（`net=+2`，#15 的靶）。

**LOSS_COLLAPSE（14）** `klinedata.kline_datetime_list`(net=0, 34h)、`api_base.get_history_df`(net=0, 23h)、
`order_api.future_order`(+27)、`order_api.option_order`(+39)、`realtime_event_source.clock_worker`(**+113**)、
`matcher.DefaultMatcher.match`(+10)、`plugin_system_risk_calculation._save_testds_to_csv`(+7)、
`trade_live_broker._process_cancel_order`(**+293**)、`trade_live_broker._process_order`(**+465**)、
`trade_live_broker._sync_worker`(+3)、`trade_live_broker._trade_status_handle`(+3)、
`trade_live_broker.etf_purchase_redemption`(+12)、`quote.run_individual_transform`(+52)、
`quote.run_tick_socket`(−1)。
⇒ #13 的四种机制：属性链截断（`etf_purchase_redemption`）、链式比较腿丢失（`_sync_worker`）、
异常解包丢失（`get_real_from_zeromq`，本轮按链序落 `LANDED_TARGET`）、
「5 指令语句压成 1 条 ∧ 别处 1 条摊成 9 条」（`kline_datetime_list`、`get_history_df`，两条 `net=0`）。

**NORMALIZER_BLIND（3）** `trade_live_broker._process_tick_order`（真盲区，见 §三.2）、
`wizard_quant_api.get_DMI.calculate_di.<genexpr>` ×2（**同路径 3 副本**，`AMBIG×3`，
配对结论不可靠，须人工定标后再分派）。

## 三、三条必读告诫

1. **链序决定归属，不是事实互斥**。`LOSS_COLLAPSE` 排在 `LANDED_TARGET` 之前，故「既压语句又有落点差」
   的单元一律落前者；`net≠0` 的 `LANDED_TARGET` 也不保证只修落点就翻正。翻正只认逐单元名单。
2. **`_process_tick_order` 的盲区已被逐层夹钳**（主代理 stdlib 实测，同一解释器）：
   保留指令序列（含解析后的跳转目标与 `argrepr`）、`NOP` 数（2/2）、`jump→NOP` 结构
   （`POP_JUMP_FORWARD_IF_FALSE@176 → @180` 两侧同）、`co_names`、`co_varnames`、`co_freevars`、
   `co_exceptiontable`（`c11b36422b00c22b1b430603` 两侧逐字节相同）、嵌套 code object 数（0/0）**全部相等**；
   唯一差是**绝对行号表**（orig 起于 941，prod 起于 496）。判据仍报 `Different control flow`。
   ⇒ 两种解释待定标：(a) 判据的逐单元归属按反编译 AST 的名字/位置索引，与我的 qualname 路径不同源；
   (b) 判据对**行号相对结构**敏感。若 (b) 成立，本形还牵着 `calculate_di` 两条。
   **这条按盲区登记，禁止写成「已覆盖」或「无差异」**；其成本＝1 单元，且不卡任何文件翻正
   （`trade_live_broker` 差 10 单元）。
3. **同路径歧义必须人工定标**：`calculate_di.<genexpr>` 的 3 个副本共享 qualname 路径，
   最佳匹配在此无效（`ratio` 全等时配对结果不可复现）。分派前要先用出现次序定标。

4. **本表的 `LANDED_TARGET` 不等于「归 #14」**。逐内容差复跑后改判：
   `trade_info_utils.query_strategy_id` 与 `query_trade_strategy_info` 的真差是**共享隐式尾声 epilogue
   未被认成单一落点**（产物逐路内联 `LOAD_CONST None/RETURN_VALUE`、共用尾不发），与
   `handlers.TWHThreadController._target` 同一判据面 ⇒ 三条并入 **#15**；本表把它们列在
   `LANDED_TARGET` 是链序（先查 hunk 形状再查语义）所致，**分派以 #15 简报为准**。
   `trade_info_utils` 剩下两条（`get_trade_status` 纯目标偏移、`kill_trade_process` 两跳转目标换位）仍属 #14。

## 四、与轮门禁的关系（Round 10 交付路径）

盘上「只差 1 单元」文件 8 个，恰分为 **4 + 3 + 1**：

| 家别 | 文件 | 数 |
|---|---|---|
| `REORDER` → **#14** | `IQEngine/core/bar.pyc`、`IQEngine/core/strategy/strategy_universe.pyc`、`IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc`、`fly/dumpload/load_daily.pyc` | **4** |
| `LOSS_COLLAPSE` → **#13** | `IQData/api/api_base.pyc`、`IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`、`IQEngine/plugins/plugin_system_matcher/matcher.pyc` | 3 |
| `LANDED_TARGET` → **#15** | `IQCommon/logger/handlers.pyc` | 1 |

⇒ **最短门禁路径是 #14 的 `REORDER` 面**：9 个纯重排单元里 4 个文件各只差 1 单元，
一次正确的落点/重排修复理论上可同时翻正 4 个文件（远超轮门禁要求的「≥1」）。
#13 次之（3 个文件，其中 `clock_worker` 压着 +113、`get_history_df`/`kline_datetime_list` 是 `net=0` 的纯压形，
先证小形再碰大形）。#15 单文件单单元，前提已被订正后的读数证实。
在飞的 #16 改成员关系（`while True` 归还体内 `if`），落地后**必须用本链重取本表再派 #14/#13**。
