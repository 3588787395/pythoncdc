# FIX R14-04 — 同目标真值边判据：`not A and not B` 被发成 `A or B`（未落地，共要件）

尺：`scripts/pyc_verify.py single <pyc> --source <pycdc 产物>`；基线字节 `region_analyzer 640d33a77dcb71c2` / `region_ast_generator 851b0723732a2402`。
补丁文本：`arms/r14_04_and_polarity_reps.py`（REPS_STATE 三处 + OLD_AO/NEW_AO 一处，作用点 `region_ast_generator.py:24233-24239`、`:21195`、`:20819`、`:385`）。

## 判据（结构事实，无名字/偏移/指令计数）

在 `_if_extract_condition_from_instructions` 的「链式比较 + rhs 操作数」拼接处：头块（链式比较取**末段**）与 rhs 操作数块（同样取链式比较末段）的条件跳转**都是 IF_TRUE 且落在同一个块**时，形状是 `not A and not B`（两条真值边都跳过体），而不是 `A or B`（or 短路的头成员真值边落在体入口）。此时逐员 `_negate_expr` 取反、臂体取 rhs 末段的落空边、**不登记 else**（rhs 的跳转目标是自然续接点），并用状态位 `_r14_and_ext` 复用既有 or 扩展臂装配（`_has_or_ext` 原来只看 then/else 双双非空）。

## 电池读数（本轮实测，判据只喂产物）

```
MODE andor delta 39
m01_and_not_cc           success units=2/2 succ time_count -= 1 | if frequency == 'MIN' and time_count > count: | return 1 | return 0
m02_plain_and_not        success units=2/2 succ def g(a, b, c, d, x): | if not (a > b or c > d): | x -= 1 | return x
m03_cc_only              success units=2/2 succ def g(a, b, c, d, e, f, x): | if not a > b > c and not d > e: | x -= 1 | return x
m04_cc_cc                failure units=1/2 succ if not a > b > c and not d > e > f: | pass | x -= 1 | return x
```

m04（两操作数都是链式比较）仍红：产物多一条 `pass`——then 落到了链式比较的清理块；下一版应沿用「清理/连接块跟随其后继」的既有做法取真正的体首块。

## 语料面板（13 文件，实测零回归，0 翻正）

quotation（153 单元尺）：

```
quotation.pyc              success units=153/153 su fails=0 
restored True 851b0723732a2402
```

12 个残余文件：

```
klinedata.pyc              failure units=63/64 succ fails=1 <module>.get_kline_by_count_new
handlers.pyc               failure units=29/30 succ fails=1 <module>.TWHThreadController._target
wizard_quant_api.pyc       failure units=55/58 succ fails=3 <module>.filter_desicion,<module>.get_DMI.calculate_di.<gene
trade_info_utils.pyc       failure units=38/41 succ fails=3 <module>.kill_trade_process,<module>.query_trade_strategy_in
api_base.pyc               failure units=27/28 succ fails=1 <module>.get_history_df
real_quote.pyc             failure units=43/45 succ fails=2 <module>.RealQuoteData.get_real_minute_kline,<module>.RealQu
order_api.pyc              failure units=35/37 succ fails=2 <module>.future_order,<module>.option_order
strategy.pyc               failure units=26/27 succ fails=1 <module>.Strategy.tick_worker_thread
realtime_event_source.pyc  failure units=12/13 succ fails=1 <module>.RealtimeEventSource.clock_worker
__init__.pyc               failure units=41/43 succ fails=2 <module>.PluginRiskCalculation._on_publish_after_trading_end
trade_live_broker.pyc      failure units=118/128 su fails=10 <module>.TradeLiveBroker._process_order,<module>.TradeLiveBr
quote.pyc                  failure units=86/92 succ fails=6 <module>.Quote.build_current_period_df,<module>.Quote.check_
```

api_base 的失败单元 `get_history_df` 由基线 `len 1881/1881 net=+0 hunks=20 real=5 reloc=15 deleted=36 inserted=36` 变为 `len 1881/1881 net=+0 hunks=2 real=0 reloc=2 deleted=2 inserted=2` —— 五条真差全部消失，只剩 @994/@1006 两处 `IF_TRUE` 落点差（属 R14-05，见下）。单元仍红 ⇒ 文件仍 27/28。

## 裁决

0 单元翻正 ⇒ 按「fires without flips 不落地」本轮不落地；补丁与判据保留为共要件。core/ 收尾实测：`git status --porcelain -- core/` 0 行，`region_ast_generator.py` 仍 851b0723732a2402。

## R14-05（strategy 与该两处落点差的正镜像判据，已定位到可复用谓词）

需要「正极性 or 链不取反」的判据。实测 strategy 的 IfRegion@512：`merge=568`、`then_blocks` 被污染（[536,552,562,564,612,628,…]，**不含体首块 568**），`_then_entry_offsets_excluding_connectors` 同样不含 568 ⇒ 「真值边落在 then 入口」这条测试在该形失效（臂成员归属本身就是 R14-02 的未解结）。可直接复用的同层判据是既有 `_chain_block_is_pure`（`:20433`）：末成员的**落空边**进入的块若含 STORE_*/POP_TOP 等用户语句⇒ 那条边才是体（即 `not A and not B`，需要取反，R14-04 已覆盖）；若落空边仍是纯求值块（如 @524→@536 的链式比较操作数）⇒ 链仍在续接，正极性 `or`，不取反、落点应保持体首块。
