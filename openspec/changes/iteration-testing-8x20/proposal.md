## Why

The region-based decompiler (region_analyzer + region_ast_generator + code_generator) currently passes 327 unit tests but has unknown residual bugs per region type. Prior ad-hoc testing showed tryexcept had ~10% failure rate and match had ~17% failure rate before recent fixes. A systematic iterative fuzz-testing protocol is needed to drive all 8 region types (if, loop, tryexcept, with, match, assert, boolop, ternary) to zero bugs through controlled round-based testing: each round requires collecting ≥10 bug instances before any fixing begins, then fixes all 10+ before the round counts.

## What Changes

- **New iteration testing framework**: Dedicated test directory structure under `tests/iteration/regions/<region-type>/round-<N>/` storing per-round test files, bug catalogs, and fix logs
- **Pattern generators**: Enhanced generators for each of 8 region types producing syntactically valid, semantically diverse Python patterns
- **Round driver**: Orchestrator that for each region type runs 20 rounds; each round generates test patterns until ≥10 bugs are found, records all bug instances, then stops for fixing; after fixes are applied, re-runs to confirm zero bugs before advancing
- **Bug catalog**: JSON per-round catalog capturing source pattern, decompiled output, error type, and fix description
- **Comprehensive reporting**: Summary JSON/Markdown after all 8×20 rounds complete

## Capabilities

### New Capabilities
- `iteration-testing-framework`: Systematic round-based fuzz testing infrastructure for 8 region types with 20 rounds each, per-region per-round file storage, bug cataloging, and fix verification

### Modified Capabilities

## Impact

- `tests/iteration/` directory structure (new files, no existing file changes)
- `core/cfg/region_analyzer.py`, `core/cfg/region_ast_generator.py`, `core/cfg/code_generator.py` will receive bug fixes as bugs are discovered during iteration rounds
- Test infrastructure only; no API changes to the decompiler library itself
