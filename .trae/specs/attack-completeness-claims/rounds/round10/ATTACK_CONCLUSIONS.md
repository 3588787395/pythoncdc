# Attack Conclusions — L0–L6

This is the terminal index of attack conclusions. It summarizes already-recorded evidence; it does not re-adjudicate it and does not add new code fixes.

| layer | conclusion | key reading | evidence |
|---|---|---|---|
| L0 theory | **Breached**: C1 field formula does not match the implementation; the induction step is not binary-closed; region uniqueness/ownership has counterexamples | 22 tie blocks; triple-combination probes break the binary projection; B172–B176 | `rounds/round2/ATTACK_L0_THEORY.md` |
| L1 measure | **Breached**: 128 is not a mutually exclusive language partition; variant dimensions are folded; line-level evidence is incomplete | 97-node set misses 7 node types; 279 declared variants → 118 triggered (42.3%); 24/25 rows have gaps | `rounds/round3/ATTACK_L1_MEASURE.md` |
| L2 judge | **Breached**: `pyc_verify` does not execute and is semantically blind to value/annotation/docstring/argument-slot differences | mutation miss **366/1311 = 27.92%**; `x=1→x=True` **83/84 = 98.81%**; function docstring **108/108**; parameter reorder **159/162** | `rounds/round4/ATTACK_L2_JUDGE.md` |
| L3 mechanism | **Breached**: 0/7 mechanism families are shape-general; guard families conflict under stacking; B142 is shape-level | 6 stacking probes collapse; H1–H11 hazards; B142 elevated, B143 reduction-level | `rounds/round5/ATTACK_L3_MECHANISM.md` |
| L4 runtime | **Breached**: off-corpus real pyc judge-green rate is low; semantic differences are executable; scale is superlinear | 46 real pyc: judge green **4/46 = 8.70%**, uncompileable **7/46 = 15.22%**, unit **2765/3079 = 89.80%**; execution diff **14/56**; 4000 statements ≈ 89.84 s | `rounds/round6/ATTACK_L4_RUNTIME.md` |
| L5 evidence | **Breached**: the 402 corpus has no usable original source; the 6617/6617 result is judge self-consistency, not semantic truth | original source **0/402**; 405 stamps / 3342 records / **197** unique products; 10/32 forms zero; 61.44% ≤3 forms; 402/14237 = 2.82% | `rounds/round7/ATTACK_L5_EVIDENCE.md` |
| L6 method | **Delivered, not passed**: four-pillar method + falsifiable gates + roadmap; tooling implemented for semantic diff, mutation, J space, rule manifest, fuzz, canary, gate report | method + review + roadmap; tools and selftests in `round9/` | `rounds/round8/COMPLETENESS_METHOD.md`, `METHOD_REVIEW.md`, `roadmap.md` |

## What the attacks established

1. The v8 100% is **not** a semantic or language-completeness result. It is a shape/path count plus a judge that does not execute.
2. The old denominator folds host context, variant slots, and composition depth; the J v2 space (1556 entries) is larger than 128 and currently mostly uncovered.
3. The old judge has a measurable blind spot (27.92% mutation miss; 98.81% on `1` vs `True`). A green unit can still be semantically wrong.
4. The corpus cannot serve as a source-level oracle: 0/402 original sources are usable.
5. The correct terminal reading is **“shape baseline achieved (v8), completeness not established.”**

## What the attacks did not establish

- They did not prove that every B163–B219 item is a distinct product defect; several are measurement/definition defects or need dedup.
- They did not produce a full 1556-entry semantic run, full 402 semantic diff, full mutation report, rule-trace proof, or independent canary custody.
- They did not fix the four Task 9.5 fuzz findings or the six J R7 diffs.
- They did not show that any unexecuted gate would pass if run; “not established” is not “green.”

## Honest terminal classification

| classification | items |
|---|---|
| **Breached with executable evidence** | L0 theory, L1 measure, L2 judge, L3 mechanism, L4 runtime, L5 evidence |
| **Delivered but not validated as complete** | L6 method and the Task 9 toolchain |
| **Blocked at v9 terminal** | G1, G2a, G2b, G2c, G3, G4, G6; G5 baseline only |
| **Closed** | none of B163–B219 in this task |
