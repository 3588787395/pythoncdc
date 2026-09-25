# diag4 · FACTS · Round 69（只读诊断）

臂名前缀：`r69diag4`。仓库只读，所有产物在 `D:/Temp/opencode/r69gate/diag4`。

## Step 0 · baseline replay

### 0.1 targets（`h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl`）

| 文件 | matched/total | 缺陷函数（name, orig, decomp, hunks, first_diff） |
|---|---|---|
| real_quote.pyc | 40/44 | get_cache_l2_data_by_one 321/322 h=2 fd=197；get_real_minute_kline 253/254 h=3 fd=197；get_tick_direction 259/258 h=3 fd=102；one_prod_to_ndarray 605/607 h=5 fd=424 |
| order_api.pyc | 32/34 | future_order 101/92 h=2 fd=36；option_order 83/73 h=3 fd=39 |
| realtime_event_source.pyc | 11/12 | clock_worker 1275/1286 h=10 fd=481 |

与 `targets.md` 预读数：**逐字段相同**（OFF 4+2+1=7 支，first_diff/hunks 全一致）。

### 0.2 canary（`h62.py run --arm=landed --list=canary.txt --out=dump/landed_canary.jsonl`）

| 产物 | matched/total | sha |
|---|---|---|
| quotation.pyc | 143/143 | `4d41187e356544e0` ✓ |
| market_time.pyc | 10/10 | `af77224b34b203c4` ✓ |
| IQCommon datetime_func.pyc | 26/26 | `e711b8ea86d49a15` ✓ |
| IQData datetime_func.pyc | 25/25 | `9d09af09249da177` ✓ |

与合同 §3.1 逐字节相同 ✓。

### 0.3 battery（`closeout67.py battery landed`，45 项）

- **182/200 matched**、缺陷函数 **18**（bad 列求和 2+2+1+4+1+1+4+1+2=18）、**worse-than-landed=0**、ERR=0。
- 与 BRIEF §4「45 项电池 landed：182/200、缺陷 18、worse=0、ERR=0」**逐字段相同** ✓。
- 有缺陷的 9 项：round63_b2/probe_r63b2_cases(7/9,d=+2)、probe_r63b2_cases2(7/9,d=+0)、round65_diag1/r65_trytail(8/9,d=-3)、round65_diag2/fs2(6/10,d=-12)、round67_diag4/r67d4_controls(7/8,d=+0)、round67_diag5/r67_ccprefix2(2/3,d=-1)、round67_diag5/r67_site2(4/8,d=-43)、round67_diag6/r67d6_boolop_ternary(5/6,d=-12)、r67d6_boolop_ternary2(6/8,d=-16)。

### 0.4 strict（`sstrict67.py build_landed targets.txt`）

| 文件 | strict ok/func | missing | extra |
|---|---|---|---|
| real_quote.pyc | 41/45 | 0 | 0 |
| order_api.pyc | 33/36 | 0 | 0 |
| realtime_event_source.pyc | 11/12 | 0 | 0 |
| **合计** | **85/93, defects 8** | 0 | 0 |

逐条缺陷（与 targets.md STRICT 段相同）：
- real_quote：get_cache_l2_data_by_one [seq_len] 321/322；get_real_minute_kline [seq_len] 253/256；get_tick_direction [seq_len] 259/260；one_prod_to_ndarray [seq_len] 606/608。
- order_api：base_order [target_diff] #136 POP_JUMP_IF_TRUE；future_order [seq_len] 101/93；option_order [seq_len] 83/74。
- realtime：clock_worker [seq_len] 1276/1287。

**Step 0 结论：与 BRIEF/targets 预读数逐字段相符，无更正。**


## Step 1 · hunk tables（nested_diff.py，按 code-object 全路径配对；CACHE 已滤）

判定标记：`ART`=纯 NOP/EXTENDED_ARG/JUMP 计数伪影；`MOVE`=整段位移（语句不增删）；`LOSS`=语句丢失；`DUP`=重复发射。

### real_quote.pyc（TOTAL differing 6 / 45）
| code object | orig/decomp(指令) | hunks | 判定 |
|---|---|---|---|
| /RealQuoteData#23（类体） | 131/123 | 4 | ART（4 处全为 `delete NOP NOP`，严格/官方均 OK） |
| /RealQuoteData#23/get_bar#24 | 267/266 | 1 | ART（`delete NOP`） |
| /RealQuoteData#23/get_cache_l2_data_by_one#34 | 355/356 | 1 | MOVE+ART：`insert JUMP_BACKWARD@134`（唯一 hunk，纯跳转 +1，无语句增删） |
| /RealQuoteData#23/get_tick_direction#39 | 297/299 | 3 | MOVE：`delete orig[172:202]`(30 instr, JUMP_FORWARD+`if flag==1/elif flag==-1` 臂身) → `insert decomp[268:299]`(31 instr 同体)；+1 EXTENDED_ARG ART。零语句增删 |
| /RealQuoteData#23/get_real_minute_kline#21 | 280/287 | 6 | MOVE：`delete orig[65:100]`(35 instr, `return EMPTY_DAY_BAR_NP_ARRAY`+`datetime.now()` 段) → `insert decomp[221:259]`(38 instr 同体)；4 处 EXTENDED_ARG ART。零语句增删 |
| /RealQuoteData#23/one_prod_to_ndarray#11 | 659/665 | 7 | MOVE：`delete orig[389:423]`(34 instr, `int(temp_time[11:13])` 段) → `insert decomp[208:237]`(29 instr 同体)；另有 4 处 `JUMP_FORWARD→EXTENDED_ARG+JUMP_BACKWARD`（循环回边方向改变）与 `replace orig[153:155]→decomp[153:162]`(+7)。零语句净增删 |

⇒ 与 R67-diag5 结论一致：**纯位移族，零语句增删**。

### order_api.pyc（TOTAL differing 2 / 37）
| code object | orig/decomp | hunks | 判定 |
|---|---|---|---|
| /future_order#39 | 115/107 | 5 | LOSS：`delete orig[72:80]`(8 instr, `strategy_log.info(...format...)` 调用前段)、`delete orig[89:90]`/`replace orig[91:92]`(f-string 的 `'买入'/'卖出'` 常量槽)、`delete orig[104:109]`(5 instr, `order_.amount, KW_NAMES, PRECALL, CALL`)、`insert LOAD_CONST None+RETURN_VALUE`(+2)。**净 −8，分支体被空化** |
| /option_order#40 | 94/85 | 6 | LOSS：`delete orig[39:43]`(4 instr, `strategy_log.info(...)` 头)、`replace orig[44:47]→decomp[40:50]`、`insert POP_TOP`、`replace orig[60:61] LOAD_ATTR futures_direction → decomp[64:65] LOAD_ATTR hedge_type`、`delete orig[63:73]`(11 instr, `'OPEN'` 比较臂)、`delete orig[85:88]`(3 instr, `KW_NAMES,PRECALL,CALL`)。**净 −9** |

### realtime_event_source.pyc（TOTAL differing 1 / 13）
| code object | orig/decomp | hunks | 判定 |
|---|---|---|---|
| /RealtimeEventSource#20/clock_worker#5 | 1442/1458 | 14 | **DUP+MOVE+ART**：`delete orig[1192:1304]`(112 instr `persist_flag==False→set_trade_stop_status` 段) ↔ `insert decomp[1274:1409]`(135 instr 含 `before_trading_date==initial_trading_date` 与 `holiday_not_do_before=='0'` 段)；`replace orig[1097:1110]`(13 instr `event_queue.put(dt, PRE_BEFORE_TRADING_START)`)→decomp 2 instr；`replace orig[1411:1413]`(`LOAD_CONST None;RETURN_VALUE`)→`decomp[1412:1429]`(18 instr `holiday_not_do_before=='0'` 段)；`delete orig[959:976]`(17 instr 同一 `holiday_not_do_before=='0'` 段)；另有 NOP/EXTENDED_ARG/JUMP_FORWARD 伪影。**净 +16（官方 +11）** |

## Step 2 · 根因实测（每支函数）

仪器：`probe_chain.py`（区域结构）、`probe_off.py`（按 offset 定向区域）、`probe_elif.py`（elif 发射调用栈 + `generated_blocks` 命中）、`muldiff.py`（指令多重集差分，滤 CACHE）、`lines.py`（产品侧带行号反汇编）。
说明：`nested_diff.py`/`regdump.py` 不折叠 EXTENDED_ARG/NOP，故 Step 1 hunk 表含计数伪影，本节判定已剔除。

### 2.1 real_quote.pyc（4 支，全部 MOVE/位移族）

四个函数的区域结构共同签名（同一判据，覆盖 4/7）：

**`IfRegion.then_blocks` 与 `else_blocks` 在物理块序列上交错；`then_blocks` 含位于 `merge_block` 之后的块；`then_blocks` 自身内部非单调。发射固定按 then→else 次序，故物理位置靠后的块被提前发射 ⇒ 纯位移，零语句增删。**

- **get_tick_direction#39**：`IfRegion entry=858 merge=1102`，`then=[862,1106,1108,1112,1392,1124,1128,1458,1126,1174,1570,1176,1388,1224,1332,1390]`（含 1106..1570，**全部 > merge 1102**），`else=[944,956,1024,1036]`（全部 < 1102）；且存在嵌套 `IfRegion entry=944 merge=1102`（1102 为 else 独占 merge）。hunk `delete orig[172:202] ↔ insert decomp[268:299]` 正是 then 臂身被移到 else 之前。
- **get_real_minute_kline#21**：`IfRegion entry=88 merge=570 then=[110,270,358,282,370] else=[372,560]` —— then 内 **282 排在 358 之后（非单调）**；嵌套 `IfRegion entry=110 merge=358 then=[282,570,574,578,582,580,...]`（then 含 > merge 358 的 570..1308）。hunk `delete orig[65:100] ↔ insert decomp[221:259]` = `return EMPTY_DAY_BAR_NP_ARRAY`+`datetime.now()` 段位移。
- **one_prod_to_ndarray#11**：`IfRegion entry=458 merge=1720 then=[480,548,638,1530,676,798,1418,836,956,1472,1526,994,1098,1136,1240,1278,1414] else=[1588,1612,1716]` —— then 内 **1530/1418/1472/1526 与 638/676/798 交错**；另有 `LoopRegion entry=418` 自含 `LoopRegion entry=454`（自嵌套）与 `LoopRegion entry=2638` 自含 `entry=2710`。hunk `delete orig[389:423] ↔ insert decomp[208:237]` + 4 处 `JUMP_FORWARD→EXTENDED_ARG+JUMP_BACKWARD`（回边方向改变，属 ART/位移）。
- **get_cache_l2_data_by_one#34**：`IfRegion entry=616 merge=1592 then=[744,752,754,1106,802,852] else=[1108,1120,1548,1124,1590,1126,1280,1174,1224,1364,1366,1546]` —— then/else **逐块交错**（1106 在 then，1108 在 else）；`IfRegion entry=590` 的 then/else 同样交错。唯一 hunk 为 `insert JUMP_BACKWARD@134`（+1 跳转指令），零语句增删。

⇒ 四支共享同一结构签名；但**归约方式必须是"按原块位置重排发射序"**，即 BRIEF §8 所称的线性化/重排通道。该通道需读取并按块起始位置排序（等价于偏移序），与硬规则"禁按偏移启发"直接冲突，且只覆盖 real_quote 4 支、不触及 order_api(LOSS)/realtime(DUP)，无法成为"一处修多支"的安全判据。

### 2.2 order_api.pyc（2 支，LOSS 族）—— 根因与 BRIEF §8 所述线不同

`regdump.py` 读数（`/future_order#39`）：
```
IfRegion@340 then=[382] else=[386,552,556]
  elif_conditions=[386]
  inline_boolop_chains={blocks:[386(386-412), 414(414-550)], op:'or'}
```
- `muldiff`：原字节码中 `entrust_direction(...).upper()` **恰出现 1 次** ⇒ 原源码不存在 `or` 短路（原形近似 `elif not is_trade():`）。
- 两个块的跳转目标**不同**：块 386 结尾 `POP_JUMP_IF_TRUE → 676`；块 414 结尾 `POP_JUMP_IF_FALSE → 556`。合法 `or` 短路链要求两环共享同一假目标 ⇒ **该 `or` 链是分析器误构造，不是源码结构**。
- 误判后果：块 414（内含完整 `strategy_log.info(fstr.format(...))` 调用 + `'买入'/'卖出'` + `order_.amount, KW_NAMES, PRECALL, CALL`）被当作 `or` 链"第二环"，其内容按链操作数片段处理而被丢弃；块 556（三元选择的假臂）泄漏为 `else: """卖出"""`。`/option_order#40` 同形（`LOAD_ATTR futures_direction→hedge_type`、`'OPEN'` 比较臂整段删除、`KW_NAMES,PRECALL,CALL` 删除，净 −9）。

⇒ 根因位置在 **`core/cfg/region_analyzer.py` 的 `inline_boolop_chains` 形成处**，与 BRIEF §8 点名的 `region_ast_generator._try_build_ternary_kwarg_call`（生成器侧）**不是同一处**。
⇒ 但按 BRIEF §8 禁令，"R50/R65/R67 三轮同线若重走必须实测证明判据不同"——本仓库 checkout 内 `rounds/round68/specs/ADR-1` 与任何 `rounds/` 目录均不存在，**无法取证既往臂读数**，故"判据不同"无法举证 ⇒ 按禁令判 NONE。

### 2.3 realtime_event_source.pyc（1 支，DUP 族）

`probe_off.py`：`IfRegion entry=7604 then=[7630,7634,8592,8666,8688,8852,8904,8926,8948,8964,8974,8976,8980,9144]`；`IfRegion entry=7634 elif_conditions=[8592] else_blocks=[8592,8666,8688,8852,8904,...] merge=9194`；`LoopRegion entry=5598` 对象重复出现两次且互相嵌套。

`probe_elif.py`（watch=8592，打印 `_if_generate_elif_chain/_if_generate_full_elif_chain` 调用栈与 `generated_blocks` 命中）：
```
ELIFCHAIN _if_generate_elif_chain       entry=7604 cond=[8592] else=[]          cond_generated=[(8592, False)]  <<< WATCH
   region_ast_generator.py:18075 <- 11868 <- 3184 <- 22395 <- 15213 <- 18120 <- 11868
ELIFCHAIN _if_generate_full_elif_chain  entry=7634 cond=[8592] else=[8592,...]  cond_generated=[(8592, False)]  <<< WATCH
   region_ast_generator.py:11684 <- 3184 <- 22828 <- 15213 <- 18120 <- 11868 <- 3184
ELIFCHAIN _if_generate_then_branch      entry=7634 ...                           cond_generated=[(8592, False)]
ELIFCHAIN _if_generate_elif_chain       entry=7634 ...                           cond_generated=[(8592, False)]
```
- **块 8592 被两条不同路径各发射一次，且两次进入时 `8592 ∉ self.generated_blocks`**，发射后亦未被标记 ⇒ 去重条件永不成立。
- 路径 A（entry=7604，`region_ast_generator.py:18075`）位于 **[R23-A] or-extension 分支**：`L18071-18074` `if not region.elif_conditions: region.elif_conditions = _or_elif_ir.elif_conditions`（**借用另一区域的 elif 臂**），随后 `L18075` 调 `_if_generate_elif_chain(region)`。region 7604 自身 `else_blocks=[]`，却拿到了 `elif_conditions=[8592]` ⇒ 结构不一致的 elif 被发射。
- 路径 B（entry=7634，`L11684` `_if_generate_full_elif_chain`）是区域自身合法 elif，携带真实 body（`if check_handle_date(now_date): ...` else `...`）。
- `muldiff` 读数：`LOAD_FAST check_trading_time` orig@[8594] 1 次 ↔ decomp@[7802, 9056] 2 次（**+1**）；`PUSH_NULL` orig 2 / decomp 3；净 **+16 指令 ≈ 一次重复条件块（约 15–16 条）**。
- 产品侧（`lines.py`）：行 262 `if before_trading...` / 275 `elif check_trading_time(...)`（**带真体**，来自路径 B）/ 282 `elif now_date == ... and ...` / 312 `elif check_trading_time(...): pass`（**空体**，来自路径 A）。原字节码 8592（原行 527）在物理上紧跟块 8590（原行 516–524 的 `elif broker_persist is not None` 体，产品行 303–311），故**行 312 才是位置正确的一支**，而携带 body 的行 275 位置错——即 body 与位置分家，单删任一支都不可靠。

⇒ 该根因落在 **R23-A or-extension 的 elif 臂借用 + `generated_blocks` 未标记**，与 BRIEF §8 所述"elif 臂重复发射（过冲族）"同族但具体成因（跨区域借用）未在 BRIEF 中指明；BRIEF 提到的 `rounds/round68/specs/ADR-1` 在本 checkout 中不存在，无法比对。


## Step 3 · 候选判定

硬规则：「没有最小合成复现（`synth/`）就不许写 spec」。

| 支 | 候选 | 判定依据 |
|---|---|---|
| real_quote | **NONE** | 结构签名（then/else 交错 + then 越过 merge）已统一识别 4/7，但唯一可行的归约方式是「按原块物理位置重排发射序」= 线性化/重排通道，等价于读取并按块起始位置排序，直接违反硬规则「禁按名字/偏移启发」；且该通道只覆盖 real_quote，不触及 order_api(LOSS)、realtime(DUP)，不构成「一处修多支」。按 BRIEF §8「要么给统一判据（一处修多支），要么如实 NONE」⇒ NONE。 |
| order_api | **NONE** | 根因已定位到 `region_analyzer.inline_boolop_chains` 误构造（两环跳转目标不同、原码 `or` 只出现 1 次，实测证伪），与 BRIEF §8 点名的生成器 `_try_build_ternary_kwarg_call` 不同处。但 BRIEF §8 要求「重走 R50/R65/R67 同线必须先实测证明判据与既往臂不同」；本 checkout 无 `rounds/` 目录、无 `rounds/round68/specs/ADR-1`，既往臂读数不可得，「不同」无法举证 ⇒ 按禁令判 NONE。 |
| realtime | **NONE** | 根因实测为「块 8592 被 R23-A or-extension 的 elif 臂借用路径与区域自身 elif 路径各发射一次，且两次进入时 `8592 ∉ generated_blocks`，发射后亦未标记」。但产品侧两支的 **body 与位置分家**（带 body 的行 275 位置错、位置正确的行 312 是 `pass`），单删任一支都会引入新缺陷（删 A 则丢 body、删 B 则 `check_trading_time()` 调用次数改变）；正确的修法需要同时重挂 body，属跨区域归属重排，无 `synth/` 最小复现可验证其不波及其他链 ⇒ 不落 spec。 |

因此本轮 **不产生 `specs/cand_r69_*.json`，不跑 `h62 build/run/ab`**（无候选即无 A/B）。

## Step 4 · 门禁复核（本轮未改落地代码，故全部为 Step 0 读数的再确认）

- 落地 arm 未被修改：`F:/Downloads/pythoncdc-main` 全程只读，未执行任何 `git` 写命令，未触碰 `*OK.py`，未更新 `pyc_index.json`。
- 因无候选，`h62.py build/run/ab`、`closeout67.py battery`、`sstrict67.py`、canary sha 均**不需要重跑**；Step 0 记录的读数即为本轮最终读数：
  - targets：real_quote 40/44、order_api 32/34、realtime 11/12，OFF 7 支，与 `targets.md` 逐字段相同。
  - canary：143/143 `4d41187e356544e0`、10/10 `af77224b34b203c4`、26/26 `e711b8ea86d49a15`、25/25 `9d09af09249da177`。
  - battery：182/200、缺陷 18、worse=0、ERR=0。
  - strict：41/45 + 33/36 + 11/12 = 85/93、defects 8、missing 0、extra 0。

## Step 5 · VERDICTS

| # | 靶 | 函数 | 根因（实测） | 族 | 判定 |
|---|---|---|---|---|---|
| 1 | real_quote | get_cache_l2_data_by_one#34 | IfRegion@616/@590 then/else 物理块交错（1106→then, 1108→else），发射按 then→else 定序 | MOVE | **NONE** |
| 2 | real_quote | get_real_minute_kline#21 | IfRegion@88 then 非单调（358 排在 282 前），嵌套 IfRegion@110 then 含 >merge(358) 的块 | MOVE | **NONE** |
| 3 | real_quote | get_tick_direction#39 | IfRegion@858 merge=1102，then 含 1106..1570（全 >merge），else 全 <merge，嵌套 IfRegion@944 merge 同为 1102 | MOVE | **NONE** |
| 4 | real_quote | one_prod_to_ndarray#11 | IfRegion@458 then 内 1530/1418/1472/1526 与 638/676/798 交错；LoopRegion@418/2638 自嵌套 | MOVE | **NONE** |
| 5 | order_api | future_order#39 | `inline_boolop_chains` 把 [386,414] 误判为 `or` 链（两环目标 676 vs 556 不同、原码 `or` 仅 1 次），块 414 全体被丢、块 556 泄漏为 else | LOSS | **NONE**（§8 举证不可得） |
| 6 | order_api | option_order#40 | 同上（`'OPEN'` 比较臂 + `KW_NAMES,PRECALL,CALL` 整段被丢，净 −9） | LOSS | **NONE**（同上） |
| 7 | realtime | clock_worker#5 | 块 8592 被 R23-A 借用路径（L18071-18075, region.else_blocks=[] 却得 elif_conditions）与区域自身路径各发射一次，`generated_blocks` 两次均未命中且未回填；body 与位置分家（275 带体、312 为 pass） | DUP | **NONE** |

**总计：候选 NONE，7/7 缺陷本轮不改；落地读数与 Step 0 相同（targets 83/90、canary 204/204、battery 182/200 defects 18 worse 0 ERR 0、strict 85/93 defects 8）。**

## 对 BRIEF / 预读数的更正

1. **`rounds/round68/specs/ADR-1` 在本仓库 checkout 中不存在**（`F:/Downloads/pythoncdc-main` 下无 `rounds/` 目录），工作区 `D:/Temp/opencode/r69gate` 下也无该文件。因此 §8 要求的「实测证明判据与既往臂（R50/R65/R67）不同」**无法取证**——这是本轮 order_api 判 NONE 的直接原因，不是根因缺失。
2. **order_api 的根因位置与 §8 点名处不同**：§8 指向 `region_ast_generator._try_build_ternary_kwarg_call`（生成器侧）；实测证据指向 `region_analyzer.py` 的 `inline_boolop_chains` 形成处（分析器侧），且该 `or` 链经「两环跳转目标不同 + 原码 `or` 仅出现 1 次」双重证伪。后续轮次若重走此线，应从分析器侧取证，而非生成器侧。
3. **Step 0 读数与 BRIEF/targets 无差异**：targets 40/44、32/34、11/12；canary 143/143、10/10、26/26、25/25；battery 182/200/18/0/0；strict 85/93/defects 8——逐字段一致，无需更正。
4. **仪器注意（不影响读数，但影响后续轮次）**：`nested_diff.py` 与 `regdump.py` 均不折叠 `EXTENDED_ARG`/`NOP`，hunk 表含计数伪影（本文件已用 ART/MOVE/LOSS/DUP 标注区分）；`nhunks.py` 存在同名 code object 的 `AssertionError` 风险，优先用 `nested_diff.py`。
5. **潜伏 bug**：同进程内对同一 pyc 连续调用两次 `RegionASTGenerator.analyze()` 会在 `region_analyzer.py:8573` `_identify_try_except_regions` 触发 `UnboundLocalError: cannot access local variable 'region'`；`probe_elif.py`/`probe_off.py` 已按「单次 analyze」改写规避。
6. **`LoopRegion entry=5598`（clock_worker）对象在其自身 `blocks` 列表中重复出现并互相嵌套**——这是本轮观测到但未展开的独立异常，建议后续轮次单独取证。

---

diag4 收口：Step 0（复核）/ Step 1（hunk 表）/ Step 2（逐函数根因实测）/ Step 3（候选 NONE×3）/ Step 4（门禁再确认）/ Step 5（VERDICTS）/ 更正 6 条，全部完成。

## Step 6 · 候选尝试与否决（臂 `r69d4c1`，2026-09-25 追加）

### 6.0 既往臂取证（本节推翻本文件「对 BRIEF 的更正」第 1 条）
`F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/` **存在**（round25–round68 全在）：
- `round68/specs/ADR1_contract_fix.md` **存在**（BRIEF 所称 "ADR-1" 的实际文件名是 `ADR1_contract_fix.md`，不是 `ADR-1`）。
- 与本线相关的既往臂：`round68/batches/b3_diag4/`（`specs/cand_r68_orchain_tail*.json` + `synth/r68d4_orchain*.py`）、`round68/batches/b5_diag6/FACTS.md`（order_api 判 NONE，理由「kwarg 槽内三元/表达式语句错位族」）、`round51/OUTCOME.md`（`_try_build_ternary_kwarg_call` 41500-41505 线）。
- **判据差异举证（BRIEF §8 要求）**：既往 or 链线全部落在**生成器侧** `core/cfg/region_ast_generator.py`（R68-diag4 主站点 L17587-17588「条件被 BoolOp(or) 整体**替换**」、R50/51 站点 `_try_build_ternary_kwarg_call`）；本轮站点在**分析器侧** `core/cfg/region_analyzer.py` L19135-19167「`or` 链**形成**时的合法性检查被空转」。文件、行号、机制三者均不同 ⇒ 满足 §8「实测证明判据与既往臂不同」，允许重走；但见 6.3，实测结果为**否决**。

### 6.1 更正本文件 Step 2.2 的一处错误论证
Step 2.2 原写「块 386 结尾 `POP_JUMP_IF_TRUE→676`、块 414 结尾 `POP_JUMP_IF_FALSE→556`，两环目标不同 ⇒ `or` 链非法」——**该论证错误，作废**：对 `if A or B: T else: E`，A→T(676)、B→E(556) 目标本就**必须不同**，不能据此证伪。

**重做的实测（`dis` orig 360–580，future_order）**：
```
386 LOAD_GLOBAL is_trade / 402 CALL / 412 POP_JUMP_FORWARD_IF_TRUE 676
414 LOAD_GLOBAL strategy_log / 426 LOAD_ATTR info
436 LOAD_CONST '生成订单，订单号：{order_id}，…{side}{oper}，数量：{share}手'
438 LOAD_METHOD format / 460..506 (order_id, symbol, entrust_direction.value.upper())
542 LOAD_CONST 'BUY' / 544 COMPARE_OP == / 550 POP_JUMP_FORWARD_IF_FALSE 556
552 LOAD_CONST '买入' / 554 JUMP_FORWARD 558 / 556 LOAD_CONST '卖出'
```
⇒ **块 414（414–550）是 `is_trade()` 为假时的分支体（整条 `strategy_log.info(...)` 语句），550 处的跳转是该语句实参里三元表达式 `… == 'BUY' and '买入' or '卖出'` 的条件跳转，不是 `or` 短路环**。

`region_analyzer.py` L19135-19167 的 `or` 链形成逻辑：链首 = `first_else`（386，末指令为 `IF_TRUE`，`_or_body_block`=676）→ fallthrough 取 414 → 414 末指令是条件跳转 ⇒ 入链；`'IF_FALSE'` 分支算出 `_or_ft`=552 后 **`if/else` 两臂都 `break`，比较结果被丢弃**（L19160-19163），`len(_or_chain)>=2` 即登记 `{'blocks':[386,414],'op':'or'}`。⇒ 根因表述修正为：**合法性检查空转，语句体块 414 被误登记为 `or` 第二环**。

### 6.2 最小合成复现（`synth/r69d4_orchain.py` → `r69d4_orchain.pyc`，名单 `synth/r69d4_list.txt`）
| 臂 | 读数 |
|---|---|
| landed | **2/6** `[['v1',25,25,0,1],['v3',25,25,0,1],['v4',27,25,0,3],['v5',27,17,0,18]]` |
| r69d4c1 | **2/6，逐字节同上（sha `9092157fb483b27c` 两臂相同）** |

合成件在 landed 上**咬合**（4 支缺陷），但候选臂读数**完全不动** ⇒ 判据在我构造的形态上不成立/无效，**witness 与判据未咬合**。

### 6.3 spec 与门禁读数
`specs/cand_r69d4_orchain_legit.json`（`mk_spec_d4.py` 生成）：单文件 `core/cfg/region_analyzer.py`，锚点 = L19158-19164（8 行，落地字节 `count==1`，`h62 build` 已断言），插入 +12 行，三要素注释齐全。
`python -X utf8 h62.py build --spec=specs/cand_r69d4_orchain_legit.json --dst=r69d4c1`
⇒ `mirrors built: head pristine == worktree bytes, cand patched (1 edits, core/cfg/region_analyzer.py, BOM=False, nl=CRLF)`

**五列读数（landed → r69d4c1）**
| 列 | landed | r69d4c1 | 合同 |
|---|---|---|---|
| targets | 40/44、32/34、11/12；order_api Σ\|Δ\| = 9+10 = **19** | real_quote 40/44、realtime 11/12 **逐字段不变**；order_api 32/34 但 `future_order 101/79`（92→79）、`option_order 83/48`（73→48）⇒ Σ\|Δ\| = 22+35 = **57** | **§3.3 拒：目标支 Σ\|Δ\| 净增 19→57** |
| battery(45) | 182/200、缺陷 18、worse=0、ERR=0 | worse-than-landed **0**、无 ERR，非绿项同源 | ✓ |
| canary(4) | 4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177 | **四支 sha 逐字节不变** | ✓ |
| strict | 85/93、defects 8 | **86/93、defects 7**（`base_order [target_diff] #136` 转绿；future/option seq_len 由 92/73 恶化为 79/48） | 表面 +1，但同尺内目标支大幅倒退 |
| synth | 2/6 | **2/6（不动）** | **§3.5 拒：witness 未咬合** |

**结论：候选 `r69d4_orchain_legit` 否决（REJECT）**——两道硬门各拒一次（Σ\|Δ\| 净增、synth 未咬合）。

### 6.4 本轮移交的阴性/阳性证据
1. **阴性（可复放）**：`region_analyzer.py` L19158-19163 的 `_or_ft == _or_body_block` 合法性检查**不是** future_order/option_order 丢失的根因；强制执行它使 `future_order` 92→79、`option_order` 73→48（Σ\|Δ\| 19→57）。该路线在当前归约方式下已证伪，后续轮次不要重走「丢弃非法 or 链」这一形态。
2. **阳性（同一次实验的副产物，值得单独取证）**：同一改动让严格尺 `order_api::base_order [target_diff] #136` **转绿**（strict 33/36→34/36，targets strict 85→86、defects 8→7），且 canary 4 sha 不变、battery worse=0 ⇒ `base_order` 的跳转目的缺陷与这条 `or` 链登记确有因果；「保留链但修正其 `_or_body_block` 归属/或只对 base_order 形态生效」是下一轮的可探方向（**必须先给出能把 future/option 两支也保住的归约方式，否则 Σ\|Δ\| 门必拒**）。
3. 爆炸半径：本次改动只影响 `order_api.pyc`（real_quote/realtime 三支 sha 与 landed 完全相同，battery 45 项 worse=0、canary 4 sha 不变）⇒ 站点影响面窄，后续在此站点继续取证是安全的。
4. 合规：仓库未写入（`git status --porcelain core/ pycdc.py` 空；全仓 `git status` 仅历史遗留 untracked，本轮无新增/修改受控文件）；未跑 402 全量扫描；单条命令均 <300s；产物只落 `D:/Temp/opencode/r69gate/diag4`。

## Step 7 · 最终 VERDICTS（覆盖 Step 5）

| # | 靶 | 函数 | 判定 | 依据 |
|---|---|---|---|---|
| 1-4 | real_quote | get_cache_l2_data_by_one / get_real_minute_kline / get_tick_direction / one_prod_to_ndarray | **NONE** | 纯位移族，四支共享「then/else 物理块交错 + then 越过 merge」结构签名；唯一归约方式是按块物理位置重排发射序 = 线性化/重排通道，与「禁按偏移启发」冲突；ADR-1 虽已把位移族纳入可采纳判据，但本轮未给出非偏移的归约方式 ⇒ 不落 spec |
| 5-6 | order_api | future_order / option_order | **NONE** | 根因已定位并可复放（L19135-19167 合法性检查空转、语句体块被登记为 `or` 第二环），与既往臂（生成器侧 L17587 / `_try_build_ternary_kwarg_call`）判据确属不同；但候选 `r69d4_orchain_legit` 被两道硬门否决（Σ\|Δ\| 19→57；synth 2/6 不动）⇒ 本轮无候选 |
| 7 | realtime | clock_worker | **NONE** | 根因定位到 R23-A or-extension 跨区域借用 elif 臂（L18071-18075）+ `generated_blocks` 两次未命中未回填；但产品侧 body 与位置分家（275 带体、312 为 `pass`），单删任一支必引入新缺陷，需 body 重挂，无 synth ⇒ 不落 spec |

**本轮最终：候选 NONE，落地读数与 Step 0 完全相同**（targets 40/44+32/34+11/12、canary 204/204 四 sha、battery 182/200 缺陷 18 worse 0 ERR 0、strict 85/93 缺陷 8）。

## 附：本文件内被本节推翻/修订的条目
- 「对 BRIEF 的更正」**第 1 条（`rounds/` 与 `rounds/round68/specs/ADR-1` 不存在）作废**——正确事实见 6.0：`rounds/` 存在，ADR-1 的实际路径是 `.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round68/specs/ADR1_contract_fix.md`。更正第 1 条中「因此无法取证既往臂读数 ⇒ order_api 判 NONE」的推理链一并作废；order_api 判 NONE 的真实理由是 6.3 的两道硬门否决。
- 「对 BRIEF 的更正」**第 2 条部分作废**：`rounds/round68/specs/ADR1_contract_fix.md` 存在，故其对判据 3 的更正（位移族改按「hunk 数严格下降 + first_diff 回移 + Σ\|Δ\| 不升」判）对本文件 Step 5 中 real_quote 的 NONE 判定**继续有效**（本轮仍未给出归约方式，NONE 的理由不依赖 Σ\|Δ\| 口径）。
- Step 2.2 的「两环跳转目标不同 ⇒ `or` 链非法」论证**作废**，正确读数见 6.1。
