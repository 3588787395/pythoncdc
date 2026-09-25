# Round 70 — OUTCOME

起始 HEAD = Round 70 start 提交 `9e4056f8`（core 三文件指纹 = R69 落地态 `c6cf9d568dd317b4` /
`240ecbaea36eeb70` / `be5490c1118c7199`；官方尺 5746 / 5712 / 99.41%，ok 392、partial 10）。
本轮把落地态推进到 **5746 / 5717 / 99.50%，ok 394、partial 8、failed 0**（+5 matched）；
**本轮 1 支 pyc 修到完全 OK（mandate 达成）：`IQCommon/util/fileio_utils.pyc` 12/14 → 14/14**，
mandated ruler（`scripts/pyc_verify.py`，pylingual `compare_pyc`）15/15 全等；
`trade_info_utils.pyc` 官方 39/40 → **40/40**（mandated ruler 仍 36/41，见 §6 尺子分歧）。
原始读数与判定全部在 `logs/EVIDENCE.md`（A–G）与 `logs/gate/`、`logs/dump/`。

## 1. 本轮形态

延用用户 mandate：partial 分批、只读诊断子代理并行，中心集中验证回退；每轮至少一支 pyc
修到完全 OK，再验 quotation 金丝雀，再批量回归，提交并 push；402 全量扫描归中心。
本轮形态（工作区 `D:/Temp/opencode/r70gate`，R69 交接的 provision70 已由上一会话完成，
5 个诊断代理已完成并留下 FACTS/specs，本轮由中心续做**五连复测 → 合并 → 落地 → 门禁**）：

- 10 支 partial 分 5 批（diag1 `trade_live_broker`、diag2 `quote`、diag3 `klinedata`+`real_quote`+
  `trade_info_utils`、diag4 `order_api`+`risk_calculation`+`fileio_utils`、diag5
  `realtime_event_source`+`api_base`），`provision70.py` 的 PY_FILES 已按交接改用 `closeout69.py`
  （82 项电池，含 round68/69 见证）；
- 中心按 ADR-1 逐件独立五连复测（10 支合集 + 金丝雀 4 sha + 82 项电池 + 严格逐文件差分 +
  合成咬合），全部在中心镜像上重跑，不采信代理读数；
- **采纳 3 件（c1=diag1、c3=diag3、c4=diag4）、回退 1 件（c2=diag2 拆臂证伪）、NONE 2 支
  （diag5 两支均未产出候选）**；合并 `mkfinal70.py m70`（region_analyzer 7 edits，
  逐条锚点断言「前序编辑应用后 anchor 恰出现 1 次」全过）→ `mbuild70.py m70` 出
  `mirr_m70` → 复测 → `land70.py --apply`（dry-run 断言 replay==mirror）→
  `landproof mirr_m70` 33 core 文件 **same=33 diff=0**。

10 支合集 h62 读数（`landed` = R69 落地字节 → `m70`）：**IMPROVED=3 SAME=6 MOVED=1
REGRESSION=0 ERR=0，完全匹配文件 0 → 2**；官方缺陷函数 `34 → 29`、Σhunk 147 → 145、
Σtrue-diff 5234 → 5149；严格尺 `436/488 缺陷 52 → 441/488 缺陷 47`。

## 2. 修到完全 OK 的 pyc

| pyc | 官方 landed → m70 | mandated ruler (`pyc_verify.py`) | 严格尺 | 说明 |
|---|---|---|---|---|
| `IQCommon/util/fileio_utils.pyc` | 12/14 → **14/14 100.00%** | **15/15 success_rate=100%** | `FileIO.write`、`FileLock.acquire` 两条 seq_len 全消，文件级缺陷集空 | **本轮旗舰（双尺全清）**：c4 = diag4 `cand_r70diag4_c3.json`（3 edits 全在 region_analyzer：①while-true 循环出口候选剔除 `_find_loop_else`；②R102 有界 DFS 出口 `block_to_region[_cur_jt].entry ∈ body_set` 守卫；③`for_iter_exit` 截断豁免），合成见证 `r70diag4_witness` landed 1/2 → c4 **2/2** |
| `IQCommon/util/trade_info_utils.pyc` | 39/40 → **40/40 100.00%** | 36/41（87.80%，仍 failure） | `trade_operation` seq_len 304→302 消失、同函数既有 `target_diff #94` 露出（缺陷函数数不变） | c3 = diag3 `cand_r70_tradeinfo_25b.json`（2 edits：`_25b_then_arm_orphan_return_none` 守卫 + 条件串合取）。官方尺全清，mandated/严格尺仍红 ⇒ **登记为尺子覆盖分歧（§6），不计入旗舰** |

mandate「至少一支修到完全 OK」由 **fileio_utils** 达成；`trade_info_utils` 为官方尺第二支全清。

## 3. 落地集（m70：1 个 core 文件、7 处编辑）

| 文件 | 落地字节 | 编辑 | `git diff --numstat` |
|---|---|---|---|
| `core/cfg/region_analyzer.py` | 1 754 683 → **1 763 461 B**（+125 行），sha256 `c6cf9d568dd317b4c46b…` → `20e2c9fc941aaa4f…`，无 BOM，CRLF 28 140、裸 LF **0** | 7 edits（c1×2 + c3×2 + c4×3，按落地字节位置排序重放） | +125 / −0 |
| `core/cfg/region_ast_generator.py` | **未改动**，sha256 `240ecbaea36eeb70…` 不变 | 0 | — |
| `core/cfg/comprehension_generator.py` | **未改动**，sha256 `be5490c1118c7199fe0a…` 不变 | 0 | — |

`py_compile` + `ast.parse` 三支全 OK（`logs/gate/G0_syntax_form_r70.txt`）。行号见最终落地字节；
三要素注释（识别条件 / 归约方式 / AST 映射）由各 spec 的 repl 内嵌 docstring 携带，来源：

1. **c1（diag1，`cand_r70_r57e_exc.json`）**：`_r57e_in_loop_branch_convergence` 循环分支
   会合游走对异常边后继（`exception_successors`）的豁免 —— 消费者 `trade_live_broker` 的
   `on_order_response` / `on_trade_response` 转绿（官方 109 → 111/119，gap 10 → 8）。
2. **c3（diag3，`cand_r70_tradeinfo_25b.json`）**：merge 为 None 候选点上的「裸 `return None`
   孤儿块」判据（臂可达、不在臂块集、`else_succ` 前向不可达、非子区域入口）—— 消费者
   `trade_info_utils::trade_operation` 官方全清。
3. **c4（diag4，`cand_r70diag4_c3.json`）**：while-true 循环出口候选剔除 + R102 有界 DFS
   出口守卫 + `for_iter_exit` 截断豁免 —— 消费者 `fileio_utils` 全清（旗舰）。

7 处全为同层次结构身份判据；无 `region.entry in r.blocks` 型跨层包含新增
（G0：landed=2/1/0 → merged=2/1/0，**new=0**）、无函数名/文件名/偏移/阈值启发、
无新增 self 状态、无按名字白名单。

## 4. 回退件（c2 = diag2，拆臂证伪，ADR-1）

diag2 名下唯一候选 `cand_r70diag2_af`（2 edits / 2 文件：analyzer T1 三元归并块承载后继 if +
generator T3 `_try_wrap_fstring_pending_call` 后继语句通道）。中心拆臂复测
（`dump/r70c2a_mini.jsonl` / `dump/r70c2g_mini.jsonl`，`batches/b0_diag2_rejected/`）：

- **c2a（仅 analyzer T1）**：`quote::get_price` 230/232 → 230/**251**（更差）且
  `risk_calculation/__init__` 33/35 → **32/35**（新增 `get_daily_summary` 622/647 过冲）；
- **c2g（仅 generator T3）**：quote 72/81 维持、risk 33/35 维持（惰性）；
- **c2 = T1+T3**：quote 72 → 73/81（get_price 转绿）但 risk_calculation 回归仍在。

ADR-1：任何回归即拒 ⇒ **整件回退**，quote 本轮维持 72/81。10 支合集与 402 批量回归
（G3）均以**不含 c2** 的 m70 为准。

## 5. 门禁（严格串行，全过）

- **G0** `ast`+`py_compile` 三支 OK；跨层模式 landed=2/1/0 → merged=2/1/0，**new=0**。
- **G1** 10 支合集 `IMPROVED=3 SAME=6 MOVED=1 REGRESSION=0 ERR=0`；完全匹配文件
  **0 → 2**（fileio_utils 14/14、trade_info_utils 40/40）；trade_live_broker 109 → 111/119。
- **G2** 金丝雀 4 支产物 sha 与 R69 落地态**逐字节相同**（`4d41187e356544e0` quotation、
  `af77224b34b203c4` market_time、`e711b8ea86d49a15` / `9d09af09249da177` datetime_func）、
  官方 143/143+10/10+26/26+25/25、严格两臂均 **209/211 缺陷 2**
  （change_his_to_forward #250、get_trend #10，与 R69 逐字同）。
- **G3** `pyc_batch_verify.py batch --index pyc_index.json --all --round 70`
  **402 verified / 0 failed**、Traceback 0、FAIL 0；**mandated ruler 首录**：
  `pyc_verify.py batch`（8 分片）402 支 **6498/6623 单元 = 98.11%**、346 支文件全等、
  56 failure、0 compile_error / 0 error（`logs/gate/G3v_pycverify_r70.json`）。
- **G4** stats **5746/5717/99.50%**（matched +5、完全匹配 392 → 394、partial 10 → 8）。
- **G4′** 严格尺 10 支发布产物 **436 → 441/488、缺陷 52 → 47、FIXED 5、NEW=0**
  （NEW 两条均为既有函数换 kind/计数：clock_worker seq_len 1287→1286、
  trade_operation seq_len→target_diff #94）。
- **G5** 索引审计 402→402、added/removed 0、key-shape 0、round-stamp-only 399、
  **substantive=3 且全为改善**（fileio 0.857→1.0 ok、trade_info 0.975→1.0 ok、
  trade_live_broker 0.916→0.933）。
- **G5′** blast **changed=8 identical=394 unresolved=0、REGRESSED=0**：3 支 substantive 改善 +
  1 支 MOVED（realtime_event_source clock_worker 纯位移 |Δ| 11→10）+ 4 支**文本移位**
  （graph / backtest_info_utils / ptrade_broker / ptradeAccount：`else: if` → `elif` 等价重排
  与语句再嵌套，官方计数两侧全等且双臂 fully matched，b4 四支严格尺
  187/192 缺陷 5 → **189/192 缺陷 3**，纯改善）。未手改任何生成文件（8 支 *OK.py 全由
  G3 工具链重写）。
- **G6** 电池（cands）82 项 worse-than-landed=**0**（c1/c3/c4 三臂）；扩展 82 项
  （m70 臂）worse=**0**，维持 **318/356 缺陷 37** 水平（R70 基线）。
- **G7** 见证 82 项（head=R69 镜像 vs m70）worse=**0**、REGRESSION=0。
- **G8** 402/402 `*OK.py` 在位 + `py_compile` bad=0（SyntaxWarning 容忍，与 R69 同口径）+
  G3 无 Traceback / FAIL → **PASS**。
- **landproof** `mirr_m70` vs 落地 repo：33 core 文件 **same=33 diff=0**；
  `land70.py` dry-run 断言 replay==mirror OK（1 763 461 B）。

## 6. 副作用与尺子分歧裁定（如实入档）

- **旗舰分歧（R68 matcher 先例）**：`trade_info_utils` 官方 40/40 但 mandated ruler 36/41
  （`trade_operation` 仍不全等）+ 严格 `target_diff #94`。按 R68 口径**旗舰取双尺全清的
  fileio_utils**，trade_info_utils 记「官方尺全清、严格/mandated 仍红」。
- **mandated ruler 基线首录**：402 支 6498/6623 = **98.11%**、346 支全等。该尺比官方尺严
  （嵌套 code object 前缀配对 + `Missing/Extra/Different control flow/Different bytecode`），
  R70 起作为记录基线（R69 无此读数，无可比列）。
- **G1 `MOVED=1` = `realtime_event_source`**：`clock_worker` decomp 1286→1285
  （jump=10、true=481 不变），官方 matched 11/12 不变；按 ADR-1 位移族判**改善**（|Δ| 11→10）。
- **G4′ 换 kind 两条**：clock_worker seq_len（1276,1287→1286）、trade_operation
  seq_len→target_diff #94 —— 均为**同函数**既有缺陷换形，无新增缺陷函数（FIXED 5：
  on_order_response、on_trade_response、FileIO.write、FileLock.acquire、set_trade_status）。
- **diag5 两支 NONE**（如实记录）：`realtime_event_source::clock_worker` 三处独立根因
  （`_or_rhs_block` 记账吞 IfRegion.entry / @7604 与 @7634 争认块 8592 / `_loop_postprocess`
  推迟致伪 break+`while True` 包裹），需成对落地且属分析层区域重构，无同层次轻判据；
  `api_base::get_history_df` seq_diff #419 极性 + 位移，2254 汇合点归属未钉死到单一赋值点，
  且所需改动落在 R69 已判「过重」的 `inline_boolop_chains` 6 读点族 ⇒ 均不产候选。
- 本轮**落地回退 0 件**（c2 在合并前被拆臂证伪，未进 m70）。

## 7. 残余 8 支 partial（gap 合计 29 个函数）

| 家族 | 涉及（m70） | 已知证据 |
|---|---|---|
| **位移 / 线性化通道** | `quote` 72/81（余 9）、`real_quote` 40/44、`klinedata` 43/45、`api_base` 24/25 | diag2 T 系候选需先解决 risk_calculation 过冲副作用；`get_history_df` 2254 汇合点归属 |
| **多 hunk 大文件残余** | `trade_live_broker` 111/119（8 gap） | `_process_order` 454/396、`_sync_worker` 349/347、`etf_basket_order` 693/693 等未见改善 |
| **R50 kwarg 槽位 bail** | `order_api` 32/34 | `future_order`/`option_order` 两支，or-chain 站点因果仍在但需窄化 |
| **try/loop-exit JUMP_FORWARD** | `risk_calculation/__init__` 33/35、`realtime_event_source` 11/12 | 三签名纠缠（diag5 判据：成对落地 + 区域重构） |

## 8. 下一轮（R71）线索与交接

1. **diag2 的 risk_calculation 过冲**是 quote 余 9 的闸门：T1 的三元归并判据需要把
   「merge 承载后继 if」限制到 get_price 形态（值段空 + 单前驱），或把 T3 的
   `post_consumer_extra_stmts` 通道单独验证 —— 先做 `get_daily_summary` 最小复现再动。
2. **`trade_info_utils::trade_operation` target_diff #94**（POP_JUMP_IF_FALSE 终点
   orig=('write_info', LOAD_FAST) vs decomp=(None, FOR_ITER)）：官方尺对跳转容差计入而全清，
   严格/mandated 尺仍红；下一轮若取「双尺全清支数」为尺，需先补这条发射侧判据。
3. **diag5 两支**：按其 FACTS 的三签名纠缠，`clock_worker` 需「成对落地」提案
   （`_or_rhs_block` 记账 + 争认块仲裁 + `_loop_postprocess` 推迟撤销一起上），
   建议先出三份独立合成复现再评估合并风险。
4. **电池与见证**：82 项 closeout69 电池继续为 R71 基线（本轮 G6/G7 全部 worse=0）；
   mandated ruler（`pyc_verify.py`）402 全量读数 6498/6623=98.11% 为首录基线，
   R71 起门禁应含 G3v 分片重跑（8 分片，每片 <40s）。
5. **技术债**：generator `_os_dbg_*` 调试导入清理仍未做（diag2 的 T1 anchor 里仍可见
   `_R23N20_DEBUG` 死代码）；本轮 analyzer 的 7 处 repl 均为干净判据，无新增调试残留。
