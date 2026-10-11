# R21-34 (note + next ticket) — clock_worker placement after M1+M3b, and the missing nested IfRegion

## 1. M1+M3b re-anchored and measured as a PAIR (this is new information)

Both banked builds were cut against generator `37d9fecb893704ac` (gate-31 bytes), which predates
three landings, so neither could be installed as-is. `rounds/round36/merge_m1_m3b.py` re-anchors
them onto the current base `87910190b7ef7c35` by hunk: it diffs each candidate against its own base
(hunks recovered by `difflib`, applied right-to-left, each placed by a 24-line contiguous seam that
must match exactly once, falling back to the narrowest unique pre/post anchor when a later landing
edited the neighbourhood) and keeps only the hunks that belong to each candidate:

* M1 (`01970a924b74afb4`) — both hunks are its own: the 38-line module-level helper
  `_r52_m1_undispatched_struct_entries` and the 20-line use in the `_r23_or_*` else handling.
* M3b (`3aa27a55eff25a80`) — five hunks, but FOUR are already-landed content that r59a carried
  because its base predates gate 32: the 82-line `[R21-25]` helper `_r2125_identical_none_tail_else`,
  the 4-line `[R21-25 发射]` use and the 19-line `[R54-B1]` guard. Only the 23-line `[R21-24-M3b]`
  veto is new, and only that was merged. Installing M3b whole would have duplicated landed code.

Merged file: `D:/Temp/r36/MERGED_m1_m3b.py`, `3d4f27de6d80ab6e`, +81 lines, `py_compile OK`.

Measured in my own mirror against the sealed products:

| unit | sealed (gate 35) | M1+M3b merged |
|---|---|---|
| `realtime_event_source :: clock_worker` | `len orig=1424 prod=1311 delta=-113 hunks=7` | `len orig=1424 prod=1421 delta=-3 hunks=8` |
| file `realtime_event_source.pyc` | 12/13 | 12/13 (no flip) |

So the pair takes the residual from 113 lost instructions to 3 net, but the *hunk* count goes UP by
one, which is the honest reading: the content is now emitted, just not where the original puts it.
The `--all` dump shows exactly one mechanism left:

```
== delete  orig[1179..1288 @7972..@8586]  del=109      ┐ the same ~106 instructions are rendered
== insert  orig[1390..1390 @9194..]        prod[...] ins=106 ┘ 1200 offsets LATE, i.e. a RELOCATION
== delete  orig[949..966 @6690..@6782]     del=17      (holiday_not_do_before guard, still lost)
== replace orig[1393..1395 @9210..@9212]   del=2 ins=17
```

M1 renders the seven undispatched structural entries into the else arm (its own claim: "the existing
bulk-claim then skips them"), and the AST then places them after the `@9194` neighbourhood instead of
at `@7972`. That is the same relocation family as `_sync_worker` and quote's `run_individual_transform`
(NOTE_R21-31) — three residuals, one *placement* root, and it is NOT closed by any declaration added
so far. `@6690`'s 17 instructions are an independent loss and stay on the M1/M3 ticket.
Do not install: no flip. The next action on clock_worker is a placement-side measurement of where
the else-arm statements are spliced, not another arm-body criterion.

## 2. The trade_status blocker named (from FIX_R21-33_r36 §3)

`trade_live_broker :: _trade_status_handle` needs `while True:` (hunk B, analyzer `efd455859b69d8a1`,
measured `delta=+1 hunks=2`) plus the false-edge block emitted AFTER the body as the `if`'s merge.
Hunk C proved generator-side that the merge cannot be placed there: `_generate_block_statements`
renders one block's own instructions and does not dispatch the nested regions it owns, so the then
arm cannot be built by any block-level call. The then arm's regions exist
(`IfRegion IF_THEN cond=@150..184 merge=@296`, `IfRegion IF_ELIF_CHAIN cond=@318..338 merge=@830`),
but the header block's own tail test is not declared as a region at all — the LoopRegion swallowed it
as its condition.

Ticket (analyzer, one mechanism): when `_identify_loop_regions` gives a `while True` header block a
conditional jump whose both exits stay inside the cycle (the criterion already written in hunk B),
also declare the nested `IfRegion` for that test — `condition_block` = the header block, `then_blocks`
= the fall-through subtree, `merge_block` = the jump target that carries the back edge — so the
generator renders `if cond: <regions>` and reduces the merge after it. Acceptance bar unchanged: a
measured unit flip (`_trade_status_handle` to `delta=0 hunks=0 landings=0 judge_diff=False`, broker
124→125/128), the 20-file panel with zero decreases, and the other six broker units' shapes reported
before/after.
