# FIX_R21-61 — `_sync_worker`: step-1 answer is NEGATIVE — the loop-condition window contains **no** chained comparison; the real defect is CPython 3.11's *duplicated* `while`-test layout (entry copy + latch copy), which the pipeline emits as body statements

Worker: r90a. Spec `region-reduction-v3-full-corpus-100pct-10rounds`.
Unit: `<module>.TradeLiveBroker._sync_worker`, `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` (file 127/128).
Written **immediately after step 1** (mandatory evidence 5), appended per step.

## 0. Base certification (plain landed bytes, no banked base)

Mirror `D:/Temp/r90` = repo copy of `core/ scripts/ parsers/ utils/ bytecode/ pycdc.py`.

| file | sha256[:16] | required | ok |
|---|---|---|---|
| `core/cfg/region_ast_generator.py` | `b4363f5858e58074` | `b4363f5858e58074` | YES |
| `core/cfg/region_analyzer.py` | `842e2748bcdfeb66` | `842e2748bcdfeb66` | YES |

These are byte-identical to `rounds/round39/r87/LANDED_r87_region_{analyzer,ast_generator}.py`
(same two sha16s), i.e. gate-39 landed bytes. Corpus at rest: 6615/6617 units, 400/402 files.

Baseline judge line (my own regeneration, `DELIVER/products/BASE_r90a_broker_product.py`, 7.8 s):

```
***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow
[single] .../trade_live_broker.pyc
[single] 产物 D:/Temp/r90/DELIVER/products/BASE_r90a_broker_product.py
[single] status=failure units=127/128 success_rate=99.22%
```

The product is CR-stripped byte-identical to `rounds/round39/r87/products/MEASURED_r87_base_broker_product.py`
(176226 bytes both) and to the installed `trade_live_brokerOK.py` / `trade_live_broker.py`
(sha16 `f25d834a6b0d763e`, 179288 bytes) — so the base reproduces exactly and the only failing
unit in the file is the target (canaries `_process_order`, `_process_cancel_order`, `ipo_stocks_order`,
`_trade_status_handle`, `etf_purchase_redemption` are all inside the 127 Equal).

**There is no ground-truth source.** `site-packages/.../trade_live_broker.py` is *our own product*
(byte-identical to `…OK.py`); `trade_live_broker_decompiled_test.py` is 0 bytes; the pyc header records
source size 246695, which is not on disk. So no text can be copied — it must be derived.

## 1. Step 1 as ordered: does the analyzer see a chained comparison in the loop condition?

Probe `DELIVER/rigs/PROBE_r90a_step1.py` (read-only: it only *calls* landed analyzer methods and reads
`block_to_region`; it cannot change bytes — and `git status` over `core/ scripts/ parsers/ utils/
bytecode/ pycdc.py` is **empty**, so inertness is proven stronger than a byte-compare).
Log: `DELIVER/logs/PROBE_r90a_step1_sync.txt`, `DELIVER/logs/PROBE_r90a_step1_chainedkeys.txt`.

Over `_sync_worker` (54 CFG blocks):

* `_identify_chained_compare_regions` machinery: `_is_chained_compare_header` — **54 evaluations, 2 fires**,
  headers `@1890` and `@2668`. `_detect_chained_compare_pattern` returns a *real* pattern for both:
  `compare_ops=['<=','<']`, `extra_chain_blocks=[2026]` at `@1890` and `[2844]` at `@2668`.
  (Hygiene note: my first pass printed `ops=[] chain_blocks=None` for these and I nearly wrote down
  "pattern is None"; the keys are `compare_ops` / `extra_chain_blocks`, not `ops` / `chain_blocks`.
  `PROBE_r90a_step1_chainedkeys.txt` is the corrected reading and supersedes §2 of
  `PROBE_r90a_step1_sync.txt`.)
* Regions actually **declared** in the tree: **1** — `IfRegion entry=2668 cc_blocks=[2844] ops=['<=','<']`.
  `@1890` is detected but never declared, because `@1890` is already claimed by `LoopRegion@1890`
  (the Step-1 `claimed` guard: blocks taken by Phase-1 Loop/Try/With regions are skipped).
* **Neither `@1890` nor `@2668` lies in the failing window.** The window `@232..@1212` contains
  **zero** `COPY`/`SWAP` instructions. Its six `COMPARE_OP`s are independent legs:
  `@356 <`, `@514 >=`, `@536 ==`, `@868 <`, `@1026 >=`, `@1048 ==` (chain-compare opcodes are only at
  `@2014/@2016/@2832/@2834`, i.e. line 1404 = the *second* loop).

**Therefore the ticket's Fifth-addendum premise is FALSE as stated for this unit.** The chained-compare
machinery is not broken here (both its fires are in the second loop, whose condition our product already
renders correctly as `while pre_before_trading <= int(...) < int(post_after_trading):` at
`BASE_r90a_broker_product.py:848`), and it cannot be extended to declare anything in `@232..@1212`,
because there is no chain there to declare. Step 2's rule ("COMPARE_OP sharing an operand + its own
short-circuit block") would key on a pattern that **does not occur** in the failing window; had I written
it, it would have been a zero-fire rule. Per campaign rule *fires without flips* it would not have been
installable, so no candidate bytes were produced and **no collateral sweep (mandatory evidence 2) was
required or run** — nothing changed to sweep.

## 2. Re-measurement of the orchestrator's claims (mandatory evidence 6)

| claim | verdict | measurement |
|---|---|---|
| `delta=-3` net of `+221/−224`, 5 windows, orig=404 prod=401 | **HOLDS** | `DELIVER/logs/ALLWIN_base_sync.txt`: `len orig=404 prod=401 delta=-3`; windows `#1 del=1 ins=7`, `#2 del=0 ins=37`, `#3 del=0 ins=177`, `#4 del=61 @700..@1210`, `#5 del=162 @1890..@2884` → ins=221, del=224 |
| block graph: `@704` head, `POP_JUMP_BACKWARD_IF_TRUE->704` from `@704`/`@876`, `POP_JUMP_BACKWARD_IF_FALSE->704` from `@1056`, forward from `@232`/`@364` | **HOLDS** | independent re-derivation `DELIVER/logs/JIGSIG_orig_sync_worker.txt`: `target 704: FORWARD from [232,364]; BACKWARD from [704,876,1056]`, sizes `@232 n=15 @364 n=18 @522 n=4 @544 n=15 @700 n=1 @704 n=21 @876 n=18 @1034 n=4 @1056 n=15` |
| "@704 also reached by **forward conditional** jump from `@700`" | **PARTLY WRONG** | `@700` is an *unconditional* `JUMP_FORWARD ->704`; the conditional-forward preds are exactly `[232,364]` |
| signature ("one target hit both ways") is corpus-unique to `_sync_worker` | **HOLDS** | `DELIVER/logs/CENSUS_r90a_signature_rows.txt` via dis-level census of all 402 files / 6617 units in 5 s: `signature_units=1`, `files_with_signature=1` |
| **discriminator = chained comparison in the loop condition** | **FALSE** | see §3 — a plain `<`/`>=`/`==` or-chain reproduces it |
| 11 hand-written loop texts failed | not re-run (closed axis), but see §4: they failed because none used the shape of §3 |

## 3. The construct that actually reproduces the layout (whole-module `compile()`)

`DELIVER/exp_shapes.py`, log `DELIVER/logs/EXP_shapes_r90a.txt`, `DELIVER/logs/EXP_S2_full_blocks.txt`.
Python 3.11.7 on this machine. Signature = target reached by both a forward and a backward conditional jump.

| shape | BOTH-target | fwd preds | bwd preds |
|---|---|---|---|
| **S2 `while (x<pre or x>=post or (h=='0' and not is_trading_date(...))): time.sleep(60)`** | **424** | **[0, 134]** | **[424, 596, 740]** |
| S3 `if <chain>: while <chain>: sleep(60)` | 900 | [452, 584] | [900, 1072, 1242] |
| S4 `while True: while <chain>: sleep(60); sleep(1)` | 452 | [4, 136] | [452, 624, 794] |
| **ORIG `_sync_worker`** | **704** | **[232, 364]** | **[704, 876, 1056]** |

S2 is **block-for-block isomorphic** to the original, including block sizes:

| S2 | n | | ORIG | n |
|---|---|---|---|---|
| @0 IF_TRUE→424 | 16 | | @232 IF_TRUE→704 | 15 |
| @134 IF_TRUE→424 | 15 | | @364 IF_TRUE→704 | 18 |
| @266 IF_FALSE→888 | 4 | | @522 IF_FALSE→702 | 4 |
| @280 IF_TRUE→892 | 14 | | @544 IF_TRUE→1214 | 15 |
| @424 BWD_IF_TRUE→424 | **21** | | @704 BWD_IF_TRUE→704 | **21** |
| @596 BWD_IF_TRUE→424 | 15 | | @876 BWD_IF_TRUE→704 | 18 |
| @728 IF_FALSE→896 | 4 | | @1034 IF_FALSE→1212 | 4 |
| @740 BWD_IF_FALSE→424 | 14 | | @1056 BWD_IF_FALSE→704 | 15 |

**Mechanism**: CPython 3.11 lays a `while <short-circuit-chain>:` out with the test **emitted twice** —
an *entry copy* whose true exits jump forward into the body and whose false exit leaves the loop, and a
*latch copy* placed after the body whose true exits jump **backward** into the body head. So the signature
is not a duplicated `or` chain written twice in the text, and not a chained comparison: it is one
`while` statement whose condition is an `or`-chain (with an `and` tail) whose legs all share the loop's
true-exit. No chained comparison is needed — S2 has none. The ticket's row-3/row-1 reproductions both
happen to be `while`-with-chain tests; the chain-compare "survived four controls" claim is a
misattribution (S5, the only chained-compare shape, gives a *different* signature: BOTH=204,
fwd from [152], bwd from [394,434]).

**Target rendering** (source lines 1381–1386, i.e. what the unit must emit):

```python
        while True:
            while (int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading
                    or int(datetime.datetime.now().strftime('%H%M')) >= post_after_trading
                    or (holiday_sync_account == '0'
                        and not self.engine.data_proxy.is_trading_date(datetime.datetime.now().date()))):
                time.sleep(60)
```

## 4. Minimal synthetic repro (fails today) — the cheapest possible acceptance harness

`DELIVER/repro/repro_rotated_while.py` → `.pyc` (compiled here with the same interpreter), decompiled by
the landed pipeline into `DELIVER/products/REPRO_r90a_rotated_while.py`, judged
(`DELIVER/logs/JUDGE_repro_rotated_while.txt`):

```
***<module>.sync_worker: Failure: Different control flow
[single] status=failure units=1/2 success_rate=50.00%
```

Our 12-line function renders as

```python
        while int(...strftime('%H%M')) < pre_before_trading:     # only leg 1 survives
            time.sleep(60)
            return int(...) >= post_after_trading                 # latch copy → body statement
            continue
        if holiday_sync_account == '0' and not engine...is_trading_date(...):  # entry copy legs 3/4
            pass                                                  # → orphaned if
```

identical in kind to the real unit's garbage (`BASE_r90a_broker_product.py:840-847`). The same file also
reproduces window #5's disease: `while pre <= x < int(post): … pre_before_trading` with the latch copy's
chained compare emitted as a body statement.

## 5. Death map (where the loop-condition assembly loses the chain) — measured, with landed line numbers

Probe `DELIVER/rigs/PROBE_r90a_step1b.py`, step-by-step guard walk `DELIVER/logs/PROBE_r90a_step1b_sync.txt`,
`DELIVER/logs/PROBE_r90a_walkstep.txt`. The inner loop exists: `LoopRegion cond=@232 entry=@232 header=@704
back=[704] body=[704,876,1034,1056,1212] blocks=[232,704,876,1034,1056,1212,2064,2066,2168]`.

1. **`_detect_while_boolop_forward_chain`** (`region_analyzer.py:28132`) accepts leg 1 `@232`
   (`POP_JUMP_FORWARD_IF_TRUE`, true-exit = header `@704`), then walks to the fallthrough successor `@364`
   and dies at `region_analyzer.py:28155-28157`:
   `region_for_ft = self.block_to_region.get(@364)` = the **enclosing** `while True` `LoopRegion@232`
   (`cond=None`, body owns `230,232,364,522,544,700,702,…`), and its
   `interrupts_boolop_forward_chain(@364)` → **True** → `break`.
   Measured: `STEP 0 @232 … ft=@364 owner=LoopRegion@232 interrupts=True → DEAD`.
   Result: chain length 1 → Step 5 (`region_analyzer.py:26951-26953`) requires `len(chain) >= 2` → `continue`.
   This is r71a's "priority rebuild reclaims the blocks" finding, now pinned to one guard line.
2. Even with the veto lifted, **`all_same_target`** (`region_analyzer.py:28189-28201`) is *structurally*
   unsatisfiable for this chain: `@232`/`@364` jump to the header `@704`, but the `and` tail `@522` jumps
   to `@702` (loop exit). That is the same fact [R21-13] `_inline_and_chain_exits_agree`
   (`region_ast_generator.py:19451`) reads in the opposite direction, and it is why the landed
   `_detect_while_condition_nested_and_or_chain` returns **None** here (`region_analyzer.py:28288`):
   `[R7-B45]` covers **and-head + or-tail** (`while A and (B or C):`), not **or-head + and-tail**
   (`while A or B or (C and not D):`). So a *generalization* of [R7-B45]/[B6], not a new veto, is what
   this shape needs.
3. **The latch copy is inside the body.** `loop.body_blocks = [704,876,1034,1056,1212]` — the second copy's
   legs are body members, so `_loop_generate_while` renders them as statements (`return …`, `if …: continue`,
   bare `is_trading_date(…)` call, `continue`). Folding the entry legs without *also* dropping the latch copy
   cannot produce the target text: the emitter would then print the chain twice, which no source text
   compiles to (that is S3's layout, and S3's block graph differs: fwd preds of its both-target are the
   `while`'s own legs, and the `if`'s legs sit before it).
4. `@1890`'s chained compare is detected but **not declared** (Phase-1 `claimed` guard), while `@2668`
   (its latch copy) *is* declared as `IfRegion@2668` — the mirror image of the same duplication disease in
   the second loop, and the reason window #5 shows `del=162 ins=0`.

## 6. Fire census of the predicate the next rule must key on (mandatory evidence 1, BEFORE any edit)

Predicate **P(L)** over a `LoopRegion L` with `condition_block is not None`, read off the CFG only:
(a) L's header receives a **forward** conditional jump from a block **not in L's own block set**
(entry-copy leg owned elsewhere); (b) L's header receives a **backward** conditional jump from a block
**inside L's body** (latch-copy leg). `fire := (a) and (b)`.
Rig `DELIVER/rigs/CENSUS_r90a_predicate.py` (read-only, landed analyzer).

| scope | files | loop-cond evaluations | fires |
|---|---|---|---|
| `rounds/round38/PANEL_20files.txt` | 20 | **82** | **1** |
| whole corpus (`r8_corpus_paths.txt`) | 402 | **173** | **1** |

Single fire, both scopes, identical line:

```
FIRE …/trade_live_broker.pyc :: unit=_sync_worker loop cond=@232 header=@704
     forward-legs-outside=[364] latch-legs-in-body=[704,876,1056] owners=@364:two_owner(LoopRegion@232)
```

Logs: `DELIVER/logs/CENSUS_r90a_predicate_panel.txt`, `DELIVER/logs/CENSUS_r90a_predicate_corpus.txt`
(63 s whole corpus; every file processed, no `ANALYZE_FAIL`, no `MISSING`).

**Owner counting rule (the 148-vs-186 discrepancy).** For a chain-candidate block `b`:
`zero_owner` ⇔ `block_to_region.get(b) is None`; `one_owner` ⇔ the owner **is** this LoopRegion;
`two_owner` ⇔ the owner is a *different* region (here the enclosing `while True` LoopRegion) while `b` is
simultaneously an entry leg of this loop's condition chain — i.e. the double-role case [B11] already names
for chain heads. Census above counts a leg once, under its `block_to_region` key, and reports the *inner*
loop's own condition block as `one_owner` (not as `zero_owner`); a count that treats "claimed by the
enclosing loop" as *unowned for the inner loop* turns 148 into 186 — that is the whole difference, and it
is why the two numbers were never reconcilable.

## 7. Halves / ablation table (mandatory evidence 3)

| side | generator sha16 | analyzer sha16 | delta | windows | landings | judge verdict |
|---|---|---|---|---|---|---|
| base (both landed) | `b4363f5858e58074` | `842e2748bcdfeb66` | −3 | 5 | 6 | `Different control flow`, units=127/128 |
| half A / half B / pair | — | — | — | — | — | **not applicable: no candidate was produced** (§1) |

A one-sided ablation cannot be reported for a change that does not exist; inventing one would have been the
same trap the ticket records ("a one-sided ablation lied to me twice this week").

## 8. What the next dispatch should build (design, all facts measured above)

One identification-time rule, no counters/thresholds/names/offsets, no retrospective repair:

* **Rule** (analyzer, at while-condition chain assembly): a `LoopRegion L` satisfying P(L) has a
  *duplicated test*. Its condition chain is the **maximal short-circuit run whose true exits are L's header**
  — extend the walk of `_detect_while_condition_boolop_chain` across legs whose owner is L's ancestor
  **only when** the leg is not in L's body and its conditional jump target is exactly `L.header_block`
  (the structural fact, not the ownership fact, is what makes absorption legal: absorbing a leg that jumps
  elsewhere would move a test out of its loop), and generalize `[R7-B45]`'s nested walk to
  **or-head + and-tail** so `all_same_target`'s exception for the conjunctive tail is proven from
  `[R21-13]`'s exit-agreement fact rather than assumed.
* **Second half** (mandatory, else no flip): the backward-jumping legs in `L.body_blocks` are the latch copy
  of the *same* condition and must be removed from the body sequence when the condition is assembled from
  the forward legs. Proof of sameness, not preference: both runs have identical conditional-jump target sets
  and identical loop-exit targets (`@702/@1212 → @1214`), and the copy that ends the body has no other
  successor inside the loop.
* **Acceptance checks before asking for an install**: the repro of §4 flips to Equal (cheap, 2 s) — it is the
  canary for this axis; `_sync_worker` then gives the signature in its own product window
  (`allwin` window #4 `del=61 @700..@1210` must shrink toward 0, and `ins=177` window #3 likewise);
  collateral is *provable empty* for any rule keyed on P, because P fires on 1 of 6617 units — still run
  the 402-file CR-stripped sweep, but expect `changed files = {trade_live_broker}`; canaries
  `replace_utils 9/9`, `quote 92/92`, `quotation 153/153`, `realtime_event_source 12/13` unchanged.
* **Do not** re-open: chained-compare widening for `@232..@1212` (no chain there, §1), `while False: pass`
  retention hacks, the exception-table axis, or a twelfth hand-written loop text (§3/§4 now give the shape
  and a machine-checked repro, so texts are no longer the instrument).

## 9. Deliverables in this directory

```
FIX_R21-61_sync_worker_chained_compare_loop_condition.md          this document (hypothesis falsified)
build_cand_r90a_r2161.py                                          base certifier: rebuilds landed bytes
                                                                  byte-exactly from the repo, prints both sha16
                                                                  (NO patch applied — none earned a fire)
jigsig.py, exp_shapes.py                                          block-graph / signature / compile-shape rigs
rigs/PROBE_r90a_step1.py, PROBE_r90a_step1b.py                    read-only analyzer probes (step 1)
rigs/CENSUS_r90a_signature.py, CENSUS_r90a_predicate.py           corpus censuses (§2, §6)
repro/repro_rotated_while.{py,pyc}                                minimal failing input (§4)
products/BASE_r90a_broker_product.py                              landed-bytes product (127/128)
products/REPRO_r90a_rotated_while.py                              pipeline output for the repro
logs/  JUDGE_base_broker.log, JUDGE_repro_rotated_while.txt,
       ORIG_sync_worker_dis.txt, JIGSIG_orig_sync_worker.txt, EXP_shapes_r90a.txt,
       EXP_S2_full_blocks.txt, ALLWIN_base_sync.txt, PROBE_r90a_step1_sync.txt,
       PROBE_r90a_step1b_sync.txt, PROBE_r90a_step1_chainedkeys.txt,
       PROBE_r90a_walkstep.txt, CENSUS_r90a_signature_rows.txt,
       CENSUS_r90a_predicate_panel.txt, CENSUS_r90a_predicate_corpus.txt
```

Repo untouched: `git status --short core/ scripts/ parsers/ utils/ bytecode/ pycdc.py` → empty
(checked after every write; no `\r\r\n` introduced anywhere since no source byte was rewritten).
