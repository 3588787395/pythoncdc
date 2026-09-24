# Round 63 batch 4 — measured baseline on the LANDED R62 bytes
(dump: D:/Temp/opencode/r62gate/dump/f4_402.jsonl, arm f4 == worktree sha b9778ee0130865d55888; row = [fn, orig_instrs, decomp_instrs, jump_diffs, true_diffs])

## IQCommon/common/main.pyc  29/33 matched
  - get_same_shard_server_ip_info: orig=192 decomp=173 jumpdiff=11 truediff=62  deficit=-19
  - get_server_ip_info: orig=194 decomp=166 jumpdiff=9 truediff=71  deficit=-28

## IQCommon/strategy/wizard_quant_api.pyc  51/53 matched
  - calculate_di: orig=75 decomp=73 jumpdiff=0 truediff=45  deficit=-2
  - params_analysis: orig=133 decomp=126 jumpdiff=1 truediff=117  deficit=-7

## IQData/api/api_base.pyc  23/25 matched
  - get_future_history_df: orig=973 decomp=957 jumpdiff=3 truediff=229  deficit=-16
  - get_history_df: orig=1742 decomp=1719 jumpdiff=14 truediff=1277  deficit=-23

## IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc  16/18 matched
  - get_kline_by_count: orig=854 decomp=841 jumpdiff=3 truediff=807  deficit=-13
  - get_price: orig=550 decomp=544 jumpdiff=4 truediff=475  deficit=-6

## IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc  32/35 matched
  - _on_publish_after_trading_end: orig=486 decomp=481 jumpdiff=3 truediff=33  deficit=-5
  - _save_testds_to_csv: orig=71 decomp=68 jumpdiff=7 truediff=19  deficit=-3
  - get_TradeMode_trades: orig=1839 decomp=1753 jumpdiff=4 truediff=1620  deficit=-86

## Notes
- Official ruler counts a function as matched only when its whole instruction series agrees; a `deficit=+0` row with nonzero truediff is a *shape* defect (control-flow / ordering), not a length one.
- Landing rules for a candidate: it must move its own named witness (the per-function tuple above) toward orig, and be inert-vs-improving elsewhere; a spec whose witness does not move is by definition not the mechanism.
