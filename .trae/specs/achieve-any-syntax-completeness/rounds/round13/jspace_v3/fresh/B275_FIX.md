# B275: nested `try/except/finally` inside an outer `try` gained an extra `try`

## Symptom

The 12 `m04_module_try.py` entries were behaviourally equal (R1-R6) but blocked
by R7: the decompiled product added one inner `try` around the `for`:

```python
# product before B275
try:
    try:
        try:                 # extra, not in the artifact
            for i in range(2):
                with _CM() as j:
                    ...
        except ValueError:
            CFG = 1
    finally:
        DONE = 1
except NameError:
    DONE = 2
```

`co_code` was 300 bytes vs 298 and `co_exceptiontable` differed (the extra
`try` adds one protected range).  R7 is blocking by spec, so the 12 entries were
excluded with `r7_code_object_diff`.

## Root cause

`core/cfg/region_ast_generator.py::_region_has_outer_handler_over_finally_copy`
answers "is this finally region nested inside an outer `try`?" by looking for an
outer `PUSH_EXC_INFO` handler that protects the *normal-path copies* of the
finally body (`region.finally_copy_blocks`).

For this shape the inner finally's normal-path copy exit is itself inside the
**outer** handler's protected range.  `_collect_finally_body_blocks` therefore
does not register that copy as a "finally body block" (its own protected-range
test fails), so `finally_copy_blocks` is empty.  The function returned `False`,
the W13 marker-NOP counter believed the region was not nested, and it wrapped
the `for` in an extra `try`.

The exception-path copies in `region.finally_blocks` are still protected by the
same outer handler, so they carry the same structural evidence.

## Fix

In `_region_has_outer_handler_over_finally_copy`:

- When `finally_copy_blocks` is empty, fall back to `finally_blocks` as the
  ledger (`{block.start_offset: 0}`).
- When the fallback is active, only accept a handler target block that is
  **outside** `region.blocks`.  A `try` nested in the finally body has its own
  handler inside the region; that is not an outer wrapper.
- When `finally_copy_blocks` is non-empty, the ledger and every existing test are
  bit-for-bit unchanged (C3).

The docstring records the B275 rule next to the existing ①②③④ mapping rules.

## Evidence

`b275_regression.py` decompiles the repaired `m04` pyc and two controls, then
recompiles the product and compares `co_code`, `co_exceptiontable`, `co_names`,
`co_varnames`, `co_flags` and `co_consts` recursively:

```text
[B275] m04_module_try     EQUAL
[B275] c04_CTryNest       EQUAL
[B275] control_flat       EQUAL
[B275] PASS
```

Direct measurement on the repaired `m04` pyc:

| Quantity | Before | After |
|---|---:|---:|
| `co_code` (bytes) | 300 | **298** |
| `co_code` == artifact | no | **yes (298 == 298)** |
| `co_exceptiontable` | differs | **equal (129 == 129 bytes)** |
| extra inner `try` | yes | **no** |

The original `test_repros/round2/m04_module_try.pyc` is a different artifact: it
loads, but raises `TypeError: 'module' object does not support the context
manager protocol` at the `with` (256-byte `co_code`).  The repaired probe
replaces `json` with a real `_CM` context manager and keeps the
ternary/with/try/finally nesting; see `MODULE_WITNESS.md`.  B275 is a
decompiler fix, not a corpus change.

## Regression

Full 1556-entry base rerun (`judgment_space_v3.json`, 3 shards) compared with the
archived `semantic_v3_merged.json`:

| Check | Result |
|---|---|
| verdict changes | **0** |
| status changes | **0** |
| product SHA changes | **12**, all `m04`/`JS-TRY-*` (expected B275 effect) |
| shard totals | `covered_5tuple=1050`, `EQUAL=1132`, `ERROR=424` — identical to archive |

The 36 repaired-probe rerun is 36/36 `EQUAL`; the 62 async rerun is 62/62
`EQUAL`; the module manifest rerun is **32/32 `EQUAL`**.  All 1556 C5 records
still carry judge SHA256 `dbcb1e246dd549f2c66a1d779f31eba0506f9c99364db02a679523dde84d8174`.

The base rerun decompiled all 1556 pycs, including the 376 real-package
modules.  Since only the 12 `m04` products changed, B275 does not alter any
`site-packages/**OK.py` product.  `tests/test_product_freshness.py` already
fails at `HEAD` (the committed `matcherOK.py` / `trade_info_utilsOK.py` are
stale from an earlier code state); the same two outputs are byte-identical with
and without B275, so this is pre-existing regen debt, not a B275 regression.

The raw post-B275 reruns are archived under `b275_regression/`
(`regress_shard0..2.json`, `regress_repair.json`, `regress_async.json`), so the
comparison can be recomputed without a temporary directory.  The
machine-readable comparison (shard summaries, changed IDs, per-family checks)
is `B275_REGRESSION.json`: `verdict_changes=[]`, `status_changes=[]`,
`product_sha_changes=12` (all `JS-TRY-*`).  The repair/async reruns show 0
verdict and 0 product-SHA changes against the archived evidence.  The
module-family check compares the archived
`semantic_module.json` (20 `EQUAL` + 12 `DIFFERENT`) with the post-B275
`semantic_module_b275.json` (32 `EQUAL`): the 12 verdict and 12 product-SHA
changes are exactly the intended `DIFFERENT -> EQUAL` improvements on the
`JS-TRY-*` entries, not regressions.

## Reading

| Reading | Before B275 | After B275 |
|---|---:|---:|
| covered_5tuple | 1168 | **1180** |
| excluded | 388 | **376** |
| uncovered | 388 | **376** |
| semantic_failures | 0 | **0** |
| green | 1168 | **1180** |
| coverage_pct | 75.06% | **75.84%** |

The 12 `m04` entries leave the R7 exclusion list; the 376 real-package modules
remain behind the safety gate.  G1 is still **FAIL/BLOCKED**:

```text
[coverage] J_total=1556 covered_5tuple=1180 probe_only=0 unexecuted=0 n/a=0 inconclusive=0 excluded=376 uncovered=376 coverage=75.84%
[coverage] GATE FAIL: uncovered=376 (covered_5tuple is the only numerator)
```

## Reproduce

```powershell
python -X utf8 .../fresh/close_module_family.py `
  --space .../fresh/judgment_space_v3a.json `
  --out-space .../fresh/judgment_space_v3m.json `
  --out-manifest .../fresh/module_manifest.json `
  --report .../fresh/module_family_report.json
python -X utf8 .../fresh/b275_regression.py
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/judgment_space_v3.json `
  --out .../fresh/b275_regression/regress_shard0.json --offset 0 --limit 519
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/judgment_space_v3.json `
  --out .../fresh/b275_regression/regress_shard1.json --offset 519 --limit 519
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/judgment_space_v3.json `
  --out .../fresh/b275_regression/regress_shard2.json --offset 1038 --limit 519
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/repair_manifest.json `
  --out .../fresh/b275_regression/regress_repair.json `
  --product-dir .../fresh/semantic_products/repair
python -X utf8 tools/completeness/semantic_runner.py `
  --space .../fresh/async_manifest.json `
  --out .../fresh/b275_regression/regress_async.json `
  --product-dir .../fresh/semantic_products/async
python -X utf8 .../fresh/b275_regression_report.py
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

## Limits

- The original `m04` artifact is not executable; the 12 entries are covered by
  the shape-preserving repaired probe whose pyc SHA256 is bound in
  `judgment_space_v3m_b275.json`.  This is not a claim that the original pyc
  executes.  The rr-v5r74 `repair_note` said the probe "load-fails"; it loads
  and raises `TypeError` at the `with`.  This round corrects that note in
  `judgment_space_v3m.json` / `judgment_space_v3m_b275.json`; the pyc binding,
  verdicts and readings are unchanged.
- The 376 real-package modules are untouched: they still need an audited
  sandbox side-effect whitelist and dependency closure (`six`, `jsonpickle`,
  `IQEngine`, ...).
- G1, G3, G4 and G6 remain as recorded in `checklist.md`; no completeness claim
  is made.
