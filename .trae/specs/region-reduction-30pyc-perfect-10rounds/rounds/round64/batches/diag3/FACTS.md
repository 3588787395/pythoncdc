# FACTS.md — Round 64, diag3 (DIAGNOSE ONLY)

All numbers below were re-derived by me on the current landed bytes. Nothing is copied from the
Round 63 brief.

## 0. Landed bytes I measured against (verified before any measurement)

```
$ cd /f/Downloads/pythoncdc-main
$ sha256sum core/cfg/region_ast_generator.py core/cfg/region_analyzer.py
7ec41fa2f9cdd5d62c1aeea25e695d84a3c84b0de537937b2e867676fae95f0d *core/cfg/region_ast_generator.py
c694d2514eb2f2b21ccf3a7b58fb9cca6563acbb6c6712da24183f94479360b6 *core/cfg/region_analyzer.py
$ wc -c core/cfg/region_ast_generator.py core/cfg/region_analyzer.py
3086600 core/cfg/region_ast_generator.py      (BOM + pure CRLF)
1721959 core/cfg/region_analyzer.py      (no BOM + pure CRLF)
```
sha prefixes `7ec41fa2f9cdd5d62c1a` / `c694d2514eb2f2b21ccf` and both sizes MATCH the brief.

## 1. Targets (`D:/Temp/opencode/r64gate/diag3/my4.txt`)

```
F:/Downloads/pythoncdc-main/site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc
F:/Downloads/pythoncdc-main/site-packages/IQCommon/util/trade_info_utils.pyc
F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc
F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc
```

## 2. Baseline, landed arm — official ruler (`h62.py run --arm=landed`)

`dump/landed.jsonl`, console log `logs/landed_run.txt`.

| file | official matched/total | defect functions `[orig, decomp, jumpdiff, truediff]` |
|---|---|---|
| real_quote.pyc | **39/44** | `get_cache_l2_data` [337,335,2,313]; `get_cache_l2_data_by_one` [321,320,2,300]; `get_real_minute_kline` [253,254,3,197]; `get_tick_direction` [259,258,3,102]; `one_prod_to_ndarray` [605,607,5,424] |
| trade_info_utils.pyc | **38/40** | `get_trade_list` [339,323,14,148]; `trade_operation` [304,302,2,40] |
| order_api.pyc | **32/34** | `future_order` [101,92,2,36]; `option_order` [83,73,3,39] |
| \_\_\_init\_\_\_.pyc (risk_calculation) | **32/35** | `_on_publish_after_trading_end` [486,481,3,33]; `_save_testds_to_csv` [71,68,7,19]; `get_TradeMode_trades` [1839,1753,4,1620] |

Every tuple reproduces the Round 63 numbers exactly (cross-check passed).

## 3. Baseline, landed arm — STRICT ruler (`_r10_strict_check.strict_compare`)

Products from `build_landed/`, driven by `strict.py` (pair list `dump/pairs_landed.jsonl`),
report `logs/strict_landed.txt`.

| file | strict ok/functions | defects `[kind] detail` |
|---|---|---|
| real_quote.pyc | 40/45 | `get_cache_l2_data` [seq_len] 337→336; `get_cache_l2_data_by_one` [seq_diff] #18 `('<JUMP>','JUMP')` vs `('None','POP_TOP')`; `get_real_minute_kline` [seq_len] 253→256; `get_tick_direction` [seq_len] 259→260; `one_prod_to_ndarray` [seq_len] 606→608 |
| trade_info_utils.pyc | 36/41 | `get_trade_list` [seq_len] 345→329; `get_trade_status` [target_diff] #70 FOR_ITER; `get_trade_unit_info` [seq_len] 240→241; `set_trade_status` [target_diff] #113 JUMP; `trade_operation` [seq_len] 304→302 |
| order_api.pyc | 33/36 | `base_order` [target_diff] #136 POP_JUMP_IF_TRUE; `future_order` [seq_len] 101→93; `option_order` [seq_len] 83→74 |
| \_\_\_init\_\_\_.pyc | 33/37 | `_on_publish_after_trading_end` [seq_len] 488→481; `_on_set_positions` [seq_len] 297→298; `_save_testds_to_csv` [seq_len] 75→68; `get_TradeMode_trades` [seq_len] 1843→1753 |

**TOTAL STRICT = 142/159.** Note the two rulers disagree on the function *population*
(official 44/40/34/35 vs strict 45/41/36/37) and on counts (`one_prod_to_ndarray`
official orig=605 / strict orig=606; `_save_testds_to_csv` official 71 / strict 75).

## 4. Pinned-shape battery, landed arm (`D:/Temp/opencode/r64gate/shapes_r63.txt`, 11 pyc)

`dump/shapes_landed.jsonl`:

| shape pyc | matched/total | defects |
|---|---|---|
| round63_b1/r63_ft | 1/2 | `fund_transfer_case` [65,65,0,6] |
| round63_b1/r63_ft2 | 1/2 | `t2` [109,109,0,6] |
| round63_b1/r63_ft4 | 1/2 | `t4` [31,22,1,23] |
| round63_b2/probe_r63b2_cases | 6/9 | `c5_elif_nochain_try` [57,37,2,28]; `c6_elif_try_then_more` [50,50,1,15]; `c8_elif_chain_only` [31,33,1,15] |
| round63_b2/probe_r63b2_cases2 | 3/9 | `d1_elif_try` [57,37,2,28]; `d2_elif_notry` [44,45,1,28]; `d3_if_try` [57,37,2,28]; `d6_elif_try_two_chain_and` [57,37,2,28]; `d7_elif_try_assign` [61,39,1,26]; `d8_elif_try_chain_or_plain` [50,37,2,21] |
| round63_b2/repro_r63b2_tail_cmp_return | 1/2 | `case_elif_try_tail_return` [210,186,2,158] |
| round63_b3/r63b3_chained_value_ctx_prefix | 2/2 clean | — |
| round63_b4/r63b4_tern_in_elif_chain | 3/3 clean | — |
| round63_b5/r63b5_w1 | 1/2 | `init_connection` [42,41,0,25] |
| round63_fix1/r63b3_chainstore_prefix | 2/2 clean | — |
| round63_fix2/r63b4_cond_boolop_stmt_steal | 13/13 clean | — |

Battery fully-clean files on landed: **4/11**.

## 5. Candidate J2 — measured on my 4 files + the 11-shape battery

Spec `specs/cand_r64d3_j2.json` (single edit, anchor verified unique, CRLF+BOM-preserving
mirror build reported `1 edits, core/cfg/region_analyzer.py, BOM=False, nl=CRLF`).

| file | landed | j2 | verdict |
|---|---|---|---|
| real_quote.pyc | 39/44 | 39/44 | MOVED, no matched-count change. `get_real_minute_kline` truediff 197→194 (better), `get_tick_direction` [259,258,**3**,102]→[259,258,**1**,105], `one_prod_to_ndarray` [605,**607,5,424**]→[605,**606,7,421**] |
| trade_info_utils.pyc | 38/40 | 38/40 | `trade_operation` [304,302,**2**,40] → [304,302,**1**,40] (jumpdiff halved) |
| order_api.pyc | 32/34 | 32/34 | byte-identical products (SAME) |
| \_\_\_init\_\_\_.pyc | 32/35 | 32/35 | byte-identical products (SAME) |

`h62.py ab` → **TALLY SAME=2 IMPROVED=0 REGRESSION=0 MOVED=2 ERR=0**.
Strict ruler on j2 (`logs/strict_j2.txt`): **TOTAL STRICT OK = 142/159 — identical to landed**
(`trade_operation` still `[seq_len] 304→302`).
Shape battery on j2 (`dump/shapes_j2.jsonl`): 10 SAME, 1 MOVED, 0 REGRESSION, still 4/11 clean.

The one specimen-verified product change on trade_info_utils (`build_landed` vs `build_j2`) is
exactly one line — `write_info.append(items)` moves from 24 to 20 spaces of indent, i.e. out of
the `if items[0] in trade_id_list:` body and back to `for`-body level, which is what the original
line 324 is. `return True` is NOT moved (contrast J1, see ANALYSIS §3).

## 6. Exact replay commands

```
cd D:/Temp/opencode/r64gate/diag3
python -X utf8 h62.py run --arm=landed --list=my4.txt --out=dump/landed.jsonl
python -X utf8 mkpairs.py dump/landed.jsonl landed dump/pairs_landed.jsonl
python -X utf8 strict.py dump/pairs_landed.jsonl logs/strict_landed.txt
python -X utf8 h62.py run --arm=landed --list=D:/Temp/opencode/r64gate/shapes_r63.txt --out=dump/shapes_landed.jsonl

python -X utf8 mkspec_j2.py                                            # writes specs/cand_r64d3_j2.json
python -X utf8 h62.py build --spec=specs/cand_r64d3_j2.json --dst=j2
python -X utf8 h62.py run  --arm=j2 --list=my4.txt --out=dump/j2.jsonl
python -X utf8 h62.py ab   --a=dump/landed.jsonl --b=dump/j2.jsonl
python -X utf8 mkpairs.py dump/j2.jsonl j2 dump/pairs_j2.jsonl
python -X utf8 strict.py dump/pairs_j2.jsonl logs/strict_j2.txt
python -X utf8 h62.py run  --arm=j2 --list=D:/Temp/opencode/r64gate/shapes_r63.txt --out=dump/shapes_j2.jsonl
python -X utf8 h62.py ab   --a=dump/shapes_landed.jsonl --b=dump/shapes_j2.jsonl

# probes (each prints, i.e. each is proven to fire)
python -X utf8 align.py <pyc> build_landed/<OK.py> <func>
python -X utf8 disf.py  <pyc> <func> --start=A --end=B
python -X utf8 regdump.py <pyc> <func>
python -X utf8 probe_own.py <pyc> <func> 1000 918 656 726
python -X utf8 probe_cbb.py <pyc> trade_operation 874 654
python -X utf8 probe_diffarms.py <pyc> trade_operation   # landed vs mirr_j1 collected-set diff
# repro (NEGATIVE result, see NONE.md N3)
python -X utf8 h62.py run --arm=landed --list=my_repro.txt --out=dump/repro_landed_v5.jsonl
python -X utf8 h62.py run --arm=j2     --list=my_repro.txt --out=dump/repro_j2_v5.jsonl
python -X utf8 probe_cbb2.py <repro.pyc> probe_join     # region forest of the clone
python -X utf8 probe_be.py   <repro.pyc> probe_join     # back-edge max() keys
```

## 7. Repro attempts on D1 — measured, NEGATIVE (`test_repros/round64_diag3/r64d3_postif_join.py`)

| version | region over-claim present? | landed official | j2 official |
|---|---|---|---|
| v1-v3 | no (join block became `back_edge_block` and was pruned at 18291) | 2/2 | — |
| v4 | **yes**, `IfRegion@38 else_blocks=[200,212,254,266,308]` | 2/2 clean | 2/2 clean |
| v5 | **yes**, isomorphic to `trade_operation` (see ANALYSIS §6) | 2/2 clean | 2/2 clean |

Back-edge `max()` keys measured (`logs/probe_be_tradeop.txt`, `logs/probe_be_repro.txt`):
real `738 → (1,22,738)` vs join `1000 → (1,6,1000)`; v3 repro `50 → (1,6,50)` tied with join
`254 → (1,6,254)` → join block won the start_offset tiebreak and was therefore pruned by
`region_analyzer.py:18291` before the region was built; v4/v5 `50 → (1,18,50)` vs join
`(1,6,·)` → the over-claim survives to the region forest — but the product is still correct,
so the nesting-depth hypothesis tested by v5 is falsified as well. Conclusion in
`NONE.md` N3: the `not merge` conjunct at `region_analyzer.py:26569` is necessary but not
sufficient for the visible `trade_operation` symptom; the discriminating step lives in
`region_ast_generator.py`.
