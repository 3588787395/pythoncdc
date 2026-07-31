# LOOP Region Round_06 Condition Reconstruction Spec

> Parent spec: `iterate-region-test-fix` (umbrella for 10 regions × 20 rounds).
> This change-id scopes Task 2.6 (LOOP round_06) of the parent spec into a concrete,
> self-contained spec for the repair-engineer pass.
> Test engineer's findings: `iterate-region-test-fix/rounds/loop/round_06/test_engineer/findings.md`.

## Why

The pythoncdc decompiler mis-reconstructs while-loop **conditions** whenever the
condition becomes a multi-term `BoolOp` (`and`/`or`), a `not`-wrapped `BoolOp`,
or a chained comparison. The decompiled output either drops comparison terms,
drops `not`, flips boolean logic (De Morgan inversion), drops the pre-loop
initialization assignment, or emits invalid Python (`break` outside a loop).
Recompiled bytecode therefore no longer matches the original
instruction-by-instruction. The test engineer's round_06 sweep documented 15
distinct LOOP errors (R6-01..R6-15) across 7 root-cause clusters (A..G).

## What Changes

- **Cluster A/B (BoolOp condition + pre-loop init drop, R6-01..R6-06):** Fix the
  BoolOp forward-chain detection in `_detect_while_boolop_forward_chain` /
  `_detect_boolop_conditional_chain` so the **first** comparison term is not
  dropped (e.g. `a<1 and b<1 and c<1` must keep `a<1`), and fix
  `_build_boolop_expression` / `not` wrapping so `not (a<0 and b<0)`,
  `not a or not b`, `not a>5 or a<0` reconstruct verbatim (no De Morgan flip).
  Pre-loop init statements (`a = 0`) immediately preceding a BoolOp-conditioned
  while must be preserved as pre-statements, not absorbed into the BoolOpRegion.
  R6-01 fix (remove `pre_stmts = []` clearing at
  `region_ast_generator.py:3762`/`4005`/`4123` region for BoolOp case) is
  already in place and MUST be retained.
- **Cluster C (ternary in while condition, R6-07):** Reconstruct
  `while (x if c else 1):` as a single while-test `IfExp`, not as a hoisted
  outer `if (c and x):` wrapping a degenerate `while x:`.
- **Cluster D (nested for-else + outer break, R6-11/12):** Preserve the inner
  for-else `else: continue` clause and the outer `break` in
  `_find_loop_else` / `_detect_break_continue`; do not inject a spurious inner
  `continue`.
- **Cluster E (post-loop statement dropped with break, R6-10):** Preserve code
  after the loop (`print('end')`) when the loop body contains `break`; the
  break target / natural_exit must not absorb trailing statements.
- **Cluster F (while-true init drop, R6-13/14/15):** Populate
  `LoopRegion.init_blocks` during identification so `n = 0` / `a = 0; b = 0`
  before `while True:` are emitted as pre-statements (same family as the known
  l15/wl30 defects).
- **Cluster G (chained comparison in while condition, R6-08/09):** Reconstruct
  `while 0 < x < 10:` and `while a == b == c:` as a single chained-compare
  while-test; do NOT emit a spurious `break` inside the loop or a module-level
  `break` (currently a recompile SyntaxError masked as SKIP).
- **Deliverable:** Write
  `iterate-region-test-fix/rounds/loop/round_06/repair_engineer/fix_report.md`
  with: fixes applied (file:line), algorithm justification (4 principles),
  docstring updates, regression results, residual errors, known limitations.

## Impact

- Affected specs: parent `iterate-region-test-fix` (Task 2.6).
- Affected code:
  - `core/cfg/region_analyzer.py` — BoolOp chain detection
    (`_detect_while_boolop_forward_chain`, `_detect_boolop_conditional_chain`,
    `_detect_boolop_chain_start`), loop identification Step 7 condition_block
    search (`region_analyzer.py:3062`), `_classify_loop_type` (3798),
    `_find_loop_else` (3990), `_detect_break_continue` (4388), chained-compare
    pre-loop capture `_cc_pre_loop_blocks` (3069), `LoopRegion.init_blocks`
    population for while-true.
  - `core/cfg/region_ast_generator.py` — `_loop_generate_while` (3551) and its
    BoolOp / ternary / chained-compare test reconstruction sub-helpers,
    while-true init_blocks emission (3554), ternary-in-while-condition handling
    (3584-3780), while-true short-circuit (3782), `_loop_generate_for` (3188),
    `_process_if_blocks` (13853).
- Affected tests: 16 repros under `tests/exhaustive/{while_loop,for_loop}/test_r6_*.py`
  (15 R6 LOOP errors + 1 CTRL-1 try/except excluded from the 10-target).
- Baseline inviolable: `tests/exhaustive/{while_loop,for_loop}/` baseline is
  5 failed / 308 passed (313 total) pre-round_06. After adding the 16 round_06
  repros: 19 failed / 2 skipped / 308 passed (329 total). No regression on the
  308 previously-passing tests is permitted. Cross-region regressions
  (ternary, if_region, control_flow_matrix) are also forbidden.

## ADDED Requirements

### Requirement: BoolOp forward-chain detection captures all terms

The BoolOp forward-chain detector SHALL capture every comparison term in a
multi-term `and`/`or` while-condition, including the **first** term whose
block is the loop's `cond_block`. The detector MUST NOT begin the chain at
the second term.

#### Scenario: Three-term `and` while-condition
- **WHEN** source is `while a < 1 and b < 1 and c < 1:`
- **THEN** the reconstructed `test` is `BoolOp(And, [a<1, b<1, c<1])` (all
  three terms, original order)
- **AND** recompiled bytecode matches the original instruction-by-instruction

#### Scenario: Compound `and`/`or` while-condition
- **WHEN** source is `while a < 5 and b < 5 or a == 1:`
- **THEN** the `test` is `BoolOp(Or, [BoolOp(And, [a<5, b<5]), a==1])`
- **AND** no spurious outer `if (a<5):` is hoisted out of the while-test

### Requirement: `not`-wrapped BoolOp reconstructs verbatim

A `not`-wrapped BoolOp while-condition SHALL reconstruct verbatim (no De
Morgan inversion). `not (a<0 and b<0)` → `UnaryOp(Not, BoolOp(And, [a<0, b<0]))`,
NOT `BoolOp(Or, [a>=0, b>=0])`. `not a or not b` → `BoolOp(Or, [Not(a), Not(b)])`,
NOT `BoolOp(And, [a, b])`.

#### Scenario: `not (a and b)` parenthesised
- **WHEN** source is `while not (a < 0 and b < 0):`
- **THEN** the `test` is `Not(BoolOp(And, [a<0, b<0]))` (verbatim, no flip)

#### Scenario: `not a or not b` distributed
- **WHEN** source is `while not a or not b:`
- **THEN** the `test` is `BoolOp(Or, [Not(a), Not(b)])` (no De Morgan flip to
  `And`)

### Requirement: Pre-loop init statement preserved before BoolOp while

A pre-loop initialization assignment (`a = 0`) immediately preceding a
while-loop whose condition is a BoolOp / chained-compare SHALL be emitted as
a pre-statement of the loop, NOT absorbed into the condition region or
cleared by `pre_stmts = []`.

#### Scenario: Single init before `or` while-condition
- **WHEN** source is `a = 0\nwhile a < 3 or a < 6:\n    a += 1`
- **THEN** the decompiled output contains `a = 0` immediately before the
  `while` statement
- **AND** the `test` is `BoolOp(Or, [a<3, a<6])`

### Requirement: Chained comparison while-condition reconstructs as single Compare

A chained-comparison while-condition (`0 < x < 10`, `a == b == c`) SHALL
reconstruct as a single `Compare` node with multiple operators, and the
decompiled output MUST be syntactically valid Python (no `break` outside a
loop, no spurious `break` inside the loop body).

#### Scenario: Two-operator chained comparison
- **WHEN** source is `while 0 < x < 10:`
- **THEN** the `test` is `Compare(0, [Lt, Lt], [x, 10])`
- **AND** the body contains no spurious `break` and there is no module-level
  `break`

### Requirement: while-True pre-loop init via `init_blocks`

A `while True:` loop preceded by initialization(s) (`n = 0`, `a = 0; b = 0`)
SHALL have those initializations captured in `LoopRegion.init_blocks` at the
**identification** stage and emitted as pre-statements by `_loop_generate_while`.

#### Scenario: Single init before `while True` in function scope
- **WHEN** source is `def f():\n    n = 0\n    while True:\n        n += 1\n        if n >= 10: break`
- **THEN** the function body contains `n = 0` before the `while True:`

### Requirement: Post-loop statement preserved when body contains `break`

Code after a while-loop whose body contains `break` SHALL be preserved as
sequential statements after the loop, NOT absorbed into the break target /
natural_exit.

#### Scenario: `print('end')` after break-loop
- **WHEN** source contains `while n < 10:\n    ...\n    if n == 5: break\n    print(n)\nprint('end')`
- **THEN** the decompiled output contains `print('end')` after the `while`

### Requirement: Nested for-else + outer break preserved

A nested `for ... else: continue` followed by an outer `break` SHALL
reconstruct both the inner `else: continue` clause and the outer `break`,
without injecting a spurious inner `continue`.

#### Scenario: Inner for-else continue + outer break
- **WHEN** source is `for i in range(5):\n    for j in range(5):\n        if j == 3 and i == 2: break\n    else: continue\n    break`
- **THEN** the inner for has an `else: continue` clause
- **AND** the outer body contains the trailing `break`
- **AND** no spurious `continue` is injected in the inner body

### Requirement: Ternary in while-condition reconstructs as single IfExp test

A while-condition that is a ternary (`while (x if c else 1):`) SHALL
reconstruct the `test` as a single `IfExp(c, x, 1)`, NOT as a hoisted outer
`if (c and x):` wrapping a degenerate `while x:` plus a spurious
`if (not c): continue`.

#### Scenario: Ternary while-condition
- **WHEN** source is `while (x if c else 1):`
- **THEN** the `test` is `IfExp(c, x, 1)`

## MODIFIED Requirements

### Requirement: `_detect_while_boolop_forward_chain`

Original behavior: builds the chain starting from `cond_block` and appends
fall-through successors; in practice the chain's first term (`cond_block`
itself) is sometimes dropped from the rebuilt expression when the
`BoolOpRegion` is later reconstructed, because the chain is treated as
"starting after" the cond_block rather than "starting at" it.

Modified behavior: the chain MUST include `cond_block` as its first term and
the rebuilt `BoolOp` expression MUST include `cond_block`'s comparison as the
first operand. This honors Principle 4 (parent references child entry): the
while-loop's `test` references the BoolOpRegion's entry (=`cond_block`) as
the abstract expression node, and Principle 3 (nesting = abstract node): the
BoolOpRegion is a single abstract expression node nested inside the loop's
test slot.

### Requirement: `_loop_generate_while` pre_stmts handling

Original behavior (pre-R6-01 fix): the BoolOp branch cleared
`pre_stmts = []`, discarding init statements extracted at step 5
(cond_block != header branch, L3811) before appending BoolOp-region stores.

Modified behavior (R6-01 fix, MUST retain): preserve `pre_stmts` extracted
at step 5 (which already filters walrus via `_has_prev_copy` guard, leaving
only pure initialization assignments like `a = 0`). Only append non-cond_block
chain-block stores from the BoolOp region. This honors Principle 2 (unique
ownership): the init store belongs to the loop's pre-statements, not to the
BoolOpRegion's expression.

### Requirement: `_loop_generate_while` while-True init emission

Original behavior: when the loop is `while True:` with no condition_block,
`init_blocks` is sometimes empty because identification did not populate it,
causing `n = 0` to be dropped.

Modified behavior: identification MUST populate `LoopRegion.init_blocks` with
the pre-header assignment block(s) for while-True loops, and
`_loop_generate_while` MUST emit them as pre-statements (the existing
emission code at L3554 is correct once `init_blocks` is populated).

### Requirement: `_find_loop_else` / `_detect_break_continue` for break + post-loop

Original behavior: when the loop body contains `break`, the break target /
natural_exit absorbs trailing post-loop statements.

Modified behavior: the break target MUST be exactly the loop's natural exit
(no trailing fall-through absorption), and any statements after the loop
MUST remain in the parent region's sequential statement list. This honors
Principle 2 (unique ownership): post-loop statements belong to the parent
region, not to the loop's break exit.

## REMOVED Requirements

### Requirement: `pre_stmts = []` clearing in BoolOp branch of `_loop_generate_while`

**Reason**: Violates Principle 2 (unique ownership) by re-claiming init
stores that step 5 already extracted for the loop's pre-statements, causing
pre-loop inits (`a = 0`) to be dropped before BoolOp-conditioned whiles.

**Migration**: The clearing is removed (already done as the R6-01 fix at
`region_ast_generator.py:4123` region). Step 5's `_has_prev_copy` guard
continues to filter walrus (COPY+STORE left on stack), so only pure
initialization assignments are extracted — no double-extraction risk.

## Algorithm 4 Principles (MUST follow — violations forbidden)

1. **自底向上归约 / Bottom-up reduction:** identify inner regions (BoolOp,
   chained-compare, ternary) before the outer loop region. The loop's `test`
   is rebuilt from the already-identified inner region's entry, not from
   raw CFG walk.
2. **每块唯一归属 / Unique ownership:** each CFG block belongs to exactly
   one region. Init stores belong to the loop's pre-statements; BoolOp
   comparison blocks belong to the BoolOpRegion; post-loop statements belong
   to the parent region.
3. **嵌套即抽象节点 / Nesting = abstract node:** a BoolOpRegion / ternary /
   chained-compare nested in the loop's `test` is a single abstract
   expression node; the loop region does not flatten it.
4. **父引用子入口 / Parent references child entry:** the while-loop's `test`
   references the BoolOpRegion's entry block (=`cond_block`) as the abstract
   expression node, not a re-walk of the chain.

## FORBIDDEN (hard constraints)

- NO post-processing patches (no AST rewriting after region AST generation).
- NO cross-region heuristics / special cases (no "if loop has BoolOp and
  break then ..." rules).
- NO hardcoded depth limits on chain length.
- NO flattening of nesting (no inlining the BoolOpRegion into the loop).
- NO heuristic priority overrides.
- Do NOT modify any `+OK.py` generated files.
- Do NOT modify existing passing tests (the 308 baseline tests are
  inviolable).
- Each fix MUST be correct at the IDENTIFICATION stage (one-pass
  correctness) — no second-pass cleanup.

## Target

Fix **≥10 of the 15** R6 errors. Mark unfixable ones as known limitations
with root-cause analysis (do NOT patch them with forbidden heuristics).
