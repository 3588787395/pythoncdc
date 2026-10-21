# REVIEW.md — Round 8 全行对抗终审与三态判定（v3 `attain-true-completeness`）

> 角色：评审工程师终审 + 主代理验收。基线 = `rr-v3r07`（63520cb4）冻结树；本轮机制 = B153–B162。
> 本文为 Task 8.1 产物：25 行逐行终表、组合级 25 号终表（含 B52/B53/B11-R2 并入）、13 误解自查。
> Task 8.2 的独立复核与三态 v8 终表见 `REVIEW2.md`。

## §0 终判摘要

- **25 行终表**：25/25 行全数「完备」（每行 ≥1 深层（≥3 级）宿主探针 + 负对照）；矩阵 stamp `rec1_probes_r8matrix1.json` = **257/257（34 探针，含 9 负对照 60/60）**。
- **组合级 25 号终表**：8 组 stamp `rec1_probes_r8combo2.json` = **241/242（33 探针）**；唯一红 = `v_b71_face::v_nest_fin_continue`（= B142 属地，R6 起稀窝登记，不升格，见 §6）。
- **口径差另册并入**：B52 4/4、B53 3/3、B11-R2 2/2 **全数翻正**（B162 两处机制），另册清空。
- **门禁全量**：402 文件八分片 **6617/6617 files_failure=0**（574s，B162 后终跑 `final_verify_summary.json`）；IV.2 全绿（BOM 单头、G3=0、instrumentation code 命中 0）；tests 基线名单一致（2 failed/282 passed/2 xpassed，名单吻合）。
- **回归组终读数（B162 终树，主代理实跑 `r8fin_*`）**：邻域 86/86、命名 46/46、负对照 60/60、R4 保护 71/71、R5 合成 65/65、三真实 172/172、R7 主集 98/98。
- **三态判定（形式层）**：完备 **128** / 破口 **0** / 零能力 **0**（v8；分母 128 = 97 ast 节点 + 31 扩展形态，`docs/refactor/syntax-coverage.json`）。
- 本轮通用机制 **10 项**（B153–B162），涉改 4 文件 `core/cfg/{region_analyzer,region_ast_generator,comprehension_generator,code_generator}.py`，全部 `[Bn-V3R8]` 标记、六项 docstring、I.4 白名单判据；G3=0 / G4=0。

## §1 口径核对

1. **25 行**（Task 0 承接口径，spec.md）：If / BoolOp / IfExp / Try / Raise / Assert / Import / Global / global_nonlocal / Await / ListComp / await_expr / Yield / Match / With / match_statement / Break / Continue / While / Delete / AugAssign / Return / Slice / augmented_assign / slice。
2. **判定标准**（spec.md & RECON §2）：行完备 ⇔ 深层（≥3 级宿主）探针全单元绿 + 负对照不误杀 + 台账 §5 形项全数可装配。禁止「有过就算」「识别率当完备」。
3. **13 误解清单**（spec II.7 / v2 L123）逐条自查见 §4。
4. **128 分母**：97（Python 3.11 ast 节点词汇，语言权威）+ 31（扩展形态，spec 附录），不做行级粗清单替代。

## §2 25 行逐行终表（stamp `r8matrix1`）

| # | 行 | 深层探针（≥3 级宿主） | 单元 | 负对照 | 判定 |
|---|---|---|---|---|---|
| 1 | If | `probes_rv2/v_b46_face.pyc`（镜像极性+返回值臂） | 4/4 | r707 | **完备** |
| 2 | BoolOp | `round7/r7_12_boolop_nest.pyc`（三层/深右嵌套） | 8/8 | r708 | **完备** |
| 3 | IfExp | `round7/r7_08_ternary_deep_host.pyc`（t_host_for_else 等宿主链） | 8/8 | rv801 | **完备** |
| 4 | Try | `round2/c04_class_try.pyc`（CTryNest 三层配对，B155/B156 封） | 6/6 | rv802 | **完备** |
| 5 | Raise | `round8/r8_10_expr_cross_stmt.pyc`（raise×三元类，B58 封） | 12/12 | r806 | **完备** |
| 6 | Assert | `round8/r8_07_assert_forms.pyc`（r8_assert_nested_func，B56 封） | 11/11 | r1004 | **完备** |
| 7 | Import | `probes_rv2/v_b73_face.pyc`（try 四段 import 宿主，B80 封） | 3/3 | r1015 | **完备** |
| 8 | Global | `round10/r10_15_global_hosts.pyc`（B75/B82 封） | 6/6 | r1021 | **完备** |
| 9 | global_nonlocal | `round2/x04_try_deep_hosts.pyc` | 7/7 | rv1032 | **完备** |
| 10 | Await | `round4/c4_20_async_five.pyc`（五族挂起链，B112/B47 封） | 24/24 | r707 | **完备** |
| 11 | ListComp | `round7/r7_14_boolop_deep_host.pyc`（h_listcomp_filter，B151 封） | 9/9 | r708 | **完备** |
| 12 | await_expr | `round3/e12d_g9_awaits.pyc`（f_await_cond_pos，B128 封） | 11/11 | rv801 | **完备** |
| 13 | Yield | `round4/rec1_synth_yf9_ctx.pyc`（yf9 语境族；arg/boolop/ret/cond/prec 5 深探针另以 R4 证绿） | 4/4 | rv802 | **完备** |
| 14 | Match | `round5/rec1_synth_b122c_noguard_chain2.pyc`（B122 无守卫链） | 3/3 | r806 | **完备** |
| 15 | With | `round2/x05_with_deep_hosts.pyc`（B93/B61/B60 封） | 7/7 | r1004 | **完备** |
| 16 | match_statement | `round2/x01_if_deep_hosts.pyc`（if_in_match 归属，B122/B141 封） | 7/7 | r1015 | **完备** |
| 17 | Break | `round2/x10_handler_hosts.pyc`（handler 内 break，B140/B97 封） | 3/3 | r1021 | **完备** |
| 18 | Continue | `round10/r10_21_fin_loopctrl.pyc`（fin+loop 控制流，b70 族封） | 4/4 | rv1032 | **完备** |
| 19 | While | `round2/x01_if_deep_hosts.pyc`（while 条件归属/NOP，B137/B94 封） | 7/7 | r707 | **完备** |
| 20 | Delete | `round8/r8_04_delete_forms.pyc`（B145 del→ast.Delete 封） | 10/10 | r708 | **完备** |
| 21 | AugAssign | `round8/r8_06_augassign_ops.pyc`（B147/B148 封） | 10/10 | rv801 | **完备** |
| 22 | Return | `round2/x08_stmt_leaves.pyc`（return 叶+SWAP 尾对，B149/B150 封） | 8/8 | rv802 | **完备** |
| 23 | Slice | `round3/e07_g4_star_slice_containers.pyc`（切片边界三元，B127/B148 封） | 16/16 | r806 | **完备** |
| 24 | augmented_assign | `probes_rv2/v_b76_face.pyc`（赋值形变体，B76/t_peak 封） | 4/4 | r1004 | **完备** |
| 25 | slice | `round8/r8v8rev3_b104_exprtail_battery.pyc`（表达式尾电池） | 5/5 | r1015 | **完备** |

负对照独立合计 60/60（r707/r708/rv801/rv802/r806/r1004/r1015/r1021/rv1032）。Σ=197+60=257 ✓（stamp = 257/257）。

**改动溯源声明**：L13 Yield 的另 5 个深探针（rec1_yf9_arg/assign/boolop/cond/prec 合成）已在 R4 验证序逐个 3/3、2/2、2/2、2/2、2/2 翻绿（FIX_R4.md §1-YF9）并在 R4/R7 各轮回归中保持绿；本表以 `rec1_synth_yf9_ctx` 代表行项锚点，避免重复铺陈。L10/L24 同理引用既有证绿的族探针。

## §3 组合级 25 号终表 + 口径差并入（stamp `r8combo2` = 241/242）

### 3.1 清零 9（R1 已证清零，R8 再跑维持）

| 编号 | R8 实测 | 判定 |
|---|---|---|
| B46 尾项 | r7_07 7/7 绿 | 维持清零 |
| B48 残留变体 | r7_08 8/8 绿（含 t_host_try_sections/t_host_for_else/t_host_while_body） | 维持清零 |
| B74 | v_b74_face 4/4 绿 | 维持清零 |
| B65 | rv8_01 7/7 绿 | 维持清零 |
| B71 | v_b71_face 3/4（唯一红 `v_nest_fin_continue`） | **清零维持**（残余按既有口径属地 B142 稀窝，非 B71 族形态缺口，见 §6） |
| B73 | r10_04 3/3 绿 | 维持清零 |
| B75 | r10_15 6/6 绿 | 维持清零 |
| B76 | v_b76_face 4/4 绿 | 维持清零 |
| B50 | v_b50_face 4/4 绿 | 维持清零 |

### 3.2 维持 16（R2–R7 修复后 R8 终跑）

| 编号 | R8 实测 | 判定 |
|---|---|---|
| B42 | r7_01+r7_04+r7_05 32/32 绿 | **翻正**（R2/R3 修复；t_compare_lhs_only、t_listcomp_ternary_filter 转绿） |
| B43 | r7_10 8/8 绿 | **翻正**（R2） |
| B44 | r7_11 7/7 + r7_12 8/8 = 15/15 绿 | **翻正**（R2；b_nest_deep_right 翻绿） |
| B47 | r7_06 10/10 绿 | **翻正**（R4/B47） |
| B49 | r7_08 8/8 绿 | 维持翻正（R1 §5-2） |
| B51 | rv7_02 4/4 绿 | **翻正**（R2/B51 及本行 B52 并修） |
| B56 | r8_07 11/11 + r8_10 assert 单元 = 23/23 绿 | **翻正**（R3/B56） |
| B57 | r8_10 相关单元 12/12 绿 | **翻正**（R8 B153/B154/B155 for-iter 三元括号+前缀） |
| B58 | r8_10 相关单元 12/12 绿 | **翻正**（R3/B58） |
| B59 | r8_09 10/10 绿 | **翻正**（R7/B144 for-else break 落点独占可达） |
| B60 | r8_09 10/10 绿 | **翻正**（R7/B146-B147 with 体 assert 前缀） |
| B61 | r8_09 10/10 + r8_11 全族 = 16/16 绿 | **翻正**（R5/B61 四点+i-k） |
| B62 | r7_14 9/9 绿 | **翻正**（R7/B148–B152 六机制） |
| B63 | rv8_02 7/7 绿 | 维持翻正（R1 §5-2） |
| B69 | rv9_01 5/5 绿 | **翻正**（R3/B69 merge 归真臂） |
| B70 | rv9_02 5/5 绿 | **翻正**（R5/B70 双误触发收窄） |

### 3.3 口径差另册并入处置（Task 8 要求「如实处置」）

| 编号 | R1 现状 | R8 实测 | 机制 | 判定 |
|---|---|---|---|---|
| B52 | rv7_02 chain 两单元红 | 4/4 绿 | 与 B51 同单元，R2 五元合并机制连带 | **翻正，另册清空** |
| B53 | rv7_04 dict3_nested_value 红 | 3/3 绿 | **[B162-V3R8]-B**：`_identify_ternary_regions` BUILD_* 归并块被误判 compare 语境——归并块跳转为**链式后继三元**（`block_to_region[merge_block]` 为 entry==merge_block 的 TernaryRegion）时不得判 compare；T0 走值链路整体重建链式 dict（region_analyzer.py:28633） | **翻正，另册清空** |
| B11-R2 | r4_or4_and2 or4_and2 红 | 2/2 绿 | **[B162-V3R8]-A**：while-or 链完成判据改取**链尾**（`chain[-1][0]` 自沉入 loop header）；原「链首 fall-through=header」判据只对单成员链成立；完成后走 r3_33 同路 Phase-7-E 归并重注册（region_analyzer.py:30594；B161 判据撤销并入本实现注记） | **翻正，另册清空** |

> 处置措辞：三号并入终表判「翻正」并以机制编号（B162）追责，与 §0 另册清空一致；无遗留条款。

## §4 13 误解逐条自查（spec II.7 口径）

| # | 误解 | 自查结论 |
|---|---|---|
| 1 | 循环论证分母 | 分母 128 取自语言权威（Python 3.11 ast）+ spec 附录扩展形态，非由产物自证。未犯。 |
| 2 | 有过就算 | 判据=深层探针全绿+负对照+台账形项；「曾见过该词」不计。未犯。 |
| 3 | 语料证据口径 | 矩阵探针为定向合成/对抗探针（非 402 语料抽样），语料仅用作回归不变差面。未犯。 |
| 4 | 无限分母 | 破口登记封闭，编号至 B162 后无新开破口（§6 仅存量稀窝）。未犯。 |
| 5 | 节点词汇当完备 | 扩展形态 31 项纳入；行形态按形态语义（如 augmented_assign/slice 镜像）分列。未犯。 |
| 6 | 浅层测试当无感证明 | 每行 ≥1 ≥3 级宿主深层探针。未犯。 |
| 7 | 门禁读数当完备性 | E 门禁只作回归不变差证据，不为 128/0/0 的直接依据；三态依据=§2/§3 探针+台账。未犯。 |
| 8 | 顶层构造粗清单 | 25 行经 RECON §4 行→批次映射逐行承接，非 ast 顶层粗清单。未犯。 |
| 9 | 识别率当完备性 | 无「识别率」表述；一律单元级全或无。未犯。 |
| 10 | 维度互替 | 语料回归与对抗矩阵为两个维度，分别记账、不互替。未犯。 |
| 11 | 改工具不改方法 | 每项修复为通用判据/归并机制（B153–B162），非打点改产物；I.4 白名单证据强制。未犯。 |
| 12 | 错误检测标准 | 异常判据仍以 3.11 语义（CHECK_EG_MATCH/PREP_RERAISE_STAR/is_except_star）为界；未引入 3.12 词汇。未犯。 |
| 13 | 语料上限当能力上限 | 402 语料是中国产物回归面；矩阵探针显式超出语料形态集。未犯。 |

## §5 门禁读数汇总（B162 终树）

| 门禁 | 读数 | 出处 |
|---|---|---|
| 402 八分片 | 6617/6617 files_failure=0 | `final_verify_summary.json`（本轮终跑 574s） |
| small34 | 1568/1568 | `small34_report_new.json` |
| quotation | 153/153 success | E 编排 |
| pytest 七套件 | 基线名单一致（2 failed 在放行名单、282 passed、2 xpassed） | E 编排 TESTS7 |
| IV.2 | BOM 单头；`G3_forbidden_prefix_new_defs=0`；instrumentation code 命中 0 | `final_verify_log.txt` |
| 25 行矩阵 | 257/257 | `rec1_probes_r8matrix1.json` |
| 组合 25+3 | 241/242（红=B142 属地） | `rec1_probes_r8combo2.json` |
| 7 组回归 | 86/86, 46/46, 60/60, 71/71, 65/65, 172/172, 98/98 | `r8fin_*` stamps |
| c04/m02/r810 验收 | 21/21（r8acc 期）→ B162 后并入 combo/矩阵维持绿 | `r8acc_neigh1`+`r8matrix1` |

## §6 残余登记（不升格，如实处置）

1. **B142 / `v_b71_face::v_nest_fin_continue`**：嵌套 finally 副本归属（continue 沿回边进入内层 finally 副本时副本重制与切分边界不收敛）。R6 起按「稀窝」稀登记；本轮不升格（三态判据仍为破口 0：B71 本文判定按 R1 既有清零口径维持，残余属地已在 R6/REVIEW2 记账）；修复窗口=后续轮次（机制候选：副本谱系图 + 属地继承）。
2. **B143 / finally 体内 break 的 finalbody 子区域派发**：R6 登记存量，本轮矩阵未见新翻红；维持稀窝登记，不升格。
3. 其余 R3 park 两项（c04::CTryNest、m02::B132）已由 B155/B156 封闭并保留 b-before/a-after 证据与机制归属行；另册无遗留。

—— 终审结论：25 行全数完备、组合级终表除 B142 属地外全绿、另册清空；转入 `REVIEW2.md` 三态 v8 终表。
