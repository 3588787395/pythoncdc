# Round 6 · FIX_B111 —— if 臂出口凭空造出的函数尾 `return None` sink

轮次：Round 6 / 破口 = **B111**（`site-packages/fly/data/quote_handler.pyc` / `<module>.get_kline_local`，
Round-4 REVIEW §3 行 #7，签名 C 轴）。
判定尺：唯一判据 `scripts/pyc_verify.py`（未改、未替代；interp 3.11.7 64 位）。
落地文件：**`core/cfg/region_analyzer.py` 单文件**（分析端归属判据；`region_ast_generator.py`
与 `code_generator.py` 逐字节未动，sha 不变）。
产物一律先删后 `python -X utf8 pycdc.py -o <base>OK.py <pyc>` 重生成，无手改 `*OK.py`。
插桩全部在 `D:/Temp/rrv6/`（b111_cfg.txt / b111_tail.py / b111_probe.py / b111_walk.py /
b111_split.py / b111_loop.py / b111_cand.py / b111_flat.py / b111_arms.py / b111_a02v.py /
b111_finish.py / b111_pins.py），生产目录零新增脚本（合成臂与索引条目属交付物 4，另计）。

**结论标记：「代码已落地」**。
**语料翻转：+1 文件级翻面 —— quote_handler 78/79 → 79/79 status=success（本 round 需要的整文件翻面）**；
单元翻转 `quote_handler.<module>.get_kline_local` Different control flow → **Equal**。
`IQCommon/logger/handlers.pyc` 仍 **29/30**（本判据不触及它，未强行凑，见 §5）。
合成臂：**+3 臂 / +6 单元全绿**（`test_repros/round6/r6_probe_index.json` 34 → 37 条目，
64/73 · 25 success/9 failure → **70/79 · 28 success/9 failure**，failure 逐位仍 9 条，零条绿臂转红）。

---

## 1. 凭空 sink 的证据（before → after，实测原文）

### 1.1 ORIG 边集合（入轮探针 `D:/Temp/rrv6/b111_probe.py`，per-code-object CFG）

```
b@344 last=POP_JUMP_FORWARD_IF_FALSE tgt=420 preds=[236,266,322] succs=[382,420]   ← 外层 if 的链首成员 A
b@382 last=POP_JUMP_FORWARD_IF_TRUE  tgt=496 preds=[344]          succs=[420,496]  ← B
b@420 last=POP_JUMP_FORWARD_IF_FALSE tgt=500 preds=[344,382]      succs=[458,500]  ← C1
b@458 last=POP_JUMP_FORWARD_IF_FALSE tgt=500 preds=[420]          succs=[496,500]  ← C2
b@496 last=RETURN_VALUE            preds=[382,458] succs=[]                        ← 臂体 `return default_dataframe`
b@500 last=POP_JUMP_FORWARD_IF_FALSE tgt=698 preds=[420,458] succs=[566,698]       ← if 之后的兄弟语句块
```
四条出口边各自落点：A 假边 → **链内 420**（不是任何 sink），B 真边 → 臂体 496，
C1/C2 假边 → 汇合 500。函数**最后二块**是 3524 `LOAD_FAST df; RETURN_VALUE` 与
3528 `LOAD_FAST default_dataframe; RETURN_VALUE`（dis 原文），
**ORIG 全函数没有任何 `LOAD_CONST None; RETURN_VALUE` 尾块**。

### 1.2 PROD（入轮）原文

```
off3526 LOAD_FAST df / off3528 RETURN_VALUE
off3530 LOAD_FAST default_dataframe / off3532 RETURN_VALUE
off3534 LOAD_CONST None / off3536 RETURN_VALUE          ← 凭空 sink：位于 PROD 末块之后 +2 指令
blk@344(line329 `if len(start) != 8:`) preds=[236,266,322] succ=[3534, 384]  ← A 的假边被改投凭空 sink
终态表达式 return 块 off3530（= ORIG 3528）比 ORIG 少一条汇入边（Round-4 登记 off3060→3528 vs →3530）
```
发射形态：`if A:` 套 `if B or (C1 and C2): return …` 再 `else:` —— 外层 if **无 else**，
其臂出口在源码里没有落点，只能落到作用域尾 ⇒ 重编译在函数尾凭空生成 `LOAD_CONST None; RETURN_VALUE`。
语义也已失真：ORIG 条件为 `(A∧B) ∨ (C1∧C2)`，PROD 形态为 `A ∧ (B ∨ (C1∧C2))`。

### 1.3 after（落地代码 + 先删后重生成）

发射单条 `if len(start) != 8 and len(start) != 12 or len(end) != 8 and len(end) != 12:`
→ 判据 79/79 status=success，即 per-instruction 序列与跳转目标逐位相同：
A 假边复原为链内落点（→420），凭空 off3534/3536 消失（指令 −2），终态
`return <expr>` 块恢复其入边。**接受形态已独立证真**：
`pyc_verify single --source D:/Temp/rrv6/b111_flat.py` = **79/79 success**
（该候选 = 在入轮产物上仅把二语句改成一条扁平混合链并把 else 体退回一层，产物只在 scratch）。

## 2. 与 B119 的关系：不是同一条规则（证明）

`[R5-B119 loopsink]` 的判据对象是 **CFG 里真实存在的相邻二 sink 块**
（`_is_trivial_sink`：`len(instructions)==2` ∧ `LOAD_CONST None`+`RETURN_VALUE` ∧ 无后继 ∧ 恰一前驱 ∧
前驱末指令是送出区域的跳转 ∧ 至少一条来自 LoopRegion 角色块）。本单元逐条不成立：

1. **ORIG 里根本没有 sink 块可归属**（§1.1：末二块都是表达式 return，全函数无 `LOAD_CONST None;
   RETURN_VALUE`）。PROD 的 3534 是**重编译 our 发射源码时新造的**，不在任何被分析的 CFG 中，
   因而不在 `_loop_tail_exit_sink_pair()` 的输入域内 ⇒ 把该判据的宿主从「循环自然出口」
   放宽到「if 臂出口」对此单元命中数恒为 0（放宽也无法闭，且会误伤 quotation.get_stock_exrights
   —— Round 5 §2.1 已实测那条 C3 收窄不可撤）。
2. **「每条入边各得一份落点」在此不可由抑制发射实现**：臂出口的落点必须是一个语句级位置。
   若保留 PROD 的二层嵌套，则 C1 必须同时在 A 的真路径（B 假边 → C1）与 A 的假路径
   （A 假边 → C1）上求值 ⇒ 只能**复制链成员的语句**（形状纪律明令禁止）或改投他处。
   唯一正确形态是扁平混合链（§1.3 实测 79/79）。
3. 真正的破口在**归约期的边归属**，与 sink 无关：BoolOp 链本已在主扫描建成
   `[(344,and),(382,or),(420,and),(458,and)]`（`D:/Temp/rrv6/b111_walk.py` 原文：
   `_create_boolop_region_from_chain start=[(344,'and'),(382,'or'),(420,'and'),(458,'and')] -> BoolOpRegion`），
   随后在 `_identify_boolop_regions` 的「循环条件前缀剥链」步被剥成残链
   `[(382,or),(420,and),(458,and)]`（`D:/Temp/rrv6/b111_split.py`：`_identify_boolop_regions`
   返回后已是残链 ⇒ 剥链就在该步内），344 降级成外层 if 条件块，并出现一块两主
   （IfRegion@344.blocks ∋ 382 与 BoolOpRegion/IfRegion@458 同持 382，原则 2 被破坏）。

**新规则的表述（归属门）**：一个链成员可以被改判为「某循环的条件前缀」并被剥去，
唯一身份证据是**该块正是该 LoopRegion 的 `condition_block` 角色块**；
「从 condition_block 沿 `POP_JUMP_*_IF_*` 前驱反向可达」不构成归属。
实测越权现场（`D:/Temp/rrv6/b111_loop.py`）：5 个循环
（cond=710/1070/1430/1790/2150，均为 if/elif 阶梯内层 while）的可达集都等于
`[344, 382, 420, 458, 500, 698, …, cond]` —— 逃逸路径是「链的汇合块 500 本身以
POP_JUMP_FORWARD_IF_FALSE 结尾」，于是一条与循环毫无关系的 if 臂条件被当成循环条件前缀剥掉。
剥链后 `_guard_idx` 按名字集合求交（bv(344)={len,start} ∩ rv={BASE_DIR,end_year,files,
start_year,stock_code,stock_dir,type_dir}=∅）也无从否决 ⇒ 必须用角色身份门，而不是形状/计数门。

与工单点名的两条已被否证路线的关系：(a) B121 的「放宽 sinkexit 目标形状测试」——本票**未**触碰
`_boolop_chain_exits_are_distinct_sinks`（该门对本单元求值即在 `succs` 非空处返回 False，不拦折叠）；
本票改的是折叠**之后**的剥链归属，正是 B121 §3 重归因的「边落地」侧。(b) B120 的
`region_analyzer.py:4881/4891/5221/5234` 与 `dominator_analyzer.get_all_loops` 路径未被使用；
`Region.exit` 仍零消费者、`_trailing_rn_exit_count` 仍 2 处未动。

## 3. 代码落点

- 新判据 `RegionAnalyzer._boolop_member_is_loop_condition_entry()`（紧邻
  `_loop_tail_exit_sink_pair` 之前，与 R4-B116 / R5-B119 同属出口边归属家族），
  六项 ①算法依据 ②归约顺序 ③唯一归属判定 ④嵌套处理 ⑤入口引用语义 ⑥反编译流程 + C1/C2/C3 齐备；
  输入全在白名单内（块对象身份 + LoopRegion 角色字段 + 区域成员集合），
  无文件名/函数名/偏移特判、无深度或计数上限、无文本后处理、无禁止前缀命名、
  不复制任何 sink 语句、不发射死代码。
- 唯一消费点：`_identify_boolop_regions` 的剥链步（`_found` 求值处）一处 +
  该方法 docstring 的 Step 4c 归属说明（六项 + C 条款就地补齐）。
- 生成端零改动：缺陷不是「多发射一条语句」，而是「归约期把成员改投了错误的宿主」，
  抑制发射无处可抑制（§2 证明 1）。

## 4. 门禁读数（终态 = 落地代码，产物先删后重生成）

```
single quote_handler                78/79 → 79/79  status=success                  ← 本票锚点翻转（整文件翻面）
single handlers                    29/30（仍 TWHThreadController._target）          未回退、未被强凑
batch round6/r6_probe_index（追加前）64/73 单元  34 文件  25 success / 9 failure    = 基线逐位
batch round6/r6_probe_index（追加后）70/79 单元  37 文件  28 success / 9 failure    +3 臂全绿，零绿臂转红
batch round1/r1_probe_index        108/110 单元  46 文件  44 success / 2 failure    STAY
batch round1/r1_regress_index       34/34  单元  17 文件  17 / 0                    STAY
batch round2/r2v3_probe_index      105/126 单元  62 文件  41 / 21                   STAY
batch round3/r3_probe_index        101/122 单元  56 文件  35 / 21                   STAY
batch round4/r4_probe_index（40 臂） 77/87  单元  40 文件  30 / 10                   STAY
pytest 六套件                      277 passed / 2 failed / 2 xpassed
                                  （仍 test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function）= 基线
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；compileall -q core rc=0
```

42 个 pin（先删后重生成再判，**全部 = 基线，零回退**）：trading_dates_mixin 14/14 · stock_position 37/37 ·
cgroup_utils 8/8 · email_utils 4/4 · calexrights_func 8/8（二份）· future_contract_info 29/29 ·
fly/logger 64/64 · IQData/utils/logger 28/28 · ptradeAccount 137/137 · executor 10/10 · history_api 19/19 ·
quote 86/92 · trade_live_broker 118/128 · IQCommon/strategy 2/2 · IQEngine/core/strategy 20/20 ·
plugin_fly_data/strategy 26/27 · IQData/api/api_base 27/28 · IQEngine/api/api_base 49/49 ·
matcher 16/17 · IQCommon/data/finance 31/32 · local_variables/finance 132/132 · bar 84/85 ·
local_variables/bar 22/22 · fly/common/function 4/4 · risk_calculation/function 15/15 ·
plugin_system_trade/function 70/71 · load_daily 26/27 · realtime_event_source 12/13 ·
IQCommon/profiler_func 17/17 · IQData/utils/profiler_func 15/15 · IQEngine/utils/profiler_func 17/18 ·
flytools 65/66 · **quotation 153/153 success** · klinedata 61/64 · wizard_quant_api 55/58 ·
handlers 29/30 · real_quote 43/45 · risk_calculation/__init__ 41/43 · order_api 35/37 · trade_info_utils 37/41。
逐文件失败单元名单亦与基线同位（quote 仍 build_current_period_df/check_frequency/…；
klinedata 仍 get_kline_by_count_new/get_multiminute_his_data/kline_datetime_list；
wizard 仍 filter_desicion + 二条 genexpr）⇒ **无「翻转一个单元、输掉另一个单元」**。
未跑 402 八分片批（按工单由主代理持有）。

## 5. 标记 · True-hits vs flips · 残留

```
新增标记 [R6-B111 armscope]：3 处（新判据 docstring ×1、剥链步消费点注释 ×1、
  _identify_boolop_regions docstring Step 4c ×1）
必须存活的标记（core/cfg 三文件合计，逐条 = 基线）：
  [R2-B106] 4 · [R2-B107] 7 · [R2-B108] 5 · [R3-B115] 1 · [R3-B109] 3 ·
  [R4-B116 sinkexit] 4 · [R5-B100-armjoin-trueentry] 4 · [R5-B119 loopsink] 3
残留 grep（python 计数）：禁止前缀新增方法 0；Region.exit 写入 0；_trailing_rn_exit_count 2（未动未消费）；
  新符号只 `_boolop_member_is_loop_condition_entry` 3 处（def + 消费 + docstring 引用）；
  硬编码深度/数量/语句上限 0；文件名·函数名·偏移特判 0；文本后处理 0；复制 sink 语句 0。
True-hits vs flips：
  True-hits（拦截次数）= quote_handler.get_kline_local 1 条链 ×5 个越权循环（§2 实测），
  合成臂 2 条（a01/a02）；quotation/handlers/ptradeAccount 等 42 pin 上判据拦截未改变任何读数
  （读数逐位 = 基线）⇒ 命中不扩散。
  flips = 语料单元 1（get_kline_local Different→Equal，文件 78/79→79/79 翻面）
          + 合成臂 2（deform 实测，见下）。
判据实弹可反证性（deform，`D:/Temp/rrv6/b111_finish.py`：同进程把判据桩为「恒 True」= 入轮语义再发射）：
  生产态   a01 2/2 success · a02 2/2 success · a03 2/2 success
  桩态     a01 ***<module>.r6_b111_a01: Different control flow  units=1/2
            a02 ***<module>.r6_b111_a02: Different control flow  units=1/2
            a03 2/2 success（对照：臂真的收尾于函数尾，判据不得越权，恒绿）
  ⇒ a01/a02 为常驻牙齿（只有本判据在场才绿），a03 为必须恒绿的对照。
```

**handlers 29/30 未闭（如实登记）**：本票判据不触及它 —— handlers 的 `_target` 拦路石是
Round 5 §1.2/§5 登记的「merge=412 须改判为 else 臂入口」，与本票的「链成员被越权改投循环条件前缀」
不是同一件事；未强行放宽（那会踩回 R5 §2.1 已证的 C3 收窄）。

**新观察到的独立残余（未在本票投资）**：造臂时 `total = total % 7` 形态的同宿主孪生
（`D:/Temp/rrv6/b111_a02v.py` 第一版）在判据在场时仍 1/2 Different control flow，
而 `total = total + limit` 形态 2/2 success ⇒ BINARY_OP `%` 参与的臂尾兄弟语句另有一条
边落地/发射残缺口，本票未归因、未修，登记为 B111 轴的邻位残余。

## 6. 索引追加（交付物 4 已执行）

`test_repros/round6/r6_probe_index.json` 34 → **37** 条目，新增三臂（`.py` / `.pyc` / `OK.py` 三件套齐备，
索引内**全部 37 条**路径逐一核对 missing=0，含既有 34 条）：

```
r6_b111_a01_armchain_twin       混合链 if 臂出口 + 终态表达式 return、臂后无兄弟语句      2/2 success（桩态 1/2）
r6_b111_a02_armchain_sibling    同一臂出口，臂后有兄弟语句                                2/2 success（桩态 1/2）
r6_b111_a03_armends_fn_control  对照：臂真的收尾于函数尾（判据必须不越权）                2/2 success（桩态亦 2/2）
```
追加后 r6 读数 70/79 单元 · 28 success / 9 failure ⇒ 相对追加前 64/73 · 25/9 为纯增量，
原 9 条红臂逐位不变。

## 7. 终态文件完整性（落地态，非回滚态）

```
core/cfg/region_analyzer.py      2052197 → 2058547 bytes / CRLF 32266 → 32336 / 前导 BOM 1 → 1 /
                                 全 CRLF（bare LF 0 → 0）/ sha256[:16] 0212c54e4d0c790e → 38a1d5142d132fd7
core/cfg/region_ast_generator.py 3685863 bytes / CRLF 58685 / BOM 1 / sha256[:16] 9c36c741bd972593  ← 未触碰，逐字节不变
core/cfg/code_generator.py       299897 bytes / CRLF 6022 / 无 BOM / sha256[:16] 28aba10bae133952   ← 未触碰
```
