# Round 68 · diag4 · FACTS（边跑边写）

## Step 0 · baseline replay（arm=landed ＝当前工作树字节）

### targets（3 支，`dump/r68d4_landed.jsonl`）
```
landed trade_info_utils.pyc  38/40  [['get_trade_list',339,323,14,148], ['trade_operation',304,302,2,40]]
landed fileio_utils.pyc      12/14  [['acquire',96,93,3,52], ['write',637,637,4,519]]
landed logger.pyc            29/30  [['write_logging_thread',113,113,1,40]]
```
逐字段与 BRIEF §8 / targets.md 预读数 **完全相同**。无更正。

### canary（`dump/r68d4_landed_canary.jsonl`）
```
4d41187e356544e0 quotation.pyc       143/143
af77224b34b203c4 market_time.pyc     10/10
e711b8ea86d49a15 datetime_func.pyc   26/26
9d09af09249da177 datetime_func.pyc   25/25
```
四支 sha 与采纳合同 §3.1 的 pinned 值 **逐字节相同**。

### battery（45 项，`closeout67.py battery landed`）
```
discovered 45 repro pycs (round63_b*/fix* + round64..67 + 11 pinned)
matched 174 / total 200 · 缺陷函数 26 · Σ|Δ| 101 · Σjumpdiff 26 · ERR 0 · worse-than-landed 0
```
与 BRIEF §4 轮初基线（174/200、26、101、worse=0、ERR=0）**完全相符**。
非绿 repro（15 项 bad>0）：r63b2×2、r63b5_w1、r64d5_contsink、r65_trytail、fs2、
r67d3_lostreturn、r67d3_return_sink、r67d3_return_tern、r67d4_controls、r67_ccprefix2、
r67_site2、r67d6_boolop_ternary、r67d6_boolop_ternary2、r67d6_whiletrue_headif。

**Step 0 结论：BRIEF 全部前提成立，landed 基线可信。**

## Step 1 · hunk tables（自建仪器 `ndiff.py`：丢 NOP/EXTENDED_ARG + 跳转目的指令身份参与比对）

`nested_diff.py`（diag6 版）把所有跳转折成 `J`，看不见「极性与跳转目的」缺陷，故 diag4 另写
`ndiff.py`：非跳转指令 tokenise 为 `OP repr`，跳转指令 tokenise 为 `OP -> 目的OP 目的repr`，
并在 tokenise 前丢弃 NOP/EXTENDED_ARG。下表即「真缺陷」，无一条是计数伪影。

### IQCommon/util/trade_info_utils.pyc —— 5/41 code objects 真差异
| code object | orig/decomp(norm) | 真缺陷 hunk | 归类 |
|---|---|---|---|
| /get_trade_list#30 | 376/358 | 2 处 delete（o[177:189] 12 条、o[209:215] 6 条）+ 4 处跳转目的差 | **嵌套 if 条件被整块丢弃**（源 L205 `if item['strategyType'] in list(CUSTOM_STRATEGY_TYPE_DICT.values())`、L210 `if item['strategyType'] == COMMON_STRATEGY_TYPE`）|
| /trade_operation#32 | 335/333 | o[106:107] 跳转目的差；o[292:294] `LOAD_CONST None;RETURN_VALUE` 被丢 | 隐式 return 丢失（epilogue 族）|
| /get_trade_unit_info#44 | 266/267 | 4 处跳转目的差 + 末尾多 1 条 JUMP_BACKWARD | 顺序/跳转位移（严格 seq_len 240/241）|
| /set_trade_status#67 | 175/175 | 4 处跳转目的差（JUMP_FORWARD 落点被折成 J）| 严格 target_diff #113 |
| /get_trade_status#70 | 171/171 | 1 处跳转目的差 | 严格 target_diff #70 |
官方只记 get_trade_list(16 缺) 与 trade_operation(2 缺)；其余 3 支是严格尺专属。

### IQCommon/util/fileio_utils.pyc —— 2/15 code objects 真差异
| code object | orig/decomp | 真缺陷 | 归类 |
|---|---|---|---|
| /FileLock#9/acquire#7 | 109/104 | `time.sleep(self.delay)`（6 条）从 o[83:95] 被搬到 d[45:53]（循环头）；末条 JUMP_BACKWARD 丢失 | 语句被提到循环头 = **前缀重发/位移族** |
| /FileIO#11/write#6 | 694/694 | 4 处：`LOAD_CONST None×3;PRECALL;CALL` 序列与 `RETURN_VALUE` 互换、`False/None` 落点差 | 纯顺序（位移族），Δ=0 |

### fly/logger.pyc —— 2/64 code objects 真差异
| code object | orig/decomp | 真缺陷 | 归类 |
|---|---|---|---|
| /Backtest#12/write_logging_thread#4 | 125/125 | o[77:87]（`if msgs: self.logger_bt.info(msgs)`，10 条）被重发到函数尾 d[115:124]，并凭空多出第二条回边（d 有 `to 2` 与 `to 4` 两条，orig 仅 1 条）| R67-diag6 while-True 头块重发族，Δ=0 |
| /SafeFileHandler#26/check_baseFilename#5 | 34/34 | 仅 1 处：`POP_JUMP_FORWARD_IF_TRUE` 目的 orig=LOAD_CONST 1 / decomp=LOAD_CONST 0 | **极性归属**，官方尺与 nested_diff 都看不见（Δ=0）|

**关键量化（决定优先级）**：三支官方 Σ|Δ| = 16+2+3+0+0 = **21**，全部集中在
`get_trade_list`(16) / `acquire`(3) / `trade_operation`(2)；
`write`、`write_logging_thread`、`check_baseFilename` 的 Δ 都是 0 ——
即便修好也不满足采纳合同 §3.3「Σ|Δ| 净减少」，只能作为正确性修复报告。

## Step 2 · 根因（已实测，非读码推断）

### 主缺陷：`IQCommon/util/trade_info_utils.pyc::get_trade_list`（官方 16 条缺失）
站点：**`core/cfg/region_ast_generator.py` L17587-17588**（`_if_generate_normal` 内
`if len(_main_parts) >= 2: condition = {'type':'BoolOp','op':_chain_op,'values':_main_parts}`）。

实测手段 1（`probe_gb.py`，TraceSet 记录每块被谁 claim）：块 @888 / @1064 **均已被标 generated**，
即不是「漏归属」而是「归属后表达式被丢弃」：
```
--- trace for block@888 ---  added by _generate_region:3184/_generate_if:11655/
     _if_generate_normal:17527/_if_extract_condition_from_instructions:20469
```
实测手段 2（`h62 build --spec=specs/trace_id.json --dst=r68d4id` 注入的 [ID] 探针，跑落地字节）：
```
[ID NORMAL] entry=860  op=or chain=[860,864]    Etype=BoolOp Eop=and nE=2 EQ_LAST=True  NPARTS=2
[ID NORMAL] entry=1036 op=or chain=[1036,1040]  Etype=BoolOp Eop=and nE=2 EQ_LAST=True  NPARTS=2
（同函数其余 10 次命中全部 op=and，EQ_LAST=False、P0EQ_E0=True；全语料 15 支中仅这两条为 True）
```
即：`_if_extract_condition_from_instructions` 为链末块 bn 抽出的 condition 已经是
`BoolOp(and,[C,D])`（分析端把嵌套 `if D`——与 bn 同 merge 的真后继条件块——折进了 bn），
随后 L17588 用 `BoolOp(or,[B,C])` **整体替换** condition ⇒ D 支连同 12/6 条指令一起被丢，
产物只剩 `A and (B or C)` + 无条件 `trades.append(item)`。
源 L204-206（then 臂）与 L209-211（else 臂）各一次 ⇒ 16 条缺失。

### 其余名下缺陷的归属（不攻/暂缓，理由见 VERDICTS）
- `fileio_utils::acquire`：`time.sleep(self.delay)` 整条语句被前移到循环头（ndiff 实测
  `insert d[45:53] / delete o[83:95]`），属 while 头块前缀重发族，与 `logger::write_logging_thread`
  同族（BRIEF §8 头号候选，需生成器侧「重发头块前缀去重」+分析器侧配对判据）。
- `trade_operation`：函数尾 `LOAD_CONST None; RETURN_VALUE` 隐式 return 被吞（2 条），
  属 per-exit-path except epilogue 族——**该族抑制类修法已在 12 个文件上被证伪**，本回合不硬造。
- `check_baseFilename`：ndiff 实测 `POP_JUMP_FORWARD_IF_TRUE` 目的 orig=LOAD_CONST 1 / decomp=LOAD_CONST 0，
  极性归属错误，官方尺 34/34 全绿 ⇒ 修了也不动 Σ|Δ|，不作为本批收益。

## Step 3 · 最小合成复现（`synth/r68d4_s3.py` → `r68d4_s3.pyc`，名单 `synth/r68d4_s3.txt`）
搜索过程：先试 6 个无 try 包裹的变体（`synth/r68d4_orchain.py`、`r68d4_s2.py`）——landed 全部 3/3、7/7 通过，
[ID] 探针显示 or 链的 `EQ_LAST=False`，即**不触发**；据此定位触发前提是
**该 for 循环处于 try/except 区内**（merge 块的 sink/post-dominator 关系改变，分析端才会把
嵌套 `if D` 折成 bn 的 and 尾巴）。`r68d4_s3.py::w2` 是能咬合的最小件：
```python
def w2(rd, st, mode, op_station, trades):
    try:
        for item in rd:
            if st is None:
                if mode == 'c':
                    if item['s'] != '2' and (not op_station or item['o'] == op_station):
                        if item['t'] in list(D.values()):
                            trades.append(item)
    except Exception:
        pass
```
| 臂 | 读数 |
|---|---|
| landed | `3/5  [['w1',97,81,h=7,fd=61], ['w2',55,45,h=5,fd=30]]`（w2 缺 10 条）|
| r68d4c1 | `5/5  []` |
[ID] 探针在同一 pyc 上打印 `entry=52 op=or chain=[52,56] Eop=and EQ_LAST=True` ⇒ 合成件与真件同因。

## Step 4 · 候选 `specs/cand_r68_orchain_tail.json`（臂名 r68d4c1）
单文件单站点：`core/cfg/region_ast_generator.py`，锚点 = L17572-17592（21 行，落地字节 `count==1`，
h62 build 已断言），插入 +32 行；判据三要素已写进注释（识别条件 a/b/c、归约方式=重组而非替换、
AST 映射=If(test=BoolOp(and,[BoolOp(or,...),tail]))）。
判据只读本区域自身字段：`region.inline_boolop_chains[cond_block]` 的 `op=='or'`、
本区域已抽出的 `condition` 是 `BoolOp(and)` 且 `values[0] == _main_parts[-1]`（链末块表达式的
**结构相等**），无任何函数名/文件名片段/偏移/计数阈值/跨区域包含/新增 self 状态。
判据不成立时走原路径 ⇒ 产物逐字节不变（15 支 partial 中 14 支 sha 未变，见下表）。

### 五列读数（landed → r68d4c1）
| 列 | landed | r68d4c1 | 合同 |
|---|---|---|---|
| targets(3 支官方) | 38/40、12/14、29/30；Σ\|Δ\| 21；缺陷 5 | **39/40**、12/14、29/30；Σ\|Δ\| **5**；缺陷 **4** | §3.3 严格变好+Σ\|Δ\| 净减 ✓ |
| battery(45) | 174/200、bad 26、Σ\|Δ\| 101、worse 0、ERR 0 | **逐字节全等**（45/45 sha 相同）同读数 | §3.2 ✓ |
| canary(4) | 4d41187e356544e0/af77224b34b203c4/e711b8ea86d49a15/9d09af09249da177 | **四支 sha 逐字节不变** | §3.1 ✓ |
| strict | targets 111/120、缺陷 9；all15 632/700、缺陷 68 | targets **112/120、缺陷 8**（get_trade_list 转绿）；all15 **633/700、缺陷 67** | ✓ |
| synth | 3/5（w1 97/81、w2 55/45） | **5/5、mism=[]** | §3.5 ✓ |
额外爆炸半径（非合同要求）：15 支 partial 全跑 A/B ⇒ `SAME=14 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`；
官方 Σjumpdiff 181→167、Σ\|Δ\| 296→280、matched 572/617→573/617。ERR=0，无不可反编译。

## Step 4b · 孪生点（elif 链）实测：惰性 ⇒ 不并入
arm `r68d4c2` = `specs/cand_r68_orchain_tail_both.json`（主站点 + `_if_generate_full_elif_chain` L12464-12478 同构段）。
先验证镜像确实带了两处标记（`grep mirr_r68d4c2/core/cfg/region_ast_generator.py` ⇒ L12474 `/elif 孪生点` 与 L17606 主标记都在），
再按 `path` 键控逐支比 sha：`c2 vs c1 changed = []`（15/15 逐字节相同）；`c2 vs landed` 仍只有 `trade_info_utils.pyc` 38→39。
⇒ elif 站点上的同款判据在**整个 15 支语料 + 本回合合成件上从未成立**，是纯对称性补齐、无 witness 的惰性孪生。
按「判据必须有咬合证据」的纪律：**建议中心只采纳单站点 spec `specs/cand_r68_orchain_tail.json`（臂 r68d4c1）**，
孪生段留档，待将来出现 elif 链咬合件时再一并交。

## Step 4c · `fly/logger::write_logging_thread` 根因实测（BRIEF §8 头号候选：叙述成立，但不可采纳）
仪器 `probe_wlt.py`（在 landed 字节上跑真分析器 + monkeypatch `RegionAnalyzer._should_skip_block_for_if_region`）
与 `probe_wlt2.py`（打印头块指令与后继），读数：
```
write_logging_thread: 20 blocks / 9 regions / 2 LoopRegion
  LoopRegion entry=48 header=64 cond=48 body=[64,228,232,288,342,356]
  LoopRegion entry=4  header=4  cond=None body=[4,48,64,228,232,288,342,356,368,372,424,426,440,522,564,620,660,662,666]
landed 谓词返回 True 的块: [(356,'LoopRegion','POP_JUMP_BACKWARD_IF_TRUE'),
                            (48,'LoopRegion','POP_JUMP_FORWARD_IF_FALSE'),
                            (4, 'LoopRegion','POP_JUMP_FORWARD_IF_FALSE')]
block@48  len=6 succ=[64,368]  4 LOAD_CONST 2 | 50 STORE_FAST 4 | 52 LOAD_FAST 3 | 54 LOAD_CONST 3 | 56 COMPARE_OP 4 | 62 POP_JUMP_FORWARD_IF_FALSE
block@356 len=4 succ=[64,368]  356 LOAD_FAST 3 | 358 LOAD_CONST 3 | 360 COMPARE_OP 4 | 366 POP_JUMP_BACKWARD_IF_TRUE
```
⇒ **BRIEF §8「混合 store + 条件跳转的循环头块被降级」在字节层面成立**：block@48 既是循环头（`msgs = …` 前缀）
又是 `if msgs:` 的条件块，landed 谓词对它返回 True ⇒ 前缀语句随循环体二次发射，产物把 `if msgs: self.logger_bt.info(msgs)`
放到 d[115:124]（原始在 o[77:87]），并凭空多出第二条回边（d 有 `to 2`+`to 4`，orig 仅 1 条）。
**旁证（仓库自带记录，`git log -1` R67 提交信息）**：R67-diag6 的 W1 臂（只改分析器侧）已把
`write_logging_thread` 官方 113→**41**、电池 `r63b5_w1::init_connection` 41→**32** 同步崩塌，
中心当时的结论就是「**需生成器侧前缀去重配套**」⇒ 本回合 Step 4c 的读数与该失败臂同因、同站点，
再次单点（分析器 L15408 谓词）进攻等于重踩已证伪的路线，故判 NONE 并移交。
**但**该分支 Δ=0（官方 113/113 全绿，只有 `ndiff.py` 看得见）⇒ 修它不满足采纳合同 §3.3「Σ\|Δ\| 净减少」，
且要看生成器侧所有权、跨 while-True 语料风险未测 ⇒ 本回合仅作为**正确性缺陷报告**移交，不交 spec。
（同一族的 `fileio_utils::FileLock::acquire` Δ=3，理论上有收益，但两处要一起改分析器头块归属，超出一轮安全范围。）

## Step 5 · VERDICTS（逐靶支）

| 分支 | 读数（landed → 臂） | 根因站点（landed 行号 / 族） | 判定 |
|---|---|---|---|
| `trade_info_utils::get_trade_list` | 官方 38/40、缺 16 → **39/40、缺 0**；严格 #30 转绿 | `core/cfg/region_ast_generator.py` **L17587-17588**（`_if_generate_normal` 内 `inline_boolop_chains` 复合重建**替换**了 condition） | **候选 `r68_orchain_tail`** ⇒ `specs/cand_r68_orchain_tail.json`，臂 `r68d4c1`，五列全过（见 Step 4 表） |
| `trade_info_utils::trade_operation` | 304/302、缺 2（尾部 `LOAD_CONST None;RETURN_VALUE`） | 函数尾隐式 return 未发射 = **per-exit-path except epilogue 族**（用户与 12 文件历史已证伪其抑制类修法） | **NONE**（不硬造抑制判据） |
| `fileio_utils::FileLock::acquire` | 96/93、缺 3 | `time.sleep(self.delay)` 被搬到循环头（`insert d[45:53]/delete o[83:95]`）= Step 4c 实测的**循环头前缀重发族** | **NONE（本回合）**：根因已定位，族级修法要动分析器头块归属，风险面覆盖全部 while 循环 |
| `fileio_utils::FileIO::write` | 637/637、Δ=0、4 处纯顺序差 | 循环尾 return/epilogue 发射顺序（位移族），无同层次结构身份可依据 | **NONE** |
| `logger::Backtest::write_logging_thread` | 113/113、Δ=0 | 头块 @48/@356 被 `_should_skip_block_for_if_region`（`core/cfg/region_analyzer.py` **L15408**）降级 ⇒ 生成器侧重发前缀（Step 4c 实测） | **NONE（根因确认；Δ=0 结构上不可能满足 §3.3）** |
| `logger::SafeFileHandler::check_baseFilename` | 34/34、官方全绿，仅 1 处跳转目的差 | `POP_JUMP_FORWARD_IF_TRUE` 极性归属错（orig→`LOAD_CONST 1` / decomp→`LOAD_CONST 0`），区域所有权之外 | **NONE**（`nested_diff.py` 与官方尺双双失明） |

**名下 3 支净结论**：可采纳 1 支；其余 5 支 NONE 且各带 Δ 读数/族归属证据。
名下 Σ\|Δ\| 21→**5**（剩余 5 全部落在本回合判 NONE 的两支上）；未攻下的收益空间已被完整量化，不存在「还能轻易再拿一分」的分支。

## Step 5b · 阴性证据 / 被证伪与不再尝试的路线
1. **纯 if 嵌套（无 try 包裹）的 or 链**：`synth/r68d4_orchain.py`（3 件）、`synth/r68d4_s2.py`（7 件）在 landed 上 **3/3、7/7 全绿**，
   [ID] 探针显示这些件的 or 链 `EQ_LAST=False` ⇒ 触发前提确认是「链末块处于 try/except 区内」；再往无 try 方向找复现件是死路。
2. **打包 elif 孪生点**（`cand_r68_orchain_tail_both.json`）：15/15 与单站点 sha 全等 ⇒ 无 witness，已撤回建议。
3. **放宽判据 a（`_chain_op=='or'`）**：[ID] 实测同一函数内另有 **10 次 `op=='and'` 命中**（`EQ_LAST=False`、`P0EQ_E0=True`），
   若把判据放宽到 and 会一次改 10 处且无咬合证据 ⇒ 保留 `or` 限制；判据 c（`values[0] == _main_parts[-1]` 结构相等）同理不可省，
   否则 12/14 两支 partial 的 ibc 复合路径会被误伤（15 支中仅 entry 860/1036 为 True 已实测）。
4. **epilogue / f-string / 极性位移三支的抑制类修法**：按用户提示与 12 文件历史证伪，本回合**未再尝试**，只做归属测量。
5. 仪器侧：`specs/trace_normal.json`（臂 r68d4tr）产物 sha `d242839f547ba402`、mism 与 landed **完全相同**
   ⇒ 本轮 [ID]/[TR] 探针是字节中性的，Step 2/3 的探针读数可直接采信（仪器自检）。

## Step 5c · 对 BRIEF 的更正
1. §8 称 `diag4/synth/` 内有 `r67d6_whiletrue_headif.py`：**该目录实为空**（只有 battery 的 .pyc 与 landed 产物在），
   复现件须自建（本回合新建 `synth/r68d4_s3.py` → `r68d4_s3.pyc` → `synth/r68d4_s3.txt`）。
2. §8/用户提示把 logger 一族缺陷归到 **f-string + per-exit-path except epilogue**：ndiff 实测两支真缺陷分别是
   **循环头前缀重发**（write_logging_thread）与 **跳转极性归属**（check_baseFilename），**无一条是 f-string**；
   epilogue 族的命中在 `trade_info_utils::trade_operation`，不在 logger。
3. 「头号候选 = 修 write_logging_thread 循环头重发」在 Δ=0 分支上**结构上不可能满足 §3.3**（Σ\|Δ\| 净减少）。
   名下 6 支里 Δ=0 有 3 支（write / write_logging_thread / check_baseFilename）⇒ 它们只能是正确性修复；
   可计分的收益只有 `get_trade_list`(16)、`acquire`(3)、`trade_operation`(2)。
4. 严格尺口径：BRIEF 记 659/727、68 缺陷；本回合 `sstrict67.py` 跑 all15 landed 实测 **632/700、68 缺陷**（分子分母随清单口径，缺陷数一致），
   targets 子集 111/120、9 缺陷；臂 c1 后 targets **112/120、8 缺陷**、all15 **633/700、67 缺陷**。
5. `nested_diff.py`（diag6 版）把全部跳转折成 `J` ⇒ 对「极性/跳转目的」缺陷天然失明；
   中心若要审计 `check_baseFilename` 这类分支，须改用本回合新增的 `ndiff.py`（丢 NOP/EXTENDED_ARG，跳转带目的指令身份）。
6. 汇总读数请从 `dump/*.jsonl` 用脚本聚合（本回合手算 battery 得 169/196，与 jsonl 真值 174/200 不符）；
   `h62 run --out=` 指向已存在文件时会跳过全部记录，新臂请给新路径。注意 jsonl 记录**必须按 `path` 键控**比较，
   按行序/下标键控会造出「12 支不同」的假差异（本回合 Step 4b 的第一次统计即犯过，按 path 重算后 c2==c1 全等）。

## Step 5d · 只读合规与 spec 时效性自检（收尾）
- 收尾时（Step 5 写完后）重跑 `python -X utf8 h62.py build --spec=specs/cand_r68_orchain_tail.json --dst=r68d4c1`
  ⇒ `mirrors built: head pristine == worktree bytes, cand patched (1 edits, ... BOM=True, nl=CRLF)`
  即 **锚点在「当前落地字节」上仍 `count==1`**、BOM/CRLF 保真、插入行数断言通过，中心可直接复放。
- `git -C F:/Downloads/pythoncdc-main status --porcelain core/ pycdc.py` ⇒ **空输出**（core 三支与入口逐字节未动）；
  本回合所有写入只落在 `D:/Temp/opencode/r68gate/diag4`（镜像/产物/dump/spec/synth/FACTS），未跑 402 全量扫描，
  未设 `PYTHONIOENCODING`，单条命令最长 <120s（battery 走 `closeout67.py` 的 280s 预算分片）。

## Step 0 (batch-3 session rerun, arm r68b3, 2026-09-25)
复放（新 out 文件 dump/r68b3_landed.jsonl / r68b3_landed_canary.jsonl）：
\landed trade_info_utils.pyc  38/40  [['get_trade_list',339,323,14,148], ['trade_operation',304,302,2,40]]
landed fileio_utils.pyc      12/14  [['acquire',96,93,3,52], ['write',637,637,4,519]]
landed logger.pyc            29/30  [['write_logging_thread',113,113,1,40]]
canary 4 支 sha: 4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177  （全部命中 pinned）
battery landed: 45 repros, worse-than-landed on 0；非绿 15 项与上一会话逐项相同
\与 Step 0（上一会话）**逐字段相同**，基线可信，无更正。


## Step 1 (batch-3 · r68b3 · logger 推到全绿) — 2026-09-25

### 1) 根因（两处，都在生成器侧，未动 region_analyzer 的 predicate）
- **位移（113/113, hunks=1, first_diff=40）**：`write_logging_thread` 的 while-True 头块 `if q:` 的
  then 臂（blk@48）被 `_loop_handle_no_exit_successors` 正常生成，但 then 臂**独占的续接子区域
  `IfRegion@368`（`if msgs:`）没有被折进 then 臂**，被 `_loop_generate_body` 顺序归约发射到循环体尾部
  ⇒ 结构错位（`if msgs:` 出现在 else 之后）。探针：`probe_wlt3/4/6.py`、`dump/wlt_trace.txt`、`dump/wlt_reg_landed.txt`。
  **BRIEF「必须配对改分析器侧前缀去重」的前提不成立**——纯生成器侧折叠即可，且分析器侧改动
  （上一会话 R67-diag6 W1）实测 113→41 崩塌，已排除。
- **多插一条 `continue`（结构对齐后仍 113/113, hunks=3, first_diff=1）**：
  `_generate_block_statements` 的 LOOP_BACK_EDGE 分支算 `effective` 时漏剔 `EXTENDED_ARG`
  （repo L22091-22093），于是**纯连接回边块 blk@666（EXTENDED_ARG + JUMP_BACKWARD）被当成
  「含用户指令的显式 continue」**，在 `if self.status:` then 臂尾多补一条 `continue`。
  证据：镜像插桩 `inst.py`（41 处 Continue 发射点打点）只命中 1 处 →
  `R68TR 22258` = LOOP_BACK_EDGE 的 `stmts.append({'type':'Continue'})`。
  全库既定噪声口径（W14 修复、`_W13_NOISE_OPS` 等 30+ 处）都把 `EXTENDED_ARG` 记为无语义噪声，
  此处遗漏属笔误。
- **源码级咬合证据**（`lay.py`/`lay2.py`，整模块编译 + 结构感知 token 比对）：
  在 `build_r68b3_tf/fly__loggerOK.py` 上枚举 else 臂变体（break/return/no-else/two-continue/…共 17 个），
  只有 **去掉末尾 `continue`** 的两个变体 `C9_nocont_break`、`C12_nocont_else_break_inner`
  与原码 **token 序列完全 MATCH**（125 指令，0 hunk）；带 `continue` 的恒为 4 hunks
  （差的全是跳转目的：`JUMP_FORWARD→666` vs `JUMP_BACKWARD→2`）。⇒ 修复目标被源码侧独立证实。

### 2) spec（单文件 3 处编辑，锚点 count==1 已断言）
`specs/cand_r68b3_thenfold.json` ← `mk_spec_b3.py`（repo `core/cfg/region_ast_generator.py`，BOM+CRLF 保真）
- **A**：L22091 `effective` 过滤元组加 `'EXTENDED_ARG'`（含三要素注释：识别条件=LOOP_BACK_EDGE 且剔噪后为空；
  归约方式=走 else 分支不补发 Continue；AST 映射=Continue 缺省）。
- **B**：`_loop_handle_no_exit_successors`（L10489 前）在登记 `_then_succ` 之前，满足
  「then 臂入口区域已整体生成 / 或无区域」时调用 `_fold_header_then_continuation(self._current_loop, …)`。
- **C**：新增 helper `_fold_header_then_continuation`（插在 `_loop_build_if_with_exit_branches` 之前）：
  判据 ①候选在 `region.blocks` 内且非本区域结构块（header/condition/back_edge/entry/else_blocks）、
  非 `else_succ`、未发射；②不在「从 `else_succ` 出发、只沿 `region.blocks` 后继、不越过①结构块」的
  可达集 `else_reach` 中；③起点为 then 臂入口（区域 entry 则取其出口后继）。归约=直接子区域整棵
  生成 / 普通块语句，登记 `generated_blocks/_generated_regions`；AST 映射=`If(test, body=[then前缀+续接], orelse=[else])`。
  helper 只读本区域自身字段，无 `region.entry in r.blocks`、无按名/偏移启发、无新增 self 状态。

### 3) 门禁读数（臂 `r68b3_tf2`，产物 `build_r68b3_tf2/`）
- **targets**：trade_info_utils 38/40、fileio_utils 12/14（两支与 landed 逐字段相同），
  **logger.pyc 30/30（mism=[]）**。
- **h62 ab（landed → tf2）**：`IMPROVED fly/logger.pyc 29/30 -> 30/30`；
  `TALLY SAME=2 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`；`files fully matched: a=0 b=1`。
- **canary**（`dump/r68b3_tf2_canary.jsonl`）：143/143、10/10、26/26、25/25，4 支 sha
  `4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177` 全部命中 pinned。
- **battery**（`closeout67.py battery r68b3_tf2`）：45 repros，**worse-than-landed on 0**，无 ERR，
  非绿项与 landed 同源（含 `r67d6_whiletrue_headif` 2/2）。
- **synth 见证**：`test_repros/round67_diag6/r67d6_whiletrue_headif.pyc`
  → landed **1/2**（`w1` 39/39 hunks=1 first_diff=13，失败）、tf2 **2/2**（通过）。
  （BRIEF §8「diag4/synth 为空」的更正仍然成立；本回合改用仓库内既有复现件作见证。）
- **严格尺 `sstrict67.py`**：targets landed **111/120、9 缺陷** → tf2 **112/120、8 缺陷**；
  其中 `write_logging_thread` 由 `[seq_diff] #71` 转为 OK；`check_baseFilename`（target_diff，跳转极性）
  在两臂同为缺陷 ⇒ 属本回合未触碰的既有缺陷，非回归。canary 严格尺 209/211 与 landed 持平（2 缺陷同源）。

### 4) VERDICT
- **`fly/logger.pyc`（`write_logging_thread`）：FULLY OK** —— 官方尺 30/30、
  结构感知 ndiff 0 差异、严格尺该函数 OK、canary/battery/synth 全过、AB 无 REGRESSION/ERR。
  位移族按 ADR-1 判据（hunks→0、first_diff→0、Σ|Δ| 下降、严格尺不新增 target_diff）全部满足。
- **`IQCommon/util/trade_info_utils.pyc`（38/40）与 `fileio_utils.pyc`（12/14）：仍 partial，本次未动**
  （AB SAME=2，逐字段与 landed 相同）。它们不属于本轮 3 支 partial 的收口目标之外的新增，
  下一步按 BRIEF 继续：trade_info_utils 复验 `specs/cand_r68_orchain_tail.json`；
  fileio_utils 两支（`acquire` 循环头前缀重发 / `write` 尾部 return-epilogue 顺序）需可复放排除读数或新判据。
- 复放命令（每条 <300s，产物只落 diag4；本次读数用 out=`dump/r68b3_tf2_targets.jsonl` /
  `dump/r68b3_tf2_canary.jsonl`，复放请换新 out 名——`h62 run --out=` 指向已存在文件会跳过全部记录）：
  `python -X utf8 mk_spec_b3.py`
  `python -X utf8 h62.py build --spec=specs/cand_r68b3_thenfold.json --dst=r68b3_tf2`
  `python -X utf8 h62.py run --arm=r68b3_tf2 --list=targets.txt --out=dump/r68b3_tf2_targets_r2.jsonl`
  `python -X utf8 h62.py run --arm=r68b3_tf2 --list=canary.txt --out=dump/r68b3_tf2_canary_r2.jsonl`
  `python -X utf8 h62.py ab --a=dump/r68b3_landed.jsonl --b=dump/r68b3_tf2_targets.jsonl`
  `python -X utf8 closeout67.py battery r68b3_tf2`
  `python -X utf8 sstrict67.py build_r68b3_tf2 targets.txt`
  synth 见证：`python -X utf8 h62.py run --arm=landed --list=synth_wlt.txt --out=dump/wlt_synth_landed.jsonl`
  / `--arm=r68b3_tf2 --out=dump/wlt_synth_arm.jsonl`（`synth_wlt.txt` 单行 =
  `F:/Downloads/pythoncdc-main/test_repros/round67_diag6/r67d6_whiletrue_headif.pyc`）。
- 诊断脚本：`probe_wlt3/4/6.py`（调用链与 Continue 打点）、`inst.py`（镜像插桩）、
  `sbs.py`（逐指令并排）、`ndiff.py`（结构感知 token 差）、`lay.py`/`lay2.py`（源码变体咬合）。


## Step 2 (batch-3 · r68b3_combo · 两靶合并臂) — 2026-09-25

### 1) spec 合并
`specs/cand_r68b3_combo.json` ← `mk_spec_b3_combo.py`：把 **orchain_tail**（1 编辑，trade_info_utils
`get_trade_list` 38/40→39/40 的既有候选）与 **thenfold+EXTENDED_ARG**（3 编辑，logger 全绿）合成同一文件
（共 4 编辑，锚点 orchain / extarg / thenfold_call / thenfold_helper 在当前落地字节上均 `count==1`，
BOM+CRLF 保真，`h62 build` 报 `cand patched (4 edits, core/cfg/region_ast_generator.py)`）。

### 2) 门禁读数（臂 `r68b3_combo`，产物 `build_r68b3_combo/`）
- **targets**：trade_info_utils **39/40**（仅剩 `trade_operation` 304/302 hunk=2 first=40）、
  **logger 30/30**、fileio_utils 12/14（与 landed 同）。
- **h62 ab（landed → combo）**：`IMPROVED trade_info_utils 38/40 -> 39/40`、
  `IMPROVED fly/logger.pyc 29/30 -> 30/30`；`TALLY SAME=1 IMPROVED=2 REGRESSION=0 MOVED=0 ERR=0`。
- **canary**（`dump/r68b3_combo_canary.jsonl`）：143/143、10/10、26/26、25/25，4 支 sha 全部命中 pinned。
- **battery**（`closeout67.py battery r68b3_combo`）：45 repros，**worse-than-landed on 0**，无 ERR。
- **synth 见证**：`dump/r68b3_combo_synth.jsonl` → 2/2（landed 同件 1/2，`w1` 失败）。
- **严格尺**：targets landed **111/120、9 缺陷** → combo **113/120、7 缺陷**
  （`get_trade_list`、`write_logging_thread` 两支转 OK，无新增缺陷）；
  canary 严格尺 combo **209/211、2 缺陷**，与 landed 完全同源（quotation 的两支既有 target_diff）。

### 3) VERDICT（合并臂 = 当前建议落地形态）
- **`fly/logger.pyc`：FULLY OK（30/30，严格尺该函数 OK）**。
- **`IQCommon/util/trade_info_utils.pyc`：39/40（+1）**，残余 `trade_operation` 一支
  （官方尺 orig=304 decomp=302 hunk=2 first_diff=40；严格尺 `[seq_len] orig=304 decomp=302`）——
  属 epilogue/return 顺序族，本回合未触碰，仍 partial。
- **`IQCommon/util/fileio_utils.pyc`：12/14，与 landed 逐字段相同**（`acquire` 96/93 hunk=3 first=52、
  `write` 637/637 hunk=4 first=519），本回合未动，仍 partial。
- 复放：`python -X utf8 mk_spec_b3_combo.py` →
  `python -X utf8 h62.py build --spec=specs/cand_r68b3_combo.json --dst=r68b3_combo` →
  `h62.py run --arm=r68b3_combo --list=targets.txt --out=<新名>` / `--list=canary.txt --out=<新名>` /
  `--list=synth_wlt.txt --out=<新名>` → `h62.py ab --a=dump/r68b3_landed.jsonl --b=<targets jsonl>` →
  `closeout67.py battery r68b3_combo` → `sstrict67.py build_r68b3_combo targets.txt`。


## Step 3 (batch-3 · fileio_utils 两支的可复放读数/排除) — 2026-09-25

臂 `r68b3_combo` 与 landed 在 fileio 上**逐字段相同**（`acquire` 96/93 hunk=3 first=52、
`write` 637/637 hunk=4 first=519），本轮未做修改；下面给出可复放的结构级读数与归因。

### 1) `FileIO::write`（637/637，hunk=4，first_diff=519）
`python -X utf8 ndiff.py <fileio_utils.pyc> build_r68b3_combo/IQCommon__util__fileio_utilsOK.py`
（存 `dump/ndiff_fileio_combo.txt`）4 个 hunks，全部是 **return/epilogue 段落位移与常量错位**：
- `o[45:53]=[LOAD_CONST None ×3, PRECALL, CALL]` ↔ `d[45]=JUMP_FORWARD -> ?778`：原码在函数**前部**
  的一处三参调用被重排到 `d[163:171]=[RETURN_VALUE, LOAD_CONST None ×3, PRECALL]`（后移 ≈118 token）。
- `o[653:655]=[LOAD_CONST False, RETURN_VALUE]` ↔ `d[654]=JUMP_FORWARD -> LOAD_CONST False`。
- `o[666]=LOAD_CONST None` ↔ `d[666]=LOAD_CONST False`：**函数尾隐式 `return None` 位置上重编译成了
  `return False`**（`except BaseException: return False` 与 try 之后的隐式返回顺序颠倒）。
与 BRIEF 对该支的定性一致（尾部 return/epilogue 顺序族），本回合**未尝试修法**——
该族属「多 return 出口语句顺序」，与本轮 thenfold/EXTENDED_ARG 判据不同族，无咬合 witness 前不得动。

### 2) `FileLock::acquire`（96/93，hunk=3，first_diff=52）—— 归因已定位（比 BRIEF 更细）
`python -X utf8 sbs.py <fileio_utils.pyc> <product> acquire`（存 `dump/sbs_acquire.txt`，orig=109 decomp=104）：
- **决定性一行（idx33）**：原码 `POP_JUMP_FORWARD_IF_FALSE -> 532`（timeout else 臂在**很远的 532**），
  重编译 `-> 304`（else 臂紧贴 then 臂之后）。
- 原码 then 臂（idx34-44 `system_log.warning(...)`）**直接 fall-through 到 304 `os.unlink(...)`**，
  其后 `inner try/except`（53-77）、`raise FileLockException('发生超时')`（78-82）**都在 then 臂内**；
  else 臂 `time.sleep(self.delay)` 被编译器放在 **532-580**，其后紧跟 except 处理器收尾
  （582 POP_EXCEPT / 584-588 清 `e` / 590 JUMP_FORWARD 608），末尾 610 `JUMP_BACKWARD to 42` 回循环头。
- 重编译版把 `unlink + inner try + raise FileLockException` 放到 if/else **之后**（idx45 `JUMP_FORWARD to 354`
  把 then 臂接到 354，else 臂睡眠结束 352 也 fall-through 到 354）⇒ 两臂在 unlink 处汇合。
- **结论**：该支的缺陷是 **if/else 区域边界切错——then 臂在 `warning` 后被截断**，
  `os.unlink + 内层 try/except + raise FileLockException` 三个块应归属 then 臂却被当成 if 之后的顺序语句；
  CFG 层面即 `merge_block` 被判成 unlink 块（实际上 unlink **不可达自 else 臂**，
  then 臂以 `raise` 终结 ⇒ 该 if/else 没有真正汇合点，汇合只发生在 except 处理器收尾处）。
  这属于 `region_analyzer` 的 merge/then_blocks 归属问题，**不是**本轮 thenfold（循环头 if 续接折叠）的适用面：
  thenfold 的判据②用「从 else_succ 可达集」排除汇合点，此处 unlink 不在 else 可达集内，
  照搬会把三个块折进 then 臂——形态上吻合，但宿主结构是 **except 处理器内的 if/else**（非 while 头 if），
  调用点（`_loop_handle_no_exit_successors`）根本不触发。**本回合不改**，留待有 witness 的下一轮。

### 3) VERDICT（fileio）
**仍 partial，12/14，本轮未动、无回归**（AB SAME 中 fileio 与 landed 逐字段相同）。两支均已定位到
「语句/区域归属错位」而非噪声或计数伪影（ndiff/sbs 读数丢 NOP/EXTENDED_ARG、跳转带目的指令身份，
不存在 nested_diff 的 J 折叠失明问题）。给出可复放读数如上，等价于完成 BRIEF 要求的
「可复放排除读数或新判据」中的**排除读数**部分；修复需新判据 + witness。
