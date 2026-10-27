# Module-level-only family: 32 entries and the module-code call witness

## Why this family is special

The spec says every J entry must have a callable entrypoint and that a bare
module import is not semantic coverage.  Thirty-two entries point at sources
whose only top-level statements are module-level `for`/`while`/`try`/`assert`
forms:

| Source | Entries | Top-level statements |
|---|---:|---|
| `test_repros/round2/m06_module_loops.py` | 14 | `Assign`, `For`, `While` |
| `test_repros/round2/m04_module_try.py` | 12 | `Import`, `Try` (nested) |
| `test_repros/round2/m08_module_stmts.py` | 6 | `Import`, `AnnAssign`, `AugAssign`, `Assign`, `Delete`, `Assert`, `If`, `Expr` |

There is no probe-defined function or class to call.  A `globals().get(...)`
read would be a bare state inspection, and a synthetic wrapper source would
change the J record's `p_j`/`pyc` and the host label.  Both are rejected.

## Callable entrypoint

`close_module_family.py` uses the original module code object itself:

```python
(lambda _c: __import__('types').FunctionType(_c, globals())())(
    __loader__.get_code(__name__))
```

- `__loader__.get_code(__name__)` returns the code object of the artifact under
  test (the original `pyc` on the original side, the compiled product source on
  the product side).
- `types.FunctionType(code, globals())()` **calls** that code object; the
  module body is re-executed in the module namespace.
- The judge compares the call's return/exception, stdout/stderr/events/files,
  and the post-call module globals.  It is therefore a post-import state
  witness, not an import-only pass.

No source or pyc is synthesised for the 20 `m06`/`m08` entries.  The C1/C2
hashes remain the original probe hashes.

## Discrimination check

The witness must catch a wrong product.  `module_witness_mutation.py` compares
the real `JS-WHILE-024` product and a copy with `TOTAL += i` changed to
`TOTAL -= i`:

```text
[witness] product: EQUAL
[witness] mutated: DIFFERENT
[witness] mutated diffs: [
  {"path": "$.metadata.code.co_code.sha256", ..., "dimension": "R7"},
  {"path": "$.module_values.TOTAL.v", "original": "103", "product": "97", "dimension": "R5"}
]
[witness] PASS: mutation detected in module_values.TOTAL
```

Run it with:

```powershell
python -X utf8 .../fresh/module_witness_mutation.py
```

## `m04_module_try.py` repair

The historical probe load-fails before any decompiler code runs:

```python
with (CFG if 0 else json) as j:
```

`json` is a module, not a context manager, so the original artifact raises
`TypeError: 'module' object does not support the context manager protocol`.
A minimal executable copy is written to
`repaired_sources/m04_module_try.py` and `repaired_pyc/m04_module_try.pyc`:

```python
class _CM:
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False

with (CFG if 0 else _CM()) as j:
```

The ternary/with/try nesting is preserved; the historical `test_repros/` file
is untouched.  The 12 affected entries point at the repaired copy and carry a
`repair_note`.

## Result

`semantic_runner` on the 32-entry `module_manifest.json`:

| Verdict | Count | Detail |
|---|---:|---|
| `EQUAL` | 20 | `m06`/`m08`; covered |
| `DIFFERENT` | 12 | repaired `m04`; R7 only |

The 12 `m04` products are behaviorally equal (R1-R6) but the decompiled source
adds an inner `try` around the `for`:

```python
try:
    try:
        try:                 # extra, not in the original
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

`co_code` is 300 bytes vs 298 and `co_exceptiontable` differs.  R7 is blocking
by spec, so these 12 are **excluded** with reason `r7_code_object_diff`; they
are not counted as covered.  This is a new decompiler defect family (B275), not
a corpus defect.  The full `semantic_module.json` retains the DIFFERENT records;
`apply_module_results.py` filters them out of the merge and writes the explicit
exclusion reason.

## Readings

| Reading | Before module family | After 20 EQUAL witnesses |
|---|---:|---:|
| covered_5tuple | 1148 | **1168** |
| excluded | 408 | **388** |
| uncovered | 408 | **388** |
| semantic_failures | 0 | 0 |
| coverage_pct | 73.78% | **75.06%** |

Evidence: `semantic_module.json` (20 EQUAL / 12 DIFFERENT), `semantic_module_equal.json`,
`semantic_v3m_merged.json`, `COVERAGE_V3M.md`, `coverage_v3m.json`.

## Reproduce

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

## Residual

- 12 `m04` entries: R7 extra-try defect (B275), excluded.
- 376 real-package modules: safety gate, unchanged.

G1 remains **FAIL/BLOCKED**.
