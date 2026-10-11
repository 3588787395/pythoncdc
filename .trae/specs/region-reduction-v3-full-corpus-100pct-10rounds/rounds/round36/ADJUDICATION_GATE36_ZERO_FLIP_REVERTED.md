# Gate 36 adjudication — hunk A certified corpus-wide at zero flips, reverted; round 36 lands nothing

## Chain (single clean run, strictly serial)

`python -X utf8 .trae/specs/.../gate_chain.py 36 35` with the repo holding only hunk A
(`core/cfg/region_ast_generator.py` `87910190b7ef7c35` → `7344dcc566442e58`), analyzer untouched at
`35e227ac3e7b25af`. Log `D:/Temp/gate_chain_36_030645.log`, boot `D:/Temp/gate_chain_36_boot.log`:

```
STAGE regen   rc=0  364s   [regen 合计] ok=402 bad=0
STAGE verify  rc=0  162s   786/786  469/469  538/538  887/887  855/855  998/999  797/801  1281/1282
STAGE report  rc=0    0s   [units] 6611/6617 -> 6611/6617 (99.9093%)  [files] 399 -> 399
                          [gates] 文件级回退=0  UNIT_REGRESSIONS=0  新增失败单元=0  翻正单元=0
STAGE checks  rc=0  113s   quotation 153/153 | small34 1562/1568 | selfcheck 判据可用 | pytest 2 failed 282 passed 2 xpassed
CHAIN_DONE label=36
```

Every shard number equals the round-35 sealed baseline (summed independently from
`rounds/round35/after/shard*_report.json`: 6611/6617, 399/402 files), so the corpus verdict is
byte-for-byte unchanged: **hunk A restores the swallowed statement but flips no unit anywhere in the
402-file verification face.** Therefore it is not installed (registered rule: fix tickets are
accepted on measured flips, zero-flip predicates are banked and reverted byte-exactly).

### small34 reading corrected, my own stale note falsified

I flagged `small34 1562` against the 1560 recorded in project memory as an unexplained +2 while all
shards held, and went to check instead of writing it up. `D:/Temp/r9main/gate_small34_35.json`
(generated_at 2026-10-12T02:11, i.e. the gate-35 chain itself) already reads
`units_success 1562, units_total 1568, success 31, failure 3`, and a per-row diff of the 35 vs 36
JSONs returns **0 differing rows**. So the witness moved nothing; the stale number was in my note,
not in the corpus. Project memory corrected.

## Revert proof

`git status --porcelain -- core/ site-packages/` before the revert listed exactly the two files the
chain was expected to touch (`core/cfg/region_ast_generator.py`, and the broker product rewritten by
regen). After restoring the generator from `D:/Temp/r36/pristine_87910190b7ef7c35_region_ast_generator.py`
(sha16 `87910190b7ef7c35`) and `git checkout -- site-packages/`, the same command returns **0 lines**.
The mirror `D:/Temp/r30chk` is likewise restored byte-identical (`cmp` against the repo) for both
core files.

## Banked this round (all reproducible from the named base bytes by the named builder)

| file | hash | base | verdict |
|---|---|---|---|
| `CANDIDATE_r36_R21-33a_store_split_BANKED_not_landed.py` | `7344dcc566442e58` | gen `87910190b7ef7c35` | fires, 0 flips corpus-wide at gate 36, 0 regressions; co-requisite for `_trade_status_handle` (−3/3 → +6/2) |
| `CANDIDATE_r36_R21-33b_while_true_region_analyzer_BANKED.py` | `efd455859b69d8a1` | analyzer `35e227ac3e7b25af` | the correct loop shape (measured by `compile()` signature match), victim −3/3 → **+1/2**, no flip |
| `CANDIDATE_r36_R21-33c_merge_join_FALSIFIED.py` | `7a02cc2a06d55447` | gen `87910190b7ef7c35` | generator-side merge placement: **−85/2**, a regression; closes the generator-only route |
| `CANDIDATE_r36_M1_M3b_merged_BANKED_not_landed.py` | `3d4f27de6d80ab6e` | gen `87910190b7ef7c35` | M1+M3b re-anchored as a pair: clock_worker −113/7 → **−3/8**, relocation not placement; no flip |

A banked-bytes trap worth the record: the first copy of the hunk-B candidate hashed
`35e227ac3e7b25af`, i.e. pristine, because an earlier restore had already overwritten the mirror.
It was rebuilt from its own builder and re-hashed to `efd455859b69d8a1` before banking; a banked
candidate whose bytes are not its candidate is worse than no candidate.

## Round 36 status against the spec's per-round bar

The spec demands at least one pyc solved per round. Round 36 solved none: the only two mechanisms
left in the corpus each need a *second* criterion that has now been measured rather than guessed —
`_trade_status_handle` needs the analyzer to declare the nested `IfRegion` (R21-34, task #85), and
`clock_worker` needs the else-arm statements placed at their own offsets instead of spliced late
(NOTE_R21-34 §1). Both are recorded with their numbers, the residual stays **3 files / 6 units at
6611/6617 (99.9093%), 399/402 files**, and the next gate label remains 36 against
`rounds/round35/after` because nothing landed.
