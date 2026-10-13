# FIX_R21-64 — `_sync_worker`: CPython's *duplicated* `while <BoolOp>:` test (entry copy + latch copy) must be assembled as ONE condition, not split into per-leg `while` loops + body statements

Worker: r93a. Spec `region-reduction-v3-full-corpus-100pct-10rounds`, round 40.
Unit: `<module>.TradeLiveBroker._sync_worker`, `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` (file 127/128; flipping it = broker 128/128, corpus 401/402).

## 0. Base certification (landed bytes, verified)

Mirror `D:/Temp/r93` = repo copy of `core/ scripts/ parsers/ utils/ bytecode/ pycdc.py`.

| file | sha256[:16] | required | ok |
|---|---|---|---|
| `core/cfg/region_ast_generator.py` | `b4363f5858e58074` | `b4363f5858e58074` | YES |
| `core/cfg/region_analyzer.py` | `842e2748bcdfeb66` | `842e2748bcdfeb66` | YES |

## 1. Repro canary (base)

`repro/repro_rotated_while.pyc` decompiled on landed bytes → `repro/REPRO_base_product.py`:

```
***<module>.sync_worker: Failure: Different control flow
[single] status=failure units=1/2 success_rate=50.00%
```

Product garbage (base) — matches FIX_R21-61 §4 and TICKET eighth addendum exactly:
```python
        while int(...strftime('%H%M')) < pre_before_trading:   # only leg 1 survives
            time.sleep(60)
            return int(...) >= post_after_trading              # latch copy -> body stmt
            continue
        if holiday_sync_account == '0' and not engine...is_trading_date(...):
            pass
```

## 2. Design (two mandatory halves) — TO APPEND

(filled as implemented)

## 2b. What landed (both halves), with the measured hunks

Candidate analyzer sha16 (pair) `1471c92eca157e46`; Half-1-only `0f767ea7b09e93a9`; builder `build_r93.py` (byte-level, `split(b'\r\n')`, unique-anchor asserts, BOM+CRLF preserved, `py_compile` gate after each write). Generator `region_ast_generator.py` is UNCHANGED (still `b4363f5858e58074`) — both halves live in the analyzer, at identification time, one-way, no retrospective pass.

Three analyzer edits, all gated behind predicate **P** (fires exactly once corpus-wide):

1. **`_r2164_duplicated_test_predicate(loop)`** — predicate P verbatim from FIX_R21-61 §6: header receives (a) a FORWARD conditional jump from a block outside `loop.blocks` and (b) a BACKWARD conditional jump from a block inside `loop.body_blocks`. Reads only terminator opcode class / `conditional_successors` / region-block membership.
2. **`_detect_duplicated_while_test_chain(cond_block, loop)`** (Half 1) — for a P-loop, assemble the single condition chain:
   * **or-head**: from `cond_block` walk fall-through while each leg's FORWARD conditional target `is loop.header_block` (legs entering the body); ≥2 required. Absorbs the ancestor-owned leg `@364`/`@136` legally because its target is exactly the header (the structural conjunct, not ownership).
   * **and-tail**: from the last or-leg's fall-through, collect FORWARD conditional legs whose targets are the loop exit, proven same exit via the landed `[R21-13]` fact (`_is_equivalent_exit_block`, the exit-agreement method `region_ast_generator.py:19451` reads in the opposite direction). Closes when a tail leg's fall-through reaches the header through pure-jump blocks (`_reaches`, fixed to accept an immediate-successor-is-target hit — the real `@700 JUMP_FORWARD→@704` that the repro lacks).
   * returns `[(@232,'or'),(@364,'or'),(@522,'and'),(@544,'and')]` (real) = `A or B or (C and not D)`. Called first in `_detect_while_condition_boolop_chain`; Step 5 then folds `len>=2`.
3. **Step 5 guard-skip** — the recheck-variable guard-trim (`region_analyzer.py:27086`, `_guard_idx2`) deletes the fold because the header block recomputes only leg A (`back_edge==header` stops its traversal), so the conjunctive-tail vars (`holiday`, `is_trading_date`) look unrelated. For a P-loop the whole or-head+and-tail chain is legitimate, so the trim is skipped (`if P: …; continue`).
4. **`_r2164_purge_latch_legs(loop, boolop_region)`** (Half 2) — the latch copy is a body-block member, so it is emitted as body statements (`return <cmp>`, `if …: continue`, bare call, `continue`, `while False: pass`). Remove those body legs at identification time and **re-claim them under the condition BoolOpRegion** (they duplicate the condition), so neither the loop nor the enclosing `while True` renders them. Proof of sameness, not preference: a leg qualifies iff (a) it ends in a conditional jump, carries no STORE, and its loads are a non-empty subset of the assembled condition's loads (the same test recomputed at the back edge), or (b) it is a pure jump/noise exit stub (`@1212`). The body-start header is never purged (it also carries the loop's real statement — `@704` loads `time`, not a subset).

Measured result — first loop renders byte-for-byte as the GOLD oracle `broker_GOLD_PROOF.py:840`:
```python
while int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading or int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading) or holiday_sync_account == '0' and not self.engine.data_proxy.is_trading_date(datetime.datetime.now().date()):
    time.sleep(60)
```

## 2c. Measured negative on the FULL flip (report failure as failure)

`_sync_worker` contains **two** independent duplicated while tests:
* **loop 1** `@232/@704` mixed `or`-head+`and`-tail — predicate P FIRES, fixed by R21-64 (condition matches GOLD 840, latch purged, no `while False`).
* **loop 2** `@1890/@2072` `while pre_before_trading <= int(...) < int(post):` chained comparison — **P does NOT fire** (measured: forward-legs-outside `[]`, `back_edge=2844 != header=2072`). This is window #5 (`del=162 @1890..@2884`), present UNCHANGED in base and candidate.

Consequence: R21-64 alone does **not** flip `_sync_worker` to Equal; the file stays **127/128**. The GOLD 128/128 requires BOTH this fix and a loop-2 (chained-compare duplicated-test) fix, which is outside predicate P and outside this ticket's scope (FIX_R21-61 §8 "do not re-open the chained-compare axis"; that axis is loop 2's cause, not loop 1's). All instruction-delta / window / census / canary numbers below are measured, not claimed.

## 3. Halves ablation table

| side | analyzer sha16 | broker judge | broker delta / windows | repro judge | loop-1 `del=61 @700..@1210` window |
|---|---|---|---|---|---|
| base (landed) | `842e2748bcdfeb66` | 127/128 Different control flow | −3 / 5 windows (#1..#5) | 1/2 | present (#4 del=61) |
| Half 1 only (chain, no purge) | `0f767ea7b09e93a9` | 127/128 Different control flow | +19 / loop-1 `del=61` gone; latch leaks `while False: pass` in loop body | 1/2 | eliminated; latch copy still emitted (`while False`) |
| Half 2 alone | — | = base (purge is gated on the fold; with no assembled chain there is nothing to purge) | = base | = base | n/a |
| **pair (Half 1 + Half 2)** | `1471c92eca157e46` | 127/128 Different control flow | +19 / windows #1 del2 @700, #2 ins23 @1210, #3 ins160 @1214, **#4 del162 @1890 (=loop 2)** | 1/2 (loop 1 clean, loop 2 chained-compare stray remains) | **eliminated** (loop 1 == GOLD 840) |

Half 1 alone is a no-flip (latch copy leaks as body statements); Half 2 cannot fire without Half 1's assembled chain; the pair is required for loop 1 to render correctly — matching FIX_R21-61 §5.3's "one half = no flip". Neither flips the *unit* because loop 2 + the reconnect-nesting flattening are separate, P-negative defects.

## 4. Regression canaries (pair installed, fresh `--source` products)

All six match their baselines exactly — collateral is empty, as predicate P predicts.

| file | expected | measured |
|---|---|---|
| `plugin_system_event_source/realtime_event_source.pyc` | 12/13 | 12/13 (failure = its own known unit, not `_sync_worker` family) |
| `IQCommon/util/replace_utils.pyc` | 9/9 | 9/9 |
| `plugin_system_risk_calculation/function.pyc` | 15/15 | 15/15 |
| `fly/data/quote.pyc` | 92/92 | 92/92 |
| `fly/data/quotation.pyc` | 153/153 | 153/153 |
| `fly_api/order_api.pyc` | 37/37 | 37/37 |

Built on the landed bytes only (`function.pyc` reads 15/15, so no dependence on the clock_worker chain `db1f0e96072cdcb3`).

## 5. P census with the rule's ACTUAL predicate

`census_r93.py` calls `RegionAnalyzer._r2164_duplicated_test_predicate` over every `LoopRegion` with a non-None `condition_block`, all 402 files (log `logs/CENSUS_r93_corpus.txt`):

```
DONE files=402 evaluations=173 fires=1
FIRE trade_live_broker.pyc :: _sync_worker :: cond=@232 hdr=@704
     chain=[(232,'or'),(364,'or'),(522,'and'),(544,'and')]
```

173 evaluations / 1 fire — identical to FIX_R21-61 §6. No `ANALYZE_FAIL`, no `MISSING`.

## 6. Full 402 sweep

`sweep_r93.py` regenerates every corpus product with the candidate analyzer and CR-stripped
byte-compares each against its committed `<name>OK.py` (CR-stripped; log `logs/SWEEP_r93_corpus.txt`):

```
files_compared 402
MISSING/FAIL 0
CHANGED_COUNT 1
  CHANGED site-packages\IQEngine\plugins\plugin_system_trade\trade_live_broker.pyc
```

`CHANGED = {trade_live_broker}` exactly as predicted. The changed broker product is judged
**127/128** (base and candidate both fail ONLY `_sync_worker: Different control flow` — no other
broker unit regressed). This proves the rule's blast radius is the single P-loop.

## 7. Verdict

* Half 1 (duplicated `or`-head+`and`-tail chain assembly) + Half 2 (latch-copy purge, re-claimed under the condition BoolOpRegion) are both implemented at identification time, gated on predicate P, one-way, no retrospective repair, no names/offsets/counters/thresholds. The pair makes loop 1 of `_sync_worker` render **byte-for-byte as the GOLD oracle** (`broker_GOLD_PROOF.py:840`) and eliminates the loop-1 `del=61 @700..@1210` window.
* **The unit does NOT flip: `_sync_worker` stays 127/128 (broker not 128/128).** Measured cause: `_sync_worker` contains a SECOND duplicated while test — loop 2 `while pre_before_trading <= int(...) < int(post):` (chained comparison, `@1890/@2072`) — on which predicate P provably does not fire (forward-legs-outside `[]`, `back_edge=2844 ≠ header=2072`). It is window #4/#5 (`del=162 @1890..@2884`), unchanged by R21-64. A third, independent defect (the reconnect block rendered as a flat `if A and B and C and D:` instead of the nested `if A: if B: if C: if D:`) also predates and is orthogonal to P. GOLD 128/128 therefore needs loop 1 + loop 2 + reconnect-nesting, i.e. this ticket is **necessary but not sufficient** for the flip.
* **Canary**: repro `repro_rotated_while.pyc` remains **1/2**, but it DOWNGRADES from the base's
  `Different control flow` to `Different bytecode` — i.e. loop 1's control flow is now correct
  (`while A or B or C and not D: sleep(60)`, matching the target), and the only residual is loop 2's
  chained-compare stray instruction (`pre_before_trading`), which P does not cover.
* **Zero collateral confirmed**: 6/6 canaries at baseline, P census 173 evals / 1 fire, 402-file sweep CHANGED = {trade_live_broker}. Repo untouched.

The flip bar (`_sync_worker` Equal, broker 128/128, repro 2/2) is NOT met by this ticket; the
measured halves table above documents exactly what moved and why the remainder did not, rather
than an unmeasured claim. Recommended follow-up (not in scope): a chained-compare duplicated-test
rule for loop 2 (`back_edge≠header`, exit-joined latch legs) — the axis FIX_R21-61 correctly kept
out of the loop-1 cause.

## 8. Deliverables

```
DELIVER/FIX_R21-64_duplicated_while_test_condition.md   this document
DELIVER/region_analyzer_R21-64a.py                       pair candidate, sha16 1471c92eca157e46
DELIVER/region_analyzer_R21-64a_half1.py                 Half-1-only candidate, sha16 0f767ea7b09e93a9
DELIVER/region_ast_generator_LANDED_UNCHANGED.py         generator (unchanged), sha16 b4363f5858e58074
DELIVER/BROKER_cand.py / BROKER_half1.py                 broker products (pair / Half-1)
build_r93.py                                             byte-level builder: regenerates the candidates
                                                          from landed repo bytes (BOM+CRLF, unique-anchor
                                                          asserts, py_compile gate), `half1`|`all` mode
sweep_r93.py, census_r93.py                              sweep + P census rigs
repro/probe_sync.py                                      read-only region/CFG probe
logs/  SWEEP_r93_corpus.txt, CENSUS_r93_corpus.txt,
       <canary>_cand.py (6), dep_broker_err.txt, gold/mine/base sync diffs
```

Patch + full-file candidates delivered; NOT installed into the repo.


