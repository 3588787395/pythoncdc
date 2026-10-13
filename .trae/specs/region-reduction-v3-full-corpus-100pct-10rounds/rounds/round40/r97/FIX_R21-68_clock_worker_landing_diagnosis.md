# FIX_R21-68 (DIAGNOSIS ONLY) — clock_worker landing / region-declaration diagnosis

Engineer r97a, round 40. **Diagnosis only**: nothing implemented, no candidate delivered, no
whole-corpus regen (only single-file regens; 4 engineers are live on the other residual unit).
Repo `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` was read-only; all writes went to
`D:/Temp/r97`. The campaign is NOT complete: 2 files / 2 units still fail; this doc addresses
`realtime_event_source.clock_worker` only.

## 0. Platform (the safe base) and mirror
* analyzer = landed repo HEAD `core/cfg/region_analyzer.py`, sha256[:16] **`842e2748bcdfeb66`**
  (verified by hashing the working-tree file; note the repo's core files live in `core/cfg/`, and
  `git show HEAD:…` returns empty blobs there — git-lfs — so hash the file, not the blob).
* generator = banked `[R21-63]` candidate `rounds/round40/r92/CANDIDATE_r2163_675ec7afa414bbb5.py`,
  sha256[:16] **`675ec7afa414bbb5`** (sha1 of that same file is `ca5025cdf1019ed8`, i.e. the campaign
  names by sha256[:16]).
* mirror `D:/Temp/r97/mirror` (core+scripts+parsers+utils+bytecode+pycdc.py, all `__pycache__`
  removed); installed pair verified: `analyzer=842e2748bcdfeb66 generator=675ec7afa414bbb5`.
* NOT used: chain base `db1f0e96072cdcb3` (regresses `plugin_system_risk_calculation/function.pyc`).
* runtime: CPython 3.11.7. Product written fresh to `mirror/out/r97base_realtime_event_source.py`
  (21,548 B) and judged with `--source` (never the in-place product).

## 1. Rigs and their 口径 (they are NOT interchangeable)
| rig | 口径 | reads on this base |
|---|---|---|
| `allwin_r63.py` | drops NOP/CACHE/EXTENDED_ARG | `len orig=1424 prod=1426 delta=+2`, `hunks=2` |
| `unit_diff.py` | same list, prints resolved landing indices | `hunks=2 landings=7 judge_diff=True` |
| `win_r91.py` | opcode-name-only, **keeps EXTENDED_ARG** | `orig=1442 prod=1448 delta=+6`, `windows=4` |

`LOG_r97a_base_measure.txt`, `LOG_r97a_allwin_base.txt`, `LOG_r97a_unitdiff_base.txt`,
`LOG_r97a_winr91_base.txt`.

## 2. Re-measurement of the brief's numbers on my own bytes — CONFIRMED
Judge: `units=12/13`, `***<module>.RealtimeEventSource.clock_worker: Failure: Different control
flow`; 12/13 is the whole file, clock_worker is its only failing unit.

The residual is **insert-only**, exactly two manufactured instructions (`allwin_r63`, the 口径 I
use for every delta below):

```
== #1 insert orig[1046..1046 @7248..-] prod[1046..1047] del=0 ins=1   ->  + @7252 JUMP_FORWARD
== #2 insert orig[1099..1099 @7582..-] prod[1100..1101] del=0 ins=1   ->  + @7590 JUMP_FORWARD
hunks=2
```

and `win_r91`'s 4 windows / 6 instructions are the **same two jumps plus the four `EXTENDED_ARG`s
they force** (prod jumps to a far label): `+@7184 EXTENDED_ARG`, `+@7250 EXTENDED_ARG +@7252
JUMP_FORWARD`, `+@7588 EXTENDED_ARG +@7590 JUMP_FORWARD`, `+@7612 EXTENDED_ARG`. Direct count:
original has 14 `EXTENDED_ARG`s in the unit, product has 18 (+4), NOPs 4 vs 4, so 1424 → 1426 and
1442 → 1448 are the same defect seen through two filters. **One mechanism, not six.**

The 7-landing table reproduced verbatim (`LOG_r97a_unitdiff_base.txt`):

```
~ @7184 POP_JUMP_FORWARD_IF_FALSE -> orig idx1040 | prod @7186 -> idx1392
~ @7210 POP_JUMP_FORWARD_IF_TRUE  -> orig idx1046 | prod @7212 -> idx1046
~ @7246 POP_JUMP_FORWARD_IF_FALSE -> orig idx1099 | prod @7248 -> idx1047
~ @7268 POP_JUMP_FORWARD_IF_FALSE -> orig idx1086 | prod @7274 -> idx1101
~ @7602 POP_JUMP_FORWARD_IF_FALSE -> orig idx1115 | prod @7614 -> idx1392
~ @8972 POP_JUMP_FORWARD_IF_FALSE -> orig idx1384 | prod @8984 -> idx1385
~ @8978 JUMP_FORWARD              -> orig idx1384 | prod @8990 -> idx1392
```

Decoding the indices into offsets (unit_diff口径, `NOP/CACHE/EXTENDED_ARG` dropped):

| orig idx | offset | what it is in the original |
|---|---|---|
| 1040 | `@7216` | the **third leg's test** of the *same* statement (`self.pre_before_trading_date == self.initial_trading_date`) |
| 1046 | `@7248` | the or-condition's **shared body entry** (`now_date != self.first_run_date`, leg D) |
| 1099 | `@7582` | the **next statement's** first block (`now_date > self.before_trading_date`, leg A′) |
| 1086 | `@7492` | the `else:` body (`event_queue.put(PRE_BEFORE_TRADING_START); self.pre_before_trading_date = now_date`) |
| 1115 | `@7634` | the third leg's test of statement 2 (`self.before_trading_date == self.initial_trading_date`) |
| 1384 | `@9144` | **the loop body's tail statement `time.sleep(FPS)`**, which then falls through to the re-test |

| prod idx | offset | what it is in the product |
|---|---|---|
| 1047 | `@7254` | D test (arm 2's condition) |
| 1101 | `@7592` | A′ test |
| 1385 | `@9154` | the product's counterpart of orig `@9142`, the **body-end `JUMP_FORWARD → 9206`** which in the original sits *before* the sleep block and is therefore the "skip the tail statement" edge; landing `@8984` there means the failing leg takes the body-end jump (no `time.sleep(FPS)`) instead of entering `@9156` = the sleep statement |
| 1392 | `@9206` | `LOAD_DEREF self` = the **`while self.active:` re-test block** (= orig `@9194`) |

Landing-count arithmetic (measured, `LOG_r97a_*` + the jumper tally below):

* original jumps landing on `@9194`: **6, all unconditional `JUMP_FORWARD`** (`@8348 @8546 @8590
  @8850 @8902 @9142`) + 1 fall-through from `@9192`; **0 conditional** jumps land there.
* product jumps landing on `@9206`: **11** (`@7186 @7252 @7590 @7614 @8360 @8558 @8602 @8862 @8914
  @8990 @9154`) — the 6 legitimate ones plus **5 extra**, of which 2 are the manufactured inserts.
* original jumps landing on `@9144` (the tail `time.sleep(FPS)`): **4** (`@8924 @8946 @8972`
  conditional, `@8978` unconditional). Product: 2 land on its `@9156` counterpart, 1 on `@9154`
  (past the sleep), 1 on `@9206` — i.e. **3 of the 4 tail-statement landings were re-anchored away
  from `time.sleep(FPS)`**, which is a semantic change, not a cosmetic one.

So the residual is not "6 spurious bytes"; it is *"every exit that the original routes to a
statement got routed to the loop's re-test label"*, plus two jumps that exist only because an arm
was declared with an empty body.

## 3. Q1 — what the analyzer actually declares (original's numbering; `LOG_r97a_q1_regiondump.txt`)

### 3.1 the flat chain containing `@7186`
```
IfRegion  type=IF_ELIF_CHAIN  entry=@7186  exit=@7216  n_blocks=48
  condition_block=@7186      merge_block=@7216
  then_blocks  = [7212]                                   <-- ONE block, and it is a bare JUMP_FORWARD
  else_blocks  = [7248 7372 7488 7492 7582 7604 7620 7630 7632 7634 7668 7706 7708 7710 7712 7814
                  7972 7980 8166 8170 8184 8186 8256 8294 8306 8350 8354 8400 8450 8504 8544 8548
                  8588 8592 8666 8688 8852 8904 8926 8948 8964 8974 8976 8980 9144]   (46)
  elif_conditions = [7248]        elif_bodies = [[7372, 7488]]
  elif_final_else = [7492 7582 7604 7634 7620 7632 7668 8592 7630 7706 8666 8904 7708 7972 8688
                     8852 8926 9144 7710 7980 8170 8948 7712 8166 8184 8964 8976 7814 8186 8974
                     8256 8980 8294 8306 8350 8354 8588 8400 8450 8548 8504 8544]              (43)
  inline_boolop_chains = {'and': [Block@7248-7268, Block@7270-7370]}     <-- only D∧E mounted
  metadata = {then_all_chained_compare: False, is_empty_then_chained_compare: False,
              merge_has_store: False, merge_only_simple_ops: False}
```
Per arm (tail class / jump / fall-through, all read from the CFG):
```
arm0-then   cond=@7186  tail=POP_JUMP_FORWARD_IF_FALSE jump=@7214 fall=@7202
            declared body = [@7212]  tail=JUMP_FORWARD jump=@7216 fall=None
            => arm tail declared to reach the region's own merge/exit (@7216); NO statement block.
arm1(elif)  cond=@7248  tail=POP_JUMP_FORWARD_IF_FALSE jump=@7492 fall=@7270
            declared body = [@7372 tail=POP_TOP fall=@7488, @7488 tail=RETURN_VALUE]
            => arm tail terminator = RETURN_VALUE (reaches nothing).
final-else  first=@7492 (tail=STORE_ATTR fall=@7582) … tail=@9144 (tail=POP_TOP fall=@9194)
            => arm tail declared to fall through into @9194 = the enclosing loop's back_edge_block.
```
Contradictions visible in the declaration itself: `@7248` is simultaneously *this chain's
`elif_conditions[0]`* and *`else_blocks[0]`* and the first block of the mounted `and` boolop chain;
`@7216` is simultaneously this chain's `merge_block`/`exit` and the `condition_block` of a sibling
region; and `elif_final_else` swallows `@7582` (which is a **later sibling statement**, not an else)
and `@9144` (the loop body's tail statement).

### 3.2 the enclosing regions
```
IfRegion IF_THEN  entry=@7164 exit=@7216  n_blocks=51
   condition_block=@7164  merge_block=@7216  then_blocks=[7186 … 9144] (50 blocks!)  else_blocks=[]
IfRegion IF_THEN  entry=@7216 exit=@7582  n_blocks=6   (the third leg C, declared as its OWN statement)
   condition_block=@7216  merge_block=@7582  then_blocks=[7248 7270 7372 7488 7492]
IfRegion IF_THEN  entry=@7582 exit=@7634  n_blocks=28  (statement 2's first leg A′)
IfRegion IF_ELIF_CHAIN entry=@7634 exit=@9194 n_blocks=36   <-- merge == enclosing loop's back_edge_block
   elif_conditions=[8592]  elif_final_else=[8904 8926 9144 8948 8964 8976 8974 8980]
LoopRegion WHILE  entry=@5598 header=@5614 condition_block=@5598 back_edge_block=@9194
   back_edge_blocks=[9194]  is_while_true=False  break=[6690]  body_blocks=96 blocks [5614 … 9194]
LoopRegion WHILE  entry=@5598 header=@5598 condition_block=None back_edge_block=@6792 is_while_true=True
   (the outer `while True:`; its back edge plays no part in any of the 7 landings)
```
Block roles the analyzer itself assigns (`ana.block_roles`): `@7164/@7186/@7216/@7248/@7270/@7492/
@7582` = `LOOP_BODY`; `@9194` = **`LOOP_BACK_EDGE`**; owner of all of them = the outer
`TryExceptRegion` entry=`@6` (region ownership does not discriminate here).
Original fall-through-into-a-later-test facts (the signature the brief asked for):
`@7216 → @7248` ✓, `@7492 → @7582` ✓, plus `@7164 → @7186` and `@7582 → @7604`; and legs whose
**false** exit lands on a later test **of the same statement**: `@7184 → @7216` (with a second
jumper `@7212 → @7216`) and `@7602 → @7634` (second jumper `@7630 → @7634`).

## 4. The original's own source shape at the two sites (decoded from `dis`, Q3)

Statement 1 (`@7164 … @7580`) is ONE `if` with a **flat `or` of an `and` group**, not a nested pair:

```
if (now_date > self.pre_before_trading_date and pre_before_trading <= now_time < pm_close) \
      or self.pre_before_trading_date == self.initial_trading_date:
        # legs: A=@7164..@7184, B=@7186..@7214, C=@7216..@7246
        # or TRUE entry  = @7248 (shared by B's IF_TRUE @7210 and C's fall-through)
        # or FALSE exit = @7582 (the next statement)
    if now_date != self.first_run_date:                     # @7248, D-false -> @7492
        system_log.debug('获取重登信号量')                     # @7270..
        if login_semaphore.acquire(timeout=LOGIN_TIMEOUT * 60) is False:   # E
            system_log.error(...); self.event_queue.put((dt, SYSTEM_EXIT)); return
    else:                                                    # @7492
        self.event_queue.put((dt, PRE_BEFORE_TRADING_START))
        self.pre_before_trading_date = now_date              # @7580, falls through to @7582
```
Our product renders that as `if A: if B or C: pass elif D and E: … else: …` — hence
`if A`-false jumping away from `C`'s test, `C`-false jumping into `D`'s test, and a manufactured
`JUMP_FORWARD` for the empty `pass` arm.

Statement 2 (`@7582 …`) is the same flat shape (`(A′ and B′) or C′` with `C′`'s test at `@7634`,
`A′`-false `→ @7634`), and its chain's arms end on the **tail statement** `@9144 time.sleep(FPS)`,
which then falls through into the re-test `@9194`.

`@9194` vs `@9206`: they are the **same block**. The original's re-test is
`@9194 LOAD_DEREF self / @9196 LOAD_ATTR active / @9206 EXTENDED_ARG / @9208
POP_JUMP_BACKWARD_IF_TRUE → 5614`. In the product every offset after `@7252` is shifted +12 by the
two inserts, so the product's copy of that block starts at `@9206` (`LOAD_DEREF self`) and that
instruction is unit_diff index **1392**. `@9206` is therefore *not* a later leg of a BoolOp or of a
chained compare — it is the loop's condition re-test, which the `while self.active:` LoopRegion
declares as its `back_edge_block`.

## 5. Q2 — which declaration produced prod idx 1392, and why three targets collapsed

`prod idx 1392` = `prod @9206` = the `while self.active:` re-test block = orig `@9194`, declared
`role=LOOP_BACK_EDGE`, `back_edge_block` of the enclosing `LoopRegion`, **and simultaneously the
`merge_block`/`exit` of `IF_ELIF_CHAIN entry=@7634`** (and of four more regions in this unit:
`IF_THEN_ELSE @8294`, `@8400`, `@8666`, `@8948`, all `exit=@9194`).

Answer by measured block role:

* **not (b)** — the `back_edge_block=@9194` election is *correct*: the original itself puts exactly
  6 unconditional `JUMP_FORWARD`s there (genuine `continue`s) and 0 conditional ones. And the
  `condition_block=None` guard the brief points at (`region_analyzer.py:4958-4992`) is not on this
  path at all: the victim loop declares `condition_block=@5598` (non-`None`). The loop that does
  declare `condition_block=None` (`while True:`, back edge `@6792`) is not involved in any of the
  7 landings.
* **it is (a) chain-boundary + (c) arm membership, seen as one defect.** The chain-boundary fold is
  measurable: the single statement `if (A and B) or C: BODY` was split into `IF_THEN @7164` +
  `IF_ELIF_CHAIN @7186` + a sibling `IF_THEN @7216`, with the *body entry* `@7248` claimed as
  `elif_conditions[0]`. That fold makes arm 0's declared body a **bare jump block** (`[7212]`,
  `tail=JUMP_FORWARD → merge`), which the generator must render as an empty `then` (`pass`) and
  therefore *manufactures* a `JUMP_FORWARD` to the arm's end. Because the chain's
  `elif_final_else` then swallows `@7582` (a sibling statement) and `@9144` (the loop body's tail
  statement), **no declared label exists for "the statement after this arm"**; the only label the
  AST can express for anything leaving these arms is the region end, which for chain `@7634` *is*
  the enclosing loop's `back_edge_block`, i.e. `Continue` → `JUMP to @9206`. That single absence of
  a tail-statement label is what the three originally-distinct targets (`@7216`, `@7634`, `@9144`)
  collapsed onto.
* In short: the collapse is an **over-absorbing `elif_final_else` + a `merge_block` that was set to
  the loop's back-edge instead of the region's tail statement**, with the empty-arm `JUMP_FORWARD`s
  as the visible symptom. It is a declaration problem, exactly as the brief predicted
  (`no-landing-channel-in-generator`), and the actionable criterion is *"re-anchor the region end
  label to the tail-statement block, and mount the `or` fold instead of emitting a `pass` arm"*.

## 6. Q4 — censuses of the candidate predicates (no implementation)

Rosters: the 402-file gate roster extracted from `rounds/round39/after/shard*_report.json`
(`files_total` sums to 51×7+45 = 402, `paths_by_status` union = 402 paths; all resolve).

| id | level | definition (short) | EVAL | FIRE | files |
|---|---|---|---|---|---|
| P2 | dis only | `or`-fold witness: forward-test block `Y` falls through into a test block `S` that an **earlier forward** conditional jump also enters, `Y`'s jump target `F ≠ S` | 45 | 45 | 25 |
| **C** | analyzer | **the declaration contradiction**: chain with `elif_conditions` + an arm whose declared body is only bare `JUMP_FORWARD → merge` + `merge_block` is itself a test block + `merge`'s fall-through ∈ `elif_conditions` | 2915 chain-region visits | **3 rows = 1 unique region** | **1** |
| D | analyzer | region's declared `merge/exit` == enclosing loop's `back_edge_block`, while a block inside the region falls through to it and receives conditional jumps from inside the region | 632 | 104 | 33 |
| E | analyzer | D **and** some unconditional jump inside the region also lands on that label | 632 | 81 | 25 |

Logs: `LOG_r97a_census_orfold_part1.txt` (P2, whole 402 in one run: `files=402 units=6617
P(all-shares)=188/63files P2=45/25files`), `LOG_r97a_census_decl_corpus_c1..3.txt` (C, 140+140+122
files), `LOG_r97a_census_decl2_corpus_c1..3.txt` (D), `LOG_r97a_census_declE_c1..3.txt` (E), and
`LOG_r97a_census_decl_p2files.txt` (C restricted to the 25 P2-firing files: `files=25
chain_regions_EVAL=1458 FIRE=3`, i.e. the same single region).

* **C is corpus-unique.** Its one fire is precisely the victim:
  `chain entry=@7186 merge=@7216 fall->elif=@7248 empty_arm=arm0 body=[7212] type=IF_ELIF_CHAIN`
  in `realtime_event_source.clock_worker` (printed 3× only because my region walk visits a region
  both from the top level and through its ancestors — deduplicated, it is 1 region in 1 file).
  Zero collateral by construction.
  Caveat (口径): my EVAL counts every `IfRegion` with non-empty `elif_conditions` per visit
  (2915), which is a superset of r89a's 1269 `IF_ELIF_CHAIN` regions; the FIRE is type-independent
  and deduplicated.
* **P2 covers only site 1**: in clock_worker it fires exactly once, at the victim `Y=@7216`
  (`fall->S=@7248 jump->F=@7582 shortcircuit_from=[7202]`), and does **not** fire at statement 2's
  `@7634` because there the shared entry `@7668` is a `GET_ITER` block, not a test.
* **D/E are a family, not a gate**: 104 (D) / 81 (E) sites in 33 / 25 files, and all files except
  `realtime_event_source` and `trade_live_broker` are currently Equal — so a rule keyed on the
  tail-statement/back-edge collapse has to reproduce the bytes of **23 green files** (`quote_handler`
  12, `history_api` 9, `klinedata` 9, `finance_data_source` 8, `trade_live_broker` 8, `quotation` 6,
  …). That is the same over-fire class the campaign already measured at −269/−274 for
  `[R21-49]`/`[R21-53]`. E's narrowing removed 23 of 104 fires and did not isolate clock_worker.

## 7. Q5 — verdict

**Partially dispatchable; NOT dispatchable as a clock_worker 13/13 ticket on the numbers I measured.**

* Dispatchable, precise, zero-collateral half — the ticket text I would pre-digest for round 41:
  * **mechanism** = a flat CPython `if (X and Y) or Z:` condition is folded into
    `IF_THEN(X) + IF_ELIF_CHAIN(Y)` with `Z`'s test block claimed as the chain's `merge_block` and
    the shared body entry claimed as `elif_conditions[0]`; the fold leaves the first arm's declared
    body a bare `JUMP_FORWARD` block, which the generator renders as an empty `pass` arm plus a
    manufactured `JUMP_FORWARD`, and the same fold's `elif_final_else` then absorbs the following
    sibling statement and the loop body's tail statement, so the only remaining end label is the
    enclosing loop's `back_edge_block` (= `Continue` = the re-test).
  * **site** = `core/cfg/region_analyzer.py`, the `IF_ELIF_CHAIN` arm/merge assignment path that
    produces `elif_final_else` over-absorption and `merge_block == a conditional test block`, driven
    by predicate **C** (fires 1× over 402 files / 6617 units, at `chain entry=@7186` in
    `realtime_event_source.clock_worker`). A correct `or`-fold mount would extend
    `inline_boolop_chains` (which today carries only the inner `{'and': [@7248, @7270]}` entry) with
    the `{'or': [@7164, @7186, @7216]}` triple and re-designate `@7248` as body rather than as an
    elif condition.
  * **acceptance** = clock_worker stays `12/13` unless BOTH sites move; the measurable sub-target is
    `landings=7 → ≤3` and `hunks=2 → ≤1` with `delta=+2 → ≤+1` (allwin口径), predicate C firing
    exactly 1× corpus-wide, and `plugin_system_risk_calculation/function.pyc` 15/15 +
    `replace_utils` 9/9 + `trade_live_broker` 127/128 unchanged.
* The blocking fact for the flip: the unit needs **all six** spurious instructions and **all seven**
  landings gone, and 3 of those landings (`@7590`, `@8984→@9154`, `@8990→@9206`, i.e. the
  `time.sleep(FPS)` tail-statement anchor) belong to site 2, whose only signatures I could name
  (D, E) fire 104×/81× in 33/25 files — 23 of them currently green. I did not find a
  corpus-unique recognizer for site 2 in this diagnosis, and I did not implement anything to test
  whether fixing C alone re-anchors site 2 transitively (the two sites share the same
  `elif_final_else` over-absorption, so that is the first experiment a round-41 dispatch should
  measure, before writing any second rule).
* Also recorded so nobody re-spends a turn: the three landings are **semantically load-bearing** —
  the product currently skips `time.sleep(FPS)` on 2 paths and skips the whole statement 2 on the
  `@7590` path, so "equal instruction count" is not the target; the target is the tail-statement
  anchor.

## 8. Artifacts (all under `D:/Temp/r97/DELIVER`, mirror under `D:/Temp/r97/mirror`)
`FIX_R21-68_clock_worker_landing_diagnosis.md` (this file),
`LOG_r97a_base_measure.txt`, `LOG_r97a_allwin_base.txt`, `LOG_r97a_unitdiff_base.txt`,
`LOG_r97a_winr91_base.txt`, `LOG_r97a_q1_regiondump.txt` (2632 lines: instruction stream, full block
graph with preds/succs, region tree, block ownership+roles, all LOOP/CHAIN declarations, per-arm
tails), `LOG_r97a_census_orfold_part1.txt`, `LOG_r97a_census_decl_p2files.txt`,
`LOG_r97a_census_decl_corpus_c{1,2,3}.txt`, `LOG_r97a_census_decl2_corpus_c{1,2,3}.txt`,
`LOG_r97a_census_declE_c{1,2,3}.txt`, and the rigs `m97.py`, `probe_r97_q1.py`,
`CENSUS_r2168_orfold.py`, `CENSUS_r2168_decl.py`, `CENSUS_r2168_decl2.py`.
No repo file was modified; no candidate was produced; no whole-corpus regen was run.
