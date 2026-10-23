# Gate Report

- overall: **BLOCKED**
- blockers: G1, G2a, G2b, G2c, G3, G4, G6

| gate | status | key reading |
|---|---|---|
| G1 | **FAIL** | 51/1556 covered, 6 diffs |
| G2a | **FAIL** | 51/100, diff=6 |
| G2b | **UNESTABLISHED** | 0/402, diff=? |
| G2c | **UNESTABLISHED** | 0/46, diff=? |
| G3 | **UNESTABLISHED** | killed=? survived=? |
| G4 | **INCONCLUSIVE** | proved=0/339, reason=no_rule_traces |
| G5 | **PASS** | 6617/6617, baseline-only |
| G6 | **FAIL** | 20/24, leaks=0 |

## Dual readings

- shape: 6617/6617; 1568/1568; 153/153; v8 128/0/0 (100%)
- judgment: 51/1556 covered; 6 semantic failures; 1505 uncovered (integrated sample)
- rules: 339 total, 0 proved, 339 open
- canary: 20/24 equal

Allowed claims: 形态基线达成（仅回归）

Forbidden claims: J 门槛达标; 语料完备; 规则完备; 语义完备

## Audit

- sampled: 6/51
- at least one failure: True
- hash-chain checks: 6/6
