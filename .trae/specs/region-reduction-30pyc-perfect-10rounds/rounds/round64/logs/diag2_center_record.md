# diag2 (R64) — center record at the moment its agent hit the 150-turn cap

Agent `acdf74341001d72b4` failed with "Reached the maximum turn limit (150)" after ~29 min / 158 tool
uses, having measured but not documented. Nothing it wrote was lost; this file records what the center
read directly out of `diag2/dump/*.jsonl` before launching a continuation agent.

## Landed bytes verified before trusting any number
- `core/cfg/region_ast_generator.py` sha256 `7ec41fa2f9cdd5d62c1a…`, 3 086 600 B (R63 landing)
- `core/cfg/region_analyzer.py` sha256 `c694d2514eb2f2b21ccf…`, 1 721 959 B
- both `git hash-object` == `git rev-parse HEAD:<path>`; worktree clean of tracked edits

## Measurements read from diag2/dump (4 targets + 11 pinned R63 repros)
| arm | targets matched | pinned battery | what moved |
|---|---|---|---|
| landed | 158/168 | 34/48 | — |
| c1 = `specs/cand_r64b2_chaincompare_yield.json` | 159/168 | **40/48** | `scheduler.is_run_interval_time_now` [225,201,2,173] cleared; `round63_b2/repro_r63b2_tail_cmp_return` and `probe_r63b2_cases2` shapes improve |
| c2 = `specs/cand_r64b2_condcomp_consumer.json` | 159/168 | not run | `api_base.get_future_history_df` [973,957,3,229] cleared |

No target got worse in either arm (wizard 51/53 and klinedata 42/45 unchanged in both).
`c1.jsonl` is a 15-file run (targets+battery in one pass) = 199/216, consistent with 159 + 40.

## Anchor sites (both specs touch only region_ast_generator.py)
- c1 anchor starts at `if _nr_ast:` / the `stmts.extend(_nr_ast)` statement-list append.
- c2 anchor starts at the `if _ni.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):`
  scan that sets `_next_is_assign_store`.
Different hunks ⇒ expected mergeable, but `mbuild`'s sequential uniqueness assertion is the proof,
not this guess.

## Still open after both arms
`wizard_quant_api` calculate_di/params_analysis, `klinedata` 3 defects, `scheduler` get_checked_time
[106,106,0,43] + run_daily [77,71,0,56], `api_base` get_history_df [1742,1719,14,1277].
None of diag2's four files is reachable to fully-OK this round; the round's closing requirement
therefore depends on diag1 (`realtime_event_source` 11/12, `clock_worker` only) or diag5
(`matcher` 16/17, `match` only).
