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
