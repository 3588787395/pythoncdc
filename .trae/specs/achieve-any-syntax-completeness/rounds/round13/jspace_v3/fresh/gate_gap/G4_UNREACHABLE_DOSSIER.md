# G4 unreachable-rule dossier (D1 / D2 / D3)

> **Evidence only.** `core/`, `scripts/`, `tests/`, `tools/completeness/*.py` were not modified. No `status` / `witnesses` / `semantic_domain` / `proof` / `composition` field was touched, and no `rule_universe` file was rewritten (this round creates new `universe_v2.json` / `manifest_v2.json` / `traces_v2.json` / `coverage_v2.json`). `judgment_space.json`, `rule_universe_current.json` and `rule_traces_current.json` are read-only inputs.

## 0. Reading: the new authoritative baseline (current HEAD)

The same command set as `fresh/g4_audit/G4_CURRENT.md`, re-run against the current tree (cwd = `F:\Downloads\pythoncdc-main`):

```powershell
python -I -X utf8 tools/completeness/rule_universe.py --code core/cfg \
  --json fresh/gate_gap/universe_v2.json
python -I -X utf8 tools/completeness/rule_manifest.py --generate \
  --universe fresh/gate_gap/universe_v2.json --manifest fresh/gate_gap/manifest_v2.json
python -I -X utf8 .../fresh/g4_audit/trace_g4_current.py \
  --universe fresh/gate_gap/universe_v2.json \
  --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
  --out fresh/gate_gap/traces_v2.json
python -I -X utf8 tools/completeness/rule_manifest.py --check \
  --universe fresh/gate_gap/universe_v2.json --manifest fresh/gate_gap/manifest_v2.json \
  --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
  --traces fresh/gate_gap/traces_v2.json --json fresh/gate_gap/coverage_v2.json
```

| metric | old (2026-10-27, stale) | **new (current HEAD)** |
|---|---:|---:|
| independent rules | 342 | **344** |
| branch positions | 5791 | **5894** |
| `isinstance_ast` / `opcode_eq` | 15 / 327 | **15 / 329** |
| `rules_hit` | 243 | **244** |
| `empty_cov` (never hit by the J space) | 99 | **100** |
| `unmapped` / `orphan` / `anchor_orphans` | 0 / 0 / 0 | **0 / 0 / 0** |
| `proved` / `open` | 0 / 342 | **0 / 344** |
| G4 | FAIL | **FAIL** (`mapping_or_proof_gap`) |

Measured at HEAD `cb5fa830` (2026-11-17); the old column is the 2026-10-27 reading whose line anchors have since drifted.

Trace summary: `entries=1556` (unique pycs=131) `failed=0`. The 100 rules below are exactly the ones whose `coverage[rule_id] == []` in `coverage_v2.json`.

### Runtime evidence behind the tiering

`_gap_exec.py` replays exactly the same pipeline as `trace_g4_current.py` (`build_cfg` -> `RegionASTGenerator` -> `CFGASTConverter` -> `CFGCodeGenerator` over the 131 J pycs) but records the **executed line set per file** (`--out .../gap_exec_v2.json`):

```text
  core/ast_nodes.py                                1017 lines
  core/cfg/ast_converter.py                         850 lines
  core/cfg/ast_generator_v2.py                     1209 lines
  core/cfg/basic_block.py                            47 lines
  core/cfg/cfg_builder.py                           299 lines
  core/cfg/code_generator.py                       1464 lines
  core/cfg/comprehension_generator.py              1801 lines
  core/cfg/dominator_analyzer.py                    244 lines
  core/cfg/opcode_feature_detector.py                88 lines
  core/cfg/pattern_parser.py                       1194 lines
  core/cfg/peephole_patterns.py                     152 lines
  core/cfg/region_analyzer.py                     16045 lines
  core/cfg/region_ast_generator.py                24352 lines
  core/pyc_objects.py                               191 lines
```

`core/cfg/{structured_analyzer,objective_patch_detector,patch_detector,patch_detector_enhanced,exception_handler}.py` are **absent** from that table, i.e. those modules executed **0 lines** on the J trace.

Static import reachability from `pycdc.py` is *not* the discriminator, because `core/cfg/__init__.py` re-exports these modules: `from core.cfg import build_cfg` (`pycdc.py:83`) runs the package barrel, so almost every module is import-reachable. The decisive fact is whether any line of the module **executed**:

| file | in `pycdc.py` import closure | reached via | executed lines |
|---|---|---|---:|
| `core/cfg/ast_generator_v2.py` | yes | `core/cfg/region_ast_generator.py:236` | 1209 |
| `core/cfg/basic_block.py` | yes | `core/cfg/region_ast_generator.py:225` | 47 |
| `core/cfg/code_generator.py` | yes | `<pycdc.py seed>:0` | 1464 |
| `core/cfg/comprehension_generator.py` | yes | `core/cfg/region_ast_generator.py:237` | 1801 |
| `core/cfg/exception_handler.py` | yes | `core/cfg/structured_analyzer.py:11717` (lazy) | 0 |
| `core/cfg/objective_patch_detector.py` | **no** | - | 0 |
| `core/cfg/patch_detector.py` | **no** | - | 0 |
| `core/cfg/region_analyzer.py` | yes | `core/cfg/region_ast_generator.py:228` | 16045 |
| `core/cfg/region_ast_generator.py` | yes | `<pycdc.py seed>:0` | 24352 |
| `core/cfg/structured_analyzer.py` | yes | `core/cfg/ast_generator_v2.py:14` | 0 |

## 1. Tier decision rule (mechanically re-computable)

| tier | criterion | meaning |
|---|---|---|
| **D1** | the rule's file executed **0 lines**, and there is no consumer importer in `core/` (only the package barrel `core/cfg/__init__.py`, CLI scripts, or legacy modules that themselves executed 0 lines) | module-level dead region: no tracer can enter it without changing the product call chain or the universe |
| **D2** | module is live (has executed lines) but the rule's enclosing function/method executed **0 lines** | imported, but never constructed / entered at runtime |
| **D3** | the rule's enclosing function **has executed lines** but the rule's branch line did not | the function is reachable; what is missing is an input shape that triggers the branch |

Per-rule fields in `g4_unreachable.json`: `importers_in_core` / `importers_barrel` / `importers_cli` / `importers[*].executed` (did that import statement line execute) / `refs_total` / `refs_executed` (did any call site of the function execute) / `scope_lines_executed` / `scope_lines_total` / `class_lines_executed` / `in_pycdc_import_closure` / `closure_via`.

## 2. Summary

| tier | rules | files | criterion mix |
|---|---:|---:|---|
| **D1** | **23** | 4 | `no_consumer_importer` x15, `consumer_importer_never_executes` x8 |
| **D2** | **56** | 5 | `class_never_constructed` x31, `class_live_callee_unentered` x25 |
| **D3** | **21** | 4 | `function_entered_branch_unhit` x21 |
| total | **100** | 10 | 29.1% of the universe |

By file:

| file | D1 | D2 | D3 | total |
|---|---:|---:|---:|---:|
| `core/cfg/ast_generator_v2.py` | 0 | 32 | 0 | **32** |
| `core/cfg/region_ast_generator.py` | 0 | 5 | 13 | **18** |
| `core/cfg/code_generator.py` | 0 | 16 | 1 | **17** |
| `core/cfg/objective_patch_detector.py` | 11 | 0 | 0 | **11** |
| `core/cfg/structured_analyzer.py` | 7 | 0 | 0 | **7** |
| `core/cfg/region_analyzer.py` | 0 | 2 | 3 | **5** |
| `core/cfg/patch_detector.py` | 4 | 0 | 0 | **4** |
| `core/cfg/comprehension_generator.py` | 0 | 0 | 4 | **4** |
| `core/cfg/exception_handler.py` | 1 | 0 | 0 | **1** |
| `core/cfg/basic_block.py` | 0 | 1 | 0 | **1** |

## 3. D1 list (23 rules, module-level dead region)

### 3.1 Clusters and mechanism

- **`core/cfg/patch_detector.py` / `P1Detector._is_local_region_var` (1 rules)** - `patch_detector.py` executed **0 lines** and has 0 importers in `core/` (`grep -rn patch_detector core/` only hits the sub-string inside `objective_patch_detector`) -> a standalone detector module, not on the decompile chain.
- **`core/cfg/objective_patch_detector.py` / `ObjectivePatchDetector.analyze_file` (3 rules)** - `objective_patch_detector.py` on 131 J pycs executed **0 lines**; it has 0 importers in `core/` (the only references are `scripts/phase6_final_test.py:7`, `scripts/run_baseline_detection.py:20` and the module's own `__main__` self-import at `objective_patch_detector.py:15`) -> the module is not on the `pycdc.py` call chain.
- **`core/cfg/objective_patch_detector.py` / `ObjectivePatchDetector._extract_test_pattern` (4 rules)** - Same cluster: `objective_patch_detector.py` executed 0 lines and has no `core/` importer; its only call site `objective_patch_detector.py:182` sits inside `analyze_file`, which also executed 0 lines.
- **`core/cfg/objective_patch_detector.py` / `ObjectivePatchDetector._node_signature` (3 rules)** - Same cluster; the call site `objective_patch_detector.py:181` is inside `_check_d2_special_branches`, which executed 0 lines.
- **`core/cfg/objective_patch_detector.py` / `ObjectivePatchDetector._check_d2_special_branches` (1 rules)** - Same cluster: no `core/` importer, module executed 0 lines.
- **`core/cfg/patch_detector.py` / `P2Detector._extract_opname_strings` (3 rules)** - Same cluster: `patch_detector.py` executed 0 lines, no `core/` importer.
- **`core/cfg/structured_analyzer.py` / `StructuredAnalyzer._identify_with_structures` (5 rules)** - `structured_analyzer.py` executed **0 lines**; its importers are only the package barrel `core/cfg/__init__.py:66`, legacy `ast_generator_v2.py:14` (the `ASTGeneratorV2` class body itself executed 0 lines) and `exception_handler.py:14` (that module also executed 0 lines) -> no live user. The `StructuredAnalyzer()` construction point `ast_generator_v2.py:3508` never executed; the region pipeline never builds the class.
- **`core/cfg/structured_analyzer.py` / `StructuredAnalyzer._identify_try_except_pre_311` (2 rules)** - Same cluster: `structured_analyzer.py` executed 0 lines and the construction point never ran.
- **`core/cfg/exception_handler.py` / `_find_handler_type_load` (1 rules)** - `exception_handler.py` executed **0 lines**; its only `core/` importer is the lazy import at `structured_analyzer.py:11717`, and `structured_analyzer` itself executed 0 lines -> a chained dead region.

### 3.2 Per-rule evidence lines

- `RULE-d53ac6879d6a | core/cfg/patch_detector.py:328 | sym=Assign | scope=P1Detector._is_local_region_var (0/14 lines executed) | importers: consumer=0 barrel=0 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/patch_detector.py:302` (executed=no) `if var_name and not self._is_local_region_var(`
- `RULE-b3b3c27de3f4 | core/cfg/objective_patch_detector.py:89 | sym=AsyncFunctionDef | scope=ObjectivePatchDetector.analyze_file (0/29 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:17` (executed=no) `verdicts = detector.analyze_file("path/to/file.py")`
- `RULE-526c2f9c8010 | core/cfg/objective_patch_detector.py:197 | sym=Attribute | scope=ObjectivePatchDetector._extract_test_pattern (0/15 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:182` (executed=no) `test_source = self._extract_test_pattern(child.test)`
- `RULE-20568d2871b4 | core/cfg/objective_patch_detector.py:195 | sym=BoolOp | scope=ObjectivePatchDetector._extract_test_pattern (0/15 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:182` (executed=no) `test_source = self._extract_test_pattern(child.test)`
- `RULE-93efbfe2473b | core/cfg/objective_patch_detector.py:199 | sym=Call | scope=ObjectivePatchDetector._extract_test_pattern (0/15 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:182` (executed=no) `test_source = self._extract_test_pattern(child.test)`
- `RULE-2845ddf0b9b8 | core/cfg/objective_patch_detector.py:93 | sym=ClassDef | scope=ObjectivePatchDetector.analyze_file (0/29 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:17` (executed=no) `verdicts = detector.analyze_file("path/to/file.py")`
- `RULE-2b862ecf9a11 | core/cfg/objective_patch_detector.py:191 | sym=Compare | scope=ObjectivePatchDetector._extract_test_pattern (0/15 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:182` (executed=no) `test_source = self._extract_test_pattern(child.test)`
- `RULE-1f3252f64295 | core/cfg/objective_patch_detector.py:213 | sym=Constant | scope=ObjectivePatchDetector._node_signature (0/11 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 5 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:192` (executed=no) `left = self._node_signature(test_node.left)`
  - ref: `core/cfg/objective_patch_detector.py:200` (executed=no) `func = self._node_signature(test_node.func)`
- `RULE-2d4b43ea95f6 | core/cfg/objective_patch_detector.py:89 | sym=FunctionDef | scope=ObjectivePatchDetector.analyze_file (0/29 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:17` (executed=no) `verdicts = detector.analyze_file("path/to/file.py")`
- `RULE-3d070d0913cc | core/cfg/objective_patch_detector.py:181 | sym=If | scope=ObjectivePatchDetector._check_d2_special_branches (0/11 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:124` (executed=no) `d2_score, d2_detail = self._check_d2_special_branches(method_node)`
- `RULE-4c10258ace4e | core/cfg/patch_detector.py:425 | sym=List | scope=P2Detector._extract_opname_strings (0/15 lines executed) | importers: consumer=0 barrel=0 cli=0 | caller-refs 2 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/patch_detector.py:404` (executed=no) `found.update(self._extract_opname_strings(comparator))`
  - ref: `core/cfg/patch_detector.py:449` (executed=no) `found.update(self._extract_opname_strings(comp))`
- `RULE-b56901a142a6 | core/cfg/objective_patch_detector.py:207 | sym=Name | scope=ObjectivePatchDetector._node_signature (0/11 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 5 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:192` (executed=no) `left = self._node_signature(test_node.left)`
  - ref: `core/cfg/objective_patch_detector.py:200` (executed=no) `func = self._node_signature(test_node.func)`
- `RULE-bd1b6b8bb350 | core/cfg/patch_detector.py:425 | sym=Set | scope=P2Detector._extract_opname_strings (0/15 lines executed) | importers: consumer=0 barrel=0 cli=0 | caller-refs 2 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/patch_detector.py:404` (executed=no) `found.update(self._extract_opname_strings(comparator))`
  - ref: `core/cfg/patch_detector.py:449` (executed=no) `found.update(self._extract_opname_strings(comp))`
- `RULE-fd29f404c20d | core/cfg/objective_patch_detector.py:211 | sym=Subscript | scope=ObjectivePatchDetector._node_signature (0/11 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 5 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/objective_patch_detector.py:192` (executed=no) `left = self._node_signature(test_node.left)`
  - ref: `core/cfg/objective_patch_detector.py:200` (executed=no) `func = self._node_signature(test_node.func)`
- `RULE-87d3e450c5e4 | core/cfg/patch_detector.py:425 | sym=Tuple | scope=P2Detector._extract_opname_strings (0/15 lines executed) | importers: consumer=0 barrel=0 cli=0 | caller-refs 2 (executed 0) | pycdc-closure=no | D1/no_consumer_importer`
  - ref: `core/cfg/patch_detector.py:404` (executed=no) `found.update(self._extract_opname_strings(comparator))`
  - ref: `core/cfg/patch_detector.py:449` (executed=no) `found.update(self._extract_opname_strings(comp))`
- `RULE-fac0e268c522 | core/cfg/structured_analyzer.py:13926 | sym=DUP_TOP | scope=StructuredAnalyzer._identify_with_structures (0/152 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes`
  - ref: `core/cfg/structured_analyzer.py:184` (executed=no) `self._identify_with_structures()`
- `RULE-7f1501983cc4 | core/cfg/structured_analyzer.py:13926 | sym=DUP_TOP_TWO | scope=StructuredAnalyzer._identify_with_structures (0/152 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes`
  - ref: `core/cfg/structured_analyzer.py:184` (executed=no) `self._identify_with_structures()`
- `RULE-a2f801d5aefb | core/cfg/structured_analyzer.py:13926 | sym=ROT_THREE | scope=StructuredAnalyzer._identify_with_structures (0/152 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes`
  - ref: `core/cfg/structured_analyzer.py:184` (executed=no) `self._identify_with_structures()`
- `RULE-c708889ddc61 | core/cfg/structured_analyzer.py:13926 | sym=ROT_TWO | scope=StructuredAnalyzer._identify_with_structures (0/152 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes`
  - ref: `core/cfg/structured_analyzer.py:184` (executed=no) `self._identify_with_structures()`
- `RULE-36dde631fda0 | core/cfg/structured_analyzer.py:13288 | sym=SETUP_EXCEPT | scope=StructuredAnalyzer._identify_try_except_pre_311 (0/28 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes`
  - ref: `core/cfg/structured_analyzer.py:13244` (executed=no) `self._identify_try_except_pre_311(analyzed_blocks)`
- `RULE-36f063d106a0 | core/cfg/structured_analyzer.py:13288 | sym=SETUP_FINALLY | scope=StructuredAnalyzer._identify_try_except_pre_311 (0/28 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes`
  - ref: `core/cfg/structured_analyzer.py:13244` (executed=no) `self._identify_try_except_pre_311(analyzed_blocks)`
- `RULE-c500ada1eadd | core/cfg/structured_analyzer.py:13926 | sym=UNARY_OP | scope=StructuredAnalyzer._identify_with_structures (0/152 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes`
  - ref: `core/cfg/structured_analyzer.py:184` (executed=no) `self._identify_with_structures()`
- `RULE-137de19b1304 | core/cfg/exception_handler.py:88 | sym=_UNCOND_JUMP_TARGET_OPS | scope=_find_handler_type_load (0/62 lines executed) | importers: consumer=1 barrel=0 cli=0 | caller-refs 2 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes`
  - ref: `core/cfg/exception_handler.py:205` (executed=no) `found_offset = _find_handler_type_load(analyzer, block, i)`
  - ref: `core/cfg/exception_handler.py:240` (executed=no) `found_offset = _find_handler_type_load(analyzer, check_block, check_index)`

## 4. D2 list (56 rules, module live but function/method never entered)

### 4.1 Clusters and mechanism

- **`core/cfg/code_generator.py` / `CodeGenerator._generate_dict_node` (16 rules)** - `CodeGenerator.generate()` (`code_generator.py:110`) only calls `_generate_dict_node` when `isinstance(node, dict)` (`code_generator.py:133`); the tracer passes the `ASTNode` returned by `CFGASTConverter().convert(...)`, and the dict fallback inside `_generate_node()` (`code_generator.py:185`) never fires either -> all 212 lines of the function executed 0 lines, and all 20 call sites of `_generate_dict_node` are inside it. Contrast: the **expression-level** dict entry `_generate_expression` (`code_generator.py:3778`, also `isinstance(node, dict)`) *is* live (155 lines executed), so dict nodes do reach the code generator - what is dead is the **statement-level** entry `generate(dict)` / `_generate_node(dict)`. The `CodeGenerator` class itself is live (1464 lines of the same file executed) and `CFGCodeGenerator` is only an alias (`code_generator.py:6715`).
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._remove_unreachable_code` (3 rules)** - Same cluster: the `ASTGeneratorV2` class executed 0 lines.
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._generate_entry_sequence` (3 rules)** - Same cluster: the `ASTGeneratorV2` class executed 0 lines.
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._generate_if_ast` (10 rules)** - The `ASTGeneratorV2` class executed **0 lines** on the J trace (all 1209 executed lines of `ast_generator_v2.py` belong to `ExpressionReconstructor`); every caller of `_generate_if_ast` is another `ASTGeneratorV2` method (`ast_generator_v2.py:9197/9268/9299/...`), none of which executed -> the class is never constructed. The region pipeline only takes `ExpressionReconstructor` from this module (`region_ast_generator.py:236`).
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._generate_if_ast.extract_elif_chain` (6 rules)** - Nested function of `_generate_if_ast` (`ast_generator_v2.py:13416`); its only call site `ast_generator_v2.py:13894` is inside the 0-line parent function -> doubly unreachable.
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._generate_block_content_skip_iterator` (2 rules)** - Same cluster: the `ASTGeneratorV2` class executed 0 lines.
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._generate_comprehension_function` (1 rules)** - Same cluster: the `ASTGeneratorV2` class executed 0 lines.
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._extract_iterator_v2` (1 rules)** - Same cluster: the `ASTGeneratorV2` class executed 0 lines.
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._has_terminal_statement` (1 rules)** - Same cluster: the `ASTGeneratorV2` class executed 0 lines.
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._generate_inner_while_from_block` (1 rules)** - Same cluster: the `ASTGeneratorV2` class executed 0 lines.
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._process_instruction_sequence` (1 rules)** - Same cluster: the `ASTGeneratorV2` class executed 0 lines.
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._extract_with_context` (1 rules)** - Same cluster: the `ASTGeneratorV2` class executed 0 lines.
- **`core/cfg/ast_generator_v2.py` / `ExpressionReconstructor._extract_comp_elt` (1 rules)** - Same module (`ast_generator_v2.py` is live), but this comprehension-element side path executed 0 of its 88 lines and none of its call sites executed.
- **`core/cfg/region_analyzer.py` / `RegionAnalyzer._extract_with_items._parse_bind_unpack` (2 rules)** - Parser for `with ... as (a, b)` bind-unpacking; the module is live (`region_analyzer.py` has 16045 executed lines) but this nested function executed 0/44 lines -> no with-target was ever an unpacking form.
- **`core/cfg/region_ast_generator.py` / `RegionASTGenerator._build_multi_target_del_targets` (1 rules)** - The `del a, b` multi-target side path executed 0/88 lines while the module is live.
- **`core/cfg/region_ast_generator.py` / `RegionASTGenerator._build_ternary_boolop_condition` (2 rules)** - Ternary/boolop condition side path; the function executed 0/171 lines while the module is live.
- **`core/cfg/region_ast_generator.py` / `RegionASTGenerator._generate_return_ast` (2 rules)** - The `return`-statement reconstruction side path executed 0/122 lines while the module is live.
- **`core/cfg/basic_block.py` / `BasicBlock.is_conditional` (1 rules)** - The `conditional_ops` set arm at `basic_block.py:193` lives in `BasicBlock.is_conditional`, which executed 0/23 lines **and has 0 call sites in `core/`** (caller-refs 0), although `basic_block.py` has 47 executed lines in other methods.
- **`core/cfg/ast_generator_v2.py` / `ASTGeneratorV2._extract_function_args` (1 rules)** - Same cluster: the `ASTGeneratorV2` class executed 0 lines.

### 4.2 Per-rule evidence lines

- `RULE-eb29ec1ad01a | core/cfg/code_generator.py:285 | sym=AnnAssign | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-1b5b4d7115d9 | core/cfg/code_generator.py:378 | sym=Assert | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-eed79a22277c | core/cfg/code_generator.py:283 | sym=Assign | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-0b22204ea11f | core/cfg/code_generator.py:277 | sym=AsyncFor | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-702b6dd6ca34 | core/cfg/code_generator.py:367 | sym=AsyncFunctionDef | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-42045b244e8a | core/cfg/ast_generator_v2.py:3965 | sym=AsyncWith | scope=ASTGeneratorV2._remove_unreachable_code (0/38 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:3861` (executed=no) `ast_nodes = self._remove_unreachable_code(ast_nodes)`
- `RULE-3b46d229d0af | core/cfg/code_generator.py:281 | sym=AugAssign | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-cd714078ea23 | core/cfg/ast_generator_v2.py:6568 | sym=BINARY_ADD | scope=ASTGeneratorV2._generate_entry_sequence (0/624 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:3562` (executed=no) `entry_ast = self._generate_entry_sequence(entry_block)`
- `RULE-c56bc072e6e4 | core/cfg/ast_generator_v2.py:13181 | sym=BINARY_AND | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:9197` (executed=no) `nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=True, _entry_block_pro`
- `RULE-dda45a0ced72 | core/cfg/ast_generator_v2.py:10477 | sym=BINARY_DIVIDE | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:9197` (executed=no) `nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=True, _entry_block_pro`
- `RULE-5361acaaa053 | core/cfg/ast_generator_v2.py:10477 | sym=BINARY_FLOOR_DIVIDE | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:9197` (executed=no) `nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=True, _entry_block_pro`
- `RULE-c7b3c96bb6c8 | core/cfg/ast_generator_v2.py:10477 | sym=BINARY_MODULO | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:9197` (executed=no) `nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=True, _entry_block_pro`
- `RULE-0062e270c4a1 | core/cfg/ast_generator_v2.py:6568 | sym=BINARY_MULTIPLY | scope=ASTGeneratorV2._generate_entry_sequence (0/624 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:3562` (executed=no) `entry_ast = self._generate_entry_sequence(entry_block)`
- `RULE-bcde89ee3e2a | core/cfg/ast_generator_v2.py:13181 | sym=BINARY_OR | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:9197` (executed=no) `nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=True, _entry_block_pro`
- `RULE-2675d342ef0c | core/cfg/ast_generator_v2.py:6568 | sym=BINARY_SUBTRACT | scope=ASTGeneratorV2._generate_entry_sequence (0/624 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:3562` (executed=no) `entry_ast = self._generate_entry_sequence(entry_block)`
- `RULE-f1bef410c01e | core/cfg/ast_generator_v2.py:10477 | sym=BINARY_TRUE_DIVIDE | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:9197` (executed=no) `nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=True, _entry_block_pro`
- `RULE-010c1b2cf1d7 | core/cfg/ast_generator_v2.py:13459 | sym=Break | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:13894` (executed=no) `elif_tests, elif_bodies, final_else = extract_elif_chain(else_body)`
- `RULE-1c8e48e5d568 | core/cfg/ast_generator_v2.py:7387 | sym=CALL_KW | scope=ASTGeneratorV2._generate_block_content_skip_iterator (0/2225 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 8 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:6684` (executed=no) `content = self._generate_block_content_skip_iterator(current)`
- `RULE-dff33ce626a7 | core/cfg/code_generator.py:369 | sym=ClassDef | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-6ce83d58fb8b | core/cfg/ast_generator_v2.py:13459 | sym=Continue | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:13894` (executed=no) `elif_tests, elif_bodies, final_else = extract_elif_chain(else_body)`
- `RULE-a758f665e9f5 | core/cfg/ast_generator_v2.py:5966 | sym=DICT_ADD | scope=ASTGeneratorV2._generate_comprehension_function (0/216 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:3530` (executed=no) `return self._generate_comprehension_function()`
- `RULE-8c816c79d0c7 | core/cfg/code_generator.py:324 | sym=Delete | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-df8d199ebe90 | core/cfg/code_generator.py:289 | sym=Expr | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-cdc6b865739a | core/cfg/ast_generator_v2.py:26984 | sym=FOR_ITER_RANGE | scope=ASTGeneratorV2._extract_iterator_v2 (0/72 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:15553` (executed=no) `iterator = self._extract_iterator_v2(loop.header_block)`
- `RULE-681e794c6afb | core/cfg/ast_generator_v2.py:13459 | sym=For | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:13894` (executed=no) `elif_tests, elif_bodies, final_else = extract_elif_chain(else_body)`
- `RULE-d712e20d2506 | core/cfg/code_generator.py:365 | sym=FunctionDef | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-05f8183d28bc | core/cfg/ast_generator_v2.py:10653 | sym=GET_ATTR | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:9197` (executed=no) `nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=True, _entry_block_pro`
- `RULE-a99b10fa310d | core/cfg/code_generator.py:326 | sym=Global | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-1fbb15a6c511 | core/cfg/ast_generator_v2.py:3992 | sym=If | scope=ASTGeneratorV2._has_terminal_statement (0/26 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 4 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:3969` (executed=no) `if self._has_terminal_statement(with_body):`
- `RULE-3c8a43d55e71 | core/cfg/code_generator.py:388 | sym=Import | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-1601748f4b42 | core/cfg/code_generator.py:388 | sym=ImportFrom | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-ae6695fa4fca | core/cfg/ast_generator_v2.py:13459 | sym=Match | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:13894` (executed=no) `elif_tests, elif_bodies, final_else = extract_elif_chain(else_body)`
- `RULE-1f2bf6bdcd1e | core/cfg/code_generator.py:262 | sym=Module | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-5aba44e010fc | core/cfg/ast_generator_v2.py:17919 | sym=NOT | scope=ASTGeneratorV2._generate_inner_while_from_block (0/94 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 3 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:11655` (executed=no) `block_ast = self._generate_inner_while_from_block(block)`
- `RULE-3ed21c936d06 | core/cfg/code_generator.py:331 | sym=Nonlocal | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-a310f7ea600b | core/cfg/ast_generator_v2.py:23481 | sym=PREP_RERAISE_STAR | scope=ASTGeneratorV2._process_instruction_sequence (0/3627 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 8 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:14435` (executed=no) `assignment_ast = self._process_instruction_sequence(assignment_instrs)`
- `RULE-d1e1d76ee83d | core/cfg/ast_generator_v2.py:11556 | sym=PRINT_EXPR | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:9197` (executed=no) `nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=True, _entry_block_pro`
- `RULE-b611d12faec6 | core/cfg/ast_generator_v2.py:11556 | sym=PRINT_ITEM | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:9197` (executed=no) `nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=True, _entry_block_pro`
- `RULE-beabfd586993 | core/cfg/ast_generator_v2.py:11556 | sym=PRINT_NEWLINE | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:9197` (executed=no) `nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=True, _entry_block_pro`
- `RULE-cc118c63f579 | core/cfg/code_generator.py:318 | sym=Pass | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/code_generator.py:133` (executed=no) `self._generate_dict_node(node)`
- `RULE-0bc203be8823 | core/cfg/ast_generator_v2.py:3954 | sym=Raise | scope=ASTGeneratorV2._remove_unreachable_code (0/38 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:3861` (executed=no) `ast_nodes = self._remove_unreachable_code(ast_nodes)`
- `RULE-85708f1fc4e5 | core/cfg/ast_generator_v2.py:21979 | sym=SETUP_WITH | scope=ASTGeneratorV2._extract_with_context (0/14 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 0 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
- `RULE-cbb06f6eb54d | core/cfg/ast_generator_v2.py:13459 | sym=Try | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:13894` (executed=no) `elif_tests, elif_bodies, final_else = extract_elif_chain(else_body)`
- `RULE-6048d12971c9 | core/cfg/ast_generator_v2.py:13459 | sym=While | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:13894` (executed=no) `elif_tests, elif_bodies, final_else = extract_elif_chain(else_body)`
- `RULE-7ccfdf2f5d77 | core/cfg/ast_generator_v2.py:3965 | sym=With | scope=ASTGeneratorV2._remove_unreachable_code (0/38 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:3861` (executed=no) `ast_nodes = self._remove_unreachable_code(ast_nodes)`
- `RULE-9ba093d040b1 | core/cfg/ast_generator_v2.py:8527 | sym=YIELD | scope=ASTGeneratorV2._generate_block_content_skip_iterator (0/2225 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 8 (executed 0) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:6684` (executed=no) `content = self._generate_block_content_skip_iterator(current)`
- `RULE-8fc89ce420ac | core/cfg/ast_generator_v2.py:3330 | sym=_APPEND_OPS | scope=ExpressionReconstructor._extract_comp_elt (0/88 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/ast_generator_v2.py:3285` (executed=no) `'elt': self._extract_comp_elt(instrs),`
- `RULE-e950c889b956 | core/cfg/region_analyzer.py:16977 | sym=_BIND_STORE_OPS | scope=RegionAnalyzer._extract_with_items._parse_bind_unpack (0/44 lines executed) | importers: consumer=10 barrel=1 cli=3 | caller-refs 2 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/region_analyzer.py:16991` (executed=no) `_sub, _nj = _parse_bind_unpack(j)`
- `RULE-a6c5590d7e93 | core/cfg/region_analyzer.py:16990 | sym=_BIND_UNPACK_OPS | scope=RegionAnalyzer._extract_with_items._parse_bind_unpack (0/44 lines executed) | importers: consumer=10 barrel=1 cli=3 | caller-refs 2 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/region_analyzer.py:16991` (executed=no) `_sub, _nj = _parse_bind_unpack(j)`
- `RULE-996e7c860ca0 | core/cfg/region_ast_generator.py:65140 | sym=_DELETE_NAME_OPS | scope=RegionASTGenerator._build_multi_target_del_targets (0/88 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/region_ast_generator.py:65044` (executed=no) `_mt_targets = self._build_multi_target_del_targets(`
- `RULE-31256e3fd90e | core/cfg/region_ast_generator.py:55933 | sym=_STORE_OPS_R2P02 | scope=RegionASTGenerator._build_ternary_boolop_condition (0/171 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 2 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/region_ast_generator.py:58089` (executed=no) `_build_ternary_boolop_condition(region) 构建 BoolOp AST 作为 test。`
- `RULE-5c5d7b71d2bb | core/cfg/region_ast_generator.py:78449 | sym=_skip_ops | scope=RegionASTGenerator._generate_return_ast (0/122 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 19 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/region_ast_generator.py:8998` (executed=no) `_ret_ast = self._generate_return_ast(_bsucc)`
- `RULE-048e69dc7408 | core/cfg/region_ast_generator.py:55935 | sym=_v105_sub_attr | scope=RegionASTGenerator._build_ternary_boolop_condition (0/171 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 2 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/region_ast_generator.py:58089` (executed=no) `_build_ternary_boolop_condition(region) 构建 BoolOp AST 作为 test。`
- `RULE-60fc44ca8092 | core/cfg/basic_block.py:193 | sym=conditional_ops | scope=BasicBlock.is_conditional (0/23 lines executed) | importers: consumer=22 barrel=1 cli=0 | caller-refs 0 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
- `RULE-b0bb824910b4 | core/cfg/ast_generator_v2.py:4906 | sym=return | scope=ASTGeneratorV2._extract_function_args (0/228 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 8 (executed 2) | pycdc-closure=yes | D2/class_never_constructed`
  - first code call site: `core/cfg/ast_generator_v2.py:3858` (executed=no) `args_info = self._extract_function_args(code_obj, kwonly_names=kwonly_names)`
- `RULE-26ee397f261c | core/cfg/region_ast_generator.py:78394 | sym=skip_ops | scope=RegionASTGenerator._generate_return_ast (0/122 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 19 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered`
  - first code call site: `core/cfg/region_ast_generator.py:8998` (executed=no) `_ret_ast = self._generate_return_ast(_bsucc)`

## 5. D3 list (21 rules, reachable but needs a new input shape)

These functions **did execute** (`scope_lines_executed > 0`), so they cannot be excluded as unreachable; what is missing is a J entry that triggers the branch. The shapes below are **hypotheses inferred from the branch guard** and have not yet been proven by a probe.

| rule | location | scope | executed lines | candidate input shape (unverified) |
|---|---|---|---:|---|
| `RULE-adbedd33701f` | `core/cfg/code_generator.py:4085` | `CodeGenerator._generate_expression` | 155/527 | a dict `FunctionObject` node (lambda / genexpr value) whose `code` field is itself a dict `CodeObject`: the `'<genexpr>'` branch needs a `closure` Tuple, the `'<lambda>'` branch renders a placeholder (`code_generator.py:4085-4098`). `_generate_expression` already executed 155/527 lines and its dict entry (`code_generator.py:3778`) did fire, so dict expression nodes do arrive; but the region pipeline normally rewrites FunctionObjects into `Lambda` via `_convert_lambda_function_objects` (`region_ast_generator.py:33688`), so this arm only fires for a shape that survives that conversion. Not yet demonstrated. |
| `RULE-05ce2ee31a3b` | `core/cfg/region_ast_generator.py:13577` | `RegionASTGenerator._loop_handle_header` | 242/797 | a loop header whose prefix contains `IS_OP/IS_NOT/NOT_OP/UNARY_NOT` (`while x is not y:` / `while not f():`) and ends with an assignment statement. |
| `RULE-1cd90d76c906` | `core/cfg/region_ast_generator.py:13577` | `RegionASTGenerator._loop_handle_header` | 242/797 | a loop header whose prefix contains `IS_OP/IS_NOT/NOT_OP/UNARY_NOT` (`while x is not y:` / `while not f():`) and ends with an assignment statement. |
| `RULE-18912491428c` | `core/cfg/region_analyzer.py:8237` | `RegionAnalyzer._is_except_break_exit` | 7/40 | try/except inside a loop where the handler ends with `break` after `POP_EXCEPT` (`PURE_JUMP_OPS`/`POP_BLOCK`). |
| `RULE-a197991fd9e1` | `core/cfg/region_analyzer.py:8246` | `RegionAnalyzer._is_except_break_exit` | 7/40 | try/except inside a loop where the handler ends with `break` after `POP_EXCEPT` (`PURE_JUMP_OPS`/`POP_BLOCK`). |
| `RULE-9890ff971e58` | `core/cfg/region_ast_generator.py:41678` | `RegionASTGenerator._generate_try` | 709/2164 | a nested outer-try handler block containing `CHECK_EXC_MATCH`/`CHECK_EG_MATCH` (`except E as e:` type matching). |
| `RULE-b2e2ae122393` | `core/cfg/region_analyzer.py:8235` | `RegionAnalyzer._is_except_break_exit` | 7/40 | try/except inside a loop where the handler ends with `break` after `POP_EXCEPT` (`PURE_JUMP_OPS`/`POP_BLOCK`). |
| `RULE-cd390e67679f` | `core/cfg/region_ast_generator.py:54367` | `RegionASTGenerator._generate_boolop_impl` | 506/1935 | a boolop whose prefix instructions contain `STORE_*` (the `flag = a and b` shape where the prefix stores an intermediate value before the expression is rebuilt). |
| `RULE-532506346aa4` | `core/cfg/region_ast_generator.py:76375` | `RegionASTGenerator._build_chained_complex_target_assign` | 5/183 | chained complex target assignment `a.b = c[d] = expr` (several non-name targets). |
| `RULE-f3e459303717` | `core/cfg/region_ast_generator.py:14671` | `RegionASTGenerator._b33_await_owner_merged_stmts` | 20/151 | `async with a() as x, b() as y:` (merged multi-owner with a noise instruction run). |
| `RULE-d7cb17e16c13` | `core/cfg/comprehension_generator.py:4064` | `ComprehensionGenerator._b247_mixed_boolchain` | 24/279 | a mixed and/or boolean chain (`a and b or c`) in a comprehension / ternary context. |
| `RULE-eea05924d17d` | `core/cfg/region_ast_generator.py:22142` | `RegionASTGenerator._try_build_ternary_operand_chained_compare` | 8/223 | a conditional expression whose operand is a chained compare (`x if a < b < c else y`). |
| `RULE-54c66455c6d9` | `core/cfg/comprehension_generator.py:298` | `ComprehensionGenerator.try_generate_comprehension_assign` | 193/588 | a comprehension assignment `x = [i for i in y]` whose code object instruction stream hits the `_cso` set. |
| `RULE-51fbefc39b4b` | `core/cfg/region_ast_generator.py:46427` | `RegionASTGenerator._b86_complete_with_items` | 39/124 | a `with` target that is an attribute/subscript (`with a() as obj.attr:`). |
| `RULE-ba395f773988` | `core/cfg/comprehension_generator.py:856` | `ComprehensionGenerator._find_returns_pending_value_successor` | 26/109 | a tail-of-body return whose value needs frame bookkeeping instructions (`PUSH_NULL`/`CACHE`). |
| `RULE-eb169da1a935` | `core/cfg/region_ast_generator.py:44096` | `RegionASTGenerator._generate_handler_body_statements` | 439/1285 | an except body whose prefix contains noise instructions (`RESUME`/`POP_TOP`, ...). |
| `RULE-9eea46812142` | `core/cfg/comprehension_generator.py:1902` | `ComprehensionGenerator._value_chain_key_split_point` | 2/31 | a value chain with an unconditional jump in the middle of the key split. |
| `RULE-969c990c53ef` | `core/cfg/region_ast_generator.py:76690` | `RegionASTGenerator._build_multi_target_unpack` | 9/124 | multi-target unpacking `a, b = c = ...` or `(a, b), c = ...`. |
| `RULE-e8aa239b163e` | `core/cfg/region_ast_generator.py:7838` | `RegionASTGenerator._generate_loop` | 125/424 | `x = yield from it` (the STORE that closes a yield-from). |
| `RULE-a8dffc095ffd` | `core/cfg/region_ast_generator.py:53295` | `RegionASTGenerator._build_boolop_augassign_target` | 3/92 | boolop augmented assignment to an attribute/subscript target: `obj.attr += a and b` / `obj[k] += a and b`. |
| `RULE-e255ab564575` | `core/cfg/region_ast_generator.py:53329` | `RegionASTGenerator._build_boolop_augassign_target` | 3/92 | boolop augmented assignment to an attribute/subscript target: `obj.attr += a and b` / `obj[k] += a and b`. |

## 6. Route A / Route B scale estimates (not executed)

### Route A: extend the tracer to the legacy / CLI paths

**What to change** (`fresh/g4_audit/trace_g4_current.py`, about +10 lines):

1. For every pyc, reuse the **same `cfg`** and additionally run the legacy pipeline: `legacy_ast = generate_ast_v2(cfg)` (`ast_generator_v2.py`'s `generate_ast_v2(cfg, recursive=True)` takes a `ControlFlowGraph`, not a code object) then `CodeGenerator().generate(legacy_ast)` (the dict entry at `code_generator.py:110/133`). `generate_ast_v2` constructs `ASTGeneratorV2`, whose `__init__` (`ast_generator_v2.py:3508`) constructs `StructuredAnalyzer`.
2. Optional: call `ObjectivePatchDetector().analyze_file(...)` / `P2Detector` explicitly (offline detectors).
3. Take the **union** of rule hits from both pipelines; the `records` schema of `traces_v2` stays unchanged.
4. Note `CFGCodeGenerator` is only an alias of `CodeGenerator` (`code_generator.py:6715`), so the dict entry and the current tracer entry are the **same class**; the only difference is whether a `dict` or an `ASTNode` is passed in.

**Upper bound on rules saved** (must be measured, not promised):

| sub-route | target rules | count | note |
|---|---|---:|---|
| A1 legacy decompile pipeline | `CodeGenerator._generate_dict_node` 16 + `ASTGeneratorV2.*` 32 + `StructuredAnalyzer.*` 7 + `exception_handler._find_handler_type_load` 1 | **56** | all unlocked by one `generate_ast_v2` entry |
| A2 offline detectors | `ObjectivePatchDetector.*` 11 + `P*Detector.*` 4 | **15** | only by explicitly invoking a detector that is not on the decompile path |
| A3 new input shapes | the D3 21 rules | **0** | a tracer change cannot help; new J entries are required |

**Risks:**

- Wording risk: the gate would move from "the live `pycdc.py` path is covered" to "some pipeline touches it", and legacy `ASTGeneratorV2`/`StructuredAnalyzer` are exactly the paths `pycdc.py` does not take - trading a wider input domain for a lower `empty_cov` weakens the completeness claim.
- Engineering risk: `ast_generator_v2.py` (27691 lines) and `structured_analyzer.py` (16096 lines) are legacy code and may raise or hang on 3.11 bytecode; the tracer wraps each entry in `try/except BaseException`, so any failure lands in `failed_entries` and the reading itself must be discounted.
- Domain risk: `patch_detector` / `objective_patch_detector` are **patch detectors**; running them only proves "the detector runs", not "the decompile path is covered".
- Bottom line: A1 can at best push `empty_cov` from 100 down to 21 (= D3); A1+A2 fully successful still leaves `empty_cov = 21`. **G4 stays FAIL** because `proved = 0`.

### Route B: exclude D1/D2 from the universe by review

**Evidence needed:** the per-rule evidence in this dossier (importer counts + executed lines + call sites) plus reviewer sign-off. Note `rule_universe.py` has **no exclusion mechanism**: the universe is mechanically enumerated from the source (`tools/completeness/rule_universe.py:166-208`), so an "exclusion" requires introducing a `reviewed_exclusions` list into the tool or the universe - a tool change, out of scope for this read-only round.

**After exclusion:**

| scenario | universe | empty_cov | gate reading |
|---|---:|---:|---|
| current | 344 | 100 | FAIL `mapping_or_proof_gap` |
| exclude D1 (23) | 321 | 77 | FAIL `mapping_or_proof_gap` |
| exclude D1+D2 (79) | 265 | **21** | FAIL `mapping_or_proof_gap` |
| exclude D1+D2+D3 (100) | 244 | **0** | **FAIL `not_all_proved`** |

**Can it PASS: no.** The last row is the decisive one: once `empty_cov` reaches 0, `rule_manifest.py --check` falls through to `elif ready != total: g4="FAIL"; reason="not_all_proved"` (`tools/completeness/rule_manifest.py:193-195`).

### The missing item: proof / composition theory (neither the tracer nor the exclusion)

The PASS criterion is `ready == total`, where `ready` counts only rules with `status == "proved"` that satisfy **all four** obligations (`rule_manifest.py:157-172`):

1. `witnesses.positive` and `witnesses.negative` both non-empty, and every id present in the J space (`_witness_ok`, `rule_manifest.py:106-116`);
2. `semantic_domain.hosts` and `semantic_domain.depths` both non-empty (`_domain_ok`, `rule_manifest.py:119-124`);
3. `proof.proof_id` non-empty;
4. `composition` non-empty (`rule_manifest.py:163-165`).

But `--generate` emits exactly the empty defaults for those four fields (`rule_manifest.py:49-76`: `semantic_domain={hosts:[],depths:[],note:"not declared in v1"}`, `witnesses={positive:[],negative:[]}`, `composition=[]`, `proof.proof_id=None`, `status="open"`), and `proved` has been **0** in every historical reading (this round: 0 of 344, all `open`).

So the missing item is the **per-rule semantic proof and composition obligation**: under which hosts/depths the rule holds (`semantic_domain`), positive and negative witnesses, a `proof_id` pointing at a checker, and the **composition** between rules (in the three stages region reduction -> AST generation -> code generation, how the output of rule A becomes the precondition of rule B). This round only closes the *reachability* half (which 100 rules are not executed and why); it does not close that half.

## 7. Appendix: one evidence line per rule (100 rules, machine generated)

```text
RULE-d53ac6879d6a | core/cfg/patch_detector.py:328 | sym=Assign | scope=P1Detector._is_local_region_var (0/14 lines executed) | importers: consumer=0 barrel=0 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-b3b3c27de3f4 | core/cfg/objective_patch_detector.py:89 | sym=AsyncFunctionDef | scope=ObjectivePatchDetector.analyze_file (0/29 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-526c2f9c8010 | core/cfg/objective_patch_detector.py:197 | sym=Attribute | scope=ObjectivePatchDetector._extract_test_pattern (0/15 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-20568d2871b4 | core/cfg/objective_patch_detector.py:195 | sym=BoolOp | scope=ObjectivePatchDetector._extract_test_pattern (0/15 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-93efbfe2473b | core/cfg/objective_patch_detector.py:199 | sym=Call | scope=ObjectivePatchDetector._extract_test_pattern (0/15 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-2845ddf0b9b8 | core/cfg/objective_patch_detector.py:93 | sym=ClassDef | scope=ObjectivePatchDetector.analyze_file (0/29 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-2b862ecf9a11 | core/cfg/objective_patch_detector.py:191 | sym=Compare | scope=ObjectivePatchDetector._extract_test_pattern (0/15 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-1f3252f64295 | core/cfg/objective_patch_detector.py:213 | sym=Constant | scope=ObjectivePatchDetector._node_signature (0/11 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 5 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-2d4b43ea95f6 | core/cfg/objective_patch_detector.py:89 | sym=FunctionDef | scope=ObjectivePatchDetector.analyze_file (0/29 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-3d070d0913cc | core/cfg/objective_patch_detector.py:181 | sym=If | scope=ObjectivePatchDetector._check_d2_special_branches (0/11 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 1 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-4c10258ace4e | core/cfg/patch_detector.py:425 | sym=List | scope=P2Detector._extract_opname_strings (0/15 lines executed) | importers: consumer=0 barrel=0 cli=0 | caller-refs 2 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-b56901a142a6 | core/cfg/objective_patch_detector.py:207 | sym=Name | scope=ObjectivePatchDetector._node_signature (0/11 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 5 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-bd1b6b8bb350 | core/cfg/patch_detector.py:425 | sym=Set | scope=P2Detector._extract_opname_strings (0/15 lines executed) | importers: consumer=0 barrel=0 cli=0 | caller-refs 2 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-fd29f404c20d | core/cfg/objective_patch_detector.py:211 | sym=Subscript | scope=ObjectivePatchDetector._node_signature (0/11 lines executed) | importers: consumer=0 barrel=0 cli=2 | caller-refs 5 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-87d3e450c5e4 | core/cfg/patch_detector.py:425 | sym=Tuple | scope=P2Detector._extract_opname_strings (0/15 lines executed) | importers: consumer=0 barrel=0 cli=0 | caller-refs 2 (executed 0) | pycdc-closure=no | D1/no_consumer_importer
RULE-eb29ec1ad01a | core/cfg/code_generator.py:285 | sym=AnnAssign | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-1b5b4d7115d9 | core/cfg/code_generator.py:378 | sym=Assert | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-eed79a22277c | core/cfg/code_generator.py:283 | sym=Assign | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-0b22204ea11f | core/cfg/code_generator.py:277 | sym=AsyncFor | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-702b6dd6ca34 | core/cfg/code_generator.py:367 | sym=AsyncFunctionDef | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-42045b244e8a | core/cfg/ast_generator_v2.py:3965 | sym=AsyncWith | scope=ASTGeneratorV2._remove_unreachable_code (0/38 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-3b46d229d0af | core/cfg/code_generator.py:281 | sym=AugAssign | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-cd714078ea23 | core/cfg/ast_generator_v2.py:6568 | sym=BINARY_ADD | scope=ASTGeneratorV2._generate_entry_sequence (0/624 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-c56bc072e6e4 | core/cfg/ast_generator_v2.py:13181 | sym=BINARY_AND | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-dda45a0ced72 | core/cfg/ast_generator_v2.py:10477 | sym=BINARY_DIVIDE | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-5361acaaa053 | core/cfg/ast_generator_v2.py:10477 | sym=BINARY_FLOOR_DIVIDE | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-c7b3c96bb6c8 | core/cfg/ast_generator_v2.py:10477 | sym=BINARY_MODULO | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-0062e270c4a1 | core/cfg/ast_generator_v2.py:6568 | sym=BINARY_MULTIPLY | scope=ASTGeneratorV2._generate_entry_sequence (0/624 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-bcde89ee3e2a | core/cfg/ast_generator_v2.py:13181 | sym=BINARY_OR | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-2675d342ef0c | core/cfg/ast_generator_v2.py:6568 | sym=BINARY_SUBTRACT | scope=ASTGeneratorV2._generate_entry_sequence (0/624 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-f1bef410c01e | core/cfg/ast_generator_v2.py:10477 | sym=BINARY_TRUE_DIVIDE | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-010c1b2cf1d7 | core/cfg/ast_generator_v2.py:13459 | sym=Break | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-1c8e48e5d568 | core/cfg/ast_generator_v2.py:7387 | sym=CALL_KW | scope=ASTGeneratorV2._generate_block_content_skip_iterator (0/2225 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 8 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-dff33ce626a7 | core/cfg/code_generator.py:369 | sym=ClassDef | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-6ce83d58fb8b | core/cfg/ast_generator_v2.py:13459 | sym=Continue | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-a758f665e9f5 | core/cfg/ast_generator_v2.py:5966 | sym=DICT_ADD | scope=ASTGeneratorV2._generate_comprehension_function (0/216 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-fac0e268c522 | core/cfg/structured_analyzer.py:13926 | sym=DUP_TOP | scope=StructuredAnalyzer._identify_with_structures (0/152 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes
RULE-7f1501983cc4 | core/cfg/structured_analyzer.py:13926 | sym=DUP_TOP_TWO | scope=StructuredAnalyzer._identify_with_structures (0/152 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes
RULE-8c816c79d0c7 | core/cfg/code_generator.py:324 | sym=Delete | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-df8d199ebe90 | core/cfg/code_generator.py:289 | sym=Expr | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-cdc6b865739a | core/cfg/ast_generator_v2.py:26984 | sym=FOR_ITER_RANGE | scope=ASTGeneratorV2._extract_iterator_v2 (0/72 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-681e794c6afb | core/cfg/ast_generator_v2.py:13459 | sym=For | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-d712e20d2506 | core/cfg/code_generator.py:365 | sym=FunctionDef | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-adbedd33701f | core/cfg/code_generator.py:4085 | sym=FunctionObject | scope=CodeGenerator._generate_expression (155/527 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 244 (executed 87) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-05f8183d28bc | core/cfg/ast_generator_v2.py:10653 | sym=GET_ATTR | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-a99b10fa310d | core/cfg/code_generator.py:326 | sym=Global | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-05ce2ee31a3b | core/cfg/region_ast_generator.py:13577 | sym=IS_NOT | scope=RegionASTGenerator._loop_handle_header (242/797 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-1fbb15a6c511 | core/cfg/ast_generator_v2.py:3992 | sym=If | scope=ASTGeneratorV2._has_terminal_statement (0/26 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 4 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-3c8a43d55e71 | core/cfg/code_generator.py:388 | sym=Import | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-1601748f4b42 | core/cfg/code_generator.py:388 | sym=ImportFrom | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-ae6695fa4fca | core/cfg/ast_generator_v2.py:13459 | sym=Match | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-1f2bf6bdcd1e | core/cfg/code_generator.py:262 | sym=Module | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-5aba44e010fc | core/cfg/ast_generator_v2.py:17919 | sym=NOT | scope=ASTGeneratorV2._generate_inner_while_from_block (0/94 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 3 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-1cd90d76c906 | core/cfg/region_ast_generator.py:13577 | sym=NOT_OP | scope=RegionASTGenerator._loop_handle_header (242/797 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-3ed21c936d06 | core/cfg/code_generator.py:331 | sym=Nonlocal | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-18912491428c | core/cfg/region_analyzer.py:8237 | sym=POP_BLOCK | scope=RegionAnalyzer._is_except_break_exit (7/40 lines executed) | importers: consumer=10 barrel=1 cli=3 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-a310f7ea600b | core/cfg/ast_generator_v2.py:23481 | sym=PREP_RERAISE_STAR | scope=ASTGeneratorV2._process_instruction_sequence (0/3627 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 8 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-d1e1d76ee83d | core/cfg/ast_generator_v2.py:11556 | sym=PRINT_EXPR | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-b611d12faec6 | core/cfg/ast_generator_v2.py:11556 | sym=PRINT_ITEM | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-beabfd586993 | core/cfg/ast_generator_v2.py:11556 | sym=PRINT_NEWLINE | scope=ASTGeneratorV2._generate_if_ast (0/3938 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 33 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-a197991fd9e1 | core/cfg/region_analyzer.py:8246 | sym=PURE_JUMP_OPS | scope=RegionAnalyzer._is_except_break_exit (7/40 lines executed) | importers: consumer=10 barrel=1 cli=3 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-cc118c63f579 | core/cfg/code_generator.py:318 | sym=Pass | scope=CodeGenerator._generate_dict_node (0/212 lines executed) | importers: consumer=2 barrel=3 cli=2 | caller-refs 20 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-a2f801d5aefb | core/cfg/structured_analyzer.py:13926 | sym=ROT_THREE | scope=StructuredAnalyzer._identify_with_structures (0/152 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes
RULE-c708889ddc61 | core/cfg/structured_analyzer.py:13926 | sym=ROT_TWO | scope=StructuredAnalyzer._identify_with_structures (0/152 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes
RULE-0bc203be8823 | core/cfg/ast_generator_v2.py:3954 | sym=Raise | scope=ASTGeneratorV2._remove_unreachable_code (0/38 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-36dde631fda0 | core/cfg/structured_analyzer.py:13288 | sym=SETUP_EXCEPT | scope=StructuredAnalyzer._identify_try_except_pre_311 (0/28 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes
RULE-36f063d106a0 | core/cfg/structured_analyzer.py:13288 | sym=SETUP_FINALLY | scope=StructuredAnalyzer._identify_try_except_pre_311 (0/28 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes
RULE-85708f1fc4e5 | core/cfg/ast_generator_v2.py:21979 | sym=SETUP_WITH | scope=ASTGeneratorV2._extract_with_context (0/14 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 0 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-cbb06f6eb54d | core/cfg/ast_generator_v2.py:13459 | sym=Try | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-c500ada1eadd | core/cfg/structured_analyzer.py:13926 | sym=UNARY_OP | scope=StructuredAnalyzer._identify_with_structures (0/152 lines executed) | importers: consumer=3 barrel=1 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes
RULE-6048d12971c9 | core/cfg/ast_generator_v2.py:13459 | sym=While | scope=ASTGeneratorV2._generate_if_ast.extract_elif_chain (0/115 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-7ccfdf2f5d77 | core/cfg/ast_generator_v2.py:3965 | sym=With | scope=ASTGeneratorV2._remove_unreachable_code (0/38 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-9ba093d040b1 | core/cfg/ast_generator_v2.py:8527 | sym=YIELD | scope=ASTGeneratorV2._generate_block_content_skip_iterator (0/2225 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 8 (executed 0) | pycdc-closure=yes | D2/class_never_constructed
RULE-8fc89ce420ac | core/cfg/ast_generator_v2.py:3330 | sym=_APPEND_OPS | scope=ExpressionReconstructor._extract_comp_elt (0/88 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-e950c889b956 | core/cfg/region_analyzer.py:16977 | sym=_BIND_STORE_OPS | scope=RegionAnalyzer._extract_with_items._parse_bind_unpack (0/44 lines executed) | importers: consumer=10 barrel=1 cli=3 | caller-refs 2 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-a6c5590d7e93 | core/cfg/region_analyzer.py:16990 | sym=_BIND_UNPACK_OPS | scope=RegionAnalyzer._extract_with_items._parse_bind_unpack (0/44 lines executed) | importers: consumer=10 barrel=1 cli=3 | caller-refs 2 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-9890ff971e58 | core/cfg/region_ast_generator.py:41678 | sym=_CHECK_OPS_r08b | scope=RegionASTGenerator._generate_try (709/2164 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 10 (executed 5) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-996e7c860ca0 | core/cfg/region_ast_generator.py:65140 | sym=_DELETE_NAME_OPS | scope=RegionASTGenerator._build_multi_target_del_targets (0/88 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 1 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-b2e2ae122393 | core/cfg/region_analyzer.py:8235 | sym=_NOISE | scope=RegionAnalyzer._is_except_break_exit (7/40 lines executed) | importers: consumer=10 barrel=1 cli=3 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-cd390e67679f | core/cfg/region_ast_generator.py:54367 | sym=_STORE_CHK_R02 | scope=RegionASTGenerator._generate_boolop_impl (506/1935 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-31256e3fd90e | core/cfg/region_ast_generator.py:55933 | sym=_STORE_OPS_R2P02 | scope=RegionASTGenerator._build_ternary_boolop_condition (0/171 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 2 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-137de19b1304 | core/cfg/exception_handler.py:88 | sym=_UNCOND_JUMP_TARGET_OPS | scope=_find_handler_type_load (0/62 lines executed) | importers: consumer=1 barrel=0 cli=0 | caller-refs 2 (executed 0) | pycdc-closure=yes | D1/consumer_importer_never_executes
RULE-532506346aa4 | core/cfg/region_ast_generator.py:76375 | sym=_b107_store_ops | scope=RegionASTGenerator._build_chained_complex_target_assign (5/183 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 5 (executed 5) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-f3e459303717 | core/cfg/region_ast_generator.py:14671 | sym=_b33_noise | scope=RegionASTGenerator._b33_await_owner_merged_stmts (20/151 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-d7cb17e16c13 | core/cfg/comprehension_generator.py:4064 | sym=_bounce_names | scope=ComprehensionGenerator._b247_mixed_boolchain (24/279 lines executed) | importers: consumer=3 barrel=0 cli=0 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-eea05924d17d | core/cfg/region_ast_generator.py:22142 | sym=_cmp_ops_set | scope=RegionASTGenerator._try_build_ternary_operand_chained_compare (8/223 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 2 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-54c66455c6d9 | core/cfg/comprehension_generator.py:298 | sym=_cso | scope=ComprehensionGenerator.try_generate_comprehension_assign (193/588 lines executed) | importers: consumer=3 barrel=0 cli=0 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-51fbefc39b4b | core/cfg/region_ast_generator.py:46427 | sym=_ctx_value_ops | scope=RegionASTGenerator._b86_complete_with_items (39/124 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-ba395f773988 | core/cfg/comprehension_generator.py:856 | sym=_frame_bookkeeping | scope=ComprehensionGenerator._find_returns_pending_value_successor (26/109 lines executed) | importers: consumer=3 barrel=0 cli=0 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-eb169da1a935 | core/cfg/region_ast_generator.py:44096 | sym=_hb_noise_ops | scope=RegionASTGenerator._generate_handler_body_statements (439/1285 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 13 (executed 3) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-9eea46812142 | core/cfg/comprehension_generator.py:1902 | sym=_jump_ops | scope=ComprehensionGenerator._value_chain_key_split_point (2/31 lines executed) | importers: consumer=3 barrel=0 cli=0 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-969c990c53ef | core/cfg/region_ast_generator.py:76690 | sym=_mt_store_ops | scope=RegionASTGenerator._build_multi_target_unpack (9/124 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 2 (executed 2) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-5c5d7b71d2bb | core/cfg/region_ast_generator.py:78449 | sym=_skip_ops | scope=RegionASTGenerator._generate_return_ast (0/122 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 19 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-048e69dc7408 | core/cfg/region_ast_generator.py:55935 | sym=_v105_sub_attr | scope=RegionASTGenerator._build_ternary_boolop_condition (0/171 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 2 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-e8aa239b163e | core/cfg/region_ast_generator.py:7838 | sym=_yf_store_ops | scope=RegionASTGenerator._generate_loop (125/424 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 2 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-a8dffc095ffd | core/cfg/region_ast_generator.py:53295 | sym=attr | scope=RegionASTGenerator._build_boolop_augassign_target (3/92 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
RULE-60fc44ca8092 | core/cfg/basic_block.py:193 | sym=conditional_ops | scope=BasicBlock.is_conditional (0/23 lines executed) | importers: consumer=22 barrel=1 cli=0 | caller-refs 0 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-b0bb824910b4 | core/cfg/ast_generator_v2.py:4906 | sym=return | scope=ASTGeneratorV2._extract_function_args (0/228 lines executed) | importers: consumer=5 barrel=2 cli=0 | caller-refs 8 (executed 2) | pycdc-closure=yes | D2/class_never_constructed
RULE-26ee397f261c | core/cfg/region_ast_generator.py:78394 | sym=skip_ops | scope=RegionASTGenerator._generate_return_ast (0/122 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 19 (executed 0) | pycdc-closure=yes | D2/class_live_callee_unentered
RULE-e255ab564575 | core/cfg/region_ast_generator.py:53329 | sym=subscr | scope=RegionASTGenerator._build_boolop_augassign_target (3/92 lines executed) | importers: consumer=0 barrel=2 cli=4 | caller-refs 1 (executed 1) | pycdc-closure=yes | D3/function_entered_branch_unhit
```

## 8. How to recompute

```powershell
# executed lines (runtime evidence)
python -I -X utf8 fresh/gate_gap/_gap_exec.py \
  --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
  --out D:/temp/opencode/cl_layout/gap/gap_exec_v2.json
# tiering + evidence lines + this document
python -I -X utf8 fresh/gate_gap/_gap_dossier.py \
  --universe fresh/gate_gap/universe_v2.json \
  --coverage fresh/gate_gap/coverage_v2.json \
  --exec D:/temp/opencode/cl_layout/gap/gap_exec_v2.json \
  --out-json fresh/gate_gap/g4_unreachable.json \
  --out-md fresh/gate_gap/G4_UNREACHABLE_DOSSIER.md
```

