# Repair of the 36 `c4_error` entries

The fresh baseline has 36 `inconclusive` entries.  All 36 come from three
historical probes whose **original artifact** fails at module load, before any
decompiled product is executed.  They are corpus defects, not decompiler
defects.  The historical files under `test_repros/` are left untouched; this
directory carries minimal executable copies and a manifest overlay.

| Historical probe | Entries | Original failure | Minimal fix |
|---|---:|---|---|
| `test_repros/round4/c4_15_star_import.py` | 12 (`JS-IMPORT-002..019`) | `NameError: name 'path' is not defined` | Add `from os import path` before the star import; the star import and all `path` uses are preserved. |
| `test_repros/round2/c05_class_with.py` | 12 (`JS-WITH-003..030`) | `NameError: name '_CM' is not defined` | Add a minimal `_CM` context manager before `CWith`; class-level `with` forms and nesting are unchanged. |
| `test_repros/round2/c01_class_assign.py` | 12 (`JS-ANNASSIGN-001..013`) | `NameError: name 'B' is not defined` | Bind the class-body value as a default: `(lambda v, B=B: v * B)(2)`; the assignment form is unchanged. |

Why each failure happens:

- `from os.path import *` imports `join`, `exists`, ... but not the module name
  `path`; the probe body and `e01_use()` read `path`.
- A class-body `with _CM()` executes while the class is being created; the
  probe never defines `_CM`.
- A lambda inside a class body does not close over class-body names; `B` is
  unbound when the lambda is called.

## Reproduction

```powershell
python -X utf8 .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/repair_invalid_probes.py
python -X utf8 tools/completeness/semantic_runner.py `
  --space .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/repair_manifest.json `
  --out .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/semantic_repair.json `
  --report .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/semantic_repair_report.json `
  --product-dir .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/semantic_products/repair
```

Result: `records=36`, `EQUAL=36`, `covered_5tuple=36`.  The repaired overlay
therefore raises the full reading from `1050/1556` to `1086/1556`, with
`inconclusive=0` and `semantic_failures=0`.

## Scope discipline

- Only the three affected `p_j`/`pyc` pairs are rewritten in
  `judgment_space_v3r.json`; every other entry is byte-identical to
  `judgment_space_v3.json`.
- Each rewritten entry carries
  `pyc_provenance="repaired_invalid_probe"` and a `repair_note`.
- `REPAIR_REPORT.json` records the original/repaired source and pyc SHA256 for
  each file, plus the observed failure and fix.
- No file under `tests/`, `scripts/pyc_verify.py`, or the external
  `pylingual/equivalence_check.py` is modified.
