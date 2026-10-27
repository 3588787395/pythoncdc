# Async-only family: 62 entries closed with a real `asyncio.run` driver

## Why the preparer emitted no calls

`jspace_v3_prepare.py` derives calls from top-level `def`/`class` nodes.  Its
`function_calls()` deliberately returns `[]` for `AsyncFunctionDef` because a
bare `eval("fn(...)")` only creates a coroutine object; the coroutine body never
runs and the object cannot be compared semantically.  That left 62 entries with
`no_top_level_callable_with_constructible_arguments` across four sources:

| Source | Entries |
|---|---:|
| `test_repros/round6/r6_07_async_five.py` | 36 |
| `test_repros/round5/r5_10_comp_async.py` | 12 |
| `test_repros/round6/r6_08_async_cross.py` | 12 |
| `test_repros/round4/rec1_synth_b47_ternary.py` | 2 |

## Driver model

`close_async_family.py` adds one self-contained call expression per async
entrypoint.  The expression:

1. executes a fixed driver prelude in a private dict (`_d`), so the module under
   test is not polluted with helper globals;
2. calls the module-level async function through `globals()[name]`;
3. drives it with `_d['_asyncio'].run(...)`;
4. consumes async generators with `_d['_consume'](...)`.

The generated shape is:

```python
(lambda _d: (exec(<driver source>, _d),
             _d['_asyncio'].run(globals()['fn'](_d['_g'], ...)))[1])({})
```

The driver prelude (SHA256 `d58a006df621fc05631cbc175b1bee5c2b97e15a6bbff3eafab141cb494701b7`)
defines:

| Driver | Meaning |
|---|---|
| `_g(x)` | `async def`, returns `x + 1` |
| `_h(x)` | `async def`, returns `x * 2` |
| `_AI(xs)` | async iterable over `xs` (`__aiter__`/`__anext__`) |
| `_AMgr()` | async context manager returning `10` |
| `_CM()` | sync context manager returning `5` |
| `_IO()` | object with async `a()`/`b()` returning `1`/`2` |
| `_consume(agen)` | async generator consumer |

Arguments are structural, not arbitrary: `g`/`h` are async callables, `ait` is
an async iterable (pairs when the function unpacks `async for k, v in ait`),
`mgr` is async/sync according to the body, `io` exposes async methods, `flag`
is exercised in both truth values, and `xs`/`b` are small deterministic
iterables.

## Why this is not a fake green

- The coroutine body actually runs under `asyncio.run`; its return value,
  exceptions, stdout/stderr/events and post-call globals are compared.
- The original artifact remains the original `pyc`; no source/pyc is rewritten
  and no synthetic entrypoint is compiled.
- The driver lives in a private namespace, so `module_values` still observes
  only the module under test.
- All 62 entries are `EQUAL`; none needed an R7 tolerance.

## Result

| Reading | Before | After async family |
|---|---:|---:|
| covered_5tuple | 1086 | **1148** |
| excluded | 470 | **408** |
| uncovered | 470 | **408** |
| semantic_failures | 0 | 0 |
| coverage_pct | 69.79% | **73.78%** |

Evidence: `semantic_async.json` (62/62 `EQUAL`), `semantic_v3a_merged.json`,
`COVERAGE_V3A.md`, `coverage_v3a.json`.

## Reproduce

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

## Residual

The async family has no residual.  The remaining 408 entries at this stage were
376 real-package modules plus 32 module-level-only entries; the latter are
handled in `MODULE_WITNESS.md`.
