# Round 68 · diag1 · FACTS

名额：`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`（官方 108/119，gap 11，严格缺陷 17）

## Step 0 · baseline replay（arm=landed ＝ 当前工作树字节）

### targets（dump/landed.jsonl）
`landed trade_live_broker.pyc  108/119`
官方缺陷函数（[name, orig, decomp, jump_diffs(hunks), true_diffs(first_diff)]）：

| function | orig | decomp | hunks | first_diff | 与 brief |
|---|---|---|---|---|---|
| _process_cancel_order | 293 | 292 | 16 | 43 | ✔ |
| _process_order | 454 | 396 | 9 | 349 | ✔ |
| _sync_worker | 349 | 347 | 0 | 296 | ✔ |
| _trade_status_handle | 114 | 112 | 0 | 107 | ✔ |
| after_trading_cancel_order | 155 | 155 | 3 | 122 | ✔ |
| etf_basket_order | 693 | 693 | 11 | 216 | ✔ |
| etf_purchase_redemption | 377 | 369 | 1 | 37 | ✔ |
| get_max_amount | 201 | 213 | 2 | 18 | ✔（过冲 +12） |
| ipo_stocks_order | 1075 | 1076 | 10 | 437 | ✔（过冲 +1） |
| on_order_response | 445 | 444 | 6 | 57 | ✔ |
| on_trade_response | 392 | 391 | 6 | 57 | ✔ |

Σ|Δ|（官方尺，本支）= |293-292|+|454-396|+2+2+0+0+8+12+1+1+1 = **57**；缺陷函数 11。

### canary（dump/landed_canary.jsonl）
sha 逐字节符合 BRIEF §3 合同：
```
4d41187e356544e0  quotation.pyc        143/143
af77224b34b203c4  market_time.pyc       10/10
e711b8ea86d49a15  datetime_func.pyc     26/26
9d09af09249da177  datetime_func.pyc     25/25
```
### battery（closeout67.py battery landed，45 项）
`repro pycs discovered: 45` → **174/200、缺陷函数 26、Σ|Δ| 101、worse-than-landed=0、ERR=0**
⇒ 与 BRIEF §4 轮初基线**逐字段一致**，无更正。

**结论：Step 0 全部读数与 brief/targets.md 预读数一致，基线可信。**

## Step 1 · hunk tables（nested_diff.py，按 code-object 全路径配对）

产物：`build_landed/IQEngine__plugins__plugin_system_trade__trade_live_brokerOK.py`
全表：`dump/nd_landed.txt`。**15 of 128** code objects 有差异。

**先记一条仪器更正**（见文末「对 BRIEF 的更正」）：targets.md 里 mism 的第 4/5 列被标成
`hunks/first_diff`，实际是 `len(jump_diffs)/len(true_diffs)`（见 `scripts/pyc_batch_verify.py` L328-335）。

| code object | orig | decomp | hunks | 真缺陷 or 伪影 | 主签名 |
|---|---|---|---|---|---|
| /TradeLiveBroker#28 | 434 | 430 | 2 | **伪影**(NOP×2) | 类体只丢 2 个 NOP |
| get_orders#4/\<listcomp\>#7 | 14 | 15 | 1 | 真(过冲+1) | 多出发射 `LOAD_ATTR symbol`；官方尺**不计**嵌套 code obj |
| _process_order#22 | 520 | 464 | 27 | **真(缺56)** | 6 处 `strategy_log.info/error(...)` 整条语句被吞 + 4 处 f-string 内三元常量被吞 |
| _process_cancel_order#24 | 344 | 344 | 6 | 半伪影 | NOP/EXTENDED_ARG 位移 + 尾部 `JUMP_FORWARD`↔`RETURN None`（尾跳转被写成 return） |
| _sync_worker#34 | 412 | 410 | 8 | **真(位移族)** | orig[239:404] 165 条整段错位；官方 jump=0/true=296 ⇒ 近乎全序列偏移 |
| _trade_status_handle#35 | 130 | 126 | 3 | **真** | orig[7:17] `get_trade_status(self.trade_id, True)` 调用整条丢；尾部 JUMP↔RETURN |
| on_order_response#36 | 511 | 509 | 3 | **真(位移)** | `system_log.debug('后端服务…%s'%entrust_no)` 从 orig[483:499] 被搬到 decomp[438:453] |
| on_trade_response#37 | 448 | 446 | 3 | **真(位移)** | 同上同形（孪生函数，同一处根因可一次修两支） |
| etf_basket_order#56 | 769 | 769 | 2 | **真(位移)** | `strategy_log.warning('该股票【%s】行情数据异常'%stock)` 从 orig[274:285] 搬到 decomp[516:527]，量相等 |
| etf_purchase_redemption#57 | 427 | 415 | 5 | **真** | decomp 里出现**合并污染常量** `'list_info00orderstrresultentrust_noselforderorder…'` ⇒ co_names/co_consts 串位，f-string/拼接文本被并成一个常量 |
| get_max_amount#64 | 218 | 233 | 1 | **真(过冲+15)** | decomp[212:227] 多出一整条 `int(float(result[0]) …)` 语句 ⇒ **语句双发** |
| ipo_stocks_order#84 | 1206 | 1214 | 14 | **真(位移+缺)** | `strategy_log.error('账户无可转债交易权限…')` 丢；末尾 debug 长 f-string 整段被搬到 decomp[1167:1212] |
| after_trading_cancel_order#87 | 177 | 180 | 2 | 真(过冲+3) | orig `JUMP_FORWARD` 在 decomp 里变成**两处** `LOAD_CONST None/RETURN_VALUE` ⇒ 空 return 双发 |
| on_order_response_list_handle#90 | 125 | 126 | 1 | **伪影** | 只有 `insert EXTENDED_ARG`；但严格尺有 target_diff#23 |
| on_trade_response_list_handle#91 | 125 | 126 | 1 | **伪影** | 同上（孪生） |

官方尺 Σ|Δ|(本支)=**86**，其中 `_process_order` 一支占 **58**（67%）、`get_max_amount` 12、`etf_purchase_redemption` 8。

### 严格尺 target_diff 家族（nested_diff 看不见，因为它把跳转归一为 `J`）
`_process_tick_order#27 JUMP`、`get_ipo_stocks#189 POP_JUMP_IF_TRUE→(None,FOR_ITER)`、
`on_order_response_list_handle#23 / on_trade_response_list_handle#23 POP_JUMP_IF_NONE→(None,FOR_ITER)`、
`on_pre_before_trading_start#4 POP_JUMP_IF_FALSE`、`rzrq_credit_order#406 JUMP` —— 6 项都是
**跳转终点错**而非序列错；两支孪生（list_handle）终点都落在 `FOR_ITER`，是同一形状的强证据。

### 归属结论（选攻方向）
1. `_process_order`（58）＝最大矿，签名是「若干条完整 Expr 语句消失」⇒ 与「菱形汇合点 merge 回收」无关，
   更像**语句级早退/丢弃**；优先。
2. `get_max_amount`（+12/+15 过冲）＝语句双发，独立且可能小修。
3. 位移族（on_order/on_trade_response 孪生 + etf_basket_order + _sync_worker）＝同一根因、一次可动 4 支。

## Step 2/4 · W1（已证伪，阴性证据）

**根因（实测）**：`_process_order` 少 56 条的主体不是「菱形汇合点找不到」，而是
**try 体内的内联三元被 R47 消费点守卫拒建 TernaryRegion**。
探针（`probe_analyzer.py` + `probe_succ.py`，均在我的工作区，仓库只读）：
```
[TP-ENTER] off=1634
[TP-EXIT L22713] off=1634 mb=None vt=None mc=None jfs=False tb=1754 fb=1758
BLOCK 1754 succ=[1760, 3026] csucc=[1760]      # LOAD_CONST '买入'; JUMP_FORWARD 1760
BLOCK 1758 succ=[1760, 3026] csucc=[1760]      # LOAD_CONST '卖出'
BLOCK 1760 pred=[1754,1758] instrs=FORMAT_VALUE, LOAD_FAST order_amount, FORMAT_VALUE,
                 BUILD_STRING 9, PRECALL, CALL, PRECALL, CALL, POP_TOP, JUMP_FORWARD 2912
NCPD(1754,1758) = None
```
⇒ `find_nearest_common_post_dominator` 被**异常边**（两条值块各有后继 3026＝except handler，
见 `BasicBlock.exception_successors`）打散，merge_block=None，落进
`core/cfg/region_analyzer.py` **L22710-22713** 的 R47 守卫 `return None`
（该守卫注释自陈「典型场景：try-except 内的 f-string inline if-else」）。
上游 `IfRegion@1634 blocks=[1634,1754,1758]` 因此按语句级 if 归约，
生成 `if …: Expr('买入') else: Expr('卖出')`，**整条 `strategy_log.info(_(f"…"))` 语句连同
汇合块 1760 的消费者全部丢失**（该形状在 `_process_order` 内出现 4 次：1634/2236/2310/2574）。

**候选 W1**：`specs/cand_r68_w1.json`（analyzer，锚点 landed `count==1`）——
在 merge_block 的各条既有回收通道之后、消费者扫描之前，加一条
「异常边屏蔽」判据：`true/false` 各自的 `conditional_successors`（=successors−exception_successors）
均为同一单块且该块首条非噪声指令不是无条件跳转 ⇒ 令 merge_block 为该共享块。
三要素已写进注释。

**A/B 实测（arm=r68w1）**：`_process_order 454/396 → 454/369`，**变差 27 条**。
其余 10 支官方读数逐字段不变。⇒ **W1 与 R67-diag1b 的「菱形汇合点 merge 回收朴素版」
完全同值（396→369）**，判据方向不同（异常边屏蔽 vs 原朴素汇合点）但**失败点相同**：
生成端 `merge_context='fstring'`（`__fstring_target__`）的 JoinedStr 重建本身是坏的。
产物证据（`build_r68w1` vs `build_landed` 的 `_process_order` 段）：
```
- if order.entrust_direction == EntrustDirection.BUY:
-     """买入"""
- else:
-     """卖出"""
+ f"股票strategy_log_生成订单，订单号：{order!s} {type_str!s}代码：{order!s} 数量：order{'买入' if …!s}{order_amount!s
```
（常量文本串位 `strategy_log_`、属性链被截成 `{order!s}`、f-string **未闭合**，
且吞掉其后 4 条语句 `order.set_entrust_no / self.close_orders[…] / on_*_list_handle`。）
同一坏形在 landed 的 `etf_purchase_redemption` 已经可见（污染常量
`'list_info00orderstrresultentrust_noselforderorder…'`），说明这是**既有的生成端缺陷**，
不是我的识别判据能修的。
⇒ **W1 判 NONE**（违反采纳合同第 3 条：Σ|Δ| 变大）。
⇒ **本支「f-string 内联三元」簇（_process_order 56 缺、etf_purchase_redemption 8 缺）
在生成端 `__fstring_target__` 修复之前不可攻**，这是给中心的「中心级建议」。

## Step 3/4 · E1（cand_r68_e1，上一会话已建臂，本会话补全读数 + 复核）

spec：\diag1/specs/cand_r68_e1.json\（file=core/cfg/region_analyzer.py，anchor 在落地字节 count==1，
h62 build 断言通过）。判据：elif 臂**全集出边**（原判据只看 \_body[-1]\ 单块）落入 final_else 候选 ⇒
F 并入 \_chain_merge_candidates\、从 final_else/else_blocks 移除（三要素写在 spec 注释里）。

### 五列实测
| 列 | landed | r68e1 |
|---|---|---|
| targets（trade_live_broker 官方） | 108/119 | **110/119**（after_trading_cancel_order、get_max_amount 出列） |
| Σ\|Δ\|（官方，本支） | 86 | **74**（净 −12） |
| 45 电池 | 174/200, df=26, Σ\|Δ\|=101, ERR=0 | **174/200, df=26, Σ\|Δ\|=101, worse=0**（逐字段不变） |
| canary 4 sha | 4/4 命中 | **4/4 逐字节不变** |
| synth e1.pyc | 3/4（e1 38/40 hunks=3） | **4/4 全 matched**（见证咬合） |
| 严格尺 sstrict67 | 106/123, defects=17 | **107/123, defects=16** |

产物 diff（build_landed → build_r68e1，整文件仅 2 处）：
1. \fter_trading_cancel_order\：\elif isinstance(order_param, str):\ → \if isinstance(order_param, str):   （链把后随独立 if 的条件误认领成自己的 elif；严格尺该支 seq_len 156/159 → **OK**，真修好）
2. \get_max_amount\：删掉链尾 \else: max_amount = int(float(result[0].get('enable_buy_amount')))
### ⚠ 复核结论：e1 在 get_max_amount 上**制造了新的 target_diff**（R42 假 ok 形状）
逐指令比对（去掉 CACHE/EXTENDED_ARG 后 orig=218、r68e1 decomp=218，**唯一差异就是一条跳转终点**）：
\orig   #174 offset=776 POP_JUMP_FORWARD_IF_TRUE -> 802  (LOAD_GLOBAL int  ← int(float(...enable_buy_amount)))
landed #174 offset=776 POP_JUMP_FORWARD_IF_TRUE -> 1018 (LOAD_GLOBAL int  ← 同样的赋值，正确)
r68e1  #174 offset=776 POP_JUMP_FORWARD_IF_TRUE -> 1016 (LOAD_FAST max_amount ← 落到 out_info[sid]=max_amount)
\- 语义：源码是 \if (entrust_bs=='1' and entrust_type in ('6','7','9')) or (entrust_bs=='2' and entrust_type=='7'): X else: Y\。
  landed 发射 \elif not(A and B): if C and D: X else: Y  /  else: X\（X 双发 +12 条 ⇒ seq_len 201/213），
  r68e1 删掉外层 \else: X\ ⇒ \A and B\ 为真时**不赋值就执行 \out_info[sid]=max_amount\**（unbound），
  计数对齐成 201/201 但跳转终点错 ⇒ 官方尺判 matched（假 ok），严格尺判 target_diff。
- 严格尺上 get_max_amount 由 \seq_len\ **变成** \	arget_diff #163\ —— 该 code object 之前是 seq_len（跳转比对因长度不齐未报），
  现在长度齐了、跳转暴露。按 ADR-1 字面，rule 2 的「不得新增 target_diff」只约束纯位移型，
  本支属过冲型走 rule 1（Σ|Δ| 净减 12 ✓）；但**语义上确实是回退**，中心复测时这一条最该被先验。
- 判据根因：e1 的「臂全集出边 ∩ final_else」在 get_max_amount 上误命中 ——
  802 同时是**链的 else 目标**（被链条件块 776 直接指）**和** arm2 内层 \if C and D\ 的 then 目标。
  可区分的同层结构身份：**F 是否为链某条件块的直接后继**（after_trading_cancel_order 上为否，get_max_amount 上为是）。
  ⇒ e1 需要加这道门再复测；本轮先把它记为「有真修复但带一条新 target_diff」，**暂不送采纳**。

## Step 2/4 · B1（matcher 过吸收三修，spec=specs/cand_r68b1_j.json）

**指派更正**：本会话操作方给 diag1 的活是 **3 支 partial**（trade_live_broker 108/119、
fly/data/quote.pyc 70/81、IQEngine/plugin_system_matcher/matcher.pyc 16/17），
而 \BRIEF.md §8\ 写的是「你名下只有 1 支」。以下按 3 支报数。
（注意：canary 里的 \ly/data/quotation.pyc\ **不是** \ly/data/quote.pyc\，是两个文件。）

### Step 2 · 根因（全部在镜像里实测，非读码推断）

matcher::match 的唯一失配函数。区域 dump（dumpregions2.py，mirr_head vs mirr_r68b1_j）
显示 **25 个 IfRegion 的块集不同**，共同形态是「分支体越过汇合点继续吸块」：

- 头号形：\IfRegion 1324 cond=1324 merge=1384 then=[1372…4960] else=[]  → 修后 \	hen=[1372] else=[]\。同族 1068/1110/1372/1444/1486/1570/1612/1912/…
- 机制（三条同时成立才发作）：
  1. **收集门未开**：\_collect_branch_blocks\ L26852 是 \if len(collected) > 1 and not merge:\，
     有 merge 的收集**永不剪枝** ⇒ 越界块原地留下；
  2. **循环豁免恒真**：\_w14_pred_is_child_structural_exit\ L26952 对 LoopRegion 用
     \ny(b in in_set for b in rblocks)\，而外层 LoopRegion@6.blocks 包住全函数 ⇒ 循环内剪枝恒死；
  3. **倒序识别 + 收集期拿不到 IfRegion**：\_identify_conditional_regions\ 按 start_offset
     倒序处理，且收集期间 \self.regions\ 只有 Phase-1 区域（Loop/Ternary/BoolOp/Try/With/Match），
     \self.regions\ 到 L1814 才整体赋值、\self.block_to_region\ 收集期只有 BoolOpRegion
     （market_time 实测 map_size=15）⇒ 任何依赖「外层/子 IfRegion 对象」的判据都拿不到数据。
- **canary 回归形（必须挡住）**：\ly/common/market_time::trade_is_open\ 剪枝
  \entry=148 b=278 pred=224 merge=172\；278 是本臂共享 eturn False\、pred 224 是嵌套子 if 尾部
  \JUMP_FORWARD\，且 **entry=148 支配 278** ⇒ 属本臂合法体内块，剪掉即把 \market_time\ 打回 9/10。
- **quotation 回归形（必须挡住）**：\ly/data/quotation::change_his_to_forward\ 剪枝
  \entry=1558 b=1748 pred=1304 merge=1266\；1304 是整个 if 之前的块、**支配 entry=1558**，
  它对 1748 的直连边是区域级共享边；剪掉会把该 IfRegion 的 else 从
  \[1558,1746,1748,…,2906]\ 砍成 \[1558,1746]\ ⇒ canary sha 变。
  注意 \merge=1266\ **就是该函数的循环头**，所以「merge ∈ entry.successors」「merge==循环头」
  这两条同层判据**分不开**这两案（实测 spec i 用前者 ⇒ matcher 掉回 16/17）。

### 候选组合矩阵（全部 matcher 单文件 A/B + canary ab 实测）

| spec | 改动 | matcher | canary |
|---|---|---|---|
| cand_r68b1_ab | (a)+gate | 16/17 | **REGRESS** market_time 10→9 + quotation sha 变 |
| cand_r68b1_c | 仅 (c) 循环豁免收紧 | 16/17 | SAME=4 |
| cand_r68b1_d | (a)+gate+(c) | 17/17 | 同 ab 失败 |
| cand_r68b1_de | gate+(c)（**证 (a) 非必需**） | 17/17 | 同 ab 失败 |
| cand_r68b1_f | gate+(c)+R68-D 后继豁免 | 16/17（豁免过宽） | SAME=4 |
| cand_r68b1_g | gate+(c)+R68-E 支配守卫(仅 merge≠None) | 17/17 | 3 SAME + **quotation sha 变** |
| cand_r68b1_h | 同 g 但不看 merge | 17/17 | 同 g |
| cand_r68b1_i | g + \merge ∉ entry.successors ⇒ 跳剪\ | 16/17 | SAME=4（sha 全同） |
| **cand_r68b1_j** | **gate + (c) + R68-E（支配 ∨ 前驱支配 entry）** | **17/17** | **SAME=4** |

（(a) = 外层 IfRegion merge 并入 boundary_stop，实测无效：收集期 \self.regions\ 里根本没有 IfRegion；
(AB 关系) = 包住 (a) 的那版同样 canary 失败，证明失败来自 gate 而非 (a)。）

### 判据三要素（已写进 region_analyzer.py 注释，anchor 在落地字节 count==1，h62 build 断言通过）

1. **[R68-B] 收集门开到「有 merge」**（L26852 \if len(collected) > 1 and not merge\ → \if len(collected) > 1\）
   - 识别条件：收集块存在**集外且不在 stop 内**的前驱；
   - 归约方式：逐点迭代剪枝至收敛，再做 entry 可达性收敛；
   - AST 映射：被剪除块回归其真实父级顶点序列按偏移补发，分支体只留本臂独有前缀。
2. **[R68-E] 有 merge 收集的剪枝守卫**（插入 \_w14_pred_is_child_structural_exit\ 调用点之前）
   - 识别条件：\entry ∈ block.dominators\（entry 支配候选块 ⇒ 块属本臂，集外前驱只是嵌套子区域尾部回流）
     **或** \entry ∈ pred.dominators\（前驱支配 entry ⇒ 该前驱位于本区域入口上游，它对臂内块的直连边是区域级共享边）；
   - 归约方式：跳过该块的外部前驱剪枝；
   - AST 映射：体内块留在本臂末尾。
   - 两条同层身份来自 \BasicBlock.dominates\（= \self in other.dominators\，DominatorAnalyzer 在
     \RegionAnalyzer.analyze\ L1408 \self.dom_analyzer.analyze()\ 时算好，收集时已可用）。
3. **[R68-C] 循环豁免收紧**（\_w14_pred_is_child_structural_exit\ L26952 前）
   - 识别条件：子结构是 LoopRegion 且其 **entry 不在本臂收集集内**（循环未嵌套在本臂中）；
   - 归约方式：跳过该循环的豁免判定，让外部前驱剪枝正常生效；
   - AST 映射：被挡下的后继块回归其真实父级顶点序列按偏移补发。
   - 没有它，外层 LoopRegion@\* 会因为 \ny(b in in_set …)\ 恒真把剪枝全挡掉。

### 五列实测（arm=r68b1_j，全部与 landed 同表 A/B）

| 列 | landed | r68b1_j |
|---|---|---|
| **matcher.pyc**（本轮头号） | 16/17，mism=\[715,715,10,517]\ | **17/17**，mism=[]，Σjump 10→**0**，Σtrue_diffs 517→**0** |
| trade_live_broker（官方） | 108/119，Σ\|Δ\|=86 | 108/119，Σ\|Δ\|=**85**（ipo_stocks_order 1→0） |
| trade_live_broker 严格尺 | 106/123，defects=17 | 106/123，defects=**17**（唯一变化：ipo \seq_len 1075/1076\ → \seq_diff #624\，**未新增 target_diff**） |
| fly/data/quote.pyc | 70/81 | **70/81，sha 逐字节相同**（SAME=1，未动） |
| 45 电池 | 174/200，df=26，Σ\|Δ\|=101 | **175/200**，Σ\|Δ\|=101，Σtrue_diffs 474→465，**worse=0**（SAME=44 IMPROVED=1 REGRESSION=0；r64d5_contsink 1/2→2/2） |
| 电池严格尺 | 173/204，defects=31 | **174/204，defects=30**（唯一 FIXED：r64d5_contsink probe seq_diff；**无新增缺陷**） |
| canary 4 sha | 4/4 命中 | **SAME=4，逐字节不变**（market_time 10/10、quotation 143/143、两支 datetime_func 不变） |
| 合成见证（见下） | 16/17 | **17/17** |
| ERR | 0 | **0** |

\Σ|Δ|\ 口径 = 逐 mism \|orig_count - decomp_count|\ 求和（缺失/过冲型判据）。
本轮 trade_live_broker 的净变化只有 ipo_stocks_order 一列：1 → 0，**且 decomp_count 1076→1075 正好等于 orig_count**
（不是「少发射」换来的）；true_diffs 437→278。jump_diffs 10→18 上升 8，按 ADR-1「match 可以有非零 jump_diffs」
与 rule 1（缺失/过冲型只看 Σ|Δ| 净减）不构成 veto，此处明写以便中心复核。

### Step 3 · 合成见证（synth/m2_r68.py → synth/m2_r68.pyc，list=synth/list_m2.txt）

\mk_m2.py\：把 \uild_r68b1_j/…matcherOK.py\ **裁成只剩 \DefaultMatcher.match\ 一个方法**、
模块级 import 全换成 stub（IntEnum 常量 + \check_price/Trade/Event/EventEnum/_/strategy_log/AbstractMatcher\），
178 行，CPython 3.11.7 编译（magic 0xa70d 与靶 pyc 一致）。
- landed：**16/17，mism=\[715,715,10,517]\**（与真 matcher 同签名）
- r68b1_j：**17/17** ⇒ **见证咬合**
（另建 \synth/m_r68.py\ 手写裁剪版：landed true_diffs=372 → 臂 2，改善但未清零，
 因该形在修后仍让父区域 else 被剪、子区域 else 不被剪而出现跨层不一致 ⇒ **不入验收名单**，仅作辅证。）

## VERDICTS

| 靶支 | landed | 候选 | 理由 |
|---|---|---|---|
| **IQEngine/plugin_system_matcher/matcher.pyc** | 16/17 | **候选 \cand_r68b1_j\（采纳）** | matched 16→**17/17 全 OK**、Σjump 10→0、Σtrue_diffs 517→0；canary SAME=4、电池 worse=0、锚点 count==1、合成见证 16/17→17/17 |
| **IQEngine/plugin_system_trade/trade_live_broker.pyc** | 108/119 | **候选 \cand_r68b1_j\（附带收益，非本轮主攻）** | matched 不变，但 Σ\|Δ\| 86→85、严格尺 ipo \seq_len\ 缺陷被消掉且未新增 target_diff；头号缺陷 \_process_order\（缺 58）仍由生成端 \__fstring_target__\ 卡死 ⇒ 见 Step 2/4·W1 的中心级建议 |
| **fly/data/quote.pyc** | 70/81 | **候选 \cand_r68b1_j\（不变）** | 本轮修的是区域剪枝，quote.pyc 的 11 个失配函数无一变化（sha 逐字节相同、SAME=1），既不变好也不变坏 ⇒ 要攻它需另立候选 |
| e1（cand_r68_e1） | 108/119 → 110/119 | **暂不送采纳** | get_max_amount 造出新 target_diff（R42 假 ok），需加「F 是否为链条件块直接后继」门后复测 |
| w1（cand_r68_w1） | 454/396 → 454/369 | **NONE** | Σ\|Δ\| 变大，与 R67-diag1b 同值失败；根因在生成端 f-string 三元重建 |

## 对 BRIEF 的更正

1. **§8「你名下只有 1 支」不成立**：操作方本轮给 diag1 的是 3 支（trade_live_broker / fly/data/quote.pyc /
   matcher.pyc）。本文件按 3 支报数。
2. **canary 里的 \ly/data/quotation.pyc\ ≠ 靶 \ly/data/quote.pyc\**（两个文件）。quotation 属
   「4 sha 逐字节不变」的硬门，本轮不得改动；本轮 spec 的 [R68-E] 第 (b) 条正是为了在修 matcher 的同时
   **保住** quotation 与 market_time 的 sha（spec g/h 只有第 (a) 条 ⇒ quotation sha 变，被否）。
3. **§2「禁止新增 self 状态」本轮满足**：3 处改动全是局部变量与提前 \continue\，无任何新 \self.\ 字段。
4. **仪器提醒追加**：\h62.py run --out=\ 是按 \rm|path\ resume 的；换臂必须换 out 文件（本轮已遵守）。
   \sstrict67.py\ 的产物名推导对 scratch 路径会拼出 \D___Temp__…OK.py\，列目录时用 \-*m_r68*\ 通配。
5. **补一条可复用读数**：\lock.dominators\ 在 \RegionASTGenerator.__init__\ 之后仍是**空的**，
   必须等 egion_analyzer.analyze()\ 跑到 L1408 \self.dom_analyzer.analyze()\ 才被填充；
   探针若在 analyze 之前读 \dominators\ 会得到 \[]\，据此写判据会静默失效（本轮 spec j 第一版就踩了这个坑，
   \entry in pred.dominators\ 方向也写反过一次，两次都在实测里被抓住）。

## Step 5 · 最终候选定稿与复现（specs/cand_r68_b1.json，arm=r68b1_final）

\specs/cand_r68b1_j.json\ 内容原样定稿为 **\specs/cand_r68_b1.json\**（3 edits，
\ile=core/cfg/region_analyzer.py\，anchor 在落地字节 count==1）。
用新文件**从零重建**镜像并复跑全表，逐项与 j 臂一致：

\mirrors built: head pristine == worktree bytes, cand patched (3 edits, core/cfg/region_analyzer.py, BOM=False, nl=CRLF)
matcher.pyc                     16/17 -> 17/17            IMPROVED
canary（quotation/market_time/2x datetime_func）  SAME=4 REGRESSION=0
trade_live_broker.pyc           ipo_stocks_order [1075,1076,10,437] -> [1075,1075,18,278]   MOVED
battery45                       SAME=44 IMPROVED=1 REGRESSION=0  (files fully matched a=30 -> b=31)
synth witness synth/m2_r68.pyc  16/17 -> 17/17            IMPROVED
\
- 电池 IMPROVED = ound64_diag5/r64d5_contsink.pyc 1/2 -> 2/2\；未修复文件的 mism 列表与 landed 逐项相同。
- 产物留档：\dump/final_{match,canary,targets,bat45,m2}.jsonl\（与 \dump/r68b1j_*\ 同值）。
- **交付清单**：\specs/cand_r68_b1.json\（spec）+ \synth/m2_r68.py\/\synth/m2_r68.pyc\/\synth/list_m2.txt\/\mk_m2.py  （合成见证与生成器）+ \dump/landed_battery45.jsonl\（电池基线）+ \dumpregions2.py\/\probe_m0.py\（仪器）+ 本 FACTS。
