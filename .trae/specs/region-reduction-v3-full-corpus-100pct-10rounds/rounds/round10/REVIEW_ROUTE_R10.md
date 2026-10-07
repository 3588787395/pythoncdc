# Round 10 起点路由：40 个残余单元按**一条链**重取（新字节口径）

口径写明，防再次桶间漂移：
- 基线报告＝`rounds/round9/after/shard*_report.json`（本轮封表读数，40 失败单元／16 文件）；
- 产物读**盘上现字节**（Round 9 落地代码重生成，`bad=0`），输入 `.pyc` 读盘（输入从不被重写）；
- 序列归一化**解析跳转目标**（相对跳转归一到其后第一条保留指令的 `opname@offset`），剔 `NOP/CACHE/EXTENDED_ARG`；
- 同名多实例按 **difflib 最佳匹配**配对，歧义显式标 `AMBIG×n`；
- 判定链**首中即止**（阈值随表打印）：
  1 `NORMALIZER_BLIND`：归一化序列已相等（我这仪器看不见差）
  2 `REORDER`：opcode 多重集相等（`net=0`，只有顺序/目标差）
  3 `LOSS_COLLAPSE`：存在 `orig≥3 块 → prod≤1` 的 hunk（语句被压成一条发射点）
  4 `LANDED_TARGET`：存在 **1→1 同 opcode、仅目标不同** 的孤立 hunk（落点轴）
  5 `LOSS`：净少指令；6 `EXTRA`：其余。
仪器：`D:/Temp/r9main/route10.py`，原表 `D:/Temp/r9main/route10.txt`（56 行，逐单元）。

## 一、类计数（40 单元，互斥完备）

| 类 | 单元数 | 归属 |
|---|---|---|
| `LOSS_COLLAPSE` | **14** | #13（省略族——含新靶形「5 指令语句被压成 1 条」） |
| `LANDED_TARGET` | **13** | #14（落点轴，但**净差不为 0 者同时压着内容差**，见 §三） |
| `REORDER` | **9** | #14 的**纯重排**面——这才是它的可翻正上界 |
| `NORMALIZER_BLIND` | **4** | 仪器盲区（≠无缺陷），其中 1 条属 #15 |
| 合计 | 40 | — |

⇒ **#14 的真实上限由 14 降为 9**（Round 9 落掉 2 条，且 3 条从「多重集相等」改判为带内容差）；
排产预期必须按 9 记账，不得按 14 或 35。

## 二、逐单元名单（完整路径尾段 + qualname 尾段）

**REORDER（9，`net=0`）**
`trade_info_utils.get_trade_status`(1 hunk)、`trade_info_utils.kill_trade_process`(3)、
`bar.BarData._history_bars`(1)、`strategy_universe.StrategyUniverse._on_clear_de_listed`(1)、
`strategy.Strategy.tick_worker_thread`(4)、`trade_live_broker.etf_basket_order`(39)、
`trade_live_broker.get_ipo_stocks`(1)、`trade_live_broker.rzrq_credit_order`(1)、`load_daily.<module>`(20)。
⇒ 五个文件只差 1 单元者在此列（`bar`/`strategy_universe`/`strategy`/`load_daily` 加 `api_base`…见 §四）。

**LANDED_TARGET（13）**
`klinedata.get_kline_by_count_new`、`klinedata.get_multiminute_his_data`、
`wizard_quant_api.filter_desicion`、`trade_info_utils.query_strategy_id`、
`trade_info_utils.query_trade_strategy_info`、`real_quote.get_real_minute_kline`、
`real_quote.get_tick_direction`、`plugin_system_risk_calculation._on_publish_after_trading_end`、
`trade_live_broker.ipo_stocks_order`、`quote.build_current_period_df`、
`quote.check_frequency`、`quote.get_individual_data`、`quote.get_real_from_zeromq`。

**LOSS_COLLAPSE（14，逐条名）**
`klinedata.kline_datetime_list`(net=0, 34 hunks)、`api_base.get_history_df`(net=0, 23)、
`order_api.future_order`(+27)、`order_api.option_order`(+39)、
`realtime_event_source.clock_worker`(**+113**)、`matcher.DefaultMatcher.match`(+10)、
`plugin_system_risk_calculation._save_testds_to_csv`(+7)、
`trade_live_broker._process_cancel_order`(**+293**, ratio 0.177)、
`trade_live_broker._process_order`(**+465**, ratio 0.131)、
`trade_live_broker._sync_worker`(+3)、`trade_live_broker._trade_status_handle`(+3)、
`trade_live_broker.etf_purchase_redemption`(+12)、
`quote.run_individual_transform`(+52)、`quote.run_tick_socket`(−1)。
⇒ 三个已定名机制在此列：属性链截断（`etf_purchase_redemption`）、链式比较腿丢失（`_sync_worker`）、
函数内 import 丢失（`_on_publish_after_trading_end` 本轮按链序落 `LANDED_TARGET`，其 collapse 未再命中）；
新增第四形＝§XVI 的「5 指令语句压成 1 条」（`kline_datetime_list`、`get_history_df`，两条 `net=0`）。

**NORMALIZER_BLIND（4）**
`handlers.TWHThreadController._target`(AMBIG×2)、`wizard_quant_api.get_DMI.calculate_di.<genexpr>`×2(AMBIG×2)、
`trade_live_broker._process_tick_order`。

## 三、三条必读告诫

1. **链序决定归属，不是事实互斥**。`LOSS_COLLAPSE` 排在 `LANDED_TARGET` 之前，
   所以「既有被压语句又有落点差」的单元一律落 `LOSS_COLLAPSE`；反之 `net≠0` 的 13 条
   `LANDED_TARGET` 也**不保证**只修落点就翻正。逐单元翻正仍只认名单，不认桶数。
2. **`NORMALIZER_BLIND` 不是「无缺陷」**。`handlers._target` 我上一轮按 G7 判据主张它缺
   `LOAD_CONST`+`RETURN_VALUE`，而**目标解析后的序列却判为相同** ⇒ 差异在常量身份/行号表一类
   我这仪器不覆盖的面上。#15 的靶面须以判据自身的 verdict 文本重取，不得由我的归一化代劳；
   这条盲区按「钉死盲目性」的纪律登记，禁止写成「已覆盖」。
3. **`AMBIG×2` 三处**（`handlers._target`、两个 `calculate_di.<genexpr>`）已按最佳匹配配对，
   配对分数比 `ratio` 打印在同列——若两可选项 `ratio` 相同则本表结论不可靠，须先人工定标再分派。

## 四、与轮门禁的关系（Round 10 交付路径）

盘上「只差 1 单元」文件 8 个，按本链的家别恰分为 **4 + 3 + 1**：

| 家别 | 文件（差 1 单元） | 数 |
|---|---|---|
| `REORDER` → **#14** | `IQEngine/core/bar.pyc`、`IQEngine/core/strategy/strategy_universe.pyc`、`IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc`、`fly/dumpload/load_daily.pyc` | **4** |
| `LOSS_COLLAPSE` → **#13** | `IQData/api/api_base.pyc`、`IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`、`IQEngine/plugins/plugin_system_matcher/matcher.pyc` | 3 |
| `NORMALIZER_BLIND` → **#15** | `IQCommon/logger/handlers.pyc` | 1 |

⇒ **最短门禁路径是 #14 的 `REORDER` 面：9 个纯重排单元里 4 个文件各只差 1 单元**，
一次正确的落点/重排修复理论上可同时翻正 4 个文件（远优于轮门禁要求的「≥1」）；
#13 次之（3 个文件，且其中 `matcher`/`clock_worker` 压着 +10/+113 的大差额，须先证小形）；
#15 只 1 个文件，且其差在我的仪器外（见 §三.2）。
在飞的 #16 改的是成员关系（`while True` 归还 `if`），落地后**必须用本链重取一次本表再派 #14/#13**，
否则派发的名单是改前的字节口径。
