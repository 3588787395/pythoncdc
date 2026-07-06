## ADDED Requirements

### Requirement: BoolOp containing nested Ternary decompiles correctly
When a BoolOp expression (`and`/`or`) contains a ternary expression as an operand, the decompiler SHALL produce the correct source code with proper parenthesization.

#### Scenario: and with ternary operand
- **WHEN** source code is `z = a and (b if c else d)`
- **THEN** decompiled output is `z = a and (b if c else d)` (parenthesized IfExp)

#### Scenario: or with ternary operand
- **WHEN** source code is `z = a or (b if c else d)`
- **THEN** decompiled output is `z = a or (b if c else d)` (parenthesized IfExp)

### Requirement: BoolOpRegion merge_block uses short-circuit target
When a BoolOp chain contains both SHORT_CIRCUIT_JUMP_OPS and FORWARD_CONDITIONAL_JUMP_OPS blocks with different jump targets, the merge_block SHALL be set to the short-circuit jump target (the final convergence point), not the conditional jump target.

#### Scenario: Mixed short-circuit and conditional jumps
- **WHEN** `a and (b if c else d)` is compiled, B1's JUMP_IF_FALSE_OR_POP targets offset 16 (merge) and B2's POP_JUMP_IF_FALSE targets offset 14 (ternary false branch)
- **THEN** BoolOpRegion.merge_block is the block at offset 16, not offset 14

### Requirement: Ternary branch blocks included in BoolOpRegion
When a BoolOp chain block has conditional successors that form a ternary pattern (both branches reach the merge point), both branch blocks SHALL be included in the BoolOpRegion's block set.

#### Scenario: Ternary branches in BoolOp
- **WHEN** `z = a and (b if c else d)` is decompiled
- **THEN** BoolOpRegion.blocks includes both the true-value block (LOAD b) and false-value block (LOAD d)

### Requirement: is_condition_context false for mixed chains
When a BoolOp chain starts with SHORT_CIRCUIT_JUMP_OPS and extends to FORWARD_CONDITIONAL_JUMP_OPS, `is_condition_context` SHALL be False (it's an assignment context, not a conditional).

#### Scenario: Short-circuit chain with ternary extension
- **WHEN** BoolOp chain is [(B1, 'and'), (B2, 'and')] where B1 has JUMP_IF_FALSE_OR_POP and B2 has POP_JUMP_IF_FALSE
- **THEN** BoolOpRegion.is_condition_context is False

### Requirement: BoolOpRegion not child of IfRegion at same entry
When a BoolOpRegion and IfRegion share the same entry block and the entry block is owned by BoolOpRegion, the BoolOpRegion SHALL NOT be added as a child of the IfRegion.

#### Scenario: Same entry block ownership
- **WHEN** BoolOpRegion and IfRegion both have entry at B1, and block_to_region[B1] is BoolOpRegion
- **THEN** BoolOpRegion.parent is None (not IfRegion)

### Requirement: IfExp parenthesized in BoolOp code generation
When generating a BoolOp expression that contains an IfExp (ternary) as a value, the IfExp SHALL be wrapped in parentheses.

#### Scenario: IfExp as BoolOp value
- **WHEN** BoolOp AST has values [Name('a'), IfExp(test=Name('c'), body=Name('b'), orelse=Name('d'))]
- **THEN** generated code is `a and (b if c else d)` with parentheses around the IfExp

### Requirement: Nested ternary detection in BoolOp expression building
When building a BoolOp expression, if a chain block has conditional successors that both exist in the region and both reach the merge point, the chain block SHALL be reconstructed as a ternary expression rather than a simple operand.

#### Scenario: Ternary reconstruction from chain block
- **WHEN** chain block B2 has LOAD c; POP_JUMP_IF_FALSE → B4, where B3 (LOAD b) and B4 (LOAD d) are both in region.blocks
- **THEN** the operand for B2 is IfExp(test=Name('c'), body=Name('b'), orelse=Name('d')) instead of just Name('c')

### Requirement: Fall-through block skipped for nested ternary
When the last chain block in a BoolOp is reconstructed as a nested ternary expression, the fall-through block SHALL NOT be appended as an additional operand.

#### Scenario: Ternary already covers fall-through
- **WHEN** chain block B2 is detected as a ternary header and reconstructed as IfExp
- **THEN** B3 (the fall-through successor) is not added again as a separate BoolOp operand
