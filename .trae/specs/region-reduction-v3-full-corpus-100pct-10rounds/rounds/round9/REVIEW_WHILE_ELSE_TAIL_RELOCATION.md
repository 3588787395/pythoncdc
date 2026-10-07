# Round 9：语料实证——循环体尾语句被绑成 `while … else:`（三个失败单元）

主代理只读取证（`ast` 解析 HEAD 产物 + 交叉比对封表失败单元名单），不导入 core、不跑发射器，
故不与在飞工单 `r9-fix-landing-ordering` 争任何写面。

## 一、检出

谓词：产物里 `ast.While` 且 `orelse` 非空。真源写 `while … else:` 在 Python 里合法但极罕见
（只有循环**正常耗尽**且未被 `break` 离开才执行），所以它出现在反编译产物里是强信号。

18 个残差产物中命中 **5 处**，其中 **4 处所在单元正在失败**：

| 产物 | While 行 | 宿主单元 | 循环测试 | `else` 分支实际内容 | 该单元是否失败 |
|---|---|---|---|---|---|
| `trade_live_broker` | 425 | `_process_order` | `len(self.open_orders) > 0` | **`time.sleep(0.001)`**（行 494） | 失败 |
| `trade_live_broker` | 523 | `_process_cancel_order` | `len(self.pending_cancel_orders) > 0` | **`time.sleep(0.001)`**（行 570） | 失败 |
| `trade_live_broker` | 896 | `_trade_status_handle` | `self.trade_status != trade_status` | **`time.sleep(0.5)`**（行 913） | 失败 |
| `plugin_system_risk_calculation/__init__` | 540 | `_save_testds_to_csv` | `True`（外层） | 尾语句 | 失败 |
| `api_base` | 33 | `decorate_api_exc` | — | — | **通过**（对照组） |

`api_base` 那一处所在单元读 Equal，说明该形**本身不必然**是缺陷；但 4/5 落在失败单元上，
与残差整体占比（42/6617 单元）不成比例，须按缺陷处理。

## 二、形状与既有轴的因果关系（关键推断，交由工单证实/否证）

三处的 `else` 体**恰好是循环体的尾语句**（一次 `time.sleep`）。原码形状显然是：

```
while len(self.open_orders) > 0:
    …body…
    time.sleep(0.001)          ← 每一轮都要执行的体尾
```

产物把它降成「循环正常结束时才执行的 else」⇒ 语义与字节码同时变：
体尾块的前驱边从「回边之前顺序续体」被改判成「循环出口的续体」。
这正是本轮 §XI 计数的**落点/边界族**的一个具体可检出面：
不是抽象的「第 N 条边的目标差 4–5 个块」，而是**循环出口边把体尾块认领成了 else 分支**。

⇒ 对 `r9-fix-landing-ordering` 的直接含义：该票在 A1 体回来之后剩下的 28–32 处差里，
至少这一形是可见、可判、可用块事实表达的候选闭合点；
`_process_order` / `_process_cancel_order` / `_trade_status_handle` 三单元同时受它影响，
其中 `_trade_status_handle` 只差 1 个单元（属 §X 的十个一步可翻正文件之一）。

## 二B、字节码铁证（`_trade_status_handle`，主代理 stdlib 取证）

原码 `dis` 中 `time.sleep(0.5)` 那段（off 830–868，行 1470）之后紧接的是：

    off=870  EXTENDED_ARG
    off=872  JUMP_BACKWARD  to 46        ← 回到循环测试块

⇒ 该 sleep 是**循环体的最后一块**，其后是回边；若源码真写成 `while … else: sleep(0.5)`，
则 else 块应由循环**出口边**进入并向后跳过循环（fall through 到循环之后），
绝不会带一条 `JUMP_BACKWARD` 回测试块。产物把它降格成 `while … else:` **在字节码层面即可判为错**。

同法尚未对另外三处（`_process_order`、`_process_cancel_order`、`_save_testds_to_csv`）逐条复验，
工单须自行以同一判据（sleep 块后继是否为回边）确认/否证，不得把我这一次证明当作四处的担保。

**全量占比补测**（407 产物穷举 `ast`）：`while…else` 全文仅 **7 处**，4 处在失败单元上、3 处在通过单元上。
⇒ 本形解释 **42 个残差单元中的 4 个**，不是 35 个落点单元的通用解释；
不得因它形状漂亮就把它当成主因（§X 的落点族射程不因此改变）。

## 三、禁止项

- 不得用「看到 `While.orelse` 就一律不发射 else」这种输出端禁令（那是以少发射换全绿）。
  判据必须问边的事实：体尾块的**前驱**是循环体的顺序续体还是循环出口边。
- 必须先在**当前 HEAD 字节**下把此形做成合成臂（前缀 `r9lo_`，进 `r9lo_probe_index.json`）
  并读红，再动生产码；`api_base` 那一处（读 Equal 的同形）必须留作负对照，防过度收紧。
- 本文件是主代理取证，不是结论；因果由工单以逐单元名单证明或否证。
