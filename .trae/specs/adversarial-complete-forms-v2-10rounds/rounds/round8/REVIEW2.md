# Round 8 复核报告 REVIEW2（任务 8.3 · 独立评审工程师）

- 规范：`adversarial-complete-forms-v2-10rounds`（spec.md 理论基准 I 全部 + II.7）
- 评审角色：独立评审工程师（与修复工程师不同批；对修复结论不作协商通容）
- 被审对象：HEAD `865b901e` 上的 Round 8 全部修复批次（FIX_A/FIX_B/FIX_C；累计 diff 基线 = `git diff 5f784272..HEAD -- core/`，7 文件 +3350/−180）
- 判据唯一：`scripts/pyc_verify.py`（RV2 口径 = 先 regen 后 verify）
- 证据前缀：`r8v8rev_`（本评审新建：探针 `test_repros/round8/` 15 .py + 15 .pyc + regen OK.py；JSON/驱动/核验脚本 `rounds/round8/`）；前任会话证据 `r8v8fixB_repro_rev2B/rev2C.json` 经逐条通读后引用
- 纪律：只审查不修复；零 git commit/push；regen 副作用（M 态 `*OK.py` 30 件 + 前任 shard0.json 时戳）已全部 `git checkout --` 还原（终态 `git status` M 态 = 0）

---

## §0 终判

**打回**（打回项 = 4 族 5 形态域内缺口；A 合规零打回、B 读数逐位一致、C 域内 5 新 FAIL ⇒ 终判条件「C 域内零新 FAIL」不满足）

| # | 打回项 | 探针（失败单元） | 违反条款 | 机制一句话 |
|---|--------|----------------|---------|-----------|
| 1 | **B104-R2a**（while 头链+and 混合形折叠） | `r8v8rev_b104_chain4_battery.py::v2`（`while 0 < x < 10 and flag:`） | C2/C3 + I.3 推论 + I.2 | 循环头被拆为 `if 0<x<10:` 前置守卫 + `while flag:`，链段被 if-guard 语句路径接管、重检泄漏为体尾 `if 0<x<10: pass/break`——正是 e08_while 注册症状「while 头宿主折叠」在 H5 设计案例同形（链+and 混合条件）上的复发；FIX_B §1 H5 的设计案例即 `while 0 < x < n < 100 and n < 100`，属声称覆盖域 |
| 2 | **B104-R2b**（while 头 4 元链重检泄漏） | 同上 `::v4`（`while 0 < x < 10 < x*2 < 100:`） | C1/C2 + I.4-⑤ 注册症状「禁常量/布尔占位」 | 循环头正确、但回边重检协议段泄漏为体首幻影 `if 0 < x and 10 < True and x*2 < True: pass / elif 10 < True and x*2 < True: pass`——`10 < True` 布尔占位与 e04_deep 注册症状逐字同签；e08（while 宿主 3 元）与 CCMP.m（4 元链）均声称已封闭，本形态 = 两声称域的交集成员失败，[B104-H4] 重检/清栈抑制（region_ast_generator.py:7930/:7980）对 4 元链布局未收敛 |
| 3 | **B105-R2**（嵌套海象实参位值链蒸发） | `r8v8rev_b105_walrus_battery.py::v2`（`return g((a := h((b := h()))), a + b)`） | C1 + I.3 推论（教科书「深层才错」） | 海象值表达式内再嵌海象（深度 2）：输出只剩 `a = h((b := h()))`，外层 g 调用 + 第二实参 + return 整体蒸发。单层实参位（e06_call_arg）、兄弟双海象（H3 根因案）均过 ⇒ [B105-H2/H3] 栈净效应判据（region_ast_generator.py:56550/:56541）对嵌套值链不收敛——判据族声称「实参位按 STORE 目标+值链块整体认领」（REVIEW §3 #15），形态属域内 |
| 4 | **B107-R2**（≥3 目标复杂链 + 前置语句 → 目标蒸发） | `r8v8rev_b107_mtarget3_battery.py::v1`、`r8v8rev_b107_iso_battery.py::t2/t3`、`r8v8rev_b107_iso2_battery.py::u1/u2` | C1 + I.3 推论 | 同块内前置任意普通语句（`s = v + w` / `q = Q()`）后接 ≥3 目标复杂链：目标 2+ 整体蒸发（`o.a = p[k] = q.r = v` → `o.a = v`；4 目标 u1 仅剩中段 `p[k] = s`）。链单独成块（任意 N）与前置语句×2 目标均过 ⇒ [B107-H1/H2]（:56173/:56312/:58694）仅覆盖链首起窗场景——REVIEW §3 #17 注册症状「后续目标退 None/丢失」，普通语句序列是最不特殊的宿主形态，属域内 |
| 5 | **B103-R2**（or 模式 + 裸名守卫 → 守卫静默丢失） | `r8v8rev_bmatch_guards_battery.py::v3`、`r8v8rev_bmatch_or3iso.py::w2/w3`（`case 1 \| 2 \| 3 if g:`） | C1/C3 + I.2（用算法替代模式匹配） | or 模式守卫被静默丢弃（`case 1|2|3 if g:` → `case 1|2|3:`，输出语义改变——比控制流失配更严重的静默语义腐蚀）。隔离实验（or3iso w1–w4）：比较形守卫（`if x > 1`）保真、单字面量+裸名守卫保真、or 模式+裸名守卫丢失 ⇒ guard 提取对守卫**表达式形态**敏感——守卫 fail 边（POP_JUMP_FORWARD_IF_FALSE → 下一 case）对两种形态结构同一，判据却形态有别 = 模式匹配非协议判据；e06_or_guard 封闭声明（or+guard，证据仅用比较形）属域内缺口，锚 = pattern_parser.py:351/:1224（F2 search_start / or 臂链材料收集与守卫提取的接合处） |

**打回计数说明**：5 形态归并 4 族（B104 ×2）；全部为「守卫声称覆盖域内新 FAIL」，非域外新形态。域外新形态与登记项见 §4。

**其余面结论**：
- **A 逐 hunk 合规：零打回**（§1；`_steps < 8` 声明验证为真、按存量同型第 3 处登记；两处报告措辞勘误登记，均不构成条款违反）
- **B 读数独立复跑：逐位一致**（§2；31 探针 + 站桩 3 面 + 34 集分片 0 + 负对照，零虚报）
- **C 变体攻击：10 面 PASS、5 形态域内 FAIL**（§3）；B102 电池复用 = 8/10 与登记残余逐位一致（ideg/pin 为 FIX_C §3.5 注册移交项，非新 FAIL）
- **移交项复核：8 项全部成立**（§5）

---

## §1 逐 hunk 合规表（A 审查；I.1–I.7 零容忍逐 hunk）

范围 = `git diff 5f784272..HEAD -- core/`（ast_converter +51、ast_generator_v2 +67、code_generator +2、comprehension_generator +263、pattern_parser +508、region_analyzer +1362、region_ast_generator +1277）。

### 1.1 G3 新增方法全列核对（`git diff ... | grep "^\+.*def "`，24 个 def 全列）

新增/改签名 def：`_b113_extract_flat_clauses`、`_find_comp_append_op`(签名扩展)、`_pure_jf_argval`、`_collect_or_arm_chain_instrs`、`_head_pop_top_then_guard_load`、`_b74_guard_arm_targets_case_body`(签名扩展)、`_is_while_guard_continue_only_backedge`、`_b102_chain_reachable_blocks`、`_b102_degenerate_chain_pairs_finally`、`_b102_cleanup_target_of`(嵌套)、`_find_star_else_blocks`、`_mr_resolve_or_arm_jump`、`_pure_jump_target`(嵌套)、`_mr_head_has_wildcard_discard`、`_detect_boolop_short_circuit_chain`(签名扩展)、`_try_build_match_case_ternary_stmt`、`_b77_pure_value_block`(嵌套)、`_try_build_orprefix_and_boolop_from_ternary`、`_build_chained_complex_target_assign`。
**七违禁前缀（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）命中 = 0** ⇒ G3 PASS。

### 1.2 I.4 黑名单五项逐项（新增行 grep 实测）

| 项 | 方法 | 实测 | 判定 |
|----|------|------|------|
| ① 文件/函数名白名单 | 新增行 grep `name == '`/`co_name ==` | 命中全为 opcode 比较（`opname == 'PUSH_NULL'` 族 = 块内指令序白名单）与编译器合成名（`func_name == '<setcomp>'` 族 = co_name 元数据→推导式产出 opcode，FIX_C §7.2 声明在案、round7 §1 4a 既有口径）；**零目标文件/函数名白名单** | PASS |
| ② start_offset 魔法阈值 | 新增行 grep `start_offset` 数值比较/`offset == \d{2,}` | 零命中（[B121] 判据 3 的 `P.start_offset < header.start_offset` 为**块偏移次序关系**，非阈值） | PASS |
| ③ 跨层 `X.entry in Y.blocks` 反查 | 新增行 grep `.entry in` | 零新增 | PASS |
| ④ 新增 self 跨方法状态 | 新增行 grep `self.X =` | 零新增（[B75]/[B82] 瞬态键挂 region 对象单次 generate 生命周期，round1 REVIEW2 B5-B6 既有口径维持） | PASS |
| ⑤ 硬编码深度/计数上限 | 新增行 grep | `_steps < 8` ×1 新增（[B82]，见 1.3 专项）；`_b105_depth > 0`（>0 方向性判断非上限） | **登记**（声明属实，非打回） |

### 1.3 [B82] `_steps < 8` 声明真伪专项验证（FIX_B §10/§12 声称「[B75] 落地存量同型镜像，同常数同语义」）

- `git grep -n "_steps < 8" 5f784272 -- core/`：region_ast_generator.py **:27891**（`while _walk ... _steps < 8`，round1 批 B 33d6e87e [B75] 落地）与 **:34316**（`_cur` 形，round6 fbfc2e7b）；region_analyzer.py:28872 `_r3k_steps < 8`。HEAD 现存 3 处（:28019/:28189/:34759）——[B82] hunk 在**同一方法** `_b75_consume_arm_return_copies` 内新增第 3 处。
- **声明验证 = 真**：同常数（8）、同语义（透明块链回溯环防护）、同宿主方法（[B75] 判据族本体）；round1 REVIEW2 B5-B6 hunk 审定曾对 [B75] 整体判 I.4 PASS。
- 失败模式核验（region_ast_generator.py:28189-28208）：步数耗尽 ⇒ `_b82_handler_entry is None` ⇒ `_b82_ok = False` ⇒ **不认领、回退原路径**（保守回退，不产错误发射，非「以少发射换全绿」——被抑制的是修复新增认领而非既有发射）。判据主终止 = 结构条件（CHECK_EXC_MATCH 命中/成员关系/透明性/前驱存在），步数界为防御环护。
- **处置：登记不打回**。存量同型镜像属实、零容忍黑名单的既有处置口径（存量登记 + 同型扩展）维持；残留风险（>8 透明块的链回溯将保守放弃认领 = 召回缺口非正确性缺口）记入 §4 供后续批次改 visited-set。

### 1.4 I.6 落地锚点核验（FIX_A §4 + FIX_B §13 + FIX_C §9 全表，75 锚）

驱动 `r8v8rev_anchor_check.py`（rounds/round8/）：**75/75 标记全部在树，0 NOT-FOUND**；58 锚窗口内命中，17 锚行号漂移（+21～+722，全部为后续批次同文件上方增量所致的**正向单调漂移**，标记内容逐一在近邻行实测命中；FIX_B §13 的 "≈" 编号为批次中期近似，FIX_B §5/§10 详细锚与 FIX_C §9 终态锚均逐条对上）。代表性复核：[B99-C3] :30700→:31422、[B98-R1] :42537→:42780、[B77] :36395→:36622、[B82] :28084 命中、[B83] :29748→:29909、B81 F1-F4/F2-F3、B103 G1-G11+t2、B102 E1-E7、B113 C1-C4、B96 D1-D3、B106 F1-F4 全命中。**I.6 PASS（0 锚虚报）**。

### 1.5 I.7 注释合规（每族首个锚点方法 docstring 六项 + C 条款）

驱动 `r8v8rev_docstring_check.py`（+`_check2`）实测：

| 族 | 首锚方法 | 六项 | C 条款 | 判定 |
|----|---------|------|--------|------|
| B121 | `_is_while_guard_continue_only_backedge`（:7731） | 6/6 | C1/C2/C3 | PASS（judged 逐条与代码一致，判据 1/2a 可见对应） |
| B109 | `_cleanup_try_else_in_loop_body`（:5294） | 6/6 | C1/C2/C3 | PASS |
| B98-R1 | `_try_build_orprefix_and_boolop_from_ternary`（:42780） | 三要素式（识别条件/归约方式/AST 映射）+【反编译逻辑】框架 + C1/C2/C3 | 齐 | PASS（内容与代码一致；FIX_B §13「六项要素」措辞过宽，§5 详述准确——**措辞勘误登记**） |
| B77 | `_try_build_match_case_ternary_stmt`（:36622） | 6/6 | C1/C2/C3 | PASS |
| B107 | `_build_chained_complex_target_assign`（:58694） | 6/6 | C1/C2/C3 | PASS |
| B81 | `_extract_case_guard_from_blocks`（pattern_parser） | 6/6 | C1/C2/C3 | PASS |
| B103 G2 | `_collect_or_arm_chain_instrs`（:1224） | 6/6 | C1/C2/C3 | PASS |
| B103 G2b | `_pure_jf_argval`（:1209） | 紧凑判据+C1/C2/C3（8 行码量的微谓词） | 齐 | PASS（docstring 与代码一致；FIX_C §2.4「六项模板齐全」对双方法并书过宽——**措辞勘误登记**；I.7 强制类 = `_identify_*`/`_generate_*`，本方法不在强制类） |
| B102 E2 | `_b102_degenerate_chain_pairs_finally` / `_b102_chain_reachable_blocks` / `_find_star_else_blocks` | 6/6 ×3 | C1/C2/C3 | PASS |
| B113 C1 | `_b113_extract_flat_clauses`（:1892） | 6/6 | C1/C2/C3 | PASS |
| 触及的 `_identify_*`/`_generate_*` 强制类 11 方法（loop/cond/boolop/ccmp/match/try_ident + gen_ternary/match/with/trybody/handler） | 存量六项保持 | 6/6 ×11 | 齐 | PASS（FIX_B §0.1 B108/B111 docstring 补正落树核实） |
| `_loop_generate_while`（B104-H4 宿主） | 无 docstring（**存量状态**，5f784272 即无；方法名不匹配 I.7 强制类 `_identify_*_regions`/`_generate_*` 字面模式；hunk 带 [B104] 判据注释块 :7930/:7980） | — | 注释块内声明 | PASS（存量 + 既有 hunk 注释口径；登记备查） |

**插桩/BOM**：`R8CDBG|R8FIXBDBG|R8CDBGE|_os_r8` 全 core/ **零命中** ✓；region_analyzer.py 与 region_ast_generator.py 首 3 字节 `efbbbf` × 计数 1（**单头**，FIX_C §8.3 所称前段双 BOM 已恢复）✓；新增行 print( = 0 ✓。

**A 部分小结：I.4/I.5/I.6/I.7 + 插桩/BOM 全项零打回；3 项登记（1.3 `_steps < 8`、两处报告措辞勘误）。**

---

## §2 读数独立复跑表（B 审查；防虚报）

| 面 | 修复报告声称终态 | 本评审实测 | 证据 | 判定 |
|----|----------------|-----------|------|------|
| 攻击面 31 探针（位B 域 16 项） | B77 8/8、B78 1/4、B79 3/4、B80 2/3、B82 2/3、B83 2/2、B98_matrix 7/15、B98_hosts 13/18、B98_resid 2/5、B99 9/9、B104 14/14、B105 13/13+12/12、B107 14/14、B108 14/14、B111 28/28+22/22 | **逐位一致**（rev2B.json 逐条通读核对：含 B98/B78-B82 各失败单元名单与 FIX 报告移交清单一致） | `r8v8fixB_repro_rev2B.json`（前任会话，引用） | ✓ |
| 攻击面 31 探针（位C 域 14 项） | B81 4/4、B103 13/13+8/8、B102 13/13+8/8+10/10、B113 9/9+14/14、B96 13/13、B106 13/13+13/13+27/27、B112 21/24（e05/e07/e07.\<listcomp\> 三移交单元） | **逐位一致**（rev2C.json 逐条通读核对） | `r8v8fixB_repro_rev2C.json`（前任会话，引用） | ✓ |
| 站桩 quotation | 152/153（唯一失败 change_his_to_forward） | **152/153**，唯一失败同名 | `r8v8rev_quotation.json` | ✓ |
| 站桩 round1face | 417/423 | **417/423**（trade_info_utils 36/41 五基线存量 + quotation 面；逐文件一致） | `r8v8rev_full_round1face.json` | ✓ |
| 站桩 round2face | 239/251 | **239/251**（v_b46 1/4、v_b71 3/4、v_b73 2/3、v_b74 4/4、v_b75 2/3、rvC_v2 2/2 + 六 site 文件存量失败名单一致） | `r8v8rev_regress_round2face.json` | ✓ |
| 34 集分片 0（8 分片口径） | 183/190（shard0 证据基线），NEWFAIL=0 | **183/190**，逐文件 failures 集合与 HEAD 证据**完全一致**、regen pyc_sha 逐文件一致、NEWFAIL=0 | `r8v8rev_34set_shard0.json`（+index）；前任 M 态复跑亦仅时戳差（已随还原清除） | ✓ |
| 站桩负对照 future_contract_info.pyc | 未涉站点面，应无扰动 | **27/29**（check_user/info_conbine 失败）@HEAD = **27/29 同二单元** @5f784272（临时 worktree 实测）⇒ 零扰动 | 本表 + §3 末行 | ✓ |

**B 部分小结：全部读数逐位一致，零虚报。**（34 集 1505/1568 总声称以分片 0 抽验 + NEWFAIL 检查代验，符合派发指令口径。）

---

## §3 变体攻击表（C 审查；探针 = `test_repros/round8/` r8v8rev_* 前缀，.py + py_compile + .pyc + RV2 验证）

| 探针 | 攻击形态 | 预期域（守卫声称） | 实测 | 判定 |
|------|---------|-------------------|------|------|
| r8v8rev_b104_chain4_battery::v1 | 4 元链 for 宿主 | CCMP.m（4 元）× e04（for 宿主）交集 | PASS | ✓ |
| ::v3 | 链含 Call 末操作数 return 位 | CCMP.m 同签 | PASS | ✓ |
| ::v5 | 4 元链 for 宿主 + continue 体 | e04 域 + 宿主交叠 | PASS | ✓ |
| ::v2 | `while 0 < x < 10 and flag:` | **H5 设计案例域**（链+and 混合） | **FAIL：循环头折叠**（`if 0<x<10:` + `while flag:` + 幻影 `pass/break`） | **打回 §0#1** |
| ::v4 | 4 元链 while 宿主 | **e08（while 宿主）× CCMP.m（4 元）交集** | **FAIL：重检泄漏为体首幻影 `if 0<x and 10<True and x*2<True`**（e04 注册占位签名） | **打回 §0#2** |
| r8v8rev_b105_walrus_battery::v1 | `while (n := f(x)) > 3:` 回边重检 | B105-H4 | PASS | ✓ |
| ::v2 | 嵌套海象实参 `g((a := h((b := h()))), a+b)` | B105 家族（实参位值链，H2/H3） | **FAIL：外层调用+实参 2+return 蒸发** | **打回 §0#3** |
| ::v3 | `a = b = f()` 负对照 | 排除面（须维持） | PASS | ✓ |
| ::v4 | if 条件位海象 + 体消费 | B105-H1 | PASS | ✓ |
| r8v8rev_b107_mtarget3_battery::v2 | `a, *b = c, *d = e, f` UNPACK_EX 链 | B107-H3/H4 | PASS | ✓ |
| ::v3 / iso::t1 / iso2::u3 | 4 目标链单独成块 / 3 目标单独 / 2 目标+前置语句 | B107-H1/H2 | PASS ×3 | ✓ |
| ::v1 / iso::t2/t3 / iso2::u1/u2 | **≥3 目标复杂链 + 同块前置普通语句** | B107 家族（多目标整体认领） | **FAIL ×5：目标 2+ 蒸发**（u1 仅剩中段单赋值——目标选择亦不一致） | **打回 §0#4** |
| r8v8rev_bmatch_guards_battery::v1 | guard 后多语句体 | B81/B103 | PASS 2/2 | ✓ |
| ::v4 | 真 guard + return 体 | B81 F1-F4 | PASS 2/2 | ✓ |
| ::v3 + or3iso::w2/w3 | or 3 支 + **裸名**守卫 | **B103 e06 or+guard 封闭域** | **FAIL：守卫静默丢弃**（w1 比较形保真 / w4 单字面量裸名保真 ⇒ 形态敏感） | **打回 §0#5** |
| ::v2 + nestnoguard::n1 | 字面量 case 臂内嵌套 match（± 守卫） | 无任何探针面覆盖（e09 = 序列宿主；r4v4r nested_guard = for 宿主 is-not-None 非嵌套 match） | pycdc **挂死/0 字段崩溃**；5f784272 worktree 同挂（**存量**） | **域外登记**（§4 B122 候选） |
| r8v8rev_b102_2eselsefin::v1/v2 | 双 except\* + else + finally（非空体 / 嵌套函数宿主） | B102 E1-E7（任意 handler 数、else、finally、宿主） | **PASS 4/4** | ✓ |
| r8v8fc_b102_battery（复用） | 电池 10 形态 | FIX_C 登记终态 8/10（ideg/pin 移交残余） | **8/10 = 登记态逐位**（ideg、pre_inner 两单元，非新 FAIL） | ✓ |
| r8v8rev_b113_doubfor_battery::v1-v4 | 双 for+if / 嵌套推导 / 三重 for 双 if / dict 双 for | B113 C1-C4（任意子句位置、任意种类） | **PASS 10/10** | ✓ |
| r8v8rev_b106_mixed_battery::v1-v4 | `f(a,*b,**kw)` / `f(*a,*b)` / `lambda *a,**k: k(*a)` / 星作推导元素 | B106 F1-F4 | **PASS 7/7** | ✓ |
| 站桩负对照 future_contract_info.pyc | 未涉站点面 | 应与 5f784272 同读 | 27/29 同二失败单元 @两树 | ✓ |

**C 部分小结：10 攻击面 PASS；5 形态域内 FAIL（打回）；1 形态域外（登记移交）；B102 电池 = 登记残余态确认。**

---

## §4 新发现与登记

1. **B122 候选（域外新形态，移交下轮，不计打回）**：字面量 case 臂内嵌套 match（`match x: case 1: match y: ...`，± 守卫）使 pycdc **无限挂死**（n1，>60s 硬验证）或 0 字节崩溃（v2 含守卫形）。**5f784272 worktree 同挂 ⇒ 存量缺陷非本轮引入**。判据事实：(a) e09_nested_match 自证仅覆盖序列宿主（`case [a, b]:` 外层），字面量宿主无任何探针面；(b) FIX_C §9 G8「嵌套二次归约合法」的归纳基证据不足；(c) r4v4r `nested_guard` 单元经核实**并非嵌套 match**（for 宿主 `if v is not None` 守卫）。登记建议：外层字面量 case 体首块上内层 match 的支配种子行走无终止边界（疑似候选循环互指），判据方向 = 内层 match 认领时以 case 体块集为 L(A) 上界（[B17] try 体边界同构，白名单可表达）。
2. **G4 存量同型第 3 处登记**：[B82] `_steps < 8`（region_ast_generator.py:28189）。声明「[B75] 存量同型镜像」**验证为真**（1.3）；保守回退失败模式；建议后续批次统一改 visited-set（与 B102/B103 的 `_seen` 有限集口径对齐），>8 透明块链的召回缺口随同消除。
3. **报告措辞勘误 ×2（登记，非打回）**：FIX_C §2.4「`_collect_or_arm_chain_instrs` / `_pure_jf_argval`（新增）：六项模板齐全」——`_pure_jf_argval` 实为紧凑判据 + C 条款（8 行码微谓词，与代码一致）；FIX_B §13「[B98-R1] 新增方法，六项要素」——实为三要素 +【反编译逻辑】框架（FIX_B §5 的「判据/归约/AST 映射/C1-C3」详述准确）。两处均不掩盖代码行为失实，docstring 与代码一致性（I.7 硬要求）无违反。
4. **B104 打回项的机制补充**（供修复工程师定位）：v4 幻影体首 `if 0 < x and 10 < True and x*2 < True / elif 10 < True and x*2 < True` 说明回边重检段在 4 元链下被 `_generate_block_statements` 路径以折叠常量占位重建（[R106] 前缀剥离族对重检段误适用）；v2 折叠说明 pre-loop 链头归约对「链后随 and 尾」的条件链未封闭（`_is_chained_compare_header` 命中后链头唯一归属未达真链头/条件链整体）。两形态均可用白名单判据（块末 opcode + 跳转目标同一性 + 栈净效应）表达，无 I.4 障碍。

---

## §5 移交项复核（8 项：移交理由是否成立）

| 项 | 移交方与理由摘要 | 复核结论 |
|----|----------------|---------|
| **B78**（条件位融合三元） | FIX_A §5 + FIX_B §7 双方独立移交；hop 块判别元 + 折叠常量合成判据事实在案；嵌套 if 替代输出经字节码实测不等（验证必败） | **成立**。判据方向确需 `_identify_ternary_regions`/`_is_ternary_block`（识别层）与 IfRegion 条件重建（发射层）协同——两批次各自单侧均无合法输入/载体；「不修」优于「硬修」：任何单侧补丁必产嵌套 if 形 = 错误输出（I.3 个案补丁 + 错构），实测判据事实（hop 判别元）已够下批直取 |
| **B79**（嵌套双层 finally×continue） | FIX_A §5（发射层装配）+ FIX_B §8（识别层分区混装：两重叠 TRY_FINALLY 块集合交叉，dump 在案） | **成立**。分区混装先于装配（生成层拿混装输入无解，C1）；继续副本判据（@74 尾 JUMP_BACKWARD→header 同一性 + B71 边类型外推）已核实待识别层修复后消费；跨层双批次独立结论一致 |
| **B80**（finally 条件段×else import×handler return） | FIX_B §9（配额耗尽，FIX_A §5 判据在案） | **成立**（较弱但合规：读数 2/3 维持零回退、判据方向「尾随块前驱仅含 finally 域末块→归 finally；多前驱汇合禁复制多域」在案可直取；非「硬修失败退回」） |
| **B82-v_swap**（两臂 return 互换） | FIX_B §10：try 主臂 return 路径布局在异常表区间外（函数入口 0-56），识别层 try 区域不含主臂路径 | **成立**。异常表区间成员关系（I.4 白名单核心项）为判据方向，属识别层 `_identify_try_except_regions` 领地；生成层无合法输入（C1），单侧不可闭合；判据事实（区间无条目 + 副本序列同构）实测在案 |
| **B98-R2**（表达式位交叉） | FIX_B §5 未竟表：消费点（return/compare/walrus/call-arg/外层三元 then 臂）各需独立重建路径；M1 前缀豁免实验证伪归档（get_last_stat 反退已回滚） | **成立**。验伪记录 = 方法论存证（实验-回滚纪律正确）；五消费点逐一有锚点与已排除方向，非笼统弃修 |
| **B98-R3**（宿主交叠）+ **B44**（≥3 层存量） | R3 与 R2 同源消费点形态宿主不引入新机制；B44 = `_build_boolop_expression` 双入口归纳（round3 判据草案），工程量独立批次 | **成立**。拆分登记（R1 已落地 +7/15、hosts +13/18 外溢）与「同源随 R2 认领」的依赖关系如实；B44 独立批次理由（双入口归纳重构）成立 |
| **B112**（yield await / async 闭包推导式 / .\<listcomp\>） | FIX_C §6：根因 = [Round6-B31] await 挂起协议链消费门（region_ast_generator.py）+ ExpressionReconstructor 平铺重建（ast_generator_v2.py 禁改文件），均在位C授权文件（pattern_parser/exception_handler/comprehension_generator/code_generator/ast_converter + 受限 region_analyzer）之外；判据方向双签名在案 | **成立**。授权边界派发事实核对无误（位B批已终、B31 门不在位C授权域）；三轮插桩追踪的排除方向（转换层无 Yield 节点可重组 / MAKE_FUNCTION 已丢弃）证明授权域内确无落锚点；「不修」符合 I.3（域内硬修必为无效补丁）；b96 电池 b3/b7 同根 4 units 伴生面如实登记 |

**8/8 成立**：全部移交均为「判据方向在授权文件外/需跨层协同 + 已实测排除单侧方案 + 判据事实存档」，无一项为「能修而不修」或以移交掩饰硬修失败。

---

## §6 II.7 十三条误解自查（终判宣告前逐条）

| # | 误解 | 是否触犯 | 说明 |
|---|------|---------|------|
| 1 | 循环论证分母 | 否 | 分母 = 探针单元/pyc 文件（源码构成），ruler = pyc_verify 外部判据；未以实现枚举当分母 |
| 2 | 有过就算 | 否 | B104/B107 等族多数单元 PASS 仍因成员 FAIL 打回其封闭声明；B102 电池 8/10 仅按「与登记残余一致」放行而非按通过率 |
| 3 | 语料证据口径 | 否 | 全部变体为定向构造最小形态；站桩语料面仅作回归/负对照 |
| 4 | 无限分母 | 否 | 探针清单封闭（15 .py/38 单元 + 引用 31 探针 + 站桩面）；未随深度膨胀计分 |
| 5 | 节点词汇当完备 | 否 | 判定全部基于字节等价验证读数与 regen 输出形态，非「节点可产出」 |
| 6 | 浅层测试当无感证明 | 否 | 恰以深度 2 外推（嵌套海象）与形态外推（裸名守卫、4 元链、前置语句）击破浅层全绿——未采信任何「浅层过即封闭」 |
| 7 | 门禁读数当完备性 | 否 | 站桩/34 集（B 部）与域判定（C 部）分列；B 全绿未用于抵消 C 域内 FAIL |
| 8 | 顶层构造粗清单 | 否 | 逐单元至块/指令级机制（`10 < True` 占位签名、`_steps` 耗尽路径、guard fail 边同一性对比） |
| 9 | 识别率当完备性 | 否 | 打回/登记判定基于「声称域成员资格 + 结构协议判据可表达性」，非命中率 |
| 10 | 维度互替 | 否 | A（合规）/B（读数）/C（变体）三维独立呈报，互不反驳（B 逐位一致不妨碍 C 打回） |
| 11 | 改工具不改方法 | 否 | 本评审零 core/ 改动；仅新增评审驱动/探针/证据 JSON（r8v8rev_ 前缀） |
| 12 | 错误检测标准（3.11 except\* 口径） | 否 | B102 复核沿用 CHECK_EG_MATCH/PREP_RERAISE_STAR/is_except_star；无 3.12 PRELOAD_RERAISE 引入 |
| 13 | 语料上限当能力上限 | 否 | B122 候选来自构造探针（非「语料未见故不管」）；打回项判定基于判据形态敏感/栈模拟缺口，未以语料覆盖面为由豁免 |

**自查结论：未触犯任一条。**

---

## §7 产出物与纪律声明

- 本报告：`rounds/round8/REVIEW2.md`。
- 证据（`r8v8rev_` 前缀，rounds/round8/）：`r8v8rev_quotation.json`、`r8v8rev_full_round1face.json`、`r8v8rev_regress_round2face.json`、`r8v8rev_34set_shard0.json`(+`_index`)、`r8v8rev_variant_results.json`（C 部全量结果与判定）；核验脚本 `r8v8rev_anchor_check.py`（75 锚）、`r8v8rev_docstring_check.py`/`_check2.py`（I.7）；驱动副本 `r8v8rev_station.py`、`r8v8rev_34set.py`（输出前缀隔离，未覆盖任何修复批证据）。
- 探针（`test_repros/round8/`，15 .py + 15 .pyc + regen OK.py）：`r8v8rev_b104_chain4_battery`、`r8v8rev_b105_walrus_battery`、`r8v8rev_b107_mtarget3_battery`、`r8v8rev_b107_iso_battery`、`r8v8rev_b107_iso2_battery`、`r8v8rev_bmatch_guards_battery`、`r8v8rev_bmatch_v1..v4`、`r8v8rev_bmatch_or3iso`、`r8v8rev_bmatch_nestnoguard`、`r8v8rev_b102_2eselsefin`、`r8v8rev_b113_doubfor_battery`、`r8v8rev_b106_mixed_battery`。
- 引用前任证据：`r8v8fixB_repro_rev2B.json` + `rev2C.json`（逐条通读核对后引用）。
- 纪律：只审查零修复；全部命令 ≤300s（超时探针以单函数拆分与 60s 硬杀进程处置）；5f784272 考古用临时 worktree 已移除；regen 副作用（M 态 `*OK.py` 29 件 + 前任 shard0.json）已 `git checkout --` 全部还原，终态 `git status` M 态 = 0、仅余本评审与前任的 `??` 未跟踪证据；未覆盖任何既有探针/证据文件。

---

## §8 整改终审（d4cf7b23；派发指令编号 §7.0–§7.5，因本文件既有 §7 产出物声明顺延为 §8.0–§8.5，内容一一对应）

- 评审角色：独立评审工程师·终审身份（对修复结论不作协商通容；结论只有 通过/打回）
- 终审对象：整改批 diff = `git diff 49603022..HEAD -- core/`（HEAD = d4cf7b23；pattern_parser.py +29、region_analyzer.py +378、region_ast_generator.py +311，合计 +676/−42）——即本报告 §0 打回 5 项 + FIX_R2.md §0-§7 声明的整改闭环
- 判据唯一：`scripts/pyc_verify.py`（RV2 口径 = 先 regen 后 verify）
- 证据前缀：`r8v8rev3_`（本终审新建；探针 `test_repros/round8/` 7 .py + 7 .pyc + regen OK.py；驱动/JSON `rounds/round8/`；原探针复跑证据 = `r8v8fixB_repro_rev3.json`（R8FB_STAMP=rev3，新 stamp 未覆盖任何既有件））

### §8.0 终判

**轮终判：放行**（Round 8 整改批（6c4468ef + d4cf7b23）整体放行；打回项数 = 0；新登记域外移交 1 项（B123 候选）+ 残差风险登记 2 项）

| # | 整改项 | A 合规（逐 hunk） | B 读数复跑 | C 新变体攻击（域内新 FAIL） | 终判 |
|---|--------|------------------|-----------|---------------------------|------|
| 1 | **B104-R2a**（while 头链+and 混合形折叠） | 通过：六识别层方法 + 生成侧组合判据全为 I.4 白名单（块末 opcode/跳转目标集合同一性/栈净效应/区域成员关系），回边重检副本存在性 = rotate-while 协议判别元（I.3 协议判据非模式匹配），未命中返回 None = C3 封闭；H5 与复发形判据差异已消除（§8.1 特别核查） | 6/6（v2 复活 + v1/v3/v4/v5 维持）；B104_main 14/14；round1face 417/423 | **零**：5 元链+and 尾（元数外推）、H5 原设计案例亲跑不复发、and-lead 镜像序、R2a∩R2b 交集、多操作数尾/首、海象/f-string/字典推导尾全 PASS；IfExp 尾 = 域外存量（两树同败 → B123 登记移交，非打回） | **通过** |
| 2 | **B104-R2b**（4+ 元链回边重检泄漏/True 占位） | 通过：`_B104_CC_RECHECK_EVAL_OPS` = 块内 opcode 序白名单完备化（语句副作用 opcode 排除 ⇒ 含用户语句的块不命中 = 封闭性）；STORE 边界多语句切分 = 块内 opcode 序；单语句位形与原整段同判（B104_main 14/14 维持实证） | 同上 6/6（v4 复活）；B104_main 14/14 | **零**：5 元链（`0<x<10<50<x*2<100`）重检无泄漏、4 元链+and 尾+双语句体交集位形全 PASS | **通过** |
| 3 | **B105-R2**（嵌套海象深度 2 值链蒸发） | 通过：净栈深改按本块指令前缀逐条 stack_effect 求和（块内 opcode 序 + CPython 值栈净效应，绝对栈深含 PUSH_NULL；对任意嵌套深度同判非深度枚举）；前缀不可得 ValueError 回退原模拟 = C3 封闭 | 5/5（v2 复活 + v1/v3/v4 维持）；B105_main 13/13、B105_call 12/12 | **零**：深度 3 三重嵌套海象（深度外推）、海象在链式比较条件操作数位全 PASS | **通过** |
| 4 | **B107-R2**（≥3 目标复杂链+前置语句目标蒸发） | 通过：交错 COPY 协议不变式（非末段段后深度 == 1、末段后 == 0）= 栈净效应协议代数性质，对任意目标数同判；2 目标链新旧读法同值（既有 2 目标读数零扰动，iso2 4/4 + B107_main 14/14 维持）；C3 同步收紧交回单目标路径；docstring ①③+C3 已随新不变式同步修订 = I.7 正面合规样例 | mtarget3 6/6、iso 5/5、iso2 4/4（五失败单元全复活）；B107_main 14/14 | **零**：4 目标混合链（首简单名+3 复杂）、4 目标全复杂链、3 目标链后接 return 全 PASS | **通过** |
| 5 | **B103-R2**（or 模式+裸名守卫静默丢弃） | 通过：POP_TOP 丢弃段剥离后按真值守卫臂形态判定（块内 opcode 序 + 跳转目标，`_simple_guard_jump_target >= jump_target_offset` 纪律不变）= 协议完备化（前导 POP_TOP 为 or 臂链 S 点对主体副本丢弃的协议本身，任意支数同判），消除守卫表达式形态敏感（I.2） | bmatch_v3 2/2 + or3iso 5/5（v3/w2/w3 复活、w1/w4 保真维持）；B103_main 13/13、B103_guard 8/8 | **零**：or 4 支+裸名守卫（支数外推）、or 支+复合守卫 `if (g and h):`、or 4 支+比较形守卫对照全 PASS（守卫全部保真） | **通过** |

**终判依据链**：A 逐 hunk 零打回（§8.1）∧ B 读数与 FIX_R2 §6 声称逐位一致零虚报（§8.2）∧ C 声称覆盖域内新 FAIL = 0（§8.3）⇒ 5/5 通过，轮放行。域外新形态（IfExp 尾）与残差风险按纪律登记移交（§8.4），不计打回。

### §8.1 整改 hunk 合规表（A 审查；I.4/I.3/I.7 零容忍逐 hunk）

| # | hunk（锚点实测在树） | 判据归类（I.4 白名单） | 黑名单/合规核查 | 判定 |
|---|---------------------|----------------------|----------------|------|
| 1 | pattern_parser.py:251-261/:265-268/:269-277 [B103-R2] POP_TOP 丢弃段剥离 + 真值守卫臂判据 | 块内指令序 + 跳转目标（`_b103r2_guard_ops` 首条 ∈ LOAD_VAR_OPS ∧ 末条 ∈ POP_JUMP 族 ∧ middle 全 POP_TOP；丢弃段只能是 POP_TOP 序列——守卫在基本块首个条件跳转处终结的协议保证） | 任意 or 支数同判（非 3 支特判；or 4 支实测 PASS）；比较形守卫经 `has_compare_and_jump` 分支不受影响（w1/v3 实测保真） | PASS |
| 2 | region_analyzer.py:4270 `_b104r2_cond_eval_seq` | 块内 opcode 序 + 指令栈效应（条件求值段 = 末次「栈深回零点」之后；末条回零不计边界 = 链末段 COMPARE 归零属求值段本体） | 无名字/常量/偏移读取 | PASS |
| 3 | :4304 `_b104r2_is_cleanup_to` | 块内指令序（POP_TOP/噪声/无条件跳转）+ 后继集合（唯一后继 == dest） | 注：`if has_jump` 两分支返回式相同 = 无行为差异冗余分支（登记级，非违反） | PASS |
| 4 | :4329 `_b104r2_cond_jump_exits_loop` | 块末 opcode（BACKWARD/FORWARD 条件跳转族）+ 跳转目标集合同一性（exit/等价出口/经纯清理块） | — | PASS |
| 5 | :4350 `_b104r2_has_recheck_mirror` | 块内 opcode 序同一性（条件求值段）+ 跳转目标 + 区域成员关系（体内/header 尾副本）= rotate-while 复制协议判别元，排除「外层 if 一次性守卫」 | I.3 协议判据（每迭代重测 ⇔ 体内有副本），非形态匹配 | PASS |
| 6 | :4379 `_b104r2_absorb_mixed_cc_chain` | (a) 透明桥（全 JUMP/噪声/POP_TOP 指令序）(b) 链末段块末跳转族 (c) 链协议逐段回溯（前驱跳转目标 == 当前段跳出目标/经清理块桥接）+ 真链头 `_is_chained_compare_header`（COPY(2)+COMPARE 对，元数无关）+ `set(segments) == {head}∪extras` 一致性 (d) 失败边收敛同一出口 (e) 全段重检副本 (f) 尾操作数逐块回溯 | 终止性 `_seen` 有限集（无计数上限，G4）；未命中返回 None = C3 | PASS |
| 7 | :4540 `_b104r2_absorb_leading_and_operands` | 镜像序同判（FORWARD 条件跳转 → 同一循环出口 + fall-through 续接 + 重检副本） | 同上 | PASS |
| 8 | :4791-4792 初始化、:4957-4958 首操作数吸收调用点（while-true cc 回溯命中 ∧ `_chain_extra` 非空）、:5246-5254 混合吸收调用点（WHILE_LOOP ∧ condition_block 已找到 ∧ 非 while-true）、:5395-5400 metadata + `region.entry = 首操作数块` | 区域成员关系接口 + 原则 4（入口引用语义） | 命中块整体并入 LoopRegion（C2 唯一归属）；metadata 键 `cc_mixed_cond_tail/lead_blocks` 为本层区域自描述 | PASS |
| 9 | region_ast_generator.py:229-246 :242 `_B104_CC_RECHECK_EVAL_OPS` | 块内指令序（纯值求值 opcode 集：装载/COPY/SWAP/比较协议/二元一元/下标/构造器/PRECALL+CALL 族/KW_NAMES/FORMAT_VALUE/噪声） | 语句副作用 opcode（STORE_*/DELETE_*/RETURN_*/IMPORT_*/异常帧/跳转控制/UNPACK_*）在集外 ⇒ 含用户语句的块不命中 = 判据封闭性 | PASS |
| 10 | :6827 `_b104r2_cond_expr_from_operand_block` | 块内 opcode 序 + 栈效应（与识别侧 `_b104r2_cond_eval_seq` 同判据）；跳转极性定否（[R38] 同族口径） | None-skip 残差风险登记（§8.4.6，域内未实证） | PASS |
| 11 | :7996-8034 混合条件 BoolOp(And) 组合（:8020-8022）+ 尾/首块标记已生成 + 首块前置语句提入 pre_stmts（:8031-8034） | 区域成员关系 + 块序（leads + Compare + tails） | 首块前置语句经 `_if_extract_cond_instructions` 按源序提入 | PASS |
| 12 | :8061-8072 噪声集补 JUMP_FORWARD/JUMP_ABSOLUTE + 后继守卫放宽至 `region.back_edge_block` | 块内指令序 + 区域成员关系（成功后继 ∈ region.blocks 或 == back_edge_block）；JUMP_BACKWARD 仍在集外 ⇒ continue 语句块不命中 | 放宽目标仅限本区域回边块（成员关系），非无界放宽 | PASS |
| 13 | :8098-8104 `_ps_ops_r2a` 混合条件同块重检镜像判定 | 块内 opcode 序同一性（条件求值段比对） | 命中同按重检抑制处理（体语句提取 + 整块抑制） | PASS |
| 14 | :8110-8135 `_store_segs_b104r2` 多语句前缀 STORE 边界切分（UNPACK_SEQUENCE/UNPACK_EX 组整段保持；UNPACK_EX oparg 位域解码） | 块内 opcode 序（STORE 边界） | oparg 位域解码 = 协议参数非魔法阈值；单语句位形分段结果与原整段同判（B104_main 14/14 维持实证） | PASS |
| 15 | :8159-8171（back_edge 白名单替换 (i)）/ :8180-8200（清理出口中间段替换 (ii)） | 块内指令序（`_B104_CC_RECHECK_EVAL_OPS`）+ 跳转目标块指令序 | 对任意链长/操作数表达式形态同判（4/5 元链 + BINARY_OP/CALL 操作数实测 PASS） | PASS |
| 16 | :56955-56992 [B105-R2] 净栈深前缀求和 + ValueError 回退 | 块内 opcode 序 + CPython 值栈净效应（含 PUSH_NULL 漏计修正） | 基本块无内部跳转 ⇒ 前缀求和 = 该指令处真值栈深；回退路径 = C3 逐位保持 | PASS |
| 17 | :58921-58936/:58951-58953/:59004-59016/:59024-59025 [B107-R2] 交错 COPY 不变式 | 栈净效应协议代数（非末段 == 1 / 末段 == 0；2 目标链两种读法同值 ⇒ 既有读数零扰动） | docstring ①③+C3 随代码同步修订 = 本批 I.7 正面合规样例 | PASS |

**I.4 黑名单五项逐项（新增 676 行实测）**：① 目标文件/函数名白名单 = 0 命中（新增行 `name ==`/`co_name ==` 零）；② start_offset 魔法阈值 = 0 新增；③ 跨层 `X.entry in Y.blocks` 反查 = 0 新增；④ 新增 self 跨方法状态 = 0（新增行 `self.X =` 赋值零命中；`self._b104r2_*` 15 处全为方法调用；`_seen` 12 处全为局部变量）；⑤ 硬编码深度/计数上限 = 0 新增（`_b107_expected` 的 0/1 = 交错 COPY 协议不变式非上限；UNPACK_EX oparg 位域解码 = 协议参数；`depth = 0`/`insert(0, …)` = 循环初始化）。**G3**：新增 def 7 个全 `_b104r2_*` 前缀（:4270/:4304/:4329/:4350/:4379/:4540 region_analyzer + :6827 region_ast_generator），七违禁前缀（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）= 0 命中。**插桩/BOM**：新增行 print( = 0、`os.environ/getenv/DEBUG/R8*DBG` 插桩族 = 0；region_analyzer.py 与 region_ast_generator.py 首 3 字节 `efbbbf` × 计数 1（单头）；pattern_parser.py 无 BOM = 存量（49603022 与 5f784272 两基线 `git show` 原始字节核验均 `222222`/BOM 0，FIX_R2 §6.5 如实记录属实）。

**B104-R2a 特别核查（派发指令专项；H5 设计案例同形复发是否真正消除）**：
1. `_detect_boolop_conditional_chain`（region_analyzer.py:29684）本次整改**零触碰**——修复不是改 boolop 链检测器，而是在 Phase 1 循环识别内以 `_b104r2_absorb_mixed_cc_chain` 把「链段 + 透明桥 + 清理块 + and 尾/首操作数块」**先占并入 LoopRegion**（唯一归属），使 `_identify_chained_compare_regions` 不再抢占为 IfRegion（折叠根因消除）。
2. **H5 与复发形之间判据分支差异 = 已消除**：判据链 (a)-(f) 全部读协议结构事实（桥透明性/跳转目标同一性/链协议回溯/失败边收敛/重检副本存在），无任何一处读「尾操作数的表达式形态」——裸名尾、比较尾、海象尾、f-string 尾、字典推导尾、多操作数尾走同一分支全 PASS（§8.3 实测）；操作数形态只进入生成侧通用 `expr_reconstructor`（与识别判据解耦）。原 v2 失败的形态敏感（REVIEW2 §0#1）不复存在。
3. **H5 原设计案例亲跑**（FIX_B §1 所引 `while 0 < x < n < 100 and n < 100:`）：`r8v8rev3_b104_chain5_battery::v2` regen 保真 `while 0 < x < n < 100 and n < 100:`（无折叠、无幻影 break、无重检泄漏），RV2 PASS——**不复发确认**。

**A 部分小结：17 hunk 全 PASS；黑名单五项零命中；G3/G4/插桩/BOM 全过；2 处报告措辞过宽 + 1 处死分支登记（见 §8.4），零打回。**

### §8.2 读数独立复跑表（B 审查；防虚报；与 FIX_R2 §6 声称核对）

| 面 | FIX_R2 声称 | 本终审实测 | 证据 | 判定 |
|----|-------------|-----------|------|------|
| 变体电池 7 件（RV2 逐件） | b104_chain4 6/6、b105_walrus 5/5、b107_iso 5/5、b107_iso2 4/4、b107_mtarget3 6/6、bmatch_v3 2/2、bmatch_or3iso 5/5 | **逐位一致**：6/6、5/5、5/5、4/4、6/6、2/2、5/5（全部 success、零失败单元） | `r8v8rev3_battery_rerun_main.json` | ✓ |
| guards_battery（防误伤面） | 前审绿面 = v1/v4 单元（v2 = B122 登记） | 整文件 regen **HANG >120s 硬杀**——49603022 基线 worktree 同挂 >90s = **两树同挂（B122 存量维持，非整改误伤）**；绿单元经分立探针复验 **v1 2/2、v4 2/2**；tracked `guards_batteryOK.py` 基线即 0 字节（前任「0 字节崩溃」读数与本次「挂死」为同一 B122 灾难族：pycdc 建文件后挂死/崩溃落盘 0 字节） | `r8v8rev3_battery_rerun_bmatch.json` + 基线 worktree 实测 | ✓（域外存量维持） |
| nestnoguard（防误伤面） | n1 = B122 登记（挂死） | 整文件 regen **HANG**——49603022 基线同挂 >90s = **两树同挂（存量维持）**；tracked `nestnoguardOK.py` 基线即 0 字节 | 同上 | ✓（域外存量维持） |
| 原登记探针抽验 6 件（R8FB_STAMP=rev3） | B104_main 14/14、B105_main 13/13、B105_call 12/12、B107_main 14/14、B103_main 13/13、B103_guard 8/8 | **逐位一致**：14/14、13/13、12/12、14/14、13/13、8/8（合计 74/74） | `r8v8fixB_repro_rev3.json`（新 stamp，未覆盖既有件） | ✓ |
| 站桩 round1face | 417/423 | **417/423**（24 文件逐文件一致：trade_info_utils 36/41 五基线存量 + quotation 152/153，其余 22 文件全绿） | 本节记录（station 输出） | ✓ |

**B 部分小结：全部读数与 FIX_R2 §6 声称逐位一致，零虚报；域外 B122 两形态两树同挂 = 整改未引入新扰动。**

### §8.3 收紧守卫新变体攻击表（C 审查；探针 = `r8v8rev3_*` 前缀，test_repros/round8/，py_compile 3.11.7 同法 + RV2 验证）

| 探针（单元） | 攻击形态 | 域归属 | 实测 | 判定 |
|--------------|---------|--------|------|------|
| r8v8rev3_b104_chain5_battery::v1 | 5 元链 while + and 裸名尾（`while 0<x<10<50<x*2<100 and flag:`，元数外推） | **B104-R2a 声称域**（链协议任意元数） | PASS（regen 保真 `while 0 < x < 10 < 50 < x * 2 < 100 and flag:`） | ✓ |
| ::v2 | **H5 原设计案例亲跑**（`while 0 < x < n < 100 and n < 100:`） | B104-R2a 声称域 | PASS（保真，无折叠/幻影/重检泄漏） | ✓ |
| ::v3 | and-lead 镜像序 4 元链（`while flag and 0<a<b<c<d:`，首操作数吸收声称域） | B104-R2a 声称域 | PASS | ✓ |
| ::v4 | R2a∩R2b 交集：4 元链 + and 尾 + 双语句体 | 两整改声称域交集 | PASS | ✓ |
| r8v8rev3_b104_foror_battery::v1/v2 | for 宿主 4 元链 + or 尾（`if 0<a<b<c<d or e: pass`） | 域邻探查（or 尾不在 and 尾声称域内） | **PASS 3/3**（现机械自处理，无需整改介入） | ✓ |
| r8v8rev3_b104_opdeep_battery::v1 | 海象作 and 尾操作数（`while 0<x<10 and (y := f(x)):`） | B104-R2a 声称域（任意尾操作数） | PASS（`(y := f(x))` NamedExpr 保真重建） | ✓ |
| ::v2/v3 | 多操作数 and 尾（`... and flag and x < limit`）/ 多操作数 and 首（`while flag and g2 and 0<a<b<c:`） | B104-R2a 声称域（(f) 多操作数同判） | PASS 4/4 | ✓ |
| r8v8rev3_b104_exprtail_battery::v1 | f-string and 尾 | 域内（操作数求值段含 FORMAT_VALUE/BUILD_STRING） | **HEAD PASS；49603022 基线 FAIL（折叠+幻影重检）⇒ 整改净增益** | ✓ |
| ::v2 | 字典推导式 and 尾（内层 code object） | 域内 | **HEAD PASS；基线 FAIL ⇒ 整改净增益** | ✓ |
| ::v3 | **IfExp and 尾**（`while 0<x<10 and (y if y else x):`） | **域外**（IfExp 尾 = 多块钻石位形，超出单块尾操作数吸收判据域；两树同败 = 存量） | **FAIL**：HEAD 输出 `while 0<x<10: if y: continue / y / continue / x+=1 / n+=1`；基线输出另形同败（`while 0<x<10: break / if y: continue ...`）；该探针 49603022 = 2/5 → HEAD = 4/5 | **域外登记移交**（B123 候选，§8.4.5；非打回） |
| r8v8rev3_b105_walrus3_battery::v1 | 三重嵌套海象（`f((a := g((b := h((c := i()))))), a+b+c)`，深度外推） | **B105-R2 声称域**（任意嵌套深度） | PASS（深度 3 值链整树保真） | ✓ |
| ::v2 | 海象在链式比较条件操作数位（`if 0 < (n := len(x)) < 10:`） | 域邻（B105 × COPY(2) 链协议交叉） | PASS | ✓ |
| r8v8rev3_b107_mixed4_battery::v1 | 4 目标混合链首简单名（`a = b.c = d[k] = e.f = v`） | **B107-R2 声称域**（交错 COPY 任意 N） | PASS | ✓ |
| ::v2 | 3 目标复杂链 + 链后接 `return v` | 域内邻例（后继 return 位形） | PASS | ✓ |
| ::v3 | 4 目标全复杂链（`b.c = d[k] = e.f = a.g = v`） | B107-R2 声称域 | PASS 4/4 | ✓ |
| r8v8rev3_bmatch_or4_battery::v1 | or 4 支 + 裸名守卫（`case 1\|2\|3\|4 if g:`，支数外推） | **B103-R2 声称域**（S 点丢弃段协议任意支数） | PASS（`case 1 \| 2 \| 3 \| 4 if g:` 守卫保真） | ✓ |
| ::v2 | or 支 + 复合守卫（`case 1\|2 if (g and h):`，跨块 fail 边） | 域内邻例（守卫表达式形态再外推） | PASS（`if g and h:` 保真） | ✓ |
| ::v3 | or 4 支 + 比较形守卫（w1 对照支数外推） | 域内对照 | PASS 4/4 | ✓ |

**C 部分小结：7 探针 28 单元，声称域内新 FAIL = 0；1 单元（IfExp 尾）域外两树同败登记移交；2 单元（f-string/字典推导尾）为基线败 → 整改后 PASS 的净增益实证。**

### §8.4 勘误与登记复核

1. **I.7 勘误 2 项复核 = 属实，放行并记录**：
   - `_generate_block_statements_body`（region_ast_generator.py:53198，I.7 强制类 `_generate_*`）：基线（49603022）与 HEAD docstring **逐字节一致**（存量六项保持、未扩 [B105] 条目）——②所列为跨块守卫清单，[B105-R2] 为块内判据不在其列，docstring 无失实陈述；子守卫行为由内联注释块 :56955-56970 完整承载且与代码逐条一致 ⇒ **存量 docstring 未随扩成立，非注释与行为矛盾** ⇒ 按 `_loop_generate_while` 存量口径同类登记放行。
   - `_collect_pattern_blocks`（pattern_parser.py:108，非强制类）：基线与 HEAD 单行 docstring 一致（未随 hunk 扩充）；内联注释块 :251-261 与代码一致 ⇒ 登记放行。**附注（报告引文勘误，登记）**：FIX_R2 §5 引该 docstring 原文作「排除pattern continuation」，树内实为「包括pattern continuation」——引文措辞偏差，非代码行为失实。
2. **FIX_R2 §1/§7.2 措辞过宽登记（新增，非打回）**：「`_b104r2_*` 六方法 docstring ①-⑥+C1/C2/C3 齐全」——实测仅 `_b104r2_absorb_mixed_cc_chain` 具全 ①-⑥+C1/C2/C3；其余五方法 + `_b104r2_cond_expr_from_operand_block` 为紧凑判据式 docstring（与代码一致、非 I.7 强制类）——同本报告 §1.5 `_pure_jf_argval` 措辞勘误既有口径，登记。
3. **G3 复核 = 合规**：新增 def 7 个全 `_b104r2_*` 前缀（非七违禁前缀），实测 0 命中。
4. **B122 维持 = 确认**：三形态（guards_battery 整件 / bmatch_v2 分立 / nestnoguard n1）在 49603022 与 HEAD **两树同挂**（>90s 硬验证）⇒ 存量缺陷维持域外移交，非整改误伤；「0 字节崩溃 vs 挂死」读数差异为同一 B122 灾难族内观察口径差（pycdc 建文件后挂死，落盘 0 字节），登记澄清。
5. **新登记 B123 候选（域外，移交下轮，不计打回）**：while 头链式比较 + **IfExp 尾操作数**（`while 0<x<10 and (y if y else x):`）→ 循环头退化为纯链、IfExp 钻石块泄漏为体（HEAD：`while 0<x<10: if y: continue / y / continue / x+=1 / n+=1`）。**两树同败**（49603022 探针 2/5 → HEAD 4/5，整改对该探针净改善 +2）⇒ 存量缺口非整改回归。机理：IfExp 尾操作数为多块钻石（test/then/else/merge），`_b104r2_absorb_mixed_cc_chain` 的尾操作数判据（单块、块末条件跳转 → 循环出口）不覆盖块集形；判据方向（白名单可表达）= 尾操作数吸收扩为**块集判据**（merge 块块末条件跳转 → 循环出口 + then/else fall-through 续接 + 全集 recheck mirror 存在）。证据 = `r8v8rev3_b104_exprtail_battery`（.py/.pyc/OK.py）+ `r8v8rev3_variant_results.json`。
6. **None-skip 残差风险登记（B104-R2a 生成侧，登记不打回）**：`_b104r2_cond_expr_from_operand_block` 返回 None 时调用方静默跳过该操作数（region_ast_generator.py:8026-8028），若其余 vals ≥ 2 则 BoolOp 缺员发射 = 潜在静默语义腐蚀路径；实测域内 16 变体未触发（海象/f-string/字典推导/多操作数全部重建成功），且识别侧 recheck-mirror 判据先要求条件求值段非空，None 罕见；建议后续批次把 skip 改为「任一操作数重建失败 ⇒ 整体不认领回退」（docstring「保守」措辞随同修正）。
7. **移交项维持复核**：B112 三单元（21/24）与 8 项移交（B78/B79/B80/B82-v_swap/B98-R2/R3/B44）维持——FIX_R2 §6.1 r2fixallB/C 半与登记残余名单逐位一致（前任段证据通读引用）+ 本终审 B104/B105/B107/B103 攻击面探针全绿无恶化；B122 维持（上行 4）；`_steps < 8` 存量三处与本批 diff 无交（新增行 `_steps` = 0 命中）维持 G4 登记口径。

### §8.5 II.7 十三条误解自查（终判宣告前逐条）

| # | 误解 | 是否触犯 | 说明 |
|---|------|---------|------|
| 1 | 循环论证分母 | 否 | 分母 = 探针单元/pyc 文件（7 探针 28 单元 + 复跑 7+2+6+1 面），ruler = pyc_verify RV2 外部判据 |
| 2 | 有过就算 | 否 | 5 项逐项以「域内新 FAIL = 0」独立判通过；域外 IfExp 尾如实登记 B123 不以其余全绿豁免，f-string/字典推导尾基线败不冒充整改功 |
| 3 | 语料证据口径 | 否 | 全部变体为定向构造最小形态；站桩面仅作回归 |
| 4 | 无限分母 | 否 | 探针清单封闭（r8v8rev3_ 7 件 + 复用 9 既有 + 6 抽验 + 1 站桩），未随深度膨胀计分 |
| 5 | 节点词汇当完备 | 否 | 判定全部基于字节等价读数 + regen 输出逐行肉眼核（H5/海象/or 守卫/链目标保真形态逐条引录） |
| 6 | 浅层测试当无感证明 | 否 | 恰以 5 元链/深度 3/4 目标/or 4 支/复合守卫外推攻击；全部 PASS 后方判协议一般化成立 |
| 7 | 门禁读数当完备性 | 否 | B（读数）与 C（域判定）分列；IfExp 尾域外登记未以 B 全绿抵消 |
| 8 | 顶层构造粗清单 | 否 | 逐单元至块/指令级（重检副本 opcode 序同一性、交错 COPY 深度不变式、S 点 POP_TOP 丢弃段、PUSH_NULL 漏计差 = 块内调用条数） |
| 9 | 识别率当完备性 | 否 | 通过/打回基于「声称域成员资格 + 判据协议一般化 + 白名单可表达」，非命中率 |
| 10 | 维度互替 | 否 | A/B/C 三维独立呈报互不反驳（B 逐位一致不妨碍 C 域外如实登记） |
| 11 | 改工具不改方法 | 否 | 本终审零 core/ 改动（终态 git status M/D = 0）；仅新增 r8v8rev3_* 证据与探针 |
| 12 | 错误检测标准 | 否 | 3.11 口径维持（POP_JUMP_* 族/CHECK_EG_MATCH/PREP_RERAISE_STAR；无 3.12 PRELOAD_RERAISE 引入） |
| 13 | 语料上限当能力上限 | 否 | B123 候选来自构造探针（非「语料未见故不管」）；IfExp 尾域外归属以判据结构（单块 vs 钻石块集）+ 两树同败实证，非以语料覆盖面豁免 |

**自查结论：未触犯任一条。终判（§8.0 放行）有效。**

### §8.6 本终审产出物与纪律声明

- 本节：`rounds/round8/REVIEW2.md` §8（派发指令 §7.0-§7.5 对应 §8.0-§8.5）。
- 证据（`r8v8rev3_` 前缀，rounds/round8/）：`r8v8rev3_battery_rerun.py`/`_main.json`/`_bmatch.json`（变体电池复跑）、`r8v8rev3_variant_results.json`（C 部全量结果/域归属/B123 登记）、`r8v8rev3_finalize_evidence.py`（证据汇编）；原探针复跑 = `r8v8fixB_repro_rev3.json`（R8FB_STAMP=rev3 新 stamp）。
- 探针（`test_repros/round8/`，r8v8rev3_ 7 .py + 7 .pyc + regen OK.py，未覆盖任何既有探针）：`r8v8rev3_b104_chain5_battery`、`r8v8rev3_b104_foror_battery`、`r8v8rev3_b104_opdeep_battery`、`r8v8rev3_b104_exprtail_battery`、`r8v8rev3_b105_walrus3_battery`、`r8v8rev3_b107_mixed4_battery`、`r8v8rev3_bmatch_or4_battery`。
- 纪律：只审不修、零 core/ 改动、零 git commit；全部命令 ≤300s（挂死探针 90-120s 硬杀进程处置）；49603022 考证用临时 worktree 两处（r8base/r8base2）已全部移除；regen M 态 `*OK.py`（变体电池 7 + 复跑探针 6 + 站桩/调度 1 等，含逐位同写未显 M 态的 v1/v4/v2/guards/nestnoguard OK）终态已 `git checkout --` 全部还原，`git status` M/D = 0；B122/B123 域外项如实登记移交。
