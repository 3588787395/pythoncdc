# TICKET R21-76 — `clock_worker`: the last failing unit in the corpus (round 41 opener)

## Sealed starting state (gate 40 landed 2026-10-13 13:42)
- Landed: `region_analyzer.py = 1471c92eca157e46` [R21-64], `region_ast_generator.py = 566ff5c502276e48` [R21-74].
- Corpus: **6616/6617 units (99.9849 %)**, **401/402 files**. Residual: 1 file / 1 unit =
  `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc :: <module>.RealtimeEventSource.clock_worker`
  (12/13, *Different control flow*). Next gate label **41** vs `rounds/round40/after`.

## Target measurements on the landed bytes (both 口径, not interchangeable)
- `unit_diff`/`allwin`: `orig=1424 prod=1426 delta=+2`, `hunks=2`, `landings=7`, insert-only
  `@7248 +1`, `@7582 +1`.
- `win_r91` (opcode-name-only, keeps EXTENDED_ARG): `orig=1442 prod=1448 delta=+6`, 4 insert windows
  `@7184 +1, @7248 +2, @7582 +2, @7602 +1` = the two manufactured `JUMP_FORWARD`s (`@7252`, `@7590`) plus the
  `EXTENDED_ARG`s they force.

## Declared facts (dumped twice, r97a then r101a)
`IF_ELIF_CHAIN cond=@7186 merge=@7216`, `then_blocks=[7212]` (bare JUMP_FORWARD ⇒ arm 0 renders `pass` +
manufactured jump); **`@7248` double-claimed** as `elif_conditions[0]` and `else_blocks[0]`, and it is also the
first then-block of sibling `IF_THEN entry=@7216 merge=@7582 then=[7248,7270,7372,7488,7492]`;
`elif_final_else` = 43 blocks and it swallows `@7582` (a later SIBLING statement) and `@9144` (the loop tail
`time.sleep(FPS)`), leaving no declared label for the tail statement.

## Closed by measurement — do not re-open
1. **Predicate C refusal alone** `c93e8994893ee530`: removes the double claim and the sweep reads `401 same / 1
   changed`, but the unit collapses `+2 → −269`, `hunks 2 → 4`, `landings 7 → 2` with three statement ranges lost
   (`@7582..@7836`, `@7960..@8276`, `@8282..@9192`). Proven cause: those blocks are emitted today ONLY because
   `elif_final_else` absorbs them.
2. **R21-60 arm ordering/fall-through**: fires 0× in `clock_worker` over 1269 chains; the true end label `9194`
   demands both spurious jumps.
3. Broad signatures P2/D/E fire in 45/104/81 files including 23 currently-Equal files (the −269/−274 class).

## Work order (r103a)
First build a **GOLD oracle** for `clock_worker` the way the broker was cracked: reconstruct the function's source
from the block graph, splice it into the product, and judge `pyc_verify single --source`. `13/13` proves the target
is expressible and converts the residual into a scored distance. Then decompose oracle-vs-product into individual
textual facts and test each by compiling shapes, so only CFG-visible facts get rules. The candidate must ship the
predicate-C refusal **and** a positive claim that owns `@7582` and `@9144` as sequential loop-tail statements, in one
patch, from region data only (no names/offsets/counters), correct-at-identification, unique membership preserved.
Acceptance is the judge: `units=13/13`; collateral is my own 402-file CR-stripped sweep, which must read
`files_compared=402 MISSING/FAIL=0 CHANGED=1={realtime_event_source}` — remember the sweep rig's relative-path trap
that made a vacuum look like a zero-collateral pass.
