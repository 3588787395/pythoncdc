## Context

The pythoncdc decompiler uses a region-based approach: CFG → dominator analysis → region identification → AST generation → code output. Three core files handle this:

- `core/cfg/region_analyzer.py` (~11800 lines): Region identification (if, loop, try, with, match, assert, boolop, ternary)
- `core/cfg/region_ast_generator.py` (~14700 lines): AST generation from identified regions
- `core/cfg/code_generator.py` (~4700 lines): Python source code from AST

Current test coverage: 327 control_flow_matrix unit tests pass. Prior ad-hoc iteration testing revealed:
- tryexcept: ~10% failure before POP_TOP fix → now 0/200
- match: ~17% failure before NOP heuristic fix → now 0/200 (multi-case)
- if/with/loop/ternary/boolop/assert: 0/200 each in quick checks

However, these quick checks used only 200 patterns per type with simple generators. The 8×20 protocol requires sustained 20-round testing per region with progressively harder patterns, collecting ≥10 bugs per round before fixing. This stress-tests edge cases not covered by simple generators.

## Goals / Non-Goals

**Goals:**
- Implement 8×20 iteration testing protocol: 8 region types × 20 rounds each
- Each round: generate patterns until ≥10 bugs found → record all bugs → fix all → verify zero → round done
- Per-region per-round file storage for reproducibility
- Bug catalog with source, decompiled output, error type, fix description
- Enhanced pattern generators that increase complexity across rounds
- Complete all 160 rounds (8 types × 20 rounds); no stopping before all done
- Drive actual bug fixes in region_analyzer.py, region_ast_generator.py, code_generator.py

**Non-Goals:**
- Single-case match → if/else ambiguity (C-class, fundamentally indistinguishable from bytecode)
- While-True no back-edge (D-class, partial fix exists, low priority)
- BoolOp+Ternary edge cases requiring deep chain-detection refactoring
- Performance optimization of the decompiler itself
- New region types beyond the 8 currently supported

## Decisions

### D1: Round protocol — collect-then-fix

**Decision**: A round only counts if ≥10 bug instances are collected. If <10 bugs found after exhaustive generation, the round doesn't count and we move to next region type or use harder generators.

**Rationale**: The user's explicit requirement: "收集到10个错误实例，才开始解决，解决完才算一轮。那有一次执行20轮是说法。找不到错误一次也不算。" This prevents gaming the metric by counting trivial rounds.

**Alternative considered**: Count rounds regardless of bug count — rejected because it would inflate metrics without genuine bug discovery.

### D2: Per-region per-round directory structure

**Decision**: `tests/iteration/regions/<region-type>/round-<N>/` with files:
- `patterns.py` — generated test patterns for this round
- `bugs.json` — catalog of all bug instances found
- `fix_log.md` — description of fixes applied

**Rationale**: User's explicit requirement: "创建专门目录每区域每轮存放测试文件". Enables reproducibility and audit trail.

**Alternative considered**: Single flat directory — rejected because 160 rounds × multiple files = unmanageable flat directory.

### D3: Progressive pattern complexity

**Decision**: Generators increase complexity across rounds:
- Rounds 1-5: basic patterns (single construct, simple bodies)
- Rounds 6-10: moderate complexity (nested constructs, multi-statement bodies, combined features)
- Rounds 11-15: advanced patterns (deep nesting, edge cases, unusual combinations)
- Rounds 16-20: adversarial patterns (known hard cases, boundary conditions, regression seeds from earlier rounds)

**Rationale**: Simple patterns find obvious bugs early; complex patterns stress edge cases. Re-seeding from earlier bugs prevents regression.

**Alternative considered**: Random uniform generation — rejected because it wastes rounds on already-clean patterns.

### D4: Bug definition

**Decision**: A bug is any pattern where `ast.dump(ast.parse(decompiled)) != ast.dump(ast.parse(original))` OR where decompilation raises an exception. Semantic-only differences (e.g., single-case match → if) count as bugs for match region but are tagged as "C-class" and excluded from the ≥10 threshold.

**Rationale**: Structural AST equality is objective and automatable. C-class issues are known limitations, not fixable bugs.

**Alternative considered**: Behavioral equivalence testing — rejected because it's much harder to automate and can miss structural issues.

### D5: Region processing order

**Decision**: Process regions in order: if → loop → with → tryexcept → match → assert → boolop → ternary. Earlier regions are building blocks for later ones; fixing if-region bugs may reduce bugs in nested contexts.

**Rationale**: Topological dependency — if/loop are foundational, match/with contain nested if/loop, boolop/ternary are phase-2 regions.

### D6: Automation level

**Decision**: Semi-automated — the framework auto-generates patterns and catalogs bugs, but a human (or AI agent) must implement fixes between rounds. The framework re-runs verification after fixes.

**Rationale**: Bug fixes require understanding of region analysis algorithms and cannot be mechanically generated.

## Risks / Trade-offs

- **[Risk] Some region types may have 0 bugs after initial rounds** → Mitigation: Increase generator complexity progressively; if 0 bugs after 500+ patterns at max complexity, declare region clean and skip remaining rounds
- **[Risk] C-class match ambiguity inflates bug counts** → Mitigation: Tag C-class bugs separately; they don't count toward ≥10 threshold
- **[Risk] Fix for one region type regresses another** → Mitigation: Run full control_flow_matrix test suite after every fix
- **[Risk] 160 rounds could take very long** → Mitigation: Each round is bounded by pattern count; early rounds with simple generators are fast; clean regions skip quickly
- **[Trade-off] AST equality vs semantic equivalence** → AST equality is strict but objective; some equivalent-but-different structures count as bugs, driving fixes that improve fidelity
