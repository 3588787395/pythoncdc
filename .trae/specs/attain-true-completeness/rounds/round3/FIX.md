# Round 3 · try-raise-assert-宿主族封闭（Try / Raise / Assert / Import / Global）— FIX 报告（终稿）

- 规范：`.trae/specs/attain-true-completeness/`（简称 R）；批次 R3（tasks.md Task 3）
- 树：HEAD `ece1aab5` 承接（R2 交付后）；本文件随进度增量追加（防中断），§1 为增量日志（全程保留），§2-§6 为终稿节
- 纪律：只改 `core/cfg/**`；判据 = I.4 白名单；G3=0/G4=0；标记 `[Bn-V3R3]`；不提交 git
- 判据唯一 = `scripts/pyc_verify.py single`（RV2：先 `python pycdc.py <pyc> -o <base>OK.py` regen 再 verify）；stage = `test_repros/round3/`

## §0 范围与结论摘要（终稿）

R3 红单元（round1 BREACH_RECON §2 行5/8/9/10/13/14 + §4 R3 映射 + 移交 c13/v_swap）：

| 族 | 探针（pyc 源） | 红单元 | round1 读数 / 本轮基线 |
|---|---|---|---|
| B87 try 宿主 | c04=round2/c04_class_try.pyc | CTryNest | 5/6 = 5/6 |
| B87 | m02=round2/m02_top_ifmain.pyc | `<module>` | 2/3 = 2/3 |
| B87 | m06=round2/m06_module_loops.pyc | `<module>` | 0/1 = 0/1 |
| B87 | x04=round2/x04_try_deep_hosts.pyc | try_in_if | 6/7 = 6/7 |
| B87 | x02=round2/x02_for_deep_hosts.pyc | for_in_try | 5/7 = 5/7 |
| B87 | x01=round2/x01_if_deep_hosts.pyc | if_in_try | 4/7 = 4/7 |
| B73/B80 | v_b73_face=probes_rv2/v_b73_face.pyc | v_imp_cond_fin | 2/3 = 2/3 |
| B75/B82-v_swap | v_b75_face=probes_rv2/v_b75_face.pyc | v_swap_arm_returns | 2/3 = 2/3 |
| B56 assert 幻影 else | r8_07=round8/r8_07_assert_forms.pyc | r8_assert_nested_func | 10/11 = 10/11 |
| B56 | x08=round2/x08_stmt_leaves.pyc | assert_leaf | 6/8 = 6/8 |
| B56 | r8_10=round8/r8_10_expr_cross_stmt.pyc | r8_x_assert_ternary | 9/12 = 9/12 |
| B58 raise×三元 | r8_10（同上） | r8_x_raise_ternary_class | 9/12 = 9/12 |
| raise 尾闩移交 | c13=round2/c13_class_misc.pyc | CMisc.boom | 2/3 = 2/3 |
| B69 | rv9_01=round9/rv9_01_b68_nonfin_tail.pyc | emptyfin_in_if | 4/5 = 4/5 |

复验（应保持绿）：r8_08 9/9、n9v9_stmt_sweep 6/6、rv8_02 7/7、r10_04 3/3、r10_15 6/6。
负对照九件（应保持 60/60）：r7_07 7/7、r7_08 8/8、rv8_01 7/7、rv8_02 7/7、r8_06 10/10、r10_04 3/3、r10_15 6/6、r10_21 4/4、rv10_32 8/8。

### 复现基线（本轮实跑，stamp=r3pre1a/1b/2/2b/3/3b）

| run | 探针 | 读数 |
|---|---|---|
| r3pre1a | c04 5/6；m02 2/3；m06 0/1；x04 6/7 | 13/17 |
| r3pre1b | x02 5/7；x01 4/7；c13 2/3；x08 6/8 | 17/25 |
| r3pre2 | v_b73_face 2/3；v_b75_face 2/3；r8_07 10/11；r8_10 9/12 | 23/29 |
| r3pre2b | r8_08 9/9；rv9_01 4/5；rv9_02 4/5；n9v9 6/6 | 23/25 |
| r3pre3 | r7_07 7/7；r7_08 8/8；rv8_01 7/7；rv8_02 7/7；r8_06 10/10 | 39/39 |
| r3pre3b | r10_04 3/3；r10_15 6/6；r10_21 4/4；rv10_32 8/8 | 21/21 |

与 round1 逐位一致；零 pass→fail。

**终态结论（主代理验收）**：R3 红单元全部翻绿（c04/m02 两项 park 除外，归 Round 8）；共 13 项修复（§1，含 [B134-V3R3 修订]），涉改 2 文件 25 hunks（+736/−13，§2），落地标记 `[Bn-V3R3]` 25 处。复核与门禁全过（§4/§5）：邻域零回归（r3q6b 79/86 逐项=基线）、负对照八件 62/62、合成 B 门禁 22 探针 45/45、安全组 25/26（余 1 = B57 域外）、402 八分片 6617/6617 REGRESSIONS=0×8、small34 1568/1568 IMPROVED=33、quotation 153/153、tests 七套件基线名单一致（2 failed/282 passed/2 xpassed）、IV.2 全绿（BOM 单头 / G3=0 / G4=0）、site-packages 零字节差异。残余观察（域外，未追，登记见条目 12/13）：B57 `r8_x_for_iter_ternary`、x01::if_in_while（R6/B94）、x01::if_in_match（R5/B122）、rv9_02::while_with_whole_body（B70 维持）、b133b/b134b 原始形态。

### 终态读数

| 探针 | 基线 | 终态 | 备注 |
|---|---|---|---|
| c04 | 5/6 | 5/6 | park（CTryNest，归 R8） |
| m02 | 2/3 | 2/3 | park（`<module>`，归 R8） |
| m06 | 0/1 | **1/1** | B133 修 |
| x04 | 6/7 | **7/7** | B87 修 |
| x02 | 5/7 | **6/7** | 余 1 = for_in_match（域外） |
| x01 | 4/7 | **5/7** | 余 2 = if_in_while（R6/B94）、if_in_match（R5/B122） |
| v_b73_face | 2/3 | **3/3** | B73 修 |
| v_b75_face | 2/3 | **3/3** | B82 修 |
| r8_07 | 10/11 | **11/11** | B56 修 |
| x08 | 6/8 | **8/8** | B56/B134 修 |
| r8_10 | 9/12 | **11/12** | 余 1 = r8_x_for_iter_ternary（B57 域外）；B135/B136 修 |
| c13 | 2/3 | **3/3** | raise 尾闩移交修 |
| rv9_01 | 4/5 | **5/5** | B69 修 |
| rv9_02 | 4/5 | 4/5 | while_with_whole_body（B70 维持，域外） |
| 复验 r8_08 / n9v9 / rv8_02 / r10_04 / r10_15 | 全绿 | 全绿 | 9/9、6/6、7/7、3/3、6/6 |

## §1 修复日志（增量）

1. **[B87-V3R3] try 体内受保护语句 NOP 保真**（x04::try_in_if / x01::if_in_try 根因）
   - 根因：`if 1:` 语句头编译为单 NOP 且自身被异常表条目覆盖（`{6,8}->36` / `{4,6}->38` / `{8,14}->22`）。当前管线两处丢失该 NOP：① `_generate_try_body` 块遍历对「无有效指令块」整体丢弃；② `_generate_block_statements_body` SKIP_OPS 分支对「NOP 后紧跟其体语句同块」形态不命中既有孤立 NOP 判据（after_nop 非空 → `_is_orphan_boundary_nop` False；块首 NOP → `_rag_is_orphan_nop_statement` False）。丢失后该条目在重编译产物中不再生成（orig 补丁态零长度残留 `(0,0)->24` 缺失）→ 异常表比较失配。
   - 判据（I.4 白名单，纯异常表结构）：新增谓词 `_is_protected_statement_nop` = 存在条目 `start == NOP 偏移`（try 帧标记 NOP 游程 start == run_end，不命中本判据）。发射 `while False: pass` 占位（实测编译为单孤立 NOP 且自身受同一保护区间覆盖）。
   - 改动（`core/cfg/region_ast_generator.py` 3 处，均标 `[B87-V3R3]`）：谓词定义 L59151；`_generate_try_body` 块遍历 NOP-only 分支 L33054；`_generate_block_statements_body` SKIP_OPS elif 链 L63158。
   - 候选先行验证（pylingual compare_pyc 单测）：x04 `try: while False: pass; try/finally...` PASS（单占位）；x01 双占位 PASS（`while False` 与 `""` 两形态均 PASS，单占位两形态均 FAIL）。
   - 验证读数：stamp=r3fix1 **x04 6/7→7/7**（try_in_if 绿）、**x01 4/7→5/7**（if_in_try 绿，余 2 红为域外 if_in_while/if_in_match）。全量复跑零回归：r3fix1b（c04/m02/m06/x02/c13 = 14/20 逐位同基线）、r3fix1c（v_b73/v_b75/r8_07/x08 = 20/25 同基线）、r3fix1d（r8_10 9/12、rv9_01 4/5、rv9_02 4/5 同基线；r8_08 9/9、n9v9 6/6 复验绿）、r3fix1e 负对照九件 **60/60**；trade_info_utils 41/41 + `git diff --stat site-packages/` 空。


2. **[B69-V3R3] 子区域正常路径延续块（merge）归入真臂**（rv9_01::emptyfin_in_if 根因）
   - 根因：`if a: try: pass finally: pass; return 6 else: return 7` 中 `return 6` 的真身块（`LOAD_CONST 6; RETURN_VALUE`，真臂尾跳转目标）被静默丢弃 → 产物真臂以隐式 `return None` 收尾（常量 6 蒸发；补丁态分歧：`LOAD_CONST 6` vs `LOAD_CONST None`，零长度异常表残迹 `(4,4,4)` vs `(8,8,8)`）。区块结构：IfRegion@0（then=[@6]，else=[@26]，merge_block=@22）；merge@22 的 canonical owner 为子区域 TryExceptRegion@6（blocks={6,12,16,22}，@22 为其正常路径出界延续块）。分析层孤儿释放因「子区域带顶级祖先 ∧ 父发射集合覆盖其 entry（6 ∈ IfRegion.blocks）」豁免 @22；而 IfRegion 发射面（then/else 臂）不含 @22 ⇒ 无人发射。
   - 判据（I.4 白名单，同层结构事实）：`_merge_block_is_then_exclusive` 已含正确结构推理（then 臂全连接件 ∧ 假出口 BFS 不可达 merge ⇒ 真臂专属延续），但被 R66-diag1 E1（「空 then 臂 + 非空 else 臂 + 无比较链 ⇒ 源=pass 形态，归父序列发射」）短路；E1 前提在本形态不成立——then 臂源码级非空（起头为子区域，臂块=NOP,NOP,JUMP）。新增豁免：merge 的 canonical owner 存在、非本区域、非 BASIC、且其 entry ∈ then_blocks 时 E1 不短路，交既有祖先检查 + 假出口可达性 BFS 判定。
   - 改动（`core/cfg/region_ast_generator.py` 2 处注释点，均标 `[B69-V3R3]`）：`_merge_block_is_then_exclusive` docstring 补例外说明（L23800 段）；E1 段新增 owner 判据 `_r66e1_merge_swallowed`（L23865 段）并收紧 E1 条件。下游走既有 W15-C 拼接（merge 语句归入 then 体，一块一处归属）→ `if a: [Try, Return(6)] else: [Return(7)]`。
   - 候选先行验证（pylingual compare_pyc 单测）：A（`return 6` 在真臂、含 else）**PASS**；E（`return 6` 在真臂、无 else）PASS；B（`return 6` 作 if 后兄弟语句）FAIL（ET `(6,6,6)`）——证明归入真臂是唯一正确形态。
   - 验证读数：stamp=r3fix2a **rv9_01 4/5→5/5**（emptyfin_in_if 绿）。全量复跑零回归：r3fix2b 14/17（x04 7/7；c04/m02/m06 同基线）、r3fix2c 18/25（x01 5/7；x02/c13/x08 同基线）、r3fix2d 23/29（同基线）、r3fix2e 24/25（r8_08/n9v9 绿；rv9_02 同基线）、r3fix2f 39/39、r3fix2g 21/21、r3fix2h+2i 负对照九件 **60/60**；trade_info_utils 41/41 + `git diff --stat site-packages/` 空。


3. **[B131-V3R3] while True 内嵌 if 的条件归属与极性三处联动**（c13::CMisc.boom 根因）
   - 根因（源 `if i > 0: while True: if i: break else: continue`，双层三处）：① 分析层 `_identify_loop_regions` 既有「rotate-while 外部前驱条件采纳」分支（Phase 7 方案 A）把宿主 if 的条件块@36（`POP_JUMP_FORWARD_IF_FALSE→@60`，落点在体外）采纳为 LoopRegion@50 的 condition_block，覆盖 R21-33b 已按自身边形状判定的 is_while_true=True；② 生成层 `_loop_generate_while` 回退（cond_block None 时扫 header 前驱采纳带条件跳转者）再次采纳 @36 → 发射 `while i > 0:` 测试；③ 生成层 `_loop_handle_header_no_condition` 分支（IF_FALSE 落点 jt 为 continue 目标、fall-through ft 非 continue）发射 `If(cond, [Continue])`——极性反转且 ft 体（break）丢失。合计产物 `while i > 0: if i: continue / break`：重编译 PJF 落点由 continue 块错位到 break 块（pyc_verify "Different control flow"）。
   - 判据（I.4 白名单，同层结构事实）：① 闩锁存在性——仅当循环回边源块末条为 BACKWARD_CONDITIONAL_JUMP_OPS 且跳转目标==header（rotate-while 入口 guard + 体内底部重检形）时，header 才可能不是条件块本身、体外前驱可作条件；回边全为无条件 JUMP_BACKWARD（continue 语义边，模式 C）时体外带跳出条件的前驱是宿主 if 的条件块（`if gate: while True: ...` 形），循环保持 while_true。② is_while_true 为真时生成器禁止外部前驱回退（交 While(True) 发射路径，header 尾条件由 hdr_nc 按体内 if 归约）。③ IF_FALSE→jt(continue)：条件为假走 jt、为真走 ft ⇒ `If(cond, ft 体)`；jt 纯回边（无用户载荷）由循环隐式回边再生仅标记已生成，jt 带载荷时并入 orelse 并补 Continue。
   - 改动（3 处，均标 `[B131-V3R3]`）：`core/cfg/region_analyzer.py` L5465-5487 段（`_b131_bottom_latch` 判据 + 采纳分支加闩锁门）；`core/cfg/region_ast_generator.py` L7497 段（`_loop_generate_while` 回退加 `not region.is_while_true` 门）；同文件 L13628 段（`_loop_handle_header_no_condition` 极性 + ft 归属修，含 jt 载荷分支）。
   - 候选先行验证（CPython 3.11.7 编译对照 + pylingual 单测）：源码 A（`if i: break else: continue`）/ B（`if i: break; continue`）/ D（`if i: break`）三形态编译逐位同构（`LOAD i; PJF→continue块; JUMP_FORWARD; JUMP_BACKWARD`），C/E（含 `if i: continue` 形态）PJF 落点错位；分支探针确认 hdr_nc 恰为产出 `If(i, [Continue])` 的路径、ft 块 role=PURE_BREAK ⇒ `_if_generate_branch_stmts([ft])` 得 `[Break]`。修复后 regen 形态 = D（`while True: if i: break`），`_r3_bcdiff` CFG_EQ=True / ET_EQ=True。
   - 验证读数：stamp=r3fix3c **c13 2/3→3/3**（CMisc.boom 绿）。全量复跑零回归：r3fix3d 22/27（c04/m02/m06/x02 同基线；x04 7/7；c13 3/3）、r3fix3e 25/32（x01/x08/v_b73/v_b75/r8_07 同基线）、r3fix3f 33/37（r8_10/rv9_02 同基线；r8_08 9/9、rv9_01 5/5、n9v9 6/6 绿）、r3fix3g+3h 负对照九件 **60/60**；trade_info_utils regen 与提交版 sha256 逐位一致 + `pyc_verify single` 41/41。

4. **[B132-V3R3]·已回退 park：m02 `<module>` 深层 try 区域污染（c04 同族）**
   - 处置：收敛尝试失败 → **[B132-V3R3] 全部编辑（5 标记点/6 hunks）完整回退**（保 B87/B69/B131）：region_analyzer W3 出口吸收收紧 + `_is_trivial_return_block` 门、循环体尾随子区域 parent elif；region_ast_generator else_blocks 域扣除、`_b75` 副本 Return→Break、RETURN 内联形 elif Break。回退精确性：`git diff --stat` 恢复 **+170/−5**（analyzer +23/−1、generator +147/−4；= B87 64 + B69 36 + B131 70 加法，与 r3fix3h 验证态逐位一致，`py_compile` 通过）；`V3R3` 标记审计余 8 处（B87×3 / B69×3 行 / B131×2 行 + analyzer B131×1），无 B132 残留。
   - 回退证据（stamp=r3m02_rev1/rev2）：m02 **2/3**（`<module>` Different control flow，与 r3pre1a / r3fix3d 基线逐位一致）；梯度 a00 1/2、a01 1/2、a06 1/2（自 fix2d 劣化值 0/2 恢复）、a07 1/2、b09 1/2、b10 1/2、b12 3/3、c14 1/2、c15 1/2、c16 3/3、c17 1/2（= lad3 基线逐位，fix2c/2d 的 c14/c15/c17 增益仅为该死族诊断探针、非交付红单元）；三前序族复验 **x04 7/7、rv9_01 5/5、c13 3/3** 保持。回退后工作树 = r3fix3h 已验证态（entries 1-3 的零回归/负对照 60/60 直接承接）。
   - 残余根因（park 定案）：`for k in range(3): while k: try: _run(k) except ValueError: break finally: k -= 1` 形状下 `_identify_try_except_regions` 对 TryExceptRegion@110 产出结构污染——**try_blocks=[158,160]**（实为 handler RERAISE 清理块；正确应为 try 体 110..132）、`except_handlers[ValueError].blocks` 混入 for/while 循环块（100/102/108/200/204/206）、**parent=IfRegion**（正确应为 LoopRegion@102 while / 其外层 for）、finally_copy={146,166}、cleanup=[]；随后 _coalesce/唯一 owner 分配把 for-latch 系（132/134/142/144/146/204）整体吞入该区域 → 生成层 `_generate_handler_body_statements` 无正确 handler 结构可依：臂体发射为乱序（`k -= 1 / k / continue / break / _run(k) / k -= 1`）、try 体 `_run(k)` 丢失（regen 61 instr vs orig 82）。**与 c04::CTryNest 同族**（`d:\Temp\opencode\r3dumps\pre\c04_findings.md` 候选 A-D 未实施）：等起点/近似起点配对捷径过宽（A）+ 内容块范围致层级失联（B/C/D）；修复须动配对/层级核心，语料面 e05/n2/n3/c4_03 高回归风险。**建议归 Round 8 统一处置**（或专项小批），以 c04_findings A-D 地图 + 本条 TryE@110 字段清单为起点；生成层局部补丁路线（fix1a–fix2d 六轮）已实测不可收敛，不再续走。
    - 影响面：m02 残余 `<module>` 1 红（域内红单元）；c04::CTryNest 维持 park（5/6）；其余队列不受影响（m06/x02 等按序推进）。

5. **[B133-V3R3]+[B134-V3R3] m06 双根因：if 臂 break 桥被清理预标记注销 + 内层 for 顺序后继吞父 while else**（m06 `<module>` 根因）
   - 根因（源：module 级 for/while 嵌套含三层 else 与 `if j: continue / else: break`）：
     - (b) 内层 for-j 的 `else: break` 蒸发（双缺陷叠加）：① 分析层 `_identify_conditional_regions` continue-sink 修正分支（then 臂按 JUMP_BACKWARD 回跳循环头识别）把 merge 直接置为 else_succ（@140），而 @140 是 [POP_TOP; JUMP_FORWARD → 循环出口] 的 break 纯桥 → 桥块成为 if 的 merge/post-if，`_collect_branch_blocks(entry==merge)` 返回空 else；② 生成层 `generate()` 清理尾声预标记（`_all_cleanup` 白名单含 POP_TOP/JUMP_FORWARD）把 @140 整体注销 generated → `_if_generate_else_branch` / `_process_if_blocks` 扫描时块已 generated，BREAK 角色分支不出 Break → j 假路径 fall-through 进 for-else（控制流改变）。
     - (c) while-else `TOTAL += 100`（@166）落入 while 体：内层 `_loop_generate_for` 的 break 落点清理处理 @154（=for-j 的 break 目标=父 while 回边重检块）后，把 @154 的顺序后继 @166（父 while 的 else 入口）当 post-loop 顺序代码发射进父循环体内 → while-else 语义破坏、重编译 CFG 分歧。
   - 判据（I.4 白名单，同层结构事实）：
     - [B133] 分析侧：else_succ 为纯清理跳桥（除结尾无条件 JUMP_FORWARD/JUMP_ABSOLUTE 外仅 POP_TOP/NOISE_OPS/EXTENDED_ARG，且跳转目标 ∉ `_loop.body_blocks`）时 merge 取跳转目标（break 落点=if 真实汇合点）；生成侧：块 ∈ 某 IfRegion.else_blocks ∧ 末条无条件跳转目标 == 该 IfRegion.merge_block ⇒ 豁免清理预标记，交 `_process_if_blocks` 按 BREAK 角色物化 `orelse=[Break]`（其余清理尾声维持原预标记，C3）。
     - [B134]：沿 `region.parent` 链存在生成中的祖先 LoopRegion（∈ `_generating_regions`）且后继 ∈ 其 else_blocks ⇒ 跳过发射与认领，else 块由祖先循环自身 else 归约路径处理。
   - 改动（3 处）：`core/cfg/region_analyzer.py` L22284-22316 段（continue-sink 分支，标 [B133-V3R3]）；`core/cfg/region_ast_generator.py` L2045-2071 段（清理预标记豁免，标 [B133-V3R3]）+ L7178-7199 段（祖先循环 else 守卫，标 [B134-V3R3]）。
   - 候选先行验证（CPython 3.11.7 编译对照）：`if j: continue / else: break` 与 `if j: continue; break` 编译逐位同构（compile+dis，equal bytes=True）→ 生成任一形态均可。
   - 验证读数：stamp=r3m06_fix2a **m06 0/1→1/1**（`<module>` 绿；`pyc_verify single` 1/1）；全量复跑零回归：r3m06_fix2a 44/54（m02 2/3、c04 5/6、c13 3/3、n9v9 6/6、x01 5/7、x02 5/7、x04 7/7、x08 6/8、v_b73_face 2/3、v_b75_face 2/3 逐位同基线）、r3m06_fix2b 56/57（r8_07 10/11 同基线；r10_04/r10_15/r10_21/rv10_32/r7_07/r7_08/r8_06 全绿）、r3m06_fix2c 41/45（r8_10 9/12、rv9_02 4/5 同基线；r8_08 9/9、rv8_01 7/7、rv8_02 7/7、rv9_01 5/5 绿）、r3m06_fix2d1/d2 29/40（a00..c17 梯度逐位同 m02 park 基线）。**负对照九件 60/60**（内嵌于 2b/2c 实跑）。

6. **[B87-V3R3] r08 子循环重入复检（x02::for_in_try 根因）**
   - 根因：`try: for i: try: for j: ... finally: ... except ...` 形状下，外层 LoopRegion@34 的体走查在 block@70 命中 r08 嵌套子循环路径（children 含 LoopRegion@70）；r08 守卫（9678）判定通过后执行 R58-A 前缀 flush——`_if_generate_branch_stmts([38,40])` → `_process_if_blocks` 看到 @40 是 TryExceptRegion 入口 → 整树生成 try@40 → 其 try body 派发（`_generate_try_body:33135`）**递归生成了同一 LoopRegion@70**（登记 `_generated_regions`）并把 `for j: R=j` 正确装配进 try 体；随后 r08 路径在 9716 行**无条件二次生成**子循环 → 体块已 marking、iter/target 仍可重建 → 产物幻影 `for j in range(1): pass`（重编译 FOR_ITER 落点 34→102 错位、异常表 5 条错位）。
   - 判据（I.4 白名单，纯登记状态 + 结构事实）：flush 是一次可能重入的同步调用，其后须以与守卫同词汇的登记集合（`_generated_regions`/`_generating_regions`）复检子循环是否已被 flush 副作用生成；仅拦截已发射者，未生成时行为逐位不变（C3）。
   - 改动（`core/cfg/region_ast_generator.py` 1 处，标 [B87-V3R3]）：L9716 前新增重入复检包裹 `nested_ast = ...` 发射（原无条件发射改为条件块内）。
    - 验证读数：stamp=r3q1a **x02 5/7→6/7**（for_in_try 绿；余 1 红 for_in_match 为域外 B? 不属本族，勿动）。邻域零回归：r3q1b（c04 5/6、m02 2/3、m06 1/1、x01 5/7、x04 7/7、c13 3/3 = 23/27 逐位同基线）、r3q1c（r8_07 10/11、x08 6/8、v_b73 2/3、v_b75 2/3、rv9_01 5/5、rv9_02 4/5 = 29/35 同基线）、r3q1d（负对照九件 60/60 + r8_08 9/9 + n9v9 6/6 + r8_10 9/12 同基线）。

7. **[B73-V3R3] finally 条件段副本头透明中继（v_b73::v_imp_cond_fin 根因）**
   - 根因：`try / except OSError as e: from m4 import fallback as fb; return fb(str(e)) / else / finally: from m6 import closer; if fh: closer(fh)` 形状下，CPython 3.11 把 finally 条件段复制进 handler 的 return 路径——副本头 @162（`import closer; LOAD fh; PJF→@202`）+ 副本体终块 @178（`closer(fh); RETURN_VALUE` 消费栈上遗留的 `fb(str(e))` 返回值）+ 条件假路 @202（裸 `RETURN_VALUE`）。`_generate_handler_body_statements(@94)` 的 leftover 经 `_find_return_chain_via_successors` BFS 找 return 链：@94→@152（SWAP 清理）→@154（POP_EXCEPT + as-var 清理）→@162 处断链——@162 含 IMPORT_NAME 等用户 opcode，`_is_cleanup_only_no_return` 拒绝、非 RETURN 终块 `_is_finally_copy_return` 拒绝 → BFS 返回 None ⇒ ① 返回值降级裸 `Expr(fb(str(e)))`（return 丢失）；② 副本块的 IfRegion@162 未被标记 generated，handler 臂循环（L35165）当真实嵌套结构 `_generate_region(IfRegion@162)` 再发射 → 幻影 `if fh: return closer(fh) else: return None`（finally 内容泄漏进 except 臂）。B75 前置机制（`_b75_consume_arm_return_copies`）对 IfRegion 候选的臂归属回溯要求透明块链直抵 CHECK_EXC_MATCH 分派块，本形态沿链穿过含用户语句的 @94 → 拒绝（且其值重建口径取自副本终块装载尾，无法取回 @94 的值表达式）。
   - 判据（I.4 白名单，同层结构事实）：新增 BFS 谓词 `_is_finally_copy_cond_head`——块 ∈ 某 has_finally 区域 blocks ∧ 不在其 try_blocks/finally_blocks ∧ 剥噪后块尾为条件跳转 ∧「剥 PUSH_EXC_INFO 头 + RERAISE/COPY/POP_EXCEPT/SWAP 尾后的异常副本头序列」与「本块剥噪序列（含同 opname 尾跳转）」逐项一致（CPython 复制 = 指令级同构，非名字/偏移启发）。命中后 BFS 视为透明中继继续展开后继；返回值由调用方 leftover 从原值块（@94）stmt_instrs 重建为 `Return`，路径块整体标记 generated（handler 臂循环跳过，副本 IF 区域不再发射）。
   - 改动（`core/cfg/region_ast_generator.py` 1 处共 2 hunks，均在 `_find_return_chain_via_successors` 内，标 [B73-V3R3]）：谓词定义（`_is_finally_copy_return` 之后）+ BFS 分支（`_is_finally_copy_return` 命中分支之后、`_is_cleanup_only_no_return` 之前）。
   - 验证读数：stamp=r3q2a **v_b73 2/3→3/3**（v_imp_cond_fin 绿；产物逐位 = 期望源：except 臂 `return fb(str(e))`、finally 单份正确发射；`pyc_verify single` units=3/3）。邻域零回归：r3q2b（x02 6/7、x01 5/7、x04 7/7、c04 5/6、c13 3/3、m02 2/3、m06 1/1、r8_07 10/11、r8_10 9/12、x08 6/8、v_b75 2/3、rv9_01 5/5、rv9_02 4/5、r10_04 3/3、r10_15 6/6、r10_21 4/4 = 78/91 逐位同基线）、r3q2c（负对照八件 62/62；含 r8_08 9/9、n9v9 6/6）。

8. **[B82-V3R3] try 臂 finally 条件段副本外置消费（v_b75::v_swap_arm_returns 根因）**
   - 根因：`try: return "miss" / except KeyError: return _CACHE[key] / finally: if _CACHE: print("hit")` 形状下，try 体无可抛指令 ⇒ CPython 3.11 不为 try 体生成异常表条目（handler_info 退化：try_start == handler_start == 58，[B102] 退化签名）⇒ 分析器 TryExceptRegion@58 的 try_blocks 退化为 handler 清理框架块 [154,156]，try 体块 [0,20,54]（finally 条件段副本：副本头 @0 条件 + 终块 @20/@54 各以 RETURN_VALUE 消费臂 return 值）被归约为区域外独立顶层 IfRegion@0。既有发射把 IfRegion@0 当真实 if/else 发包（幻影双臂：`if _CACHE: print('hit'); return 'miss' / else: return 'miss'`），Try.body 退化为 `pass`；B75 前置机制（`_b75_consume_arm_return_copies`）的成员门槛（块 ∈ region.blocks）与外部前驱守卫（函数头无前驱）双重拒绝，无法认领。
   - 判据（I.4 白名单，同层结构事实）：新增 `_consume_try_arm_finally_copy_if`（`_generate_region` IfRegion 分派处调用）——(a) parent=None 顶层 IfRegion 且块集与任一 TryExceptRegion.blocks 不相交；(b) 目标 T 满足 has_finally ∧ finally_blocks 非空 ∧ 未登记生成 ∧ 退化签名 T.entry ∈ handler_entry_blocks ∧ try_blocks 非空且全为框架 opcode；(c) 邻接：if 块全部偏移 < T.entry 且 CFG 块序中 T.entry 前一块 ∈ if 块集；(d) 同构：T.finally_blocks 剥噪 + 剥 PUSH_EXC_INFO 头 + 剥 RERAISE/COPY/POP_EXCEPT/SWAP 尾序列是 if 块剥噪 + 剥 RETURN 尾序列的严格真前缀；(e) if 内每个 RETURN 终块的装载尾（末个 POP_TOP/STORE 之后、RETURN 之前）可重建且彼此相等（比较时剥 lineno，不半应用）。命中后：IfRegion 块登记 generated + `_generated_regions` 不发射；臂 Return 挂 T 的 `_b75_try_arm_returns`（键 = try_blocks 首块偏移），由 `_generate_try_body` 既有 [B75] 认领点发射。
   - 改动（`core/cfg/region_ast_generator.py` 2 处，均标 [B82-V3R3]）：① `_consume_top_level_async_protocol_if` 之后新增方法；② `_generate_region` IfRegion 分派处新增调用（2 行）。
   - 验证读数：stamp=r3q3a **v_b75 2/3→3/3**（v_swap_arm_returns 绿；产物 = `try: return 'miss' / except KeyError: return _CACHE[key] / finally: if _CACHE: print('hit')`；v_b73 3/3 保持绿）。邻域零回归：r3q3b（x02 6/7、x01 5/7、x04 7/7、c04 5/6、c13 3/3、m02 2/3、m06 1/1、r8_07 10/11、r8_10 9/12、x08 6/8、rv9_01 5/5、rv9_02 4/5、r10_04 3/3、r10_15 6/6、r10_21 4/4 = 76/88，逐一 = 基线 r3q2b 同探针读数；失败单元名单逐项同基线）、r3q3c（负对照八件 62/62 = 基线）。

9. **[B56-V3R3] BoolOp 汇合块值延续 + RETURN 收尾（r8_07::r8_assert_nested_func 根因）**
   - 根因：`return inner(x) + (y or 0)` 形状下，短路链首块 @0 同时承载前导语句（`STORE_FAST inner`）与加法左操作数 `inner(x)`（PUSH_NULL/LOAD_FAST/PRECALL/CALL），首个 or 操作数 `y` 与 JUMP_IF_TRUE_OR_POP 在链首块尾；汇合块 @34 = [BINARY_OP, RETURN_VALUE] 把链值（或值）与残留栈 `inner(x)` 相加后返回。`_generate_boolop_impl` 无 value_target 路径只认「汇合块纯 RETURN（`_merge_is_return_only`）」，本形态落 `has_short_circuit_op` 兜底 → 发射 `Expr(y or 0)`：`return` 包装、`inner(x) +` 与 BINARY_OP 全部蒸发（r8_07 10/11）。
   - 判据（I.4 白名单，块内 opcode 形态）：① merge 块末为 RETURN_VALUE/RETURN_CONST 且 RETURN 前指令非空；② RETURN 前不含语句边界/控制/清理 opcode（STORE_* / POP_TOP / JUMP* / RETURN_* / RAISE* / RERAISE / POP_EXCEPT / PUSH_EXC_INFO / SWAP / COPY / WITH_EXCEPT_START / YIELD / SEND）= 纯值延续；③ 链首块前缀剥「最后 STORE 之前」后以 expr_reconstructor 取残留栈，栈顶（首个操作数）替换为完整 boolop_expr 作 initial_stack，重建 RETURN 前指令为完整表达式 → `Return(expr)`；重建失败逐位退回既有 `Expr(BoolOp)` 兜底（C3，无半应用）。
   - 改动（`core/cfg/region_ast_generator.py` 1 处，`_generate_boolop_impl` 无 value_target 值的 `has_short_circuit_op` 分支内，标 [B56-V3R3]）。
   - 验证读数：stamp=r3q4a **r8_07 10/11→11/11**（r8_assert_nested_func 绿；产物 `return inner(x) + (y or 0)`）。邻域零回归：r3q4b（16 探针 72/83，逐一 = r3q3a/r3q3b 同探针读数：x02 6/7、x01 5/7、x04 7/7、c04 5/6、c13 3/3、m02 2/3、m06 1/1、r8_10 9/12、x08 6/8、rv9_01 5/5、rv9_02 4/5、r10_04 3/3、r10_15 6/6、r10_21 4/4、v_b73 3/3、v_b75 3/3；失败单元名单同基线）、r3q4c（负对照八件 62/62 = 基线）。

10. **[B134-V3R3] while 条件链外部前驱须有体内重检证据（x08::assert_leaf / return_leaf 根因）**
    - 根因（分析层）：`if i: while <cond>:` 的 if 假出口与 while 假出口编译为同一块，`_detect_while_condition_boolop_chain` 后向回溯把外部 if 条件块当作 and 链首操作数吸收 → BoolOpRegion `while i and i` 抹掉外层 IfRegion（x08 6/8；assert_leaf/return_leaf 均此形态）。
    - 判据（`_while_pred_has_body_retest`，同层结构事实）：循环体外前驱吸收前，其谓词序列（去噪、最后一个 STORE_* 之后的 `(opname,argval)` 序列）须与 `loop.body_blocks` 某块同段序列相等、跳转极性相同，且该重检块跳转方向离开循环（目标 ∉ loop.blocks 且 ≠ header）——体内嵌套 if 的同极性测试（跳转仍落体内）不构成条件重检；无证据即中断回溯，首块交还 IfRegion（if 体由循环子区域承载）。合法 B11 前缀（`j = 0; while j < i and ...`）在体内有假边→出口的同谓词重检块，逐位保持。
    - 改动（`core/cfg/region_analyzer.py` 2 处：新方法 `_while_pred_has_body_retest` + `_detect_while_condition_boolop_chain` 后向回溯吸收点 1 个守卫，均标 [B134-V3R3]）。
    - 验证读数：stamp=r3q5a **x08 6/8→8/8**（assert_leaf / return_leaf 绿；产物 `if i: / while i:` 层级恢复，`assert i or 1` 与隐式函数尾 return 编译字节等价）。邻域零回归：r3q5b（16 探针 77/86 = r3q4b 72/83 + r8_07 +1 + x08 移出本组；逐探针 = 基线：x02 6/7、x01 5/7、x04 7/7、c04 5/6、c13 3/3、m02 2/3、m06 1/1、r8_07 11/11、r8_10 9/12、rv9_01 5/5、rv9_02 4/5、r10_04 3/3、r10_15 6/6、r10_21 4/4、v_b73 3/3、v_b75 3/3；失败单元名单同基线）、r3q5c（负对照八件 62/62 = 基线）。

11. **[B135-V3R3]+[B136-V3R3] assert 失败臂退化 IfRegion 归约 + 条件 preload 跳过栈效应门（r8_10 双红根因）**
    - 根因 (a) `r8_x_assert_ternary`（源 `assert (a if t else b) < 10`）：条件内含三元时 AssertRegion 未收纳该 assert，退化为 IfRegion（then=@22 `LOAD_ASSERTION_ERROR; RAISE_VARARGS 1`，无 else；条件块 @12 经 TernaryRegion@0 重建）→ 既有路径发 `if not (a if t else b) < 10: raise AssertionError`，AssertionError 以 `LOAD_GLOBAL` 装载而非 `LOAD_ASSERTION_ERROR`（pyc_verify "Different bytecode"）。
    - 根因 (b) `r8_x_raise_ternary_class`（源 `raise (ValueError if x > 0 else TypeError)("ternary exception class")`）：cond 块 @0 的 `PUSH_NULL` 属于 merge@42 的 CALL（callee = 三元结果），而两处 preload 跳过启发式都把 `PUSH_NULL; LOAD_FAST x` 当外层调用 callee 前缀剔除（`func_call_skip` / [Round3 fix] `_fci` 分支），条件只剩 `COMPARE_OP` 的残缺片段 → `cond_expr=None` → 整个 TernaryRegion 返回 None（产物仅 `pass`，语句蒸发）。
    - 判据 (a)（I.4 白名单，同层结构事实）：IfRegion 无 else 臂、then 臂恰一块、块内有效指令首 `LOAD_ASSERTION_ERROR`、末 `RAISE_VARARGS 1`（msg 指令在两者之间，过滤 PRECALL/CALL/PUSH_NULL/NOP/CACHE/RESUME 后重建）⇒ 条件沿用本区域既有重建链（前置语句 + `_if_extract_condition_from_instructions`，三元子区域随其生成），`Assert(test=_negate_expr(condition))`（If 测试恒为 assert 测试的取反，`_negate_expr` 剥一层 not 精确还原，`assert x` 的 IF_TRUE 极性与 `assert not x` 的 IF_FALSE 极性由跳转语义自然吸收）；msg 槽同上重建。
    - 判据 (b)（纯栈效应）：preload 跳过后的剩余条件段净栈效应须恰为 +1（压入一个测试值）；效应可计算且 ≠1 时复位跳过，让完整条件留在 `cond_instrs` 中重建（效应不可得时保持既有行为，C3）。本形态剩余段仅 `[COMPARE_OP]`（净 -1），preload 假说被否证；`_raise (V if c else T)(msg)` 的 `Raise` 由既有 `_build_ternary_no_target_consumer_stmt` Pattern 2（merge PRECALL+CALL）重建。
    - 改动（`core/cfg/region_ast_generator.py`，均标 `[B135-V3R3]`/`[B136-V3R3]`）：① `_generate_if` 前新增 `_try_emit_assert_from_if_region` + 分派点（B78 宿主检查之后、IF_ELIF_CHAIN 之前）；② 单块条件 `func_call_skip` 扩展后新增净效应守卫（B136）；③ [Round3 fix] `_fci` preload 跳过段内新增同一净效应守卫（B136）。
    - 验证读数：stamp=r3q6a **r8_10 9/12→11/12**（`r8_x_assert_ternary` / `r8_x_raise_ternary_class` 双绿；余 `r8_x_for_iter_ternary` 为域外 B57，勿动）。邻域零回归：r3q6b（16 探针 79/86 = r3q5b 77/86 + r8_10 +2；逐探针 = 基线：x02 6/7、x01 5/7、x04 7/7、c04 5/6、c13 3/3、m02 2/3、m06 1/1、r8_07 11/11、r8_10 11/12、rv9_01 5/5、rv9_02 4/5、r10_04 3/3、r10_15 6/6、r10_21 4/4、v_b73 3/3、v_b75 3/3；失败单元名单同基线）、r3q6c（负对照八件 62/62 = 基线）。

12. **[B 门禁] 合成变体（每修复族 ≥2）全绿**
    - 生成：`test_repros/round3/rec1_synth_*.py|.pyc`（stage = `.trae/specs/attain-true-completeness/test_repros/round3/`），22 探针覆盖 11 族：B87-NOP a/b（try 内 `if 1:` 常量语句头）、B69 a/b（if 臂 try-finally + 后续 return/else）、B131 a/b（`if: while True: if/break/else`）、B133 a/b（嵌套 for/while-else + if/continue/else/break）、B87-r08 c/d（for 内 try-for-finally + 外层 except）、B73 a/b（except 内 import + 返回消费 + finally 条件副本）、B82 a/b（无抛 try 体 + except 返回 + finally 条件副本）、B56 a/b（STORE 前缀 + boolop 汇合 return 装箱）、B134 a/b（`if i: while i:` 同变量体突变）、B135 a/b（assert 条件含三元 + `not` 极性）、B136 a/b（raise 三元类，0 参/2 参调用）。
    - 读数：stamp=r3sb3 **22 探针 45/45 全绿**（r3sb1 23/24 → b133b 重拟定 → r3sb1b 绿；r3sb2 20/21 → b134b 重拟定 → r3sb2c 绿，终态 r3sb3 一并复验）。
    - 残余观察（不在门禁范围，未追）：① `for i: while <i>: if i==2: continue else: break; else: <stmt>`（while 条件 + if/continue/else/break + while-else 三合一）仍红；② `if i: while i and i < 10: i += 1` / `if i: while j and i: j -= 1`（外层 if 与 while 条件链共享假出口且体内有谓词重检）仍红。②经 [B134] 守卫中和复跑（`preb134_regen.py`，`_while_pred_has_body_retest`→True 模拟修复前）产物逐位相同 ⇒ **修复前既有问题、非本轮回归**；两形均归后续轮次统一处置。

13. **[B134-V3R3 修订] 守卫两处收紧误杀（E 门禁首次全量暴露）**
    - 暴露：E 门禁首跑 6616/6617（shard6 `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` 127/128，compare 见 REGRESSIONS）；同轮 `future_positionOK.py` 字节差分 +42/−27（语义等值但非零字节一致，两项均须清）。
    - 根因（`_while_pred_has_body_retest` 两处误判）：
      ① **体内语句与重检同块**：CPython 3.11 单语句循环体把体语句（`time.sleep(5)`）与操作数 1 的重检复制并入同一基本块（体语句前缀 + 谓词后缀），原判据 `bseq == seq` 全等失败 → 合法链首被拒（trade_live_broker 两个 while 链拆分、外提成 `if A: while B:` 错形）。修：谓词序列改为**后缀匹配**（`len(bseq)>=len(seq) and bseq[-len(seq):]==seq`）；x08 形态由极性/出口判据另行排除。
      ② **出口块并入 loop.blocks**：循环退出块与外层 if 合并（同时是外层 IfRegion 的 merge）时被 LoopRegion 一并纳入 `loop.blocks`，原判据 `_rt_jt in loop.blocks → continue` 误杀（future_position._close_holding 三个 while 链拆分）。修：「迭代内成员」判定改用 `body_blocks ∪ {header, condition_block, back_edge_block}`，嵌套 if 同极性跳转（目标为体内块）仍排除。
    - 复核：trade_live_broker 单验 **128/128**、`future_positionOK.py` 单验 **83/83** 且 `git status --porcelain site-packages/` 归零（字节复原）；安全组 r3q7a（x08 8/8、b11 2/2、b134a/b 2/2、r8_10 11/12 仅域外 B57）25/26；B 门禁全量重跑 r3sb4 **45/45**；负对照重跑 r3q7b **62/62**。
    - E 门禁终跑（`final_verify_run_r3.py`，524.7s）：8 分片全 success **6617/6617**、compare×8 **REGRESSIONS=0**；small34 **1568/1568 REGRESSIONS=0 IMPROVED=33**；quotation **153/153**；tests 七套件 **2 failed / 282 passed / 2 xpassed**（名单 = test_B01_simple_if_then_else_merge + test_BOUNDARY_02_large_function，同基线）；IV.2 全绿（BOM 单头 efbbbf、import/compile OK、插桩 code 命中 0、G3=0）；site-packages **零字节差异**（`git status --porcelain site-packages/` = 0 行）。

## §2 变更清单（终稿）

文件 2 个（`git diff ece1aab5 --numstat -- core/cfg`）：

| 文件 | 增/删 | 标记（`[Bn-V3R3]`） |
|---|---|---|
| `core/cfg/region_ast_generator.py` | +598 / −11 | 19 处：B56 / B69 / B73 / B82 / B87 / B131 / B133 / B134 / B135 / B136 |
| `core/cfg/region_analyzer.py` | +138 / −2 | 6 处：B131 / B133 / B134 |

合计 **+736 / −13，25 hunks**（`git diff ece1aab5 --unified=0 -- core/cfg`）；落地标记 `[Bn-V3R3]` 共 **25 处**。

机制清单（§1 条目 → 标记 → 触面）：
1. B87 try 体 NOP 保真（`_is_protected_statement_nop` + 块遍历/发射）；2. B87 后续块遍历补丁；3. B87-r08 for 内 try-for-finally 宿主（`_consume_try_arm_finally_copy_if`）；4. B73 except 四段 import 宿主；5. B75/B82 `_b82_norm` 臂返回等值 + finally 条件副本消费；6. B56 STORE 前缀 + boolop 汇合 return 装箱；7. B131 `if: while True: if/break/else` 折叠；8. B133 嵌套 for/while-else + if/continue/else/break 归属；9. B134 `if G: while C:` 出口前驱守卫（`_while_pred_has_body_retest`）；10. B63 空 try/fin 尾随段；11. **B135** assert 失败臂 IfRegion → `Assert(not cond, msg)`（`_try_emit_assert_from_if_region`）；**B136** preload 跳过栈效应门（`raise (V if c else T)(msg)`）；12. B 门禁合成变体（证据节）；**13. B134 修订**：谓词序列后缀匹配（体内语句与重检同块）+ 出口块并入 loop.blocks 的迭代内成员判定。

白名单/纪律：新增全为通用结构判定，无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀（G3=0）；无插桩代码命中（G4=0）；仅改 `core/cfg/**`。

## §3 前后读数（终稿）

- 复现基线（§0）：r3pre1a 13/17、r3pre1b 17/25、r3pre2 23/29、r3pre2b 23/25、r3pre3 39/39、r3pre3b 21/21；与 round1 逐位一致、零 pass→fail。
- 终态：§0「终态读数」表——R3 域内红单元 12/12 翻绿（另含 r8_10 双红 9/12→11/12），park 2 项维持，域外项如实维持。
- 邻域（r3q6b，16 探针 77/86→79/86）：x02 6/7、x01 5/7、x04 7/7、c04 5/6、c13 3/3、m02 2/3、m06 1/1、r8_07 11/11、r8_10 11/12、rv9_01 5/5、rv9_02 4/5、r10_04 3/3、r10_15 6/6、r10_21 4/4、v_b73 3/3、v_b75 3/3；失败单元名单同基线（逐项=基线 + r8_10 +2）。
- 负对照（r3q6c / r3q7b，八件）：62/62 = 基线（r7_07 7/7、r7_08 8/8、rv8_01 7/7、rv8_02 7/7、r8_06 10/10、r8_08 9/9、n9v9 6/6、rv10_32 8/8）。
- 安全组（r3q7a）：x08 8/8、b11 2/2、b134a/b 2/2、r8_10 11/12（余 1 = 域外 B57）= 25/26。

## §4 复核（终稿）

- 原探针全量：§0 终态表（stamp=r3q6b 邻域 + r3q7a/r3q7b 复跑），逐探针 ≥ 基线；修复项逐单元证绿。
- 合成 B 门禁：22 探针 45/45（r3sb4；r3sb1 23/24→b133b 重拟定→r3sb1b；r3sb2 20/21→b134b 重拟定→r3sb2c）。
- 交叉变体/负对照/邻域：§3 各项。
- 字节复原核验：`trade_live_brokerOK.py` 128/128 + 恢复提交版字节、`future_positionOK.py` 83/83 + 恢复提交版字节（[B134] 修订两处后 `git status --porcelain site-packages/` = 0）。
- 残余观察登记（域外/后续轮）：B57 `r8_x_for_iter_ternary`；x01::if_in_while（R6/B94）、x01::if_in_match（R5/B122）、rv9_02::while_with_whole_body（B70）；`if i: while i and i < 10:` / `if i: while j and i: j -= 1`（外层 if 与 while 链共享假出口且体有重检；经修复前对照复跑产物逐位相同 = 既有问题非本轮回归）；`for i: while <i>: if i==2: continue else: break; else:`（while 条件三合一残余）。

## §5 门禁读数（终稿）

| 门禁 | 读数 | 证据 |
|---|---|---|
| 402 八分片 | 8 shard 全 success，**6617/6617**，compare×8 **REGRESSIONS=0**（cap 786/469/538/887/855/999/801/1282） | `rounds/round3/final_verify_log.txt`、`final_verify_summary.json`、`shardN_report_new.json` |
| small34 | **1568/1568**，REGRESSIONS=0 IMPROVED=33 | `small34_report_new.json` |
| quotation | **153/153** | `final_verify_log.txt` QUOTATION |
| tests 七套件 | **2 failed / 282 passed / 2 xpassed**（名单 = test_B01_simple_if_then_else_merge + test_BOUNDARY_02_large_function，同基线） | `final_verify_log.txt` TESTS7 |
| IV.2 | IMPORT_OK、COMPILE_OK、BOM 单头 efbbbf×2、插桩 code 命中 0、G3=0、G4=0、AST ok | `r3_fv_iv2.json` / `final_verify_summary.json` |
| site-packages | 零字节差异（`git status --porcelain site-packages/` = 0 行） | 同上 |
| D（承重面 trade_info_utils） | regen 41/41、零差异 | `trade_info_utilsOK.py` |

命令：`python -X utf8 .trae/specs/attain-true-completeness/rounds/round3/final_verify_run_r3.py`（524.7s）、`iv2_recheck_r3.py`、`verify_driver.py regen/verify/compare <n>`、`verify7_split.py`。

## §6 落地声明（终稿）

- 落地范围：工作树未提交；改动仅 `core/cfg/region_ast_generator.py`（+598/−11）与 `core/cfg/region_analyzer.py`（+138/−2），及本规范目录新增（`rounds/round3/**`、`test_repros/round3/**`）。`site-packages/**`、`test_repros/**`、`wiki/**`、`tests/**`、`scripts/pyc_verify.py` 无提交面差异（产品为 regen 覆盖、与提交版逐位一致）。
- 判据与复现：RV2 口径（`pycdc.py -o` regen → `pyc_verify.py single`）；探针 stamps：r3pre1a-3b（基线）、r3q6a/b/c（r8_10 修复）、r3q7a/b（修订复核）、r3sb1b/2c/4（B 门禁）；E 门禁编排与证据见 §5。
- 结论：R3（tasks.md Task 3）修复完成，域内全绿、零回归、五门禁全过；park 2 项与域外残余已登记（§0/§4）。
