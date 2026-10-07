# Round 9 开局：42 残差单元的实测普查与三轴切分（主代理）

封表时点：2026-10-07。before = `rounds/round8/after/shard*_report.json`（6575/6617、384/402）。
仪器：`nop_census.py`（逐指令 first-diff 分类）、`nop_census2.py`（剔除 NOP/CACHE/EXTENDED_ARG 后按序列
下标重标跳转目标再比对）、以及本轮新增的「单元指令数比」读数（下方表）。三者都是**代理仪器**，
判据仍只有 `scripts/pyc_verify.py`；任何候选修复必须回到 `single` + 全量门禁取证。

## I. 被否证的假设（如实入库）

`TradeLiveBroker._process_order` / `_process_cancel_order` / `_trade_status_handle` 三个单元的 first-diff
同形：orig 在 off=44 有一条承载行号 804（/989/1445）的 `NOP`，产物该偏移直接放真实指令。
查 `co_lines()`：原码语句在 803 行结束、NOP 承载 804、下一条语句起于 **820** 行 ⇒ 我先假设
「残差主体是行锚 NOP 造成的位移」（`TARGET_DELTA` 的偶数差值恰为 2 的倍数，NOP＝2 字节）。

两次独立否证：
1. 剔除 NOP/CACHE/EXTENDED_ARG 并重标跳转目标后，42 单元中 **`NOP_ONLY` = 0**；
2. 指令数比显示这三单元的差**不是位移而是缺失**（见 §II）。
⇒ Round 8 `REVIEW_NOP.md` 的「NOP 是足迹不是缺陷」在残差归因层面第二次得到支持；不再为 NOP 立票。

## II. 实测：产物把方法体「编译没了」

`_process_order` 的 code object：orig **520** 条指令，产物 **42** 条；`_process_cancel_order` 344 → 40；
`order_api.option_order` 94 → 55。产物的函数文本看着是完整的（`break` 之后仍有 30+ 行语句），
但那些语句**不在字节码里**。机制已用最小样例证实：CPython 3.11 会丢掉循环体内
`break` 之后的同块语句——

    def f(c, a, g, h):
        while c:
            if a:
                g(); continue
            break
            h()          # ← 编译后 h() 完全消失（co_names == ()）

⇒ 发射层在循环体中部放了一条**多余的无条件 `break`**，其后整个方法体被 CPython 视为死码丢弃。
文本完整、字节码截断，这正是 `compare_pyc` 报 "Different control flow" 而人工读产物看不出破绽的形态。

## III. 42 单元的三轴切分（按指令数比）

| 轴 | 判据 | 单元数 | 名单（节选） |
|---|---|---|---|
| **A 体吞并** | orig/dec ≥ 1.3 ⇒ 产物少掉成块语句 | **6** | `trade_live_broker._process_order` 520/42、`_process_cancel_order` 344/40、`order_api.option_order` 94/55、`order_api.future_order` 115/88、`wizard_quant_api.get_DMI.calculate_di.<genexpr>` 64/50（**两条单元**） |
| **B 一条之差** | \|orig−dec\| ≤ 3 | **14** | `klinedata.get_multiminute_his_data` 535/536、`real_quote.get_tick_direction` 297/298、`quote.check_frequency` 132/133、`quote.run_tick_socket` 347/348、`quote.get_individual_data` 354/355、`finance.get_fields` 177/178、`function.reconnect` 101/102、`wizard_quant_api.filter_desicion` 195/197、`real_quote.get_real_minute_kline` 280/283、`klinedata.kline_datetime_list` 413/417、`trade_live_broker._sync_worker` 412/410、`quote.get_real_from_zeromq` 793/791、`trade_info_utils.query_strategy_id` 118/117、`__init__._save_testds_to_csv` 81/75 |
| **C 等长错位** | 条数近乎相等、跳转**目标**不同 | **21** | `api_base.get_history_df` 1900/1900、`matcher.match` 800/790、`trade_live_broker.etf_basket_order` 769/769、`rzrq_credit_order` 786/786、`ipo_stocks_order` 1206/1203、`get_ipo_stocks` 497/497、`_process_tick_order` 188/188、`strategy.tick_worker_thread` 294/294、`strategy_universe._on_clear_de_listed` 70/70、`bar._history_bars` 66/66、`trade_info_utils.get_trade_status` 175/175、`query_trade_strategy_info` 123/123、`kill_trade_process` 673/673、`load_daily.<module>` 1017/1017、`quote.run_individual_transform` 412/359、`quote.build_current_period_df` 124/113、`realtime_event_source.clock_worker` 1442/1330、`handlers._target` 203/200、`__init__._on_publish_after_trading_end` 531/527、`klinedata.get_kline_by_count_new` 650/649、`etf_purchase_redemption` 427/415 |
| 无法映射 | `<module>` 单元名 | 1 | `load_daily.<module>` 已改由指令数读数覆盖 |

C 轴里剔 NOP 后**只有 1 处配对不同**的六个单元（`_process_tick_order` `JUMP_BACKWARD` 差 16、
`rzrq_credit_order` `JUMP_FORWARD` 差 28、`get_ipo_stocks` `POP_JUMP_FORWARD_IF_TRUE` 差 24、
`get_trade_status`、`bar._history_bars`、`strategy_universe._on_clear_de_listed`）是最经济的靶面：
结构几乎全对，只差**一条边的落点被换成相邻块**，属原则 4（入口引用语义）层面。

## IV. 取向与禁止项

- A 轴优先：无条件 `break` 的发射必须回到区域归约事实（该边是否为循环出口边、落点是否同区、
  出口之后是否还有未被认领的体语句），**不允许**用「发射后再搬语句」的事后修正（rules.md §1.3 单向数据流）。
  工单简报见 `FIX_BODY_SWALLOW_BRIEF.md`（根因已定位到 `IfRegion@318.else_blocks` 含块 44、
  `merge_block=3128`＝父循环 `back_edge_block`）。
- B/C 轴禁止并案：`_sync_worker` 是**测试极性反转**（orig `POP_JUMP_FORWARD_IF_TRUE→704`
  vs 产物 `POP_JUMP_FORWARD_IF_FALSE→562`），与 target-delta 不同轴。

## V. C 轴的紧致子族（补测：difflib 逐指令对齐，剔 NOP 后）

对 41 个可映射单元做「剔 NOP/CACHE/EXTENDED_ARG + 跳转目标改为序列下标」后的差异块计数：
**`NOP_ONLY_after_strip` 仍为 0**，而 **8 个单元只有 1–2 处差异、且每一处都是同 opcode、
只有跳转目标下标不同**：

    get_trade_status                    JUMP_FORWARD            to@155 vs to@150
    BarData._history_bars               POP_JUMP_FORWARD_IF_FALSE  to@32  vs ...
    StrategyUniverse._on_clear_de_listed POP_JUMP_FORWARD_IF_FALSE to@27  vs ...
    TradeLiveBroker._process_tick_order  JUMP_BACKWARD          to@24  vs to@20
    TradeLiveBroker.rzrq_credit_order    JUMP_FORWARD           to@496 vs to@491
    TradeLiveBroker.get_ipo_stocks       POP_JUMP_FORWARD_IF_TRUE to@230 vs ...
    load_daily <module>                  JUMP_FORWARD           to@666 vs to@684
    kill_trade_process / filter_desicion 各 2 处（POP_JUMP_FORWARD_IF_NONE 目标）

目标下标差为 4–5 条指令 ⇒ 区域边界附近的**语句排布次序**换了 4–5 条指令的位置，
而不是多写/少写语句。这 8 个单元是本轮单位成本最低的一族（其余单元的差块数 ≥5，最多 53）。

## VI. 仪器自我纠偏（两次测量，结论未变但过程必须入库）

上表 §V 用的 `nop_census2.py` 在重标跳转目标时有缺陷：目标若落在被剔除的 NOP 上就退回**原始偏移**，
两侧口径不一致。我随即另写一个探针 `D:/Temp/r9main/ctx.py`，把无法解析的目标一律记为哨兵 `-1`，
它报 `bar._history_bars` 两侧**完全相同**——我据此一度怀疑「NOP_ONLY=0」是错的。

复核结论：那个「完全相同」才是仪器假象。ctx.py 把**两个不同的**错误落点都折叠成同一个 `-1`，
制造了伪等式（`to@-1 == to@-1`）。改用正确口径——目标落在 NOP 上时**向后推进到第一条真实指令**
再按下标比对——重跑 42 个单元：

| 差块数（剔 NOP、目标按真实指令下标解析） | 单元数 |
|---|---|
| `NOP_ONLY`（差异全由 NOP 足迹解释） | **0** |
| 1 | 8 |
| 2 | 4 |
| 3 | 3 |
| 4 | 7 |
| 5 | 5 |
| ≥8 | 15 |

⇒ §I 的否证与 §V 的「8 个单元只差 1 处」都成立，且 `bar._history_bars` 的差是**落点真的不同**，
不是 NOP 足迹。教训与既有约定同源（归一化器必须说明它真正重绑了什么；把「查不到」折成常量
会让两侧的不同塌成相同）：任何判据/仪器的归一化函数，都要先拿一对已知不同的样本验证哨兵不可达。

### 正确口径下的紧致靶面名单（12 个单元，逐条实测）

| 差块数 | 文件 | 单元 | 不同的那条跳转：orig → prod（真实指令下标） |
|---|---|---|---|
| 1 | `IQCommon/data/finance` | `get_fields` | `JUMP_FORWARD` to@50 → to@143 |
| 1 | `IQCommon/util/trade_info_utils` | `get_trade_status` | `JUMP_FORWARD` to@151 → to@147 |
| 1 | `IQEngine/core/bar` | `BarData._history_bars` | `POP_JUMP_FORWARD_IF_FALSE` to@32 → to@51 |
| 1 | `IQEngine/core/strategy/strategy_universe` | `_on_clear_de_listed` | `POP_JUMP_FORWARD_IF_FALSE` to@27 → to@33 |
| 1 | `trade_live_broker` | `_process_tick_order` | `JUMP_BACKWARD` to@22 → to@19 |
| 1 | `trade_live_broker` | `rzrq_credit_order` | `JUMP_FORWARD` to@490 → to@485 |
| 1 | `trade_live_broker` | `get_ipo_stocks` | `POP_JUMP_FORWARD_IF_TRUE` to@225 → to@215 |
| 1 | `fly/dumpload/load_daily` | `<module>` | `JUMP_FORWARD` to@661 → to@679 |
| 2 | `IQCommon/strategy/wizard_quant_api` | `filter_desicion` | `POP_JUMP_FORWARD_IF_NONE` to@181 → to@195 |
| 2 | `IQCommon/util/trade_info_utils` | `kill_trade_process` | `POP_JUMP_FORWARD_IF_NONE` to@641 → to@643 |
| 2 | `IQEngine/plugins/plugin_system_trade/function` | `reconnect` | `JUMP_FORWARD` to@84 → to@99 |
| 2 | `fly/data/quote` | `build_current_period_df` | `POP_JUMP_FORWARD_IF_TRUE` to@121 → to@111 |

差值分两种符号形态：prod 落点**靠前**（−2/−4/−5/−10，共 5 条）与**靠后**（+3/+16/+19/+24/+62/+69）。
靠前＝产物少跳过了几条指令（块被前移）；靠后＝产物把目标块排到了更后面（块被后移或中间多塞了块）。
两类都属「语句/块在区域边界处的排布次序」，与 §II 的 A 轴（体被 `break` 吞掉）不同机制，不得并案。

## VII. A 轴再切分：AST 级死码扫描（把「体被吞」拆成两个不同缺陷）

谓词（一次性扫描，未落地为常驻仪器）：解析每个残差产物，`ast.walk` 中对任一语句列表 `body`，
若下标 i 处为 `Break/Continue/Return/Raise` 且 `body[i+1:]` 非空，即报告一处死码。
18 个残差产物中只有 **3 个文件、共 11 处**（逐处实测，函数名以产物 AST 的 `walk` 路径为近似，不作证据）：

| 产物 | 处数 | 明细（宿主函数 / 行号 / 终止语句 / 其后死亡语句数→后继类型） |
|---|---|---|
| `trade_live_broker` | 5 | `_process_order` 429 `break`→2→Try；`_process_cancel_order` 528 `continue`→5→Assign、564 `continue`→1→Try；`_sync_worker` 855 `return`→4→Continue、856 `continue`→3→If |
| `quote` | 3 | `run_individual_transform` 1332 `continue`→9→If；`get_real_from_zeromq` 1084/1116 `continue`→1→`continue` |
| `wizard_quant_api` | 3 | `read_config_file` 543/597/622 `continue`→1→`continue` |

**关键反例（限定的实证）**：`wizard_quant_api.read_config_file` 的 3 处与 `quote.get_real_from_zeromq`
的 2 处所在单元**都读 Equal**（该文件失败单元是 `get_DMI.calculate_di.<genexpr>`×2 与 `filter_desicion`；
`get_real_from_zeromq` 的失败单元另有其形）。⇒ 原码本身就写有不可达语句时，两侧编译结果相同，
死码形状本身**不是**缺陷；只有与「指令数比 ≥1.3」同时成立才算 A1。
按「指令数比 ≥1.3 ∧ 存在死码形状」的严格交集，**A1＝3 个单元**：
`_process_order`(520/42)、`_process_cancel_order`(344/40)、`run_individual_transform`(412/359)。
`_sync_worker` 虽有 855/856 两处死码，但比值 412/410≈1.0 ⇒ 原码同处本就不可达，
它的差是测试极性反转，不是吞并（不得并案）。
**A2＝4 个单元**（比值≥1.3 而**无**死码形状，语句被直接省略）：`order_api.option_order`(94/55)、
`order_api.future_order`(115/88)、`wizard_quant_api.get_DMI.calculate_di.<genexpr>`(64/50，两条单元)。

**A1＝死码吞并**（上述 3 文件）与 **A2＝发射端整块缺失**：§III 指令数比里的 `order_api.option_order`
（94/55）与 `order_api.future_order`（115/88）**在本扫描中零命中**——产物文本里没有任何
「终止语句之后还有语句」的形状，字节码却少了 39/27 条指令 ⇒ 语句是被生成端**直接省略**的，
不是被 CPython 当死码丢弃的。两种形状修法不同，禁止并案。

须同时记录的诚实限定：原始源码本身就可能写有不可达语句；若原码也这样，两侧编译结果相同，
该处死码就不是缺陷。判据以「指令数比 ≥1.3」为准（已逐单元核对），死码扫描只用于**定位形状**。
- 仪器已知缺陷：单元名 → code object 用路径尾段匹配，同名/嵌套宿主可能错配；
  本轮 §II/§III 的关键读数（520/42、344/40、94/55）已用 `co_firstlineno` + 唯一命中复核，
  确认**不是**错配而是真实截断。

## VIII. C 轴三个标本的逐位对齐（把「落点差」收敛成一个候选根因）

剔 NOP/CACHE/EXTENDED_ARG 并按真实指令下标重标跳转后，三个单元**只有 1 条指令不同，且只差目标下标**：

| 单元 | 位置 | orig 落点 | prod 落点 | 方向 |
|---|---|---|---|---|
| `bar._history_bars` | #27 `POP_JUMP_FORWARD_IF_FALSE` | #32（跳 5 条） | #51（跳 24 条） | prod 更晚 |
| `strategy_universe._on_clear_de_listed` | #19 `POP_JUMP_FORWARD_IF_FALSE` | #27 | #33 | prod 更晚 |
| `trade_live_broker._process_tick_order` | #30 `JUMP_BACKWARD` | #22 | #19 | prod 更早 |

「prod 更晚」两侧指令流完全同序同长、只有一条边不同，含义唯一：原码里该条件假边的**汇合块**
就是 5 条指令之后那个块（两条边在同一块汇合），而产物把中间那段排进了臂内部，
于是假边一路跳到更后。⇒ 形状是 **IfRegion 的 merge/边界取得过晚，把本属区域之后的块吸进臂里**。
「prod 更早」（回边锚到更靠前的块）是同族的另一端：回边锚点选择偏早。

**统一假设（待工单验证，不作结论）**：A1（`IfRegion@318.else_blocks` 吸入父循环前导块 44、
`merge_block` 取到父循环 back_edge 块 3128）与 C 轴「prod 更晚」两例，同为
**IfRegion 的 merge/成员边界计算错误**——一侧吸过界（吞到区域入口之前与父区域出口），
一侧吸太晚（吞掉汇合块之后的块）。若成立，一处边界判据的修正上界约 **A1 3 + C 8 ≈ 11 个单元**，
是 42 残差中最大的单一杠杆。工单必须先用最小合成孪生分别复现**两个方向**（Battery before corpus），
禁止只按其中一侧调门限。

## IX. 42 单元互斥台账与「落点」轴的真实射程（单趟重算，阈值明示）

仪器：`D:/Temp/r9main/ledger.py`（只读 stdlib：marshal+dis+compile+ast+difflib，**不导入 core**，
故在 `region_analyzer.py` 处于中间态时仍可安全运行）。每单元记四项：
剔噪后指令数比、差块数、首个差块是否仅跳转目标不同、产物该函数是否存在死码。

| 互斥桶 | 判据 | 单元数 | 代表读数 |
|---|---|---|---|
| A1 体吞并 | 比≥1.15 ∧ 有死码 | **3** | `_process_order` 507/42、`_process_cancel_order` 333/40、`run_individual_transform` 407/355 |
| A2 整段省略 | 比≥1.28 ∧ 无死码 | **4** | `option_order` 94/55、`future_order` 115/88、`calculate_di.<genexpr>` ×2（64/50，各少 14 条＝一条 boolop `and` 支腿） |
| 纯落点 | opcode 序列**完全相同**，仅跳转目标不同 | **11** | 8 个只差 1 块：`_history_bars` 32→51、`get_fields` 50→143、`reconnect` 84→99、`load_daily.<module>` 661→679、`_on_clear_de_listed` 27→33、`kill_trade_process` 641→643、`get_trade_status` 151→147、`_process_tick_order` 22→19、`rzrq_credit_order` 490→485、`get_ipo_stocks` 225→215；另 2 个差 2 块、`tick_worker_thread` 差 4 块 |
| 混合内容差 | opcode 序列不等 | **24** | 但其中 **24 个的首个差块仍是同 opcode 的跳转目标差**（IF_FALSE 12、FOR_ITER 4、IF_NONE 3、IF_TRUE 3、JUMP_FORWARD 2） |

**对 §VIII 的自我修正（按精确谓词重测，不用算术）**：谓词取「首个差块两侧**长度相等且 opcode 序列逐位相同**
⇒ 该单元第一处分歧只是跳转落点」。42 单元实测结果是一个**完整二分**（35+7=42，无重叠、无未归类）：

| 第一处分歧 | 单元数 | 名单 |
|---|---|---|
| **仅落点**（first-hunk target-only） | **35** | 其余全部；含 11 个「整条 opcode 序列相同、只有目标不同」的紧致例与 24 个「先落点错、其后才有内容差」的单元 |
| **内容缺失/多出**（first-hunk content） | **7** | `trade_live_broker`: `_process_order`、`_process_cancel_order`、`_sync_worker`、`_trade_status_handle`；`order_api`: `option_order`、`future_order`；`quote`: `run_individual_transform` |
| 归一化后完全相等（NOP_ONLY） | **0** | §I/§VI 两次独立否证 NOP 主体假说，此处再次为 0 |

⇒ **#14（落点/边界）的真实射程是 35 个单元**，而不是 §VIII 按互斥桶估的「≈11」；
**#13（内容缺失）开局单元是 7 个**——注意 `wizard_quant_api.calculate_di.<genexpr>` 两条
**不在**此列：它们的 boolop `and` 支腿丢失发生在序列后段，第一处分歧仍是落点，
故该二单元归 #14 之后再补 #13 复测，不得预先认领。
`_sync_worker` 与 `_trade_status_handle` 是**新落入内容轴**的两个（此前只在 §III 的比值表里出现过），
#13 工单靶面由 6 修正为 7。
两桶相加＝42，是**互斥且完备**的分区；#14 落地后必须重算本表，
届时「先落点错、后内容差」的 24 个可能整段消失，也可能暴露新的内容轴——以重测为准，
禁止用算术代替重测（既有约定：台账数字须在写入时算出）。

## X. 轮门禁可行性核对（决定 #13/#14 派发次序，实测非推断）

从 `rounds/round8/after` 逐文件读数：**只差 1 个单元就整文件 OK 的文件共 10 个**——

    finance.get_fields / bar.BarData._history_bars / strategyUniverse._on_clear_de_listed /
    load_daily.<module> / function.reconnect / Strategy.tick_worker_thread /
    DefaultMatcher.match / api_base.get_history_df / TWHThreadController._target /
    RealtimeEventSource.clock_worker

把 §IX 的首分歧二分套到这 10 个单元上：**全部落在「首分歧＝落点」的 35 个之列，
无一出现在 7 个内容先行单元名单里**（那份名单是 `_process_order`、`_process_cancel_order`、
`_sync_worker`、`_trade_status_handle`、`option_order`、`future_order`、`run_individual_transform`）。

⇒ 结论（对派发次序是硬约束）：
- **#14 一条票就可能带来最多 10 个文件转完全 OK**（384→394），轮门禁「≥1 个 pyc 由 failure 转 success」
  由 #14 单独即可满足；这也正是判据该统一的地方——一个边界/落点修正若只翻动这 10 个中的 1–2 个，
  说明机制还没找对，而不是"先收下这一两个"。
- **#13 是第二条独立路径**（`order_api` 35/37→37/37，加 2 个省略单元），不得用它的翻转去抵 #14 的射程。
- 本轮若 #14 零翻转，仍须由 #13 单独交付 ≥1 文件转 OK 才能开下一轮；两者皆零翻转＝门禁未过，禁止下一轮。

## XI. #14 的上界检验：落点之外每个大单元还压着内容差（HEAD 口径逐块分类）

把每单元的差块分成「两侧 opcode 序列相同、只差目标」与「内容差」两类（9 个大单元实测）：

| 文件.单元 | 差块数 | 仅落点 | 内容差 |
|---|---|---|---|
| `trade_live_broker.etf_basket_order` | 39 | 37 | **2** |
| `trade_live_broker.ipo_stocks_order` | 35 | 34 | **1** |
| `matcher.DefaultMatcher.match` | 25 | 24 | **1** |
| `klinedata.kline_datetime_list` | 31 | 27 | 4 |
| `realtime_event_source.clock_worker` | 45 | 38 | 7 |
| `quote.get_real_from_zeromq` | 39 | 34 | 5 |
| `api_base.get_history_df` | 20 | 15 | 5 |
| `trade_live_broker._sync_worker` | 18 | 9 | 9 |
| `quote.run_individual_transform` | 21 | 12 | 9 |

⇒ **落点修好≠单元翻正**：这些单元即使 37/34/24 条落点全部对上，
仍被 1–9 条内容差挡着。内容差的形状（逐条打印取证）：

- `ipo_stocks_order`：orig `JUMP_BACKWARD to@450` + `JUMP_FORWARD to@732`，产物只剩一条
  `JUMP_FORWARD to@731` ⇒ **回边跳消失**（与 #14 的回边锚点同族，非新增轴）。
- `matcher.match`：产物**少 10 条**——`order.asset.symbol` 取属性 + `LOAD_CONST None/3` +
  `BUILD_SLICE`… ⇒ **表达式/切片整段未产出**，属 #13 的省略形。
- `etf_basket_order`：产物少 11 条（`BINARY_OP %`…`POP_TOP/POP_TOP/LOAD_CONST None/RETURN_VALUE`…）
  同时多 11 条（`strategy_log.warning('该股票【%s】行情数据异常'…`）⇒ **语句被放进了错误的臂**，
  删除与插入成对，属排位形。

结论：#13 的第二波候选（在 #14 落地、落点噪声退去后才可判）至少含 `matcher.match`（省略形）；
`etf_basket_order` 的成对删插与 `ipo_stocks_order` 的回边消失应并回 #14 而不是新开票。
本表的意义是给 #14 的验收设**上界预期**：它单独最多把这 9 个单元中「内容差恰为回边/排位形」者翻正，
不能按「35 全翻」计成绩。


## XII. 42 单元的完备互斥分派（按 opcode 多重集；取代 §IX 的「射程」表述）

判据（`D:/Temp/r9main/routing2.py`，产物一律取自 `git show HEAD:`，避开在飞工单重生成过的文件）：
剔噪后比较两侧 opcode **多重集**与**净指令差**。多重集不等的单元，
**任何只做重排/改落点的修复都不可能翻正它**——这是比 §IX「首分歧」更硬的可达性判据。

| 分派 | 判据 | 单元数 | 归属 |
|---|---|---|---|
| `REORDER_ONLY` | 多重集相同，仅顺序/目标不同 | **12** | **#14（落点与重排）——这才是它的真实射程** |
| `CONTENT_LOSS` | 产物净少指令 | **16** | #13（省略/吞并族） |
| `CONTENT_EXTRA` | 产物**净多**指令 | **9** | **此前无人开票 ⇒ 新轴 #17「多发射」** |
| `POLARITY_or_jump_kind` | 跳转种类互换（IF_TRUE↔IF_FALSE 等） | **2** | 新轴 #18（`api_base.get_history_df`、`klinedata.kline_datetime_list`）——**本行原写 `_sync_worker` 为误记**：`routing2.py` 对 HEAD 产物实测该桶只含这两条，`_sync_worker` 落 `CONTENT_LOSS(+3)`（miss 前列 `LOAD_ATTR×2, JUMP_FORWARD×2`）。2026-10-08 主代理按仪器原读数订正 |
| `IMPLICIT_TAIL` | 只差 `LOAD_CONST`+`RETURN_VALUE` | **1** | #15（G7b） |
| `NORMALIZER_BLIND` | 归一化序列已相同却仍判失败 | **2** | 未定：差在常量身份或行号表，我这仪器看不见 |

合计 12+16+9+2+1+2 = **42**，互斥且完备。

**必须说出自打**：§IX 我写的「#14 射程 35 个单元」在**首分歧**口径下不错，但对排产是**误导**——
其中 23 个单元在后面还压着内容增删，落点修对了也不会翻正。
可达性一律以本表为准：**#14 最多 12、#13 最多 16、#17 是 9 个从没被认领的单元**。
`matcher.match`/`clock_worker` 之类在此表里落到 CONTENT_* 而非落点族，与 §VI 的直觉不同。

两点仪器限定：单元名到 code object 仍按名字尾段匹配（同名多实例会错配，本表内 `calculate_di.<genexpr>`
两条即属此情形）；`NORMALIZER_BLIND` 说明我的归一化丢掉了判据真正比较的某些事实，
不能当作「这两单元没差别」。


## XIII. §XII 的收紧复算（把「净多指令」桶里的搬运与真多出分开）

§XII 用 opcode 多重集的**净值**分桶，把「先搬走一大批、再补回一小批」的单元也算进了 `CONTENT_EXTRA`。
按 **insert / delete 分列**重算 42 个单元（同 HEAD 产物、同归一化）：

| 严格分派 | 单元数 | 说明 |
|---|---|---|
| `NET_LOSS`（删多于插） | **16** | #13 省略族 |
| `MIXED/REORDER`（插删相抵或纯重排） | **14** | #14 落点/重排族（含 §XII 的 12 个 `REORDER_ONLY`） |
| `NET_EXTRA`（插多于删） | **7** | 其中 **5 个只多 1–2 条指令**（`check_frequency`、`get_individual_data`、`get_tick_direction`、`get_real_minute_kline`、`filter_desicion`），形如多一个 `LOAD_CONST None` 之类 ⇒ **归 #15 隐式尾声面**；另 2 个是重排量大（`get_history_df` ins=4、`_sync_worker` ins=174/del=140） |
| `JUMP_KIND_SWAP`（IF_TRUE↔IF_FALSE 类互换） | **3** | #18 极性轴（比 §XII 估的 2 个多 1） |
| `NORMALIZER_BLIND` | **2** | 我的归一化看不见其差别（常量身份/行号表面），不得当作无差别 |

合计 16+14+7+3+2 = **42**，互斥完备。

**自我纠正两处**：① §XII 的「9 个净多指令单元」在分列 insert/delete 后是 **7**，且其中只有 5 个是真正的
少量多发射，应并入 #15 而不是自成一大族；② 极性等桶由 2 修正为 **3**。
排产含义不变的一点是硬的：**#14 的可达上限就是 14 个（其中 12 个连多重集都相同）**，
剩下 28 个必须靠 #13/#15/#18 或尚未立案的 `NORMALIZER_BLIND` 两单元。


## XIV. §XIII 的 `NORMALIZER_BLIND = 2` 撤销：那是我的取对象缺陷，不是判据看不见的事实

逐对象枚举 `wizard_quant_api` 里 `calculate_di` 下的**三个** `<genexpr>`（按遍历序配对，非按名字）：

| 配对 | 剔噪指令数 orig/prod | 含 NOP 是否全等 | 该单元状态 |
|---|---|---|---|
| #0 | 46/46 | **是** | 读 Equal（本来就不在残差里） |
| #1 | 64/**50** | 否 | 失败单元 |
| #2 | 64/**50** | 否 | 失败单元 |

`routing2.py` 用「路径尾段 == 名字」取 code object，对同名多实例**恒返回第一个**，
于是把 #0 那两个副本当成「归一化后已全等却仍失败」的两条 `NORMALIZER_BLIND` 记进表。
实际两个失败单元是 #1/#2，各少 14 条指令，且此前独立的多重集测量已给出缺失内容
（2 个 `COMPARE_OP`、2 个 `BINARY_SUBSCR`、2 个 `LOAD_CONST` 等 ⇒ boolop `and` 支腿被丢），属 #13。

**修正后的完备分派（仍互斥、仍合计 42）**：

    NET_LOSS 18 | MIXED/REORDER 14 | NET_EXTRA 7 | JUMP_KIND_SWAP 3      （18+14+7+3 = 42）

⇒ #13 的省略面由 16 增至 **18**；#14 上限仍是 **14**（其中 12 个多重集全等）；
`NORMALIZER_BLIND` 一栏**删除**——它没有指向判据的盲区，而是指向我自己仪器的名字错配。

**仪器规矩（写死）**：任何逐单元断言必须先按**遍历序 + 完整 qualname**定位 code object，
同名多实例要逐个列出并标号；用名字尾段 `pick` 得到的「相等/不等」一律不得入表。
本轮此前两处被推翻的「纠正」（`handlers`、`while…else`）与本次这处同源。


## XV. 同名多实例修正后的终版分派（三种口径各自写明，排产只认最严的一种）

`routing3.py` 对同名 code object **按最佳匹配配对**（`difflib.ratio` 取最优并报告歧义数），
不再「按名字取首个」。歧义行 3 条：`handlers.TWHThreadController._target`（该文件内两个 `_target`）、
`get_DMI.calculate_di.<genexpr>`（三个，取 #1/#2）。修正后 42 单元分派：

| 口径（谓词写死） | LOSS | REORDER | EXTRA | 合计 |
|---|---|---|---|---|
| **长度相等即 REORDER**（`routing3`，剔噪后指令数） | 17 | **18** | 7 | 42 |
| **opcode 多重集相等才算 REORDER**（§XIII，`routing2`） | 18 | **14**（+ 极性互换 3） | 7 | 42 |
| 两者差异的来源 | 1 条从 LOSS 移到 REORDER | 3 条长度相等但跳转种类互换 | 同 | — |

⇒ **排产取严口径**：一次纯落点/重排修复的**可翻正上限 = 14 单元**（其中 12 条连 opcode 序列都同序），
其余 4 条要等 #18（极性）与 #13（省略 17–18 条，视口径）；`#14` 若只带来 ≤14 单元翻转属**符合预期**，
不得按 35 或 18 记账。§XIII 里 `LOSS=18` 与本表 `LOSS=17` 的差是同名配对修正所致，
两个数都各自的口径下成立，本表是终版。

## XVI. `#18 极性轴` 撤销：那是**只看 opcode 多重集、不看跳转目标**造成的仪器假象

`POLARITY_or_jump_kind`（§XII 记 2、§XIII/§XV 记 3）的定义是「`IF_TRUE` 少 N 条 ∧ `IF_FALSE` 多 N 条 ∧ `|net|≤2`」。
`ops()` 只数 opname——**跳转目标被完全丢弃**，因此「同一站点少了 4 条指令、其条件测试被重写」也会表现成
「种类互换」。主代理改用**目标解析后的序列**（相对跳转一律归一到其后第一条保留指令的
`opname@offset`）＋ `difflib` 对齐复验，两单元逐 hunk 分类（HEAD 产物，`D:/Temp/r9main/pol.py`）：

| 单元（完整路径＋qualname） | 判据链原判 | hunk 总数 | **孤立的「换 opcode」hunk** | 同 opcode 仅目标差 | 多指令块（内容差） |
|---|---|---|---|---|---|
| `IQData/api/api_base.pyc :: <module>.get_history_df` | POLARITY | 23 | **0** | 17 | 6（含 `orig[449:454]=5 → prod 1`、`orig[527:536]=9 → prod 1`、`orig[514:515]=1 → prod 9`） |
| `IQCommon/api/klinedata.pyc :: <module>.kline_datetime_list` | POLARITY | 34 | **0** | 27 | 7（含 `orig[158:163]=5 → prod 1`、`orig[327:328]=1 → prod 9`、`delete orig[333:341]=8`） |

⇒ **零条孤立极性互换**：两单元没有任何一个站点是「只把 `IF_TRUE` 写成 `IF_FALSE`、其余不动」。
它们的所有差都是**同一族的两种面**——同 opcode 的跳转目标差（#14 落点轴）＋ 多指令块的省略/挪位（#13 省略轴）。
两单元共享的形状尤其值得注意：**一段 5 指令语句被压成 1 条，同时别处 1 条被摊成 9 条**
（`api_base` 在 orig[449]/orig[514]，`klinedata` 在 orig[158]/orig[327]）；被压掉的 5 条实测是
`LOAD_CONST 1 / BINARY_OP -= / STORE_FAST time_count / LOAD_FAST frequency / …`
＝ `time_count -= 1` 那一轮的循环测试算术，其测试本身随后被写成反极性——**极性差异是省略的后果，不是原因**。

**分派结论（取代 §XV「其余 4 条要等 #18」那句）**：
- `#18` 作为独立工单**撤销**，不得派发（派出去只会让工程师去找一条不存在的「极性规则」）；
- 这两单元并入 `#14`（落点）与 `#13`（省略）名单；`#13` 的 5→1 / 1→9 形状是**新增的具体靶形**，
  已并入 `FIX_STMT_FRAGMENT_BRIEF.md` 的机制清单；
- `#14` 的可翻正上限仍按严口径 **14** 记账，不因本撤销而改变；
- §XII/§XIII 中凡按 opname 多重集定义的桶，**须在目标解析后复验**才可开票——本轮已按此条
  撤销 #18，并订正 §XII 极性桶名单误记（第二条是 `klinedata.kline_datetime_list`，非 `_sync_worker`）。

**方法教训（写进台账纪律）**：分桶谓词里丢掉的每一个字段（这里是跳转目标）都是将来的一个假轴。
「换个漂亮名字 + 一个不存在的修法」比「少一个桶」危险得多，因为它会吃掉一整轮的门禁窗口。
