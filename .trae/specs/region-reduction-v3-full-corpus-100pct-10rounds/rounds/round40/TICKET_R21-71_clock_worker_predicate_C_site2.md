# TICKET_R21-71 — clock_worker: fix the shared-body-entry double-claim (predicate C), then measure site 2 before writing any second rule

Round 40 banked ticket (gate label 40 still unconsumed). Source: r97a's diagnosis
`rounds/round40/r97/FIX_R21-68_clock_worker_landing_diagnosis.md`, re-read by me; the platform is
`[R21-63]` generator `675ec7afa414bbb5` + landed analyzer `842e2748bcdfeb66`, which I measured in `D:/Temp/r91m`:
`plugin_system_risk_calculation/function.pyc` **15/15**, `replace_utils` 9/9, `trade_live_broker` 127/128,
`realtime_event_source` 12/13. **Do not** build on `db1f0e96072cdcb3`: it regresses `function.pyc` to 14/15
(`create_daily_stats` loses three `period_*` assignments and the `break`; `[R21-63]` is exactly the narrowing of the
offending half, hunk H3).

## Measured residual on the platform (two counting 口径, both reported)
`clock_worker` = 12/13, sole failure `Different control flow`.
- `allwin`/`unit_diff`: `orig=1424 prod=1426 delta=+2, hunks=2, landings=7`.
- my `win_r91` (opcode-name-only): `orig=1442 prod=1448 delta=+6`, **4 windows, all inserts, no deletion window**:
  `@7184 +1`, `@7248 +2`, `@7582 +2`, `@7602 +1` — the two manufactured `JUMP_FORWARD`s (`@7252`, `@7590`) plus the
  `EXTENDED_ARG`s their far target forces. The two rigs count instructions differently; only the judge certifies.

Seven landings, of which **three collapse onto one target**: prod index 1392 = `@9206`, the `while self.active:`
re-test, which is the *same* block as orig `@9194` (`@9206` is `@9194` plus one `EXTENDED_ARG`). Original facts:
6 jumps to `@9194` (all unconditional `JUMP_FORWARD` = real `continue`s), **zero** conditional ones; 4 jumps go to
`@9144 time.sleep(FPS)`, of which we re-anchor 3 (`@8984→@9154`, `@8990→@9206`); our product stacks **11** jumpers on
`@9206`. Three landings are semantic, not cosmetic: we skip `time.sleep(FPS)` on two paths and skip statement 2
entirely on the `@7590` path.

## Mechanism, already decided by role census (not by diff appearance)
Not a `back_edge_block` election error: the victim loop declares `condition_block=@5598`, so the
`if condition_block == header:` guard is off-path, and the election is correct. The claim bug is:

```
original   if (A and B) or C: BODY
rendered   IF_THEN @7164  +  IF_ELIF_CHAIN @7186  +  sibling IF_THEN @7216
           chain merge = C's test @7216
           SHARED BODY ENTRY @7248 claimed as elif_conditions[0]
                            (double-claimed with else_blocks[0] and with the mounted {'and':[@7248,@7270]})
           => arm 0's declared body degenerates to the bare jump block [7212]  ->  rendered as `pass`
              plus a manufactured JUMP_FORWARD
           => elif_final_else (43 blocks) swallows sibling statement @7582 and loop-tail statement @9144
              -> no declared label exists for "the tail statement", so the only expressible exit
                 is the loop back edge
```

Fall-through facts that any correct rule must key on: `@7216→@7248`, `@7492→@7582`, `@7184→@7216`, `@7602→@7634`.

## Census already performed — the predicate to reuse
Over all 402 files / 6617 code objects, the **declaration contradiction** predicate (a chain whose `elif_conditions`
entry is also its body-entry, i.e. an arm whose declared body is a bare jump block while the chain merge is entered
from a fall-through that belongs to the shared body) fires on **exactly 1 unique region in 1 file**: `clock_worker`'s
`chain entry=@7186 merge=@7216 fall->elif=@7248 empty_arm=arm0 body=[7212]`. By construction it is zero-collateral.
For contrast, the dis-level `or`-fold witness fires 45 times in 25 files, and the tail-statement-vs-back-edge
candidates 104/33 and 81/25 files — with **23 currently-Equal files** among them, i.e. the same over-fire class that
measured −269/−274 in earlier tickets. Do not re-run those.

## Work order — the transitivity measurement comes FIRST
1. Reproduce the platform numbers (`function.pyc` 15/15 etc.) in your own mirror before touching anything.
2. Implement the identification-time refusal/re-designation for the contradiction: `@7248` is the **body entry**
   (sequential statement sequence after the `or`-chain test), not `elif_conditions[0]`; the empty arm must not absorb
   it. Correct-at-identification, own block data only (region membership, terminator class, fall-through target,
   predecessor sets), no names/offsets/counters/thresholds.
3. **Then measure, do not assume:** does removing the double claim also re-anchor site 2 — the swallowed `@7582` and
   the loop-tail `@9144` — transitively through the same over-absorbing `elif_final_else`? Report landings/hunks/delta
   before and after for `clock_worker`, and the judge verdict. r97a explicitly did **not** test this, and it is the
   single question that decides whether `clock_worker` is one rule or two.
4. Acceptance for landing (unchanged from round 40's rule): a **measured unit flip** — `realtime_event_source.pyc`
   13/13, which also flips the FILE (400→401). `landings 7→≤3, hunks 2→≤1, delta +2→≤+1` is the partial to report if
   it does not flip; a partial is banked, never installed. No-regression panel: `function.pyc` 15/15,
   `replace_utils` 9/9, `trade_live_broker` 127/128 with `_process_order` Equal, `quote` 92/92, `quotation` 153/153,
   `order_api` 37/37, `arg_checker` 49/39/43, `profiler_func` 17/15/18. Mandatory 402-product CR-stripped sweep
   (`git archive HEAD site-packages | tar -x`; never `cmp` against checked-out files) with `CHANGED` listed and each
   changed file judged.

Axes closed on this unit — do not re-open: arm ordering (`R21-60`, falsified by a 1269-region census; under the true
end label `9194` the end-label law *demands* both jumps), `[R21-44]` conjunct-⑧ (−274/5), `[R21-49]`/`[R21-53]`
(−269), `[R21-48]`, `[R21-52]`, `[R21-54]` re-nesting (CPython renders `else: if …` with 0 `co_code` difference from
`elif …`), and `_orphaned_blocks` as an emitter (0 events).
