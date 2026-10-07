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

1. **切片/下标操作数被吞**（P0）：`BUILD_SLICE` + `BINARY_SUBSCR` + `CONTAINS_OP` 一串整体消失。
   宿主即 Round 9 记名的 `_split_subscr_operands` / `_build_effective_stmts`，
   并由**明令禁止的 `MIN_INSTRS_FOR_SUBSCR_ASSIGN` 计数门控**放行——
   `rules.md §2` 禁硬编码计数上限，本案（10 条语句被整条丢掉）就是该门控的代价。
   **要求**：该常量在**当前 HEAD** 是 1 处定义 + **6 处使用**（Round 9 记的行号已被 B124/B125 落地推移，
   以下为 `git show HEAD:` 复测）：定义 `:27`；
   使用 `_split_subscr_operands:2863`、`_build_effective_stmts:3535`、
   `_generate_block_statements_body:52856 / 53079 / 53205`、`_generate_stmts_from_instrs:56805`
   （4 个宿主方法、6 个调用点）。**一次改全**，不得只改一处（改一处＝部分修，
   且同一决策被复制进 4 个方法本身违反「一处决策，复用它」）。
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
