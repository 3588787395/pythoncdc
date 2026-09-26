# Round 71 · OUTCOME

起始 HEAD = Round 71 start 提交 `bbc0869d`（其上为 R70 落地记录 `b21c5c61`；core 三文件
指纹 = R70 落地值 `20e2c9fc941aaa4f` / `240ecbaea36eeb70` / `be5490c1118c7199`，
官方尺 5746/5717/99.50%、ok 394、partial 8、failed 0，mandated ruler 6498/6623 = 98.11%）。
本轮把 **mandated ruler 推进到 6515/6623 = 98.37%**（+17 单元），官方尺维持
**5746/5717/99.50%**（ok 394、partial 8、failed 0，本轮无官方计数变动）；
**本轮 9 支 pyc 在新验证脚本 `scripts/pyc_verify.py`（pylingual `compare_pyc`）下修到完全 OK**
（mandate 达成），其中 `fly_api/base.pyc` 在 **mandated 63/63 与严格尺 63/63 双尺全清**
（官方 h62 口径该支 41/41 本已全等）。
原始读数与判定全部在 `logs/EVIDENCE.md`（A–H）与 `logs/gate/`、`logs/dump/`。

## 1. 本轮形态

延用用户 mandate：partial 分批、只读诊断子代理并行、中心集中验证回退；每轮至少一支 pyc
修到完全 OK，再验 quotation 金丝雀，再批量回归，提交并 push；402 全量扫描归中心。
本轮形态（工作区 `D:/Temp/opencode/r71gate`，R70 交接 provision71 已完成）：

- **Mission**：集中处理新验证脚本暴露的 56 支 failure，重点是控制流族
  （Different control flow 102 单元 / Different bytecode 17 / Extra bytecode 6）；
  中心解析出 48 支官方 ok 但 pylingual failure 的分歧集。
- 三件修复代理各出 1 份候选（fix1 = 异常隐式收尾被当 else 臂、fix2 = F-THENOVER
  影子认领+放宽、fix3 = 异常表/AssertRegion 收口），中心 ADR-1 独立复测 **三件全采纳**；
  diag1 只读诊断给出全族聚类与到行根因，并**实测否定**了「多数是嵌套 try-except」的
  线索（主族 F-THENOVER 与 try 无关，try/异常边只对应 F-EXCTABLE / F-ASSERT）。
- 合并 `mkfinal71.py m71`（generator 5 edits/+137、analyzer 5 edits/+80，链式锚点全过）→
  `mbuild71.py m71` → `mirr_m71` → 七连复测 **GO** → `land71.py --apply` ×2
  （dry-run 断言 replay==mirror）→ `landproof` 33/33。
- 门禁严格串行：G0 → G1 → G2 → G3 → G3v → G4 → G4′ → G5 → G5′ → G6 → G7 → G8 全过。

## 2. 修到完全 OK 的 pyc（mandate 达成，mandated ruler 口径）

`G3v_delta_r71.txt`：**failure → success 共 9 支、转红 0 支**；18 支 sha 变化文件失败单元
45 → 28（net −17、fixed=17、NEW=0）。

| pyc | mandated landed → m71 | 官方（h62） | 说明 |
|---|---|---|---|
| `IQEngine/plugins/plugin_fly_data/fly_api/base.pyc` | 61/63 → **63/63 success** | 41/41 → 41/41（h62 口径该支本已全等；**strict 62/63 → 63/63**、mandated 63/63） | **旗舰（mandated + strict 双尺全清）**：fix3 异常表/AssertRegion 收口 + fix2 THENOVER；严格 `OverNightOrder.__init__ [seq_len]` 修绿 |
| `IQCommon/exception.pyc` | 33/34 → **34/34** | 32/32 不变 | fix1 异常隐式收尾判据 |
| `IQData/entry.pyc` | 4/5 → **5/5** | 5/5 不变 | 同上族 |
| `IQData/utils/exception.pyc` | 30/31 → **31/31** | 29/29 不变 | 同上族 |
| `IQEngine/utils/exception.pyc` | 30/31 → **31/31** | 29/29 不变 | 同上族 |
| `plugin_system_accounts/__init__.pyc` | 5/6 → **6/6** | 6/6 不变 | fix2 THENOVER 影子认领 |
| `.../benchmark_account.pyc` | 19/20 → **20/20** | 20/20 不变 | 同上族 |
| `.../stock_account.pyc` | 24/25 → **25/25** | 25/25 不变 | 同上族 |
| `plugin_system_risk_calculation/function.pyc` | 14/15 → **15/15** | 15/15 不变 | 同上族 |

另有 9 支仍为 failure 但单位只减不增（klinedata 59→61/64、wizard 54→55/58、strategy 25→26/27、
quotation 151→152/153、quote 79→80/92、load_daily 25→26/27、trade_info/matcher/realtime 计数全等）。
严格尺同步修绿 4 条 target_diff/seq_len：`init_stock_pool_filter`、`OverNightOrder.__init__`、
`get_trend`、`filter_abnormal_data`。

## 3. 落地集（m71，两个 core 文件）

| 文件 | 落地字节 | 编辑 | `git diff --numstat` |
|---|---|---|---|
| `core/cfg/region_ast_generator.py` | 3 199 517 → **3 210 453 B**（+137 行），sha256 `240ecbaea36eeb70…` → `6203253987adedcf…`，BOM 保留、CRLF 51 505、裸 LF 0 | 5 edits：R71-exception_exit×1、r71f2_full×2、R71-exctable×2 | +140 / −3 |
| `core/cfg/region_analyzer.py` | 1 763 461 → **1 769 617 B**（+80 行），sha256 `20e2c9fc941aaa4f…` → `8ca47f7d6b9244cf…`，无 BOM、CRLF 28 220、裸 LF 0 | 5 edits：R71-analyzer-merged（exctable-analyzer 2 + assert 3） | +83 / −3 |
| `core/cfg/comprehension_generator.py` | 未改动，sha256 `be5490c1118c7199fe0a…` | 0 | — |

`py_compile` + `ast.parse` 三支 OK（`logs/gate/G0_syntax_form_r71.txt`）。三要素注释随 spec
repl 内嵌 docstring 携带（同层次结构身份判据，无函数名/文件名/偏移/阈值启发、无新增 self 状态）；
跨层 `region.entry in r.blocks` 型模式 landed=2/1/0 → merged=2/1/0 ⇒ **本轮 0 新增**
（`[R71-assert]` 注释因字面含该模式串先被 G0 计为 +1，改写为「区域入口属于它层块集」型表述后
repo / mirr_m71 / 合并 spec / R71-assert.json 四处同步，计数回到 2/1/0）。

落地来源与判据：

1. **fix1 `R71-exception_exit.json`**（generator，+62 行）：`_if_generate_else_branch` 把
   try 块的**隐式收尾**当成了 else 臂 ⇒ 消费者含 `IQCommon/exception`、`IQData/entry`、
   两支 utils/exception 的 `__exit__` 单元（mandated 26→19）。
2. **fix2 `r71f2_full.json`**（generator，2 edits）：F-THENOVER 影子认领 + 放宽守卫
   ⇒ 消费者含 accounts 三支、`risk_calculation/function`、`strategy`、`load_daily`、
   `quotation.get_trend`（mandated +6、strict ok 2164→2170、synth t01/t02/t22 3/3）。
3. **fix3 `R71-exctable.json` + `R71-exctable-analyzer.json` + `R71-assert.json`
   （经 `R71-analyzer-merged.json` 前置自检等价合并）**：异常表出口/重复 AssertRegion 收口
   ⇒ 消费者 `fly_api/base`（官方+mandated 双全清）、`IQData/entry`；known-unfixed 2 条如实留档。

## 4. 落地与门禁（严格串行，全过）

- `land71.py --apply`：`Land71_replay_r71.txt` 两文件 `replay==worktree: True`；
  `Land71_landproof_r71.txt` **33 core 文件 same=33 diff=0**。
- **G0** 语法/形态 PASS、跨层模式 0 新增。
- **G1** 56 支官方靶 `SAME=38 MOVED=18 IMPROVED=0 REGRESSION=0 ERR=0`、fully matched 48→48。
- **G2** 金丝雀 4/4 pin 全中（quotation 重钉 `3eb76e512df9ab1e`）；quotation 官方 143/143、
  mandated 152/153（仅 `change_his_to_forward`）。
- **G3** `batch --all --round 71` **402 verified / 0 failed**、Traceback 0、FAIL 0。
- **G3v** mandated ruler **6515/6623 = 98.37%**（R70 98.11%，**+17 单元**）：
  success 355(+9) / failure 47(−9) / error 0；转绿 9、转红 0。
- **G4** 官方 `5717/5746 = 99.50%`、ok 394、partial 8、failed 0（与 R70 持平）。
- **G4′** 严格 div48 `ok 1776 → 1780/1819`、缺陷 `43 → 39`、target_diff `20 → 17`、
  **NEW=0、FIXED=4 文件**。
- **G5** 索引 402→402、substantive=0、round-stamp-only=402、matched delta 0。
- **G5′** blast 出货产物变更 18 支、**unresolved=0、REGRESSED=0**（9 支 failure→success，
  其余只减不增，逐支证据见 `blast71_expected.json`）。
- **G6** 真基线臂 `prev`（HEAD blob 还原 R70 字节的 `mirr_prev`）vs `m71`，82 项电池
  **worse=0**；**G7** 逐项 prev vs m71 **SAME=82、REGRESSED=0**。
- **G8** 402/402 `*OK.py` 在位、py_compile bad=0、Traceback 0、FAIL-line 0。

## 5. 副作用与尺子分歧裁定（如实入档）

- **键撞导致的首版读数更正**：`gates71a.py` 用 `basename@parent` 作行键，`exception.pyc@utils`
  与 `api_base.pyc@api` 各有两支同键文件 ⇒ G1 丢 2 行（读作 37/17=54）；G4′ 丢 1 行 31 函数
  （读作 ok 1745→1749）。`gates71a_fix.py` 以**全路径键**重算，更正为 G1 `38/18=56`、
  G4′ `ok 1776→1780`（缺陷 43→39 两版一致）；其余门禁文件不受影响。
- **G6 基线臂语义**：landing 后 `arm=landed` 即 R71 字节，与 `m71` 同源而使对比空转；
  按 R68 先例重建 `mirr_prev`（HEAD blob + LF→CRLF 还原，size/sha 断言 = R70 记录值）作真基线。
- **G1 MOVED=18** 全部为 `gained=[] lost=[]`（缺陷集合不变、仅产物文本变化），
  含金丝雀 quotation 与 9 支转绿文件；按 ADR-1 位移族判据：hunk 降 + first_diff 回移 +
  Σ|Δ| 不升 + 严格尺无新增 ⇒ 放行。
- **金丝雀 quotation 重钉**：`4d41187e356544e0 → 3eb76e512df9ab1e`，官方 143/143 不变、
  mandated 151/153 → 152/153（`get_trend` 转绿、无新增 failure）、严格 `get_trend` 修绿
  ⇒ 净改善，按停止条件允许。
- **mandated 与官方计数分歧**：本轮官方 5717 不变而 mandated +17 —— 官方尺只计字节等价函数，
  新尺额外判控制流结构；两支尺子读数分歧（如 `trade_info_utils` 官方 40/40 / mandated 36/41）
  维持 R68/R70 先例登记，不计回归。
- 未手改任何 `*OK.py`（18 支变更全部由工具链重写）。

## 6. 归档

`rounds/round71/`：`logs/EVIDENCE.md`（A–H）、`logs/gate/`（G0–G8 + G3v + G3v_delta +
G2_canary_pin + G2_quotation_pycverify + G5p + Land71_landproof + Land71_replay +
blast71_expected）、`logs/dump/`（56 靶/金丝雀/各候选臂/严格 json/电池 jsonl/8 分片 mandated 报告）、
`specs/`（m71 合并件两份 + r71f2 + 三件候选与其 rejected 变体）、`batches/`
（diag1_salvage、diag1、fix1、fix2、fix3 的 BRIEF/FACTS/specs）、`scripts/`
（provision71、gates71a/_fix、gates71b、mkfinal71、mbuild71、land71、mkmirr_prev71、mkblast71、
merge_g3v71、mkarchive71r、h62、closeout69、audit5_g5_67、sstrict67、briefs）。

## 7. 交接（R72 建议起点）

- 剩余 mandated failure 47 支：头部 `trade_info_utils` cf=5、`quote` 12 单元、`real_quote`、
  `klinedata` 3 单元、`trade_live_broker` 8 单元；long tail cf=1 约 26 支。
- fix3 known-unfixed 2 条：ra `:14865` 重复 AssertRegion、孤儿 else 尾语句；
  quotation `change_his_to_forward` 与 G1 位移族文本差异可作下一轮候选。
- R70 交接项 `trade_operation target_diff #94` 发射侧判据仍待处理；
  `provision72` 的 `PY_FILES` 建议继续用 `closeout69.py` 82 项电池。
