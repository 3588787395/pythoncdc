# Gate 37 adjudication and landing record — R21-36 landed, quote.pyc fully green, 6613/6617, 400/402

Landed pair (both required; measured alone and together):
* `core/cfg/region_analyzer.py` `efd455859b69d8a1` → **`c069d359cbfe76b0`** — the banked R21-16
  handler-body half (`r46a`, whose own build base predated gate 36) re-anchored hunk-by-hunk onto the
  landed analyzer by `rounds/round36/merge_r46a_onto_landed.py`: 4 hunks applied right-to-left, the one
  diff block that IS the landed R21-33b hunk skipped, and the merge PROVED by re-diffing the result
  against the candidate (only residual = R21-33b). Installing the candidate whole would have silently
  reverted a landed criterion.
* `core/cfg/region_ast_generator.py` `37997bdac555b2e9` → **`20fa73b4e8231f0f`** — `[R21-36 r62a]`,
  +112 lines in three hunks (`:21973` state declarations, `:22139` the 75-line detection,
  `:23110` the 33-line emission, plus a one-line arm-trim at `:22217`).

## Who produced it, and how I got it

Engineer r62a hit its 150-subagent-turn cap **without delivering a candidate file or a FIX doc**; its
final message was an intermediate "now let me run the panel" line. Its mirror held
`patched_generator_20fa73b4.py` and `DELIVER_installed_analyzer_c069d359.py`, and its own
`core/cfg/*` had already been restored to the landed bytes — so the WIP existed only as side files.
I reclaimed it by installing THAT pair into my own mirror and measuring it there rather than trusting
its absent report; everything below is my measurement, and the criterion description is read out of
the diff against the landed bytes, not out of prose.

## The criterion, read from the code

The arm whose `else` block ends in a *pure back-edge block* (uninhabited by the region, payload = one
`JUMP_BACKWARD` after stripping `EXTENDED_ARG/NOP/CACHE/RESUME`, sole predecessor = that arm's tail
block, and marked `'CONTINUE'` by the loop's own `continue_map`, not `'LOOP_BACK_EDGE'`) is an arm
that **cannot reach the merge**, so blocks of `then_blocks` with an offset beyond the arm's tail are
sequential code AFTER the whole `if`, not arm body. Emission then appends an explicit `Continue` to
`orelse` (registering the back-edge block as generated, which retracts the parent body's own emission)
and re-emits the tail blocks after the `If`. Any unmet emission premise (the `If` node is not last,
`orelse` empty, arm already terminated, tail statements empty) falls back byte-exactly.

The load-bearing discrimination is its condition ③ — forward reachability from `else_blocks`, stopping
at the loop header so the back edge cannot drag the whole body into the reachable set, must NOT intersect
the then-blocks beyond the tail. That is exactly what separates this from gate 36's landed shape, where
the join block HAS a predecessor inside the other arm and therefore had to be emitted after the `if`
with the arm negated into a guard. Two opposite renderings, one structural test between them.

## Measurements

| build | `quote :: run_individual_transform` | quote file | broker |
|---|---|---|---|
| sealed gate 36 | `−52 / 10` | 91/92 | 125/128 |
| analyzer half alone | `delta=0 / 2 hunks` (one 9-instruction block misplaced) | 91/92 | unchanged |
| **pair (landed)** | **`delta=0 hunks=0`** | **92/92** | **product byte-identical, 125/128** |

20-file panel on the pair: 19 files byte-identical, only `quote` moved; units
`153/153 92/92 64/64 30/30 58/58 41/41 28/28 45/45 27/27 37/37 125/128 17/17 12/13 43/43
49/49 39/39 43/43 17/17 15/15 18/18` — zero decreases, all six canaries exact.

Chain (`gate_chain.py 37 36`, log `D:/Temp/gate_chain_37_090154.log`): regen **ok=402 bad=0** (546 s,
slow because three engineers were running concurrently), verify rc=0 all eight shards
(`786/786 469/469 538/538 887/887 855/855 998/999 798/801 1282/1282`), report
`[units] 6612/6617 -> 6613/6617 (99.9395%) [files] 399 -> 400` and
`文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0 翻正单元=1`, checks `quotation 153/153 ·
small34 1563 -> 1564 (moves by exactly the flip) · selfcheck OK · pytest 2 failed 282 passed` (the two
registered residents only), `CHAIN_DONE`.

Residual sealed 09:23:04, `UNREGISTERED=0`: **2 files / 4 units** —
`trade_live_broker._process_order` (−68/14), `_process_cancel_order` (−1/3), `_sync_worker` (−3/5),
`realtime_event_source.clock_worker` (−113/7).

## Negative that must be recorded

`_sync_worker` did **not** move: the broker product is byte-identical under this criterion. So the
"one placement family covers quote + `_sync_worker` + clock_worker" claim from
`rounds/round32/NOTE_R21-31_sync_worker_is_a_relocation.md` is **dead for `_sync_worker`** — its
polarity-flip-plus-moved-call pair needs its own mechanism, and this landing does not substitute for
it. `clock_worker` is likewise untouched by it (its product bytes are unchanged in the panel).
