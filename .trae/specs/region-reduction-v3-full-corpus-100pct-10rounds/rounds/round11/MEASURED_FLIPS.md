# Round 11 实测翻正记录（只登记我亲自量到的读数，不转录工程师的自报数）

## 1. B133 case 1 — `fly/dumpload/load_daily.pyc` **27/27 status=success**

时间 2026-10-08 04:49。验证方式**不入仓库**：施工者当时仍在 A/B 之间来回还原镜像
（12:26 我取到的 `region_analyzer.py` 仍是封表字节 38a1d5142d132fd7，12:43 才变成 4db00de8e56b2503），
而 `region_analyzer.py:3332-3349 _compute_arm_level_join` 改的正是**臂级汇合点选择**，
与同时在跑的 B134（bar / strategy_universe 纯落点）、B136（handlers 环出口落点）、B137（strategy 四处目标差）
是同一族判据——若把改后字节装进仓库，三张诊断票的行号锚点与实际行为都会漂。
故我在**自己的镜像** `D:/Temp/r11b133/wt` 里复验：

| 项 | 值 |
|---|---|
| 镜像 `core/cfg/region_analyzer.py` | `4db00de8e56b2503`（改后） |
| 镜像 `core/cfg/region_ast_generator.py` | `e9a8f65f6451bcc8`（封表，未动） |
| `fly/dumpload/load_daily.pyc` | 26/27 → **27/27 status=success**（整文件翻正） |
| `fly/data/quotation.pyc` | **153/153** 不回退 |
| `IQCommon/util/trade_info_utils.pyc` | 37/41（**未**变 38/41） |
| `matcher` 16/17、`handlers` 29/30 | 不变（与该票无关，符合预期） |
| 仓库 `git status --porcelain -- core/` | 0（仓库字节未被本次验证触碰） |

**该字节状态只含 case 1**：`trade_info_utils` 保持 37/41 而非施工者报的 38/41，说明这次取到的镜像文件
只落了 case 1（`_compute_arm_level_join` 的越区汇合证据否证），case 2（`_try_body_terminates_abnormally`
在 `self.regions` 未填充阶段读它）不在其中。两半各自移动自己靶的字节这一点与施工者的 A/B 表一致。

## 2. 落地前置条件（顺序不可颠倒）

1. 等 B133 交付最终补丁（含两半）并声明终态；
2. 等 B134/B136/B137 三张诊断票返回（它们正在读 `core/` 的行号与行为，装补丁会让锚点漂，
   本 session 已因此作废过工单）；
3. 用 `install_and_measure.sh` 装入（备份原字节 → 整份复制 → `py_compile` → 标记计数 →
   landed sha 与原字节相同即 exit 3 拒绝空转安装）；
4. 跑整链路 `gate_round.py 11 10 --stage regen/verify/report/checks` + `residual_report.py 11 10`，
   `regen` 若非 `ok=402 bad=0` 则**先 stat 产物尺寸再读 report**（本轮 9 单元假回退即出自 99 字节残次产物）；
5. 四项门禁必须为 0 才记翻正；任一哨兵回退即按 sha256 逐字节回滚并把证据留档。

## 3. B139 前置 oracle — 我亲自复现 `IQEngine/core/bar.pyc` **85/85 status=success**

时间 2026-10-08 05:21。做法：把封表产物**复制到 `D:/Temp/r139mine/barOK_oracle.py`**（仓内产物未动，
`git status --porcelain -- site-packages/` 复验为 0），只改一处语句：

```
改前（产物现形，嵌套）：
    if engine.config.strategy.frequency == '1m':
        if frequency == '1d' or ExecutionContext.phase() == ExecutionPhase.BEFORE_TRADING_START:
            dt = engine.data_proxy.get_previous_trading_date(engine.calendar_dt.date())

改后（原语形，单一 BoolOp 测试）：
    if engine.config.strategy.frequency == '1m' and frequency == '1d' or ExecutionContext.phase() == ExecutionPhase.BEFORE_TRADING_START:
        dt = engine.data_proxy.get_previous_trading_date(engine.calendar_dt.date())
```

判据：`pyc_verify single site-packages/IQEngine/core/bar.pyc --source D:/Temp/r139mine/barOK_oracle.py`
→ **`status=success units=85/85 success_rate=100.00%`，rc=0**。

结论与含义：
1. `_history_bars` 的差**不是落点选择错**，而是把 `(A and B) or C` 渲染成了 `if A: if B or C:`——
   两者**语义不等**（`A and (B or C)` ≠ `(A and B) or C`），所以 opcode 序列不变而跳转目标全变，
   这才在我先前的 TARGET_ONLY 分类里伪装成「纯落点」。分类键只说「同 opcode 仅目标不同」，
   并不说宿主是落点选择器——又验证一次「形状≠机制」。
2. 整文件只差这一条语句 ⇒ bar.pyc 是**第二个可翻正文件**，且目标形状已被 oracle 钉死为唯一一处。
3. 顺带把 §五 那条不采信记落成结论：B134 的 `units=85/85` 是对的，`status=failure` 是转写误差
   （判据 :129 使 failure 与 85/85 不可共存，我实测的正是 success）。

## 4. B139 判别臂实测（05:31，HEAD 字节，全部在 scratch 生成与判定）

| 臂 | 源码形状 | 读数 | 产物 `if` 形 |
|---|---|---|---|
| `b1_call_in_or` | `if cfg=='1m' and freq=='1d' or C.phase()==1:`，体为赋值，函数随后 `return` | **failure 3/4** | `if cfg == '1m':` + `if freq == '1d' or C.phase() == 1:` |
| `b2_no_call` | 同上，`or` 侧换成普通比较 `ph == 1`（隔离「调用」变量） | **failure 1/2** | 同样嵌套 |
| `b3_tail_stmt` | 同上，体后另有 `print(dt)` 再 `return` | **failure 1/2** | 同样嵌套 |
| `a1_and_or` | `if a and b or c:` 体为 **`return 1`** | success 2/2 | `if a and b or c:`（正确平铺） |
| `a2_or_and` | `if a or b and c:` 体为 `return 1` | success 2/2 | 正确 |
| `a3_not_or` | `if not i or not x:` 体为 `return 1` | success 2/2 | 发成 `not (i and x)`（De Morgan，字节仍可判等） |
| `a4_ctl_plain_and` | `if a and b:` | success 2/2 | 正确 |

⇒ **判别变量不是优先级本身**：同为 `(A and B) or C`，体为 `return`（终止）时平铺正确，
体为赋值（**非终止、落空续体**）时被拆成嵌套 `if A: if B or C:`。
所以「`a and b or c` 在我们这儿是坏的」这种笼统说法不成立，工单须按「and 短路 + or 操作数尾部
汇合回外层序列」这一结构事实立案；`b2` 已隔离掉「调用」这一无关变量（无调用同样红）。
另注 `a3`：`not i or not x` 被发成 `not (i and x)` 仍判等通过——
故 B134 记的 `strategy_universe` 目标形 `if not i or not X:` **未必**与本缺陷同源，
B139 若不能自然覆盖它，须另案而非放宽判据换读数。

## 5. 第二个 oracle 实测：`strategy_universe.pyc` **11/11 status=success**（05:39）

产物现形（`strategy_universeOK.py`，`_on_clear_de_listed` 内）：
```
            if i:
                if not i.delisted_date > self._engine.trading_dt:
                    de_listed.add(o)
```
把这两行 if 合成一条语句后（scratch 副本 `D:/Temp/r139mine/su_oracle.py`，仓内产物未动）：
```
            if not i or not i.delisted_date > self._engine.trading_dt:
                de_listed.add(o)
```
判据 `single strategy_universe.pyc --source <副本>` → **status=success units=11/11 rc=0**。

**这条比字节不等更重：产物的形与原语义不等价。**
`if i: if not X: add(o)` 只在 `i 真且 X 假` 时 add；
`if not i or not X: add(o)` 在 `i 假` 时也 add（等价于 `not (i and X)`）。
即当 `get_assets(o)` 返回假值时，现产物**漏掉** `de_listed.add(o)`。
故这不是「同义改写后字节不同」，而是**逆 De Morgan 方向走错**：
发射端把 `not i or not X` 折成了 `i and not X`（否定只作用到第二个操作数）。
与 §3/§4 的 bar 面同族（都该是**单一 BoolOp `or` 测试**，却被拆成嵌套 if），
但 bar 是 `A and B or C` 被拆成 `A and (B or C)`，su 是 `¬A ∨ ¬B` 被拆成 `A ∧ ¬B`——
两个方向都是「把 or 的短路结构拆成外层 if 的嵌套」，所以一条判据**可能**同时覆盖；
B139 须分别以两文件的逐单元读数证明覆盖了哪一面，未覆盖的一面另案，禁止放宽换数。

## 6. su 面也有最小判别臂（05:49）

`D:/Temp/r139mine/arms3/c1_demorgan_or.py`：`for a in items:` 内
`if not b or not b > x: s.add(a)`（赋值/收集型非终止体）→ **status=failure units=1/2**。
即 §5 的 `¬A ∨ ¬B → A ∧ ¬B` 折错方向**无需语料即可复现**，B139 的两面各有一枚最小复现臂
（bar 面 `b1/b2/b3`，su 面 `c1`）。

未采信的旁证：同批的第二条臂 `c2_and_neg_ctl`（`if b and not b > x:`）脚本在其后中止，
`pycdc.py` 是否产出未知，**故我不声明它是绿的**；B139 建电池时须自行重跑并记录每条臂的读数，
不得沿用本条未完成的输出。

## 7. B133 case 1 的**代码审读**（主代理自读 diff，14:18）

对比封表字节与我镜像内的改后字节（`diff -u`，+76 行新方法 + 约 40 行注释与一处分支插入）：

* 新增 `BasicBlock` 级判据方法 `_armjoin_is_dual_role_meeting(join, arm_of)`，标记
  `[r10-b133-armjoin-dualrole]`，带完整六项模板与 C1/C2/C3 段。
* 判据内容：`join` 的前驱中，凡块末是**无条件前向跳转且 argval == join.start_offset** 者记入
  `_jump_arms`；凡块末**既非任何跳转族也非 return/raise 终态**（即顺序边、其唯一正常后继为 join）者记入
  `_fall_arms`；认领要求两集皆非空**且不相交**（同一臂既跳入又直落 ⇒ 只是该臂内部汇合点，不认领）。
  全部只用块末 opcode 与前驱/后继身份，**零名字/偏移/计数/深度**，零新增 self 状态（G3/G4 合规）。
* 调用点在 `_compute_arm_level_join` 的逐层 BFS 分箱处：`len(_arms)==2` 且前驱分箱恰为 `{0,1}`
  （无 E/S/N 箱）且 `join ∉ 臂内子区域块集`（原则3）时启用 `(4c)`。
* 票面把 `(4c)` 写成既有 `(4)`/`(4b)` 例外族的**第三员**，并明确它与自己发射端
  `[R9-B124 elifchain-exit-in-armtail]` 的条件 (b) 是同一条结构判据的两半
  （归约端认领、发射端切开），**不是并行尺子**——这正是本项目反复要求的形式。
* 实测根因叙述自洽：`load_daily` 的 if@740 中真汇合 `@2478` 因「E 箱恒空」被旧 (4) 拒绝，
  BFS 越出作用域把外层链的 `@2768`（其 E 证据来自 `@104→@2768` 的跨越跳过边）认领为 merge，
  于是真汇合连同其后兄弟语句被吸进 else 臂。

**落地前置（不得提前的理由写死）**：
1. B139 的 7 枚臂与 B134/B137 的宿主测量都以**当前封表 analyzer 字节**为基线；
   `(4c)` 改的正是汇合块选择，装入后 bar/su/strategy_universe 诸臂的红绿可能整体移位 ⇒
   必须等它们交回基线与读数，再装 B133；
2. B133 与 B139 交付的都是**整份文件**，同文件覆盖风险见 `TICKETS_ROUND11.md` §六 的顺序纪律；
3. 装入即触发整链路 `gate_round.py`，四项门禁任一非 0 便按 sha256 回到本节记录的封表字节。

## 8. B133 **已装入仓库**（06:42），装前先在镜像里做了 16 文件回归筛

### 8.1 装前筛（全部在 `D:/Temp/r11b133/wt` 镜像内产出与判定，未动仓内产物）

以 round 9 封表读数为基线，对**全部 16 个残余文件**用改后 analyzer 重新产码 + 逐单元判等：

```
file                                                      baseline  patched  delta
IQCommon/api/klinedata.pyc                                    61/64     62/64    +1 (improved)
IQCommon/util/trade_info_utils.pyc                            37/41     38/41    +1 (improved)
fly/dumpload/load_daily.pyc                                   26/27     27/27    +1 (整文件翻正)
其余 13 个残余文件（handlers 29/30、wizard 55/58、api_base 27/28、real_quote 43/45、
bar 84/85、strategy_universe 10/11、order_api 35/37、strategy 26/27、realtime_event_source 12/13、
matcher 16/17、risk_calculation/__init__ 41/43、trade_live_broker 118/128、quote 86/92）  全部 0
16 文件合计单元 706 -> 709    regressions = []    （quotation 仍 153/153）
```

判据是**失败单元名集合**而非只比总数；两处 +1 的改进是工程师 A/B 表里没有的：
`klinedata` 61→62 与 `trade_info_utils` 在其表中被记为「case 1 单独不动」，
实测最终交付字节下 case 1 也各推进 1 单元 ⇒ 工程师的 A/B 表是**旧一字节的读数**，
不能当最终事实引用（我据此更正 §7 之前那句「case-1-only」判断的来路：
交付补丁确实含 case 2，见 hunk `@@ -11524,26 +11635,145 @@`，
而我先前用自拟标记名 grep 判成「无 case 2」是方法错误，已在同条更正）。

### 8.2 装入动作与序位

`cp core/cfg/region_analyzer.py → /d/Temp/r10gate/pre_b133_analyzer.py`（原字节留档）→
整份复制改后文件 → `py_compile` 通过 → 落地 sha256 前 16 位 `e926a54f17753b33`，
标记 `_armjoin_is_dual_role_meeting` 与 `[r10-b133-armjoin-dualrole]` 各命中 3 次。
整链路以 **label 11 / before 10** 启动（`gate_chain11.sh`：regen → verify → report → checks → residual），
`rounds/round10/after` 的封表读数即本轮对照基线。
**本轮翻正在门禁四项（文件级回退=0 ∧ UNIT_REGRESSIONS=0 ∧ 新增失败单元=0）读回之前不算成立**；
任一非 0 即执行 `cp /d/Temp/r10gate/pre_b133_analyzer.py core/cfg/region_analyzer.py` 回滚。

## 9. 三个只差 1 单元的文件收敛到**同一族**：or 链被折叠成嵌套 if（B137 @06:44）

`strategy.tick_worker_thread` 实测 `len 294/294 net=+0 hunks=4 全为 same-opcode target-only content=0`
（**否证我给它贴的 ANCHOR 标签**：四处差没有一处需要线锚 NOP，两对跳转各共享同一原始落点）。
真实形状：原字节是一条三操作数 `or` 链
`dt_strf > '15:15:00' or dt_strf < '08:30:00' or ('11:30:00' < dt_strf < '12:30:00')`，体为 `time.sleep(60)`；
产物发成 `elif not (A or B): if C: time.sleep(60)`（`strategyOK.py:231-237`，第二对在同函数 :241-246），
即把 `A or B or C` 折成 `¬(A∨B) ∧ C`——**语义不等**（原式任一操作数为真即执行体，折后须 A、B 皆假且 C 真）。
证据细节：操作数 C 的真边 `@562 JUMP_FORWARD ->@568` 两侧一致，只有 A、B 的 `POP_JUMP_FORWARD_IF_TRUE`
边被改投到链尾汇合 `@820 ->@1286` 与外层 `while` 回边块，故差异全落在目标上而 opcode 序列不变。

⇒ 与 §3（bar：`A and B or C` 被折成 `A ∧ (B ∨ C)`）、§5（su：`¬A ∨ ¬B` 被折成 `A ∧ ¬B`）同族：
**三处都是「or 的短路链被折叠/逆 De Morgan」**，涉及 3 个只差 1 单元的整文件
（bar 84/85、strategy_universe 10/11、strategy 26/27）。B139 的判据若按「or 链的每一操作数真边
须投到同一臂体」这一身份事实成立，则一票可覆盖三文件；若只覆盖 bar/su，strategy 另案，
不得为凑三绿放宽判据。宿主线索（B134 实测）：`region_analyzer.py:_detect_boolop_conditional_chain`
的 `:29013-29014`（`_sb_has_body` 闸）与 `:29736-29737`+`:29942-29943`（循环归属豁免 + `len(chain)<2`）。

**锚点漂移声明**：B133 已装入 `region_analyzer.py`（+76 行 @3051 之后、+119 行 @11524 之后），
故 B134/B137/B139 若在装入后仍引用 `>11524` 的行号，须整体 **+195**、`3051..11524` 区间 **+76**
再核对；本档记录的行号一律以**它们自己实测时的字节**为准，采用前由主代理逐条 grep 复验。

## 10. 主代理自做的判据实验（07:57，镜像 `D:/Temp/r139m/wt`，仓库 core 未动）

**探针读数**（在 `_detect_boolop_conditional_chain` 内按 `self.cfg.code.co_name == '_history_bars'` 打印）：

```
head=0   _sb_has_body=False cond_start=0   last_off=12
head=18  _sb_has_body=False cond_start=0   last_off=28
head=34  _sb_has_body=True  cond_start=0   last_off=126     ← bar 的链头块被误拒
head=128 _sb_has_body=False cond_start=132 last_off=138
```

根因坐实：算 `_cond_start_offset` 的栈深回溯**只在** `if _r54_mixed or (前一条为 LOAD_*)` 分支里跑；
未跑时它保持初值 0（`:29008`，且 `:29007` 注释「扫描整个块…因为它们的条件可能更复杂」是**有意**的豁免），
于是 `_sb_has_body`（`:29208-29218`）从块首扫起，把块内**前一条已完成语句**的 `STORE_FAST`
（`engine = Engine.instance()`、`dt = engine.calendar_dt`）当成 if 体语句 ⇒ `:29246 return None`，
混合链不启动，`or` 尾被折进嵌套 if。

**实验**：把同一段栈深回溯改为在 `_cond_start_offset <= 0` 时也无条件执行（12 行）。读数：

| 项 | 基线 | 实验后 |
|---|---|---|
| `IQEngine/core/bar.pyc` | 84/85 | **85/85 status=success**（整文件翻正；产物里那条测试已是 `… == '1m' and frequency == '1d' or ExecutionContext.phase() == …`） |
| `fly/data/quotation.pyc` | 153/153 | **152/153**（破一个原本通过的单元） |
| r139_ 电池 16 臂 | 30/35（5 红） | **30/35，逐臂无变化**（r139_01/02/03/08/09 同红，其余 11 同绿） |
| head=34 | `_sb_has_body=True, cond_start=0` | `_sb_has_body=False, cond_start=120` |

**结论（不落地）**：方向对、判据过宽——`:29007` 的有意豁免正是 quotation 那一格的护身符，
 blanket 回溯把它抹掉了；且电池臂一动不动，说明「块内含前置已完成语句」并非该族全部形状的必要条件，
 真正缺的是「用哪一条身份事实把 bar 的 @34 与被豁免块分开」。已按此派 B139b：
 要求找出可测的判别事实（候选：条件段之前是否存在**栈深归零的语句边界**、块是否有多条语句、
 是否区域入口/循环体头、前置语句目标是否落在同一区域内），并把判据贴着既有豁免
 （`_import_store_offsets`、`_b67_iter_target_offsets`）同风格落地，禁止放宽任何 `[C3]` 守卫换读数。

## 11. B133 的常驻电池入库（08:09）与一条索引格式事实

把工程师留在 `D:/Temp/r133/arms/` 的 9 枚臂提升进仓：`test_repros/round11/{r1..r4,s5..s9}_b130_*.py{,.c}`，
产物一律先删后用 `pycdc.py -o` 重生成（9/9 生成成功），索引 `test_repros/round11/r133_probe_index.json`。
当前字节读数：**9 文件 18/18 单元全绿**。

**牙口只在一处**：`s9_b130_c2_return_in_loop_then_break` 在 B133 之前是 **1/2 红**、装后 2/2（工程师 A/B 表
与我镜像复验一致），故它能侦测 `(4c)`/case 2 被回退；`r1..r4`（我原票要求的四条最小复现）在 HEAD 就是 2/2，
**没有判别力**（B130 §Q4 早已如实写明），它们只能证明「未把健康例子改坏」，不能证明判据仍在。
以后登记电池须照此逐臂标注「装前是红还是绿」，否则 9/9 绿会被误读成 9 枚牙。

索引格式事实（我自己踩的）：`scripts/pyc_verify.py` 的 `--index` 要求条目是**对象**（`e['path']`，可选 `source`），
写成字符串列表会在 `collect_targets` 抛 `TypeError: string indices must be integers`；
仓内既有索引（如 `r139_probe_index.json`）即 `[{"path": "..."}]` 形状。新建索引一律照该形状并先跑一次 batch 复验。

## 12. handlers 的宿主实测（主代理 08:23，镜像 `D:/Temp/r11b133/wt`）

`build_cfg(_target, co_firstlineno=61)` + 真实 `RegionASTGenerator(cfg).region_analyzer.analyze()`：

```
loops: 2
 Loop entry=90  WHILE header=104 cond=90  body=12 else=[408] back=390
   404 in body=False  in else=False  in blocks=True
   408 in body=False  in else=True   in blocks=True
blk@404 owner=LoopRegion role=None preds=[390] succ=[]  tail=RETURN_VALUE
blk@408 owner=LoopRegion role=None preds=[90]  succ=[]  tail=RETURN_VALUE
```

即 **`@404` 是 LoopRegion 的普通成员**（在 `blocks` 内、既不在 `body_blocks` 也不在 `else_blocks`）、
零后继、唯一前驱是回边块 `390` ——它就是「循环出口后的落点」。消费端 `_loop_generate_while`
只取 `body_blocks` 与 `else_blocks`，因此**没有任何人请求发射 `@404`**，那一对
`LOAD_CONST None/RETURN_VALUE` 就此消失（与 B127 工程师的结论一致，与他否证的 G7/sink 面无关）。

**建议判据（身份事实，供 B136b 实测）**：某块 owner 为 LoopRegion ∧ `∈ blocks` ∧
`∉ body_blocks ∪ else_blocks` ∧ 零后继 ∧ 其前驱含本循环的回边/尾块 ⇒ 它是循环出口的落点，
必须由循环区域之后作为续体发射（原则 2：成员关系即发射责任；不得再用「登记 generated」代替发射）。
须测的反例边界：真 `while…else` 的 else 入口（如 `@408`：前驱是 condition_block 90 而非回边块）
必须**不**被本判据捕获；`r10g7_`/`r133_` 电池与 quotation/anchor/small34 哨兵按主代理既有清单执行。
