# G4 current-source measurement (rr-v5r77)

## The frozen G4 reading was stale

`rounds/round9/rule_universe.json` was generated before the recent product
fixes.  Comparing its per-file `sha256` records with the current tree shows
**14 of 20 `core/cfg` files changed**:

```text
core/cfg/__init__.py, ast_converter.py, ast_generator_v2.py, cfg_builder.py,
code_generator.py, comprehension_generator.py, dominator_analyzer.py,
exception_handler.py, patch_detector.py, pattern_parser.py,
peephole_patterns.py, region_analyzer.py, region_ast_generator.py,
structured_analyzer.py
```

The old trace mapped rule IDs to old line numbers, so its
`187/339 hit, 152 never-hit` reading no longer described this tree.  It is
kept as historical evidence, not used as the current G4 denominator.

## Current measurement (read-only, no product edits)

```powershell
python -X utf8 tools/completeness/rule_universe.py --code core/cfg `
  --json .../fresh/g4_audit/rule_universe_current.json
python -X utf8 tools/completeness/rule_manifest.py --generate `
  --universe .../rule_universe_current.json --manifest .../rule_manifest_current.json
python -X utf8 .../fresh/g4_audit/trace_g4_current.py `
  --universe .../rule_universe_current.json `
  --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json `
  --out .../rule_traces_current.json
python -X utf8 tools/completeness/rule_manifest.py --check `
  --universe .../rule_universe_current.json --manifest .../rule_manifest_current.json `
  --jspace .../judgment_space.json --traces .../rule_traces_current.json `
  --json .../rule_coverage_current.json
```

The trace replays the same in-process region pipeline as Task 6.4
(`build_cfg` -> `RegionASTGenerator` -> `CFGASTConverter` ->
`CFGCodeGenerator`) over the 131 unique pycs referenced by the 1556 J entries.
`traced_entries=1556`, `failed_entries=0`.

## Readings

| Metric | Stale round9 | Current (rr-v5r77) |
|---|---:|---:|
| Independent rules | 339 | **342** |
| Branch positions | 5663 | **5791** |
| `isinstance_ast` / `opcode_eq` | 15 / 324 | **15 / 327** |
| Rules hit by J traces | 187 | **243** |
| `empty_cov` (never hit) | 152 | **99** |
| `proved` | 0 | **0** |
| `open` | 339 | **342** |
| `unmapped` / `orphan` | 0 / 0 | **0 / 0** |
| G4 | FAIL | **FAIL** |
| `reason` | `mapping_or_proof_gap` | **`mapping_or_proof_gap`** |

The current measurement improves fidelity, not the verdict: **G4 is still
FAIL** because no rule has a proof and 99 rules were never executed by the J
space.  No `proof_id`, `composition`, or witness was fabricated.

## Why the 99 are never hit

`G4_REACHABILITY_CURRENT.json` classifies every never-hit rule by its
innermost enclosing scope and by whether any *other* rule in the same scope
executed:

| Class | Count | Meaning |
|---|---:|---|
| `scope_observed_branch_unhit` | **29** | The function ran, but this dispatch/branch line did not. |
| `scope_never_observed_has_refs` | **66** | The function never ran on the 131 J pycs, but its name is referenced elsewhere (legacy/alternate path or unexercised live path). |
| `scope_never_observed_zero_refs` | **4** | No reference outside the definition; dead-code candidates. |

The four zero-reference candidates are:

```text
core/cfg/objective_patch_detector.py:89/93  ObjectivePatchDetector.analyze_file
    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))  (x2)
    isinstance(node, ast.ClassDef)
core/cfg/ast_generator_v2.py:21964          ASTGeneratorV2._extract_with_context
    instr.opname in ('BEFORE_WITH', 'SETUP_WITH')
```

The 29 branch-unhit rules are concentrated in
`CodeGenerator._generate_dict_node` (16 dict-literal dispatch arms),
`ASTGeneratorV2._generate_entry_sequence` (3), and small groups in
`_generate_block_content_skip_iterator`, `_generate_try`,
`_process_instruction_sequence`, `_generate_comprehension_function`,
`_generate_expression`, `try_generate_comprehension_assign`,
`_find_returns_pending_value_successor`, `_generate_boolop_impl`, and
`_b247_mixed_boolchain`.

The 66 never-observed-with-refs rules are led by
`ASTGeneratorV2._generate_if_ast` (10) and its `extract_elif_chain` nested
function (6), `StructuredAnalyzer._identify_with_structures` (5), and
`ObjectivePatchDetector._extract_test_pattern` (4).  `ast_generator_v2` is
the legacy generator; the region path does not call it for these inputs.

This is a **J-input coverage gap plus legacy/dead code**, not a proof-only
gap.  Closing it requires either new J entries that execute those branches,
or a reviewed decision to exclude dead code from the independent universe —
neither of which is done here.

## Corpus diagnostic (not a gate input)

To test whether the 99 never-hit rules are reachable at all, the same region
pipeline was traced over the 402 real-package pycs
(`corpus_402_space.json`) instead of the J space:

```powershell
python -X utf8 .../fresh/g4_audit/trace_g4_current.py `
  --universe .../rule_universe_current.json `
  --jspace .../corpus_402_space.json `
  --out .../rule_traces_corpus402.json
```

Readings: `traced_entries=402`, `failed_entries=0`, **233/342** rules hit,
109 never hit.  Compared with the J trace:

| Set | Count |
|---|---:|
| J hit | 243 |
| 402-corpus hit | 233 |
| J ∩ corpus | 224 |
| J-only | 19 |
| corpus-only | 9 |
| union | **252 / 342** |
| J-never rules hit by corpus | **9 / 99** |
| still never hit by either | **90 / 99** |

The 9 corpus-only rules are all in `region_ast_generator.py` /
`region_analyzer.py`.  By the reachability classes, they comprise 8
`scope_never_observed_has_refs` and 1 `scope_observed_branch_unhit`.  After
the union, the 99 become: **28** observed-but-branch-unhit, **58**
never-observed-with-refs, **4** zero-reference candidates.  None of the four
zero-reference candidates is executed by the 402 corpus either.

This narrows the J-input claim but does **not** change the verdict: the corpus
is a different input domain, the J denominator stays 1556, and the 402 trace
is not evidence for J coverage.  G4 remains **FAIL** with 90 rules unexecuted
by both domains and `proved=0`.

## What this round does not claim

- It does not claim G4 PASS, rule completeness, or corpus completeness.
- It does not replace the historical round9 artifacts; it adds current-tree
  artifacts and marks the old reading as superseded for this tree.
- It does not treat "referenced" as "alive" or "zero-reference" as a formal
  dead-code proof.  The classification is a candidate signal.

## Evidence

| File | SHA256 |
|---|---|
| `rule_universe_current.json` | `F3AA931FFEA8BBEC7AB5F620C5EA1DC3A09B25C895AFE17E9655E293E9AC7C27` |
| `rule_manifest_current.json` | `D248D291D20ECD34F65B298FA175214A2DD2ADCA6C472CDEC9A5F047D88498FE` |
| `rule_traces_current.json` | `5917DC5F469DC6E6EE0EAE3F59CDAE7E880D0C36C0710FBE26FA890C63B1D8F8` |
| `rule_coverage_current.json` | `14AD782DA0E7BEB2AE320DAE6D305BE129684423A8497EBCA81A908B322C341F` |
| `G4_REACHABILITY_CURRENT.json` | `D51E54735A16D410A0F8313A4CC8B5B1BA3E4A21130A848EEEFD7572EE06DE81` |
| `rule_traces_corpus402.json` (diagnostic only) | `8EAFB17A0762256A5442D4CDB1B30ADEF4FE978BEF8554782D146951575101FA` |
