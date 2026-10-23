# Task 9 Snapshot — Tools, Fuzz, Canary and Gate

## Status

- Task 9.1–9.4: complete.
- Task 9.5: tools and local-bootstrap evidence complete; **independent C custody/rotation not met**.
- Task 9.6: gate integration and dual readings complete; **G1–G6 are not all green**, overall `BLOCKED`.
- Task 9.7: this snapshot is the final Task 9 commit (`rr-v4r09:`).
- No completeness claim is made. The only allowed reading is the v8 shape baseline as a regression-only result.

## Commit chain

| task | commit | content |
|---|---|---|
| 9.1 | `8e7da421` | `semantic_diff.py` + self-test 17/17 |
| 9.2 | `55ef429e` | `mutation_test.py` + self-test 9/9 + 1/1 smoke |
| 9.3 | `93833cd9` | J v2 1556 + C1–C5 checker; 0/1556 |
| 9.4 | `da3486e8` | rule universe 339 + manifest; G4 INCONCLUSIVE |
| 9.5 | `d8e8774e` | fuzz 24 (20/4) + 4 minimized + bootstrap canary (20/24) |
| 9.6 | `97a07eb7` | semantic runner + gate report; overall BLOCKED |

## Gate snapshot

| gate | status | reading |
|---|---|---|
| G1 | FAIL | 51/1556 C1–C5 covered in the integrated sample (3.28%) |
| G2a | FAIL | 51 J sample: 45 EQUAL / 6 DIFFERENT; no 100-case clean run |
| G2b | UNESTABLISHED | no 402-artifact semantic_diff run |
| G2c | UNESTABLISHED | no 46-real-pyc semantic_diff run |
| G3 | UNESTABLISHED | no full mutation report |
| G4 | INCONCLUSIVE | 339 rules, 0 proved, no rule traces |
| G5 | PASS | historical baseline 6617/6617, 1568/1568, 153/153; not rerun this round |
| G6 | FAIL | 20/24 canary EQUAL; 0 leak hits; local-bootstrap only |

Overall: **BLOCKED**. Blockers: G1, G2a, G2b, G2c, G3, G4, G6.

## J sample

- `J_total=1556`; 100 sampled; 51 had usable C1/C2.
- `45 EQUAL / 6 DIFFERENT`; all six are R7-only in the current sample.
- `covered_5tuple=51`; `probe_only=1117`; `uncovered=1505`; `semantic_failures=6`.
- The 49 skipped sample entries are C1 source-missing; the full J has 388 such entries.
- C3 products are in `semantic_products/`; C1/C2/C3 hashes are bound in `semantic_j_sample.json`.
- The sample is not a substitute for a full 1556 run.

## Fuzz and canary

- Bounded fuzz: 24 cases, 20 EQUAL / 4 DIFFERENT; all 4 minimized.
- Fuzz findings: starred unpack (R6/R7), generator send (R1/R7), positional-only signature (R7), finally return (R1/R5/R7).
- No new B number has been assigned; dedup/registration is Task 10.
- Bootstrap canary: 24 (8/8/8), 20 EQUAL / 4 DIFFERENT, 0 leak hits, G6 FAIL.
- Canary private plaintext is git-ignored in `.canary-private/`; only the manifest of hashes is committed.
- Weekly 4 CPU-hour fuzzing and continuous 4-hour no-new-DIFF are **not** established.

## Rules

- Independent universe: 339 `(kind,symbol)` rules, 5663 occurrences.
- Manifest: 339/339 mapped, 0 unmapped, 0 orphan, 0 proved, 339 open.
- No rule traces, so G4 remains `INCONCLUSIVE`, not PASS.
- The 339 count is not reconciled to the historical 191/174/123 marker counts; Task 10 must keep the provenance of each number explicit.

## Not done

- 9.5c independent C-role custody and quarterly rotation.
- 9.6b independent third-party audit; the gate audit is a deterministic 6/51 in-process sample.
- Full J C1–C5 production, G2b/G2c, full G3 mutation, G4 witnesses, G6 24/24.
- No product fixes for the four fuzz findings in this task.

## Evidence index

- `SEMANTIC_DIFF.md`, `semantic_diff_selftest.json`
- `MUTATION_TEST.md`, `mutation_selftest.json`, `mutation_smoke_server_version.json`
- `JSPACE_C1C5.md`, `JUDGMENT_SPACE.md`, `judgment_space.json`, `COVERAGE_C1C5.md`, `coverage_c1c5.json`
- `RULE_MANIFEST.md`, `rule_universe.json`, `rule_coverage.json`, `rule_manifest_selftest.json`
- `FUZZ_CANARY.md`, `fuzz_report.jsonl`, `fuzz_summary.json`, `minimized/`, `canary_report.json`, `canary_leak_scan.md`, `canary_manifest.json`
- `GATE_INTEGRATION.md`, `GATE_REPORT.md`, `gate_report.json`, `dual_readings.md`, `coverage_c1c5_sample.json`, `semantic_j_sample.json`
