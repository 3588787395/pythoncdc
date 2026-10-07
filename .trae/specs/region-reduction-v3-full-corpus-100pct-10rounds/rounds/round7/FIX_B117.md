# Round 7 · FIX_B117 —— D 族「出口边落点被认领广播吞掉」：认领步与发射步分离，语料 1 整文件翻面

轮次：Round 7 / 破口 = **B117**（`rounds/round4/REVIEW.md` §3 行 #2 与 §6）。
主靶 `site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` 12/13、
次靶 `site-packages/IQEngine/utils/profiler_func.pyc` 17/18。
判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代；interp 3.11.7 64 位）。
落地文件：**`core/cfg/region_ast_generator.py` 单文件**；`region_analyzer.py`、`code_generator.py` 逐字节未动。
产物一律先删后 `python -X utf8 pycdc.py -o <base>OK.py <pyc>` 重生成，无手改 `*OK.py`。
插桩全部在 `D:/Temp/rrv7/`（`b117_diff.py` / `b117_ops.py` / `b117_dis.py` / `b117_pdis.py` /
`dump_cfg7.py` / `b117_reg.py` / `b117_trace_sf.py` / `b117_trace2.py` / `b117_dbg.py` /
`b117_arms.py` / `b117_final.py` / `b117_pins.py` / `b117_deform.py`），生产目录零新增脚本；
交付物 4 的三臂属 `test_repros/round6/`，另计。

**结论标记：「代码已落地」**。
**语料翻转：+1 文件级翻面 —— `IQEngine/utils/profiler_func.pyc` 17/18 → 18/18 status=success**
（单元 `<module>.ProfilerTool.show_func` Different control flow → Equal，指令差量 **−67 → 0**）。
`realtime_event_source.pyc` 仍 **12/13**（其站点与本票不同，见 §3；未强行凑）。
合成臂：**+3 臂 / +6 单元全绿**（`test_repros/round6/r6_probe_index.json` 37 → **40** 条目，
70/79 · 28 success/9 failure → **76/85 · 31 success/9 failure**，原 9 条红臂逐位不变）。

---

## 1. 出口边在哪一行被丢（file:line 证据 + 前驱集，全部实测）

靶单元 `<module>.ProfilerTool.show_func`（`co_firstlineno=146`，26 块）。ORIG 边事实（`dump_cfg7.py` +
`b117_reg.py` 原文）：

```
blk@950  n=1  preds=[254,816]  succs=[954]           last=GET_ITER        ← 循环①的 for_iter_setup（二分支汇合块）
blk@954  n=1  preds=[950,956]  succs=[956,1060]      last=FOR_ITER 1060   ← 循环①头；耗尽边落点 = 1060
blk@956  n=1  preds=[954]      succs=[954]           last=JUMP_BACKWARD   ← 回边
blk@1060 n=58 preds=[954]     succs=[1412]          last=GET_ITER        ← 出口边落点：8 条语句段 + 循环②的迭代器准备
blk@1412 n=1  preds=[1060,1414] succs=[1414,1660]   last=FOR_ITER 1660   ← 循环②头
blk@1414 n=45 preds=[1412]    succs=[1412]          last=JUMP_BACKWARD
blk@1660 n=8  preds=[1412]    succs=[]              last=RETURN_VALUE None ← 函数尾
LoopRegion@954  FOR_LOOP header=954 back_edge=956 setup=950 body=[954,956] else=[1060] blocks=[950,954,956,1060]
LoopRegion@1412 FOR_LOOP header=1412 back_edge=1414 setup=1060 body=[1412,1414] else=[1660] blocks=[1060,1412,1414,1660]
```

**丢边链（两步分离，缺一不可）**：

1. `region_ast_generator.py:5878-5887`（`_loop_generate_for` 的 `_other_loop_fis` 过滤）把
   循环① 的 `else_blocks=[1060]` 从 `_filtered_else_blocks` 中**剔除**，理由写着「交由该 LoopRegion 的
   `_loop_generate_for` 完整处理」⇒ 循环① **不再交付** 出口边之后的语句段（`else_stmts=[]` ⇒
   `_sequential_after_loop=[]`，`_loop_generate_for(entry@954)` 实测只返回 1 条 `For`）。
2. 但「交给循环②」这一步在同一宿主里**从未发生**：`_generate_block_statements_body` 的
   GET_ITER for_iter_setup 守卫（`region_ast_generator.py:51872-51902`）在处理 blk@950 时
   整树生成 LoopRegion@954，随后 `for _lb in _lr.blocks: self.generated_blocks.add(_lb)`
   （原 `:51818-51820`，现 `:51899-51904`）把 **LoopRegion@954 的全部成员块**登记为「已生成」——
   其中包括它并未发射的 1060。父顺序流随后走查 `reg@1060`（1 块 BASIC 区域）时命中
   `if block in self.generated_blocks: continue`（`_generate_basic_region`，`:51147`）⇒ 整段 58 指令不发射，
   且循环② 也永远不以 `For` 形态出现（守卫对 @1412 的递归生成机会被同一次认领吞掉）。

调用栈实证（`b117_trace_sf.py` / `b117_trace2.py` 原文）：

```
CALL _loop_generate_for entry@954 setup=950 blocks=[950,954,956,1060] gen_setup=True → RET For ret_n=1
_generate_region(reg@950 BASIC) > _generate_basic_region > _generate_block_statements(blk@950)
  > _generate_block_statements_body(blk@950) > _generate_region(reg@954 FOR_LOOP) > For
_generate_region(reg@1060 BASIC) > _generate_basic_region → ret_n=0      ← 语句段无人发射
_generate_region(reg@1412 BASIC)（非 FOR_LOOP！）> blk@1412 → ret_n=0
_generate_region(reg@1414 BASIC) → ['Assign','Assign','Expr','Expr']     ← 循环体被平铺
UNGENERATED show_func -> [144]
```

即：**离开区域的边（FOR_ITER 耗尽边 954→1060）被区域成员登记当成区域内直落**，穿过该边的语句段失去唯一
发射方。这正是工单登记的 D 族方向（内吞，与 A 族外推相反）。条款：§1.2 原则2（认领者≠发射者，语句段失主）
+ 原则1（区域应向父层交付「出口边之后的顺序代码」，此处未交付）+ §1.5 **C3**（落点块的发射点未被显式认领）。

## 2. 落地的规则（认领广播 ≡ 发射事实）

新方法 `RegionASTGenerator._loop_unemitted_exit_landing(region, block)`（`region_ast_generator.py:51692`，
标记 `[R7-B117 exitclaim]`，与 `[R4-B116 sinkexit]` / `[R5-B119 loopsink]` / `[R6-B111 armscope]` 同族）：
block 是「区域出口边的落点、且区域自身归约并未发射」的块 ⇔
(a) `block ∉ {header_block, condition_block, back_edge_block, metadata['for_iter_setup']} ∪ body_blocks`；
(b) `block` 是角色块（header/condition）**正常后继**中不属于循环体的那块（出口边落点，由块末跳转 opcode 体现）；
(c) 从 `body_blocks − {header, condition}` 出发沿**正常后继**正向展开不可达 `block`（遍历不越过角色块，
异常后继 `exception_successors` 不参与）——可达者为体内延续（break 落点、continue 回边），不属本判据。
唯一消费点 = GET_ITER 守卫的认领广播（`:51899-51904`）：`_lb not in self.generated_blocks`
（区域自己没登记 ⇒ 没发射）且判据为真时**跳过认领**，把块留给父顺序流，由其宿主（本例是后继
LoopRegion 的 for_iter_setup 守卫）发射。输入全在白名单内（区域成员关系 + 前驱/后继 + 块末 opcode +
异常边排除），无文件名·函数名·偏移·块号特判，无深度/数量/语句上限，无文本后处理，不复制语句，
不把任何臂塌成 `pass`，不发射死代码，不消费 `Region.exit`（无写入方）也不读 `_trailing_rn_exit_count`
（`:2357`/`:2363` 本票未动、未据其立规则）。落地后 `show_func` 实测：`blk@1060` 被父层重新走查
（`CALL _generate_block_statements blk@1060`），8 条语句段 + `for y in zip(...)` + 体 + 尾块全部复原。
docstring 六项 ①算法依据 ②归约顺序 ③唯一归属判定 ④嵌套处理 ⑤入口引用语义 ⑥反编译流程 + C1/C2/C3 齐备；
被触方法 `_generate_block_statements_body` 的 ③ 项就地补齐同一口径（`:51781-51783`）。

## 3. 两靶是否同一站点（实测否证交办合并）

* `profiler_func.show_func`：**是**上述站点（守卫认领广播 + `_other_loop_fis` 让位），本票修复并翻面。
* `realtime_event_source.clock_worker`：**不是同一站点**。入轮差量已移动（工单 −102 → 实测 **−112**，
  `orig ins 1442 / prod ins 1330`），丢失段为 `delete orig[1192:1259] off7972-8344` +
  `replace orig[1260:1306] off8348-8590`（即工单点名的 `if persist_flag is False:` 段，100→114 条）
  与 `delete orig[959:976] off6690-6782`。落地态复测：**12/13、−112 逐位不变**（`PRED` 在该单元零调用），
  证实 Round 5 §1 行⑤的实名站点仍是 `region_ast_generator.py:21080`（or-extension 正臂只交臂首块），
  与本票的「成员认领广播」无交集。⇒ 本票不动 21080（避免重复 Round 5 的「命中未翻转」），
  clock_worker 残余留在 §6。
* 工单 §anchor 的 PROD 读数（`off5598 jump_off=None`、`preds=[78,79]`）方向正确：那同样是
  「穿过区域的边失去发射方」，但边类型是 `if self.active` 的**函数退出边**（ORIG `blk@5598
  preds=[5492,5594,6792] succs=[5614,9214,exc 9218]`，`blk@9214 preds=[5598] last=RETURN_VALUE`），
  落点在 21080 而非本票判据域。

## 4. 门禁读数（终态 = 落地代码；两靶 + 全 6 批 + pin 均先删后重生成）

```
single IQEngine/utils/profiler_func            17/18 → 18/18 status=success        ← 本票锚点翻转（整文件翻面）
single …/realtime_event_source                 12/13（仍 clock_worker，−112 不变）  未回退、未被强凑
batch round6/r6_probe_index（追加前 37 臂）     70/79 单元 37 文件 28/9               = 基线逐位
batch round6/r6_probe_index（追加后 40 臂）     76/85 单元 40 文件 31/9               +3 臂全绿，原 9 红臂逐位不变
batch round1/r1_probe_index                   108/110 单元 46 文件 44/2             STAY
batch round1/r1_regress_index                  34/34  单元 17 文件 17/0             STAY
batch round2/r2v3_probe_index                 105/126 单元 62 文件 41/21            STAY
batch round3/r3_probe_index                   101/122 单元 56 文件 35/21            STAY
batch round4/r4_probe_index                    77/87  单元 40 文件 30/10            STAY
pytest 六套件                    2 failed, 277 passed, 2 xpassed（仍 test_B01_simple_if_then_else_merge、
                                 test_BOUNDARY_02_large_function）= 基线
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；compileall -q core rc=0
```

Pins（先删后重生成再判，全部 = 基线，失败单元名单亦同位 ⇒ 无「翻一个输一个」）：
**quotation 153/153 success · quote_handler 79/79 success · handlers 29/30（仍 TWHThreadController._target）** ·
IQEngine/utils/logger(handlers) 17/17 · trading_dates_mixin 14/14 · stock_position 37/37 · cgroup_utils 8/8 ·
email_utils 4/4 · calexrights_func 8/8（二份）· future_contract_info 29/29 · ptradeAccount 137/137 ·
executor 10/10 · history_api 19/19 · matcher 16/17（仍 DefaultMatcher.match）· IQCommon/data/finance 31/32
（仍 get_fields）· local_variables/finance 132/132 · core/bar 84/85（仍 BarData._history_bars）·
local_variables/bar 22/22 · load_daily 26/27（仍 `<module>`）· quote 86/92（仍 build_current_period_df/
check_frequency/…）· klinedata 61/64（仍 get_kline_by_count_new/get_multiminute_his_data/…）·
wizard_quant_api 55/58（仍 filter_desicion + 二条 genexpr）· real_quote 43/45 · order_api 35/37 ·
trade_info_utils 37/41 · trade_live_broker 118/128。
未跑：402 语料八分片批（并行会话占机，按工单禁止）。

## 5. 标记 · True-hits vs flips · 残留

```
新增标记 [R7-B117 exitclaim]：3 处（判据 docstring、认领广播消费点注释、_generate_block_statements_body ③ 项）
必须存活的标记（core/cfg 三文件合计，前缀口径，逐条 = 基线）：
  [R2-B106] 4 · [R2-B107] 7 · [R2-B108] 5 · [R3-B115] 1 · [R3-B109] 3 · [R4-B116 sinkexit] 4 ·
  [R5-B100-armjoin-trueentry] 4 · [R5-B119 loopsink] 3 · [R6-B111 armscope] 3
残留 grep（python 计数）：新符号 `_loop_unemitted_exit_landing` 3 处（def + 消费 + ③ 文档引用）；
  R5-B117 0 · `_or_extension_arm_block_run` 0 · `R7-B117 probe` 0 · 禁止前缀新增方法 0 ·
  硬编码深度/数量/语句上限 0 · 文件名·函数名·偏移·块号特判 0 · 文本后处理 0 · 抑制式/死代码发射 0 ·
  `print(` 42 / `_fallback` 14 / `_temp_` 2 / `probe` 30 均为**入轮既存**计数（本票新增代码不含上述任一 token），
  临时插桩全在 D:/Temp/rrv7，生产目录零新增脚本。
True-hits vs flips：
  True-hits（判据实际拦截认领的次数）= 语料 1 处（`profiler_func.show_func`：PRED reg@954 blk@1060 → True，
    实测原文 `already_gen=False, body=[954,956], hdr=954, setup=950, els=[1060], blocks=[950,954,956,1060]`）；
    其余 39 臂 / 29 pin / 6 批的认领广播无一被跳过（读数逐位 = 基线）⇒ 命中不扩散。
  flips = 语料文件 1（profiler_func 17/18→18/18，单元 show_func Different→Equal，差量 −67→0）+ 0 单元回退。
  合成臂 flips：0（三臂在入轮代码态亦为 2/2；见 §7 的常驻牙齿如实登记）。
```

## 6. 收窄后的残余（下一票的可执行表述）

1. **B117 有两种落点，本票只闭了其一**：`profiler_func` 形 = 出口边落点块被**区域成员认领广播**吞掉
   （已闭）；`clock_worker` 形 = `if self.active`（ORIG `blk@5598`，假边落 `blk@9214` 函数尾 sink，
   `preds=[5492,5594,6792]`）的函数退出边在 **or-extension 正臂序列**（`region_ast_generator.py:21080`，
   同形站点 21099）被截成臂首块，尾随语句段失去发射方。两票不同站点，不得再当作「同机制」并档。
2. `clock_worker` 还需与 Round 5 §6.2 / Round 7 FIX_CHAIN_TAIL §7.1 的**臂尾外提 / while 出口叶再归位**
   并轨才有翻转（单点 21080 已实测 −102→−4 而 0 翻面）。
3. `region_ast_generator.py:5878-5887` 的 `_other_loop_fis` 让位仍是一次「只让位不背书」的剔除：
   更彻底的表述是让位时**当场**要求后继 LoopRegion 可被发射（后继区域的 entry/setup 可达性），
   本票选择在认领侧闭（发射事实侧），避免同时改两处。
4. 本票判据不适用于 while 区域（`condition_block` 形态的出口边）：语料内未观测到同形损失，
   判据 (b) 支路已为条件块留口，但未在实测覆盖范围内启用过 ⇒ 下一票须自带标本。

## 7. 常驻牙齿登记（如实：三臂非判据可反证臂）

追加的三臂（`.py`/`.pyc`/`OK.py` 三件套齐备，索引 40 条路径 missing_pyc=0 / missing_OK=0）：

```
r6_b117_a01_loopexit_run    循环耗尽边 + 尾随语句段 + 后继 for（range/tuple 混排）   2/2 success
r6_b117_a02_forrange_past   同一边后的 `for range(...)` 段                            2/2 success
r6_b117_a03_forelse_ctl     对照：出口边落点在区域内（真 for-else，判据必须不越权）    2/2 success
```

反证实验（`D:/Temp/rrv7/b117_deform.py` + 同判据桩 False 的第二轮）：把判据桩为恒 False（= 入轮语义）后
三臂**仍 2/2 success**，`profiler_func.show_func` 亦只在真实语料形状下失败 ⇒ 这三臂覆盖的是形状而非
判据本身：造臂需要「前一循环的 for_iter_setup 是二分支汇合块」（`blk@950 preds=[254,816]`）这一
ingredient 才会触发守卫认领广播路径；本票试过带 if/else 汇合迭代器的候选
（`D:/Temp/rrv7/cand_a01.py`），桩态与落地态**同为 1/2**（该候选另有一条未归因缺陷），故未采纳为绿臂。
⇒ 牙齿留待下一票随 `clock_worker` 站点一并补；本票验收信号是语料整文件翻面（§4 第一行）。

## 8. 终态文件完整性（落地态）

```
core/cfg/region_ast_generator.py  入轮 3685863 B / 行 58686 / CRLF 58685 / 前导 BOM 1 / sha256[:16] 9c36c741bd972593
                                  终态 3691860 B / 行 58770 / CRLF 58769 / bare LF 0 / BOM 1 / sha256[:16] 2e3051ed3614bd91
core/cfg/region_analyzer.py       2058547 B / CRLF 32336 / BOM 1 / sha256[:16] 38a1d5142d132fd7   ← 逐字节未动
core/cfg/code_generator.py        299897 B / CRLF 6022 / 无 BOM / sha256[:16] 28aba10bae133952     ← 逐字节未动
test_repros/round6/r6_probe_index.json  37 → 40 条目（三臂 + 三 OK.py 产物齐备）
site-packages/IQEngine/utils/profiler_funcOK.py、…/realtime_event_sourceOK.py 与 29 pin 产物均先删后重生成
```
