## Why

The region-based decompiler has persistent bugs in condition/BoolOp/elif/ternary interaction patterns. Recent fixes addressed `or+elif`, `and+elif`, `chain-cmp+elif`, and `chain-cmp+or+elif` — but these were found ad-hoc. A systematic iteration-testing protocol is needed: per region type, generate targeted test patterns, collect ≥10 real bug instances per round, fix all, repeat for 20 rounds. This ensures correctness exhaustively rather than opportunistically.

## What Changes

- **Iteration test infrastructure**: Per-region-type test generators that produce targeted patterns combining the region with other constructs (elif, BoolOp, ternary, nested conditions, loops, try/with, match)
- **Round protocol enforcement**: A round only counts when ≥10 distinct bug instances are collected; fixing them completes the round; <10 bugs means the round doesn't count
- **Dedicated test directories**: `tests/iteration/<region-type>/round-NN/` storing test files per region per round
- **8 region types × 20 rounds = 160 rounds total**: IF, WHILE_LOOP, FOR_LOOP, TRY_EXCEPT, WITH, MATCH, BOOL_OP, TERNARY
- **Bug collection before fix**: Accumulate bug instances in a round's directory, only start fixing once ≥10 are found, fix all at once to complete the round
- **C-class identification**: Patterns producing identical bytecode (indistinguishable by decompiler) are marked and don't count toward the ≥10 threshold

## Capabilities

### New Capabilities
- `iteration-testing-v2`: Systematic per-region-type iteration testing framework with round protocol, bug collection threshold, and dedicated test directories

### Modified Capabilities

## Impact

- `core/cfg/region_ast_generator.py`: Bug fixes from iteration rounds
- `core/cfg/region_analyzer.py`: Region identification fixes
- `tests/iteration/`: New test directory tree (8 region types × up to 20 round subdirs)
- `tools/round_driver.py`: Round execution driver script
