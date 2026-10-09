# 第 20 轮开工前提：IfRegion 识别的**顺序墙**（本轮实测得出，非推测）

已落地（门 19）：`region_ast_generator.py dff6e81a5f2ff9f6`、`ast_generator_v2.py beeaf14435e22922`、
`region_analyzer.py 640d33a77dcb71c2`；语料 **6586/6617 单元、391/402 文件**，残余 11 文件 / 31 单元
（名册 `rounds/round19/RESIDUAL_ROUND19.md`）。

## 事实（grep/读码所得，行号为 pristine 分析端）

1. `_identify_conditional_regions` 在 **:18463**，其主循环遍历 `self.cfg.get_blocks_in_order()`
   ＝**按块偏移升序** ⇒ 父区（@992）先于子区（@996）构造。这与原则1「自底向上归约」相反。
2. 该函数内 **没有任何跨 IfRegion 的 claimed 集合**：`claimed` 只存在于
   `_identify_chained_compare_regions`（**:17994**，初值取 loop/try/with/match/assert 区域的 blocks）。
   ⇒ 构造父区时「子区已成形」这一前提不成立。
3. `_collect_branch_blocks`（**:31494**）docstring 自己声明两件事：
   「不使用 block_to_region 排除，区域归属冲突由上层调用者处理」，以及原则4 的例外
   「entry 是子入口块，必须被收集」（`stop.discard(entry)`）。
   ⇒ 把「已识别区域的内部块」当边界既拿不到（见 2），拿错了又把臂体退化成 `pass`（见下）。

## 已实测否决的一条写法（勿重复）

在 `else_stop = {then_succ} | (boundary_stop - {else_succ})` 之后加入
「`self.regions` 中 entry 等于本臂入口的区域，其 blocks 减 entry 并入本臂停止集」：

```
api_base 27/28（未翻正）  strategy 26 -> 25  klinedata 63 -> 61
quotation 153 -> 151      matcher 17 -> 16
```

⇒ 零翻正 + 四处回退。原因即上面的 2：那一刻区域集合尚未定序，
把未定形的块集当边界会切掉正常臂体。

## 下一手的可用出口（api_base + strategy，两文件各只差落点 2/4）

- 父区的正确 merge 就是**子区的 merge（@1098）**，且不必依赖子区身份即可由结构推出：
  复用 `_find_nearest_common_post_dominator`（:2354）、`_compute_in_loop_if_merge`（:2974，3 调用点）、
  `_compute_merge_from_jump_targets`、`get_if_branch_boundary_stop`（:864）、
  `[R31-B]` 同层停止集规则（:20366 / :22744）、merge-claim 守卫（:22920、:29975-29993）。
- 若要真正把子区先归约（改识别顺序），波及面大，必须先证明其余 15 个面板文件逐读数不动。
- 修 `klinedata` 的两处之一（臂尾出口身份）同样落在这条 merge/边界带上（见
  `rounds/round19/banked_r19t3/` 与 `DIAG_R1516`），三处可能共一条判据。

镜像工程师 r20d 正按上述出口施工（`D:/Temp/r20d`，只交整文件，不动实时仓库）。

## 附：`real_quote.<module>.RealQuoteData.get_tick_direction`（+1 单元档，生成端，唯一真差已定位）

`unit_diff … --all` 读 `hunks=1 landings=1 delta=1`；把对齐后**逐条带操作数**比出来，
真差只有**一处插入**，其余 11 条 `replace` 全是它造成的 2 字节位移影子：

```
ORIG  @1090 CALL ; @1100 POP_TOP ; @1102 LOAD_FAST redata ; @1104 RETURN_VALUE
PROD  @1090 CALL ; @1100 POP_TOP ; @1102 JUMP_FORWARD ->1108 ; @1104 LOAD_FAST redata ; @1106 RETURN_VALUE
                                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                          原来「顺序落入共享 return redata」的那条路径，
                                                          被改成先无条件跳到 @1108（下一段 redata 检查块），
                                                          于是多插 1 条 JUMP_FORWARD（+2 字节）
```

⇒ 缺陷形状：**一条臂体以 `Call`（`self.log.quote.debug(…)`）语句结尾时，发射端在该语句之后
补了一条无条件跳转**，而原字节码此处**落空进入共享的 `return redata`**（该 `return` 在产物里也发了，
所以不是丢语句，是多插一条死跳）。
开票要点：判据应为「臂尾语句本身以无条件跳/返回结尾 or 臂的后继就是区域的 merge 且 merge 由落空边进入」
时不发这条跳；`landings=1` 那处 `@1022 JUMP_FORWARD ->199 vs ->202` 同为位移影子，不是第二缺陷
（勿按 11 条记账）。该文件另有 1 个失败单元 `get_real_minute_kline`（+2 ⇒ 不产生整文件翻绿）。

### 源码级补充（同单元，实读 `real_quoteOK.py` line 984-997）

```
if redata: …
elif flag == 1:  system_log.debug('分笔数据转化异常，默认返回空值')
elif flag == -1: system_log.debug('分笔数据返回空值')      ← 末条 elif 臂
else:            return redata                             ← else 体就紧跟在臂体之后
try:
    if redata: …                                            ← 区域的 merge（@1108）
```

原字节码：末条 elif 臂体 `CALL; POP_TOP`（@1090/@1100）之后**无跳**，直接**落入紧随的 else 体**
`@1102 LOAD_FAST redata; RETURN_VALUE`。
产物：同一位置多发一条 `@1102 JUMP_FORWARD -> 1108`（即臂尾“跳过 else 体去往 merge”的跳），
而它要去的 merge 前面紧接的 else 体本身**以 RETURN 结尾**（永不落到 merge），
CPython 因此**省略**这条臂尾跳 ⇒ 产物多出的是一条**死跳**（+1 条 / +2 字节），
其余 11 处差异全是这 2 字节的位移影子。

判据形状（生成端，勿写成绝对偏移）：**当 if/elif 链的 merge 只能经由「紧随某臂体之后的
else 体」进入，而该 else 体自身以无条件终结（RETURN/RAISE）结尾时，末条臂不得再发臂尾跳过跳**。
落点候选与既往否决：`_if_generate_normal` / `_process_if_blocks` 的臂尾跳支（`:21283-21319`、
`:25336-25340` 带 R64-B2 让位契约注释）；`_loop_tail_exit_sink_pair`（分析端 :28390 / 生成端 :52045）
经 r19t5 实测只打另一对（本形上把 landings 3→0 但仍 29/30 那类），**不是**本单元的支路。

### 判决性实验（同解释器实编两形，非推断）：本单元的根因是**把链后的语句捏成 `else:` 臂**

```
形A  if r: a() elif 1: b() elif -1: c() else: return r ; after()
     →  … CALL; POP_TOP @152; JUMP_FORWARD 160 @154; LOAD_FAST redata @156; RETURN_VALUE @158
        （JUMP_FORWARD 计 3 条）                ↑ 与**产物**逐指令同形（多这一条跳）
形B  if r: a() elif 1: b() elif -1: c() ; return r
     →  … CALL; POP_TOP @152; LOAD_FAST redata @154; RETURN_VALUE @156
        （JUMP_FORWARD 计 2 条）                ↑ 与**原字节码**逐指令同形（无此跳）
```

⇒ 原源码在该处**没有 else**：`return redata` 是 **if/elif 链之后的语句**（链的 merge/续体）。
产物把它当成 `else:` 臂发出，于是末条 elif 臂必须跳过 else 体 ⇒ 多一条死跳（+2 字节），
连带 11 处位移影子与 1 处落点差。**先前把它记作「发射端多发一条跳」是错的定性**——
缺的是「else 臂的身份判错」，不是跳本身。

判据形状（识别端/装配端二选一，结构判据）：**`elif_final_else` 不得等于本区域的 merge/续体块**；
若候选 else 体块就是「末条臂落空所到达、且链条件跳转的目标同一块」，则该块是续体不是臂，
链不带 else，语句交回链后正常发射。
候选落点：分析端 IfRegion 构造里的 `elif_final_else` 赋值处，与生成端 elif 链装配
（`_if_generate_elif_chain` 读 `elif_conditions/elif_bodies/elif_final_else` 的段）。
注意本轮 r20d 工程师只占 `region_analyzer.py`；若要动分析端须等其交付落地或否决后再做，
或先在生成端装配处加同一条结构判据（读区域已有字段，不新建第二真相源）。

## R20-2 两次生成端尝试＝实测零翻正（未装实时仓库，镜像 `D:/Temp/r20e`）

在 `_if_generate_elif_chain` 的 `_r23n18_partial_merge_block = None` 之前插入
「末条 elif 臂体落空即进入候选 else 体 ⇒ 判为链续体，清 `elif_final_else`、
`else_blocks=[]`、并从 `region.blocks` 释放这些块」的结构判据，两版取臂尾块的写法都试过：

```
v1  region.elif_bodies[-1][-1]                       → real_quote 43/45（无翻正）
v2  max(所有 elif_bodies 的块, key=start_offset)      → real_quote 43/45（无翻正）
两版 collateral 全部不动：quote 86/92、matcher 17/17、quotation 153/153、
klinedata 63/64、trade_live_broker 118/128
```

⇒ 判据**没有在该区域命中**（或命中后仍被别处重新取得 else 臂）。
下一手不要再接这个猜测，先做**一次只读打印**（独立进程建 CFG，不在 analyzer/generator 内 print）：
对 `real_quote.pyc` 里含原偏移 `@1022/@1090/@1102/@1108` 的那条 IfRegion/IF_ELIF_CHAIN，
导出 `condition_block / elif_conditions / elif_bodies（逐臂块表）/ elif_final_else / merge_block / blocks`
六个字段的实际值与偏移，再判断「else 臂」究竟在哪个字段、由哪一段代码取得。
注意本战役已两次栽在「未先看字段实值就写判据」上（klinedata 的单点修、api_base 的停止集）。

## R20-2 的判决字段实值（独立进程建 CFG 所得，`real_quote.pyc::<module>.RealQuoteData.get_tick_direction`）

```
IfRegion entry=858  merge=1106
   elif_conditions = [944, 1024]        # flag == 1  /  flag == -1
   elif_bodies     = [[956], [1036]]
   elif_final_else = [1102]             ← 被当成 else 臂的块
IfRegion entry=944  merge=1102  elif_conditions=[1024]  elif_bodies=[[1036]]  elif_final_else=[]
（另有 @1102/@1106 的 BASIC 区域、TryExceptRegion entry=1108、LoopRegion entry=1174）
```

关键结构事实（原字节码跳转）：`@942 JUMP_FORWARD -> 1106`、**`@1022 JUMP_FORWARD -> 1102`**、
`@1034 POP_JUMP_FORWARD_IF_FALSE -> 1102`（orig），且末条臂体 `@1036` 以 `CALL; POP_TOP`（@1090/@1100）
**落空进入 @1102**。⇒ `@1102` 同时是**臂尾跳过跳的落点**与**末臂的落空后继**：
它是链之后的续体语句（`return redata`），不是 else 臂。产物把它当 else 臂 ⇒
末臂必须跳过它 ⇒ 多发一条死 `JUMP_FORWARD`（就是本单元唯一真差）。

**下一手应用的判据（比我先前的两条都强，且有实值支撑）**：
`elif_final_else[0]` 若等于**本链任一臂体末指令 `JUMP_FORWARD` 的落点**，
或等于**末条臂体的落空后继**，即判为幻影 else：清 `elif_final_else`、
`else_blocks=[]`，并把该块从 `region.blocks` 释放给宿主语句流（照 `[B71]` 的释放写法）。
我先前两版只测了「末臂落空后继」一条，且都在 `_if_generate_elif_chain` 里
（`region.elif_bodies[-1][-1]` / 按最大 start_offset 取臂尾块），**两次均零翻正**——
说明该链在生成端根本没走到我插桩的那段（或 `elif_bodies` 的实参形态与我假设不同：
本 dump 显示它确实是按臂分组的块表）。⇒ 先确认这条链由哪个入口装配
（`entry=858` 的 IfRegion 在生成端的分派路径），再决定插桩点；
不要在未确认命中前先猜第三版判据。

## R20-2 停手登记（主代理，17:12）

- v1/v2 两版判据**零翻正 ⇒ 插桩点未被命中**（该链 `entry=858` 的装配路径不是
  `_if_generate_elif_chain` 里我改的那一段，或 `elif_bodies` 在运行时的形态与 dump 所见不同）。
  下一手必须**先证明命中**再写判据：在镜像里给该处加一个只写文件计数器（不读 CFG 属性），
  跑 `real_quote` 看计数是否为正；计数为零就说明走的是别的路径，改判据没用。
- v3（加「else 块 == 任一臂体末跳的落点」一条）在镜像里把 `region_ast_generator.py` 写成
  **语法错误**（IndentationError @15603），随后所有产物读数 `units=0/45`、`0/92`、`0/17`、`0/153`、`0/64`
  全部是**坏具产生的 VOID**，不是回退也不是证据（依 [[feedback-no-record-before-measurement]]：
  失败的具给出的数不记账）。实时仓库 `core/` 全程未写（`git status --porcelain core/` = 0，
  三件哈希仍 `dff6e81a5f2ff9f6 / beeaf14435e22922 / 640d33a77dcb71c2`）。
- 本轮（第 19 轮）落地成果不变：**6586/6617 单元、391/402 文件**（`order_api` 整文件翻绿）。
  R20-1（api_base+strategy，工程师 r20d 在飞）与 R20-2 均**未**产生可安装候选。
