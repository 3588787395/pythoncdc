# LOOP Region Round_06 — Test Engineer Findings

Scope: LOOP region defects (while/for loops, break/continue, for-else/while-else, loop
conditions) discovered by minimal repros. Python 3.11.15. No code was modified — test
engineer role only.

## 1. Problem points found in the code (file:line references)

Loop region detection — `core/cfg/region_analyzer.py`:
- `_identify_loop_regions` 6-section docstring & algorithm: `region_analyzer.py:2912`
  - Step 7 WHILE_LOOP condition_block search (the chain that mis-attributes pre-loop
    init blocks and complex conditions): `region_analyzer.py:3062` onward
  - The `_cc_pre_loop_blocks` / chained-compare pre-loop capture (over-absorbs the
    assignment preceding a while with a chained/boolop condition): `region_analyzer.py:3069`
- `_classify_loop_type`: `region_analyzer.py:3798`
- `_find_loop_else` (else_blocks / natural_exit; nested for-else + outer break loss):
  `region_analyzer.py:3990`
- `_detect_break_continue` (break target / natural_exit; post-loop statement absorbed
  into break exit): `region_analyzer.py:4388`

Loop AST generation — `core/cfg/region_ast_generator.py`:
- `_generate_loop`: `region_ast_generator.py:2939`
- `_loop_generate_for`: `region_ast_generator.py:3188`
- `_loop_generate_while`: `region_ast_generator.py:3551`
  - while-true init_blocks emission (drops `n = 0` before `while True`): `region_ast_generator.py:3554`
  - ternary-in-while-condition handling (hoists ternary as `if` instead of `while` test):
    `region_ast_generator.py:3584`-`3780`
  - while-true short-circuit (returns before emitting pre-loop init): `region_ast_generator.py:3782`
- `_process_if_blocks`: `region_ast_generator.py:13853`

Root-cause categories observed:
- **A. BoolOp / chained-compare while-condition mishandled** — the condition region
  (BoolOpRegion / chained-compare) drops comparison terms, drops `not`, or flips
  boolean logic. The while `test` is rebuilt wrong.
- **B. Pre-loop init statement dropped** — the assignment immediately before a while
  with a complex (boolop) condition is absorbed into the condition region / not emitted
  as a pre-statement.
- **C. Ternary in while condition not reconstructed** — `while (x if c else 1):` is
  hoisted into an outer `if (c and x):` wrapping a degenerate `while x:`.
- **D. Nested for-else with `else: continue` + outer `break`** — the else clause and
  outer break are lost; a spurious `continue` is injected in the inner body.
- **E. Post-loop statement dropped when body contains `break`** — code after the loop
  (e.g. `print('end')`, `result = n`) is absorbed into the break target / natural_exit.
- **F. `while True` + init assignment (function scope)** — init(s) before `while True`
  dropped (same family as known `test_l15whiletruebreak_*`).
- **G. Chained comparison in while condition → invalid output** — emits `break` outside
  a loop (SyntaxError on recompile); framework masks as SKIP.

## 2. Error table (≥10 real LOOP errors)

All repros live in `tests/exhaustive/{while_loop,for_loop}/test_r6_*.py` and archived in
`minimal_repros/`. "Result" = pytest outcome of `verify_decompilation`.

| ID | test file | source code | failure summary | root cause |
|----|-----------|-------------|-----------------|------------|
| R6-01 | while_loop/test_r6_while_boolop_init_drop.py | `a = 0`<br>`while a < 3 or a < 6:`<br>`    a += 1` | 23 vs 21 instrs; decompiled drops `a = 0` (condition `a<3 or a<6` kept) | B |
| R6-02 | while_loop/test_r6_while_compound_andor.py | `a = 1; b = 2`<br>`while a < 5 and b < 5 or a == 1:`<br>`    a += 1; b += 1` | 35 vs 37; `a<5 and` hoisted into outer `if (a<5):`, while-test reduced to `b<5 or a==1`, spurious `if (a<5): pass` in body | A |
| R6-03 | while_loop/test_r6_while_not_or_logic.py | `a = 0`<br>`while not a > 5 or a < 0:`<br>`    a += 1` | 23 vs 25; decompiled `while a > 5 and a < 0:` — `not … or` flipped to `and` (wrong logic) + `a=0` dropped | A+B |
| R6-04 | while_loop/test_r6_while_not_paren_boolop.py | `a = 1; b = 1`<br>`while not (a < 0 and b < 0):`<br>`    a -= 1; b -= 1` | opcode mismatch instr 1; decompiled `while a < 0 and b < 0:` — `not` dropped entirely + inits dropped | A+B |
| R6-05 | while_loop/test_r6_while_or_not.py | `a = 1; b = 1`<br>`while not a or not b:`<br>`    a += 1; b += 1` | opcode mismatch instr 1; decompiled `while a and b:` — De Morgan flip (`not a or not b` → `a and b`) + inits dropped | A+B |
| R6-06 | while_loop/test_r6_while_and_three.py | `a=0; b=0; c=0`<br>`while a < 1 and b < 1 and c < 1:`<br>`    a += 1` | 41 vs 25; decompiled `while b < 1 and c < 1:` — first `and` term `a<1` dropped + all 3 inits dropped | A+B |
| R6-07 | while_loop/test_r6_while_ternary_cond.py | `x = 5; c = True`<br>`while (x if c else 1):`<br>`    x -= 1` | 17 vs 22; decompiled hoists `if (c and x):` then `while x:` + spurious `if (not c): continue` | C |
| R6-08 | while_loop/test_r6_while_chained_cmp.py | `x = 5`<br>`while 0 < x < 10:`<br>`    x -= 1` | SKIP (recompile SyntaxError); decompiled emits `break` inside loop + trailing `break` at module level (invalid Python) | G |
| R6-09 | while_loop/test_r6_while_triple_cmp.py | `a=1; b=2; c=3`<br>`while a == b == c:`<br>`    a += 1` | SKIP (recompile SyntaxError); decompiled emits spurious `break` + dead `a += 1` + module-level `break` | G |
| R6-10 | while_loop/test_r6_while_break_post_stmt.py | `n = 0`<br>`while n < 10:`<br>`    n += 1`<br>`    if n == 5: break`<br>`    print(n)`<br>`print('end')` | 30 vs 28; decompiled drops the post-loop `print('end')` | E |
| R6-11 | for_loop/test_r6_for_else_break_outer.py | `for i in range(5):`<br>`    for j in range(5):`<br>`        if j == 3 and i == 2: break`<br>`    else: continue`<br>`    break` | 27 vs 24; decompiled loses `else: continue` + outer `break`, injects spurious inner `continue` | D |
| R6-12 | for_loop/test_r6_for_else_continue_break.py | `for i in range(3):`<br>`    for j in range(3):`<br>`        if j == 1: break`<br>`    else: continue`<br>`    break` | 24 vs 21; same family as R6-11 (simpler inner condition) | D |
| R6-13 | while_loop/test_r6_whiletrue_init_in_func.py | `def f():`<br>`    n = 0`<br>`    while True:`<br>`        n += 1`<br>`        if n >= 10: break` | nested code obj 12 vs 10; drops `n = 0` before `while True` | F (l15 family) |
| R6-14 | while_loop/test_r6_whiletrue_multi_init.py | `def f():`<br>`    a = 0; b = 0`<br>`    while True:`<br>`        a += 1`<br>`        if a > 10: break` | nested code obj 14 vs 10; drops both `a=0` and `b=0` | F (l15 family) |
| R6-15 | while_loop/test_r6_whiletrue_break_else.py | `n = 0`<br>`while True:`<br>`    n += 1`<br>`    if n > 10: break`<br>`else: pass` | 12 vs 10; drops `n = 0` (and trivial `else: pass`) | F (l15 family) |

Real LOOP errors documented: 15 (13 FAIL + 2 SKIP-with-invalid-output).
New distinct defects beyond the known l15/wl30 families: 12 (R6-01..R6-12), of which
10 FAIL (R6-01..R6-07, R6-10..R6-12) and 2 SKIP (R6-08, R6-09).

## 3. Current loop success rate

Baseline before round_06: `tests/exhaustive/for_loop/ tests/exhaustive/while_loop/` →
5 failed / 308 passed (313 total).

After adding the 16 round_06 repros:
- 308 passed / 329 total → **93.6% pass rate** (19 failed, 2 skipped)
- The 308 previously-passing tests are unchanged (no regressions introduced).
- Of the 16 new repros: 14 FAIL, 2 SKIP, 0 PASS.

## 4. CTRL (non-LOOP) cases

| ID | test file | note |
|----|-----------|------|
| CTRL-1 | while_loop/test_r6_while_break_try_except.py | `while + try/except + break` — same root cause as known `test_wl30whilebreakintry_n/x` (except-cleanup pollution, PUSH_EXC_INFO/POP_EXCEPT placement). This is the Round_05 deferred Bug #10 ("while + try/finally + break + except cleanup pollution"), a TRY-region defect, not a LOOP defect. Not counted toward the 10. |

## 5. Notes for the fix engineer

- The highest-leverage cluster is **category A/B**: every while-loop whose condition is a
  BoolOp (`and`/`or`), a `not`-wrapped BoolOp, or a chained comparison is currently
  mis-reconstructed. Single-comparison while-loops and simple `while not x:` work; the
  breakage appears once the condition becomes a multi-term BoolOpRegion or chained
  compare. Investigate the condition_block ↔ BoolOpRegion/chained-compare region
  interaction in `_identify_loop_regions` (Step 7, `region_analyzer.py:3062`) and the
  `test` reconstruction in `_loop_generate_while` (`region_ast_generator.py:3551`).
- Category B (pre-loop init dropped) co-occurs with A — the init block immediately
  preceding the while is being absorbed into the condition region. `r6_while_boolop_init_drop`
  isolates this (condition correct, only `a = 0` missing).
- Category D (nested for-else + `else: continue` + outer `break`) is a structural
  reduction gap in `_find_loop_else` / `_detect_break_continue` for the
  for-else-with-outer-break idiom.
- Category E (post-loop statement dropped with break) is in break-target /
  natural_exit handling.
- Category F (while-true init) reproduces the known l15 failure with distinct sources;
  category G (chained cmp) emits invalid Python and is masked as SKIP by the test
  framework — worth asserting explicitly that decompiled output is syntactically valid.
