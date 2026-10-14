# FIX_R21-63 — narrowing `[R21-38-r63a]`: the break-landing-is-inner-flow guard must not silently
# claim a block that carries its own statement payload (`create_daily_stats` 14/15 → 15/15)

Ticket **R21-63 (was R21-58 narrowing, task #143)** · spec `region-reduction-v3-full-corpus-100pct-10rounds`
· round 40 · engineer **r92a** · mirror `D:/Temp/r92` (repo `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`
is READ-ONLY for this ticket: `git status --porcelain -- core/` empty before and after; no write anywhere
under the repo, none under sibling mirrors r88/r89/r90/r91).

## 0. Mirror certification

| file | required sha256[:16] | measured in `D:/Temp/r92` |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `b4363f5858e58074` | `b4363f5858e58074` **OK** |
| `core/cfg/region_analyzer.py` | `842e2748bcdfeb66` | `842e2748bcdfeb66` **OK** |

Builder credibility control (nothing taken on trust, including borrowed tooling): `D:/Temp/r88/work/`
builders/logs copied to `D:/Temp/r92/work/` (only `MIRROR =` repointed). The banked single-hunk
transplants re-hash to exactly the sha16s the brief and r88a's §F/§G document:

| artifact | documented sha16 | measured from the copy |
|---|---|---|
| `abl_S1_both_P1P2.py` (step 1 = M1+r63a) | `411c2bd948cd33ad` | `411c2bd948cd33ad` **OK** |
| `abl_S1_only_M1.py` | `e5849f71a6682aa1` | `e5849f71a6682aa1` **OK** |
| `abl_S1_only_r63a.py` | `1e1e0cdeecf7957b` | `1e1e0cdeecf7957b` **OK** |
| `REANCHORED_r2158_db1f0e96072cdcb3.py` (full chain) | `db1f0e96072cdcb3` | `db1f0e96072cdcb3` **OK** |
| `REANCHORED_r2158_m1clean_979058f420b97f64.py` (r63a-free chain) | `979058f420b97f64` | `979058f420b97f64` **OK** |

Rig note: `pycdc.py:613` declares `--region` with `default=True`, so the brief's
`python -X utf8 pycdc.py <pyc> -o <out>` and r88's explicit `--region` are the same code path.

## 1. Measured facts I build on (r88a §F/§G + my own re-reads; NOT re-derived here)

* Layered chain on landed `b4363f5858e58074`: step1 `411c2bd948cd33ad` → +`[R21-45]`AB `945ffcd098db6b00`
  → +`[R21-44]` `07deef97054dbadb` → +`[R21-46]`AB `db1f0e96072cdcb3` (clock_worker `+2 / 2 windows /
  7 landings`, judge 12/13) — but `function.pyc` **14/15**, `<module>.create_daily_stats`
  `Different control flow`, `delta=-32`.
* `[R21-24-M1]` alone (`e5849f71a6682aa1`): clock_worker `-6/5/12`, `function.pyc` **15/15**.
* `[R21-38-r63a]` alone (`1e1e0cdeecf7957b`): clock_worker `-113/7/18` (= landed base, buys nothing
  solo), `function.pyc` **14/15** → r63a is the sole carrier.
* r88a §G: the r63a-free full chain `979058f420b97f64` is corpus-swept CHANGED=1 (target only) but
  clock_worker reads `0 / 4 windows / 10 landings` — so **r63a is load-bearing for the endpoint's
  2-window/7-landing shape** (it interacts with steps 3–4), and deleting it is not the fix.

## 2. What `[R21-38-r63a]` actually is, on the landed bytes

Diff `pristine b4363f5858e58074` → `abl_S1_only_r63a.py 1e1e0cdeecf7957b` = 5 hunks (all pure inserts
except H5). Line numbers below are in the **full chain `db1f0e96072cdcb3`** (61739 lines).

| hunk | lines | content | silent-claim? |
|---|---|---|---|
| H1 | 401–502 (shared with M1) | helper defs: `_r52_m1_undispatched_struct_entries` (M1), `_r63a_break_landing_is_inner_flow`, `_r63a_block_dominated_by` (emitted **twice** by the merge rig; second def shadows the first, identical body — harmless) | predicate only, no effect |
| H2 | 7044–7047 | `_r58_collect_break_target_stmts`: `if _r63a_break_landing_is_inner_flow(self, bb): continue` | skips collecting a break-target block's statements (they may be collected by the arm renderer instead) |
| H3 | 27415–27429 | `if _meaningful_instrs: if _r63a…(self, block): ents=_r52_m1…([block]); if ents: emit region; generated_blocks.add(block); generated_offsets.add(…); continue` | **YES — marks the block generated and emits nothing when the block is not a structural-region entry** |
| H4 | 32296–32301 | try/except handler tail `hb` with role BREAK/PURE_BREAK: `if _r63a…(self, hb): generated_blocks.add(hb); …; continue` | **YES — claims the handler block, emits nothing** |
| H5 | 54654–54655 | conjunct appended to the `[R21-55]` single-forward-pure-jump-break rule: `and not _r63a…(self, _r55_s)` | NO — that site's `_r55_pure` predicate already proves `_r55_s` has no payload instruction at all; it can only refuse a Break, never delete statements |

Hypothesis from the shape (to be MEASURED in §3, not asserted): the `create_daily_stats` loss is
`del=32 ins=0` = the three `strftime` assignments plus the `break` terminator of one block, emitted
by nothing — i.e. a **claim-without-emit**, which only H3 and H4 can produce. H5 is provably payload-
free by its own enclosing conjunct; H2 removes collection, not emission, of a *break-target* block.

## 3. Per-hunk ablation on the full chain — METHOD

Each row: start from `REANCHORED_r2158_db1f0e96072cdcb3.py` (assert `db1f0e96072cdcb3`), delete exactly
that hunk's lines (revert-to-pristine shape; for H5 restore the single `…'JUMP_ABSOLUTE')):` line),
install as the mirror generator with the landed analyzer `842e2748bcdfeb66` in the same line of output,
regenerate `function.pyc` + `realtime_event_source.pyc`, judge with the sole judge
`scripts/pyc_verify.py single`, and read `create_daily_stats` / `clock_worker`
(`unit_diff` for delta+landings, `allwin_r63` for unfiltered windows). A product **byte-identical
(CR-stripped) to the full-chain product** means that hunk was NOT the producer.

 rig: `D:/Temp/r92/work/abl92_hunk.py` → `D:/Temp/r92/work/LOG_abl92_hunk.txt`
 products: `D:/Temp/r92/work/abl92out/`

_(results appended below once measured)_

## 3. Per-hunk ablation RESULT — **H3 is the sole producer**

`work/abl92_hunk.py` → `work/LOG_abl92_hunk.txt`. Every row resets BOTH core files, prints BOTH
sha16s, regenerates + judges both files; `IDENTICAL` / `DIFFERS` is CR-stripped byte-equality against
the CTRL (un-ablated chain) product of the same row.

| row | hunk reverted | gen sha16 | `function.pyc` | `create_daily_stats` | product vs chain | clock_worker `delta/windows(hunks)/landings` | product vs chain |
|---|---|---|---|---|---|---|---|
| CTRL | none (= `db1f0e96072cdcb3`) | `db1f0e96072cdcb3` | **14/15** | `delta=-32 hunks=8` | — | `+2 / 2 / 7` | — |
| H2 | `_r58_collect_break_target_stmts` skip | `324845939a44a08b` | 14/15 `delta=-32` | unchanged | **IDENTICAL** | `+2 / 2 / 7` | **IDENTICAL** |
| **H3** | **`if _meaningful_instrs:` claim-without-emit** | `8fb69856a351e23e` | **15/15** | **`delta=0 hunks=0 judge_diff=False`** | DIFFERS | **`-3 / 4 / 10`** | DIFFERS |
| H4 | handler-tail `hb` claim | `81a9020fe75b7363` | 14/15 `delta=-32` | unchanged | **IDENTICAL** | `+3 / 3 / 7` | DIFFERS |
| H5 | `[R21-55]` conjunct `not …(_r55_s)` | `41602e40972bb149` | 14/15 `delta=-32` | unchanged | **IDENTICAL** | `+3 / 3 / 7` | DIFFERS |
| H3+H4 | both | `33cd0cd06a9eaefb` | 15/15 | `delta=0 hunks=0` | DIFFERS | `-3 / 4 / 10` | DIFFERS |

Readings:

* **H3 alone reproduces the collateral** — removing it takes `function.pyc` from 14/15 to 15/15 with
  `create_daily_stats delta=0 hunks=0` and `judge_diff=False`. H2/H4/H5 removals leave the `function.pyc`
  product **byte-identical** to the chain product, which by the ablation rule proves they are NOT the
  producer. The §2 structural prediction (only H3/H4 can silently claim a payload-bearing block, and
  H5's enclosing `_r55_pure` conjunct already proves its block payload-free) is confirmed by the
  measurement.
* **H3 is simultaneously load-bearing for the chain's gain** — plain revert costs clock_worker
  `+2 / 2 / 7` → `-3 / 4 / 10`. So the fix must be a conjunct, not a deletion; that also retires the
  "just drop r63a" route for the endpoint shape (r88a §G measured the same thing one layer up:
  r63a-free chain `979058f420b97f64` = `0 / 4 / 10`).
* **H4 and H5 do real work on clock_worker** (`+3 / 3 / 7` when each is reverted alone) — both are kept
  untouched.

## 4. The narrowing conjunct — `[R21-63]`, one site, one condition

The defect is a **claim without an emission channel**. H3 marks `block` generated and emits *only*
`self._generate_region(_r63a_ents[0])`; when `block` is not the entry of an undispatched structural
region, `_r63a_ents` is empty and the guard still runs `generated_blocks.add(block); continue`, so the
block's own `_meaningful_instrs` payload is deleted while the pre-existing `_generate_block_statements`
+ Break branch underneath — the code that actually renders `period_close/period_label/period_open` and
the `break` — is skipped. `delta=-32 ins=0` is exactly that.

Conjunct added to the guard (marker `[R21-63]`, full-chain line 27415+):

```python
_r63a_ents = _r52_m1_undispatched_struct_entries(self, [block])
if _r63a_ents and _r63a_break_landing_is_inner_flow(self, block):
```

i.e. **the break/else claim is admitted only when the region it would dispatch exists.** The predicate
is hoisted from the emission channel directly underneath, so it reads no new data — only
region-set membership, entry identity and the two dispatch ledgers (`_generated_regions`,
`_generating_regions`) that `[R21-24-M1]`'s own helper already consumes. Both calls are pure reads, so
hoisting the evaluation order is semantics-free; the only cost is one extra pure lookup per BREAK-role
block with payload.

Compliance with the constraint list: **no function names, no file names, no absolute offsets, no
per-file counters, no thresholds/magic numbers**. One-way by construction (a conjunct can only shrink
the fire set). Correct-at-identification (decided when the block is about to be claimed, from that
block plus the generator's own region set — no cross-region or cross-level heuristic). Unique block
membership is untouched: the refused claim leaves `block` unclaimed and lets the existing owner emit.

Builder: `work/build_cand_r92a_r2163.py` (asserts input sha16 `db1f0e96072cdcb3`, anchor `count == 1`,
the other three r63a call sites present verbatim, `py_compile` clean, CRLF, BOM preserved, 0 `\r\r\n`) →
**`work/CANDIDATE_r2163_675ec7afa414bbb5.py`** (61755 lines, 3891724 B).

## 5. Acceptance bar — both arms, analyzer `842e2748bcdfeb66` in every row

`work/measure92.py` → `work/LOG_measure92.txt` (rows are `unit_diff` + `allwin_r63` + `pyc_verify single`):

| bytes | `function.pyc` | `create_daily_stats` | `realtime_event_source.pyc` | clock_worker `delta/windows/landings` | judge |
|---|---|---|---|---|---|
| landed `b4363f5858e58074` (control) | **15/15** | `delta=0 hunks=0` | 12/13 (`clock_worker`) | `-113 / 7 / 18` | 12/13 |
| chain `db1f0e96072cdcb3` (the un-installable base) | **14/15** | `delta=-32 hunks=8` | 12/13 (`clock_worker`) | `+2 / 2 / 7` | 12/13 |
| **`[R21-63]` `675ec7afa414bbb5`** | **15/15 PASS** | **`delta=0 hunks=0 judge_diff=False`** | **12/13, sole failure still `clock_worker`, no new failure** | **`+2 / 2 / 7` = gain KEPT** | 12/13 |

Canaries on the candidate: `trade_live_broker.pyc` **127/128** with sole failure
`***<module>.TradeLiveBroker._sync_worker: Different control flow` (⇒ `_process_order` Equal),
`replace_utils.pyc` **9/9**, `fly/data/quotation.pyc` **153/153**, `fly/data/quote.pyc` **92/92**,
`order_api.pyc` **37/37**. All hold.

**Not a flip** — clock_worker stays 12/13 with its two spurious `JUMP_FORWARD` windows; no unit was
turned. The deliverable is the un-blocked prerequisite chain.

## 6. Corpus collateral sweep (all 402 roster products + the 3 duplicate artifacts)

Roster built from `r88/work/head_products.txt` ∩ existing `.pyc` = 405, which is a strict SUPERSET of
the canonical `baseline/shards/shard0..7.json` 402 (set-diff `canon_not_in_mine` = **empty**); the 3
extras are `IQCommon/api/klinedataOK.pyc`, `IQCommon/api/klinedataOK_check.pyc`,
`fly/dumpload/_load_algo_recomp.pyc`. HEAD control re-extracted with `git archive HEAD` into
`D:/Temp/r92/head` and certified unchanged vs r88a's copy (407 products compared, **0 content
differences**), so the sweep is measured against the same control r88a used.

`work/sweep.py` 2 budgeted chunks (0 → NEXT=317 → done): **ok=405 bad=0**.
`work/sweep_cmp.py` CR-stripped:

```
compared=405 identical=402 CHANGED=3 missing=0
  CHANGED site-packages/IQCommon/api/klinedataOK.pyc                              head=100529B swept=100960B
  CHANGED site-packages/IQCommon/api/klinedataOK_check.pyc                        head=100361B swept=100978B
  CHANGED site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc  head=20205B swept=21183B
```

* **On the canonical 402 the candidate is `identical=401 CHANGED=1` = the target only — zero
  collateral**, versus `CHANGED=2` for the chain r88a measured (`function.pyc` was the regression).
* `plugin_system_risk_calculation/function.pyc` swept product is **byte-identical to the committed HEAD
  product** (29631 B, CR-stripped) — the repair is not merely "15/15 by judge", it restores the exact
  protected bytes, so the file cannot move in the gate.
* `realtime_event_source.pyc` candidate product is **byte-identical to the chain product** (21183 B) —
  the conjunct changes nothing on the target, which is the strongest form of "gain kept".
* The two `klinedata*` duplicates (`work/canary92.py`, the duplicated-module canary rule): they differ
  from HEAD under **LANDED `b4363f5858e58074` as well as CHAIN and R2163, with the same unit readings
  61/64 and 60/64 and the same failing units** — i.e. HEAD simply stores stale products for those two
  debug copies; not chain collateral, not caused by `[R21-63]`. `_load_algo_recomp.pyc` is a stub in all
  three variants and identical to HEAD. The canonical `klinedata.pyc` **is** byte-identical to HEAD.

## 7. Consequences for the campaign

1. `675ec7afa414bbb5` = the four-layer clock_worker chain with `[R21-38-r63a]` narrowed. It **keeps
   `+2 / 2 / 7`** and returns `function.pyc` to 15/15, so it is the installable replacement for
   `db1f0e96072cdcb3`; `db1f0e96072cdcb3` itself must not be installed.
2. R21-60 (arm ordering by chain-end exit label) can now ride a base that is green on `function.pyc`.
3. Axes this ticket closes: *deleting* r63a (r88a §G, `-3/4/10` for the endpoint shape), reverting H2
   (inert both ways), reverting H4 or H5 (no effect on `function.pyc`, both cost clock_worker).
   "Hunt for a fifth hunk" is also closed — H1 is helper definitions only (and note it emits
   `_r63a_block_dominated_by` twice; the duplicate is shadowed and harmless, but a future re-anchor of
   the step-1 hunks should dedupe it, since the *later* layer `[R21-45]`/`[R21-46]` calls that helper at
   full-chain line 22601 and therefore depends on H1 surviving).
4. Recorded for the panel-bias ledger (§14 of the round-39 adjudication): the chain's collateral was
   invisible for four tickets because `function.pyc` is in no `PANEL_20files.txt`. The 402 sweep is the
   only instrument that saw it, and it is what saw it here too.

## 8. Deliverables (`D:/Temp/r92/DELIVER`)

| file | what |
|---|---|
| `FIX_R21-63_r63a_create_daily_stats_conjunct.md` | this doc |
| `CANDIDATE_r2163_675ec7afa414bbb5.py` | the narrowed full-chain generator (installable) |
| `build_cand_r92a_r2163.py` | builder (anchor-asserting, py_compile + CRLF/BOM clean) |
| `abl92_hunk.py`, `LOG_abl92_hunk.txt` | per-hunk ablation rig + 6-row log |
| `measure92.py`, `LOG_measure92.txt` | acceptance measurement rig + LANDED/CHAIN/R2163 rows |
| `sweep.py`, `sweep_cmp.py`, `roster92.txt`, `LOG_sweep.txt` | 402+3 collateral sweep and comparison |
| `canary92.py`, `LOG_canary92.txt` | duplicated-module canary LANDED/CHAIN/R2163 |

Repo state: `git status --porcelain -- core/ parsers/ bytecode/ utils/ scripts/ pycdc.py` = **empty**
before and after; nothing written under the repo, nothing under r88/r89/r90/r91.
