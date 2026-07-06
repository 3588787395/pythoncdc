## 1. Fix Test Regressions

- [ ] 1.1 Investigate C06 NestedIf test failure — run the failing test, examine expected vs actual output
- [ ] 1.2 Fix C06 regression caused by BoolOpRegion parent assignment change
- [ ] 1.3 Investigate XP04 BoolOpInIf test failure — run the failing test, examine expected vs actual output
- [ ] 1.4 Fix XP04 regression caused by BoolOp/Ternary priority or code generation changes
- [ ] 1.5 Run full test suite to confirm 0 failures, 327 passed, 11 skipped

## 2. BoolOp+Ternary Overlap Fix Completion

- [ ] 2.1 Fix `if a and (b if c else d): pass` decompilation — currently produces syntax error with `return c and b`
- [ ] 2.2 Fix `z = (a if b else c) and d` — currently decompiles as just `a if b else c` (missing `and d`)
- [ ] 2.3 Fix `z = (a if b else c) or d` — currently decompiles as just `a if b else c` (missing `or d`)
- [ ] 2.4 Fix `z = a or b if c else d` — decompiles as `z = a if c else d` (missing `or b`)
- [ ] 2.5 Verify BoolOp+Ternary fixes don't regress existing `z = a and b`, `z = a and b and c`, `z = a if b else c` tests
- [ ] 2.6 Run full test suite after BoolOp+Ternary completion

## 3. Match-in-Loop Control Flow Fix

- [ ] 3.1 Analyze bytecode pattern for `for i in range(5): match i: case 1: break; case _: pass`
- [ ] 3.2 Fix match case body generation to preserve break/continue when inside a loop (check `_loop_depth`)
- [ ] 3.3 Fix match case body generation to preserve return statements
- [ ] 3.4 Test: `for i in range(5):\n    match i%3:\n        case 0:\n            print('zero')\n        case 1:\n            continue\n        case _:\n            break` decompiles correctly
- [ ] 3.5 Run full test suite after match-in-loop fix

## 4. Iteration Testing Framework Setup

- [ ] 4.1 Create `D:\Temp\opencode\iteration_tests\` base directory
- [ ] 4.2 Create iteration driver script template that: generates patterns, compiles, decompiles, checks syntax+semantics, counts errors, writes results
- [ ] 4.3 Create pattern generators for each of the 8 region types (if, loop, try, with, match, boolop, ternary, assert)
- [ ] 4.4 Verify the driver works end-to-end on a simple test case

## 5. Iteration Testing: BoolOp Region (20 rounds)

- [ ] 5.1 Run rounds 1-5 for boolop-region (simple and/or chains, 2-4 operands, mixed and/or)
- [ ] 5.2 Run rounds 6-10 for boolop-region (nested boolop, boolop in assignment, boolop in condition)
- [ ] 5.3 Run rounds 11-15 for boolop-region (boolop+ternary overlap, boolop in loop condition, boolop in match guard)
- [ ] 5.4 Run rounds 16-20 for boolop-region (complex mixed patterns, edge cases with short-circuit semantics)
- [ ] 5.5 Record all results; if <10 errors in 3 consecutive rounds, move to next region

## 6. Iteration Testing: Ternary Region (20 rounds)

- [ ] 6.1 Run rounds 1-5 for ternary-region (simple ternary, nested ternary, ternary in assignment)
- [ ] 6.2 Run rounds 6-10 for ternary-region (ternary in loop, ternary in if, ternary in match)
- [ ] 6.3 Run rounds 11-15 for ternary-region (ternary with complex expressions, chained ternary, ternary+boolop)
- [ ] 6.4 Run rounds 16-20 for ternary-region (edge cases, walrus in ternary, ternary in comprehension)
- [ ] 6.5 Record all results

## 7. Iteration Testing: If Region (20 rounds)

- [ ] 7.1 Run rounds 1-5 for if-region (simple if, if-else, elif chains)
- [ ] 7.2 Run rounds 6-10 for if-region (nested if, if in loop, if in try)
- [ ] 7.3 Run rounds 11-15 for if-region (if-else with return, if with assignment, complex elif)
- [ ] 7.4 Run rounds 16-20 for if-region (deep nesting, if+match, if+with combinations)
- [ ] 7.5 Record all results

## 8. Iteration Testing: Loop Region (20 rounds)

- [ ] 8.1 Run rounds 1-5 for loop-region (simple for, while, for-else, while-else)
- [ ] 8.2 Run rounds 6-10 for loop-region (nested loops, break/continue, loop with try)
- [ ] 8.3 Run rounds 11-15 for loop-region (for with match, while-True, enumerate/unpack)
- [ ] 8.4 Run rounds 16-20 for loop-region (complex loop+control flow, loop in function with return)
- [ ] 8.5 Record all results

## 9. Iteration Testing: Try Region (20 rounds)

- [ ] 9.1 Run rounds 1-5 for try-region (try-except, try-except-else, try-finally)
- [ ] 9.2 Run rounds 6-10 for try-region (nested try, multiple except, try in loop)
- [ ] 9.3 Run rounds 11-15 for try-region (try with match, try with with, re-raise)
- [ ] 9.4 Run rounds 16-20 for try-region (complex exception handling, try-else-finally combinations)
- [ ] 9.5 Record all results

## 10. Iteration Testing: With Region (20 rounds)

- [ ] 10.1 Run rounds 1-5 for with-region (simple with, with-as, multiple with items)
- [ ] 10.2 Run rounds 6-10 for with-region (with in loop, with in if, nested with)
- [ ] 10.3 Run rounds 11-15 for with-region (with+try, with+match, with+boolop)
- [ ] 10.4 Run rounds 16-20 for with-region (complex with patterns, with in function)
- [ ] 10.5 Record all results

## 11. Iteration Testing: Match Region (20 rounds)

- [ ] 11.1 Run rounds 1-5 for match-region (simple match, match with wildcard, match with or-pattern)
- [ ] 11.2 Run rounds 6-10 for match-region (match in loop, match in if, match with guard)
- [ ] 11.3 Run rounds 11-15 for match-region (match+break/continue, match+return, match in try)
- [ ] 11.4 Run rounds 16-20 for match-region (complex match patterns, nested match, match+with)
- [ ] 11.5 Record all results

## 12. Iteration Testing: Assert Region (20 rounds)

- [ ] 12.1 Run rounds 1-5 for assert-region (simple assert, assert with message, assert+boolop)
- [ ] 12.2 Run rounds 6-10 for assert-region (assert in loop, assert in if, assert in function)
- [ ] 12.3 Run rounds 11-15 for assert-region (assert+ternary, assert+comparison, assert in try)
- [ ] 12.4 Run rounds 16-20 for assert-region (complex assert patterns, edge cases)
- [ ] 12.5 Record all results

## 13. Final Validation

- [ ] 13.1 Run full control_flow_matrix test suite (327+ tests) — must be 0 failed
- [ ] 13.2 Run fuzz test suite (6908+ tests) — must be 0 errors
- [ ] 13.3 Run deep fuzz test suite (17304+ tests) — must be 0 syntax errors, 0 semantic errors
- [ ] 13.4 Run edge case tests — must be 0 errors
- [ ] 13.5 Compile summary of all iteration testing results across 8 regions × 20 rounds
