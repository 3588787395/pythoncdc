# Round 10 工单 #14（续）简报：纯落点面 9 单元——四条「单站点目标差」是本轮最短门禁路径

取证口径：输入 `.pyc` 读盘（从不被重写），产物读**盘上现字节**（Round 9 落地代码重生成，`bad=0`）；
只读 stdlib（`dis`/`marshal`/`compile`/`difflib`），**未导入 core、未跑发射器**，
因在飞工单 #16 正在写 `core/cfg/region_analyzer.py`。
仪器：`D:/Temp/r9main/r10land.py` → 原表 `D:/Temp/r9main/r10land.txt`（逐站点带上下文）。
配对按**完整 qualname 路径**（`/` + unit 点换斜杠），副本数≠1 者显式拒判（见 §五）。

序列归一化：剔 `NOP/CACHE/EXTENDED_ARG`；跳转目标归一化为「目标 offset 在保留序列中的下标」，
**`-1` 的含义是跳转落点恰被剥掉的行锚 `NOP` 占据**（不是错误，是一条独立事实，见 §三）。

## 一、靶面分档（实测 hunk 数＝同 opcode、仅目标不同的孤立站点数）

| 档 | 单元（完整 qualname） | 序列长 | 总 hunk | 孤立目标差 | 该档含义 |
|---|---|---|---|---|---|
| **A 单站点**（先打） | `trade_info_utils.<module>.get_trade_status` | 171/171 | 1 | **1** | 一个 `JUMP_FORWARD` 落点选晚 |
| | `bar.<module>.BarData._history_bars` | 66/66 | 1 | **1** | 一个 `IF_FALSE` 落点选晚 |
| | `strategy_universe.<module>.StrategyUniverse._on_clear_de_listed` | 70/70 | 1 | **1** | 一个 `IF_FALSE` 落点选晚 |
| | `trade_live_broker.<module>.TradeLiveBroker.get_ipo_stocks` | 481/481 | 1 | **1** | 一个 `IF_TRUE` 落点选早 |
| **B 互换对** | `trade_info_utils.<module>.kill_trade_process` | 659/659 | 2 | **2** | 两条跳转的目标**互相换位** |
| **C 锚点档** | `strategy.<module>.Strategy.tick_worker_thread` | 288/288 | 4 | 4 | 其中 2 条 prod 目标 `=-1`＝落到行锚 NOP |
| **D 重复体**（后打） | `trade_live_broker.<module>.TradeLiveBroker.etf_basket_order` | 756/756 | 34 | 31 | 落点上下文**逐条相同**，我的仪器分不出该落哪一个副本 |
| | `load_daily.<module>` | — | 20 | — | 同上性质，待人工定标 |
| | `trade_live_broker.<module>.TradeLiveBroker.rzrq_credit_order` | — | 1 | 1 | 与 A 档同形 |

⇒ **A 档四条分属四个文件，但只有两条能单独翻正文件**（按盘上「只差 1 单元」读数）：

| A 档单元 | 所在文件 | 文件读数 | 单独修好该单元的效果 |
|---|---|---|---|
| `bar._history_bars` | `IQEngine/core/bar.pyc` | 84/85 | **整文件翻正** |
| `strategy_universe._on_clear_de_listed` | `IQEngine/core/strategy/strategy_universe.pyc` | 10/11 | **整文件翻正** |
| `trade_info_utils.get_trade_status` | `IQCommon/util/trade_info_utils.pyc` | 37/41 | +1 单元（该文件另有 3 条：`kill_trade_process`(B 档)、`query_strategy_id`、`query_trade_strategy_info`；四条齐修才翻正） |
| `trade_live_broker.get_ipo_stocks` | `…plugin_system_trade/trade_live_broker.pyc` | 118/128 | +1 单元（该文件差 10 条，本票不指望翻正） |

⇒ **A 档即可交付 2 个 pyc 由 failure 转 success**（`bar`、`strategy_universe`），已满足轮门禁「≥1」；
B 档 `kill_trade_process` 与 `query_*` 两条同文件单元若一并闭合，`trade_info_utils` 37/41 → 40/41（仍差 1，
其 `LANDED_TARGET` 面另计）。C/D 档另表处理，禁止与 A 档混记为一个判据的成绩。

## 二、A 档逐条事实（不得用偏移入码，这些数字只是取证复演凭据）

1. `get_trade_status`：`JUMP_FORWARD` 应落 seq#151（`COMPARE_OP POP_JUMP_BACKWARD_IF_TRUE …`，
   即 try 之后继续判断的那一段），产物落 seq#147（`POP_EXCEPT RERAISE …` ＝ handler 尾声）。
   **落点被认领给了异常尾声**。
2. `bar._history_bars`：`POP_JUMP_FORWARD_IF_FALSE` 应落 seq#32（`COMPARE_OP POP_JUMP_FORWARD_IF_TRUE …`
   ＝该 if 的假臂汇合处），产物落 seq#51（`CALL STORE_FAST …` ＝两条之后）。
   **假臂汇合块被跳过**。
3. `strategy_universe._on_clear_de_listed`：`POP_JUMP_FORWARD_IF_FALSE` 应落 seq#27（`COMPARE_OP
   POP_JUMP_FORWARD_IF_TRUE …`），产物落 seq#33（`CALL POP_TOP JUMP_BACKWARD …` ＝回边之前）。
   **同形：假臂汇合块被跳过，落到了体尾**。
4. `get_ipo_stocks`：`POP_JUMP_FORWARD_IF_TRUE` 应落 seq#225（`POP_JUMP_FORWARD_IF_FALSE …`），
   产物落 seq#215 —— **落点选早了 10 个保留位**（与前两条方向相反，判据不得单向）。

共同形状：这些都是**循环/try 结构内**的一条前向条件跳转的汇合块选择；
方向有早有晚 ⇒ 判据必须问「两条入边共享的块是哪一个」，
不能写成「取最早」或「取最晚」这类单向规则（那是以方向巧合换读数）。

## 三、C 档的独立事实：`tick_worker_thread` 有 2 条跳转落到行锚 NOP

`#180`、`#184` 两条 `POP_JUMP_FORWARD_IF_TRUE` 在原始字节码里落 seq#197，
在产物里目标偏移**恰是被剥离的 `NOP`**（本仪器打 `-1`）。
CPython 3.11 用 `NOP` 做行锚，跳进锚点与跳进锚点后的第一条实指令是**不同的字节码偏移**，
判据据此判 `Different control flow` 是合理的。⇒ 该档的修法要看发射时**循环头锚点的归属**
（哪一块拥有该 `NOP` 锚），不在本票 A 档判据内，须另列站点复验；
`trade_live_broker._process_tick_order` 那条「序列全同而判据仍判失败」的单元极可能同属此档
（见 `REVIEW_ROUTE_R10.md` §三.2 的逐层夹钳）。

## 四、判据要求（白名单事实；禁偏移/禁计数/禁名特判）

汇合块必须由**边的事实**选出，而非由偏移序：
- 候选块 `J` 必须是**两条入边的共享落点**：一条来自臂的无条件前向跳转（`JUMP_FORWARD`）或 fall-through，
  另一条来自该条件测试的假（或真）分支跳转；
- `J` 的**前驱集合**须同时含「臂侧」与「测试侧」，且 `J` 不是 handler 尾声
  （块首指令为 `POP_EXCEPT`/`RERAISE`/`PUSH_EXC_INFO` 者属 TryExceptRegion，依每块唯一归属不认作汇合块）——
  这条正是 A 档 #1 的失败形；
- `J` 若带向后边（回边）指向本循环，则它是**体尾**而非出口（Round 9 §XVI 已证真 else 体不带回边）——
  这条正是 A 档 #2/#3 的失败形；
- 方向不可预设：`get_ipo_stocks` 是选早，`_history_bars`/`_on_clear_de_listed` 是选晚，
  `get_trade_status` 是把控制权让给了异常尾声。

## 六、两台仪器的 hunk 数不一致——A 档扩容前必须先解这处歧义（不得按乐观值记账）

同两个文件、同一段字节码，两台仪器对「差多少处」给出不同数：

| 单元 | 严格下标仪器（`r10land.py`，跳转目标＝保留序列下标，**非跳转指令不比 argrepr**） | 带身份仪器（`route10.py`/`pol.norm`，跳转目标＝下一条保留指令的 `opname@offset`，非跳转指令**比 argrepr**） |
|---|---|---|
| `load_daily.<module>` | **1** 处（`#654 JUMP_FORWARD` 应落 seq#661＝`CALL POP_TOP PUSH_NULL…`，产物落 seq#679＝`CALL POP_TOP JUMP_FORWARD PUSH_EXC_INFO…`），len 1010/1010 | **20** hunk（`REORDER`，`net=0`） |
| `trade_live_broker.rzrq_credit_order` | **1** 处（`#453 JUMP_FORWARD` 应落 seq#490，产物落 seq#485），len 780/780 | 1 hunk（同档） |
| `etf_basket_order` | 31 处（但落点上下文逐条相同） | 39 hunk |

⇒ `load_daily` 的 19 处额外差**只出现在比 `argrepr` 的那台仪器上** ⇒ 它们不是指令搬运，
而是**名字/常量身份层面的差**（例如同名 `LOAD_NAME` 指到不同名、或 `LOAD_CONST` 身份不同）。
这种差**一条落点判据修不掉**。因此：
- 不许把 `load_daily` 计入 A 档「单站点即翻正」的名单，除非先用带身份仪器逐条比出那 19 处到底是什么；
- 反过来说，若那 19 处确为同一根因的下游表现（例如一个块被错误认领导致其中的名字归属改变），
  则 A 档判据**同时**是 `load_daily` 的解——两种解释都要写进回报，不得只报有利的一种。

## 七、派发前置与禁止项

1. **等 #16 落地/封表后再派**：#16 改区域成员关系（`while True` 归还体内 `if`），
   本简报的 seq 下标全部要在**新字节**下用 `r10land.py` 重取一遍；旧下标只作形状凭据。
2. **先臂后码**：A 档四条各做合成臂（前缀 `r10ld_`），≥3 深度变体，≥2 MATCH 负对照
   （至少含：一个汇合块本就在 handler 之后的合法形；一个真 `while…else`）。
   红→绿才算命中；红→红＝该轴被否证（B122/B123 的先例）。
3. 禁 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀；禁硬编码深度/计数/偏移/名；
   禁「少发射换全绿」；禁按文件名/函数名特判。
4. D 档（`etf_basket_order` 31 个、`load_daily` 20 个）**不得当成 31/20 个缺陷记账**：
   其落点上下文逐条相同，是我的仪器分不出副本，不是有 31 处独立错位。
   要动须先按出现次序人工定标，再以区域成员关系定归属。
5. 零翻转即按 sha256 逐字节回滚；**回报必须边做边写**（`rounds/round10/FIX_LANDING_R10.md`），
   Round 9 的工程师在 150 回合上限处截断且回报文件 0 字节，本票禁止重复该缺陷。
