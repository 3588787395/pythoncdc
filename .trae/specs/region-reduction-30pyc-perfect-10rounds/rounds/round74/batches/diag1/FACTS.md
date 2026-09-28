# Round 74 · diag1 · 77 失败单元子机理归属 — FACTS

工作区 `D:/Temp/opencode/r74gate/diag1` · 基线 HEAD **`6bb9716a`**（R73 落地）·
repo `F:/Downloads/pythoncdc-main` **全程只读**（无创建/修改/删除、无 git 操作、未动任何 `*OK.py`、
未跑 402 全量、未用 `land74.py --apply`）· 所有读数只写本区 `dump/`。

---

## 0. 结论（四问各一句）

1. **F-ABSORB 67 三拆 = A 7 / B 10 / A∩B 3 / C 53**（A∪B = 14）。落点形态：
   **落点不同指令 35 · 落点同但 len 变 25 · opname 变+len 变 7**（F-PAD 8 全为「落点同/len 等」，F-POLARITY 1、F-OTHER 1）。
2. **11 个 inside-try 单元三选一 = (a) 10 / (b) 0 / (c) 1**。
   (c) 唯一命中 `strategy.tick_worker_thread`；(b) 0 的硬证据是 11 单元 `handler code sigs identical=True`
   且首分歧指令角色全部 `PROTECTED`（无一为 `HANDLER`）。
3. **F-PAD 8 单元对 `pad_e2fix`**：**同形态（ELSE 臂）但判据未覆盖 3**（`kill_trade_process` / `query_strategy_id` /
   `modify_batcktes_info`）、**pad6 已压掉 ELSE 仍失败（另一子机制）1**（`check_frequency`）、
   **无 DUP/ELSE 的新形态 4**（`query_trade_strategy_info` / `reconnect` / `etf_basket_order` / `run_tick_socket`）。
4. **重叠面**：`in-try ∩ F-PAD = 2`（`quote.run_tick_socket`、`flytools.modify_batcktes_info`）；
   `in-try ∩ (A∪B) = 2`（`trade_operation`、`get_cache_l2_data_by_one`，均 B 类）；
   `in-try ∩ boolop 链 = 4`（`run_tick_socket`、`get_fields`、`clock_worker`、`tick_worker_thread`）。

主表：`dump/trisect74.txt`（A/B/C、落点、PAD 形态、重叠面全量）·
`dump/root11.txt`（11 单元三选一逐单元判定）·
`dump/try_units4.txt`（11 单元指令级 diff 原始读数）。

---

## §1 F-ABSORB 67 三拆（fix1 主攻面）

### §1.0 判据与交叉核对（`dump/trisect74.txt:99-104`，命令 `python -X utf8 d74_trisect.py`）

| 类 | 判据（BRIEF_diag1 §2.1） | 自动判据实现 | 计数 |
|---|---|---|---|
| **A** same-target 共享 else（abs1 `_is_nested_if_else_pattern` 豁免可解） | 链成员条件跳转汇聚同一块 | `chain.json` 中某链 `same_target=True` 且 `nested_ret=True` | **7** |
| **B** orphan-child 丢语句（合并后 child 不在 `blocks/then_blocks`） | 区域树 children 覆盖差 | `chain.json` `orphans[].covered == false` | **12 全体 / 10 属 F-ABSORB** |
| **C** 其余（boolop 链尾/链内其他归约） | — | 非 A 非 B | **53**（F-ABSORB 内） |

交叉核对（两套独立实现集合相等）：

- `|chain A| = 7` vs `|abs1 臂 n_regions != base 臂| = 7`，**symdiff = 0**。
  与 R73-fix2 交接：这 7 个中的 4 个 A-only 单元正是 `specs/abs1_nested_same_exit.json`
  已转绿的 4 个（`r73gate/fix2/FACTS.md:127`，strict 79→75、新增缺陷 0）；3 个 A∩B
  未转绿——同件 `:150-156` 已记录 `get_multiminute_his_data` 丢语句（`seq_len 482→471`）与
  `kline_datetime_list` 两处修正，并把定性为「共享尾 region 合并后生成器跳过 orphan child」。
- `|chain B(covered=False)| = 12` vs `|abs1 base.orphans parent_covered=False| = 12`，**symdiff = 0**；
  未覆盖 orphan 条目合计 **27**（F-ABSORB 10 单元 18 条、`kill_trade_process` 1 条、`_sync_worker` 8 条）。
- `same_target=True`（不管 `nested_ret`）共 **22** 单元 ⇒ **必须加 `nested_ret` 才是 A**（否则多 15 个假阳）。

### §1.1 A 类（7 单元）— `dump/trisect74.txt:27-31, 40-43`；逐链 `argval→block` 在 `:105-155`

| 单元 | 链 | 成员 argval→blk（同 target 汇聚） | nreg base→abs1 | 落点形态 |
|---|---|---|---|---|
| `trade_live_broker.get_max_amount` | chain#3,#4 | `and 910 → blk778 / blk790`，last=`POP_JUMP_FORWARD_IF_FALSE` | 32→28 | 落点同/len 变 |
| `finance.get_financial_and_growth_factors` | chain#0 | `and 114 → blk6 / blk10`，last=`POP_JUMP_FORWARD_IF_NOT_NONE` | 26→24 | 落点不同指令 |
| `finance.get_financial_statements_pit_mode` | chain#0 | 同上 `and 114 → blk6 / blk10` | 23→21 | 落点不同指令 |
| `local_finance.get_local_financial_factors` | chain#0 | `and 84 → blk6 / blk10` | 24→22 | 落点不同指令 |
| `klinedata.get_multiminute_his_data`（**A∩B**） | chain#0 | `and 2710 → blk0 / blk68` | 35→33 | 落点同/len 变 |
| `klinedata.kline_datetime_list`（**A∩B**） | chain#1,#3 | `and 1150 → blk1034/1072`；`and 1646 → blk1412/1596` | 58→54 | 落点不同指令 |
| `api_base.get_history_df`（**A∩B**） | chain#7,8,9,10,12,14 | `and 4052/4170/4628/4746/6892/7076 → 双 blk` | 229→217 | 落点不同指令 |

链站点全部 `region_analyzer.py:26653`（`chain.json`）。
**判据行**：`trisect74.txt:107` `chain#3 same_target=True nested_ret=True site=region_analyzer.py:26653` 等。

### §1.2 B 类（F-ABSORB 10 单元；另有 F-PAD 1、F-POLARITY 1）— 区域树 `dump/trisect74.txt:156-622`

| 单元 | 孤儿总数 | 未覆盖条目 | 未覆盖 child（parent→child） | 证据行 |
|---|---|---|---|---|
| `quote.get_real_from_zeromq` | 33 | 2 | `LoopRegion@398→BoolOpRegion@192`、`IfRegion@788→Region@1024` | `trisect74.txt:163,183` |
| `quote.get_individual_data` | 31 | 2 | `LoopRegion@494→BoolOpRegion@412`、`IfRegion@884→Region@1120` | `:193,209` |
| `trade_info_utils.trade_operation` | 16 | 1 | `WithRegion@414→WithRegion@1178` | `:227` |
| `real_quote.get_cache_l2_data_by_one` | 17 | 3 | `TernaryRegion@0→Region@44/@54/@56` | `:246-248` |
| `real_quote.get_tick_direction` | 30 | 2 | `LoopRegion@408→BoolOpRegion@308`、`IfRegion@858→Region@1102` | `:260,274` |
| `risk_calculation._save_testds_to_csv` | 4 | 1 | `LoopRegion@108→LoopRegion@262` | `:382` |
| `handlers.TWHThreadController._target` | 17 | 2 | `LoopRegion@504→Region@1012`、`LoopRegion@504→Region@1016` | `:386-387` |
| `klinedata.get_multiminute_his_data`（A∩B） | 33 | 1 | `IfRegion@68→Region@2710` | `:320` |
| `klinedata.kline_datetime_list`（A∩B） | 55 | 2 | `IfRegion@370→Region@396`、`IfRegion@756→Region@782` | `:324,327` |
| `api_base.get_history_df`（A∩B） | 219 | 2 | `IfRegion@1954→Region@1984`、`IfRegion@2654→Region@2680` | `:409,413` |
| *（F-PAD）* `trade_info_utils.kill_trade_process` | 38 | 1 | 非 F-ABSORB，随 §3 标注 | `chain.json` |
| *（F-POLARITY）* `trade_live_broker._sync_worker` | 23 | 8 | 非 F-ABSORB，随 §3 标注 | `chain.json` |

**全部 27 条未覆盖条目的 `in_blocks/in_then/in_else` 三者皆为 `False`、`glob_covered=True`**
（各单元块起始行：`trisect74.txt:157/191/223/240/258/289/323/379/384/402`，逐条打印）⇒ 即 R73-fix2 FACTS 所述「合并后 child 不在 `blocks/then_blocks`、
但仍在全局序内」的形态；生成器跳过它 ⇒ 丢语句。A∩B 三单元（klinedata×2、api_base）
**同时**踩两种机理，是 fix1/fix2 合并时的最高风险点。

### §1.3 C 类（53 单元）— 全量行 `dump/trisect74.txt:44-97`，总表 `:682-759`

判据：`chain` 无 `same_target&nested_ret` 链、且无未覆盖 orphan。落点形态分布
（`trisect74.txt:635-639`，C 列）：落点不同指令 **27**、落点同/len 变 **20**、opname 变 **6**。
其中 **17 个 C 类单元带 boolop 链但 `nested_ret=False`**（故不入 A；`trisect74.txt:45-97` 各行 `chains=`），
in-try 内的 3 个（`get_fields`、`clock_worker`、`tick_worker_thread`）是 fix3 的 (c) 候选（§2/§4）。

### §1.4 落点形态表（BRIEF「落点同/len 变 vs 落点不同指令」）— `dump/trisect74.txt:623-639`

| 落点形态 | F-ABSORB | × in-try | A | B | A+B | C |
|---|---|---|---|---|---|---|
| **L1 落点不同指令**（`lands on DIFFERENT instr`） | **35** | IN 6 / OUT 29 | 3 | 3 | 2 | 27 |
| **L3 落点同、len 变**（`target instr same but len …`） | **25** | IN 3 / OUT 22 | 1 | 3 | 1 | 20 |
| **L5 opname 变 + len 变** | **7** | IN 0 / OUT 7 | 0 | 1 | 0 | 6 |
| F-PAD · **L2 落点同、len 等** | 8（另一族） | IN 2 / OUT 6 | — | — | — | — |
| F-POLARITY（极性翻转 `IF_TRUE→IF_FALSE`） | 1 | OUT 1 | — | — | — | — |
| F-OTHER（`opname+length equal`） | 1 | OUT 1 | — | — | — | — |

---

## §2 11 个 inside-try 单元逐单元三选一根因（fix3 主攻面）

### §2.1 口径与自动判据（`dump/root11.txt:1-3`，命令 `python -X utf8 d74_root.py`）

三选一按 `BRIEF_fix3.md §2.2` 原文定义，落成可复现规则：

| 选项 | 定义（BRIEF_fix3 原文） | 自动判据 |
|---|---|---|
| **(a)** | 共享尾/merge 被 try 内臂吸收（shared exit in try） | 其余全部 |
| **(b)** | handler 出口错位（except 块落点/`reraise` 或 `return` 落点不同） | **handler 指令 opname 序列两侧不等**，或首分歧落点 `role=HANDLER` |
| **(c)** | try 内 boolop/elif 链归约 | **et 逐条完全相同** 且首分歧是条件跳转且 `(opname, ORIG target)` 命中 `chain.json` 成员 `last/tgt` |

handler 指令的界定（`handler_sigs()`，实现见 `d74_root.py`；边界读数 `dump/handler_bounds.txt`）：
对每条 et 条目取 `[target, min(下一个 handler target, 下一个 protected 起点))`；
若 `target` 自身又是「深度 ≤ 本条目」的 protected 起点（嵌套 try 体起点），该条目判为 `amb=True` 跳过
——否则会把整段 try 体误当 handler（`run_tick_socket` 的 `(d=1,t=522)` 就是这类假阳，实测把
`[522,1280)`/`[522,1282)` 的 141/142 条指令差异误报成 handler 差异；去掉后同一区间逐条相等）。

**首分歧用三把尺，不可互换**（详见 §2.4）：
- 尺 A = `fam74` 的 `firstA/firstB`（`fam74 reason` 行）
- 尺 B = `firstdiv73` 的 `(opname, argval)`（`firstdiv73 div=` 行）
- 尺 C = 本探针的归一化键（`LOAD_CONST` 的 code object 归一为 `<code:co_name>`，规避文件名/行号噪声）

### §2.2 逐单元判定表（证据 = `dump/root11.txt` 行号；指令级 diff = `dump/try_units4.txt` 行号）

| # | 单元 | et ORIG/PROD | fam74 尺 A 首分歧 | firstdiv73 尺 B | 首分歧角色 | handler 码 | **三选一** | 子机理与证据 |
|---|---|---|---|---|---|---|---|---|
| 1 | `quote.run_tick_socket`（F-PAD） | 13/12 | `idx11 … target 158→364` 同指令/len 等 | `idx14 528 vs EXTENDED_ARG@66` | PROTECTED(d0)×2 | **identical** (3/3) | **(a)** | **a1 整块搬家**：`o66 POP_JUMP_IF_FALSE 528 → o68 …1122`，两侧落点块同为 `self.log.quote.warning('tick数据返回为空')…`（`root11.txt:18-19`）；`try_units4.txt:49` `delete ORIG[93:117](24) [(528,'LOAD_FAST'),…]` ⇒ 528 块整体移到 try 体尾 1122；`o138 JUMP_FORWARD to 684 → to 528`（`try_units4.txt:47-48`）⇒ et 13→12 合并 |
| 2 | `trade_info_utils.trade_operation` | **18/18 identical** | `idx93 … 324→172` 落点不同指令 | `idx108 1000→1042` | PROTECTED(d1)×2 | **identical** (4/4) | **(a)** | **a3 假臂直跳 merge/backedge 吃掉中间块**：全函数唯一差异 `o676 POP_JUMP_IF_FALSE 1000→1042`（`root11.txt:41-42`）；ORIG 落点1000=`write_info.append(items)`、PROD 落点1042=`JUMP_BACKWARD` ⇒ false 臂跳过 append。`chains=0` ⇒ 非 (c) |
| 3 | `real_quote.one_prod_to_ndarray` | 10/10（位移 +12） | `target instr same but len 601/603` | `idx89 1724→1736` | **OUTSIDE×2** | **identical** (6/6) | **(a)** | **a4 try 内大块重排+出口位移**：`o412 POP_JUMP_IF_FALSE 1724→1736`（`root11.txt:53,64-65`），两侧落点均为 body-exit merge（`role=OUTSIDE`）；instr 659→665、difflib 12+18 插/35 删（`try_units4.txt:182` 起）；et 条目数不变、全部 range 平移 |
| 4 | `real_quote.get_real_minute_kline` | **7→8** | `target instr same but len 250/253` | `idx108 372 vs EXTENDED_ARG@108` | PROTECTED(d0)×2 | **identical** (2/2) | **(a)** | **a1 整块搬家**：`o108 POP_JUMP_IF_FALSE 372 → o110 …1118`（`root11.txt:76,87-88`），两侧落点块同为 `datetime.datetime.now()…`（`try_units4.txt:404-417`）；instr 280→287、`insert PROD[220:258](38)` 含 `EMPTY_DAY_BAR_NP_ARRAY` 早返回 + datetime 块（`try_units4.txt:490-499`），et 7→8 |
| 5 | `real_quote.get_cache_l2_data_by_one` | 5/5 | `idx95 … 226→138` 落点不同指令 | `idx77 FOR_ITER 590→592` | PROTECTED(d0)×2 | **identical** (2/2) | **(a)** | **a3 并入循环回边**：`try_units4.txt:574-576` `replace o468 POP_JUMP_IF_FALSE 538→590` + `insert PROD o590 JUMP_BACKWARD to 336` ⇒ 假臂并入循环回边；其余 13 条差异全为 +2 平移 |
| 6 | `finance.get_fields`（R73 IN-TRY k=18） | 8/8 | `idx18 JUMP_FORWARD 90→254` 落点不同指令 | `idx4 740→742` | PROTECTED(d0)×2 | **identical** (2/2) | **(a)** | **a3 跳到隐式 epilogue**：`try_units4.txt:675` `replace ORIG[23:24] [(92,'JUMP_FORWARD to 236')] → PROD [(92,'EXTENDED_ARG'),(94,'JUMP_FORWARD to 742')]`，742=`LOAD_FAST fields; RETURN_VALUE`；`chains=1` 但链 target=672、首分歧 target=740 ⇒ 链不匹配 ⇒ 非 (c) |
| 7 | `flytools.modify_batcktes_info`（F-PAD） | 22/22（条数/层不变） | `idx162 … 380→404` 同指令/len 等 | `idx151 LOAD_CONST None vs NOP@700` | ORIG=PROTECTED(d0) / PROD=**PROTECTED(d1)** | **identical** (5/5) | **(a)** | **a4 +2 平移**：首分歧即 `o700 LOAD_CONST None → NOP`（`root11.txt:156-157`），700 起全 +2；`depth>=1` len 仅 `58→60`（该 protected range 因 NOP 插入变长，非 handler 变化）；`chains=0` |
| 8 | `email_utils.send_email`（et=5） | 5/5 | `idx22 … 206→332` 落点不同指令 | `idx28 674→1120` | ORIG=PROTECTED(d0) / PROD=**OUTSIDE** | **identical** (2/2) | **(a)** | **a2 共享 `return None` 尾内联**：`try_units4.txt:814,821-824` `insert PROD[193:195] [(1120,'LOAD_CONST'),(1122,'RETURN_VALUE')]`，把共享尾插在 handler 起点 1124 之前；ORIG gap `[1118,1120)` 1 条 return、PROD gap `[1118,1124)` 2 条；`o130` 后 `o1136→o1140` 仅 +4 平移 |
| 9 | `realtime_event_source.clock_worker` | 24/24 | `idx664 … 2494→2476` 落点不同指令 | `idx717 LOAD_CONST <code object …>`（**code 元数据噪声**） | PROTECTED(d0)×2 | **identical** (4/4) | **(a)** | **a2 返回合并 + a4 大块搬移**：归一化尺分歧 `idx768 LOAD_DEREF self → NOP`、`idx770 POP_JUMP_IF_FALSE 9214→9138`；ORIG gap `[9210,9218)` 双 `return None` → PROD gap `[9240,9244)` 单 `return`（`try_units4.txt:845,854`、`root11.txt:196`）；`try_units4.txt:860-865` `o5612 POP_JUMP_IF_FALSE 9214→9138`；`delete ORIG[959:976](17)@6690`（`try_units4.txt:934`）与 `insert PROD[1168:1278](110)@7792`（`try_units4.txt:1021`）为同段搬移；`chains=3` 但链 target=6280/7164/9144、分歧 target=9214 ⇒ 非 (c) |
| 10 | `cgroup_utils.set_cgroup_config` | **4→5** | `target instr same but len 540/541` | `idx508 4414→4416` | PROTECTED(d0)×2 | **identical** (2/2) | **(a)** | **a2 共享尾内联**：`try_units4.txt:1258-1261` `replace ORIG[620:621] [(4412,'JUMP_FORWARD to 4446')] → PROD [(4412,'LOAD_CONST None'),(4414,'RETURN_VALUE')]` ⇒ 共享 `return None@4446` 被内联，et 新增 gap `[4412,4416)` 把 `(120,4446)` 拆成 `(120,4412)+(4416,4448)` ⇒ 4→5 |
| 11 | `strategy.tick_worker_thread` | **3/3 identical** | `idx61 … 156→12` 落点不同指令 | `idx73 568→820` | PROTECTED(d0)×2 | **identical** (2/2) | **(c)** | **try 内 `or` 链归约**：et 逐条相同、instr 294/294；`chain-match=(0, blk=512, op='or', last='POP_JUMP_FORWARD_IF_TRUE', tgt=568)`（`root11.txt:246`）；et 逐条相同、gaps 逐条相同、instr 294/294（`try_units4.txt:1274-1310`）；全函数仅 4 条 `POP_JUMP_FORWARD_IF_TRUE` 目标不同（o522/o534 `568→820`、o992/o1004 `1038→1286`），4 条都是 try 区内 `or` 链成员（`dump/chain.json` blk 512/524、982/994，`same_target=true, nested_ret=false`）；ORIG 落点568=`time.sleep(60)`（链共享体）、PROD 落点820=`JUMP_FORWARD to 1286` ⇒ 产品把 `or` 链共享体接到合并跳，`sleep` 臂在产品中成死块 |

**tally：`{'a': 10, 'c': 1}`（`dump/root11.txt:249`）**

### §2.3 (b)=0 的硬证据（BRIEF 问 2 要的可复现读数）

1. **11/11 `handler code sigs identical=True`**（`root11.txt` 各单元 `handler code sigs identical=` 行，
   n 分别为 3/4/6/2/2/2/5/2/4/2/2）——两侧 `except` 块的指令 opname 序列逐条相等，即
   **handler 的 `reraise`/`return` 落点结构没有错位**。
2. **首分歧指令角色 11/11 为 `PROTECTED`**（`root11.txt` 各 `div instr role` 行；
   `modify_batcktes_info` 的 PROD 侧为 `PROTECTED(d1)` = 嵌套 try 体内，仍非 handler）。
   **首分歧落点角色**：9 单元两侧 `PROTECTED`；`one_prod_to_ndarray` 两侧 `OUTSIDE`；
   `send_email` ORIG=`PROTECTED(d0)`、PROD=`OUTSIDE`（落点 1120 落在 PROD 的 et 空隙 `(1118,1124)` 内，
   即 handler 起点 1124 之前的共享 return 段；`root11.txt:166,173,176-179`）。
   ⇒ **无一落在 HANDLER 区**。
3. `depth>=1` 的 `(end-start)` 长度序列在 10/11 单元两侧完全相同（`root11.txt` 各 `-> SAME` 行）；唯一变化
   `modify_batcktes_info` 的 `58→60` 是 **protected range 因插入 NOP 变长**，其 handler 码仍 identical。

> **口径修正（要交 fix3）**：`BRIEF_fix3 §1` 备注「`send_email` 首分歧在 handler 内」
> 与实测不符——`send_email` 首分歧指令 `o130` 位于 et 条目 `(14,166,1120,0)` 的 protected 段内、
> 落点 ORIG=`PROTECTED(d0)`/PROD=`OUTSIDE`（`root11.txt:164-167,175-176`、`try_units4.txt:790-800`）。
> 其真实机理是 **(a) 共享 `return None` 尾被物化到 handler 起点之前**，副作用才是 handler 起点 1120→1124。

### §2.4 三把「首分歧」尺（FACTS 必须写明，否则读数不可比）

| 尺 | 来源 | 实测例 |
|---|---|---|
| **A** `fam74.firstA/firstB` | `fam74_r74.json`，`firstA` 前导数字恒为 `2*firstidx`（11/11 已验证） | `get_fields` `idx18 JUMP_FORWARD 90→254` |
| **B** `firstdiv73` 的 `(opname,argval)` | `dump/units74_join.json → fd.div/off` | `get_fields` `idx4 POP_JUMP_IF_NOT_NONE 740→742` |
| **C** 归一化键（本探针 `norm()`） | `d74_root.py` | `clock_worker` `idx768 LOAD_DEREF→NOP`、`idx770 …9214→9138` |

- 尺 A 的下标**不等于** `dis.get_instructions` 过滤流下标（例：`trade_operation` firstidx=93 文本是
  `186 POP_JUMP_FORWARD_IF_FALSE to 324`，而该过滤流 idx93 是 `o598`）⇒ **`firstA/firstB` 只能当不透明串引用**。
- 尺 B 在 `clock_worker` 上先撞 code object 元数据（`LOAD_CONST <code object … file/line 不同>`），
  真 CF 分歧要到尺 C 才出现。
- `firstdiv73.origTryDepth`：**0=首分歧不在异常区、1=在**（66/11 分布），与 `dump/crosstab74.txt`
  第 5 列合计的 `OUT66/IN11` 一致（trisect 复算见 `trisect74.txt:5-10`）；它**不是** try 嵌套深度。`tryverdict73.txt` 的 `nest`/`origNest`/`prodTryNest`
  三者口径另见 `dump/nest_semantics.txt`（`prodTryNest` 是产品文件级 `ast.Try` 最大嵌套，与本表无对应）。

---

## §3 F-PAD 8 单元的 pad 残留形态 vs 已落地 `pad_e2fix`（fix2 主攻面）

读数：`dump/trisect74.txt:640-665`（命令同上）；
形态数据源 `D:/Temp/opencode/r73gate/fix1/dump/padshape_landed.json`（只读）；
归因原文 `D:/Temp/opencode/r73gate/fix1/FACTS.md §5`。

| 单元 | in-try | R73 landed 形态 | 与 `pad_e2fix`（pad6）的关系 |
|---|---|---|---|
| `trade_info_utils.kill_trade_process` | 否 | `dup=[]  else_ret=[312,316]  nret=7` | **同形态（ELSE 臂）未覆盖**：else 臂非「纯 return 收尾」/不满足 gap 反序判据，两次编辑均未命中 |
| `trade_info_utils.query_strategy_id` | 否 | `dup=[]  else_ret=[1080]  nret=3` | **同形态（ELSE 臂）未覆盖**：形状是 ELSE，但区域结构不满足判据 |
| `flytools.ProcessWrite.modify_batcktes_info` | **是** | `dup=[]  else_ret=[817,820]  nret=5` | **同形态（ELSE 臂）未覆盖**：同 else 臂但不满足反序/gap 判据 |
| `quote.check_frequency` | 否 | `dup=[]  else_ret=[1012]  nret=2` | **pad6 已压掉（`else_ret [1012]→[]`）仍 80/92** ⇒ 该单元残余位移 **+38、另一子机制** |
| `trade_info_utils.query_trade_strategy_info` | 否 | `dup=[]  else_ret=[]  nret=2` | **新形态**：无 DUP/ELSE，位移来自另一站点（嵌套 return 尾次序） |
| `function.reconnect` | 否 | `dup=[]  else_ret=[]  nret=1` | **新形态**：无 DUP/ELSE（`nret=1`），不同子机制 |
| `trade_live_broker.etf_basket_order` | 否 | `dup=[]  else_ret=[]  nret=6` | **新形态**：try/except 清理尾声族，与 5 个已修单元不同站点 |
| `quote.run_tick_socket` | **是** | `dup=[]  else_ret=[]  nret=2` | **新形态**：无 DUP/ELSE，pad6 下仅行号平移；本单元真根因见 §2 表 #1（(a) a1） |

形态分组小结：**同形态未覆盖 3 / pad6 已清但仍有别的位移 1 / 新形态 4**。
8 单元全部 `L2 落点同指令、len 相等`（`trisect74.txt:630-631`），与 F-ABSORB 的 L1/L3 不同族。

---

## §4 重叠面（BRIEF 问 4）

| 交面 | 单元 | 归属建议 | 证据 |
|---|---|---|---|
| **`in-try ∩ F-PAD`（BRIEF(d) 指定 2 个）** | `quote.run_tick_socket`、`flytools.modify_batcktes_info` | **fix3 主修**（try/except 归约路径），fix2 观察；两者 (b) 判定均为 (a)，与 fix2 的 A/B 靶区**不重叠** | `trisect74.txt:666-670`（count=2） |
| **`in-try ∩ (A∪B)`** | `trade_info_utils.trade_operation`（B）、`real_quote.get_cache_l2_data_by_one`（B） | **fix3 主修**；fix2 的 B 类判据（orphan 未覆盖）在这两单元同样成立 ⇒ 合并时须双批各自回归 | `trisect74.txt:671-675`（count=2） |
| **`in-try ∩ boolop 链`（fix3 (c) 候选）** | `run_tick_socket`(1链)、`get_fields`(1)、`clock_worker`(3)、`tick_worker_thread`(2) | 只有 `tick_worker_thread` 真是 (c)；另 3 个链不匹配首分歧 ⇒ 归 (a) | `trisect74.txt:676-681` |
| **A∩B（fix1/fix2 内部重叠）** | `klinedata.get_multiminute_his_data`、`klinedata.kline_datetime_list`、`api_base.get_history_df` | fix1/fix2 **同改**，且是 R73-fix2 已知「klinedata 丢语句」单元 | `trisect74.txt:40-43` |
| **非 in-try 但跨族** | `trade_info_utils.kill_trade_process`（F-PAD 且 B 类）、`trade_live_broker._sync_worker`（F-POLARITY 且 B 类） | fix2 同时面对 PAD 形态与 orphan 覆盖差 | `trisect74.txt:671` 起 / `chain.json` |

`BRIEF_fix3 §1` 的第 4 个靶 `real_quote.get_tick_direction` 标注 **OUT**
（`origTryDepth=0`，`trisect74.txt:716`），不属 diag1 的 11 单元，但属 fix3 mandate；
其 class = **B**（未覆盖 orphan 2 条，`LoopRegion@408→BoolOpRegion@308`、`IfRegion@858→Region@1102`）
⇒ **fix3 若改 try 归约，会同时触碰 fix2 的 B 类判据面**，须在 fix3 FACTS 里标注。

---

## §5 dump 索引与命令行（全部在 `D:/Temp/opencode/r74gate/diag1`，每条 <300s）

| 命令 | 产物 | 内容 |
|---|---|---|
| `python -X utf8 d74_join.py` | `dump/units74_join.json` / `.tsv`、`dump/join_gap.txt` | 五方 join 主表（fam74 × filecat × firstdiv73 × exctable × tryverdict），含 `fd.div/off/origTryDepth`；`join_gap.txt:6` `join gaps (missing centre rows): []`（join 无缺失），`:5` 记 2 组重复键 |
| `python -X utf8 d74_chain.py` | `dump/chain.json` | 77 单元 boolop 链（`members[].blk/op/last/argval/tgt`、`same_target`、`nested_ret`、`site`）+ `orphans[].covered` |
| `python -X utf8 d74_abs1.py` | `dump/abs1.json` | base / abs1 双臂区域树（`n_regions`、`orphans[].parent_covered/glob_covered`） |
| `python -X utf8 d74_nest.py` | `dump/nest_semantics.txt` | `nest` / `origNest` / `prodTryNest` 口径核对 |
| `python -X utf8 d74_try.py` | `dump/try_units.txt` | 11 单元 ET 条目 + 首分歧上下文 + 产品源行 + shape 分类 |
| `python -X utf8 d74_try2.py` | `dump/try_units2.txt` | 双尺（firstidx / div）的 ORIG/PROD 指令与落点窗口 |
| `python -X utf8 d74_try3.py` | `dump/try_units3.txt` | 逐条 et 条目 diff（same/shifted/CHANGED/NEW/GONE）+ 落点窗口 + `role=` + chain 归属 + 未覆盖 orphan |
| `python -X utf8 d74_try4.py` | `dump/try_units4.txt` | 归一化尺分歧 + EXTENDED_ARG 修正落点 + et union 空隙 + difflib 指令级 insert/delete/replace 逐块（含所属 et） |
| `python -X utf8 d74_root.py` | `dump/root11.txt` | **11 单元三选一判定表**（et/handler/落点角色/链匹配/verdict） |
| `python -X utf8 d74_trisect.py` | `dump/trisect74.txt` | **A/B/C 三拆 + 落点形态 + PAD 形态归因 + 重叠面**（77 行全表） |
| `d74_root.py` 运行时附带 | `dump/handler_bounds.txt` | 逐 et 条目 handler 边界与 `amb` 标记（(b) 判据的原始读数） |
| `python -X utf8 strict_repo67.py dump/strict_list74.txt dump/strict_repo74.json` | `dump/strict_repo74.json` / `.txt`、`dump/strict_list74.txt` | repo 产品严格尺 75 缺陷（per-unit `seq_len orig=/decomp=`，判语句丢失） |

只读中心件（未覆盖其 dump）：`firstdiv73.py`、`exctable73.py`（`dump/exctable_diff73.txt`）、
`tryverdict73.py`（`dump/tryverdict73.txt`）、`fam73.py`。

**重复键提醒**：`calexrights_func.pyc <module>.change_his_to_forward` ×2、
`wizard_quant_api.pyc <module>.get_DMI.calculate_di.<genexpr>` ×2；
按 `(pyc基名, name)` join 会把两对各自合并成一行（`dump/join_gap.txt:5` 记录了这 2 组，
`:6` 的 `join gaps` 为空），引用计数时按「文件+单元」而非「单元名」去重。

---

## §6 对 fix1 / fix2 / fix3 的建议与风险

**fix1（F-ABSORB A 类 + 落点形态）**
- A 类 7 单元的判据已闭合（`same_target & nested_ret` ⇔ abs1 `n_regions` 变化，symdiff=0），
  可直接以 `chain.json` 的链成员 `argval→blk` 作为 spec 锚点清单（§1.1 表即锚点集）；
  R73-fix2 的 `abs1_nested_same_exit.json` 已把其中 4 个 A-only 单元转绿（`r73gate/fix2/FACTS.md:127`），
  剩余风险全在 3 个 A∩B。
- 风险：A∩B 三单元（klinedata×2、api_base）同时有 orphan 未覆盖，**单改 A 判据不会让 B 类语句回来**，
  必须与 fix2 的 generator 补发射同批验证，否则会出现「区域数对了但语句仍丢」。
- L3（落点同/len 变）25 个里 A=1、B=3、A+B=1、C=20 ⇒ C 类的 L3 大多是纯偏移量问题，
  与 PAD 机理相邻但**不是** PAD（F-PAD 才是 len 相等），判据别混。

**fix2（A 类补强 / B 类 orphan / F-PAD）**
- B 类 12 单元 27 条未覆盖 orphan，`in_blocks/in_then/in_else` 三者皆 False —— 补发射的判据应只依赖
  「child 不在 blocks/then_blocks」这一结构事实（不要用偏移阈值/函数名）。
  这正是 R73-fix2 自己开出的处方（`r73gate/fix2/FACTS.md:156`「方向 = `region_ast_generator` 侧补
  orphan child region 发射，另起 `abs2` 单臂自证」），本轮已有 27 条精确清单可直接锚定。
- F-PAD 8 单元中 3 个是**同形态未覆盖**（判据差异：else 臂非纯 return 收尾、反序/gap 不满足），
  1 个已被 pad6 清掉形状但仍失败（`check_frequency` +38 大位移），4 个是**无 DUP/ELSE 的新形态**
  ⇒ pad_e2fix 不能覆盖本批，需要新的判据分支，且必须与 `check_frequency` 的大位移子机制分开归因。
- `kill_trade_process`、`_sync_worker` 两单元同时是 B 类（1 条 / 8 条未覆盖 orphan），
  fix2 内部就会碰到「PAD 形态 vs orphan 覆盖差」双判据，需在同一 arm 里排序。

**fix3（11 个 inside-try）**
- **(b) 0 个**：不要把力气花在 handler 出口上——11 单元 handler 码两侧逐条相等、首分歧全在 protected 段。
  真靶是 **(a) 共享尾/merge 被 try 内臂吸收**（10 个），子机理分四种：
  **a1 整块搬家**（`run_tick_socket`、`get_real_minute_kline`）、
  **a2 共享 `return None` 尾内联/合并**（`send_email`、`set_cgroup_config`、`clock_worker`）、
  **a3 假臂直跳 merge/backedge/隐式 epilogue**（`trade_operation`、`get_cache_l2`、`get_fields`）、
  **a4 try 内大块重排+出口位移**（`one_prod_to_ndarray`、`modify_batcktes_info`）。
- **(c) 1 个**：`tick_worker_thread` —— et 完全相同、唯一差异是 4 条 try 内 `or` 链成员的落点
  （`568→820`、`1038→1286`），且 `same_target=true, nested_ret=false` ⇒ **与 F-ABSORB 的 A 判据同源但
  `nested_ret` 不成立**，属 BRIEF 说的「与 F-ABSORB/PAD 判据同源」交中心项。
- `trade_operation`（R70 遗留 `target_diff #94`）已定位到**唯一**指令 `o676 POP_JUMP_IF_FALSE 1000→1042`
  （et 逐条相同）⇒ 修复只需让 false 臂落到含 `write_info.append(items)` 的块，不需要动 handler。
- 风险1：`get_tick_direction` 是 fix3 mandate 的第 4 单元但 **OUT**，且 class=B（orphan 未覆盖 2 条）——
  改 try 归约可能顺带改变 B 类覆盖，须与 fix2 对齐。
- 风险2：`run_tick_socket` / `modify_batcktes_info` 是 **in-try ∩ F-PAD**，fix3 改动会让 fix2 的 PAD 读数变化
  （`padshape_landed.json` 的 `ln/else_ret` 至少发生行号平移），两批合并前必须各自跑官方 35/41 靶。
- 风险3：三把首分歧尺不可互换（§2.4），任何 spec 的断言必须写明用哪一把，否则「首分歧前移/后移」的
  结论会因尺不同而相反。

---

## §7 只读与纪律自证

- repo 内**零**创建/修改/删除；未执行任何 `git` 写操作；未运行 402 全量；未使用 `land74.py --apply`；
  未手改任何 `*OK.py`（`d74_root.py` 等仅以 `compile(src, ok, 'exec')` 内存编译读取）。
- 从 repo 导入时统一 `python -X utf8`（并保持 `PYTHONDONTWRITEBYTECODE=1` 习惯），单命令 <300s。
- 跨批只读引用：`D:/Temp/opencode/r73gate/fix1/{dump/padshape_landed.json,FACTS.md,specs/pad_e2fix.json}`、
  `D:/Temp/opencode/r73gate/fix2/{FACTS.md,specs/abs1_nested_same_exit.json}` —— 均只读，未写入。
- 本区产物：`d74_*.py` 10 个探针 + `dump/` 18 个文件 + 本 `FACTS.md`；无 `specs/` 交付（按 BRIEF §4）。
