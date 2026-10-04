# Round 1 评审报告（Task 1.1）—— round10 终态承接复验

- 评审角色：对抗性独立审计（只读）。零 core/ 修改、零 wiki/ 修改、零 test_repros/ 既有文件修改、零 git 提交。
- 判据工具：`scripts/pyc_verify.py`（ruler = pylingual-equivalence_check，compare_pyc_sha256 = 9c7567bd6776b36b），解释器 3.11.7。
- 树状态：HEAD = `8236b6a0`（rr-v2r00b 承接事实修正）；`git status --porcelain` 仅 7 个 untracked 文件，全部位于本目录（rounds/round1/，本轮工作产物）——core/、wiki/、test_repros/ 零在途变更。
- 实测证据（本目录）：
  - `tmp_probe_report.json`（15:23，21 文件 141/171：预跑探针面）
  - `r1_residual_replay.json`（16:27，72 文件 404/446：round4+round7 全 20 文件+round8 全 16 文件+round9 全 15 文件+round10 全 20 文件）
  - `r1_sentry_replay.json`（16:29，24 文件 417/423：round6 全 16 pyc + 六哨兵 + option_account + quotation）
  - 三份报告 ruler sha 与 round10 终审一致（9c7567bd6776b36b），同树（无 core 提交介入）读数可直接对比 round10 终态。

---

## §0 终判摘要

| 项 | 结论 |
|---|---|
| A. v6 口径核对 | **通过**：syntax-coverage.json 128/128；wiki 五页 v6 数字一致（形式层 128/0/0=100%、组合级挂账 25 号、6 组零专攻）；台账锚点抽查 16 处语义全部在树相符，存在系统性行号漂移（+1~+2784，round10 修复插入所致，台账自声明锚点为 2026-09-29 快照，不构成矛盾数字/伪锚点，移交重锚） |
| B. 残余名单复验 | **承接确认**：20 项未封闭逐位持平（无变好无变差）、3 项封闭确认成立、0 项异常；新破口 0（B77 未启用） |
| C. 覆盖矩阵 | 39 组实测（round10 §0 称 41 = 表A17+表B10+表C14，实列 39 行，口径差如实登记）；35 组有覆盖、**6 组零专攻** + 7 个组内空白格，作为 Round 2–9 主题输入 |
| D. 合规审计 | 新增违反 = 0；**存量命中 4 族如实登记**（ast_generator_v2.py 魔数×2、structured_analyzer.py depth>3、DBG_OR 插桩×18），移交清理；BOM 双核心单头 ✓；任务书五插桩模式零命中；工作树干净 ✓ |

**评审结论：通过（承接成立）**。round10 终态（v6 口径）在当前树逐位复现，III.5 承接名单实测口径确认；未发现在途代码变更；存量遗留（§4）非本轮/round10 新增，按 I.6 复审机制登记移交，不构成打回。

---

## §1 v6 口径核对

### 1.1 工具实测数字

- `docs/refactor/syntax-coverage.json`：denominator 128（97 ast 节点 + 31 扩展形态）、numerator 128、coverage_pct overall = 100.0、uncovered 两数组皆空、covered_extra_forms 31 项全列 ✓（spec II.2 分母构成逐项相符）
- 判据来源核对：分子来源声明 = "程序可产出节点词汇 + core/ast_nodes.py AST* 类映射"——属 II.7 误解 2（有过就算）的**残余风险面**，由台账 §5 不变式层（形式层）三态判定补足；本核对确认两层分列、无互替（II.5）✓

### 1.2 wiki 五页数字一致性（禁手改/禁矛盾，II.3 数字规则）

| 页面 | 关键读数 | 与 v6 一致性 |
|---|---|---|
| `wiki/concepts/decompile-invariant-completeness.md` §0/§5.5 | 路径 128/128；形式层 完备 128 / 破口 0 / 零能力 0；挂账 25 号；6 组零专攻 | ✓ |
| `wiki/concepts/branch-coverage.md:18` | "路径层 128/128 = 100%；不变式层（形式层）完备 128 / 破口 0 / 零能力 0 ⇒ 100%；挂账 25 号" | ✓ |
| `wiki/concepts/syntax-audit-ledger.md:18` | "路径 128/128；完备 128 / 破口 0 / 零能力 0 ⇒ 100%；挂账 25 号（已并入总纲）" | ✓ |
| `wiki/index.md:155` | "v6 终审：路径 100% / 形式层 128/0/0 ⇒ 100%；挂账 25 号" | ✓ |
| `wiki/overview.md:43` | "路径层 128/128 = 100% × 不变式层：完备 128 / 破口 0 / 零能力 0 ⇒ 100%；挂账 25 号" | ✓ |

五页零矛盾数字 ✓（II.3 数字规则遵守）。挂账 25 号透明分层口径五页一致（不计入形式层分母）✓。

### 1.3 台账 §5 判"完备"形态锚点抽查（16 处 ≥10 达标）

抽查方法：按台账声锚行号读取代码 + grep 重定位；"相符" = 该行号或漂移后位置存在声称的机制且语义一致。

| # | 锚点声称 | 实测 | 判定 |
|---|---|---|---|
| 1 | RegionType 19 类 `region_analyzer.py:170-189` | :169-189 逐一确认 19 类（BASIC…TERNARY） | 相符（漂移 -1） |
| 2 | `Region.add_child:221` | :221 精确命中 | 相符（0） |
| 3 | `BlockSemantics.is_continue/is_break/is_return :199-201` | :198-200 | 相符（-1） |
| 4 | clamp `:5105`（假循环 clamp） | :5104-5108 POP_JUMP_BACKWARD_IF_TRUE/FALSE 判定 | 相符（±1） |
| 5 | `_find_loop_else:5242` | def 在 **:5450**（+208） | 语义相符（漂移） |
| 6 | except\* 规则4 `:9731/:9813` | 规则4 文档 `:10094`、`return 'except_star'` `:10176/:10371`（+325~360） | 语义相符（漂移） |
| 7 | except\* 发射 `code_generator.py:702/2079` | :702 `except_keyword = 'except*' if is_except_star else 'except'` 精确命中；:2093-2110 第二发射点 | 相符（0/漂移） |
| 8 | continue 守卫 `region_ast_generator.py:10289/:10423-10427` | `_block_is_continue_target:12425` + `_loop_else_set:12559-12563`（+2136） | 语义相符（漂移） |
| 9 | elif 链 `'_is_elif': True :17027/17261` | :19195/:19429（+2168） | 语义相符（漂移） |
| 10 | augassign `code_generator.py:1149` | :195 `isinstance(node, ASTAugAssign)` 发射路径在树（-954） | 语义相符（漂移） |
| 11 | except\* 生成 `is_except_star=True :26839-26843` | :29201 + :30205/:30251（CHECK_EG_MATCH/PREP_RERAISE_STAR 3.11 标记，符合 II.7 误解12 检测标准） | 语义相符（漂移） |
| 12 | B48 落地 `_B48_INPLACE_BINOP_MAP ~:1984` | :1987 + `_b48_attach_ternary_augassign:1991` + `[B48]` 发射标记 :40547/:42496 | 相符（+3） |
| 13 | B72 落地 `_detect_global_declarations ~:2082` | :2041（-41） | 相符（漂移） |
| 14 | B68/B71 门控 `_b68_is_tryfin_tail_releasable :3175-3194` | :3106 + `[B71]` 标记 :3117/:3178 | 相符（漂移） |
| 15 | `_build_boolop_expression:32662`（表B BoolOp） | 定义行未按原行号命中；调用链 10+ 处在树（region_ast_generator :5281/:7056/:14150/:18622/:19124/:23151/:23284） | 语义相符（定义行漂移待重锚） |
| 16 | async 管线 `:30154` | GET_YIELD_FROM/await 识别链 :3971/:7236/:7277/:7295 在树 | 语义相符（漂移） |

**漂移结论**：16/16 语义相符、0/16 伪锚点；行号漂移 +1 ~ +2784，方向与 round10 修复插入位置一致（B48/B72/B46/B71 落地插入 region_analyzer 前部 ~40 行 + continue 守卫区 + 生成区多处）。台账证据规则自声明"锚点 = 2026-09-29 审计亲眼所见"，属历史快照性质，**不构成 II.3 违反**；但按 I.6 复审可执行性，移交 Round 10 终审（Task 10.2）统一重锚为当前行号（防未来审计按图索骥失败）。

---

## §2 残余破口登记面逐项复验（核心）

判定口径（任务书）：读数与 round10 终态持平 = 承接确认；变好 = 查证封闭者；变差 = 回退严重警告。实测 = 本目录三份重放报告（同 ruler、同树）。

### 2.1 逐项表

| 破口 | 锚点（探针 → 单元） | 机制（round10 §4/§5） | 违反条款归属 | round10 终态 | 本次实测 | 判定 |
|---|---|---|---|---|---|---|
| B42 | r7_01 → t_arg_multi_mixed | 三元×参数位 | C1（CALL 参数栈位越界） | 8/9 MISMATCH | 8/9 同单元同签名（Different bytecode） | 未封闭·持平 |
| B42 | r7_04 → t_compare_lhs_only | 三元×比较 LHS | C1 | 6/7 MISMATCH | 6/7 同单元（Different control flow） | 未封闭·持平 |
| B42 | r7_05 → t_listcomp_ternary_filter | 三元×推导式 filter | C1/C2 | 15/16 MISMATCH | 15/16 同单元 | 未封闭·持平 |
| B43 | r7_10 → c_chain_and_combo | 链式比较×BoolOp | C1（汇合块消费点错位） | 7/8 MISMATCH | 7/8 同单元 | 未封闭·持平 |
| B44 | r7_11 → b_and_or_repeat + r7_12 → b_nest_three_layers/b_nest_deep_right | BoolOp 重复/三层/深右嵌套 | C1/C3（B1 双入口同族） | 6/7 + 5/8 MISMATCH | 同签名 4 单元全持平 | 未封闭·持平 |
| B46-尾项 | r7_07 → t_nest_in_condition | 融合条件三件套（实施降级在案） | C2（臂融合超批体量） | 6/7 MISMATCH（唯一失败=降级项） | 6/7 同单元 | 降级在案·持平 |
| B46-b_ternary_lhs_and | r7_12 → b_ternary_lhs_and | BoolOp 条件×三元 LHS | C1 | MISMATCH | 持平 | 未封闭·持平 |
| B47 | r7_06 → t_await_ternary_branches/t_await_assign_ternary/t_await_deep_ternary | await×三元臂 | C1（外提越 POP_JUMP 对） | 7/10 MISMATCH×3 | 7/10 同 3 单元 | 未封闭·持平 |
| B48-残留变体 | r7_08 → t_host_while_body（同文件 t_host_for_else/t_host_try_sections/t_host_match_case） | while/for-else/try/match 体宿主 augassign×三元 | C2（宿主变体判据未触达） | 4/8 MISMATCH×4 | 4/8 同 4 单元（t_host_while_body Different bytecode line14 offset24 逐字节同签名） | 未封闭·持平（降级在案） |
| B49 | r7_08 → t_host_for_else | for-else else 体三元增强赋值 | C1（else 臂前驱集归属） | MISMATCH | 持平 | 未封闭·持平 |
| B50 | r7_08 → t_host_try_sections | try sections 宿主尾段归属 | C1/C3（多前驱汇合复制） | MISMATCH | 持平 | 未封闭·持平 |
| B51 | rv7_02 → chain_two_ternary/chain_three_ternary | if 三元链复合值（变体面） | C1 | MISMATCH×2 | 2/4 持平 | 未封闭·持平 |
| B53-族 | rv7_04 → dict3_nested_value | dict 嵌套三元值（变体面） | C1 | MISMATCH | 2/3 持平 | 未封闭·持平 |
| B56 | r8_07 → r8_assert_nested_func | assert 原生形态降级 | C3（幻影 else 源） | 10/11 MISMATCH | 10/11 同单元 | 未封闭·持平 |
| B56/B57/B58 | r8_10 → r8_x_assert_ternary/r8_x_for_iter_ternary/r8_x_raise_ternary_class | assert/for-iter/raise×三元 | C1/C3（区域抢占越界） | 9/12 MISMATCH×3 | 9/12 同 3 单元（line9 offset16 逐字节同签名） | 未封闭·持平 |
| B59/B60/B61-族 | r8_09 → r8_dh_for_else_del/r8_dh_with_assert/r8_dh_match_multi；r8_11 → r8_dh2_match_guard | 深宿主组合（with 首赋值/mapping rest/match guard） | C1/C2 | 7/10 + 5/6 MISMATCH×4 | 同 4 单元持平 | 未封闭·持平 |
| B62 | r7_14 → h_return_composite | return(call+BoolOp) 尾语句蒸发 | C1（RETURN_VALUE 前消费链） | MISMATCH | 持平（同文件其余 3 单元 h_listcomp_filter_composite×2/h_if_ternary_chain_composite 亦持平） | 未封闭·持平 |
| B63 | rv8_02 → tryfin_then_more | 空 try/fin 后非纯常量尾随段 | C1 | 6/7 MISMATCH | 6/7 同单元 | 未封闭·持平 |
| B65 | rv8_01 → chain_value_boolop | 链式赋值×嵌套 BoolOp 值 | C1（共享值栈消费点错位） | 6/7 MISMATCH | 6/7 同单元 | 未封闭·持平 |
| B69 | rv9_01 → emptyfin_in_if | if 臂内空 try/fin 吞尾随 return | C1/C3 | 4/5 MISMATCH | 4/5 同单元 | 未封闭·持平 |
| B70 | rv9_02 → while_with_whole_body | while True+with 幻影 break | C3（无 is_break 源注入） | 4/5 MISMATCH | 4/5 同单元 | 未封闭·持平 |
| B11-R2 | r4_or4_and2 → or4_and2 | or4_and2 嵌套组合（B1/B44 同族） | C1/C3 | 1/2 MISMATCH | 1/2 同单元 | 未封闭·持平 |
| B71 | r10_21 → fin_continue/fin_break | finally 体仅循环控制发射归属层 | C1/C3（W11-A 认领分支） | 2/4 MISMATCH×2 | 2/4 同 2 单元 | 未封闭·持平（实施降级在案） |
| B73 | r10_04 → imp_try_sections | try 四段 import 宿主泄漏 | C1（B50 族 import 变体） | 2/3 MISMATCH | 2/3 同单元 | 未封闭·持平 |
| B74 | r10_06 → imp_combo_lambda_default | match case 体首 import guard 幻影 | C3（B16/B56 族变体） | 2/3 MISMATCH | 2/3 同单元 | 未封闭·持平 |
| B75 | r10_15 → g_in_try_except | try 宿主 global + finally 条件段归属错位 | C1/C3（B50/B32 族变体） | 5/6 MISMATCH | 5/6 同单元 | 未封闭·持平 |
| B76 | rv10_32 → v_aug_boolop_rhs | augassign×BoolOp RHS 体蒸发 | C1（短路链消费至 STORE 缺失） | 4/5（总口径 26/27） | 7/8，26/27 总口径逐位复现（rv10_31 13/13 + rv10_32 7/8 + rv10_33 6/6 = 26/27） | 未封闭·持平 |
| **B72（封闭确认）** | r10_14/r10_16 → 7/7+7/7；n10_03 2/2、n10_04 3/3；rv10_31 13/13 | nonlocal 声明缺失（STORE_DEREF+co_freevars/co_cellvars 元数据判据） | —（已封闭） | 全 MATCH | **全 MATCH 复现** | **已封闭·确认** |
| **B48 主形态（封闭确认）** | r7_03 → 7/7；r8_06 → 10/10 | in-place BINARY_OP oparg 13-25 + AugAssign 发射 | —（已封闭） | 7/7、10/10 | **逐位复现** | **已封闭·确认** |
| **B64（封闭确认）** | rv8_02 内 with_body_tryfin_chain 单元 MATCH；rv8_03 → 6/6 | with 体空 try/fin 尾随 return（B68 修复覆盖） | —（已划除） | 该单元 MATCH | **复现** | **已封闭·确认** |

### 2.2 站桩回归读数（常设纪律，spec「每轮门禁」）

| 哨兵面 | 基线（round10 终态） | 本次实测 | 判定 |
|---|---|---|---|
| round6 全量 16 pyc | 115/115 零失败 | **115/115**（n6_01 8/8 在内） | 持平 ✓ |
| round7 全量 16 文件 | 108/128（20 失败名单） | **108/128**，失败单元逐位一致 | 持平 ✓ |
| round8 全量 13 文件 + 变体 3 文件 | 110/118（8 失败名单）+ rv8 面 | **110/118** 失败名单逐字一致（r8_assert_nested_func/r8_dh_for_else_del/r8_dh_with_assert/r8_dh_match_multi/r8_x_assert_ternary/r8_x_for_iter_ternary/r8_x_raise_ternary_class/r8_dh2_match_guard）；rv8_01 6/7、rv8_02 6/7、rv8_03 6/6 | 持平 ✓ |
| round9 站桩（r9_01..10 + n9_01..02） | 50/50 | **50/50**（B2/B3/B4 守卫族防回归面零漂移） | 持平 ✓ |
| 六哨兵 + option_account + quotation | 302/308 | **302/308**（115/120 中 trade_info_utils 5 失败名单逐字一致 + option_account 35/35 + quotation 152/153 唯一失败 change_his_to_forward） | 持平 ✓ |

### 2.3 复验统计与口径瑕疵登记

- **确认未封闭：20 项登记面全部持平**（沿袭残留 13 项 + round10 新登记 7 项含 B46 尾项/B48 残留变体）；**封闭确认：3 项**（B72/B48 主形态/B64）；**异常：0 项**（无一变好、无一变差——承接名单实测口径成立，spec III.5 权威性确认）。
- **登记面口径瑕疵（非破口，如实登记）**：
  1. round10 REVIEW2 §5 变体表内记 "rv10_31 5/5、rv10_32 4/5、rv10_33 5/5"（合计 14/15），与其标题口径 "3 探针 27 单元 → 26/27" 不自洽；实测 13/13 + 7/8 + 6/6 = **26/27 与标题口径逐位一致**（唯一失败 v_aug_boolop_rhs）。表内分数系部分单元粗记，移交归档勘误，不影响终判。
  2. round10 §4.1 决策表含 B52/B53/B63 三项（P2/P3，机制在案、实测残留持平），但 spec III.5 沿袭残留名单未列入——III.5 名单与决策表存在子集差。本轮实测已按决策表口径补齐复验（B53-族 rv7_04、B63 rv8_02、B52 同 B42 判据族），移交 1.2 修复工程师按**决策表全 29 项**认领，勿漏 B52/B53/B63。
  3. III.5 挂账口径 "25 号" 与决策表 29 项 + B76 的对应关系：25 = 29 − 已封闭划除项（B64 等）的当前存续计数，wiki 五页与 spec 一致引用，无矛盾；建议 Round 10 终审重算时给出逐号清单防口径歧义。

---

## §3 128 形态对抗覆盖矩阵（以 round10 §1 矩阵 39 实列组为起点 × III.2–III.4 全名单）

覆盖深度分档：**深≥3** = ≥3 轮专攻探针或深度≥3 探针面；**交叉宿主** = 仅作为其他组探针宿主被动覆盖；**浅** = 单轮少量探针；**空白** = 零专攻。

### 3.1 表A — 语句与结构（III.2 全名单 32 形态 → 17 组）

| # | 形态组（III.2 成员） | 对抗轮次 | 深度 | 空白 |
|---|---|---|---|---|
| A1 | Module | — | **空白** | ★组①：模块级语句序/docstring/顶层 if-main/区域树根装配零专攻 |
| A2 | If（IF/IF_THEN/IF_THEN_ELSE/ELIF_CHAIN） | R1/R7/R9 | 深≥3（B2 守卫族防回归面） | — |
| A3 | For / AsyncFor | R3/R6 | 深≥3 | — |
| A4 | While | R3 | 浅→深（round8 宿主被动） | — |
| A5 | Break / Continue | R3/R9/R10 | 深≥3 | B71 2 单元残留 |
| A6 | Try（含 try_finally_only） | R2/R6/R9/R10 | 深≥3 | B71/B73/B75 残留 |
| A7 | TryStar（except*） | R2 | 浅 | 仅 R2 一轮，建议 R4 再攻深度外推 |
| A8 | With / AsyncWith | R6/R9 | 深≥3（B66/B68 封闭面） | — |
| A9 | Match | R4/R10 | 深≥3 | B74 残留 |
| A10 | Raise / Assert | R8 | 深≥3 | B56–B58 残留 |
| A11 | Return / Pass / Expr | R8 | 深≥3 | — |
| A12 | Delete / Assign / AugAssign / **AnnAssign** | R8/R10 | 深≥3 | ★组③：AnnAssign 专攻零（组内空白） |
| A13 | Import / ImportFrom / Alias | R10 | 深≥3（26/28 专攻面） | B73/B74 残留 |
| A14 | Global / Nonlocal | R10 | 深≥3（33→39/40 专攻面） | B75 残留（B72 已封闭） |
| A15 | FunctionDef / AsyncFunctionDef / **ClassDef** | 宿主（全轮） | 交叉宿主 | ★组②：ClassDef 体专攻零（类级赋值/方法间语句/装饰器位） |
| A16 | ExceptHandler | R2/R8 | 深≥3 | — |
| A17 | match_case / withitem | R4/R6 | 深≥3 | — |

### 3.2 表B — 表达式形态（III.3 全名单 → 10 组）

| # | 形态组 | 对抗轮次 | 深度 | 空白 |
|---|---|---|---|---|
| B1 | BoolOp and/or | R1/R7/R9 | 深≥3 | B44/B11-R2 残留（B1 族已封闭，防回归监控） |
| B2 | IfExp | R7/R8/R9 | 深≥3 | B42/B46/B47/B49/B51 残留 |
| B3 | Compare/BinOp/UnaryOp/Constant/Name/Attribute/Subscript/Starred/List/Tuple/Dict/Set/Slice/Index | R7/R8 | 深≥3 | — |
| B4 | Lambda | R7 | 浅 | 建议 R3 组合宿主加深 |
| B5 | ListComp/SetComp/DictComp/GeneratorExp/comprehension | R5/R9 | 深≥3 | — |
| B6 | Call / keyword / arguments / arg | R8 被动 | 交叉宿主 | ★组⑤：keyword_args/star_args **调用点**专攻零 |
| B7 | JoinedStr / FormattedValue | — | **空白** | ★组④：fstring_conversion 零专攻 |
| B8 | Await / Yield / YieldFrom | R6/R7 | 深≥3 | B47 残留 |
| B9 | NamedExpr（海象） | R7/R8 被动 | 交叉宿主 | 随组⑤登记 |
| B10 | 上下文/操作符叶子 | 全轮隐式 | 深≥3 | — |

### 3.3 表C — 31 扩展形态（III.4 全名单 → 12 组）

| # | 形态组 | 对抗轮次 | 深度 | 空白 |
|---|---|---|---|---|
| C1 | elif 链 | R1/R7/R10 | 深≥3（r10_06 5/5） | — |
| C2 | for-else / while-else | R3/R8 | 深≥3 | B49/B61 残留 |
| C3 | except* 异常组 | R2 | 浅 | 同 A7，建议深度外推 |
| C4 | match+守卫+8 模式 | R4/R10 | 深≥3 | B74/B60 残留 |
| C5 | 多上下文 with / try_finally_only | R6/R8/R9 | 深≥3 | — |
| C6 | multi_target_assign / augmented_assign | R8/R10 | 深≥3 | B65 残留 |
| C7 | chained_comparison / walrus / **keyword_args / star_args / slice** | R7（部分） | 深≥3 | ★组⑤组内：chained_comparison 已覆盖；walrus/keyword_args/star_args/slice 调用点零专攻 |
| C8 | relative_import / star_import / global_nonlocal | R10 | 深≥3（r10_05 4/4） | global_nonlocal 见 A14 |
| C9 | fstring_conversion | — | **空白** | ★组④ |
| C10 | nested_comprehension | R5 | 深≥3 | — |
| C11 | decorator_with_args | — | **空白** | ★组⑥ |
| C12 | async 五件套 | R6 | 深≥3（B37/B40/B41 残留在册） | — |

### 3.4 空白格清单（Round 2–9 主题输入，优先级排序）

1. ★组① Module 专攻（A1）——风险理由：区域树根装配/模块级语句序/docstring 位零探针；Round 2 首选
2. ★组② ClassDef 体专攻（A15 组内）——类体宿主全十轮零探针；Round 2
3. ★组④ fstring_conversion（B7/C9）——JoinedStr/FormattedValue conversion/format-spec 位；Round 3
4. ★组⑤ keyword_args/star_args/walrus/slice 调用点（B6/B9/C7 组内）——Round 3
5. ★组③ AnnAssign（A12 组内）——Round 4
6. ★组⑥ decorator_with_args（C11）——Round 4
7. 次级空白：TryStar/except*（A7/C3）仅 R2 一轮单轮覆盖——Round 4 深度外推；Lambda 单轮浅覆盖——Round 3 组合加深
8. round10 §0 口径注记：其称 "41 组（表A17+表B10+表C14）"，§1 实列 39 行（表C 12 行）——41 与 39 的差系表C 计数口径（14 vs 实列 12），本轮矩阵按实列 39 行如实登记，移交归档勘误

---

## §4 算法合规审计（I.4 黑名单五项 + BOM/插桩/在途变更）

审计前提：工作树 core/ 零在途变更（git status 证据见 §0），当前树 = round10 终审通过态（round10 REVIEW2 §1 逐 hunk 6/6 放行覆盖全部近期 diff）。本轮职责 = 验证无新增 + 对存量全树扫描登记。

| 红线 | 扫描命令/方法 | 命中与定性 | 结论 |
|---|---|---|---|
| ① 文件名/函数名白名单特判 | grep `test_repros\|round\d\|co_filename\|__name__ == '\|\.pyc'\|_OK\.py` in core/cfg/ | 9 命中：7 处注释文档性引用（round67_diag4/round14_join/round1 等，非判据）+ 2 处 `__main__` 入口（独立工具脚本）+ 2 处 `type(x).__name__ == 'LoopRegion'`（region_ast_generator:6528、region_analyzer:20099）| **新增 0**。类型名内省属结构分发非语料名特判，存量观察项移交 Round 6 |
| ② start_offset 魔数比较 | grep `start_offset ==\|start_offset >\|start_offset <\|offset == \d{4,}` | 命中 11 处：(a) structured_analyzer:6925/6932 已注释 ✓；(b) structured_analyzer:7937-8175 `start_offset == 0` ×6——0 为模块起始语义值非魔数，豁免；(c) **ast_generator_v2.py:9050 `if elif_block.start_offset == 62: continue`，原文注释 "[临时调试] 硬编码跳过 offset 62（验证思路）"——实锤 I.4 魔数 + I.5 条件性少发射（跳过 elif 条件生成），且该文件在用链在树（parsers/unified_generator:100、ast_builder:19273/19298、core/cfg/__init__:76/205、region_ast_generator:147、code_generator:4005 共 8 处 import）；(d) ast_generator_v2.py:14990 `block.start_offset == 74: pass` 死语句魔数 | **新增 0**；存量违规 2 处（ast_generator_v2:9050/:14990）——非 round10 修复引入（round10 diff 仅触 region_analyzer/region_ast_generator），属历史遗留，登记移交 Round 8 清零冲刺清理（修复受 I.4 白名单约束） |
| ③ 跨层 `entry in blocks` 反查 | grep `\.entry in .*\.blocks\|entry in self\.blocks` | 14 命中：region_ast_generator:1352/1371/1396/1413（孤儿块释放守卫族 = B4/C3 显式认领判据，白名单"区域成员关系"合法用途）；:17938 注释明确禁用跨层反查 ✓；:20776/:27379/:28997/:33038、region_analyzer:24968/24970/:30478（区域成员关系测试，识别器内归属判定）；:36073 注释声明不跨层 ✓ | **新增 0**。存量命中经抽样定性为 C3 守卫落地/区域成员关系判据（I.4 白名单允许项），非未封闭跨层启发式；全量逐条定性移交 Round 6 注释审计轮 |
| ④ self 新增跨方法状态 | 树与 round10 终审逐位一致 + round10 REVIEW2 §1 H1-H5 逐 hunk 审计（"无新增 self 跨方法状态"） | 无新增 | PASS |
| ⑤ 条件性不发射（少发射换绿）/硬编码深度上限 | grep `if depth > \d+\|MAX_DEPTH\|max_depth = \d` + round10 §2 哨兵零回归证据 | **structured_analyzer.py:14330 `if depth > 3: # 限制搜索深度`——I.4/I.5 硬编码上限存量命中**（辅助搜索限制非归约终止判据，该文件非本规范涉改六文件、非 round10 引入）；哨兵面全部持平（§2.2）证明无"少发射换绿"新增 | **新增 0**；存量 1 处登记移交 Round 8 |
| 禁止前缀方法（I.5） | grep `def _(fix_\|patch_\|fallback_\|hack_\|workaround_\|temp_)\w+` in core/cfg/ | 零命中 | PASS |
| BOM（IV.2） | 字节级：region_analyzer.py 头 3 字节 = `efbbbf`、全文 BOM 计数 = 1；region_ast_generator.py 同 = `efbbbf` ×1 | 双核心恰一单头完整，无双 BOM（round9 事故未复发） | **PASS** |
| 插桩残留 | 任务书模式 grep `R10DBG\|R9DBG\|_R23N20_DEBUG\|_probe_r\|_patch_dbg` in core/cfg/ = **0 命中**；扩大模式 `DBG_\|_DEBUG =` in core/ = **region_analyzer.py DBG_OR ×18**（:18324-18625，`os.environ.get('DBG_OR')` 门控 print，R67 时代 or-tail restore 调试输出，默认关闭不改变判定行为） | 任务书五模式零命中 PASS；**存量插桩 DBG_OR×18 登记**——round10 §6 扫描模式未含 DBG_ 系故漏网，属历史遗留，移交清理（清理属删除性变更，不触算法判据） | PASS（新增 0）+ 存量登记 |
| 在途变更 | `git status --porcelain` = 7 untracked 全在 rounds/round1/（本轮产物：REVIEW.md + 3 重放 JSON + 2 index JSON + 1 汇总脚本）；core/ wiki/ test_repros/ scripts/ parsers/ 零改动 | 干净 | **PASS** |
| 命令时限 | 全部命令 ≤300s（重放批 9.8s/39.1s/4.1s） | — | PASS |

**存量遗留汇总（非新增、不构成承接轮打回，移交清单见 §6）**：
1. `core/cfg/ast_generator_v2.py:9050`——[临时调试] start_offset==62 跳过（I.4 ②/I.5，在用链 8 处 import）
2. `core/cfg/ast_generator_v2.py:14990`——start_offset==74 死语句魔数（I.4 ②）
3. `core/cfg/structured_analyzer.py:14330`——depth>3 硬编码上限（I.4 ⑤/I.5）
4. `core/cfg/region_analyzer.py:18324-18625`——DBG_OR 插桩 ×18（G0 插桩残留）

---

## §5 新破口登记

**无**。72 文件 + 24 文件 + 21 文件三面重放共 537 单元中，全部 MISMATCH 均与 III.5 承接名单/round10 决策表逐项对号（§2.1），无名单外新失败单元；**B77 未启用**。II.7 十三条误解自查：本轮未以门禁读数代完备宣告（§1 仅核数字一致性）、未以语料口径限分母（128 分母 = ast 权威）、未犯浅层测试当无感证明（承接确认≠完备宣告，仅证读数持平）、检测标准对准 3.11 标记（§1.3 #11）——无违反。

---

## §6 交接单（致 1.2 修复工程师）

### 6.1 可封闭优先级排序（判据草案沿 round10 §4 全 29 项 + B76，补录 B52/B53/B63）

| 优先级 | 破口 | 判据草案（同层结构事实，I.4 白名单） |
|---|---|---|
| **P1** | B48 残留变体（r7_08 t_host_while_body 等 4 单元） | B48 通道 `_b48_attach_ternary_augassign`（region_analyzer:1991）扩展宿主判定：宿主区域类型（WHILE/FOR-ELSE/TRY/MATCH 子区域体）由区域成员关系 + 后继集合判定，禁止名字/深度特判 |
| **P1** | B71（r10_21 fin_continue/fin_break） | W11-A 认领分支：finally 域内循环控制终结块（BlockSemantics.is_break/is_continue = :198-200 事实）归属由终结块后继 = 循环头/出口块的成员关系判定；发射归属层修复（W11-A 取证在案） |
| **P1** | B46 尾项 t_nest_in_condition | `_detect_ternary_pattern`（:22144 区段）融合条件三件套按臂块集成员关系 + 判别跳转逃逸边检测（同 B46 已封闭部分判据对称外推） |
| **P2** | B72 收尾核查 | 已封闭，仅防回归监控（rv10_31 13/13 面） |
| **P2** | B76（augassign×BoolOp RHS 体蒸发） | round10 REVIEW2 §5 判据草案在案：STORE 前 JUMP_IF_TRUE_OR_POP 短路链 + BINARY_OP 消费至 STORE；装配器对"块集非空但发射为空"必须报错禁止静默 |
| **P2** | B65/B63/B69/B70/B56 族/B57/B58/B59/B60/B61/B62 | round10 §4.1 判据草案逐项在案（孤儿块释放守卫族/异常表区间/BlockSemantics 事实），锚点实测持平（§2.1） |
| **P2** | B73/B74/B75（import/global 宿主族） | round10 §5 判据草案在案（B50/B32/B16/B56 族变体，异常表区间 + 声明发射集元数据判据） |
| **P3** | B42×3/B43/B44×4/B47×3/B49/B50/B51/B52/B53/B11-R2 | round10 §4.1 判据草案在案；B1/B44 同族项随 B1 双入口回归面监控 |
| **清理** | §4 存量遗留 4 族 | ast_generator_v2:9050/:14990 魔数删除、structured_analyzer:14330 深度上限改判据、DBG_OR×18 删除——删除性变更，不触算法，涉改文件 = ast_generator_v2.py/structured_analyzer.py/region_analyzer.py |

### 6.2 并行派发建议（破口族不相交 ∧ 涉改文件不相交）

- 位 1：B48 变体 + B46 尾项（region_analyzer.py 识别/装配区段）
- 位 2：B71 + B73/B75（region_ast_generator.py finally/try 归属发射区段）
- 位 3：B74 + B76 + B65（region_analyzer match/BoolOp 装配区段 + 装配器空发射报错）
- 清理位（可并入任一位）：§4 存量 4 族

### 6.3 判据与门禁提醒

- 判据只取 I.4 白名单（块末 opcode/后继前驱集合/异常边/区域成员关系/code object 元数据/指令 oparg）；禁止名字白名单、start_offset 魔数、跨层无守卫反查、self 新增跨方法状态、以少发射换全绿、硬编码深度上限（I.4 黑名单 + I.5）
- 修复语义 = 封闭守卫恢复 C1/C2/C3（I.3 推论：深层才错 = 条款破坏），禁止语料个案补丁（I.6）
- 触及方法 docstring 六项模板（I.7）+ C 条款声明；落地声明必须写明「代码已落地」（I.6）
- 自测门禁 = 本轮全部 MISMATCH 转 MATCH ∧ 负对照保持 MATCH（n6/n7/n8/n9/n10/rv 面）∧ 34 小测试集无回退 ∧ 站桩回归面（§2.2 五行读数）不变差 ∧ IV.2 门禁自检清单全过
- 负对照基线（本轮实测，勿回退）：n6_01 8/8、n7_01/n7_02 各 5/5、n8_01 4/4、n8_02 5/5、n9_01 3/3、n9_02 4/4、n10_01..04 合计 9/9、rv9_03 4/4、rv10_31 13/13、rv10_33 6/6
