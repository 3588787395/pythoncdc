# Round 9 ticket #13 简报：A2「语句省略」族（HEAD 机制口径 6 个单元，主代理实测定位）

## 靶面修正：以 HEAD 字节重测「省略 vs 挪位」（写盘一次，口径明示）

口径：`.pyc` 输入不在 git 内（`.gitignore: *.pyc`），但**输入从不被重写**，故直接读盘；
产物一律取 `git show HEAD:<path>` 到 `D:/Temp/r9main/headstate/`，**不读工作树**
（`r9-fix-ifregion-boundary` 正在改生产码并重生成 `trade_live_brokerOK.py`——
我一度用工作树读数，同一函数在两条命令之间从 42 条指令变成 463 条，那张表随即作废）。
序列剔 `NOP/CACHE/EXTENDED_ARG`、嵌套 code object 归一为 `<co>`，再按 difflib 统计删除段与插入段：

| 单元 | 指令数 orig/prod | del | ins | 差块数 | 形状 | 归属 |
|---|---|---|---|---|---|---|
| `_process_order` | 507/42 | 470 | 5 | 5 | **OMISSION** | #13 |
| `_process_cancel_order` | 333/40 | 299 | 6 | 3 | **OMISSION** | #13 |
| `option_order` | 94/55 | 42 | 3 | 4 | **OMISSION** | #13 |
| `future_order` | 115/88 | 30 | 3 | 4 | **OMISSION** | #13 |
| `run_individual_transform` | 407/355 | 84 | 32 | 21 | **OMISSION** | #13 |
| `_sync_worker` | 404/401 | 192 | 189 | 18 | **DISPLACEMENT** | → 移交 #14 |
| `_trade_status_handle` | 127/124 | 18 | 15 | 11 | **DISPLACEMENT** | → 移交 #14 |
| `build_current_period_df` | 123/113 | 17 | 7 | 6 | **OMISSION** | #13（虽属"首分歧＝落点"集） |
| `get_individual_data` | 351/352 | 13 | 14 | 14 | **DISPLACEMENT** | → 移交 #14 |

判据：`min(del,ins) ≥ 0.5·max(del,ins) ∧ max ≥ 10` 记 DISPLACEMENT（大块挪位），否则 OMISSION。
⇒ **#13 按机制的靶面是 6 个单元**：`_process_order`、`_process_cancel_order`、`option_order`、
`future_order`、`run_individual_transform`、`build_current_period_df`（后者首分歧虽是落点，
但 del 17 / ins 7 是净缺失，且它的宿主计数门正是本案要修的 `MIN_INSTRS_FOR_SUBSCR_ASSIGN`）。
`_sync_worker`、`_trade_status_handle`、`get_individual_data` 三个删除段≈插入段，
是**大块被重新排位**，属 #14 的落点/边界轴；把它们留在 #13 会让工单去"补语句"，而真正缺的是排位。
先前作废表里 `_process_cancel_order` 被判为 DISPLACEMENT，也是同一污染所致——HEAD 口径为 OMISSION。
`wizard_quant_api.calculate_di.<genexpr>` 两条仍不在本表（首分歧是落点，见 `REVIEW_RESIDUAL_CENSUS.md` §IX）。

## 计数门的实际散布面（HEAD 口径逐调用点取证，工单必须先读完）

`git show HEAD:core/cfg/region_ast_generator.py` + `ast` 归属（BOM 需 `utf-8-sig` 才能 `ast.parse`）：

    :27      MIN_INSTRS_FOR_SUBSCR_ASSIGN = 3      # 注释自陈：value + container + index 三指令
    :2863    _split_subscr_operands(def 2812)
    :3535    _build_effective_stmts(def 3493)
    :52734   ┐
    :52957   ├ _generate_block_statements_body(def 51983)   ← 同一判定复制 3 处
    :53083   ┘
    :56683   _generate_stmts_from_instrs(def 56626)

⇒ 该「`STORE_SUBSCR` ∧ 表达式指令数 ≥3」判定被**复制到 4 个方法、6 个调用点**。
两点直接后果，工单必须一并处理：

1. **只改 `_build_effective_stmts` 是无效修复**：另外 3 个方法仍按旧计数取捨，
   会出现"一个单元翻正、同族其他单元原地不动"的假进展——历史上本规范已因此判退过零翻转票。
2. **C3 违反本身就是缺陷**（rules.md「一处判定、多处复用」）：修复的正确形态是把该判定收敛为
   **一个** 结构判据方法（输入＝本语句指令段 + 块成员事实；输出＝能否解出 container/index/value
   三元），6 个调用点全部改调它；删除常量时须报告影响面（几处调用被收敛、原语义何处保留）。

计数为何是错的代理：CPython 把 `a[b] = c` 的下标与容器装载可能跨块或被拆进表达式续体，
此时"段内指令条数 <3"并不等于"不是下标赋值"，而 `build_current_period_df`（del 17 / ins 7）
正是 LHS 的 `LOAD_FAST+LOAD_CONST+STORE_SUBSCR` 被当成"凑不满三条"而裸发射值段。
判据应问「段内是否存在 `STORE_SUBSCR`，且其容器/下标/值三个操作数在本语句段内都能归位」，
不问条数。

## 与 #14 的关系（不得并案）

`#14` 是**区域边界/落点**错（臂把汇合块之后的块吸进来、回边锚点偏早）；本案 6 个单元是
**内容根本不产出**——区域划分在探针里是对的，丢的内容发生在把块内指令重建为语句的那一步。
两个口径要分清，不得混用：按「首处分歧」二分是 35 落点 / 7 内容；按「机制」分（本表 del≈ins 判据）
是 **#14 36 个（35 落点 − `build_current_period_df` + `_sync_worker` + `_trade_status_handle` + `get_individual_data`）/ #13 6 个**，两数互斥且相加＝42。
先前写的「11 + 6 ＝ 17」是按互斥桶估的旧数，已被 `REVIEW_RESIDUAL_CENSUS.md` §IX 与本表取代，不再引用。

## 共同形状（三处独立实测，同一宿主）

宿主经主代理 grep 核实存在：`_build_effective_stmts`（`core/cfg/region_ast_generator.py:3493`）、
`_split_subscr_operands`（`:2812`）、模块级常量 `MIN_INSTRS_FOR_SUBSCR_ASSIGN = 3`（`:27`）。
⇒ 现口径里有**一个按指令条数取捨的门**，属 rules.md §2 明令禁止的计数特判；本案的修复方向是
把它换成块/结构事实（哪条指令属于哪个子表达式），而不是调数值。

### 1) `IQCommon/strategy/wizard_quant_api.pyc` — `get_DMI.calculate_di.<genexpr>`（2 个失败单元）

三个 genexpr 逐一配对（按 `co_firstlineno`，剔 NOP/CACHE/EXTENDED_ARG 后的真实指令数）：

    ORIG  genexpr@385 → 46   genexpr@388 → 64   genexpr@390 → 64
    PROD  genexpr@262 → 46   genexpr@263 → 50   genexpr@264 → 50

⇒ 第一条全对，后两条**各少 14 条**。少在哪：orig@388 有 **2 个 `COMPARE_OP >` + 2 个
`POP_JUMP_FORWARD_IF_FALSE`，且两条假边同跳 to 202**（`DUP_TOP=0` ⇒ 不是链式比较），
产物只剩 **1 个 `COMPARE_OP` + 1 个跳转**；`BINARY_SUBSCR` 8→6、`LOAD_CONST` 7→5。
两条假边同目标＝一个 `and` 短路；⇒ **三元表达式 test 位置里的 boolop `and` 支腿被丢掉一条**。

### 2) `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` — `option_order`（94→55）/ `future_order`（115→88）

`option_order` 原码在 487–493 行有 **3 处表达式内条件跳转**（off 342/416/502，line 490/491/493），
即一条 `strategy_log.info(f'…{三元}…')` 调用里嵌了多个三元。
产物（`option_orderOK.py:225-239`）把该调用**降级成一条裸三元语句**并结束了函数：

    if order_ is None:
        return None
    elif not is_trade():
        '买入' if order_.entrust_direction.value.upper() == 'BUY' else '卖出'   # ← 只此一个三元，父调用消失
    return order_.order_id

⇒ **子表达式被当成独立语句发射，承载它的父语句整体丢失**（与 §1 同向：重建时只接回一部分操作数）。

### 3) `fly/data/quote.pyc` — `build_current_period_df` / `get_individual_data`

工单 `r9-quote-char` 已定性并由主代理逐单元名单复核：前者尾随 `t['k'] = [1 if c else 0]`
的 LHS（`LOAD_FAST + LOAD_CONST + STORE_SUBSCR`）丢失、裸发射为表达式语句；
后者为三元/比较重建 off-by-one（+1 指令）。两条复现臂已在盘：
`test_repros/round9/r9q_01_subscript_ternary_assign`、`r9q_05_chained_ternary_retry_try`、
`r9q_18_nested_subscript_dict_ternary`、`r9q_22_fstring_subscript_assign`（对照）、
`r9q_12_chained_cmp_then_retry_try`，均在 `r9_quote_index.json`（26 臂，43/53 单元）。

## 工单要求

1. 先取证后编码：对上面 6 个单元逐一确认「丢失的是**父语句**还是**支腿**」，
   并给出块内指令到子表达式的归属证据（哪条指令属于哪个 AST 节点）。禁止用文本比对代替指令证据。
2. 判据必须写成块/结构事实：例如「一条语句的指令序列在本块内可完整切分为
   值生产段 + 存储段 ⇒ 必须重建为赋值语句；切分不出存储段时不得只发射值段」，
   「boolop 成员若有多条同目标假边 ⇒ 每个成员腿各自重建，不得合并成一条」。
   禁止以指令条数阈值、函数名、文件名为条件（rules.md §2）。
3. 若确认 `MIN_INSTRS_FOR_SUBSCR_ASSIGN` 就是罪魁，**移除该计数门**并以块成员事实取代；
   必须**一次收敛全部 6 个调用点 / 4 个方法**（见上节），只改一处即宣告修好属无效修复；
   删除常量须报告运行时影响面（不许留下未消费的死常量）。
4. docstring 六项模板 + C1/C2/C3 + 标记 `[R9-B1xx <slug>]`；识别与发射两端各自改动须在报告分列。
5. 验收（逐单元名单前后对比，不许只报总数）——靶面按机制口径＝**6 个单元**：
   `trade_live_broker` 118/128：`_process_order`、`_process_cancel_order` 转 Equal（≥120/128）；
   `order_api` 35/37：`option_order`、`future_order` 转 Equal（37/37）；
   `quote` 86/92：**仅 `build_current_period_df`** 转 Equal。
   **不在本票靶面**（按机制已移交 #14，若被顺带翻正须单列证据而非计入成绩）：
   `wizard_quant_api` 的两条 `calculate_di.<genexpr>`、`quote.get_individual_data`、
   `trade_live_broker._sync_worker`、`_trade_status_handle`。
   锚点不回退：quotation 153/153、flytools 66/66、history_data_source 19/19、quote_handler 79/79、
   ptradeAccount 137/137；七套 r1–r8 电池 + `r9_probe_index`(8/8) + `r9_quote_index`(43/53 中
   **16 条对照臂必须仍 2/2**) 零绿转红；pytest 六套件仍 277/2/2 同名单。
6. 全量 402 门禁由主代理执行。零翻转则按 sha256 逐字节回滚并把否证作为交付。
