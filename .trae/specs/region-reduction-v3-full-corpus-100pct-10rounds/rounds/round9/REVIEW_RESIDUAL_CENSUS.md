# Round 9 开局：42 残差单元的实测普查与三轴切分（主代理）

封表时点：2026-10-07。before = `rounds/round8/after/shard*_report.json`（6575/6617、384/402）。
仪器：`nop_census.py`（逐指令 first-diff 分类）、`nop_census2.py`（剔除 NOP/CACHE/EXTENDED_ARG 后按序列
下标重标跳转目标再比对）、以及本轮新增的「单元指令数比」读数（下方表）。三者都是**代理仪器**，
判据仍只有 `scripts/pyc_verify.py`；任何候选修复必须回到 `single` + 全量门禁取证。

## I. 被否证的假设（如实入库）

`TradeLiveBroker._process_order` / `_process_cancel_order` / `_trade_status_handle` 三个单元的 first-diff
同形：orig 在 off=44 有一条承载行号 804（/989/1445）的 `NOP`，产物该偏移直接放真实指令。
查 `co_lines()`：原码语句在 803 行结束、NOP 承载 804、下一条语句起于 **820** 行 ⇒ 我先假设
「残差主体是行锚 NOP 造成的位移」（`TARGET_DELTA` 的偶数差值恰为 2 的倍数，NOP＝2 字节）。

两次独立否证：
1. 剔除 NOP/CACHE/EXTENDED_ARG 并重标跳转目标后，42 单元中 **`NOP_ONLY` = 0**；
2. 指令数比显示这三单元的差**不是位移而是缺失**（见 §II）。
⇒ Round 8 `REVIEW_NOP.md` 的「NOP 是足迹不是缺陷」在残差归因层面第二次得到支持；不再为 NOP 立票。

## II. 实测：产物把方法体「编译没了」

`_process_order` 的 code object：orig **520** 条指令，产物 **42** 条；`_process_cancel_order` 344 → 40；
`order_api.option_order` 94 → 55。产物的函数文本看着是完整的（`break` 之后仍有 30+ 行语句），
但那些语句**不在字节码里**。机制已用最小样例证实：CPython 3.11 会丢掉循环体内
`break` 之后的同块语句——

    def f(c, a, g, h):
        while c:
            if a:
                g(); continue
            break
            h()          # ← 编译后 h() 完全消失（co_names == ()）

⇒ 发射层在循环体中部放了一条**多余的无条件 `break`**，其后整个方法体被 CPython 视为死码丢弃。
文本完整、字节码截断，这正是 `compare_pyc` 报 "Different control flow" 而人工读产物看不出破绽的形态。

## III. 42 单元的三轴切分（按指令数比）

| 轴 | 判据 | 单元数 | 名单（节选） |
|---|---|---|---|
| **A 体吞并** | orig/dec ≥ 1.3 ⇒ 产物少掉成块语句 | **6** | `trade_live_broker._process_order` 520/42、`_process_cancel_order` 344/40、`order_api.option_order` 94/55、`order_api.future_order` 115/88、`wizard_quant_api.get_DMI.calculate_di.<genexpr>` 64/50（**两条单元**） |
| **B 一条之差** | \|orig−dec\| ≤ 3 | **14** | `klinedata.get_multiminute_his_data` 535/536、`real_quote.get_tick_direction` 297/298、`quote.check_frequency` 132/133、`quote.run_tick_socket` 347/348、`quote.get_individual_data` 354/355、`finance.get_fields` 177/178、`function.reconnect` 101/102、`wizard_quant_api.filter_desicion` 195/197、`real_quote.get_real_minute_kline` 280/283、`klinedata.kline_datetime_list` 413/417、`trade_live_broker._sync_worker` 412/410、`quote.get_real_from_zeromq` 793/791、`trade_info_utils.query_strategy_id` 118/117、`__init__._save_testds_to_csv` 81/75 |
| **C 等长错位** | 条数近乎相等、跳转**目标**不同 | **21** | `api_base.get_history_df` 1900/1900、`matcher.match` 800/790、`trade_live_broker.etf_basket_order` 769/769、`rzrq_credit_order` 786/786、`ipo_stocks_order` 1206/1203、`get_ipo_stocks` 497/497、`_process_tick_order` 188/188、`strategy.tick_worker_thread` 294/294、`strategy_universe._on_clear_de_listed` 70/70、`bar._history_bars` 66/66、`trade_info_utils.get_trade_status` 175/175、`query_trade_strategy_info` 123/123、`kill_trade_process` 673/673、`load_daily.<module>` 1017/1017、`quote.run_individual_transform` 412/359、`quote.build_current_period_df` 124/113、`realtime_event_source.clock_worker` 1442/1330、`handlers._target` 203/200、`__init__._on_publish_after_trading_end` 531/527、`klinedata.get_kline_by_count_new` 650/649、`etf_purchase_redemption` 427/415 |
| 无法映射 | `<module>` 单元名 | 1 | `load_daily.<module>` 已改由指令数读数覆盖 |

C 轴里剔 NOP 后**只有 1 处配对不同**的六个单元（`_process_tick_order` `JUMP_BACKWARD` 差 16、
`rzrq_credit_order` `JUMP_FORWARD` 差 28、`get_ipo_stocks` `POP_JUMP_FORWARD_IF_TRUE` 差 24、
`get_trade_status`、`bar._history_bars`、`strategy_universe._on_clear_de_listed`）是最经济的靶面：
结构几乎全对，只差**一条边的落点被换成相邻块**，属原则 4（入口引用语义）层面。

## IV. 取向与禁止项

- A 轴优先：无条件 `break` 的发射必须回到区域归约事实（该边是否为循环出口边、落点是否同区、
  出口之后是否还有未被认领的体语句），**不允许**用「发射后再搬语句」的事后修正（rules.md §1.3 单向数据流）。
  工单简报见 `FIX_BODY_SWALLOW_BRIEF.md`（根因已定位到 `IfRegion@318.else_blocks` 含块 44、
  `merge_block=3128`＝父循环 `back_edge_block`）。
- B/C 轴禁止并案：`_sync_worker` 是**测试极性反转**（orig `POP_JUMP_FORWARD_IF_TRUE→704`
  vs 产物 `POP_JUMP_FORWARD_IF_FALSE→562`），与 target-delta 不同轴。

## V. C 轴的紧致子族（补测：difflib 逐指令对齐，剔 NOP 后）

对 41 个可映射单元做「剔 NOP/CACHE/EXTENDED_ARG + 跳转目标改为序列下标」后的差异块计数：
**`NOP_ONLY_after_strip` 仍为 0**，而 **8 个单元只有 1–2 处差异、且每一处都是同 opcode、
只有跳转目标下标不同**：

    get_trade_status                    JUMP_FORWARD            to@155 vs to@150
    BarData._history_bars               POP_JUMP_FORWARD_IF_FALSE  to@32  vs ...
    StrategyUniverse._on_clear_de_listed POP_JUMP_FORWARD_IF_FALSE to@27  vs ...
    TradeLiveBroker._process_tick_order  JUMP_BACKWARD          to@24  vs to@20
    TradeLiveBroker.rzrq_credit_order    JUMP_FORWARD           to@496 vs to@491
    TradeLiveBroker.get_ipo_stocks       POP_JUMP_FORWARD_IF_TRUE to@230 vs ...
    load_daily <module>                  JUMP_FORWARD           to@666 vs to@684
    kill_trade_process / filter_desicion 各 2 处（POP_JUMP_FORWARD_IF_NONE 目标）

目标下标差为 4–5 条指令 ⇒ 区域边界附近的**语句排布次序**换了 4–5 条指令的位置，
而不是多写/少写语句。这 8 个单元是本轮单位成本最低的一族（其余单元的差块数 ≥5，最多 53）。
- 仪器已知缺陷：单元名 → code object 用路径尾段匹配，同名/嵌套宿主可能错配；
  本轮 §II/§III 的关键读数（520/42、344/40、94/55）已用 `co_firstlineno` + 唯一命中复核，
  确认**不是**错配而是真实截断。
