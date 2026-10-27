# J v3 fresh evidence (2026-10-27)

This directory re-runs the complete 1556-entry J v3 pipeline on the current
Windows tree.  It exists because the historical `COVERAGE_V3.md` binds products
under `/workspace/...` and `/tmp/j3prod/...`, which are not reproducible here.

## Environment

- CPython 3.11.7 (Windows, 64-bit), repository root as cwd.
- Judge: `tools/completeness/semantic_diff.py` (SHA256 is bound in every C5).
- Checker: `tools/completeness/coverage_checker.py` 2.0.0.
- `pyc` files are `.gitignore`d; the manifest binds their SHA256.  The run kept
  all 1556 existing pyc (`pyc_regenerated=0`, `pyc_kept=1556`,
  `pyc_failed=0`).  If a pyc is missing, `jspace_v3_prepare.py` regenerates it
  from `p_j` under `--pyc-dir`.

## Pipeline

### 1. Prepare J v3

```powershell
python -X utf8 tools/completeness/jspace_v3_prepare.py `
  --space .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json `
  --out .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/judgment_space_v3.json `
  --pyc-dir .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/pyc `
  --report .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/prepare_report.json
```

Reading: `entries=1556`, `with_calls=1086`, `without_calls=470`;
derivation reasons: 376 `unsafe_host_module: real-package module`, 94
`no_top_level_callable_with_constructible_arguments`.

### 2. Semantic shards (C1-C5)

```powershell
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/judgment_space_v3.json --out .../fresh/semantic_shard0.json `
  --report .../fresh/semantic_shard0_report.json `
  --product-dir .../fresh/semantic_products/shard0 --offset 0 --limit 519
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/judgment_space_v3.json --out .../fresh/semantic_shard1.json `
  --report .../fresh/semantic_shard1_report.json `
  --product-dir .../fresh/semantic_products/shard1 --offset 519 --limit 519
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/judgment_space_v3.json --out .../fresh/semantic_shard2.json `
  --report .../fresh/semantic_shard2_report.json `
  --product-dir .../fresh/semantic_products/shard2 --offset 1038 --limit 518
```

### 3. Merge and check

```powershell
python -X utf8 .../fresh/merge_evidence.py `
  --out .../fresh/semantic_v3_merged.json --space .../fresh/judgment_space_v3.json `
  --shard .../fresh/semantic_shard0.json `
  --shard .../fresh/semantic_shard1.json `
  --shard .../fresh/semantic_shard2.json
python -X utf8 tools/completeness/coverage_checker.py `
  --space .../fresh/judgment_space_v3.json `
  --evidence .../fresh/semantic_v3_merged.json `
  --judge tools/completeness/semantic_diff.py `
  --out .../fresh/COVERAGE_V3_FRESH.md --json .../fresh/coverage_v3_fresh.json
```

### 4. Repair the 36 load-invalid probes

See `REPAIR.md`.  Then:

```powershell
python -X utf8 .../fresh/repair_invalid_probes.py
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/repair_manifest.json --out .../fresh/semantic_repair.json `
  --report .../fresh/semantic_repair_report.json `
  --product-dir .../fresh/semantic_products/repair
python -X utf8 .../fresh/merge_evidence.py `
  --out .../fresh/semantic_v3r_merged.json --space .../fresh/judgment_space_v3r.json `
  --shard .../fresh/semantic_shard0.json --shard .../fresh/semantic_shard1.json `
  --shard .../fresh/semantic_shard2.json --repair .../fresh/semantic_repair.json
python -X utf8 tools/completeness/coverage_checker.py `
  --space .../fresh/judgment_space_v3r.json `
  --evidence .../fresh/semantic_v3r_merged.json `
  --judge tools/completeness/semantic_diff.py `
  --out .../fresh/COVERAGE_V3R.md --json .../fresh/coverage_v3r.json
```

## Readings

| Reading | Fresh baseline | After invalid-probe repair |
|---|---:|---:|
| J_total | 1556 | 1556 |
| covered_5tuple | 1050 | 1086 |
| probe_only | 0 | 0 |
| unexecuted | 0 | 0 |
| n/a | 0 | 0 |
| inconclusive | 36 | 0 |
| excluded | 470 | 470 |
| uncovered | 506 | 470 |
| semantic_failures | 0 | 0 |
| green | 1050 | 1086 |
| coverage_pct | 67.48% | 69.79% |

The fresh baseline reproduces the historical `covered_5tuple=1050` exactly.
The two historical `DIFFERENT` entries (`JS-IF-017`, `JS-IF-021`, both the
B142 nested-finally/continue family) are now `EQUAL`; `semantic_failures` is 0.
The 36 `inconclusive` entries were all caused by three load-invalid probes, not
by decompiler output; see `REPAIR.md`.

## Remaining gap

`covered_5tuple=1086/1556`; G1 still **FAIL/BLOCKED** because 470 entries are
`excluded`:

| Reason | Count | Detail |
|---|---:|---|
| `unsafe_host_module: real-package module` | 376 | Safety gate: pyc-only business-package modules may have process/network/trading side effects; dependency closure (`six`/`jsonpickle` etc.) is incomplete in the sandbox. |
| `no_top_level_callable_with_constructible_arguments` | 94 | 62 sources contain only `async def` (eval cannot await; async driver not yet derived); 32 contain only module-level statements (state-witness model not yet adopted). |

No claim of completeness is made.  The next tractable families are the 32
module-level-only probes (post-import state witnesses) and the 62 async-only
probes (sync driver over `asyncio.run`), followed by the safety-gated 376.
