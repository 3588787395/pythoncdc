## ADDED Requirements

### Requirement: Round-based iteration protocol
The system SHALL execute a round-based iteration testing protocol with exactly 20 rounds per region type, for 8 region types (if, loop, with, tryexcept, match, assert, boolop, ternary), totaling 160 rounds maximum.

#### Scenario: Round with sufficient bugs
- **WHEN** a round generates test patterns and finds ≥10 bug instances
- **THEN** the round is counted, all bugs are recorded, fixes are applied, and verification confirms zero bugs before advancing

#### Scenario: Round without sufficient bugs
- **WHEN** a round generates test patterns and finds <10 bug instances after exhaustive generation
- **THEN** the round does NOT count toward the 20-round target

#### Scenario: All rounds complete
- **WHEN** 20 valid rounds have been completed for a region type
- **THEN** the system advances to the next region type in order: if → loop → with → tryexcept → match → assert → boolop → ternary

### Requirement: Per-region per-round file storage
The system SHALL create a dedicated directory `tests/iteration/regions/<region-type>/round-<N>/` for each round, containing:
- `patterns.py`: The generated test patterns for that round
- `bugs.json`: Catalog of all bug instances with source, decompiled output, error type
- `fix_log.md`: Description of fixes applied in that round

#### Scenario: Round directory creation
- **WHEN** a new round begins for region type "if" round 3
- **THEN** directory `tests/iteration/regions/if/round-3/` is created with empty `patterns.py`, `bugs.json`, and `fix_log.md`

#### Scenario: Bug catalog content
- **WHEN** a bug is found during a round
- **THEN** an entry is appended to `bugs.json` containing: `{"id": "<unique>", "source": "<original>", "decompiled": "<output>", "error_type": "<ast_mismatch|exception>", "exception": "<traceback if applicable>"}`

### Requirement: Bug definition and classification
The system SHALL classify a bug as any test pattern where `ast.dump(ast.parse(decompiled)) != ast.dump(ast.parse(original))` OR where decompilation raises an exception. C-class bugs (single-case match → if/else ambiguity) SHALL be tagged separately and SHALL NOT count toward the ≥10 threshold.

#### Scenario: AST mismatch bug
- **WHEN** the decompiled output parses to a different AST than the original source
- **THEN** the pattern is recorded as a bug with error_type "ast_mismatch"

#### Scenario: Exception bug
- **WHEN** the decompilation process raises an exception
- **THEN** the pattern is recorded as a bug with error_type "exception"

#### Scenario: C-class bug excluded from threshold
- **WHEN** a match region bug is solely due to single-case match being decompiled as if/else
- **THEN** the bug is tagged "C-class" and does not count toward the ≥10 bugs-per-round requirement

### Requirement: Progressive pattern complexity
The system SHALL increase pattern generator complexity across rounds:
- Rounds 1-5: basic patterns (single construct, simple bodies)
- Rounds 6-10: moderate complexity (nested constructs, multi-statement bodies)
- Rounds 11-15: advanced patterns (deep nesting, unusual combinations)
- Rounds 16-20: adversarial patterns (known hard cases, regression seeds from earlier rounds)

#### Scenario: Basic round generation
- **WHEN** round 2 of "if" region type is being generated
- **THEN** the pattern generator produces basic if/else patterns with simple assignment bodies

#### Scenario: Adversarial round generation
- **WHEN** round 17 of "tryexcept" region type is being generated
- **THEN** the pattern generator includes regression seeds from bugs found in rounds 1-16

### Requirement: Fix verification
The system SHALL re-run all bug patterns from the current round after fixes are applied, and SHALL confirm zero bugs before the round is counted as complete.

#### Scenario: Successful fix verification
- **WHEN** fixes are applied and all previously-failing patterns now pass
- **THEN** the round is marked complete and the system advances to the next round

#### Scenario: Incomplete fix verification
- **WHEN** fixes are applied but some patterns still fail
- **THEN** additional fixes MUST be applied and verification re-run until zero bugs

### Requirement: Full test suite regression check
The system SHALL run the complete control_flow_matrix test suite (pytest) after every bug fix, and MUST NOT advance to the next round if any existing test regresses.

#### Scenario: No regression after fix
- **WHEN** a bug fix is applied and all 327+ control_flow_matrix tests still pass
- **THEN** the fix is accepted and round verification continues

#### Scenario: Regression detected
- **WHEN** a bug fix causes any previously-passing control_flow_matrix test to fail
- **THEN** the fix MUST be reverted or adjusted before proceeding

### Requirement: No early termination
The system SHALL NOT stop before all 160 rounds (8 types × 20 rounds) are attempted. If a region type reaches 0 bugs across multiple consecutive rounds at maximum complexity, remaining rounds MAY be fast-tracked but MUST still be executed.

#### Scenario: Region type becomes clean
- **WHEN** 5 consecutive rounds at maximum complexity yield 0 bugs for a region type
- **THEN** the remaining rounds for that type are fast-tracked (still executed but with reduced pattern count) and the system proceeds to the next region type

#### Scenario: All region types complete
- **WHEN** all 8 region types have completed their 20 rounds
- **THEN** a final summary report is generated with total bugs found, total fixes applied, and per-region statistics

### Requirement: Summary reporting
The system SHALL produce a final summary in `tests/iteration/results/summary.json` containing: per-region total bugs, per-round bug counts, C-class bug counts, and overall statistics.

#### Scenario: Final summary generation
- **WHEN** all 8×20 rounds are complete
- **THEN** `tests/iteration/results/summary.json` is written with complete statistics for all region types and rounds
