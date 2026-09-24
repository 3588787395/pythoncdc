# Round 63 central verification EVIDENCE (live log)

HEAD at round open = `96a5f310` (Round 62 record). Landed bytes measured throughout:
`core/cfg/region_ast_generator.py` sha256 `b9778ee0130865d55888` / 3 059 418 B / BOM / pure CRLF,
`core/cfg/region_analyzer.py` sha256 `eab9c782a0b6` / 1 719 972 B / no BOM / pure CRLF.

## A. Instrument validation
- Central corpus baseline reused: `D:/Temp/opencode/r62gate/dump/f4_402.jsonl` — 402 records,
  402 unique paths, 0 errors, Σmatched 5675, Σtotal 5746, 381 fully-matched files.
- Each of the five batch agents re-measured its own targets with `--arm=landed`; all 21 partial
  rows agree with the published FACTS (see `collect` run + `diag*/dump/landed.jsonl`).
- `diag4/dump/landed_402.jsonl` vs central `f4_402.jsonl`: **0 disagreements** over 402 records
  (matched count AND product sha) → diag4's arm resolution is sound, so its 402 candidate dumps
  are usable evidence once the candidate mirror is proven identical.
- Mirror identity proven by hash: central `mirr_b4s/core/cfg/region_ast_generator.py` ==
  `diag4/mirr_c3/...` == `c54b2d972170084aa55e…` (20-hex prefix). The shipped bytes are literally
  the measured bytes.

## B. Five-batch deliverables and central readings
| batch | deliverable | central reading | disposition |
|---|---|---|---|
| diag1 (trade_live_broker, quote, quote_handler) | `specs/cand_fstail3.json` (generator, 3 edits, +287 lines) | own witnesses: `fund_transfer 123→88 (−35)` becomes `123→98 (−25)`; other 2 files byte-identical; TALLY REGRESSION=0 IMPROVED=0 MOVED=1 SAME=2 | witness moves but no file flips; 402 not yet measured centrally |
| diag2 (klinedata, real_quote, scheduler) | `specs/FALSIFIED_cand_chainmerge_armowned.json` + `NONE.md` | measured here first: 3/3 files defect-set identical to landed (scheduler `is_run_interval_time_now 225/201` unmoved) → INERT | rejected (agent agrees; renamed to FALSIFIED) |
| diag3 (matcher, realtime_event_source, graph, fly/logger, fileio_utils) | `specs/cand_r63_claim.json` + `NONE.md` | anchor-OK but agent-measured inert on its own witness (same-level BoolOp sibling is never dispatched) | rejected; mechanism handed to `fix1` implementer |
| diag4 (api_base, history_data_source, risk_calculation, wizard_quant_api, main) | `specs/c1.json`, `specs/c2.json`, `specs/cand_r63b4_tern_slot.json` | c1 (delete the containment disjunct): history_data_source 16/18→17/18, 402 REGRESSION=0 IMPROVED=1 MOVED=2. c2 (slot set {entry, condition_block, merge_block, elif_conditions}): 402 REGRESSION=2 (order_api.base_order, order_api_trade.order_market) → falsified. tern_slot (`r.entry is region.entry or region.parent is r`): same witness, 402 REGRESSION=0 IMPROVED=1 MOVED=2 SAME=399, Σmatched 5675→5676 | **candidate to land** |
| diag5 (common_func ×2, order_api, flyAccount, trade_info_utils) | `specs/cand_r63b5_hdrjt.json`, `cand_r63b5_hdrjt2.json` | agent-measured: witness `init_connection [42,41,0,25]` → `[42,41,3,12]` moves, but deficit stays −1 and the emitted shape loses `i += 1` / inner `break`; c2 variant `[42,41,2,15]` worse | rejected for landing, documented for R64 |

## C. Strict-side deltas of the shipping candidate (tern_slot, 402)
```
history_data_source.pyc   16 -> 17   get_price [550,544,4,475] -> gone   sum truediff -475
trade_live_broker.pyc    104 -> 104  fund_transfer 123->88 => 123->106 ; market_fund_transfer 94->67 => 94->77   truediff +0
flyAccount.pyc            21 -> 21   _do_request 436->429 => 436->443 (overshoot +7), truediff +5
CORPUS over changed files: sum truediff 3749 -> 3279 (-470)
```
Residual to carry as a named item: `_do_request` arm-polarity shape (diag5's own root cause site
`_loop_build_if_with_exit_branches` L10444-10448 — that is the pre-landing line number;
in the landed file the def is at `region_ast_generator.py:10470`, symbol verified present).
Verified inertness attribution: `fix2/dump/b4c_402.jsonl` and `dump/p402_final.jsonl` carry the
identical row `_do_request [436, 443, 2, 384]`, so the overshoot belongs to the b4 pair,
not to chainstore/fstail.

## D. Implementer phase (2 focused agents, same law, private arms)
- `fix1` → `fix1/specs/cand_r63b3_chainstore.json` (generator, 5 edits, +165 lines): new
  `_r63b3_reduce_value_ctx_chain_store` + `_r63b3_is_chain_cleanup_arm`, plus an optional
  `terminator_ops` parameter on `_split_block_condition_prefix` (default `None` keeps the two
  existing consumers byte-identical). Central reading (`mirr_f1`, py_compile OK):
  `matcher.pyc::match 713/689 (−24, jd9, td524)` → `715/715 (0, jd10, td517)` — the 26 lost
  instructions are restored (length parity), official count stays 16/17.
- `fix2` → `fix2/specs/cand_r63b4_boolop_exit.json` (`region_analyzer.py`, 1 edit, +22 lines:
  `_all_ternary_cond_c = not (is_condition_context and merge is not None)`). Central reading
  over batch-4's 5 pyc: `history_data_source 16/18 → 17/18` with `get_kline_by_count` gone,
  REGRESSION=0 SAME=4.
- Combination proven centrally (`mirr_c4g2a` = b4s generator + fix2 analyzer):
  **`history_data_source.pyc 16/18 → 18/18`** (both rows fixed) → the round's fully-OK file.

## E. Final shipping set and its gates
Final merged spec: `final_region_ast_generator.py.json` (9 edits, +474 lines = b4s tern_slot +
b1f f-string tail + fix1 chain-store) + `fix2/specs/cand_r63b4_boolop_exit.json` (analyzer).
`mbuild.py final` → generator 3 086 600 B (BOM, pure CRLF), analyzer 1 721 959 B (no BOM, CRLF);
both `py_compile` OK.

Pinned battery (16 items = 10 R63 repros + 6 R62 dd witnesses), landed → combo(b4s+fix2):
```
matched 39 -> 42   clean 5 -> 7   REGRESSION=0 IMPROVED=2 MOVED=1 SAME=13
  IMPROVED round63_b4/r63b4_tern_in_elif_chain.pyc   2/3 -> 3/3
  IMPROVED round63_fix2/r63b4_cond_boolop_stmt_steal 11/13 -> 13/13
  MOVED    round63_b1/r63_ft2.pyc  t2 109->74 (-35) => 109->92 (-17)
```
21-partial A/B of the FINAL arm vs the central corpus baseline:
```
SAME=17 IMPROVED=1 MOVED=3 REGRESSION=0  net matched +2
  history_data_source.pyc  16/18 -> 18/18 (+2)
  matcher.pyc              16/17 (match 713/689 -> 715/715)
  trade_live_broker.pyc    104/119 (fund_transfer -35 -> 0-length-deficit, market_fund_transfer -27 -> -17)
  flyAccount.pyc           21/23 (_do_request 429 -> 443 vs orig 436: shape overshoot, carried as drift item)
```
Corpus A/B: `dump/p402_final.jsonl` (8 shards) vs `D:/Temp/opencode/r62gate/dump/f4_402.jsonl` —
result recorded below.

## F. Corpus A/B result of the final arm  (measured — gate closed 04:32)

### F.1 402-file A/B, round-start landed bytes vs final arm
`h62.py ab --a=D:/Temp/opencode/r62gate/dump/f4_402.jsonl --b=dump/p402_final.jsonl`
(A = R62 shipping state 402 records; B = `mirr_final`, proven byte-identical to the
worktree by `closeout63.py landproof mirr_final` → 33 core files, same=33 diff=0):

```
TALLY SAME=398 IMPROVED=1 REGRESSION=0 MOVED=3 ERR=0     blast radius 4/402
IMPROVED history_data_source   16/18 -> 18/18
MOVED    matcher               match [713,689,9,524] -> [715,715,10,517]
MOVED    trade_live_broker     fund_transfer [123,88,1,57] -> [123,123,0,6]
                              market_fund_transfer [94,67,1,41] -> [94,77,1,41]
MOVED    flyAccount            _do_request [436,429,2,379] -> [436,443,2,384]
files fully matched: a=381 b=382      summed matched: 5675 -> 5677
```

### F.2 Landed-byte re-measurement (independent of the mirror)
`fix1/dump/wl.jsonl` is a *separate process* that read the live worktree after landing.
Cross-checked against `dump/p402_final.jsonl`: 402/402 records paired, zero unpaired,
summed matched 5677 = 5677, fully-matched files 382 = 382, and per-file
`(matched_functions, sha)` disagree on exactly **one** file (`flyAccount.pyc`, 21/21 with
different text sha — the two runs differ only in that product's bytes, official count
unchanged). The landed worktree therefore reproduces the measured combo.

### F.3 Battery on the LANDED bytes (`logs_g6_battery_landed.txt`, 16 items)
matched 42, clean 7 (r63b3 2/2, r63b4_tern 3/3, r63b4_cond_boolop 13/13, r62f_r102name,
w_B, w_C, w_D 2/2), `candidate columns worse-than-landed on 0 repro(s)`.
Residual deficits carried as known debt: r63_ft4 d=-9, probe_r63b2_cases d=-18,
probe_r63b2_cases2 d=-94, repro_r63b2_tail_cmp_return d=-24, r63b5_w1 d=-1, w_A d=-4, w_E d=-2.

### F.4 Official serial gate on the landed worktree
```
G1 single  target history_data_source.pyc      18/18 100.00%  (OK.py rewritten by the toolchain, 31915 chars)
G2 single  fly/data/quotation.pyc              143/143 100.00%;  strict 148/150, defect set verbatim unchanged
           fly/common/market_time.pyc          10/10 official + 10/10 strict
G3 batch --index pyc_index.json --all --round 63  402 verified / 0 failed / ok 382 / partial 20
G4 stats                                      5746 funcs / 5677 matched / 98.80%
```
Index diff vs HEAD, entry by entry: 402 entries, no adds/removes; **401** differ only in
`last_tested_round`; exactly **1** entry changed otherwise — the target
(`partial→ok`, `16→18`, `0.8888…→1.0`). Tracked products modified in the worktree: exactly
4 `*OK.py` = the F.1 IMPROVED/MOVED set. No generated file was hand-edited.

### F.5 Strict-ruler defect-set diff over the 4 moved files (HEAD vs now)
`prevok/difftot.json` (HEAD blobs materialised privately, repo untouched):
```
history_data_source  22/24 -> 22/24  get_kline_by_count 844(-13) -> 859(+2); get_price 549(-4) -> 555(+2)
matcher              16/17 -> 16/17  match: seq_len 689/715 GONE, replaced by seq_diff #182 (order, not loss)
trade_live_broker    102/123 -> 102/123  fund_transfer seq_len 88 GONE -> seq_diff #75 FORMAT_VALUE const;
                                         market_fund_transfer 67(-27) -> 77(-17)
flyAccount           21/23 -> 21/23  _do_request 431(-5) -> 445(+9)  [overshoot, recorded as debt]
```
No file lost a strict match count.

### F.6 Arms rejected by measurement (not by prose)
```
fix1 wg-vs-wl pair  REJECTED as evidence: base mismatch proved at byte level —
      mirr_g1 sha 082fa9910150acc9f2a7 == central mirr_f1, `getattr(region,` count 175
      (pre-tern_slot), size 3 069 504 vs landed 3 086 600. Its "REGRESSION 18/18->16/18"
      measures the *absence* of the other two edits, not a chainstore defect. chainstore's
      own witness is the matcher row in F.1.
fix1 mirr_nog1      comparator only (spec note: "never landed"); wn.jsonl stopped at 185/402
      when the agent died, so no conclusion was drawn from it.
fix2 f3             (store-gate removed) 16/18 on target and 11/13 on its own repro -> falsified
fix2 b4x            (expansion switched off wholesale) target stops at 17/18; 402: SAME=401
      IMPROVED=1 REGRESSION=0, files 381 -> 381 — strictly dominated by the narrow gate.
diag2 c1            (analyzer, batch 2) inert on its own named witness — renamed FALSIFIED_*
```


## G. b1f单独读数 (adopted evidence, mirror-identity proven)
`diag1/mirr_c2` and `mirr_c4` and central `mirr_b1f` are byte-identical
(`90e1a8df8ff3d8fc7f5b`, 3 074 467 B). `diag1/dump/c2_402.jsonl` + `c2_402s1.jsonl` = 402 records,
no overlap, 0 errors: products changed = **1** (`trade_live_broker.pyc`), IMPROVED=0,
REGRESSION=0, Σmatched 5675→5675, `fund_transfer −35 → −25`.

