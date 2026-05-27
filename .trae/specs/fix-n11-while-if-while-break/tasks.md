# Tasks

- [x] Task 1: Remove BINARY_OP from has_body_stmt check in _check_elif_chain
  - [x] 1.1: In `_check_elif_chain` (region_analyzer.py ~line 8726), remove `'BINARY_OP'` from the `has_body_stmt` check's instruction name tuple
  - [x] 1.2: Verify the fix creates IfRegion:14 for the n11 pattern by running a debug script

- [x] Task 2: Add _is_structural_entry check in _process_if_blocks
  - [x] 2.1: Before the CONTINUE role check, detect if the block is the entry of a nested LoopRegion/TryExceptRegion/WithRegion/MatchRegion
  - [x] 2.2: Skip CONTINUE role handling when _is_structural_entry is True

- [x] Task 3: Process natural back edge before other body blocks in _loop_generate_body
  - [x] 3.1: Add early natural back edge processing before the body_blocks iteration loop
  - [x] 3.2: Verify the fix generates `y += 1` correctly inside the inner while loop

- [x] Task 4: Verify n11 test fixes
  - [x] 4.1: Run `python -m pytest tests/exhaustive/nested/test_n11while_if_while_break_a_b.py -v --tb=short` and confirm it passes
  - [x] 4.2: Run `python -m pytest tests/exhaustive/nested/test_n11while_if_while_break_n_m.py -v --tb=short` and confirm it passes

- [x] Task 5: Run full regression suite
  - [x] 5.1: Run full 10-region regression: `python -m pytest tests/exhaustive/basic/ tests/exhaustive/if_region/ tests/exhaustive/for_loop/ tests/exhaustive/while_loop/ tests/exhaustive/try_except/ tests/exhaustive/with_region/ tests/exhaustive/match_region/ tests/exhaustive/boolop/ tests/exhaustive/ternary/ tests/exhaustive/nested/ --tb=no -q`
  - [x] 5.2: Verify total failures do not increase beyond current baseline (76f/1734p vs baseline 77f/1730p — improved)

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 4
