# Round 67 · diag5 · FACTS (running record)

**Status: COMPLETE** — step 0/1/2/3/4/5 全部落地在本文件；交付一份生成器 spec + 一份 analyzer 后续步 spec。
**TL;DR**：名下主靶 `r66d3_pred::v6` 的同层拆分需要**两步**（生成器半边 + analyzer 半边），单文件规则下
本批只能先交生成器半边（它有 5 支独立 witness、在 54+16 支被测文件上 0 回归）；两步合成的 pair 已实测
**r66d3_pred 2/3 → 3/3**。见文末 FINAL 段。

## Step 0 · baseline replay (--arm=landed) — ALL MATCH BRIEF, no drift
- targets (10.2 s): real_quote 40/44 mism=[[get_cache_l2_data_by_one,321,322,2,197],[get_real_minute_kline,253,254,3,197],[get_tick_direction,259,258,3,102],[one_prod_to_ndarray,605,607,5,424]];
  order_api 32/34 mism=[[future_order,101,92,2,36],[option_order,83,73,3,39]]; scheduler 44/45 mism=[[run_daily,77,71,0,56]]  → byte-identical to targets.md.
- battery (7.6 s): 31 items, total **115/127**, 12 defect functions — identical line-by-line to the brief table, incl. `round66_diag3/r66d3_pred.pyc 2/3 [['v6',36,34,2,16]]`.
- canary: quotation 143/143 sha=4d41187e356544e0; market_time 10/10 sha=af77224b34b203c4; IQCommon/util/datetime_func 26/26 sha=e711b8ea86d49a15; IQData/utils/datetime_func 25/25 sha=9d09af09249da177 — all 4 shas identical.
- Dumps: dump/landed.jsonl, dump/landed_batt.jsonl, dump/landed_canary.jsonl; products in build_landed/.

---
# 主要发现（一句话）
落地字节上存在一个**与 analyzer L20949 判据无关、独立可复现、纯生成器侧**的语句丢失族：
「值语境链式比较三元（TernaryRegion + chained_compare_ops>=2）的条件块带前导已完结语句」——
`_generate_ternary` 的 Phase-7-D 分支（generator 落地 L35031-35045）用
`_build_chained_compare_from_region_data` 直接由**区域数据**建 Compare，**完全绕开**了
同函数 `else` 分支（L35070+）里那套 pre_stmts 前导语句扫描，于是块内前导语句无人发射。
这正是 v6 需要的「同层拆分」的**生成器那一半**，且它不需要动 analyzer 就能独立成立。

## 证据链（全部实测，landed = 当前工作树）

### E1 · landed 上该形状的独立复现（无需碰判据 (d)）
`synth/r67_ccprefix.py` → w1..w4；`synth/r67_ccprefix2.py` → w5/w6；`synth/r67_site2.py` → c1..c6。
landed 读数（`dump/landed_synth.jsonl`）：
```
r67_ccprefix.pyc  1/5  [['w1',36,34,2,16],['w2',31,29,2,26],['w3',36,30,2,32],['w4',32,27,1,26]]
r67_ccprefix2.pyc 1/3  [['w5',41,39,1,39],['w6',51,50,5,24]]
r67_site2.pyc     3/8  [['<lambda>',20,3,0,19],['c1',39,37,2,15],['c3',44,42,1,38],['c5',33,11,0,32],['c6',38,36,3,25]]
```
w2/w3/w4/w5/c6 的头块**都不是 CFG 入口块**（在 if-body / try-body / elif 臂内），
所以 R66-diag3 的合取 (a) 根本不成立 → 三元区域照常建出 → 前导语句 `k = 1` / `m = k + 2` /
`f(dc)` 整段丢失（见 `build_landed/...r67_ccprefixOK.py`）。⇒ **该缺陷与判据 (d) 无关，是生成器侧独立缺陷。**

### E2 · 判据 (d) 的现状读数（单变量：只动 analyzer）
`specs/probe_noD.json`（删除 (d) 那三行，analyzer-only）：电池 31 项
`SAME=30 IMPROVED=0 REGRESSION=0 MOVED=1`，v6 `[36,34,2,16] -> [36,34,1,34]`，
产物 = `dc = int(dc) if 0 < int(dc) <= 200 else 200` 且 **`k = 1` 消失**（34 vs 原 36，缺 2 条）。
⇒ 证明 (d) 当初的立论成立：撤销后生成器不发射前导段。整体删除 (d) 不可落地。

### E3 · 生成器侧候选（本批交付 spec）
`specs/cand_r67_ccprefix.json`（**generator-only，2 edits**，文件
`core/cfg/region_ast_generator.py`）：新增
`_r67_split_cc_ternary_stmt_prefix(region, pre_stmts)`，在 Phase-7-D 分支
`_r63b3_reduce_value_ctx_chain_store(...) is None` 之后调用；helper 复用
`_split_block_condition_prefix`（与 Assert / 旋转 while / R63-b3 **同一条划界**）+
`_build_statements_from_instructions` + 既有 `results = list(pre_stmts)` 发射通道。
锚点 count 均 == 1（A_DEF/A1 各 1，实测打印）。

| 量表 | A/B（vs landed） |
|---|---|
| targets 3 支 | SAME=3 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0 |
| battery 31 项 | SAME=31 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0（115/127 不变，24 支全对齐不变）|
| canary 4 支 | SAME=4（sha 逐支不变：4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177）|
| synth 3 支（16 个函数）| **IMPROVED=3 REGRESSION=0**：1/5→4/5、1/3→2/3、3/8→4/8 |

被修好的合成函数：w2 w3 w4（前导 1/2 条赋值 + 表达式语句）、w5（try 内）、c6（elif 臂内）。
仍失败：w1(=v6，需 analyzer 后续步)、w6/c1/c3/c5/`<lambda>`（另属他族，见下）。

**发射点计数实测（谁在真正消费本判据）**：在 probe arm `mirr_probe_site`（=3 编辑版 + 打印）
上跑遍 43 支被测文件（31 电池 + 3 靶支 + 4 金丝雀 + 1 合成），helper 共触发 **3 次，
全部来自站点 1（Phase-7-D 分支，patched L35102）**；站点 2（R106 补判分支，L35124）**零触发**。
⇒ 交付收紧版（2 编辑，只挂站点 1）；宽版（3 编辑，含 R106 站点）
`specs/cand_r67_ccprefix_wide.json` 在同一 43 支上读数**逐支相同**（SAME=31/4/3），
中心可按取舍偏好二选一，但宽版在 402 上无 witness 支撑。

### E4 · v6 需要两步（analyzer 后续步已写好并实测）
`specs/cand_r67_dsplit_analyzer.json`（**analyzer-only**）：把判据 (d) 的
「块内任何位置有 STORE_*/POP_TOP ⇒ 整体拒绝」换成「按块自身栈深归零点划出
**表达式段**，只有表达式段内含 STORE_*/POP_TOP 才拒绝」（只放宽、不收紧：
原 (d) 的成立条件被完整保留为外层 if；栈效应不可得/下溢 ⇒ 退回落地行为）。
实现用 `dis.stack_effect`（须在该处 **局部 `import dis`** —— region_analyzer 模块级没有
`import dis`，第一版漏掉导致 NameError 被上层吞掉、产物退化成 `if 0 < int(dc): if 200: pass`
式垃圾；这是一个**必须写进轮次的教训**：analyzer 里用 dis 必须局部导入）。

| 步 | r66d3_pred.pyc | 电池 | 金丝雀 | 靶支 |
|---|---|---|---|---|
| analyzer (d') 单独 | 2/3（v6 `[36,34,2,16]→[36,34,1,34]`，`k=1` 仍丢）| SAME=30 MOVED=1 REGRESSION=0 | SAME=4 | SAME=3 |
| **pair**（generator 候选 + analyzer (d')）| **3/3 —— v6 全对齐** | SAME=30 **IMPROVED=1** REGRESSION=0 | SAME=4 | SAME=3 |
| synth 3 支（pair）| 1/5→**5/5**、1/3→2/3、3/8→4/8 | | | |

⇒ **单文件规则下 v6 本批不可闭**：pair 才能把 `r66d3_pred` 推到 3/3，而 generator-only
在 landed 上对 v6 完全惰性（analyzer 仍拒绝建区域）、analyzer-only 则是**丢语句**。
两条都是实测，不是推断。落地次序必须是 生成器先行 → analyzer 后随（R68）。

---
# Step 1 · 归一化 hunk 表（landed，`nhunks.py --ctx=0`，全表存 `logs/nh_<fn>.txt`）

## real_quote.pyc（40/44，strict 41/45）
| 函数 | orig/decomp(归一后) | 归一化实质 hunk | 判定 |
|---|---|---|---|
| `get_cache_l2_data_by_one` | 355/356（官方 321/322）| 1 条：`insert orig[134:134]@584(0) decomp[134:135]@588(1)`（内容 = `EXTENDED_ARG`）| **纯位移副产物**：产物里跳距跨过 255 多出一枚 `EXTENDED_ARG`，无语义语句增减 |
| `get_real_minute_kline` | 280/287（253/254 官方）| 6 条，主项 `delete orig[65:100]@356(35)` + `insert orig[252:252]@1308(0) decomp[221:259]@1104(38)` | 35 条整体被搬到函数尾 ⇒ **发射次序/线性化通道**，非归属判据 |
| `get_tick_direction` | 297/299（259/258 官方）| 3 条，主项 `delete orig[172:202]@942(30)` + `insert orig[297:297]@1572(0) decomp[268:299]@1412(31)` | 30 条搬尾，与上一轮「纯位移」读数一致（本次实测复放）|
| `one_prod_to_ndarray` | 659/665（605/607 官方）| 7 条：5 条 `replace 1→2`（全是 `EXTENDED_ARG` 追加）+ `delete orig[389:423]@1418(34)` + `insert orig[201:201]@792(0) decomp[208:237]@846(29)` | 同一位移族 + 跳距副产物 |
⇒ **候选：NONE（本批名下不可闭）**。四支的 counts 差全部由「整块语句段被搬到函数尾」+「随之而来的 `EXTENDED_ARG` 长度位」构成，**没有任何一条缺失/多余语句**，归属判据在此无用。
排除读数：`get_tick_direction` 删 30 @942 / 插 31 @1412（同一段的跳转目标归一后同为 `J`，逐指令内容一致）；`get_real_minute_kline` 删 35 @356 / 插 38 @1104。
按 BRIEF 指路与 [[project-r64-matcher-displacement-lead]]，该族只能在**生成器重排/线性化通道**统一处理（一处修四支），按文件分头做判据必然是取巧。

## order_api.pyc（32/34，strict 33/36）
| 函数 | 归一后 | hunk |
|---|---|---|
| `future_order` | 115/107（官方 101/92）| `delete orig[72:80]@414(8)`、`delete orig[89:90]@552(1)`、`replace orig[91:92]@556(1) decomp[82:87]@484(5)`、`delete orig[104:109]@632(5)`、`insert orig[115:115]@688(0) decomp[105:107]@634(2)` |
| `option_order` | 94/85（官方 83/73）| `delete orig[39:43]@206(4)`、`replace orig[44:47]@254(3) decomp[40:50]@208(10)`、`insert …@352(1)`、`replace …@352(1)→@356(1)`、`delete orig[63:73]@394(10)`、`delete orig[85:88]@510(3)` |
| `base_order` | 200/200 | **归一化后 0 条实质 hunk**（官方 34/34 亦 OK）；strict 的 `target_diff #136 POP_JUMP_IF_TRUE 终点` 是 **常量↔LOAD 配对**差异（orig `('order_obj', LOAD_FAST)` vs decomp `(长 f-string 常量, LOAD_CONST)`），被 nhunks 的 `J`/常量归一吸收 ⇒ 纯**栈槽位配对**问题，不是语句增减 |
⇒ 与 R50 归档一致：三支都是 **kwarg 槽位上的三元被 bail**（`_try_build_ternary_kwarg_call`），
实测行号已漂移，当前 landed：（见下 grep 读数）。`base_order` 的 strict 差异说明 bailed 的三元被
降级成语句后**改变了 merge 块的栈占用**（`'order_obj'` 的 LOAD 被常量顶替）。

## scheduler.pyc（44/45，strict 50/52）
`nhunks.py` 对 `run_daily` / `func_wrapper` **直接断言失败**：
`AssertionError: [72, 255]` / `[262, 437]` —— 该 pyc 里同名 code object 各 2 个
（`.<module>/run_daily@72`、`.<module>.Scheduler/run_daily@255`、
`Scheduler.run_daily/func_wrapper@262`、`Scheduler.run_interval_trade/func_wrapper@437`）。
⇒ 归一化 hunk 表对这两支**不可用**（工具层限制，记录）。
`run_daily`：BRIEF 与 [[project-r65-diag5-leads]] 第 3 条已判「cellvar 降级、区域层之外」，本批**未攻**（遵守禁令）。
`func_wrapper` 只有 strict `[seq_len] 219/215`（官方 44/45 内已 OK）⇒ 归一化后同尺寸，属 cellvar/免费变量降级族，与 `run_daily` 同因。

---
# Step 2 · 落地字节归因（全部 `grep -n` 实测，非上一轮旧行号）

## 交付候选 `cand_r67_ccprefix`（生成器侧）
`F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py`（landed 行号）：
- L34785 `def _generate_ternary(...)` —— 唯一消费方；helper 插在其**之前**（anchor = 该行本身，count==1）
- L35031-35033 Phase-7-D 分支的**结构判据**（`chained_compare_ops>=2 ∧ chained_compare_blocks`）—— 本候选的挂载点
- L35038 `cond_expr = self._build_chained_compare_from_region_data(region)` —— 由**区域数据**建 Compare，**不扫指令**
- L35041-35045 `_r63b3_reduce_value_ctx_chain_store(...)` / `if _r63b3_stmts is not None: return`（= 本候选 anchor A1，16 空格缩进，count==1）
- L34693 `def _r63b3_reduce_value_ctx_chain_store` —— 其内部 L34766-34778 已在**同一分支**上做前导段拆分
  （`_split_block_condition_prefix` + `_build_statements_from_instructions` + `pre_stmts.extend`），
  但只在「两臂都是链自身短路结构」时进入；真三元值臂 ⇒ `_r63b3_is_chain_cleanup_arm` 为假 ⇒ 早退，前导段无人发射。**这就是缺陷点。**
- L35070+ `else:` 分支（普通三元）才有那套 pre_stmts 扫描（L35130-35580：`POP_TOP` 分支 L35326、
  `STORE_*` 分支 L35457、`[R62 Fix1]` L35247、`[R94 fix]` L35321）—— Phase-7-D 分支整体绕开它
- L35790 `results = list(pre_stmts)` —— 既有发射通道，本候选一字不改地复用
- L336 `def _split_block_condition_prefix`（同一条栈深划界，既有消费者：AssertRegion / 旋转 while LoopRegion / R63-b3）
- L27926 `def _build_statements_from_instructions`

同层次字段证据：helper 只读 `region.chained_compare_ops` / `region.chained_compare_blocks` /
`region.condition_block`（本区域自身字段）+ 该块自身的 `dis.stack_effect` 前向和，
**无** `region.entry in r.blocks` 型跨区域跨层次包含、无函数名/文件名/偏移/阈值、无新增 `self` 状态。

## analyzer 后续步 `cand_r67_dsplit_analyzer`（本批**不**作为交付 spec）
`F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py`（landed 行号）：
- L20932 `def _detect_ternary_pattern(block)`、L20948 `if not _can_be_ternary_header(block):`、
  L20949 `[R66-diag3 value-context chained-compare gate]` 注释、**L21026-21028 = 合取 (d)**
  （`if any(i.opname.startswith('STORE') or i.opname == 'POP_TOP' for i in block.instructions): return None`）、
  L21029 `_r66_saved = ...`（撤销三处）、L21041 复查 `_can_be_ternary_header` 并回滚
- L20253 `def _can_be_ternary_header(block)`（[R24-A] `self.entry is not analyzer.cfg.entry_block` 合取即 (a) 的来源）
- 实测坑：region_analyzer **模块级没有 `import dis`**（只有 L1869 `import dis as _dis`、L3709/L12388/L14020 函数内 `import dis`），
  在该处使用 `dis.stack_effect` 必须**局部 `import dis`**，否则 NameError 被上层吞掉 → 产物退化为
  `if 0 < int(dc): if 200: pass` 式垃圾（第一版实测即如此，`[36,28,0,29]`）。

## order_api 归因（未交 spec，读数记录）
- `_try_build_ternary_kwarg_call` def = landed **L43162**；唯一调用点 = landed **L38156**
  （`if _kwarg_call is not None: results.append(...); return results`）
- 函数内前三个 bail：L43178 `if not region.merge_block`、走链 while（L43189-43200）、
  L43214-43215 `if kw_names_instr is None or call_instr is None`
- `future_order` 实测丢的是**分支体里的日志调用语句**：`delete orig[72:80]@414(8)` =
  `LOAD_GLOBAL strategy_log / LOAD_ATTR info / LOAD_CONST f-string / LOAD_METHOD format / LOAD_FAST order_ …`
  整条 `strategy_log.info('生成订单…'.format(...))` 在产物里变成 `pass`
  （产物片段：`elif is_trade() or order_.entrust_direction.value.upper() == 'BUY': pass` / `else: """卖出"""`）
  ⇒ 与 `base_order` strict `target_diff`（POP_JUMP_IF_TRUE 终点常量↔LOAD 配对错位）**同一处**：
  臂体被空化 + 消费点错位，属 R50 kwarg-槽位 bail 族，**不是**位移族，也**不是**本批候选能覆盖的形状。

---
# Step 5 · 超出自检范围的额外回归样本（16 支全量缺陷文件，非 402 扫描）
`targets16.txt`（中心 `D:/Temp/opencode/r67gate/targets16.txt` 原样拷贝，16 支 / 官方缺陷 39 条）。
landed 跑完 31.7 s，候选 40.5 s，`dump/landed16.jsonl` / `dump/ccp16.jsonl` / `dump/pair16.jsonl` / `dump/da16.jsonl`：

| arm | 16 支 A/B vs landed |
|---|---|
| `ccp_final`（交付候选，generator 2 编辑）| **SAME=16 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0** |
| `pair`（候选 + analyzer (d')）| **SAME=16 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0** |
| `dsplit_a`（analyzer (d') 单独）| **SAME=16 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0** |

⇒ 三个臂在**全部 16 支已知缺陷文件**上产物 sha 逐支不变（含 `matcher.pyc::match` 715/715、
`trade_live_broker` 107/119、`api_base::get_history_df` 1742/1719 这些三元密集支）。
合并电池/靶支/金丝雀：**54 支被测文件、0 回归、0 位移**（产物逐字节相同 ⇒ 严格尺读数必然相同，
已对 3 支靶支实测 strict 亦逐条相同：41/45、33/36、50/52）。

# Step 3/4 · 交付清单
- 合成复现：`synth/r67_ccprefix.py|pyc|txt`（w1..w4）、`synth/r67_ccprefix2.py|pyc|txt`（w5/w6）、
  `synth/r67_site2.py|pyc|txt`（c1..c6）、名单合集 `synth/_all3.txt`。
  landed 上 5+3+8=16 个函数里 **9 支失败**；候选修好 6 支（w2 w3 w4 w5 c6 + r67_ccprefix 计数 1/5→4/5）。
  注：`cstrict.py` 的产物名推导只认 `site-packages/`，对 `synth/` 路径报 NO-PRODUCT（工具限制，记录）；
  合成件用官方尺读数。
- **交付 spec：`specs/cand_r67_ccprefix.json`**（单文件 `core/cfg/region_ast_generator.py`，2 edits，
  每个 anchor 在 LF 归一文本中 count==1，`h62 build` 实测通过并断言 head==worktree）。
  三要素注释在 `_r67_split_cc_ternary_stmt_prefix` 的函数体内。
- 同形宽版（同一 helper 也挂到 R106 补判分支，3 edits）：`specs/cand_r67_ccprefix_wide.json`
  —— 在 54 支上读数与收紧版**逐支相同**，且 R106 站点在 43 支 + 16 个合成函数上**零触发**
  （实测打印 `callsite=35102` × 3、`callsite=35124` × 0）⇒ 无 witness，不交付，供中心取舍。
- analyzer 后续步（**不在本批落地**）：`specs/cand_r67_dsplit_analyzer.json`。
  单独落地 = 丢语句（`v6 [36,34,2,16]→[36,34,1,34]`，`k = 1` 消失）；
  与交付候选一起落地 = `r66d3_pred.pyc 2/3 → 3/3`（`v6` 消失，电池 IMPROVED=1 SAME=30 REGRESSION=0，
  金丝雀 4 sha 不变，16 支不变，合成 `r66d3_pred` 全 3 函数 OK）。
  ⇒ 交给 R68 作为**第二步**，前置条件就是本批这条生成器判据先落地。

# 逐靶支最终判定
| 靶支 | 判定 |
|---|---|
| `round66_diag3/r66d3_pred::v6`（名下主靶）| 两步制：**第一步已成交付 spec**（生成器同层拆分，实测独立修好 w2/w3/w4/w5/c6）；**第二步 analyzer (d') 已写成 spec 并实测**，pair ⇒ v6 3/3。单文件规则下 v6 **本批不可闭**，实测证据见 E2/E4（analyzer-only 丢语句、generator-only 对 landed 的 v6 完全惰性）。|
| `real_quote` 残余 4 支 | **候选：NONE**。归一化 hunk 表实测：无语义增减，全部是「30/35 条整段搬到函数尾」+「`EXTENDED_ARG` 长度位」；counts 不等的两支是纯位移、`get_cache_l2_data_by_one` 是位移副产物。归**生成器线性化通道**统一处理，不属本批一条判据。|
| `order_api::future_order/option_order/base_order` | **候选：NONE（本批）**。丢的是分支体内 `strategy_log.info('…'.format(...))` 整条表达式语句（臂被空化成 `pass`）+ merge 块消费点常量↔LOAD 错位，正是 R50 `_try_build_ternary_kwarg_call`（现 landed L43162，唯一调用点 L38156）kwarg 槽位 bail 族；本批未找到不含函数名/偏移的同层判据，且无合成复现（不许提交 spec）。|
| `scheduler::run_daily` | **未攻**（BRIEF 禁令：cellvar 降级，区域层之外）。|
| `scheduler::func_wrapper` | **候选：NONE**。官方尺已 OK，只有 strict `[seq_len] 219/215`；与 `run_daily` 同因（cellvar/闭包变量降级），且 `nhunks.py` 因同名 code object ×2（@262/@437）无法出表。|

## 「判据在真实语料上是否咬合」探针实测（arm `probe_site` = 宽版 + 站点行号打印）
- 43 支（31 电池 + 3 靶支 + 4 金丝雀 + 1 合成）：helper 触发 **3 次，全部来自合成件
  `r67_ccprefix.pyc` 的 w2/w3/w4**（`callsite=35102 condoff=6 prefix∈{2,6,6}`）；
- 16 支已知缺陷文件（`targets16.txt`）：helper 触发 **0 次**；R106 站点（35124）合计触发 **0 次**。
⇒ 诚实结论（写给中心，别让读的人误判）：本候选在**我可达的全部样本上字节惰性**，
只有合成 witness 咬合。它的价值是「修掉一个已证明存在、且此前无任何发射方负责的语句丢失族」，
54+16 支 0 回归 + 金丝雀 sha 逐支不变 ⇒ 落地风险实测为 0；**语料净收益需中心 402 扫描定**
（若 402 上同样 0 咬合，则本候选是「安全但无收益」，中心可据此降级，而不是按回归处理）。

---
# FINAL（交付态，全部读数已在最终 spec 字节上重放确认）

## 交付
- **`specs/cand_r67_ccprefix.json`** —— 单文件 `core/cfg/region_ast_generator.py`，2 edits，
  anchor 各 count==1，`h62 build` 通过（BOM=True / CRLF / 插行断言通过）。
  注释三要素齐：识别条件 (1)(2)(3) / 归约方式 / AST 映射。
  最终重放（arm `ccp_final`，dump/f_*.jsonl）：
  `synth 3 支 IMPROVED=3 REGRESSION=0（1/5→4/5, 1/3→2/3, 3/8→4/8）`、
  `battery SAME=31 IMPROVED=0 REGRESSION=0`、`canary SAME=4（sha 逐支不变）`、
  `targets SAME=3`、`targets16 SAME=16`、strict(靶支) 41/45·33/36·50/52 与 landed 逐条相同。
- `specs/cand_r67_dsplit_analyzer.json` —— analyzer 第二步（**本批不落地**，单独落地会丢语句）。
- `mk_pair.py` —— 两步合成的可复放配方：`h62 build --spec=specs/cand_r67_ccprefix.json --dst=ccp_final`
  → `python -X utf8 mk_pair.py` → `h62 run --arm=pair …`。
  复放读数（最终版，`dump/pv_batt.jsonl`）：**`r66d3_pred.pyc 2/3 → 3/3`，
  TALLY SAME=30 IMPROVED=1 REGRESSION=0**；canary SAME=4；targets SAME=3；targets16 SAME=16；
  合成件 `r67_ccprefix.pyc 1/5 → 5/5`。⇒ **v6 的形状已被彻底解决，只是需要两步落地顺序。**

## 对 BRIEF 的更正 / 补充（4 条）
1. **行号**：BRIEF 写「analyzer 现 L20949 那条判据」。实测 L20949 只是该 gate 的**注释首行**；
   gate 体是 L20948-21053，而**合取 (d) 的实际拒绝语句在 L21026-21028**。按 L20949 动手会改错位置。
2. **前提更正（关键）**：BRIEF 把 v6 描述成「只差把 (d) 改成同层拆分」。实测两半：
   (i) 只改 analyzer（删 (d) 或 (d')）⇒ 三元建出但 `k = 1` 整段丢失（`[36,34,1,34]`），不可落地；
   (ii) 只改生成器 ⇒ 对 landed 的 v6 **完全惰性**（区域根本没建）。
   并且该生成器半边在 **头块不是 CFG 入口块** 的同族形状上**今天就在丢语句**（w2/w3/w4/w5/c6 五支 witness，
   与判据 (a)/(d) 无关）⇒ 它不是「v6 的附属步骤」，而是一条独立的落地缺陷，故本批交付它。
3. **陷阱（写给下一个用 analyzer 栈判据的人）**：`core/cfg/region_analyzer.py` **没有模块级 `import dis`**
   （只有 L1869 `import dis as _dis` 与 L3709/L12388/L14020 的函数内导入）。在该 gate 里直接写
   `dis.stack_effect` 会 NameError，且被上层宽 except 吞掉，产物退化成
   `if 0 < int(dc): if 200: pass` 式垃圾（实测 `[36,28,0,29]`）而不报错。必须局部 `import dis`。
4. **工具限制**：`nhunks.py` 按 `co_name` 唯一匹配，`scheduler.pyc` 有 2 个 `run_daily`（@72/@255）
   与 2 个 `func_wrapper`（@262/@437）⇒ 直接 AssertionError，出不了表（已记录，非绕过）。
   `cstrict.py` 的产物名只认 `site-packages/`，对 `test_repros/` 之外的合成目录报 NO-PRODUCT。

## 仓库零改动核验
`git status --porcelain -- core/ pycdc.py` → **空**；`git status --porcelain | grep -c "^ M"` → **0**。
`h62 build` 每次自带 `head mirror == worktree bytes` 断言，全部通过。本轮对仓库只读。
