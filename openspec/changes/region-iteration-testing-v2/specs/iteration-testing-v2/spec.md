## ADDED Requirements

### Requirement: Region-type iteration test generator
The system SHALL provide a per-region-type test generator that produces targeted source patterns combining the region with other constructs. Each generator SHALL cover interaction patterns specific to its region type: IF (elif, BoolOp conditions, ternary, nested if), WHILE_LOOP (break/continue, else, nested), FOR_LOOP (else, nested, match-in-loop), TRY_EXCEPT (multi-except, else, finally, nested), WITH (multi-with, as-var, nested), MATCH (wildcard, guard, class, sequence, mapping, nested), BOOL_OP (and/or/chain-cmp + elif/else/ternary interactions), TERNARY (nested ternary, ternary in conditions).

#### Scenario: IF region generator produces elif+BoolOp patterns
- **WHEN** IF region test generator runs for round 1
- **THEN** it generates patterns like `if a and b: ... elif z: ...`, `if a or b: ... elif z: ... else: ...`, `if 0 < a < 10 or x > 100: ... elif z: ...`

#### Scenario: BOOL_OP region generator produces condition interaction patterns
- **WHEN** BOOL_OP region test generator runs for round 1
- **THEN** it generates patterns combining and/or/chain-cmp with elif, else, ternary, and nested conditions

### Requirement: Round protocol with bug threshold
The system SHALL enforce a round protocol: collect bug instances in a round directory, only start fixing once ≥10 distinct bugs are accumulated, fix all bugs to complete the round. A round with <10 bugs does NOT count. The round counter SHALL only increment for qualifying rounds.

#### Scenario: Round with 10+ bugs counts
- **WHEN** a round accumulates 12 bug instances and all 12 are fixed
- **THEN** the round is marked complete and the round counter increments

#### Scenario: Round with fewer than 10 bugs does not count
- **WHEN** a round only finds 7 bug instances
- **THEN** the round does not count, test generation continues until ≥10 bugs are found

#### Scenario: All bugs fixed to complete round
- **WHEN** 10 bugs are collected and fixes are applied
- **THEN** the round is complete only after ALL 10 bugs are verified fixed

### Requirement: Dedicated test directory structure
The system SHALL organize test files in `tests/iteration/<region-type>/round-NN/` directories. Each round directory SHALL contain: generated test source files, bug report files listing discovered issues, and a round status file tracking progress.

#### Scenario: Directory created per region per round
- **WHEN** round 3 of IF region starts
- **THEN** directory `tests/iteration/IF/round-03/` exists with test and bug files

#### Scenario: Round status file tracks progress
- **WHEN** a round is in progress
- **THEN** `tests/iteration/<region-type>/round-NN/STATUS.md` exists showing bug count, fix count, and round state

### Requirement: Eight region types tested
The system SHALL run iteration testing for 8 region types: IF, WHILE_LOOP, FOR_LOOP, TRY_EXCEPT, WITH, MATCH, BOOL_OP, TERNARY. Each region type SHALL undergo up to 20 qualifying rounds.

#### Scenario: All 8 region types are covered
- **WHEN** iteration testing completes
- **THEN** IF, WHILE_LOOP, FOR_LOOP, TRY_EXCEPT, WITH, MATCH, BOOL_OP, TERNARY regions have all been tested

#### Scenario: 20 rounds per region type maximum
- **WHEN** IF region testing completes
- **THEN** 20 qualifying rounds have been executed for IF region

### Requirement: C-class identification for identical bytecode patterns
The system SHALL identify C-class patterns: source patterns that produce identical bytecode and are thus indistinguishable by the decompiler. C-class patterns SHALL be marked but SHALL NOT count toward the ≥10 bug threshold.

#### Scenario: C-class pattern identified and excluded from bug count
- **WHEN** two source patterns produce identical bytecode
- **THEN** both are marked as C-class and do not count toward the round's bug threshold

#### Scenario: Non-C-class bug counts toward threshold
- **WHEN** a decompilation produces incorrect output for a pattern with unique bytecode
- **THEN** the bug instance counts toward the ≥10 threshold

### Requirement: Targeted bug pattern research
The system SHALL research the codebase for potential bugs before generating tests, constructing specific patterns that expose real issues rather than random testing. Research SHALL focus on interaction boundaries between region types and edge cases in condition handling.

#### Scenario: Codebase research drives test generation
- **WHEN** round generation begins for a region type
- **THEN** the generator first analyzes relevant code paths and known failure modes, then constructs tests targeting those areas

### Requirement: All rounds must complete before stopping
The system SHALL continue executing rounds until all 8 region types have completed 20 qualifying rounds each. Partial completion is not acceptable. The process SHALL NOT stop early even if bug rates drop.

#### Scenario: Testing continues despite low bug rates
- **WHEN** a region type finds only 3 bugs in a round
- **THEN** testing continues generating more patterns until ≥10 bugs are found to qualify the round

#### Scenario: Full completion required
- **WHEN** 7 of 8 region types have completed 20 rounds
- **THEN** the remaining region type continues testing until it also completes 20 rounds
