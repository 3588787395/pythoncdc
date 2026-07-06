## Context

The Python bytecode decompiler (`pythoncdc`) uses a region-based approach: CFG → hierarchical regions via dominator + back-edge detection → AST generation. Prior work fixed 14+ bugs across region identification and AST generation, but complex overlapping patterns remain broken:

1. **BoolOp+Ternary overlap**: `z = a and (b if c else d)` decompiles incorrectly because BoolOpRegion and IfRegion compete for the same blocks with wrong merge/parent assignment
2. **Match-in-loop control flow**: `break`/`continue` inside match cases within for/while loops are lost during decompilation
3. **2 test regressions** (C06, XP04) introduced during the BoolOp+Ternary fix

Current testing is ad-hoc — bugs are found one at a time without systematic coverage per region type.

## Goals / Non-Goals

**Goals:**
- Fix all 3 remaining bug categories (BoolOp+Ternary, match-in-loop, regressions)
- Establish a systematic iteration testing protocol: 8 region types × 20 rounds each
- Each round requires ≥10 errors found before any fix is applied (round doesn't count otherwise)
- All test files organized in `D:\Temp\opencode\iteration_tests\<region>\<round>\`
- Zero regressions across all existing test suites (327+ control_flow_matrix tests, fuzz tests)

**Non-Goals:**
- Fixing Category C (match vs if-elif bytecode equivalence) — fundamental CPython limitation
- Fixing Category D (while True `return None` vs `break` in functions) — genuinely indistinguishable
- Adding new region types or changing the core region reduction algorithm
- Performance optimization

## Decisions

### Decision 1: BoolOp+Ternary fix strategy
**Choice**: Extend BoolOp chain detection to recognize ternary headers as nested expressions rather than chain operands.

**Rationale**: When a `FORWARD_CONDITIONAL_JUMP_OPS` block in a short-circuit chain has a different jump target than the short-circuit merge point, it indicates a ternary expression nested inside the BoolOp, not another BoolOp operand. The fix involves:
1. Correct `merge_block` calculation: use the short-circuit jump target (not the last chain block's target) when they differ
2. Include ternary branch blocks in the BoolOpRegion's block set
3. Detect nested ternary during expression building via `_try_build_nested_ternary_in_boolop`
4. Skip fall-through block addition when last chain block is a ternary header
5. Fix `is_condition_context` when chain starts with SHORT_CIRCUIT_JUMP_OPS but extends to FORWARD_CONDITIONAL_JUMP_OPS
6. Prevent IfRegion from claiming BoolOpRegion as child when they share the same entry block
7. Parenthesize IfExp operands in BoolOp code generation

**Alternatives considered**:
- Stop BoolOp chain at ternary boundary → loses the `and` relationship entirely, falls through to IfRegion which generates wrong code
- Separate TernaryRegion first then compose → requires architectural changes to allow region nesting

### Decision 2: Match-in-loop fix strategy
**Choice**: During AST generation for match cases inside loops, preserve break/continue/return by checking loop depth and generating appropriate control flow statements instead of dropping them.

**Rationale**: The current match case generation treats all case bodies as regular statement lists, losing loop control flow. By checking `self._loop_depth` during match case body generation, we can correctly emit break/continue statements.

### Decision 3: Iteration testing framework
**Choice**: Python script per round that generates pattern-specific test cases, runs them, counts errors, and writes results to a dedicated directory.

**Structure**: `D:\Temp\opencode\iteration_tests\<region_type>\<round_N>\test_round.py` with results in `results.txt`.

**8 Region types**:
1. `if-region` — IfRegion (if/elif/else)
2. `loop-region` — LoopRegion (for/while, for-else, while-else)
3. `try-region` — TryExceptRegion (try/except/else/finally)
4. `with-region` — WithRegion (with/as)
5. `match-region` — MatchRegion (match/case)
6. `boolop-region` — BoolOpRegion (and/or chains)
7. `ternary-region` — TernaryRegion (x if cond else y)
8. `assert-region` — AssertRegion (assert statements)

**Round protocol**:
1. Generate 50-100 test patterns for the region type (increasingly complex per round)
2. Compile each pattern → decompile → check syntax + semantics
3. Collect all errors; if <10, expand patterns and re-run (doesn't count as a round)
4. If ≥10 errors, fix ALL errors in source code
5. Re-run all tests to verify zero regressions
6. Record round results
7. Advance to next round

### Decision 4: is_condition_context fix
**Choice**: When a BoolOp chain starts with `SHORT_CIRCUIT_JUMP_OPS` and is extended with `FORWARD_CONDITIONAL_JUMP_OPS`, it is NOT a condition context — it's an assignment context where the ternary is nested inside the BoolOp.

**Rationale**: `is_condition_context` was incorrectly set to `True` because the last block had `POP_JUMP_IF_FALSE`, but the chain originates from a short-circuit assignment pattern (`z = a and ...`), not a conditional (`if a and ...:`).

## Risks / Trade-offs

- **[Risk]** BoolOp+Ternary fix changes region block sets, potentially affecting overlap resolution with other region types → **Mitigation**: Run full regression suite after each fix; the `add_child` guard prevents parent-child conflict for same-entry regions
- **[Risk]** Match-in-loop fix may not cover all edge cases (e.g., return vs break disambiguation in while-True) → **Mitigation**: Acknowledge Category D as known limitation; only fix unambiguous break/continue in for loops
- **[Risk]** Iteration testing may find very few errors in later rounds → **Mitigation**: Rounds with <10 errors don't count; move to next region type after 3 consecutive empty rounds
- **[Risk]** Parenthesization of IfExp in BoolOp may over-parenthesize in simple cases → **Mitigation**: Only parenthesize when IfExp is a value inside BoolOp, which is always necessary due to Python precedence rules
