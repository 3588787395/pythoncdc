# Bytecode Mismatch Analysis Report
# 39 Partial PYC Files — Detailed Function-Level Analysis
# Generated: 2026-09-16

================================================================================
1. EXECUTIVE SUMMARY
================================================================================

Total pyc files:    402
OK (100% match):   363
Partial (<100%):    39
Failed (0%):         0
Cumulative match rate: 97.75%

Across the 39 partial files, 166 functions have bytecode mismatches.
These fall into 6 pattern categories, with try-region and loop-region
being the dominant root causes.

================================================================================
2. CATEGORY DISTRIBUTION (across 166 mismatched functions)
================================================================================

  Category         Count   %age    Description
  ──────────────── ────── ───────  ──────────────────────────────────────────
  try-region          78   47.0%   try/except/finally block boundary errors
  loop-region         55   33.1%   for-else / while-else reconstruction errors
  if-region           18   10.8%   if/elif/else chain reconstruction errors
  other                7    4.2%   Uncategorized (assert, walrus, etc.)
  boolop-region        5    3.0%   Short-circuit and/or errors
  with-region          3    1.8%   WITH statement context manager errors
  ──────────────── ────── ───────
  TOTAL              166  100.0%

================================================================================
3. DETAILED ANALYSIS OF TOP 3 LOWEST-RATE FILES
================================================================================

----------------------------------------------------------------------
3.1 function.pyc (73.33% — 11/15 matched)
   Path: site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc
----------------------------------------------------------------------

  Function: create_daily_stats
  Pattern:  loop-region (for-else with break)
  Details:  orig=482 instrs, decomp=281 instrs — MASSIVE divergence
            jump_diffs=5, true_diffs=393
            Divergence at index 72: orig has JUMP_BACKWARD (loop back-edge),
            decomp has BUILD_LIST. The for-else construct was completely
            lost. The decompiler omitted the else clause of the for-loop
            and collapsed 200+ instructions, likely misidentifying the
            else-block as part of the loop body.
  Root cause: for-else with conditional break inside a for-in loop.
            The decompiler fails to properly emit the else clause when
            the loop contains a break statement inside an if-block.

  Function: create_orders_stats
  Pattern:  loop-region (for loop with nested conditional)
  Details:  orig=311, decomp=315 — moderate divergence
            jump_diffs=1, true_diffs=103
            Divergence at index 193: after a COMPARE_OP, the decompiled
            code diverges — orig does `len(future_positions) > 0` while
            decomp generates `order['filled'] = None` followed by different
            logic. The inner if/elif/else chain inside the for-loop is
            incorrectly reconstructed.
  Root cause: Nested if/elif/else inside a for-loop body. The decompiler
            merges an elif branch with the else branch, causing subsequent
            instructions to be offset.

  Function: create_transactions_stats
  Pattern:  loop-region (for loop with nested conditional)
  Details:  orig=294, decomp=298
            jump_diffs=1, true_diffs=133
            Divergence at index 142 (follows a JUMP instruction).
            Similar pattern to create_orders_stats — the decompiler
            incorrectly handles the if/elif/else chain inside the loop
            body, causing trade['commission'] access to be replaced with
            different operations.
  Root cause: Same as create_orders_stats — nested conditional inside loop.

  Function: save_testds_to_json
  Pattern:  try-region+with-region (nested try-except, with-statement)
  Details:  orig=361, decomp=360
            jump_diffs=10, true_diffs=121
            CRITICAL: POP_EXCEPT is replaced by JUMP_FORWARD at index 188.
            The try block boundary is lost. The decompiler then generates
            PUSH_EXC_INFO where the original has RETURN_VALUE, and
            CHECK_EXC_MATCH where the original has the next except handler.
            This cascades through 4 levels of nested try-except blocks.
  Root cause: Deeply nested try-except blocks (4 levels). The decompiler
            loses track of the POP_EXCEPT/RERAISE cleanup sequence,
            causing the entire exception handling chain to be emitted
            in the wrong order. The finally/except boundaries are
            incorrectly placed.

----------------------------------------------------------------------
3.2 trade_info_utils.pyc (77.5% — 31/40 matched)
   Path: site-packages/IQCommon/util/trade_info_utils.pyc
----------------------------------------------------------------------

  Function: check_and_update_trade
  Pattern:  try-region+with-region
  Details:  orig=253, decomp=267
            jump_diffs=3, true_diffs=186
            Divergence at index 36: orig does `for items in csv_reader:`
            but decomp does `file_io = FileIO(trade_list_file)`. The
            with-statement context manager body was incorrectly
            reconstructed — the iterator from the with-block's result
            was replaced by a new FileIO call.
  Root cause: with-statement inside try-except. The decompiler
            confuses the context manager's __enter__ result with the
            variable in the subsequent for-loop.

  Function: create_user_code_iqe
  Pattern:  try-region+with-region
  Details:  orig=915, decomp=907 (large function!)
            jump_diffs=4, true_diffs=279
            Divergence at index 550: orig has JUMP_FORWARD(2908) but
            decomp has LOAD_CONST(user_strategy). A jump target is
            lost, causing the subsequent if-block's else branch to be
            emitted as the main body.
  Root cause: Large function with with-statement and try-except.
            The decompiler loses track of the JUMP_FORWARD at the
            end of an if-block inside a with-block, causing the
            else-clause to be merged with the if-body.

  Function: get_last_stat
  Pattern:  try-region
  Details:  orig=717, decomp=571 (orig is 25% larger!)
            jump_diffs=1, true_diffs=182
            Divergence at index 480: result_data['data'] vs item[12].
            The decompiler generates completely different variable
            accesses, suggesting the for-loop inside the try block
            was reconstructed with wrong iteration variable.
  Root cause: Complex try-except with for-loop and boolean operations.
            The decompiler merges the for-else with the except block,
            producing incorrect variable bindings.

  Function: get_trade_list
  Pattern:  try-region+with-region
  Details:  orig=383, decomp=386
            jump_diffs=14, true_diffs=228
            CRITICAL: JUMP_FORWARD is replaced by LOAD_GLOBAL(os).
            PUSH_EXC_INFO is replaced by LOAD_ATTR(path). The entire
            except handler entry sequence is missing — the decompiler
            emits the code inside the except block as if it were
            regular code (not inside an exception handler).
  Root cause: try-except around with-statement. The decompiler
            fails to emit the exception table entries properly,
            causing the except handler's code to be placed in-line
            rather than as an exception handler target.

  Function: get_trade_unit_info
  Pattern:  try-region+with-region
  Details:  orig=273, decomp=244
            jump_diffs=9, true_diffs=45
            PUSH_EXC_INFO replaced by LOAD_FAST(fp) at index 191.
            The with-statement's __exit__ cleanup (fp.__exit__) is
            incorrectly emitted as direct method calls without the
            proper exception handling wrapper.
  Root cause: with-statement followed by try-except. The decompiler
            generates the __exit__ call sequence incorrectly, missing
            the PUSH_EXC_INFO/POP_EXCEPT pair that Python uses for
            with-statement exception propagation.

  Function: get_user_info
  Pattern:  try-region
  Details:  orig=104, decomp=61 (orig is 70% larger!)
            jump_diffs=3, true_diffs=52
            SWAP(2) replaced by POP_TOP at index 40. The with-statement
            cleanup sequence (SWAP/POP_TOP for __exit__) is missing
            entirely in the decompiled version. The decompiler omits
            the with-as variable binding entirely.
  Root cause: with-as statement. The `with X as Y:` pattern is
            decompiled without the `as Y` part, losing the variable
            binding and the __exit__ cleanup sequence.

  Function: kill_trade_process
  Pattern:  try-region+with-region
  Details:  orig=673, decomp=670
            jump_diffs=6, true_diffs=286
            Divergence at index 138: orig does os.path.getsize() but
            decomp does app_log.warning(). Completely different code
            paths — the decompiler chose the wrong branch of an
            if/elif chain inside a try block.
  Root cause: if/elif/else chain inside try-except-with. The
            decompiler incorrectly resolves the branch targets,
            selecting the wrong elif branch as the active code path.

  Function: set_trade_status
  Pattern:  try-region+with-region
  Details:  orig=180, decomp=183
            jump_diffs=4, true_diffs=10 (relatively small divergence)
            JUMP_FORWARD(868) replaced by LOAD_CONST(None) at index 149.
            A JUMP_FORWARD that skips to the end of the try block is
            replaced by a LOAD_CONST(None)+RETURN_VALUE sequence,
            indicating the decompiler incorrectly terminated the
            function instead of jumping to the finally block.
  Root cause: try-except-with with early return. The decompiler
            converts a jump-to-finally into a direct return, skipping
            the finally block's cleanup code.

  Function: trade_operation
  Pattern:  try-region+with-region
  Details:  orig=339, decomp=316
            jump_diffs=3, true_diffs=133
            LOAD_GLOBAL(len) replaced by JUMP_BACKWARD at index 169.
            The decompiler inserts a loop back-edge where the original
            has a conditional check, indicating the loop body was
            incorrectly extended to include post-loop code.
  Root cause: for-loop inside with-statement inside try-except.
            The loop's back-edge target is miscalculated, causing
            the code after the loop to be included in the loop body.

----------------------------------------------------------------------
3.3 __init__.pyc (80% — 8/10 matched)
   Path: site-packages/IQEngine/plugins/plugin_system_log/__init__.pyc
----------------------------------------------------------------------

  Function: setup
  Pattern:  loop-region (for-in loop with if/elif/else)
  Details:  orig=351, decomp=279 (orig is 25% larger!)
            jump_diffs=1, true_diffs=293
            Divergence at index 25: orig has EXTENDED_ARG+POP_JUMP but
            decomp has POP_JUMP with a smaller target. The large if/elif/else
            chain inside the for-loop body causes the decompiler to
            collapse multiple branches. Specifically, the `for log_instance
            in (user_log, system_log, strategy_log):` loop followed by
            the `if engine.config.strategy.run_type == RunType.BACKTEST:`
            elif chain is incorrectly reconstructed.
  Root cause: for-loop with complex multi-branch if/elif/else inside.
            The decompiler fails to properly handle the EXTENDED_ARG
            prefix on jump instructions, causing the jump target to be
            truncated and the elif branches to be merged.

  Function: trade_logs_control
  Pattern:  try-region+with-region
  Details:  orig=213, decomp=214
            jump_diffs=1, true_diffs=144
            Divergence at index 42: orig has LOAD_GLOBAL(os) but decomp
            has JUMP_FORWARD(420). The if-condition `os.path.exists()`
            is replaced by a jump, indicating the decompiler inverted
            the condition and placed the else-branch code first.
  Root cause: if-condition inside while-loop inside with-statement.
            The decompiler incorrectly inverts a conditional branch,
            placing the else-block before the if-block. The with-
            statement's exception handling interferes with the
            conditional branch resolution.

================================================================================
4. ROOT CAUSE ANALYSIS BY PATTERN CATEGORY
================================================================================

4.1 try-region (78 functions, 47.0%)
────────────────────────────────────
Root cause: The decompiler fails to correctly reconstruct the exception
table and handler boundaries for try/except/finally blocks.

Specific failure modes:
  a) POP_EXCEPT is misplaced or missing — the decompiler emits the
     except-handler code without the proper POP_EXCEPT cleanup, causing
     the recompiled code to have a different exception table.
  b) PUSH_EXC_INFO is replaced by JUMP_FORWARD — the entry into an
     except handler is converted to a forward jump, losing the
     exception binding.
  c) Nested try-except blocks cause the decompiler to lose track of
     which exception handler is active, mixing handlers from different
     levels.
  d) try-else clauses are either omitted or merged with the try body,
     causing the else-block to execute unconditionally.
  e) finally blocks are emitted as regular code rather than as cleanup
     handlers, causing them to execute at the wrong time.

Most impactful sub-pattern: try-except inside with-statement (accounts
for ~40% of try-region mismatches). The BEFORE_WITH opcode's cleanup
sequence conflicts with the try block's exception handling.

4.2 loop-region (55 functions, 33.1%)
──────────────────────────────────────
Root cause: The decompiler fails to correctly reconstruct for-else and
while-else patterns, and miscalculates loop back-edge targets.

Specific failure modes:
  a) for-else: The else clause is completely omitted. The decompiler
     treats the code after the for-loop as continuation code rather
     than as the else-block that only executes when break is NOT hit.
  b) JUMP_BACKWARD replaced by non-loop opcodes (e.g., BUILD_LIST) —
     the loop's back-edge is lost, causing the entire post-loop code
     to be collapsed or omitted.
  c) FOR_ITER target miscalculation — the decompiler computes the
     wrong offset for the FOR_ITER instruction, causing the loop
     body to include extra instructions or miss some.
  d) Nested for-loops with break/continue — the decompiler confuses
     the break/continue targets between inner and outer loops.
  e) Loop inside try-except — the exception handler's jump targets
     interfere with the loop's back-edge calculation.

Most impactful sub-pattern: for-else with conditional break (accounts
for ~60% of loop-region mismatches). The create_daily_stats function
loses 200+ instructions due to this pattern.

4.3 if-region (18 functions, 10.8%)
────────────────────────────────────
Root cause: The decompiler fails on complex if/elif/else chains,
particularly when branches have different sizes or contain jumps.

Specific failure modes:
  a) elif is converted to else:if — the decompiler emits `else: if X:`
     instead of `elif X:`, which changes the bytecode structure
     (extra nesting level, different jump targets).
  b) Condition negation errors — the decompiler incorrectly inverts
     the condition of a branch, placing the if-body and else-body
     in the wrong order.
  c) EXTENDED_ARG prefix on jump instructions is mishandled — when
     the jump offset exceeds 256 bytes, an EXTENDED_ARG prefix is
     needed, and the decompiler sometimes drops it, truncating the
     target offset.
  d) Missing else clause — the else branch is simply omitted.

4.4 boolop-region (5 functions, 3.0%)
─────────────────────────────────────
Root cause: Short-circuit boolean operations (and/or) are incorrectly
reconstructed.

Specific failure modes:
  a) `a and b` is decompiled as `a; b` (losing the short-circuit
     semantics, though this may be semantically equivalent when
     there are no side effects, it produces different bytecode).
  b) `a or b or c` chains generate wrong JUMP_IF_TRUE_OR_POP targets.
  c) Boolean operations inside if-conditions interact with the
     if-statement's conditional jump, causing double-negation errors.

4.5 with-region (3 functions, 1.8%)
───────────────────────────────────
Root cause: WITH statement context manager cleanup is incorrectly
reconstructed.

Specific failure modes:
  a) The `with X as Y:` pattern loses the `as Y` binding — the
     variable Y is never assigned, and the __exit__ call receives
     wrong arguments.
  b) BEFORE_WITH + SWAP + POP_TOP sequence (for __exit__ cleanup)
     is replaced by direct method calls, changing the exception
     propagation behavior.
  c) Multiple with-statements (with A as a, B as b:) are split
     into nested with-statements, changing the cleanup order.

4.6 other (7 functions, 4.2%)
─────────────────────────────
Includes: walrus operator (:=), assert statements, generator
expressions with complex conditions, and class-body code that
uses nonlocal/super in unusual ways.

================================================================================
5. MINIMAL REPRODUCTION TEST CASES
================================================================================

# ----- 5.1 try-region: nested try-except-finally -----
def test_nested_try_except_finally():
    try:
        try:
            x = 1 / 0
        except ZeroDivisionError:
            x = 0
    except Exception:
        x = -1
    finally:
        x += 1
    return x

# ----- 5.2 try-region: try-except-else -----
def test_try_except_else():
    try:
        x = risky()
    except ValueError:
        x = default()
    else:
        x = process(x)
    return x

# ----- 5.3 try-region: with-inside-try -----
def test_with_inside_try():
    try:
        with open("test.txt") as f:
            data = f.read()
    except OSError:
        data = ""
    return data

# ----- 5.4 try-region: deeply-nested try (4 levels) -----
def test_deep_nested_try():
    try:
        try:
            try:
                try:
                    x = outer()
                except OSError:
                    x = ""
            except ValueError:
                x = "val"
        except RuntimeError:
            x = "run"
    except Exception:
        x = "exc"
    return x

# ----- 5.5 loop-region: for-else with break -----
def test_for_else_break():
    for i in range(10):
        if i == 5:
            break
    else:
        return "no break"
    return "broken at %d" % i

# ----- 5.6 loop-region: for-else without break -----
def test_for_else_no_break():
    for i in range(10):
        pass
    else:
        return "completed"
    return "unreachable"

# ----- 5.7 loop-region: while-else with break -----
def test_while_else_break():
    x = 10
    while x > 0:
        x -= 1
        if x == 3:
            break
    else:
        return "completed"
    return "interrupted at %d" % x

# ----- 5.8 loop-region: nested for with break -----
def test_nested_for_break():
    result = []
    for i in range(5):
        for j in range(5):
            if j == 3:
                break
        result.append(i)
    return result

# ----- 5.9 loop-region: for-loop inside try-except -----
def test_for_in_try():
    try:
        result = []
        for item in items:
            result.append(process(item))
    except Exception:
        result = []
    return result

# ----- 5.10 if-region: elif chain -----
def test_elif_chain(x):
    if x == 1:
        return "one"
    elif x == 2:
        return "two"
    elif x == 3:
        return "three"
    else:
        return "other"

# ----- 5.11 if-region: if-else inside for-loop -----
def test_if_else_in_for(items):
    result = []
    for item in items:
        if item > 0:
            result.append("positive")
        else:
            result.append("non-positive")
    return result

# ----- 5.12 boolop-region: short-circuit and/or -----
def test_boolop_and_or(a, b, c):
    if a and b or c:
        return True
    return False

# ----- 5.13 boolop-region: chained or -----
def test_chained_or(a, b, c, d):
    return a or b or c or d

# ----- 5.14 with-region: with-as binding -----
def test_with_as_binding():
    with open("test.txt") as f:
        data = f.read()
    return data

# ----- 5.15 with-region: with-in-for-loop -----
def test_with_in_for(filenames):
    results = []
    for name in filenames:
        with open(name) as f:
            results.append(f.read())
    return results

================================================================================
6. IMPACT SUMMARY — WHICH PATTERN TYPES ARE MOST COMMON
================================================================================

Rank  Category        Funcs  %age   Impact Level
───── ─────────────── ────── ──────  ─────────────────────────────────────────
 1    try-region        78   47.0%  ★★★★★ CRITICAL — accounts for nearly half
                                        of all mismatches. Most severe when
                                        combined with with-statement (try+with).
                                        Affects 7 of 9 functions in the #2 worst
                                        file (trade_info_utils.pyc).

 2    loop-region       55   33.1%  ★★★★☆ HIGH — accounts for one-third of
                                        mismatches. Most severe when the loop
                                        has an else clause (for-else/while-else).
                                        Responsible for the #1 worst file's
                                        main issue (function.pyc, 73.33%).

 3    if-region         18   10.8%  ★★☆☆☆ MEDIUM — typically causes small
                                        divergences (10-65 true_diffs) but
                                        affects many files. Most common in
                                        functions with 3+ elif branches.

 4    other              7    4.2%  ★☆☆☆☆ LOW — diverse unclassified issues.

 5    boolop-region      5    3.0%  ★☆☆☆☆ LOW — affects specific patterns
                                        of chained and/or operations.

 6    with-region        3    1.8%  ★☆☆☆☆ LOW — standalone with-statement
                                        issues; most with-issues are already
                                        counted under try-region (combined).

================================================================================
7. RECOMMENDATIONS FOR DECOMPILER IMPROVEMENT
================================================================================

Priority 1 (try-region): Fix exception table reconstruction
  - Ensure POP_EXCEPT is emitted at the correct position after each
    except-handler body, before transitioning to the next handler or
    the finally block.
  - When a with-statement is inside a try block, preserve the
    BEFORE_WITH cleanup sequence (SWAP/POP_TOP for __exit__) and
    don't merge it with the try block's exception handling.
  - For nested try blocks, maintain a stack of active exception
    handlers and emit POP_EXCEPT in the correct order (innermost first).

Priority 2 (loop-region): Fix for-else / while-else reconstruction
  - After the FOR_ITER instruction, check if the code immediately
    following the loop's back-edge is an else-block (i.e., code that
    only executes when the loop completes without break).
  - When a JUMP_BACKWARD (loop back-edge) is followed by code that
    isn't a simple loop continuation, emit it as the else clause.
  - Preserve the exact FOR_ITER jump target — the target should point
    to the first instruction after the else-block, not after the loop.

Priority 3 (if-region): Fix elif chain reconstruction
  - When emitting elif branches, ensure the JUMP_FORWARD at the end
    of each branch targets the same location as the final else branch.
  - Handle EXTENDED_ARG prefix correctly for jump offsets > 256 bytes.
  - Don't convert elif to nested else:if — this changes the bytecode
    structure by adding an extra nesting level.

================================================================================
END OF REPORT
================================================================================
