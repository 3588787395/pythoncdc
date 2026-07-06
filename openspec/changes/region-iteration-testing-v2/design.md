## Context

The pythoncdc decompiler converts Python bytecode back to source code using a region-based approach. Region identification (RegionAnalyzer) classifies basic blocks into structural regions (IF, LOOP, TRY, etc.), and AST generation (RegionASTGenerator) converts regions to Python AST nodes. Recent sessions fixed critical bugs in `or+elif`, `and+elif`, `chain-cmp+elif`, and `chain-cmp+or+elif` patterns — all found through ad-hoc testing rather than systematic discovery.

The existing iteration-testing-8x20 change had a simpler protocol without the bug-threshold requirement and without the "collect first, fix after" discipline. This v2 redesign enforces: accumulate ≥10 bugs per round, then fix all, then the round counts.

Key files:
- `core/cfg/region_analyzer.py` (~8300 lines): Region identification
- `core/cfg/region_ast_generator.py` (~14900 lines): AST generation
- `core/cfg/cfg_builder.py`: CFG construction
- `core/cfg/expr_reconstructor.py`: Expression reconstruction

## Goals / Non-Goals

**Goals:**
- Systematically test 8 region types (IF, WHILE_LOOP, FOR_LOOP, TRY_EXCEPT, WITH, MATCH, BOOL_OP, TERNARY) with 20 qualifying rounds each
- Enforce bug-threshold: rounds only count when ≥10 distinct bugs are collected
- Fix bugs only after collection threshold is met (collect-then-fix discipline)
- Create persistent test artifacts in `tests/iteration/<region>/round-NN/`
- Identify C-class patterns (identical bytecode) and exclude them from bug counts
- Complete all 160 rounds without stopping early

**Non-Goals:**
- Performance optimization of the decompiler
- Refactoring region identification algorithm (only fix bugs found)
- Adding new region types beyond the 8 specified
- Testing non-region features (imports, classes, comprehensions)

## Decisions

### D1: Round driver as Python script, not pytest framework
**Choice**: Single `tools/round_driver.py` script that orchestrates test generation, bug collection, fix application, and round progression.
**Rationale**: The round protocol (collect ≥10 bugs, fix all, count round) doesn't fit pytest's test-pass/fail model. A custom driver gives precise control over round state and bug accumulation.
**Alternative**: pytest with custom fixtures — rejected because round state management would be awkward in pytest's discover-and-run model.

### D2: Test generators produce source strings, not bytecode
**Choice**: Each region-type generator produces Python source code strings. The decompiler compiles → decompiles → compares.
**Rationale**: Testing at source level is what the decompiler must handle. Compiling to bytecode is Python's job; decompiling back is ours.
**Alternative**: Direct bytecode manipulation — rejected because it doesn't test the real input path and is fragile across Python versions.

### D3: Bug = decompilation output differs from expected structure
**Choice**: A bug is defined as: decompiled output is syntactically different from the original in a way that changes semantics (not just formatting). Specifically: missing elif, wrong condition, wrong body, duplicated statements, or structural nesting errors.
**Rationale**: Semantic equivalence is the correctness criterion. Formatting differences (e.g., extra parentheses) are not bugs.
**Alternative**: AST-level comparison — could be added later but string comparison with normalization is simpler and catches real issues.

### D4: C-class detection via bytecode comparison
**Choice**: When a pattern is flagged as potentially wrong, compile it and compare bytecode with the original. If bytecodes are identical, the pattern is C-class (decompiler cannot distinguish).
**Rationale**: This prevents counting "bugs" that are impossible to fix — the decompiler can only recover what the bytecode preserves.
**Alternative**: Manual C-class marking — rejected as error-prone and not scalable.

### D5: Round state persisted in STATUS.md files
**Choice**: Each round directory contains a STATUS.md file tracking: bug count, fix count, round state (collecting/fixing/complete), and bug descriptions.
**Rationale**: File-based state survives process restarts and is human-readable.
**Alternative**: Database — overkill for this use case.

### D6: Test generation uses targeted pattern research
**Choice**: Before generating tests for a round, analyze the relevant code paths in region_analyzer.py and region_ast_generator.py to identify potential weak points, then construct tests targeting those areas.
**Rationale**: Random testing finds shallow bugs; targeted testing finds deep structural issues. The codebase analysis approach maximizes bug discovery per round.

## Risks / Trade-offs

- [Risk: Some region types may have very few bugs left] → Continue generating increasingly complex interaction patterns; rounds that can't reach 10 bugs after extensive testing may be marked as "stable" after exhausting the pattern space
- [Risk: Bug fixes in one region type may break another] → Run full test suite after each fix; maintain a regression test set
- [Risk: 160 rounds is a lot of manual work] → Automate test generation and verification as much as possible; the round driver handles mechanical steps, human focuses on diagnosis and fix
- [Risk: C-class patterns may be over-identified, hiding real bugs] → Only mark as C-class when bytecodes are truly identical; when in doubt, treat as a real bug
