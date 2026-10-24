# Gate Report

- overall: **BLOCKED**
- blockers: G1, G2a, G2b, G2c, G3, G4, G5, G6

| gate | status | key reading |
|---|---|---|
| G1 | **FAIL** | 395/1556 covered, 189 diffs |
| G2a | **FAIL** | 1556/100, diff=189 |
| G2b | **FAIL** | 402/402, diff=3 |
| G2c | **FAIL** | 46/46, diff=24 |
| G3 | **FAIL** | killed=32 survived=602 |
| G4 | **FAIL** | proved=0/339, reason=mapping_or_proof_gap |
| G5 | **FAIL** | 6617/6617, baseline-only |
| G6 | **FAIL** | 20/24, leaks=0 |

## Dual readings

- shape: 6617/6617; 1568/1568; 153/153; v8 128/0/0 (100%)
- judgment: 395/1556 covered; 189 semantic failures; 1161 uncovered (integrated sample)
- rules: 339 total, 0 proved, 339 open
- canary: 20/24 equal

Allowed claims: 形态基线达成（仅回归）

Forbidden claims: J 门槛达标; 语料完备; 规则完备; 语义完备

## Audit

- sampled: 156/1556
- at least one failure: True
- hash-chain checks: 156/156
