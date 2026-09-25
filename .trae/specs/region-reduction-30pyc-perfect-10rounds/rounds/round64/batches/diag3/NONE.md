# NONE.md — Round 64, diag3 (what I am NOT claiming, and what failed)

## N1 — No score-moving candidate
Across my four target files I found **no** single-anchor candidate that increases the
official matched-function count. The one real defect I could pin to a line
(`trade_operation`'s join-block over-claim, ANALYSIS §1) is a *one-line* product
misindentation inside an already-failing function, so its best possible official effect is
`jumpdiff 2 → 1` — which J2 delivers. I am **not** claiming J2 as a score mover, and I am
not claiming it as a strict-ruler win either (strict stays 142/159 on both arms; `trade_operation`
is still `[seq_len] 304→302`). Its honest value: a principled widening of W14-C to
`merge is not None` calls, measured REGRESSION=0 on 4 files + 11 pinned shapes, with three
incidental truediff/jumpdiff improvements (`get_tick_direction` 3→1,
`one_prod_to_ndarray` 424→421, `get_real_minute_kline` 197→194).

## N2 — Rejected candidate kept on disk
`specs/cand_r64d3_j1.json.rejected` — over-prunes (`trade_operation` `[304,302,2,40] →
[304,283,2,69]`, and dedents `return True` out of `if len(write_info) > 0:`). Reason
recorded in ANALYSIS §1.3 and localised with `probe_diffarms.py`.

## N3 — THE REPRO FAILED. I could not build a synthetic `.py` that reproduces D1's defect
`test_repros/round64_diag3/r64d3_postif_join.py` / `.pyc` (py3.11) is the fifth attempt.
It is a faithful morphological clone of `trade_operation` — v5's region forest is
one-for-one isomorphic:

```
repro : IfRegion@16  then=[38,54,74,98,118,130,280,292,334,346] merge=388
        IfRegion@38  then=[54]  merge=74          IfRegion@74  then=[98]  merge=118
        IfRegion@118 then=[130] else=[280,292,334,346,388] merge=14      <-- over-claim
        IfRegion@280 then=[292] merge=334         IfRegion@334 then=[346] merge=388
real  : IfRegion@656 then=[678..918] merge=1000
        IfRegion@678 then=[690] merge=704         IfRegion@704 then=[716] merge=726
        IfRegion@726 then=[738] else=[874,886,896,908,918,1000] merge=654 <-- over-claim
        IfRegion@874 then=[886] merge=896         IfRegion@896 then=[908] merge=918
```

Block 388 (= the post-if `out.append(r)` join statement) is collected into the nested
region's else arm by `_collect_branch_blocks(entry=200, merge=14)`, exactly as 1000 is by
`entry=874 merge=654`. **Yet the product is correct: `h62.py run --arm=landed` on the repro
reports `2/2` matched, and the `j2` arm also `2/2`.** So the blocking conjunct at
`region_analyzer.py:26569` is *necessary but not sufficient* for the visible symptom, and
`region_ast_generator.py` absorbs the identical over-claim in the synthetic case but not in
`trade_operation`. I did not find the extra ingredient within budget; I am reporting the
failure rather than shipping a repro that does not reproduce.

Two hypotheses were tested; only the first is a real precondition, the second was falsified:
1. **Precondition (measured).** The join block must NOT be the `LoopRegion.back_edge_block`,
   else the caller-side in-loop filter at `region_analyzer.py:18291` deletes it before the
   region is built (v1-v3 died here). Back-edge choice is `max()` over
   `(no exc-epilogue ops, #non-jump instructions, start_offset)` at
   `region_analyzer.py:4088-4095`, so the `continue` block must carry more statements than
   the join block — real: `738 → (1,22,738)` beats join `1000 → (1,6,1000)`; v3 repro tied at
   `(1,6,·)` and the join block won the start_offset tiebreak (evidence:
   `logs/probe_be_tradeop.txt`, `logs/probe_be_repro.txt`, `logs/probe_loop_*.txt`).
2. **Falsified hypothesis.** That the enclosing `if` must sit below additional sequential `if`s
   inside the outer `if` body. v4 (single level) already carries the over-claim
   (`IfRegion@38 else_blocks=[200,212,254,266,308]`), and v5 (three levels, isomorphic to the
   real forest) is still 2/2 clean — so extra nesting buys nothing.

**Follow-up for whoever owns `region_ast_generator.py`:** the discriminating question is why
the emitter honours the stolen block in `trade_operation` and self-heals in the clone. Start
from `_current_if_regions`/`block_to_region` registration order for the two cases
(`logs/probe_cbb2_tradeop.txt` vs `logs/probe_cbb2_repro_v5.txt`).

## N4 — Deliberately NOT proposed
* No same-level region guard for the F1/F2-classified defects (`trade_operation`'s
  1464/1466 epilogue hunk, `real_quote`'s five large-truediff functions,
  `_save_testds_to_csv`'s mangled import, `_on_publish_after_trading_end`'s dropped loop
  body) — per the brief, those are expression-emission / epilogue families whose
  suppression fixes were falsified in earlier rounds.
* No change at a `merge = else_succ` site (region_analyzer.py:17633) — that anchor is a
  non-monotone cascade and my measurement did not require it.
* No claim that J2 is safe corpus-wide: it is measured on **4 files + 11 pinned shapes only**
  (per the 300 s / no-402-file-sweep rule). The center must run the full corpus gate.

## N5 — Not diagnosed by me this round
`real_quote` (all 5), `get_trade_list` `[339,323,14,148]`, `get_TradeMode_trades`
`[1839,1753,4,1620]`, `_on_set_positions` `[seq_len] 297→298`, `base_order`
`[target_diff] #136`. See ANALYSIS §5 for the reason and for the first probe to run.
