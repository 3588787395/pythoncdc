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

### 5. Close the 62 async-only entries

See `ASYNC_DRIVER.md`.  The preparer emitted no calls for `async def` because a
bare `eval('fn(...)')` only creates a coroutine.  `close_async_family.py` adds
self-contained call expressions that run a fixed driver prelude in a private
namespace and invoke the module-level async entrypoint through
`asyncio.run(...)` (async generators are consumed).

```powershell
python -X utf8 .../fresh/close_async_family.py `
  --space .../fresh/judgment_space_v3r.json `
  --out-space .../fresh/judgment_space_v3a.json `
  --out-manifest .../fresh/async_manifest.json `
  --report .../fresh/async_family_report.json
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/async_manifest.json --out .../fresh/semantic_async.json `
  --report .../fresh/semantic_async_report.json `
  --product-dir .../fresh/semantic_products/async
python -X utf8 .../fresh/merge_evidence.py `
  --out .../fresh/semantic_v3a_merged.json --space .../fresh/judgment_space_v3a.json `
  --shard .../fresh/semantic_v3r_merged.json --repair .../fresh/semantic_async.json
python -X utf8 tools/completeness/coverage_checker.py `
  --space .../fresh/judgment_space_v3a.json `
  --evidence .../fresh/semantic_v3a_merged.json `
  --judge tools/completeness/semantic_diff.py `
  --out .../fresh/COVERAGE_V3A.md --json .../fresh/coverage_v3a.json
```

### 6. Close the 32 module-level-only entries

See `MODULE_WITNESS.md`.  The callable entrypoint is the original module code
object obtained from the loader:

```python
(lambda _c: __import__('types').FunctionType(_c, globals())())(
    __loader__.get_code(__name__))
```

The call re-executes the module body and the judge compares the call result,
stdout/stderr/events/files and post-call globals.  Twelve entries point at
`m04_module_try.py`, whose `with (CFG if 0 else json)` load-fails; a minimal
`_CM()` copy is written under `repaired_sources/` / `repaired_pyc/`.

```powershell
python -X utf8 .../fresh/close_module_family.py `
  --space .../fresh/judgment_space_v3a.json `
  --out-space .../fresh/judgment_space_v3m.json `
  --out-manifest .../fresh/module_manifest.json `
  --report .../fresh/module_family_report.json
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/module_manifest.json --out .../fresh/semantic_module.json `
  --report .../fresh/semantic_module_report.json `
  --product-dir .../fresh/semantic_products/module
python -X utf8 .../fresh/apply_module_results.py `
  --space .../fresh/judgment_space_v3m.json `
  --evidence .../fresh/semantic_module.json `
  --out-space .../fresh/judgment_space_v3m_applied.json `
  --out-evidence .../fresh/semantic_module_equal.json `
  --report .../fresh/module_results_report.json
python -X utf8 .../fresh/merge_evidence.py `
  --out .../fresh/semantic_v3m_merged.json `
  --space .../fresh/judgment_space_v3m_applied.json `
  --shard .../fresh/semantic_v3a_merged.json --repair .../fresh/semantic_module_equal.json
python -X utf8 tools/completeness/coverage_checker.py `
  --space .../fresh/judgment_space_v3m_applied.json `
  --evidence .../fresh/semantic_v3m_merged.json `
  --judge tools/completeness/semantic_diff.py `
  --out .../fresh/COVERAGE_V3M.md --json .../fresh/coverage_v3m.json
```

## Readings

| Reading | Fresh baseline | +36 repair | +62 async | +20 module witness |
|---|---:|---:|---:|---:|
| J_total | 1556 | 1556 | 1556 | 1556 |
| covered_5tuple | 1050 | 1086 | 1148 | 1168 |
| probe_only | 0 | 0 | 0 | 0 |
| unexecuted | 0 | 0 | 0 | 0 |
| n/a | 0 | 0 | 0 | 0 |
| inconclusive | 36 | 0 | 0 | 0 |
| excluded | 470 | 470 | 408 | 388 |
| uncovered | 506 | 470 | 408 | 388 |
| semantic_failures | 0 | 0 | 0 | 0 |
| green | 1050 | 1086 | 1148 | 1168 |
| coverage_pct | 67.48% | 69.79% | 73.78% | 75.06% |

The fresh baseline reproduces the historical `covered_5tuple=1050` exactly.
The two historical `DIFFERENT` entries (`JS-IF-017`, `JS-IF-021`, both the
B142 nested-finally/continue family) are now `EQUAL`; `semantic_failures` is 0.
The 36 `inconclusive` entries were all caused by three load-invalid probes, not
by decompiler output; see `REPAIR.md`.

The 62 async entries are all `EQUAL` under the `asyncio.run` driver.  The 20
`m06`/`m08` module-level entries are all `EQUAL` under the module-code call
witness; the 12 repaired `m04` entries are `DIFFERENT` only in R7 (the product
adds an extra nested `try`; `co_code` 300 vs 298, `co_exceptiontable` differs),
so they are excluded, not counted.  See `ASYNC_DRIVER.md` and
`MODULE_WITNESS.md`.

## Remaining gap

`covered_5tuple=1168/1556`; G1 still **FAIL/BLOCKED** because 388 entries are
`excluded`:

| Reason | Count | Detail |
|---|---:|---|
| `unsafe_host_module: real-package module` | 376 | Safety gate: pyc-only business-package modules may have process/network/trading side effects; dependency closure (`six`/`jsonpickle` etc.) is incomplete in the sandbox. |
| `r7_code_object_diff` | 12 | Repaired `m04_module_try.py` family: behavior R1-R6 matches, but the product adds an inner `try` around the `for`, so `co_code` 300 vs 298 and `co_exceptiontable` differ; R7 blocks by spec. New defect family B275. |

No claim of completeness is made.  The remaining tractable defect is the
`m04` extra-try R7 family (12 entries); the 376 real-package modules remain
behind the safety gate and require an audited sandbox/whitelist before they can
enter the G1 numerator.
