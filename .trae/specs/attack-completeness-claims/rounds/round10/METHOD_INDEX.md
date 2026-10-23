# Method and Evidence Index (v9 terminal)

## Method documents

| document | role |
|---|---|
| `rounds/round8/COMPLETENESS_METHOD.md` | four pillars: judgment space, semantic differential, proof obligations, continuous evidence; falsifiable gates |
| `rounds/round8/METHOD_REVIEW.md` | three review rounds; attack-style critique |
| `rounds/round8/roadmap.md` | implementation order, acceptance readings, rollback conditions |
| `rounds/round9/GATE_INTEGRATION.md` | how G1–G6 + dual readings + audit are integrated; sample boundary |
| `rounds/round10/VERIFICATION.md` | v9 terminal verification; actual vs. not run |
| `rounds/round10/FINAL_REPORT.md` | terminal verdict and blockers |
| `rounds/round9/SUMMARY.md` | Task 9 snapshot (tools, fuzz, canary, gate) |

## Tools

| tool | function | self-test / evidence |
|---|---|---|
| `tools/completeness/semantic_diff.py` | execute source vs. product; R1–R7; sandboxed, non-OS | 17/17, `round9/SEMANTIC_DIFF.md` |
| `tools/completeness/mutation_test.py` | independent AST mutations; baseline EQUAL precondition; miss/false-kill accounting | 9/9 + 1/1 smoke, `round9/MUTATION_TEST.md` |
| `tools/completeness/jspace_generator.py` | J v2 (1556): p_j / pyc / expected_label / input_model / excluded | `round9/JSPACE_C1C5.md` |
| `tools/completeness/coverage_checker.py` | C1–C5 five-tuple coverage | 13/13, `round9/coverage_c1c5.json` |
| `tools/completeness/semantic_runner.py` | J entry → product → semantic_diff → C1–C5 | `round9/semantic_j_sample.json` |
| `tools/completeness/rule_universe.py` | independent 339-rule enumeration | 12/12, `round9/RULE_MANIFEST.md` |
| `tools/completeness/rule_manifest.py` | manifest/anchor reconciliation + coverage lemma | `round9/rule_coverage.json` |
| `tools/completeness/fuzz_driver.py` | 24 templates; bounded or long-run generation | `round9/fuzz_report.jsonl` |
| `tools/completeness/minimize.py` | line-level ddmin preserving status + dimensions | `round9/minimized/` |
| `tools/completeness/canary_runner.py` | canary generation/run/leak scan | `round9/canary_report.json` |
| `tools/completeness/fuzz_selftest.py` | synthetic fuzz/minimize/canary checks | 11/11 |
| `tools/completeness/gate_report.py` | aggregate G1–G6 + dual readings + audit | `round9/GATE_REPORT.md` |
| `tools/completeness/gate_report_selftest.py` | gate aggregation checks | 12/12 |
| `tools/completeness/dual_readings.py` | Markdown dual-reading renderer | `round9/dual_readings.md` |

## Core evidence

| evidence | content |
|---|---|
| `round9/coverage_c1c5.json` | full J baseline: 0/1556 covered |
| `round9/coverage_c1c5_sample.json` | integrated sample: 51/1556, 6 semantic failures |
| `round9/semantic_j_sample.json` | 51 C1–C5 records with hashes and verdicts |
| `round9/semantic_products/` | 51 products used in the sample |
| `round9/rule_universe.json` | 339 rules, 5663 occurrences, 15 isinstance / 324 opcode |
| `round9/rule_coverage.json` | 0 proved / 339 open; no traces |
| `round9/fuzz_summary.json` | 24 cases: 20/4 |
| `round9/minimized/` | four minimized repros |
| `round9/canary_manifest.json` | 24 IDs + hashes only (no plaintext) |
| `round9/canary_report.json` | 20/24, leaks 0, G6 FAIL |
| `round9/gate_report.json` | overall BLOCKED |
| `round9/dual_readings.md` | shape vs. judgment-space readings |
| `round10/VERIFICATION.md` | terminal gate accounting |
| `round10/BREACH_TRIAGE.md` | B163–B219 + fuzz maps |
| `round10/ATTACK_CONCLUSIONS.md` | L0–L6 conclusions |
| `round10/FINAL_REPORT.md` | terminal verdict |

## Historical inputs

| document | use |
|---|---|
| `rounds/round2/ATTACK_L0_THEORY.md` | L0 theory/mechanism evidence |
| `rounds/round3/ATTACK_L1_MEASURE.md` | L1 denominator/variant evidence |
| `rounds/round3/BREACH_REGISTRY.md` | authoritative B-number registry |
| `rounds/round4/ATTACK_L2_JUDGE.md` | judge blind spots / mutation |
| `rounds/round5/ATTACK_L3_MECHANISM.md` | mechanism sampling / B142 elevation |
| `rounds/round6/ATTACK_L4_RUNTIME.md` | off-corpus / runtime diff |
| `rounds/round7/ATTACK_L5_EVIDENCE.md` | corpus/evidence audit |
| `rounds/round8/REVIEW.md` + `REVIEW2.md` | v8 historical shape baseline |
| `.trae/specs/attain-true-completeness/rounds/round8/final_verify_summary.json` | G5 historical baseline |
