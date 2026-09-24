# Round 63 batch 1 — measured baseline on the LANDED R62 bytes
(dump: D:/Temp/opencode/r62gate/dump/f4_402.jsonl, arm f4 == worktree sha b9778ee0130865d55888; row = [fn, orig_instrs, decomp_instrs, jump_diffs, true_diffs])

## IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc  104/119 matched
  - _process_cancel_order: orig=293 decomp=292 jumpdiff=16 truediff=43  deficit=-1
  - _process_order: orig=454 decomp=396 jumpdiff=9 truediff=349  deficit=-58
  - _sync_worker: orig=349 decomp=347 jumpdiff=0 truediff=296  deficit=-2
  - _trade_status_handle: orig=114 decomp=112 jumpdiff=0 truediff=107  deficit=-2
  - after_trading_cancel_order: orig=155 decomp=155 jumpdiff=3 truediff=122  deficit=+0
  - etf_basket_order: orig=693 decomp=693 jumpdiff=11 truediff=216  deficit=+0
  - etf_purchase_redemption: orig=377 decomp=355 jumpdiff=2 truediff=100  deficit=-22
  - fund_transfer: orig=123 decomp=88 jumpdiff=1 truediff=57  deficit=-35
  - get_all_orders: orig=79 decomp=78 jumpdiff=2 truediff=24  deficit=-1
  - get_etf_stock_info: orig=144 decomp=117 jumpdiff=1 truediff=139  deficit=-27
  - get_max_amount: orig=201 decomp=213 jumpdiff=2 truediff=18  deficit=+12
  - ipo_stocks_order: orig=1075 decomp=1076 jumpdiff=10 truediff=437  deficit=+1
  - market_fund_transfer: orig=94 decomp=67 jumpdiff=1 truediff=41  deficit=-27
  - on_order_response: orig=445 decomp=444 jumpdiff=6 truediff=57  deficit=-1
  - on_trade_response: orig=392 decomp=391 jumpdiff=6 truediff=57  deficit=-1

## fly/data/quote.pyc  70/81 matched
  - build_current_period_df: orig=115 decomp=108 jumpdiff=5 truediff=12  deficit=-7
  - check_frequency: orig=121 decomp=120 jumpdiff=1 truediff=21  deficit=-1
  - check_limit: orig=330 decomp=311 jumpdiff=2 truediff=248  deficit=-19
  - get_individual_data: orig=312 decomp=311 jumpdiff=1 truediff=156  deficit=-1
  - get_price: orig=230 decomp=188 jumpdiff=0 truediff=227  deficit=-42
  - get_real_from_zeromq: orig=703 decomp=678 jumpdiff=0 truediff=660  deficit=-25
  - initImagedata: orig=243 decomp=225 jumpdiff=0 truediff=190  deficit=-18
  - load_bars_from_hundsun: orig=477 decomp=470 jumpdiff=0 truediff=464  deficit=-7
  - load_get_price: orig=171 decomp=136 jumpdiff=1 truediff=167  deficit=-35
  - run_individual_transform: orig=362 decomp=321 jumpdiff=2 truediff=263  deficit=-41
  - run_tick_socket: orig=306 decomp=307 jumpdiff=2 truediff=228  deficit=+1

## fly/data/quote_handler.pyc  55/57 matched
  - get_kline_binary: orig=129 decomp=128 jumpdiff=3 truediff=58  deficit=-1
  - get_kline_local: orig=760 decomp=682 jumpdiff=12 truediff=547  deficit=-78

## Notes
- Official ruler counts a function as matched only when its whole instruction series agrees; a `deficit=+0` row with nonzero truediff is a *shape* defect (control-flow / ordering), not a length one.
- Landing rules for a candidate: it must move its own named witness (the per-function tuple above) toward orig, and be inert-vs-improving elsewhere; a spec whose witness does not move is by definition not the mechanism.
