# Round 71 · EVIDENCE（原始读数索引）

全部读数由中心在 `D:/Temp/opencode/r71gate/center` 独立重跑，不采信子代理自报数字。
判读工具：`h62.py`（官方尺 + 产物 sha）、`sstrict67.py`（严格尺）、`closeout69.py`（82 项电池）、
`scripts/pyc_verify.py`（mandated ruler，pylingual `compare_pyc`）、`pyc_batch_verify.py`（402 批量）、
`gates71a.py` / `gates71a_fix.py`（G0–G4′）、`gates71b.py`（G5′–G8、landproof）。

## A. 基线（landing 前，arm=landed = R70 落地字节）

- 56 支官方靶 `dump/landed56_r71.jsonl`（08:23 写出）：合计 **1957/1986、Σ|Δ|=186**、
  fully matched **48/56**；`dump/landed_canary_r71.jsonl`：quotation `4d41187e356544e0` 143/143、
  market_time `af77224b34b203c4`、IQCommon datetime_func `e711b8ea86d49a15`、
  IQData datetime_func `9d09af09249da177` — 与 R70 归档 sha 逐字节相同。
- 严格靶 `dump/strict_landed_r71.json`（div48）：**1776/1819、缺陷 43、target_diff 20**。
- mandated ruler 基线 = R70 归档 `rounds/round70/logs/gate/G3v_pycverify_r70.json`：
  **6498/6623 = 98.11%**、success 346 / failure 56、compile_error 0。
- 索引快照 `dump/index_before71.json`（`git show HEAD:pyc_index.json`，R70 出货态
  5717/5746、ok 394、partial 8、failed 0）。

## B. 只读诊断与三件候选（子代理产物 + 中心判决）

- diag1 `FACTS.md`：102 个 cf 单元全族聚类（F-ABSORB 68 / F-PAD 17 / F-META 5 / F-OTHER 4 /
  F-POLARITY 3 / F-EXCTABLE 2 / F-TERNARY 2 / F-ASSERT 1），根因到行
  （ra-gen `:22445-22450` F-THENOVER guard、`:24173/:26152/:26587/:26615/:27010` F-EXCTABLE、
  ra `:15259-15261/:15303/:15310` F-ASSERT）；synth 14/30 支可复现。
  用户线索「多数是嵌套 try-except」实测**部分否定**：主族 F-THENOVER 与 try 无关。
- fix1 `specs/R71-exception_exit.json`（generator 1 edit +62）→ 中心 `dump/c1_verdict.md`：
  56 靶 SAME=47/MOVED=9/REG=0、mandated 失败 26→19、电池 worse=0、
  严格 cf1 772/792 缺陷 20 无新增、synth `exc_A` 4/5→**5/5 success** ⇒ **采纳**。
- fix2 `specs/r71f2_full.json`（generator 2 edits）：56 靶 mandated +6、battery 0、
  strict ok 2164→2170、synth t01/t02/t22 **3/3 绿**、quotation 官方 143/143 维持 ⇒ **采纳**。
- fix3 `specs/R71-exctable.json` + `R71-exctable-analyzer.json` + `R71-assert.json`
  + `R71-analyzer-merged.json`：`fly_api/base` mandated **63/63 + 严格 63/63**（官方 h62 41/41 本已全等）、
  `IQData/entry` mandated **5/5**、
  22 靶 REG=0、金丝雀 sha 全同、battery 0、strict NEW=0；known-unfixed 2 条如实留档
  （ra `:14865` 重复 AssertRegion、孤儿 else 尾语句）⇒ **采纳**。

## C. 合并 m71 与镜像复测（landing 前，`dump/m71_verdict.md`，七项全 PASS ⇒ GO）

- 前置自检：`R71-analyzer-merged` ≡ `exctable-analyzer` + `assert` 顺序套用，LF 归一逐字节相等。
- `mkfinal71 m71`：generator **5 edits / +137**（exception_exit×1、r71f2_full×2、exctable×2）、
  analyzer **5 edits / +80**（analyzer-merged×5），链式锚点各恰出现 1 次。
- `mbuild71 m71` → `mirr_m71`：generator 3199517→**3210453 B**（BOM 保留）、
  analyzer 1763461→**1769596 B**（无 BOM），行尾统一、净行数与 spec 一致。
- a) 56 靶 `dump/m71_56.jsonl`：**SAME=38 IMPROVED=0 REGRESSION=0 MOVED=18 ERR=0**，
  fully matched 48→48（18 个 MOVED 全为 `gained=[] lost=[]`：缺陷集合不变、仅产物文本变）。
- b) 金丝雀 `dump/m71_canary.jsonl`：3 支 sha SAME，quotation 重钉 `3eb76e512df9ab1e`、
  官方 **143/143**、mandated **151/153 → 152/153**（`get_trend` 转绿，failure 集
  `{change_his_to_forward}`，不新增）。
- c) 电池 82 项 `dump/m71_battery.txt`：`candidate columns worse-than-landed on 0 repro(s)`。
- d) 严格 div48 `dump/strict_m71_r71.json`：**1776→1780/1819、缺陷 43→39、target_diff 20→17**，
  `NEW defect functions=0 / NEW target_diff=0 / FIXED=4`（wizard_quant_api.init_stock_pool_filter、
  fly_api/base.OverNightOrder.__init__、quotation.get_trend、load_daily.filter_abnormal_data）。
- e) mandated（18 支 sha 变化文件）`dump/m71_pv.txt`：失败单元 **45 → 28，net −17、
  fixed=17、NEW=0**；9 支转全绿。
- f) 合成咬合 `dump/m71_synth.txt`：**10/10 PASS**（6 正向 success + 4 负向 sha 同 landed）。
- g) 叠加一致性 `dump/m71_union.txt`：三候选各自修绿的 (pyc,函数) 并集 **17 单元，
  m71 上 17 仍绿 / LOST=0 / 未测=0**，各视角 NEW failing units=0。

## D. 落地

- `land71.py land --apply` ×2（generator、analyzer），`logs/Land71_replay_r71.txt`：
  `replay==worktree: True`（analyzer 1769617 B、generator 3210453 B，BOM 一致）。
- 落地字节：`region_analyzer.py` 1 763 461 → **1 769 617 B**（+80 行、sha `20e2c9fc941aaa4f` →
  `8ca47f7d6b9244cf`、无 BOM、CRLF 28 220、裸 LF 0）；
  `region_ast_generator.py` 3 199 517 → **3 210 453 B**（+137 行、sha `240ecbaea36eeb70` →
  `6203253987adedcf`、BOM 保留、CRLF 51 505、裸 LF 0）；`comprehension_generator.py` 未改。
- 落地前修正一条注释：`[R71-assert]` 注释字面含被禁跨层模式串（G0 regex 计入注释），
  改写为「区域入口属于它层块集」型表述后 repo / `mirr_m71` / 合并 spec / `R71-assert.json`
  四处逐字节同步（sha `8ca47f7d6b9244cf`），模式计数 2/1/0 → **new=0**；
  `Land71_landproof_r71.txt`：**33 core 文件 same=33 diff=0**。

## E. 门禁 G0–G8（landing 后，`logs/gate/`）

- G0 `G0_syntax_form_r71.txt`：三支 ast+py_compile OK；跨层模式 landed=2/1/0 = merged=2/1/0，
  **new=0** ⇒ PASS。
- G1 `G1_targets_r71.txt`（56 支官方靶，全路径键重算）：
  **SAME=38 MOVED=18 IMPROVED=0 REGRESSION=0 ERR=0**、fully matched 48→48。
  （首版用 `basename@parent` 键，`exception.pyc@utils`、`api_base.pyc@api` 撞键丢 2 行，
  由 `gates71a_fix.py` 以全路径键重算，仅 G1/G4′ 两个文件受影响。）
- G2 `G2_canary_r71.txt` + `G2_canary_pin_r71.txt`：4 支产物 sha 与 pin 全中
  （quotation 为本轮新 pin `3eb76e512df9ab1e`）⇒ PASS；
  `G2_quotation_pycverify_r71.txt`：quotation **status=failure units=152/153**、
  唯一 failure = `change_his_to_forward`（较基线少 `get_trend`）。
- G3 `G3_batch_r71.txt/.err`：`batch --index pyc_index.json --all --round 71`
  **402 verified / 0 failed**、ok 394、partial 8、failed 0、Traceback 0、FAIL 0。
- G3v `G3v_pycverify_r71.json`（mandated ruler，8 分片 `logs/dump/rep0-7.json` 合并）
  **6515/6623 = 98.37%**（R70 6498/6623 = 98.11%，**+17 单元**）：
  success **355**（+9）、failure **47**（−9）、compile_error 0、error 0；
  逐文件 `G3v_delta_r71.txt`：**转绿 9 支、转红 0 支**。
- G4 `G4_stats_r71.txt`：`total 402 / verified 402 / ok 394 / partial 8 / failed 0`、
  **5717/5746 = 99.50%**（与 R70 持平，官方计数本轮无变动）。
- G4′ `G4p_strict_after_r71.txt`（div48，全路径键重算）：
  **ok 1776 → 1780/1819、缺陷 43 → 39、target_diff 20 → 17**、
  TALLY SAME=44 IMPROVED=4 REGRESSION=0、**NEW=0 / FIXED=4 文件**。
  （首版同因撞键丢 1 行 31 函数，读数 1745→1749，已重算更正。）
- G5 `G5_index_audit_r71.txt`：entries 402→402、added/removed 0、
  key-shape diff 0、**round-stamp-only=402 / substantive=0**、matched 5717→5717 delta 0
  （官方计数本轮未变，符合预期）。
- G5′ `G5p_blast_r71.txt` + `blast71_expected.json`：出货产物变更 **18 支**、
  identical=384、**unresolved=0**；每支附官方读数与 mandated 状态迁移
  （9 支 failure→success、其余单位只减不增）⇒ REGRESSED=0。
- G6 `G6_battery_ext_r71.txt`：真基线臂 `prev`（HEAD blob 还原的 `mirr_prev`，R70 字节，
  `mkmirr_prev71.py` 断言 size/sha = R70 记录值）vs `m71`，82 项
  **candidate columns worse-than-landed on 0 repro(s)**。
  说明：landing 后 `arm=landed` 已解析为 R71 字节，与 `m71` 同源，故 G6 一律改用 `prev` 臂。
- G7 `G7_witness_repro71.txt`：逐项 prev vs m71 判定 **SAME=82、REGRESSED=0、NO-RECORD=0** ⇒ PASS。
- G8 `G8_artifacts_r71.txt`：402/402 `*OK.py` 在位、py_compile bad=0、Traceback 0、FAIL-line 0 ⇒ PASS。

## F. 落地字节与索引指标

- `core/cfg/region_ast_generator.py` **3 210 453 B** sha256 `6203253987adedcf7bd0…`、BOM=True、
  CRLF 51 505、裸 LF 0；`git diff --numstat` **+140 / −3**（净 +137）。
- `core/cfg/region_analyzer.py` **1 769 617 B** sha256 `8ca47f7d6b9244cfa784…`、BOM=False、
  CRLF 28 220、裸 LF 0；`git diff --numstat` **+83 / −3**（净 +80）。
- `core/cfg/comprehension_generator.py` 108 192 B sha256 `be5490c1118c7199fe0a…` 未改。
- `pyc_index.json`：402 条，仅 round stamp 变化（substantive 0）。

## G. mandated ruler 转绿 9 支（`G3v_delta_r71.txt`，全部 failure → success）

`IQCommon/exception`（33/34→34/34）、`IQData/entry`（4/5→5/5）、`IQData/utils/exception`、
`fly_api/base`（61/63→**63/63**）、`plugin_system_accounts/__init__`（5/6→6/6）、
`benchmark_account`（19/20→20/20）、`stock_account`（24/25→25/25）、
`plugin_system_risk_calculation/function`（14/15→15/15）、`IQEngine/utils/exception`。
mandate「本轮至少一支修到完全 OK」由 **9 支**达成（其中 `fly_api/base` 官方与 mandated 双尺全清）。

## H. 金丝雀与 quotation 重钉（停止条件复核）

- 三支金丝雀 sha 与 R69/R70 pin 逐字节相同，官方 143/143（quotation）、10/10、26/26、25/25 维持。
- quotation 唯一允许的变更：产物 sha `4d41187e356544e0` → `3eb76e512df9ab1e`，
  官方读数不变 143/143，mandated 151/153 → **152/153**（`get_trend` 转绿、无新增 failure），
  严格 `get_trend [target_diff]` 修绿 ⇒ 属净改善，按 ADR-1 允许并重钉 pin。
