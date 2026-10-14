# R21-31 (note, not a dispatch) — `_sync_worker` is a RELOCATION, and it looks like the same family as quote and clock_worker M2

Measured read-only from the sealed gate-31 bytes (`unit_diff … _sync_worker --prod <on-disk OK.py> --all`).
Registered as `−3/5/6`, which reads like a small loss. It is not: the streams are re-ordered en masse.

```
len orig=404 prod=401 delta=-3
== replace orig[52..53 @@362] prod[52..59]  del=1 ins=7
   - @362 POP_JUMP_FORWARD_IF_TRUE
   + @362 POP_JUMP_FORWARD_IF_FALSE / @364 LOAD_GLOBAL NULL+time / @376 LOAD_ATTR sleep /
     @386 LOAD_CONST 60 / @388 PRECALL / @392 CALL / @402 POP_TOP
== insert orig[70..70 @@520] prod[76..113]   ins=37   (RETURN_VALUE, then the whole
     `int(datetime.datetime.now().strftime('%H%M'))` computation + SWAP/COPY)
== insert orig[71..71 @@522] prod[114..291]  ins=177  (the `if self.receive_trade_response_flag == 1:`
     body: STORE_ATTR receive_order_response_flag / receive_trade_response_flag … )
== delete orig[90..151 @@700..@1210] del=61  (the same `time.sleep(60)` + `int(datetime…strftime)` text)
```

So ~214 instructions appear EARLY in the product and the corresponding 61 disappear later, netting −3. The
unit is 404/401 with 5 hunks and 6 landings. Two independent sub-defects are visible in the first hunk
alone: the condition is emitted with **flipped polarity** (`IF_TRUE` → `IF_FALSE`) and the `time.sleep(60)`
call is moved INTO that arm.

## Why this is filed as a note

The shape — a region that is rendered in the wrong place because something declared it and then dispatched
it out of order — is the shape r49a assigned to clock_worker **M2** (analyzer labels the region's own entry
as `BlockRole.BREAK`, the BREAK path renders nothing, and `_loop_handle_child_region_entry` dispatches the
region after the loop) and the shape r46a hit in `quote.run_individual_transform` (the relocated
`else: warning` block, `@752..@1114 → @1260+`). Three residuals in three different files, one candidate
common root on the analyzer/declaration side.

r51a is working M2 right now (analyzer). **The first action for this item is not a new engineer, it is a
free measurement:** after r51a's candidate exists, run it against `trade_live_broker.pyc :: _sync_worker` and
`quote.pyc :: run_individual_transform` and compare hunk counts (`_sync_worker` 5/6 landings, quote 10/3).
If M2 moves them, one declaration-side criterion covers three units and is the highest-value landing left in
the corpus. If it does not, `_sync_worker` needs its own ticket with the polarity-flip + call-migration pair
named above, and the relocation claim dies here rather than becoming a fourth "looks like the same family"
guess.

Not dispatched: six engineer mirrors are already running (r50a, r51a, r52a, r53a, r54a, r56a), and I do not
start a seventh on a mechanism whose cheapest disambiguation is a measurement of someone else's candidate.

## RESULTS of the predicted free measurement (02:07, on r51a's live build — a trend read, not a verdict)

Analyzer snapshot measured: `36dea812a1f9c180` (r51a's mirror at 01:49, still mid-flight), generator =
sealed `37d9fecb893704ac`, products regenerated in my own mirror and judged with `--prod`/absolute pyc paths.

| unit | sealed shape | under r51a's live analyzer | verdict |
|---|---|---|---|
| `clock_worker` | `−113 / 7 / 18` | **`−122 / 7 / 18`** | 9 instructions WORSE, no hunk or landing change |
| `quote.run_individual_transform` | `−52 / 10 / 3` | `−52 / 10 / 3` | byte-for-byte unaffected (product 94155 B = sealed size) |
| `trade_live_broker._sync_worker` | `−3 / 5 / 6` | `−3 / 5 / 6` | unaffected |

So the "one dispatch-order family covers three units" hypothesis is **falsified for quote and for
`_sync_worker` by this build**: M2's current criterion does not move them at all. Two consequences, stated
without flattering the intermediate state:
1. Do NOT collapse `_sync_worker` or `quote` into the clock_worker ticket on the strength of a shared
   *appearance*; each keeps its own ticket (R21-28/R21-32 family notes and r46a's banked analyzer half).
2. r51a's in-flight build is currently moving `clock_worker` in the wrong direction (−113 → −122 with the
   same 7 hunks). That is not yet a judgement of the delivered candidate — the file was still being edited,
   and a moving hash is never a verdict — but when the DELIVER lands I will re-measure this exact triple, and
   if the delivered build still fails to reduce the M2 hunk while having zero effect elsewhere, the
   "analyzer role declaration" route for M2 closes and the relocation becomes generator-side, which is a
   materially different round 33.
