# FIX_R21-77 — clock_worker: the six-fact conjunction, implemented in the pipeline

Engineer **r104a** · round 41 · unit `<module>.RealtimeEventSource.clock_worker`
File: `site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`
Mirror: `D:/Temp/r104` (copies of `core parsers bytecode utils scripts pycdc.py`).
No repo `core/` write, no `*OK.py` edit, no repo-mutating git command was performed
(`git` was never invoked at all). All patched files live in the mirror.

Definition-of-done target: the PIPELINE product judging `status=success units=13/13`.
Oracle / distance measure: `D:/Temp/r103/DELIVER/GOLD_realtime_event_source_PROOF.py`
(= `D:/Temp/r104/GOLD_varF.py`; `status=success units=13/13`, `clock_worker` code object
byte-identical to the original).

## HEADLINE RESULT (honest)

**The pipeline did NOT reach 13/13. It reached 12/13 with ONE of the six facts implemented and
three of them moved**, on a candidate that is provably zero-collateral corpus-wide.

* Shipped rule: **[R21-77-F5]** — one analyzer criterion, a structural *generalisation* of the
  already-landed redundant-`while True`-wrapper removal (which today is gated by a
  `len(body_outer − body_inner) <= 2` **counter**, i.e. itself a rule violation).
* It deletes the spurious `while True:` wrapper (ladder **step 5**) and, as a direct consequence of
  the wrapper's over-absorbing body being reclaimed, it also **restores the holiday block `@6690`
  inline** (ladder **step 1**, first half) and **removes the loop-tail duplicated holiday/
  `before_trading_date` lines** (ladder **step 2**, 4 of the 5 lines).
* Steps 3, 4, 6 and the dominant 112-instruction half of step 1 are **still unimplemented** (§6).

| metric | base (landed) | + F5 (this round) | GOLD (13/13) |
|---|---|---|---|
| judge | 12/13 Different control flow | **12/13 Different control flow** (sole failure still `clock_worker`) | 13/13 success |
| allwin `delta`/hunks | −113 / 7 | −113 / 6 | 0 / 0 |
| win_r91 `delta`/windows | −112 / 15 | −114 / 9 | 0 / 0 |
| text distance to oracle | 4 hunks, +84 −74 | **4 hunks, +66 −53** | 0 hunks |

The text distance to the oracle tightened by 18 added / 21 removed lines and the window count by 6
windows — but per this round's own load-bearing fact, **that is not the bar**; the bar is the judge,
and the judge is unchanged at 12/13. This candidate is therefore a **zero-flip candidate under the
project bar** and must not be installed on its own. It is delivered as a measured, safe,
zero-collateral *step* plus the diagnosis of what still blocks the rest (§6).

## 0. Platform (installed + re-hashed BEFORE anything)

`hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]`:

| file | sha16 | byte-equal to banked source |
|---|---|---|
| `core/cfg/region_analyzer.py` | `1471c92eca157e46` | YES — `$SP/rounds/round40/r93/region_analyzer_R21-64a_FINAL.py` |
| `core/cfg/region_ast_generator.py` | `566ff5c502276e48` | YES — `$SP/rounds/round40/r102/CANDIDATE_r2174_566ff5c502276e48.py` |

The repo's landed pair already IS this pair (the mirror copies taken from repo `core/` hash equal to
the banked copies, byte-for-byte), so nothing had to be substituted and nothing was.
`region_ast_generator.py` was **never edited** in this round; it still hashes `566ff5c502276e48`.
After the patch the analyzer hashes `da5d6b3717657f86` (first, over-firing variant — NOT delivered)
and finally **`996a1b1acf143458`** (narrowed, delivered).

## 1. Base reproduction (fresh regen, judged with `--source`) — all four witnesses MATCH

`logs/base_measure.txt`, `logs/win_base.txt`, `logs/gold_diff_base.txt`:

```
PROD D:/Temp/r104/out/rt_base.py size=20555
JUDGE_RT     [single] status=failure units=12/13 success_rate=92.31%  (sole failure clock_worker, Different control flow)
JUDGE_BROKER [single] status=success units=128/128 success_rate=100.00%
allwin_r63   len orig=1424 prod=1311 delta=-113  hunks=7
win_r91      orig instrs=1442 prod instrs=1330 delta=-112  windows=15
gold_diff    unit=clock_worker ours=244 lines GOLD=254 lines hunks_vs_GOLD=4 +84 -74
```

## 2. Why the unit is broken — block/region evidence (diagnosis, not a premise)

`dump_cw_r104.py` / `dump_loops_r104.py` on the landed platform, 67 regions / 191 blocks:

```
WHILE header=5598 cond=None is_while_true=True  back=6792 n_body=103 children=[WHILE 5614]   <-- SPURIOUS wrapper
WHILE header=5614 cond=5598 is_while_true=False back=9194 n_body=97   <-- the real `while self.active:`
WHILE header=5738 cond=5614 ...  n_body=1                              <-- inner `while dt.replace(...) <= last_date_time:`
```

Both loop regions are driven by the **same test block `@5598`** (`LOAD_DEREF self / LOAD_ATTR active /
POP_JUMP_FORWARD_IF_FALSE 9214`): CPython 3.11 uses that block both as the back-edge target of the
loop tail and as the entry of the code after the test, so one test becomes two `LoopRegion`s. That
violates principle 2 (unique block membership) and is what the product renders as `while True:` +
`while self.active:`. The wrapper's body over-absorbs `@6690 @6702 @6778` (the holiday branch) and
`@9210 @9214` (post-loop code) which the real loop's body does **not** contain — that single
mis-claim is what pushed the holiday statements out of the `if self.is_holiday_today():` arm into a
`break`-folded stub (step 1) and duplicated them again at the loop tail (step 2).

Landed code already recognised this shape but decided it with a **count**:
`region_analyzer.py:5492  if body_a_set and body_b_set and len(_diff_a) <= 2`. Here the difference
set is 6 blocks, so the wrapper survived. Replacing the counter by structure is the whole fix.

## 3. [R21-77-F5] the rule (correct-at-identification, analyzer-side, general)

Site: `core/cfg/region_analyzer.py`, `_identify_loop_regions` dedup branch + helper
`_r104_outer_wrapper_is_redundant` / `_r104_reaches` + the post-removal reclaim. Builder:
`build_f5_r104.py` (asserts exactly one anchor occurrence, re-emits BOM + all-CRLF, asserts no
`\r\r\n` and no bare LF, then `py_compile`).

Precondition (already the landed branch's own precondition): `outer.is_while_true` and
`outer.header_block is inner.condition_block` — the two loop regions share one test block.

Judged purely from block/region data (no function name, no file name, no absolute offset key, no
counter, no threshold):

1. **the inner loop's normal exit never comes back to that test block** — the test block's own
   conditional jump target is forward-reachable-tested against the header; not reachable ⇒ there is
   no second round, so an "outer loop" cannot exist. A genuine
   `while True: while x: …; while y: …` wrapper *does* come back (x's exit falls into y, y's back
   edge returns to the header) and is kept — this replaces the counter the landed comment used for
   exactly that protection.
2. **every body block the wrapper has and the real loop lacks** is either the shared test block
   itself, or a block lying inside the real loop's own body offset span (it was sandwiched in the
   real loop's body all along and is *reclaimed* into it), or a block outside that span that cannot
   reach the test block (post-exit sequential code the wrapper merely over-collected). Anything else
   means the wrapper has its own loop content ⇒ refuse.
3. **the wrapper's back-edge block(s) lie inside the real loop's body** — the only path that would
   "restart" the wrapper is the real loop's own tail re-entering the shared test. A real
   `while True:` wrapper has its back edge outside the inner body (its own tail), and is refused.

Clause 3 is not decoration: without it (variant `da5d6b3717657f86`) the rule fired on
`fly/data/quote.pyc :: Quote.run_individual_transform` and on
`plugin_system_risk_calculation/__init__.pyc :: _save_testds_to_csv` and **broke two currently-Equal
units** (measured: quote 92/92 → **91/92 `Different control flow`**, that file 43/43 → **42/43**).
With clause 3 those two sites evaluate False and the corpus sweep returns zero collateral.
No repair of already-emitted text is performed anywhere: the reclaim edits the analyzer's region
`body_blocks`/`blocks`/`block_to_region` before any rendering.

## 4. Fire census for [R21-77-F5] (`census_f5_r104.py`)

The census measures on the **pre-removal region set** (it runs `analyze()` with the new predicate
inert — the patch is additive, so that is exactly the landed pipeline), then evaluates the shipped
predicate on every surviving pair. Landed verdict is recomputed as `extra <= 2` for the side-by-side.

20-file panel `$SP/rounds/round38/PANEL_20files.txt` (`logs/census_f5_narrow_panel.txt`,
repo-root-joined; 20/20 compared, MISSING/FAIL=0):

```
pairs=7  pair_files=5  landed_fires=0  new_fires=3  verdict_diffs=3  verdict_diff_files=2
  handlers.pyc        TWHThreadRotatingFileHandler._target  extra=3  landed=False new=True
  realtime(2 units)   clock_worker extra=6 landed=False new=True ; events extra=3 landed=False new=True
```

All 402 files `$SP/rounds/round40/r95/corpus402.txt`, 8 shards of 51 (`logs/census_f5_corp_*.txt`,
paths joined to the repo ROOT, `files_compared=51` per shard, `MISSING/FAIL=0` in every shard):

```
new fires = 6   in 5 files:
  IQCommon/exception.pyc                        create_custom_exception            extra=4
  IQData/utils/exception.pyc                    create_custom_exception            extra=4
  IQEngine/utils/exception.pyc                  create_custom_exception            extra=4
  IQCommon/logger/handlers.pyc                  TWHThreadRotatingFileHandler._target extra=3
  IQEngine/.../realtime_event_source.pyc        RealtimeEventSource.clock_worker   extra=6  (TARGET)
  IQEngine/.../realtime_event_source.pyc        RealtimeEventSource.events         extra=3  (TARGET file)
landed_fires = 0 (no site where the counter already fired is newly refused: the patch is additive)
```

Collateral test (the one that matters): all six fire sites were regenerated and CR-stripped-compared
against their committed products — only `realtime_event_source` differs (§7). The three
`create_custom_exception` fires and the `_target` fire are **inert** (zero product bytes change; in
those units the wrapper is already rendered equivalently), so **no currently-Equal file is touched**.
`realtime_event_source::events` also stays green (12/13, sole failure still `clock_worker`).

## 5. Halves / pair matrix — steps 1(holiday half)/2/5 are co-requisite, delivered together

One rule, so the halves matrix is: landed base, this rule, and the un-implemented steps as measured
text-only variants (r103a's ladder, re-measured from `D:/Temp/r103/DELIVER/GOLD_var*.py` with my
rigs, `logs/ladder_r104.txt`).

| candidate | delta | hunks | win windows | judge |
|---|---|---|---|---|
| landed pipeline (rt_base) | −113 | 7 | 15 | 12/13 Different control flow |
| **[R21-77-F5] pipeline (delivered)** | −113 | **6** | **9** | **12/13 Different control flow** |
| + step3 as text (`varC`) | −2 | 2 | — | 12/13 |
| + step4 as text (`varD`) | −3 | 1 | — | 12/13 |
| + step5 as text (`varE`) | 0 | 0 | — | **12/13 — still fails at instruction parity** |
| + step6 as text (`varF` = GOLD) | 0 | 0 | — | **13/13 success** |

Co-requisites, stated plainly: steps 3+4 are useless without 6 (varD is instruction-identical to
nothing and still judged Different), and step 6 alone is worthless (it only moves two jump targets
once parity is reached). F5 is a strict prerequisite for 3/4/6 in the *pipeline*: while the wrapper
exists, the `@6322/@6496/@7164` arms are emitted inside the wrong loop body, so no or-chain rule can
be evaluated against the right string.

## 6. The five steps still unimplemented, and the specific blocker for each

1. **Step 1 dominant half — the 112-instruction in-branch run `@7972..@8586`** (the
   `if persist_flag is False: … return`, `self.before_trading_date = now_date`,
   `try/except server_restart_not_do_before`, the `if server_restart=='0' / elif broker_persist`
   chain) is still dropped: the product emits `else: break` for the `for i in range(60)` arm and
   then jumps to the `elif check_trading_time(...)` chain rendered **one nesting level too deep**
   (inside `if now_date > self.before_trading_date:`, product lines 273-288) with a leftover
   `server_restart_do_before_type = '0'` at the loop tail (line 289). Blocker: the run's blocks are
   claimed by `IF_ELIF_CHAIN cond=7634 then=[…7972,7980,8170,…]` whose merge is the loop back edge
   `@9194`; the only emitter that reaches them today is the over-absorbing `elif_final_else`, which
   is exactly the mechanism the closed route `c93e8994893ee530` proved unfalsifiable-but-collapse-prone
   (removing the absorption alone gives `+2 → −269`). So this step needs a *positive* tail claim that
   re-homes the run, not a refusal — i.e. a second rule, blocked behind a real design decision, not
   behind measurement. I did not attempt it because a half-claim is the −269 route.
2. **Step 2 residue — 1 of the 5 duplicated tail lines** (`server_restart_do_before_type = '0'`)
   survives F5; its run is the same claimed-by-`elif_final_else` object as (1).
3. **Step 3 — `@7164` `(A and B) or C` + the swallowed `system_log.debug('获取重登信号量')`.**
   Product still emits `if now_date > self.pre_before_trading_date:` / `if … or …: pass` /
   `elif now_date != self.first_run_date and login_semaphore.acquire(...) is False:` (lines
   251-260) where the oracle has `if (A and B) or C:` with a nested `if now_date != first_run_date:`
   carrying the debug call. Blocker: only **three** `BOOL_OP` regions are declared in the whole unit
   (`merge=6280, 7164, 9144`) while the unit contains ≥5 short-circuit tests; `@7164`'s region is
   `IF_THEN cond=7164 then=[7186,…] merge=7216` with an *empty* then arm `IF_ELIF_CHAIN cond=7186
   then=[7212]`, i.e. the and-chain is being assembled as a nested if/elif, and the debug call sits
   in a block that is another region's merge. Per project memory (`[R21-48]`, gate-38 `c4a934d5`)
   this exact −6 has already been falsified four ways; I did not re-open it.
4. **Step 4 — `@6322`/`@6496` `is_holiday` or-chains.** Same family as (3) (one general rule, two
   sites): the product renders the holiday arm as `if A: if B or C: … elif A': if not B': …`,
   i.e. a **negated** and re-nested version of `(A and B) or C` / `(A' and B') or C'`.
5. **Step 6 — the `@8904` elif + chained-comparison inner `if` fold** (`and delay_after_trading >=
   now_time >= after_trading`), the fact that actually flips the judge. Product lines 282-288 keep
   the inner `if` (and its `else: time.sleep(FPS)`). Blocker: a fold of this shape is only valid
   when the inner if's else *is* the chain's own continuation, and the enclosing
   `IF_THEN_ELSE cond=8948 … merge=9194` currently claims `@9194` (the back edge) as its merge, so
   the "chain continuation" reading is not available from the declared region data. Implementing it
   as a textual `elif … and …` special case would be a name/offset-keyed hack, which the rules reject.

Consequence: the acceptance test ("pipeline emits a text judging 13/13") is **not met**, and no
subset of what I could implement meets it, so I am not asking for a gate.

## 7. Panel after the patch (all rows hold; `broker 128/128` did not move)

`logs/panel_narrow.txt` (fresh regen from the mirror + `pyc_verify single --source`):

```
[panel realtime]      status=failure units=12/13  failing=['***<module>.RealtimeEventSource.clock_worker: Failure: Different control flow']
[panel broker]        status=success units=128/128
[panel function]      status=success units=15/15
[panel replace_utils] status=success units=9/9
[panel quote]         status=success units=92/92
[panel quotation]     status=success units=153/153
[panel order_api]     status=success units=37/37
```

## 8. Corpus collateral sweep (all 402, CR-stripped vs committed products)

`sweep_r104.py` (repointed from `$SP/rounds/round40/r93/sweep_r93.py`; **repo-relative list joined to
the repo ROOT**, mirror `pycdc.py`, `cwd=mirror`), 4 shards of ~101, `logs/sweep_f5b_*.log`:

```
shard    0: files_compared=101 MISSING/FAIL=0 CHANGED_COUNT=0
shard  101: files_compared=101 MISSING/FAIL=0 CHANGED_COUNT=0
shard  202: files_compared=101 MISSING/FAIL=0 CHANGED_COUNT=1
shard  303: files_compared= 99 MISSING/FAIL=0 CHANGED_COUNT=0
TOTAL files_compared=402  MISSING/FAIL=0  CHANGED=1
  CHANGED site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc
```

Exactly as expected: `{realtime_event_source}` only. (For contrast, the un-narrowed `da5d6b37`
variant produced CHANGED=3 including the two currently-Equal files named in §3 — that variant is
kept in `logs/sweep_f5_*.log` as the falsification record, not delivered.)

Round-14 battery at mirror depth (`.trae/specs/.../rounds/round14/repro/run_repro.py`,
`ROOT=D:\Temp\r104`): **`RED=8 / 9`** — equal to the briefed baseline reading, zero new failures.

## 9. Definition of done — NOT met, stated with the command that proves it

```
python -X utf8 scripts/pyc_verify.py single <abs realtime_event_source.pyc> --source D:/Temp/r104/out/pnl_realtime.py
  [single] status=failure units=12/13 success_rate=92.31%
```
The oracle judging 13/13 is `GOLD_realtime_event_source_PROOF.py`; my product is 12 hunks-lines
(+66 −53) away from it and the judge is unchanged. Per §5/§6 the missing quantity is facts 3, 4, 6
and the 112-instruction half of fact 1 — not a polish item.

## 10. Files (see MANIFEST_R104.md)

`region_analyzer_R21-77-F5_996a1b1acf143458.py` (deliverable), `backup/region_analyzer_landed.py`
(`1471c92eca157e46`, byte-exact restore target), `build_f5_r104.py` (byte-exact builder),
`census_f5_r104.py`, `sweep_r104.py`, `panel_r104.py`, `measure_r104.py`, `dump_cw_r104.py`,
`dump_loops_r104.py`, `probe_loops_r104.py`, `probe_f5_r104.py`, `rigs/{allwin_r63,win_r91,gold_diff_r104}.py`,
`out/{rt_base,rt_f5,pnl_*}.py`, `logs/*`.

## 11. Cross-checks recorded after the sweep

**Repo untouched** (re-hash at the end, not just at the start):
`REPO core/cfg/region_analyzer.py = 1471c92eca157e46`, `REPO core/cfg/region_ast_generator.py =
566ff5c502276e48` — both equal to the mandated platform, so no repo `core/` write happened;
all patching happened in `D:/Temp/r104/core/`.

**Ladder re-measured by me**, not quoted (each r103a variant file regenerated through MY rigs +
MY judge, `logs/ladder_r104.txt`) — it reproduces the briefed ladder exactly, which also re-proves
the oracle under my own tooling:

```
GOLD_varA_holiday  delta=+13  hunks=5  status=failure units=12/13
GOLD_varB          delta= -7  hunks=4  status=failure units=12/13
GOLD_varC          delta= -2  hunks=2  status=failure units=12/13
GOLD_varD          delta= -3  hunks=1  status=failure units=12/13
GOLD_varE          delta=  0  hunks=0  status=failure units=12/13   <-- instruction parity is NOT judge equivalence
GOLD_varF          delta=  0  hunks=0  status=success units=13/13   <-- the oracle, confirmed on my platform
```

**Definition of done, verbatim output** (`logs/definition_of_done.txt`):

```
python -X utf8 scripts/pyc_verify.py single <repo>/site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc --source D:/Temp/r104/out/pnl_realtime.py
[single] status=failure units=12/13 success_rate=92.31%      <-- NOT 13/13
```

## 12. What I recommend the next round do (from the region data, not from prose)

F5 is a strict prerequisite: until the wrapper is gone, `@6322/@6496/@7164` arms render inside the
wrong loop body and the or-chain rules cannot even be measured against the right string. It is
delivered here as a zero-collateral, judge-neutral step (it does not move the verdict, so the project
bar says revert-or-hold; hold it next to the next candidate rather than landing it alone).
The cheapest remaining route to 13/13 is, in order:
(a) one analyzer rule for the `(A and B) or C` shared-body family (covers steps 3 + 4 in one
criterion — both sites are the same shape, and `@7164`'s empty then arm `IF_ELIF_CHAIN cond=7186
then=[7212]` is the manufactured-jump signature that dies with it);
(b) a positive back-edge/merge tail claim that re-homes `@7972..@8586` (step 1 dominant half + the
last line of step 2) instead of refusing the absorption (the `c93e8994` refusal route is closed —
−269);
(c) the `@8904` elif chained-compare fold (step 6), which is the fact that flips the judge and the
only one invisible to `allwin`/`win_r91` — score it with a jump-target/`landings` comparison or the
judge directly, never with instruction parity.

