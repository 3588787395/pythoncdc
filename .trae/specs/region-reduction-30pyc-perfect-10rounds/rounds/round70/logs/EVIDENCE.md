# Round 70 — EVIDENCE（原始读数索引）

全部读数由中心在 `D:/Temp/opencode/r70gate/center` 镜像上独立重跑，不采信诊断代理自报。
仪判工具：`h62.py`（官方尺 + 产物 sha）、`sstrict67.py`（严格尺）、`closeout69.py`（82 项电池）、
`scripts/pyc_verify.py`（mandated ruler，pylingual `compare_pyc`）、`pyc_batch_verify.py`（402 批量）。

## A. 基线（landing 前，arm=landed = R69 落地字节）

- 10 支合集 `dump/landed10_r70.jsonl`：trade_live_broker 109/119、quote 72/81、real_quote 40/44、
  klinedata 43/45、order_api 32/34、risk_calculation 33/35、fileio_utils 12/14、
  trade_info_utils 39/40、api_base 24/25、realtime_event_source 11/12
  —— 与 R69 出货读数逐支相同（Σ 415/449，gap 34）。
- 金丝雀 `dump/landed_canary_r70.jsonl`：quotation `4d41187e356544e0` 143/143、
  market_time `af77224b34b203c4` 10/10、datetime_func `e711b8ea86d49a15` 26/26、
  datetime_func `9d09af09249da177` 25/25 —— 与 R69 归档 sha 逐字节相同。
- 严格尺 `dump/strict_landed_r70.json`：**436/488、缺陷 52**（= R69 出货值）。
- 索引快照 `dump/index_before70.json`（HEAD pyc_index.json）。

## B. 四候选中心五连复测（landing 前）

| 臂 | 10 支合集 | 金丝雀 | 82 项电池 | 严格尺 | 合成 |
|---|---|---|---|---|---|
| r70c1（diag1 exc） | IMPROVED=1（trade_live_broker 109→111/119）MOVED=1（realtime |Δ| 11→10）REG=0 | SAME×4 | worse=0 | 438/488 缺陷 50、FIXED=2、NEW=0 | r70_exc_r57e 1/2→**2/2** |
| r70c2（diag2 af） | IMPROVED=1（quote 72→73/81）**REGRESSION=1（risk 33→32/35）** | SAME×4 | — | — | — |
| r70c3（diag3 25b） | IMPROVED=1（trade_info 39→**40/40**）REG=0 | SAME×4 | worse=0 | 436/488 缺陷 52（同函数换 kind #94） | witness 105→103（方向性改善） |
| r70c4（diag4 c3） | IMPROVED=1（fileio 12→**14/14**）MOVED=1（trade_info 产物文本 break 缩进）REG=0 | SAME×4 | worse=0 | 439/488 缺陷 49、FIXED=3、NEW=0 | witness 1/2→**2/2** |

- c2 拆臂：`dump/r70c2a_mini.jsonl`（analyzer T1 单上：get_price 230/**251** 变差 +
  risk 33→**32/35** 回归）、`dump/r70c2g_mini.jsonl`（generator T3 单上：双支惰性）
  ⇒ ADR-1 整件回退。
- c4 副作用核查：trade_info 产物 diff 仅 `break` 缩进一处（计数全等）；
  blast 四支文本移位归因 `dump/b4_head.jsonl` vs `dump/b4_m70.jsonl`（官方计数全等、
  双臂 fully matched、head run-to-run 确定性验证 `dump/h1a.jsonl`==`dump/h1b.jsonl`）。

## C. 合并 m70 与镜像复测（landing 前）

- `mkfinal70.py m70`：3 份 spec、7 edits（region_analyzer），重放断言逐条「前序编辑后
  anchor 恰 1 次」全过；`mbuild70.py m70` → `mirr_m70`（1 754 683 → 1 763 461 B，+125 行）。
- 10 支合集 `dump/m70_10.jsonl`：**IMPROVED=3 SAME=6 MOVED=1 REGRESSION=0 ERR=0**、
  fully matched 0→2（fileio 14/14、trade_info 40/40）。
- 金丝雀 `dump/m70_canary.jsonl`：4 sha 与 landed 全同。
- 电池（82 项，m70 vs landed）：worse-than-landed=0。
- 严格尺 `dump/strict_m70_r70.json`：**441/488、缺陷 47**（FIXED 5、无新增缺陷函数）。
- 合成 `dump/synth_m70.jsonl`：r70_exc_r57e **2/2**、r70diag4_witness **2/2**、
  r70_witness_25b 4/5（105→103）、wret 对照 2/2。

## D. 落地

- `land70.py land --spec=specs/m70_region_analyzer.py.json --mirror=mirr_m70`：
  dry-run `replay == measured mirror bytes: OK (region_analyzer.py, 1763461 bytes)`。
- `--apply`：`applied: 1754683 -> 1763461 bytes, CRLF 28140, BOM=False, equals measured mirror=True`。
- 落地后 repo==mirror 逐字节相同；sha256 `20e2c9fc941aaa4f010c23d46425e498432978f14589b52dcda4bbb7f85ce4df`；
  `py_compile`+`ast.parse` OK。
- `landproof mirr_m70`：33 core 文件 **same=33 diff=0**（`logs/gate/Land70_landproof_r70.txt`）。

## E. 门禁 G0–G8（landing 后，`logs/gate/`）

- G0：三支 ast+py_compile OK；跨层模式 landed=2/1/0 → merged=2/1/0，new=0；PASS。
- G1：`G1_targets_r70.txt`（IMPROVED=3 SAME=6 MOVED=1 REG=0 ERR=0、cleared=2）。
- G2：`G2_canary_r70.txt`（SAME=4/4）+ `G2_strict_canary_{head,m70}_r70.txt`
  （两臂均 209/211 缺陷 2）。
- G3：`G3_batch_r70.txt`（**402 verified / 0 failed**、ok 394、partial 8、Traceback 0、FAIL 0）
  + `G3v_pycverify_r70.json`（mandated ruler：6498/6623 = **98.11%**、346 success /
  56 failure / 0 error；分片 8×`rep*.json` 在 `logs/dump/`）。
- G4：`G4_stats_r70.txt`（**5746/5717/99.50%**）。
- G4′：`G4p_strict_after_r70.txt`（436 → 441/488、缺陷 52 → 47）。
- G5：`G5_index_audit_r70.txt`（added/removed 0、round-stamp-only 399、**substantive=3 全改善**、
  matched delta +5）。
- G5′：`G5p_blast_r70.txt`（changed=8 identical=394 unresolved=0 REGRESSED=0）。
- G6：`G6_battery_cands_r70.txt` + `G6_battery_ext_r70.txt`（worse=0 两表）。
- G7：`G7_witness_repro70.txt`（82 项 head vs m70，worse=0）。
- G8：`G8_artifacts_r70.txt`（402 OK.py 在位、py_compile bad=0、Traceback 0、PASS）。

## F. 落地字节与索引指纹

- `core/cfg/region_analyzer.py`：1 763 461 B、sha256 `20e2c9fc941aaa4f…`、无 BOM、
  CRLF 28 140、裸 LF 0、numstat +125/−0。
- `core/cfg/region_ast_generator.py`：3 199 517 B、sha256 `240ecbaea36eeb70…` 不变。
- `core/cfg/comprehension_generator.py`：108 192 B、sha256 `be5490c1118c7199fe0a…` 不变。
- `pyc_index.json`：402 条、substantive 3（见 G5）。

## G. mandated ruler 单支读数（flagship 双尺验证）

- `pyc_verify.py single fileio_utils.pyc`：**success 15/15 = 100.00%**。
- `pyc_verify.py single trade_info_utils.pyc`：failure 36/41 = 87.80%
  （官方尺 40/40 与该尺的分歧按 §6 登记，旗舰不取该支）。
