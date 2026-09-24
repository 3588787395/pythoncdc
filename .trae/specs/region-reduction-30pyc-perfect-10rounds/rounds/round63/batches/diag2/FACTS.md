# Round 63 batch 2 — measured baseline on the LANDED R62 bytes
(dump: D:/Temp/opencode/r62gate/dump/f4_402.jsonl, arm f4 == worktree sha b9778ee0130865d55888; row = [fn, orig_instrs, decomp_instrs, jump_diffs, true_diffs])

## IQCommon/api/klinedata.pyc  42/45 matched
  - get_all_real_daily_kline: orig=188 decomp=187 jumpdiff=3 truediff=26  deficit=-1
  - get_multiminute_his_data: orig=479 decomp=478 jumpdiff=3 truediff=16  deficit=-1
  - kline_datetime_list: orig=389 decomp=389 jumpdiff=9 truediff=228  deficit=+0

## IQData/plugins/plugin_system_realquote/real_quote.pyc  39/44 matched
  - get_cache_l2_data: orig=337 decomp=335 jumpdiff=2 truediff=313  deficit=-2
  - get_cache_l2_data_by_one: orig=321 decomp=320 jumpdiff=2 truediff=300  deficit=-1
  - get_real_minute_kline: orig=253 decomp=254 jumpdiff=3 truediff=197  deficit=+1
  - get_tick_direction: orig=259 decomp=258 jumpdiff=3 truediff=102  deficit=-1
  - one_prod_to_ndarray: orig=605 decomp=607 jumpdiff=5 truediff=424  deficit=+2

## IQEngine/utils/scheduler.pyc  42/45 matched
  - get_checked_time: orig=106 decomp=106 jumpdiff=0 truediff=43  deficit=+0
  - is_run_interval_time_now: orig=225 decomp=201 jumpdiff=2 truediff=173  deficit=-24
  - run_daily: orig=77 decomp=71 jumpdiff=0 truediff=56  deficit=-6

## Notes
- Official ruler counts a function as matched only when its whole instruction series agrees; a `deficit=+0` row with nonzero truediff is a *shape* defect (control-flow / ordering), not a length one.
- Landing rules for a candidate: it must move its own named witness (the per-function tuple above) toward orig, and be inert-vs-improving elsewhere; a spec whose witness does not move is by definition not the mechanism.
