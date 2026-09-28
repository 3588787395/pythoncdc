# Round 74 · EVIDENCE（原始读数索引）

全部读数由中心在 `D:/Temp/opencode/r74gate/center` 独立重跑，不采信子代理自报数字。
判读工具：`h62.py`（官方尺 + 产物 sha）、`sstrict67.py`（严格尺）、`closeout69.py`（电池）、
`scripts/pyc_verify.py`（mandated 尺）、`scripts/pyc_batch_verify.py`（402 批量官方尺）、
`adr73.py`（候选 ADR-1 复测）、`gates74.py`（G0/G1/G2/G4′/G5/G6/G7/G5′/G8 + landproof）、
`g4g8replay74.py`（G4 统计 + 落地重放复核）、`g9run74.py`（G9 合成）、
`merge_g3v74.py`（8 分片合并 + delta）、`tryverdict_summary74.py`（try 定量判决汇总）。

## A. 基线（landing 前 = R73 落地字节，arm=prev）

- 起始 HEAD `cd1cd670`（其上 `6bb9716a` = R73 落地）；`mkmirr_prev74.py` 用 HEAD blob
  （LF→CRLF 还原）建 `mirr_prev`，size/sha 断言：generator **3214913 / `33e22ee451148af83545`**、
  analyzer **1778913 / `b9dcc727ea5918ea9013`**、comprehension **115583 / `b432a355809898525224`**。
- 官方 41 靶基线 `dump/off_landed41.jsonl` + 金丝 `dump/can_landed.jsonl` →
  `dump/prev_c.jsonl`（45 行，quotation 重复 1 行）；G1 TALLY 的 prev 列即此。
- 严格基线 `dump/strict_prev73.json`：**ok 1853 / functions 1929 / defects 76**
  （G4p 去重口径 ok 1704、缺陷 75）。
- mandated 基线 = R73 归档 `rounds/round73/logs/gate/G3v_pycverify_r73.json`
  （合并脚本读取路径已改指 round73）：**6540/6617 = 98.84%**、success 367 / failure 35。
- 官方基线（R73 归档）：**5717/5746 = 99.50%**、ok 394、partial 8、failed 0。
- 索引快照 `dump/index_before73.json`（402 条，字节级复制）。

## B. 四批与候选探针

- 家族地图 `dump/fam74_r74.json`（77 单元：F-ABSORB 67 OUT58/IN9、F-PAD 8、F-POLARITY 1、
  F-OTHER 1）、`dump/crosstab74.txt`、`dump/filecat74.json`（35 支）。
- try 判决 `dump/tryverdict73.txt` / `dump/firstdiv73.txt` / `dump/exctable_diff73.txt`
  （77 单元 / 76 可探）→ `logs/TRYVERDICT_r74.txt`（11/76 inside、65/76 outside）。
- fix1：`specs/abs1.json`、`specs/abs2_orphan_child_emit.json`、`specs/absj.json`、
  `FACTS.md`、`synth/`；fix2：`FACTS.md` + `specs/pad7_*.json`；
  fix3：`specs/try7_1..11.json`（`dump/` 内 off_/m35_/md_/can_/strict_ 逐臂读数）。

## C. 中心 ADR-1 独立复测（`adr73.py` 串行单跑，77 单元）

| 臂 | 产物 | 读数 | 判定 |
|---|---|---|---|
| absj | `dump/adr74_absj.json` | changed 5 WORSE=0 IMPROVED=5 | 通过 |
| absjt | `dump/adr74_absjt.json` | changed 10 **WORSE=1** `real_quote.get_tick_direction hunks_norm 2→3` | 拒收 |
| absj9 | `dump/adr74_absj9.json` | changed 10 **WORSE=1**（同上） | 拒收 |
| absj3 | `dump/adr74_absj3.json` | changed 7 **WORSE=0** IMPROVED=7 | **采纳** |

IMPROVED（absj3）：finance.get_financial_and_growth_factors / get_financial_statements_pit_mode、
local_finance.get_local_financial_factors、api_base.get_history_df、
real_quote.one_prod_to_ndarray / get_cache_l2_data_by_one、trade_live_broker.get_max_amount。

## D. 候选臂并列读数（absj3 = m74）

- 官方 41 靶 `dump/off_absj341.jsonl` vs `dump/off_landed41.jsonl` →
  **SAME=34 IMPROVED=2 MOVED=5 REGRESSION=0 ERR=0**、fully matched 36→36。
- 严格 `dump/strict_absj3.json`（45 行）：ok 1859 / defects 70（raw）。
- 电池 `closeout69 battery landed absj3` → worse-than-landed 0 repro。
- mandated focus9 `dump/md_absj3_focus9.json`：real_quote 41→43（2 CLEARED）、
  finance 29→31（2 CLEARED）、quote/trade_info_utils/flytools/email_utils/
  realtime_event_source/cgroup_utils/strategy 各不变、**NEW failure=0**。
- 拒收臂读数一并入档：`dump/off_absjt41.jsonl`（SAME=34 IMPROVED=3 REG=0）、
  `dump/strict_absjt.json`（defects 68 raw，NEW defect functions=0）、
  `dump/md_absjt_focus9.json`。

## E. 落地（`land74 --apply`，replay == measured mirror）

- `m74_region_ast_generator.py.json`（6 edits/+185，来源 `abs2t3.json`）
  与 `m74_region_analyzer.py.json`（1 edit/+34，来源 `abs1.json`）。
- 落地后字节：generator **3226993 B，sha256 `e54dd931e91e9f6aafea06239c7aba1483889c97e03a3285afa8560990c51d42`**；
  analyzer **1781244 B，sha256 `d6b11bcabf1a4256aa37a7ea013be5d4a93ac7cc19db1453498db614d3f55a48`**。
- `dump/G3_batch_r74.txt`：total 402 / verified 402 / ok 394 / partial 8 / failed 0 /
  matched 5720 / 5746 = **99.55%**。

## F. 门禁原始读数（logs/gate）

- `G0_syntax_form_r74.txt`：ast/py_compile OK ×3；raw 9→10、code-only 7→8、
  **sanctioned-try-guard=1 other=0**（新增行 `and region.entry in _ft3_rr.blocks`，
  上下文 TryExceptRegion，diff 证据在文件内）⇒ PASS。
- `G1_targets_r74.txt`：TALLY ERR=0 IMPROVED=2 MOVED=5 REGRESSION=0 SAME=37、
  fully matched prev=36 landed=36 ⇒ PASS。
- `G2_canary_pin_r74.txt`：4/4 pin、sha SAME=4/4；`G2_quotation_pycverify_r74.txt`：152/153。
- `G3v_pycverify_r74.json` + `G3v_delta_r74.txt`：**6540 → 6546/6617 = 98.93%**、
  turn green 1（local_finance 20/21→21/21）、turn red 0 ⇒ PASS。
- `G4_stats_r74.txt`：5720/5746 = 99.55% ⇒ PASS；`G4p_strict_after_r74.txt`：
  ok 1704→1710、缺陷 75→69、IMPROVED=4 REGRESSION=0 SAME=40 ⇒ PASS。
- `G5_index_audit_r74.txt`：402→402、round-stamp-only=400、substantive=2
  （improved=2 worsened=0 other=0：real_quote matched 40→42、trade_live_broker 111→112）⇒ PASS。
- `G5p_blast_r74.txt`：changed=7 unresolved=0 **REGRESSED=0**；
  `G6_battery_ext_r74.txt`：worse-than-landed 0；
  `G7_witness_repro73.txt`：IMPROVED=1 SAME=81 REGRESSED=0；
  `Land73_landproof_r74.txt`：33 core 文件 same=33 diff=0；
  `G8_artifacts_r74.txt`：402 products missing=0 py_compile bad=0 Traceback=0 FAIL-line=0；
  `G9_synth_r74.txt`：IMPROVED=1 REGRESSED=0 SAME=24 ⇒ PASS；
  `Land74_replay_r74.txt`：两文件 HEAD+spec == worktree **PASS**。

## G. 电池与真基线

`dump/batt_prev_landed74.txt`（prev = HEAD blob 还原 R73 字节 vs landed = R74 字节）：
candidate columns worse-than-landed **0 repro**；`dump/repro65_prev.jsonl` /
`dump/repro65_landed.jsonl` 为 G7 witness 两侧读数。

## H. 交接 R75（如实入档）

- `try7_10d` / `try7_9` 的收益与唯一回退 `real_quote.get_tick_direction hunks_norm 2→3`
  （`dump/adr74_absjt.json` / `adr74_absj9.json`）；
- fix2 `pad7_89` 官方 REGRESSION=1 + strict NEW=1，6 个未攻单元清单见 OUTCOME §6；
- fix3 缺 `FACTS.md` 与 `trym`；`trade_operation` target_diff #94；
- 最大残留 trade_live_broker 13 / quote 11 / trade_info_utils 5 / flytools 1 / email_utils 1。
