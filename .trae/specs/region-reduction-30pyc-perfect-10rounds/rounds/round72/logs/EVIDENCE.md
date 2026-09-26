# Round 72 · EVIDENCE（原始读数索引）

全部读数由中心在 `D:/Temp/opencode/r72gate/center` 独立重跑，不采信子代理自报数字。
判读工具：`h62.py`（官方尺 + 产物 sha）、`sstrict67.py`（严格尺）、`closeout69.py`（82 项电池）、
`scripts/pyc_verify.py`（mandated ruler，pylingual `compare_pyc`）、`pyc_batch_verify.py`（402 批量）、
`cand72.py`（候选 ADR-1 复测）、`gates72.py`（G0/G1/G2/G4′/G5/G6/G7/G5′/G8 + landproof）、
`merge_g3v71.py`（8 分片合并 + delta）、`replay72check.py`（落地重放独立复核）。

## A. 基线（landing 前 = R71 落地字节，arm=prev）

- 起始 HEAD `37dc4a01`（其上 `6c0a8f8c` = R71 落地）；`mkmirr_prev72.py` 用 HEAD blob
  （LF→CRLF 还原）建 `mirr_prev`，断言 size/sha = R71 记录值：generator 3210453/`6203253987adedcf7bd0`、
  analyzer 1769617/`8ca47f7d6b9244cfa784`、comprehension 108192/`be5490c1118c7199fe0a`
  （本轮 comprehension 为 worktree 已改项，mirror 持 HEAD 字节、断言 mir==HEAD bytes 成立）。
- 47 靶官方基线 `dump/prev_fail47_r72.jsonl`；金丝雀 `dump/prev_canary_r72.jsonl`；
  严格 div48 `dump/strict_prev72.json`：**ok 1780/1819、缺陷 39**（= R71 读数）。
- mandated 基线 = R71 归档 `rounds/round71/logs/gate/G3v_pycverify_r71.json`：
  **6515/6623 = 98.37%**、success 355 / failure 47。
- 索引快照 `dump/index_before72.json`（`git show HEAD:pyc_index.json`，出货态 5717/5746、
  ok 394、partial 8、failed 0）。

## B. 只读诊断与两件候选（子代理产物 + 中心判决）

- diag1 `FACTS.md`：108 单元族聚类（F-ABSORB 70 / F-PAD 14 / F-OTHER 12 / F-EXTRA 6 /
  F-POLARITY 3 / F-TERNARY 2 / F-EXCTABLE 1），A 组 58 单元 = 42/6/5/2/2/1；根因到行
  （ra `:20432/:23303/:26646/:15929`、ra-gen `:3199-3223/:22512/:17753/:15503/:185/:26482/:14865/:88-100/:46`
  、`comprehension_generator :520-521/:573`）；`synth/` 24 支（`verify_readings.txt` 11 支复现 +
  负对照 2 支 success + R71 老形状 5 支转绿）；`fam72.json` 真实判据重算。
  diag1 独立定位的 F-EXTRA 行与 fix2 完全同源（无分歧）；F-EXTRA 提案 = 直接采纳 fix2 的
  `prev_end` 记账不变式。
- fix1 `specs/fix1_comp_split.json`（3 edits / +79 行，`dump/fix1a_*.txt|jsonl`）：
  四支靶官方 72/72·64/64·60/60·16/16 逐项不变；mandated 11 失败 → **0**
  （future_position 79/83 → 83/83 等 4 支全绿）；金丝雀 SAME=4；电池 worse=0；
  严格 454/456·缺陷 2 → **455/456·缺陷 1**。
- fix2 `specs/broker_comp_return.json`（1 edit / +20 行，`dump/f2*.txt|jsonl`）：
  25 支官方 SAME=23 REG=0 MOVED=2；mandated broker **35/42 → 38/38 success**、
  trade_live_broker 114/129 → 114/128、其余 23 支字节相同；金丝雀 4 pin；电池 worse=0；
  两臂 strict ok=1186/1243 缺陷 57 完全一致。ADR-1 事故如实留档：第一版无条件
  `prev_end=len` 让 asset_mixin 官方 16/16 → 15/16（嵌套推导式被拆两条 Return），拒收后判据
  收紧为「本块 comp_indices 尾项」，恢复 16/16 且 sha 与 landed 相同。

## C. 中心 ADR-1 候选复测（`cand72.py`，f1 / f2 / 合并 m 三臂，全 PASS）

- 官方（29 支并集列表 all16+t_fix1+canary+head25）：f1 SAME=25 MOVED=4、f2 SAME=27 MOVED=2、
  m SAME=23 MOVED=6，**三臂 REGRESSION=0 ERR=0、fully matched 数不降**。
- mandated 移动文件逐支（`dump/pv_*.txt`）：
  - f1：asset_mixin 1→0、future_position 4→0、live_future_position 4→0、option_position 2→0；
  - f2：broker 7→0、trade_live_broker 15→14；
  - m：两集合并，**移动单元 −18、new-failing-units=0**，5 支转 success。
- 金丝雀 pin：三臂 quotation `3eb76e512df9ab1e`、market_time `af77224b34b203c4`、
  datetime_func `e711b8ea86d49a15` / `9d09af09249da177` 全中。
- 电池（m 臂）：`closeout69 battery landed m` → **worse-than-landed=0**（82 项）。
- 严格（div48，m 臂）：**ok 850 → 851/867（该子集口径）、NEW=0**，asset_mixin `<listcomp>` 修绿。
  （全量 div48 见 G4′。）

## D. 合并与落地

- `mkfinal72.py merged72 fix1_comp_split + broker_comp_return`：comprehension_generator
  **4 edits / +99 行**，链式锚点各恰出现 1 次，输出
  `merged72_comprehension_generator.py.json`（归档 `specs/R72-merged-comprehension.json`）。
- `mbuild72.py m` → `mirr_m`：108192 → 115583 B、BOM=False、行尾统一、净行数与 spec 一致。
- `land72.py land --spec=… --mirror=mirr_m`（dry-run）→ `replay == measured mirror bytes: OK`
  → `--apply`：`applied: 108192 -> 115583 bytes, CRLF 2115, BOM=False, equals measured mirror=True`
  （原始两行输出见 `logs/gate/Land72_replay_r72.txt` 的独立复核 `replay72check.py`：
  HEAD+spec 重放 ≡ `mirr_m` ≡ worktree 双 True，net +99）。
- 落地字节：`comprehension_generator.py` 108192 → **115583 B**（sha `be5490c1118c7199` →
  `b432a35580989852`、BOM=False、CRLF 2115、裸 LF 0、`git diff --numstat` +100/−1）；
  `region_analyzer.py`、`region_ast_generator.py` 未改。
- `Land72_landproof_r72.txt`：**33 core 文件 same=33 diff=0**。

## E. 门禁 G0–G9（landing 后，`logs/gate/`）

- G0 `G0_syntax_form_r72.txt`：三支 ast+py_compile OK；跨层模式 HEAD=8/3/0 → worktree=8/3/0，
  **new=0** ⇒ PASS。
- G1 `G1_targets_r72.txt`（47 支 failure 靶，全路径键）：**SAME=39 MOVED=8 IMPROVED=0
  REGRESSION=0 ERR=0**、fully matched 39→39（8 个 MOVED 全为 `gained=[] lost=[]`：缺陷集合不变、
  仅产物文本变）。
- G2 `G2_canary_pin_r72.txt`：4 支产物 sha 与 pin **4/4 全中**（quotation `3eb76e512df9ab1e`
  维持、未重钉）⇒ PASS；`G2_quotation_pycverify_r72.txt`：quotation **status=failure
  units=152/153**、唯一 failure = `change_his_to_forward`（与基线同，无新增）。
- G3 `G3_batch_r72.txt/.err`：`batch --index pyc_index.json --all --round 72`
  **402 verified / 0 failed**、ok 394、partial 8、failed 0、Traceback 0、FAIL 0。
- G3v `G3v_pycverify_r72.json`（mandated，8 分片 `chunks/rep0-7.json` 合并）
  **6529/6617 = 98.67%**（R71 6515/6623 = 98.37%，**+20 净成功单元**）：success **361**（+6）、
  failure **41**（−6）、compile_error 0、error 0；逐文件 `G3v_delta_r72.txt`：**转绿 6 支、转红 0 支**；
  分母 −6 为幻影单元消失（broker −4、live −1、trade_live_broker −1）。
- G4 `G4_stats_r72.txt`：`total 402 / verified 402 / ok 394 / partial 8 / failed 0`、
  **5717/5746 = 99.50%**（与 R71 持平）。
- G4′ `G4p_strict_after_r72.txt`（div48，全路径键）：**ok 1780 → 1781/1819、缺陷 39 → 38**、
  TALLY SAME=47 IMPROVED=1 REGRESSION=0、defect-better-files=1（`asset_mixin <listcomp>` 修绿）。
- G5 `G5_index_audit_r72.txt`：entries 402→402、added/removed 0、**round-stamp-only=402 /
  substantive=0**。
- G5′ `G5p_blast_r72.txt` + `blast72_expected.json`：出货产物变更 **11 支**、identical=391、
  **unresolved=0**；6 支附 mandated 迁移（全绿）、2 支官方 no-regression、3 支在 47 靶之外但
  G3 批量总数不变（5717/5746、ok394/partial8）⇒ REGRESSED=0。
- G6 `G6_battery_ext_r72.txt`：真基线臂 `prev`（HEAD blob 还原的 `mirr_prev`，R71 字节）vs
  landed，82 项 **candidate columns worse-than-landed on 0 repro(s)**。
- G7 `G7_witness_repro72.txt`：逐项 **SAME=82、REGRESSED=0、NO-RECORD=0** ⇒ PASS。
- G8 `G8_artifacts_r72.txt`：402/402 `*OK.py` 在位、py_compile bad=0、Traceback 0、FAIL 0 ⇒ PASS。
- G9 `G9_synth_r72.txt`：33 支合成（fix2 7 支 + fix1 linebreak + diag1 24 支）mandated 迁移
  **IMPROVED=4 REGRESSED=0 SAME=29** ⇒ PASS（fix2 的 chain/if-listcomp 全部 success，
  diag1 `c02_genexpr` 转绿；linebreak_and_jump 2/6 → 2/6 SAME，其失败属未修族）。

## F. 落地字节与索引指标

- `core/cfg/comprehension_generator.py` **115 583 B** sha256 `b432a3558098985252240c72e1d26960f9c92650f65b4fe2514513694ae93fab`、
  BOM=False、CRLF 2115、裸 LF 0；`git diff --numstat` **+100 / −1**（净 +99）。
- `core/cfg/region_ast_generator.py` 3 210 453 B sha `6203253987adedcf…` 未改；
  `core/cfg/region_analyzer.py` 1 769 617 B sha `8ca47f7d6b9244cf…` 未改。
- `pyc_index.json`：402 条，仅 round stamp 变化（substantive 0）。

## G. mandated 转绿 6 支（`G3v_delta_r72.txt`，全部 failure → success）

`IQEngine/data/asset_mixin`（20/21 → 21/21）、`position_model/future_position`（79/83 → 83/83）、
`position_model/live_future_position`（71/75 → 75/75）、`position_model/option_position`
（65/67 → 67/67）、`plugin_system_simulation/broker`（35/42 → 38/38）、
`plugin_system_simulation/live`（32/33 → 32/32）。
mandate「本轮至少一支修到完全 OK」由 **6 支**达成（其中 broker 与 live 为 Extra/重复发射族全清，
future_position 为 genexpr 跳转族全清）。

## H. 金丝雀与停止条件复核

- 四支金丝雀 sha 与 R71 pin 逐字节相同（`G2_canary_pin_r72.txt`：4/4 OK），官方
  143/143（quotation）、10/10、26/26、25/25 维持；quotation mandated **152/153** 与基线持平，
  唯一 failure 仍为 `change_his_to_forward` ⇒ 无新增、无需重钉。
- 已知残留（如实入档）：fix1 续行缩进取固定 16 列（更深缩进推导式合法但非最优，精确对齐需
  跨层传缩进，按 ADR-1 不做）；diag1 分歧点：F-ABSORB 主体 / F-PAD / F-POLARITY / F-TERNARY /
  F-EXCTABLE 未修，交接下轮。
