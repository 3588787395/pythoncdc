# Round 9：`fly/data/quote.pyc` 六单元定性（工单 `r9-quote-char` 回报 + 主代理独立复核）

判据封表时点：2026-10-07。对象 `site-packages/fly/data/quote.pyc` = 86/92。
主代理复核（不采信自述）：① `git status --short -- core site-packages` 为空 ⇒ 该工单确实零生产改动；
② 他们引用的每个符号与行号都经 grep 验证存在（`_build_effective_stmts`:3493、
`MIN_INSTRS_FOR_SUBSCR_ASSIGN`:27、`_split_subscr_operands`:2812、`_generate_boolop`:39377、
`_generate_try`:29521、`_generate_loop`:5017、`_if_generate_full_elif_chain`:15052、
`_identify_try_except_regions`（`region_analyzer.py`:8484）、`_r8_b121_implicit_tail_landing_sinks`:51549）；
③ 电池读数由主代理复算（见 §III）；④ G7 对 `quote` 的影响由主代理用两套报告**逐单元名单**独立复算（§IV）。

## I. 六单元定性与归属（工单结论，主代理按名单核实其存在性）

| 单元 | 首差 | 认领区域 | 判定 | 缺的判据（块/边事实表述） |
|---|---|---|---|---|
| `build_current_period_df` | off4 `POP_JUMP_FORWARD_IF_TRUE` 230→212，−9 指令 | `IfRegion@0.then_blocks` | **缺判据** | 尾随 `t['k']=[1 if c else 0]` 的下标赋值被裸发射：LHS 的 `LOAD_FAST+LOAD_CONST+STORE_SUBSCR` 丢失。现门是**指令条数下限**（`MIN_INSTRS_FOR_SUBSCR_ASSIGN=3`）——按 rules.md §2 属禁止的计数特判，应改为「本块内存在 `STORE_SUBSCR` 且其容器/下标装载同在本块」的成员事实 |
| `check_frequency` | off188 `POP_JUMP_FORWARD_IF_TRUE` 198→236 | 终块 blk[456] pure-none，属 `IfRegion@304.then`，由 `AssertRegion@424.condition_block` 接入 | **已守卫但误判** | 见 §IV：B121 修好、G7 又退回。应放宽为「由**已发射的终止语句**（raise/assert）的跳转 argval 接入的汇合落点」也算落点 |
| `get_real_from_zeromq` | off286 `JUMP_FORWARD` 342→344，−2 | `BoolOpRegion@192` + `IfRegion@98/0.merge_block` | **缺判据** | `while not x and c<3` 布尔链 + if/elif/else→return 喂 try 时，多写了一条 `continue`：每出口边只应产出一条 continue |
| `run_individual_transform` | off182 `POP_JUMP_FORWARD_IF_FALSE` 676→540，−14 块；退化异常范围 `start==end==184` | `LoopRegion@334/@586` + `TryExceptRegion@686/@640` | **缺判据** | 内层 `try` 体被塌成 `pass`，循环体被倒进第一个 `except`。嵌套 TryRegion 必须归约为单一抽象节点、由父区域按入口消费（原则 3/4） |
| `run_tick_socket` | off22 `POP_JUMP_FORWARD_IF_FALSE` 158→364，−1 块 | `TryExceptRegion@24/@70` | **已守卫但误判** | 外层 try 的**内层 except** 里写 `return None`，其 handler 出口离开所在区域时应是汇合落点而非内联语句（共享尾巴判据 `:15052/15552`） |
| `get_individual_data` | off2 `POP_JUMP_FORWARD_IF_FALSE` 622→624，+1 | `IfRegion@0.condition_block` + `LoopRegion@494/IfRegion@506.then` | **缺判据** | 链式三元 `int(x) if 0<int(x)<=200 else 200` 在块内指令重建时 off-by-one（与单元 1 同宿主 `_build_effective_stmts`/`_split_subscr_operands`） |

主代理对该表的两点独立修正/保留：
1. 单元 4 的「−91 指令」与主代理 §II 指令数比读数（orig 412 / prod 359，差 53）**量级不一致**，
   方向一致。差异应归因于是否把 NOP/CACHE/EXTENDED_ARG 计入；引用该数时须注明口径。
2. 单元 1/6 同宿主 ⇒ 一条「下标/三元重建」判据可覆盖 2 个单元，且能顺带**移除一处被 rules.md
   禁止的计数门**，属"修算法"而非"加门"，优先级高于其单元数表面价值。

## II. 与本轮其它轴的分区关系

- 单元 4 属主代理 §VII/§VIII 的 **A1 家族**（体被吞并）：`run_individual_transform` 同时是
  A1 的三个单元之一（产物 1332 行 `continue` 后死 9 条）。工单给的机制（try 体塌成 pass）比
  主代理给的（`break/continue` 死码）更靠前，**是同一个丢失的上游解释**，应并入 A1 工单取证。
- 单元 2 属 B121/G7 轴，与区域边界无关 ⇒ 独立成票（见 §IV）。
- 单元 5 的"handler 出口离开所在区域"与 A1 的"臂的 merge 取了父区域出口块"方向相反但同族，
  留给 `r9-fix-ifregion-boundary` 工单一并验证。

## III. 电池复核（主代理读数）

`test_repros/round9/r9_quote_index.json` 原登记 10 条（六单元的损失复现臂），另有 16 条
边界对照臂在盘上未登记 ⇒ 第二真相源风险，已按形状核对后**全部登记**（10→26 条，
缺产物 0）。复算读数：**26 文件 / 43–53 单元**；
10 条损失臂全部 **1/2**（每条恰好复现一个失败单元），16 条对照臂全部 **2/2**。

盘上标本与索引的闭合审计（主代理）：`r9q_*.pyc` 26 条**全部已登记**，无未登记 pyc、无缺产物；
另有 1 条草稿 `r9q_05_guard_boolop_retry_try_return.py`（无 .pyc 也无产物）**不登记**——
登记需要跑 pycdc，而 `r9-fix-ifregion-boundary` 工单正在改 `region_analyzer.py`，
此刻产出的字节属于中间态。该草稿留到下一个可跑发射器的时点再定形，避免把未验证标本混进判据面。

## IV. G7 的代价（主代理独立复算，逐单元名单）

`rounds/round8/after_preG7_b121_only`（B121 未加 G7）与 `after`（加 G7 之后）对同一文件对比：

    preG7  87/92  失败名单：build_current_period_df, get_individual_data,
                              get_real_from_zeromq, run_individual_transform, run_tick_socket
    postG7 86/92  失败名单：上述五个 + check_frequency − （无）
    ⇒ G7 在 quote 上净退 1 单元，退回的正是 `check_frequency`

综合两个文件：**G7 是用 `quote.check_frequency` 换回 `history_data_source.get_bars`**（各 +1/−1）。
这不是 G7 应回滚的理由——`get_bars` 那两条是源码真写的 `else: return None`——但它说明
G7 的判别式（handler-epilogue ∨ 前驱末指令 POP_TOP）**尚未抓到真正的不变式**。
工单给的候选不变式：终块是**已由终止语句（raise/assert/return）收尾的前驱之跳转 argval 落点**
且该落点为本区域汇合块 ⇒ 落点；若终块是某臂的**唯一成员**（臂体语句）⇒ 发射。
`r9g7_01/04` 与 `r9q_02_assert_else_implicit_tail` 已分别钉住两侧，锚点
`history_data_source` 19/19 与 `flytools` 66/66 已在 `r8` 电池中常驻，可直接作为验收面。
