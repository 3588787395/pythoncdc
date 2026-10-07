# Round 5 · FIX_LOOP_SINK —— 循环 / for-iter 出口的「相邻双隐式 return None sink」唯一归属

轮次：Round 5 / 破口 = B102（`quotation.get_fundflow_day`，本轮命名锚点）+ B99（`handlers.TWHThreadController._target`）。
判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代；interp 3.11.7 64 位）。
轴：与六票 if/elif 汇合族**不同**的相邻隐式 sink 归属面 —— 承 R4-B116（短路链面）的同一不变式，
本票把它表达为**循环 / for-iter 区域**的形态。
落地文件：`core/cfg/region_analyzer.py`（判据，分析端）+ `core/cfg/region_ast_generator.py`（**单一漏斗消费点一处**）。
产物一律**先删后** `python -X utf8 pycdc.py -o <base>OK.py <pyc>` 重生成，无手改。
插桩：全部探针在 `D:/Temp/rrv5/`（probe_sink.py / probe_shape.py / probe_shape2.py / probe_variant.py /
probe_cand.py / pins2.py / make_arms.py / read_r4.py / sens_census.py + `bk2/` 入轮备份），生产目录零新增脚本。

**结论标记：「代码已落地」**。
**语料翻转：+1 文件级翻面（锚点 quotation 152/153 → 153/153，153/153 = 100%）**；
单元翻转 `quotation.<module>.get_fundflow_day` Different control flow → **Equal**。
B99（handlers 29/30）**未闭**，本票实测它需要第二条机制（见 §5）。
合成臂翻转：**+3 臂 / +6 单元全绿**（`r4_probe_index` 37→40 条目，71/81 → 77/87 单元，27→30 success，
failure 逐位仍 10 条，零条绿臂转红）。

---

## 1. 两个锚点的 sink / 边证据（before → after，实测原文）

### 1.1 B102 `site-packages/fly/data/quotation.pyc` / `<module>.get_fundflow_day`

入轮探针（`D:/Temp/rrv5/probe_sink.py`，per-code-object CFG）原文：

```
blk 156 n=6 preds=[70] succs=[198, 268] last=POP_JUMP_FORWARD_IF_FALSE 268   ← elif 条件块
blk 198 n=3 preds=[156] succs=[204, 272] last=FOR_ITER 272                   ← for 头部（LoopRegion@198.entry）
blk 204 n=21 preds=[198] succs=[] last=RETURN_VALUE                          ← 循环体必返
blk 268 n=2 preds=[156] succs=[] last=RETURN_VALUE None                      ← sink A（仅被 elif 假边引用）
blk 272 n=2 preds=[198] succs=[] last=RETURN_VALUE None                      ← sink B（仅被 FOR_ITER 耗尽边引用）
认领：IfRegion@70.block_to_region=[70,112,156,268]  LoopRegion@198=[198,204,272]
```

ORIG 线性证据（`dis` 原文）：`196 POP_JUMP_FORWARD_IF_FALSE to 268` / `202 FOR_ITER to 272` /
`268 LOAD_CONST None JT` / `270 RETURN_VALUE` / `272 LOAD_CONST None JT` / `274 RETURN_VALUE`。

PROD（入轮）发射 `…for item in prod_code: … return returninfo` 后在**臂内**多材料化一条 `return None`，
于是 sink 对的**落点次序被调换**：`off196 → 272`、`off202 → 268`（工单登记值逐位复现）。
指令数不变（2 对 sink 都在），只差边归属 ⇒ 判据报 Different control flow。

after：该二块不再材料化为语句 ⇒ 臂以 for 循环收尾、函数尾无显式 return；重编译按「每条入边一份副本」
在函数尾声再生 2 对 sink，边落点复原为 `→268 / →272`。读数 **153/153、status=success** ✓。

接受形态实测（`pyc_verify single --source`，产物只在 scratch）：

```
q_drop_armret（臂内不发射 return None）      153/153 success      ← 本票落地的形态
q2（PROD 现形，臂内 return None）            152/153 目标互换
q3（return None 挪到链之后·函数级）          152/153 Different control flow（否决）
```

### 1.2 B99 `site-packages/IQCommon/logger/handlers.pyc` / `<module>.TWHThreadController._target`

入轮实测（逐位复现 Round-1 §7.3 锚点，Round-4 §6 登记的 preds 为块索引，本票为块偏移）：

```
blk 90  n=3 preds=[46] succs=[408, 104] last=POP_JUMP_FORWARD_IF_FALSE 408   ← while 头测（从未进入）
blk 390 n=3 preds=[378,212] succs=[404, 104] last=POP_JUMP_BACKWARD_IF_TRUE 104 ← 回边测试（正常退出）
blk 404 n=2 preds=[390] succs=[] last=RETURN_VALUE None                       ← sink（回边正落）
blk 408 n=2 preds=[90]  succs=[] last=RETURN_VALUE None                       ← sink（头测假边）
blk 412 n=8 preds=[0,46] succs=[458,1012] …                                  ← if 之后的同层兄弟语句
认领：LoopRegion@90.blocks ∋ {404,408}；IfRegion@46.blocks=[404,408,46,90]、
      IfRegion@0.blocks=[404,0,46,408,90] merge=412  ← 二 sink 被上层 IfRegion 重复列为成员（原则2 反向）
```

PROD 把两块并成臂尾一条 `return None` ⇒ −1 指令对（判据 Different control flow）。

**接受形态实测（本票新增的决定性事实，7 张票以来第一次把该单元的接受形态钉死）**：

```
h_else_noarmret（臂以 while 收尾、不发射 return None、后续兄弟语句归 else 臂）→ 30/30 success ✓
h_else_armret  （else 形态 + 臂内 return None）                               → 29/30
h_drop_only    （只删 return None、后续仍为兄弟语句）                          → 29/30
v3 逐指令比对：orig=203 cand=203 posdiff=0 equal=True（全序列逐位相同）
```

⇒ B99 的残余**不是** sink 发射点单点问题，而是两半：①二 sink 不材料化（本票已闭的引理）
**加上** ②IfRegion@0 的 merge=412 必须改判为 **else 臂入口**（then 臂任何块都不以 412 为后继，
412 的全部前驱是条件链的假边 ⇒ 它不是汇合点）。本票判据按 C1 只校验归属、不向任何区域追加块，
故 ②不成立（见 §5）。终态读数 handlers **29/30（未回退，仍 29/30）**。

## 2. 落地的归属不变式（判据 + 唯一消费点）

不变式：**函数尾声的相邻二块若都是「无后继 · 恰一个前驱 · 前驱以条件跳转/FOR_ITER 把控制权送出自身所属区域 ·
块内容恰为 `LOAD_CONST None; RETURN_VALUE`」的落点块，且其中至少一条边来自 LoopRegion 的区域出口角色块
（condition_block / header_block / back_edge_block），则它们是区域出口边的落点，不是语句：两块都不得材料化，
重编译按入边数在函数尾各生成一份副本。** 违反时的两种形态即 B99（并成一块，−2）与 B102（落点次序调换）。

- 判据：`core/cfg/region_analyzer.py` `_loop_tail_exit_sink_pair()`（紧邻 R4-B116 的
  `_boolop_chain_exits_are_distinct_sinks` 之后，同一 sinkexit 家族；CFG 级 memoize）。
  输入全在白名单内：块末 opcode、前驱/后继集、块指令数与 LOAD_CONST/RETURN_VALUE 形态、
  `block_to_region` 区域成员关系、LoopRegion 的角色块；无文件名/函数名/偏移特判、无深度或计数上限、
  无文本后处理、无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 命名、
  未复活 `Region.exit` / `_trailing_rn_exit_count`（本票零投资）。
- 消费点：`core/cfg/region_ast_generator.py` `_generate_block_statements`（既有「单一漏斗」）内
  紧随 `[B86-phantom]` 守卫之后一处：命中即登记 `generated_blocks/generated_offsets` 并发射空语句列表，
  **不复制、不重复发射任何块的语句**（排除「靠复制块语句来多发射一个 sink」的错误解）。
- 分析端为主的理由：判据要读 `block_to_region`（区域成员关系）与 LoopRegion 角色块，这些只在分析端存在；
  生成端只保留一个布尔消费点，与 R4-B116 的「一处判定、多处复用」同构。
- 文档字符串：新方法六项 ①算法依据 ②归约顺序 ③唯一归属判定 ④嵌套处理 ⑤入口引用语义 ⑥反编译流程
  + C1/C2/C3 齐备；被触碰的 `_generate_block_statements` 六项中 ③唯一归属判定 已就地更新为含
  `[R5-B119 loopsink]` 的归属描述。

### 2.1 判据的 C3 收窄是本票实测出来的（不是先验）

首版判据**不要求**「至少一条边是循环出口边」，实测在 quotation 内**换了一个失败单元**：

```
guard-off-broad（宽判据） quotation 152/153：失败单元 = <module>.get_stock_exrights（原为 Equal）
  其尾声二块 640 preds=[562]、644 preds=[520] 的前驱都是 if 条件块假边（无循环角色块）
  ⇒ 材料化的 `return None` 是臂尾真语句，删掉即丢一条 sink（指令数 −2）
收窄后 get_stock_exrights hits=0，Equal 复原 ✓
```

即：**纯 if 链的臂尾 sink 对属 R4-B116 建区门已闭的短路面**，本票按 §1.5 C3 把判据闭合在
「循环/for-iter 出口边 + 函数尾声相邻二块」这一语义位置；quotation 终态 153/153 即该收窄版的读数。

## 3. 门禁读数（终态 = 落地代码，产物先删后重生成）

```
single quotation                    152/153 → 153/153  status=success            ← 本票锚点翻转
single handlers                    29/30（仍 TWHThreadController._target）        未回退
batch round1/r1_probe_index        108/110 单元  44 success / 2 failure           STAY（2 条仍 r1_73、_search/handler_ifelse=B101）
batch round1/r1_regress_index       34/34 单元  17 success / 0 failure            STAY
batch round4/r4_probe_index（追加前）71/81 单元  27 success / 10 failure          STAY 逐位
batch round4/r4_probe_index（追加后）77/87 单元  30 success / 10 failure          +3 臂全绿，绿臂零转红
batch round2/r2v3_probe_index      105/126 单元  41 / 21                          STAY
batch round3/r3_probe_index        101/122 单元  35 / 21                          STAY
pytest 六套件                      277 passed / 2 failed / 2 xpassed（仍 test_B01_simple_if_then_else_merge、
                                  test_BOUNDARY_02_large_function）              = 基线
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；compileall -q core OK
```

22 pin（先删后重生成再判，全部 = 基线）：trading_dates_mixin 14/14 · stock_position 37/37 ·
cgroup_utils 8/8 · email_utils 4/4 · calexrights_func 8/8（二份）· future_contract_info 29/29 ·
fly/logger 64/64 · ptradeAccount 137/137 · executor 10/10 · history_api 19/19 · quote 86/92 ·
trade_info_utils 37/41 · trade_live_broker 118/128 · strategy 26/27 · api_base 27/28 · matcher 16/17 ·
finance 31/32 · bar 84/85 · function 70/71 · load_daily 26/27 · realtime_event_source 12/13 ·
profiler_func(IQEngine/utils) 17/18。
同名 basename 的其它文件（IQCommon/strategy 2/2、IQEngine/core/strategy 20/20、IQEngine/api/api_base 49/49、
local_variables/finance 132/132、local_variables/bar 22/22、risk_calculation/function 15/15、
fly/common/function 4/4、IQCommon/profiler_func 17/17、IQData/utils/profiler_func 15/15）
全部仍 100% success ⇒ **零 sink-collapse 回退**。未跑 402 八分片批（按工单由主代理持有）。
**终态复判（最后一次代码改动之后，产物再删再生）**：quotation **153/153 success** ·
handlers 29/30（仍 `_target`）· r1_probe 108/110 · r1_regress 34/34 · trading_dates_mixin 14/14 ·
stock_position 37/37 · r4_probe（40 臂）77/87 · 30/10 ⇒ 与上表逐位相同（后续改动全在 docstring 内）。

## 4. 标记 · True-hits vs flips · 残留

```
新增标记 [R5-B119 loopsink]：3 处（region_analyzer.py 判据 docstring ×1，region_ast_generator.py 守卫注释 ×1、
③唯一归属判定 ×1）
必须存活的标记（core/cfg 三文件合计，逐条 = 基线）：
  [R2-B106] 4 · [R2-B107] 7 · [R2-B108] 5 · [R3-B115] 1 · [R3-B109] 3 ·
  [R4-B116 sinkexit] 4 · [R5-B100-armjoin-trueentry] 4
残留 grep（python 计数）：硬编码深度/数量/语句上限 0；文件名·函数名·偏移特判 0；文本后处理 0；
禁止前缀新增方法 0；Region.exit 未读未写；_trailing_rn_exit_count 未动；复制块语句式补发射 0。
True-hits vs flips：见 §4.1。
```

### 4.1 True-hits vs flips（实测）

判据 True-hit census（`D:/Temp/rrv5/sens_census.py` B 段：逐 code object 建 CFG + analyze + 取判据集合；
范围 = r1_probe 46 + r4_probe 40 + 4 个 pin 文件）：

```
命中文件 9 个 / 命中 code object 9 个：
  r1_62_cand_while_epi_dup 1 · r1_63_cand_while_epi_dup_fn 1
  r4v3_b09_b99_while_try_ifarm 1 · r4v3_b10_b99_while_try_fnend 1 · r4v3_b11_nested_not_in_loop 1
  r4v3_a38_b119_while_twin_sinks 1 · r4v3_a39_b119_foriter_edge_swap 1
  handlers.pyc 1（在 _target，但命中的是函数尾二块 1016 preds=[458] / 1020 preds=[504]，
                  不是 B99 的 404/408 —— 见 §1.2）
  quotation.pyc 1（= get_fundflow_day，二块 268/272）
True-hits 9 → flips：语料单元 1（quotation.get_fundflow_day Different→Equal，文件 152/153→153/153）
                    + 合成臂 1（r4v3_a39，见下方 deform 实测）
其余 7 次命中零读数变化：r1_62/r1_63/b09/b10 命中前后同为 success（无回退）、b11 命中前后同为
failure（命中未翻转，如实登记）、a38/a40 同为 success、handlers 同为 29/30（未恶化亦未闭）。
```

**判据的实弹可反证性（deform 测试，`D:/Temp/rrv5/deform_guard.py`：在生产进程内把判据桩为恒空集再发射）**：

```
GUARD-ON   a38 2/2 success · a39 2/2 success（发射体 = …for i in x: return 2，无 return None）
GUARD-OFF  a38 2/2 success · a40 2/2 success
GUARD-OFF  a39 ***<module>.a39: Failure: Different control flow  units=1/2
           发射体 = '…elif isinstance(x, list):\n        for i in x:\n            return 2\n        return None\n'
           ← 正是 B102 形态：臂尾多材料化一条 return None
⇒ a39 是常驻牙齿臂（只有本判据在场才绿）；a40 是必须恒绿的对照（判据对其 hits=0）。
```

### 4.2 终态文件完整性（落地态，非回滚态）

```
core/cfg/region_analyzer.py      2045409 → 2052197 bytes / \n 32167 → 32266 / 前导 BOM 1 / 全 CRLF /
                                 bare LF 0 / sha256[:16] 2a7517c61b083449 → 0212c54e4d0c790e
core/cfg/region_ast_generator.py 3684310 → 3685863 bytes / \n 58668 → 58685 / 前导 BOM 1 / 全 CRLF /
                                 bare LF 0 / sha256[:16] ab05c4c6bb9da904 → 9c36c741bd972593
core/cfg/code_generator.py       未触碰
禁止前缀新增方法 0（`def _merge_` 2 处在入轮备份 D:/Temp/rrv5/bk2/ 中即已存在，本票零新增）；
Region.exit 写入 0（`.exit =` 赋值 0 处）；`_trailing_rn_exit_count` 仍 2 处 = 入轮逐位（未动、未消费）；
core/ 全量 .py 内 probe[0-9] 残留 0；新增符号只 _loop_tail_exit_sink_pair（3 处：def + memoize + 消费）
与 _loop_tail_sink_pair_cache（2 处）。
```


## 5. r1_73 与收窄后的残余

**r1_73 状态：1/2 MISMATCH（未翻面），且本票确认它不属本轴。** 实测 CFG 原文：

```
blk 18  n=1 preds=[14,54,136] succs=[148,20] last=FOR_ITER 148
blk 148 n=2 preds=[18]      succs=[]          last=RETURN_VALUE None    ← 循环耗尽 sink（单前驱）
blk 194 n=2 preds=[152,164] succs=[]          last=RETURN_VALUE None    ← if 链汇合 sink（二前驱，非相邻二块）
```

r1_73 的两个 sink **既不相邻也不是「单前驱落点对」**（194 有二前驱；按块序末二块是 164/194，164 非 sink）
⇒ 判据 hits=0。它真正的拦路石是**前票登记的 try/else 认领面**，本票实测复现：
`blk 54 n=6 preds=[24] succs=[18] last=JUMP_BACKWARD` 被 **LoopRegion@18** 认领，
而它的前驱 `blk 24` 属 **TryExceptRegion@24** —— else 体落在 try 区域内却归了循环 ⇒ 另一条归属轴
（try/else 成员认领），本票未触碰、判为**独立破口**。

**B99 最窄表述（下一票）**：二 sink 的「不材料化」引理本票已落地并可用（quotation 即证据），
B99 差的只是第二条：`IfRegion.then_blocks` 全部路径都终止于无后继 sink 块、而 merge 块的全部前驱
都是区域自身条件块的假边时，merge 不是汇合点而是 **else 臂入口**（then/else 边界求解，rules §3.2.1；
亦即 FIX_PARENT_EDGE §4.2 预告的「另一半」）。接受形态已实测为 30/30（§1.1/§1.2 v3 行）。

## 6. 索引追加（交付物 4 已执行）

`test_repros/round4/r4_probe_index.json` 37 → 40 条目，新增三臂（每条 `.py` / `.pyc` / `OK.py` 三件套齐备，
索引内所有既有路径 + 新路径逐一核对 missing_pyc=0、missing_OK=0）：

```
r4v3_a38_b119_while_twin_sinks          while 宿主双 sink（头测假边 + 回边正落）      2/2 success
r4v3_a39_b119_foriter_edge_swap         for-iter 边互换（elif 假边 + FOR_ITER 耗尽）   2/2 success
r4v3_a40_b119_loop_single_sink_control  对照：循环只有一个尾声 sink（判据必须不命中）  2/2 success
```

追加后 r4 索引读数 77/87 单元 · 30 success / 10 failure ⇒ 相对追加前 71/81 · 27/10 为纯增量，
原有 10 条红臂逐位不变（无绿臂转红）。

