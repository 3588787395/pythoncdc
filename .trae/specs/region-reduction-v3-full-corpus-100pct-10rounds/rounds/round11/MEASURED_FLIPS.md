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
