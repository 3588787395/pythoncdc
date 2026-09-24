# Round 63 batch 3 — measured baseline on the LANDED R62 bytes
(dump: D:/Temp/opencode/r62gate/dump/f4_402.jsonl, arm f4 == worktree sha b9778ee0130865d55888; row = [fn, orig_instrs, decomp_instrs, jump_diffs, true_diffs])

## IQCommon/graph.pyc  29/31 matched
  - _get_influence_task: orig=207 decomp=195 jumpdiff=2 truediff=124  deficit=-12
  - _process_task_queue: orig=378 decomp=378 jumpdiff=1 truediff=118  deficit=+0

## IQCommon/util/fileio_utils.pyc  12/14 matched
  - acquire: orig=96 decomp=93 jumpdiff=3 truediff=52  deficit=-3
  - write: orig=637 decomp=637 jumpdiff=4 truediff=519  deficit=+0

## IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc  11/12 matched
  - clock_worker: orig=1275 decomp=1286 jumpdiff=10 truediff=481  deficit=+11

## IQEngine/plugins/plugin_system_matcher/matcher.pyc  16/17 matched
  - match: orig=713 decomp=689 jumpdiff=9 truediff=524  deficit=-24

## fly/logger.pyc  28/30 matched
  - logging_process: orig=99 decomp=95 jumpdiff=2 truediff=62  deficit=-4
  - write_logging_thread: orig=113 decomp=113 jumpdiff=1 truediff=40  deficit=+0

## Notes
- Official ruler counts a function as matched only when its whole instruction series agrees; a `deficit=+0` row with nonzero truediff is a *shape* defect (control-flow / ordering), not a length one.
- Landing rules for a candidate: it must move its own named witness (the per-function tuple above) toward orig, and be inert-vs-improving elsewhere; a spec whose witness does not move is by definition not the mechanism.
