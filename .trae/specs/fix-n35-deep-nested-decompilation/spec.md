# Fix n35 Deep-Nested Decompilation Failure Spec

## Why
When decompiling `if a > 0: for x in range(10): try: pass; except IndexError: pass`, the outer `if` condition is lost. The decompiled output starts with the for-loop's iter call instead of the if-condition, producing 27 instructions vs the expected 21. The root cause is in `region_analyzer.py`'s `_parse_exception_table` merge step and `_identify_try_except_regions`'s `pre_handler_blocks` logic, which together cause the if-condition block to be incorrectly claimed by the TryExceptRegion.

## What Changes
- **Fix 1 (pre_handler_blocks)**: In `_identify_try_except_regions`, when adding pre-handler blocks to try_blocks, skip blocks that are before `try_start_for_blocks` AND have successors branching outside the try range. This prevents the if-condition block (which branches to both the for-loop body and the code after the if) from being claimed by the TryExceptRegion.
- **Fix 2 (merge)**: In `_parse_exception_table`'s merge step, skip merging entries whose `try_start >= existing['handler_start']` UNLESS the handler's instructions are already within the existing try range. This prevents cleanup entries from extending `try_end` past the handler entry block, which would trigger the `pre_handler_blocks` code path.
- **Fix 3 (BACKWARD_CONDITIONAL_JUMP_OPS)**: In `_detect_break_continue`, also check for conditional backward jumps (not just `JUMP_BACKWARD`) when determining if a block is a loop backedge target. This fixes loop detection for conditional back-edges in nested structures.
- **Fix 4 (LoopRegion in elif chain)**: In `_check_elif_chain`, allow `LoopRegion` as a valid existing region type for elif chain detection (alongside IfRegion, TernaryRegion, TryExceptRegion, etc.).
- **Fix 5 (IfRegion child in loop body)**: In `region_ast_generator.py`'s loop body generation, when a block is the condition block of a child IfRegion that has no exit (break/return), generate the IfRegion as a statement rather than treating the block as a plain loop body block.

## Impact
- Affected specs: nested region decompilation (n35 pattern: if > for > try/except)
- Affected code: `core/cfg/region_analyzer.py` (Fixes 1-4), `core/cfg/region_ast_generator.py` (Fix 5)
- Baseline: 77f/1730p on full exhaustive test suite
- Expected: n35 tests pass, no regressions

## ADDED Requirements

### Requirement: Exception table merge must not extend try_end past handler entry
The `_parse_exception_table` method SHALL NOT merge exception table entries that would extend `try_end` past the handler entry block, unless the handler's instructions are already within the existing try range. When a cleanup entry (resolved by `_find_actual_handler_start` to the same handler_start as a main entry) has `try_start >= existing['handler_start']`, and the handler block's instructions are NOT within the existing try range, the cleanup entry SHALL be skipped during merging.

#### Scenario: n35 pattern — if > for > try/except
- **WHEN** decompiling `if a > 0: for x in range(10): try: pass; except IndexError: pass`
- **THEN** the decompiled output preserves the outer `if` condition and produces bytecode-equivalent results (21 instructions matching the original)

#### Scenario: te28 pattern — if > try/except (no regression)
- **WHEN** decompiling `if a > 0: try: pass; except IndexError: pass`
- **THEN** the handler IS already within the existing try range, so the merge correctly includes the cleanup entry to extend try_end, preserving existing behavior

### Requirement: Pre-handler blocks with outer branches must not be claimed by TryExceptRegion
The `_identify_try_except_regions` method SHALL NOT add blocks before `try_start_for_blocks` to `try_blocks` if those blocks have successors that branch outside the try range (offset >= try_end_for_blocks) and are not the handler entry block. Such blocks belong to outer control structures (e.g., an if-condition) and should not be claimed by the TryExceptRegion.

#### Scenario: if-condition block before for > try/except
- **WHEN** a block before the try range has successors both into the try range and outside the try range
- **THEN** the block SHALL NOT be added to try_blocks, allowing it to be claimed by the correct outer IfRegion

### Requirement: Conditional backward jumps recognized as loop backedges
The `_detect_break_continue` method SHALL recognize conditional backward jumps (e.g., `JUMP_BACKWARD_IF_TRUE`, `JUMP_BACKWARD_IF_FALSE`) as loop backedge indicators, not just unconditional `JUMP_BACKWARD`.

#### Scenario: Loop with conditional back-edge in nested structure
- **WHEN** a block contains a conditional backward jump to a loop header
- **THEN** the block SHALL be recognized as a loop backedge target, not misclassified

### Requirement: LoopRegion allowed in elif chain detection
The `_check_elif_chain` function SHALL allow `LoopRegion` as a valid existing region type for the first else block, alongside IfRegion, TernaryRegion, TryExceptRegion, WithRegion, and BoolOpRegion.

#### Scenario: elif chain where else block is a LoopRegion
- **WHEN** the first else block in an elif chain is already claimed by a LoopRegion
- **THEN** the elif chain detection SHALL proceed rather than returning None

### Requirement: IfRegion child in loop body generated as statement
When generating loop body statements, if a block is the condition block of a child IfRegion that has no exit paths (no break/return in its content blocks), the IfRegion SHALL be generated as a statement (if/else) rather than treating the block as a plain loop body block.

#### Scenario: if-statement inside for-loop body with no exits
- **WHEN** a loop body block is the condition block of a child IfRegion with no break/return exits
- **THEN** the IfRegion SHALL be generated as an if-statement in the loop body

## MODIFIED Requirements

### Requirement: Zero regression on full exhaustive test suite
After applying all fixes, the full exhaustive test suite SHALL NOT have more failures than the baseline (77f/1730p). Any regression SHALL be reported and the change reverted.

## REMOVED Requirements
(None)
