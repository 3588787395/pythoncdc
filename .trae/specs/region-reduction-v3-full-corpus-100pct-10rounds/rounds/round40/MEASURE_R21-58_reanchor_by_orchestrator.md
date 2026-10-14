# MEASURE_R21-58 — my own re-anchor verification (the orchestrator's numbers, not the engineer's)

2026-10-13 08:06–08:08, mirror `D:/Temp/v40`, base = re-anchored chain generator
`REANCHORED_r2158_db1f0e96072cdcb3.py` (sha16 `db1f0e96072cdcb3`, from `D:/Temp/r88/work/`) installed over the
gate-39 analyzer `842e2748bcdfeb66`. The chain itself is r73a P1+P2 → r74a [R21-45] A+B → r73a [R21-44] →
r75a [R21-46] A+B, previously ending at `30a4d7827122e165` on gate-38 bytes.

| file | on this base | product vs committed (CR-stripped) |
|---|---|---|
| `realtime_event_source.pyc` | `len orig=1424 prod=1426 delta=2`, **2 windows, 7 landings**, `status=failure units=12/13` | differs (the chain's intended effect) |
| `trade_live_broker.pyc` | `status=failure units=127/128`, only `_sync_worker` failing | **identical** — `_process_order` stays Equal |
| `IQCommon/util/replace_utils.pyc` | `status=success units=9/9` | **identical** |
| `fly/data/quote.pyc` | `status=success units=92/92` | **identical** |

Readings that matter for round 40:
1. **The re-anchor is faithful.** `delta=+2 / 2 windows / 7 landings` and a 21548-byte product are exactly the
   gate-38 endpoint's numbers, so gate 39's `[R21-55c]`/`[R21-56]` changes neither broke nor quietly absorbed the
   chain.
2. **The chain is inert on the three highest-risk files** — byte-identical products, so it cannot re-introduce the
   `replace_utils` collateral that killed gate 39 attempt 1, and it does not disturb the fresh `_process_order` flip.
3. It still does **not** flip `clock_worker` on its own: the two spurious `JUMP_FORWARD → @9206` remain, which is the
   sequencing question, not a regression question.

Pending from the engineer's run: the corpus-wide 402-file sweep (I have done 3 files by hand; it covers all 402).
Nothing is installed; landed bytes remain generator `b4363f5858e58074` / analyzer `842e2748bcdfeb66`, corpus
6615/6617 (99.9698 %), 400/402 files, gate label 40 unconsumed.


## Unexplored axis, now checked and closed as *derivative*: the exception tables

Every reading this week compared `co_code` only, so I checked `co_exceptiontable` for both residual units on my
re-anchored base:

| unit | `co_code` bytes | `co_exceptiontable` bytes | first table difference |
|---|---|---|---|
| `clock_worker` orig | 9330 | 175 | byte 5: orig `0x01` vs prod `0x07` |
| `clock_worker` prod | 9342 | 176 | (same prefix, then same structure) |

Both tables share the same head pattern and differ by exactly one byte of length plus small encoded values, and
`co_stacksize` (9/9) and `co_flags` (equal) match. The table encodes handler **ranges as offsets**, so two extra
`JUMP_FORWARD`s that shift every subsequent offset necessarily change those varints; there is no evidence of an
extra or missing handler entry. Conclusion: the table difference is a **consequence** of the `co_code` difference,
not an independent defect — do not open a "handler-range" ticket on the strength of it.

## The mechanism nobody has tried on this unit, and what makes it plausible

A flat `if/elif/else` chain gives every arm except the **last** a jump to the single end label; the last arm falls
through. Our product manufactures jumps at product `@7252` and `@7590` (both → `@9206`) where the original falls
through, i.e. **the arms are in an order where two non-final arms are the ones the original put last**. Every
closed axis changed *which region exists* (declaration, filter, collection, membership) or *whether to nest*; none
reordered the arms of the existing flat chain by the one structural fact that decides fall-through: **which arm's
CFG exit is the chain's own end-label block**. That is a successor-comparison predicate over region data, not a
name/offset/count rule, and it is the next thing to try (ticket R21-60).

## Addendum (2026-10-13 08:34, orchestrator, my own mirror `D:/Temp/r91m`) - independent confirmation: [R21-58] costs a green unit

I installed ONLY the re-anchored generator `db1f0e96072cdcb3` (copied content-addressed from
`D:/Temp/r88/work/REANCHORED_r2158_db1f0e96072cdcb3.py`, sha16 re-verified after copy) over the landed analyzer
`842e2748bcdfeb66` in a fresh mirror, regenerated the two files r88a's 402-product sweep flagged as CHANGED, and
judged both with `scripts/pyc_verify.py single --source`:

| file | product | units | verdict |
|---|---|---|---|
| `plugin_system_risk_calculation/function.pyc` | HEAD (landed bytes) | 15/15 `status=success` | green control |
| `plugin_system_risk_calculation/function.pyc` | re-anchored `db1f0e96072cdcb3` | **14/15 `status=failure`** | `create_daily_stats: Failure: Different control flow` |
| `plugin_system_event_source/realtime_event_source.pyc` | re-anchored `db1f0e96072cdcb3` | 12/13, clock_worker `len orig=1424 prod=1426 delta=2 hunks=2 landings=7` | unchanged best-known (still not Equal) |

Provenance cross-check: my regenerated product is 29815 bytes on disk = 29355 CR-stripped, exactly r88a's
`swept=29355B`, so his sweep and my run are the same candidate.

**What is lost** (`unit_diff` on `create_daily_stats`: `del=32 ins=0` over `@196..@336`): the three assignments and
the loop-exiting `break` that follow a nested `if/else` inside a `for ... else:` body are not emitted at all -

```python
for account in ('STOCK_account', ...):
    if account in daily_result:
        if is_csv:  daily_dts = [...]
        else:       daily_dts = [local_to_utc(...)]
        period_close = daily_result[account]['date'].strftime('%Y-%m-%dT07:00:00.000Z')   # DROPPED
        period_label = daily_result[account]['date'].strftime('%Y-%m')                   # DROPPED
        period_open  = daily_result[account]['date'].strftime('%Y-%m-%dT01:31:00.000Z')   # DROPPED
        break                                                                            # DROPPED
else:
    daily_dts = None
```

so the emitted product ends the `if account in daily_result:` body at the `if is_csv/else` region, and the
`for/else` header test compiles to `JUMP_BACKWARD` instead of `JUMP_FORWARD` (`orig[34..35]` vs `prod[34..35]`).
The damage is not only the deleted statements: because the locals are never assigned, three later reads flip
`LOAD_FAST period_close` -> `LOAD_GLOBAL period_close` (`@680`, `@684`, `@688`) - the drop silently changes scope.

**Consequence for round 40, in force now:**
1. The re-anchored chain is NOT a safe platform. Any clock_worker candidate built on `db1f0e96072cdcb3` (R21-60,
   r89a) must also be measured against `function.pyc`, and installing it would read `文件级回退=1` at the gate -
   the gate-39 `replace_utils` pattern repeated. My earlier "chain base is inert" certification is WITHDRAWN: I
   judged broker, replace_utils and quote only, not the corpus. The 402-product CR-stripped sweep is what caught
   it, which is exactly why it is now mandatory.
2. The narrowing question is shape-shaped, not name-shaped: when a statement sequence follows a nested if/else
   region that is itself the last statement of an enclosing conditional arm, and the enclosing container is a
   `for ... else` whose `else` is reached by the loop's natural exit, [R21-58] currently claims those following
   statements to the else/merge side and emits nothing for them. A correct identification-time rule keeps them in
   the arm's own block sequence; the discriminator available at that point is block data (which arm falls through
   into which block, and that the to-be-dropped blocks carry STORE_* and a BREAK-style terminator).
3. Banked value: this shape (`for/else` + trailing statements after a nested if/else + `break`) is a positive
   red for any future [R21-58]-style relaxation and belongs in the repro battery - 32 instructions, 4 statements,
   plus a scope change. An easy-to-watch red.

## Addendum 2 (2026-10-13 09:25, orchestrator, mirror `D:/Temp/r91m`) - [R21-63] verified: the chain becomes installable, and clock_worker's residual changes shape

r92a (dispatched onto the collateral I measured above) localized it by hunk ablation on the full chain and
delivered generator `675ec7afa414bbb5` (`.../rounds/round40/r92/CANDIDATE_r2163_675ec7afa414bbb5.py`): the offender
is hunk **H3**, whose `if _meaningful_instrs:` branch claims a block and `continue`s with no emission channel,
skipping the pre-existing `_generate_block_statements` + `Break` path. Its conjunct hoists the lookup that the
emission underneath already consumes, so the claim requires a non-empty entry list. I re-measured the candidate
myself over the landed analyzer `842e2748bcdfeb66`:

| file | landed HEAD control | full chain `db1f0e96` | **[R21-63] `675ec7af`** |
|---|---|---|---|
| `plugin_system_risk_calculation/function.pyc` | 15/15 | **14/15 (regression)** | **15/15 (collateral gone)** |
| `realtime_event_source.pyc` | 12/13 | 12/13 | 12/13, sole failure still `clock_worker`, no new failure |
| clock_worker shape, my opcode-name rig | `-113` (7 windows) | `+6` at the chain level | `+6`, **4 windows, all inserts**: @7184 +1, @7248 +2, @7582 +2, @7602 +1 |

So the chain is now a *safe platform* and buys still exactly zero flips. Note the shape change my rig reads: with
H3 narrowed, `clock_worker`'s loss is **only spurious insertions** - six instructions, all of them the arm-tail
`JUMP_FORWARD`s landing on the `while self.active:` re-test - with no deletion window at all. That is the same
residual r89a adjudicated as *demanded* by the chain's single end label, which is why R21-60 (arm permutation) is
falsified and why closing these six needs the chain-boundary/fold axis (`[R21-49]`/`[R21-53]` surface, previously
measured at -269), not another veto.

Rig note, stated rather than hidden: my `win_r91.py` counts 1442 original instructions where the campaign's
`unit_diff`/`allwin` count 1424, so its `delta` and window counts are not interchangeable with the engineers'
numbers; both rigs agree on the verdict (12/13, `Different control flow`), and only the judge reading certifies.
