# FIX_R21-82 — write the emission ledger at every structural-emission site (not only the funnel)

## The rule (one paragraph)

`[R21-81]` added a third ownership ledger `_r2181_emitted_entries` (entry blocks of regions that
actually became source) and consumed it at the if-arm gate
(`region_ast_generator.py:26836`) so a registered nested-region entry that `generated_blocks`
already holds is re-dispatched *unless* the funnel already emitted it. The ledger, however, was
written at only ONE place — the five type-dispatch returns of the central funnel `_generate_region`
(lines 4447/4465/4470/4475/4480). Structural regions are also emitted by DIRECT calls to
`_generate_if/_generate_try/_generate_loop/_generate_with/_generate_match` that bypass the funnel
(18 such calls outside the funnel span). Because those emissions were never recorded, an ancestor
arm that re-offers such an entry sees it as "not yet emitted" and dispatches it a second time,
which is the shape `[R21-81]` blamed for the two collateral regressions (`quote 92/92->89/92`,
`real_quote 45/45->42/45`). R21-82 extends the ledger to EVERY structural-emission site: it records
`self._r2181_note_emitted(<region>, <result>)` POST-emission at each bypass caller, guarded on the
produced source being non-empty (the helper itself early-returns on an empty/falsy AST). The
predicate reads only `region.entry` (region data) and the AST result's emptiness — no function
names, no file names, no absolute offsets as keys, no counters, no thresholds, no magnitude
comparisons; correct-at-identification (the fact "this region became source" is recorded the moment
it is known, no retrospective repair, no reordering, no re-emitting strings). The 18 sites are
enumerated from the AST, not hard-coded, so the rule is position-independent.

## Emission-site list covered (18 direct calls outside `_generate_region`, 4369-4691)

| line | method | region arg -> result var | shape |
|---|---|---|---|
| 903 / 1292 | `_generate_match` | `_wildcard_match -> _match_ast` | assign |
| 1438 | `_generate_match` | `_wildcard_match -> entry_ast` | list-assign |
| 9479 | `_generate_match` | `_entry_region -> _match_ast` | assign |
| 9932 | `_generate_if` | `_header_if_region -> _if_ast` | assign |
| 10091 | `_generate_loop` | `_child_while_cond -> _child_while_ast` | assign |
| 10218 | `_generate_if` | `_header_if_region -> _if_ast_p41` | assign |
| 14597 | `_generate_match` | `entry_region -> match_ast` | assign |
| 29370 | `_generate_if` | `region` (bare `return`) | rewritten to bind+record+return |
| 29880 / 30087 / 30098 / 30511 / 30841 | `_generate_try` | `ntr -> nested_ast` | assign (try-body) |
| 32032 | `_generate_try` | `nr -> _nested_ast` | assign (handler body) |
| 32703 | `_generate_try` | `nr -> nested_ast` | assign (finally body) |
| 38238 | `_generate_match` | `relevant_ref -> nested_gen` | assign |
| 38595 | `_generate_match` | `nested_region -> generated` | assign |

The funnel returns themselves (already recorded by `[R21-81]`) are skipped, so the two halves
compose without double-recording (set add is idempotent).

## Excluded-premise reconciliation — why this is not a repeat of `[R21-79]` / `[R21-81]`

* It is not `[R21-79]` (analyzer tail-release): R21-82 touches **no analyzer criterion**, no tail
  release, no chain-walk fold; it is purely an emitter-side ledger write. The analyzer platform is
  the pinned F5 `996a1b1acf143458` unchanged.
* It is not `[R21-81]` (funnel-only ledger): R21-81 is the *base* this ticket completes; the whole
  point is that the funnel-only ledger is *incomplete* and that incompleteness was the named cause
  of R21-81's two regressions. R21-82 is the follow-up the `[R21-81]` FIX doc itself requested
  ("write the ledger at every structural emission site").

## Verdict — FALSIFIED (inert), do not install, do not progress to panel/sweep

R21-82 is **byte-identical to `[R21-81]` on every product probed**:
- victim `realtime_event_source.pyc`: 20628 B / `7f3d1796815eb4f5`, `instrs=-77`, `jsites=-3`,
  `back=+0`, `hunks_vs_ORACLE=4`, judge `12/13` — identical to base81; instrs did NOT move toward 0;
- `quote.pyc`: 93849 B, **89/92** (unchanged, still regressed vs committed 92/92);
- `real_quote.pyc`: 54675 B, **42/45** (unchanged, still regressed vs committed 45/45).

So the ledger-completion hypothesis is wrong in BOTH directions on this base: it recovers no victim
instruction (step 1 fails) and it does not restore the two regressions (step 2 fails). This confirms
the orchestrator's independent addendum-2 finding (caller-side post-claim at 16 bypass sites moved
the victim nothing) and localises it: whatever suppresses the `@7972..@8586` run is NOT a missing
ledger record at the bypass sites. The gate at `:26775/:26836` refuses those entries for a reason
the emitted-entry ledger does not touch. Banked, not installed; no panel or 402 sweep run per the
step-1 stop rule.
