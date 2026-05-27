# Tasks

- [ ] Task 1: Apply Fix 1 — pre_handler_blocks outer branch check in region_analyzer.py
  - [ ] 1.1: In `_identify_try_except_regions`, after the BEFORE_WITH check and before `pre_handler_blocks.append(block)`, add a check: if `block.start_offset < try_start_for_blocks` AND the block has any successor with `succ.start_offset >= try_end_for_blocks` and `succ != handler_entry_block`, then `continue` (skip this block)
  - [ ] 1.2: Verify the n35 test shows improvement (if-condition block no longer claimed by TryExceptRegion)

- [ ] Task 2: Apply Fix 2 — exception table merge guard in region_analyzer.py
  - [ ] 2.1: In `_parse_exception_table`'s merge loop, before the `existing['try_start'] = min(...)` line, add: if `entry['try_start'] >= existing['handler_start']`, check whether the handler block's instructions are already within the existing try range. If NOT, `continue` (skip this entry). If the handler block cannot be found, also `continue`
  - [ ] 2.2: Verify n35 test passes and te28 (if > try/except) does not regress

- [ ] Task 3: Apply Fix 3 — BACKWARD_CONDITIONAL_JUMP_OPS in _detect_break_continue
  - [ ] 3.1: In `_detect_break_continue`, change the backedge detection condition from `i.opname.startswith('JUMP_BACKWARD')` to `i.opname.startswith('JUMP_BACKWARD') or i.opname in BACKWARD_CONDITIONAL_JUMP_OPS`
  - [ ] 3.2: Verify no regressions in for_loop and while_loop tests

- [ ] Task 4: Apply Fix 4 — LoopRegion in _check_elif_chain
  - [ ] 4.1: In `_check_elif_chain`, add `elif isinstance(existing, LoopRegion): pass` alongside the existing IfRegion/TernaryRegion/TryExceptRegion checks
  - [ ] 4.2: Verify no regressions in if_region tests

- [ ] Task 5: Apply Fix 5 — IfRegion child in loop body generation in region_ast_generator.py
  - [ ] 5.1: In the loop body generation code (around line 2497), before `body_blocks_no_header.append(block)`, check if the block is the condition_block of a child IfRegion. If so, and the IfRegion has no exit paths (no break/return in content blocks), generate the IfRegion as a statement instead of appending the block
  - [ ] 5.2: Verify n35 test passes with correct output

- [ ] Task 6: Run full regression test suite
  - [ ] 6.1: Run full exhaustive test suite: `python -m pytest tests/exhaustive/basic/ tests/exhaustive/if_region/ tests/exhaustive/for_loop/ tests/exhaustive/while_loop/ tests/exhaustive/try_except/ tests/exhaustive/with_region/ tests/exhaustive/match_region/ tests/exhaustive/boolop/ tests/exhaustive/ternary/ tests/exhaustive/nested/ --tb=no -q`
  - [ ] 6.2: Compare failure count against baseline (77f/1730p). If regressions exist, investigate and fix or revert
  - [ ] 6.3: Run n35-specific tests to confirm fix: `python -m pytest tests/exhaustive/nested/test_n35deepnested_a_b_indexerror.py tests/exhaustive/nested/test_n35deepnested_n_m_stopiteration.py tests/exhaustive/nested/test_n35deepnested_x_y_valueerror.py -v`

# Task Dependencies
- Task 1 and Task 2 are the core fixes for n35; both are needed together
- Task 3 and Task 4 are independent fixes found in the same investigation
- Task 5 depends on Tasks 1-4 (needs correct region structure to generate proper AST)
- Task 6 depends on all other tasks being complete
