# Tasks

> Spec: `fix-loop-r06-conditions/spec.md`
> Goal: fix ≥10 of 15 R6 LOOP errors (R6-01..R6-15) per the test engineer's
> `iterate-region-test-fix/rounds/loop/round_06/test_engineer/findings.md`.
> Hard constraints: algorithm 4 principles, no post-processing patches, no
> cross-region heuristics, no hardcoded depth limits, no flattening, no
> heuristic priority overrides. Baseline 308 passing tests inviolable.

## STATUS (round_06 complete)
- **Result: 11/15 R6 errors fixed (target ≥10 met).**
- PASS: R6-01, R6-03, R6-04, R6-05, R6-06, R6-10, R6-11, R6-12, R6-13, R6-14, R6-15
- Known limitations (deferred): R6-02 (compound and/or), R6-07 (ternary in while),
  R6-08/09 (chained cmp in while). Root-cause analysis in `fix_report.md` §8.
- Baseline regression: 0 regressions; +3 baseline tests fixed as bonus
  (`test_l15whiletruebreak_{a,n,x}.py` via R6-13/14/15 while-true init extraction).
- Cross-region regression: 0 regressions (ternary, if_region, control_flow_matrix
  failure sets identical pre/post fix).
- Deliverable: `iterate-region-test-fix/rounds/loop/round_06/repair_engineer/fix_report.md`.

## Phase 0: Baseline & state verification
- [x] Task 0.1: Confirm R6-01 fix is in place
  - Verified the `pre_stmts = []` clearing is removed at the BoolOp branch in
    `region_ast_generator.py` (R6-01 fix retained, see Fix 5 in fix_report.md).
  - `pytest tests/exhaustive/while_loop/test_r6_while_boolop_init_drop.py -x` → PASS.
- [x] Task 0.2: Capture pre-fix R6 baseline
  - Baseline (16 R6 repros deselected): 5 failed / 308 passed (313 total).
  - 5 baseline failures: `test_l15whiletruebreak_{a,n,x}.py`,
    `test_wl30whilebreakintry_{n,x}.py`.

## Phase 1: Cluster A/B — BoolOp condition + pre-loop init (R6-02/03/04/05/06)
Highest-leverage cluster. Fix at the IDENTIFICATION stage in
`region_analyzer.py`.

- [x] Task 1.1: Fix first-term drop in `_detect_while_boolop_forward_chain`
  - Fixed: changed predecessor-stop predicate from `pred in loop.blocks` to
    `pred in set(loop.body_blocks)` so init+condition blocks are not treated as
    body stores. Also relaxed BoolOpRegion replacement rule to supersede
    incomplete generic BoolOpRegions. See Fix 2 in fix_report.md.
  - Target: R6-06 → PASS (`while a<1 and b<1 and c<1:` keeps `a<1`).
- [x] Task 1.2: Fix `not`-wrapped BoolOp verbatim reconstruction (no De Morgan)
  - Fixed: added jump-target-based op_type correction in
    `_detect_while_boolop_forward_chain` (Fix 3) and OR-last-block IF_TRUE
    `not` wrapping in `_build_boolop_expression` with IF-region guards (Fix 4).
  - Targets: R6-04 → PASS, R6-05 → PASS, R6-03 → PASS.
- [~] Task 1.3: Fix compound `and`/`or` (R6-02) — DEFERRED (known limitation)
  - Root cause: nested BoolOp grouping (`(a<5 and b<5) or a==1`) requires
    inferring grouping from short-circuit targets, which the flat-chain
    detector cannot express. Fixing risks regressing the 11 passing homogeneous
    BoolOp cases. Documented in fix_report.md §8 (R6-02).
- [x] Task 1.4: Re-run cluster A/B regression
  - `pytest tests/exhaustive/while_loop/ -k r6` → R6-01/03/04/05/06 PASS,
    R6-02 SKIP. No new failures.
  - Full `tests/exhaustive/while_loop/ tests/exhaustive/for_loop/` → 0 baseline
    regression.

## Phase 2: Cluster F — while-true init drop (R6-13/14/15)
- [x] Task 2.1: Emit while-True init via entry-block extraction
  - Implemented: in `region_ast_generator.py` entry-region dispatch, when
    `entry_region.is_while_true` and entry_block contains STORE instructions,
    extract its statements as pre-statements. See Fix 6 in fix_report.md.
  - Targets: R6-13 → PASS, R6-14 → PASS, R6-15 → PASS.
  - Bonus: also fixed 3 baseline `test_l15whiletruebreak_{a,n,x}.py` failures.
- [x] Task 2.2: Re-run cluster F regression
  - R6-13/14/15 PASS. Full suite: 0 baseline regression (3 baseline tests newly
    pass).

## Phase 3: Cluster E — post-loop statement dropped with break (R6-10)
- [x] Task 3.1: Fix break target / natural_exit absorption of trailing stmts
  - Fixed: changed W3 trivial-exit absorption from
    `_check_block_has_trailing_return_none` to `_is_trivial_return_block` so
    blocks with real user statements (e.g. `print('end')`) stay standalone.
    See Fix 1 in fix_report.md.
  - Target: R6-10 → PASS.
- [x] Task 3.2: Re-run cluster E regression
  - R6-10 PASS. Full suite: 0 baseline regression.

## Phase 4: Cluster G — chained comparison in while condition (R6-08/09)
- [~] Task 4.1: Reconstruct chained-compare while-test as single Compare — DEFERRED (known limitation)
  - Root cause: LoopRegion misclassifies chained-compare intermediate blocks as
    break targets. Requires a new chained-compare-while identification path
    (Principle 1) so the while-test references the Compare as a single abstract
    node. Documented in fix_report.md §8 (R6-08/09).
  - Targets: R6-08 SKIP, R6-09 SKIP (recompile SyntaxError masked as SKIP).
- [~] Task 4.2: Re-run cluster G regression — N/A (no fix applied)

## Phase 5: Cluster D — nested for-else + outer break (R6-11/12)
- [x] Task 5.1: Preserve inner for-else + outer break (no spurious continue)
  - Fixed three issues: (1) `_cleanup_try_else_in_loop_body` now preserves
    else_blocks containing `continue` to parent loop headers (Fix 7);
    (2) outer-break detection handles terminal break targets with no successors
    (Fix 8); (3) `_loop_process_natural_back_edge` skips pure JUMP_BACKWARD
    blocks to prevent spurious `continue` (Fix 9). See fix_report.md.
  - Targets: R6-11 → PASS, R6-12 → PASS.
- [x] Task 5.2: Re-run cluster D regression
  - R6-11/12 PASS. Full suite: 0 baseline regression.

## Phase 6: Cluster C — ternary in while condition (R6-07)
- [~] Task 6.1: Reconstruct ternary while-test as single IfExp — DEFERRED (known limitation)
  - Root cause: requires a new `_detect_while_ternary_condition` detector
    analogous to the BoolOp chain detector, plus an IfExp reconstruction branch
    in `_loop_generate_while`. Documented in fix_report.md §8 (R6-07).
  - Target: R6-07 FAIL (17 vs 22 instrs).
- [~] Task 6.2: Re-run cluster C regression — N/A (no fix applied)

## Phase 7: Cross-region regression & known-limitation triage
- [x] Task 7.1: Full cross-region regression
  - `tests/exhaustive/{ternary,if_region}/ tests/control_flow_matrix/` →
    75 failed / 1607 passed / 67 skipped / 43 xfailed / 8 xpassed.
  - Failure sets verified identical pre/post fix via `diff` of sorted FAILED
    lists → **0 cross-region regressions**.
  - while_loop + for_loop baseline: 5 failed → 2 failed (3 l15 baseline tests
    newly pass); 0 regressions.
- [x] Task 7.2: Triage unfixable R6 errors as known limitations
  - R6-02, R6-07, R6-08, R6-09 documented with root-cause analysis in
    `fix_report.md` §8. No forbidden heuristics applied.

## Phase 8: Deliverable
- [x] Task 8.1: Write `fix_report.md`
  - Path: `iterate-region-test-fix/rounds/loop/round_06/repair_engineer/fix_report.md`
    (created `repair_engineer/` directory).
  - Contents: 9 fixes (file:line, before/after, R6 IDs), Algorithm 4 principles
    compliance table, forbidden heuristics audit, docstring update note,
    regression results (R6 + baseline + cross-region), residual errors /
    known limitations (root-cause analysis for R6-02/07/08/09).
- [ ] Task 8.2: Sync parent `tasks.md`
  - Update `iterate-region-test-fix/tasks.md` Task 2.6 with the round_06
    summary line (X/15 fixed + Y known limitations, baseline regression
    status).

# Task Dependencies
- Task 0.1 → all subsequent (R6-01 must remain fixed).
- Task 0.2 → all subsequent (baseline must be captured before any change).
- Task 1.1 → Task 1.2/1.3 (chain detection comes first, then `not` wrapping,
  then compound precedence).
- Task 1.4 → Task 2.x / 3.x / 4.x / 5.x / 6.x (cluster A/B regression must
  be clean before moving on, to isolate regressions).
- Phase 7 (Task 7.1) depends on all of Phase 1-6.
- Task 8.1 depends on Phase 7.
- Task 8.2 depends on Task 8.1.

# Parallelizable Work
- Phase 2 (cluster F), Phase 3 (cluster E), Phase 4 (cluster G), Phase 5
  (cluster D), Phase 6 (cluster C) are largely independent once Phase 1
  (cluster A/B) regression is clean. They MAY be attempted in parallel
  after Task 1.4 passes, provided each is validated against the same
  baseline snapshot.
- Phase 7 (Task 7.1) is a single consolidated regression run — not
  parallelizable.
