## ADDED Requirements

### Requirement: Assert-as-inner nesting tests
The test suite SHALL contain a test class for each structural region type (If, For, While, Try, With, Match) that verifies assert statements decompile correctly when nested inside that region type.

#### Scenario: Assert inside if-branch
- **WHEN** source code is `if debug:\n    assert x > 0`
- **THEN** decompiled output contains an `ast.Assert` node inside the `ast.If` body

#### Scenario: Assert inside for-loop body
- **WHEN** source code is `for item in items:\n    assert isinstance(item, int)`
- **THEN** decompiled output contains an `ast.Assert` node inside the `ast.For` body

#### Scenario: Assert inside while-loop body
- **WHEN** source code is `while running:\n    assert health_check()`
- **THEN** decompiled output contains an `ast.Assert` node inside the `ast.While` body

#### Scenario: Assert inside try body
- **WHEN** source code is `try:\n    assert valid(data)\nexcept AssertionError:\n    handle_invalid()`
- **THEN** decompiled output contains an `ast.Assert` node inside the `ast.Try` body

#### Scenario: Assert inside with body
- **WHEN** source code is `with open('f') as f:\n    assert f.readable()`
- **THEN** decompiled output contains an `ast.Assert` node inside the `ast.With` body

#### Scenario: Assert inside match case body
- **WHEN** source code is `match mode:\n    case 'strict':\n        assert valid(data)`
- **THEN** decompiled output contains an `ast.Assert` node inside the `ast.match_case` body

### Requirement: Expression-level region as outer tests
The test suite SHALL contain tests for semantically-valid combinations where expression-level regions (BoolOp, Ternary) appear as outer regions containing other expression-level regions.

#### Scenario: BoolOp containing Ternary
- **WHEN** source code is `result = a and (b if c else d)`
- **THEN** decompiled output contains a BoolOp expression with a Ternary (IfExp) as one operand

#### Scenario: Ternary containing BoolOp
- **WHEN** source code is `result = (a and b) if c else d`
- **THEN** decompiled output contains a Ternary (IfExp) expression with a BoolOp as the value

### Requirement: Decoupling proof tests
For each inner region type (If, For, While, Try, With, Match, BoolOp, Ternary), the test suite SHALL verify that the decompiled AST subtree for that inner region is structurally identical regardless of which parent region type contains it.

#### Scenario: If-region AST subtree independent of parent
- **WHEN** the same `if inner_cond: x = 1` code is nested inside 5 different parent region types (if, for, while, try, with)
- **THEN** the `ast.dump()` of the inner `ast.If` node is identical across all 5 parent contexts

#### Scenario: For-loop AST subtree independent of parent
- **WHEN** the same `for i in range(3): y = i` code is nested inside 5 different parent region types
- **THEN** the `ast.dump()` of the inner `ast.For` node is identical across all 5 parent contexts

#### Scenario: While-loop AST subtree independent of parent
- **WHEN** the same `while cond: y = 1` code is nested inside 5 different parent region types
- **THEN** the `ast.dump()` of the inner `ast.While` node is identical across all 5 parent contexts

#### Scenario: Try-except AST subtree independent of parent
- **WHEN** the same `try: x = 1\nexcept: pass` code is nested inside 5 different parent region types
- **THEN** the `ast.dump()` of the inner `ast.Try` node is identical across all 5 parent contexts

#### Scenario: With-statement AST subtree independent of parent
- **WHEN** the same `with ctx(): x = 1` code is nested inside 5 different parent region types
- **THEN** the `ast.dump()` of the inner `ast.With` node is identical across all 5 parent contexts

#### Scenario: Match-statement AST subtree independent of parent
- **WHEN** the same `match x:\n    case 1: y = 1` code is nested inside different parent region types
- **THEN** the `ast.dump()` of the inner `ast.Match` node is identical across all parent contexts

#### Scenario: BoolOp-expression AST subtree independent of parent
- **WHEN** the same `z = a and b` code is nested inside 5 different parent region types
- **THEN** the `ast.dump()` of the inner `ast.BoolOp` node is identical across all 5 parent contexts

#### Scenario: Ternary-expression AST subtree independent of parent
- **WHEN** the same `z = x if c else y` code is nested inside 5 different parent region types
- **THEN** the `ast.dump()` of the inner `ast.IfExp` node is identical across all 5 parent contexts

### Requirement: Test infrastructure reuse
All test classes SHALL extend the existing `ControlFlowTestCase` base class from `tests/control_flow_matrix/base.py` and use its `decompile()`, `verify_syntax()`, and `find_node()` methods.

#### Scenario: Test class inheritance
- **WHEN** a new test class is defined for region decoupling
- **THEN** it extends `ControlFlowTestCase` and sets `SOURCE_CODE` class attribute

### Requirement: Complete 2-layer nesting coverage
After this change, every semantically-valid 2-layer nesting combination of the 8 region types SHALL have at least one passing test.

#### Scenario: Coverage completeness
- **WHEN** all semantically-valid pairs of (outer_region, inner_region) are enumerated
- **THEN** each pair has at least one test that verifies correct decompilation
