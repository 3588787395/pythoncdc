## Why

The decompiler's region identification and AST generation still contain bugs that only surface under specific combination patterns (e.g., BoolOp+Ternary overlap, match-in-loop control flow, nested ternary in BoolOp). The current ad-hoc testing approach finds bugs one at a time without systematic coverage. We need a rigorous iteration protocol: for each region type, run 20 rounds where each round requires finding ≥10 errors before fixing, ensuring thorough coverage and no regressions.

## What Changes

- Introduce a structured iteration testing framework with dedicated test directories per region type per round
- Fix the BoolOp+Ternary overlap bug (`z = a and (b if c else d)` decompiles incorrectly)
- Fix match-in-for/while break/continue control flow loss
- Fix the 2 test regressions introduced during BoolOp+Ternary work (C06, XP04)
- Run 20 rounds of iteration testing per region (8 region types × 20 rounds = 160 rounds minimum)
- Each round: generate test patterns → run → collect ≥10 errors → fix all → verify → round complete
- If <10 errors found in a round, the round does not count (must find more patterns)

## Capabilities

### New Capabilities
- `iteration-testing-framework`: Systematic fuzz-and-fix testing framework with per-region, per-round test isolation and error counting
- `boolop-ternary-fix`: Correct decompilation of BoolOp expressions containing nested Ternary/IfExp operands (e.g., `a and (b if c else d)`)
- `match-loop-control-flow`: Correct handling of break/continue/return inside match cases within loops

### Modified Capabilities

## Impact

- `core/cfg/region_analyzer.py`: BoolOp chain detection merge calculation, `_create_boolop_region_from_chain` ternary branch inclusion, `is_condition_context` fix, parent assignment fix
- `core/cfg/region_ast_generator.py`: `_try_build_nested_ternary_in_boolop` helper, `_build_boolop_expression` ternary-aware operand reconstruction, fall-through block skip for nested ternary, `_filter_module_level_returns` recursive filter, BoolOpRegion parent isolation
- `core/cfg/code_generator.py`: BoolOp value parenthesization for IfExp operands
- `tests/`: New iteration test directories and test files under `D:\Temp\opencode\iteration_tests\`
