# Round 8 修复批 位A（识别域）修复报告（任务 8.2 · 批次一）

- 修复工程师子代理（位A·识别域）
- 工作树：`F:\Downloads\pythoncdc-main`（Windows / Git Bash / python 3.11.7）
- 涉改文件边界遵守声明：**仅改 `core/cfg/region_analyzer.py`**（`git status --porcelain core/` = 1 文件 `M core/cfg/region_analyzer.py`；未触碰 region_ast_generator.py / comprehension_generator.py / code_generator.py / pattern_parser.py / exception_handler.py）
- 判据唯一：`scripts/pyc_verify.py`（ruler = pylingual equivalence_check；读数全部 RV2 口径 = 先 regen（pycdc -o）后 verify）
- 证据前缀：`r8v8fixA_*`（`rounds/round8/`，本批新建；round1..8 既有文件只读未动）
- 零 git 写操作；未还原/未手改任何 `*OK.py`（regen 副作用按纪律保留登记）

---

## §0 修复总览

| 项 | 状态 | before → after |
|----|------|----------------|
| **B121**（while 头形成误归约） | **封闭**（守卫谓词 + inline 链合并一致性双 hunk） | r7v7r_b121_whilehdr **3/5 → 5/5**；r7v7r_b117_f2tail **6/7 → 7/7** |
| **B109 残**（while-else 嵌套双宿主） | **封闭**（while 双门收敛豁免支） | r4v4r_b109_loopelse **8/9 → 9/9**（nested_loop_else 转 MATCH）；c4_02 维持 **14/14** |
| B78（条件位融合三元） | **本批未封闭**（见 §5） | v_b46_face 1/4 → 1/4 |
| B79（嵌套双层 finally×continue） | **本批未封闭**（见 §5） | v_b71_face 3/4 → 3/4 |
| B80（finally 条件段×else 臂 import） | **本批未封闭**（见 §5） | v_b73_face 2/3 → 2/3 |
| B83（try 体 while 内 raise → 镜像块泄漏 finalbody） | **本批未封闭**（见 §5） | rvC_v2 1/2 → 1/2 |

附带收益（34 小测试集）：`jq_trans_module` 63/65 → **65/65**、`trade_live_broker` 115/128 → **118/128**、`quote` 81/92 → **84/92**（合计 +8 单元，均无新增失败）。

---

## §1 B121：while 头形成误归约（封闭）

### 破口回顾
round8 REVIEW.md §3 表行 #1（机制权威 = round7 REVIEW2 §4.2）：rotate-while 布局下，`if gate: while rest: BODY; if flag: continue` 的入口 guard 块因体内 continue 的 `JUMP_BACKWARD` 落于其上而获得回边，被识别为独立循环 header；宿主 if 条件块经 Step 7(b) 扫描被提升为该伪循环 condition_block → 重建为 `while gate: while rest:`（gate 语义「进入前测一次」变「每迭代重测」，宿主 IfRegion 消失）。违反 I.1 原则 2（每块唯一归属）+ 原则 3（嵌套即抽象节点），归 I.3 修复语义 = 封闭守卫、恢复 C2/C3。

### 根因（亲跑逐块核实）
`b121r_min_continue` 布局：guard@36（`POP_JUMP_FORWARD_IF_FALSE → 90`，90 与宿主 if 假边共享）+ 体首@40 + latch@86（`POP_JUMP_BACKWARD_IF_TRUE → 40`）+ continue@84（`JUMP_BACKWARD → 36`）。自然循环集 = {header=40, 回边 86→40}（真 while）∪ {header=36, 回边 84→36}（伪 header，唯一回边源为 continue 语义边）。guard-loop 经 Step 7(b) 选中宿主 if 条件块（block 0，假边同落 90）为 condition_block → 幻影外层 while。

### 守卫设计（判据逐条 I.4 白名单）
新增谓词 `_is_while_guard_continue_only_backedge(header, body, back_edge_sources)`（判定要点三条同时满足才判伪，任一不满足放行既有路径）：
1. **回边唯一来源为 continue 语义边**：每条回边源块末条指令 ∈ {JUMP_BACKWARD, JUMP_BACKWARD_NO_INTERRUPT} 且 argval 目标块 == header（回边目标同一性）。真嵌套外层 while 的闩锁回边源为 POP_JUMP_BACKWARD_IF_*（条件反向跳转），据此排除（round7 REVIEW2 §4.2 判据方向①「入口 guard 块 back edge 来源 = 自身 continue 语义边」）。依据：块末 opcode + 后继/前驱集合 + 回边目标同一性。
2. **header 为 rotate-while 入口 guard**：(a) header 末条 ∈ FORWARD_CONDITIONAL_JUMP_OPS、跳转目标 E ∉ body（循环后合并/出口块）；(b) body 内存在另一 rotate-while 的条件闩锁回边（loop_analyzer.back_edges 中源/目标均 ∈ body、目标 ≠ header、源块末条 ∈ BACKWARD_CONDITIONAL_JUMP_OPS）——证明 header 实为内层 while 入口条件块。依据：块末 opcode、argval 目标块同一性、区域成员关系（body 集合）。
3. **宿主 if 假边共享 guard 出口**：存在 header 前驱 P（P ∉ body、P ≠ header、P.start_offset < header.start_offset），P 末条 ∈ FORWARD_CONDITIONAL_JUMP_OPS 且跳转目标 == E（round7 REVIEW2 §4.2 判据方向②「宿主 if 假边与 guard 出口共享块区分——前驱集合」）。依据：前驱集合、前驱末条条件跳转目标、块偏移次序。

命中即 `continue` 跳过该伪 header（不创建 LoopRegion、不登记 block_to_region）：guard 块由内层 while 的 condition_block 扫描认领（Step 7(b) 既有路径），宿主 if 条件块由 _identify_conditional_regions 归约为 IfRegion——每块唯一归属恢复（原则 2）。

**B121-secondary（浅层修复暴露的伴生缺口，同批封闭）**：浅层转 MATCH 后，深层变体（`b121r_min_continue_deep`，双宿主 if）暴露第二层缺口——内层 while 的 continue 体块（`if flag: continue`）被发射为 `pass`。根因：`if gate2: if gate: …` 双宿主 if 的 inline and 链合并 IfRegion（entry=链首、condition_block=链末、blocks 重收集链块与臂块）创建后，识别序更早的内层 IfRegion（entry=链中后继成员块，children 挂有包裹的 LoopRegion）仍存留于区域列表；生成层按「entry 落于其它区域 blocks」包含过滤剔除该失活区域后 parent 链断裂，子循环体块（含 continue 块）被孤儿逻辑释放，continue 块（纯 JUMP_BACKWARD ∈ 清理 opcode 集）被顶层清理预标记吞没。修复（analyze() 内，`filtered_conditional_regions` 定稿处）：对每个携带 inline_boolop_chains 的合并 IfRegion R，遍历链中后继成员块，找 entry 命中且 parent 为空、无 else 臂、非 IF_ELIF_CHAIN、blocks ⊆ R.blocks 的内层 IfRegion S——溶解 S（列表移除、S 独占 block_to_region 移交 R、S.children 重挂 R）。判据 = 区域成员关系 + 前驱/后继集合（I.4 白名单）；恢复原则 3/4 的层级可达性。

### 触及方法与 docstring 增补
- `_identify_loop_regions`：docstring Step 4 增补一行（抑制项列举）；识别体内新增守卫调用注释块（含 C 条款说明）。
- 新增谓词 `_is_while_guard_continue_only_backedge`：完整「六项 + C1/C2/C3」docstring（区域类型/算法依据/判定要点/归约顺序/唯一归属/嵌套处理/入口引用语义/反编译流程/C 条款）。

### 自测读数
- r7v7r_b121_whilehdr：**3/5 → 5/5**（b121r_min_continue、b121r_min_continue_deep 均 MATCH；负对照 b121r_minimal / b121r_minimal_shallow 维持 MATCH）
- r7v7r_b117_f2tail：**6/7 → 7/7**（b117r_while_host_deep 转 MATCH）
- 邻域负对照（亲跑）：顶层 while+continue、真嵌套 `while gate: while rest:（continue）`、无 continue 双宿主 if+while、`if a: if b: x else: y`、纯 `and` 源码形 6 单元全 MATCH（t_variants 探针，out_r42h/probeA/）

---

## §2 B109 残：while-else 嵌套双宿主（封闭）

### 破口回顾
round8 REVIEW.md §3 表行 #11（机制 = round4 REVIEW §4.1 / REVIEW2 §4.1）：`nested_loop_else`（`for x: … while x: … else: return None …`，内层 while 位于外层 for 体内）内层 while 的 orelse 丢失（else 体降级为顺序语句）。违反 C3（loop-else 守卫未外推至嵌套）。封闭方向（在案）：`_find_loop_else` 守卫外推至嵌套双宿主，「回边 entry + else 块集合成员关系逐层封闭」。

### 根因（亲跑逐块核实）
`_cleanup_try_else_in_loop_body` 的伪 else 清理对嵌套双宿主失守：内层 while 的 else 体（return None 块）的唯一正常前驱 = 内层 while 的条件块（假出口），但「全部正常前驱归属本循环」豁免判据的 owned 集合只含 body_blocks/header/else_blocks——条件块缺席（本形态下 for 体首与 while 守卫融合，条件块是父循环 body_blocks 成员）→ 真 else 被误判 spurious 剔除 → orelse 丢失。

### 守卫设计（判据逐条 I.4 白名单）
在 `_cleanup_try_else_in_loop_body` 的豁免收集处新增**「while 双门收敛豁免」支**（仅 `lr.region_type == RegionType.WHILE_LOOP` 且 `lr.has_break`）：循环的每个条件求值块（条件块，无则 header；与回边块 back_edge_block）的条件假出口——越体（∉ body_blocks）、非 header、非 break 落点（∉ break_blocks）的 conditional_successors——收敛到唯一块且该块 ∈ else_blocks 时，将该 else 块加入豁免集（真 loop-else 结构签名，与区域创建期 `_b109_real_loop_else` 判据同源同层，即 round4 整改 3eb329d1 形态外推至清理层/嵌套双宿主）。
- c4_02::nested_loop_else：cond@8 假出口 = 42，回边@38 假出口 = 42 → 收敛 → 豁免 → orelse 保留 ✓
- 无 else 语义的顺序收尾（初判/回边复判各落独立 return None 块，如 risk_calculation `__init__._save_testds_to_csv` 第二个 while：262→354 与 336→350 分叉）不收敛 → 维持旧剔除 ✓（该文件曾在本批中间态出现裸 `else:` IndentationError，即以此收敛判据收紧后消除——回退处理条款执行记录）
- for 循环不适用该支（FOR_ITER 耗尽边语义不同，c4_02::e04_deep for-else 由原「前驱归属」豁免支继续覆盖）。

依据：conditional_successors 集合、body_blocks/header_block/condition_block/back_edge_block/break_blocks/else_blocks 成员关系、region_type（均 I.4 白名单）。

### 触及方法与 docstring 增补
- `_cleanup_try_else_in_loop_body`：原无 docstring，本批补齐完整「六项 + C1/C2/C3」docstring，与代码一致（收敛豁免支在「唯一归属判定」项声明）。

### 自测读数
- r4v4r_b109_loopelse：**8/9 → 9/9**（nested_loop_else 转 MATCH；normal_while / for_else_ctrl / while_else_not_returnnone 等负对照维持 MATCH）
- c4_02_loop_else：**14/14 维持**（B109 主面无回退）
- risk_calculation `__init__`：IndentationError（中间态）→ 编译通过（终态）

---

## §3 自测门禁读数（终态代码，全部亲跑）

1. **本批复现转 MATCH**：见 §0 表（B121 3/5→5/5 + 6/7→7/7；B109 8/9→9/9；B78/B79/B80/B83 持平，未封闭项说明见 §5）。
2. **攻击面零新失败**（`r8v8fixA_probe_detail.json`，驱动 = `r8v8fixA_attack.py`，复用 r7v7_attack 协议，探针面 = test_repros/round7/ 全部 r7v7_*/n7v7_*/r7v7r_*）：**attack 122/122、neg 18/18、r7v7r 变体 35/35**（r7v7r_b121_whilehdr 转全 MATCH，34/35 → 35/35）；对 round7 终态 `r7v7fix_probe_detail.json` 逐文件逐单元比对：WORSE=0、失败集合差 = 空、**NEWFAIL=0**。
3. **站桩 6 面不变差**（驱动 = `r8v8fixA_station.py`，对照 = round7 终态基线）：

   | 面 | round7 终态基线 | 本批复数 | 判定 |
   |----|----------------|---------|------|
   | round2face | 235/251 | **235/251** | 持平 ✓ |
   | probe42 | 176/196 | **176/196** | 持平 ✓ |
   | round1face | 417/423 | **417/423** | 持平 ✓ |
   | residual（a+b） | 418/446 | **418/446**（251/277 + 167/169） | 持平 ✓ |
   | oldface（a+b） | 664/692 | **664/692**（217/227 + 447/465） | 持平 ✓ |
   | quotation | 152/153 | **152/153**（唯一失败 change_his_to_forward 基线一致） | 持平 ✓ |

   `r8v8fixA_compare_regress.py` 产 `r8v8fixA_station_regress_compare.json`：5 面 WORSE=0（improved 计数均为对 round1/2/3 旧快照基线的既登记改善名单，round8 REVIEW §2 同口径）；另对 residual/oldface 与 round7 终态 JSON（r8v8_full_*）做逐单元 diff：**零位移**。
4. **34 小测试集**（驱动 = `r8v8fixA_34set.py` 4 分片，基线 = harden-completed-forms-10rounds/baseline/failing_index.json）：**1505/1568** = round7 终态基线，**NEWFAIL=0**、compile_error=0；FIXED 8 单元（§0 附带收益）。
5. **IV.2 门禁自检**：IMPORT_OK；py_compile 通过；BOM head3=`efbbbf` count=**1**（单头保持）；无遗留插桩（本批零 env 门控/零 print 插桩）；G0——触及方法 docstring 六项 + C 条款与代码一致（`_is_while_guard_continue_only_backedge` 新建全文、`_cleanup_try_else_in_loop_body` 补齐全文、`_identify_loop_regions` Step 4 行内增补）；G3——七前缀 def 零新增；G4——硬编码上限/魔法阈值零新增（新 hunk 内无数字阈值、无计数上限、无名字/偏移白名单）。
6. **回退处理记录**：B109 首版守卫（owned 集合纳入 condition_block）引发 34 集 1 文件 compile_error（裸 `else:`）；按「收紧守卫判据（仍白名单）直到零回退且复现仍 MATCH」条款，收紧为 while 双门收敛豁免后零回退且 r4v4r_b109_loopelse 维持 9/9。中间态探针（r8v8fixA_attack/station/34set 首轮读数）已全部被终态重跑覆盖，以上 §3 全部为终态代码读数。

---

## §4 代码已落地声明

**代码已落地**（I.6）：以下 hunk 实证在树（`core/cfg/region_analyzer.py`，当前行号）：

| # | 锚点 | 内容 |
|---|------|------|
| 1 | `core/cfg/region_analyzer.py:1834-1891` | [B121-secondary] inline and/or 链合并 IfRegion 与被吸收内层 IfRegion 的一致性溶解 + children 重挂接（analyze() 内，filtered_conditional_regions 定稿处） |
| 2 | `core/cfg/region_analyzer.py:4246` | `_identify_loop_regions` docstring Step 4 增补（新守卫列举） |
| 3 | `core/cfg/region_analyzer.py:4356-4375` | [B121] `_identify_loop_regions` 识别体内守卫调用（命中即 continue 跳过伪 header） |
| 4 | `core/cfg/region_analyzer.py:7631-7760` | 新增谓词 `_is_while_guard_continue_only_backedge`（六项 + C 条款 docstring :7633 起；实现判据 1/2a/2b/3 :7697/7712/7723/7736 起） |
| 5 | `core/cfg/region_analyzer.py:5196-5245` | `_cleanup_try_else_in_loop_body` 六项 + C 条款 docstring 补齐（[B109 残余修复] 于「唯一归属判定」项声明） |
| 6 | `core/cfg/region_analyzer.py:5391-5445` | [B109 残余修复] while 双门收敛豁免支（`lr.region_type == RegionType.WHILE_LOOP` 门控 :5418；`_b109_conv_target in lr.else_blocks` :5443） |

diff 规模：+274/−4 行（`git diff --stat core/cfg/region_analyzer.py`）；除本文件外 core/ 零改动。

### 证据 JSON 清单（rounds/round8/）
- `r8v8fixA_probe_index.json` / `r8v8fixA_probe_results.json` / `r8v8fixA_probe_detail.json`（攻击面 122+18+35 终态读数）
- `r8v8fixA_regress_round2face.json` / `r8v8fixA_regress_probe42.json` / `r8v8fixA_full_round1face.json` / `r8v8fixA_full_residual_a.json` / `r8v8fixA_full_residual_b.json` / `r8v8fixA_full_oldface_a.json` / `r8v8fixA_full_oldface_b.json` / `r8v8fixA_quotation.json`（站桩 6 面终态读数）
- `r8v8fixA_station_regress_compare.json`（5 面对照汇总，WORSE=0）
- `r8v8fixA_34set_shard{0..3}.json` + `r8v8fixA_34set_shard{k}_index.json`（34 集终态读数，1505/1568）
- 驱动脚本：`r8v8fixA_attack.py`（复用 r7v7_attack 协议 + 增加 r7v7r_* 面）、`r8v8fixA_station.py`（r8v8_station 独立副本，输出前缀 r8v8fixA_）、`r8v8fixA_compare_regress.py`（同前）、`r8v8fixA_34set.py`（分片驱动）

---

## §5 未封闭项（本批退回，不硬上）

| 项 | 当前读数 | 未封闭原因（域归属 + 卡点） |
|----|---------|---------------------------|
| **B78**（条件位融合三元：while/if 条件位 + for 体 append 位） | v_b46_face 1/4（v_while_cond_nest / v_if_cond_nest / n_for_body_nest 均 Different control flow） | 亲跑核实现行输出：条件位/实参位嵌套三元整体被 IfRegion 语句路径接管（`while (a if f1 else b) if (c if f2 else d) else 0:` → 伪 if 嵌套链）。卡点：识别层需新增「融合三元链」识别（真值块以条件跳转终结——与 enclosing if 的分支判定融合，`_is_ternary_block` 的 JUMP_FORWARD 终结校验不匹配），且表达式重建需 IfRegion 条件位内联三元支持——涉及 `_identify_ternary_regions` 判据族重设计 + 生成层 IfRegion 条件重建协作，判据面与位B（IfRegion 条件表达式重建）相交，超出本批「单批内零回退收敛」可安全落地的范围。判据方向（round8 REVIEW §3 行 2 的「判定位块值消费」草案）已核实与机理一致，移交后续批次（建议位A/位B 合并批）。 |
| **B79**（嵌套双层 finally×continue） | v_b71_face 3/4（v_nest_fin_continue） | 亲跑核实现行输出：内层 finally 正常路径副本与 continue 路径副本被误装配进 try 体（append(1) 双发、嵌套层级错位），continue 的 JUMP_BACKWARD→for header 边丢失。卡点：副本归属 = TryExceptRegion 的 try/finally 块集合划分与生成层 `_generate_try` 正常/异常路径副本装配协作——「continue 回边目标 = 循环 header 同一性 + finally 域成员关系」判据需在生成层副本选择处消费，单改识别层无法闭合（误装配发生在发射层装配决策）。 |
| **B80**（finally 条件段 × else 臂 import × handler return 归属错位） | v_b73_face 2/3（v_imp_cond_fin） | 亲跑核实现行输出：finally 条件段（`if fh: closer(fh)`）被复制进 except 臂且 `return fb(str(e))` 退化为表达式——「尾随块多前驱汇合禁止复制到多域」判据的消费点在生成层 handler/finalbody 装配（多域复制发生在 `_generate_try` 的 handler 臂装配），识别层 try/handler/finally 块集合本身划分正确，单改识别层不闭合。 |
| **B83**（try 体 while 循环内 raise → 循环体镜像块泄漏进 finalbody） | rvC_v2 1/2（drain） | 亲跑核实（区域树 dump）：TryExceptRegion 块划分正确（try_blocks=[8,12,64,94]、finally_blocks=[210,282] 异常路径副本、正常路径副本 140 均已唯一归属），泄漏发生在生成层 finalbody 装配把循环体块（12/64/94/136）二次发射、而正常路径 finally 副本（sink.append）未发射——review 在案判据「镜像块前驱 ⊆ exception_successors ⇒ 留 finalbody，正常前驱 ⇒ 认领」的「认领」半支已由现有 block_to_region 满足，剩余修复点 = 生成层 finalbody 装配的镜像剔除（region_ast_generator.py，位B 领地），本批禁越界。 |

以上 4 项均为「判据在 I.4 白名单可表达、机制已在案并经本轮亲跑核实」，但封闭动作的主消费点位于发射/装配层（位B/位C 文件）或需识别-发射两侧协同重构，按「禁止越界改发射域文件」与「不能两全即退回」纪律退回；探针读数与本批前后一致（无回归）。

---

## §6 纪律声明

- 涉改文件 = `core/cfg/region_analyzer.py` 唯一；位B/位C 文件零改动（§1-§2 两项修复的全部守卫判据均在区域归约算法内以 I.4 白名单事实表达）。
- 零 git 写操作；rounds/round1..8/ 既有文件只读；未还原/未手改任何 `*OK.py`（本批 regen 重跑产生的 OK.py 更新均为 regen 副作用，按纪律保留登记）。
- 全部命令 ≤300s（长面分片：34 集 4 分片、residual/oldface a|b 分片）。
- 本报告读数全部亲跑实测（regen + pyc_verify single/batch），未沿用任何未复跑读数。
