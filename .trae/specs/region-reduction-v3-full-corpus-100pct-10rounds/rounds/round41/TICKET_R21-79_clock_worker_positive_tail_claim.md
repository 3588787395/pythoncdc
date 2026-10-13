# TICKET R21-79 — clock_worker: positive sequential-tail claim for `elif_final_else`

**Owner:** r107a (mirror `D:/Temp/r107`, analyzer-only). **Dispatched:** 2026-10-14 00:46.
**Base (pinned):** `region_analyzer.py = 996a1b1acf143458` (banked `[R21-77-F5]`,
`rounds/round41/CANDIDATE_r2177f5_996a1b1acf143458.py`), `region_ast_generator.py = 566ff5c502276e48`
(landed, untouched). Production `core/` is NOT to be edited by this ticket; deliverable = patch script +
candidate + FIX doc + MEASURE doc in `D:/Temp/r107/DELIVER/`.

## Defect (measured, see `MEASURE_R21-79_fe_overabsorption_census.md`)

`IfRegion@7186` (`IF_ELIF_CHAIN`, `cond=7186`, `merge=7216`, 48 blocks) mounts **42 blocks** as its
`elif_final_else`, and the span `@7972..@8586` (112 instructions, oracle lines 498–524) is inside that
set. Nothing in the range is unowned, so the drop is absorption-side: blocks that are the code *after the
whole if/elif statement* are claimed as the chain's else body and therefore never emitted at their own
position. `@9144` (the loop-tail statement) is claimed twice over — by `@7186` and by the inner chain
`IfRegion@7634`'s 8-block final-else.

The decisive edge data: real else-arm content `@7492` has predecessors `[7248, 7270]`, both inside the
chain; the first tail block `@7582` has predecessors `[7216, 7492]` where **7216 is the chain's own
declared merge**, and every later block in the set is entered only from the merge or by fall-through from
such a block (`@7634` ← 7582/7630/7632, `@7706` ← 7668 + back edge 7960, `@7972` ← 7706/7814,
`@8294` ← 8256/8282, `@9144` ← nothing outside the set). Arms of the run exit onto the loop back edge
`@9194`; the run's only terminal sink is `@8166` (`RETURN_VALUE`, no successors).

## Required rule (one mechanism)

At chain assembly, a candidate final-else block belongs to the **tail**, not to the else arm, when its
entry edges come only from the chain's declared merge (or transitively from blocks already classified
that way). Express it with region data only — declared `merge`, the chain's own `conditions`/`bodies`,
predecessor/successor edges, and tail opcode class. No function names, no file names, no absolute offsets
as keys, no counters, no thresholds, no magnitude comparisons.

## Excluded premises (already falsified — do not re-implement)

1. **Region-entry exclusion.** "Drop any block that is another region's entry" would gut every legitimate
   `else: if a: …` (the nested `IfRegion` entry lives in the else body by design). Entry-status is a
   symptom (15 of 42 here); edge boundedness is the cause.
2. **Narrower refusal of the elif fold** (`[R21-48]` family): measured inert, or `+2 → −269`.
3. **Post-hoc text reordering in the generator's postprocess**: banned by correct-at-identification.

## Acceptance bar

1. `rounds/round41/oracle_diff_r104.py <product>`: `hunks_vs_ORACLE < 4` **and** `DELTAS instrs` moving
   from `−114` toward `0` (the step-1 drop closing is the observable this ticket exists for).
   Second view: `rounds/round41/hunk_attribution_r107.py <product>` must stop labelling the
   `step1 reconnect/persist tail @7972..@8586` keywords.
2. 20-file panel (`rounds/round38/PANEL_20files.txt`) regenerated: every currently-`Equal` unit stays
   Equal — `trade_live_broker 128/128`, `quote 92/92`, `quotation 153/153`, `order_api 37/37`,
   `plugin_system_risk_calculation/function 43/43`, `replace_utils 9/9`. Any regression falsifies the
   candidate for install regardless of the victim's improvement.
3. Whole-corpus sweep of all 402 products, **ROOT-joined** path list, with
   `files_compared=402`, `MISSING/FAIL=0` printed before any `CHANGED=…` is believed
   (`rounds/round41` lesson: a relative list under `cwd=mirror` reads all-MISS and prints a false zero).
   Bar: `CHANGED = {realtime_event_source.pyc}` only.
4. Judge `13/13` is the flip. A zero-hunk oracle diff is sufficient-not-necessary; `indeg-equal=True` is
   the CFG-visible witness. **Zero flip ⇒ bank, never install** (`[[feedback-fires-without-flips]]`).

## Interaction with R21-78 (r106a, same file, different mechanism)

r106a is editing the short-circuit chain walkers that populate `inline_boolop_chains` (steps 3, 4, 6);
this ticket edits the nested-elif expander (`:21543` docstring, `final_else = []` at `:22173`,
refinements `:22768`/`:22788`/`:22790`, `result['final_else']` at `:22853`, shared-block removal
`:22954-22959`). Disjoint functions, same 2.1 MB file, same pinned base ⇒ **the merge is by re-applying
both delivered patch scripts onto `996a1b1acf143458`** (`D:/Temp/r91m/merge_pair_r107.py` does exactly
that, rewriting each script's mirror path prefix into a private merge tree and asserting BOM/CRLF/no
`\r\r\n`/`compile()` after each), then measuring the merged analyzer alone, each half alone, and the
pair-vs-base matrix before anything is considered for `install_pair.py`. Precedent for the discipline:
unioning two halves that share a footing can fail the merge proof — supersede rather than union
(`[[feedback-pair-interaction-suppression]]`, `[[pythoncdc-fix-agent-dispatch-hazards]]`).
