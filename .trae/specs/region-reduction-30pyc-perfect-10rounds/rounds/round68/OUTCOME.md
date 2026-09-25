# Round 68 — OUTCOME

起始 HEAD = Round 67 记录提交 `ffc6dc7a`（官方尺 5746 / 5701 / 99.22%，ok 387、partial 15）。
本轮把落地态推进到 **5746 / 5709 / 99.36%，ok 392、partial 10、failed 0**（+8 matched、+5 支全清）。
原始读数与判定全部在 `logs/EVIDENCE.md`（A–G）与 `logs/gate/`、`logs/dump/`。

## 1. 本轮形态

用户 mandate：剩余 partial **分 5 批、由 5 个子代理快速完成，再集中验证回退**；每轮至少把一支 pyc
修到完全 OK，再验 quotation 金丝雀，再批量回归，**提交并 push**；所有命令 <300 秒、门禁严格串行、
402 全量扫描归中心（子代理禁止跑）。

- 15 支 partial 按 `max(严格缺陷, 官方 gap)` 贪心均衡分 **5 批**（工作区 `diag1`/`diag3`/`diag4`/
  `diag5`/`diag6`），每批 1 个**只读**诊断代理并行诊断并各自交付候选 spec；
  另有 `diag2`（`quote` + `matcher` 名下）交付的唯一候选 `cand_r68_else_join_cut.json`
  在 ADR-1 记录下**自行撤回**（实测 `matcher 715/715 → 713/466`、`quote 70/81 → 64/81`），不进合并集。
- 中心集中验证：`mkfinal68.py m68 <6 份 spec>` 合并 → `m68_region_analyzer.py.json`（6 edits）+
  `m68_region_ast_generator.py.json`（11 edits），**链式锚点断言全过**；`mbuild68c.py m68` 出镜像
  `center/mirr_m68` 后再量测；采纳判据按 ADR-1 更正版执行（缺失/过冲族要求 Σ|Δ| 净减；
  纯位移族要求归一化 hunk 数严格下降 + `first_diff` 回移 + Σ|Δ| 不升 + 严格尺不得新增 `target_diff`）。
- **采纳 5 件、回退 0 件**；五件单臂（`b1..b5`）在 15 支合集上的读数与合并集一致、无互相冲突，
  合并集 `m68` 一次过门。

15 支合集 h62 `ab`（prev=R67 字节 → m68）读数：**SAME=4 IMPROVED=7 REGRESSION=0 MOVED=4 ERR=0**、
完全匹配文件 0 → **5**；金丝雀 `SAME=4`；45 项电池 `SAME=39 IMPROVED=6 REGRESSION=0`。
合集量级：`matched 572 → 580 / 617`、缺陷函数 `45 → 37`、`Σ|Δ| 296 → 256`、
hunk 合计 `181 → 151`、true-diff 合计 `9059 → 5911`。

## 2. 修到完全 OK 的 pyc（mandate 至少一支 → 本轮 5 支）

| pyc | 官方 prev → landed | 严格尺（发布产物） | 备注 |
|---|---|---|---|
| `IQEngine/utils/scheduler.pyc` | 44/45 → **45/45 100%** | **52/52、bad=[]** | G1 单验：`missing_in_decomp []`、`extra_in_decomp []`，双尺全清 |
| `fly/simtradding/flyAccount.pyc` | 21/23 → **23/23 100%** | **23/23** | G1 单验：`missing/extra` 皆空，双尺全清 |
| `IQCommon/strategy/wizard_quant_api.pyc` | 52/53 → **53/53 100%** | 54/56（余 2 为既有） | `params_analysis` 消失 |
| `fly/logger.pyc` | 29/30 → **30/30 100%** | 63/64 | 严格余 1 = R67 已知 `check_baseFilename target_diff #14` |
| `IQEngine/plugins/plugin_system_matcher/matcher.pyc` | 16/17 → **17/17 100%** | 16/17 | 严格余 1 = `target_diff #192`，见 §6 |

本轮旗舰取 `scheduler`、`flyAccount`（**双尺全清**）；另三支为官方尺全清、严格尺余量均属既有缺陷
（NEW=0 见 §4 G4′）。

## 3. 落地集（m68：2 个 core 文件、17 处编辑）

| 文件 | 落地字节 | 编辑 | `git diff --numstat` |
|---|---|---|---|
| `core/cfg/region_analyzer.py` | 1 753 093 B，sha256 `27089306098c35dc1f3a…`（前值 `af8cc88b9f89779b3ef0…`），无 BOM，CRLF、裸 LF **0**，27 998 行 | 6 edits | +126 / −2 |
| `core/cfg/region_ast_generator.py` | 3 193 950 B，sha256 `3cd0fcd6cbd7446c3703…`（前值 `f712bc20d7ad44542e18…`），BOM **保留**，CRLF、裸 LF **0**，51 310 行 | 11 edits | +591 / −64 |
| `core/cfg/comprehension_generator.py` | **未改动**，sha256 `be5490c1118c7199fe0a…` 不变 | 0 | — |

`py_compile` + `ast.parse` 三支全 OK；`closeout67.py landproof mirr_m68` = 33 core 文件
**same=33 diff=0**；`land68.py land --apply` 断言「spec 重放 == 实测镜像字节」逐文件通过
（dry-run 与 apply 各跑一次，产物与测量镜像逐字节相同）。行号为最终落地字节上的标记：

**region_analyzer.py（6 edits）**

1. **L? `is_block_entry` `[R68-diag5]`** — then 臂入口块（比较链归约时一并登记进 `block_to_region`）
   自身即是嵌套区域入口时不再落进「`not contains_block` ⇒ return True」路径：只读本区域块集成员关系。
   消费者：`wizard_quant_api::params_analysis`（官方 52→53，B4 交付）。
2. **`[R68-b2 and-chain]`** — 短路链段边界由「首个未访问、非本块条件跳转的后继」确定（只读本块
   `successors`）：AST 形状 `[entry, seg1, seg2, …]`，每个合取支一个子节点。
   消费者：`klinedata::get_all_real_daily_kline`（B2 交付）。
3. **`_then_exit_succs` `[R68-diag5]`** — 嵌套区域之后的语句永久从 AST 消失的那处：以该臂出口集与
   `_chain_merge_candidates` 求交、唯一后继时把 `If.body` 补成 `[Try, …, Return]` 完整序列。
   消费者：同上（`params_analysis`）。
4. **`[R68-B]`** — 外部性判定（异常边经 `exception_successors` 排除）：收集块存在集外且不在 `stop` 内的
   前驱，逐点迭代剪枝至收敛，再取 `entry` 可达性收敛；被剪除块回归其真实父级。
5. **`[R68-E·有 merge 收集的剪枝守卫]`** — `entry`/`pred` 支配关系守卫：跳过该块的外部前驱剪枝，
   体内块留在本臂末尾（避免「每块唯一归属」被破坏）。
6. **`[R68-C·循环豁免收紧]`** — 子结构是外层循环体时**取消**循环豁免，让外部前驱剪枝正常生效，
   被挡下的后继块回归真实父级顶点序列按偏移补发。

第 4–6 条来自 B1（`cand_r68_b1.json`），消费者是 `matcher::match`（官方 16/17 → **17/17**）。

**region_ast_generator.py（11 edits）**

1. **调用点（`_loop_handle_no_exit_successors` 内 `if not _then_is_continue:` 块）`[R68-b3 修复]`** —
   循环头条件 break 的 then 臂续接块折叠：先查 `get_entry_region_for_block`，只在「该区域已生成
   （`id in _generated_regions`）且其块全部已登记」时折叠；三要素写在同函数下方 helper
   `_fold_header_then_continuation` 的 docstring（L10509，`[R68-b3 修复]`），调用点以 `_r68_*` 变量名标识。
   消费者：`trade_info_utils::get_trade_list`、`logger`（B3 交付）。
2. **`_loop_build_if_with_exit_branches` `[R68-b3 修复]` + `[R68-diag6/b5 init-if fold]`** — 出环臂归约
   `_r68_branch`：then/else 共用同一条出环臂归约；非出口块若本身是可折叠区域入口则整棵生成并折叠。
3. **`[R68-b2 cell-swap]` ×2** — 值段中的 `SWAP` 只换栈位不产生值：先从值段剔除再由既有 C2 归约
   `N→STORE` 整体归约；目标按 `STORE` 源序（不反转）、值仍取表达式栈栈序。
   消费者：`klinedata` 的元组/下标支（B2 交付）。
4. **`[R68-D4-ORCHAIN-TAIL]`** — 测试语境 or-chain 末段重组：把 `b1..bn` 折成 `BoolOp(or, parts)`
   作为前段、末段单列，产出 `If(test=BoolOp(and,[BoolOp(or,[…]), tail]))`。
5. **`[R68-diag3 C3]`** — `IfRegion` 的 `merge_block` 是纯回边块且非本循环登记尾块 ⇒ 显式 `Continue`
   作为 `if` 结果的**兄弟语句**追加；标签缺失（`None`/空表）时不发。
6. **`[R68-diag6]` ×2、`[R68-diag6/b5]`、`[R68-diag6/b5 init-if]`** — merge 末尾 `RETURN`/`GET_AWAITABLE`
   轮询两条通路的 `Return(_merge_consumer_expr)` 并入本语句发射（记入 `generated_blocks` 杜绝重复）、
   模式 A2-AS（`SWAP, POP_EXCEPT, LOAD_CONST, STORE_FAST, DELETE_FAST, RETURN_VALUE` 既不短缺也不溢出
   才走该通路）、以及兄弟切片栈深反向游走表补上缺的 1 项键。

**禁止形态核对**：17 处编辑全部只读本区域/本块自身字段与本块自身指令序列；
`grep -c 'region.entry in r.blocks'` 型跨层包含 **HEAD=2 / WORK=2（analyzer）、3 / 3（generator）、
0 / 0（comprehension）——全部为 HEAD 既有、本轮 0 新增**（`logs/gate/G0_syntax_form_r68.txt`）；
无函数名/文件名片段/偏移/阈值启发、无新增 `self` 状态、无按名字白名单。

## 4. 串行门禁（严格串行，逐条见 `logs/gate/`）

| 门禁 | 读数 |
|---|---|
| G0 语法与形态 | `ast.parse` + `py_compile` 全 OK；analyzer 1 753 093 B / sha `27089306098c35dc1f3a` / 裸 LF 0 / 27 998 行；generator 3 193 950 B / sha `3cd0fcd6cbd7446c3703` / BOM 有 / 裸 LF 0 / 51 310 行；comprehension 未改；跨层模式 0 新增 |
| G1 完全 OK 靶 1 | `scheduler` 官方 **45/45 100.00%**、`missing/extra` 皆空、严格 **52/52 bad=[]** |
| G1 完全 OK 靶 2 | `flyAccount` 官方 **23/23 100.00%**、`missing/extra` 皆空、严格 **23/23** |
| G2 金丝雀 | 4 支产物 sha 与 R67 归档**逐字节相同**：`4d41187e356544e0`（quotation）、`af77224b34b203c4`（market_time）、`e711b8ea86d49a15`、`9d09af09249da177`（datetime_func ×2）；官方 **143/143、10/10、26/26、25/25** |
| G2 严格金丝雀 | **209/211**，余 2 = `quotation::change_his_to_forward #250`、`quotation::get_trend #10`，缺陷集**逐字同 R67** |
| G3 批量 | `batch --index pyc_index.json --all --round 68` → **402 verified / 0 failed**、ok 392、partial 10 |
| G4 `stats` | **5746 funcs / 5709 matched / 99.36%**（轮初 5701 / 99.22%）⇒ matched **+8**、完全匹配文件 **387→392** |
| G4′ 严格尺（发布产物，15 支） | **641/700**（轮初 632/700、缺陷函数 68→**59**）；FIXED 13、NEW 4 全为**既有缺陷函数换 kind**、无新增缺陷函数 |
| G5 索引审计 | 402→402 条目、added=0 removed=0、key-shape 0、round-stamp-only=395、**substantive=7 且全为改善** |
| G5′ 产物 blast | `identical=388 changed=14 unresolved=0`；Σ\|Δ\| **296→256**；matched 5701→5709；完全匹配 387→392；improved=7、**regressed=0**、moved=7 |
| G6 电池 | 45 项 `174/200 → 182/200`、缺陷函数 `26 → 18`（fewer 6、equal 39、**WORSE 0**）、errors=0 |
| G7 见证（本轮 28 支） | `SAME=16 IMPROVED=10 REGRESSION=0 MOVED=2 ERR=0`，完全匹配 **10 → 20** |
| G8 产物体检 | 402/402 `*OK.py` 在位（missing 0）、`py_compile` bad=0（仅既有 SyntaxWarning）；G3 日志 `FAIL/Traceback` 0 命中 |

G6 的真基线列由 `mkmirr_prev68.py` 建 `center/mirr_prev`（R67 HEAD blob + LF→CRLF 复原，
generator 3 153 249 B `f712bc20d7ad44542e18`、analyzer 1 742 308 B `af8cc88b9f89779b3ef0`、
comprehension 108 192 B `be5490c1118c7199fe0a` 三支指纹命中 R67 提交记录），落地后
`landed` 臂与 R67 字节可区分，电池因此读到真实前后差。

**索引 substantive=7 逐支**（`logs/gate/G5_index_audit_r68.txt`）：`klinedata` 42→43、
`wizard_quant_api` 52→53、`trade_info_utils` 38→39、`matcher` 16→17、`scheduler` 44→45、
`logger` 29→30、`flyAccount` 21→23 —— 与五批单臂读数逐支吻合。

## 5. 五批判定（集中验证：采纳 5、回退 0）

| 批 | 工作区 / 名下靶支 | 交付 spec（采纳） | 单臂实测消费者 |
|---|---|---|---|
| B1 | `diag1`：`trade_live_broker` | `cand_r68_b1.json`（analyzer 3 edits：`[R68-B]`/`[R68-E]`/`[R68-C]`） | **`matcher` 16→17/17**（B1 名下靶支 `trade_live_broker` 108/119 未动，如实记为旁支收益） |
| B2 | `diag3`：`klinedata` 等 3 支 | `cand_r68b2_andchain.json`（analyzer 1）+ `cand_r68b2_final_gen.json`（generator 3） | `klinedata` 42→**43**/45、`scheduler` 44→**45**/45（全清） |
| B3 | `diag4`：`trade_info_utils` 等 3 支 | `cand_r68b3_combo.json`（generator 4） | `trade_info_utils` 38→**39**/40、`logger` 29→**30**/30（全清） |
| B4 | `diag5`：`real_quote` 等 3 支 | `cand_r68_wizapib.json`（analyzer 2） | `wizard_quant_api` 52→**53**/53（全清）；`api_base::get_history_df` [1742,1740,14,1263] → [1742,1742,11,89] |
| B5 | `diag6`：`order_api` 等 3 支 | `cand_r68b5_initc.json`（generator 4） | `flyAccount` 21→**23**/23（全清） |
| （diag2） | `quote` + `matcher` | `cand_r68_else_join_cut.json` —— **自行撤回**（ADR-1 实测） | 未进合并集 |

五支单臂均在 15 支合集上 `REGRESSION=0`、金丝雀 `SAME=4`、电池无 worse；合并后
`m68` 一次过 G0–G7，无二次回退。`test_repros/round68_diag{1,3,4,5,6}/`（28 支见证 + README）
与 `batches/{b0_diag2,b1_diag1,b2_diag3,b3_diag4,b4_diag5,b5_diag6}/`（FACTS/specs/synth，`b0_diag2`
为撤回件留档）为各批凭据。

## 6. 尺子分歧与副作用裁定（如实记录）

- **`matcher::match` 官方 vs 严格**：官方 17/17 计入匹配（跳转容差吸收 6 条布局相关跳转地址，
  非跳转 token 序列逐字相同），严格尺仍报 `target_diff #192`（终点 `LOAD_FAST 'order'` vs `'self'`）。
  按 ADR-1 第 2 条属「同一函数换 kind」，**不计新增缺陷函数**；本轮旗舰因此不取 matcher，
  而取 `scheduler`/`flyAccount`（双尺全清）。新 kind 已记入 §4 G4′ 的 NEW=4。
- **`fileio_utils::write`**：`[637,637,4,519] → [637,636,0,38]` —— `Σ|Δ|` 0→1（唯一上升支），
  但 hunk `4→0`、true-diff `519→38`、文件仍 12/14；严格 kind `seq_diff → seq_len`（缺陷数不变）。
  按 ADR-1 第 2 条（hunk 数严格下降 + `first_diff` 回移 + 不得新增 `target_diff`）判**改善后仍红**，
  不构成回退；官方尺与严格尺对该支的读数差异已留档。
- **4 支「读数逐字相同但产物文本变」**：`api_data`、`resource_utils`、`function`、`quote`
  —— 严格缺陷集合完全一致，仅 `*OK.py` 文本随重排/轮次戳变化，`blast` 计入 `moved` 不计 `improved`。
- 45 项电池 `worse-than-landed=0`、15 支 `REGRESSION=0`、28 支见证 `REGRESSION=0`、
  402 批量 `failed=0` —— 无一例回退，故本轮**回退 0 件**。

## 7. 残余 10 支 partial（gap 合计 37 个函数）

| 家族 | 涉及（官方读数） | 已知证据 |
|---|---|---|
| **位移 / 线性化通道**（整段搬到函数尾，零语句增减） | `real_quote` 40/44、`klinedata` 43/45（余 `kline_datetime_list`、`get_multiminute_his_data`）、`quote` 70/81 | 归一化 hunk 表；[[project-r66-displacement-family-lead]]；本轮 B1/B2 只清了同族的头两支 |
| **try/loop-exit JUMP_FORWARD + IMPORT_FROM-as-value** | `risk_calculation/__init__` 33/35、`realtime_event_source` 11/12 | 三签名纠缠（`JUMP_FORWARD`↔`LOAD_CONST None/RETURN_VALUE` 互换）；见 [[project-r47-try-body-return-guard]] |
| **R50 kwarg 槽位 bail / 臂体空化** | `order_api` 32/34 | `_try_build_ternary_kwarg_call`；`base_order` 严格 `target_diff #136` 为常量↔LOAD 消费点错位 |
| **多 hunk 大文件残余** | `trade_live_broker` 108/119（11 gap、17 严格缺陷） | 本轮 B1 未动其名下靶支；`_process_order` orig 454 vs decomp 396 为最大单支 |
| **改善后仍红** | `fileio_utils` 12/14、`trade_info_utils` 39/40、`api_base` 24/25（`get_history_df` 11 true-diff） | §6 裁定，均属同一函数 kind 变化，无新增缺陷 |

## 8. 下一轮（R69）线索

1. **位移族仍是最大矿**（`real_quote` 4 + `klinedata` 2 + `quote` 部分）：B1 的剪枝判据已证明
   「块归属层」可一次修多支；下一步应把 `first_diff` 回移判据做成生成器侧的线性化通道，
   起点是产物尾部整段插入点与 `_loop_build_if_with_exit_branches`（L10479 区）的调度顺序。
2. **`matcher::match` 的 `target_diff #192`** 是本轮最大「官方尺看不见」的语义残留：
   `if not (A and B)` 的极性归属，应在 or-chain 折叠处（`_generate_if` /
   `_build_ternary_boolop_condition` 路径）保持极性；同时值得给官方尺加「jump-target 常量身份」检查。
3. **`trade_live_broker` 名下 11 gap 尚未开工**（本轮 B1 改道去修 matcher）：`_process_order`
   396/454、`after_trading_cancel_order`、`etf_basket_order` 三支是最大缺口，且该文件在 G5′ 中
   读数已改善（td 1739→1559）⇒ 先读它当前 hunk 表再定批次。
4. **`order_api` / `risk_calculation`** 的 try 尾 JUMP_FORWARD 族与 B5 的 init-if 折叠判据可能同源：
   `_loop_build_if_with_exit_branches` 的出环臂归约已能处理「非出口块折叠」，可测试把 try 尾
   `JUMP_FORWARD` 也交给同一条 `_r68_branch`。
5. **技术债**：generator 内 `_os_dbg_*` 调试导入仍需清理（[[project-r65-debug-import-cleanup]]，
   402 惰性噪声移除，不得当收益报告）；B3 的 then-fold 调用点无独立 `[R68-*]` 行内标签
   （三要素在 helper docstring），下轮补标签时须连带重跑 G0–G3。
6. **电池与见证**：45 项电池已 182/200、缺陷函数 18；本轮 28 支新见证（`round68_diag*`）
   已入库并会在 R69 电池自动纳入，继续按 `fewer > equal、WORSE=0` 判门。
