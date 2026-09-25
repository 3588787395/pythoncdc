# FACTS · Round 69 · diag5（只读诊断代理）

工作区：D:/Temp/opencode/r69gate/diag5
仓库：F:/Downloads/pythoncdc-main（只读）
名下靶支：
- site-packages/IQCommon/util/trade_info_utils.pyc（official 39/40，strict 37/41，缺陷 4）
- site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc（official 33/35，strict 34/37，缺陷 3）

---

## Step 0 · baseline replay

### 0.1 official（h62 run --arm=landed --list=targets.txt → dump/landed.jsonl）
| 文件 | matched/total | mism |
|---|---|---|
| trade_info_utils.pyc | **39/40** | `[['trade_operation', 304, 302, 2, 40]]` |
| plugin_system_risk_calculation/__init__.pyc | **33/35** | `[['_on_publish_after_trading_end',486,481,3,33], ['_save_testds_to_csv',71,68,7,19]]` |

与 targets.md 预读数：**逐字段相同**（39/40 gap1；33/35 gap2；hunks 2/3/7；first_diff 40/33/19）。✔

### 0.2 canary（h62 run --arm=landed --list=canary.txt → dump/landed_canary.jsonl）
| 文件 | matched/total | mism |
|---|---|---|
| fly/data/quotation.pyc | 143/143 | [] |
| fly/common/market_time.pyc | 10/10 | [] |
| IQCommon/util/datetime_func.pyc | 26/26 | [] |
| IQData/utils/datetime_func.pyc | 25/25 | [] |

与 ADR 合同 4 支 sha 基线：matched 全平，mism 为空。✔

### 0.3 45 项电池（closeout67.py battery landed）
- 复现件发现数 **45**；合计 **182/200**、缺陷函数 **bad 合计 18**、`worse-than-landed on 0 repro(s)`（本轮为 landed 自比）、ERR=0。
- 与 BRIEF §4：182/200、缺陷 18、worse=0、ERR=0 —— **逐字段相同**。✔

### 0.4 严格尺（sstrict67.py build_landed targets.txt → dump/strict_landed.json）
| 文件 | strict | 缺陷明细 |
|---|---|---|
| trade_info_utils.pyc | **37/41** missing=0 extra=0 | get_trade_status [target_diff] #70 FOR_ITER；get_trade_unit_info [seq_len] 240/241；set_trade_status [target_diff] #113 JUMP；trade_operation [seq_len] 304/302 |
| __init__.pyc | **34/37** missing=0 extra=0 | _on_publish_after_trading_end [seq_len] 488/481；_on_set_positions [seq_len] 297/298；_save_testds_to_csv [seq_len] 75/68 |
| TOTAL | 71/78，缺陷 7 | |

与 targets.md 预读数：**逐字段相同**。✔

**Step 0 结论：全部与 brief/targets 预读数逐字段相符，无需更正。**


---

## Step 1 · hunk tables（nested_diff.py，按 code-object 全路径配对）

### 1.1 IQCommon/util/trade_info_utils.pyc  vs build_landed/IQCommon__util__trade_info_utilsOK.py
`TOTAL differing code objects: 4 of 41`

| code object 路径 | orig/decomp | 归一化 hunks | 内容 | 判定 |
|---|---|---|---|---|
| `<root>`（模块级） | 396/390 | 2 | delete NOPx3 @orig325、delete NOPx3 @orig335 | **NOP 计数伪影**（模块级两处各 3 个 NOP；官方/严格尺均未把它记为缺陷） |
| `/trade_operation#32` | 339/337 | 1 | delete orig[296:298]=`LOAD_CONST None, RETURN_VALUE` | **真缺陷**（官方 OFF trade_operation 304/302 hunks=2 first_diff=40；decomp 少 2 条：末尾 return 被吃掉） |
| `/get_trade_unit_info#44` | 273/274 | 2 | replace orig[254:256]=`EXTENDED_ARG,JUMP_BACKWARD`→decomp[254:255]=`JUMP_FORWARD`；insert decomp[270:272]=`EXTENDED_ARG,JUMP_BACKWARD` | **真缺陷**（回边重放置，BRIEF §8 签名 (c) 族；strict seq_len 240/241） |
| `/set_trade_status#67` | 180/179 | 1 | delete NOP @orig109 | 计数差是 **NOP 伪影**；但严格尺另有真缺陷 **[target_diff] #113 JUMP 终点**（nested_diff 把跳距归一成 `J`，看不见） |
| （get_trade_status） | 无 diff | 0 | — | nested_diff 无差异；真缺陷是严格尺 **[target_diff] #70 FOR_ITER 终点**（跳目标归一化后不可见） |

### 1.2 IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc vs build_landed/...__init__OK.py
`TOTAL differing code objects: 3 of 43`

| code object 路径 | orig/decomp | 归一化 hunks | 内容 | 判定 |
|---|---|---|---|---|
| `/PluginRiskCalculation#18/_on_set_positions#9` | 336/337 | 2 | replace orig[256:258]=`EA,JUMP_BACKWARD`→decomp[256]=`JUMP_FORWARD`；insert decomp[302:304]=`EA,JUMP_BACKWARD` | **真缺陷**（签名 (c) 回边重放置；strict seq_len 297/298，官方已平） |
| `/PluginRiskCalculation#18/_on_publish_after_trading_end#10` | 531/523 | 2 | delete NOP @482；replace orig[491:499]=`JUMP_FORWARD, LOAD_GLOBAL time, LOAD_ATTR sleep, LOAD_CONST 0.01, PRECALL, CALL`(→8条) → decomp[490]=`NOP`(1条) | **真缺陷**：decomp 丢了 `time.sleep(0.01)` 语句（官方 486/481 hunks=3 first_diff=33、严格 488/481） |
| `/PluginRiskCalculation#18/_save_testds_to_csv#28` | 81/75 | 7 | ①insert decomp NOP@16 ②replace orig[37]`JUMP_BACKWARD`→decomp[38]`JUMP_FORWARD` ③delete `LOAD_CONST 0`@58 ④delete `IMPORT_NAME …, IMPORT_FROM THREAD_STATUS`@60:62 ⑤delete `POP_TOP`@63 ⑥replace orig[66:68]=`LOAD_CONST None, RETURN_VALUE`→decomp[63]=`JUMP_FORWARD` ⑦delete orig[79:81]=`LOAD_CONST None, RETURN_VALUE` | **真缺陷，且一函数内同时命中 R67-diag6 三签名**：(c)②回边丢失、(b)④⑤ `IMPORT_FROM THREAD_STATUS` 被物化成 STORE+if、(a)⑥ `JUMP_FORWARD`↔`LOAD_CONST None/RETURN_VALUE` 互换（R47 禁令约束 Expr→Return） |

**Step 1 结论**：4 处纯 NOP 伪影（模块级 x2、set_trade_status x1、_save_testds x1、_on_publish x1 共 5 处 NOP 行）；真缺陷集中在 4 个函数体：trade_operation（尾 return 丢失）、get_trade_unit_info/_on_set_positions（回边重放置 (c)）、_on_publish_after_trading_end（sleep 语句丢失）、_save_testds_to_csv（三签名齐全）；另 get_trade_status/set_trade_status 为跳目标 target_diff（仅严格尺可见）。

---

## Step 2 · 根因（已实测锁定 / 进行中）

### 2.1 trade_operation（official 304/302，Δ2 = \LOAD_CONST None; RETURN_VALUE\ 被吃）

**CFG 事实（orig .pyc，cfg=build_cfg(trade_operation)）**
| block | 指令 | pred | succ | 归属 |
|---|---|---|---|---|
| 350 | \os.path.exists\ + PJIF→1468 | 348 | 1468,1526 | IfRegion@350 entry/condition |
| 414..1438 | with 体（13 个 then 臂块） | — | — | IfRegion@350.then_blocks / WithRegion@414 |
| 1438 | \LOAD_CONST False; RETURN_VALUE\ | 1416 | [] | then 臂末（sink） |
| 1442 | PUSH_EXC_INFO, WITH_EXCEPT_START, PJIF | 全部 then 臂块 | 1448,1450,1456 | **with 异常处理（不属 then 臂）** |
| 1456/1458 | POP_TOP / POP_EXCEPT,POP_TOP,POP_TOP | 1442 | 1458 / **1464**,1526 | with 抑制清理（**不属 then 臂**） |
| **1464** | **\LOAD_CONST None; RETURN_VALUE\** | 1458 | [] | try 体孤立平凡 return |
| 1468 | \pp_log.warning(文件不存在)\ | **350** | 1522,1526 | 条件 false 入口（被分析器当 merge） |
| 1522 | \LOAD_CONST False; RETURN_VALUE\ | 1468 | [] | 
eturn False |
| 1526 | except 匹配块（异常表边） | 1450,414,1468,350,1334,1416,1458 | — | handler 入口 |

- IfRegion@350: \	hen=[414…1438]\(30 块)、\else=[]\、\merge=1468\；TryExceptRegion@350.try_blocks 含 1464。

**根因 A（直接丢语句点）**：\core/cfg/region_ast_generator.py:24694–24757\（\_generate_try_body\ 的 trivial-return 分支）对 block 1464 判定 \_is_trivial_return=True\ 后三条发射条件全为假：
1. \_is_cond_jump_target=False\（唯一 pred 1458 末指令是 POP_TOP，非条件跳转）；
2. \_loop_depth==0\；
3. \_is_inlined_ret=False\ —— \[F-TRY-BODY-RETURN]\ pass（:24394–24416）在 24396 行对「已在 \_try_blocks_eff\」的块直接 \continue\，1464 因本就在 egion.try_blocks\ 内被跳过，永远进不了 \_inlined_ret_offsets\。
→ :24757 \generated_blocks.add(block); continue\ **消费而不发语句**，违反 :18334 自述的「每块唯一归属：块属于此区域但语句被丢弃」。

**根因 B（结构判定）**：\core/cfg/region_analyzer.py\ 既有规则 \_if_arm_is_sink\（:26703）把 then 臂判为汇点（臂内块全部 RETURN/RAISE 结束、异常边被 \_exc\ 跳过），调用侧据此置 \merge := 对侧入口(1468)\、\else_blocks=[]\、AST=\If(test, T, [])\，false 臂降级为 if 之后的兄弟语句序列。**副作用**：with 的异常抑制路径 1458→1464 在兄弟形态下会落进兄弟语句，编译器因此不再需要那个隐式 eturn None\，原 .pyc 里的 1464 就再也生不出来。

**两个手工变体（均已实测）**
| 变体 | 源形状 | official | nested_diff(trade_operation) | orig↔变体指令逐条比 |
|---|---|---|---|---|
| dump/else_variant.py | if: with… + else: warn; return False | **40/40** | 无差异 | 339 vs 339，仅 1 处跳目标（PJIF to 1000 vs 	o 1042） |
| dump/retnone2_variant.py | if: with…; return None（12sp）+ 兄弟 warn; return False | **40/40** | 无差异 | 339 vs 339，同上 1 处跳目标 |
| dump/retnone_variant.py（8sp，已否决） | 
eturn None 落在 if 之外 | 39/40（更差） | 丢整段 warning（delete orig[298:313]） | — |

**关键实测**：else_variant 与 
etnone2_variant 编译后指令序列 **完全相同**（equal=True，len 339/339）→ 两种形状在字节码层等价；缺的只是「既没有 else、也没有 return None」的当前落地形状（302 条，少 2 条）。
（待续：根因 C/D = _on_publish_after_trading_end、_save_testds_to_csv）

### 2.2 _on_publish_after_trading_end（official 486/481，hunks 3，Δ-5）

**源 vs 产物**（build_landed/…____init__OK.py L252-255）：
\# 产物                       # orig 源（L381-386，由字节码行号反推）
if is_end:                   if is_end:
    from ... import THREAD      while True:
    if THREAD_STATUS:               from ... import THREAD_STATUS
        pass                         if THREAD_STATUS:
                                         break
                                     time.sleep(0.01)
\orig 字节码（L381=2746 NOP、L382=import、L383=\if THREAD_STATUS\、L384=\reak\(JUMP_FORWARD→2808)、L386=\	ime.sleep(0.01)\、2806 JUMP_BACKWARD→2748）。
**丢的正是 8 条**：NOP(2746 头) + JUMP_FORWARD(break) + time.sleep 五条 + JUMP_BACKWARD → 与 nested_diff \delete NOP@482\ + eplace orig[491:499]→decomp[490]\ 完全对上（-1 + (1-8) = -8）。

**区域事实**（generate() 后）：
| region | entry | blocks/body | 备注 |
|---|---|---|---|
| LoopRegion | **2748** | body=[2746,2748,2764,2766] | \while True\（2746=头 NOP，2766=sleep+回边） |
| IfRegion | **2748** | blocks=[2748,2764] then=[2764] merge=2766 | \if THREAD_STATUS: break\ |
| IfRegion | 2686 | then=[2748] merge=2808 | \if is_end:\ |

**根因（实测）**：\core/cfg/region_analyzer.py::get_entry_region_for_block\ 的同 entry 多区域裁决：\_type_priority = {'WithRegion':6,'TryExceptRegion':5,'MatchRegion':4,'BoolOpRegion':3,'TernaryRegion':3,'IfRegion':2,'LoopRegion':0}\，升序排序取 \_matching[-1]\ → **IfRegion(2) 压过 LoopRegion(0)**。block 2748 同时被 LoopRegion@2748 与 IfRegion@2748 认领（\while True\ 的回边落点恰好是「import + if THREAD_STATUS 测试」共处的同一基本块），裁决取 IfRegion。
\probe_loop.py\ 追踪：\generate → _generate_if(2686) → _if_generate_then_branch → _process_if_blocks → _generate_region(IfRegion 2748)\，**LoopRegion@2748 全程未被派发**；生成后 \generated_blocks\ 仅有 2748/2764/2808，**2746、2766 从未生成** → \while True:\/\reak\/\	ime.sleep\/\JUMP_BACKWARD\ 一并消失，块 2764 的 break 落成 \pass\。

### 2.3 _save_testds_to_csv（official 71/68，hunks 7）

**产物**（L535-552，三签名齐全）：
\while True:
    while not self._stop_save_csv_thread:
        try: is_end, daily_result = self.daily_result_list.get(timeout=1)
        except Empty: pass
        csv_writer(daily_result, is_end)
        if is_end: break
    while not self._stop_save_csv_thread:
        THREAD_STATUS = ('THREAD_STATUS',)      # ← 应为 from ... import THREAD_STATUS
        if THREAD_STATUS: break
        time.sleep(0.01)
    break
\| 签名 | 位置 | 现象 |
|---|---|---|
| (b) import 物化 | orig[58]\LOAD_CONST 0\、orig[60:62]\IMPORT_NAME,IMPORT_FROM THREAD_STATUS\、orig[63]\POP_TOP\ 全删 | \rom ... import THREAD_STATUS\ 被物化成 \THREAD_STATUS = ('THREAD_STATUS',)\ |
| (c) 回边重放置 | orig[37]\JUMP_BACKWARD\ → decomp[38]\JUMP_FORWARD\ | 某循环回边变成前向跳转 |
| (a) 尾部 Expr/Return 互换 | orig[66:68]\LOAD_CONST None,RETURN_VALUE\ ↔ decomp[63]\JUMP_FORWARD\；orig[79:81]\LOAD_CONST None,RETURN_VALUE\ 被删 | 两条尾部 return 丢失 |

（2.3 逐块根因未完成——尚未定位 import 物化与回边丢失的具体代码路径。）

### 2.4 签名 (b)「import 物化」根因（锁定，已实测）
**现象**：rom ...function import THREAD_STATUS 被反成 THREAD_STATUS = ('THREAD_STATUS',)，并丢 LOAD_CONST 0(level)、IMPORT_NAME、IMPORT_FROM、POP_TOP（nested Δ-4）。
**定位手段**：monkeypatch _build_store_statement 打印带 IMPORT_NAME 的调用栈 →
\_generate_region → _generate_loop → _loop_generate_while(6396) → _loop_generate_body(6935) → _loop_dispatch_block(7422) → _loop_handle_header(8013) → _loop_process_header_instructions(9850)\。
**根因**：\core/cfg/region_ast_generator.py:: _loop_process_header_instructions\（:9752–9913）**没有 IMPORT_NAME/IMPORT_FROM 分支**。\LOAD_CONST level + LOAD_CONST fromlist + IMPORT_NAME + IMPORT_FROM\ 全被累进 _hdr_instrs，到 \STORE_FAST\（:9820）交给 _build_store_statement → 退化成 X = ('X',)（正是 :7110–7114 注释自述的失败模式），IMPORT 三条被静默丢弃。
同族两处**都有**该分支并互相注明「镜像」：\_loop_extract_for_iter_pre_stmts\（:7115–7134）、\_loop_extract_pre_stmts_from_block\（:7287–7306）——唯独 header 处理器缺。
**实测（monkeypatch 补该分支后重新整支反编译）**：
| 文件 | official before | official after | nested hunks |
|---|---|---|---|
| risk_calc \_save_testds_to_csv\ | 71/68（true_diffs 19） | **71/70（true_diffs 11）** | 7 → **4** |
| risk_calc \_on_publish_after_trading_end\ | 486/481 | 486/481（不变，其 import 不在 header） | 3 → 2 |
| trade_info_utils \	rade_operation\ | 304/302 | 304/302（无副作用） | 不变 |
→ **候选 A（cand_r69_loop_hdr_import）**：给 \_loop_process_header_instructions\ 补 IMPORT 分支（三要素齐：识别条件=header 指令流中 \IMPORT_NAME\ 及其后 ≤3 条内 \IMPORT_FROM\ + 随后 \STORE_*/POP_TOP\ 收尾；归约方式=\_process_instruction(IMPORT_NAME)\ 产出 ImportFrom 推入 \_hdr_stmts\、清空缓冲、跳过收尾指令；AST=\ImportFrom(module, names, level=0)\）。同层次（单块指令流）、无名字/偏移启发、无新 self 状态。
_save_testds_to_csv 剩余 4 hunks：①NOP 伪影 ②\JUMP_BACKWARD→JUMP_FORWARD\(c) ⑥\LOAD_CONST None,RETURN_VALUE ↔ JUMP_FORWARD\(a) ⑦尾 eturn None\ 丢失(a)。

---

## Step 3 · 合成复现（synth/）

**形状筛选实测**（`probe_synth5.py`：每个形状编 .pyc → 反编译 → 记录 `_loop_process_header_instructions` 是否被调用 + 是否出现 `x = ('x',)`）：

| 形状 | `phi` 调用数 | 物化 `exists = ('exists',)` | import 正常 |
|---|---|---|---|
| `try_A`（`while True:` + import + `if x: break`，末尾无其它语句） | 0 | 是 | 否 |
| `t_n2`（`while True:` + import + `if x:break` + `time.sleep` + `if stop:break`） | 1 | **是** | 否 |
| **`t_n3`（`while not stop:` + import + `if x:break` + `g()`）** | **1** | **是** | **否** |
| `t_n1`（外 `while True` 包内 `while not stop` + import） | 0 | 否 | 是 |
| `t_n4`（`while True` + `try/except` + import） | 1 | 否 | 是 |
| `t_n5`（`while True` + import + `if x:break` + 内层 `while` + `break`） | 0 | 否 | 是 |

→ **最小合成复现 = `synth/t_n3.py`**（须满足「header 块内既有 import 又有跳转」才走 `_loop_process_header_instructions`；
`try_A` 虽同样物化，但走的是 `_loop_handle_header` 的另一条早退路径，**与本候选不同源**，故排除、只作对照）。

`t_n3.py` 源：
```
def f(stop):
    while not stop:
        from os.path import exists
        if exists:
            break
        g()
```

**失败签名（landed / head 臂）**：`matched 1/2`、`[['f', 18, 18, 1, 15]]`，产物写成
`exists = ('exists',)`（`LOAD_CONST 0` / `IMPORT_NAME os.path` / `IMPORT_FROM exists` / `POP_TOP`
四条全丢，`IMPORT_NAME+IMPORT_FROM` 被并进 `_hdr_instrs` 后在 `STORE_FAST` 交给
`_build_store_statement`）。

**名单**：`synth/listA.txt`（`t_n3.pyc` / `t_n2.pyc` / `try_A.pyc`）。

---

## Step 4 · 候选与 A/B

**spec**：`specs/cand_r69_loop_hdr_import.json`（`mk_spec_r69a.py` 生成；anchor = 
`region_ast_generator.py` 9811–9819 的 `UNPACK_EX` 分支，**count==1 已实测**；+33 行，BOM/CRLF 归一）。
**臂名**：`r69diag5_loopimport`（`h62.py build --spec=… --dst=r69diag5_loopimport`）。
**landproof**：`mirr_head` 33 core 文件 **same=33 diff=0**（与仓库字节一致）；
`mirr_r69diag5_loopimport` same=32 **diff=1**（仅被 patch 的 `region_ast_generator.py`）。

**三要素（已写进 spec 插入块的注释）**
- **识别条件**（同层次·单块指令流）：本 header 块指令序列中出现 `IMPORT_NAME`；其前两条是该
  import 的 `LOAD_CONST level` / `LOAD_CONST fromlist` 实参；其后为 `IMPORT_FROM`/`IMPORT_STAR`，
  再由 `STORE_*` + `POP_TOP` 收尾。全部读本块自身字段，不跨区域、不按名字/偏移/计数阈值、不新增 self 状态。
- **归约方式**：`IMPORT_NAME` → `self._process_instruction(instr, block, [])` 产出 ImportFrom 推入
  `_hdr_stmts` 并清空 `_hdr_instrs`；`IMPORT_FROM`/`IMPORT_STAR` 属该语句组成部分，清缓冲后跳过；
  后续 `STORE_*` 到达时缓冲已空 → `_build_store_statement` 因 `value_instrs` 为空返回 `None`
  （`region_ast_generator.py:49853/49887`），`POP_TOP` 走既有「缓冲为空」分支被跳过。
  **发射次序不变、无「先发射后正则修文本」。**
- **AST 映射**：`ast.ImportFrom(module=…, names=[alias], level=0)`，作为该循环 header 的前缀语句，
  与 header 内后续的 break 条件 `if` 同层。
- **同构依据**：与本文件 `_loop_extract_for_iter_pre_stmts`（:7115–7134）、
  `_loop_extract_pre_stmts_from_block`（:7287–7306）两处**既有**同一分支逐条镜像；本改动只是把
  已存在的分支补到缺失的 header 处理器（:9752–9913），**不新建谓词**。

### 五列读数

| 列 | 臂/工具 | 读数 | 判定 |
|---|---|---|---|
| **targets（official）** | `h62 run --arm=r69diag5_loopimport` | trade_info_utils **39/40**（`trade_operation 304/302,2,40` 不变）；risk_calc **33/35**（`_on_publish 486/481,3,33` 不变；**`_save_testds_to_csv [71,68,7,19] → [71,70,7,11]`**） | 文件级 official 计数未变（2+1 个缺陷函数仍在），单函数真差 19→11 |
| **canary** | `h62 run --list=canary.txt` | quotation **143/143**、market_time **10/10**、IQCommon datetime_func **26/26**、IQData datetime_func **25/25**，四支 TALLY **SAME=4** | 通过 |
| **canary sha（合同 1）** | sha256(LF 归一)[:16] | `4d41187e356544e0` / `af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177` —— **landed / head / r69diag5_loopimport 三臂全部逐字节相同且全等于 pin** | **通过** |
| **battery** | `closeout67.py battery landed r69diag5_loopimport` | 45 项逐项对比，`candidate columns worse-than-landed on 0 repro(s)`，ERR=0 | **通过** |
| **strict** | `sstrict67.py build_r69diag5_loopimport targets.txt` | trade_info_utils **37/41**（4 缺陷逐字不变）；risk_calc **34/37**（`_on_publish 488/481`、`_on_set_positions 297/298` 不变；**`_save_testds_to_csv [seq_len] 75/68 → 75/72`**）；STRICT TOTAL **71/78 defects=7** | ok 计数未变，但 seq_len 族 \|Δ\| 收敛 |
| **synth** | `h62 ab` landed vs cand | `t_n3 1/2 → 2/2`、`t_n2 1/2 → 2/2` **IMPROVED**；`try_A 1/2 → 1/2` SAME（非本路径）；TALLY SAME=1 **IMPROVED=2** REGRESSION=0 ERR=0 | **咬合（landed 失败 / 本臂通过）** |

### ADR-1 判据核算（两支名下）
- **缺失/过冲族（seq_len）Σ|orig−decomp|**：
  - trade_info_utils：`get_trade_unit_info 1` + `trade_operation 2` = **3 → 3**（不变）
  - risk_calc：`_on_publish 7` + `_on_set_positions 1` + `_save_testds 7→3` = **15 → 11**
  - 合计 **18 → 14，净减少 4** ✔；且 decomp 条数 **68 → 72**（朝 75 靠），**不是以少发射换** ✔
- **纯位移族（target_diff）**：`get_trade_status #70 FOR_ITER`、`set_trade_status #113 JUMP`
  两处逐字不变，**未新增 target_diff** ✔
- **nested hunks**：`_save_testds_to_csv` **7 → 4**（删掉 3 个 import 相关 hunk）；
  `trade_operation` 2 → 2；`_on_publish` 2 → 2；`_on_set_positions` 2 → 2（无新增）

### 剩余缺口（候选 A 未覆盖）
- `_save_testds_to_csv` 剩 4 hunks：①`insert NOP`（伪影）②`orig[37] JUMP_BACKWARD → decomp[38] JUMP_FORWARD`（签名 c）
  ⑥`orig[66:68] LOAD_CONST None/RETURN_VALUE ↔ decomp[67] JUMP_FORWARD`（签名 a）⑦`delete orig[79:81] LOAD_CONST None/RETURN_VALUE`（签名 a）。
- `_on_publish_after_trading_end`（Δ5 / 严格 Δ7）与 `trade_operation`（Δ2）**未被候选 A 触及**。

---

## Step 5 · 收口

### VERDICTS（逐靶支）

**① `site-packages/IQCommon/util/trade_info_utils.pyc`（official 39/40 → 39/40，strict 37/41 → 37/41）**
- **候选：NONE。**
- 本臂对这支**逐字节零影响**（official 元组 `[['trade_operation',304,302,2,40]]` 与 4 个严格缺陷全部不变）。
- 唯一剩余官方缺陷 `trade_operation seq_len 304/302` 的根因是 `_if_arm_is_sink`（`region_analyzer.py:26703`）
  判 then 为汇点 → `else=[]` + merge:=对侧入口 → 兄弟化，加上 `_generate_try_body` 的 trivial-return
  发射分支三条件全假（`region_ast_generator.py:24694–24757`，`:24757` 处消费不发语句）。
  **实测（不是推断）**：`dump/else_variant.py`（补 `else:`）与 `dump/retnone2_variant.py`（`return None` @12sp）
  反编译后指令序列**完全相同**（equal=True, len 339/339），official 均 **40/40**，仅与 orig 差 1 处跳目标
  （`PJIF to 1000` vs `to 1042`，official 不计）；`dump/retnone_variant.py`（`return None` @8sp）39/40 **更差，已否决**。
  **但至今找不到满足 §2 三要素的同层次判别子**：block 1464（`LOAD_CONST None; RETURN_VALUE`）**不在
  `then_blocks` 内**、是 WithRegion 抑制清理的唯一 pred(1458)，任何判据都必须跨 WithRegion 边界读
  `try_blocks`/跨层次字段 ⇒ 按「诚实 NONE 优于过重规则」（§8）**放弃候选**，只留证据链。

**② `site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc`
（official 33/35 → 33/35，strict 34/37 → 34/37）**
- **候选：`cand_r69_loop_hdr_import`（臂 `r69diag5_loopimport`），采纳条件全绿，但不关闭官方 gap。**
- 收益落在 `_save_testds_to_csv`（official `[71,68,7,19] → [71,70,7,11]`；strict `seq_len 75/68 → 75/72`；
  nested `orig 81/decomp 75 → 79`，hunks **7 → 4**）。
- 合同核对：①金丝雀 4 支 sha **全等于 pin**（landed/head/cand 三臂逐字节相同）✔
  ②45 项电池 `worse-than-landed=0`、ERR=0 ✔ ③ADR-1 seq_len 族 Σ|Δ| **18 → 14 净减 4**、
  非少发射换、未新增 `target_diff` ✔ ④锚点 `count==1`、无 ERR、无不可反编译 ✔
  ⑤合成见证 `t_n3`/`t_n2` landed **1/2** → 本臂 **2/2** ✔
  ⚠ **但「严格 ok 计数」71/78 未变**（该函数仍是 `seq_len` 缺陷，只是 |Δ| 由 7 收到 3），
  **官方文件级计数 39/40、33/35 也未变**——是否算「严格变好」请中心按 ADR-1 的 Σ|Δ| 口径裁定；
  我不主张它关闭 gap。

### 候选：`cand_r69_loop_hdr_import`（1 条）
- 文件：`specs/cand_r69_loop_hdr_import.json`；落点 `core/cfg/region_ast_generator.py`::
  `_loop_process_header_instructions`（def :9752–9913），anchor = :9811–9819 `UNPACK_EX` 分支（count==1），+33 行。
- 咬合合成：`synth/t_n3.py`（+ 对照 `synth/t_n2.py`），名单 `synth/listA.txt`。

### 被否决的候选（留档，未做成 spec）
- **候选 B「entry 优先级 LoopRegion vs IfRegion」**（`region_analyzer.py::get_entry_region_for_block` :27643–27676，
  `_type_priority` 中 IfRegion=2 > LoopRegion=0，升序取 `_matching[-1]`，次键为字节跨度）：
  monkeypatch 试跑（`dump/loopfix_riskcalc.py`）让 `_on_publish_after_trading_end` 由 **486/481 → 486/486**，
  但**官方仍 33/35**，且带来三个副作用：①循环头 import 被物化成 `THREAD_STATUS = ('THREAD_STATUS',)`
  （本候选 A 恰好可修）②`event_bus = self._engine.event_bus` 被吞进 `if is_end:`（缩进 16sp vs 正确 8sp，
  jump 目标改变，jump_diffs=2）③末尾多出 2×`return None`。且原试跑判据
  `IfRegion.blocks ⊆ LoopRegion.body` 是**跨区域跨层次包含**，直接违反 §2 ⇒ **不提交**。
- **签名 (a)（`JUMP_FORWARD` ↔ `LOAD_CONST None/RETURN_VALUE` 互换）**：BRIEF §8 已标注「受 R47 禁令约束」，
  且 `orig[79:81]` 是函数尾隐式 return（decomp 不写 `return None` 属正确行为）——未找到不撞禁令的判据，**放弃**。

### 对 BRIEF 的更正（中心请读）
1. **§0 Step 4 的严格尺命令缺目录前缀**：`sstrict67.py` 内部是 `os.path.join(GATE, sys.argv[1])`，
   必须传 **`build_<臂名>`**（如 `build_landed`），传裸臂名会 100% `NO-PRODUCT`。我实跑用的是
   `sstrict67.py build_head targets.txt` / `sstrict67.py build_r69diag5_loopimport targets.txt`。
2. **§3.1 的金丝雀 sha 口径**：实测为 **sha256(产物字节把 `\r\n` 归一成 `\n`) 的前 16 位十六进制**；
   直接 `sha256(raw bytes)[:16]` 会对不上（quotation 会得到 `d9b9a8b277a20f16`）。四支按 LF 归一后全部命中 pin。
3. **§8 对签名 (b) 的描述需修正**：不是「`IMPORT_FROM THREAD_STATUS` 被物化成 **`STORE_NAME`** + `if`」，
   实测是物化成 **`THREAD_STATUS = ('THREAD_STATUS',)`（`STORE_FAST`）**，丢失
   `LOAD_CONST 0(level)`/`IMPORT_NAME`/`IMPORT_FROM`/`POP_TOP` 四条（nested Δ-4）；调用栈是
   `_loop_generate_while(6396) → _loop_generate_body(6935) → _loop_dispatch_block(7422) →
   _loop_handle_header(8013) → _loop_process_header_instructions(9850) → _build_store_statement`，
   **根因是 `_loop_process_header_instructions` 缺 IMPORT 分支**（同文件 :7115–7134、:7287–7306 两处已有并互注「镜像」）。
4. **§6 的「当前站点」清单可补一行**：`_loop_process_header_instructions` def **:9752**、
   `_loop_handle_header` def **:7666**（IMPORT 路径调用点 :8013）、`_build_store_statement` def **:49851**
   （`if not instrs: return None` @:49853、`value is None → return None` @:49887）、
   `_loop_extract_for_iter_pre_stmts` IMPORT 分支 **:7115–7134**、
   `_loop_extract_pre_stmts_from_block` IMPORT 分支 **:7287–7306**。
5. **§5 补一条仪器陷阱**：`h62.py run` 与 `sstrict67.py` 读名单文件时若被 PowerShell
   `Set-Content -Encoding UTF8` 写入会带 **BOM**，首条路径会变成 `\ufeffD:\...` 直接 `Errno 22`；
   名单必须用 Python `io.open(..., encoding='utf-8')` 写（无 BOM）。
6. **合成复现的形状陷阱（对后续代理有用）**：`while True:` + `from m import x` + `if x: break`
   这个「最显然」的形状（`synth/try_A.py`）**不走** `_loop_process_header_instructions`
   （`_loop_handle_header` 在更早的分支返回），因而**不是**本缺陷的见证；必须让 header 块内**同时**
   含 import 与跳转才走该路径（`synth/t_n3.py` 满足：`while not stop:` + import + `if x: break` + `g()`）。
7. **Step 0 结论：与 BRIEF/targets.md 预读数逐字段相符，无需更正**（official 39/40、33/35，
   mism 元组与 hunks 2/3/7、first_diff 40/33/19 全中；canary 4 支全平；battery 182/200、缺陷 18、worse=0；
   strict 37/41 + 34/37 = 71/78 defects 7）。
8. **官方 gap 现状**：本轮候选 A **不改变**任何官方文件级计数（39/40、33/35 原样），累计 gap 仍为 **3**。
   本轮真正推进的是根因实测 + 合成复现 + 单函数真差 19→11 / |Δ| 7→3。
