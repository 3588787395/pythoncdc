# Fix n17 for-if-elif-else Decompilation Failure Spec

## Why
When decompiling `for item in items: if item > 0: a = item * 2; elif item < 0: b = abs(item); else: c = 0`, the output is `for item in items: item > 0; continue` — the if-elif-else structure is completely lost. This affects 5 nested tests (n17for_if_elif_else_a/b/c and n17for_if_elif_else_n/m/x) and represents a fundamental gap in handling if-elif-else chains inside for loops.

## What Changes
- **region_analyzer.py**: Add `LoopRegion` to the allowed region types in `_check_elif_chain` so that elif chain detection works when the else-branch condition block is inside a LoopRegion
- **region_ast_generator.py**: In `_loop_dispatch_block`, when a CONTINUE-role block with meaningful instructions is also the `condition_block` of an IfRegion child of the current loop AND the IfRegion contains no BREAK/RETURN blocks, generate the IfRegion directly instead of appending to `body_blocks_no_header`
- **region_ast_generator.py**: In `_process_if_blocks`, when processing a LOOP_BODY block that is part of an IfRegion's then/else blocks (i.e., `region` parameter is not None), use `_build_effective_stmts` for effective instructions instead of falling through to `_generate_block_statements`

## Impact
- Affected specs: nested region (n17 tests), for_loop region (potential side effects on break/continue/return patterns)
- Affected code:
  - `core/cfg/region_analyzer.py` — `_check_elif_chain` method (~L9003-9014)
  - `core/cfg/region_ast_generator.py` — `_loop_dispatch_block` method (~L2478-2500), `_process_if_blocks` method (~L5265-5284)

## ADDED Requirements

### Requirement: elif chain detection inside loops
The system SHALL detect elif chains when the else-branch condition block maps to a LoopRegion in `block_to_region`. Currently, `_check_elif_chain` returns `None` when `block_to_region[first_else]` is a LoopRegion, preventing elif chain detection for if-elif-else structures inside for/while loops.

#### Scenario: for-if-elif-else elif chain detection
- **WHEN** decompiling `for item in items: if item > 0: a = item * 2; elif item < 0: b = abs(item); else: c = 0`
- **THEN** the outer IfRegion SHALL be classified as `IF_ELIF_CHAIN` (not `IF_THEN_ELSE`)

### Requirement: IfRegion generation for CONTINUE-role condition blocks
The system SHALL generate IfRegion AST nodes when a CONTINUE-role block with meaningful instructions is the `condition_block` of an IfRegion child of the current loop, provided the IfRegion contains no BREAK or RETURN exits (i.e., all branches loop back). This ensures that if-elif-else chains inside loops are generated as structured if statements, not as standalone expression statements.

#### Scenario: CONTINUE-role condition block with if-elif-else
- **WHEN** a for loop body block has role=CONTINUE with meaningful instructions AND is the condition_block of an IfRegion with no BREAK/RETURN exits
- **THEN** the IfRegion SHALL be generated as a full if-elif-else AST node, not as standalone expression + continue

#### Scenario: CONTINUE-role condition block with break/return (no regression)
- **WHEN** a for loop body block has role=CONTINUE with meaningful instructions AND is the condition_block of an IfRegion that contains BREAK or RETURN exits
- **THEN** the block SHALL be processed by the existing CONTINUE handler (appended to body_blocks_no_header), preserving the conditional break/continue/return generation path

### Requirement: Correct statement generation for LOOP_BODY blocks inside IfRegion
The system SHALL generate correct `Assign` AST nodes (not `Expr(Assign(...))`) for LOOP_BODY blocks that are part of an IfRegion's then/else blocks. When `_process_if_blocks` is called with a non-None `region` parameter and encounters a LOOP_BODY block with effective instructions, it SHALL use `_build_effective_stmts` instead of falling through to `_generate_block_statements`.

#### Scenario: LOOP_BODY block with assignment inside if-elif-else
- **WHEN** a LOOP_BODY block containing `a = item * 2` is processed as part of an IfRegion's then/else blocks
- **THEN** the block SHALL generate an `Assign` AST node, not `Expr(Assign(...))`

#### Scenario: LOOP_BODY block with conditional break (no regression)
- **WHEN** a LOOP_BODY block is processed as a standalone block (region=None) and `_try_generate_conditional_break` succeeds
- **THEN** the block SHALL generate a conditional break/continue AST node as before

## MODIFIED Requirements

### Requirement: No regressions from n17 fix
The fix SHALL NOT increase the total number of test failures. The current baseline is 77 failed / 1730 passed. The fix should reduce failures (by fixing n17 tests) without introducing new failures, particularly in break/continue/return patterns in loops (if60ifelsebreak, fl03forbreak, fl13forbreakelse, fl16forbreakcontinue, fl19forreturn, for07_break, for09_break_continue, for20_complex_body).

## REMOVED Requirements
(None)
