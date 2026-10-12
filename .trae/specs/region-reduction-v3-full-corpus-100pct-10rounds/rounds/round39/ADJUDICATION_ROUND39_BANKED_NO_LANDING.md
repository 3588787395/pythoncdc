# ADJUDICATION_ROUND39 — five engineers, four banked candidates, zero flips (2026-10-12)

Round 39 has consumed no gate label: the corpus still reads the gate-38 sealed
**6614/6617 (99.9547%), 400/402 files, residual 2 files / 3 units**
(`rounds/round38/RESIDUAL_ROUND38.md`, `UNREGISTERED=0`). Nothing from this round is installed;
`git status --porcelain -- core/ site-packages/` = 0 lines all round, and the landed bytes are still
generator `11324f276cce6d5b` / analyzer `f7d849e974904492`.

**Every number below was re-measured by me in a clean mirror (`D:/Temp/v39`, built from repo `core/
scripts/ parsers/ utils/ bytecode/ pycdc.py`), not copied from an engineer's report.** Where a
claim comes only from an engineer I say so.

## 1. Residual shapes on the landed bytes (measured 12:34, repo `unit_diff.py`)

| unit | shape |
|---|---|
| `realtime_event_source.clock_worker` | `orig=1424 prod=1311 delta=-113` (hunk 1 = the 17-instruction `if holiday_not_do_before == '0': event_queue.put(...)` body at `@6690`) |
| `trade_live_broker._process_order` | `orig=507 prod=439 delta=-68` (hunk 1 = 15 instructions `@1638..@1710`, the whole `strategy_log.info(_('生成订单…'))` statement) |
| `trade_live_broker._sync_worker` | `orig=404 prod=401 delta=-3` (hunk 1 = `POP_JUMP_FORWARD_IF_TRUE` vs our `IF_FALSE` + inline `time.sleep(60)`) |

## 2. Ticket numbering collision, fixed on the record

`R21-44` was taken twice today (r71a for broker `_sync_worker` compound-while, r73a for clock_worker
or-tail). From here I pre-assign numbers in the dispatch: **R21-45 = r74a**, **R21-46 = r75a**,
**R21-47 = r76a**. `rounds/round39/r71/FIX_R21-44_sync_worker_compound_while.md` and
`rounds/round39/r73/FIX_R21-44_clock_worker_or_tail.md` both keep their original filenames; the
collision itself is the finding, not a typo to hide.

## 3. `_sync_worker` — r71a, banked, `changed files = 0 of 20`

Analyzer candidate `0d568cdd7fe0f167` (`_r2144_detect_while_condition_nested_or_and`, the mirror of
the landed `[R7-B45]`, returning `or_run + and_group = [(232,'or'),(364,'or'),(522,'and'),(544,'and')]`).
Census `head_ok=1, FIRES=1` over the 20 panel files ⇒ corpus-unique. Judge stays **126/128**, delta
stays **−3** (no shrink). Cause of inertness, from the engineer's probe: the BoolOpRegion is built but
`analyze()`'s `block_to_region.clear()` + priority rebuild (`region_analyzer.py:1871` / `:4119`)
reclaims blocks 232/364/522/544 to the enclosing `while True` LoopRegion (BoolOp priority 20 loses),
so the generator never consumes it. Forced retention (the engineer's second product) proves the
generator rebuilds the compound test correctly but the backward recheck leaks `while False: pass`
and the delta **worsens −3 → +19**. Co-requisites to reopen: guard the condition-context BoolOpRegion
from the reclaim, and fold the re-test blocks as the loop back edge. I did not independently re-run
the reclaim probe (it is an in-process census, not a product reading); the product numbers I did verify
as unchanged from landed.

## 4. clock_worker — the real chain, and where it now stands

| base / candidate | sha16 | my measurement | judge |
|---|---|---|---|
| repo landed bytes | `11324f276cce6d5b` | `delta=-113 hunks=7` | 12/13 |
| P1+P2 re-anchored on gate 38 (r73a) | `cf5868e68208adf6` | `delta=-6`, hunks `@6778..@6782`(del 3) `@7270..@7308`(del 6) `@9210..@9212`(rep 2→3) | 12/13 |
| r73a or-tail [R21-44] on plain landed (half-alone) | `248d5253c432eb6b` | not installed; census 847 evals / 2 fires | 12/13 |
| r74a [R21-45] **A+B** on the anchored base | `f51f9de14d216cda` | **`delta=-4`**, unfiltered windows = spurious `JUMP_FORWARD` @6496, spurious `JUMP_FORWARD` @7254, and the 6-instruction `debug` loss @7270..@7308 | 12/13, broker 126/128, quote 92/92, quotation 153/153, order_api 37/37 |
| r74a A+B+R21-44 | `3e7af79a63b5d0cf` | `delta=-5` (closes a hunk, worsens the count) | 12/13 |
| r75a [R21-46] onlyA on r74c | `05abc061c9fb10ed` | `delta=+2`: `delete orig[1050..1067 @7268..@7368] del=17` **paired with** `insert @9194 ins=17` — the 17-instruction block is restored but emitted at the function tail | 12/13 |
| r75a A+B on r74c | `0a2f4a81c593b1c6` | `delta=+3`; **all three windows are single spurious `JUMP_FORWARD`** (@6496/@7254/@7592) | 12/13 |
| **best known** r75a A+B on r74d (A+B+R21-44) | `30a4d7827122e165` | **`delta=+2 / 2 windows / 7 landings`** | 12/13, no other file changed |
| r76a [R21-47A] gated relaxation of conjunct ⑧ | `e38c0348a48a35e6` | `delta=-274 / 5 windows` — window-for-window identical to the blanket relaxation r74a measured; blast radius 1 file | 12/13 |

Two corrections to my own dispatch briefs, both from r76a's re-measurement and confirmed by me:
1. My "r75's A restores content but misplaces it, so A+B must be the fix" framing was half wrong:
   **r75's A+B already emits the 17-instruction block inside its arm**; only A alone relocates it. The
   residual on that base is three single spurious forward jumps, not a loss.
2. The deliverable base is **not** r74c: `@6496` is a [R21-44] site, so best-known is `r74d + R2146AB`
   (`30a4d782`), which is why the residual is "+2 / 2 windows / 7 landings" rather than "+3 / 3".

## 5. The clock_worker blocker, stated as one named region to declare

`compile()` on 3.11.7 in jump-index topology (`rounds/round39/r76/SHAPE_topology_site7164.txt`) settles
the source shape at site `@7164`: `if A and B or C:` **then** `if D: debug(); if E: … ; <@7492 tail
sequential>`. The original matches all six in-window jumps; our product mis-threads three, and "flat
fold but keep @7492 as E's else" still mis-threads D's false exit (+49 vs the original's +36) — so the
fold and the else-tail are two independent requirements, not one.

Why nothing fires usefully: after the fold, the arm's `then=[@7248,@7270,@7492,@7372,@7488]` contains
`@7248`, which is owned by **no region** (only an `inline_boolop_chains` member with `op=None`), and
`_generate_block_statements` swallows it — which is exactly the −274 catastrophe. The named fix, per
r76a and endorsed by me as the correct next ticket: **declare a synthetic
`IfRegion(entry=@7248, then=[@7270], else=[], merge=@7492)`** (analyzer-side, at identification time)
paired with the phantom-else rule, as a co-requisite pair. This is the axis ticket R21-34 named three
rounds ago ("the outer if has no declared region so no block-level call can build its then arm").

Falsified on this unit, do not re-run: blanket or gated relaxation of [R21-44] conjunct ⑧ (−274);
the `_orphaned_blocks` release path as the emitter (0 events in this file); the `merge_block is None`
analyzer census (this code object has zero such IfRegions); treating `@7248+@7270` as one `B and C`
BoolOp (the `debug()` result is `POP_TOP`-discarded, i.e. a statement — the ibc fold is inexpressible).

## 6. What the round changed in method, not just in bytes

- **Nesting is a landing channel.** The campaign's standing conclusion "the generator has no landing
  channel" (three tickets) was too narrow: `R21-43` landed today (gate 38) precisely by re-nesting an
  elif chain, and every candidate in this file works the same lever.
- **Half-alone measurement is cheap and keeps lying impossible.** The pair installed at gate 38 needed
  both halves (generator alone = 27 differing bytes and still `Different`), and r74/r75's 2×2 tables are
  the only reason I could rank `30a4d782` without re-running four builds.
- **Two engineers died with usable bytes and no doc** (r75a truncated report, r71a's numbering
  collision). Reclaiming them cost me four independent judge runs plus four `unit_diff` runs; the
  successor briefs therefore demand "write the doc EARLY, append as you go".

Next gate label **39** still runs against `rounds/round38/after`; round 39 has not consumed it because
nothing landed.
