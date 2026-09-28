# R74 fix2 — FACTS.md（进行中）

工作区 `D:\Temp\opencode\r74gate\fix2`；镜像臂目录一律 `center/mirr_<arm>` + `center/build_<arm>`。
仓库只读；判据只写 `region_ast_generator.py` / `region_analyzer.py` / `comprehension_generator.py`。

## 0. 判据与工具链（本轮新确认）

| 事实 | 证据 |
| --- | --- |
| 权威判据是 pylingual（`scripts/pyc_verify.py single <pyc> --source <OK.py>`），不是 byte-diff | `pylingual/equivalence_check.py::compare_pyc` |
| `h62.py run` 的 matched_functions 走 `pyc_batch_verify.bytecode_diff` → `testqouter.round1.base.compare_bytecode`，会假阳 | flytools landed byte-diff 65/65，但 pylingual 65/66 |
| `compare_bytecode` 归一化会吃掉 NOP 与重复尾 return：landed raw86→78、orig raw85→78，两者 `match=True` | `cbcmp.py` 读数 |
| 所以「多写 `return None`」通常被归一化吸收，「少写一个 return 让编译器改发 `JUMP_FORWARD`」才是真差异（true_diffs） | `cbcmp.py` 对 json_persistance |
| **CPython 结构事实（本轮实测）**：源码**零 return** 的 `def f(): try: if: with…else: … except: …` 会为每条离开函数的路径各发一份隐式 `LOAD_CONST None; RETURN_VALUE`（本例 4 份），且行号归属到该路径最后一句 | `synth_persist.py` variant `B_noret` ret=[36,49,57,79] == orig |
| 显式 `return None` 会额外插一个行标 `NOP`；`if x: return None`/`except…: return None` 与 `pass`/省略 **bytecode 完全等价**（elision），但「handler 之后还有代码」的 return 必然开新行 | 本轮 CPython 实测 |
| `block.predecessors` 是 **set**；`line_number_table` 是 offset→行 的 dict（行 = 最大 key ≤ offset）；`block.instructions` 无 `positions` | 探针多次踩到 |
| `>` 重定向写 UTF-16；脚本日志一律 Python 内 `io.open(...,'w',encoding='utf-8')` | 多次 |

## 1. 单元根因表

| # | 单元 | 状态 | 根因 | 臂/spec |
| --- | --- | --- | --- | --- |
| 1 | `fly/common/flytools.pyc :: ProcessWrite.modify_batcktes_info` | **已修，闭环全绿** | 两处：①`_extend_with_body_end` 把 normal-exit `__exit__` 块后的**隐式函数尾**收进 `with_blocks`，`_generate_with` 当源码 return 发射 ⇒ 多 1 个行标 NOP（235 vs 234，firstdiv idx151）；②except handler 的 4 份**编译器复制 exit copy**（`POP_EXCEPT*+LOAD_CONST+STORE_FAST+DELETE_FAST+RETURN`，四条控制流各一份、盖离开时所处行）被物化成 4 条源码 `return None`，而原源**无 return**（四尾 `T0@906 L1148 / T1@918 L1144 / T2@930 L1147 / T3@942 L1146` = 分支语句行） | `pad7_7` = `specs/pad7_5a2.json`(analyzer) + `specs/pad7_6b.json`(generator，3 edits) |
| 2 | `IQEngine/…/plugin_system_persist/json_persistance.pyc :: persist` | **非靶单，但被 pad7_6 打破；pad7_7 已复原** | 见 §2 | `specs/pad7_5a2.json` 的 P5 |
| 3 | `IQCommon/util/trade_info_utils.pyc` ×3 | 未定 | 三单都是条件跳转目标在两个 `LOAD_CONST None; RETURN_VALUE` 块间互换 | `pad7_1`/`pad7_2` 两次尝试均 pylingual 35/41 且新增 `check_trade_name` 失败，**不得合并** |
| 4 | `IQEngine/…/function.pyc :: reconnect` | 未定 | 假说：条件块 false-target == then 路径终点跳转目标 ⇒ 该目标是 merge，不得转 elif（orig `JUMP_FORWARD→148` vs prod `→174`） | — |
| 5 | `fly/data/quote.pyc :: check_frequency / run_tick_socket`、`load_get_price` | 未定 | firstdiv 见下 §3 | — |
| 6 | `…/trade_live_broker.pyc :: etf_basket_order / _sync_worker` | 未定 | firstdiv 见下 §3 | — |

## 2. pad7_6 的回归与修正（本轮最重要发现）

`pad7_6` = `specs/pad7_5a.json`(I1 判据) + `specs/pad7_6b.json`(I1 skip + I2 handler-copy 抑制)。

* flytools 达成 pylingual **66/66**（+1，零新增）。
* 但 all402 byte-diff 出现 **1 处新增失配**：`IQEngine/plugins/plugin_system_persist/json_persistance.pyc :: persist`（landed 7/7 → pad7_6 6/7），`true_diffs` 首条 index31 orig `LOAD_CONST` vs decomp `JUMP_FORWARD`。触犯 ADR-1。

### 2.1 根因（已定案）

原源 `persist` **零 return**（`synth_persist.py` 的 `B_noret` 复现 orig 的 4 份隐式尾 ret=[36,49,57,79]）。decomp 却要从 CFG 的 4 个 return 块里发射语句：

| 块 | 行 | 位置 | pad7_7 处理 |
| --- | --- | --- | --- |
| 164 | 64(=with 行) | `__exit__` 之后 = with 的 normal-exit 尾 | I1 抑制 |
| 190 | 64 | with 的 handler 尾（`POP_EXCEPT` 链之后） | **仍发射**（由父层 emit 成 `with` 后面那句 `return None`） |
| 234 | 67 | else 分支尾 | 现有逻辑已丢弃 |
| 344 | 70 | except handler 尾（无 `as` ⇒ 无 STORE/DELETE，I2 不命中） | 仍发射 |

* landed（3 条显式 return）→ 编译出 4 份 return + 1 个 NOP → 归一化后 78==78，`match=True`。
* pad7_6（抑制 164，剩 190、344）→ 编译器把 normal 路径改成 `JUMP_FORWARD` 跳到 190 那句 return ⇒ 少 1 条指令，`true_diffs` 非空，77≠78。
* flytools 不同：**它的 with handler 尾 return（块 748）就在 `region.blocks` 里**（`WithRegion.blocks` 含 748、`cleanup_blocks=[748]`），由 with 层自己吃掉、根本不进 `_generate_block_statements`；所以抑制 722 之后 fall-through 上**没有**后续 `return None` 可撞，编译器重建隐式尾 ✓。

### 2.2 判据修正 = P5（`specs/pad7_5a2.json`）

`_is_implicit_with_tail_return` 在原 4 条之后追加：

> **P5**：本 `WithRegion` 必须**拥有** with 语句的 post-handler 尾 return —— 在 `region.blocks ∪ region.with_blocks` 里存在**另一块**裸 `LOAD_CONST None; RETURN_VALUE`，其唯一前驱的最后指令是 `POP_EXCEPT`。
> 拥有 ⇒ 这一层自己负责该尾，`with` 之后父层不会冒出 `return None`，抑制 164 后 fall-through 直接到函数尾、编译器重建隐式尾；
> 不拥有 ⇒ 父层会把那条尾 emit 成 `with` 后面的语句，normal 路径撞上去，抑制只会把 `LOAD_CONST+RETURN` 变成 `JUMP_FORWARD`。
> 判据只读 region 自己的块集 + 前驱 + 前驱末 opcode，无函数名/文件名/偏移阈值/名字白名单/新 self 状态。

* flytools：`blocks` 含 748，748 前驱 742 末指令 `POP_EXCEPT` → **真** → 抑制（与 pad7_6 一致）。
* persist：`blocks`=[26,168,234,176,82,142,164]，唯一的裸 return 是 234，其前驱 194 是 `else` 体（末指令 `POP_TOP`）→ **假** → 不抑制（回到 landed 行为）。

## 3. 首分歧（10 靶单，`norm()` 归一后）

* `trade_info_utils`：`query_strategy_id` `→644`/`→648`、`query_trade_strategy_info` `→614`/`→618`、`kill_trade_process` idx551 `POP_JUMP_IF_NONE 3864`/`3868`。
* `quote :: check_frequency` idx76 `310 POP_JUMP_FORWARD_IF_FALSE 560` vs `→562`；`run_tick_socket` idx14 `66 →528` vs `EXTENDED_ARG 2; …IF_FALSE 1122`；`load_get_price` idx58 orig `282 …IF_FALSE 486` vs prod `POP_TOP`（产品侧整条 if 丢失）。
* `trade_live_broker :: _sync_worker` idx53 off362 `COMPARE_OP <` 后 `POP_JUMP_IF_TRUE 704` vs `IF_FALSE 562`；`etf_basket_order` idx604 off404 `IF_TRUE 634` vs `IF_FALSE 356`。
* `function :: reconnect`：orig `JUMP_FORWARD→148` vs prod `→174`。
* `flytools :: modify_batcktes_info`：idx151 `700 LOAD_CONST None` vs `700 NOP`（+1 NOP）；idx178 四条条件跳转目标置换（已修）。

## 4. 臂读数（闭环 a–e）

### `pad7_7` = `mbuild74.py pad7_7 specs/pad7_5a2.json specs/pad7_6b.json`（analyzer +102 行 / generator +110 行，BOM False/True 保留）

| 门 | 读数 | 结论 |
| --- | --- | --- |
| a mbuild74 | anchor 断言全过 | ✅ |
| b h62 `--list=dump/tgt5.txt` | trade_info_utils 40/40、flytools 65/65、function 71/71、quote 72/81、trade_live_broker 111/119（与 landed 同） | ✅ 不回退 |
| b′ h62 all402（8 分片） | landed 5717/5746 → pad7_7 **5717/5746**；mism 集合 cleared=0 new=0 | ✅ 零差异 |
| c′ mand74 `dump/fail74_full.txt`（35 文件 ×3 分片） | landed fail-units **76 → 75**；CLEARED 1 = `flytools :: ProcessWrite.modify_batcktes_info`；NEW 0 | ✅ |
| c″ mand74 `dump/tgt6.txt`（5 靶 + json_persistance） | flytools 65/66→**66/66**；persist 7/7→7/7；其余 4 文件不变 | ✅ |
| d h62 canary4 | sha16 = `3eb76e512df9ab1e` / `af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177` | ✅ 全中 |
| d′ `closeout69.py battery landed pad7_7` | `candidate columns worse-than-landed on 0 repro(s)` | ✅ |
| e `sstrict67.py build_pad7_7 <strict_list74>` | landed 75 defects → pad7_7 **75**；cleared 0 / new 0 | ✅ |
| g 合并臂 `padm` | 未跑（待 10 单齐或按批跑） | 待 |

### 被否的臂（保留作证据）

* `pad7_1`、`pad7_2`（trade_info_utils 尝试）：pylingual 35/41，新增 `check_trade_name` 失败。
* `pad7_5`（I1+skip，未加 P5）：flytools 通过，但 all402 byte-diff 新增 `json_persistance::persist` 失配 → **ADR-1 弃臂**。
* `pad7_6`（I1+skip+I2，未加 P5）：同上，`dump/h62_6_402.json` mismatch 30 vs landed 29。

## 5. 复现/探针（`dump/`）

`probe5d.py`（I1 决策日志）、`probe6.py`（region 块集/前驱/prev-nop 事实）、`probe7.py`（全函数 return 块清单）、`probe8.py`（哪些块真的进 `_generate_block_statements`）、`probe9.txt`（region 属性 dump）、`synth_persist.py`（CPython 源码形状 → bytecode 对照）、`cbcmp.py`（逐函数 compare_bytecode）、`both.py`（首分歧）、`mkp7.py`（生成 `pad7_5a2.json`）、`h62_*_402.json`、`md7_7_*`、`strict_*74.json`、`batt_77.txt`。


## 6. kill_trade_process 配对裸 return 的形态枚举与互斥证明（交中心 ADR-1）

三把尺对同一函数结论互相冲突，先把**全部候选形态**摆全（指令数 = dis.get_instructions 计数；
pylingual = pyc_verify.py single 对该形态产物的判读；证据 dump/mkcand3/4/5.py、dump/c5..c11.py、dump/vt.py）：

| 形态 | 指令数 | pylingual | 备注 |
| --- | --- | --- | --- |
| **b1 = F+G 现形态**：if A: <链> else: R1 + 之后 R2 | **674** | **PASS（tiu 36/41 → 39/41）** | 与 landed 唯一差 = 多 1 条 JUMP_FORWARD |
| b4 = landed 形态：<链> else: R1 + 中段 else: R2（= c5） | 673 | FAIL | 两条裸 return 的跳转目标互换 |
| b7 = then 尾 trailing R2 + else: R1 | 673 | FAIL | 互换 |
| c11 = 中段 if A: <链> else: R1、无 trailing | 673 | FAIL | 互换 |
| c8 / c9 = if x is None: R1 内联在链前 | 672 | FAIL | R1 落到链前 |
| c10 = <链>; if x is None: R1; R2 | 678 | 未跑 | 相对 674 为 +5 |

**形式化互斥（为什么 673 一族必然 FAIL）**
ORIG 要求两条边同时成立：A-假 → R1（R1 在链**之后**）与 链-假 → R2。
若 R1 是 mid-else，则 链-假 必须**跳过** R1 才能到 R2；CPython 对「跳过一个 4 字节裸 return」
只会发一条前向无条件跳转，因此该形态的指令数必为 674。任何 673 形态都省掉了这条跳转 ⇒
两个跳转目标必然互换（实测 3274/3602 各自指向对方的 4 字节块）。
**pylingual PASS ⟺ 674 ⟺ sstrict seq_len 577 → 578。**

### 6.1 三把尺的读数（同一函数）

| 尺 | landed | pad7_89 |
| --- | --- | --- |
| pylingual（权威） | kill_trade_process FAIL（tiu 36/41） | **PASS**（tiu 39/41） |
| h62 ytecode_diff | tiu 40/40 | tiu 39/40（kill 573 vs 572，jump_diffs=4） |
| sstrict seq_len | 577 | **578（+1）** |

> **【给中心 ADR-1 的移交项】** G4p 的 
ewdef 集合将包含 kill_trade_process
> （sstrict seq_len 577→578，dump/st_arm.json 中唯一 NEW）。本轮**不改** sstrict 判据、
> **不改** gates 判据、不改任何 ADR 裁决；仅记录互斥证据，由 ADR-1 终裁。

## 7. Edit D（配对裸 return 的「后者=函数收尾」判据）的二次收窄

### 7.1 隔离过程

pad7_89b（A+C+F+Gv2，**无 D**）→ exception 3/3 全绿、flytools 65/66 绿，但 tiu 掉到 **37/41**
（kill_trade_process + query_trade_strategy_info 双挂）；pad7_89（+D）→ tiu **39/41**，但
IQCommon/IQData/IQEngine 三处 exception.pyc 各新增 1 处失败。

逐臂矩阵 + dump/patchD.py 探针（向镜像插 D74 cb=… else_blocks=… then_n=… cand=… 日志）把
D 的命中点钉死为 4 处：

| 站点 | cb | then_n | cand | then 臂内有无异常边 | 结果 |
| --- | --- | --- | --- | --- | --- |
| IQCommon/exception.pyc :: ModifyExceptionFromType.__exit__ | 0 | 4 | 218 | **无**（全为 getattr/setattr 普通调用） | D 命中 ⇒ 新增 else: return None ⇒ pylingual 33/34 |
| 	rade_info_utils :: kill_trade_process | 3270 | 9 | 3868 | **有**（两段 	ry: os.unlink…） | 必须命中 |
| 	rade_info_utils :: query_trade_strategy_info | 0 | 15 | 618 | **有**（	ry/with FileLock） | 必须命中 |
| 	rade_info_utils :: query_strategy_id | 0 | 10 | 376 | **有**（	ry/with FileLock） | 必须命中 |

### 7.2 收窄判据（同层结构身份，只读本函数 CFG）

在原判据上追加一条：**then 臂内至少存在一个带 exception_successors 的块**（CPython 只在源码真有
	ry/except 时才给臂内块挂异常表边）。

* 臂内**零异常边** ⇒ 该收尾块只是本 if 语句自身的**短路落点**（or/and 链的 POP_JUMP_* 目标），
  不是源码语句；摘出它会连带把 else 臂从隐式续行块升格成显式 else: return None，重编译多出一条
  else 控制流（__exit__ 实测正是如此）。
* 臂内**有异常边** ⇒ try/with 的正常出口必须汇到一条写在 if/else 之后的语句上，收尾块是真源码语句。
* 判据只读块的异常表边；**无**函数名/文件名/偏移阈值/名字白名单/新增 self 状态/跨层 
egion.entry in r.blocks。

### 7.3 收窄后读数（pad7_89 = specs/pad7_8 + specs/pad7_9，analyzer +144 / generator +94 行）

| 门 | 读数 | 结论 |
| --- | --- | --- |
| b h62 --list=dump/tgt35.txt | TALLY SAME=31 IMPROVED=0 REGRESSION=1 MOVED=3 ERR=0；files fully matched a=27 b=26 | REGRESSION 仅 	rade_info_utils 40/40→39/40（§6 已裁） |
| b′ h62 canary4 ab | SAME=4 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0 | ✅ sha16 3eb76e512df9ab1e / f77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177 全中 |
| c mandcheck.py build_landed build_pad7_89 | **TOTAL failures base=36 arm=33**，六文件 ixed/new 里 **new 全为空**；tiu -kill_trade_process,-query_strategy_id,-query_trade_strategy_info | ✅ 零新增 |
| c′ exception ×3 逐个 pyc_verify | IQCommon 34/34、IQData 31/31、IQEngine 31/31，均与 landed 同 | ✅ 回归消除 |
| d sstrict67.py build_pad7_89 dump/tgt41.txt | landed 74 defects → arm **75**；**NEW = 仅 kill_trade_process seq_len orig=577 decomp=578**，GONE = 空 | 交 §6.1 ADR-1 |
| e closeout69.py battery landed pad7_89 | candidate columns worse-than-landed on 0 repro(s) | ✅ |
| f flytools | h62 65/65；pylingual 65/66（存量 ProcessWrite.modify_batcktes_info） | ✅ 无新增 |

### 7.4 产物与探针

specs/pad7_8.json（edits 4，delta 144）、specs/pad7_9.json（edits 4，delta 94）、
dump/h62_c_t35.jsonl / h62_c_t41.jsonl / h62_c_can.jsonl / h62_v2.jsonl、
dump/st_arm.json vs dump/st_landed.json、dump/dec_{landed,pad7_89,pad7_89b,pad7_89nd,pad7_8D}_*.txt、
探针 dump/patchD.py（D74 日志）、dump/nod.py（把 D 关掉的镜像 mirr_pad7_89nd）、dump/dec.py、
dump/disall.py、dump/vmar.py（arm vs landed 的 pylingual 对读）。
