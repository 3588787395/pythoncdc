# Round 64 central verification EVIDENCE (live log)

All readings in this file are produced by the two rulers only: the **official** matcher
(`scripts/pyc_batch_verify.py` → `single` / `batch --index pyc_index.json --all --round N` / `stats`,
Σfc frozen at 5746) and the **strict** checker (`_r10_strict_check.py`). They are never cross-subtracted.

## A. Instrument validation before any candidate

* Round-start A/B baseline `dump/landed402_r64.jsonl` (copied from `r63gate/dump/p402_final.jsonl`,
  i.e. produced on the R63 landed bytes): **402 rows, matched 5677/5746, 382 files fully OK**.
* Landed bytes re-fingerprinted at 07:2x: `region_ast_generator.py` 3 086 600 B sha `7ec41fa2f9cdd5d62c1a`
  (BOM + pure CRLF), `region_analyzer.py` 1 721 959 B sha `c694d2514eb2f2b21ccf` (no BOM + pure CRLF).
* diag3 independently reproduced the Round 63 per-function tables on its four files
  (39/44, 38/40, 32/34, 32/35 with the same `[orig, decomp, jumpdiff, truediff]` tuples) ⇒ the
  harness and the baseline agree.
* `rank20.py` → `logs/rank20.txt`: the 20 partials ranked by defect-function count; two are 1 function
  from clean (`realtime_event_source` 11/12, `matcher` 16/17).

## B. Incident: a diagnose agent re-flowed the worktree core file

At 07:51:04 the worktree `region_ast_generator.py` was found as **pure LF, 3 036 663 B,
sha `5ffe31558df46f7f636d`** — text-identical to HEAD (proved by a line-list diff of 49 938 lines),
but it breaks `mbuild.py`/`h62.py` line-ending asserts. Handled without any git write:

* `restore_crlf.py` rewrote the file as CRLF **only after proving** `current.replace('\n','\r\n')`
  hashes to `7ec41fa2f9cdd5d62c1a…`; post-restore hygiene = BOM True, CRLF 49 937, bare LF 0, and
  `git status` clean.
* diag1's continuation independently observed the same drift and rebuilt on the restored base;
  diag1 patched its private `h62.py` and the shared `mbuild.py` asserts to be base-style aware.
* Consequence recorded: after 08:2x the worktree bytes represent **R64**, so any later `--arm=landed`
  reading is the new round's state — re-verified by the G-series below.

## C. Mirror ladder (official ruler, 402 files, one variable at a time)

| arm | contents | matched | files OK | A/B vs round-start |
|---|---|---|---|---|
| `landed402_r64` | R63 bytes | 5677 | 382 | baseline |
| `d4a` | diag4 a (1 edit) | — | — | targets 98→103/108, battery inert, canary inert |
| `d4b` | diag4 b (3 edits) | — | — | targets 99/108, complementary to d4a |
| `d4ab` | a+b merged (4 edits +54) | 5684 | 383 | IMPROVED=4 REGRESSION=0 MOVED=0 SAME=398 |
| `d4ab_c1` | + diag2 c1 (5 edits +87) | 5685 | 383 | IMPROVED=1 REGRESSION=0 MOVED=0 SAME=401 |
| `d4abj2` | + diag3 J2 | 5681 | 381 | **REGRESSION=2** → rejected |
| `d4abc1_d1k` | + diag1 both + kbin (13 edits) | 5688 | 384 | IMPROVED=7 REGRESSION=0 MOVED=2 SAME=393 |
| **`full2` (landed)** | + diag2 c2 (13 edits) | **5689** | **384** | **IMPROVED=8 REGRESSION=0 MOVED=3 SAME=391** |

Battery/canary per stage: pinned `shapes_r63.txt` (11 pyc, 48 checks) 34/48 clean-4 → d4ab 34/48
(byte-inert) → `d4abc1_d1k` 42/48 clean-7, `ab` REGRESSION=0; `canary4.txt` (204 functions)
**byte-identical at every stage** (SAME=4).

`mkfinal.py` merges by offset order with chained uniqueness: after each of the 12 generator edits is
applied, the next edit's anchor still occurs exactly once ⇒ no two candidates share a hunk.

## D. Attribution of the three MOVED rows (measured, not assumed)

Stacks on top of `d4ab_c1`, each measured on the same 3-file list (`att3.txt`:
`crypto_utils`, `klinedata`, `quote_handler`):

| arm | added edit | crypto_utils | klinedata `get_multiminute_his_data` | quote_handler |
|---|---|---|---|---|
| landed | — | 9/9, strict **7/9** | [479,478,**3**,16] | 55/57 |
| `att_sib` | diag1 c1 (sibling merge-entry dispatch) | unchanged | [479,478,3,16] | **56/57** |
| `att_fv` | diag1 c2 (FORMAT_VALUE back-fill) | unchanged | [479,478,3,16] | 55/57 |
| `att_kbin` | analyzer closed-shared-exit-prefix | 9/9, strict **9/9** | [479,478,**5**,16] | 56/57 |

⇒ Both negative-looking MOVED rows belong to the single analyzer edit, which is also the only edit
that can clear `get_kline_binary` (closing `quote_handler.pyc` to 57/57) and the only one that fixes
`crypto_utils` on the strict ruler. Adopted with `klinedata` strict 56→54 recorded as the cost.

## E. Strict-ruler (G4′) view of the whole blast radius

11 products changed out of 402. Strict ok-functions, landed → full2 (`logs/cs_*_cf2.txt`, and
re-measured post-landing in `logs/gate/G4p_strict_blast11.txt`):

| file | official | strict |
|---|---|---|
| `main.pyc` | 29/33 → **33/33** | 29/31 (missing=3) → **34/34 (missing=0)** |
| `quote_handler.pyc` | 55/57 → **57/57** | 68/72 → 69/72 |
| `crypto_utils.pyc` | 9/9 → 9/9 | **7/9 → 9/9** |
| `klinedata.pyc` | 42/45 → 42/45 | **56/63 → 54/63** |
| `graph.pyc` | 29/31 → 30/31 | 32/34 → 33/34 |
| `common_func.pyc` | 18/21 → 19/21 | 19/22 → 20/22 |
| `api_base.pyc` | 23/25 → 24/25 | 25/27 → 26/27 |
| `scheduler.pyc` | 42/45 → 43/45 | 48/52 → 49/52 |
| `logger.pyc` | 28/30 → 29/30 | 61/64 → 62/64 |
| `trade_live_broker.pyc` | 104/119 → 105/119 | 102/123 → 103/123 |
| `risk_calculation/__init__.pyc` | 32/35 → 32/35 (gap 86 → 38) | 33/37 → 33/37 |
| **TOTAL** | 5677 → **5689** corpus-wide | **480 → 492 / 537** |

## F. Arms rejected by measurement (kept under `batches/`)

| arm | measurement |
|---|---|
| diag3 `cand_r64d3_j1` | `trade_operation` [304,302,2,40] → [304,**283**,2,69] (over-pruned) and `return True` dedented out of its loop |
| diag3 `cand_r64d3_j2` | looked inert on 4 files + 11 repros (official-neutral, battery 0 REGRESSION), but stacked on `d4ab` the 402 A/B measures **REGRESSION=2** (`plugin_fly_data/strategy/strategy.pyc` 24/24 → 23/24, previously fully OK), files-OK 383→381, and deepens `clock_worker` [1275,1286,10,481]→[1275,1288,9,489], `ipo_stocks_order` [1075,1076,10,437]→[1075,1080,13,445] |
| diag5 `cand_r64d5_contbare` / `_contbare2` / `_r57e_direct` | arms `cA`, `cA2`, `dgB`, `cW` each measure **77/85 on diag5's own four targets — identical to the landed 77/85**; battery stays 34/48 ⇒ no measurable gain to adopt (`diag5/dump/*.jsonl`) |
| diag5 `diag_r64d5_contsink` / `diag_r64d5_flip2` | anchors hard-code function/file names (按名启发) → rejected on shape by 禁止跨区域跨层次启发式规则, before measurement |
| diag1 `r64d1b_sibdispatch_attempt` | the repro deliberately records that c1's shape did **not** reproduce synthetically (`test_repros/round64_diag1/NONE.md`); c1 ships on its corpus witness only |
| diag4 `r64d4_deferred_prefix` | 3/3 clean on **both** the pre-round and landed bytes ⇒ it is not a discriminating witness for D4-A; `r64d4_boolop_poptop_merge` is (2/3 → 3/3) |

## G. Landing and the serial official gates (post-landing, on the worktree)

```
region_ast_generator.py  3 086 600 -> 3 103 160 B  12 edits +208  sha c6c6a7dd69ab3ff64b8b  BOM CRLF-only
region_analyzer.py       1 721 959 -> 1 724 219 B   1 edit  +35   sha 9b5cae3ce5a96bc39eec  CRLF-only
closeout64.py landproof mirr_full2                 => 33 core files same=33 diff=0
```

| gate | raw log | reading |
|---|---|---|
| G0 py_compile + ast.parse | `logs/gate/` (inline) | both OK; CRLF 50 145 / 27 625, bare LF 0 |
| G1 `single` main.pyc | `G1_single_main.txt` | ok, **33/33, 100.00%**, missing/extra empty, `mainOK.py` 22 110 chars rewritten by the toolchain |
| G2 quotation | `G2_single_quotation.txt` | official **143/143**; strict **148/150**, defect set verbatim (`change_his_to_forward` #250, `get_trend` #10) |
| G2 others | `G2_single_others.txt` | market_time 10/10, `IQCommon/util/datetime_func` 26/26, `IQData/utils/datetime_func` 25/25; strict 61/61, 文件级 3/3 |
| G3 `batch --all --round 64` | `G3_batch_all_round64.txt` | 402 verified, **ok 384 / partial 18 / failed 0**, 5689/5746, 99.01% — exactly what the `full2` mirror predicted |
| G4 `stats` | `G4_stats.txt` | same series as G3 |
| G4′ strict over the 11 changed products | `G4p_strict_blast11.txt` | **492/537**, 文件级全清 2/11 |
| G6 battery, 19 items | `G6b_battery19_landed.txt`, `G6b_battery19_r63.txt`, `G6b_battery_compare.txt` | pre-round column 49 matched / 7 clean → landed column **61 / 14**, 9 witnesses flipped, **0 witness worse** |

Index audit against `HEAD:pyc_index.json` (`idx_head.json`): 402 entries, **0 added / 0 removed**;
`last_tested_round` stamped on all 402; substantive changes on exactly **8 entries** = the 8 IMPROVED
rows (`main` partial→ok 29→33, `quote_handler` partial→ok 55→57, `graph` 29→30, `common_func` 18→19,
`api_base` 23→24, `scheduler` 42→43, `logger` 28→29, `trade_live_broker` 104→105). The three MOVED
files show no index change, which is exactly why the strict ruler is co-equal.

`git status` after G3: 14 tracked modifications = 2 core + `pyc_index.json` + **11 `*OK.py` products**,
and the 11 products are precisely the sha-level blast radius of the mirror A/B (no extra file moved,
none hand-edited).

### G.1 Specimen diff of the two closed files (what "fully OK" actually restored)

`git diff --numstat` on the toolchain products:

* `site-packages/IQCommon/common/mainOK.py` — **7 added, 0 removed**: the whole
  `get_same_shard_server_ip_info` tail came back, including the two dict comprehensions
  (`{name: info['index'] for …}` / `{info['index']: name for …}`), `sorted_keys.index(...)`,
  `msg = '从nginx服务器:%s…'` and `user_log.info(msg)`. Those are the 3 nested code objects the strict
  ruler had listed as `missing` pre-round.
* `site-packages/fly/data/quote_handlerOK.py` — 10 added / 5 removed, and the shape is exactly the
  mechanism the analyzer rule names:

```
-        if data is not None and data.empty or typet == 6:          # fused test, wrong polarity
-            default_dataframe = data[[… 11 columns …]]
+        if data is not None and not data.empty:
+            if typet == 6:
+                default_dataframe = data[[… 11 columns …]]
+            else:
+                default_dataframe = data[[… 7 columns …]]
```

  plus `end_time = int(end[0:8] + (end[8:12] or '1530'))` landing in its own branch instead of one
  copy plus a stray `"""1530"""` expression statement.


## H. Comment-only three-element completion, landed last and proven inert

Two of the 13 landed rules were missing part of the mandated 识别条件 / 归约方式 / AST 映射 prose
(`[R64-D4-B]` had no AST 映射 paragraph; the analyzer `chain.pop()` rule had its predicate in code
but no written 归约方式 / AST 映射). Two specs add exactly that text and nothing else:
`specs/r64doc_region_ast_generator.py.json` (1 edit, +4 lines),
`specs/r64doc_region_analyzer.py.json` (1 edit, +10 lines).

**Comment-only proof** (`logs/docproof64.py`, line-level `difflib.SequenceMatcher` of
`pre_doc/` == the `full2` landed bytes vs `mirr_docfinal`, `\r\n` kept as part of each line):

```
== region_ast_generator.py   pre_doc 3 103 160 sha c6c6a7dd69ab  -> docfinal 3 103 668 sha c9099bb0fc35
   opcodes: insert_blocks=1 delete_blocks=0 replace_blocks=0 inserted_lines=4
   inserted non-comment lines: 0            COMMENT-ONLY-ADDITION = True
== region_analyzer.py        pre_doc 1 724 219 sha 9b5cae3ce5a9  -> docfinal 1 725 369 sha 24a88392ee61
   opcodes: insert_blocks=1 delete_blocks=0 replace_blocks=0 inserted_lines=10
   inserted non-comment lines: 0            COMMENT-ONLY-ADDITION = True
ALL COMMENT ONLY = True      (BOM state unchanged on both, bare LF 0 on both)
```

Why not `ast.dump`: parsing a 3 MB source did not finish inside the 300 s command budget
(background task `bchjid1jr`, killed after the mirror had already been built). The line-level
proof is the stronger statement for this claim anyway — a comment can only change the AST by
altering a token line, and the diff shows zero token lines touched (no delete, no replace).

**Landing + post-landing gates** (serial):

```
land63.py land --spec=r64doc_region_ast_generator.py.json --mirror=mirr_docfinal --apply
  -> replay == measured mirror bytes: OK (3 103 668)   applied 3 103 160 -> 3 103 668, CRLF 50 149, BOM=True
land63.py land --spec=r64doc_region_analyzer.py.json --mirror=mirr_docfinal --apply
  -> replay == measured mirror bytes: OK (1 725 369)   applied 1 724 219 -> 1 725 369, CRLF 27 635, BOM=False
py_compile both + ast.parse both       => OK
sha256 generator c9099bb0fc3527e5b552bdc590066cab2d103343f6edca3d6a1c97a74a79bc4a
sha256 analyzer  24a88392ee61f31f5882a4dedb7f1b62cc16533ebc4909152e67b9c3ea77d107
closeout64.py landproof mirr_docfinal  => 33 core files, same=33 diff=0
```

**Product inertness.** `h62.py run --arm=docfinal` over the 11-file sha blast radius
(`changed_full2.txt`) plus the 4 canary files: **15/15 rows have the same `sha` and the same `mism`
list as the `full2` dump** (`dump/c402_full2.jsonl`), Σmatched 627 == 627. Therefore the `*OK.py`
files written by G3 still describe the final bytes and no regeneration was needed; `pyc_index.json`
carries no core-hash field (entry schema: `path, size, function_count, decompile_status,
bytecode_match_rate, ok_py_generated, last_tested_round, status, matched_functions`), so its 402
rows stay valid as measured.

**Battery on the final bytes**: `logs/gate/G6_battery_docfinal.txt` — 19 items,
matched **61/68**, files fully clean **14**, "candidate columns worse-than-landed on 0 repro(s)",
i.e. identical to the pre-doc `full2` column (49 → 61 / 7 → 14).
