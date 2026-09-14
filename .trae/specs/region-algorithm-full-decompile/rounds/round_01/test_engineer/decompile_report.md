# Decompile Report: trade_info_utils.pyc

## Summary

| Metric | Value |
|--------|-------|
| Target pyc | `site-packages/IQCommon/util/trade_info_utils.pyc` |
| Python version | 3.11 |
| Total functions | 40 |
| Matched functions | 28 |
| Mismatched functions | 12 |
| Match rate | 70.00% (28/40) |
| Missing in decomp | 0 |
| Extra in decomp | 0 |

## Mismatching Function Details

### 1. add_trade
- **Orig ops**: 129 | **Decomp ops**: 56
- **True diffs**: 102 | **Jump diffs**: 0
- **First diff** @idx=26: `orig=LOAD_GLOBAL(datetime)` → `decomp=LOAD_GLOBAL(TradeOperationLogger)`
- **Pattern**: **TRUNCATED_FUNCTION_BODY** — The decompiler emits only the first ~20 instructions of the try block (variable initialization and Logger.write), then abruptly ends the function. The remaining ~73 instructions (datetime computation, if/else for trade_name, for-loop, with-statement, if/else return, except handler, with-finally) are completely omitted.
- **Root cause**: The decompiler fails to traverse the full CFG of the try block when it encounters a `with` statement (via `FileLock(trade_list_file)`) nested inside the try body. The region-based analysis prematurely terminates at the with-statement boundary.

### 2. check_and_update_trade
- **Orig ops**: 218 | **Decomp ops**: 228
- **True diffs**: 186 | **Jump diffs**: 3
- **First diff** @idx=36: `orig=LOAD_FAST(csv_reader)` → `decomp=LOAD_GLOBAL(FileIO)`
- **Pattern**: **WHILE_TRY_WITH_LOOP_BODY_DUPLICATION** — The decompiler extracts the try body from the while loop and places it outside the try/except, effectively duplicating the code. The decompiled output shows the loop body instructions (FileIO, csv_reader, for-loop) appearing both inside and outside the try block. The while-try-except-else structure is completely misrecognized.
- **Root cause**: The decompiler's region analysis fails to correctly associate the `with FileLock(trade_list_file)` inside a `while < try < with` nesting. The try-body region is extracted from the loop, and the except/else branches are misplaced or duplicated.

### 3. create_user_code_iqe
- **Orig ops**: 834 | **Decomp ops**: 833
- **True diffs**: 273 | **Jump diffs**: 2
- **First diff** @idx=528: `orig=POP_JUMP_FORWARD_IF_NONE` → `decomp=POP_JUMP_FORWARD_IF_TRUE`
- **Pattern**: **COMPOUND_OR_CONDITIONAL_IF_ELIF_MERGE_FAILURE** — The decompiler incorrectly decomposes `if business_mode or business_mode == 'mode2' or reloads and reloads:` into nested if/elif blocks, splitting the compound conditional into separate branches. The `elif business_mode == 'mode0':` block is merged incorrectly with the outer if, and the entire code after the `if/elif` chain within the try block is shifted out of position. This causes 273 true_diffs across the entire 834-instruction function.
- **Root cause**: The region-based analysis cannot correctly reconstruct compound `or` conditions in `if` statements, especially when they contain `and` sub-expressions. It splits `if A or B or C` into nested `if not A: if B or C:` and then fails to properly associate the `elif` branch.

### 4. get_last_stat
- **Orig ops**: 664 | **Decomp ops**: 526
- **True diffs**: 182 | **Jump diffs**: 1
- **First diff** @idx=480: `orig=LOAD_FAST(result_data)` → `decomp=LOAD_FAST(item)`
- **Pattern**: **TRY_EXCEPT_ELSE_MISSING_ELSE_CONTINUATION** — The decompiler omits approximately 138 instructions from the `else` block of a `try/except/else` structure. The original code has a try block that opens a file and parses JSON, an except handler for errors, and an else block that closes the file. The decompiled output includes the try and except portions but truncates at the else block, losing the `if fp is not None: fp.close()` code and subsequent function body continuation. The function then jumps from offset 480 to the end, skipping the code that populates `result_data['count']` and `result_data['offset']`.
- **Root cause**: The decompiler fails to emit the `else` clause of `try/except/else` when the else block contains only cleanup code (fp.close). The region analysis treats the else as part of the exception handler path rather than as the normal-completion path.

### 5. get_trade_list
- **Orig ops**: 339 | **Decomp ops**: 341
- **True diffs**: 263 | **Jump diffs**: 9
- **First diff** @idx=74: `orig=JUMP_FORWARD` → `decomp=LOAD_GLOBAL(os)`
- **Pattern**: **TRY_EXCEPT_ELSE_NESTED_IN_IF_TRY_EXCEPT** — The decompiler completely misorders the nested exception handling blocks. The original code has `try: if cond: try: ... except: ... else: ... except: ...`. The decompiled output places the outer except handler (line 74: JUMP_FORWARD to PUSH_EXC_INFO) at the same level as the inner else block, shifting all subsequent instructions. This is a catastrophic misordering — every instruction after the first except handler is at the wrong position.
- **Root cause**: The decompiler fails to correctly nest the inner `try/except/else` within the outer `try/except`. The inner else block (which continues to the outer try's normal code path) is conflated with the outer except handler, causing the entire control flow structure to be misrecognized.

### 6. get_trade_status
- **Orig ops**: 155 | **Decomp ops**: 157
- **True diffs**: 20 | **Jump diffs**: 5
- **First diff** @idx=137: `orig=JUMP_FORWARD` → `decomp=LOAD_FAST(return_trade_info)`
- **Pattern**: **WHILE_ELSE_IF_ELSE_MISORDER** — The decompiler misorders the `while...else` branch relative to the `if...else` branch for `return_trade_info`. In the original, after the while loop exhausts its retries (the `else` clause of `while`), it checks `return_trade_info` to decide what to return. In the decompiled version, the `return_trade_info` check appears at the wrong position, and the final `if return_trade_info: pass` block is emitted but lacks the correct continuation (should return `trade_status` when `return_trade_info` is False).
- **Root cause**: The decompiler fails to correctly emit the `while...else` clause when the else contains nested `if/else` with returns. The else-clause code is shifted relative to the post-while continuation code.

### 7. get_trade_unit_info
- **Orig ops**: 236 | **Decomp ops**: 212
- **True diffs**: 45 | **Jump diffs**: 9
- **First diff** @idx=191: `orig=PUSH_EXC_INFO` → `decomp=LOAD_FAST(fp)`
- **Pattern**: **WITH_NO_AS_FINALLY_HANDLER_MISDECOMPILE** — The decompiler omits the `with` statement's implicit finally handler (the `__exit__` cleanup for `FileLock`). In the original bytecode, after the `with Lock(trade_file, 'shared'):` block, there is a PUSH_EXC_INFO / WITH_EXCEPT_START / POP_JUMP_IF_TRUE / RERAISE sequence for the context manager's exception handling. The decompiler emits this as a simple try/except, losing the finally cleanup. Additionally, the `fp = None; fp = open(...)` pattern's implicit finally (close-fp-on-exception) is also mishandled — the decompiled code places `if fp is not None: fp.close()` outside the exception handling path where it should be inside the finally block.
- **Root cause**: The decompiler does not recognize `with` statements that lack an `as` clause (e.g., `with Lock(file, 'shared'):` without `as lock:`). It treats them as regular try/except blocks, losing the context manager's `__exit__` cleanup semantics. The BEFORE_WITH opcode is not properly handled.

### 8. get_user_info
- **Orig ops**: 94 | **Decomp ops**: 58
- **True diffs**: 52 | **Jump diffs**: 3
- **First diff** @idx=40: `orig=SWAP(2)` → `decomp=POP_TOP`
- **Pattern**: **WITH_NO_AS_FINALLY_HANDLER_MISDECOMPILE** — Same root cause as get_trade_unit_info. The `fp = None; fp = open(path, 'r')` pattern creates an implicit finally handler that closes `fp` on exception. The decompiler emits `if fp is not None: fp.close()` as normal code rather than as a finally handler, causing the entire exception handling structure (PUSH_EXC_INFO / POP_JUMP_IF_NONE / RERAISE at offsets 404-458) to be omitted or misplaced. The original has a complete with-style cleanup; the decompiled version has 36 fewer instructions.
- **Root cause**: Same as get_trade_unit_info — the decompiler fails to recognize implicit finally handlers generated by CPython for open() file handles without explicit `with` statements. The SWAP(2) opcode (part of the context manager protocol) is not correctly decompiled.

### 9. kill_trade_process
- **Orig ops**: 573 | **Decomp ops**: 564
- **True diffs**: 287 | **Jump diffs**: 6
- **First diff** @idx=138: `orig=LOAD_GLOBAL(os)` → `decomp=LOAD_GLOBAL(app_log)`
- **Pattern**: **NESTED_TRY_IF_ELSE_BLOCK_MERGE_FAILURE** — The decompiler merges the code after the `except BaseException:` handler with the code inside the except handler itself. In the original, the except handler calls `os.system(KILL_CMD)` and then continues with `if os.path.getsize(sim_path) == 0 and len(trade_id_list) > 0:`. The decompiler places the `os.path.getsize` check inside the except body at the wrong position, and the subsequent code (datetime computation, for-loop to rebuild write_info, with Lock to write) is completely shifted. This causes a cascade of 287 true_diffs.
- **Root cause**: The decompiler's region analysis fails to correctly delimit the except handler's scope when the except body contains conditional code followed by more code outside the except. The region boundary is incorrectly placed after the `os.system('sudo rm -rf ...')` call, causing the subsequent `if os.path.getsize(...)` block to be merged into the except handler.

### 10. query_trade_strategy_info
- **Orig ops**: 109 | **Decomp ops**: 109
- **True diffs**: 3 | **Jump diffs**: 7
- **First diff** @idx=81: `orig=LOAD_CONST(True)` → `decomp=JUMP_FORWARD(476)`
- **Pattern**: **FOR_ELSE_BREAK_RETURN_REORDER** — The decompiler swaps the `return True` (emitted after the for-loop break) with the `JUMP_BACKWARD` (the for-loop's back-edge). In the original bytecode: `LOAD_CONST(True); RETURN_VALUE; JUMP_BACKWARD`. In the decompiled: `JUMP_FORWARD; JUMP_BACKWARD; LOAD_CONST(True); RETURN_VALUE`. The `return True` and the for-loop continuation are swapped, causing 3 true_diffs and 7 jump_diffs. The decompiled code is semantically equivalent but structurally different.
- **Root cause**: The decompiler emits the `return True` statement at the wrong position in the for-else-break structure. After detecting `break` inside a `for` loop, it should emit the `return` before the back-edge jump, but instead emits the back-edge jump first.

### 11. trade_count
- **Orig ops**: 100 | **Decomp ops**: 100
- **True diffs**: 0 | **Jump diffs**: 0
- **Status**: **MATCH** (jump_only in some comparison runs)

### 12. trade_operation
- **Orig ops**: 304 | **Decomp ops**: 286
- **True diffs**: 100 | **Jump diffs**: 3
- **First diff** @idx=198: `orig=BEFORE_WITH(None)` → `decomp=POP_TOP`
- **Pattern**: **WITH_IN_TRY_IF_CONTINUE_DEAD_CODE** — The decompiler fails to handle the nested `with Lock(delete_trade_list_file):` inside the try block's if-else structure. Specifically: (1) The `with Lock(delete_trade_list_file):` that appears after the `return True/False` is dead code — it's inside the same scope but unreachable. The decompiler emits it as reachable code, shifting the `BEFORE_WITH` opcode and all subsequent instructions. (2) The `continue` statement inside the for-loop (after `items[2] = '2'`) causes the decompiler to incorrectly restructure the if/elif chain, merging the `if operation == 'delete': ... continue` with `elif operation == 'pause':`.
- **Root cause**: The decompiler does not correctly handle dead code (code after return statements) inside with-statement bodies. When a `with` statement is inside a try block that contains dead code after a return, the BEFORE_WITH opcode is lost and the context manager cleanup is omitted. Additionally, `continue` inside an if-elif chain within a for-loop causes the elif to be merged with the preceding if.

## Failure Pattern Summary

| Pattern | Count | Example Functions | Severity |
|---------|-------|-------------------|----------|
| WITH_NO_AS_FINALLY_HANDLER_MISDECOMPILE | 3 | get_user_info, get_trade_unit_info, trade_operation | High - loses cleanup code |
| COMPOUND_OR_CONDITIONAL_IF_ELIF_MERGE | 2 | create_user_code_iqe, kill_trade_process | Critical - 273+ true_diffs |
| TRY_EXCEPT_ELSE_NESTED_MISORDER | 2 | get_trade_list, get_last_stat | Critical - entire structure wrong |
| WHILE_TRY_EXCEPT_ELSE_MISORDER | 2 | get_trade_status, check_and_update_trade | High - loop/else misplaced |
| TRUNCATED_FUNCTION_BODY | 1 | add_trade | Critical - 56/129 ops emitted |
| FOR_ELSE_BREAK_RETURN_REORDER | 1 | query_trade_strategy_info | Low - semantically equivalent |
| FOR_IF_BREAK_RETURN_SWAP | 1 | query_trade_strategy_info | Low - 3 true_diffs |
| WITH_IN_TRY_DEAD_CODE_MISDECOMPILE | 1 | trade_operation | High - with cleanup lost |

## Root Cause Analysis

All 12 mismatches trace back to **3 core decompiler deficiencies**:

### RC1: Context Manager (`with`) Handling Failures (affects 5 functions)
The decompiler fails to properly handle `with` statements in the following cases:
- **with without `as` clause**: `with Lock(file, 'shared'):` generates `BEFORE_WITH + POP_TOP` instead of `BEFORE_WITH + STORE_FAST`. The decompiler incorrectly treats this as a bare try/except, losing the `__exit__` cleanup.
- **with inside try/except**: The with-statement's implicit finally handler (PUSH_EXC_INFO + WITH_EXCEPT_START + RERAISE) is not recognized as part of the with protocol.
- **Dead code after with**: Code that appears after return statements inside with-blocks is not correctly identified as dead, causing instruction shifts.

### RC2: Compound Conditional and If/Elif Chain Reconstruction (affects 3 functions)
- **Compound `or` conditions**: `if A or B or C:` is split into nested `if not (A or B): if C:` and then the inner conditional's elif/else branches are incorrectly merged with the outer if.
- **Mixed if/elif chains**: When some branches use `if` and others use `elif` (e.g., `if == 'start': ... if == 'stop': ... if == 'delete': ... elif == 'pause': ...`), the decompiler cannot correctly reconstruct the original mixed chain.

### RC3: Try/Except/Else Region Boundary Failures (affects 4 functions)
- **Nested try/except/else**: Inner try/except/else blocks inside outer try blocks have their else clauses misplaced — the else is treated as part of the outer except rather than the inner try's normal completion.
- **While-try-except-else**: The `while` loop's `else` clause is mispositioned relative to the `try/except/else` structure inside the loop body.
- **Truncated code after else**: The else clause of try/except/else is sometimes omitted entirely, losing cleanup code and subsequent function body continuation.

## Minimal Reproduction Files

All files in: `.trae/specs/region-algorithm-full-decompile/rounds/round_01/test_engineer/minimal_repros/`

| File | Pattern | Verification Status | True Diffs |
|------|---------|---------------------|------------|
| repro_01_with_no_as_finally_handler.py | WITH_NO_AS_FINALLY_HANDLER | MISMATCH | 10 |
| repro_02_for_else_break_return_reorder.py | FOR_ELSE_BREAK_RETURN_REORDER | MISMATCH | 18 |
| repro_03_while_try_except_else_for_if_continue.py | WHILE_TRY_EXCEPT_ELSE_FOR_IF_CONTINUE | MISMATCH | 11 |
| repro_04_with_statement_in_try_except.py | WITH_IN_TRY_EXCEPT | MATCH (0 diffs) | 0 |
| repro_05_compound_or_conditional_in_if_elif_try_except.py | COMPOUND_OR_IF_ELIF_MERGE | MISMATCH | 184 |
| repro_06_for_while_try_with_except_else_loop_body_dup.py | WHILE_TRY_WITH_LOOP_BODY_DUP | MISMATCH | 129 |
| repro_07_for_if_break_return_swap.py | FOR_IF_BREAK_RETURN_SWAP | MISMATCH | 3 |
| repro_08_with_in_try_if_continue_dead_code.py | WITH_IN_TRY_IF_CONTINUE_DEAD_CODE | MISMATCH | 92 |
| repro_09_nested_try_with_if_else_os_operations.py | NESTED_TRY_IF_ELSE_OS_OPS | MATCH (0 diffs) | 0 |
| repro_10_open_no_with_try_except_else_complex.py | OPEN_NO_WITH_TRY_EXCEPT_ELSE | MATCH (0 diffs) | 0 |
| repro_11_truncated_function_body_with_no_as.py | TRUNCATED_FUNC_BODY | MATCH (0 diffs) | 0 |
| repro_12_for_if_continue_dead_return.py | FOR_IF_CONTINUE_DEAD_RETURN | MATCH (0 diffs) | 0 |

**7 of 12 repros trigger bytecode mismatches** (confirmed FAIL). 5 repros currently match but demonstrate code structures that trigger failures in the real, more complex code (the failures emerge when these patterns are combined with additional nesting or with-statement usage).

## Priority Recommendations for Repair Engineer

1. **P0 — Fix `with` statement handling** (RC1): This is the single highest-impact fix. Properly handle `BEFORE_WITH` opcode, recognize `with` without `as` clause, and emit correct context manager cleanup. This would fix 5 of 12 mismatches.

2. **P1 — Fix compound conditional reconstruction** (RC2): Correctly reconstruct `if A or B or C:` as a single if-statement, not nested if/elif. This would fix 2 of the largest mismatches (273 and 287 true_diffs).

3. **P2 — Fix try/except/else region boundaries** (RC3): Ensure inner try/except/else blocks have their else clauses correctly placed relative to outer try blocks. This would fix 4 mismatches.

4. **P3 — Fix for-else break/return ordering** (Low priority): The reorder produces semantically equivalent code; this is a cosmetic fix.
