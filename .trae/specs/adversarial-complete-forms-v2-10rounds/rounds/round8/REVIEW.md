# Round 8 对抗评审报告（任务 8.1 · 续作）
## 残余破口全量清单盘点 + 合规审计 + 站桩回归复核

- 规范：`adversarial-complete-forms-v2-10rounds`（spec.md / tasks.md / checklist.md）
- 评审角色：评审工程师子代理（任务 8.1 续作；只读 core/、零 git 写操作、零 *OK.py 还原）
- 基准：round7 终态（r7v7fix_* 证据链，B117–B120 修复批 384ad07c + B121 登记后树）；本轮 core/ 与 HEAD 逐字节一致（`git status --porcelain core/` = 空）
- 判据唯一：`scripts/pyc_verify.py`（ruler = pylingual equivalence_check；全部读数 RV2 口径 = 先 regen 后 verify）
- 证据前缀：`r8v8_*`（`rounds/round8/`，前任就位 + 本续作核实补录）；本轮未新建攻击探针（`n8v8_` 前缀未动用）
- 本轮性质：**续作评审批**（盘点 + 审计 + 派发），非修复批；机制权威来源 = 旧规范 round10 REVIEW.md §4 + REVIEW2.md、本规范 round1 REVIEW2/REVIEW3、round2 REVIEW/REVIEW2、round3 REVIEW/REVIEW2、round4 REVIEW/REVIEW2、round5 REVIEW/REVIEW2、round7 REVIEW.md §5 + REVIEW2.md §4.2（逐份通读后落表，非凭编号臆断）

---

## §0 三态预备结论（II.3 口径）

| 维度 | 结论 |
|------|------|
| A. 合规审计（I.4/I.5/BOM/插桩/在途变更） | **通过**：新增违反 **0**（core/ 与 HEAD 零 diff ⇒ 黑名单/前缀/插桩/新 self 状态相对 HEAD 零新增）；存量黑名单项全部登记（§1）；**勘误 1 项**：前任记录「code_generator.py head3=efbbbf」有误，实测 head3=`222222`、BOM count=0（与 HEAD 一致的存量状态，round7 REVIEW §1 #2 已同口径登记） |
| B. 站桩回归（6 面 vs round7 终态） | **通过**：round2face 235/251、probe42 176/196、round1face 417/423、residual 418/446（a 251/277 + b 167/169）、oldface 664/692（a 217/227 + b 447/465）、quotation 152/153；**WORSE 合计 = 0**（`r8v8_vs_round7_terminal.json` 8 组逐面 WORSE=0 + `r8v8_station_regress_compare.json` 5 面 same/improved/WORSE 汇总复核一致） |
| C. 残余破口全量盘点（§3） | 43 项（`r8v8_item_replay.json`）+ 补录 2 项（**B77/r7_08 漏项、r5v5_15 B106 族外推漏项**，本轮补跑补录）= **22 个开放破口族**：**可封闭 19 / 需拆分 3 / 需证伪 0**；另 **已封闭确认 10 族**（§4，含前任 43 项中 12 个 success 读数项 + B110 面内转好 + supp 4 项） |
| D. 新破口 | **Bn = 0**（本轮无新建攻击面；补录 2 项均为已登记族成员，非新形态，见 §5） |

**一句话**：证据链完整（6 面逐面 WORSE=0、43 项全部有当前读数）、合规零新增、残余清单 22 族中 19 族判据可用 I.4 白名单表达（可封闭）、3 族一号多形态需拆分（B98/B103/B112）、0 族需证伪；**B121（while 头形成误归约）浅层即破 + 复现现成 + 判据方向已在案，列清单首位、8.2 首选封闭对象**；两项前任漏项（B77、r5v5_15）已补录，**B77 为 designated 破口（round1 REVIEW2 §5 登记）且当前仍 7/8 失败，必须并入 8.2 冲刺清单**。

---

## §1 合规审计表（亲跑实测；基准 = HEAD，core/ 零在途 ⇒ 新增口径全为 0）

| # | 审计项 | 扫描方法 | 实测 | 判定 |
|---|--------|---------|------|------|
| 1 | 在途变更（core/） | `git status --porcelain core/` | **空**（0 行） | **PASS** |
| 2 | BOM 单头 | Python 字节级读首 3 字节 + 全文 `efbbbf` 计数 | `region_analyzer.py` head3=`efbbbf` count=**1**；`region_ast_generator.py` head3=`efbbbf` count=**1**；`code_generator.py` head3=`222222` count=**0**；core/ 全树其余文件 BOM=0 | **PASS（存量登记）+ 勘误**：前任记录 code_generator.py 有 BOM 不实——其为**存量无 BOM** 状态（core/ 干净 ⇒ 与 HEAD 逐字节一致；round7 REVIEW §1 #2 同口径登记在案，IV.2 的 BOM 门禁针对**产物** OK.py，非该源码） |
| 3 | I.5 七前缀（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）相对 HEAD 新增 | diff 为空 ⇒ 新增 0；存量 grep `def _(七前缀)` | 存量 3：`region_ast_generator.py:20302 _merge_block_is_then_exclusive`、`:41913 _merge_block_is_loop_back_edge`（round2/6/7 已登记历史谓词）、`core/control_flow.py:720 _merge_redundant_blocks`（非 cfg 管线，补录） | **新增 0 PASS**（存量登记） |
| 4a | I.4-① 文件/函数名白名单 | grep 抽检 `== *'(change_his_to_forward|query_strategy_id|t_host_match_case)'` 等 | 0 命中；存量均为编译器合成名判定（`'<module>'/'<lambda>'/<listcomp>` 族，round7 §1 4a 口径） | **新增 0 PASS** |
| 4b | I.4-② start_offset 魔法阈值 | grep `start_offset [<>]=? \d{3,}` | 新增 0；存量：`region_ast_generator.py:25018 b.start_offset in (192,584)`（`R7_DEBUG_IFGEN` env 门控调试，round6/7 已登记）、`structured_analyzer.py:7937/7952/7970… start_offset == 0`（legacy 判定） | **新增 0 PASS**（存量登记） |
| 4c | I.4-③ 跨层 `X.entry in Y.blocks` 反查 | grep `\.entry in .*\.blocks` in core/cfg | 存量 **15**（region_analyzer.py 3 + region_ast_generator.py 12；较 round7 登记 12 多出的 3 处系 round7 修复批 B117/B119/B120 落地代码，已经 round7 REVIEW2 §1 H4/H7 逐 hunk 审定为区域成员关系合法判据） | **新增 0 PASS**（存量登记） |
| 4d | I.4-④ 新增 self 跨方法状态 | diff 为空 ⇒ 0 | 0 | **PASS** |
| 4e | I.4-⑤ 硬编码深度/计数上限 | grep `max_depth\s*=\s*\d+\|depth\s*>\s*\d+` | 新增 0；存量：`region_analyzer.py:2663 max_depth=15`、`:2822/:2827 max_depth=3`、`:7049 _depth>10`、`:7884 depth>16`、`region_ast_generator.py:15929 _ft3_depth>8`、`:31630 max_depth=6`（与 round7 §1 4e 登记逐位对应，行号漂移） | **新增 0 PASS**（存量登记） |
| 5 | 插桩残留（R7FIXDBG 等） | grep `R7FIXDBG` in core/ = **0**；`R7_DEBUG_IFGEN` 存量 2 处 env 门控（:25018/:25056） | 修复期临时插桩全清（round7 REVIEW2 §1 专项核查口径延续） | **PASS** |
| 6 | `*OK.py` 副作用（regen，非手改） | `git status --porcelain` | **M 态 18**：`test_repros/round2/` 8（c02/c03/m03/m04/m09/nx01/x03/x10）+ round4 `c4_03_except_starOK` + round5 `r5v5_14_except_star_deepOK` + round7 7（r7v7_b2b04/b2c03/b4a03/b4c03/x_b2b04_d2/x_b2c03_pure/x_b4a03_pure）+ round8 预置 `rv8_02_with_tryfin_constretOK`；**未跟踪 6**：`test_repros/round4/r4v4r_b100_levelsOK/b101_starOK/b102_exceptOK/b103_guardOK/b109_loopelseOK.py` 5 个 + 本轮证据目录 `rounds/round8/` 1 个。全部为站桩/item_replay regen 重跑副作用（committed 快照陈旧），**依零回滚纪律未还原，登记交主代理** | **PASS（登记）** |
| 7 | 命令时限 | 本轮全部命令（grep/单验/JSON 汇总）≤300s | 成立 | **PASS** |

**合规审计新增违反数 = 0**；勘误 1 项（前任 code_generator.py BOM 记录）不构成打回（前任记录勘误，非树中违规）。

---

## §2 站桩回归读数表（6 面，对 round7 终态基线；证据 `r8v8_*` 亲跑核实）

| 面 | round7 终态基线 | 本轮读数 | 证据 JSON | same/improved/**WORSE** | 判定 |
|----|----------------|---------|-----------|------------------------|------|
| round2face | 235/251 | **235/251** | `r8v8_regress_round2face.json` + `r8v8_station_regress_compare.json` | 44/1/**0** | 持平 ✓ |
| probe42 | 176/196 | **176/196** | `r8v8_regress_probe42.json` | 28/14/**0** | 持平 ✓ |
| round1face | 417/423 | **417/423** | `r8v8_full_round1face.json` | 24/0/**0** | 持平 ✓ |
| residual（a+b） | 418/446 | **418/446**（251/277 + 167/169） | `r8v8_full_residual_a/b.json` | 61/11/**0** | 持平 ✓ |
| oldface（a+b） | 664/692 | **664/692**（217/227 + 447/465） | `r8v8_full_oldface_a/b.json` | 55/4/**0** | 持平 ✓ |
| quotation | 152/153 | **152/153**（唯一失败 `change_his_to_forward` 基线一致） | `r8v8_quotation.json` | 持平 | ✓ |

- **WORSE 合计 = 0**（`r8v8_vs_round7_terminal.json` 8 组 face 条目 missing_files/extra_files/unit_diffs 全空 + WORSE=0，与 `r8v8_station_regress_compare.json` 双源一致）。
- improved 计数来自旧快照基线的既登记改善名单（round3–round7 各轮 REVIEW2 已登记同批名单，本轮 core/ 零改动，非新改善）。
- **证据完整性核实结论**：6 面齐全、43 项 item_replay 全部有当前读数（31 failure + 12 success）、supp 10 项全 success；缺项 2 处已补录（§3 表尾 #44/#45）。

---

## §3 残余破口全量清单盘点表（核心）

**口径**：以 `r8v8_item_replay.json` 43 项为基础逐项落表（同族合并呈现，每行保留 item 级当前读数）；判据形态评估口径——「可封闭」= 守卫条件可用 I.4 白名单判据（块末 opcode / 后继前驱集合 / 异常边 / 区域成员关系 / code object 元数据 / 指令 oparg）表达；「需证伪」= 对抗核查属语料伪差/基线固有非破口/独立形态（需给证据）；「需拆分」= 一号多形态。状态机 = wiki §8.3（未定位→已定位→已落地→已复审）。**甄别原则**：登记时未封闭但后续轮已封闭的项以最近轮 REVIEW2/本轮实测读数为准，移入 §4「已封闭确认面」，不作 8.2 对象。

### 3.1 开放族总览（22 族：可封闭 19 / 需拆分 3 / 需证伪 0）

| # | 编号 | 模式一句话 | 登记出处 | 最小复现探针路径 | 当前读数（item_replay 口径） | 状态机 | 判据形态评估 | 违反条款归属 | 封闭方向建议（白名单判据草案）/ 证伪路径 |
|---|------|-----------|---------|----------------|---------------------------|--------|-------------|-------------|--------------------------------------|
| 1 | **B121**（+B121-secondary） | **while 头形成误归约**：rotate-while 布局下入口 guard 块获得 back edge 被识别为嵌套循环 header，宿主 if 条件被提升为外层 while 条件 → `while gate: while rest:`（gate 语义由「进入前测一次」变「每迭代重测」，IfRegion 消失） | round7 REVIEW2 §4.2 | `test_repros/round7/r7v7r_b121_whilehdr.pyc`（`r7v7r_b117_f2tail.pyc::b117r_while_host_deep` 为 while 宿主变体） | r7v7r_b121_whilehdr **3/5**（b121r_min_continue + _deep Different control flow）；r7v7r_b117_f2tail **6/7**（b117r_while_host_deep） | 已定位 | **可封闭**（浅层即破 + 复现现成 + 判据方向在案） | I.1 原则 2 每块唯一归属 + 原则 3 嵌套即抽象节点（C2/C3） | r7 REVIEW2 §4.2 已给判据方向：入口 guard 块的 back edge 来源是否为该 while 自身 continue 语义边（回边目标同一性）+ 宿主 if 假边与 guard 出口共享块区分（前驱集合）——均属白名单结构事实；存量性已经基线 49e5301b 同败确证。**清单首位，8.2 首选封闭对象** |
| 2 | **B78** | 条件位融合三元（B46 族残留）：while/if **条件位**融合三元 + for 体 append 位融合三元，判定位块被 IfRegion 语句路径接管 | round1 REVIEW2 §5 / round2 REVIEW §2.3 | `rounds/round1/probes_rv2/v_b46_face.pyc` | **1/4**（v_while_cond_nest / v_if_cond_nest / n_for_body_nest 均 Different control flow；负对照同败 = 非深层专属） | 已定位 | **可封闭** | C2（判定位被语句路径接管）+ C3 | 旧 r10 §4 B46（P1）判据草案：判定位块若其值被同块后续 STORE/RETURN 消费（栈事实/块内 opcode 序）则为表达式位，禁止 IfRegion 语句路径接管；round2 已证机理宿主无关（模块根/类体/方法/handler 全域触发），判据天然宿主无关 |
| 3 | **B79** | 嵌套双层 finally×continue 发射归属（B71 封闭后残余） | round1 REVIEW2 §5 / round2 §2.3 | `v_b71_face.pyc::v_nest_fin_continue` | **3/4**（v_nest_fin_continue Different control flow） | 已定位 | **可封闭** | C3（continue 回边目标跨 finally 域，无显式认领） | B71 边类型封闭判据（round1 REVIEW3 §1：`fb ∉ pred.exception_successors` 异常边区分）外推至嵌套双层：continue 回边目标 = 循环 header 块同一性 + finally 域成员关系 |
| 4 | **B80** | finally 条件段（`if fh: closer(fh)`）× else 臂 import × handler return 归属错位 | round1 REVIEW2 §5 / round2 §2.3 | `v_b73_face.pyc::v_imp_cond_fin` | **2/3**（v_imp_cond_fin Different control flow） | 已定位 | **可封闭** | C1/C2（尾随块多前驱汇合被复制到多域） | 旧 r10 §4 B50 判据：尾随块前驱仅含 finally 域末块 → 归 finally 域；多前驱汇合块禁止复制到多域（前驱集合 + finally_copy_blocks 键集，round1 FIX_A 同族判据已落地可外推） |
| 5 | **B81** | 真 guard `case 1 if flag:` 丢弃 + 幻影 continue（真 guard 装配缺口，与 B74 幻影 guard 修复无冲突） | round1 REVIEW2 §5 / round2 §4.2 | `v_b74_face.pyc::n_true_guard` | **3/4**（n_true_guard Different control flow） | 已定位 | **可封闭** | C3（guard 块与 case header 装配边界） | pattern_parser 既有 `jump_target_offset` guard 判据（round4 §5.1 B103 草案同源）扩至真 guard：guard 尾随条件跳转目标指向下一 case header（跳转目标 oparg 事实） |
| 6 | **B82** | B75 残留：两臂 return 互换（Different bytecode）+ finally 无条件段×except 臂 return | round1 REVIEW2 §5 / round2 §2.3 | `v_b75_face.pyc` | **1/3**（v_swap_arm_returns Different bytecode + n_fin_noseg Different control flow） | 已定位 | **可封闭** | C1/C2（臂块集成员 + 序列同构） | B75 修复判据域（`_b75_consume_arm_return_copies`，round1 REVIEW2 B5 hunk 已落地）扩展：finally 无条件段子型（finally 域成员 + 无条件段判定）+ 两臂 return 剥噪序列同构比对 |
| 7 | **B83** | try 体 while 循环内 raise → 循环体镜像块泄漏进 finalbody | round1 REVIEW3 §2 | `rounds/round1/probes_rvC/rvC_v2.pyc::drain` | **1/2**（drain Different control flow） | 已定位 | **可封闭** | C1（异常边与正常边未区分，镜像块误认领） | round1 REVIEW3 §2 已锁定触发条件「循环内 raise」并给出机理：副本入口前驱全经异常边；判据 = 镜像块前驱 ⊆ `exception_successors` 来源（异常边白名单）⇒ 留 finalbody，正常前驱 ⇒ 认领（B71 同族判据） |
| 8 | **B98**（3 项） | 分组 boolop 保真残余：or 尾+and 组 / and 尾+or 组尾组边界、三元/比较/海象表达式位交叉、宿主交叠、≥3 层嵌套（B44 存量交叠） | round3 REVIEW §4.1（主体已封闭：r3v3_c 15/15、e02 `<module>`/CB98 转 MATCH，round3 REVIEW2 §5.8 放行） | `e01_g1_b98_matrix.pyc`、`e02_g1_b98_hosts.pyc`、`_scratch_b98/resid.pyc` | e01 **5/15**（10 失败）；e02 **11/18**（7 失败：m_handler/4 comp 宿主/嵌套闭包/match 臂/with 体）；resid **2/5**（r_d1/r_e3/r_g2） | 已落地（部分）+ 残余已定位 | **需拆分**（一号 ≥3 子形态：① 尾组边界（or_tail_and_group/and_tail_or_group）② 表达式位交叉（三元/比较/海象 × 分组）③ 宿主交叠（for/try/match/with/comp）④ r_d1/r_e3/r_g2 实为 **B44 ≥3 层存量**应剥离独立认领） | C2/C3 + 原则 3；B44 部分 = C2 | round3 已落地判据（链块短路跳转目标集合成员关系）的**适用位扩展**：尾组边界 = 内层组操作数块跳转目标 ∉ 后续链块 fall-through 候选集；表达式位交叉 = 消费点栈位归属。建议拆分登记 B98-R1（尾组）/B98-R2（表达式位交叉）/B98-R3（宿主交叠）+ B44 独立批次（r10 §4 B44 判据草案：`_build_boolop_expression` 双入口归纳分支链嵌套右臂） |
| 9 | **B99 残** | for 宿主 BoolOp return 蒸发残余（主体已封闭：平坦链/负对照全 MATCH） | round3 REVIEW §4.1 | `_scratch_b99/b99min.pyc::for_grouped` | **8/9**（for_grouped Different control flow） | 已落地（部分）+ 残余已定位 | **可封闭**（单一交叠形态：for 宿主 × 分组 boolop） | C1/C2（for 体消费链断链） | round3 判据草案：RETURN_VALUE 前消费链若为 BoolOp（块末跳转序 = 短路跳转 + RETURN）则整体认领发射 Return(BoolOp)；判据 = 块集成员 + 块末 opcode 序，禁按宿主分支裁剪 |
| 10 | **B96** | async 推导式误生成 + 内层 code object 丢失（`a_three`/`a_four.<genexpr>`） | round2 §4.1 / round3 §4.2 承接 | `e09b_g6_async_comps.pyc` | **11/13**（a_three Different control flow + a_four.\<genexpr\> Different control flow） | 已定位 | **可封闭**（判据明确但多轮未认领，建议独立批次） | C2 + T3 生成路径 | round2 判据草案：co_flags COMPILER_FLAG_ASYNCGEN / await 指令（code object 元数据白名单）识别 async 推导式；内层推导式 code object 必须产出对应生成器单元 |
| 11 | **B109 残** | 嵌套 loop-else 双宿主仍败（主体已封闭：c4_02 = 14/14） | round4 REVIEW §4.1 / REVIEW2 §4.1 | `r4v4r_b109_loopelse.pyc::nested_loop_else` | **8/9**（nested_loop_else Different control flow；c4_02 主体 **14/14 success**） | 已落地（部分）+ 残余已定位 | **可封闭** | C3（loop-else 守卫未外推至嵌套） | `_find_loop_else` break-only 守卫（round4 整改 3eb329d1 形态）外推至嵌套双宿主：回边 entry + else 块集合成员关系逐层封闭 |
| 12 | **B102**（3 项） | except\* 多 handler / else / finally / 嵌套 / with 宿主错构（主体 e01_root 已封闭） | round4 §4.1 / REVIEW2 §4.1 / round5 §3 | `c4_03_except_star.pyc`、`r4v4r_b102_except.pyc`、`r5v5_14_except_star_deep.pyc` | c4_03 **12/13**（e04_with）；r4v4r_b102_except **5/8**（normal_finally/star_else_finally/nested_star Different bytecode）；r5v5_14 **9/10**（es_with） | 已落地（部分）+ 残余已定位 | **可封闭**（判据族明确，一次派发覆盖 else/finally/嵌套/with 四残余位） | C2/C3 + I.1 原则 2 | round4 判据草案：`CHECK_EG_MATCH`/`PREP_RERAISE_STAR`/`is_except_star` opcode 序（3.11 标记口径）+ 异常表区间成员关系——第 2+ 个 except\* 手独立认领，else 臂仅由异常表无 handler 边判定；transition 探测走 `conditional_successors`（round4 已落地判据的边界扩展） |
| 13 | **B103**（2 项） | match mapping 覆写 / class 模式默认丢失 / or+guard 错构 / `is None` 守卫 / 嵌套守卫（守卫极性修复已证形状敏感） | round4 §4.1 / REVIEW2 §4.1 | `c4_04_match_patterns.pyc`、`r4v4r_b103_guard.pyc` | c4_04 **10/13**（e04_mapping/e05_class_kw/e06_or_guard）；r4v4r_b103_guard **5/8**（GT.m/none_guard/nested_guard） | 已落地（部分）+ 残余已定位 | **需拆分**（≥3 子形态：mapping 键集覆写 / class-keyword 默认 / or+guard 组合 / `is None` 支 / 嵌套 guard；round4 REVIEW2 已证极性修复形状敏感） | C1/C2 + I.1 原则 3 | 模式子块块末 opcode（MATCH_MAPPING/MATCH_CLASS/MATCH_KEYS/MATCH_SEQUENCE/MATCH_STAR）+ case 子块集合成员关系，每 case 模式子块唯一归属；guard 判据 = 尾随条件跳转目标指向下一 case（pattern_parser 判据扩至 mapping/class/or 分支） |
| 14 | **B104** | chained_comparison 链尾操作数损坏 / while 头宿主折叠 / with 宿主 return 链蒸发 | round4 §4.1 | `c4_09_chained_compare.pyc` | **11/14**（e04_deep 链尾被常量替换 / e08_while / CCMP.m） | 已定位 | **可封闭**（round4 优先级提醒「浅层可破属高危」） | C1/C2 + I.1 原则 4 | 末操作数块（LOAD/COMPARE/BinOp/Call 序，块末 opcode 事实）必须整体归 Compare 节点，禁常量/布尔占位；宿主无关（while 头/with 同判据） |
| 15 | **B105**（2 项） | walrus 条件/实参位值链丢失 | round4 §4.1 / round5 §3 | `c4_10_walrus.pyc`、`r5v5_09_walrus_callsite.pyc` | c4_10 **8/13**（5 失败）；r5v5_09 **6/12**（6 失败） | 已定位 | **可封闭** | C1 + T3（NamedExpr 值消费链断链；B88 同族） | STORE 前值消费链块集合成员关系——比较条件与调用实参位均按「STORE 目标 + 值链块」整体认领，禁仅发射 STORE |
| 16 | **B106**（2 项 + 补录 #45） | star_args 多星/非尾星重排或丢失 | round4 §4.1 / round5 §3 | `c4_12_star_args.pyc`、`r5v5_07_starargs_callsite.pyc` | c4_12 **7/13**（6 失败，e02_shallow 浅层即破）；r5v5_07 **4/13**（9 失败）；补录 r5v5_15_lambda_combo **26/27**（lam_star.\<lambda\> Different bytecode，B106 族外推） | 已定位 | **可封闭**（浅层即破属高危；lambda 变体同判据域） | C1 + I.1 原则 4（Call 参数序保真） | CALL 实参序列指令 oparg 序（PRECALL/CALL 前操作数块序）按指令顺序重建，多 `*`/非尾 `*` 保序，禁重排/去重；lambda star-arg 变体随同判据域认领 |
| 17 | **B107** | multi_target 链式解包/属性·下标链赋值值丢失 | round4 §4.1 | `c4_07_multi_target.pyc` | **10/14**（e04_unpack/e05_star_unpack/e06_chain_target@23:18/e09_attr_chain@47:24 Different bytecode） | 已定位 | **可封闭** | C1 + I.1 原则 4 | 链式赋值目标 STORE 序列 + 同值块集合成员关系——多目标/解包目标全部按同值块认领，禁后续目标退 None |
| 18 | **B108** | try-finally-only finally 体复制进 try 体 / finally 内 `del`→`pass` | round4 §4.1 | `c4_06_try_finally_only.pyc` | **12/14**（e01_root/e06_while Different control flow） | 已定位 | **可封闭** | C1（finally 体块唯一归属失败）+ C2 + I.1 原则 2 | try 区域 `generated_blocks` 唯一归属——finally 体块不得同时归 try 体；DELETE_* opcode 识别为 Delete 语句（round2 B84 已落地同族判据外推至 finally 域） |
| 19 | **B111**（2 项） | 局部类方法 decorator-with-args → 元组 `@((x,))` | round4 §4.1 / round5 §3 | `c4_19_decorator_args.pyc`、`r5v5_12_decorator_cross.pyc` | c4_19 **27/28**（e09_method_local.Local）；r5v5_12 **21/22**（d_deep.Local） | 已定位 | **可封闭**（单形态，两探针同签名） | C1 + I.1 原则 4（decorator_list 引用语义） | 装饰器 Call 重建块集合 + decorator 发射序——按 Call 结构重建，禁退元组字面量 |
| 20 | **B112** | async：`yield await` 丢失 / async 闭包推导式蒸发（+\<listcomp\> Missing bytecode） | round4 §4.1 | `c4_20_async_five.pyc` | **21/24**（e05_async_compound.go Different control flow + e07_async_closure.outer.inner Different control flow + .\<listcomp\> Missing bytecode） | 已定位 | **需拆分**（① yield await 语义保留 ② async 闭包推导式 = B96 域 + Missing bytecode 子形态） | C1 + T3 | ① GET_AWAITABLE/YIELD_VALUE opcode 序保 yield 语义；② 随 B96 批次认领（co_flags 元数据判据同源），Missing bytecode 单元以内层 code object 产出为封闭判据 |
| 21 | **B113 残** | 多 for 子句推导式子句丢失（直接探针 c4_18 = 30/30，最小复现 comp2 破） | round4 §4.1 最小复现（round4 REVIEW2 §5 裁定维持破口） | `test_repros/round4/_scratch_m4/comp2.pyc`（另 c4_05.e09_comp_host(+\<listcomp\>) 2 失败单元归此族） | comp2 **6/9**（e1.\<listcomp\>/e2/e2.\<listcomp\> Different bytecode）；c4_05 **12/14**（e09_comp_host + .\<listcomp\>） | 已定位（round4 REVIEW2 §5 驳回「证伪降级」） | **可封闭** | C1 + I.1 原则 2 | round4 REVIEW2 §5 已给方向：存在等价源（`for a in (x,)` 形）可逐字节复现原始字节码——推导式体内识别扁平子句 `LOAD <iter>; STORE <tgt>` 并重构为等价 `for <tgt> in (<iter>,)`（comprehension_generator.py 子句块归约） |
| 22 | **B77**（补录 #44） | match case 臂内三元 `return "x" if flag else "y"` 装配缺口（B46 族 match 臂宿主变体） | round1 REVIEW2 §5（designated）/ round2 REVIEW §2.3 | `test_repros/round7/r7_08_ternary_deep_host.pyc::t_host_match_case` | **7/8**（t_host_match_case Different control flow；本轮补录核实，读数源 = `r8v8_full_residual_a.json` residual 面 regen+verify） | 已定位 | **可封闭** | C2/C3（case 臂内判定位被语句路径接管，同 B46 机理） | 判据与 B46/B78 同族：case 臂块集成员 + 判定位块值被臂内 STORE/RETURN 消费（块内 opcode 序）⇒ 表达式位；**designated 破口且当前仍失败，必须并入 8.2 冲刺清单**（前任 43 项清单漏项） |

### 3.2 补录行

| # | 项 | 说明 |
|---|----|------|
| 44 | **B77**（上表 #22） | 前任 43 项清单漏项。r7_08 为 round1 designated 破口登记面、round2 REVIEW §2.1 起持续站桩登记（7/8），`r8v8_full_residual_a.json` 实测仍 7/8 失败（t_host_match_case）。已补入盘点表并计入开放族（可封闭）。 |
| 45 | r5v5_15_lambda_combo **26/27**（lam_star.\<lambda\> Different bytecode） | 前任 43 项清单漏项。round5 REVIEW §3 登记「同 round3 F5 / B106 族存量」；本轮亲跑单验复核（regen + pyc_verify single，命令 ≤300s）读数 26/27 与 round5 登记一致。不设新编号（同 B106 机理），并入 B106 批次封闭验证面（上表 #16）。 |

### 3.3 盘点总判

- **开放 22 族** = 可封闭 **19**（B121、B77、B78、B79、B80、B81、B82、B83、B99残、B96、B102、B104、B105、B106、B107、B108、B109残、B111、B113残）+ 需拆分 **3**（B98、B103、B112）+ 需证伪 **0**。
- **需证伪 = 0 的论证**：31 个失败项全部为 `Different control flow / Different bytecode / Missing bytecode` 实结构差异，逐项有锚点 + 机理登记；round2 登记的 3 个探针退化伪差单元（x01.if_in_try / x03.while_in_try / x04.try_in_if，`if 1:`/`while 1:` 折叠形）**不在**本轮 43 项内（历轮已剔除，探针协议自 round3 起全改非常量条件）；本轮无新证据推翻任何登记破口的「破口」定性（round4 REVIEW2 §5 对 B113 的「证伪降级」主张已裁定驳回，本轮读数 comp2 6/9 维持）。
- 排序（浅层即破/纯形态 > 深层 onset；复现现成 > 需新建）：**B121（浅层即破 + 判据方向在案）→ B77/B78（B46 判据族，B77 为 designated）→ B104/B106（浅层可破高危）→ B81/B82/B83/B79/B80（round1 面浅层单元）→ B99残/B109残/B113残/B111/B108/B107（单形态收尾）→ B102（判据族一次派发）→ B96/B112（async 域，判据明确但工程量大）→ B98/B103（先拆分再认领）**。

---

## §4 已封闭确认面（不作 8.2 对象；防回归锚点）

| 族 | 封闭轮次与权威出处 | 本轮确认读数 |
|----|-------------------|-------------|
| B114（模块根点号 import 幻影别名） | round5 REVIEW2 §6.3 放行（整改批 711dc506） | item_replay `B114-closed-confirm`：r5v5_01_module_root **3/3 success** |
| B115（if 体首 while 条件融合） | round5 REVIEW2 §6.3 放行 | item_replay `B115-closed-confirm`：r5v5_08_slice_callsite **11/11 success** |
| B116（函数内裸注解丢弃） | round5 REVIEW2 §6.3 放行 | item_replay `B116-closed-confirm`：r5v5_03_annassign **11/11 success** |
| B117（else-continue 深层漏接） | round7 REVIEW2 §0/§3a 封闭确认（384ad07c） | item_replay `B117-closed-confirm/-confirm2`：r7v7_b2b04 **3/3**、r7v7_x_b2b04_d2 **2/2 success** |
| B118（then=continue·else=break 出口边丢失） | round7 REVIEW2 封闭确认 | item_replay `B118-closed-confirm/-confirm2`：r7v7_b2c03 **3/3**、r7v7_x_b2c03_pure **2/2 success** |
| B119（空 try 体 + 非空 finally 体重复发射） | round7 REVIEW2 封闭确认 | item_replay `B119-closed-confirm/-confirm2`：r7v7_b4a03 **3/3**、r7v7_x_b4a03_pure **2/2 success** |
| B120（for-else×嵌套 if/else×循环后共享 return 误归属） | round7 REVIEW2 封闭确认 | item_replay `B120-closed-confirm`：r7v7_b4c03 **3/3 success** |
| B100（relative_import 层级丢失→产物非法） | round4 REVIEW2 §2/§4 封闭确认 | supp：c4_14 **5/5**、r4v4r_b100_levels **5/5 success** |
| B101（star_import 丢失） | round4 REVIEW2 §2/§4 封闭确认 | supp：c4_15 **7/7**、r4v4r_b101_star **6/6 success** |
| B110（多上下文 with 含 return→多余 return None） | round4 登记；当前面**无失败单元**（c4_05 现存 2 失败均归 B113 族） | item_replay `B110`：c4_05 **12/14**，失败仅 e09_comp_host(+\<listcomp\>)；建议封闭批以独立负对照正式确认后划除 |
| round4 宣告完备 6 族（elif 链/augmented_assign/keyword_args/slice/global-nonlocal/fstring_conversion） | round4 REVIEW §3.1 | supp：c4_01 **14/14**、c4_08 **13/13**、c4_11 **14/14**、c4_13 **13/13**、c4_16 **21/21**、c4_17 **12/12 全 success**（完备维持确认） |
| B109 主体 / B113 直接探针 / B102 e01_root / B98 主体 / B99 平坦链 | round4/round3 REVIEW2 复审放行 | item_replay：c4_02 **14/14**、c4_18 **30/30** success（族残余见 §3 对应行） |

---

## §5 清单外攻击与新破口

- 本轮为任务 8.1 **续作评审批**（前任因配额中断，证据已就位），职责 = 核实 + 审计 + 盘点 + 派发，未新建攻击探针；`test_repros/round8/` 无 r8v8_/n8v8_ 新探针需求（旧规范 `rv8_*` 文件在案，前缀规避规则已遵守，零覆盖）。
- 清单外补测 2 项（§3.2 补录）：r7_08（B77 designated，residual 面读数 + 本轮核实）、r5v5_15（B106 族外推，亲跑单验）——均为**已登记族成员**，非新形态。
- **新破口 Bn = 0**（无新形态证据；B122 及以后编号未动用）。

---

## §6 8.2 修复派发建议（封闭批次划分）

**并行判据**（spec：破口族不相交 ∧ 涉改文件不相交）落实如下；**B121 必列首位**。

| 位 | 涉改主文件 | 批内顺序（串行） | 理由 |
|----|-----------|-----------------|------|
| **位A** | `core/cfg/region_analyzer.py`（识别/认领域） | **B121（首选）** → B78 → B109残 → B79/B80/B83（try/finally 认领域） | B121/B78/B109残 同属循环头/条件位/loop-else 识别判据域；B79/B80/B83 同属 finally 域认领（B71 边类型封闭判据族外推） |
| **位B** | `core/cfg/region_ast_generator.py`（发射/装配域） | B108 → B99残 → B104 → B105 → B107 → B111 → B98拆分后子形态（R1/R2/R3） | 全部为发射/装配/值消费链判据（值链断裂族 B88 同域）；B98 拆分登记后按子形态逐个认领 |
| **位C** | `core/cfg/pattern_parser.py` + `exception_handler.py` + `comprehension_generator.py` + `code_generator.py` + `ast_converter.py` | B77 → B81 → B103拆分子形态 → B102 → B113 → B96 → B112拆分 → B106 | match/异常组/推导式/实参序判据域；与位A/位B 涉改文件不相交 |

- **族相交处理**（同位串行避免冲突）：B98↔B99（for 宿主交叠，均位B）、B96↔B112（async 推导式同域，均位C）、B77↔B78↔B81/B103（B46/guard 判据族，跨位A/位C——B77 归位C match 装配域，B78 归位A 条件识别域，判据同源须合并回归）。
- **跨文件族**：B104（analyzer 识别 + ast_generator 条件 Compare 重建）主锚位B、B102（analyzer 归并 + exception_handler + code_generator 发射）主锚位C——合并批统一回归 e01/e02/e03、c4_03/r4v4r_b102/r5v5_14 面。
- **门禁提醒**（对 8.2 修复工程师）：自测门禁 = 本轮全部 MISMATCH 复现转 MATCH ∧ 负对照保持 MATCH ∧ 站桩 6 面（§2 基线 235/251、176/196、417/423、418/446、664/692、152/153）不变差 ∧ IV.2 门禁自检全过；触及方法 docstring 六项模板 + C1/C2/C3（I.7）；落地声明「代码已落地」（I.6）；判据禁黑名单五项（I.4）。B121 修复后 r7v7r_b121_whilehdr 须 5/5 且 r7v7r_b117_f2tail 7/7，B117–B120 已封闭面（§4）不得回退。

---

## §7 II.7 十三条误解自查（本轮结论宣告前逐条自检）

| # | 误解 | 本轮是否触犯 | 说明 |
|---|------|------------|------|
| 1 | 循环论证分母 | 否 | 盘点分母 = 43+2 探针项（源码构成），判据 = pyc_verify 外部 ruler；未以 RegionType 枚举或实现自身当分母 |
| 2 | 有过就算 | 否 | 31 个失败项逐一列失败单元并归属族，未把 MATCH 缺口当通过；B110 主体转好如实单列已封闭确认面而非计入开放清单 |
| 3 | 语料证据口径 | 否 | 盘点基础 = 历轮定向构造探针（round1–7 攻击面），站桩语料面仅作回归旁证；补录读数亦为探针单验 |
| 4 | 无限分母 | 否 | 清单封闭（43+2 项 / 22 开放族），不随深度/组合膨胀计分 |
| 5 | 节点词汇当完备 | 否 | 「已封闭确认」以当前实测读数（regen+verify 字节等价）为准，非以 AST 节点可产出为准 |
| 6 | 浅层测试当无感证明 | 否 | 保留每族 onset 事实（B121 深度 1、B117 深度 2、B120 深度 3 已封闭如实记录）；未以浅层 MATCH 宣告任何开放族完备 |
| 7 | 门禁读数当完备性 | 否 | §2 站桩 WORSE=0 仅作回归判定；§3 独立给三态盘点，未据门禁读数宣告完备 |
| 8 | 顶层构造粗清单 | 否 | 逐项到 pyc/失败单元/登记出处/锚点域/判据形态，机制均引最近轮 REVIEW 原文（round7 REVIEW2 §4.2 B121 字节码证据、round4 REVIEW2 §5 B113 裁定等） |
| 9 | 识别率当完备性 | 否 | 可封闭/需拆分判定基于判据在 I.4 白名单上的可表达性，非识别命中率 |
| 10 | 维度互替 | 否 | 站桩（回归）/盘点（三态）/合规（I.4/I.5）三维独立呈报，互不作反驳 |
| 11 | 改工具不改方法 | 否 | 零 core/零工具改动；补录读数用唯一判据 scripts/pyc_verify.py；零 git 写操作 |
| 12 | 错误检测标准（3.11 except\* 标记） | 否 | B102 机制引述沿用 3.11 口径（CHECK_EG_MATCH/PREP_RERAISE_STAR/is_except_star），无 3.12 PRELOAD_RERAISE 混用 |
| 13 | 语料上限当能力上限 | 否 | 可封闭判定基于判据可表达性（白名单结构事实在 pyc 中全部保留，旧 r10 §4.2 论证延续），未以「语料未见」作封闭或放弃依据 |

**自查结论：未触犯 II.7 任一条。**

---

## §8 产出物与纪律声明

- 本报告：`rounds/round8/REVIEW.md`（本轮唯一新增交付）。
- 复用证据（前任就位，本轮逐份核实）：`r8v8_station.py` + 6 面读数 JSON、`r8v8_station_regress_compare.json`、`r8v8_vs_round7_terminal.json`(+.py)、`r8v8_item_replay.json`(+supp、+.py)、`r8v8_quotation.json`。
- 本轮补测：`r5v5_15_lambda_combo` regen+single（补录 #45 读数）；r7_08 读数取自 residual 面证据 JSON（regen+verify 在案）。
- 纪律：只读 core/（零修改）；零 git 操作；未还原任何 `*OK.py`（M 态 18 + 未跟踪 6 已登记 §1#6，交主代理）；rounds/round1..7/ 只读；未覆盖任何既有探针文件。
