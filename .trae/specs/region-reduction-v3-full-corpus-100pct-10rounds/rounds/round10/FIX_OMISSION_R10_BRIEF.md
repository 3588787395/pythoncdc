# Round 10 工单 #13（续）简报：省略族按语句级取证分档——`matcher` 一条语句即可翻正一个文件

取证口径同 `FIX_LANDING_R10_BRIEF.md` §开头（输入读盘、产物读盘上现字节、只读 stdlib、按完整 qualname 配对、
副本不唯一即**拒判**）。仪器：`D:/Temp/r9main/r10loss.py` → 原表 `D:/Temp/r9main/r10loss.txt`。
本节只列**多指令 hunk**（`orig+prod ≥ 4`），逐条给出被吞语句的原始指令串。

## 一、优先级（按「修好即翻正整文件」排）

| 优先 | 单元 | 文件读数 | 被吞内容（实测指令串，非猜测） | 判断 |
|---|---|---|---|---|
| **P0** | `matcher.<module>.DefaultMatcher.match` | **16/17（差 1）** | `orig[347:357]`＝10 条整体消失：`LOAD_FAST order / LOAD_ATTR asset / LOAD_ATTR symbol / LOAD_CONST None / LOAD_CONST 3 / BUILD_SLICE / BINARY_SUBSCR / LOAD_CONST ('688','689') / CONTAINS_OP / POP_JUMP_FORWARD_IF_FALSE` ⇒ 一条 **`order.asset.symbol[None:3] in ('688','689')`** 测试语句（切片下标 + 成员测试）被整条吞掉 | **单语句、单单元、单文件**：修好即整文件 OK。全文件仅这 1 个大 hunk（其余 24 处是小目标差） |
| **P1** | `realtime_event_source.<module>.RealtimeEventSource.clock_worker` | **12/13（差 1）** | 三处：① `orig[1179:1289]`＝**110 条压成 1 条 `JUMP_FORWARD`**——`if persist_flag is not False:` 的整个体（`IS_OP` 测试 + `set_trade_stop_status(self._engine.config.strategy.trade_id)` + `system_log…`）；② `orig[949:966]`＝17 条消失（`if holiday_not_do_before == '0': event_queue.put(dt, EventEnum.BEFORE_TRADING_START)`）；③ 那 17 条**在 prod[1264:1282] 以 18 条重新出现**＝被搬到循环尾之后（不是纯丢失）。另有 3 处 `IF_TRUE/JUMP_FORWARD` 目标差 | 一个单元内**同时**含「吞体」「搬块」「目标差」三形 ⇒ 三者都对才翻正；`IS_OP` 的 `is not` 测试作臂头是本案入口，先证 ① 再说 ②③ |
| **P2** | `api_base.<module>.get_history_df` | 27/28（差 1，但同文件另有 `#14` 面） | `orig[449:454]`＝`POP_JUMP_FORWARD_IF_TRUE / LOAD_FAST time_count / LOAD_CONST 1 / BINARY_OP -= / STORE_FAST time_count` 压成 `POP_JUMP_FORWARD_IF_FALSE`；`orig[514:515]` 反向摊成 9 条（`max_len_real_data = count` 一类） | §XVI 的新靶形（5→1 ∧ 1→9）。极性与省略是**同一处的两副面孔**：被吞的 `time_count -= 1` 使测试改写反形 |
| **P2** | `klinedata.<module>.kline_datetime_list` | 61/64 | `orig[158:163]` 与 `get_history_df` **逐条同形**（同一段 `time_count -= 1` + 测试算术） | 与上一条**同一根因**，两处独立文件 ⇒ 一条判据覆盖二单元（不是两个缺陷） |

## 二、机制归并（把 Round 9 的 4 类收成 3 条判据面）

1. **切片下标测试表达式被整条吞**（P0）：`BUILD_SLICE` + `BINARY_SUBSCR` + `CONTAINS_OP` 一串整体消失。

   **主代理自纠（本简报首版的机制归因被代码否证）**：我首版写「宿主即
   `MIN_INSTRS_FOR_SUBSCR_ASSIGN` 计数门控」——**不对**。`git show HEAD:` 读该常量两处使用：
   `_split_subscr_operands:2863`（`if len(expr_instrs) < MIN_…: return None`，其职责是把
   `value/container/index` 三段切开供**下标赋值**用）与 `_build_effective_stmts:3535`
   （`if instr.opname == 'STORE_SUBSCR' and len(expr_instrs) >= MIN_…`，R102 增广赋值委托路径）。
   两者都以 **`STORE_SUBSCR`** 为前提，而 P0 被吞的是
   `… symbol[None:3] in ('688','689')` 的**测试表达式**（`CONTAINS_OP` + `POP_JUMP_FORWARD_IF_FALSE`，
   全串无 `STORE_SUBSCR`）⇒ 该计数门控**不是 P0 的宿主**。
   这是本 campaign 第四次「简报锚点/机制错、靶面事实对」，事实部分（10 条指令、单 hunk、单文件差 1）不变。

   **给工程师的替代候选（须自行证实/否证，不得当结论用）**：表达式重建失败即静默丢整条语句——
   `Subscript(value=Attribute(order.asset.symbol), slice=Slice(None,3))` 套在
   `Compare(…, In)` 内，若重建器返回 `None`，其宿主语句分支是否**静默不发**？
   要求：用自有探针（导入 core、打点，跑完即撤）定位**实际丢弃点**，并检查该处是否属
   `rules.md` 禁的「静默豁免」（失败即丢而不留痕）。找到丢弃点才算命中，勿照我的候选写判据。

   **顺带项（与本条分开，不得并案）**：`MIN_INSTRS_FOR_SUBSCR_ASSIGN` 本身仍是
   `rules.md §2` 明令禁止的硬编码计数门控——当前 HEAD 实测 1 处定义（`:27`）+ **6 处使用**
   分布于 4 方法：`_split_subscr_operands:2863`、`_build_effective_stmts:3535`、
   `_generate_block_statements_body:52856 / 53079 / 53205`、`_generate_stmts_from_instrs:56805`。
   它的消除属**其自身能解释的那些单元**（如 `etf_purchase_redemption` 的属性链截断一类下标/切片形），
   若改须六处一次改全（改一处＝部分修，且同一决策被复制进 4 个方法本身违规）。
2. **`is not` / 极性测试作臂头时整个体被跳**（P1 ①）。判据须问块的事实：
   臂入口块末条是前向条件跳转、其**真/假**落点之一在循环区段内、且该区段块的回边存在 ⇒ 该体属臂，不属汇合。
   与 `FIX_WHILE_ELSE_TAIL_BRIEF.md` §七 订正后的 `region_analyzer.py:4810` 认领面**同源不同层**：
   那层是「汇合块被认成 else」，这里是「臂体被跳」——不得并案，但两处必须同向复验。
3. **体尾语句被搬到循环之后**（P1 ②③）：内容没丢，位置错 ⇒ 属 `#14` 的落点/排位面，
   本票只主张「不是省略」，禁止把 17 条搬位记成 17 条省略。

## 三、禁止项与验收

- 禁以指令条数/长度/深度决定丢不丢（P0 的病根正是条数门控）；禁名特判；禁 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`。
- 禁「少发射换全绿」：P1 若以「不发 `if persist_flag is not False:` 的体」让读数变好而体仍缺，判 FAIL。
- 先臂后码：`r10ls_` 前缀，≥10 复现、深度 ≥3（裸语句 / 循环内 / try 内 + 类方法语境），
  负对照 ≥2（含一条 `x[1:3] in (...)` 已 OK 的形与一条 `is not` 已 OK 的形）。
  红→绿才算命中；红→红＝该轴被否证。
- 回报**边做边写**（`rounds/round10/FIX_OMISSION_R10.md`），零翻转按 sha256 逐字节回滚。
- 排序前置：#16 在飞（改成员关系）→ 落地后本表所有 seq 下标须用 `r10loss.py` 重取；
  与 #14 A 档**同轮不同判据面**，若同票派发须按 `tasks.md §10.0` 的串行门禁执行（402 gate 唯一）。

## 八、共要件与派切分（Round 10 裁定后追加，见 `ADJUDICATION_R10_B126_REVERTED.md`）

`trade_live_broker` 的 `_process_order` / `_process_cancel_order` / `_trade_status_handle` 三条 LOSS_COLLAPSE 单元
**同时需要** #16 的结构改判（`while True:` + 体内 `if`）与本案的省略补回才会翻正。
#16 的补丁已按零翻转纪律回滚，但**已验证可用**，保存在：

- 补丁 `D:/Temp/r9main/RAVED_R10_B126.patch`（288 行，标记 `[r10-b126-else-backedge-refute]`／
  `[r10-b126-whiletrue-ifjoin]`／`[r10-b126-loopheader-tail-confluence]`）
- 回滚前整文件字节 `D:/Temp/r9main/WIP_R10_B126_analyzer.py`（sha256 `515da6c6e1a21f76…`）
- 其自有电池复测读数：`r9w16_*` 18 臂 **26/37 → 33/37，BROKE=0**（主代理自有复验，非工程师自述）

⇒ **谁接 `trade_live_broker` 那三条，谁必须先应用该补丁**，且应用后先复跑 `r9w16_*` 达到
units ≥ 33/37  ∧ BROKE=0 再作业；翻正按逐单元名单记，**两票共担，禁止任一票单独记功**。

**派切分建议（因两次截断的教训）**：本案首刀只取 **P0 一条**——
`matcher.DefaultMatcher.match` 中被吞的整条 `order.asset.symbol[None:3] in ('688','689')` 测试语句
（该文件只差这 1 个单元，无共要件，翻正即整文件 OK）。
`clock_worker`（一形三态）、`_process_order`/`_process_cancel_order`（须共要件）各自另立次刀，
不要在一票里同吃三种机制——Round 10 的两次 150 回合截断都发生在「一票多机制」上。

## 九、新工单候选的**宿主级**线索：函数内 `import` 的发射（`_on_publish_after_trading_end`）

事实（`git show HEAD:` 副本实测，`region_ast_generator.py`）：`IMPORT_NAME` 的协议走查被**复制进至少 4 条发射路径**
（`:590`、`:922`、`:1123`、`:1223`），且**走查窗宽度不一致**：

```
:590   for _s in range(_scan_start, min(_scan_start + 3, len(block.instructions)))        ← 硬编码 3
:922   for _s in range(_scan_start, min(_scan_start + 3, len(entry_block.instructions)))  ← 硬编码 3
:1223  for _es in range(_ei_idx + 1, min(_ei_idx + 4, len(entry_block.instructions)))     ← 硬编码 4
:1123  （委托 _process_instruction，另立一套 _import_pending_store 状态机）
```

两处违例同时成立：① `rules.md §2` 禁**硬编码指令条数**——这里直接写死「往后看 3 条／4 条」；
② 「一处决策、多处复用」——同一协议判据被抄成 4 份且**抄得不一样宽**。
后果面：3.11 的 `from X import Y` 在语句前部可能夹 `LOAD_CONST/PUSH_NULL` 之外的指令
（如注解存储、`COPY`、异常边序），窗口一过短就识别不到 `IMPORT_FROM`，
整条 `IMPORT_NAME + IMPORT_FROM` 对被丢（正是本单元实测的 `delete orig[482:484]`）。

**给工程师的要求**（先证后改，勿照抄我的推断）：
1. 用自有探针在 HEAD 字节上跑 `_on_publish_after_trading_end` 所在块，
   **打印四条路径中实际命中哪一条**、以及该块内 `IMPORT_NAME` 之后到 `IMPORT_FROM` 的实际距离；
   距离 > 3 即坐实窗口过短；否则本候选被否证，须继续找真宿主（不许强行改窗口凑绿）。
2. 修法是**一条协议走查、四处复用**（同一函数/同一谓词），窗口边界必须由**边/opcode 事实**决定
   （例如「直到遇到 `IMPORT_FROM` 或遇到块内下一条语句边界/终止跳转为止」），
   不得把 3 改成更大的常数——那仍是硬编码，只是宽一点。
3. 负对照必须包含：模块级 `import`、`from X import *`、`try` 内 `from X import Y`、
   以及 `entry_block` 与 `block` 两条不同路径的样本；四条路径在改后**共用同一谓词**（grep 证：
   `IMPORT_FROM` 的走查循环在文件里只剩一处实现被调用）。

## 十、一次**不成立**的取证尝试（记下来以免后来者重复走）

主代理试过用「块是某区域成员、但不是任何区域的 `condition_block`」的计数，
把 `matcher` 的丢弃面推广到 `order_api.option_order` / `future_order`（#22）。
在 HEAD 上实跑（`core.cfg.build_cfg` + `CFGRegionAnalyzer.analyze()`）得
`option_order: blocks=17 regions=12 cond_heads=5 member-but-not-condition=12`、
`future_order: blocks=19 regions=18 cond_heads=6 member-but-not-condition=13`。

⇒ **该度量无判别力**：`then_blocks / else_blocks / body_blocks` 里的成员**本来就不该是 condition**，
所以 12/13 这个数是正常值，不是吞并证据。把它当信号会派出一张按假指标写的票。

**正确的问法**（#22 的工程师须照此自证，勿用我的计数）：
对具体被吞的块（`option_order` 的 `strategy_log.info('生成订单…'.format(…))` 所在块、
`order_api` 两单元各自的 and/or 三元操作数串），问三件事——
① 该块是否在某区域的 `condition_block`／臂入口／`merge_block` 任一身份上出现；
② 若出现为「臂列表成员」，发射端是否**访问**了它（AST 里找它对应的语句）；
③ 未访问时，是哪个循环/递归分支跳过了它（给出 `文件:函数:行` 与误发条件的白名单事实表述）。
`matcher` 的诊断（`DIAG_B128_MATCHER_DROPSITE.md` Q0）已经示范了这个正确形状：
被吞块 `blk#47@2164` **不是任何区域的 condition**、又确在 `IF_ELIF_CHAIN` 的成员表内——
关键在于它还**没在产物 AST 里出现**（②），两者合起来才是吞并证据，单看①不是。
