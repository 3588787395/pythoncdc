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
