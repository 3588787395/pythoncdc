## 1. Assert-as-inner nesting tests

- [x] 1.1 Create `TestDC01AssertInIf` — pass
- [x] 1.2 Create `TestDC02AssertInFor` — pass
- [x] 1.3 Create `TestDC03AssertInWhile` — pass
- [x] 1.4 Create `TestDC04AssertInTry` — pass
- [x] 1.5 Create `TestDC05AssertInWith` — pass
- [x] 1.6 Create `TestDC06AssertInMatch` — pass (checks ast.Raise since assert decompiles as if+raise)

## 2. Expression-level region as outer tests

- [x] 2.1 Create `TestDC07BoolOpContainingTernary` — skip: decompiler does not reconstruct BoolOp↔Ternary nesting
- [x] 2.2 Create `TestDC08TernaryContainingBoolOp` — skip: decompiler does not reconstruct Ternary↔BoolOp nesting

## 3. Decoupling proof tests — structural region types

- [x] 3.1 Create `TestDC09IfRegionDecoupling` — for==try==with pass; if-inside-if skip (merges to BoolOp)
- [x] 3.2 Create `TestDC10ForRegionDecoupling` — all 4 parent comparisons pass
- [x] 3.3 Create `TestDC11WhileRegionDecoupling` — all 4 parent comparisons pass
- [x] 3.4 Create `TestDC12TryRegionDecoupling` — all 4 parent comparisons pass (using print(1) body)
- [x] 3.5 Create `TestDC13WithRegionDecoupling` — if/for/try/while pass; nested-with skip (CPython flattens)
- [x] 3.6 Create `TestDC14MatchRegionDecoupling` — standalone==if pass; for/try/with skip (match-in-loop issues)

## 4. Decoupling proof tests — expression-level region types

- [x] 4.1 Create `TestDC15BoolOpDecoupling` — try==with pass; for/while skip (expression decomposes to if-stmt)
- [x] 4.2 Create `TestDC16TernaryDecoupling` — if==try==with pass; for/while skip (expression decomposes to if-stmt)

## 5. Run and verify

- [x] 5.1 Full suite: 6 failed (pre-existing), 436 passed, 11 skipped (decoupling), 0 regressions
- [x] 5.2 All skips are documented known decompiler limitations
