# Round 70 · diag1 · FACTS（trade_live_broker.pyc）

臂命名：`r70diag1*`。仓库只读；写入仅在本目录 + center 下的 `mirr_r70diag1*` / `build_r70diag1*`。

## Step 0 · baseline replay（--arm=landed，R69 HEAD 5647e97b 工作树字节）

命令：
- `python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl`
- `python -X utf8 h62.py run --arm=landed --list=canary.txt --out=dump/landed_canary.jsonl`
- `python -X utf8 closeout69.py battery landed`（82 项见证）
- `python -X utf8 sstrict67.py build_landed targets.txt dump/strict_landed.json`

官方尺（targets）：

| 字段 | 实测 | targets.md 预读 | 相符 |
|---|---|---|---|
| matched/total | **109/119**（gap 10） | 109/119 | ✔ |
| mism 函数 | `_process_cancel_order`(294,293,16,22)、`_process_order`(454,396,9,349)、`_sync_worker`(349,347,0,296)、`_trade_status_handle`(114,112,0,107)、`etf_basket_order`(693,693,11,216)、`etf_purchase_redemption`(377,369,1,37)、`get_max_amount`(201,213,2,18)、`ipo_stocks_order`(1075,1075,18,278)、`on_order_response`(445,444,6,57)、`on_trade_response`(392,391,6,57) | gap 10 | ✔（10 个） |
| ERR | 0 | 0 | ✔ |

金丝雀（sha / matched）：

| pyc | sha | m/t | 合同 | 相符 |
|---|---|---|---|---|
| fly/data/quotation.pyc | `4d41187e356544e0` | 143/143 | 同 | ✔ |
| fly/common/market_time.pyc | `af77224b34b203c4` | 10/10 | 同 | ✔ |
| IQCommon/util/datetime_func.pyc | `e711b8ea86d49a15` | 26/26 | 同 | ✔ |
| IQData/utils/datetime_func.pyc | `9d09af09249da177` | 25/25 | 同 | ✔ |

严格尺（`sstrict67.py build_landed targets.txt`）：**strict 107/123 / missing=0 / extra=0 / defects=16**，
16 条明细与 targets.md 逐条相同（kind/orig/decomp 计数与跳转信息一致）：
`_process_cancel_order[seq_len] 295→297`、`_process_order[seq_len] 454→399`、
`_process_tick_order[target_diff] #27`、`_sync_worker[seq_len] 350→347`、
`_trade_status_handle[seq_len] 114→112`、`etf_basket_order[seq_diff] #254`、
`etf_purchase_redemption[seq_len] 379→369`、`get_ipo_stocks[target_diff] #189`、
`get_max_amount[seq_len] 201→213`、`ipo_stocks_order[seq_diff] #624`、
`on_order_response[seq_len] 449→448`、`on_order_response_list_handle[target_diff] #23`、
`on_pre_before_trading_start[target_diff] #4`、`on_trade_response[seq_len] 396→395`、
`on_trade_response_list_handle[target_diff] #23`、`rzrq_credit_order[target_diff] #406`。

82 项电池（closeout69 battery landed，本轮基线列）：**全部有读数、ERR=0**；带缺陷的见证（landed 自身）：
`r63b2 probe_cases 7/9 bad2`、`probe_cases2 7/9 bad2`、`r65_trytail 8/9 bad1`、`fs2 6/10 bad4`、
`r67d4_controls 7/8 bad1`、`r67_ccprefix2 2/3 bad1`、`r67_site2 4/8 bad4`、`r67d6_boolop_ternary 5/6 bad1`、
`boolop_ternary2 6/8 bad2`、`m_r68 17/18`、`s_r68 8/11 bad3`、`xp_atco 6/7`、`xp_atco2 6/8 bad1`、
`r68_big_sinkreturn 1/3 bad2`、`r68b3_headif 4/7 bad3`、`r68b4_apib_inc6 1/2 bad1`、
`r69d1_gma 1/2 bad1 d=+12`、`s_polarity 1/2 bad1`、`r69diag4_orchain 2/6 bad4`、`try_A 1/2 bad1`。
⇒ 电池基线（landed）**worse-than-landed=0 自身恒 0**；候选须复现 82 项 0 变差。

**Step 0 结论：与 targets.md / BRIEF 预读逐字段相同，无需更正。**

## Step 1 · hunk 表（nested_diff.py，按 code-object 全路径配对；产物 = build_landed 的 OK.py）

命令：`python -X utf8 nested_diff.py <pyc> <OK.py> <name-filter>`（输出见 `dump/nd_<fn>.txt`）。
官方尺 gap 10 支全部有 hunk；另有 6 支只在严格尺报（官方尺计为 matched），`*_list_handle` 两支也打出 hunk。

| # | code object | orig/decomp | hunks | 归类 | 归一化 hunk 要点 |
|---|---|---|---|---|---|
| 1 | `_process_cancel_order#24` | 344/344 | 5 | 真缺陷（循环尾位移） | `NOP` 伪影(7:8)；`JUMP_FORWARD`→`RETURN None`(269)；`EXT+JUMP_BACKWARD`(301:303) 平移到 323:325；尾 `EXT+JUMP_BACKWARD`(342:344)→`RETURN None` |
| 2 | `_process_order#22` | 520/**464** | 27 | 真缺陷（语句族丢失） | 丢 `strategy_log.error('可转债代码…')`(110:121)、`strategy_log.info('生成订单…')`(275:290 / 352:360)、期权/期货两串 format 尾(298:445)；`JUMP_BACKWARD`→`JUMP_FORWARD`×3；尾 `EXT+JUMP_BACKWARD`→`RETURN None` |
| 3 | `_sync_worker#34` | 412/410 | 8 | 真缺陷（大块位移+丢失） | 丢 53:94（`is_trading_date(datetime.now())` 一整段）与 **239:404（165 条）**；decomp 侧 99:296 整块前移；`COMPARE_OP`/`POP_JUMP` 方向与配对错位 |
| 4 | `_trade_status_handle#35` | 130/126 | 3 | 真缺陷（丢语句 + while/else 位移） | 丢 7:17 = `self.trade_info = get_trade_status(self.trade_id, True)`（含 `NOP` 伪影）；decomp 112:118 插入 while 条件复检；尾 128:130 `EXT+JUMP_BACKWARD`→`RETURN None`（`time.sleep(0.5)` 被发到 `while…else`） |
| 5 | `etf_basket_order#56` | 769/769 | 2 | 纯位移（move） | `strategy_log.warning('该股票【%s】行情数据异常')`+`return None` 由 orig[274:285] 移到 decomp[516:527]（+ 前置 `JUMP_FORWARD` 丢失） |
| 6 | `etf_purchase_redemption#57` | 427/**415** | 5 | 真缺陷（格式化串重建） | 383:395 三条 `strategy_log.info(...)` 被压成单一 `LOAD_CONST` 拼接串、丢 `.order_id`/`.symbol`；411:418 丢 `CALL/POP_TOP/LOAD_FAST order` |
| 7 | `get_max_amount#64` | 218/**233** | 1 | 真缺陷（块重复发射 +15） | decomp[212:227] 整块 `JUMP_FORWARD + max_amount=int(float(result[0].get('enable_buy_amount')))` **多发一次**（orig 该处为 `out_info[sid]=max_amount; return out_info`） |
| 8 | `ipo_stocks_order#84` | 1206/1208 | 7 | 位移/伪影（EXTENDED_ARG + 跳向） | `EXTENDED_ARG` 进出 4 处；656 `JUMP_FORWARD`→`EXTENDED_ARG+JUMP_BACKWARD`；686/810 反向；1028 `JUMP_FORWARD` 丢 |
| 9 | `on_order_response#36` | 511/**509** | 3 | 真缺陷（结构位移 R57-E）+ 2 伪影 | **整段位移**：`system_log.debug('宿主机配置为策略不接收…')`+`append` 由 orig[484:499] 前移到 decomp[438:453]（=内层 `if receive_other_response=='1'` 被提升到外层 else 之后）；`EXTENDED_ARG`(390) 与 `JUMP_FORWARD`(483) 各缺 1 ⇒ 511→509 |
| 10 | `on_trade_response#37` | 448/**446** | 3 | 同 #9（孪生） | 同款位移（orig[420:436] → decomp[375:390]）+ `EXTENDED_ARG`(327) 与 `JUMP_FORWARD`(420) 各缺 1 |
| — | `on_order_response_list_handle#90` / `on_trade_response_list_handle#91` | 125/126 | 各 1 | 伪影/位移 | decomp[28:29] 多一个 `EXTENDED_ARG` ⇒ 严格尺 `target_diff #23` |

## Step 2 · 根因（已在分析器实测）

### 根因 B（已坐实，覆盖 2/10 官方缺口）：`on_order_response` / `on_trade_response`
**实测链路**（`probe_r57e.py`，monkeypatch `RegionAnalyzer._r57e_in_loop_branch_convergence`）：

```
== fire: then@2220 else@2644 merge=2742 res=2376 ==
  blk@2220 last=NOP              succ=[2278]
  blk@2278 last=STORE_FAST        succ=[2338, 2340] exc=[2340] exc_in_succ=[2340]
  blk@2340 last=POP_JUMP_IF_FALSE succ=[2358,2368,2370] exc=[2370]
  blk@2338 last=JUMP_FORWARD      succ=[2376]
  [NOW] then@2220 votes=[2376] vis=[2220,2278,2338] all_exit=True
  [NOW] else@2644 votes=[]        vis=[2644,2742]    all_exit=True
  [NOW] exit_votes=[2376]  T@2376 preds=[2338,2364] external=[2364]  FIRE=True
  [+EXC] then@2220 vis=[2220,2278,2338,2340,2358,2364,2368,2370]   external=[]  FIRE=False
```

- `region_analyzer.py:17153-17156` 调 `_r57e_in_loop_branch_convergence(...)`，返回 **2376** 覆盖 NCPD 算出的正确 `merge=2742`（同一函数内 R57-E 被调 7 次，仅这 2 次返回非 None）。
- 机理：`_r57e_votes`（L2688-2738）把 **try 体越过 handler 的 `JUMP_FORWARD@2338` 当作「臂出口票」**（L2712-2718 只记票不深入）；又在 L2719-2723 **跳过异常边**，于是 handler 块 `2340…2364` 不进 `vis`；
  单侧规则 L2758-2765 的 `any(p not in _vis_then for p in _t.predecessors)` 就把 `2364`（handler 内 `POP_EXCEPT; JUMP_FORWARD→2376`）当成**兄弟臂外部汇入** ⇒ 返回 2376。
- 实际结构：`2376` 是 then 臂**内部**的下一条语句（`if receive_other_response=='1'`，orig L1576），
  两臂真汇聚点是循环条件块 `2742`。merge=2376 ⇒ `_collect_branch_blocks(2152, 2376)` 只收 `[2220,2278,2338]`，
  内层 if 的 `2376/2388/2550` 落到外层 `if/else` 之后发射 ⇒ 产物行序 `…994 宿主机debug / 995 append / 996 if receive_other…`，
  与 orig L1576-1586 行序相反；顺带丢掉 1 个 `JUMP_FORWARD`（内层 else 后的越臂跳，已无需）与 1 个 `EXTENDED_ARG`（跳距缩短）⇒ 511→509 / 448→446。
- **两处 firing 同因**：`(then=2220, else=2644, merge=2742)->2376` 与 `(then=2152, else=2742, merge=2742)->2376`，`[+EXC]` 变体两者都变 None。

### 根因 C（发射路径已坐实，候选 NONE，1/10）：`get_max_amount` 块 802 双发射
- orig 反汇编（`disf.py`，offset 758-1016）：
  `758: entrust_bs=='1' →IF_FALSE→778`、`770: entrust_type in ('6','7','9') →IF_TRUE→802`、
  `778: entrust_bs=='2' →IF_FALSE→910`、`790: entrust_type=='7' →IF_FALSE→910`，两条 TRUE 都落 **同一块 802**。
  ⇒ orig 是 `(A and B) or (C and D)` 的**一个**条件 + 两个分支（802=`max_amount=…enable_buy_amount`，910=`…enable_amount`）；
  两个分支共享同一块 ⇒ 源里该赋值语句**只有一条**。
- 区域树（`regdump.py get_max_amount`，`dump/regdump_get_max_amount.txt`）：
  `IfRegion@564 then=[666] else=[758,778,790,802,910] elif_conditions=[758]`（children 含 `IfRegion@778`）、
  `IfRegion@778 blocks=[778,790,802,910] then=[802] else=[910] inline_boolop_chains={and:[778,790]}`、
  `BoolOpRegion@758 blocks=[758,770]`（**只覆盖 A∧B，没把 or 的第二操作数 778/790 并进来**）。
- 产物形态（`build_landed/…trade_live_brokerOK.py` 行 1649-1659）：
  `if error: … elif not (entrust_bs=='1' and entrust_type in ('6','7','9')): if entrust_bs=='2' and entrust_type=='7': max_amount=…buy (行1655) else: max_amount=…amount (行1657) else: max_amount=…buy (行1659)`
  ⇒ 行 1655 与行 1659 都是块 802 ⇒ **+12 条**（pbv 201→213；`nested_diff` 口径 +15 条，`dump/nd_get_max_amount.txt` 1 hunk insert decomp[212:227]）。
  语义上与 orig 等价（`¬(A∧B)` 走 778，`A∧B` 走 802），差只在多发一份语句。
- **发射点实测**（`probe_gma_rm.py` / `probe_gma_emit.py`，hook `RegionASTGenerator._generate_block_statements`）：
  块 802 被调用 **2 次**：
  1. `generate → _generate_region → _generate_if → _if_generate_normal → _if_generate_then_branch → _process_if_blocks`（内层 `IfRegion@778` 的 then）
  2. `generate → _generate_region → _generate_if → _if_generate_full_elif_chain → _if_generate_elif_chain → _process_if_blocks`（`IfRegion@564` elif 链尾的 else）
  其余块各发 1 次（`emitted per block: 802×2，910×1 …`）。
- **已试不通的三次形状**（BRIEF 两次不通换形状；均记入）：`--drop=790`（decomp 213 不变）、`--drop=778`（209，仍 +8）、
  `--drop=778,790`（213）、自动判据「根区域被另一区域真包含且 entry 在其 inline_boolop_chains 内」（5 处命中、读数不变）
  ⇒ 归属/去重方向走不通：**两条发射路径各自语义正确，唯一正确修法是把 `BoolOpRegion@758` 从 [758,770] 扩成
  `(A∧B)∨(C∧D)` 全 4 块，使 `IfRegion@778` 不再独立成区、elif 链尾变 910，从结构上消除双发。**
- 同层识别判据（供下轮，尚未实现）：操作数1 的 **false 出口 == 操作数2 的入口块** 且 **true 出口 == 操作数2 的 true 出口同一块**
  ⇒ 两段短路条件是同一 `or` 表达式的操作数，必须并入一个 BoolOpRegion（op='or'）；归约方式＝合并为单条件单 then/else；
  AST 映射＝`ast.If(test=BoolOp(BoolOp(and),BoolOp(and)), body=[802], orelse=[910])`，无嵌套 if、无重复语句。
- 同文件内 `or` 正确案例：`BoolOpRegion@0`（`sid[0]=='6' or sid[0]=='5'`）已被识别为 BoolOp；差异在该 `or` 处于 **elif 位置**（前一支以 `return out_info` 终止）。

### 根因 D（已坐实，1/10，本轮未修）：`etf_basket_order` then 臂过度吸收（NCPD 不可达 ⇒ merge=None）
- `IfRegion@568` 的 then 臂吸收了 merge 之后的续接块（orig[274:285] 的 `warning+return None` 被发到 decomp[516:527]）；
  `else` 臂以 `RETURN` 终止 ⇒ NCPD 无真汇合点 ⇒ `merge_block=None`。同款 `warning('该股票【%s】行情数据异常')` 形状。
- 实测（`regdump_etf_basket.txt` + `probe_merge.py`）：`IfRegion@568 then_blocks=[674…2496]`（56 块）、`else_blocks=[1328]`、
  `merge_block` 字段缺省；同层兄弟 `IfRegion@674`/`@814` 的 `merge` 均 **=1380** ⇒ **@568 的正确 merge 也是 1380**。
- orig 反汇编：`568: POP_JUMP_IF_FALSE → 1328`；`1328`（else = `strategy_log.warning(...); return None`）与 `1276`
  都以 `RETURN_VALUE` 终止；then 侧非终态路径 `698: JUMP_FORWARD → 1380` 续接 ⇒ merge=1380。
- **sink 回退失效的确测原因**：该 code object **所有块的 `immediate_post_dominator` 均为 None**
  （`off=0/484/568/674/698/814/1276/1328/1380/2248/2496/2500/480` 逐一打点全为 None），
  ⇒ `region_analyzer.py:17296` `_then_sink = … or then_succ.immediate_post_dominator is None` 为 True、
  L17297 `_else_sink` 同为 True ⇒ L17261 起的 `if merge is None and _then_sink and not _else_sink` /
  L17348 `elif … _else_sink and not _then_sink` **两支都进不去** ⇒ merge 保持 None。
  ipdom 为 None 的来源：`dominator_analyzer.py:223-229` `strict_pdoms` 为空即置 None（多出口函数在
  `_compute_post_dominators` discard 虚拟出口后 `strict_pdoms` 为空）。
- 后果：`_collect_branch_blocks(568, merge=None, stop)` 只被循环头边界挡住，一路收到 2496 ⇒ 续接块并进 then 臂。
- **未给出候选**：要修需「一臂无条件终态、另一臂部分路径终态/部分路径续接」时求续接点的同层结构判据，
  现有 ipdom 与 NCPD 都给不出 1380；且 `dominator_analyzer.py` 不在白名单三文件内 ⇒ 按 BRIEF 只记 FACTS、不做 spec。

### 根因 E（已坐实，1/10）：`_trade_status_handle` 丢语句 + `while…else` 位移
- 丢 `self.trade_info = get_trade_status(self.trade_id, True)`（orig 7:17，line 1445-1446）；
- `time.sleep(0.5)` 在 orig 位于**循环体末**（A@842-868 之后才是 `EXT+JUMP_BACKWARD@870`），
  产物发成 `while…else:` 的 else 臂（产品行 917-918）⇒ 尾部 128:130 与 112:118 两处 hunk。

### 未判定（其余 5/10）
`_process_order`（丢 56 条语句族）、`_sync_worker`（丢 239:404 共 165 条 + 块前移）、`_process_cancel_order`（循环尾 4 处位移）、
`etf_purchase_redemption`（3 条 `strategy_log.info` 被压成拼接常量）、`ipo_stocks_order`（EXTENDED_ARG/跳向 7 处）——
尚未定位到分析器具体行号，按 BRIEF「两个方向不通就换形状」的预算，本轮先攻根因 B。

## Step 3 · 合成复现（根因 B）
- 源：`synth/r70_exc_r57e.py`；名单：`synth/r70_exc_r57e.txt`（pyc：`synth/__pycache__/r70_exc_r57e.cpython-311.pyc`，Python 3.11.7）。
  形状＝`while` 内 `if ctrl=='1'`：then 臂含 `try/except AttributeError` + 紧随的内层 `if code=='1'`，else 臂是循环体末语句（顺序落到循环条件块）。
- landed 读数（`h62.py run --arm=landed --list=synth/r70_exc_r57e.txt`）：**1/2**，`[['repro', 93, 92, 4, 55]]` ⇒ **失败签名**。
- 探针（`probe_r57e.py <synth pyc> repro`）与靶支逐字段同形：
  `then=98 else=338 merge=428 -> res=158`；`[NOW] votes_then=[158] vis=[98,104,120] exit_votes=[158] T@158 preds=[120,146] external=[146] FIRE=True`；
  `[+EXC] vis=[…122,140,146,150,152] external=[] FIRE=False` ⇒ 合成件与根因 B 同一机理（handler 块 146 = `POP_EXCEPT; JUMP_FORWARD→158` 不在 vis）。

## Step 4 · 候选与 A/B
**候选：`specs/cand_r70_r57e_exc.json`**（`mk_spec_r70.py` 生成；file=`core/cfg/region_analyzer.py`，2 edits，anchor count 均=1）

判据三要素（已写进 `_r57e_votes` 与 `_r57e_in_loop_branch_convergence` docstring）：
- **识别条件**（同层次结构身份）：游走中当前块 `cur` 的后继含异常后继 `exc`——`exc` 由本臂 try 块沿异常边唯一派生、与 `cur` 同层（同属本臂 try 区），
  故 handler 子图属于本臂必须进 `visited`；据此单侧规则 `T.predecessors ⊆ visited` 成立时，「try 体越过 handler 的 `JUMP_FORWARD`」不再是臂出口票的外部汇入。
- **归约方式**：handler 块进 `visited` ⇒ 单侧规则不命中 ⇒ 逐字保持 NCPD 算出的 merge（`_merge_e` 为 None 时不覆盖，L17155），
  臂体收集到真汇聚点，不破坏「innermost→outermost、每块每层唯一归属」；判据不命中零行为差（严格附加）。
- **AST 映射**：merge 不被改写 ⇒ `ast.If` 的 body/orelse 保持源序，内层 if 留在本臂 body 内，不被提升到对侧 `orelse` 之后。

实测改动：删掉 `_r57e_votes` 中 `if _s in _exc: continue`（`region_analyzer.py` 原 L2719-2723）并同步 docstring L2662-2663；不新增 `self` 状态。

A/B（同臂 `--arm=r70diag1`，镜像 `center/mirr_r70diag1`，产物 `center/build_r70diag1`）：

| 列 | landed | r70diag1 | 判定 |
|---|---|---|---|
| targets（官方尺） | 109/119，gap 10 | **111/119，gap 8** | ✔ `on_order_response`、`on_trade_response` 出列（IMPROVED，无 REGRESSION/MOVED/ERR） |
| 82 项电池 | 基线见 Step 0 | **worse-than-landed on 0 repro(s)** | ✔ |
| 金丝雀 4 sha | 143/143、10/10、26/26、25/25 | SAME=4、REGRESSION=0 | ✔ sha 逐字节不变 |
| 严格尺 | 107/123，defects=16，missing=0 extra=0 | **109/123，defects=14，missing=0 extra=0** | ✔ 两支 `seq_len` 缺陷整体消失，无新增 `target_diff` |
| 合成 | 1/2 | **2/2** | ✔ 咬合（landed 失败、候选通过） |

ADR-1 核对：纯位移族 hunk 数下降（`on_order_response` 3 hunk、`on_trade_response` 3 hunk 全部消除）、无新增 `target_diff`；
缺失/过冲族 Σ|orig−decomp| 由 86 降到 **84**（−2），且 matched 109→111 ⇒ **不是以少发射换**。

## Step 5 · VERDICTS

官方尺 gap 10 支逐条判词（候选 = 本轮提交的 spec；未达判据即 NONE，不硬凑）：

| 靶支（gap 内） | 缺陷 | 根因 | VERDICT |
|---|---|---|---|
| `on_order_response` | seq_len 449→448 / 3 hunk | B | **候选 `cand_r70_r57e_exc` 修好**（出列） |
| `on_trade_response` | seq_len 396→395 / 3 hunk | B | **候选 `cand_r70_r57e_exc` 修好**（出列） |
| `etf_basket_order` | seq_diff #254 | D（已坐实） | NONE：判据需白名单外文件（`dominator_analyzer.py`）或未找到同层续接点判据 |
| `get_max_amount` | seq_len 201→213（+12） | C（发射路径已坐实） | NONE：双发=内层 `IfRegion@778` then + `IfRegion@564` elif 链尾；drop 790/778/自动包含判据 3 形状实测均不修，唯一正确修法需扩 `BoolOpRegion@758` 为全 4 块 `or`（未实现） |
| `_trade_status_handle` | seq_len 114→112 | E（已坐实） | NONE：丢 1 条赋值 + `time.sleep` 落进 while-else，两处形状未分离出单一判据 |
| `_process_cancel_order` | seq_len 295→297 | 未定位 | NONE（循环尾 4 处位移，未定位到分析器行号） |
| `_process_order` | seq_len 454→399 | 未定位 | NONE（丢 56 条语句族） |
| `_sync_worker` | seq_len 350→347 | 未定位 | NONE（丢 165 条 + 块前移） |
| `etf_purchase_redemption` | seq_len 379→369 | 未定位 | NONE（3 条 `strategy_log.info` 被压成拼接常量） |
| `ipo_stocks_order` | seq_diff #624 | 未定位 | NONE（EXTENDED_ARG/跳向 7 处） |

**VERDICT：`specs/cand_r70_r57e_exc.json`（唯一候选，五列全绿，见 Step 4 表）。**
整体官方尺 **gap 10 → 8**；**未达** BRIEF「至少把一支 partial 修到 100%」的目标（本轮修好的两支是
`target_diff` 族，不属 official gap 的 seq 族？——否：两支原本就在 gap 10 清单内，出列后 gap 计数 10→8，
但余 8 支均未修复，故无单支达到 100%）。16 项严格缺陷 16 → 14，missing=extra=0。

## 对 BRIEF 的更正
1. **BRIEF 是 R69 模板**：标题/路径写 `Round 69`、`D:/Temp/opencode/r69gate/<batch>`、spec 命名 `cand_r69_<名>.json`；
   本轮实际工作区 `D:/Temp/opencode/r70gate/diag1`、臂名前缀 `r70diag1`、spec 已按 `specs/cand_r70_<名>.json` 落盘。
   其余步骤/合同/白名单/16 仪器缺陷条目逐条适用，无需更正。
2. **电池口径**：BRIEF §0 写「45 项公开电池（`closeout67.py`）」，本目录只有 `closeout69.py`（**82 项**，含 R68/R69 见证）。
   本轮以 82 项口径验证合同「worse-than-landed=0」（实测 0）；82 为 45 的超集 ⇒ 合同强度只增不减。
3. **仪器细节**：`sstrict67.py` 第一参数须为 `build_<dir>`（写 `build_r70diag1`，写 `r70diag1` ⇒ `NO-PRODUCT`）；
   `h62.py run` 的 list 文件不可带 UTF-8 BOM（PS5.1 `Set-Content -Encoding utf8` 会写 BOM ⇒ `Errno 22`），
   需用 `[IO.File]::WriteAllText`；PS5.1 无 `Select-String -First`（管道被截断，改重定向到文件）；
   `probe_*.py` 内 `os.chdir(REPO)` 会使相对路径失效，须传绝对 pyc 路径。
4. **本轮新增仪器**：`probe_r57e.py`（monkeypatch `_r57e_in_loop_branch_convergence` 打印 then/else/merge/res 与逐块游走/external）、
   `mk_spec_r70.py`（多 edits spec 生成，anchor count 自检）、`synth/r70_exc_r57e.py`（根因 B 合成见证）、
   `probe_gma_rm.py`（drop/keep 指定 IfRegion 后重测 pbv 读数，验证归属假设）、`probe_gma_emit.py`（hook
   `_generate_block_statements` 打印每个块的发射次数与调用链，定位双发点）、`regdump_get_max_amount.txt`（区域树）。
