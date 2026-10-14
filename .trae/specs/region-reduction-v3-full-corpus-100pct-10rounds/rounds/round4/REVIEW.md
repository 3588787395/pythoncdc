# Round 4 — 测试工程师 REVIEW（诊断 only，零生产代码改动）

任务：单测单元丢失簇（16 语料文件各失 1 单元，全部 `Different control flow`）的**机制归并**。
本轮全量诊断 8 个主靶 + 只钉首分歧的 8 个次靶。

产物一律「先删后由 `python -X utf8 pycdc.py -o <pyc去.pyc>OK.py <pyc>` 重生成」；**未手改任何 `*OK.py`**。
判据一律 `scripts/pyc_verify.py`（未改）。诊断器 = `test_repros/round4/_r4v3_diag.py`（本轮新建，只读，不改判据）。
零 `git` 命令。所有命令 <300s。

> 目录冲突声明：`test_repros/round4/` 在本 spec 之前已存在 **既往战役遗留** 文件
> （`n4_*`、`r4_01_boolop_merge_*`、`probe_match_*`、`ANALYSIS*.md`、`_probe_*.py` 共 69 项）。
> 本轮全部标本使用 **`r4v3_` 前缀**（对齐 Round-2 的 `r2v3_` 惯例），索引
> `test_repros/round4/r4_probe_index.json` **只含本轮 31 臂**，遗留文件一律未写入索引、未改动。

---

## 1. 判据口径与伪影排除（本轮实际用到的规则）

沿用 Round-1 §1 / Round-2 §1 / Round-3 §1，本轮实测排除如下（rules.md §5.2/§5.3）：

| 排除项 | 本轮出现位置 | 判据 |
|---|---|---|
| 跳转 argval 位移（目标**内容签名相同**） | 8 靶共 **144** 处（`_r4v3_diag oseq` 的 `discounted offset-shift artifacts` 计数逐靶列出） | 目标块前 4 opcode 签名两版相同 ⇒ 对齐伪影 |
| `LOAD_CONST <code object …>` 常量 repr（co_filename/行号/地址） | 主靶 #2 `clock_worker` idx620（off5270，orig `file "./fly_docker_py311/…", line 380` vs prod `file "realtime_event_sourceOK.py", line 204`） | §5.2「code 递归忽略元数据」 |
| 行追踪 NOP 增删 | #2 idx665（prod off5598 `+NOP`）、次靶 `flytools.modify_batcktes_info`（prod off700 `+NOP`）、`function.reconnect`（prod off70 `+NOP`）、A 组多数臂 orig idx[1:2]（orig off2 `−NOP`，签名续行） | §5.3；**注意 `flytools` 那一条是该单元唯一分歧，不可一概豁免，见 §7** |
| `CACHE/EXTENDED_ARG/PRECALL` | 全部 | 不入指令序列 |

同名嵌套 code object（`clock_worker` 内两份 `check_handle_date`）本轮**按出现顺序配对**
（`pair()` 分组成员序号，标签 `#0/#1`），不使用 name→单个 code object 的字典配对
（后者会把 orig 3 条 vs prod 7 条的**伪分歧**当成真缺陷，本轮已排除）。

---

## 2. 簇矩阵（cluster matrix）：8 主靶

签名 A = **区域汇合块/出口块身份被取成外层作用域尾（或反之）**：跳转条数不变或近不变，
臂体块 preds 塌陷、汇合块 preds 增加，**指令序列逐位同构**（+0 或 ±1 噪声）。
签名 B = **隐式 `return None` 双 sink 归并**：`LOAD_CONST None; RETURN_VALUE` 出口块对整对消失
（每塌一对 = −2 指令），另一条出口边改投到臂体/首 sink。
签名 C = **终态 return 与凭空 None 尾 sink 互换**（B111 轴）。
签名 D = **出口边整体丢失（跳边消失变直落）+ 语句段整块不发射**（大 −N）。

| # | pyc | 单元 | 读数 | 首分歧（opcode/off/目标 delta） | 指令数差 | 签名 | 归属 |
|---|---|---|---|---|---|---|---|
| 1 | `IQCommon/logger/handlers.pyc` | `TWHThreadController._target` | 29/30 | idx71 **delete** orig off404 `LOAD_CONST None` + off406 `RETURN_VALUE`；块级：ORIG off404 preds=[13] 与 off408 preds=[2] 两 sink → PROD off404 preds=[**2,13**] 单 sink（off412 起的语句块前移 4） | −2 | **B** | **B99 原锚点逐位复现**（Round-1 §7.3 的 off404/406+off408/410 双 sink），**未闭，不是新条** |
| 2 | `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | `RealtimeEventSource.clock_worker` | 12/13 | idx620 `LOAD_CONST <code>` 判伪影并排除；真首分歧 idx667 `POP_JUMP_FORWARD_IF_FALSE` off5612→**9214**`[LOAD_CONST,RETURN_VALUE,PUSH_EXC_INFO,…]`（函数尾 sink/异常边）vs prod off5614→**8468**`[LOAD_FAST,LOAD_CONST,COMPARE_OP,…]`（循环体内语句）；块级 orig off5598 `jump_off=9214 preds=[78,79,108]` → prod 同块 `jump_off=**None** preds=[78,79]`（跳边整体消失） | **−102** | **D** | **新登记 B117**（与 A/B/C 均不同：不是目标外推，是「离开函数」的出口边被吞 + 穿循环体尾随语句段 100 条不发射，delete hunks orig idx[841:857]、idx[936:941]、idx[1054:1154]） |
| 3 | `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | `Strategy.tick_worker_thread` | 26/27 | idx64 `POP_JUMP_FORWARD_IF_TRUE` off522→**568**`[LOAD_GLOBAL,LOAD_ATTR,LOAD_CONST,CALL]`(=`time.sleep(60)`) vs prod→**820**`[JUMP_FORWARD,…]`；idx68 off534→568 vs →820；idx168/172 off992/1004→**1038** vs →**1286** | +0 | **A** | **B110 同一判据轴的第二个欠伸侧**（非 B99/B111；宿主确为 `while True`+`try`，但机制不是 sink 归并） |
| 4 | `IQEngine/data/trading_dates_mixin.pyc` | `TradingDatesMixin.trading_dates_reload` | 13/14 | idx3 `POP_JUMP_FORWARD_IF_FALSE` off14→**118**`[LOAD_CONST,RETURN_VALUE,…]` vs prod off14→**30**`[LOAD_FAST,LOAD_ATTR,LOAD_ATTR,LOAD_METHOD]`（臂体）；idx21 **delete** orig off122/124 第二 sink | −2 | **B** | **新登记 B116**（B99 的**无循环宿主**孪生：候选源逐指令核对证明原形 = `if A: if not B: body`，见 §4） |
| 5 | `IQCommon/data/finance.pyc` | `get_fields` | 31/32 | idx20 `JUMP_FORWARD` off92→**236**`[LOAD_FAST,LOAD_CONST,BINARY_SUBSCR,LOAD_CONST]` vs prod off94→**742**`[LOAD_FAST,RETURN_VALUE,PUSH_EXC_INFO,…]`（函数尾/异常边） | +0 | **A** | **B100 原锚点逐位复现**（Round-1 §9 记 `#5 off92 236→742`，三轮修复后**未闭**，不是新条） |
| 6 | `IQEngine/plugins/plugin_system_matcher/matcher.pyc` | `DefaultMatcher.match` | 16/17 | idx182 `JUMP_FORWARD` off1322→**2464**`[JUMP_FORWARD,LOAD_FAST,…]`（**纯跳出口块**）vs prod→**3166**`[LOAD_FAST,LOAD_ATTR,POP_JUMP_IF_FALSE,…]`；idx196 off1382→1444 vs →1696；idx290 off1910→2164 vs →2034；**另** delete orig idx[325:335]（off2164 起 10 条语句块整块不发射，ORIG 该块 preds=[35,36,37,38,42,43] → prod preds 少 38 一条） | −10 | **A + 语句丢失** | A 族（B100/B110 轴）**加**一条独立语句块丢失面；本轮未定到行 |
| 7 | `fly/data/quote_handler.pyc` | `get_kline_local` | 78/79 | idx79 `POP_JUMP_FORWARD_IF_FALSE` off380→**420**`[LOAD_GLOBAL,LOAD_FAST,CALL,LOAD_CONST]` vs prod off382→**3534**`[LOAD_CONST,RETURN_VALUE]`（**prod 末块之后凭空新增**的 None 尾 sink）；idx686 off3060→3528 vs →3530（终态 `return <expr>` 块少一条汇入边） | **+2** | **C** | **B111 同轴（终态 return / 凭空 None 尾 sink 归属）**，但宿主不是 LoopRegion 自然出口而是 if 臂出口 ⇒ 记为 B111 轴新实例，**不另立编号** |
| 8 | `IQData/api/api_base.pyc` | `get_history_df` | 27/28 | idx175 `POP_JUMP_FORWARD_IF_TRUE` off994→**1098**`[LOAD_FAST,LOAD_CONST,BINARY_OP,…]` vs prod→**1254**`[JUMP_FORWARD,…]`；idx179 off1006→**1040** vs →**1254**；块级：ORIG off1040 preds=[18,21]→prod [21]、off1098 preds=[17,20,22]→prod [20,22] | +0 | **A** | **同 #3**：成员真边 → 臂入口 被判成 链/区域汇合块（B110 轴） |

**主靶结论**：**8 个不是同一机制**，分为 4 族：
A 族（汇合块/出口块身份）= #3、#5、#8（+#6 的一半）= **3–4 个文件**；
B 族（隐式 return None 双 sink 归并）= #1、#4 = **2 个文件**（同一判据轴，宿主类型不同：#1 有循环、#4 无循环）；
C 轴（终态 return vs 凭空 None 尾）= #7 = 1 个；
D（出口边整体丢失 + 语句段不发射）= #2 = 1 个。
**任务书假设（"几个失败单元都是 loop/worker 方法 ⇒ 闻起来像 B99/B111"）不成立**：
四个 worker 方法里只有 #1 真是 B99；#3 是 A 族、#2 是 D 族、#4 是无循环的 B 族新实例。
**按函数名相似聚类会得出错误结论**——本轮全部按 offset 签名分族。

---

## 3. 次靶 8 个（只钉首分歧，不跑全套电池）

| pyc | 单元 | 读数 | 首分歧 | 签名 | 归属 |
|---|---|---|---|---|---|
| `IQEngine/core/bar.pyc` | `BarData._history_bars` | 84/85 | `POP_JUMP_IF_FALSE` off126→**140** vs →**304**，+0 | A | B100/B110 轴 |
| `IQEngine/core/strategy/strategy_universe.pyc` | **`_on_clear_de_listed`**（任务书写成 `_on_clear_delisted`，实名带下划线，按实名匹配才命中） | 10/11 | `POP_JUMP_IF_FALSE` off112→**156**`[LOAD_FAST,LOAD_METHOD,LOAD_FAST,CALL]` vs →**198**`[JUMP_BACKWARD,…]`，+0 | A | B100/B110 轴 |
| `…/position_model/stock_position.pyc` | `StockPosition.make_trade` | 36/37 | delete orig off526/528 + off530/532（**塌两对** sink，−4）；边 off446→526 改投 →522 | **B** | **B116 同机制（两对塌）** |
| `IQEngine/plugins/plugin_system_trade/function.pyc` | `reconnect` | 70/71 | `JUMP_FORWARD` off306→**520** vs →**600**`[LOAD_FAST,RETURN_VALUE]`；off366 同 | A（+1 NOP 噪声） | B100 轴 |
| `IQEngine/utils/profiler_func.pyc` | `ProfilerTool.show_func` | 17/18 | delete orig idx[203:223]（off1060 起 20 条 = 一个 `for range(...)` 段整块不发射），−58 | **D** | **B117 同机制** |
| `fly/common/flytools.pyc` | `ProcessWrite.modify_batcktes_info` | 65/66 | **唯一分歧 = prod idx139 off700 `+NOP`**（6 处目标位移已按签名排除） | 仅 NOP | §5.3 要求逐项核查：该 NOP 是**唯一**差异 ⇒ 不能按「对齐偏移」豁免；本轮**未能归族**（如实登记：需插桩判它是行追踪还是空语句材料化） |
| `fly/dumpload/load_daily.pyc` | `<module>`（模块顶层） | 26/27 | `JUMP_FORWARD` off2454→**2478**`[PUSH_NULL,LOAD_NAME,LOAD_CONST,PUSH_NULL]` vs →**2562**`[JUMP_FORWARD,PUSH_EXC_INFO,LOAD_NAME,CHECK_EXC_MATCH]`，+0 | A | B100 轴（**模块顶层宿主**，证明与 def/方法宿主无关 ⇒ 区域成员关系形，非深度形） |
| `fly/data/quotation.pyc` | `get_fundflow_day`（**B102**） | 152/153 | `POP_JUMP_IF_FALSE` off196→**268**`[LOAD_CONST,RETURN_VALUE,LOAD_CONST,RETURN_VALUE]` vs →**272**`[LOAD_CONST,RETURN_VALUE]`；`FOR_ITER` off202→**272** vs →**268**（**两条边的目标恰好互换**，且 orig 268 是相邻两对 None-return sink） | B/C 混合 | **是本轮簇的同机制家族**：属 B99/B116 的「相邻隐式 return None sink 块归属」轴（B102 原样在册，**不另立编号**，只补锚点） |

⇒ **A 族合计 7 个文件**（主 #3/#5/#8/#6 + 次 bar/function/strategy_universe/load_daily），
**B 族合计 4 个**（主 #1/#4 + 次 stock_position/quotation-B102），
**D 族 2 个**（主 #2 + 次 profiler_func），**未归族 1 个**（flytools，纯 NOP），**C 轴 1 个**（#7）。

---

## 4. B116 的原形核对（候选源逐指令重编，Round-1 §2.2 同法）

`TradingDatesMixin.trading_dates_reload` ORIG live 序列 23 条（RESUME + 两测试 + 12 条臂体 + **三对**
`LOAD_CONST None;RETURN_VALUE`）。候选源重编比对（脚本内联于本轮，仓库零残留）：

| 候选源 | 序列比对 |
|---|---|
| `if A: if B: return / body` | 不等（idx6 `replace`，尾部 −2） |
| `if A: if B: return None / body` | 不等（同上） |
| `if A: if B: pass / body` | 不等（22 条） |
| **`if A: if not B: body`（无任何 return 语句）** | **MATCH-SEQ 23/23 逐位相同** |

⇒ 原形 = 嵌套 if + **负测试** + 无 return 语句；三对 None-return sink 分别是
「臂体尾隐式返回(off114)」「外层 if 被跳过→函数尾(off118)」「内层 if 不成立→臂尾(off122)」。
产物把它发成 `if not (A and B): body else: return None`（`trading_dates_mixinOK.py:116-123`），
**语义不等价**（A 为假时产物会执行臂体，原码直接返回）⇒ 真缺陷，非判据噪声。

---

## 5. 复现电池（`test_repros/round4/`，前缀 `r4v3_`）

生成方式＝写 `.py` → `py_compile.compile(cfile=<name>.pyc)` → `pycdc.py -o <name>OK.py <name>.pyc`
→ `pyc_verify batch --index`。生成器 `test_repros/round4/_r4v3gen.py`（28→**31** 臂，可复跑）。
索引 `test_repros/round4/r4_probe_index.json`（**31 条目**，格式与 `round1/r1_probe_index.json`、
`round2/r2v3_probe_index.json`、`round3/r3_probe_index.json` 逐字相同：`[{"path": "test_repros/round4/<x>.pyc"}, ...]`）。

### 5.1 电池汇总（本轮实测原文，唯一判据）

```
$ python -X utf8 test_repros/round4/_r4v3gen.py
built 31 arms
$ python -X utf8 scripts/pyc_verify.py batch --index test_repros/round4/r4_probe_index.json --json D:/Temp/rrv4/r4_battery.json
files_total=31  units_success=51/67  success_rate=0.7611940298507462
files_by_status={'compile_error': 0, 'error': 0, 'failure': 16, 'success': 15}   elapsed_sec=1.1
```
⇒ **16 臂今日 MISMATCH（标本）/ 15 臂今日 MATCH（对照）**，无 `error`/`compile_error`。
主靶单文件读数（本轮实测原文）：`handlers 29/30`、`realtime_event_source 12/13`、`strategy 26/27`、
`trading_dates_mixin 13/14`、`finance 31/32`、`matcher 16/17`、`quote_handler 78/79`、`api_base 27/28`。

### 5.2 标本↔对照（每条自证：唯一构造改动 + 两臂判定原文）

**B 族 = B99/B116「隐式 return None 双 sink 归并」（7 标本 + 5 对照）**

| 臂 | 今日 | 形状 | 自证：唯一改动 → 对臂 |
|---|---|---|---|
| `r4v3_b01_nested_not_method` | **MISMATCH 2/3** | `if A: if not B: body`（方法内）——**与主靶 #4 逐位同签名**（orig 23/prod 21、−2、`off14 118→30`、delete off122/124） | →**b07** 去掉内层 `not` ⇒ MATCH 3/3；→**b04** 删掉外层 `if` ⇒ MATCH 3/3；→**b02** 在外层 if 之后加一条兄弟语句 ⇒ MATCH 3/3 |
| `r4v3_b03_flat_and_control` | **MISMATCH 2/3** | `if A and not B: body`（扁平写法，同签名 −2/off14 118→30/delete 122） | →**b04** 删掉一个合取项 ⇒ MATCH 3/3 |
| `r4v3_b05_func_host` | **MISMATCH 1/2** | 宿主=普通函数（off4→70 vs →10，delete off74/76） | →**b04** 删外层 if ⇒ MATCH |
| `r4v3_b06_module_host` | **MISMATCH 0/1** | 宿主=**模块顶层**（off4→54 vs →10，delete off58/60）⇒ 宿主无感被违反，与 def/方法无关 | →**b12** 删外层 if（模块级单层 if）⇒ **MATCH 1/1** |
| `r4v3_b08_three_nested` | **MISMATCH 2/3** | 三层嵌套 ⇒ **−4（塌两对）**，与 sink 对数线性相关 | →**b01** 少一层 ⇒ 同为 MISMATCH（只证「每塌一对 = −2」的线性） |
| `r4v3_b09_b99_while_try_ifarm` | **MISMATCH 2/3** | 主靶 #1 原形：`if arm: while: try/except/else` ⇒ delete off220/222（−2） | →**b10** 去掉外层 `if`（循环即函数末语句）⇒ **MATCH 3/3**（Round-1 `r1_72` 同结论：函数末守卫有效） |
| `r4v3_b11_nested_not_in_loop` | **MISMATCH 1/2** | `if pre: while running: if not upd: body` | →**b10** 去 if 臂 ⇒ MATCH |
| `r4v3_b02/b04/b07/b10/b12` | MATCH（3/3、3/3、3/3、3/3、1/1） | **修复后必须保持 MATCH 的回归哨兵** | — |

**A 族 = 汇合块/出口块身份（B100/B110 轴）（9 标本 + 5 对照）**

| 臂 | 今日 | 形状与实测签名 | 自证/判据事实 |
|---|---|---|---|
| `r4v3_a02_while_no_try` | **MISMATCH 1/2** | `while True` + 外层 if 臂 + 内层 if/elif 链（无 try）：orig off20/134/146/158 四条**都指向回边块 410（`JUMP_BACKWARD`）**，prod 把它们分别改投 334/316/158 并把 off158 的 IF_TRUE **翻成 IF_FALSE** | →**a01**（唯一改动 = 给循环体加 `try/except`）⇒ **MATCH 2/2** ⇒ 判别轴 = **宿主区域类型（try 包裹与否）**，不是深度 |
| `r4v3_a03_no_loop_host` | **MISMATCH 1/2** | 同链、无循环：既有边外推，又有 B 族签名（`off18→420[LR,LR]` vs →422、orig idx[97:99] `LOAD_CONST,RETURN_VALUE` 被 `JUMP_FORWARD 414` 取代、尾部 delete 4 条）⇒ **A/B 两族在同一单元内耦合** | →**a04** 去掉外层 `def`（整段移模块顶层）⇒ **MATCH 1/1** |
| `r4v3_a05_for_host` | **MISMATCH 1/2** | `for` 宿主：orig off152 `IF_TRUE→416[JUMP_BACKWARD,…]` vs prod `→166`，且 off164 同目标边 **IF_TRUE→IF_FALSE 极性翻转** | 与 a02 同签名（换宿主） |
| `r4v3_a06_two_arm_chain` | **MISMATCH 1/2** | a02 删掉第三个 elif 臂 ⇒ 仍 MISMATCH | 反证：**臂数无关**（Round-3 `r3_b05` 的「删第三成员即全等」在本形不成立） |
| `r4v3_a07_no_or` | **MISMATCH 1/2**（+4） | a02 把所有 `or` 拆成单比较 ⇒ 仍 MISMATCH | 反证：**不是 B110 的「跳族混合/`or` 成员」判据**，本轮证据把 B110 的认领面收窄 |
| `r4v3_a08_diff_body` | **MISMATCH 1/2** | 臂体换成互不相同的赋值 ⇒ 仍 MISMATCH | 反证：臂体同形与否无关 |
| `r4v3_a09_else_only` | **MISMATCH 1/2** | 内层链改成 `if/else`（**无 elif 链**）⇒ 仍 MISMATCH | 反证：**elif 链不是必要条件**（B112 的「专属 elif 链层」判据在此不适用） |
| `r4v3_a13_no_outer_guard` | **MISMATCH 1/2**（−7） | a02 去掉外层 `if 'x' in ACCTS:` 守卫 ⇒ 仍 MISMATCH | 外层守卫非必要 |
| `r4v3_a14_min_arm` | **MISMATCH 1/2**（**+6**） | **最小形**：`while True: if A: if B: sleep(3)`（orig 15 / prod 21）；orig off20/off50 两条 `IF_FALSE→82[JUMP_BACKWARD]` 被 prod 改投 `102[LOAD_CONST,RETURN_VALUE]`/`80[...]` | 最小标本；prod **多出** 6 条 ⇒ 出口边被就地材料化 |
| `r4v3_a01/a04/a10/a11/a12` | MATCH（2/2、1/1、2/2、2/2、2/2） | **回归哨兵**：a01 = 语料 #3 逐特征原形（`while`+`try`+嵌套链）**今日正确**；a10 = `if A == B and C > D:` + 内层 if/elif（#8 原形）今日正确；a11/a12 = try 体内 if 链 + 尾随语句（#5/B100 原形族）今日正确 | a01/a10/a11/a12 是「不得一刀切」的下界 |

**C 轴（终态 return / 凭空 None 尾）—— 0 标本 + 5 对照（如实缺口）**

`r4v3_c01_all_paths_return_expr`、`c02_dead_tail_return_control`、`c03_loop_else_terminal_return`（B111 原形）、
`c04_loop_plain_control`、`c05_early_return_chain` **今日全部 MATCH 2/2** ⇒ 本轮**未能**为 #7
`get_kline_local`（+2 凭空 None 尾）与 B111 造出最小合成孪生（与 Round-2 B105、Round-3 B100/B104 同样处境）。
验收面须用真文件读数：`quote_handler.pyc 78/79`、`klinedata.pyc 61/64`。
D 族（#2 / profiler_func，−102 / −58）**同样未造出合成标本**（语句段整块不发射的触发面需 fix 侧插桩）。

分族合计：B 族 7 标本 + 5 对照；A 族 9 标本 + 5 对照（含 a04 一臂双职：既是 A 族宿主扩展对照，又是 a03 的自证对照）；
C 族 0 标本 + 5 对照 ⇒ **16 标本 + 15 对照 = 31**，与 §5.1 读数逐条吻合。

---

## 6. 破口登记（本轮从 B116 起）

| 编号 | 覆盖 | 锚点（opcode + offset + 目标 delta） | 机制 | 违反条款 |
|---|---|---|---|---|
| **B116**（**新**） | 主靶 #4 `trading_dates_reload`；次靶 `stock_position.make_trade`（塌两对，−4）；合成 `b01/b03/b05/b06/b08/b11` | `IQEngine/data/trading_dates_mixin.pyc` / `<module>.TradingDatesMixin.trading_dates_reload` / ORIG off **118** `LOAD_CONST,RETURN_VALUE`（preds=[0]）与 off **122**（preds=[1]）两 sink → PROD 仅存 off118（preds=[1]），off122/124 整对消失；边 off14 `POP_JUMP_IF_FALSE` 由 →118 改投 →**30**（臂体首块） | 非函数末分支内的**相邻无后继隐式 `return None` sink 块被认作同一条语句发射**，且外层 if 的臂体被外提为函数级兄弟（if 条件被 `and` 合并）。**B99 的无循环宿主孪生**：同一归属轴、同一判据面，B99 要求「循环 + 尾随 return None」，本条证明**没有循环也塌** | §1.5 **C3 守卫封闭**（守卫作用域未闭合到分支/区域层）+ §1.2 **原则2 每块唯一归属**（两块一语句）+ **原则4 入口引用语义**（`if A` 的假边 → 函数尾出口 被改投 → 臂入口）；§3.2.3 的对应面（不该做的 `and` 合并） |
| **B117**（**新**） | 主靶 #2 `clock_worker`；次靶 `ProfilerTool.show_func`（−58） | `…/realtime_event_source.pyc` / `<module>.RealtimeEventSource.clock_worker` / ORIG off **5598** 块 `LOAD_DEREF,LOAD_ATTR,POP_JUMP_FORWARD_IF_FALSE` 的 `jump_off=9214`（函数尾 sink，其后紧跟异常边 `PUSH_EXC_INFO`）preds=[78,79,108] → PROD 同块 **`jump_off=None`**（跳边整体消失，变直落）preds=[78,79]；随后 orig idx[1054:1154]（off 7972–8590，**100 条** = `if persist_flag is False: …` 一整个语句段）**未被发射** | 「离开本函数」的出口边（跳向函数尾 sink/异常边入口）被认成区域内部直落，穿过该区域的尾随语句段随之整块不发射 ⇒ 与 A 族方向相反（A 是外推，本条是**内吞**） | §1.2 **原则2**（语句段无归属方）+ **原则1 自底向上**（区域出口交付的「出口后顺序代码」丢失）+ §1.5 **C3**（出口块被区域外路径引用时未显式认领唯一发射点）。**站点未定位到行**（本轮未插桩） |
| B99（**原样在册，复现**） | 主靶 #1 + 合成 `b09` | off404/406 + off408/410 → 单 sink，preds [13]+[2] → [2,13]（Round-1 锚点逐位复现，三轮修复后**未闭**） | 同 B116，宿主 = `while` 在 if 臂内 | 同 B116；另触 **§6.4 落地验收**：见下「vestigial 守卫」 |
| B100 / B104 / B110（**既有编号的新实例，不另立**） | 主靶 #3/#5/#8/#6 + 次靶 bar / function / strategy_universe / load_daily | #5 off92 `236→742`（**Round-1 B100 锚点逐位复现**）；#3 off522/534 `568→820`、off992/1004 `1038→1288`（臂体 preds `3→1`、汇块 preds `2→4`）；#8 off994/1006 `1098/1040→1254`（臂体 preds `3→2`、`2→1`）；#6 off1322 `2464→3166`（纯跳出口块被跳过） | IfRegion/elif 链的臂出口/成员真边目标被取成**外层作用域汇合块** | 与 Round-1 §9 B100 / Round-2 B104 / Round-3 B110 同判据轴。本轮增量事实：**B110 的认领面要收窄**——`a07`（无 `or`）、`a06`（两臂链）、`a09`（无 elif）皆仍 MISMATCH ⇒ 「跳族混合 / `or` 成员 / elif 层」都不是必要条件；而 #3/#8 的实测成员边**全是 `POP_JUMP_FORWARD_IF_TRUE` 族且两名成员目标相同**（不分裂 S/F），点名 `_boolop_mixed_polarity_or_chain` 的「**目标必须分裂为 S 与 F**」这一条判据过严（`region_ast_generator.py:38240`，grep 核实存在） |
| B111（**原轴，新实例**） | 主靶 #7 | off382 改投 prod 末块后**新增** off3534 `LOAD_CONST None,RETURN_VALUE`（+2）；终态 `return <expr>` 块 off3530 少一条汇入边 | 同 B111 的终态 return / 凭空 None 尾归属轴，宿主由 LoopRegion 自然出口换成 if 臂出口 ⇒ **不另立编号**，补锚点 | §1.5 C3 + 原则2 |
| B102（**原样在册**） | `quotation.get_fundflow_day` | off196 与 FOR_ITER off202 的目标 **268/272 互换**；orig 268 = 相邻两对 None-return sink | **是本轮 B 族的同机制**（相邻隐式 return None sink 块归属），非 A 族 | 复用 B102，不另立 |
| 未归族线索（**禁止据此改判据**） | `flytools.ProcessWrite.modify_batcktes_info` | 该单元**唯一**分歧 = prod off700 单条 `NOP` 插入（其余 6 处均同签名位移） | §5.3「唯一可豁免的 NOP 差异 = PEP626 装饰器/多行签名续行」在此**不适用**（该函数无装饰器多行签名），但一条 NOP 不足以定控制流形状；本轮只登记读数 | 无法归到条款 ⇒ 如实标注「未定位」 |

### 6.1 最强生产站点（grep 核实）

**`core/cfg/region_ast_generator.py:2357-2363`：出口块计数守卫是 vestigial（算了不用）。**

```python
_trailing_rn_exit_count = 0
if _func_cfg is not None and hasattr(_func_cfg, 'blocks'):
    for _blk in _func_cfg.blocks.values():
        if _blk.successors: continue
        if self.region_analyzer._check_block_has_trailing_return_none(_blk):
            _trailing_rn_exit_count += 1
```

`grep -rn "_trailing_rn_exit_count" core/` **只有 2 处命中：置 0 与 +=1，没有任何读取点**。
它正是 Round-1 §7.3 点名的「出口块计数」那一步；计数之后紧邻的注释自陈
「最终决定：始终保留 return None」（2366-2380）。⇒ B99/B116/B102 三条的**根因面 = 该计数既未消费、
又只在函数 CFG 层统计**（`_func_cfg.blocks` 全量，不按区域/臂的成员关系分箱）。
符合 rules.md §6.4「代码已落地 vs 仅归档 spec」的 B1 教训形态。
配套符号（全部 grep 核实存在）：`region_analyzer.py:1315 _check_block_has_trailing_return_none`
（def 行 1315）、`code_generator.py:2232 _filter_trailing_return_none`（def 行 2232）、
`region_ast_generator.py:2139 _build_function_def`（def 行 2139）。
A 族配套站点：`region_analyzer.py:3054 _compute_arm_level_join`（标记 `[r3-b100-armjoin]`，
**唯一调用点 19639**；同族子判据 3033/3038/3122/3244/3328 `[r3-b100-armjoin-tailexit]`）、
`region_analyzer.py:21207 _check_elif_chain`、`region_ast_generator.py:18757 _if_generate_elif_chain`、
`region_ast_generator.py:38240 _boolop_mixed_polarity_or_chain`、`region_analyzer.py:28396 _detect_boolop_conditional_chain`。
B115/B107/B106/B108 标记实测计数：`[R3-B115` 1、`[R2-B106` 4、`[R2-B107` 7、`[R2-B108` 5（原样在册，本轮未动）。
字节事实更正：`core/cfg/region_ast_generator.py` 58669 行、`core/cfg/region_analyzer.py` 31979 行，
**两文件各带 1 个前导 BOM（实测 `[:3] == b'\xef\xbb\xbf'` = True）**；`core/cfg/code_generator.py` **无 BOM**。

---

## 7. 建议：翻掉最多文件的单条机制

1. **首选（广度）**：A 族「if/elif 链臂出口 / 成员真边的汇合块身份」= 主靶 **3 个文件**（#3 strategy、#5 finance、#8 api_base，
   外加 #6 matcher 的首分歧同族）+ 次靶 **4 个**（bar、function、strategy_universe、load_daily）⇒ **合计 7 单元**。
   落点 = `_compute_arm_level_join` 的**唯一调用点 19639 之外**的 elif/boolop 生成侧消费链
   （`_if_generate_elif_chain` / `_boolop_mixed_polarity_or_chain` 的「目标分裂 S 与 F」条款）。
   注意：a06/a07/a09 三臂反证「必要条件」清单，一刀切拒绝混合链/拒绝 elif 折叠会把 a10/a11/a12 拉红（禁止）。
2. **次选（确定性最高）**：B 族 sink 归并 = 主靶 2 个（#1、#4）+ 次靶 2 个（stock_position、quotation/B102）= 4 单元，
   但**站点已实测钉死到具体行为**（`_trailing_rn_exit_count` vestigial + 函数级分箱），
   且本轮备好 7 条标本 + 5 条 must-keep-MATCH 对照；修复方向 = 把出口块计数/归属**按区域成员关系分箱**
   （区域自身的无后继 trailing-return-None 出口块数 ≥2 ⇒ 每块各发一条隐式返回），
   **禁止**按宿主类型（while/for/try）或「函数末」位置门控（§1.5 推论、§2.2、§2.3）。
3. **#2 / profiler_func（D 族）单独排后**：−102/−58 是**语句段整块丢失**，语义危害最大（不是形状噪声），
   但需要 fix 侧插桩才能定到行；建议 B117 单独一票，不与 A/B 混修。
4. **#7 / B111 轴**：合成缺口未闭合（C 组 0 标本），验收只能用真文件读数，风险高于前两项。

---

## 8. 未完成 / 风险 / 如实声明

1. **完全诊断到位（首分歧 + 块级 preds 证据 + 原形核对 + 归族）= 主靶 8 个全部**；
   次靶 8 个按约束**只钉首分歧**（未跑电池、未造合成、未做原形候选源核对）。
2. **未闭合**：C 族（#7/B111）与 D 族（#2/B117）**0 合成标本**；`flytools` 纯 NOP 分歧未归族且无法归条款。
3. `region_ast_generator.py` / `region_analyzer.py` 的行号是**本轮实测行号**（58669 / 31979 行，各 1 BOM）；
   `code_generator.py` 6023 行、无 BOM。
4. 本轮**零生产代码改动**：只新增 `test_repros/round4/_r4v3_diag.py`、`_r4v3gen.py`、31×(`.py`/`.pyc`/`OK.py`)、
   `r4_probe_index.json`；语料侧只按认证方式重生成了 16 份 `*OK.py` 产物（8 主靶 + 8 次靶），未手改。
   `test_repros/round4/` 的既往遗留文件（`n4_*`、`r4_0*`、`probe_*`、`ANALYSIS*`、`_probe_*`）零改动、未入索引。
5. 回归哨兵（修复后任何一条转 MISMATCH 即过伸展）：`r4v3_b02/b04/b07/b10/b12`、`r4v3_a01/a04/a10/a11/a12`、
   `r4v3_c01…c05`；既往 `round1/r1_probe_index.json`、`round2/r2v3_probe_index.json`、`round3/r3_probe_index.json`
   三批须同批复跑（本轮按约束未跑全量 402/八分片，也未跑 34 集）。
6. 每条命令 <300s（最长：16 份产物重生成 + 判据单文件 ≈ 40s；电池 31 臂 1.1s）。
