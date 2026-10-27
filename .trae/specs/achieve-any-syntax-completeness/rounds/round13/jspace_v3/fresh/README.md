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
`m04_module_try.py`, whose `with (CFG if 0 else json)` raises `TypeError` at
runtime; a minimal `_CM()` copy is written under `repaired_sources/` /
`repaired_pyc/`.  The historical run left those 12 `DIFFERENT` only in R7 (an
extra inner `try`); B275 fixed the decompiler and the rerun is 32/32 `EQUAL`
(see `B275_FIX.md`).

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

### 7. B275 fix and the 32/32 module rerun

`core/cfg/region_ast_generator.py::_region_has_outer_handler_over_finally_copy`
now falls back to `finally_blocks` when `finally_copy_blocks` is empty, so the
inner finally is recognised as nested in the outer `try`.  The historical 20/12
evidence is kept; the new chain is:

```powershell
python -X utf8 .../fresh/b275_regression.py
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/module_manifest.json --out .../fresh/semantic_module_b275.json `
  --report .../fresh/semantic_module_b275_report.json `
  --product-dir .../fresh/semantic_products/module_b275
python -X utf8 .../fresh/apply_module_results.py `
  --space .../fresh/judgment_space_v3m.json `
  --evidence .../fresh/semantic_module_b275.json `
  --out-space .../fresh/judgment_space_v3m_b275.json `
  --out-evidence .../fresh/semantic_module_equal_b275.json `
  --report .../fresh/module_results_b275_report.json
python -X utf8 .../fresh/merge_evidence.py `
  --out .../fresh/semantic_v3m_b275_merged.json `
  --space .../fresh/judgment_space_v3m_b275.json `
  --shard .../fresh/semantic_v3a_merged.json --repair .../fresh/semantic_module_equal_b275.json
python -X utf8 tools/completeness/coverage_checker.py `
  --space .../fresh/judgment_space_v3m_b275.json `
  --evidence .../fresh/semantic_v3m_b275_merged.json `
  --judge tools/completeness/semantic_diff.py `
  --out .../fresh/COVERAGE_V3M_B275.md --json .../fresh/coverage_v3m_b275.json
```

The post-B275 base rerun (`judgment_space_v3.json`, offsets 0/519/1038) and the
repair/async family reruns are archived under `b275_regression/`;
`b275_regression_report.py` recomputes `B275_REGRESSION.json` from them (0
verdict / 0 status changes, 12 m04 product-SHA changes).  See `B275_FIX.md`.

## Readings

| Reading | Fresh baseline | +36 repair | +62 async | +20 module witness | +12 m04 (B275) |
|---|---:|---:|---:|---:|---:|
| J_total | 1556 | 1556 | 1556 | 1556 | 1556 |
| covered_5tuple | 1050 | 1086 | 1148 | 1168 | **1180** |
| probe_only | 0 | 0 | 0 | 0 | 0 |
| unexecuted | 0 | 0 | 0 | 0 | 0 |
| n/a | 0 | 0 | 0 | 0 | 0 |
| inconclusive | 36 | 0 | 0 | 0 | 0 |
| excluded | 470 | 470 | 408 | 388 | **376** |
| uncovered | 506 | 470 | 408 | 388 | **376** |
| semantic_failures | 0 | 0 | 0 | 0 | 0 |
| green | 1050 | 1086 | 1148 | 1168 | **1180** |
| coverage_pct | 67.48% | 69.79% | 73.78% | 75.06% | **75.84%** |

The fresh baseline reproduces the historical `covered_5tuple=1050` exactly.
The two historical `DIFFERENT` entries (`JS-IF-017`, `JS-IF-021`, both the
B142 nested-finally/continue family) are now `EQUAL`; `semantic_failures` is 0.
The 36 `inconclusive` entries were all caused by three load-invalid probes, not
by decompiler output; see `REPAIR.md`.

The 62 async entries are all `EQUAL` under the `asyncio.run` driver.  All 32
module-level entries are `EQUAL` after B275: the 20 `m06`/`m08` entries use the
module-code call witness, and the 12 repaired `m04` entries now decompile to
`co_code` 298 == 298 with an equal `co_exceptiontable`.  The pre-B275 run
(20 `EQUAL` / 12 R7 `DIFFERENT`) is retained in `semantic_module.json` and
`COVERAGE_V3M.md`.  See `ASYNC_DRIVER.md`, `MODULE_WITNESS.md` and
`B275_FIX.md`.

## Remaining gap

`covered_5tuple=1180/1556`; G1 still **FAIL/BLOCKED** because 376 entries are
`excluded`:

| Reason | Count | Detail |
|---|---:|---|
| `unsafe_host_module: real-package module` | 376 | Safety gate: pyc-only business-package modules may have process/network/trading side effects; dependency closure (`six`/`jsonpickle` etc.) is incomplete in the sandbox. |

No claim of completeness is made.  The 376 real-package modules remain behind
the safety gate and require an audited sandbox/whitelist before they can enter
the G1 numerator.
