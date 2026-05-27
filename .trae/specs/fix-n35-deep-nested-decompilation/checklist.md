# Fix n35 Deep-Nested Decompilation Verification Checklist

## Fix 1: pre_handler_blocks outer branch check
- [ ] Block before try_start with successors outside try range is skipped in pre_handler_blocks
- [ ] n35 test: if-condition block (block 0) is NOT in try_blocks after the fix

## Fix 2: exception table merge guard
- [ ] Merge step skips entries where try_start >= handler_start AND handler is NOT already in existing try range
- [ ] n35 test: try_end is NOT extended past handler entry block
- [ ] te28 test: handler IS already in try range, so merge correctly extends try_end (no regression)

## Fix 3: BACKWARD_CONDITIONAL_JUMP_OPS in backedge detection
- [ ] Conditional backward jumps are recognized as loop backedges
- [ ] for_loop tests: no regressions
- [ ] while_loop tests: no regressions

## Fix 4: LoopRegion in elif chain
- [ ] _check_elif_chain allows LoopRegion as valid existing region type
- [ ] if_region tests: no regressions

## Fix 5: IfRegion child in loop body
- [ ] IfRegion with no exits is generated as statement in loop body
- [ ] n35 test: decompiled output contains `if a > 0:` before the for loop

## Full regression
- [ ] n35 IndexError test passes (21 instructions match)
- [ ] n35 StopIteration test passes
- [ ] n35 ValueError test passes
- [ ] Full exhaustive test suite failure count <= 77 (baseline)
- [ ] No new test failures compared to baseline
