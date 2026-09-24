# Round 63 batch 5 — measured baseline on the LANDED R62 bytes
(dump: D:/Temp/opencode/r62gate/dump/f4_402.jsonl, arm f4 == worktree sha b9778ee0130865d55888; row = [fn, orig_instrs, decomp_instrs, jump_diffs, true_diffs])

## IQCommon/util/common_func.pyc  18/21 matched
  - get_crontab_execute_time: orig=93 decomp=81 jumpdiff=2 truediff=48  deficit=-12
  - get_kline_time_by_frequency_array: orig=231 decomp=228 jumpdiff=0 truediff=45  deficit=-3
  - get_kline_time_by_section: orig=210 decomp=190 jumpdiff=0 truediff=84  deficit=-20

## IQCommon/util/trade_info_utils.pyc  38/40 matched
  - get_trade_list: orig=339 decomp=323 jumpdiff=14 truediff=148  deficit=-16
  - trade_operation: orig=304 decomp=302 jumpdiff=2 truediff=40  deficit=-2

## IQData/utils/common_func.pyc  22/24 matched
  - get_kline_time_by_section: orig=210 decomp=190 jumpdiff=0 truediff=84  deficit=-20
  - handle_exrights: orig=276 decomp=268 jumpdiff=1 truediff=263  deficit=-8

## IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc  32/34 matched
  - future_order: orig=101 decomp=92 jumpdiff=2 truediff=36  deficit=-9
  - option_order: orig=83 decomp=73 jumpdiff=3 truediff=39  deficit=-10

## fly/simtradding/flyAccount.pyc  21/23 matched
  - _do_request: orig=436 decomp=429 jumpdiff=2 truediff=379  deficit=-7
  - init_connection: orig=42 decomp=41 jumpdiff=0 truediff=25  deficit=-1

## Notes
- Official ruler counts a function as matched only when its whole instruction series agrees; a `deficit=+0` row with nonzero truediff is a *shape* defect (control-flow / ordering), not a length one.
- Landing rules for a candidate: it must move its own named witness (the per-function tuple above) toward orig, and be inert-vs-improving elsewhere; a spec whose witness does not move is by definition not the mechanism.
