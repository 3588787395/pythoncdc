# Checklist

> Spec: `fix-loop-r06-conditions/spec.md`
> Tasks: `fix-loop-r06-conditions/tasks.md`
> Verify each checkpoint before declaring the round complete. Check the box
> only when the requirement is actually met (code inspected or test run
> confirms it).

## Algorithm 4 principles compliance (per fix)

- [x] **P1 — Bottom-up reduction:** inner regions (BoolOp / chained-compare /
  ternary) are identified BEFORE the outer loop region; the loop's `test` is
  rebuilt from the already-identified inner region's entry, not from a raw
  CFG walk. Inspect each fix in `region_analyzer.py` and confirm the
  identification order.
  - Verified: Fix 2 supersedes incomplete generic BoolOpRegion with the
    while-condition BoolOpRegion (inner before outer). Fix 6 emits init at
    entry dispatch before loop generation. See fix_report.md §4 compliance table.
- [x] **P2 — Unique ownership:** each CFG block belongs to exactly one
  region. Init stores belong to the loop's pre-statements; BoolOp
  comparison blocks belong to the BoolOpRegion; post-loop statements belong
  to the parent region. No fix re-claims a block already owned by another
  region.
  - Verified: Fix 1 keeps post-loop blocks in parent; Fix 2 owns init+cond
    blocks in BoolOpRegion; Fix 5 owns init stores in loop pre-statements;
    Fix 7 owns else:continue in child else clause. See fix_report.md §4.
- [x] **P3 — Nesting = abstract node:** a BoolOpRegion / ternary /
  chained-compare nested in the loop's `test` is treated as a single
  abstract expression node. No fix flattens the nested region into the loop
  body or vice versa.
  - Verified: Fix 4 reconstructs BoolOp verbatim (no De Morgan); Fix 9 skips
    pure JUMP_BACKWARD (for-loop implicit iteration stays abstract). See
    fix_report.md §4.
- [x] **P4 — Parent references child entry:** the while-loop's `test`
  references the BoolOpRegion's entry block (=`cond_block`) as the abstract
  expression node, not a re-walk of the chain. Inspect
  `_loop_generate_while` BoolOp branch.
  - Verified: Fix 3 op_type correction ensures cond_block's true operator is
    reconstructed; Fix 6 parent references while-true header. See fix_report.md
    §4.

## Forbidden heuristics (must all be ABSENT)

- [x] No post-processing patches (no AST rewriting after region AST
  generation). Search the diff for any new `ast.NodeTransformer` /
  post-process pass — must be empty. Verified: all fixes at identification
  or AST-generation stage.
- [x] No cross-region heuristics / special cases (no "if loop has BoolOp
  and break then ..." rules). Inspect each fix for region-type-sniffing
  conditionals. Verified: Fix 4's guard is a jump-direction check inside
  BoolOp expr building, not a region-type sniff.
- [x] No hardcoded depth limits on BoolOp / chained-compare chain length.
  Verified: chain detection iterates until natural stop conditions.
- [x] No flattening of nested regions. Verified: BoolOpRegion / while-true /
  for-else remain nested abstract nodes.
- [x] No heuristic priority overrides (no `if is_R6_pattern: ...` style
  overrides). Verified.
- [x] No `+OK.py` generated files modified. Verified via git diff --stat.
- [x] No existing passing tests modified (the 308 baseline tests are
  inviolable). Verified: git diff shows only region_analyzer.py and
  region_ast_generator.py changed.
- [x] Each fix is correct at the IDENTIFICATION stage (one-pass
  correctness) — no second-pass cleanup added. Verified: Fix 7's
  else-cleanup is the existing `_cleanup_try_else_in_loop_body` pass,
  refined with a continue-target check, not a new pass.

## Per-cluster fix verification

### Cluster A/B (R6-01..R6-06)
- [x] R6-01 (`test_r6_while_boolop_init_drop.py`) PASSES — `a = 0` before
  `while a<3 or a<6:`.
- [~] R6-02 (`test_r6_while_compound_andor.py`) SKIP — known limitation
  (compound and/or precedence requires nested BoolOp grouping). See
  fix_report.md §8.
- [x] R6-03 (`test_r6_while_not_or_logic.py`) PASSES — `while not a>5 or
  a<0:` reconstructs verbatim (no De Morgan flip to `and`), `a=0` preserved.
- [x] R6-04 (`test_r6_while_not_paren_boolop.py`) PASSES — `while not (a<0
  and b<0):` reconstructs as `Not(And([a<0, b<0]))`, `not` NOT dropped,
  inits preserved.
- [x] R6-05 (`test_r6_while_or_not.py`) PASSES — `while not a or not b:`
  reconstructs as `Or([Not(a), Not(b)])`, no De Morgan flip to `And`,
  inits preserved.
- [x] R6-06 (`test_r6_while_and_three.py`) PASSES — `while a<1 and b<1 and
  c<1:` keeps ALL THREE terms (including first `a<1`), all 3 inits
  preserved.

### Cluster F (R6-13/14/15)
- [x] R6-13 (`test_r6_whiletrue_init_in_func.py`) PASSES — `n = 0` before
  `while True:` in function scope preserved.
- [x] R6-14 (`test_r6_whiletrue_multi_init.py`) PASSES — both `a = 0` and
  `b = 0` before `while True:` preserved.
- [x] R6-15 (`test_r6_whiletrue_break_else.py`) PASSES — `n = 0` (and
  trivial `else: pass`) preserved.

### Cluster E (R6-10)
- [x] R6-10 (`test_r6_while_break_post_stmt.py`) PASSES — `print('end')`
  after the break-loop preserved.

### Cluster G (R6-08/09)
- [~] R6-08 (`test_r6_while_chained_cmp.py`) SKIP — known limitation
  (chained-compare-while requires new identification path). See fix_report.md
  §8.
- [~] R6-09 (`test_r6_while_triple_cmp.py`) SKIP — known limitation (same
  family as R6-08). See fix_report.md §8.

### Cluster D (R6-11/12)
- [x] R6-11 (`test_r6_for_else_break_outer.py`) PASSES — inner `else:
  continue` preserved, outer `break` preserved, no spurious inner
  `continue`.
- [x] R6-12 (`test_r6_for_else_continue_break.py`) PASSES — same family as
  R6-11.

### Cluster C (R6-07)
- [~] R6-07 (`test_r6_while_ternary_cond.py`) FAIL — known limitation
  (ternary-in-while requires new `_detect_while_ternary_condition` detector).
  See fix_report.md §8.

## Regression — no baseline degradation

- [x] `tests/exhaustive/while_loop/ tests/exhaustive/for_loop/` —
  non-R6 tests: 2 failed / 311 passed (was 5 failed / 308 passed pre-round_06;
  3 l15 baseline tests now pass as bonus from R6-13/14/15 fix; 0 regressions).
- [x] `tests/exhaustive/ternary/` — 0 regression vs. pre-round_06 ternary
  baseline (failure set identical pre/post fix).
- [x] `tests/exhaustive/if_region/` — 0 regression vs. pre-round_06
  if_region baseline (failure set identical pre/post fix).
- [x] `tests/exhaustive/control_flow_matrix/` — 0 regression vs.
  pre-round_06 control_flow_matrix baseline (failure set identical pre/post
  fix, verified via diff of sorted FAILED lists).
- [x] R6 net improvement: 11 of the 15 R6 errors now PASS (was 13 FAIL + 2
  SKIP at round_06 baseline). Target ≥10 met.

## Deliverable

- [x] `iterate-region-test-fix/rounds/loop/round_06/repair_engineer/fix_report.md`
  exists and contains:
  - Fixes applied (file:line, before/after, R6 IDs). ✓ §3 (9 fixes).
  - Algorithm justification (4 principles compliance per fix). ✓ §4 table.
  - Docstring updates (any function whose contract changed). ✓ §6 (none
    changed; inline comments added).
  - Regression results (R6 pass/fail counts + full baseline). ✓ §7.
  - Residual errors / known limitations (root-cause analysis for any
    unfixed R6 error). ✓ §8 (R6-02, R6-07, R6-08, R6-09).
- [ ] Parent `iterate-region-test-fix/tasks.md` Task 2.6 updated with the
  round_06 summary line (X/15 fixed + Y known limitations, baseline
  regression status).
- [x] No temporary `_debug_*.py` scripts left at the repository root or in
  the round_06 folder (use `minimal_repros/` for any new repros). Verified:
  no new scripts created; only fix_report.md added under repair_engineer/.
