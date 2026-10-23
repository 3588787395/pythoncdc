# Task 10 Verification — v9 Terminal Audit

## Scope and status

This is the Task 10 verification record. It is **not** a completeness pass. It records the current v9 readings, the blockers, and what was actually run.

- Code under `core/cfg/**`, `scripts/pyc_verify.py`, and `tests/**`: **unchanged in Task 10**.
- Product fixes for the four fuzz findings: **not made**.
- Full J semantic run: **not run**.
- Full 402 / small34 / quotation / pytest / IV.2 rerun: **not run**; G5 is therefore `baseline_only`.
- Root docs updated: `rules.md`, `wiki/concepts/decompile-invariant-completeness.md`, `wiki/concepts/syntax-audit-ledger.md`, `wiki/concepts/branch-coverage.md`, `wiki/overview.md`, `wiki/index.md`, `wiki/log.md`.

## Baseline commits

| commit | content |
|---|---|
| `8e7da421` | Task 9.1 semantic diff |
| `55ef429e` | Task 9.2 mutation |
| `93833cd9` | Task 9.3 J v2 + C1–C5 |
| `da3486e8` | Task 9.4 rule universe |
| `d8e8774e` | Task 9.5 fuzz + bootstrap canary |
| `97a07eb7` | Task 9.6 semantic runner + gate report |
| `2cd05c5b` | Task 9.7 snapshot |

## Gate results

| gate | status | actual reading | source |
|---|---|---|---|
| G1 judgment space | **FAIL** | full **0/1556 covered**; integrated sample **51/1556 (3.28%)**; sample statuses **51 covered / 1117 probe_only / 388 `c1_source_missing`**; top-level `uncovered=1505` = not-covered total, not the status count | `round9/coverage_c1c5.json`, `round9/coverage_c1c5_sample.json` |
| G2a J semantic diff | **FAIL** | sample 51: **45 EQUAL / 6 DIFFERENT / 0 ERROR**; full J not run | `round9/semantic_j_sample.json` |
| G2b 402 semantic diff | **UNESTABLISHED** | no run | — |
| G2c 46 real pyc | **UNESTABLISHED** | no run | — |
| G3 mutation | **UNESTABLISHED** | only 1/1 smoke; no full mutation report | `round9/mutation_smoke_server_version.json` |
| G4 rule coverage | **INCONCLUSIVE** | **339 rules; 339/339 manifest; 0 proved / 339 open; no traces** | `round9/rule_universe.json`, `round9/rule_coverage.json` |
| G5 corpus regression | **PASS (baseline_only)** | 6617/6617, 1568/1568, 153/153; pytest baseline; IV.2 historical | `round9/gate_report.json` |
| G6 canary | **FAIL** | 24 local-bootstrap: **20 EQUAL / 4 DIFFERENT**; leak hits **0**; `custody=local-bootstrap`; `rotation_ok=false` | `round9/canary_report.json`, `round9/canary_leak_scan.md` |

`gate_report.py` overall: **BLOCKED**. Blockers: **G1, G2a, G2b, G2c, G3, G4, G6**.

## Semantic sample detail

- Input: first 100 J entries; 51 had C1/C2 and a product.
- 49 entries skipped with `c1_source_missing`.
- 6 DIFFERENT, all R7 only: `JS-IF-017`, `JS-IF-021`, `JS-IF-076`, `JS-IF-088`, `JS-IF-090`, `JS-IF-097`.
- `JS-IF-017` visibly rewrites the module docstring as `__doc__ = ...`.
- This is a sample, not the 1556 full set. It must not be reported as J completion.

## Fuzz and canary

- Bounded fuzz: 24 cases, **20 EQUAL / 4 DIFFERENT**; stopped by `case_limit` at 240 s.
- Four minimized repros:
  - `FZ-raresyntax-015-11d70844` starred-unpack (6→3; R6/R7; product `NameError`)
  - `FZ-semantictrap-020-1d4bb36d` generator-send (15→14; R1/R7)
  - `FZ-raresyntax-021-5433fdc8` annotations-posonly (2→2; R7)
  - `FZ-semantictrap-023-cb72b56d` finally-return (14→10; R1/R5/R7)
- Bootstrap canary: 24 (8×3), **20 EQUAL / 4 DIFFERENT**, 0 leak hits, G6 FAIL.
- Automated weekly 4-CPU-hour fuzz and continuous 4-hour no-new-DIFF: **not established**.

## Commands actually run in this round

```text
python -m py_compile tools/completeness/semantic_runner.py \
  tools/completeness/gate_report.py tools/completeness/gate_report_selftest.py \
  tools/completeness/dual_readings.py tools/completeness/fuzz_driver.py \
  tools/completeness/minimize.py tools/completeness/canary_runner.py \
  tools/completeness/fuzz_selftest.py
python -X utf8 tools/completeness/gate_report_selftest.py   # 12/12
python -X utf8 tools/completeness/fuzz_selftest.py          # 11/11
```

The full J semantic run and the full 402 regression were not executed. No statement here should be read as a current full regression result.

## Binding conclusion

`v8 128/128` is a historical shape baseline only. The current v9 state is **BLOCKED**. The only allowed reading is:

> 形态基线达成（v8 口径）；判定空间/语义差分/变异/规则覆盖/独立 canary 未达标，完备未成立。

Forbidden readings: 「完备」「100%」「J 已覆盖」「规则完备」「语义完备」「独立 canary 通过」「G5 本轮全绿」。
