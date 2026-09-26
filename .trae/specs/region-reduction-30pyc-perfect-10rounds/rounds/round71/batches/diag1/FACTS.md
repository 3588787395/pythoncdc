# FACTS.md — Round 71 diag1：102 支 "Different control flow" 诊断事实

工作区 `D:/Temp/opencode/r71gate/diag1`；被测 repo 只读 `F:/Downloads/pythoncdc-main`
（HEAD `a31d3f79`，R70 落地基线 `b21c5c61`）。本文件只记**实测事实**，不含 patch，
`specs/` 保持为空。

---

## 1. 范围与判据

- **总体**：`filecat.json` → **50 个 .pyc、102 个 `Different control flow` 单元**
  （另有 `Different bytecode` / `Extra bytecode`，不在本诊断范围）。
- **A 组**（14 支 pyc，逐单元 verdict）：`a_units.json` 中 **38 个非 Equal 单元**。
- **B 组**：`b_jobs.json` 22 条（裸名有歧义，**权威单元全名以 `a_units.json` 的
  `<module>.X.Y` 为准**）。
- **mandated 尺**：`scripts/pyc_verify.py single <pyc> --source <ok.py>`（3.11 解释器）。
  例：`bar.pyc` → `status=failure units=82/85 success_rate=96.47%`。
- **官方尺 h62** 与 mandated 尺对「结构错误但官方 ok」的单元存在判据差异 → 记为影响面注记，
  不阻塞本诊断。
- **原始 .py 源码不存在**：site-packages 内除 `*OK.py` / `*_decompiled*` 外 0 支 `.py`；
  `*OK.py` 是反编译产物，共 1408 个。**族归类一律基于 orig pyc vs `*OK.py` 重编译产物的字节级对齐 diff**。

---

## 2. 族聚类（102 / 102 全覆盖）

工具：`t1all.py`（对齐首编辑 + hints，`t1all.out.txt`）、`cluster.py`（机械族规则，`cluster.out.txt`）。
规则**完全确定性**、可复跑：

| 族 | 规则 | 单元数 |
|----|------|-------:|
| **F-ABSORB** | 首编辑处跳转落点的指令不同，或指令条数改变 → 兄弟区域被吞 / 共享尾被错误挂载 | **68** |
| **F-PAD** | 跳转落点指令相同且条数相同，仅位置移位（NOP / EXTENDED_ARG / LOAD_CONST None 等填充物） | **17** |
| **F-META** | 指令流与异常表**全同**，仅嵌套 code-object / 行号不同（CF verdict 属伪影） | **5** |
| **F-OTHER** | 首编辑无法由以上规则解释，需人工读 | **4** |
| **F-POLARITY** | `POP_JUMP_*_IF_FALSE` ↔ `POP_JUMP_*_IF_TRUE` 极性翻转 | **3** |
| **F-EXCTABLE** | **指令流全同、异常表不同** | **2** |
| **F-TERNARY** | `JUMP_FORWARD` ↔ `RETURN_VALUE`（条件表达式被降级/升格） | **2** |
| **F-ASSERT** | `LOAD_ASSERTION_ERROR` 条数不同 | **1** |

F-ABSORB 内部再分（`cluster.out.txt` reason 字段）：

- **27 支**：跳转落点是**不同指令**（纯结构吸收/错入）——最"结构性"的一批。
- **41 支**：落点指令相同但**条数改变**（产物多发/少发语句）。

按文件分布（前 8）：`trade_live_broker.pyc` 10、`quote.pyc` 8(+2 OTHER/+1 POLARITY)、
`klinedata.pyc` 5、`real_quote.pyc` 4、`order_api.pyc` 3、`finance.pyc` 3、
`trade_info_utils.pyc` 5(2 ABSORB+2 PAD+1 META)、`exception.pyc` 3 PAD。

> 聚类是**诊断分组**，不是判据；判据提案见 §5（均为同层次结构身份，不含阈值）。

---

## 3. 根因（文件:行 + 实测证据）

### 3.1 F-THENOVER / F-ABSORB-结构（68 支主族）

**现象**：`if/elif/else` 或循环尾之后的**兄弟区域**被吸收进当前分支臂 → 跳转落点从
近端 merge 变成远端 end。

**实测**（`t1gap.out.txt`，A=orig，B=product）：

| 单元 | 首分歧 | A 落点内容 | B 落点 |
|------|--------|-----------|--------|
| `quotation.get_trend` | jump 206→220 | 后续语句 | 跨过整段 |
| `klinedata.get_history_common` | jump 446→610 (+164) | `LOAD_FAST is_dict` 守卫整段 | `LOAD_FAST fields` |
| `klinedata.get_kline_by_count_new` | 1200→1264 (+64) | `need_exrights` 整块 | `for` 循环头 |
| `bar._history_bars` | 140→304 (+164) | `ExecutionContext.phase` 守卫 | 后续调用 |
| `trade_info_utils.trade_operation` | 1000→1042 (+42) | `write_info.append(items)` | 循环回边 |
| `trade_info_utils.get_trade_status` | 810→786 | — | — |
| `finance.get_fields` | 740→742，n 177/178 | 共享尾 | EXTENDED_ARG 远跳 |
| `finance.get_financial_and_growth_factors` / `_pit_mode` | 114→118，`LOAD_CONST` vs `LOAD_GLOBAL` | and 链共享 else 挂到**内层 if** | |
| `strategy.tick_worker_thread` | 568→820 | | |
| `oauth2.post` / `HSIDOAuthCallbackHandler.post` / `OAuthCallbackHandler.post` | 638→642 / 726→730 | 相邻 return-None 块 | |
| `flytools.set_userid_containerid_dict` | 310→314 | | |
| `trade_info_utils.query_trade_strategy_info` / `query_strategy_id` | 614→618 / 644→648 | | |

**根因行号**（`core/cfg/region_ast_generator.py`，调用栈实证，`regdump.py` / `sys.settrace`）：

- `_process_if_blocks`（def `region_ast_generator.py:21468`）在**循环/分支帧内**认领"未归属的顶层区域"，
  **guard 在 `region_ast_generator.py:22445-22450`**，现有 5 条里第 (5) 条
  （`merge_block is None and exit is None`）**故意挡住**了 `quotation::get_trend`
  这类区域（注释 22420-22421 自己记录了这个反例，理由是 canary 逐字节要求）。
- 认领发生在 `region_ast_generator.py:22451-22465`，随后
  `_generate_region`（def `:3157`，`:3182` 调 `_generate_loop`）→
  `_generate_loop`（def `:4120`，`:4403` 调 `_loop_generate_for`）→
  `_loop_generate_for`（def `:4427`，`:4897` 调 `_if_generate_branch_stmts`，循环
  `else_blocks`/尾生成）→ `_if_generate_branch_stmts`（def `:24126`，`:24130` 调
  `_process_if_blocks`）→ `_generate_region` (`:22454`) → 生成嵌套 `IfRegion`。
- **analyzer 侧无过错**：t01 探针（`regdump.py`）得到 `IfRegion@0 (merge=196)`、
  `IfRegion@196 (merge=210)`、`Region@210` 三个 `parent=None` 的顶层区域——
  **树是对的，是 generator 发射层级错了**。
- 同型参考 guard 已存在：`ra-gen:21694-21704`（for_iter_setup 的
  `_fis_is_ancestor_merge`）、`ra-gen:21745-21753`（隐式 `return None`）。

### 3.2 F-EXCTABLE（2 支：`base.SplitOrder.parse_time_info`、`IQDataEntry.get_instance`）

**现象**：**指令流 144/144 全同**，异常表 `66..118` → `66..156`、`264..316` → `264..354`。

**根因（已闭环到行，`sys.settrace` 实证）**：

1. `TryExceptRegion.has_else=True`，`else_blocks=[114,118,148,150]`，
   探针（`regdump.py`）显示 `_generate_try` 返回 `keys=['body','handlers','type'] n_orelse=0`，
   **else 语句已经被塞进 `body`**（`bodylen=2`）。
2. `_generate_try_body`（定义 `region_ast_generator.py:24173`，调用点 **`:26152`**）
   在返回时把 **else 块也标成已生成** —— 实测：
   ```
   ('AFTER_BODY', 114, True) ('AFTER_BODY', 118, True)
   ('AFTER_BODY', 148, True) ('AFTER_BODY', 150, True)
   ```
3. 于是 orelse 门 `region_ast_generator.py:26587`
   （`if region.else_blocks and region.has_else and not _try_body_terminates_abnormally`）
   虽然**触达 2 次**，但循环 `:26615-26616`（`eb in self.generated_blocks → continue`）
   **8 次全部 `continue`**；`:26626 / :26639 / :26696` 从未执行。
4. `:27010 if orelse_stmts:` 触达但 `:27011` 未执行 → `try_ast['orelse']` 永远缺键。
5. 重编译后 try 体覆盖了 else 的指令 → 异常表 `end` 被撑大 → **ET 差异、指令全同**。

> 副发现（artifact，非根因）：`RegionASTGenerator.analyze()` 非幂等——二次调用时
> `region_analyzer.py:8627 _identify_try_except_regions` 抛
> `UnboundLocalError: cannot access local variable 'region'`。

### 3.3 F-ORELSE / F-BOOLOP（and 链共享 else、极性）

- 和链共享 else 挂到**内层 if**：`finance.get_financial_and_growth_factors` /
  `get_financial_statements_pit_mode`（`114→118`，其余 168 指令全同）。
  `region_analyzer.py:15849 _identify_conditional_regions`、
  `:23223 _identify_boolop_regions`、
  `:26566 _try_unify_mixed_boolop_chain`（R67 混合链统一）。
- **极性错误（已定位到辅助函数）**：`future_contract_info.info_conbine`
  原条件 `X or not S`（`A@66 IF_TRUE→94`(raise)，`B@66 IF_TRUE→124`）被还原成
  `not(X or S)`。整链 negation 由 **`region_ast_generator.py:46 _negate_expr`**
  （注释自承"用 not() 包裹而非反转运算符"）施加于**整条 BoolOp**，
  调用点 `:11992 _negate_expr(_boolop_expr)`；analyzer 侧元数据来源
  `region_analyzer.py:16874-16877 _main_inline_boolop_chain = {..., 'negate': True}`、
  `:26198`（`not (A or B ...)` 的 De Morgan 展开）。
  **缺陷**：链中**每个操作数自己的跳转极性**（`IF_TRUE→arm` vs `IF_TRUE→skip`）
  没有分别落到该操作数上，而是被一次性 `not` 到整条链外层。
- 混合链：`bar._history_bars`（`A and B or C` → `if A: if B or C:`，`140→304`）。
- F-POLARITY 3 支（`api_base.get_history`、`quote.check_industry_code`、
  `trade_live_broker._sync_worker`）是同一类极性判据的纯翻转形态。

### 3.4 F-ASSERT（1 支：`base.OverNightOrder.__init__`）— 根因已闭环到行

- 现象：`LOAD_ASSERTION_ERROR` **2 → 0**，`n 188/165`，产物形如
  `if not 0 <= h < 24: pass` + `raise AssertionError`（`synth/t24` 同形）。
- **analyzer 探针读数**（`_identify_assert_regions` wrap，t24）：
  - `regions = Counter({'IfRegion': 4, 'TernaryRegion': 2, 'TryExceptRegion': 1, 'Region': 1})`
    —— **没有 `AssertRegion`**；`_identify_assert_regions()` 返回 `[]`。
  - 9 个候选条件块全部走完 `_reach_assertion_error_block` 后仍 `is_assert=False`。
- **精确阻塞点**（CFG 逐块读数）：
  ```
  block 382  ops [POP_TOP]                       succ [384, 448] csucc [384]  reach=False
  block 384  ops [LOAD_ASSERTION_ERROR, RAISE_VARARGS]  succ [448]  csucc []  reach=True
  ```
  block 382 是链式比较 `0 <= h < 24` 的失败中转块，它的**真实 fall-through 只有 384**，
  第二个 successor **448 是 try 的异常处理入口 `PUSH_EXC_INFO`**。
  `region_analyzer.py:15259-15261`：
  ```python
  succs = list(cur.successors)
  if len(succs) != 1:
      return False
  ```
  **没有排除"指向 handler 入口的异常边"** → 在 try 区域内必然返回 `False`。
  同型守卫在 `_find_assertion_error_block` `region_analyzer.py:15303-15305`
  （返回 `None`）、`_reaches_block_via_fallthrough` `:15310` 起同样存在。
- 连锁后果：`is_assert=False` → `_identify_assert_regions`（def `region_analyzer.py:14708`）
  不产生 AssertRegion → 条件块退化为普通 `IfRegion`（`region_ast_generator.py:11711`/
  `:17691`）→ `LAE; RAISE_VARARGS` 块被当普通 raise 重建为 `raise AssertionError` →
  重编译 `LOAD_GLOBAL AssertionError` ≠ `LOAD_ASSERTION_ERROR`，且跳转目标改变。
- **触发条件（负对照 + CFG 双重钉死）**：同一形状的 A/B 读数——
  ```
  synth/t15（assert 在 try 外，OverNightOrder.__init__）
      regions {'AssertRegion': 2, 'Region': 5}
      pred 28 succ [32] reach=True      pred 62 succ [66] reach=True
  synth/t24（assert 在 try 内，init_time）
      regions {'IfRegion': 4, 'TernaryRegion': 2, 'TryExceptRegion': 1, 'Region': 1}
      pred 380 succ [384, 448] reach=False   pred 414 succ [418, 448] reach=False
  ```
  唯一差别就是 handler 边 `448`（try 入口 `PUSH_EXC_INFO`）是否出现在中转块的
  `successors` 里。
- 相关但**非本根因**的既有注释：`region_ast_generator.py:48050-48063`
  （assert→`raise AssertionError` 的字节码不一致，代码已把 `RAISE_VARARGS` 一并交给
  `expr_reconstructor` 处理）；`:49603 _build_raise_stmt_from_instrs` /
  `:49551 _reconstruct_raise_exc` 均能正确返回 `Assert`——**本轮实测这两个函数
  在 t24 上根本没被调用**（wrap 读数：仅 `_build_statement` 被调 3 次），
  因为上游压根没生成 AssertRegion。

### 3.5 F-TERNARY（2 支：`bar.BarData.limit_up` / `limit_down`）

- `A: 44 JUMP_FORWARD to 68` ↔ `B: 44 RETURN_VALUE`，`EXC 3/4`，`n 32/32`。
- 形状 = **try 内 `return <ternary>`**；`synth/t08_ternary_return_in_try.py` 复现，
  `synth/t21`（顶层 ternary，无 try）→ success。

### 3.6 F-FINALLYTAIL（`synth/t06`、`t07`；`ptradeAccount.*` 两支）

- `A: 548 JUMP_FORWARD to 620` ↔ `B: 548 LOAD_CONST None`（`n 111/110`、`127/126`）——
  finally/try 尾的正常路径副本丢失。
- 候选行：`region_ast_generator.py:25403 _find_finally_normal_copy_blocks`。

### 3.7 F-CROSS（`trade_info_utils.trade_operation`，循环尾语句越界）

- 循环体内 if 分支的**后续共享语句**被吸进分支 → `1000→1042`，且 `n` 相同（纯错位）。
- 与 §3.1 同一 guard（`ra-gen:22445-22450`）作用于循环尾；`synth/t22` 复现，
  `synth/t18`（单层 if + 循环尾）→ success（必须 if 内再串多个 if/continue）。

---

## 4. 影响面

- **102 / 102 CF 单元**已逐支跑 `t1all.py` + `cluster.py`（见 §2）。
- 直接落在 §3 根因上的：
  - F-ABSORB 68（含 F-THENOVER / F-ORELSE 共享尾 / F-CROSS）
  - F-PAD 17（填充物导致的落点位移：NOP / EXTENDED_ARG / LOAD_CONST None；
    其中与 §3.1 分支帧层级错误同源的与 F-ABSORB 一起计）
  - F-POLARITY 3 → §3.3 极性族
  - F-EXCTABLE 2 → §3.2
  - F-TERNARY 2 → §3.5
  - F-ASSERT 1 → §3.4
  - **F-OTHER 4 尚需人工读**：`quote.load_get_price`（`POP_JUMP_IF_FALSE` → `POP_TOP`，
    疑似条件被丢弃）、`quote.get_individual_data`（→ `EXTENDED_ARG`）、
    `wizard.init_stock_pool_filter` / `trade_live_broker._process_cancel_order`
    （`NOP` ↔ 实值指令，疑似填充物）。
- **F-META 5 支不是控制流缺陷**：指令流与异常表全同，仅嵌套 code-object 行号不同
  （`wizard_quant_api.<genexpr>` ×2、`broker.get_open_orders.<listcomp>`、
  `trade_info_utils.kill_trade_process`、`load_daily.<module>`）→ **应归入 line/元数据类，
  不应记 `Different control flow`**；这是判据侧的记账问题。
- **官方尺 h62 vs mandated 尺**：A 组中官方标 `ok` 的文件仍出现 CF 失败
  （如 `finance.pyc official=24/None` 但 3 个 CF 单元）→ 影响面注记，未解释，不阻塞。

---

## 5. 三要素判据提案

每条 = **(1) 同层次结构身份** + **(2) 检查位置（文件:行）** + **(3) 明确不读的东西**。
所有提案**不读**：函数名、文件名、绝对偏移、阈值启发、名字白名单、`self` 新增状态、
跨层 `region.entry in r.blocks` 型模式。

### P1 — F-THENOVER（兄弟区域不得在分支帧内认领）

1. **结构身份**：待认领区域的 `entry` 等于**发起当前分支帧的祖先 IfRegion / LoopRegion 的
   `merge_block`（或 `exit`）** ⇒ 它是本 if 的**兄弟语句**，不是它的分支内容。
   （t01 实测：`IfRegion@0.merge_block == 196 == IfRegion@196.entry`。）
2. **检查位置**：`core/cfg/region_ast_generator.py:22445-22450` 的 defer guard，
   与既有 `:21694-21704 _fis_is_ancestor_merge`、`:21745-21753` 同型，命中时
   `continue`（不认领、不写 `generated_blocks`），交回顶层区域循环按既有次序发射恰好一次。
3. **不读**：offset 数值比较、块个数阈值、函数/文件名、`_current_loop` 之外的新 self 状态。

### P2 — F-EXCTABLE（try 的 else 块不得被 try 体消费）

1. **结构身份**：当 `TryExceptRegion.has_else` 且 try 体不以
   Return/Break/Continue/Raise 异常终止时，在 `_generate_try_body` 返回的时刻必须满足
   **`region.else_blocks ∩ generated_blocks == ∅`**；orelse 门因此能取到全部 else 块，
   产出 `try_ast['orelse']`。
2. **检查位置**：`region_ast_generator.py:24173 _generate_try_body` 的块标记集合
   （调用点 `:26152`）与 orelse 门 `:26587` / skip `:26615-26616` / 落键 `:27010-27011`。
   判据的自检点就是 `:26615` 那句 `continue` 的**前置条件**。
3. **不读**：异常表 offset 区间数值、`eb.start_offset` 的具体值、try/except 名称。

### P3 — F-ASSERT（fall-through 追踪必须排除异常处理边）

1. **结构身份**：从条件块的失败出口沿 fall-through 链寻找
   `LOAD_ASSERTION_ERROR` 时，**指向某个 `TryExceptRegion` handler 入口的边
   不是控制流 fall-through 边，不计入「唯一后继」判定**。
   等价表述：`succ is a handler entry of an enclosing TryExceptRegion` ⇒ 从
   `len(succs)` 中剔除；剔除后恰为 1 才继续追踪。
   实测锚点：t24 `block 382 succ=[384, 448]`，其中 `448 = PUSH_EXC_INFO`（handler 入口），
   `block 384` 才含 `LOAD_ASSERTION_ERROR`。
2. **检查位置**：`region_analyzer.py:15259-15261`（`_reach_assertion_error_block`）、
   `:15303-15305`（`_find_assertion_error_block`）、`:15310` 起
   （`_reaches_block_via_fallthrough`）——三处同型守卫；
   上游 `:14708 _identify_assert_regions` / `:14877 is_assert`。
3. **不读**：异常表 `start/end/target` 数值、`depth<8` 之外的新阈值、
   block offset 数值、函数/文件名、`self` 新增状态。

### P4 — F-ORELSE / F-BOOLOP（布尔链极性按操作数分别重建）

1. **结构身份**：链中**每个条件块的出口跳转 opcode 极性**（`IF_TRUE→arm` vs
   `IF_TRUE→skip`）与该操作数在链中的位置一一对应；重建式 = `∧`/`∨` 按链 op，
   **每个操作数按自身极性**取 `not`（`X or not Y` 必须还是 `X or not Y`，
   不能变成 `not(X or Y)`）。
2. **检查位置**：`region_analyzer.py:16874-16877`（`{'op':'or','negate':True}` 元数据）、
   `:26198`（De Morgan 展开点）→ `region_ast_generator.py:46 _negate_expr`
   与 `:11992 _negate_expr(_boolop_expr)`：negation 必须下沉到**单个操作数**，
   而非施加于整条 BoolOp。
3. **不读**：跳转目标偏移的数值、块数/链长阈值、函数名、`self` 新增状态。

### P5 — F-TERNARY（条件表达式不得被降级为语句序列）

1. **结构身份**：原块在 `try` 异常表覆盖范围内且源形态是 `return <cond_expr>`；
   产物必须仍生成**表达式级** `Return(value=IfExp/BoolOp)`，重编译回
   `JUMP_FORWARD`（而非 `RETURN_VALUE` 提前返回）。
2. **检查位置**：`region_ast_generator.py:11711 _generate_if` /
   `:17691 _if_generate_normal` 与 `TernaryRegion` 发射路径
   （analyzer `region_analyzer.py:20352 _identify_ternary_regions`）。
3. **不读**：异常表区间数值、`depth>=1` 计数、函数名、阈值。

### P6 — F-FINALLYTAIL（finally 的正常路径副本必须保留）

1. **结构身份**：`TryFinallyRegion` 的 `finally` 存在**正常路径副本块**时，
   该副本块集必须与 handler 尾块集在 AST 中各发射一次，且**不互相吞并**。
2. **检查位置**：`region_ast_generator.py:25403 _find_finally_normal_copy_blocks`
   及其两处调用点。
3. **不读**：块 offset 数值、`n` 条数比较、函数名。

### P7 — F-CROSS（循环尾共享语句归属循环帧，不归属分支帧）

1. **结构身份**：语句块属于 LoopRegion 的 body/exit 链而非 IfRegion 的 then/else 集合
   ⇒ 分支帧不得认领。（与 P1 同一 guard 的循环侧形态。）
2. **检查位置**：`region_ast_generator.py:22445-22450` + `_generate_loop`（def `:4120`）/
   `_loop_generate_for`（def `:4427`，`:4897` 处生成循环 else/尾）。
3. **不读**：同 P1。

### P8 — F-PAD / F-POLARITY（填充物与极性不得改变结构落点）

1. **结构身份**：重编译产物与 orig 的**跳转落点必须落在同一条语句**（按
   `opname + arg` 身份比较，**不按 offset 数值**）；插入 `NOP/EXTENDED_ARG` 不得改变落点语句。
   极性则要求 `POP_JUMP_*_IF_X` 的 X 与 orig 一致。
2. **检查位置**：这两族是 §3.1/§3.3 的**下游症状**，修 P1/P4 即消；判据自检可放在
   `pyc_verify` 的对齐 diff 层（`scripts/pyc_verify.py` 的首分歧分类）。
3. **不读**：offset 数值、阈值、函数名。

### P9 — 记账修正（F-META 5 支）

指令流与异常表全同、仅嵌套 code-object 行号不同 ⇒ 不应记 `Different control flow`。
这是**判据侧分类**问题，不是生成器缺陷；建议归入 line/元数据类。

---

## 6. synth 复现集（≥10 支，已满足）

- 位置：`synth/`（`README.md` + `verify_readings.txt` + `mksynth.py`）。
- **14 / 30 复现**，mandated 尺全部 `status=failure`：
  t01, t02, t03, t05, t06, t07, t08, t12, t16, t22, t24, t25, t27, t29。
- **16 支负对照（success）**：t04, t09, t10, t11, t13, t14, t15, t17, t18, t19, t20,
  t21, t23, t26, t28, t30 —— 每支钉住一条**必要触发条件**（见 `synth/README.md`）。
- 关键形状结论（全部由"近失负对照 + 复现"成对确认）：
  - F-ASSERT 需要 **try 包裹**（t15 ✗ / t24 ✓）。
  - F-THENOVER 共享尾需要 **try/except 包裹**（t17/t28 ✗ / t29 ✓）。
  - F-EXCTABLE 需要 **try/except/else**（t20 顺序 try ✗ / t27 ✓）。
  - F-TERNARY 需要 **try 内的 return ternary**（t21 顶层 ✗ / t08 ✓）。
  - F-CROSS 需要 **循环内 if 串多层 if/continue**（t18 ✗ / t22 ✓）。
  - F-ADJRETURN 需要**兄弟分支各自 `return None`**（t19 ✗ / t25 ✓）。
  - 用户最高优先假设"多数失败是**嵌套 try-except**"——**已部分否定**：
    F-EXCTABLE 根因是 **try/except/else 的 else 被折进 try body**，与 try-in-try 无关；
    F-ASSERT 根因是 **try 的异常边污染了 fall-through 判据**，也与 try-in-try 无关；
    F-THENOVER 主族 68 支中多数 `nestA=0`。
    "try 包裹"确实**是 F-ASSERT/F-TERNARY 的必要条件**（t15 ✗→t24 ✓、t21 ✗→t08 ✓），
    但机制不是"嵌套 try"，而是**异常表/异常边的存在本身**。

---

## 7. fix1 优先级建议（1–3 族）

| 优先 | 族 | 理由 |
|-----:|----|------|
| **1** | **F-THENOVER（P1，含 F-CROSS P7）** | 影响面最大（F-ABSORB 68 + F-PAD 17 的主源）；根因已定位到**单一 guard** `region_ast_generator.py:22445-22450`，且同型 guard 已在 `:21694/:21745` 存在，风格一致。**风险**：该 guard 现有第 (5) 条是为 canary 逐字节而故意收窄的（注释 22422-22435），新判据必须逐字节自检 canary，否则会移开 canary sha。 |
| **2** | **F-EXCTABLE（P2）** | 证据最硬（指令 144/144 全同、异常表差、settrace 闭环到 `:26152→:26587→:26615→:27010`），改动面最小、可局部验证；但只覆盖 2 支单元。 |
| **3** | **F-ASSERT（P3）** | 根因闭环到**三处同型守卫的一句 `len(succs) != 1`**（`region_analyzer.py:15259-15261` 等），CFG 逐块读数证明失败仅因 try 的 handler 边污染；判据是纯结构身份（"该后继是不是 handler 入口"），t15/t24 负对照 + `_identify_assert_regions` 返回 `[]` 双重钉死；单元数 1 支、风险最低。若 fix1 要把 canary 风险降到最低，可与优先 1 对调。 |

备选（若 P1 因 canary 受阻）：**F-ORELSE/F-BOOLOP（P4）**——覆盖 F-POLARITY 3 +
F-ABSORB 中的 and/or 链共享尾与极性翻转，判据是"按操作数分别取极性"，同样干净。

---

## 8. 未决 / 阻塞

1. `wizard_quant_api.pyc :: calculate_di_genexpr`：`b_jobs` 裸名
   `CODE_MISSING A=False B=False`，须按 `a_units.json` 全名
   `<module>.get_DMI.calculate_di.<genexpr>` 处理（现归 F-META：指令全同）。
2. 官方尺 h62 对「结构错误但官方 ok」单元的判据差异未解释（影响面注记）。
3. `cfg.blocks` 是 **1-based 块序号**为 key 的 dict（`cfg.blocks[0]` → `KeyError`；
   `cfg.blocks[1]` 才是第一块；`for b in cfg.blocks` 得到 int）——探针必须用
   `cfg.get_blocks_in_order()` 或自行按 `b.start_offset` 建映射。
4. trace 探针两度失效：trace 函数内异常被静默吞掉；最终改用
   **wrap `_generate_try_body`** 的方式闭环（§3.2 的 AFTER_BODY 读数）。
5. `specs/` 保持为空（本诊断不出 patch）。
