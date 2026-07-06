## ADDED Requirements

### Requirement: Per-region iteration test directories
The system SHALL create test directories organized as `iteration_tests/<region_type>/round_<N>/` for each of the 8 region types and each of the 20 rounds.

#### Scenario: Directory creation
- **WHEN** a new round begins for a region type
- **THEN** a directory `iteration_tests/<region_type>/round_<N>/` is created with a `test_round.py` script

### Requirement: Round error threshold
Each round SHALL require at least 10 distinct error instances before any fixes are applied. If fewer than 10 errors are found, the round SHALL NOT count.

#### Scenario: Sufficient errors found
- **WHEN** test execution finds 10 or more errors
- **THEN** all errors are recorded and fixes are applied, completing the round

#### Scenario: Insufficient errors found
- **WHEN** test execution finds fewer than 10 errors
- **THEN** the round is not counted and test patterns are expanded

### Requirement: Fix-all-before-next protocol
All errors found in a round SHALL be fixed before advancing to the next round. No partial fixes are allowed.

#### Scenario: All errors fixed
- **WHEN** all ≥10 errors from a round are fixed
- **THEN** the full regression suite is run and the round is marked complete

#### Scenario: Regression detected after fix
- **WHEN** a fix introduces a regression in existing tests
- **THEN** the regression must be resolved before the round can be marked complete

### Requirement: Test pattern generation per region type
Each round SHALL generate test patterns specific to the target region type, with increasing complexity across rounds.

#### Scenario: Pattern complexity progression
- **WHEN** round N+1 begins for a region type
- **THEN** test patterns include all patterns from round N plus new more complex patterns (deeper nesting, more operands, mixed constructs)

### Requirement: 8 region types tested
The system SHALL run iteration testing for all 8 region types: if-region, loop-region, try-region, with-region, match-region, boolop-region, ternary-region, assert-region.

#### Scenario: All region types covered
- **WHEN** iteration testing completes
- **THEN** all 8 region types have been tested for up to 20 rounds each

### Requirement: Round results recording
Each round SHALL write results to `results.txt` in the round directory, including: total tests, error count, error details, fixes applied, regression check result.

#### Scenario: Results written
- **WHEN** a round completes
- **THEN** `results.txt` in the round directory contains test count, error list, fix descriptions, and regression status
