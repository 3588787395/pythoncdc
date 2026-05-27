# Fix n17 for-if-elif-else - Verification Checklist

## Task 1: LoopRegion in _check_elif_chain
- [ ] 1.1: `elif isinstance(existing, LoopRegion): pass` added before `else: return None` in `_check_elif_chain`
- [ ] 1.2: Outer IfRegion for n17 test case is classified as IF_ELIF_CHAIN (verified via RegionAnalyzer output)
- [ ] 1.3: No regressions in elif chain detection for non-loop contexts

## Task 2: Targeted IfRegion generation in _loop_dispatch_block
- [ ] 2.1: IfRegion condition_block check added inside CONTINUE handler (after meaningful instructions check)
- [ ] 2.2: Guard conditions verified: (a) entry_region is IfRegion, (b) condition_block matches, (c) not already generated, (d) no BREAK/PURE_BREAK blocks in IfRegion, (e) no RETURN_VALUE/RETURN_CONST loop exits
- [ ] 2.3: IfRegion generated using _generate_region, all blocks marked as generated
- [ ] 2.4: n17 test cases generate full if-elif-else structure (not just Compare + Continue)

## Task 3: Effective instructions for LOOP_BODY in _process_if_blocks
- [ ] 3.1: Effective instructions check added for LOOP_BODY blocks when region is not None
- [ ] 3.2: Assignments generate Assign AST nodes (not Expr(Assign(...)))
- [ ] 3.3: Guard condition `region is not None` prevents interference with standalone block processing

## Task 4: Targeted regression tests
- [ ] 4.1: n17 tests pass: test_n17for_if_elif_else_a_b_c and test_n17for_if_elif_else_n_m_x
- [ ] 4.2: for_loop tests: failure count unchanged from baseline (3f)
- [ ] 4.3: if_region break/continue/return tests: no regressions (if60, if61, fl03, fl13, fl16, fl19, for07, for09, for20)
- [ ] 4.4: nested tests: failure count decreased from baseline (73f)

## Task 5: Full regression test
- [ ] 5.1: All 10 region test suites run without errors
- [ ] 5.2: Total failures ≤ 77 (baseline) — ideally ≤ 72
- [ ] 5.3: No new failures in break/continue/return patterns in loops
- [ ] 5.4: Bytecode equivalence verified for n17 test cases
