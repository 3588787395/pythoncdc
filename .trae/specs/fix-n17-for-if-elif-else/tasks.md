# Tasks

- [ ] Task 1: Add LoopRegion to allowed types in `_check_elif_chain` (region_analyzer.py)
  - [ ] 1.1: Add `elif isinstance(existing, LoopRegion): pass` to the type check in `_check_elif_chain` at ~L9012 (before the `else: return None`)
  - [ ] 1.2: Verify that the outer IfRegion for n17 becomes IF_ELIF_CHAIN after this change
  - [ ] 1.3: Run n17 tests to confirm partial improvement (elif chain detected but AST still incorrect)

- [ ] Task 2: Add targeted IfRegion generation in `_loop_dispatch_block` (region_ast_generator.py)
  - [ ] 2.1: In the CONTINUE handler (after meaningful instructions check, before appending to body_blocks_no_header), add a check: if the block is the condition_block of an IfRegion that is a child of the current LoopRegion AND the IfRegion contains no blocks with BREAK/PURE_BREAK/RETURN role, generate the IfRegion directly
  - [ ] 2.2: The check must verify: (a) `entry_region = self.region_analyzer.get_entry_region_for_block(block)` is an IfRegion, (b) `entry_region.condition_block == block`, (c) block not in generated_blocks, (d) no block in entry_region.blocks has role BREAK/PURE_BREAK, (e) no block in entry_region.blocks contains RETURN_VALUE/RETURN_CONST instructions that exit the loop
  - [ ] 2.3: Generate the IfRegion using `_generate_region(entry_region)`, mark all blocks as generated, add to _generated_regions
  - [ ] 2.4: Run n17 tests to confirm if-elif-else structure is generated

- [ ] Task 3: Add effective instructions handling for LOOP_BODY blocks in `_process_if_blocks` (region_ast_generator.py)
  - [ ] 3.1: In `_process_if_blocks`, after the LOOP_BODY cond_break check (~L5282-5284), add: when `region is not None` (block is part of an IfRegion's then/else), check for effective instructions and use `_build_effective_stmts` instead of falling through to `_generate_block_statements`
  - [ ] 3.2: The guard condition: `if region is not None and role == BlockRole.LOOP_BODY:` then check effective instructions
  - [ ] 3.3: Run n17 tests to confirm assignments are generated correctly (Assign nodes, not Expr(Assign))

- [ ] Task 4: Run targeted regression tests
  - [ ] 4.1: Run n17 tests: `python -m pytest tests/exhaustive/nested/test_n17for_if_elif_else_a_b_c.py tests/exhaustive/nested/test_n17for_if_elif_else_n_m_x.py -v`
  - [ ] 4.2: Run for_loop tests: `python -m pytest tests/exhaustive/for_loop/ -q --tb=no`
  - [ ] 4.3: Run if_region tests with break/continue patterns: `python -m pytest tests/exhaustive/if_region/ -q --tb=no -k "break or continue or return"`
  - [ ] 4.4: Run nested tests: `python -m pytest tests/exhaustive/nested/ -q --tb=no`

- [ ] Task 5: Full regression test
  - [ ] 5.1: Run all 10 region test suites: `python -m pytest tests/exhaustive/basic/ tests/exhaustive/if_region/ tests/exhaustive/for_loop/ tests/exhaustive/while_loop/ tests/exhaustive/try_except/ tests/exhaustive/with_region/ tests/exhaustive/match_region/ tests/exhaustive/boolop/ tests/exhaustive/ternary/ tests/exhaustive/nested/ -q --tb=no`
  - [ ] 5.2: Verify total failures ≤ 77 (baseline) — ideally 72 or fewer (5 n17 tests fixed)
  - [ ] 5.3: If regressions found, identify and fix before proceeding

# Task Dependencies
- Task 1 must be done first (elif chain detection is prerequisite for correct IfRegion classification)
- Task 2 depends on Task 1 (needs IF_ELIF_CHAIN classification to work correctly, though the check doesn't require it)
- Task 3 can be done in parallel with Task 2 (independent fix for different code path)
- Task 4 depends on Tasks 1-3
- Task 5 depends on Task 4
