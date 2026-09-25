# diag4 (R64) — center reading of its on-disk dumps at 08:00 (agent still running)

**This batch contains the round's closer.** From `diag4/dump/*.jsonl` (4 targets, official ruler):

| arm | 4-file matched | main.pyc | graph.pyc | fly/logger.pyc | fileio_utils.pyc |
|---|---|---|---|---|---|
| landed | 98/108 | 29/33 | 29/31 | 28/30 | 12/14 |
| a = `specs/cand_r64d4_a_deferred_prefix.json` (1 edit, +25 lines, three-element comment present) | **103/108** | **33/33 → fully OK** | **30/31** | 28/30 | 12/14 |
| b = `specs/cand_r64d4_b_boolop_poptop_stmt.json` (3 edits, +29 lines, no AST-mapping comment) | 99/108 | 29/33 | 29/31 | 29/30 | 12/14 |

`main.pyc`'s two open defects on landed were `get_same_shard_server_ip_info` [192,173,11,62] and
`get_server_ip_info` [194,166,9,71] — arm a clears **4 functions** on that file (29→33 of 33), which
satisfies Round 64's mandatory "at least one pyc decompiled completely OK" on its own, and also clears
one of `graph :: _get_influence_task` [207,195,2,124].

What the center must still prove before adopting (do NOT take the agent's word):
1. re-measure arm a in the **center** harness (`mbuild.py`/`h62.py` under `r64gate`, not diag4's ROOT),
   single-variable against landed bytes `7ec41fa2f9cdd5d62c1a` / `c694d2514eb2f2b21ccf`;
2. pinned battery `shapes_r63.txt` (landed = 34/48, clean 4/11) — diag4 has no `shapes_a.jsonl` yet;
3. canary (quotation 143/143 official + 148/150 strict, market_time 10/10) must be byte-unchanged;
4. strict ruler both sides — `diag4/dump/strict_a.json` vs `strict_landed.json` exist, read them;
5. the 402 A/B against `r64gate/dump/landed402_r64.jsonl` (402 files, matched 5677, clean 382),
   expecting REGRESSION=0 and MOVED ⊆ {main, graph, …};
6. whether a and b compose (b fixes `logger :: logging_process` [99,95,2,62] which a does not).

Also noted while reading: **diag5 has produced no improvement yet** — its `cA`/`cA2`/`dgA`/`dgB` arms all
stay at 77/85 on its 4 files; `cA2` only reshapes `matcher :: match` ([715,715,10,517] →
[715,715,**27**,336]: jump-target diffs grow while true-diffs shrink — a MOVED, not an IMPROVED), and its
battery is unchanged at 34/48. `diag5/specs/diag_r64d5_contsink.json` and `diag_r64d5_flip2.json` contain
hard-coded function/file names (flagged by `specscan.py`) ⇒ reject-on-shape if they resurface as shipping
candidates.

## Strict ruler confirms arm a is structural, not a counting coincidence
`diag4/dump/strict_landed.json` vs `strict_a.json` (strict ruler counts nested code objects too):

| file | landed | arm a |
|---|---|---|
| main.pyc | ok 29/31, **missing** = `<get_same_shard_server_ip_info>.<dictcomp>`, `<get_server_ip_info>.<dictcomp>`, `<get_server_ip_info>.<lambda>` | **ok 34/34, missing = [], extra = [], bad = []** |
| graph.pyc | (see its own row) | ok 33/34, one `seq_diff #119 orig=('None','LOAD_CONST') decomp=('<JUMP>','JUMP')` in `_process_task_queue` |

So the landed toolchain does not emit **three nested code objects** of `main.pyc` at all, and arm a
restores all of them — that is the kind of whole-unit loss the "deferred prefix" rule was diagnosed to
prevent, which is why the official count moves by 4 on that file rather than 2.
