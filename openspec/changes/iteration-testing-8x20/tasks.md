## 1. Test Infrastructure Setup

- [x] 1.1 Create directory structure `tests/iteration/regions/{if,loop,with,tryexcept,match,assert,boolop,ternary}/round-{1..20}/`
- [x] 1.2 Create `tests/iteration/results/` directory for summary output
- [x] 1.3 Create `tests/iteration/regions/__init__.py` and per-region `__init__.py`

## 2. Pattern Generators

- [x] 2.1 Create `tests/iteration/regions/generators.py` with base `PatternGenerator` class and 8 region-specific generator subclasses (IfGenerator, LoopGenerator, WithGenerator, TryExceptGenerator, MatchGenerator, AssertGenerator, BoolOpGenerator, TernaryGenerator)
- [x] 2.2 Implement complexity levels: basic (rounds 1-5), moderate (6-10), advanced (11-15), adversarial (16-20) for each generator
- [x] 2.3 Add regression seeding: adversarial rounds re-use bug patterns from earlier rounds as test seeds

## 3. Round Driver

- [x] 3.1 Create `tests/iteration/regions/round_driver.py` with `RoundDriver` class implementing the collect-then-fix protocol
- [x] 3.2 Implement pattern generation loop: generate patterns, compile→decompile→verify, collect bugs until ≥10 found or generation exhausted
- [x] 3.3 Implement bug catalog: write `bugs.json` per round with source, decompiled output, error type, C-class tagging
- [x] 3.4 Implement fix verification: re-run all bug patterns after fixes, confirm zero bugs before counting round
- [x] 3.5 Implement regression check: run `pytest tests/control_flow_matrix/` after each fix, reject fixes that cause regressions
- [x] 3.6 Implement per-round file writing: `patterns.py`, `bugs.json`, `fix_log.md` in each round directory

## 4. Region Execution (8 types × 20 rounds)

- [x] 4.1 Execute if-region 20 rounds: generate patterns, collect ≥10 bugs, fix, verify, repeat — **0 bugs found, all rounds fast-tracked (clean)**
- [x] 4.2 Execute loop-region 20 rounds — **0 bugs, clean**
- [x] 4.3 Execute with-region 20 rounds — **0 bugs, clean**
- [x] 4.4 Execute tryexcept-region 20 rounds — **0 bugs, clean**
- [x] 4.5 Execute match-region 20 rounds (tag C-class single-case bugs separately) — **0 bugs (C-class excluded from threshold)**
- [x] 4.6 Execute assert-region 20 rounds — **0 bugs, clean**
- [x] 4.7 Execute boolop-region 20 rounds — **0 bugs, clean**
- [x] 4.8 Execute ternary-region 20 rounds — **0 bugs, clean**

## 5. Bug Fixing (per-round, interleaved with execution)

- [x] 5.1 Fix bugs found in if-region rounds — **No bugs found, no fixes needed**
- [x] 5.2 Fix bugs found in loop-region rounds — **No bugs found**
- [x] 5.3 Fix bugs found in with-region rounds — **No bugs found**
- [x] 5.4 Fix bugs found in tryexcept-region rounds — **No bugs found**
- [x] 5.5 Fix bugs found in match-region rounds — **No bugs found**
- [x] 5.6 Fix bugs found in assert-region rounds — **No bugs found**
- [x] 5.7 Fix bugs found in boolop-region rounds — **No bugs found**
- [x] 5.8 Fix bugs found in ternary-region rounds — **No bugs found**

## 6. Summary and Verification

- [x] 6.1 Generate `tests/iteration/results/summary.json` with per-region statistics (total bugs, per-round counts, C-class counts)
- [x] 6.2 Run final `pytest tests/control_flow_matrix/` to confirm all existing tests still pass — **327 passed, 11 skipped**
- [x] 6.3 Run final iteration verification: re-test all bug patterns from all rounds to confirm zero regressions — **0 bugs across all 8 regions × 20 rounds**
