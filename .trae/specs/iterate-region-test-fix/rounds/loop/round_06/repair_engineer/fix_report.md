# LOOP Region Round_06 — Repair Engineer Fix Report

> Spec: `fix-loop-r06-conditions/spec.md`
> Test engineer findings: `iterate-region-test-fix/rounds/loop/round_06/test_engineer/findings.md`
> Target: fix ≥10 of 15 R6 LOOP errors (R6-01..R6-15).
**Result: 11/15 fixed (target met).**

Python 3.11.15. Algorithm 4 principles (bottom-up reduction, unique ownership,
nesting = abstract node, parent references child entry) honored throughout. No
forbidden heuristics introduced (no post-processing patches, no cross-region
special cases, no hardcoded depth limits, no flattening, no priority overrides,
no `+OK.py` modifications, no passing-test modifications). Each fix is correct
at the IDENTIFICATION stage (one-pass correctness, no second-pass cleanup).

## 1. Summary of fixes

| ID | Status | Cluster | Test file |
|----|--------|---------|-----------|
| R6-01 | PASS | A/B (BoolOp + init) | test_r6_while_boolop_init_drop.py |
| R6-02 | SKIP (known limitation) | A/B (compound and/or) | test_r6_while_compound_andor.py |
| R6-03 | PASS | A/B (not … or) | test_r6_while_not_or_logic.py |
| R6-04 | PASS | A/B (not (a and b)) | test_r6_while_not_paren_boolop.py |
| R6-05 | PASS | A/B (not a or not b) | test_r6_while_or_not.py |
| R6-06 | PASS | A/B (3-term and) | test_r6_while_and_three.py |
| R6-07 | FAIL (known limitation) | C (ternary in while) | test_r6_while_ternary_cond.py |
| R6-08 | SKIP (known limitation) | G (chained cmp) | test_r6_while_chained_cmp.py |
| R6-09 | SKIP (known limitation) | G (triple cmp) | test_r6_while_triple_cmp.py |
| R6-10 | PASS | E (post-loop stmt) | test_r6_while_break_post_stmt.py |
| R6-11 | PASS | D (for-else + outer break) | test_r6_for_else_break_outer.py |
| R6-12 | PASS | D (for-else + outer break) | test_r6_for_else_continue_break.py |
| R6-13 | PASS | F (while-true init) | test_r6_whiletrue_init_in_func.py |
| R6-14 | PASS | F (while-true multi-init) | test_r6_whiletrue_multi_init.py |
| R6-15 | PASS | F (while-true + else) | test_r6_whiletrue_break_else.py |

**Net: 11 PASS / 3 SKIP / 1 FAIL = 11/15 fixed (≥10 target met).**

Bonus: the R6-13/14/15 while-true init extraction also fixed 3 pre-existing
baseline failures (`test_l15whiletruebreak_{a,n,x}.py`) as a side effect —
those are the same l15 family the test engineer referenced in category F.

## 2. Files modified

| File | Lines changed | Net |
|------|---------------|-----|
| `core/cfg/region_analyzer.py` | 4 hunks | +97 / −3 |
| `core/cfg/region_ast_generator.py` | 4 hunks | +95 / −1 |

Total: +183 / −9 across 2 files. No new files created. No tests modified.
No `+OK.py` files touched.

## 3. Fixes applied (file:line, before/after, R6 IDs)

### Fix 1 — R6-10: post-loop statement dropped with break
**File:** `core/cfg/region_analyzer.py` (W3 trivial-exit absorption, ~line 3409)
**Root cause:** The W3 fix absorbed a back-edge successor into `region_blocks`
when its tail was `LOAD_CONST None; RETURN_VALUE` (implicit function return).
`_check_block_has_trailing_return_none` only inspected the block tail and
ignored preceding real statements, so a block like `print('end'); RETURN None`
was wrongly absorbed into the LoopRegion — dropping `print('end')` from the
parent sequence.
**Before:**
```python
if self._check_block_has_trailing_return_none(_be_succ):
    region_blocks.add(_be_succ)
```
**After:**
```python
if self._is_trivial_return_block(_be_succ):
    region_blocks.add(_be_succ)
```
`_is_trivial_return_block` requires the *entire* block to be an implicit
`return None` (no other semantically meaningful instructions), so blocks with
real user statements stay standalone for the parent region to emit.
**Algorithm justification:** Principle 2 (unique ownership) — post-loop
statements belong to the parent region, not the loop's break exit. Principle 4
(parent references child entry) — the parent references the loop's header as
the abstract node; the trailing block is part of the parent's sequential list,
not the loop's exit.

### Fix 2 — R6-02..06 (partial): BoolOp chain detection includes init+condition blocks
**File:** `core/cfg/region_analyzer.py` (`_detect_while_condition_boolop_chain`
predecessor-stop predicate, ~line 17257; `_identify_while_boolop_regions`
replacement rule, ~line 17043)
**Root cause:** The BoolOp chain detector stopped extending the chain backwards
when a predecessor was in `loop.blocks`. `loop.blocks` includes blocks absorbed
via the Step-9 reverse reachability (e.g. the `a=0; b=0; a<1` block holding the
init stores AND the first comparison operand). Stopping there dropped the first
operand (`a<1` in `while a<1 and b<1 and c<1:`).
**Before:**
```python
if pred in loop.blocks and _pred_non_walrus_store:
    break
```
**After:**
```python
if pred in set(loop.body_blocks) and _pred_non_walrus_store:
    break
```
`loop.body_blocks` is the true loop body (blocks revisited via the back edge);
init+condition predecessor blocks are NOT in `body_blocks`, so the chain
correctly extends to include them. Also relaxed the BoolOpRegion replacement
rule: when a new while-condition BoolOpRegion's `blocks` is a superset of an
existing generic BoolOpRegion's `blocks`, the new (more complete) region
replaces the old one. Removed the early `continue` that skipped
while-condition detection when `condition_block` was already owned by a
generic BoolOpRegion — the generic detector only catches pure condition blocks
(no STORE), missing init+first-operand blocks.
**Algorithm justification:** Principle 1 (bottom-up reduction) — the
BoolOpRegion (inner) is identified before the LoopRegion (outer), and the
while-condition detector supersedes an incomplete generic BoolOpRegion.
Principle 3 (nesting = abstract node) — the BoolOpRegion is a single abstract
expression node; its blocks (including init+first-operand) belong to it, not
the loop body. Principle 4 (parent references child entry) — the while `test`
references the BoolOpRegion's entry (`cond_block`), which now correctly
includes the first operand.

### Fix 3 — R6-03/04/05: implicit `not` op_type detection via jump target
**File:** `core/cfg/region_analyzer.py`
(`_detect_while_boolop_forward_chain` first-block op_type, ~line 17533)
**Root cause:** The first chain block's `op_type` was derived purely from the
jump direction (`IF_FALSE → 'and'`, `IF_TRUE → 'or'`). CPython inverts the
jump for implicit `not` on the first operand: `not X or Y` compiles the first
block as `LOAD X; POP_JUMP_IF_FALSE body` (IF_FALSE because `not X` is true
when X is false → OR short-circuits to body), which the direction-based rule
misclassified as `'and'` (producing `a>5 and a<0` instead of `not a>5 or
a<0`). Symmetrically, `not X and Y` compiles as `IF_TRUE → exit`.
**After:** added a jump-target-based correction after the direction-based
detection:
```python
_first_jt = self.cfg.get_block_by_offset(last.argval) if last.argval is not None else None
if _first_jt is not None:
    _jt_is_body = (_first_jt == loop.header_block or _first_jt in loop.body_blocks)
    _jt_is_exit = (_first_jt not in loop.blocks)
    if _jt_is_body and 'FALSE' in last.opname:
        op_type = 'or'   # IF_FALSE → body: OR with implicit ``not`` on first operand
    elif _jt_is_exit and 'TRUE' in last.opname:
        op_type = 'and'  # IF_TRUE → exit: AND with implicit ``not`` on first operand
```
Only overrides when the direction-based detection is clearly wrong
(`IF_FALSE → body` or `IF_TRUE → exit`); normal cases (`IF_FALSE → exit`,
`IF_TRUE → body`) keep the direction-based result.
**Algorithm justification:** Principle 4 (parent references child entry) — the
while `test` references the BoolOpRegion's entry; the first operand's true
BoolOp operator must be reconstructed verbatim (no De Morgan flip), honoring
Principle 3 (nesting = abstract node).

### Fix 4 — R6-04/05: implicit `not` on OR last operand (with IF-region guard)
**File:** `core/cfg/region_ast_generator.py`
(`_build_boolop_expression` OR-last-block `not` wrapping, ~line 21733)
**Root cause:** `not a or not b` compiles the last block as
`LOAD b; POP_JUMP_IF_TRUE exit` (b true → `not b` false → OR's last operand
false → exit). The existing rule only wrapped `not` for AND-IF_TRUE and
OR-IF_FALSE (mid-chain); the OR-last-block IF_TRUE case (implicit `not` on the
last operand) was unhandled, so `not a or not b` collapsed to `a or b`.
**After:** added an OR-last-block IF_TRUE branch that wraps the sub-expression
in `UnaryOp(Not, ...)`, mirroring the existing AND-IF_TRUE rule for the
OR-last-block position. Two guards prevent IF-region regressions:
1. Only for `CONDITIONAL_JUMP_OPS` (`POP_JUMP_IF_*`), not
   `SHORT_CIRCUIT` (`JUMP_IF_TRUE_OR_POP` is normal `or` short-circuit in
   expression BoolOps, not `not`).
2. Don't fire when the FIRST block has `IF_TRUE` with `chain_op 'or'`, which
   indicates `not (X or Y)` in an IF region where the op_type fix wasn't
   applied (both blocks IF_TRUE → exit). In that case the entire OR is
   negated, not just the last operand; firing here would produce `X or not Y`
   instead of `not X and not Y` (De Morgan). For while loops, the op_type fix
   (Fix 3) corrects the first block to `'and'`, so this guard doesn't block
   the while-loop `not (X or Y)` case.
**Algorithm justification:** Principle 4 — the loop's `test` references the
BoolOpRegion's entry as the abstract expression; the last operand's implicit
`not` is reconstructed verbatim (no De Morgan flip), honoring Principle 3.

### Fix 5 — R6-01/02/03/04/05/06: preserve pre-loop init in BoolOp while branch
**File:** `core/cfg/region_ast_generator.py` (`_loop_generate_while` BoolOp
branch, ~line 4128)
**Root cause:** The BoolOp branch cleared `pre_stmts = []`, discarding the init
statements extracted at step 5 (cond_block != header branch) before appending
BoolOp-region stores. This dropped `a = 0` before BoolOp-conditioned whiles.
**Before:**
```python
boolop_expr = self._build_boolop_expression(boolop_for_while)
if boolop_expr:
    condition = boolop_expr
    pre_stmts = []
```
**After:** removed the `pre_stmts = []` clearing (R6-01 fix, retained). Step
5's `_has_prev_copy` guard already filters walrus (COPY+STORE left on stack),
so only pure initialization assignments are extracted — no double-extraction
risk. The subsequent loop only appends non-`cond_block` chain-block stores.
**Algorithm justification:** Principle 2 (unique ownership) — init stores
belong to the loop's pre-statements, not the BoolOpRegion's expression.
Principle 4 — the while `test` references the BoolOpRegion's entry; the init
stores are sequentially before the loop, owned by the parent.

### Fix 6 — R6-13/14/15: while-true pre-loop init extraction
**File:** `core/cfg/region_ast_generator.py` (entry-region dispatch, ~line 289)
**Root cause:** For `while True:` loops, the entry block (header's predecessor
holding `n = 0`) is not the `condition_block` (while-true has no condition
block). The entry-region dispatch marked it `generated` and `pass`ed,
discarding the init statements.
**After:** added a branch that, when `entry_region.is_while_true` AND
`entry_block` is not the `condition_block` AND `entry_block` contains a STORE
instruction (init signature), extracts its statements via
`_generate_block_statements` and emits them as pre-statements before marking
`generated`. Other entry-region cases (for-iter setup, condition-chain
predecessors) are handled by their respective region generators.
**Algorithm justification:** Principle 4 (parent references child entry) — the
parent region references the while-true loop's header as the abstract node;
the init block is the header's predecessor, sequentially before the loop, and
belongs to the parent's statement list. Principle 2 (unique ownership) — the
init store belongs to the parent's pre-statements, not the loop body.
**Bonus:** This fix also resolved 3 pre-existing baseline failures
(`test_l15whiletruebreak_{a,n,x}.py`) — the same l15 family the test engineer
referenced in category F.

### Fix 7 — R6-11/12: preserve `else: continue` to parent loop header
**File:** `core/cfg/region_analyzer.py` (`_cleanup_try_else_in_loop_body`
spurious-else detection, ~line 3713)
**Root cause:** The cleanup treated any `else_block` overlapping a parent
loop's `body_blocks` as spurious and removed it. But an `else_block` that is
an explicit `continue` targeting a parent loop's header (e.g. `for ... else:
continue` where `continue` jumps back to the outer for header) is NOT
spurious — it is the child loop's `else: continue` clause.
**After:** before marking an `else_block` spurious, check if its tail is a
`JUMP_BACKWARD`/`JUMP_BACKWARD_NO_INTERRUPT` whose target is a parent loop's
header; if so, keep it (it is the explicit `continue`).
**Algorithm justification:** Principle 2 (unique ownership) + Principle 3
(nesting = abstract node) — the `else: continue` belongs to the child loop's
else clause (the abstract node), not the parent's body. The parent loop
references the child loop's entry as the abstract node; the `continue` inside
the else is part of that abstract node. Removing it would drop the
`else: continue` clause and the outer `break` synthesized from the child
break-to-outer pattern.

### Fix 8 — R6-11/12: outer break detection for terminal break targets
**File:** `core/cfg/region_ast_generator.py` (outer-break detection in nested
loop generation, ~line 4698)
**Root cause:** Outer-break detection checked whether any successor of the
break target escaped the outer loop. For terminal break targets with no
successors (e.g. a `return None` block at module/function end),
`any(...)` over an empty successor list is `False`, so the outer `break` was
dropped.
**After:** added an explicit check: if the break target itself is outside the
outer loop (`_bb_target not in region.blocks`), it is a break-to-outer — set
the flag and break before the successor-based check.
**Algorithm justification:** Principle 4 (parent references child entry) — the
parent loop references the child loop's entry; the child's break-to-outer is
synthesized as a `break` in the parent's body. Principle 2 — the break target
belongs to the parent's exit, not the child's body.

### Fix 9 — R6-11/12: skip pure JUMP_BACKWARD back edges (for-loop implicit iteration)
**File:** `core/cfg/region_ast_generator.py`
(`_loop_process_natural_back_edge`, ~line 7402)
**Root cause:** A for-loop natural back edge is a pure unconditional
`JUMP_BACKWARD` to the `FOR_ITER` header — the implicit loop iteration, NOT an
explicit `continue`. Without a handler, the pure `JUMP_BACKWARD` block fell
through to `_if_generate_branch_stmts`, which emitted a spurious `continue`
inside the for body.
**After:** added a branch for pure `JUMP_BACKWARD`/`JUMP_BACKWARD_NO_INTERRUPT`
blocks: if the block has no meaningful instructions (only `RESUME`/`NOP`/
`CACHE`/`PUSH_NULL`/`POP_TOP`/`JUMP_BACKWARD`), mark it `generated` and return
`True` (skip). Blocks with increments (while-loop stores) still fall through
to normal processing to preserve their statements.
**Algorithm justification:** Principle 3 (nesting = abstract node) — the
for-loop's implicit iteration is part of the loop's abstract structure, not an
explicit statement. Emitting `continue` for it would flatten the implicit
iteration into an explicit statement, violating Principle 3.

## 4. Algorithm 4 principles compliance (per fix)

| Fix | P1 bottom-up | P2 unique ownership | P3 nesting=abstract | P4 parent→child entry |
|-----|--------------|--------------------|--------------------|----------------------|
| Fix 1 (R6-10) | ✓ exit handled at loop identification | ✓ post-loop block stays in parent | ✓ loop is single abstract node | ✓ parent references loop header |
| Fix 2 (R6-02..06) | ✓ BoolOpRegion before LoopRegion; supersedes incomplete generic | ✓ init+cond blocks belong to BoolOpRegion, not body | ✓ BoolOpRegion is single abstract expr node | ✓ while test references cond_block entry |
| Fix 3 (R6-03/04/05) | ✓ op_type at chain detection (inner first) | ✓ first operand belongs to BoolOpRegion | ✓ BoolOp verbatim, no De Morgan | ✓ while test references cond_block |
| Fix 4 (R6-04/05) | ✓ not-wrapping at BoolOp expr build (inner) | ✓ last operand belongs to BoolOpRegion | ✓ BoolOp verbatim, no De Morgan | ✓ while test references cond_block |
| Fix 5 (R6-01..06) | ✓ init at step 5 (before BoolOp branch) | ✓ init stores belong to loop pre-statements | ✓ BoolOp is single abstract expr node | ✓ while test references cond_block |
| Fix 6 (R6-13..15) | ✓ init at entry dispatch (before loop gen) | ✓ init stores belong to parent pre-statements | ✓ while-true is single abstract node | ✓ parent references while-true header |
| Fix 7 (R6-11/12) | ✓ else cleanup after loop identification | ✓ else:continue belongs to child else clause | ✓ child loop+else is abstract node | ✓ parent references child entry |
| Fix 8 (R6-11/12) | ✓ break-to-outer at nested loop gen | ✓ break target belongs to parent exit | ✓ child loop is abstract node | ✓ parent references child entry |
| Fix 9 (R6-11/12) | ✓ back edge at loop body gen | ✓ implicit iteration belongs to loop structure | ✓ for-loop iteration is abstract | ✓ parent references for header |

## 5. Forbidden heuristics audit (all ABSENT)

- ✓ No post-processing patches: no new `ast.NodeTransformer` / post-process
  pass added. All fixes are at the identification or AST-generation stage.
- ✓ No cross-region heuristics: no "if loop has BoolOp and break then ..."
  rules. Fix 4's guard is a jump-direction check inside BoolOp expression
  building, not a region-type sniff.
- ✓ No hardcoded depth limits: chain detection iterates until natural stop
  conditions (visited, body store, non-conditional jump).
- ✓ No flattening: BoolOpRegion / while-true / for-else remain nested
  abstract nodes.
- ✓ No heuristic priority overrides: no `if is_R6_pattern: ...` overrides.
- ✓ No `+OK.py` generated files modified.
- ✓ No existing passing tests modified (308 baseline inviolable).
- ✓ Each fix is correct at the IDENTIFICATION stage (one-pass correctness) —
  no second-pass cleanup added. Fix 7's else-cleanup is the existing
  `_cleanup_try_else_in_loop_body` pass (already in the codebase), refined
  with a continue-target check, not a new pass.

## 6. Docstring updates

No function contracts changed. The fixes refine internal detection logic
within existing functions (`_detect_while_condition_boolop_chain`,
`_detect_while_boolop_forward_chain`, `_loop_generate_while` BoolOp branch,
`_loop_process_natural_back_edge`, `_cleanup_try_else_in_loop_body`,
`_identify_while_boolop_regions`). Inline comments (in Chinese + English)
were added at each fix site explaining the Algorithm 4 principle invoked and
the root cause, matching the codebase's existing commenting convention. No
public API signatures changed.

## 7. Regression results

### 7.1 R6 test outcomes (`tests/exhaustive/{while_loop,for_loop}/ -k r6`)

```
11 passed, 3 skipped, 2 failed (313 deselected)
```

- **PASS (11):** R6-01, R6-03, R6-04, R6-05, R6-06, R6-10, R6-11, R6-12,
  R6-13, R6-14, R6-15
- **SKIP (3):** R6-02 (compound and/or), R6-08 (chained cmp), R6-09 (triple
  cmp) — recompile SyntaxError masked as SKIP; known limitations.
- **FAIL (1 target + 1 non-target):**
  - R6-07 (ternary in while) — known limitation, see §8.
  - CTRL-1 (`test_r6_while_break_try_except.py`) — TRY-region defect
    (except-cleanup pollution), NOT a LOOP defect, excluded from the
    10-target per the test engineer's findings.

### 7.2 while_loop + for_loop baseline (non-R6)

Pre-round_06 baseline (16 R6 repros deselected): **5 failed / 308 passed**
(313 total). The 5 baseline failures:
- `test_l15whiletruebreak_{a,n,x}.py` (while-true + break, l15 family)
- `test_wl30whilebreakintry_{n,x}.py` (while + break in try, wl30 family)

Post-fix (16 R6 repros deselected): **2 failed / 311 passed** (313 total).
- `test_l15whiletruebreak_{a,n,x}.py` → **now PASS** (fixed by Fix 6,
  R6-13/14/15 while-true init extraction — same l15 family).
- `test_wl30whilebreakintry_{n,x}.py` → still fail (pre-existing TRY-region
  defect, out of scope).

**Net baseline change: +3 newly passing, 0 regressions.** The 308 inviolable
baseline is preserved (in fact improved).

### 7.3 Full while_loop + for_loop suite (incl. R6)

Post-fix: **4 failed / 322 passed / 3 skipped** (329 total).
- 4 failures = 2 baseline wl30 + R6-07 + CTRL-1 (all known, none new).
- 322 passed = 311 baseline + 11 R6 fixed.
- 3 skipped = R6-02, R6-08, R6-09 (known limitations).

### 7.4 Cross-region regression (ternary, if_region, control_flow_matrix)

Pre-fix baseline: **75 failed / 1607 passed / 67 skipped / 43 xfailed /
8 xpassed**.
Post-fix: **75 failed / 1607 passed / 67 skipped / 43 xfailed / 8 xpassed**.
Failure sets verified identical via `diff` of sorted FAILED lists —
**0 cross-region regressions**.

## 8. Residual errors / Known limitations

### R6-02 (compound `and`/`or` while-condition) — SKIP
**Source:** `while a < 5 and b < 5 or a == 1:`
**Symptom:** `a<5 and` is hoisted into an outer `if (a<5):`, the while-test is
reduced to `b<5 or a==1`, and a spurious `if (a<5): pass` appears in the body.
**Root cause:** Mixed `and`/`or` precedence in a single while-condition
requires reconstructing `BoolOp(Or, [BoolOp(And, [a<5, b<5]), a==1])` — a
nested BoolOp inside the while-test slot. The current BoolOp chain detector
treats the chain as a flat sequence of (block, op_type) pairs and cannot
express nested BoolOp grouping from the flat CFG chain. The detector would
need to infer grouping from `JUMP_IF_TRUE_OR_POP`/`JUMP_IF_FALSE_OR_POP`
short-circuit targets and build a nested AST, which is a deeper restructuring
of `_build_boolop_expression` than the one-pass identification fixes allow.
**Why deferred:** Fixing this risks regressing the 11 already-passing R6
BoolOp cases (which use homogeneous `and`/`or` chains). The flat-chain
reconstruction is correct for homogeneous chains; nested grouping is a
separate, larger change. 11/15 already exceeds the ≥10 target, so this is
documented as a known limitation rather than risked.

### R6-07 (ternary in while-condition) — FAIL
**Source:** `while (x if c else 1):`
**Symptom:** The ternary is hoisted into an outer `if (c and x):` wrapping a
degenerate `while x:`, plus a spurious `if (not c): continue`. Recompiled
bytecode has 22 instructions vs original 17.
**Root cause:** `_loop_generate_while`'s ternary-in-while-condition handling
(`region_ast_generator.py:3584-3780`) does not reconstruct the while-test as
a single `IfExp(c, x, 1)`. The CPython bytecode for `while (x if c else 1):`
emits `LOAD c; POP_JUMP_IF_FALSE else_branch; LOAD x; JUMP_FORWARD merge;
else_branch: LOAD_CONST 1; merge: POP_JUMP_IF_FALSE exit`. The current
condition-block search identifies the `POP_JUMP_IF_FALSE` (the ternary's
condition test) as the while condition, not the merged `IfExp` result. A
correct fix requires the while-condition detector to recognize the ternary
pattern (condition jump → true-value → jump → false-value → merge → exit
jump) and reconstruct it as a single `IfExp` abstract node nested in the
while-test slot (Principle 3). This is a new detection path comparable to the
BoolOp chain detector, not a refinement of existing logic.
**Why deferred:** The ternary-in-while pattern requires a new detector
(`_detect_while_ternary_condition`) analogous to
`_detect_while_condition_boolop_chain`, plus an `IfExp` reconstruction branch
in `_loop_generate_while`. Implementing and validating this without
regressing the existing ternary region tests (`tests/exhaustive/ternary/`) is
a substantial change. 11/15 already exceeds the ≥10 target.

### R6-08/09 (chained comparison in while-condition) — SKIP
**Source:** `while 0 < x < 10:` / `while a == b == c:`
**Symptom:** Decompiled output emits a spurious `break` inside the loop body
AND a module-level `break` (invalid Python outside a loop), causing recompile
SyntaxError masked as SKIP.
**Root cause:** The LoopRegion misclassifies the chained-comparison's
intermediate comparison blocks as break targets. CPython compiles
`0 < x < 10` as `LOAD 0; LOAD x; COMPARE_OP Lt; DUP_TOP; ROT_THREE;
COMPARE_OP Lt; POP_JUMP_IF_FALSE exit; JUMP_BACKWARD header`. The intermediate
`DUP_TOP; ROT_THREE; COMPARE_OP` block is part of the chained-compare
expression, but the break detector sees the `POP_JUMP_IF_FALSE exit` (the
chained-compare's false-exit) and treats the exit jump as a break. A correct
fix requires the chained-compare region detector
(`_cc_pre_loop_blocks`/chained-compare identification) to recognize the
chained-compare pattern in the while-test slot and own the intermediate
blocks (Principle 2), so the break detector does not see them. The while-test
would then reference the chained-compare region's entry as a single
`Compare` abstract node (Principle 3/4).
**Why deferred:** The chained-compare-while detection requires the chained
compare region to be identified as an inner region before the loop (Principle
1), which is a new identification path. 11/15 already exceeds the ≥10 target.

## 9. Conclusion

**11/15 R6 errors fixed (target ≥10 met), 0 regressions, +3 baseline tests
fixed as bonus.** All fixes honor Algorithm 4 principles (bottom-up
reduction, unique ownership, nesting = abstract node, parent references child
entry) and avoid all forbidden heuristics. The 4 unfixed R6 errors (R6-02,
R6-07, R6-08, R6-09) are documented as known limitations with root-cause
analysis — each requires a new detection path (nested BoolOp grouping,
ternary-while detector, chained-compare-while detector) rather than a
refinement of existing logic, and fixing them risks regressing the 11
already-passing cases.
