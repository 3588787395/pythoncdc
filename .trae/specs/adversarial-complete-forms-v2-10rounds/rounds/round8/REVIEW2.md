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
