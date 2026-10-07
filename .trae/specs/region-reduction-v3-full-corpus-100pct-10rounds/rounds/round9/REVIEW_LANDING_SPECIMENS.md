# Round 9：落点轴两个紧标本的逐指令与行号取证（只读，未下语义结论）

仪器：stdlib only（marshal + dis + compile + co_lines），**不导入 core**，
因 `r9-fix-ifregion-boundary` 可能随时写 `region_analyzer.py`。
两例均属 `REVIEW_RESIDUAL_CENSUS.md` §IX 的「整条 opcode 序列相同、只有跳转目标不同」11 例。

## 标本 1 `IQEngine/core/bar._history_bars`（66/66 指令，第一差块＝#27 的目标）

```
        #24 LOAD_ATTR frequency      #25 LOAD_CONST '1m'   #26 COMPARE_OP ==
ORIG  #27 POP_JUMP_FORWARD_IF_FALSE  to 140   src_line=394
PROD  #27 POP_JUMP_FORWARD_IF_FALSE  to 304   src_line=287
        #28 LOAD_FAST frequency  #29 LOAD_CONST '1d'  #30 COMPARE_OP ==
        #31 POP_JUMP_FORWARD_IF_TRUE  to 206（两侧相同）
```

关键旁证：ORIG 的 #24..#31 **全在源文件同一行 394**；PROD 把 #24..#27 放在 287 行、
#28..#31 放在 **288 行**——即产物把一个原本写在单行的 `… == '1m' or … == '1d'` 拆成了两行，
且第一条短路边落点从 140 变成 304。**其余指令与第二个测试的目标完全一致。**

## 标本 2 `IQEngine/core/strategy/strategy_universe._on_clear_de_listed`（70/70，差块 #19）

```
ORIG  #18 LOAD_FAST i (104)  #19 POP_JUMP_IF_FALSE to 156  #20..#25 i.delisted_date > trading_dt (104)
      #26 POP_JUMP_IF_TRUE to 198   #27..#32 de_listed.add(o) 在 off 156（即 #19 的假边落点＝体首）
      #33 JUMP_BACKWARD to 44       #34 LOAD_FAST de_listed (106)
PROD  #18 LOAD_FAST i (77)   #19 POP_JUMP_IF_FALSE to 198  #20..#25 同上 (78)
      #26 POP_JUMP_IF_TRUE to 198   #27..#32 同体（off 156）
      #33 JUMP_BACKWARD to 44       #34 同上
```

即：**两例都只差"第一个操作数的短路边落在哪个块"**，回边锚点、第二测试目标、体与后续块都逐位相同；
行号上 ORIG 是单行（104）、PROD 把它摊成 77/78/79 多行。

## 尚未下的结论（留给 #14 工单，禁止照抄本节的形状猜测）

- 两例的 `#19/#27` 假边方向与原码布尔结构（`and` / `or` / `not` 的组合与短路次序）之间的关系，
  我没有用源码或区域模型证实；本节只保证**指令与行号事实**。
- 标本 1 的 140→304 与标本 2 的 156→198 是否同一个判据（`BoolOpRegion` 成员边 vs `IfRegion` 汇合块）
  **未知**。`region_ast_generator.py` 里已有 `[R3-B109 elif 臂 or 链成员真边同一性核验]` 三处，
  工单应先 grep 这些既有标记，确认本案是否本就归它们管（禁止另立第二真相源）。
- 行号摊开（单行→多行）可能与发射端的语句拆分有关，但行号不是判据的比较对象，
  不得据此立票。


## 三、`IQCommon/data/finance.get_fields`（31/32，整文件只差这一个单元）

两侧剔噪后**都是 175 条真实指令、都只有 2 条 `JUMP_FORWARD`**，第二条完全一致（seq#109 → seq#121）；
唯一差的就是第一条 `JUMP_FORWARD`（seq#21）的落点：

    ORIG  #21 off=92  line=654  → off 236 ＝ seq#50：
            LOAD_FAST error_msg | LOAD_CONST 'error_no' | BINARY_SUBSCR | LOAD_CONST 0 | COMPARE_OP ==
            POP_JUMP_FORWARD_IF_FALSE → 672                ← 原码 665 行的 `if error_msg['error_no'] == 0:`
    PROD  #21 off=94  line=None → off 742 ＝ seq#143：
            LOAD_FAST fields | RETURN_VALUE                 ← 函数的 `return fields`，紧接在另一条 RETURN_VALUE(seq#142) 之后

⇒ 这条边在原码里是「提前汇合」：从 654 行（存 `error_msg` / `financial_data_type` 之后）
**跳过 658–662 段**，落到 665 行那个两条路径共用的 `error_no == 0` 测试上；
产物却把它送到 `return fields`，等于让那条路径**绕开整个共用测试区**。
另外两点可作旁证：产物该 jump 的行号是 `None`（合成边，不对应任何源语句），
且它的目标块前面紧挨着另一条 `RETURN_VALUE`。

判据方向（块/边事实，不许按行号或偏移）：一条前向无条件边的落点必须是**两条入边共享的汇合块**
（本例为被 `POP_JUMP_IF_FALSE` 与顺序流共同指向的那个块），
不得取该汇合块之后、位于别的出口路径上的块。
⇒ 本单元属 §X「只差 1 个单元即可整文件 OK」名单，修好即交付 `finance` 32/32；
   这也是轮门禁本轮最该拿下的一个点。


## 四、三个「只差 1 单元」文件同形复现（对轮门禁最有价值的取证）

按**序列下标**对齐（剔 NOP/CACHE/EXTENDED_ARG，跳转目标重映射到真实指令下标）后逐文件实测：

| 文件.单元 | 指令数 orig/prod | opcode 序列 | 真实落点差 |
|---|---|---|---|
| `finance.get_fields` | 175/175 | **完全相同** | seq#21 `JUMP_FORWARD`：orig→seq#50（665 行共用测试 `error_msg['error_no'] == 0`）；prod→seq#143（`return fields`） |
| `function.reconnect` | 101/101 | **完全相同** | seq#47 `JUMP_FORWARD`：orig→off 520（1679 行 `if reconnect_flag is not False:`）；prod→off 600（跳过该块） |
| `load_daily.<module>` | 1010/1010 | **完全相同** | seq#~1082 `JUMP_FORWARD`：to@661 vs to@679（§VI 下标口径） |

⇒ **同一形状在三个不同文件上独立出现**：一条**前向无条件边**在原码里落到「两条入边共享的早先汇合块」，
产物把它送过那个汇合块、落到更后的位置。三个文件都是**只差 1 个单元**，
故这一条判据若修对，最好情形可直接把 `finance` / `function` / `load_daily` 三个文件推成完全 OK
（384→387），是本轮门禁最集中的一次机会。

**必须写明的仪器教训**：按原始偏移比较时，这三文件还各有 8–12 处 `to 740` vs `to 742` 的
**+2 抖动**，那是 2 字节编码差异造成的噪声（指令条数与 opcode 序列两边完全相同），
不是缺陷；只有把目标重映射到序列下标后剩下的那一处才是真差。
任何用原始偏移做的「差块数」统计都会把噪声算成故障数。


## 五、`IQEngine/plugins/plugin_fly_data/strategy.strategy.tick_worker_thread`（26/27，只差 1 单元）

两侧剔噪后**都是 288 条真实指令、opcode 序列完全相同**，只有 4 条边的目标不同，
且**四条全是 `POP_JUMP_FORWARD_IF_TRUE`，偏差恒定 +66**：

    seq#70  orig to#87  → prod to#153     （#74 与它同目标，同样 87→153）
    seq#180 orig to#197 → prod to#263     （#184 同上）
    orig 落点块：`LOAD_GLOBAL` 且带源行号（325 / 339）
    prod 落点块：`JUMP_FORWARD` / `JUMP_BACKWARD` 且 **line=None**（合成控制块）

⇒ 不是随机错位：**恒定 +66 说明有一段 66 条指令的块簇被放到了这些边的汇合点之前**，
于是四条真边一起被推过汇合点，落到更后的控制块上。
两两同目标（70/74、180/184）＝两处 `if A or B:` 的成员边共用的汇合块——
与 §三 `finance`、§一 `bar._history_bars`、`strategy_universe` 同属
**「boolop 成员边 / 条件边的汇合块被取晚」**一族。

累计：这条判据同时压着 **5 个只差 1 单元的文件**（`finance`、`function`、`load_daily`、
`strategy`、`strategy_universe`），全部修对的最好情形是 384→389；
这仍是**候选上界而非承诺**——最终以主代理 402 逐文件差值实测为准。
