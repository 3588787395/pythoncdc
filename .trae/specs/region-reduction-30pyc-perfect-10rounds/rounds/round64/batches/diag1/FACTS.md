# Round 64 · batch diag1 · FACTS

All numbers below are produced by the private harness `D:/Temp/opencode/r64gate/diag1/h62.py`
(`ROOT` = that directory, `REPO` = `F:/Downloads/pythoncdc-main`), which drives
`scripts/pyc_batch_verify.bytecode_diff` — the **official** matcher — per file.
Nothing here was measured with a hand-rolled comparison.

## 0. Landed bytes at measurement time

| file | bytes | sha256[0:12] | hygiene |
|---|---|---|---|
| `core/cfg/region_ast_generator.py` | 3 086 600 | `7ec41fa2f9cd` | BOM + pure CRLF |
| `core/cfg/region_analyzer.py` | 1 721 959 | `c694d2514eb2` | no BOM + pure CRLF |

**Hygiene churn observed during this session.** At ~07:53 the worktree copy of
`region_ast_generator.py` was found reflowed to **pure LF / 3 036 663 B / `5ffe31558df4`**,
and at 08:03 it was back to CRLF / 3 086 600 B / `7ec41fa2f9cd`. The two texts are
**byte-identical after `\r\n` -> `\n` normalisation** (verified with a line-list diff:
49 938 lines, equal), so every arm in this file is comparable. The reflow does break two
builders that hard-code "every `\n` is part of a `\r\n`":
`mbuild.py:72-73` and `h62.py:69-71` (both patched in place to a base-style-aware,
line-count-exact assertion; `mbuild.py` is shared, `h62.py` is diag1-private).

## 1. Arms

| arm | spec | file(s) patched | content |
|---|---|---|---|
| `landed` | — | — | worktree core, unchanged |
| `c1` | `specs/cand_r64b1_sibdispatch.json` | generator (1 edit) | sibling merge-entry dispatch |
| `c2` | `specs/cand_r64b1_fvconv.json` | generator (5 edits) | FORMAT_VALUE conversion back-fill (f-string layer) |
| `c3` | `specs/cand_r64b1_both.json` | generator (6 edits) | **c1 + c2 merged into one spec** (mbuild refuses two specs for one file: "merge them first") |
| `c3k` | `cand_r64b1_both.json` + `specs/cand_r64d1b_kbin.json` | generator (6) + **analyzer** (1) | c3 + the diag1 Job-2 fix |

Mirror hashes (`diag1/mirr_<arm>/core/cfg/…`):

| arm | region_ast_generator.py | region_analyzer.py |
|---|---|---|
| `mirr_c1` | 3 089 580 `ab52c65347d2` | 1 721 959 `c694d2514eb2` |
| `mirr_c2` | 3 089 851 `e757f4c8d5dd` | 1 721 959 `c694d2514eb2` |
| `mirr_c3` | 3 042 815 `cdd723980fa5` (LF base) | 1 721 959 `c694d2514eb2` |
| `mirr_c3k` | 3 092 831 `462c3a3856d6` (CRLF base) | 1 724 219 `9b5cae3ce5a9` |

`mirr_c3` vs `mirr_c3k`: generator text **identical** modulo line endings, analyzer differs
by exactly the one Job-2 edit. Verified.

## 2. Job 1 — is c3 additive?

**Yes: fully additive, no anchor collision, no semantic interference.**
All 6 anchors (c1's 1 + c2's 5) are unique in the landed text and were applied by
`h62.py build --spec=specs/cand_r64b1_both.json --dst=c3` (+79 lines, BOM preserved).

| arm | my4 total | trade_live_broker | fly/data/quote | quote_handler | realtime_event_source | battery | canary |
|---|---|---|---|---|---|---|---|
| landed | 240/269 | 104/119 | 70/81 | 55/57 | 11/12 | 34/48 | 204/204 |
| c1 | 241/269 | 104/119 | 70/81 | **56/57** | 11/12 | 34/48 | 204/204 |
| c2 | 241/269 | **105/119** | 70/81 | 55/57 | 11/12 | **36/48** | 204/204 |
| c3 | **242/269** | **105/119** | 70/81 | **56/57** | 11/12 | **36/48** | 204/204 |
| c3k | **243/269** | 105/119 | 70/81 | **57/57 OK** | 11/12 | 36/48 | 204/204 |

`h62.py ab --a=dump/landed.jsonl --b=dump/c3.jsonl` ->
`IMPROVED trade_live_broker 104/119 -> 105/119`, `IMPROVED quote_handler 55/57 -> 56/57`,
`SAME=2 REGRESSION=0 MOVED=0 ERR=0`.
`ab landed vs c3k` -> `IMPROVED trade 104 -> 105`, `IMPROVED quote_handler 55/57 -> 57/57`,
`SAME=2 REGRESSION=0`, **files fully matched: a=0 b=1**.
`ab c3 vs c3k` -> `IMPROVED quote_handler 56/57 -> 57/57`, `SAME=3 REGRESSION=0`.
`ab c3_shapes vs c3k_shapes` -> `SAME=11 REGRESSION=0`. `ab c3_canary vs c3k_canary` -> `SAME=4`.

## 3. Per-target defect tuples (official `bytecode_diff`, `[orig, decomp, jump_diffs, true_diffs]`)

### landed (28 mismatching functions over 4 files) — `dump/landed.jsonl`
`trade_live_broker.pyc` 104/119:
`_process_cancel_order [293,292,16,43]`, `_process_order [454,396,9,349]`,
`_sync_worker [349,347,0,296]`, `_trade_status_handle [114,112,0,107]`,
`after_trading_cancel_order [155,155,3,122]`, `etf_basket_order [693,693,11,216]`,
`etf_purchase_redemption [377,355,2,100]`, `fund_transfer [123,123,0,6]`,
`get_all_orders [79,78,2,24]`, `get_etf_stock_info [144,117,1,139]`,
`get_max_amount [201,213,2,18]`, `ipo_stocks_order [1075,1076,10,437]`,
`market_fund_transfer [94,77,1,41]`, `on_order_response [445,444,6,57]`,
`on_trade_response [392,391,6,57]`
`fly/data/quote.pyc` 70/81:
`build_current_period_df [115,108,5,12]`, `check_frequency [121,120,1,21]`,
`check_limit [330,311,2,248]`, `get_individual_data [312,311,1,156]`,
`get_price [230,188,0,227]`, `get_real_from_zeromq [703,678,0,660]`,
`initImagedata [243,225,0,190]`, `load_bars_from_hundsun [477,470,0,464]`,
`load_get_price [171,136,1,167]`, `run_individual_transform [362,321,2,263]`,
`run_tick_socket [306,307,2,228]`
`quote_handler.pyc` 55/57: `get_kline_binary [129,128,3,58]`, `get_kline_local [760,682,12,547]`
`realtime_event_source.pyc` 11/12: `clock_worker [1275,1286,10,481]` (OVERSHOOT +11)

### what each arm moves (deltas only; everything else is byte-identical to landed)
| arm | cleared | remaining on the 4 targets |
|---|---|---|
| c1 | `quote_handler::get_kline_local [760,682,12,547]` | `get_kline_binary [129,128,3,58]` |
| c2 | `trade_live_broker::fund_transfer [123,123,0,6]` (+ battery `r63_ft`, `r63_ft2`) | 13 other trade defects, all quote.pyc, 2 qh, clock_worker |
| c3 | both of the above | `get_kline_binary [129,128,3,58]` (qh), 13 (trade), 11 (quote), 1 (res) |
| c3k | **+ `get_kline_binary` → `quote_handler.pyc` = 57/57, fully OK** | 13 (trade), 11 (quote), 1 (res) |

`quote_handler.pyc` on c3k has an **empty `mism` list** — 57/57.

## 4. Battery — 11 pinned R63 repros (`D:/Temp/opencode/r64gate/shapes_r63.txt`), 48 pinned function checks

| shape | landed | c1 | c2 | c3 | c3k |
|---|---|---|---|---|---|
| probe_r63b2_cases | 6/9 | 6/9 | 6/9 | 6/9 | 6/9 |
| probe_r63b2_cases2 | 3/9 | 3/9 | 3/9 | 3/9 | 3/9 |
| r63_ft | 1/2 | 1/2 | **2/2** | **2/2** | **2/2** |
| r63_ft2 | 1/2 | 1/2 | **2/2** | **2/2** | **2/2** |
| r63_ft4 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 |
| r63b3_chained_value_ctx_prefix | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| r63b3_chainstore_prefix | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| r63b4_cond_boolop_stmt_steal | 13/13 | 13/13 | 13/13 | 13/13 | 13/13 |
| r63b4_tern_in_elif_chain | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| r63b5_w1 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 |
| repro_r63b2_tail_cmp_return | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 |
| **TOTAL** | **34/48** | **34/48** | **36/48** | **36/48** | **36/48** |
| files fully matched | 4 | 4 | 6 | 6 | 6 |

landed defect rows (unchanged on c3k except `r63_ft`/`r63_ft2`):
`c5_elif_nochain_try [57,37,2,28]`, `c6_elif_try_then_more [50,50,1,15]`,
`c8_elif_chain_only [31,33,1,15]`, `d1_elif_try [57,37,2,28]`, `d2_elif_notry [44,45,1,28]`,
`d3_if_try [57,37,2,28]`, `d6_elif_try_two_chain_and [57,37,2,28]`,
`d7_elif_try_assign [61,39,1,26]`, `d8_elif_try_chain_or_plain [50,37,2,21]`,
`fund_transfer_case [65,65,0,6]` (c2 clears), `t2 [109,109,0,6]` (c2 clears),
`t4 [31,22,1,23]`, `init_connection [42,41,0,25]`,
`case_elif_try_tail_return [210,186,2,158]`.

## 5. Canary (`canary.txt`, 4 boolop/f-string-heavy files, 204 functions)

| arm | quotation | market_time | IQCommon/util/datetime_func | IQData/utils/datetime_func | total |
|---|---|---|---|---|---|
| landed | 143/143 | 10/10 | 26/26 | 25/25 | 204/204 |
| c1 | 143/143 | 10/10 | 26/26 | 25/25 | 204/204 |
| c2 | 143/143 | 10/10 | 26/26 | 25/25 | 204/204 |
| c3 | 143/143 | 10/10 | 26/26 | 25/25 | 204/204 |
| c3k | 143/143 | 10/10 | 26/26 | 25/25 | 204/204 |

No canary file moved on any arm (`ab c3_canary vs c3k_canary` -> `SAME=4`).

## 6. Minimal repro (`test_repros/round64_diag1/r64d1b_closed_exit_prefix.py/.pyc`, CPython 3.11.7)

| arm | matched/total | tuple |
|---|---|---|
| landed | 1/2 | `kbin_repro [34, 29, 3, 15]` |
| c3 | 1/2 | `kbin_repro [34, 29, 3, 15]` |
| c3k | **2/2** | `[]` |

Landed emits `if data is not None and data.empty or c == 6:` and **loses the statement
`out = data[narrow]`**; c3k emits the nested `if/else` correctly.

## 8. Files written by this batch

* `D:/Temp/opencode/r64gate/diag1/specs/cand_r64d1b_kbin.json` — Job-2 candidate (1 analyzer edit, +35 lines)
* `D:/Temp/opencode/r64gate/diag1/specs/cand_r64b1_both.json` — unchanged (the pre-merged c1+c2 spec)
* `D:/Temp/opencode/r64gate/diag1/mk_kbin.py`, `probe_chain.py` — spec author + chain probe
* `D:/Temp/opencode/r64gate/diag1/h62.py` (lines 67-74) and `D:/Temp/opencode/r64gate/mbuild.py`
  (lines 71-74) — line-ending assertions made base-style-aware (needed since the worktree
  generator file reflows between CRLF and LF); `mbuild.py` is shared tooling, flagged here.
* `F:/Downloads/pythoncdc-main/test_repros/round64_diag1/r64d1b_closed_exit_prefix.{py,pyc}` — **reproduces** (landed/c3 defective, c3k clean)
* `F:/Downloads/pythoncdc-main/test_repros/round64_diag1/r64d1b_sibdispatch_attempt.{py,pyc}` + `NONE.md` — c1-family repro **attempted, did not reproduce**
* No file under `core/`, no `*OK.py`, no `pyc_index.json`, no git write.

## 7. Replayable commands

```bash
cd /d/Temp/opencode/r64gate/diag1
# (re)build arms -- NOTE: the two c1/c2 specs patch the SAME file, so mbuild refuses them
# together; c3 is the pre-merged 6-edit spec cand_r64b1_both.json.
python -X utf8 h62.py build --spec=specs/cand_r64b1_both.json --dst=c3
python -X utf8 ../mbuild.py c3k specs/cand_r64b1_both.json specs/cand_r64d1b_kbin.json
cp -r ../mirr_c3k ./mirr_c3k            # h62 resolves arms under diag1/mirr_<arm>

for L in my4.txt ../shapes_r63.txt canary.txt; do
  python -X utf8 h62.py run --arm=c3k --list=$L --out=dump/c3k_$(basename $L .txt).jsonl
done                                    # my4 -> dump/c3k.jsonl, shapes -> dump/c3k_shapes.jsonl
python -X utf8 h62.py ab --a=dump/c3.jsonl --b=dump/c3k.jsonl

# Job-2 diagnosis chain
python -X utf8 disf.py  F:/…/fly/data/quote_handler.pyc get_kline_binary --src=build_c3/fly__data__quote_handlerOK.py
python -X utf8 align.py F:/…/fly/data/quote_handler.pyc build_c3/fly__data__quote_handlerOK.py get_kline_binary
python -X utf8 regdump.py F:/…/fly/data/quote_handler.pyc get_kline_binary
python -X utf8 trace.py   F:/…/fly/data/quote_handler.pyc get_kline_binary 170,262,276,288,310,330,346
python -X utf8 probe_chain.py F:/…/fly/data/quote_handler.pyc get_kline_binary
python -X utf8 mk_kbin.py      # re-author specs/cand_r64d1b_kbin.json (+35 lines, anchor unique)

# repro
cd /f/Downloads/pythoncdc-main/test_repros/round64_diag1
python -X utf8 -c "import py_compile;py_compile.compile('r64d1b_closed_exit_prefix.py',cfile='r64d1b_closed_exit_prefix.pyc',doraise=True)"
cd /d/Temp/opencode/r64gate/diag1
for a in landed c3 c3k; do python -X utf8 h62.py run --arm=$a --list=repro1.txt --out=dump/repro1_$a.jsonl; done
```

Dumps: `dump/{landed,c1,c2,c3,c3k}.jsonl`, `dump/{shapes_landed,c1,c2,c3,c3k}_shapes.jsonl`,
`dump/{canary_landed,c1,c2,c3,c3k}_canary.jsonl`, `dump/repro1_{landed,c3,c3k}.jsonl`.
Logs: `logs/{disf_kbin,reg_kbin,trace_kbin,align_clockworker,allarms}.txt`.
