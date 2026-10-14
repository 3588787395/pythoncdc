# FIX R21-20 (round 30) — `handlers.TWHThreadController._target` UNDER-EMISSION: landed as an if/elif merge chain

Engineer `r44a`. Owner file: `core/cfg/region_ast_generator.py` only. Repo READ-ONLY at
`D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` (HEAD `ef855849` = the ticket commit itself; the
ticket text named `54f4d655`, one commit earlier). Mirror `D:/Temp/r38/wt`. Interpreter `python` 3.11.7,
all runs `-X utf8`, never `PYTHONIOENCODING`.

## (0) Ticket as received
`IQCommon/logger/handlers.pyc` :: `<module>.TWHThreadController._target` — the file's ONLY failing unit
(29/30 ⇒ flip = whole-file 30/30). Sealed reading:
```
len orig=199 prod=197  delta=-2  hunks=1  landings=3  judge_diff=True
== delete orig[73..75 @404..@406] prod[73..73] del=2 ins=0
   - @404 LOAD_CONST None
   - @406 RETURN_VALUE
   ~ orig[83] @456 ... ->idx193 | prod[81] @452 ->idx195
   ~ orig[90] @502 ... ->idx195 | prod[88] @496 ->idx191
   ~ orig[93] @516 ... ->idx197 | prod[91] @510 ->idx193
```
Four framings pre-falsified (fold; guard/terminator; drop-else/un-negate/trailing-else-return; "no
arrangement of return None can materialise a tail copy"). Task: treat as an UNDER-EMISSION — a statement
the source shape failed to materialise — restore the pair so the three landings collapse as shift shadows.

## (1) Mirror + sealed-hash + cmp proof
Copied `pycdc.py core parsers utils bytecode scripts` into `D:/Temp/r38/wt` (all `__pycache__` stripped;
0 `.pyc` in the mirror). Copied `.trae/specs/…/unit_diff.py` and the six `rounds/roundNN/repro*` battery
dirs at the SAME relative depth (`unit_diff.py` ROOT = 3 `..` up from SPEC_DIR; battery runners ROOT = 7
`dirname` levels from `__file__`, `cwd=ROOT`).

Sealed hashes (repo working tree == mirror == ticket):
```
region_ast_generator.py = fd0e4c4d73cf5efc
region_analyzer.py      = 35e227ac3e7b25af
ast_generator_v2.py     = beeaf14435e22922
```
mirror `unit_diff.py` `cmp`-identical to repo copy (`UNIT_DIFF_IDENTICAL`).

Mirror reproduces the sealed product (before any patch): regenerated `handlersOK.py` from the mirror,
CR-normalised, `cmp` against `git show HEAD:site-packages/IQCommon/logger/handlersOK.py`:
```
8887  sealed_lf.py
8887  baseline_lf.py
MIRROR_REPRODUCES_SEALED_PRODUCT_OK
```

## (2) Baseline readings (mirror, sealed bytes)
- `unit_diff … --all`: `len orig=199 prod=197 delta=-2 hunks=1 landings=3 judge_diff=True` (exact ticket shape).
- `pyc_verify single … --source` (out/baseline): `status=failure units=29/30 success_rate=96.67%`,
  failing unit `***<module>.TWHThreadController._target: Failure: Different control flow`.

## (3) 取证 — the emitter of the loop-exit tail

The emitted product for the py3.5 branch (baseline) was:
```
27  if sys.version_info[0] == 3 and sys.version_info[1] == 5:
28      while self.running:            # loop; body is the try/except/else at 29..39
40      return None                    # ← materialised tail
41  if sys.version_info[0] == 3:       # ← sibling if, NOT elif
...
62  else:
63      return None                    # ← materialised tail
```
Compiled baseline `_target` layout of the loop exits (from `dis`):
```
@102 POP_JUMP_FORWARD_IF_FALSE -> @404   (entry test → SHARED single copy)
@402 POP_JUMP_BACKWARD_IF_TRUE  -> @104
@404 LOAD_CONST None; @406 RETURN_VALUE  (bottom-test fall-through)
@408 LOAD_GLOBAL sys                      (COND2 test, directly)
```
Original `_target` layout (read from the pyc):
```
@102 POP_JUMP_FORWARD_IF_FALSE -> @408   (entry test → SECOND copy)
@402 POP_JUMP_BACKWARD_IF_TRUE  -> @104
@404 LOAD_CONST None; @406 RETURN_VALUE  (bottom-test fall-through,  copy1)
@408 LOAD_CONST None; @410 RETURN_VALUE  (entry-test target,          copy2)
@412 LOAD_GLOBAL sys                     (COND2 test)
```
Both copies `@404..@410` are tagged **source line 63** (`tgt.co_lines()`), i.e. the `while` line — there is
**no separate `return None` source statement** in the py3.5 branch; the two copies are the loop's
per-exit-edge inlining of the implicit function tail.

The CFG the pipeline feeds the generator (`build_cfg` + `RegionAnalyzer(cfg).analyze()`, list return) for
`_target`:
- `IfRegion entry=0` (COND1): `condition_block=46`, `then_blocks=[90,408,404]`, `else_blocks=[]`,
  **`merge_block=412`**, `elif_conditions/elif_bodies/elif_final_else = []`.
- `IfRegion entry=412` (COND2): `condition_block=412`, `else_blocks=[1012]`, `merge_block=None`.
So the analyzer DOES link COND1's false edge (`merge_block`) to COND2's entry (`@412 == COND2.condition_block`)
— the elif relation — but leaves the `elif_*` arrays empty, so the generator emits COND1 and COND2 as two
sibling top-level `If` statements. The AST `generate()` produces for `_target` is literally
`If(COND1): body=[While, Return None]` and `If(COND2): body=[If(COND3): body=[While]], orelse=[Return None]`.

Two independent generator-side mechanisms cause the −2:
1. **sibling-if, not elif** — `_if_generate_elif_chain` (`region_ast_generator.py:18974`) only runs when the
   region carries `elif_conditions`/`elif_bodies`; they are empty here, so COND2 is emitted by the top-level
   region loop (`for region in top_level_regions`, `region_ast_generator.py:1863`) as a separate statement.
   A sibling `if` makes COND1-true's loop exit fall through to COND2; the elif makes it terminal via the
   chain end so CPython duplicates the tail per exit edge.
2. **materialised tail `return None`** — the machinery that decides which implicit-`return None` terminal
   blocks are per-edge landings (do-not-emit) vs statements (emit) is
   `_r8_b121_implicit_tail_landing_sinks` (`region_ast_generator.py:52386`, consumed at the single funnel
   `_generate_block_statements` `region_ast_generator.py:52624`, kind detector `_r8_b121_scope_return_sink_kind`
   `region_ast_generator.py:52392`, join detector `_is_return_none_join_block` `region_ast_generator.py:3163`).
   Its **all-or-nothing** gate walks every trailing-`return None` terminal block in the code object and
   empties the whole set if ANY fails G1–G7. In `_target` the py3.11 stop-arm block
   `@658` (`LOAD_CONST False; self.running=False; LOAD_CONST None; RETURN_VALUE`) is a trailing-`return None`
   terminal that is **not** `pure-none` (it has a user `STORE_ATTR` statement), so the gate bails
   (`_cands=None`) and suppresses NOTHING → the loop-exit tails `@404/@408` materialise as an explicit
   `return None` in COND1's body (and `@1012` as COND2's `else: return None`), giving CPython a **shared
   join** exit (one copy).

**How the shape was decided by compile()** (`D:/Temp/r38/log/shape*.py`, `matrix.py`, in-process scorer
reusing `unit_diff.dump/dump_raw/pick` so the printed `delta/hunks/landings` match the tool exactly):
I enumerated loop-exit shapes standalone and on the full `_target`. The ONLY shape hitting
`filtered=199, entry@102→@408, retest→LOAD_CONST|RETURN|LOAD_CONST|RETURN|LOAD_GLOBAL` was
`if COND1: <while>` / `elif COND2: …` with **no** explicit tail returns and **no** trailing `else`.
A full 2×2×2 matrix over {drop COND1 tail return}×{COND2 elif}×{drop COND2 else} confirmed the unique winner
requires all three (see §6). The winning reconstructed source (`out/v7/handlersOK.py`) measured
`len orig=199 prod=199 delta=0 hunks=0 landings=0 judge_diff=False`, judge `units=30/30`.

## (4) Criterion implemented
Generator-side **undeclared if/elif merge-chain assembly** — a purely additive block at
`core/cfg/region_ast_generator.py:1963..2029` in `generate()`'s top-level region loop (67 lines inserted,
0 lines removed). When a top-level `IfRegion` R is emitted as a dict-`If` with `orelse` empty,
`merge_block` set, `else_blocks`/`elif_conditions`/`elif_bodies` empty, and its then-body's last statement
is a trailing `return None` **that corresponds to a real per-edge landing** (in `region.then_blocks` there is
a terminal block with no successors, `pure-none` kind, NOT a return-None join, exactly one predecessor),
then R's `merge_block` is looked up among the top-level regions; if it equals a later top-level `IfRegion`
R2's `condition_block`/`entry`, R2 is generated immediately, placed as R's `orelse` (the elif),
R's then-tail `return None` is dropped, R2's chain-terminal trailing-`return None` `orelse` is dropped, and
R2's blocks are marked generated so its own iteration is skipped. The reliance on the implicit function tail
is what lets CPython re-inline `return None` at both loop-exit edges.

The CFG landing precondition is the load-bearing part: without it the criterion fired on genuine
`if …; return None` / sequential-`if` patterns (see §6).

## (5) Post-patch readings + fire census + quotation + panel + batteries

`_target` (final, mirror product `out/r44a/IQCommon_logger_handlers.py`):
```
len orig=199 prod=199 delta=0
hunks=0 landings=0 judge_diff=False
```
`pyc_verify single … --source`: `status=success units=30/30 success_rate=100.00%`  → **FILE FLIP**.

Product text diff (baseline → final), CR-normalised — exactly the V7 shape:
```
-            return None                 (COND1 tail)
-        if sys.version_info[0] == 3:
+        elif sys.version_info[0] == 3:
-        else:
-            return None                 (COND2 trailing else)
```

Fire census over the 14-file panel (regenerated vs `git show HEAD:<…OK.py>`, CR-stripped, never `cmp` vs
checkout). **TOTAL_CHANGED = 1/14** — only `IQCommon/logger/handlers`:
```
fly_data_quotation                same
fly_data_quote                    same
IQCommon_api_klinedata            same
IQCommon_logger_handlers          CHANGED   (8887 -> 8827, CR-normalised)
IQCommon_strategy_wizard_quant_api same
IQCommon_util_trade_info_utils    same
IQData_api_api_base               same
IQData_..._real_quote             same
IQEngine_..._strategy             same
IQEngine_..._order_api            same
IQEngine_..._trade_live_broker    same
IQEngine_..._matcher              same
IQEngine_..._realtime_event_source same
IQEngine_..._risk_calculation     same
```
Because 13/14 products are byte-identical to HEAD, their unit counts are preserved by construction
(`quotation 153/153`, `klinedata 63/64`, `wizard_quant_api 58/58`, `trade_info_utils 38/41`,
`api_base 27/28`, `real_quote 45/45`, `strategy 26/27`, `order_api 37/37`, `broker 121/128`, `matcher 17/17`,
`realtime_event_source 12/13`, `risk_calculation 42/43`, `quote 91/92`). Named cheap guards re-judged from
the fresh products:
```
quotation  units=153/153
order_api  units=37/37
matcher    units=17/17
```
All six batteries at recorded values (run in the mirror at the same depth):
```
repro     RED=9  / 9            ✓ (recorded 9R/9)
arm       GREEN=0 RED=3 / 3     ✓ (recorded 0G/3R)
ccneg     GREEN=3 RED=1 / 4     ✓ (recorded 3G/1R)
retbreak  GREEN=2 RED=2 DRIFT_VS_BASELINE=0 / 4   ✓ (recorded 2G/2R DRIFT=0)
orderapi  GREEN=5 RED=0 / 5     ✓ (recorded 5G/0R)
tail      GREEN=13 RED=0 / 13   ✓ (recorded 13G/0R)
```
The `repro_tail` battery is the explicit regression guard for the implicit-return / join-tail machinery this
touch changes; it stayed green.

Repo untouched: `git status --porcelain -- core/ site-packages` empty; repo sealed hashes still
`fd0e4c4d73cf5efc`/`35e227ac3e7b25af`/`beeaf14435e22922`; mirror `region_analyzer.py` and
`ast_generator_v2.py` still at their sealed hashes (not edited). Candidate is CRLF-uniform
(59889 CRLF, 0 bare CR, 0 bare LF).

## (6) Negative evidence (measured, do not repeat)

**A. The criterion without the CFG landing precondition is catastrophic** (first implementation attempt,
50-line version). Fire census then read **TOTAL_CHANGED = 10/14** with severe shrinks:
```
api_base      32700 -> 10915   (1/3 of the product destroyed)
broker        175214 -> 165743 (units 121 -> 119, REGRESSION)
risk_calculation 54737 -> 51000
quotation     179081 -> 176957
order_api     33768 -> 33242
quote, klinedata, real_quote, trade_info_utils, handlers  (all changed)
```
Two broker over-fires located by diffing the broker product CR-normalised: a **62-line body deletion**
of the `crdt_compactreal_qry` loop at ~line 1940 (an over-large region consumed as elif), and a real
`return None` + `if lock_direction == '1':` → `elif lock_direction == '1':` at ~line 2779 (a genuine source
return dropped). Both are **real** `return None` statements whose tail blocks are return-None **joins**
(≥2 predecessors) rather than per-edge implicit landings — precisely what the added precondition
(`pure-none` kind ∧ not `_is_return_none_join_block` ∧ single predecessor) excludes. With it,
TOTAL_CHANGED drops to 1/14 and broker stays 121/128.

**B. Source shapes compiled that did NOT reproduce the pair** (so no return-None can be "added"; the fix is a
scope/elif change, consistent with falsified framings #1/#3/#4):
```
if COND1: while body; return None;  COND2-sibling-if   -> 197, entry@102->@404 (shared; = product)
if COND1: while body (no return);   COND2-sibling-if   -> 195, loop exits fall through to COND2 (no copy)
while body else: return None                            -> 197 (identical to sibling-if+return)
bare `return` instead of `return None`                  -> 197
two consecutive `return None`                           -> 197
pass instead of return                                  -> 197 (delta -4)
if COND1: while body (no return); elif COND2 (keep else)-> 199/0/landings=3 (COND2 tail rotation)
```
The `landings=3` in the second-to-last row was the COND2 tail-return **block order** rotating
(COND2-false landing `@1012` moved to the chain end `@1018`) because the trailing `else: return None` kept
COND2 non-terminal; dropping that else (final criterion) restores the original tail order and reads
`landings=0`. The minimal reproducing shape was only `nested_while_while` and `if COND1: while; COND2 terminal`
— never a single-loop + explicit-return form.

## (7) Final declaration

**CANDIDATE READY (file flip: handlers 30/30).**

`_target` reads `len orig=199 prod=199 delta=0 hunks=0 landings=0 judge_diff=False`; the judge prints
`status=success units=30/30`. Fire census = only `handlers` changed (1/14); all 13 others byte-identical
(no count dropped); quotation 153/153, order_api 37/37, matcher 17/17; all six batteries at recorded values
(retbreak DRIFT=0). Candidate (whole file, purely additive 67 lines) installed at
`D:/Temp/r38/DELIVER/CANDIDATE_region_ast_generator.py`:
```
sha256 691e5aa4f57065d8...   (cut -c1-16 = 691e5aa4f57065d8)
```
Caveat for the gate: `region_ast_generator.py:1863`'s top-level loop is exercised by the whole corpus; the
panel + 6 batteries are this ticket's net, but the 402-file regen is the only certification of the residual
corpus. The criterion is deliberately gated on the same per-edge-landing facts as `_r8_b121_implicit_tail_landing_sinks`
so it cannot re-materialise a real return; if the gate sees any new change beyond `handlers`, the added
`any(...)` precondition is the single place to tighten.
