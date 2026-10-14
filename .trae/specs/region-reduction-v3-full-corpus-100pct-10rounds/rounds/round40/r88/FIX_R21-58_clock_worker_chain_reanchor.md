# FIX_R21-58 — clock_worker chain: re-anchored on gate-39, re-measured, corpus-swept; the chain carries a FILE-LEVEL collateral and is NOT a verified base

Ticket **R21-58** · spec `region-reduction-v3-full-corpus-100pct-10rounds` · round 39 → round 40
Mirror `D:/Temp/r88` (repo untouched: `git status --porcelain -- core/` empty before and after; no
write anywhere under the repo). All numbers below are my own measurements in that mirror.

## 0. Gate-39 bytes certified

| file | required sha256[:16] | measured |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `b4363f5858e58074` | `b4363f5858e58074` **OK** |
| `core/cfg/region_analyzer.py` | `842e2748bcdfeb66` | `842e2748bcdfeb66` **OK** |

Mirror faithfulness control: with those bytes installed, the regenerated
`realtime_event_sourceOK.py` is byte-identical (CR-stripped) to the committed product **and** to the
`git archive HEAD` copy — so the mirror reproduces the corpus it is supposed to protect, and every
difference reported below is caused by the chain, not by the rig.

## A. Re-anchor — CLEAN. Gate 39 destroyed no anchor; nothing collided.

Each step is the campaign's own declared rebuilder, re-anchored by the campaign's own rig
(`r73/merge_hunks_copy_used_for_reanchor.py`), reused rather than re-invented (rule 6 of the brief).

| step | mechanism | rig / builder | sha16 on gate-38 | **sha16 on gate-39** |
|---|---|---|---|---|
| 0 | landed base | — | `11324f276cce6d5b` | `b4363f5858e58074` |
| 1 | P1+P2 bulk claim = `[R21-24-M1]` + `[R21-38-r63a]` | merge_hunks rig | `cf5868e68208adf6` | **`411c2bd948cd33ad`** |
| 2 | `[R21-45]` A+B (join-claim + try-else phantom break) | `r74/build_cand_r74a_r2145.py --halves a,b --no-probe` | `f51f9de14d216cda` | **`945ffcd098db6b00`** |
| 3 | `[R21-44]` and-leg/or-tail lift | `r73/build_cand_r73_r2144.py --no-probe` | `3e7af79a63b5d0cf` | **`07deef97054dbadb`** |
| 4 | `[R21-46]` A+B (ibc member stmt-prefix veto + arm return) = endpoint | `r75/build_cand_r75a_r2146.py --halves a,b` | `30a4d7827122e165` | **`db1f0e96072cdcb3`** |

Anchor assertions, all satisfied:
* **step 1**: 6 hunks applied, 0 dropped, every one by a unique 12-line content anchor; the rig's own
  faithfulness gate passed (`residual merged-vs-candidate: 5 blocks … every residual block is
  explained; merge is faithful`) and all 5 residual blocks are exactly gate 39's additions
  (`_r2156_tail_is_bounded_statements` +33 · `_r2156_relaxed_used = []` +3 · the `[R21-55c]`
  exception-edge arm replace 13 · `_r2156_relaxed_used.append(1)` +4 · the `[R21-56]` consumption
  block +14). **No chain anchor was rewritten by gate 39.**
* **steps 2–4**: every splice anchor matched `count == 1` in the new base (each builder asserts this
  itself, and `py_compile`s its output). One real collision surfaced and is recorded: the `[R21-44]`
  probe/method anchor pair still matched uniquely, but the r75 builder's `--expect-sha16` default
  (`f51f9de14d216cda`) obviously no longer holds on the new base — passed through `--expect-sha16`,
  no source edit.

Builder credibility control (rule 5 — nothing taken on trust, including my own tooling): the same
three builders run against their **banked gate-38 bases** reproduce
`f51f9de14d216cda`, `3e7af79a63b5d0cf`, `30a4d7827122e165` byte-for-byte. So the right-hand column
differs from the left purely because the base moved.

One-command rebuild: `python -X utf8 work/build_cand_r88a_r2158.py` →
`REANCHORED_r2158_db1f0e96072cdcb3.py`, asserting the landed sha16 on input, echoing every step's
anchor assertions, printing sha16 before/after, `py_compile`-clean, BOM + all-CRLF, 0 `\r\r\n`.

## B. Re-measure clock_worker on the re-anchored bytes — your `+2 / 2 / 7` is CONFIRMED

`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`,
unit `<module>.RealtimeEventSource.clock_worker`, `orig=1424`:

| bytes | delta | unfiltered windows (`allwin`) | landings (`unit_diff`) | judge |
|---|---|---|---|---|
| gate-39 landed `b4363f5858e58074` | **−113** | 7 | 18 | 12/13 |
| **`REANCHORED_r2158` `db1f0e96072cdcb3`** | **+2** | **2** | **7** | **12/13 Different control flow** |
| gate-38 endpoint `30a4d7827122e165` (adjudication §4/§7/§12/§13) | +2 | 2 | 7 | 12/13 |

**The number round 40 builds on is `delta=+2 / 2 windows / 7 landings`, judge 12/13** — unchanged by
gate 39. Stronger: the re-anchored product is **byte-identical (CR-stripped, 21183 B) to the
gate-38 endpoint product**, so `[R21-55c]`/`[R21-56]` neither absorbed nor damaged this unit; the
chain is intact and still not a flip.

The two windows (full dumps in `ALLWIN_r2158_reanchored_clock_worker.txt`; `unit_diff` alone hides
their sub-3-instruction shape — it reports the same 2 hunks but no per-window byte context):

```
#1 insert orig[1046..1046 @7248] prod[1046..1047] del=0 ins=1  →  + @7252 JUMP_FORWARD
#2 insert orig[1099..1099 @7582] prod[1100..1101] del=0 ins=1  →  + @7590 JUMP_FORWARD
```

Both are single spurious `JUMP_FORWARD` and **both target prod `@9206`** = line 216
`while self.active:`'s condition re-test — your description verified exactly, including that they
are owned by the flat chain's empty `then` arm (`if @7186: pass`). The 7 landings
(`orig idx → prod idx`): `1028 @7184 IF_FALSE→1040|1392` · `1037 @7210 IF_TRUE→1046|1046` ·
`1045 @7248 IF_FALSE→1099|1047` · `1050 @7268 IF_FALSE→1086|1101` · `1103 @7602 IF_FALSE→1115|1392`
· `1358 @8972 IF_FALSE→1384|1385` · `1361 @8978 JUMP_FORWARD→1384|1392` (three of them are the
@9206 landings; four are shifts inherited from the arm re-threading).

## C. Corpus-wide collateral sweep — 402 products, CR-stripped vs `git archive HEAD`: **CHANGED = 2**, and one is a REGRESSION

Roster verified first: `baseline/shards/shard0..7.json` == `all402_rel.txt` (402 == 402, set-diff
empty both ways, 0 missing `.pyc`). `sweep.py` 3 budgeted chunks (cursors 0 → NEXT=139 → NEXT=393 →
done): **ok=402 bad=0**. `sweep_cmp.py` (CR-stripped; a naive `cmp` flags all 402 as the checkout is
CRLF and the blob is LF):

```
compared=402 identical=400 CHANGED=2 missing=0
  CHANGED site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc  head=20205B swept=21183B
  CHANGED site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc            head=29631B swept=29355B
```

Per-changed-file judge lines (sole judge `scripts/pyc_verify.py single`):

| file | gate-39 landed | re-anchored chain | verdict |
|---|---|---|---|
| `…event_source/realtime_event_source.pyc` (target) | `units=12/13` `***…clock_worker: Different control flow` | `units=12/13` `***…clock_worker: Different control flow` | **no flip, no regression**; the +978 B is the chain restoring the −17/−6/−109 losses |
| `…risk_calculation/function.pyc` (**collateral**) | **`units=15/15` status=success** | **`units=14/15`** `***<module>.create_daily_stats: Failure: Different control flow` | **FILE-LEVEL REGRESSION.** `create_daily_stats` goes `delta=0 hunks=0` → `delta=−32 hunks=8`: `delete orig[45..77 @196..@396] del=32 ins=0` (a whole 32-instruction statement run lost) plus 7 single-instruction replaces at @138/@680/@684/@688/@1512/@1516/@1520 |

**Consequence, stated plainly: the re-anchored chain is NOT a verified base.** Installed as-is it is
`files 400 → 399`, `units 6615/6617 → 6615/6617` — the same class of collateral that killed gate 39
attempt 1, and it buys no flip. It also means **R21-60, already dispatched onto `db1f0e96072cdcb3`,
is dispatched onto a contaminated base** (see §F for the clean alternative).

## D. The canaries — ALL HOLD on this base (the chain does not re-break gate 39)

Judged from the swept products; the four non-target canaries are not in the CHANGED list, i.e. they
are byte-identical to the committed products, which is the strongest form of the reading.

| canary | required | re-anchored chain | verdict |
|---|---|---|---|
| `trade_live_broker.pyc` | 127/128 with `_process_order` Equal | **127/128**, sole failure `***…_sync_worker` ⇒ `_process_order` Equal | **HOLD** |
| `IQCommon/util/replace_utils.pyc` | 9/9 | **9/9** status=success | **HOLD** |
| `fly/data/quotation.pyc` | 153/153 | **153/153** | HOLD |
| `fly/data/quote.pyc` | 92/92 | **92/92** | HOLD |
| `…fly_api/order_api.pyc` | 37/37 | **37/37** | HOLD |

## E. Not attempted

Gated on A–D being clean. A, B, D are clean; **C is not**, so no new mechanism was spent, and no
census/probe work was done for one — which also means **`two_owner` / `zero_owner` were NOT measured
in this run** (reported as unmeasured rather than as a number under an unstated counting rule).

## F. Attribution — where the collateral actually lives

**Step-wise ablation** (`ablate88.py`; every row resets BOTH core files and prints BOTH sha16s in
the same line, per rule 2):

| row | gen | ana | clock_worker `delta/windows/landings` | `function.pyc` | `create_daily_stats` |
|---|---|---|---|---|---|
| L0 landed | `b4363f5858e58074` | `842e2748bcdfeb66` | −113 / 7 / 18 | **15/15** | `delta=0 hunks=0` |
| L1 +P1+P2 | `411c2bd948cd33ad` | `842e2748bcdfeb66` | −6 / 5 / 12 | **14/15** | `delta=−32 hunks=8` |
| L2 +`[R21-45]`A+B | `945ffcd098db6b00` | `842e2748bcdfeb66` | −4 / 3 / 9 | 14/15 | `delta=−32 hunks=8` |
| L3 +`[R21-44]` | `07deef97054dbadb` | `842e2748bcdfeb66` | −5 / 2 / 6 | 14/15 | `delta=−32 hunks=8` |
| L4 +`[R21-46]`A+B | `db1f0e96072cdcb3` | `842e2748bcdfeb66` | **+2 / 2 / 7** | 14/15 | `delta=−32 hunks=8` |

⇒ `[R21-45]`, `[R21-44]`, `[R21-46]` are **inert on `function.pyc`** — identical loss from L1 on.
The collateral is carried entirely by **step 1, the P1+P2 bulk claim**: the oldest layer of the
chain, and the only one of its layers that had never been swept corpus-wide.

**Was it new in gate 39? No.** (`g38_check88.py`, both core files reset per row)

| row | gen | ana | `function.pyc` |
|---|---|---|---|
| gate-38 landed | `11324f276cce6d5b` | `f7d849e974904492` | **15/15** |
| gate-38 P1+P2 | `cf5868e68208adf6` | `f7d849e974904492` | **14/15** `***create_daily_stats` |
| gate-38 endpoint | `30a4d7827122e165` | `f7d849e974904492` | 14/15 `***create_daily_stats` |
| gate-39 endpoint (this run) | `db1f0e96072cdcb3` | `842e2748bcdfeb66` | 14/15 `***create_daily_stats` |

⇒ **The chain has been breaking `function.pyc` since the day it was built.** The adjudication's
`30a4d782 … no other file changed` (§4) and `changed files = 1` (§8) are **20-file panel readings**;
`plugin_system_risk_calculation/function.pyc` is not in `rounds/round38/PANEL_20files.txt` and
appears in no `round39/r7*` log (grep). This is §14's bias reproducing itself one layer deeper: a
panel assembled from residual + canaries structurally cannot see collateral in the 382 files it
excludes, and here it hid it for four tickets.

**Which half of step 1** (`hunk_ablate88.py`; single-mechanism transplants of step 1 onto the
gate-39 bytes, each residual block classified block-by-block as gate-39 code or the deliberately
dropped mechanism, nothing unexplained):

| row | hunks | gen sha16 | clock_worker | `function.pyc` |
|---|---|---|---|---|
| S1 both (control) | 6 applied, 0 dropped | `411c2bd948cd33ad` | −6 / 5 / 12 | 14/15 |
| **S1 only `[R21-24-M1]`** | 2 applied, 4 dropped | `e5849f71a6682aa1` | **−6 / 5 / 12 (identical to both)** | **15/15 CLEAN** |
| **S1 only `[R21-38-r63a]`** | 5 applied, 1 dropped | `1e1e0cdeecf7957b` | **−113 / 7 / 18 (= landed base: buys nothing alone)** | 14/15 (**carries the whole regression**) |

⇒ `[R21-24-M1]` (render leftover undispatched structural entries into the arm they are sequenced in)
delivers **all** of step 1's gain and costs nothing. `[R21-38-r63a]` (the break-landing-is-inner-flow
guards) does nothing alone and is the sole carrier of the `create_daily_stats` −32.

## G. The verified base this run actually recovered — `[R21-38-r63a]`-free chain, `979058f420b97f64`

Rebuilt the whole chain on the M1-only step 1 with the same three builders:

| step | gen sha16 |
|---|---|
| L1' `[R21-24-M1]` only | `e5849f71a6682aa1` |
| L2' +`[R21-45]`A+B | `e01d81ed60758af3` |
| L3' +`[R21-44]` | `69a57fca13be8bcc` |
| **L4' +`[R21-46]`A+B** | **`979058f420b97f64`** = `REANCHORED_r2158_m1clean_979058f420b97f64.py` |

Full corpus sweep of that generator (402 regenerated, ok=402 bad=0, CR-stripped vs `git archive HEAD`):

```
compared=402 identical=401 CHANGED=1 missing=0
  CHANGED site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc head=20205B swept=21679B
```

Readings on it (analyzer `842e2748bcdfeb66` in every row, both hashes logged):

| unit | gate-39 landed | `db1f0e96` (full chain) | **`979058f4` (r63a-free chain)** |
|---|---|---|---|
| `clock_worker` | −113 / 7 / 18, 12/13 | +2 / 2 / 7, 12/13 | **0 / 4 / 10, 12/13** (`#1 del 17 @6690` · `#2 ins @7252 JUMP_FORWARD` · `#3 ins @7590 JUMP_FORWARD` · `#4 replace 2→17 @9210`) |
| `function.pyc` | 15/15 | **14/15 REGRESSION** | **15/15** |
| `trade_live_broker.pyc` | 127/128 | 127/128 | **127/128**, `_process_order` Equal |
| `replace_utils.pyc` | 9/9 | 9/9 | **9/9** |
| corpus | — | CHANGED=2 | **CHANGED=1 = the target only** |

Honest reading of the trade-off: dropping `[R21-38-r63a]` removes the 17-instruction
`self.before_trading_date = now_date` join fix and the @7270 `debug()` fix from the *endpoint*, which
is why the target's window count goes 2 → 4 and its landings 7 → 10; those two half-wins only
survive when r63a is present at step 1 (an interaction between step-1 halves and steps 3–4, not a
solo effect — §F). So:

* **`979058f420b97f64` is the verified base** — zero collateral across all 402 products, all
  canaries holding, clock_worker at `delta=0 / 4 windows / 10 landings`, judge 12/13.
* **`db1f0e96072cdcb3` (the brief's chain) is not installable** and must not be used as the R21-60
  base without first fixing `[R21-38-r63a]`'s over-claim.
* Reproduce either with `build_cand_r88a_r2158.py` (`--only R21-24-M1 --expect 979058f420b97f64`
  for the clean one).

## H. For the next hand

1. Do not build on `db1f0e96072cdcb3`. Build on `979058f420b97f64` (§G, swept clean) or re-earn the
   r63a halves against `create_daily_stats` first — the failing shape there is a **32-instruction
   delete at `@196..@396` with 7 single-instruction polarity replaces**, i.e. one of the r63a guards
   is stamping a Break/claiming a block that in `function.pyc` is real post-loop sequence. That is a
   conjunct problem inside `[R21-38-r63a]`, not a new axis.
2. Axes closed and not re-run here (brief's list, unchanged by my measurements): `[R21-44]`
   conjunct-⑧ blanket/gated (−274/5), `[R21-49]` whole-chain refusal / `[R21-53]` narrow shared-exit
   (−269), `[R21-48]` filter-suppression + phantom-else (+3/+2/+3), `[R21-52]` POP_TOP membership,
   `[R21-54]` elif→nested-else (0 `co_code` diffs), `_orphaned_blocks` as emitter (0 events),
   `merge_block is None` census (0 regions).
3. The panel is not collateral evidence. Anything in this chain that has only a 20-file panel behind
   it should be treated as unswept.
