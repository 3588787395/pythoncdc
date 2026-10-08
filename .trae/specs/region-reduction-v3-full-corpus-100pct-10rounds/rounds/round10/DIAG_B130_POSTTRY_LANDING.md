# Round 10 诊断票 B130：F1「try/except 之后的顺序续体被让给 handler 尾声」宿主定位（已完稿）

**状态**：Q1-Q4 已答毕，四问各有实测锚点；未改 `core/`、未跑 git 写、未跑 402 全量门禁。

**状态**：进行中。范围：只诊断，禁改 `core/`，禁 git 写，不跑 402 全量门禁。
**Scratch**：`D:/Temp/r130/`。所有测量均由仓外探针（`sys.path.insert(0, ROOT)`）产出，未触碰 `core/`。

## 0. 被诊断的两个单元（现象已由主代理实测，本票不重推）

| 单元 | 跳转 | 原始应落 | 产物实落 |
|---|---|---|---|
| `site-packages/fly/dumpload/load_daily.pyc :: <module>`（26/27） | `#654 JUMP_FORWARD` | `@2478`（try/except 之后的 print） | `@2562`（handler 头） |
| `site-packages/IQCommon/util/trade_info_utils.pyc :: <module>.get_trade_status`（37/41） | `#112 JUMP_FORWARD` | `@151`（两臂共用的 `error_no == 0` 测试） | `@147`（handler 尾声 `POP_EXCEPT; RERAISE`） |

## 1. Q1：TryExceptRegion 的 natural_exit / merge_block / 后继 与续体块身份

**先更正编号口径（简报本身混用了两种编号）**：`#NNN` 是**归一化序列下标**（剔 `NOP/CACHE/EXTENDED_ARG`），
`@NNNN` 在 `load_daily` 是**字节偏移**、在 `get_trade_status` 是**序列下标**。实测复演（`D:/Temp/r130/diff_jumps.py`，
自己编产品→重编译→逐条比 opcode 与跳转落点下标）：

* `load_daily.<module>`：orig seq=1010 / prod seq=1010，opcode 序列**全等**，唯一差
  `seq#654 off=2454 JUMP_FORWARD`：orig 落 `seq#661`（= 偏移 `@2478` 那条 print），prod 落 `seq#679`（= `@2562` 的 try 体尾跳）。
* `trade_info_utils.<module>.get_trade_status`：orig seq=171 / prod seq=171，同样序列全等，唯一差
  `seq#112 off=598 JUMP_FORWARD`：orig 落 `seq#151`（= 偏移 `@810`），prod 落 `seq#147`（= 偏移 `@786`）。
  ⇒ 简报的 `@151 / @147` 对应**真实字节偏移 810 / 786**（`@147` 块首指令是 `LOAD_FAST count`，
  不是 `POP_EXCEPT`；`POP_EXCEPT/RERAISE` 是它前面 handler 尾声 `@774/@780` 的窗口）。

### 1.1 `load_daily.pyc :: <module>`（探针 `D:/Temp/r130/probe_q1.py`，全文输出 `D:/Temp/r130/q1_load_daily.txt`）

承载区域 = `TRY#2`（`TryExceptRegion` 实例，`region_type=TRY_FINALLY`）：

| 字段 | 实测 |
|---|---|
| `entry` | `@622` |
| `exit` | **None**（`TryExceptRegion` 根本没有 `merge_block` 字段，`getattr` 亦为 None；`natural_exit` 只存在于 `LoopRegion` 路径，try 区域无此概念） |
| `has_else / has_finally` | True / True |
| `try_blocks` | 622,704,740,954,1072,1096,1112,1116,1254,1278,1338,1442,1556,1702,1932,2022,2086,2176,**2198**,**2456**,**2478**,2610,2618,2620 |
| `handler_entry_blocks` | `[2564]`（`PUSH_EXC_INFO; LOAD_NAME Exception; CHECK_EXC_MATCH; POP_JUMP_FORWARD_IF_FALSE→2618`） |
| `except_handlers` | `[('Exception','err',[2572,2574,2600])]` |
| **`else_blocks`** | **`[2562]`** ← 就是产物把跳转接过去的那一块 |
| `finally_blocks` | `[2692,2718,2760,2762]` |
| body→region 外后继 | `@2564`（异常边，几乎全部 try 块）；`@2626` ← `@2562`；`@2692` ← `@2562`/`@2620` |

字节码事实（`cfg.exception_table`：`{'start':622,'end':2562,'target':2564}`，`{'start':2562,'end':2564,'target':2692}`）：
`@2478` 在**保护区间 [622,2562) 之内**，`@2562` 是 try 体的**收尾跳转块**（`JUMP_FORWARD→2626`，紧接 `@2564 PUSH_EXC_INFO`）。
⇒ **简报前提「`@2478` 是 try/except 之后的语句」被证伪**：`@2478`（line 634 的 print）是 **try 体最后一条语句**，
且它是 `@740` 那个 if/else 的**汇合块**（前驱 = `{@2198(then 臂尾，JUMP_FORWARD→2478), @2456(else 臂尾，fall-through)}`）。

* **`@2478`（正确落点）的身份**：`try_block` ∧ `in region.blocks` ∧ 同时被列进 `IfRegion#13`(cond=`@740`) 的 `else_blocks`。
* **`@2562`（错误落点）的身份**：`else_block`（TryExceptRegion 的 `else_blocks[0]`，**伪 else**：源码此处无 else，它是 try 体收尾跳）∧ `in region.blocks`。
* `IfRegion#13`（cond=`@740`，即出错那条 if）：**`merge_block = @2768`**（try/except/finally **之外**的块），
  `else_blocks=[2456, 2478, 2562]`，`then=[954,1072,1116,1096,1112,1254,1278,1338,…]`。
  同区还有 `IfRegion#14`(cond=`@622`, merge=`@2768`, else 含 2456/2478) 与 `IfRegion#15`(cond=`@104`, merge=`@2768`, then 含 2562/2626)。
  ⇒ 真正的汇合块 `@2478` 被当作 else 臂的成员发射，if 的 `merge_block` 被解到了 try 结构之外。

### 1.2 `trade_info_utils.pyc :: <module>.get_trade_status`（`D:/Temp/r130/q1_tiu.txt`）

承载区域 = `TRY#2`（`region_type=TRY_EXCEPT`）：

| 字段 | 实测 |
|---|---|
| `entry` | `@296` |
| `exit` / `merge_block` | **None / 不存在** |
| `has_else / has_finally` | **False / False** |
| `try_blocks` | 296,330,406,436,438,444,446,452,456,458,498,522,526,532,534,552,554,556 |
| `handler_entry_blocks` | `[600]`（`PUSH_EXC_INFO; LOAD_GLOBAL BaseException; CHECK_EXC_MATCH; POP_JUMP_FORWARD_IF_FALSE→778`） |
| `except_handlers` | `[('BaseException', None, [618, 774])]` |
| `else_blocks` | **`[]`（空）** |
| `cleanup_blocks` | `[778, 780]`（`RERAISE` 尾声） |
| body→region 外后继 | `@430`←`@330`（with 自己的 handler）、`@598`←`@456`（FOR_ITER 耗尽边）、`@600`←几乎所有 try 块（异常边） |

* 出错的跳转块 `@598`（单条 `JUMP_FORWARD→810`，前驱只有 `@456` FOR_ITER 的耗尽边）**不在该 TryExceptRegion 里**
  （`NOT in region.blocks`），它是保护区间 `(554,598)` 右端之外的一块；`region#8 IfRegion(cond=@202, merge=@890)` 把它列进 `then`。
* **`@810`（正确落点）身份**：`NOT in` try 区域；属 `IfRegion#8` 的 `then_blocks`；是 `region#14 Region(entry=@810, BASIC)` 的入口；
  前驱 = `{@270(while 入口测的假边), @598, @786}` ⇒ 它是 **while 循环出口 / try 语句之后的共享汇合**。
* **`@786`（错误落点）身份**：`NOT in` try 区域；只属 `LoopRegion#1(WHILE, entry=@270)`；
  块内容 `LOAD_FAST count; LOAD_GLOBAL GET_TRADE_STATUS_TIME; COMPARE_OP <=; POP_JUMP_BACKWARD_IF_TRUE→@294`
  （while 的**底部重测**），其**唯一前驱** = `@774`（handler 体尾 `POP_EXCEPT; JUMP_FORWARD→786`）。
* 源码真形（由 `@598` 落在保护区间之外 + `@810` 为循环出口推得，并用 s6/s7 双臂编到 3.11.7 验证过布局）：
  `while count <= GET_TRADE_STATUS_TIME:` / `try:` … `for items in csv_reader: …` … **`break`（或等价的 `else: break`）**
  / `except BaseException: …`。产品里 **`break`/`else: break` 整条不见了**（见 `D:/Temp/r130/tiu_out.py` 1032-1049），
  于是 for 的耗尽边落到 try 体之后的 fall-through = handler 尾声的续体 `@786`。
* ⇒ 简报前提「`@151` 是两臂共用的 `error_no == 0` 测试段」**部分不确**：共用测试段是 `@890`
  （`LOAD_FAST; POP_JUMP_FORWARD_IF_FALSE`，`IfRegion#8` 的 merge），`@810` 只是通往它的跳板；
  真正的语义缺口是 **try 体尾的 `break` 没发射**，不是「测试段被抢」。


## 2. Q2：发射端在哪一步、用什么依据为这条跳转挑落点

**先说结论：两条跳转的落点都不在 `region_ast_generator.py`（发射端）被挑选，而在
`core/cfg/region_analyzer.py`（区域归约端）被决定；两处是**不同的函数、不同的判据**。**
发射端只是把「前一条臂之后还有什么语句」照抄成结构，落点由 CPython 重新编译时自然成形
（我用 `D:/Temp/r130/diff_jumps.py` 证明：orig 与 prod 归一化序列**逐条 opcode 全等、长度全等**，
唯一差就是那一条跳转的目标下标 ⇒ 发射端没有多发/少发指令，缺的是**语句归属**）。

### 2.1 `load_daily :: <module>` —— 宿主 = if 的 merge 重算规则 `[r3-b100-armjoin]`

宿主行（逐层证据链，均由 `sys.settrace` 行级探针实测，探针
`D:/Temp/r130/probe_merge_trace4.py`、`D:/Temp/r130/probe_armjoin.py`，输出
`D:/Temp/r130/merge_trace4.txt` 同型）：

| 步 | `file:function:line` | 实测 |
|---|---|---|
| 1 | `core/cfg/region_analyzer.py:_identify_conditional_regions:19524` | `merge = self._find_nearest_common_post_dominator(then_succ=@954, else_succ=@2456)` → **None**（then 臂内含 `RAISE_VARARGS` 块 `@1112`，其 ipost 链被异常边打断；`@954.postdoms=[954]`） |
| 2 | `core/cfg/region_analyzer.py:_identify_conditional_regions:19639-19644` | `_r100_join = self._compute_arm_level_join(@954, @2456, {条件块,两臂入口}∪chain_blocks, current_merge=None)` → **@2768**，随后 `merge = _r100_join`。**这一行就是把落点挑错的地方** |
| 3 | `core/cfg/region_analyzer.py:_build_basic_if_region:20995-20998` | `IfRegion(..., merge_block=merge=@2768, else_blocks=[2456,2478,2562])` |
| 4 | 判据本体 | `core/cfg/region_analyzer.py:_compute_arm_level_join:3054`，其 (4)/(4b)/(5)/(6) 号判据即误发处 |

**误发条件（只用白名单事实）**：对 if 的两条臂做逐层前向 BFS（只走「非异常边且目标偏移更大的后继」）时，
真正的同层汇合块 `@2478` 被拒——它的**正常前驱只有两条臂自己**（then 臂尾 `@2198` 的
无条件前向跳转 `JUMP_FORWARD→2478` ∧ else 臂尾 `@2456` 的 fall-through），
即 (4) 号判据要的「E 箱（来自本 if 之外的同层兄弟路径）非空」**不成立**；
(4b) 号「臂自声明出口」例外又要求**其余臂全部终态收束**（return/raise 使控制流永久离开本作用域），
而 else 臂 `@2456` 并未收束 ⇒ 也不成立。于是 BFS 继续向外走，第一个被认领的候选是
`@2768`：**它的 E 箱证据来自跨越外层 `TryExceptRegion`（TRY_FINALLY, entry=@622,
else_blocks=[2562]=try 体收尾跳）边界的跳过边 `@104→@2768`**，而不是紧随本 if 的同层兄弟路径。
⇒ 认领了跨区域的更外层汇合块后，`_collect_branch_blocks(else_succ=@2456, merge=@2768)`
（`region_analyzer.py:20287`）把真正的汇合块 `@2478` 连同 try 体尾 `@2562` 一起收进 else 臂。
（合取的另一半，产物 AST 侧：`D:/Temp/r130/ld_out.py` 第 470-472 行
`else:` 臂内含 **两条** print（缩进 16 空格），try 体在 `If` 之后**没有兄弟语句**，
故原 if 的汇合语句在产物里不作为 if 之后的语句存在 ⇒ then 臂尾跳被编译到 try 体收尾跳 `@2562`。）
**负对照（同一判据的健康例）**：`D:/Temp/r130/s5_…shapeA….pyc::f5`（源码形状与 load_daily 同：
try 体内 `if/else`，汇合语句是 try 体最后一条语句）第 1 步 NCPD 直接给出 @78，
`_compute_arm_level_join(..., current_merge=@78)` 依 (6) 返回 None ⇒ merge=@78 正确、产品正确。
⇒ 触发的必要条件是 **NCPD(两臂入口)=None**（臂内含终态 raise/return 打断后必经链），
这与 load_daily 有、s5 没有完全对应。

### 2.2 `trade_info_utils :: <module>.get_trade_status` —— 宿主 = try 的 else 子句被抑制

| 步 | `file:function:line` | 实测 |
|---|---|---|
| 1 | `core/cfg/region_analyzer.py:_find_try_else_blocks:11636-11637` | `if self._try_body_terminates_abnormally(try_region): return []` ⇒ `else_blocks=[]`、`has_else=False`（`region_analyzer.py:9721-9765` 处 `region.has_else` 因此不被置真） |
| 2 | `core/cfg/region_analyzer.py:_try_body_terminates_abnormally:11609-11610` | 命中块 **@532**（尾 opcode `RETURN_VALUE`，即 `return items[2]`）⇒ `return True` |
| 3 | 同函数 `:11582-11593` 的护栏为何没挡住 | 护栏 `if block in _loop_region_blocks: continue` 依赖 `self._filter_regions(self.regions, LoopRegion)`；**实测调用时刻 `len(self.regions)==0`**（`D:/Temp/r130/probe_loop_blocks.py` 输出：`n_regions=0 types=[] n_loop_regions=0 loop_union=[] offenders=[(532,'RETURN_VALUE',False,True),(552,...),(554,'JUMP_BACKWARD'),(556,...)]`），而 analyze 完成后 `LoopRegion(entry=@456).blocks` 明明含 532/552/554/556 ⇒ 判据在「区域表尚未填好」的阶段读空集，把**循环体内的 return** 当成了 **try 体的异常终止** |
| 4 | 落点成形 | else 子句既被抑制，发射端把 try 体最后一条语句（`for`）的完成边接到「try/except 之后 */* 的下一条语句」= while 的底部重测 `@786`（该块的唯一前驱是 handler 尾声 `@774 POP_EXCEPT; JUMP_FORWARD`），而不是循环出口 `@810` |

**误发条件（白名单事实）**：`TryExceptRegion.has_else` 的识别被
「某 try_body 块尾为 `RETURN_*`」一票否决，**而该块同时是其嵌套 `LoopRegion` 的成员**
（它的 RETURN 是循环体内的 return，不是 try 体的收尾）；
否决发生在 `self.regions` 仍为空表的时刻，因此「块在循环区域内」这一身份不可用。
（合取另一半：产物 AST 侧 `D:/Temp/r130/tiu_out.py` 1032-1049 的 `Try` 节点
`handlers=[BaseException]`、`orelse=[]`、try 体最后一条语句是 `For`，
**整个函数体内没有任何 `Break` 节点** ⇒ 原始 `@598`（保护区间右端之外、唯一前驱为 FOR_ITER 耗尽边、
落点为循环出口）对应的语句在产物里不存在。）
**负对照**：`s6`（同形状但循环体内无 return）与 `s7`（写成 `else: break`）
`_try_body_terminates_abnormally` 都返回 False（JUMP_BACKWARD 被 R119b 护栏豁免），
`_find_try_else_blocks` 返回 `[Block@126]` ⇒ `has_else=True`、`else_blocks=[126]`，产品发射
`else: break`，判据 success（见 §4）。


### 2.3 关于「发射端」的诚实说明

两案的落点都**不是** `region_ast_generator.py` 某行「枚举候选→评分→取首」选出来的：
发射端没有 goto/落点表（`grep 'goto' core/cfg/region_ast_generator.py` 无匹配），
跳转是 CPython 重编译产物时**由语句归属自然成形**。
因此给实现票的宿主必须是 `region_analyzer.py` 的两行（§2.1 步 2 / §2.2 步 1-2），
发射端一行都不用改。若实现票被要求「必须在发射端」，那它会找不到靶；
本票的实测依据是：把 merge / has_else 判对之后，发射端现有代码即可产出正确落点（s5/s6/s7 三例即证）。

`_compute_arm_level_join` 的认领循环在 `region_analyzer.py:3332-3349`（层序取首个
「正常前驱分箱 ≥ 2 箱 ∧ E 箱非空」的块），E 箱由 `_pred_labels:3213-3232` +
`_armjoin_is_skip_edge` 给出；`current_merge is None` 时的放行门在 `:3383-3388`（要求至少一臂收束）。
误发的完整链条（全部实测，`D:/Temp/r130/probe_armjoin.py` + `skip_edge`/后继直测）：

| 候选块 | 正常前驱 | `_armjoin_is_skip_edge` 实测 | 分箱结果 | 认领？ |
|---|---|---|---|---|
| `@2478`（真汇合，∈ `try_blocks`） | `{@2198(臂0 无条件 JUMP_FORWARD), @2456(臂1 fall-through)}` | `(@2198→@2478)=False`, `(@2456→@2478)=False` | `{0,1}`，E 空 | **否（(4) 拒）** |
| `@2562`（try 体尾跳，∈ `else_blocks`） | `{@2478(臂), @704(外)}}` | `(@704→@2562)=`**False** | `{0,1}`，E 空 | 否 |
| `@2626/@2690`（∈ region.blocks，finally 内联） | 单箱/臂内 | — | E 空 | 否 |
| `@2768`（**不在该 try 区域内**） | `{@2690(臂), @104(外层 if 的 after-if 跳)}` | `(@2690→@2768)=False`，`(@104→@2768)=`**True** | `{0,1,'E'}` | **是 ⇒ merge=@2768** |

臂收束门 `:3387` 得以放行，是因为 then 臂内 `@1112` 块末 `RAISE_VARARGS` 的
`all_succs=[2564]` 全是异常边 ⇒ 其「正常后继」为空 = (2) 号收束（实测，见上表所在 probe 输出）。


## 3. Q3：两文件是否同一处

**不是同一处。分开报，不并案。**（本票禁止前例中的「一判据吃两文件」结论。）
双向否证（实测，`D:/Temp/r130/`）：

| 轴 | `load_daily` | `get_trade_status` |
|---|---|---|
| 宿主函数 | `_compute_arm_level_join`（消费点 `:19639-19644`） | `_try_body_terminates_abnormally`（消费点 `_find_try_else_blocks:11636`） |
| 该宿主在**对方**单元上是否发火 | **否**：对 get_trade_status 的 6 个 IfRegion 逐一用同参数调 `_compute_arm_level_join(…, current_merge=既有merge)` 全部返回 None（merge 未越权） | **否**：`_try_body_terminates_abnormally` 对 load_daily 三个 try 区域（@64/@3614/@622）全部返回 **False**，且三者 `has_else=True`、`else_blocks` 均被正常识别 |
| 错接块的区域身份 | 正确落点 @2478 **是** try 区域成员（`try_block`），错误落点 @2562 **是** 同一 try 区域的 `else_blocks[0]` | 正确落点 @810 与错误落点 @786 **都不是** try 区域成员；@786 只属外层 `LoopRegion(WHILE, entry=@270)` |
| 缺的语句 | if/else 的**汇合语句**被吞进 else 臂（AST：`If@418.orelse` 有 2 条 print，父序列里 If 之后无兄弟语句） | **整条 `break`/`else: break` 缺失**（AST：全函数 `Break` 节点数 0，`Try.orelse==[]`，`While.body==[Try]`） |
| 触发签名 | `NCPD(两臂入口)=None`（臂内含 `RAISE_VARARGS` 块 @1112，其后继只有异常边） | `try_blocks` 内含 `RETURN_VALUE` 块（@532），且判据运行时 `self.regions` 为空表 ⇒ 循环成员身份不可用 |
| 最小复现 | **未复现**（4 条规定复现 + s5/s8 两条形状复现全 success） | **已复现**（s9，见 §4） |

共同点只有「产物序列与原始逐条同长同 opcode，唯一差是一条前向跳转的目标」这一**读数形状**；
机制、宿主函数、被错接块的身份、缺失的 AST 构造全不同 ⇒ 一条判据吃不下两文件。

## 4. Q4：最小复现（全部 `python -X utf8`，编译/反编译/判据三步齐全）

本机 CPython：**3.11.7**（`sys.version` 实测）。每条命令均 <10 s。
规定四条复现（`D:/Temp/r130/r1..r4_b130_*.py`）：

| # | 源形状 | 判据读数 |
|---|---|---|
| 1 | `try/except` + 之后一条语句（`print(y); return y`） | **status=success units=2/2** |
| 2 | `try/except/else` + 之后一条语句 | **status=success units=2/2** |
| 3 | `for` 内 `try/except` + 之后一条语句 | **status=success units=2/2** |
| 4 | 对照：`try/except` 后无语句 | **status=success units=2/2** |

⇒ **简报设想的「try 后顺序续体」最小复现不成立**：单纯形状不复现（规定 4 条全绿，含 4 号对照）。

补充形状臂（**超出规定 4 条复现预算，只为定位触发包**，同法跑真管线）：

| 臂 | 形状 | 读数 |
|---|---|---|
| s5 | try 体内 `if/else`，汇合语句是 try 体最后一条语句（+ except + finally） | success 2/2（merge=@78 正确，负对照） |
| s6 | `while` + try 内 `for`（体内无 return）+ try 体尾 `break` | success 2/2，产物写成 `else: break` |
| s7 | 同 s6 但源码显式 `except … else: break` | success 2/2 |
| s8 | case-1 形状尝试：try 体内 `if/else`，then 臂含 `raise`，汇合语句是 try 体尾 | **success 2/2（未复现）**：`NCPD(两臂)=[None]` 但 `_compute_arm_level_join(…, None)` 依 `:3387` 弃权 |
| **s9** | case-2 形状：`while` + try 内 `for`（体内两条 `return`）+ try 体尾 `break` + `except` | **failure units=1/2**，`D:/Temp/r130/diff_jumps.py` 读数：orig seq=60 / prod seq=60，opcode 全等，唯一差 `seq#38 off=146 JUMP_FORWARD`：orig 落 `seq#58`（循环出口后的 `LOAD_FAST; RETURN_VALUE`），prod 落 `seq#54`（while 底部重测，其唯一前驱是 handler 尾声 `POP_EXCEPT; JUMP_FORWARD→54`）。产物 `f10` 内 **无任何 Break 节点** ⇒ 与 get_trade_status 同一机制 |

⇒ **case 2 有可复现最小臂 s9**（21 行，源文件 `D:/Temp/r130/s9_b130_c2_return_in_loop_then_break.py`），
可作实现票的红→绿电池；**case 1 本票未拿到最小臂**，实现票须以语料单元
`fly/dumpload/load_daily.pyc::<module>`（判据 `units=26/27`，`Failure: Different control flow`，
本票实测 `D:/Temp/r130/diff_ld.txt` 复演）为靶，配合 `probe_armjoin.py` 的 s5 负对照。

s9 的宿主同签实测（`D:/Temp/r130/loop_blocks_s9.txt`，与 `get_trade_status` 的
`D:/Temp/r130/loop_blocks_tiu.txt` 逐项同形）：
`_try_body_terminates_abnormally` 被调时 `n_regions=0 / loop_union=[]`，
offenders = `[(92,'RETURN_VALUE',in_loop_union=False,in_narrowed=True), (112,'RETURN_VALUE',…), (114,'JUMP_BACKWARD',…)]`
⇒ 返回 True ⇒ `else_blocks=[]`。s5/s6/s7/s8 的同一函数都返回 False（见各 `loop_blocks_*.txt`）。


## 5. 推荐的实现位点与判据（一句话）

* **case 2（`get_trade_status`，也吃 s9）**：`core/cfg/region_analyzer.py:_try_body_terminates_abnormally:11609-11610`
  —— 判据补合取：命中「块尾 `RETURN_*`」的块**同时**须「不在任何循环区域成员内」；
  由于此刻 `self.regions` 为空表，循环成员身份须由**边**给出（该块沿后继可达一含 `FOR_ITER`/回边头的块，
  或它的某条前向路径进入一个以其自身块为回边目标的回边闭包），不得读 `self.regions`、不得读偏移/计数。
* **case 1（`load_daily`）**：`core/cfg/region_analyzer.py:_compute_arm_level_join:3332-3349`（消费点 `:19644`）
  —— 判据补：候选 J 的 **E 箱证据若来自跨越本 if 所属最内层包含区域（此处 `TryExceptRegion entry=@622`，
  且该区域把 J 的前身 try 体尾块认领为自己的 `else_blocks`）之外的跳过边，则该 E 证据不计**；
  同时把「一臂以**无条件前向跳转**落在 J′ ∧ 另一臂 fall-through 落在同一 J′ ∧ J′ 在该包含区域块集内」
  视为 J′ 的同层汇合认领（即 (4b) 的 `arm_declared_exit` 不应要求「其余臂全部终态收束」，
  在双臂共落点时该要求多余）。
* 两处均**不是静默豁免**：`_try_body_terminates_abnormally` 的 `return True` 与
  `_compute_arm_level_join` 的 `_join` 认领都是**主动改写**（一个把 has_else 关掉、一个把 merge 外推），
  不是「悄悄少发射」；但它们造成的后果都是产物少一条语句（`break` / if 后的汇合语句），
  按 `rules.md §1.5 C3` 应视为「汇合块被区域外路径引用而未显式认领」，须与主修同票封闭。

## 6. 被本票证伪 / 更正的前提（含简报与我自设的）

1. **简报：「`@2478` 是 try/except **之后**的顺序续体」＝错。** `@2478` 在异常表保护区间
   `[622,2562)` **之内**，是 try 体的**最后一条语句**（line 634 的 print），并且是 `@740` 那个 if/else 的汇合块。
   真正的 try/except 之后代码是 `@2626`/`@2692`（finally 内联）与 `@2768`。
   ⇒ 本票的现象不应叫「post-try continuation」，case 1 的准确名字是
   **「if 的汇合块被吞进 else 臂（merge 被外推到包含区域之外）」」。
2. **简报：「`@151` 起＝两臂共用的 `error_no == 0` 测试段」＝不准确。** `@151`（序列下标）＝字节偏移 `@810`，
   它只是 `JUMP_FORWARD→890` 的跳板；共用测试段是 `@890`（`LOAD_FAST; POP_JUMP_FORWARD_IF_FALSE`，
   `IfRegion#8` 的 merge）。`@147`（偏移 `@786`）块首是 `LOAD_FAST count`，
   `POP_EXCEPT/RERAISE` 在它**前面**的 handler 尾声块（`@774/@780`）。
   真正缺的语句是 try 体尾的 **`break`（或 `else: break`）**，不是「测试段被抢」。
3. **简报编号口径**：`#654/#112` 是归一化序列下标；`@2478/@2562` 是 load_daily 的**字节偏移**，
   而 `@151/@147` 是 get_trade_status 的**序列下标**（两案口径不一致，实测换算见 §1）。
4. **简报「F1 是一条判据吃两文件」**：否证见 §3（双向：对方宿主在本案单元上都不发火）。
5. **简报「TryExceptRegion 有 natural_exit / merge_block」**：`TryExceptRegion` **没有** `merge_block` 字段，
   `exit` 实测为 None（两案皆然）；`natural_exit` 只在 `LoopRegion._find_loop_else` 路径存在。
   Q1 的答案是「该区域根本没有出口字段，续体完全由发射端按语句序推断」。
6. **我自设的前提也被证伪**：我以为「try/except 后跟一条语句」的最小形状即可复现（规定 4 条复现臂 + s5/s6/s7/s8
   共 8 条形状臂中 7 条全绿），实际只有 s9（case 2 的 return-in-loop + 尾 break）复现；
   case 1 需要臂内含终态 `RAISE` **且** NCPD 给不出 merge，我未能在预算内把该组合压到 20 行以内（s8 差一步：
   规则在 `:3387` 因「无臂收束」而弃权）。
7. `load_daily` 的产物与盘上 `site-packages/fly/dumpload/load_dailyOK.py` **逐字节相同**（`diff` 无输出，512 行），
   而判据仍报 `units=26/27 Failure: Different control flow` ⇒ 该 `*OK.py` 不是通过态参照，
   不可当负对照使用（我也未删除/覆盖它）。

## 7. 探针与产物清单（全在 `D:/Temp/r130/`，`core/` 未被写入）

`probe_q1.py`（Q1 区域/身份普查）、`q1_load_daily.txt`、`q1_tiu.txt`、
`diff_jumps.py` + `diff_ld.txt` / `diff_tiu.txt`（原始↔重编译产物逐条比对）、
`scan_offs.py`（偏移→块反查）、`probe_shape.py`（源→dis/块/区域）、
`probe_else_trace.py`（try-else 识别的行级 trace）、`probe_loop_blocks.py`（判据运行时 `self.regions` 为空之实测）、
`probe_loops_membership.py`、`probe_if_merge.py`（后支配事实）、`probe_if_construct.py`（merge_block 赋值点栈）、
`probe_merge_trace4.py`（merge 逐行归因）、`probe_armjoin.py`（宿主函数直测 + 负对照）、
源与 .pyc 与产物：`r1..r4_b130_*`、`s5..s9_b130_*`（`*_out.py` 为管线产物）。

