# Round 68 · FACTS · diag3（只读诊断）

工作区 `D:/Temp/opencode/r68gate/diag3`；仓库 `F:/Downloads/pythoncdc-main` 只读。
命名前缀：臂名一律 `r68diag3*`；out 文件名一律带臂名（避开 h62 resume 语义）。

## Step 0 · baseline replay

| 靶支 | landed 读数 | BRIEF 预读 | 相符 |
|---|---|---|---|
| IQCommon/api/klinedata.pyc | 42/45 · get_all_real_daily_kline [188,187,jd3,td26] · get_multiminute_his_data [479,478,jd3,td16] · kline_datetime_list [389,389,jd9,td228] | 同 | ✅逐字段 |
| IQEngine/utils/scheduler.pyc | 44/45 · run_daily [77,71,jd0,td56] | 同 | ✅ |
| .../realtime_event_source.pyc | 11/12 · clock_worker [1275,1286,jd10,td481] | 同 | ✅ |

严格尺 `sstrict67.py build_landed targets.txt`：klinedata **56/63**（缺0 多0，7 条：
get_all_real_daily_kline[seq_len 188/187]、get_all_real_minute_kline[target_diff #54]、
get_history_common[#41]、get_kline_by_count_new[#161]、get_multiminute_his_data[seq_len 481/482]、
get_price_common[#114]、kline_datetime_list[seq_diff #151 POP_JUMP_IF_TRUE→FALSE]）；
scheduler **50/52**（run_daily[seq_len 84/75]、func_wrapper[seq_len 219/215]）；
realtime_event_source **11/12**（clock_worker[seq_len 1276/1287]）。合计 **117/127、缺陷 10**。与 targets.md 逐条相同 ✅。

金丝雀 landed sha（4 支逐字节）：
```
4d41187e356544e0 quotation.pyc 143/143
af77224b34b203c4 market_time.pyc 10/10
e711b8ea86d49a15 datetime_func.pyc 26/26
9d09af09249da177 datetime_func.pyc 25/25
```
与采纳合同要求的 4 个 sha **完全相同** ✅。

电池（closeout67.py battery landed，45 项自动发现 round63..67 + 11 pinned）：
**174/200 matched、缺陷函数 26、Σ|Δ| 101、worse-than-landed=0、ERR=0** —— 与 BRIEF §4 基线逐字段相同 ✅。
（逐行表见 dump/repro65_landed.jsonl；本轮 landed 列即基线列，后续候选臂须 worse=0。）

结论：Step 0 **无对 BRIEF 的更正**，工作树字节 == 中心轮初基线。

## Step 1 · hunk tables

用 `nested_diff.py`（按 code-object 全路径配对）+ 自产 `sbs.py`（同路径并排 + 行号）。
`python -X utf8 nested_diff.py <pyc> build_landed/<prod> `：

### IQCommon/api/klinedata.pyc —— 6/64 code objects 不同
| code object | orig/decomp | 归一化 hunk | 判定 |
|---|---|---|---|
| `<root>` | 545/541 | delete 2×NOP@344、2×NOP@350 | **伪影**（模块级 try/except 的 NOP，不参与函数级判据） |
| `/get_multiminute_his_data#54` | 535/536 | replace orig[518]=JUMP_FORWARD→decomp[518:520]=[LOAD_FAST his_data_dict, RETURN_VALUE]；replace orig[533]=LOAD_FAST his_data_dict→decomp[534]=LOAD_CONST None | **真缺陷（语义错）**：尾部 sink 的 `return his_data_dict` 被搬进 if 臂，else 臂与早退路径掉到 `return None` |
| `/kline_datetime_list#57` | 413/417 | 3×EXTENDED_ARG 插入（伪影）＋ `POP_JUMP_IF_TRUE`+`x -= 1` 组合被改写为 `POP_JUMP_IF_FALSE`、`max_len_real_data`/`time_count` 的 `-1` 被搬到尾部 | **真缺陷**（while 尾置自减 + 极性；9 jumpdiff 里 6 条是这条），形状搬移 Σ|Δ| 不变 |
| `/get_all_real_minute_kline#61` | 305/306 | 1×EXTENDED_ARG 插入 | **伪影**（官方尺已判 OK） |
| `/get_all_real_daily_kline#65` | 216/214 | delete orig[185:187]=[EXTENDED_ARG, JUMP_BACKWARD to 86] | **真缺陷**：少了第二条回边 ⇒ 源里外 if/elif 的最后臂尾有一条**显式 `continue`**（L1597）被丢掉 |
| `/get_price_common#67` | 594/596 | NOP@1、EXTENDED_ARG@126 | **伪影**（官方尺 OK，只有严格尺 target_diff #114 是另一条） |

严格尺另外 4 条 target_diff（get_all_real_minute_kline #54、get_history_common #41、
get_kline_by_count_new #161、get_price_common #114）全是**跳转终点常量身份不同**
（`POP_JUMP_IF_NONE` 的目标后第一条装载的 const/name 不同）⇒ 同族"if/else 臂顺序或三元极性"问题，
nested_diff 归一化后看不到（记为「跨臂终点重排」，非指令增减）。

### IQEngine/utils/scheduler.pyc —— nested_diff 实测（`nhunks.py` 在此直接 AssertionError，已绕开）
```
DIFF /Scheduler#25/run_daily#15   orig=92 decomp=82 hunks=4
   delete orig[4:5]=['MAKE_CELL minute']
   delete orig[30:37]=['LOAD_GLOBAL NULL + int','LOAD_FAST time_info','LOAD_CONST 1','BINARY_SUBSCR','PRECALL','CALL']
   delete orig[38:39]=['STORE_DEREF minute']
   delete orig[45:46]=['LOAD_CLOSURE minute']
MISSING-IN-PRODUCT /Scheduler#25/run_daily#15/func_wrapper#5
TOTAL differing code objects: 2 of 52
```
⇒ **实测确认 BRIEF 的 cellvar 判定成立**：`minute = int(time_info[1])` 整条语句连同
MAKE_CELL/STORE_DEREF/LOAD_CLOSURE 一起消失，内层 `func_wrapper` 闭包体在产物里根本没有对应
code object（MISSING-IN-PRODUCT）。这是**闭包单元格降级**，不是区域归属问题 ⇒ 按禁令**不投轮次**，仅记录。
`func_wrapper`@262/@437 同名对：nested_diff 按全路径配对成功，未再触发 AssertionError。

### realtime_event_source.pyc —— 1/13 code objects 不同
```
DIFF /RealtimeEventSource#20/clock_worker#5  orig=1442 decomp=1458 hunks=14   （过冲 +16）
   delete orig[959:976]=17 条（`if holiday_not_do_before == '0': self.event_queue...`）
   insert decomp[1412:1429]=同 17 条 ⇒ **整段搬尾**（Σ|Δ| 不变的形状移动）
   delete orig[1192:1304]=112 条（`if persist_flag is not False: set_trade_stop_status(self...`）
   insert decomp[1274:1409]=135 条 ⇒ 同段**被复制/放大**（+23）
   replace orig[1097:1110]=13 条 → decomp[1086:1088]=[EXTENDED_ARG, JUMP_FORWARD] ⇒ 少 11 条
   insert orig[913:913] → decomp[913:914]=['JUMP_FORWARD J'] ⇒ 多一条显式跳转（重复发射的指纹）
   + 5 处 EXTENDED_ARG/NOP 伪影
TOTAL differing code objects: 1 of 13
```
⇒ 与 R64 判定一致：**重复发射**（一个臂被发两遍 + 尾部整段搬移），不是缺语句。

## Step 2 · 根因（实测）

### 靶 A：`get_all_real_daily_kline` 少一条回边（官方 188/187）
`nested_diff` 唯一 hunk = `delete orig[185:187]=[EXTENDED_ARG, JUMP_BACKWARD to 86]`。
区域层实测（`core.cfg` 直读 landed 字节）：
```
LoopRegion@86  back_edge_block=898  back_edge_blocks=[898]
  continue_map={344:'CONTINUE', 894:'CONTINUE', 898:'LOOP_BACK_EDGE', ...}
IfRegion@856   merge_block=894 exit=894      ← 894 是内层 if/else 的汇合点，且是显式 continue
TryExceptRegion@94 try_offset_end=894
```
⇒ **源码真相**：外层 if/elif(或 else) 的最后一条臂以内层 `if fields is not None/else` 结尾，
其后还有一条**显式 `continue`**（orig 894 带 starts_line=1597）；898 才是 For 隐式尾块。
产物只发出 898 那条 ⇒ 少 2 条指令。
合成复现 `synth/r68_sink_continue.py`（52/51 指令，同一条 `delete JUMP_BACKWARD`）✅ 已复现。

### 候选 C1 已证伪（阴性证据，中心可归档）
把 `_is_loop_tail_convergence_block`（generator L10212，判据=「末指令 JUMP_BACKWARD→本循环
header ∧ 循环体内前驱 ≥2」）按**本循环自身登记字段**收窄：
`self._current_loop.back_edge_block is not block ∧ block not in back_edge_blocks ⇒ return False`。
实测 `probe_cont.py`（对 landed 核心 monkeypatch，零写入仓库）：
```
[_is_loop_tail_convergence_block] block=94 -> True  loop@6 back_edge=[96]
   continue_map={94:'CONTINUE', 96:'LOOP_BACK_EDGE', 122:'CONTINUE'}  callsite=L23696
```
看起来正中要害，但 A/B 实测**完全惰性**：
```
h62.py ab  dump/synth_landed.jsonl  dump/r68diag3_c1_synth.jsonl   → SAME=2 IMPROVED=0 REGRESSION=0
h62.py run --arm=r68diag3_c1 --list=targets.txt                    → 三支读数与 landed 逐字段相同
```
⇒ 唯一一次调用发生在 `_if_generate_branch_stmts`(L23696) 的**投机路径**上，其结果未被采用；
真正的丢弃点在别处（`_process_if_blocks` 根本没把 94 当作 CONTINUE 角色块走到 L21953 发射）。
**C1 判 NONE**，规格留在 `specs/cand_r68_sinkcont.json` 供中心复核，不作候选提交。

## Step 3 · 合成复现（synth/）

| 合成文件 | 形状 | landed | r68diag3_c3 | 备注 |
|---|---|---|---|---|
| `synth/r68_sink_continue.py` | for→try→if/else，else 臂末显式 `continue`（汇合点是纯回边但**不是**登记的 back_edge_block） | **1/2**，`DIFF /sink_continue#1 orig=52 decomp=51 hunks=1 delete orig[36:37]=['JUMP_BACKWARD J']` | **2/2（0 hunks）** | 与 klinedata::get_all_real_daily_kline 同指纹（52 条指令 vs 真身 214）；landed 失败 / C3 通过 ⇒ 咬合成立 |
| `synth/r68_sink_return.py` | 同款但臂末 `return` | 2/2 | 2/2 | **负结果**：这条合成不能复现 `get_multiminute_his_data`，该处「尾部 return」模型不完整，Step 1 的推测被自己的合成实验否证 |

配套 `probe_source.py`：编译 6 种候选源码形状，只有「臂末显式 continue」产生 `dup-pairs=1`（R1/R2/R3），
落地产物形状为 `dup-pairs=0` ⇒ 证伪「多发射/重复块」解释，确认是「少发射一条回边」。

## Step 4 · 候选与 A/B（全部实测，arm 由 `h62.py build --spec=specs/...` 生成）

### 已否证 / 无效路线（按时间顺序，供后续轮次不再重复踩）

| 候选 | 站点 | 实测读数 | 结论 |
|---|---|---|---|
| `cand_r68_sinkcont.json` (C1) | `_is_loop_tail_convergence_block` L10212-10250 尾部按登记的 back_edge 收窄 | `probe fires.py`：该谓词在 klinedata 上**唯一**调用来自 `_if_generate_branch_stmts` L23696 的投机路径，目标区域一次都不经过；A/B `TALLY SAME=2 IMPROVED=0 REGRESSION=0` | **完全惰性**，否证 |
| `cand_r68_sinkcont2.json` (C2) | `_generate_if` 尾部新增兄弟 Continue 支（无 EXTENDED_ARG 白名单） | 合成 2/2，但 klinedata 仍 42/45 | **真身上惰性**：块 894 = `EXTENDED_ARG + JUMP_BACKWARD`，纯度过滤把它判脏 |
| `cand_r68_sinkcont2b.json` (C2b) | C2 + `EXTENDED_ARG` 入噪集合 | klinedata **43/45**（+1）、canary sha 4/4 全同、battery 45 行逐格全同 worse=0、strict 118/127 defects 9、synth 2/2；但 all15 `IMPROVED=1 REGRESSION=2 MOVED=3`：`wizard_quant_api::read_config_file` 956→957、`trade_live_broker::get_ipo_stocks` 453→454（单臂 `if c:` 的自然尾形被多发射一条回边） | 有正收益但**外溢伤及 15 文件集**，不可采纳 |

### 提交候选 C3 · `specs/cand_r68_sinkcont3.json`

- `file` = `core/cfg/region_ast_generator.py`（白名单内），`anchor` = `_generate_if` 中既有
  `if _has_explicit_continue:` 兄弟追加支尾部 9 行，**count = 1**（LF 与 CRLF 两种读法均实测为 1），
  `repl` 在其后追加 79 行，`BOM=True / nl=CRLF`，`1 edits`。
- 三要素（识别条件/归约方式/AST 映射）已写进插入代码块上方注释，此处不赘述。
- 识别条件全部为本层级字段：`self._current_loop{.header_block,.back_edge_block,.back_edge_blocks,.continue_map}`
  + `region{.merge_block,.then_blocks,.else_blocks,.blocks}` + `merge_block` 自身指令纯度与末跳目标；
  无名称/偏移/计数/魔数启发，无跨层次包含判据，无新增 `self` 状态。
- 相对 C2b 只多两条同源合取项（`fires.py` 实测得出，用于挡住两处反例）：
  `then_blocks` 与 `else_blocks` **同时非空**，且本循环 `continue_map[merge_block] == 'CONTINUE'`
  （analyzer `_detect_break_continue` L6344-6376 已独立判过这条边的身份，发射侧与归约侧互证；标签缺失即退回落地行为）。

#### 五列契约读数（landed → C3）

| 列 | landed | r68diag3_c3 | 判定 |
|---|---|---|---|
| targets（3 文件） | `klinedata 42/45`、`scheduler 44/45`、`realtime_event_source 11/12` | `klinedata 43/45`、`scheduler 44/45`、`realtime 11/12` | 唯一命名目标 `get_all_real_daily_kline` 188/187→**完全匹配**；Σ\|Δ\| 2→**1**（净降 1），其余两文件逐字节不变 |
| battery（45 复现） | 174/200 · bad 26 · Σ\|Δ\| 101 · ERR 0 | **174/200 · bad 26 · Σ\|Δ\| 101 · ERR 0**，45 行逐格相同 | `worse-than-landed = 0` |
| canary（4 条 sha） | — | 4/4 `SHA-SAME`（`TALLY same=4 diff=0`），ok 143/143、10/10、26/26、25/25 | 逐字节相同 |
| strict（尺子，同 3 文件） | 117/127 · defects 10（klinedata 56/63） | **118/127 · defects 9**（klinedata **57/63**，scheduler 50/52、realtime 11/12 不变） | 净 +1 函数、defects −1 |
| synth | 1/2（1 处 DIFF，缺 1 条 `JUMP_BACKWARD`） | **2/2** | 咬合成立 |
| 外溢守卫 all15 | — | `TALLY SAME=14 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0` | **REGRESSION=0**（C2b 的两处反例被新合取项挡掉） |

`klinedata` C3 剩余两坑：`get_multiminute_his_data`（479/478，1 条）、`kline_datetime_list`（389/389 但 9 hunks）。

## VERDICTS（逐坑裁决）

| # | 坑 | 裁决 | 依据（实测） |
|---|---|---|---|
| 1 | `klinedata::get_all_real_daily_kline` 188/187（缺 1 条 `JUMP_BACKWARD`） | **已归约 → 提交 `specs/cand_r68_sinkcont3.json`（C3）** | 五列全绿 + all15 REGRESSION=0（见 Step 4 表）；合成 1/2→2/2 |
| 2 | `klinedata::get_multiminute_his_data` 479/478 | **NONE（未破）** | 缺陷是「尾部 sink `return his_data_dict` 被搬进 if 臂、另一路径落 `LOAD_CONST None`」两处 replace 型 hunk；我的合成 `r68_sink_return` 在 landed 上就 2/2 **不复现** ⇒ 现有「sink/return」模型不完整，无法给出会咬合的判据。R64/R65 的 analyzer 链弹栈代价 + R48-A 前置合取惰性（BRIEF 记载）与本次否证一致：本坑不属区域发射侧单层可解形状 |
| 3 | `klinedata::kline_datetime_list` 389/389 · 9 hunks | **NONE（未破）** | hunk 指纹：3×`EXTENDED_ARG` 插入（度量伪影，非语义）+ 真身 6 条同源：`POP_JUMP_IF_TRUE` 被写成 `POP_JUMP_IF_FALSE` 且 `max_len_real_data`/`time_count` 的 `-1`（`BINARY_OP -=`）被搬到尾部；Σ\|Δ\| 不变（389→389），属「等价改写但字节不同」的表达式/条件极性类，与本轮三个白名单文件的 continue/region 通道不同源 |
| 4 | `scheduler::run_daily` 77/71（缺 6 条） | **仅验证并记录（按禁令不投轮次攻）** | `nested_diff.py`：`func_wrapper#5` 在产物中 **MISSING-IN-PRODUCT**；`run_daily#1` hunk 全是 `MAKE_CELL`/`STORE_DEREF`/`LOAD_CLOSURE`/`COPY_FREE_VARS` 被 `LOAD_FAST`/`STORE_FAST` 取代 ⇒ **cellvar/closure 降级**，根因在 `core/*` 的代码对象/闭包收集层（区域层之外），region_ast_generator 三文件白名单不可达 |
| 5 | `realtime_event_source::clock_worker` 1275/1286 · 10 hunks | **NONE（不属本轮可解）** | 产物比原字节**多 11 条**且首分歧在 481；Step 1 指纹为「同一分支被重复发射 + 尾部块重定位」，非缺语句；与坑 1 的「缺回边」方向相反，C3 判据在其上 0 命中（all15 与 strict 读数逐字节不变） |

## 对 BRIEF 的更正

- 无更正：Step 0 全部读数（15 文件 572/617、45 缺陷、Σ|Δ| 296；battery 174/200/26/101；strict 659/727/68；发布口径 5746/5701/99.22%；4 条 canary sha）与 BRIEF 逐一吻合。
- 补充一条度量注意：`nhunks.py` 在 scheduler（重复 code-object 名）上抛 AssertionError 已复核；改道 `nested_diff.py` + 自写 `sbs.py` 全路径配对，坑 4 的判定必须走这条路径。


# ============ R68-b2 批2 会话（复核 + 新攻） ============

## Step R0 · C3 复核（臂 r68b2_c3，spec specs/cand_r68_sinkcont3.json 重新 build）

| 列 | landed（本轮重测） | r68b2_c3 | 判定 |
|---|---|---|---|
| targets | klinedata 42/45、scheduler 44/45、realtime 11/12 | klinedata **43/45**、scheduler 44/45、realtime 11/12 | ✅ 目标函数 get_all_real_daily_kline 消失（188/187→全对），其余两支逐字段不变 |
| battery 45 | 174/200 · bad 26 · Σ\|Δ\| 101 · worse=0 | **逐行逐格与 landed 完全相同**，worse-than-landed on 0 repro(s) | ✅ |
| canary 4 sha | 143/143、10/10、26/26、25/25 | TALLY SAME=4 DIFF=0 ERR=0 | ✅ 逐字节 |
| strict（3 文件） | 117/127 · defects 10 | **118/127 · defects 9**（klinedata 56/63→57/63） | ✅ 净 +1 / −1 |
| synth（4 支全量 b2_all.txt） | sink_continue 1/2、big_sinkreturn 1/3、sink_return 2/2、tailreturn 4/4 | sink_continue **2/2**，其余 3 支逐字段相同 | ✅ 咬合 |
| 外溢 all15 | 15 文件 baseline | TALLY SAME=14 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0 | ✅ REGRESSION=0 |

dump：dump/b2_all15_{landed,c3}.jsonl、dump/b2_synth_{landed,c3}.jsonl、dump/r68b2_c3_{targets,canary}.jsonl、
dump/repro65_{landed,r68b2_c3}.jsonl、dump/b2_strict_{landed,c3}.json。
**C3 仍然成立，作为 klinedata 支的候选提交。**
注意：synth/synth.txt 与 dump/synth_landed.jsonl 已被上一会话覆盖成只剩 tailreturn；
本轮改用自建全量名单 synth/b2_all.txt（4 支 pyc）。


# ============ R68-b2 批2 会话 · Step R1–R4（scheduler 根因 + 合并臂） ============

## Step R1 · 根因（两处，均为区域层同层次结构身份，实测打印）

### BUG B（generator）— C2 分支对「cell 目标元组赋值」直接 decline
core/cfg/region_ast_generator.py L14262-14304（落地字节行号）：
\14264  _c2_has_swap = any(i.opname == 'SWAP' for i in _c2_val_instrs)
14267  if not _c2_has_swap and not _c2_has_unpack:   ← SWAP 存在即整支放弃
...
14304  → _build_store_statement（只吃最后一个 STORE）
\CPython 3.11 对**目标含 cell 变量**的固定长元组赋值生成 \<e1>..<eN> + SWAP N + 源序 STORE\，
\_c2_has_swap\ 恒真 ⇒ 走 L14304，只发出末条 STORE ⇒ \minute = int(time_info[1])连同 \MAKE_CELL / STORE_DEREF minute / LOAD_CLOSURE minute\ 全部丢失（nested_diff 4 处 delete）。
无 SWAP 的普通 \,b=x,y\ 是**反源序** STORE，与本形态**互斥可辨**。
实测：\sys.settrace\ 只在 landed 上打到 C2 的 eversed(_c2_stores)\ 路径；栈重建证实
\stack[-N:]\（压栈源序）与源序目标一一对应。

### BUG C（analyzer）— and 链游走漏掉异常出边排除
\core/cfg/region_analyzer.py\ L16810-16816（落地字节行号）：
\16813  for _s in _main_current.successors:
16814      if _s.start_offset not in _main_visited and _s.start_offset != _main_cur_last.argval:
16815          _main_ft_next = _s ; break      ← 集合序 + 无异常边排除
\同文件 **or 链** L16716-16724 已有 R13c「异常表边排除」（\_or_cur_exc\/\_or_ft_exc\），
and 链漏了同一条判据 ⇒ scheduler::run_daily 的 B 段块@462 后继集先命中异常块@690
（末指令 \POP_JUMP_IF_TRUE\）并 break，链止于 [406,462]，第三合取支
\minute == current_minute\（4 条指令）整体丢失。

### body 路径同源缺陷 — SIG2 看不见 SWAP
egion_ast_generator.py\ L47391-47420：\_s2_has_swap\ 由 \stmt_instrs\ 求值，
而 SWAP ∈ \SKIP_OPS\（L48250）永远进不了 \stmt_instrs\ ⇒ 恒 False ⇒ 目标恒
eversed(_s2_stores)\ ⇒ \minute, hour = (...)\ 反序。
\sys.settrace\ 实测（probe_trace.py，watch 行 = C2/NOSWAP/UA_S2/SIG2 四个候选点）：
\FIRED: ['SIG2_body']\ —— body 见证唯一命中 SIG2，L45612/\_noswap\ 与 L46298/\_ua\ 未触发。

## Step R2 · 合成复现（synth/，两支，landed 失败 → 臂通过）

| 合成件 | 形状 | landed | r68b2_final |
|---|---|---|---|
| \synth/r68b2_cell_tuple.py\（以 \if flag:\ 结尾 ⇒ 走 C2/前缀路径） | cell 目标元组赋值 + 尾随 if | **2/3**：delete \MAKE_CELL minute\ / \int(time_info[1])\ / \STORE_DEREF minute\ / \LOAD_CLOSURE minute\ + MISSING wrapper | **3/3（0 hunks）** |
| \synth/r68b2_cell_tuple_body.py\（无尾随 if ⇒ 走 body 路径 SIG2） | 同上，整块语句路径 | **2/3**：真 diff=2（产物反序 \minute, hour\） | **3/3** |
| 名单 | \synth/b2_all.txt\(6 支)、\synth/b2_witness.txt\ | — | — |

## Step R3 · 候选与 A/B（臂 r68b2_final）

### 构建方式（两支白名单文件 ⇒ 两个 spec，须一次 build）
\python -X utf8 mb2build.py r68b2_final specs/cand_r68b2_final_gen.json specs/cand_r68b2_andchain.json
# 等价于中心口径：python -X utf8 D:/Temp/opencode/r68gate/mbuild68.py r68b2_final <上两份 spec>
\输出：\patched core/cfg/region_ast_generator.py (+154 lines, BOM=True, nl=CRLF)\、
\patched core/cfg/region_analyzer.py (+29 lines, BOM=False, nl=CRLF)\、**4 edits、每条锚点 count==1（断言通过）**。
\closeout67.py landproof mirr_r68b2_final\ ⇒  core files, same=31 diff=2\，DIFF **只有**这两支白名单文件。

| spec | file | edits | 内容 |
|---|---|---|---|
| \specs/cand_r68b2_final_gen.json\ | region_ast_generator.py | 3（= \cand_r68b2_gen_merged.json\ 的 C2+SIG2 两条 + \cand_r68_sinkcont3.json\ 的 C3） | BUG B 补支、SIG2 源序、C3 显式 continue 兄弟 |
| \specs/cand_r68b2_andchain.json\ | region_analyzer.py | 1 | BUG C：跳过 \_main_current.exception_successors\ |

三要素注释均已写入插入块上方（镜像行号：gen 14267-14296 / 47537-47547、ana 16813-16837、C3 gen 18405-18433）；
判据全部只读本块自身指令序列 + 本块自身 \exception_successors\ + 本循环 \continue_map/back_edge_*\，
无跨层包含、无名称/偏移/计数启发、无新增 \self\ 状态。

#### 五列契约读数（landed → r68b2_final）

| 列 | landed | r68b2_final | 判定 |
|---|---|---|---|
| targets（3 文件） | klinedata 42/45 · Σ\|Δ\|=2 · Σjd=15；scheduler 44/45 · Σ\|Δ\|=6；realtime 11/12 · Σ\|Δ\|=11 · Σjd=10 | **klinedata 43/45 · Σ\|Δ\|=1 · Σjd=12**；**scheduler 45/45 · Σ\|Δ\|=0**；realtime 11/12（产品 sha 逐字节 SAME） | 三靶 Σ\|Δ\| **19 → 12**（净降 7）、Σjd 25 → 22；\TALLY SAME=1 IMPROVED=2 REGRESSION=0 ERR=0\ |
| battery 45 | 174/200 · bad 26 · Σ\|Δ\| 101 | **逐行逐格与 landed 完全相同**，\worse-than-landed on 0 repro(s)\ | ✅ |
| canary 4 sha | d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177\ | **TALLY SAME=4 DIFF=0 ERR=0**，4 条 sha 与 pin 集合完全相等 | ✅ 逐字节 |
| strict（3 文件） | 117/127 · defects 10 | **121/127 · defects 6**（修 4、**新增 0**）：klinedata \get_all_real_daily_kline[seq_len]\、\get_all_real_minute_kline[target_diff #54]\；scheduler un_daily[seq_len 84/75]\、\unc_wrapper[seq_len 219/215]\ | ✅ 净 −4 |
| synth | cell_tuple 2/3、cell_tuple_body 2/3、sink_continue 1/2、big_sinkreturn 1/3、sink_return 2/2、tailreturn 4/4 | **3/3、3/3、2/2、1/3（产品与 landed 逐字节相同）、2/2、4/4** | 3 支 IMPROVED、0 REGRESSION ⇒ 咬合 |
| 外溢 all15 | 15 文件 baseline | \TALLY SAME=12 IMPROVED=2 REGRESSION=0 MOVED=1 ERR=0\ | ✅ REGRESSION=0 |

**MOVED（all15 唯一形状移动，方向为改善）**：\	rade_live_broker::_process_cancel_ordertrue_diffs **43 → 22**、matched 108/119 不变；产品 diff = 把 landed 的
\if flag==0: if len>0: … else: …\（外层 false 走「什么都不做」）纠正为
\if flag==0 and len>0: … else: …\（与原字节码两条 IF_FALSE 同指一个 else 块一致）。
同族改动在 klinedata::\get_all_real_minute_kline\ 上把严格尺 \	arget_diff #54\ 直接修没。

**中间臂 r68b2_both（只含 BUG B + BUG C + SIG2，不含 C3）**：klinedata 42/45、
**scheduler 45/45**、canary SAME=4、battery worse=0、strict **120/127 · defects 7**、
synth 两支 cell 见证 2/3 → 3/3、all15 REGRESSION=0 ⇒ B 系列自身已独立成立。

## Step R4 · 另两支的读数（不提交）

### sinktail4 / C4（\specs/cand_r68_sinktail4.json\，臂 68diag3_c4\）
\dump/big_c4.jsonl\ vs \dump/big_landed.jsonl\（\synth/r68_big_sinkreturn.pyc\）：
\matched_functions 1 → 1\、mism **逐条完全相同**（\<module> [57,57,0,36]\、
\sink_big_sinkreturn [479,478,3,16]\，Σ\|Δ\|=52、Σjd=3 **不变**），但产品文本变了
（eturn his_data_dict\ 从 if 体后移到函数尾）。
⇒ **形状移动而 Σ\|Δ\| 不变，按采纳合同 §3.3「形状移动但 Σ|Δ| 不变 ⇒ 拒」⇒ 候选：NONE**。

### realtime_event_source::clock_worker（1275/1286 · jd10 · td481）
68b2_final\ 产品 sha **与 landed 逐字节相同**（TALLY SAME=1 里的那一支）、
mf 11/12、Σ\|Δ\|=11、Σjd=10 全部不变 ⇒ 本轮三条判据在其上 **0 命中**（可复放排除读数）。
根因仍是 R64 判定的**elif 臂重复发射**（Step 1 指纹：delete orig[959:976]/insert decomp[1412:1429]
整段搬尾 + delete orig[1192:1304] 112 条 → insert 135 条 **+23 复制** + insert \JUMP_FORWARD\ 指纹），
方向与本轮「缺语句/缺回边」相反，须另开「同层重复发射」判据 + 自己的合成见证 ⇒ **候选：NONE**。


## VERDICTS（b2 会话 · 最终，取代上表中坑 1/4/5 的旧裁决）

| # | 靶支 | 裁决 | 依据（实测，臂 68b2_final\） |
|---|---|---|---|
| 1 | \klinedata\ 42/45 → **43/45** | **候选：68b2_final\**（= C3 并入 B 系列的合并臂；C3 单独也已复核成立，见 Step R0） | targets Σ\|Δ\| 2→1、Σjd 15→12；strict klinedata 56/63→**58/63**（修 \get_all_real_daily_kline[seq_len]\ + \get_all_real_minute_kline[target_diff #54]\，新增 0）；canary 4/4、battery worse=0、all15 REGRESSION=0、合成 68_sink_continue\ 1/2→2/2。剩余两坑 \get_multiminute_his_data\ / \kline_datetime_list\ 仍 **NONE**（理由同上表坑 2、3，未变） |
| 2 | \scheduler::run_daily\ 44/45 → **45/45**（Σ\|Δ\| 6→**0**） | **候选：68b2_final\**（同一臂，BUG B + BUG C 两条 spec） | nested_diff 4 处 delete 与 \unc_wrapper\ MISSING 全部消失；strict un_daily[seq_len 84/75]\、\unc_wrapper[seq_len 219/215]\ **两条同时修没**（defects −2）；合成两支 cell 见证 2/3→**3/3** 且 \sys.settrace\ 证明命中的是被改的那条路径；canary/battery/all15 全绿 |
| 3 | ealtime_event_source::clock_worker\ 11/12 | **候选：NONE** | 产品 sha 与 landed **逐字节相同**（本轮三判据 0 命中），mf/Σ\|Δ\|/Σjd 全不变；根因仍是 R64 的 elif 臂**重复发射**（非缺语句），须另立判据 + 合成见证 |
| 4 | klinedata::\get_multiminute_his_data\ 479/478 | **候选：NONE** | 合成 68_sink_return\ 在 landed 上 2/2 **不复现**，sink/return 模型不完整（未变） |
| 5 | klinedata::\kline_datetime_list\ 389/389 · 9 hunks | **候选：NONE** | 极性/尾置自减类，Σ\|Δ\| 不变（未变） |
| 6 | sinktail4 / C4 | **候选：NONE** | matched 1→1、mism 逐条相同、Σ\|Δ\|=52 不变，仅产品文本移动 ⇒ 合同 §3.3 拒（见 Step R4） |

**提交候选名：68b2_final\**（spec 两份，见 Step R3）；可独立复现的子候选：
\specs/cand_r68_sinkcont3.json\（klinedata 单支）、\specs/cand_r68b2_final_gen.json\ + \specs/cand_r68b2_andchain.json\（scheduler 单支 = 68b2_both\ 读数）。

## 对 BRIEF 的更正（b2 会话）

1. **§8 的 scheduler「禁令」被区域层实测证据推翻**。BRIEF 记 un_daily\ 为「cellvar/闭包变量降级，在区域层之外」；
   实测根因有**两条，全在白名单三文件内**：(a) generator C2 L14267 对带 SWAP 的 cell 目标元组赋值直接
   decline 落到只吃末条 STORE 的 \_build_store_statement\；(b) analyzer and 链 L16813 漏掉与同文件 or 链
   R13c 同源的**异常出边排除**。两条各修完即 **44/45 → 45/45、Σ\|Δ\| 6 → 0**，合成见证咬合。
   ⇒ \unc_wrapper\ 的严格 \seq_len\ 也一并修掉（219/215 消失）。后续轮次不必再按「禁令」回避该坑。
2. \_build_statements_from_instructions\（L28028/L28436 默认 append 含 SWAP）**不是**本形状的实际路径——
   栈探针证实前缀走 \_if_extract_cond_instructions\ L14304；BRIEF §6 未列该站点，补记。
3. body 路径的反序由 **SIG2（L47391-47420）**而非 \_noswap_unpack_result\(L45612) / \_ua_s2\(L46298) 产生：
   \sys.settrace\ 四点 watch 实测 \FIRED: ['SIG2_body']\（probe_trace.py）。
4. \h62.py build --spec=<一份>\ 只能打**单文件**；本次候选跨两支白名单文件，必须用
   \mb2build.py <dst> <spec1> <spec2>\（或中心 \mbuild68.py\，多 spec 同语义）一次建镜像，
   否则第二支 spec 会被 \ssert rel not in seen\ 拒绝。
5. \h62.py run --out=<已存在文件>\ 的 resume 语义本轮又踩到一次：\dump/b2_synth_both.jsonl   里存的是**旧 2-edit 构建**的记录，导致误判 SIG2 未生效；换 out 文件名（\2f_*\）后读数才正确。
   上表所有 b2 读数均取自新建的 \dump/b2f_*\ 与 \dump/repro65_r68b2_final.jsonl\。
