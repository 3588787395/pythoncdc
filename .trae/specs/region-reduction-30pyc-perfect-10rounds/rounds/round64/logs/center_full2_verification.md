# Center verification record — Round 64 merged set (what landed)

Landed by replay of the measured mirrors (`land63.py land --spec … --mirror … --apply`,
`closeout64.py landproof mirr_full2` => 33 core files same=33 diff=0).

```
core/cfg/region_ast_generator.py  3 086 600 -> 3 103 160 B   12 edits +208 lines
                                  BOM kept, CRLF 50 145, bare LF 0, sha c6c6a7dd69ab3ff64b8b
core/cfg/region_analyzer.py       1 721 959 -> 1 724 219 B    1 edit  +35 lines
                                  no BOM, CRLF 27 625, bare LF 0, sha 9b5cae3ce5a96bc39eec
```

## 1. Provenance of the 13 edits (each was measured single-variable against landed bytes first)

| # | source spec | file | edits | what it recognises |
|---|---|---|---|---|
| 1-2 | `diag4/specs/cand_r64d4_a_deferred_prefix.json` | generator | 1 | `[R64-D4-A]` `_try_deferred_return_in_loop`: the discarded block prefix is re-emitted through `_generate_stmts_from_instrs` when `len(_r64d4_pre) >= 2` and every produced node is `Assign|AugAssign|Expr|Return|Delete` |
| 3 | `diag4/specs/cand_r64d4_b_boolop_poptop_stmt.json` | generator | 1 | `[R64-D4-B]` BoolOp value region whose merge block starts with `POP_TOP` and `_si >= 1`: emit the solo stack statement as `Expr` alongside its statements instead of folding it into the `Assign` |
| 4 | `diag2/specs/cand_r64b2_chaincompare_yield.json` (c1) | generator | 1 | chained-compare value yield at a sibling region entry (same-level `D.parent is U.parent`) |
| 5 | `diag2/specs/cand_r64b2_condcomp_consumer.json` (c2) | generator | 1 | conditional-context consumer of a chained comparison (`if _ni.opname in ('STORE_FAST','STORE_NAME', …)`) |
| 6-12 | `diag1/specs/cand_r64b1_both.json` (c1+c2) | generator | 6 | sibling merge-entry dispatch (1 edit) + FORMAT_VALUE conversion back-fill in the f-string layer (5 edits) |
| 13 | `diag1/specs/cand_r64d1b_kbin.json` | analyzer | 1 | `_detect_boolop_conditional_chain` (landed L25558 `if len(chain) >= 2:`): stop accepting the chain once the prefix is closed on one shared exit `T` and `current` reaches `T` neither as jump target nor as fallthrough |

`mkfinal.py` chained-uniqueness replay ordered by offset: 12 generator edits merge with no anchor
collision (each anchor still occurs exactly once after the previous edits), 1 analyzer edit.

## 2. Corpus ladder (mirror harness `h62.py`, official ruler, 402 files, Σfc 5746)

| arm | contents | matched | files fully OK | A/B vs landed |
|---|---|---|---|---|
| `landed402_r64` | R63 bytes | 5677 | 382 | baseline |
| `d4ab` | 1-3 | 5684 | 383 | IMPROVED=4 REGRESSION=0 MOVED=0 SAME=398 |
| `d4ab_c1` | 1-4 | 5685 | 383 | IMPROVED=1 REGRESSION=0 MOVED=0 SAME=401 |
| **`d4abc1_d1k`** | 1-13 | 5688 | 384 | IMPROVED=7 REGRESSION=0 MOVED=2 SAME=393 |
| **`full2` (landed)** | 1-13 | **5689** | **384** | **IMPROVED=8 REGRESSION=0 MOVED=3 SAME=391** |
| `d4abj2` (rejected) | 1-4 + diag3 J2 | 5681 | 381 | **REGRESSION=2** |

Blast radius of the landed set = **11 of 402 products** (sha-level): `main`, `graph`,
`common_func`, `crypto_utils`, `api_base`, `scheduler`, `quote_handler`, `logger`, `klinedata`,
`risk_calculation/__init__`, `trade_live_broker`.

Pinned battery `shapes_r63.txt` (11 pyc, 48 checks): landed **34/48, 4 clean** → full2 **42/48,
7 clean**, `ab` REGRESSION=0 (r63_ft, r63_ft2, tail_cmp_return go clean; probe_r63b2_cases 6→7;
probe_r63b2_cases2 3→7). Canary `canary4.txt` (204 functions): **byte-identical** (SAME=4).

## 3. Strict-ruler adjudication of the three MOVED rows (G4′)

Strict over the 11 changed products: **480 → 492 ok functions (+12)**; per file

| file | official landed → arm | strict landed → arm |
|---|---|---|
| `IQCommon/common/main.pyc` | 29/33 → **33/33** | 29/31 (missing=3) → **34/34 (missing=0)** |
| `fly/data/quote_handler.pyc` | 55/57 → **57/57** | 68/72 → 69/72 |
| `IQCommon/util/crypto_utils.pyc` | 9/9 → 9/9 | **7/9 → 9/9** (MOVED is a strict *fix*) |
| `IQCommon/api/klinedata.pyc` | 42/45 → 42/45 | **56/63 → 54/63** (the only cost) |
| `IQCommon/graph.pyc` | 29/31 → 30/31 | 32/34 → 33/34 |
| `IQCommon/util/common_func.pyc` | 18/21 → 19/21 | 19/22 → 20/22 |
| `IQData/api/api_base.pyc` | 23/25 → 24/25 | 25/27 → 26/27 |
| `IQEngine/utils/scheduler.pyc` | 42/45 → 43/45 | 48/52 → 49/52 |
| `fly/logger.pyc` | 28/30 → 29/30 | 61/64 → 62/64 |
| `trade_live_broker.pyc` | 104/119 → 105/119 | 102/123 → 103/123 |
| `risk_calculation/__init__.pyc` | 32/35 → 32/35 (`get_TradeMode_trades` decomp 1753 → 1801 of orig 1839) | 33/37 → 33/37 |

Attribution of the two negative MOVED rows was measured, not assumed: stacks `att_sib`
(d4ab_c1+diag1 c1) and `att_fv` (d4ab_c1+diag1 c2) both leave `klinedata` at
`get_multiminute_his_data [479,478,3,16]`, while `att_kbin` (d4ab_c1+analyzer edit) moves it to
`[479,478,5,16]` and reflows `crypto_utils`. So the analyzer chain-stop edit
`cand_r64d1b_kbin.json` is the sole cause of both rows — and also the sole cause of
`crypto_utils` 7/9 → 9/9 and of `quote_handler` reaching 57/57. Net over its two-ruler impact:
official +2, strict +1, adopted knowingly with `klinedata` −2 recorded as this round's cost.

## 4. Rejected candidates (kept in `batches/`, with their measurements)

| arm | why rejected |
|---|---|
| diag3 `cand_r64d3_j1` | over-prunes `trade_operation [304,302,2,40]` → `[304,283,2,69]` and dedents `return True` out of its loop |
| diag3 `cand_r64d3_j2` | official-neutral on its own 4 files + 11 repros, but stacked on d4ab it measures **REGRESSION=2** over the 402 (`strategy.pyc` 24/24 → 23/24, a previously fully-OK file), clean files 383→381, and deepens `clock_worker [1275,1286,10,481]` → `[1275,1288,9,489]`, `ipo_stocks_order [1075,1076,10,437]` → `[1075,1080,13,445]` |
| diag5 `cand_r64d5_contbare` / `_contbare2` / `_r57e_direct` | arms `cA`, `cA2`, `dgB`, `cW` all measure **77/85 on its own four targets — identical to landed 77/85**, battery stays 34/48 ⇒ no measured gain to adopt |
| diag5 `diag_r64d5_contsink` / `diag_r64d5_flip2` | hard-code function/file names (跨区域按名启发)，rejected on shape by the design law before measurement |
| diag1 `r64d1b_sibdispatch_attempt` repro | c1's shape did not reproduce synthetically (recorded in `diag1/NONE`-style honesty note); the shipped c1 stays justified by its corpus witness only |

## 5. Residual leads for Round 65

- `realtime_event_source :: clock_worker [1275,1286,10,481]` — diag1 Job 3: the product emits
  `elif check_trading_time(...)` **twice** (OK.py lines 275 and 312) against one original call
  site (@8594): a ~110-instruction duplicate-arm insertion offset by a ~100-instruction deletion
  @6690, so the +11 net is meaningless. Owner = elif-chain dispatch (`_if_generate_normal` / R61
  channel); the defect is **duplicate emission**, not loss.
- `flyAccount :: _do_request [436,443,2,384]` overshoot (+7) still open; R63 pointed at
  `_loop_build_if_with_exit_branches`.
- `matcher :: match` displacement lead (memory `project-r64-matcher-displacement-lead`):
  orig[180:462]投到产物尾部，属排序问题而非归属问题。
- `region_ast_generator.py` carries **10 leftover `import os as _os_dbg_*` debug imports**
  (L32916, L44320, L46899, L47059, L47107, …) — behaviour-neutral junk; schedule a cleanup round
  gated on 402-file byte-identity.
