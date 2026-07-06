## Context

The decompiler uses 8 region types (If, Loop, Try, With, Match, Assert, BoolOp, Ternary) with dedicated `_generate_*` methods in `RegionASTGenerator`. Current tests use `ControlFlowTestCase` base class and a 6×8 matrix in `test_l2_exhaustive.py`, but Assert is never nested and expression-level regions (BoolOp/Ternary) are never outer. No test proves that an inner region decompiles identically regardless of which region type contains it.

## Goals / Non-Goals

**Goals:**
- Prove each region type's AST generation is decoupled from parent type: same inner region produces structurally identical AST subtree regardless of outer context
- Fill the 8 missing semantically-valid nesting combinations (6 assert-as-inner + 2 expression-as-outer)
- Provide a reusable test pattern that makes adding new nesting tests trivial
- Achieve 100% coverage of all semantically-valid 2-layer nesting combinations

**Non-Goals:**
- 3+ layer nesting (already covered by `test_l3_deep.py` and `test_l3_combinations.py`)
- Performance or stress testing
- Changing any production code
- Testing semantically-invalid combinations (e.g., boolop containing a with statement)

## Decisions

### D1: Single file vs. multiple test files
**Decision**: Single file `test_region_decoupling.py` in `tests/control_flow_matrix/`
**Rationale**: All existing matrix tests live there. One file keeps the decoupling proof self-contained and makes the NxN coverage matrix easy to audit. Estimated ~60 test classes.

### D2: Decoupling verification method
**Decision**: For each inner region type R, write the same R-producing source code nested inside different parent regions, then compare the AST subtree for R using `ast.dump()` equality.
**Rationale**: Simply asserting "assert appears" or "for loop exists" doesn't prove structural equivalence. Comparing `ast.dump()` of the inner subtree proves the generation code produces identical output regardless of parent. Alternative considered: compare decompiled text strings — rejected because formatting differences (indentation) would cause false negatives.

### D3: Test class organization
**Decision**: Three test groups in one file:
1. **AssertAsInner** (6 classes): Assert nested inside each structural region
2. **ExpressionAsOuter** (2 classes): BoolOp containing Ternary, Ternary containing BoolOp
3. **DecouplingProof** (8 classes): One per inner region type, each testing that region inside 5+ different parents produces identical AST subtree

**Rationale**: Group 1+2 fill missing combinations. Group 3 is the decoupling proof — the unique value of this test suite.

### D4: Source code template for decoupling tests
**Decision**: Each inner region type gets a canonical source snippet. The snippet is embedded in a minimal parent context. Example for IfRegion:
```python
# Inside if:  if flag: if inner_cond: x = 1
# Inside for: for i in r: if inner_cond: x = 1
# Inside try: try: if inner_cond: x = 1 except: pass
# etc.
```
The `if inner_cond: x = 1` part should produce identical AST whether inside if/for/try/with/match.

**Rationale**: Minimal snippets reduce risk of bytecode differences caused by optimization interactions. Alternative: use complex real-world patterns — rejected because harder to attribute failure to specific coupling.

## Risks / Trade-offs

- **[AST structural comparison may be too strict]** → Use `ast.dump()` with `indent=None` for compact comparison; if minor differences exist (e.g., `ast.Constant` vs `ast.Num`), add a normalization step
- **[Assert inside match case may not compile identically across Python versions]** → Guard with version check if needed; assert-in-match-case is valid Python 3.10+
- **[BoolOp>ternary may not produce a BoolOpRegion as outer]** → If CPython optimizes away the BoolOp wrapping, the test should verify whatever region structure actually emerges — the goal is correct decompilation, not forcing a specific region structure
