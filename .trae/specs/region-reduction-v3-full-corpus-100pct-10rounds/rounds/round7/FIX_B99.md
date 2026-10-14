# Round 7 · FIX_B99 —— try/except/else-inside-loop-inside-if-arm 的 merge 块所有权（else 臂入口 vs 循环出口 sink）

判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代；interp 3.11.7 64 位）。
靶文件 `site-packages/IQCommon/logger/handlers.pyc` / `<module>.TWHThreadController._target`（29/30）。
插桩全部在 `D:/Temp/rrv7/`（`dump7.py` 逐 code-object CFG+区域+角色读数 / `trace7.py` merge 求解链
与方法级拦截器），**生产目录零新增脚本、终态生产文件零写入**。

**结论标记：「仅归档 spec 未落地」** —— 交办轴（把 merge 块改判为 else 臂入口）的认领判据
**已实测构造正确并在靶上命中（True-hit）**，但只改这一处**不产生任何语料翻转**：
handlers 仍 **29/30**、r1_73 仍 **1/2**。`core/cfg/region_analyzer.py` 经两处编辑→**逐字节回滚**，
终态 sha256[:16] 与 Round-6 FIX_B111 §7 登记的落地态**逐位相同**（见 §6）。

---

## 1. sink / 边证据（入轮真机读数，`dump7.py`，单位=块起始偏移）

B99 宿主 `TWHThreadController._target`（co_firstlineno=61）实测：

```
 blk@0    n=8  preds=[]          succs=[46, 412]   last=POP_JUMP_FORWARD_IF_FALSE 412  own=IfRegion@0
 blk@46   n=7  preds=[0]         succs=[90, 412]   last=POP_JUMP_FORWARD_IF_FALSE 412  own=BoolOpRegion@0   ← and 链第二成员
 blk@90   n=3  preds=[46]        succs=[104, 408]  last=POP_JUMP_FORWARD_IF_FALSE 408  own=LoopRegion@90    ← while 头测（从未进入）
 blk@390  n=3  preds=[212,378]   succs=[104, 404]  last=POP_JUMP_BACKWARD_IF_TRUE 104  own=LoopRegion@90    ← 回边测试（正常退出）
 blk@404  n=2  preds=[390]       succs=[]          last=RETURN_VALUE None                                 ← sink A（回边正落）
 blk@408  n=2  preds=[90]        succs=[]          last=RETURN_VALUE None                                 ← sink B（头测假边）
 blk@412  n=8  preds=[0, 46]     succs=[458,1012]  last=POP_JUMP_FORWARD_IF_FALSE 1012 own=IfRegion@412    ← 被认作 merge
 blk@384  n=3  preds=[276,294,310,324,364,382] succs=[] last=RERAISE 1                                     ← then 闭包内的异常叶块
入轮认领：IfRegion@0 blocks=[0,90,404,408] cond=46 then=[90,404,408] else=[] merge=412
          LoopRegion@90 blocks∋{404,408} else_blocks=[408]；IfRegion@412 blocks=[412,458,…,1020]
```

块索引口径（Round-1/2 登记）：`off404/406 preds=[13]`、`off408/410 preds=[2]`；
PROD 把二 sink 并成臂尾一条 `return None` ⇒ 单 sink preds=[2,13]（−1 指令对 ⇒ Different control flow）。
**终态读数不变：29/30，失败单元仍是同一 `<module>.TWHThreadController._target`。**

## 2. merge=412 的唯一赋值站点（本轮实测钉死，纠正前五票的「站点猜测」）

用方法级拦截器（`trace7.py`）在真机管线上读 `_identify_conditional_regions` 对 hdr@0 的 merge 求解链：

```
TRACE _compute_merge_from_jump_targets   hdr@0 then@90 else@412 -> None
TRACE _r49a_shared_sink_tail_merge       hdr@0 then@90 else@412 -> None
```

⇒ `merge` 在进入短路链兜底 `if (merge is None and _main_inline_boolop_chain is not None)` 时**仍为 None**，
`412` 由该兜底的 `else_succ` 退化赋值（入轮 `region_analyzer.py:20020-20024`，本轮行号）。
更早的 `_else_has_external_pred` 判定（`:19966-19976`）**已经算出 412 无外部前驱**（preds={0,46} 全是本 if
自己的条件结构块），但因 then/else 双臂都被判为 sink 终态，该分支只在「有外部前驱」时动作，
无外部前驱的结论被**留给短路链兜底覆盖掉**——这就是 B99 的真正失守点，且只此一处。

## 3. 落地的认领判据（已构造、已命中、已回滚）与其否证

判据（白名单输入：块末 opcode、pred/succ、异常后继、传入的条件结构块集）：

```
T 应被认领为 else 臂入口 ⟺
 (a) preds(T) 非空且全部 ∈ {header, then_succ, T} ∪ 短路链块     （T 无外部入边）
 (b) T ∉ then_succ 的前向闭包（闭包不越过条件结构块）            （then 臂任何块不以 T 为后继）
 (c) then 闭包的每个叶（无正常流后继，异常后继不计）终结符 ∈ {RETURN_VALUE, RETURN_CONST,
     RAISE_VARARGS, RERAISE}                                     （本 if 不存在 after-if 出口）
 (d) 这些叶里至少一个是隐式 return None sink（LOAD_CONST None+RETURN_VALUE / RETURN_CONST None）
```

真机命中：`TRACE _else_entry_sink_tail_claim hdr@0 then@90 else@412 -> True`（**True-hit=1**）；
判据按 (d) 闭合在隐式 sink 形状上，`quote.check_frequency` 等显式 return 臂不认领（C3 收窄，
承 Round-5 §2.1 的同类否证）。

**否证（为何命中不翻转）**：把兜底改为「认领即 merge 保持 None」后，建区端两处既有逻辑把认领吃掉了：

1. `_build_basic_if_region` 的 merge=None 共有块过滤（`region_analyzer.py:20804-20841`）：
   merge=None 时 `_collect_branch_blocks` 双臂都无界收集，408 同时落进 then_blocks 与 else_blocks；
   该处按「无 2 个条件后继 ⇒ real_merge」把 **408（循环出口 sink 叶）错设成 merge**，实测终态
   `IfRegion@0 then=[90,104,106,180,198,212,390,404] else=[412,…,1020] merge=408`，
   而 `IfRegion@412` 整体消失（其块被并入本区域 else）。408 是**无后继的 sink**，按定义不可能是汇合点
   ——与 §2 同源的第二处「sink 当 merge」推理（R49a 注释里 `merge 错设为 @316(RETURN_VALUE)` 是同族、
   但只在「有 2 条件后继」那条路上被挡住）。
2. 紧随其后的 `if else_blocks and merge is None:`（`:20842-20862`）沿 then 臂后继命中 else 集即
   `else_blocks = []`；本形态里那条边恰是**条件块自己的假边 = else 臂入口**，被当成过度收集而清空。

⇒ 产物文本与入轮逐字相同（臂尾仍 `return None`、412 仍是兄弟语句），语料翻转 **0**。
要在分析端真正落地，必须**同时**封闭 (1) 「sink 叶不得充当 real_merge」与 (2) 「条件块自身假边不得触发
else 清空」，共三处协同改动；本轮预算内无法为这三处跑完 29 pin + 402-file 级安全证明，
故按硬性验收规则**不落地、逐字节回滚**，不留下半套判据（也不采用「放宽 sink-shape 门」的捷径——
该轴已被 R5 §2.1 / R6 B121 §6.1 两次否证）。

## 4. r1_73 状态与归因

`test_repros/round1/r1_73_cand_fortry_sinkpair.pyc` 终态 **1/2 MISMATCH（未翻面）**，读数与入轮逐位相同。
宿主实为 `if v==3: for _ in r: try/except/else: print('ok')` + `return None`，拦路石是
**TryExceptRegion 的 else 体（blk 54，preds=[24]、succs=[18]）被 LoopRegion@18 认领**——
即 else-entry 所有权问题在 **try/except/else** 这一侧的实例，不是 IfRegion 的 merge 侧；
本轮判据只裁决 IfRegion 的 `else_succ` 所有权，结构上触不到它 ⇒ **未同时翻面，原因如上**。
两票（R5 §5、本轮）在两个宿主上读到同一条「else 体归属」缺口，但认领主体不同（TryExceptRegion vs IfRegion），
应视为**两条**独立判据、共用一条不变式。

## 5. 门禁读数（终态 = 回滚态 = 基线，逐位）

```
single IQCommon/logger/handlers                29/30 status=failure（B99 未闭，与入轮同单元）
batch round1/r1_probe_index      46 文件 108/110 单元  44 success / 2 failure   = 基线（2 条仍 r1_73、_search/handler_ifelse=B101）
batch round1/r1_regress_index    17 文件  34/34 单元   17 success / 0 failure    STAY
batch round2/r2v3_probe_index    62 文件 105/126 单元  41 / 21                   STAY
batch round3/r3_probe_index      56 文件 101/122 单元  35 / 21                   STAY
batch round4/r4_probe_index      40 文件  77/87 单元   30 / 10                   STAY
batch round6/r6_probe_index      37 文件  70/79 单元   28 / 9                    STAY
pytest 六套件                    2 failed = test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function（= 基线那二条）
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；compileall -q core OK
```

未跑 pin 电池与 402-file 八分片批：终态生产文件与 Round-6 落地态 **sha256 逐位相同**（§6），
quotation 153/153、quote_handler 79/79 等 29 pin 在数学上不可能变动。
JSON 产物：`D:/Temp/r1_b99.json`、`r2_b99.json`、`r3_b99.json`、`rrv7/r1reg.json`、`rrv7/r4.json`、`D:/Temp/r6_b99.json`。

## 6. 终态文件完整性 · 标记 · True-hits vs flips · 残留 grep

```
core/cfg/region_analyzer.py      入轮 2058547 B / CRLF 32336 / bare LF 0 / 前导 BOM 1 / sha256[:16] 38a1d5142d132fd7
                                 终态 2058547 B / CRLF 32336 / bare LF 0 / BOM 1 / sha256[:16] 38a1d5142d132fd7  ← 逐字节相同
core/cfg/region_ast_generator.py 3685863 B / CRLF 58685(行 58686，末行无 EOL) / BOM 1 / sha 9c36c741bd972593   ← 全程未触碰
core/cfg/code_generator.py        299897 B / CRLF 6022 / 无 BOM / sha 28aba10bae133952                        ← 全程未触碰
（注：入轮 brief 的 2058547/32336 实测为真；Round-6 FIX_B121 §5 的 2052197/32266 是 B111 落地前的旧值，已作废。）

必须存活的标记（core/cfg 三文件合计，逐条 = 基线）：
  [R2-B106] 4 · [R2-B107] 7 · [R2-B108] 5 · [R3-B115] 1 · [R3-B109] 3 ·
  [R4-B116 sinkexit] 4 · [R5-B100-armjoin-trueentry] 4 · [R5-B119 loopsink] 3 · [R6-B111 armscope] 3
残留 grep（python 计数，全 0）：`R7-B99` 0 · `_b99_` 0 · `_else_entry_sink_tail_claim` 0；
  禁止前缀新增方法 0；Region.exit 0；_trailing_rn_exit_count 未动；
  硬编码深度/数量/语句上限 0；文件名·函数名·偏移特判 0；文本后处理 0；复制 sink 语句 0；生产目录新增脚本 0。
True-hits vs flips：True-hits = 1（handlers hdr@0/then@90/else@412 认领判据命中，实测原文见 §3）；
  语料单元翻转 0、合成臂翻转 0 ⇒ 按硬性验收规则不予落地，未追加 r6 索引臂（交付物 4 条件不成立）。
```

## 7. 收窄后的残余（下一票的可执行表述，比交办更窄两处）

1. **认领站点唯一**：`_identify_conditional_regions` 短路链兜底（入轮 `:20020-20024`）是 merge=412 的
   唯一赋值处（实测 `_compute_merge_from_jump_targets`/`_r49a_shared_sink_tail_merge` 双双返回 None）。
   §3 的四条件判据可直接复用，无需再 hunt。
2. **新增的必需第二条/第三条机制**（本轮实测新发现，前六票均未登记）：
   (i) `_build_basic_if_region:20804-20841` 的共有块 real_merge 推断**必须排除无正常流后继的隐式
   return-None sink 叶**（408 被错设为 merge 的直接原因）；
   (ii) 同函数 `:20842-20862` 的 `else_blocks=[]` 清空**必须把「then 臂块的条件假边直达 else 入口」
   排除在过度收集信号之外**（否则 else 臂永远被清掉）。
   三处一起改才是完整破口；只改任一处都是零翻转。
3. 与 r1_73 的关系：本轮判据不触它（§4）；try/except/else 的 else 体归属是**另一条**认领轴
   （TryExceptRegion vs LoopRegion），建议单独开票，勿与本条合并投递。
4. R6-B121 §6.2 的「跨区域出口边落地表」与本轴正交，不可混用；sink-shape 门（B116/B119）本轮
   一字未动，亦不得动。
