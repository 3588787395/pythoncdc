# Round 22 结果（OUTCOME）

一条线：**把索引拉回实测**，并为此落地漂移族的三条同层判据 J1′＋J2′＋J3′（R22-A）。
门禁顺序：最小复现电池 → 两个靶子 `single` 修到完全 OK → `quotation.pyc` → 全量
`batch --all --round 22` → `stats`。设计稿 `arm-design.md`，落地与实测记录 `fixes.md`，
最小复现集 `test_repros/round22_drift/`（37 复现 + `run_all.py` + `ANALYSIS.md`）。

## 一、解决了什么

1. **索引虚高的机制被堵住**：Round 18/19/20/21 四个周期都没有 `batch` 回写步骤（收尾只跑
   `single`＋`stats`），而 `batch` 默认跳过 `ok` 条目 ⇒ `pyc_index.json` 里 392/402 条停在
   Round 10。本轮第一次以 `include_ok=True` 复验 402/402，全部条目 `last_tested_round=22`。
2. **三条同层判据落地**（`region_analyzer.py` 汇点臂塌缩细化 / `region_ast_generator.py`
   or-短路链首落点判据 / 删 `_is_orphan_boundary_nop` 的跨区域 V-M 判据），严格尺子全量 A/B
   （402 文件 × 两世界）：`n_ok 5989 → 6004`、`Σ|orig−decomp| 1857 → 1776`、
   `improved=10 / broken=0 / worse=1`。逐文件、逐函数读数见 `fixes.md` §三。
3. **三个 pyc 由 partial 转为实测完全 OK**：

| pyc | 落地前官方尺实测（旧核） | 落地后 |
|---|---|---|
| `site-packages/IQEngine/plugins/plugin_system_persist/json_persistance.pyc` | 6/7 | **7/7 100.00%**（`single`） |
| `site-packages/fly/common/market_time.pyc` | 9/10 | **10/10 100.00%**（`single`） |
| `site-packages/IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc` | 17/18 | **18/18**（`batch --all` 复验） |

4. **被索引记成 `ok` 而实测不匹配的 5 条**：3 条（上面前三）现在是真的 ok；2 条
   （`IQCommon/util/trade_info_utils.pyc` 40/40→38/40、`fly/common/custom_tools.pyc` 6/6→5/6）
   按实测下调为 `partial`。这两条的退化自 `f89b85f2`（Round 13）起就存在（逐提交二分见
   `arm-design.md` §一），不是本轮造成，本轮只是第一次把它们复验出来。

## 二、被最小复现电池否决的那一版（本轮方法论收获）

先落地的是加强版 **J2r**（在 J2′ 的判据上再加一条 `get_entry_region_for_block(_pj) is not None`）。
它在全量 402 pyc 上严格优于落地版：`n_ok` 同为 +15、`Σ|delta|` −85 对 −81、`worse=0` 对 `worse=1`，
`improved=10 / broken=0` 两版相同 ⇒ 两把尺子都看不出它有什么问题。电池判它 FAIL：

```
r22_16_j2_andor_three_disjuncts | MISMATCH | MISMATCH | NOT-FIXED   f [seq_len] orig=17 decomp=9
FIX=16/17  GUARD=15/15  RESIDUE=5/5  FAIL=1  →  GATE: FAIL   （batt_j2r.txt；析取变体同值 batt_r3.txt）
```

形状是 `if a and b or c and d or e and g:`（中间那条 and 链）。加强判据要求"发跳转的前驱块
自己承载区域"，而 `or` 的短路汇合点不成区域 ⇒ 判据不触发 ⇒ 链被重建 ⇒ 左半析取支整体丢掉。
语料 402 个 pyc 里不存在这个形状，所以只有最小复现集看得见它。⇒ 回退 J2r、落地 J2′，
电池 `FIX=17/17  GUARD=15/15  RESIDUE=5/5  FAIL=0  GATE: PASS`（`batt_landed.txt`）。
纪律更新：**候选规则必须先过本轮最小复现集，再谈语料级 A/B**。

## 三、门禁原始输出（顺序与判据）

0. 电池（37 复现，before/after 双镜像核，零仓库写入）：`GATE: PASS`。
1. `single` 完全 OK：`json_persistance` 7/7 100.00%、`market_time` 10/10 100.00%。
2. `quotation.pyc`：`partial 142/143 99.30%`，唯一缺陷
   `change_his_to_forward: orig=547 decomp=548 jump_diffs=1 true_diffs=377` —— 与 Round 21
   记录逐字相同 ⇒ 本轮零副作用。
3. `batch --index pyc_index.json --all --round 22`：402/402、`failed_pyc 0`。
4. `stats --index pyc_index.json`：

```
  total_pyc: 402   verified_pyc: 402   ok_pyc: 362   partial_pyc: 40   failed_pyc: 0
  total_functions:       5746
  matched_functions:     5633
  cumulative_match_rate: 98.03%
```

索引条目实际被改动的只有 4 条（`instance` 29/32→31/32、`trade_live_broker` 103/119→104/119、
`custom_tools` 6/6→5/6、`trade_info_utils` 40/40→38/40）；`function_count` 逐条不变、
Σ=5746、条目数 402、added/removed=0（脚本复核）。序列上 `matched_functions` 与上一轮同为 5633，
区别是：这个 5633 现在是**复验出的实测值**，而落地前用旧核实测只有 5621（`arm-design.md` §一
逐条对照表），即本轮真实净增 12 个函数的字节码一致、`ok_pyc` 实测 359→362。

## 四、代价与残留

1. **严格尺子上唯一一处退化（如实登记）**：`IQData/api/api_base.pyc` 的 `get_history_df`
   幅度 `1742→1722` 变 `1742→1718`（该文件 `Σ|delta|` 36→40；`n_ok 25→25` ⇒ 官方尺不变，
   条目维持 23/25）。这是买 `market_time.trade_is_open`（97→89）与 `trade_live_broker.cancel_order`
   （89→71）两条战果的代价；试图消掉它的两条细化即 §二被电池否决的 J2r 系。
2. **产物与索引被全量复验同步**：`batch --all` 重写 38 个 `*OK.py`（`+1036/−978` 行）。
   其中 34 个在落地前与旧核产物逐行相同 ⇒ 变化出自本轮核；4 个（`klinedata`、`real_quote`、
   `quote_handler`、`realtime_event_source`）本来就是产物/核漂移文件。
3. **Round 21 对 `realtime_event_sourceOK.py` 的人工保全被本轮撤销**（`batch --all` 按当前核
   重写，`clock_worker` 回到 `decomp=1079` 那一版）。该条目官方读数不变（`partial 11/12`，
   `matched_functions` 未动），所以序列零影响；−197 这个真实缺陷不再靠保全产物掩盖，
   根因（截断 BoolOp 链后父臂双认领）移交任务 #28，`test_repros/round22_adoption/ANALYSIS.md`
   §1–4 已给出诊断与三个探针实验。
4. 电池残留 5 项（两世界都坏、同族异因，非本轮回归）：`r22_23`（`A and B or C`）、
   `r22_24`（`X or (A and B)` 括号形）、`r22_25`（`while A and b or C and D` 循环 test）、
   `r22_26`（`or` 后接 `and` 臂）、`r22_27`（`persist` 在 while 内 73→65）⇒ 进 Round 24+ 目标池。
5. quotation `change_his_to_forward` seq_len +1（本轮未动）；`handlers.pyc`
   `TWHThreadController._target 192→190`（逐字未动）。
6. 过量发射族仍未动：`executor.check_before_trading 243→254`、`data_proxy.get_bar 86→90`、
   `replace_utils.decrypt_database_url 295→324`、`realtime_event_source.get_one_event 19→20`。
7. `test_repros/round22_drift/ANALYSIS.md` 记录：`with` 相关形状在 3.11.9 上无法最小化复现
   （编译器把 `with` 体并进出异常表），因此那族只能靠语料测。

## 五、提交物

核：`core/cfg/region_analyzer.py`（sha256 前 16 位 `8529b7e8e36dc336 → 59b70fa360d19ad0`）、
`core/cfg/region_ast_generator.py`（`9dff8c0ea8ece556 → a203dd17fe82f824`，纯 CRLF、UTF-8 BOM 保持）。
产物：38 个 `*OK.py`（全部由 `batch --all` 生成，本轮零手写）。
记录：`pyc_index.json`（4 条目实测值＋402 条 `last_tested_round`）、
`test_repros/round22_drift/`（首次入库）、`rounds/round22/{arm-design.md,fixes.md,OUTCOME.md}`、
`tasks.md`（Task 22）。
