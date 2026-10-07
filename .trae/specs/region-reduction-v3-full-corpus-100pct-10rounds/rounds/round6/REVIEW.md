# Round 6 · REVIEW（测试工程师：诊断 only，未改任何生产码，未手改任何 `*OK.py`）

轮次：rr-v3r06 · 判据唯一 `scripts/pyc_verify.py`（ruler `compare_pyc_sha256=9c7567bd6776b36b`，interp 3.11.7）
产物一律**先删后** `python -X utf8 pycdc.py -o <base>OK.py <pyc>` 重生成。
插桩全部在 `D:/Temp/rrv6/`（probe_units.py 逐指令差、probe_cfg.py 块/前驱/落点差、probe_targets.py 落点差、
make_repros*.py 复现生成器），生产目录零新增脚本。
探针口径：`orig pyc` 的 code object vs `compile(<base>OK.py)` 的同 qualname code object；
每条指令令牌 = `OP(名字/常量) ->#流内序号@绝对偏移`；**先剥掉落点序号再对齐**（difflib），
因此「bare 令牌序列全等、仅落点不同」会被单独识别（本簇最强信号），而纯偏移位移伪影不产生 hunk。

---

## I. 四个靶的入轮读数（实测原文，产物重生成后复判）

```
single site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc  status=failure units=118/128  (10 单元，与移交名单逐位相同)
single site-packages/fly/data/quote.pyc                                          status=failure units=86/92    (6 单元，同名单)
single site-packages/IQCommon/api/klinedata.pyc                                   status=failure units=61/64    (3 单元，同名单)
single site-packages/IQCommon/strategy/wizard_quant_api.pyc                       status=failure units=55/58    (3 单元，同名单)
```
未触碰 `quotation.pyc`（153/153 锚点）。未跑 402 八分片批与 34-set（按工单纪律）。

---

## II. 靶 #1 trade_live_broker：10 单元的逐单元首个真分歧 + 聚类裁决

10 个失败单元**确实全是 `TradeLiveBroker` 的兄弟方法**（名单核实无误）。
但「8/10 同一构造」**不成立**；按落点/指令签名实测分成 6 组，最大组 = **3/10**，
把两两相邻组合并后的最强同因族 = **6/10**（证据见下）。

### G-A｜流内逐字节相同、**恰一条边落点不同**（3/10）

| 单元 | orig/prod 指令数 | 唯一真分歧（op + off + 落点） |
|---|---|---|
| `_process_tick_order` | 188/188 | `#32 @178 JUMP_BACKWARD`：orig→`@130`（`LOAD_GLOBAL LOAD_FAST LOAD_ATTR PRECALL`＝体内语句块头），prod→`@114`（`LOAD_FAST LOAD_ATTR EXTENDED_ARG POP_JUMP_FORWARD_IF_FALSE`＝外层循环测块）。preds 表逐位相同，`total jump diffs = 1` |
| `rzrq_credit_order` | 786/786 | `#459 @2368 JUMP_FORWARD`：orig→`@2534`，prod→`@2506`（−28B＝早一个块）。`total jump diffs = 1` |
| `get_ipo_stocks` | 497/497 | `#211 @1108 POP_JUMP_FORWARD_IF_TRUE`：orig→`@1154`（blk30 汇合块，preds 原=[23,27,28]）prod→`@1130`（blk26 回边块，preds 变=[23,25]）＝一条 `continue` 回边被吸进短路链的出口 |

⇒ 三条单元的**指令多重集与顺序完全相同**，只有**一条边的落点**不同。这正是 R4-B116 / R5-B119
已经确立的事实「源码形不可辨识 ⇒ 只能按落点/汇合归属拆区」的**第三个边类**：
既不是终结 `return None` sink 对（B119），也不是短路链的终结 sink 出口（B116），
而是 **①体内语句块头 vs 循环测块的 continue 落点**、**②汇合块落点**。

### G-B｜循环头 NOP 认领块消失 + 回边重落点（3/10，其中 2 条级联成死码蒸发）

三条单元的首个真分歧**形状完全相同**（`probe_units` hunk 原文）：

```
_process_order          h0 delete o@44(n=1)  = NOP  | h1 delete o@92 = EXTENDED_ARG | h2 delete o@96(n=34)  → 520→42  (−478)
_process_cancel_order   h0 delete o@44(n=1)  = NOP  | h1 delete o@92 = EXTENDED_ARG | h2 delete o@96(n=32)  → 344→40  (−304)
_trade_status_handle    h0 delete o@44(n=10) = NOP + `self.trade_info = trade_status = get_trade_status(self.trade_id, True)` → 130→126 (−4)
```

`_trade_status_handle` 的 CFG 对照是本组决定性证据（orig/prod 各 14 块）：

```
ORIG  blk1  @44  n=1 NOP            preds=[0,4]    ← 外层 while True 的头认领块；体内 continue 落在这里
      blk2  @46  n=20 POP_JUMP…IF_FALSE preds=[1,13] succ=[13(@830),3(@150)]  ← 块首 10 条是体内语句 1446
      blk13 @830 n=8  JUMP_BACKWARD → @46           ← 自然回边落在测块
PROD  blk1  @70  n=6  （NOP 块整块消失）
      blk12 @774 n=6  POP_JUMP_BACKWARD_IF_TRUE → @94   ← 测式被改写为反向条件跳
      blk13 @798 n=8  RETURN_VALUE                      ← 回边被换成函数尾 sink
```
产物源码实形（`trade_live_brokerOK.py:897-914`）= `while self.trade_status != trade_status: … else: time.sleep(0.5)`，
即 orig 的**外层无条件循环 + 体内首语句**被拍平成一个条件循环：NOP 头块与其认领身份消失、回边换成 `return None`、
体内首语句被外提为 `trade_status = self.trade_info[2]`。
`_process_order` / `_process_cancel_order` 同因级联：产物把 `break` 放在体内第一条语句之前
（`OK.py:425-430`、`523-…`），CPython 3.11 的不可达块消除随后把 break 之后的整个体（478/304 条）删掉；
`dis` 实测产物 `_process_order` 覆盖的行集 = `[423,424,425,426,427,428,429,495]`（430-493 无一行进入字节码）。
⇒ −478/−304 是**发射形**造成的，不是判据伪影；h0/h1/h2 的 NOP 与 EXTENDED_ARG 不可豁免（§5.3），
因为该 NOP 正是回边/continue 的落点块。

### G-C｜函数尾回边缺失（1/10）：`ipo_stocks_order` 786… orig 1206/prod 1203，
仅 2 个 hunk：`EXTENDED_ARG @2810` 与 `EXTENDED_ARG + JUMP_BACKWARD → #453@2380 @3572`。
即 G-B 的「回边被换成尾 sink」的轻量形态（其余指令逐位相同）。落点缺失的边是**外层循环的自然回边**。

### G-D｜语句块跨区搬移（1/10）：`etf_basket_order` 769/769（delta 0，2 hunk）
同一 11 条块（`strategy_log.warning('该股票【%s】行情数据异常') … POP_TOP POP_TOP LOAD_CONST None`）
从 orig@1328 消失、在 prod@2448 重现 ⇒ 纯搬移，不是增删。

### G-E｜短路链出口被换向（1/10）：`_sync_worker` 412/410（8 hunk）
h0 delete o@362(n=22)（块首 `POP_JUMP_FORWARD_IF_TRUE → @704`）、h1 delete o@544(n=18)、
h2 insert p@526(n=6) 以 `RETURN_VALUE` 收尾 ⇒ 两块语句被搬移且链出口换成终结 sink。
本单元**未归到具体判据**（见 §VIII）。

### G-F｜常量面（1/10）：`etf_purchase_redemption` **Different bytecode**，427/415（−12）
实测指令级差（非控制流）：orig `@2274 LOAD_GLOBAL(strategy_log) LOAD_ATTR(info) LOAD_GLOBAL(_) LOAD_CONST('生成订单，订单号：')`
→ prod `@2274 LOAD_CONST('list_info00orderstrresultentrust_noselforderorderselfstrorderselforderselforderstrategy_log_生成订单，订单号：')`，
并随后逐条缺 `LOAD_ATTR(order_id) @2312`、`LOAD_ATTR(symbol) @2328`。
⇒ 产物把 f-string 的**插值字段名当字面量拼进了常量**（`{order.order_id}` 的名称残片进入 LOAD_CONST），
`{!s}` 转换标记丢失。这是**表达式发射面**，与区域落点无关。

**聚类裁决（回答交办问题）**：
「8 of 10 共享一个构造」**被实测否证**。真实分布：
G-A=3、G-B=3、G-C=1、G-D=1、G-E=1、G-F=1。
若按「边落点/认领归属」这条**轴**合并，G-A+G-B+G-C = **7/10** 同轴（其中 6/10 的**首个**真分歧就是一条跳边的落点
或承载落点的 NOP 头块），`etf_purchase_redemption`（常量面）与 `_sync_worker`（未归因）在外面。

---

## III. 靶 #2 fly/data/quote.pyc（6 单元）

| 单元 | verdict | orig/prod | 首个真分歧 | 折扣掉的伪影 |
|---|---|---|---|---|
| `build_current_period_df` | Different bytecode | 124/113（−11） | h0 `EXTENDED_ARG @14` delete；真差在常量/格式化面，3 个 hunk | EXTENDED_ARG 位移伪影 1 条 |
| `check_frequency` | Different control flow | 132/133（+1） | h0 replace `@456 LOAD_CONST None + RETURN_VALUE`（2 条）→ prod `JUMP_FORWARD → #129@558`（1 条）＝**终结 sink 被换成跳进汇合块** | — |
| `get_real_from_zeromq` | Different control flow | 793/791 | h0 insert `p@1024 JUMP_FORWARD → #192@1034`＝多插一条正向跳边 | 后续 hunk 为位移重编号 |
| `run_individual_transform` | Different control flow | 412/359（−53） | h0 delete `o@640(n=7)`＝`message = socket.recv(); if message:`（`POP_JUMP_FORWARD_IF_FALSE → @1050`）整块丢失 ⇒ 语句搬移/吞失，与 #1 的 G-D 同族 | — |
| `run_tick_socket` | Different control flow | 347/348（+1） | h0 insert `p@66 EXTENDED_ARG`（跳距增大，随后有真跳边改动） | EXTENDED_ARG 本身 |
| `get_individual_data` | Different control flow | 354/355（+1，**仅 1 个 hunk**） | insert `p@1120 JUMP_FORWARD → #207@1126` | — |

⇒ 本文件的 4 条（`check_frequency`、`get_individual_data`、`get_real_from_zeromq`、`run_tick_socket`）
与 #1 的 G-A/G-C 同轴：**sink ↔ 正向汇合跳边 ↔ 回边**的落点唯一归属；`run_individual_transform` 属语句搬移族；
`build_current_period_df` 属常量面族。

---

## IV. 靶 #3 klinedata（3 单元）—— 与 #2 同轴的直接证据

```
get_kline_by_count_new      650/649  h0 replace o@2924: EXTENDED_ARG + JUMP_BACKWARD → #230@1268
                                          → prod JUMP_FORWARD → #608@3074     ← 回边被换成正向退出跳
get_multiminute_his_data    535/536  h0 replace o@2708: JUMP_FORWARD → #533@2758
                                          → prod LOAD_FAST(his_data_dict); RETURN_VALUE   ← 汇合跳被换成终结 return
kline_datetime_list         413/417  7 hunk，h0 仅 EXTENDED_ARG 位移（未逐个归因）
```
**同一条边的两种极性互为镜像**（回边↔正向跳↔终结 sink），跨 3 个文件出现，是本轮最硬的同因证据。

---

## V. 靶 #4 wizard_quant_api（3 单元）+ B113 双胞胎实测

* `filter_desicion` 195/197：**单个 hunk** = prod 末尾多出 `LOAD_CONST None; RETURN_VALUE`
  ⇒ 与 §III/§IV 同一「终结 sink 材料化 vs 落到既有 sink」轴。
* `get_DMI.calculate_di.<genexpr>` ×2（**同 qualname 三个 genexpr，实测两两配对**）：

```
genexpr@orig388  64 条 → prod 50 条（−14）：缺一段 `… COMPARE_OP; POP_JUMP_FORWARD_IF_FALSE` 第二合取测试块
genexpr@orig390  64 条 → prod 50 条（−14）：同上
genexpr@orig385 / orig406  46/46、26/26  ⇒ EQUAL（同文件内的天然对照组）
父块 calculate_di 本身逐位相同（90/90）
```
机制：genexpr 的 `if A and B` 过滤式被只发成 `if A`（第二个合取腿的测试块 14 条整体丢失），
区域宿主 = **genexpr 隐式 FOR_ITER 区 + 闭包单元（COPY_FREE_VARS / MAKE_CELL / LOAD_DEREF）**。

**B113 双胞胎（交办点）：本轮 5 个 genexpr 合成臂全部 MATCH ⇒ 双胞胎未取得（诚实登记）**：
`r6_g6_genexpr_and_spec`（`if A and B`，参数为 fast locals）、
`r6_g6_genexpr_doubleif_ctl`（`if A if B`，语形等价负例）、
`r6_g6_genexpr_single_ctl`、`r6_g6_genexpr_or_spec`、
`r6_g6_genexpr_nestedhost_spec`（外层 for 宿主 + 嵌套 genexpr）——判据读数全为 `success 2/2`。
方向性结论：丢失只发生在**操作数是闭包自由变量（LOAD_DEREF）**的 genexpr 过滤式上；
下一步双胞胎应把 `high/low` 改成外层函数的变量（形成 cell），并把 `sum(...)` 外套一条语句。

---

## VI. 合成复现（`test_repros/round6/`，34 个臂）与自检批读数

自跑判据（唯一判据，原文）：

```
$ python -X utf8 scripts/pyc_verify.py batch --index test_repros/round6/r6_probe_index.json --json D:/Temp/rrv6/r6_batch_union.json
[ 1/34] success 2/2 r6_g1_forhost_ctl.pyc        ← 逐条见下
{ "files_total": 34, "units_total": 73, "units_success": 64, "success_rate": 0.8767,
  "files_by_status": {"success": 25, "failure": 9, "compile_error": 0, "error": 0}, "elapsed_sec": 0.9,
  "ruler": {"compare_pyc_sha256": "9c7567bd6776b36b"}, "interpreter": "3.11.7" }

MISMATCH 文件 9 / MATCH 文件 25（MISMATCH 单元 9、MATCH 单元 64）
  r6_g1_forhost_spec / r6_g1_forhost_ctl / r6_g1_tickloop_ctl / r6_g1_tickloop_ctl2 /
  r6_g1_tryhost_spec / r6_g1_tryhost_ctl / r6_g2_hdrbreak_spec /
  r6_q2_whilehost_spec（Different bytecode @line6 off6）/ r6_q4_tryhost_spec
```

逐臂首个真分歧（合成臂，`probe_units` 原文摘要）：

| 臂 | 读数 | h0 | 一句构造改动 → 翻面 |
|---|---|---|---|
| `r6_g1_tickloop_ctl`（`while True:` 内层空体） | MISMATCH | delete `NOP @46` | `pass`→`continue` ⇒ `r6_g1_tickloop_spec` = **MATCH 2/2** |
| `r6_g1_tickloop_ctl2`（无内层 `while True`） | MISMATCH | delete `NOP @46` | 加回内层无条件循环 ⇒ spec MATCH |
| `r6_g1_forhost_spec/ctl`（宿主＝`for`） | MISMATCH | delete `o@14(n=14)`（NOP+`len(q)` 测块+回边） | 宿主 `for`→函数级 ⇒ **membership/host 轴**，与深度无关 |
| `r6_g1_tryhost_spec/ctl`（宿主＝`try`） | MISMATCH | delete `o@2(n=18)`（NOP+`if flag`） | 同上 |
| `r6_g2_hdrbreak_spec`（体首 try/finally + break + `if in tuple: …; continue`） | MISMATCH | delete `o@386(n=5)` | 删掉 `if status in (STOP,DELETE): log; continue` 一臂 ⇒ `r6_g2_hdrbreak_ctl` = **MATCH 2/2** |
| `r6_q2_whilehost_spec` | MISMATCH | 行 6 偏移 6 常量面 | 删掉 `else: … ; return None` ⇒ `r6_q2_whilehost_ctl` = **MATCH 2/2** |
| `r6_q4_tryhost_spec` | MISMATCH | Different control flow | 删掉 except 臂尾 `return None` ⇒ `r6_q4_tryhost_ctl` = **MATCH 2/2** |
| 必须存活的 MATCH 对照（任何修复后仍须 success） | | `r6_g1_tickloop_spec`、`r6_g2_hdrbreak_ctl`、`r6_g2_twoloop_spec/ctl`、`r6_g3_chainexit_spec/ctl`、`r6_g4_reloc_spec/ctl`、`r6_g5_fstring_spec/ctl`、`r6_g6_*`（5 臂）、`r6_q1/q3/q5/q6` 双臂 | |

**自证伪的臂（如实登记）**：
1. `r6_g1_tickloop_spec/ctl` 命名反了 —— 真 MISMATCH 体在 `ctl` 侧：本簇的判别构造**不是「continue 的落点」**，
   而是「无条件循环头 NOP 认领块在宿主为 `for`/`try`/空体时是否存活」。这条臂证伪了我自己先写的假设。
2. `r6_g3_chainexit_spec/ctl`、`r6_g4_reloc_spec/ctl`、`r6_g5_fstring_spec/ctl`、`r6_g6_*`、
   `r6_q1/q3/q5/q6` 全部 MATCH ⇒ 我按「汇合/搬移/常量/genexpr」写的 12 条 spec **未能复现**对应语料形；
   这些机制目前只有语料自身与逐指令证据，缺合成臂。

---

## VII. 破口登记（自 B120 起；锚点均已 grep 核实存在于工作树）

**grep 核实记录**（`core/cfg/`，行号为实测）：
`_boolop_chain_exits_are_distinct_sinks` = `region_analyzer.py:28009`（消费点 `:28564`）·
`_loop_tail_exit_sink_pair` = `region_analyzer.py:28064`（生成端唯一消费点 `region_ast_generator.py:51571`）·
`_block_is_continue_target` = `region_ast_generator.py:12836` ·
回边选择站点 = `region_analyzer.py:4881`（`max(back_edges_for_header, key=(异常清理, 语句数, b.start_offset))`），
`break/continue` 判定 = 紧随其后的 `self._detect_break_continue(body, header, natural_exit, natural_back_edge=back_edge_block, …)`（`:4891`）·
标记 `[R4-B116 sinkexit]`×`region_analyzer.py:28010/28175/28183/28560`、`[R5-B119 loopsink]`×`region_analyzer.py:28065`+`region_ast_generator.py:51519/51563`。

| 编号 | 状态 | 机制（一句话） | 锚点（最强生产站点） | 违反条款 |
|---|---|---|---|---|
| **B120** | 已定位（仅 spec） | **无条件循环头认领块（`NOP` 落点块）归属**：外层 `while True:` 的头块与内层循环/体内首语句块同属一条正向跳的落点时，产物把外层头拍平（NOP 消失、体内首语句外提、回边换成尾 `return None`），级联时 `break` 前移触发 CPython 不可达消除，整个体蒸发 | `region_analyzer.py:4881` 的 `max(..., key=(…, b.start_offset))` 回边/头认领 + `:4891 _detect_break_continue(natural_back_edge=…)`；落点消费面 `region_ast_generator.py:12836 _block_is_continue_target` | **C3 守卫封闭** + §1.2 原则2（同块被两个候选循环争抢，无显式认领守卫）；§5.3（NOP/EXTENDED_ARG 不可一概豁免） |
| **B121** | 已定位＝**B116 判据欠 Reach** | 短路链/汇合的**出口落点**判据只认「≥2 个互不相同的终结隐式 `return None` 块」（`_boolop_chain_exits_are_distinct_sinks`，`region_analyzer.py:28009` 原文条件）；本簇链出口落在**汇合块**或**回边块**（`get_ipo_stocks`@1130、`rzrq_credit_order`@2506、`check_frequency`@558、`get_multiminute_his_data`@2758）时门恒假 ⇒ 折叠发生、只错一条边 | 同 `region_analyzer.py:28009/28564`；`[R5-B100-armjoin-trueentry]` 判别器 `region_analyzer.py:30441/30455`（同目标身份分判）为其近邻 | C1 局部消费（出口身份未在本区域消费）＋原则4；承 R4-B116/R5-B119 的**同一不变式**、条件收窄处 |
| **B122** | 已定位（仅 spec） | 语句块**跨区搬移**：一条完整语句（含其后继测）被交到相邻区域的尾/头，指令多重集不变、位置改变（`etf_basket_order` 11 条 @1328→@2448，`run_individual_transform` `message = socket.recv(); if message:` 7 条丢失） | 区域尾交付/顺序续流面：`region_analyzer.py:4891` 之后的 `break_blocks/continue_map` 消费链与 `[R5-B100-armjoin-trueentry]` 宿主裁决（Round-5 回滚票 α/父边级联同站点） | §1.2 原则2 + C1 |
| **B123** | 已定位（仅 spec）**B113 宿主面补强** | genexpr 过滤式 `if A and B` 的第二合取测试块（14 条）整体丢失；宿主为 **genexpr 隐式 FOR_ITER 区 + 闭包 cell**（`COPY_FREE_VARS/MAKE_CELL/LOAD_DEREF`）。同文件另 2 个 genexpr EQUAL ⇒ 与深度无关、与操作数是否自由变量有关 | 未定位到具体判据行（候选：短路链建区门 `region_analyzer.py:28175` 成员条件 R38 与 genexpr 区识别面）；**不得据本行改判据**，交 fix 实测 | 原则1（内层先归约）+ C3 |
| **B124** | 已定位（仅 spec）**常量/表达式发射面** | f-string 插值字段被当字面量拼进 `LOAD_CONST`（名称残片 `'…selforder…strategy_log_生成订单，订单号：'`），`{!s}` 转换标记与 `LOAD_ATTR(order_id/symbol)` 丢失 | 表达式发射面（非区域落点）；本轮未定位到具体函数，**点名站点交 fix 前先 grep** | §1.2 原则4（入口引用语义）之外，属 AST→code 发射正确性 |

**未闭/未归因**（不得据此立规则）：`_sync_worker`（G-E，块搬移 + 链出口换终结 sink 的混合形，未归到单一判据）；
`kline_datetime_list` 的 7 个 hunk 未逐个核；`build_current_period_df` 的常量面细节未展开；
`rzrq_credit_order` 未确认其错边是短路链出口还是纯汇合出口（需区域树读数）。

---

## VIII. 翻转前景排序（若只封一处机制，哪个翻最多**整文件**）

1. **B121（B116 判据欠 Reach：出口落点不限终结 `return None`）** —— 命中 **8 单元 / 3 文件**
   （`get_ipo_stocks`、`rzrq_credit_order`、`_process_tick_order`、`check_frequency`、`get_individual_data`、
   `get_real_from_zeromq`、`klinedata.get_kline_by_count_new`、`get_multiminute_his_data`）；
   单独封它最有可能把 **klinedata 61/64→62-63/64、quote 86/92→89-90/92**（整文件翻面需再补 `run_individual_transform` 与 `build_current_period_df`）。
   ⇒ **首选**。既有判据只需把「终结隐式 `return None` sink」这一条成员条件推广为
   「出口落点集合互不相同（sink/汇合块/回边块）」，属**封闭守卫**、不是语料个案补丁。
2. **B120（循环头 NOP 认领）** —— 命中 **4 单元 / 1 文件**（`_process_order`、`_process_cancel_order`、
   `_trade_status_handle`、`ipo_stocks_order`），且合成臂已有 6 条 MISMATCH 复现；
   单封它把 trade_live_broker 118→122，**翻不了整文件**（还剩 G-A×3、G-D、G-E、G-F）。
3. **B122** —— 2 单元 / 2 文件（`etf_basket_order`、`run_individual_transform`）。
4. **B123** —— 2 单元 / 1 文件；**B124** —— 1 单元 / 1 文件（且属发射面，与区域轴正交）。
> 结论：**没有任何单一机制能翻掉本轮 4 个文件中的任何一个整文件**；
> trade_live_broker 至少需 B120+B121+B122+B124 四道门同时封闭才可能 128/128。
> 若目标是「翻整文件」，最小可行靶是 **klinedata（61/64，3 单元 / ≤2 族）**：B121 + 一次 EXTENDED_ARG-only 复核。

---

## IX. 完成度与诚实声明

* 全量诊断完成：**#1 trade_live_broker（10/10 单元）**、**#2 quote（6/6）**、**#3 klinedata（3/3）**、**#4 wizard_quant_api（3/3）**。
* #4 的两个 `<genexpr>` 单元只做到**逐指令差 + 丢失块定位**，未归到具体生产判据行（同 qualname 三块，
  `pyc_verify` 名单无法区分，用 `co_firstlineno` 配对 388/390 与 385/406）。
* B113 合成双胞胎**未取得**（5 臂全 MATCH），已给出下一臂的必要条件（闭包自由变量宿主）。
* 复现臂 34 个：9 MISMATCH / 25 MATCH（64/73 单元）。其中 12 条我原以为是 spec 的臂 MATCH，
  即 **B122/B123/B124 目前无语料外合成复现**，只有语料逐指令证据 —— 修复工程师若需臂级门禁，须按 §VI 末行方向补臂。
* 生产码零改动；`quotation.pyc` 与其产物未触碰；`test_repros/round6/` 内**非本轮**文件（`n6_*`、`r6_01..r6_15`、`rv6_*`，属并行会话）
  的 `.py`/`OK.py` 一字未动（我为避免污染，已删除编译期误生成的、其原有目录中不存在的 `.pyc`）。
