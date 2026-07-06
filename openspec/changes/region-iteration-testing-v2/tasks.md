## 1. Infrastructure Setup

- [x] 1.1 Create `tests/iteration/` directory structure with subdirs for 8 region types: IF, WHILE_LOOP, FOR_LOOP, TRY_EXCEPT, WITH, MATCH, BOOL_OP, TERNARY
- [x] 1.2 Create `tools/round_driver.py` with round state management (collecting/fixing/complete), bug threshold check, and round progression logic
- [x] 1.3 Implement C-class detection helper: compile two source strings, compare bytecode objects, return True if identical

## 2. Test Generators

- [x] 2.1 Create IF region test generator: elif+BoolOp, elif+chain-cmp, elif+ternary, nested if+elif, multi-elif, elif in loop, elif in try
- [x] 2.2 Create WHILE_LOOP region test generator: break/continue, else clause, nested while, while+try, while+match, conditional breaks
- [x] 2.3 Create FOR_LOOP region test generator: else clause, nested for, for+match, for+try, for+break/continue, for+elif interactions
- [x] 2.4 Create TRY_EXCEPT region test generator: multi-except, else clause, finally, nested try, try+loop, try+match, try+with
- [x] 2.5 Create WITH region test generator: multi-with, as-var, with+try, with+loop, with+match, nested with
- [x] 2.6 Create MATCH region test generator: wildcard, guard, class pattern, sequence pattern, mapping pattern, nested match, match in loop/try
- [x] 2.7 Create BOOL_OP region test generator: and+elif, or+elif, chain-cmp+elif, and+or mixing, BoolOp in ternary, BoolOp in loop conditions
- [x] 2.8 Create TERNARY region test generator: nested ternary, ternary in conditions, ternary+elif, ternary in loop, ternary+BoolOp

## 3. Bug Collection and Verification

- [x] 3.1 Implement bug detection: decompile source, compare with expected structure, identify semantic differences (missing elif, wrong condition, duplicated statements, structural errors)
- [x] 3.2 Implement bug report format: bug ID, source pattern, expected output, actual output, C-class status, fix status
- [x] 3.3 Implement round STATUS.md writer: bug count, fix count, round state, bug descriptions

## 4. IF Region Iteration (20 rounds)

- [ ] 4.1 IF round 1-5: Basic elif+BoolOp patterns, elif+chain-cmp, nested if+elif
- [ ] 4.2 IF round 6-10: Complex multi-elif, elif in nested structures, elif+ternary interactions
- [ ] 4.3 IF round 11-15: Edge cases: elif+for/while, elif+try/with, deep nesting with elif
- [ ] 4.4 IF round 16-20: Combined stress patterns, regression verification, remaining edge cases

## 5. WHILE_LOOP Region Iteration (20 rounds)

- [ ] 5.1 WHILE round 1-5: break/continue patterns, else clause, nested while
- [ ] 5.2 WHILE round 6-10: while+try, while+match, conditional break/continue with elif
- [ ] 5.3 WHILE round 11-15: while True patterns, while+BoolOp condition, while+ternary
- [ ] 5.4 WHILE round 16-20: Combined patterns, deep nesting, regression verification

## 6. FOR_LOOP Region Iteration (20 rounds)

- [ ] 6.1 FOR round 1-5: else clause, nested for, for+break/continue
- [ ] 6.2 FOR round 6-10: for+match, for+try, for+elif interactions
- [ ] 6.3 FOR round 11-15: for+BoolOp, for+ternary, for+with nested
- [ ] 6.4 FOR round 16-20: Combined patterns, deep nesting, regression verification

## 7. TRY_EXCEPT Region Iteration (20 rounds)

- [ ] 7.1 TRY round 1-5: multi-except, else clause, finally clause
- [ ] 7.2 TRY round 6-10: nested try, try+loop, try+match
- [ ] 7.3 TRY round 11-15: try+with, try+elif, exception types in conditions
- [ ] 7.4 TRY round 16-20: Combined patterns, deep nesting, regression verification

## 8. WITH Region Iteration (20 rounds)

- [ ] 8.1 WITH round 1-5: multi-with, as-var, with+try
- [ ] 8.2 WITH round 6-10: with+loop, with+match, nested with
- [ ] 8.3 WITH round 11-15: with+elif, with+ternary, with+BoolOp
- [ ] 8.4 WITH round 16-20: Combined patterns, deep nesting, regression verification

## 9. MATCH Region Iteration (20 rounds)

- [ ] 9.1 MATCH round 1-5: wildcard, guard, class pattern, sequence pattern
- [ ] 9.2 MATCH round 6-10: mapping pattern, nested match, match in loop
- [ ] 9.3 MATCH round 11-15: match+try, match+elif interactions, match+BoolOp
- [ ] 9.4 MATCH round 16-20: Combined patterns, deep nesting, regression verification

## 10. BOOL_OP Region Iteration (20 rounds)

- [ ] 10.1 BOOL_OP round 1-5: and+elif, or+elif, chain-cmp+elif patterns
- [ ] 10.2 BOOL_OP round 6-10: and+or mixing, BoolOp in ternary, BoolOp+else
- [ ] 10.3 BOOL_OP round 11-15: BoolOp in loop conditions, nested BoolOp, chain-cmp+and+or
- [ ] 10.4 BOOL_OP round 16-20: Combined patterns, C-class identification, regression verification

## 11. TERNARY Region Iteration (20 rounds)

- [ ] 11.1 TERNARY round 1-5: nested ternary, ternary in if conditions, ternary+elif
- [ ] 11.2 TERNARY round 6-10: ternary in loop, ternary+BoolOp, ternary+chain-cmp
- [ ] 11.3 TERNARY round 11-15: ternary in match, ternary in try, deeply nested ternary
- [ ] 11.4 TERNARY round 16-20: Combined patterns, C-class identification, regression verification

## 12. Final Verification

- [ ] 12.1 Run full test suite (pytest tests/) and verify no regressions
- [ ] 12.2 Verify all 160 round directories have STATUS.md with "complete" state
- [ ] 12.3 Summarize all bugs found and fixed across 8 region types × 20 rounds
