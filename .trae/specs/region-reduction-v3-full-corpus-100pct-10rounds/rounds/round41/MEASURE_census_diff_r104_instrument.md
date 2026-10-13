# `census_diff_r104.py` — a 2-second, judge-correlated structural test (certified on two controls, 07:13)

`allwin` and `win_r91` blank jump operands, which is why a candidate can read `delta=0 / hunks=0` and still be
judged *Different control flow*. This rig replaces the blanked comparison with **edge structure**: per-target
in-degree multiset, back-edge count, jump-site count, and the full opcode-name sequence — computed by compiling the
candidate text and disassembling the same-named code object against the original `.pyc`.

usage: `python -X utf8 .trae/specs/…/rounds/round41/census_diff_r104.py <product.py>`

## Controls (a finished instrument must pass both)

| arm | instrs | back | jsites | opseq equal | **indeg equal** | judge |
|---|---|---|---|---|---|---|
| ORIGINAL pyc `clock_worker` | 1442 | 4 | 123 | — | — | — |
| **`GOLD_realtime_event_source_PROOF.py`** (the 13/13 oracle) | 1442 (+0) | 4 (+0) | 123 (+0) | **True** | **True** | `13/13` |
| `GOLD_varE.py` | 1442 (+0) | 4 (+0) | 123 (+0) | **True** | **False** | `12/13` |
| landed pipeline product | 1330 (−112) | 4 (+0) | 114 (−9) | False | False | `12/13` |

varE is the proof the instrument is needed: every count matches and even the opcode-name sequence is identical, yet
the judge fails it — and the rig names the reason in one line:

```
indeg top, original : (6 -> @9194), (5 -> @4984), (4 -> @9144), (3 -> @7164) …
indeg top, varE     : (7 -> @9194), (5 -> @4984), (3 -> @7164), (2 -> @9144) …
```

The original sends **6** jumps to the loop re-entry `@9194` and **4** to the loop-tail label `@9144`; varE sends 7
and 2. That is ladder step 6 (fold the `@8904` chained-compare inner `if` into its parent `elif`) expressed as a
countable target, and it is invisible to instruction-text tools. The oracle restores both numbers exactly.

## How to use it from here
Score every candidate step of the ladder with `indeg-equal` as the pass/fail line **before** spending a judge run
(~40 s) or a gate (~13 min). `indeg-equal=True, back-equal=True, opseq-equal=True` on `clock_worker` is a strong
predictor of `13/13`; it is not a substitute for the judge, so installation still requires the judge line plus my
402-file sweep.


## `oracle_diff_r104.py` — the three axes in one command, both controls certified (07:36)

`python -X utf8 rounds/round41/oracle_diff_r104.py <product.py>` prints oracle line-diff vs the 13/13 oracle,
the `census_diff` verdict, and the judge line, in this order.

| arm | `hunks_vs_ORACLE` (clock_worker, 254-line body) | census deltas | indeg/back/opseq | judge |
|---|---|---|---|---|
| POSITIVE: the oracle itself | **0** | `instrs=+0 back=+0 jsites=+0` | True / True / True | `status=success units=13/13` |
| NEGATIVE: landed `realtime_event_sourceOK.py` | non-zero | `instrs=-112 … jsites=-9` | False | `12/13` |

A rig whose positive control is green and whose negative control is red is usable; that is the state. Candidate
adjudication is now one command instead of three, which is what makes a same-turn install+gate possible.
