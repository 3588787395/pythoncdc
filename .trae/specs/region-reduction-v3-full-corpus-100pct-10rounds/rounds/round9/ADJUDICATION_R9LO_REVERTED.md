# Round 9：`r9-fix-landing-ordering`（B123）回报的独立裁定

## 一、处置合规（主代理复核通过）

零翻转 → 按 sha256 逐字节回滚：`core/cfg/region_analyzer.py` = `38a1d5142d132fd7…` ＝ 入库 HEAD 与 Round 8 封表值；
`git status -- core` 空；标记 `[R9-B123` grep **0 命中**。
电池交付完备：`r9lo_*` 6 臂全部登记进 `r9lo_probe_index.json`，无缺产物、无缺源文件（主代理逐项闭合审计）。
HEAD 态读数 9/12 单元（3 复现臂红、3 对照臂绿），与其自述一致。

## 二、最有价值的实质发现（推翻主代理此前的排产依据）

1. **认领 `merge_block` 不是落点机制**。探针显示判据确实命中（finance 的 `IfRegion@10` merge 由 `None/672 → 236`），
   但臂的 `JUMP_FORWARD` 仍落 `to@50 → to@143`；因为 `IF_ELIF_CHAIN.blocks` 仍是 25 块（吸到 236..670）——
   **决定发射边界的是 `_check_elif_chain` 自己的 per-arm/`final_else` 收集，不是 `merge_block`**。
   ⇒ 我先前把「落点族」押在分析端边界判据上是错的（§XII 的 12 单元射程仍成立，但**修法在生成端**）。
2. **`function.reconnect` 在 HEAD 的识别已经是对的**（`IfRegion@192 merge=520`，兄弟 `IfRegion@520`）；
   坏落点是生成端为**循环头条件 `if`（它根本没有 IfRegion）**构造 elif 链时产生的。
3. **`bar` 与 `strategy_universe` 是分组问题不是边界问题**：or 链走查假定
   「首段跳转目标＝then 入口、中段必须 IF_TRUE 跳到它」；bar 需要 `(A and B) or C` 的**嵌套操作数树**
   （现结构 `{'blocks':[...], 'op':'or'}` 表达不出来），strategy_universe 需要极性敏感的尾接纳 + 逐块操作数极性。
   ⇒ 两层改动，不是单一条边界判据。
4. **松版判据造成真实回退**：finance 31/32 → **30/32**（多出 `func_get_fundamentals_daily_data`）。
   紧版无回退亦无翻转。这条正是「以少发射/放宽换全绿」的现场反例，留档。

## 三、工单回报里两处「纠正主代理」经复验**不成立**（同名文件错配）

| 工单断言 | 主代理复验（封表报告 + HEAD 产物） |
|---|---|
| 「`handlers.pyc` 读 17/17 OK，`_target` 不是只差 1 单元」 | 语料里有**两个** handlers：`IQCommon/logger/handlers.pyc` = **29/30 失败**，失败单元正是 `<module>.TWHThreadController._target`；`IQEngine/utils/logger/handlers.pyc` 才是 **17/17 通过**。其 71/71 零差对应的是后者。 |
| 「`while…else` 折叠在语料只出现于 `_process_order`」 | HEAD 副本 `trade_live_brokerOK.py` 实有 **3 处**：line425 `len(self.open_orders)>0`、line524 `len(self.pending_cancel_orders)>0`、line897 `self.trade_status != trade_status`，`else` 体分别是 `sleep(0.001)/sleep(0.001)/sleep(0.5)`；三处的字节码回边证据已由主代理逐条复验。 |

⇒ 教训（两处同源）：**按 code object 名字尾段匹配会跨文件/跨函数错配**；主代理自己的 `routing2.py` 也有同一缺陷
（`calculate_di.<genexpr>` 两条即此情形）。凡逐单元断言必须先钉死**完整路径 + qualname**，
否则「纠正」与「被纠正」可能各说一个文件。

## 四、下一票的方向（据本节实质发现改写）

靶面不再是分析端 merge 选择，而是**生成端的 elif 链构造与 boolop 操作数结构**：
`_check_elif_chain` / `_if_generate_full_elif_chain`（`:15052`）的臂收集与链成形，
外加把 or/and 混合链表达成**嵌套操作数树**。验收仍按 §XII 的 `REORDER_ONLY` 12 单元逐单元名单，
且必须复跑其自有 `r9lo_*` 3 条红臂；`r9a1_03/08` 已由工单判为 void（HEAD 即绿，不复现 A1），
不得再当牙使用。
