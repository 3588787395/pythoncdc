# Round 70 · diag5 · FACTS（实时落盘）

仓库 HEAD = 5647e97b（R69 落地），worktree 只读；GATE=D:/Temp/opencode/r70gate/center（h62/closeout69/sstrict67
的 ROOT 固定指向 center，臂名一律带 `r70diag5` 前缀避免与 diag1-4 撞车）。

## Step 0 · baseline replay（arm=landed，2026-09-26）

官方尺 `h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl`：

| pyc | matched | mism（name, orig, decomp, jumpdiff, truediff） |
|---|---|---|
| realtime_event_source.pyc | **11/12** | `clock_worker` 1275 → 1286（jump=10, true=481） |
| api_base.pyc | **24/25** | `get_history_df` 1742 → 1742（jump=11, true=89，计数相等、纯跳转差） |

金丝雀 `--list=canary.txt`：quotation **143/143**、market_time **10/10**、IQCommon datetime_func **26/26**、
IQData datetime_func **25/25**、mism 全空。

45 项电池 `closeout69.py battery landed`（清单含 round63..69 见证共 82 支）：
- 45 项子集（round63..67）= **182/200、缺陷 18、ERR 0、worse-than-landed=0**
- 全量 82 项（closeout69 口径）= **318/356、缺陷 37、ERR 0**

严格尺 `sstrict67.py build_landed targets.txt`：
- realtime_event_source **11/12 missing=0 extra=0**，唯一缺陷 `clock_worker [seq_len] orig=1276 decomp=1287`
- api_base **26/27 missing=0 extra=0**，唯一缺陷 `get_history_df [seq_diff] #419 orig=('<JUMP>','POP_JUMP_IF_TRUE') decomp=('<JUMP>','POP_JUMP_IF_FALSE')`
- STRICT TOTAL 37/39、defects=2

严格尺 canary：quotation 148/150（change_his_to_forward #250、get_trend #10）、market_time 10/10、
datetime_func 26/26 + 25/25 ⇒ 209/211、defects=2。

**与 targets.md 逐字段比对：全部相同（11/12、24/25、严格 11/12 与 26/27、缺陷明细一致、电池 182/200 与 318/356）。
唯一措辞差：官方尺 orig/decomp 打印为 1275→1286（严格尺为 1276→1287），差 1 属两尺计数口径（严格尺多计
一条），过冲量同为 11。** ⇒ 无更正。

## Step 1 · hunk tables（nested_diff.py，按 code-object 全路径配对）

### realtime_event_source.pyc
`python -X utf8 nested_diff.py <pyc> <OK.py>` ⇒ **TOTAL differing: 1 of 13**

| code object | orig | decomp | 归一化 hunk | 判定 |
|---|---|---|---|---|
| `/RealtimeEventSource#20/clock_worker#5` | 1442 | 1458 | **14** | **真缺陷**（其余 12 个 code object 逐指令相同） |

14 个 hunk（原始口径）：**9 条计数伪影 + 5 条真差异**
- 伪影 9 条（内容全为 `NOP` / `EXTENDED_ARG` / `JUMP_FORWARD` 的单点插入或删除，
  指令计数：`NOP`×1、`EXTENDED_ARG`×7（插入 5 / 删除 2）、`JUMP_FORWARD`×4，其中 3 处两种同 hunk）：
  `insert[768]`、`delete[876]`、`insert[913]`、`insert[945]`、`insert[954]`、`insert[984]`、
  `insert[1039]`、`insert[1114]`、`delete[1131]`；
- `delete orig[959:976]` = `if holiday_not_do_before == '0': self.event_queue.put((dt, BEFORE_TRADING_START)); self.before_trading_date = now_date`（17 条，L442–449）⇒ 位移；
- `replace orig[1097:1110]` = `self.event_queue.put((dt, PRE_BEFORE_TRADING_START))` + `self.pre_before_trading_date = now_date`（13 条 → 2 条 JUMP）⇒ **真·缺语句**；
- `delete orig[1192:1304]`（112 条 `persist_flag is not False` → `set_trade_stop_status` / `system_log.error` 块）+ `insert orig[1408:1408] decomp[1274:1409]`（135 条 `if before_trading_date == initial_trading_date` 头）⇒ 顺序颠倒；
- `replace orig[1411:1413] return None → decomp[1412:1429]` = holiday 块被排到 `return None` 之后（产品 L314 起）。

严格尺（NOISE= NOP/CACHE/PREALLOC/EXTENDED_ARG 过滤）：**orig=1276 decomp=1287 Δ=+11**；
mdiff 归一化 token 计数：**EXTRA Σ=+23、MISSING Σ=−12、净 +11**。
- MISSING(12 条)：`put((dt, EventEnum.PRE_BEFORE_TRADING_START))` 9 条 + `self.pre_before_trading_date = now_date` 3 条。
- EXTRA(23 条)：重复 `check_trading_time(...)` 调用 ≈14、重复 `self.before_trading_date == self.initial_trading_date` 比较 ≈6、`<JUMP> JUMP` ×4、`<JUMP> POP_JUMP_IF_FALSE` ×2。

### api_base.pyc
`nested_diff` ⇒ **TOTAL differing: 1 of 28**

| code object | orig | decomp | 归一化 hunk | 判定 |
|---|---|---|---|---|
| `/get_history_df#26` | 1900 | 1900 | **4** | **真缺陷**（计数相等、纯位移+极性） |

4 个 hunk = **同一 pattern 的 2 份拷贝**（`time_count` 与 `max_len_real_data` 各一份）：
- `replace orig[457:462] = POP_JUMP_FORWARD_IF_TRUE + time_count -= 1` → `decomp[457:458] = POP_JUMP_FORWARD_IF_FALSE`；
- `replace orig[522:527] = POP_JUMP_FORWARD_IF_TRUE + max_len_real_data -= 1` → `decomp[518:519] = POP_JUMP_FORWARD_IF_FALSE`；
- `insert decomp[526:530]` = 迟到的 `max_len_real_data -= 1`；`insert decomp[548:552]` = 迟到的 `time_count -= 1`。
⇒ **极性反（IF_TRUE↔IF_FALSE）+ 递减语句被从条件块紧随位置挪到后面的汇合点**。
严格尺 orig=1742 decomp=1742（Δ=0），首差 `seq_diff #419`；官方尺 jump=11、true=89。

## Step 2 · 根因（全部为生成器/分析器实测，非读码推断）

新增探针（均在 `F:/Downloads/pythoncdc-main` 只读运行，输出落 `dump/` 或 stdout）：
`probe_break.py`、`probe_pib.py`、`probe_bs.py`、`probe_trace.py`、`probe_trace2.py`、
`probe_gen.py`、`probe_if.py`、`probe_mark.py`、`probe_mark2.py`、`probe_dup.py`、
`probe_skip.py`、`probe_skip2.py`。

### 缺陷 I · clock_worker MISSING 12 条（`put` + `pre_before_trading_date = now_date`）

ORIG 关键控制流（offset 7164–7582，行 469–470）：

```
7164 L469  now_date > self.pre_before_trading_date      POP_JUMP_FORWARD_IF_FALSE → 7216
7186       pre_before_trading <= now_time < pm_close     →7248 / →7214
7212       JUMP_FORWARD → 7216
7214       POP_TOP
7216 L470  self.pre_before_trading_date == self.initial_trading_date  POP_JUMP_IF_FALSE → 7582
7248 L472  now_date != self.first_run_date              POP_JUMP_IF_FALSE → 7492
7492       put((dt, PRE_BEFORE_TRADING_START)); self.pre_before_trading_date = now_date   ← 12 条
7582 L482  elif ...（下一条 elif 链）
```
⇒ ORIG 源码是一条 **`if A and B or C:`** 复合条件（`(A and B) or C` 的求值序与字节码完全吻合），
**不是** 产品里的 `if A: if B or C:` 两层嵌套。

分析层把这一条复合条件拆成三个**块集合层层嵌套、但未建立父子关系**的 IfRegion（`regdump` 实测三者都是
`LoopRegion@5598.children` 的平级成员，`IfRegion@7164.children == []`）：
`@7164`(A) → 其 then 含 `@7186`(B) → 其 then 含 `@7216`(C)。
`regdump` + `probe_skip2.py` 实测重叠：
- `IfRegion@7164.then_blocks` 含 **7186 / 7248 / 7270 / 7492 / 7582 …**（既含子区域入口，也含子区域内部块），
  同时 `merge_block = 7216`；
- `IfRegion@7186.blocks` 与 `then_blocks` 均含 **7216**，而 **`IfRegion@7216.entry` 就是 7216**
  ⇒ 同一块同时是「@7164 的汇合块」「@7186 的臂内块」「@7216 的区域入口」三重身份（同层次三处认领）。

生成端实测链（`probe_mark2.py`，第一次 `generated_blocks.add(7216)` 的调用栈）：
```
_if_extract_condition_from_instructions  region_ast_generator.py:20975   ← self.generated_blocks.add(_or_rhs_block)  _or_rhs_block=7216
  ← _if_generate_normal:17841 (region=IfRegion@7186)
  ← _generate_if:11927 → _generate_region:3184
  ← _process_if_blocks:22454 (region=IfRegion@7164, block=7186)
  ← _if_generate_then_branch:15272 → _if_generate_normal:18179 → _generate_if:11927 → _generate_region:3184
  ← _loop_handle_child_region_entry:11431 (LoopRegion@5598, block=7164)
```
即：**生成 IfRegion@7186 的条件时，把块 7216 当作 `or` 右操作数块记账为已生成**（`region_ast_generator.py:20975`，
`_if_extract_condition_from_instructions` 内 `if _rhs_expr: self.generated_blocks.add(_or_rhs_block)`）。

后果（`probe_if.py` + `probe_gen.py` 实测）：
- `_generate_region → _generate_if(IfRegion@7216)` 时 `region.entry(7216) in self.generated_blocks == True`
  ⇒ 落入 `_generate_if` L11825 的「entry 已生成 ⇒ 本区域已发射」早退分支，`_if_generate_normal(7216)` **从未被调用**；
- `_process_if_blocks(blocks, IfRegion@7164, 'then')`（call#68）的发射循环 `for block in sorted(blocks,…)` 走到 7492 时
  `L21777 if block in self.generated_blocks: continue` ⇒ **块 7492 从未进 `_generate_block_statements`**
  （`probe_bs.py` / `probe_dup.py` 双重确认：7492 在 never-emitted 列表）。

**早退条件**：本次实测命中的唯一早退是 `region_ast_generator.py:11825`
`if region.entry and region.entry in self.generated_blocks:`（+ 发射循环 `L21777 if block in self.generated_blocks: continue`）。
同函数 `L22071 stmts[-1] in ('Break','Continue','Return','Raise')` 是另一处会吞后续块的跳过点
（本轮对 7492 未命中，但同型，列为风险）。
**丢的是哪一层**：`IfRegion@7216` 的 then 臂（块 7492，行 478–479）。

### 缺陷 II · clock_worker EXTRA 23 条（重复 `elif check_trading_time(...): pass` + 重复 `==` 比较）

区域重叠实测（`dump/reg_clock_worker.txt`）：
- `IfRegion@7604`（L483 链式比较 `before_trading <= now_time < pm_close`）
  `then_blocks=[7630, 7634, **8592**, 8666, …, 9144]`；
- `IfRegion@7634`（L484）
  `then_blocks=[7668,…,8588]`、`else_blocks=[**8592**, 8666, …, 9144]`、`elif_conditions=[**8592**]`。
⇒ **块 8592 同时是 @7604 的臂内块 与 @7634 的 elif 链头**（同层次两处认领，违反「每块唯一归属」）。

生成 AST 实测（`dump/ast_clock_worker.json` / `astoutline.txt`；`pycdc.decompile_pyc()` 输出与
`build_landed/...realtime_event_sourceOK.py` 在**换行归一化后逐字节相同**，LF 口径 sha `234b7875b3073335`
（raw 口径差 CRLF），⇒ 产品即当前 HEAD）：
- `If(or) test_line=470` 的 `orelse=[If check_trading_time → {If check_handle_date…, If(and) L544…}]`（产品行 275–288，真 body）；
- `If test_line=484` 的 `orelse=[If check_trading_time → Pass]`（产品行 312–313，**重复头 + pass**）。
`probe_dup.py` 实测：**没有任何语句块被 `_generate_block_statements` 发射两次**（除 block 0 伪影）⇒ +23 条 EXTRA 是
**条件表达式被重建两次**（8592 的指令被两处各取一次），不是语句双发。

### 缺陷 III · clock_worker 循环尾被挪出 + 伪 `break` / `while True` 包裹

`probe_pib.py` 实测两个 `_process_if_blocks` 调用：
- `arg0=[6322…6690]`（`if is_holiday_today:` 整臂）→ 返回 **`[If, BREAK]`** ⇒ 臂尾伪 `break`（产品行 247）；
- `_loop_postprocess ← _if_generate_branch_stmts` 中 `arg0=[6778, 9214]` → 返回 **`[Assign, BREAK]`** ⇒
  `self.before_trading_date = now_date` + `break` 被发到**内层 while 之后**（产品行 316–317）。
`probe_bs.py` 实测块发射者：`6690 → []`、`6702 → ['Expr']`（经 `_r58_collect_break_target_stmts`）、
`6778 → ['Assign']`（经 `_loop_postprocess`）⇒ `if holiday_not_do_before == '0':` 与尾部赋值
**被推迟到 `_loop_postprocess`**，于是生成器造出外层 `while True:`（产品行 216）包裹内层 `while self.active:`（行 217），
并在臂尾补 `Break`（try body/handler 各 1，见 `probe_break.py` 4 处 Break 来源）。
这也解释 `nested_diff` 里 `delete orig[959:976]`（holiday 块位移）与 `+100/−59` 两个大 hunk 的顺序颠倒。

### api_base · `get_history_df` 根因
ORIG 两处（`time_count` / `max_len_real_data`）均为「条件块尾 `POP_JUMP_FORWARD_IF_TRUE` + 紧随其后的
`x -= 1` 作为 false 路径」；DEC 把条件取反成 `POP_JUMP_FORWARD_IF_FALSE`，并把 `x -= 1` 发射到后面的汇合点
（`insert decomp[526:530]` / `decomp[548:552]`）。两处完全同型 ⇒ 修一条规则即可把 4 个 hunk 清零。

`api_regions.py` 实测（get_history_df，offset 2134–2580）：
- ORIG 字节码：`if not include and freq==MINUTE and cur not in (...)`（guard，false 全部跳到 2254）
  → guard 体内 `if not (pm_open>cur>am_close or cur>pm_close): time_count -= 1`（真→2254，假→2244 再落到 2254）
  → **2254（L422 `if frequency == ...` 块）是 guard 与内层 if 的共同汇合点，在 guard 之外**。
- DEC 产物（api_baseOK.py L295–313）却把 2254 的代码塞进 `if pm_open>cur>am_close or cur>pm_close:` 的 then 臂
  （L297–311），把 `time_count -= 1` 降级成 guard 体内的同级语句（L312），L313 才是 L443 块。
- 区域结构实测：`IfRegion@2144`(guard, cond=2190) `then=[2202,2218,2230,2228,2232,2244]`、`merge=2254`；
  `IfRegion@2202`(链式比较, cc=[2218]) `then=[2232]` `else=[2230]` `merge=2254`；
  `IfRegion@2232` `then=[2244]` `merge=2254`；`IfRegion@2254` 为 `IF_ELIF_CHAIN`(cond=2254, elif=[2318])。
  ⇒ **三重身份重叠**：块 2232 既是 `IfRegion@2202.then` 成员又是 `IfRegion@2232.entry`；
  `block_to_region[2244] = IfRegion@1782`（与 @2144/@2232 都不是同一区域，属归属竞争，
  见 `region_ast_generator.py:21560-21577` 注释记载的同型失败模式）。
- 本轮**未能把「2254 被当成内层 if 的 then」这一步钉到单一早退/单一赋值点**（时序上它与
  `_if_extract_condition_from_instructions` 的 `or` 右操作数记账同族，但未做二选一的实测隔离）。
  ⇒ 按「判据未钉死不写 spec」的纪律，不提候选。

该形状属 R69 已判定「过重」的嵌套 BoolOp 重构族（`inline_boolop_chains` 需扩成 6 读点），
本轮未找到更轻的同层次身份判据。

### ADR-1 关键结论（为什么必须成对落地）
clock_worker 严格尺 Σ|Δ| = |1276 − 1287| = **11**。
- 只修缺陷 I（补 12 条）⇒ decomp 1299，Σ|Δ| = 23（**变差**）；
- 只修缺陷 II（删 23 条）⇒ decomp 1264，Σ|Δ| = 12（**变差**）；
- 两者同时落地 ⇒ decomp 1276，Σ|Δ| = 0。
**任一单独改动都不满足 ADR-1「Σ|Δ| 净减少」**，因此不存在可独立验收的半程候选。

## Step 3 · 合成复现
**未执行**。理由：Step 2 结论是「两条缺陷必须同时落地才不劣化（见上 ADR-1 推算）」，
且两条分别落在 `_if_extract_condition_from_instructions` 的 `or` 右操作数记账与
`IfRegion@7604/@7634` 的臂归属重叠，属两个独立根因；本轮未产出任何候选 patch，
按「没有合成复现不许写 spec，没有候选不许造见证」的纪律，Step 3 跳过。

## Step 4 · 候选与 A/B
**候选：NONE（两支靶均无候选 spec，故未建臂、未跑 A/B / 电池 / 金丝雀 / 严格尺 / 合成）。**

不建候选的具体理由：
1. `clock_worker`：两个根因必须成对落地（否则 Σ|Δ| 11→23 或 11→12，违反 ADR-1）；
   修法都要求在**分析层**改区域切分（把 `A and B or C` 合成一个 IfRegion、或把 8592 的唯一归属判给 @7634）
   —— 属跨区域结构调整，没有同层次、单点、可一次正确的轻判据；且即使计数归零，官方尺
   jump=10 / true=481 的跳转目标差仍需另行解决。
2. `api_base`：4 hunk 同型可一条规则清零，但所需改动即 R69 已判「过重」的
   `inline_boolop_chains` 6 读点嵌套扩展；本轮没有找到更轻的判据，不重复提出已被回退过的中心级建议。

## VERDICTS

| 靶支 | 缺陷 | 候选 | 理由 |
|---|---|---|---|
| `realtime_event_source.pyc` → `clock_worker` | seq_len 1276→1287（MISSING 12 / EXTRA 23）+ jump=10 / true=481 | **NONE** | 三处独立根因（`_or_rhs_block` 记账吞掉 IfRegion@7216.entry → 块 7492 不发射；@7604/@7634 争认块 8592 → 条件双重建；`_loop_postprocess` 推迟 6778/6792 → 伪 break + `while True` 包裹）。两条计数类缺陷必须成对落地才不违反 ADR-1，且均需分析层区域重构，无同层次单点轻判据。 |
| `api_base.pyc` → `get_history_df` | seq_diff #419 极性 + 位移（计数相等） | **NONE** | 结构已定位（ORIG `if not (B or C): x -= 1` 且 2254 为 guard/内层共同汇合点；DEC 把 2254 塞进 `if B or C` 的 then 臂），但**「2254 被当成内层 then」这一步本轮未钉到单一早退/赋值点**，无法写三要素判据；且所需改动落在 R69 已判「过重」的 `inline_boolop_chains` 6 读点族。 |

金丝雀 4 支 / 45 项电池 / 82 项全量均未被触碰（未建臂、未改工作树），仓库保持只读。

## 对 BRIEF 的更正
1. **任务目标「至少一支 partial 修到官方 100%（全清）」本轮未达成**，两支均为 NONE；根因证据见 Step 2，
   不是流程缺步，而是两条靶支的缺陷都需要分析层区域重构（无同层次单点判据），且 `clock_worker` 的两条
   计数缺陷存在 ADR-1 成对约束（单改任一条 Σ|Δ| 必然变差）。
2. 严格尺与官方尺 `clock_worker` 的 orig 计数差 1（1276 vs 1275）系两尺口径差（官方尺含 R101/R102 尾部
   `return None` 裁剪），过冲量同为 11 —— 与 `targets.md` 一致，非更正。
3. `h62.py` / `closeout69.py` / `sstrict67.py` 的 ROOT 固定指向 `D:/Temp/opencode/r70gate/center`
   （即 `center/mirr_<arm>`、`center/build_<arm>`、`center/dump/repro65_<arm>.jsonl`），与 BRIEF §「工作区=同级目录」
   的描述不冲突但需注意产物落点在 center，不在 `diag5/`。
4. 仪器补充（BRIEF §5 未列）：Windows PowerShell **没有 `grep` 命令**，行内 `python -c` 长脚本会因引号/转义失败
   ⇒ 一律改写成 `.py` 探针文件再执行；`cfg.blocks` 的键是**块序号(int) 而非 block 对象**，
   取块集合要用 `cfg.get_blocks_in_order()` / `cfg.get_block_by_offset(off)`。

