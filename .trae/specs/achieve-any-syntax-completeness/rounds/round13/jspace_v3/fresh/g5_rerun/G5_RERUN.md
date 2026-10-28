# G5 current-tree rerun (rr-v5r77)

## Why this rerun exists

The archived `rounds/round9/g5_regression_current.json` (rr-v5r06) recorded
`2 failed, 277 passed, 2 xpassed` and called it "suite composition drift".
That note was wrong in two ways:

1. The test suite changed after the archive. `5c9833e2` added
   `tests/test_repo_tool_hygiene.py`, and `348a9af0` added
   `TestSignatureValidatorHasTeeth`; the same six legacy files plus the
   hygiene file now collect **286** tests and report
   **`2 failed, 282 passed, 2 xpassed`**, exactly the string
   `gate_report.gate_g5` already expected.
2. The frozen 402/small34 indexes store an absolute `path` from another
   checkout (`D:/admin/.qoder/...`). `pyc_verify.py batch` uses `path`, not
   `rel`, so the first rerun aborted on every shard with
   `[fatal] pyc 不存在`. The corpus itself is present and byte-identical:
   all **436** entries (402 + 34) exist under this checkout and their sizes
   match the frozen `size` fields.

This rerun changes no product code and no threshold. It remaps only the
stale absolute `path` field to this checkout, keeps `rel`/`size`/
`function_count` frozen, and reruns the exact rr-v5r06 G5 battery on the
post-B275 tree.

## Commands

```text
python -X utf8 fresh/g5_rerun/remap_baseline_indexes.py
python -X utf8 fresh/g5_rerun/run_g5_current.py
```

The remap wrote `fresh/g5_rerun/shards/shard{0..7}.json`,
`fresh/g5_rerun/shards/small34.json`, and
`fresh/g5_rerun/shards/remap_report.json` (`missing_total=0`,
`size_mismatch_total=0`, 436 entries).

The runner executed, and archived in `fresh/g5_rerun/out/run_log.txt`:

```text
python -X utf8 scripts/pyc_verify.py batch --index .../shardN.json --json .../shardN_report.json   (x8)
python -X utf8 scripts/pyc_verify.py batch --index .../small34.json --json .../small34_report.json
python -X utf8 scripts/pyc_verify.py single site-packages/fly/data/quotation.pyc
python -X utf8 -m pytest tests/test_algorithm_correctness.py tests/test_deep_nesting_pressure.py \
    tests/test_control_flow_completeness_matrix.py tests/test_complete_syntax_coverage.py \
    tests/test_boundary_cases.py tests/test_core_functional.py tests/test_repo_tool_hygiene.py \
    -p no:cacheprovider --tb=no -q
python -X utf8 -c "import core.pyc_loader_v2, core.control_flow, core.cfg, ...; print('IMPORT_OK')"
```

## Readings

| Input | Reading | Verdict |
|---|---|---|
| 402 eight shards | **6617/6617** units, 402/402 files success, 0 failure/compile_error/error | green |
| small34 | **1568/1568** units, 34/34 files success | green |
| quotation single | `status=success units=153/153 success_rate=100.00%`, rc 0 | green |
| 7-suite pytest | `2 failed, 282 passed, 2 xpassed in 11.30s`; failures are the frozen pair `B01_simple_if_then_else_merge` and `BOUNDARY_02_large_function` | matches gate expectation |
| IV.2 | `IMPORT_OK=true`, `COMPILE_OK=true`, `G3_forbidden_prefix_new_defs=0`, both BOM states `one` | green |
| `core/cfg` clean | `git status --porcelain -- core/cfg` empty | green |

Per-shard units: 786, 469, 538, 887, 855, 999, 801, 1282 (sum 6617).

`gate_report.gate_g5()` on the new evidence returns:

```json
{"status":"PASS","core_cfg_clean":true,"units":"6617/6617",
 "small34":"1568/1568","quotation":0,
 "tests":"2 failed, 282 passed, 2 xpassed in 11.30s",
 "iv2":{"import":true,"compile":true,"g3":0}}
```

## Honest boundaries

- **G5 only.** This does not change G1/G2/G3/G4/G6. G1 remains
  `1180/1556` covered with 376 excluded; G4 is being re-measured on the
  current sources separately.
- The batch compares the in-place `*OK.py` products, exactly as the
  rr-v5r06 run did; it does not regenerate them. This is the established G5
  methodology, not a fresh decompilation proof.
- The 2 pytest failures are the pre-existing frozen pair; the gate accepts
  the summary string and does not turn them green.
- The comparator is still the frozen external
  `pylingual/equivalence_check.py` (sha256 prefix `9c7567bd6776b36b`);
  `scripts/pyc_verify.py` and `tests/` were not modified.
- `gate_report.gate_g5()` hardcodes `current_run=false` and
  `baseline_only=true` for every input; the `PASS` above is computed from this
  run's `total`/`small34`/`quotation`/`pytest`/`iv2` fields, not from the
  stale round9 file.  The hardcoded labels are a tool limitation, not a claim
  that the evidence is historical.

## Evidence hashes

| File | SHA256 |
|---|---|
| `out/g5_regression_current.json` | `36BC9C36B1970649BD9466056CA3B9BF91B75F7BABCE07C72F41672DCFE30941` |
| `shards/remap_report.json` | `DF779756CF0046474AEB6BE84C6874F4478F1AB00FA318EA99CD6E4C09E8322F` |

Pre-rerun scratch (277-pass archive) is preserved under
`pre_b275/` and is **not** used as current evidence.
