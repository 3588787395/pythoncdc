# Round 72 · OUTCOME

起始 HEAD = Round 72 start 提交 `37dc4a01`（其上为 R71 落地记录 `6c0a8f8c`；core 三文件指纹 =
R71 落地值 `8ca47f7d6b9244cf` / `6203253987adedcf` / `be5490c1118c7199`；官方尺 5746/5717/99.50%、
ok 394、partial 8、failed 0，mandated ruler 6515/6623 = 98.37%）。本轮结果：**mandated ruler 推进到
**6529/6617 = 98.67%**（失败单元 108 → 88，−20），官方尺维持 **5746/5717/99.50%**（ok 394、
partial 8、failed 0，本轮无官方计数变动）；**本轮 6 支 pyc 在 mandated 尺下修到完全 OK**
（mandate 达成），另有 trade_live_broker 1 单元清零（114/129 → 114/128）。原始读数与判定全部在
`logs/EVIDENCE.md`（A–H）与 `logs/gate/`、`logs/dump/`。

mandated 分母 6623 → 6617（−6）为**幻影单元消失**而非统计口径变化：broker −4、live −1、
trade_live_broker −1 —— 重复发射的 `<listcomp>`/`return` 函数不再出现在配对里。

## 1. 本轮形态

延用用户 mandate：部分分批、只读诊断子代理并行、中心集中验证回退；每轮至少一支 pyc 修到完全
OK，再验 quotation 金丝雀，再批量回归，提交并 push；402 全量扫描归中心。本轮形态（工作区
`D:/Temp/opencode/r72gate`，provision72/prep72 已完成，47 支 failure 靶集与 85 cf + 12 bytecode
单元来自 R71 G3v）：

- **Mission**：三批并行 —— diag1 只读诊断头部 control-flow 族；fix1 打 `comprehension_generator.py`
  的 genexpr/listcomp Different bytecode 族（该文件 R72 前 0 编辑）；fix2 打头部 Extra/重复发射族。
- **fix1 `fix1_comp_split.json`**（3 edits / +79 行，仅 comprehension_generator）：CPython 3.11 按
  `and` 链操作数的源码行界选跳转方向，产物恒单行 ⇒ 恒回跳，原 pyc 前跳 ⇒ argval 分叉；按原 pyc
  自己的跳转方向选渲染，失败回退单行。
- **fix2 `broker_comp_return.json`**（1 edit / +20 行，仅 comprehension_generator）：
  `try_generate_comprehension_assign` 的 `RETURN_VALUE/RETURN_CONST` 分支 append `Return` 后漏推进
  `prev_end`，`_generate_remaining_stmts` 二次重建 ⇒ 同型 `Return` 重复发射（broker 每条 elif 臂
  `return [...]` 连写两次、6 个无原对应 `<listcomp>`）。诊断方 diag1 独立定位到同一行
  （`comprehension_generator.py:520-521` + `:573`），三方一致。
- 中心 ADR-1 独立复测 **两件全采纳**（f1 / f2 / 合并 m 三臂各自 PASS）→ `mkfinal72` 合并
  **4 edits / +99 行**（链式锚点各恰出现 1 次）→ `mbuild72 m` → `mirr_m` → 候选七项复测 **GO**
  → `land72 --apply`（dry-run 断言 replay==mirror，apply 后 equals measured mirror=True）
  → `landproof` 33/33。
- 门禁严格串行：G0 → G1 → G2 → G3 → G3v → G4 → G4′ → G5 → G5′ → G6 → G7 → G8 → G9 全过。

## 2. 修到完全 OK 的 pyc（mandate 达成，mandated ruler 口径）

`G3v_delta_r72.txt`：**failure → success 6 支、转红 0 支**。

| pyc | mandated landed → R72 | 官方（h62 口径） | 说明 |
|---|---|---|---|
| `IQEngine/data/asset_mixin.pyc` | 20/21 → **21/21 success** | 16/16 不变 | fix1 推导式跳转方向 + `<listcomp>` 谓词 |
| `.../position_model/future_position.pyc` | 79/83 → **83/83 success** | 72/72 不变 | fix1（4 个 `<genexpr>`） |
| `.../position_model/live_future_position.pyc` | 71/75 → **75/75 success** | 64/64 不变 | fix1（4 个 `<genexpr>`） |
| `.../position_model/option_position.pyc` | 65/67 → **67/67 success** | 60/60 不变 | fix1（2 个 `<genexpr>`） |
| `plugin_system_simulation/broker.pyc` | 35/42 → **38/38 success** | 24/24 不变 | fix2（Extra×4 + Different×2 + cf×1 全清） |
| `plugin_system_simulation/live.pyc` | 32/33 → **32/32 success** | 26/26 不变 | fix2 同族（重复 `return [...]`） |
| `plugin_system_trade/trade_live_broker.pyc` | 114/129 → 114/128（仍 failure） | 111/119 不变 | fix2 清 1 个 Extra，零新增 |

合成咬合：`G9_synth_r72.txt` **IMPROVED=4 / REGRESSED=0 / SAME=29 ⇒ PASS**（fix2 的 7 支
chain/if-listcomp 复现全部 success，fix1 诊断方复现 `c02_genexpr` 转绿）。

## 3. 落地字节

- `core/cfg/comprehension_generator.py` **108 192 → 115 583 B**（4 edits、净 +99 行，
  sha256 `be5490c1118c7199fe0a…` → `b432a3558098985252…`、BOM=False、CRLF 2115、裸 LF 0、
  `git diff --numstat` **+100 / −1**）。
- `region_ast_generator.py` / `region_analyzer.py` 本轮**未改**（3210453 B `6203253987adedcf`、
  1769617 B `8ca47f7d6b9244cf` 维持）。
- `Land72_replay_r72.txt`：对 HEAD 字节逐 edit 重放 ≡ `mirr_m` ≡ worktree（LF 归一）双 True；
  `Land72_landproof_r72.txt`：33 core 文件 same=33 diff=0；G0 跨层模式 HEAD=8/3/0 →
  worktree=8/3/0，**new=0**。
- `pyc_index.json`：402 条，仅 round stamp 变化（substantive 0）。

## 4. 只读诊断与剩余面（diag1 FACTS，交接下轮）

A 组 58 单元 = **F-ABSORB 42 / F-PAD 6 / F-EXTRA 5 / F-OTHER 2 / F-TERNARY 2 / F-POLARITY 1**；
全量 108 单元族聚类 = F-ABSORB 70 / F-PAD 14 / F-OTHER 12 / F-EXTRA 6 / F-POLARITY 3 /
F-TERNARY 2 / F-EXCTABLE 1（`fam72.json`，真实判据重算）。根因到行（R72 HEAD 实测行号）：
F-TERNARY `ra :20432` + `ra-gen :3199-3223/:11711/:17753`；F-ABSORB `ra :23303/:26646/:15929` +
`ra-gen :22512 [R71-thenover] 影子认领仍不充分/:17753/:15503`；F-PAD `ra-gen :185/:26482/:14865`
（落点一律 +4）；F-EXTRA `comprehension_generator :520-521/:573`（**已被 fix2 修**）；
F-OTHER `ra-gen :88-100 _flip_contains_compare`（`in`→`not in`）+ `:21530/:17753`；
F-POLARITY `ra-gen :46/:57-59/:12032/:12108`。synth 24 支中 18 支复现（11 支经
`verify_readings.txt` 复核），负对照 2 支 success，R71 老形状 5 支已转绿（R71 fix2/fix3 生效）。

**交接下轮**：剩余 41 支 failure / 88 失败单元 —— F-ABSORB 主体（and 链共享 else、链尾吸收）、
F-PAD 14、F-OTHER quote 2（外层 if 掏空、`not in` 会员判据）、F-POLARITY 3（`_sync_worker`、
`get_history`）、F-TERNARY 2、F-EXCTABLE 1（commission）、R70 交接项
`trade_info_utils.trade_operation target_diff #94`（本轮严格尺读数仍为 orig=('write_info',…) vs
decomp=(None,'FOR_ITER')）。

## 5. 门禁（严格串行，全过）

G0 PASS（三支 ast+py_compile OK、跨层 new=0）；G1 47 靶 SAME=39 MOVED=8 REG=0 ERR=0、
fully matched 39→39；G2 金丝雀 4/4 pin 全中 + quotation 官方 143/143、mandated **152/153**
（唯一 failure `change_his_to_forward`，无新增）；G3 `batch --round 72` **402 verified / 0 failed**；
G3v mandated **6529/6617 = 98.67%**（361 success +6、41 failure −6、转红 0）；G4 stats
5717/5746 = 99.50%；G4′ 严格 div48 **1780 → 1781/1819、缺陷 39 → 38、REGRESSION=0、
IMPROVED=1**（`asset_mixin <listcomp>` 修绿）；G5 索引 round-stamp-only=402、substantive=0；
G5′ blast changed=11 identical=391 unresolved=0 **REGRESSED=0**；G6 真基线臂 `prev`
（HEAD blob 还原的 `mirr_prev`，R71 字节、size/sha 断言）vs landed 82 项 **worse=0**；
G7 逐项 SAME=82 REGRESSED=0；G8 402 OK.py 在位 + py_compile bad=0 + Traceback 0；
G9 合成 29 SAME / 4 IMPROVED / 0 REGRESSED。未手改任何生成的 `*OK.py`（11 支变更全由工具链重写）。
