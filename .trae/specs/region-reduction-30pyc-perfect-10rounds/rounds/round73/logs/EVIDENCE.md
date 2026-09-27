# Round 73 · EVIDENCE（原始读数索引）

全部读数由中心在 `D:/Temp/opencode/r73gate/center` 独立重跑，不采信子代理自报数字。
判读工具：`h62.py`（官方尺 + 产物 sha）、`sstrict67.py`（严格尺）、`closeout69.py`（82 项电池）、
`scripts/pyc_verify.py`（mandated ruler，pylingual `compare_pyc`）、`pyc_batch_verify.py`（402 批量）、
`adr73.py`（候选 ADR-1 复测）、`gates73.py`（G0/G1/G2/G4′/G5/G6/G7/G5′/G8 + landproof）、
`g4g8replay73.py`（G4 统计 + 落地重放独立复核）、`g9run73.py`（G9 合成）、
`merge_g3v73.py`（8 分片合并 + delta）、`tryverdict_summary73.py`（try-except 定量判决汇总）。

## A. 基线（landing 前 = R72 落地字节，arm=prev）

- 起始 HEAD `b355043e`（其上 `8d136040` = R72 落地）；`mkmirr_prev73.py` 用 HEAD blob
  （LF→CRLF 还原）建 `mirr_prev`，断言 size/sha = R72 记录值：generator 3210453/`6203253987adedcf`、
  analyzer 1769617/`8ca47f7d6b9244cf`、comprehension 115583/`b432a35580989852`（本轮未改）。
- 41 靶官方基线 `dump/prev_c.jsonl`（45 行，quotation 与 canary 重复 1 行）；
  金丝_canary 与 41 靶同源；严格 `dump/strict_prev73.json`：**ok 1700 / defects 79**
  （`sstrict67` 打印口径含 quotation 重复行 = 1849/1929、缺陷 80；按 pyc 去重后 = 1700/1779、缺陷 79）。
- mandated 基线 = R72 归档 `rounds/round72/logs/gate/G3v_pycverify_r72.json`：
  **6529/6617 = 98.67%**、success 361 / failure 41、失败单元 88。
- 索引快照 `dump/index_before73.json`（出货态 5717/5746、ok 394、partial 8、failed 0）。

## B. 只读诊断（diag1，用户指令定向）

- 用户裁定（写入 `scripts/briefs/BRIEF_fix2.md` 第 −1 节，commit `b355043e`）：
  「根因就是嵌套 try-except 问题」。中心据实复测，读数见 `logs/TRYVERDICT_r73.txt`：
  - `dump/exctable_diff73.txt`：87 失败单元 **et_same 57 / et_diff 30**、`prod_deeper=0`、
    `orig_none_prod_try=0`、`orig_try_prod_none=0`；原 pyc **无异常表 44 / 有异常表 43**；
    嵌套深度 orig vs product **不差 0 项**。
  - `dump/firstdiv73.txt`：**首分歧在异常区内 14/87、区外 73/87**；kind 控制流 83 / 字节码 4。
  - 结论如实入档：指令在 14 单元子族成立，对其余 73 单元定量上不成立；
    两条读数并列存档，不以「少发射换」或改尺掩盖分歧。

## C. 三件候选与中心 ADR-1 独立复测（`adr73.py`，串行单跑）

| 臂 | spec | mandated 读数 | ADR-1 | 判定 |
|---|---|---|---|---|
| pad6 | `fix1/specs/pad_e2fix.json`（1 edit/+29） | 9 靶 470/509 → **476/509**、4 支转 success、NEW=0 | **WORSE=0 IMPROVED=6** | 采纳 |
| surgm | `fix3/specs/{merged_analyzer,polarity_gen}.json` 合并 | 6 靶 360/392 → **365/392**、2 支转 success | **WORSE=0 IMPROVED=4** | 采纳 |
| absm | `fix2/specs/absm_abs1_abs2.json` | 41 靶 1671/1759 → 1675/1759、+4 单元、1 支转 success | **WORSE=1**（klinedata `get_multiminute_his_data` sdelta 60→64）且 ORIG/landed 均 2 次 `get_kline_by_count_new` load、absm 仅 1（丢尾语句，instr 535/536→524） | **拒收** |
| m73 | pad6 + surgm 合并 | 41 靶 1671/1759 → **1684/1759**、**6 支转 success**、NEW=0 | **units compared 88 changed 10 WORSE 0 IMPROVED 10** | 落地 |

- 三臂金丝雀 4/4 全中（`dump/canary_*.jsonl`）。
- absm 备选方向 = `BRIEF_fix2.md` §5 的 abs2（`region_ast_generator` 补 orphan child 发射），交下轮。

## D. 合并与落地

- `mkfinal73.py m73 fix1/specs/pad_e2fix.json fix3/specs/merged_analyzer.json
  fix3/specs/polarity_gen.json` →
  `m73_region_ast_generator.py.json`（**4 edits / +61 行**，sha16 `87d7588b471f582c`）、
  `m73_region_analyzer.py.json`（**4 edits / +117 行**，sha16 `c16dccca0c99eea5`），
  链式锚点各恰出现 1 次。
- `mbuild73.py m73` → `mirr_m73`；`land73.py land --spec=… --mirror=mirr_m73`（dry-run）
  → `replay == measured mirror bytes: OK` → `--apply`：两文件 `equals measured mirror=True`。
- `g4g8replay73.py` 独立复核（从 **HEAD 字节**重放 spec，非 worktree 自证）：
  两文件 `replay==worktree: True`、anchor hits 全 1、BOM 状态不变 ⇒
  `logs/Land73_replay_r73.txt` **PASS**。
- `Land73_landproof_r73.txt`：**mirr_m73 33 core 文件 same=33 diff=0**。

## E. 门禁 G0–G9（landing 后，`center/logs/`）

- G0 `G0_syntax_form_r73.txt`：三支 ast+py_compile OK；跨层模式（**去注释 code-only** 口径）
  HEAD=7/3/0 → worktree=7/3/0，**new=0** ⇒ PASS。
  首版按 R72 口径（含注释的 raw 计数）读到 +1，逐行 diff 证据显示唯一新增行是
  fix1 写的注释「…不含…跨层 region.entry in r.blocks）」，非可执行判据；
  artifact 同时列出 raw 与 code-only 两组数字与该 diff 行，不隐藏首版 FAIL。
- G1 `G1_targets_r73.txt`（41 支 failure 靶，全路径键）：
  **SAME=30 MOVED=14 IMPROVED=0 REGRESSION=0 ERR=0**、fully matched **36→36**
  （14 个 MOVED 全为 `gained=[] lost=[]`：缺陷集合不变，仅产物文本变）。
- G2 `G2_canary_pin_r73.txt`：4 支产物 sha 与 pin **4/4 全中**
  （quotation `3eb76e512df9ab1e`、market_time `af77224b34b203c4`、
  datetime_func `e711b8ea86d49a15` / `9d09af09249da177`）⇒ PASS；
  `G2_quotation_pycverify_r73.txt`：quotation **status=failure units=152/153**
  （唯一 failure = `change_his_to_forward`，与基线同，无新增）。
- G3 `G3_batch_r73.txt/.err`：`batch --index pyc_index.json --all --round 73`
  **402 verified / 0 failed**、ok 394、partial 8、failed 0、Traceback 0、FAIL 0。
- G3v `G3v_pycverify_r73.json`（mandated，8 分片 `chunks/rep0-7.json` 由 `merge_g3v73.py` 合并）
  **6540/6617 = 98.84%**（R72 6529/6617 = 98.67%，**+11 净成功单元**）：
  success **367**（+6）、failure **35**（−6）、失败单元 **88 → 77**；
  逐文件 `G3v_delta_r73.txt`：**转绿 6 支、转红 0 支**，同状态位移 3 支
  （bar +2、flytools +1、quote +1）。
- G4 `G4_stats_r73.txt`：`total 402 / verified 402 / ok 394 / partial 8 / failed 0`、
  **5717/5746 = 99.50%**（与 R72 持平）。
- G4′ `G4p_strict_after_r73.txt`（45 靶，全路径键、quotation 去重）：
  **ok 1700 → 1704、缺陷 79 → 75**、TALLY SAME=41 IMPROVED=3 REGRESSION=0、
  defect-better-files=3、**NEW defect functions=0**。
  （`sstrict67` 打印口径含重复行 = ok 1849 → 1853、缺陷 80 → 76，两口径一致。）
- G5 `G5_index_audit_r73.txt`：entries 402→402、added/removed 0、
  **round-stamp-only=402 / substantive=0**。
- G5′ `G5p_blast_r73.txt` + `blast73_expected.json`：出货产物变更 **22 支**、identical=380、
  **unresolved=0**；6 支附 mandated 迁移（全绿）、4 支官方 no-regression、
  12 支在 41 靶之外但 G3 批量总数不变（5717/5746、ok394/partial8）⇒ REGRESSED=0。
- G6 `G6_battery_ext_r73.txt`：真基线臂 `prev`（HEAD blob 还原的 `mirr_prev`，R72 字节）vs
  landed，82 项 **candidate columns worse-than-landed on 0 repro(s)**。
- G7 `G7_witness_repro73.txt`：逐项 **SAME=82、REGRESSED=0、NO-RECORD=0** ⇒ PASS。
- G8 `G8_artifacts_r73.txt`：402/402 `*OK.py` 在位、py_compile bad=0、Traceback 0、FAIL 0 ⇒ PASS。
- G9 `G9_synth_r73.txt`（44 支合成：R72 diag1 24 支 + R73 diag1 15 支 + fix2 2 支 +
  fix3 2 支 + 本轮新增 F-PAD 形状 `pad73_shapes` 1 支）：
  **IMPROVED=3 REGRESSED=0 SAME=41** ⇒ PASS。
  转绿：`a01_ternary_return_in_try` failure 2/3 → **success 3/3**；
  `assert_or_tail` 14/20 → **16/20**、`polarity_andor` 4/7 → **6/7**。
  新增 `pad73_shapes.pyc` 两臂均 5/5（形状见证，prev 未复现 F-PAD，如实记 SAME）。

## F. 落地字节与索引指标

- `core/cfg/region_ast_generator.py` **3 214 913 B**、sha256 `33e22ee451148af8…`、
  BOM=True、CRLF 51566、裸 LF 0；`git diff --numstat` **+66 / −5**（净 +61）。
  （HEAD 3 210 453 B / `6203253987adedcf` → +4 460 B）
- `core/cfg/region_analyzer.py` **1 778 913 B**、sha256 `b9dcc727ea5918ea…`、
  BOM=False、CRLF 28337、裸 LF 0；`git diff --numstat` **+119 / −2**（净 +117）。
  （HEAD 1 769 617 B / `8ca47f7d6b9244cf` → +9 296 B）
- `core/cfg/comprehension_generator.py` 未改 115 583 B / `b432a35580989852`。
- `pyc_index.json`：402 条，仅 round stamp 变化（substantive 0）。

## G. mandated 转绿 6 支（`G3v_delta_r73.txt`，全部 failure → success）

`IQEngine/account/order`（67/68 → 68/68）、`IQEngine/api/api_base`（48/49 → 49/49）、
`IQEngine/core/commission`（9/10 → 10/10）、`IQEngine/core/slippage`（6/7 → 7/7）、
`fly/oauthenticator/oauth2`（10/12 → 12/12）、`fly/simtradding/flyAccount`（23/24 → 24/24）。
mandate「本轮至少一支修到完全 OK」由 **6 支**达成（F-PAD 4 支 + F-POLARITY/EXCTABLE 2 支）。

## H. 金丝雀与停止条件复核

- 四支金丝雀 sha 与 R71/R72 pin 逐字节相同（4/4 OK），未重钉。
- 已知残留（如实入档）：F-ABSORB 主体（`absm` 因 ADR-1 拒收，备选 abs2 交下轮）、
  quote 81/92、flytools 65/66、klinedata 43/45、trade_info_utils 4 支、
  quotation `change_his_to_forward`；try-except 子族 14 单元见 `TRYVERDICT_r73.txt`。
