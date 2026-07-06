## Why

Current tests cover the 6×8 nesting matrix (if/for/while/try/with/match as outer × 8 inner types) but leave critical gaps: AssertRegion is never tested in any nesting context, expression-level regions (BoolOp/Ternary) are only tested as inner — never verified as outer regions — and no test proves that each region's generation code operates independently of its parent's type. Without systematic decoupling proof, a bug in `_generate_try` could silently break `_generate_match` when match appears inside try, and nobody would notice until a real-world user hits it.

## What Changes

- Add a new test suite `tests/control_flow_matrix/test_region_decoupling.py` that systematically proves region generation code is decoupled
- Cover the 6 missing assert-as-inner combinations: if>assert, for>assert, while>assert, try>assert, with>assert, match>assert
- Cover the 2 missing expression-level outer combinations: boolop>ternary, ternary>boolop
- Add "same output regardless of parent" decoupling tests: for each inner region type, verify the decompiled AST subtree is structurally identical whether the parent is if/for/while/try/with/match
- Add "reverse nesting" tests: for each A>B pair already tested, also test B>A (where semantically valid)

## Capabilities

### New Capabilities
- `region-decoupling-tests`: Systematic test suite proving each region's decompilation is independent of its parent/child region type, covering all semantically valid nesting combinations including previously missing assert-inside-structural and expression-level-outer patterns

### Modified Capabilities

## Impact

- New test file: `tests/control_flow_matrix/test_region_decoupling.py` (~50-80 test classes)
- No changes to production code — this is a pure test-addition change
- Test infrastructure: `tests/control_flow_matrix/base.py` already provides `ControlFlowTestCase` base class with `decompile()`, `verify_syntax()`, `find_node()` helpers
