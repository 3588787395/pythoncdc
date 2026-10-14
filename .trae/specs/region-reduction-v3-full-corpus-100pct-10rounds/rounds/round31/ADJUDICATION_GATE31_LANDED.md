# Gate 31 adjudication: one landing, and one rejected merge that a green panel did not see

Landed file: `core/cfg/region_ast_generator.py` `pre=7d336164eff5bf65` → `post=37d9fecb893704ac`
(+313 lines, 4 additive hunks from two engineers' candidates, merged by base-line coordinates,
byte-level install, `py_compile OK`). Only two products moved corpus-wide.

## 1. Certified numbers (gate 31, `gate_chain.py 31 30`, all four stages rc=0)

- regen `ok=402 bad=0` (273 s, 8 shards)
- verify (166 s), report: **units 6603 → 6606 /6617 (99.8338%), files 396 → 397**,
  `文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0 翻正单元=3`
  - FIXED `trade_info_utils.query_strategy_id`, `trade_info_utils.query_trade_strategy_info`,
    `api_base.get_history_df`; UNIT-UP `trade_info_utils 38→40`, `api_base 27→28`
- checks (107 s): quotation **153/153**, small34 `units_success 1557 / success 29` (moved by exactly the
  +3 flips, the second unit-level witness), ruler selfcheck OK,
  pytest `2 failed, 282 passed, 2 xpassed` — the two reds remain the registered residents
  (`test_B01_simple_if_then_else_merge`, `test_BOUNDARY_02_large_function`); passed rose 280→282 because
  the two validator arms added this round are in the same suite.
- sealed residual: **5 files / 11 units**, `UNREGISTERED 行数=0` (`RESIDUAL_ROUND31.md`).

## 2. What landed

| cand | author | hunks (base lines) | criterion | measured |
|---|---|---|---|---|
| r47a | api_base | 19113 (+141), 24773 (+9) | `_r4701_and_lift_or_tail`: single-leg `IF_TRUE→T==merge_block` region with empty `else_blocks`, whose fall-through `F` is an IfRegion with its own leg to `T2==FR.merge_block`, whose fall-through `FF` is an IfRegion merging on `T2` with `IF_FALSE` exit `E is T` ⇒ test becomes `BoolOp(and,[not X, BoolOp(or,[A,B])])`, arms `then=[T2]/else=[E]/merge=None` | `get_history_df delta=0 hunks=0 landings=0 judge_diff=False`, file **28/28**; fires once corpus-wide (`api_base entries=[(992,992)]`, @2686 correctly rejected) |
| r48a | trade_info_utils | 3235 (+105), 22531 (+68) | `_r2121_shared_tail_sinks` + one consumer at the tail of `_if_generate_normal`: `orelse=[Return None]` plus a trailing sibling `Return None`, so the two exit edges join the function's terminal block instead of each inlining its own tail | both named units `0/0/0`, file **40/41** (+2 units, not a file flip); `kill_trade_process` untouched at `659/659 hunks=0 landings=2`; `JUDGE_CALLS=5138 TOTAL_FIRES=2`, corpus bytes `CHANGED=1 of 402` |

The r48a result confirms the pointer in R21-21: the AST **can** express "two exits join one shared tail" —
`compile()` on 3.11.7 shows `else: return None` alone and a trailing `return None` alone each collapse to a
single None-return block, and only the **combination** produces two distinct blocks with both exit edges
aimed at the terminal one. The ticket's earlier "shapes falsified" list was right about each shape alone.

## 3. Rejected: r45a's handlers fix, and why my panel was blind

Gate 31 was first run with **three** candidates merged (`c35a0040fd789c74`, = r45a+r47a+r48a; the log is
kept as `GATE31_ATTEMPT1_rejected_gen3.log`, the bytes as `REJECTED_GATE31_gen3_with_r45a.py`). Verdict:

    [units] 6603/6617 -> 6601/6617   [files] 396 -> 392
    [gates] 文件级回退=6  UNIT_REGRESSIONS=6  新增失败单元=6  翻正单元=4
    FILE-BROKE IQCommon/arg_checker.pyc, IQCommon/profiler_func.pyc,
               IQData/utils/arg_checker.pyc, IQData/utils/profiler_func.pyc,
               IQEngine/utils/arg_checker.pyc, IQEngine/utils/profiler_func.pyc
    NEW-FAIL  ArgumentChecker.is_valid_date.check_is_valid_date (×3 packages)
              ProfilerTool.show_func (×3 packages)

So it bought 4 flips and broke 6 units: net **−2 units, −4 files**. Attribution, each candidate alone in
my own mirror, judged with `--source`:

| build | `arg_checker` (sealed 49/49) | `profiler_func` (sealed 17/17) |
|---|---|---|
| r45a alone | **48/49** | **16/17** |
| r47a alone | 49/49 | 17/17 |
| r48a alone | 49/49 | 17/17 |
| r47a + r48a (landed) | 49/49 | 17/17 |

r45a's handlers fix is therefore correct on its own victim (`handlers 30/30` with `risk 43/43`, and its
14-file panel was byte-clean) and wrong somewhere the panel cannot see. Two separate oversights:

1. **The 14-file panel contains no duplicated-module canary.** `ArgumentChecker` and `ProfilerTool` each
   exist in three packages (`IQCommon`, `IQData/utils`, `IQEngine/utils`) — six files that were green at
   gate 30, are not residual, and are not in the panel, so a change that breaks only them reads as
   "13 SAME + my own flip".
2. **The engineer's fire census used the same blind panel.** Its report claims `TOTAL_FIRES=1`, which the
   gate contradicts. The claim was not false about the 14 files; it was silently scoped to them.

### 3a. Hunk-level attribution (measured 01:27–01:30 on the sealed gate-31 base `37d9fecb893704ac`)

r45a's candidate is three hunks on the gate-30 base: **h1** = +32 (a helper block), **h2** = +67 at base
2024 — which is *r44a's criterion itself*, transplanted — and **h3** = +2/−1 at base 8088 (the narrowing of
R21-14's third hunk). Applying each subset by content anchor (`D:/Temp/t31_hunkpick.py`) gives:

| build | `arg_checker` (49/49 sealed) | `profiler_func` (17/17 sealed) | `handlers` (29/30 sealed) |
|---|---|---|---|
| h1 | 49/49 | 17/17 | 29/30 |
| h3 | 49/49 | 17/17 | 29/30 |
| **h2** | **48/49** | **16/17** | 29/30 |
| h2+h3 | 48/49 | 16/17 | 29/30 |
| h1+h2 | 48/49 | 16/17 | 29/30 |
| h1+h2+h3 | 48/49 | 16/17 | **30/30** |

So the over-fire is **h2 — r44a's own handlers criterion**, not r45a's narrowing: the narrowing hunks are
inert on the canaries (each alone leaves all three files at their sealed counts) and the flip needs both of
them plus h2. That also means r44a's `FIX_R21-20` claim of `1/14 changed, TOTAL_FIRES=1` was measured on
the same blind panel, and the earlier note in this round's ledger ("r45a over-fires") is coarse: at build
level r45a is the first candidate that carried h2 onto the sealed bytes, so it is where the gate saw it.
Follow-up ticket: `TICKET_R21-26_handlers_criterion_over_fires_canaries.md`.

Action taken: r45a is **not installed**; its candidate stays banked (`CANDIDATE_r45a_region_ast_generator.py`,
`FIX_R21-23_r45a.md`) and the handlers ticket is re-opened with the regression named. Panel widened for the
next round to include `IQCommon/arg_checker.pyc`, `IQCommon/profiler_func.pyc` and the duplicated-package
copies. Standing rule reinforced: **the gate, not the panel, is the regression witness** — this round it
caught a −6-unit landing that every cheap stage passed.

## 4. Also this round: r46a's quote work is a measured partial, not a candidate

`fly/data/quote.pyc :: run_individual_transform` under r46a's analyzer candidate (`8efe7f0040241138`,
+56/-1, two additive criteria): my own measurement — `len orig=407 prod=407 delta=0 hunks=2 landings=2
judge_diff=True`, file still **91/92**. It shrinks `delta=-52 → 0` and `hunks 3 → 2` with `TOTAL_FIRES=1`
and no panel regression, but by the round convention a shape that does not flip the unit is not landable,
so it is banked (`CANDIDATE_r46a_region_analyzer_BANKED_NOT_LANDED.py`) as the co-requisite half. Its own
report reaches the same conclusion and names the remainder: the relocated `else: warning` block needs a
conditional-region merge re-attribution in `_identify_conditional_regions`/`_collect_branch_blocks`
(~`:20461`) for the no-common-post-dominator case — the documented high-risk ordering wall (prior stop-set
patches: zero flips + four regressions), which it deliberately did not attempt.

## 5. Next gate

Label **32** against `rounds/round31/after`. 11 units in 5 files: `trade_live_broker` (7), `quote` (1),
`realtime_event_source.clock_worker` (1, −113, now three separately-ticketed mechanisms from
`DIAG_R21-24_clock_worker_r49a.md`), `handlers._target` (1, re-ticketed after the regression),
`trade_info_utils.kill_trade_process` (1, `TICKET_R21-25`).
