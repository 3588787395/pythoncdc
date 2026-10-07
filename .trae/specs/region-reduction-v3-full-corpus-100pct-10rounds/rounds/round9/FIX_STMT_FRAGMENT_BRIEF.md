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

## 第二波已定形的一个目标：`matcher.DefaultMatcher.match`（只差 1 条内容差）

取证（HEAD 产物 + 盘上 pyc，剔噪后逐块）：该单元 25 个差块里 24 个是落点，**只有 1 个是内容差**，
形状是一段 10 条指令的整句缺失，原码 line 241：

    LOAD_FAST order | LOAD_ATTR asset | LOAD_ATTR symbol | LOAD_CONST None | LOAD_CONST 3
    BUILD_SLICE | BINARY_SUBSCR | LOAD_CONST ('688','689') | CONTAINS_OP
    POP_JUMP_FORWARD_IF_FALSE →2464 | LOAD_FAST is_first_five_trad… | POP_JUMP_FORWARD_IF_TRUE →2464
    ⇒ 源语句为 `if order.asset.symbol[:3] in ('688', '689') and is_first_five_trading_day…:`

产物里这个测试**完全不存在**（`matcherOK.py:152` 只有 `if order.asset.symbol[:3] not in ('300','688','689'):`）。
`co_consts` 实测同时含 `('300','688','689')` 与 `('688','689')` 两个元组，
⇒ 缺陷形状是**两个同形成员测试只在常量元组上不同，被合并/吞掉其一**：
发射端按形状对齐同族测试时，**没有把常量操作数身份算作区分事实**。

判据方向（须写成块/操作数事实，禁止按名字或元组内容特判）：
两条 `CONTAINS_OP` 测试若 `LOAD_CONST` 的元组对象**不同一**，即为两条独立语句，不得合并、不得互相顶替；
合并只允许发生在常量也相同的情形。

排序：本条**在 #14 落地后**再取（它的第一处分歧是落点，落点噪声退去才能确认这条内容差是否就是最后障碍）。
若届时该单元只剩这 1 条差，它就是本票最经济的单点靶；若落点修复顺带把它带走，则如实记为 #14 的战果，
不得算进 #13。

## 复现臂名册（主代理按实测形状预置，满足 spec「每缺陷 ≥10 复现 · 深度 ≥3 变体 · ≥2 MATCH 负对照」）

前缀 `r9s13_`，写在 `test_repros/round9/`，索引另立 `r9_s13_probe_index.json`（勿动 `r9_probe_index.json`
/ `r9_quote_index.json` / 在飞工单的 `r9a1_*`）。

必须复现的**省略形**（当前应读 1/2 或更低，落地后转 2/2）：

1. `r9s13_01_subscr_value_only` — `t['k'] = [1 if c else 0]`（LHS `LOAD_FAST+LOAD_CONST+STORE_SUBSCR` 被丢，值段裸发射）＝`build_current_period_df` 形
   ※ 形状已由 `r9q_01` 复现（红）；本臂的价值在**变体深度**，不得原样重造，须带 #7/#8 的长值段或跨块续体
2. `r9s13_02_nested_subscr_ternary` — `d[a][b] = [x if y else z]`；`r9q_18` 已复现该形（红），本臂只补**它没有的变体**（如三元两侧均为下标、或嵌套三层），不得重造同形臂
3. `r9s13_03_fstring_subscr_call` — `log.info(f'…{a[:3] in ("688","689")}…')` 内嵌成员测试 ＝ `option_order` 形（父调用消失）
4. `r9s13_04_slice_contains_two_tuples` — 同函数内两个 `x[:3] in (…)` 测试，常量元组**不同**（`('300','688','689')` 与 `('688','689')`）＝`matcher.match` 形
5. `r9s13_05_kwcall_embedded_ternary` — `f(name=a if c else b, other=d if e else g)`（kwargs + 三元）＝ del 段含 `KW_NAMES/CALL`
6. `r9s13_06_boolop_leg_in_test` — `if a and b and c:` 三条同目标假边只留两条
7. `r9s13_07_stmt_long_value_span` — 语句值段 >3 指令（多层属性/算术）但存储段存在 → 现计数门误判
8. `r9s13_08_subscr_across_blockedge` — LHS 的容器/下标装载与被 `POP_JUMP` 截断的表达式续体同块
9. `r9s13_09_subscr_in_for_body` — 循环体内 `d[k] = [...]`，验证修复不只在顶层有效
10. `r9s13_10_comprehension_dump` — genexpr/comprehension 内的省略形（第二波，若 #14 后仍红则计入）

**已常驻的负对照**（今日即读 2/2，修复后必须仍 2/2，直接复用、不必重写）：
`r9q_19_subscript_listcomp_assign`、`r9q_22_fstring_subscript_assign`（同为下标赋值族但当前正确，
是防"过度重建"的正面夹钳），`r9q_16_boolop_elif_and_leg`（boolop 成员腿当前正确），
`r9q_07_else_arm_pure_none_cond_false_edge`（G7 侧的臂体语句，防止本票把语句当省略吞掉）。

**变形牙**（必须做，否则臂不成立）：把新判据 stub 成恒不成立 → `r9s13_01/04/06` 必须转红；
把新判据放宽为"凡有 STORE_SUBSCR 即重建" → `r9q_19/22` 或 `r9q_07` 必须转红。
两侧都要红过，才证明判据既必要又不越界（deform 要打在守卫本体，不是打在它的打印标签上）。
