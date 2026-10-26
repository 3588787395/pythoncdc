# Research Log

## 2026-10-23（attack-completeness-claims 终验：v9 双读数 + G1–G6 门禁）

- **v8 100% 降级**：形态基线仍为 128/128，但只作历史回归口径；v9 判定空间 J v2 = **0/1556 covered**（9.3 全量），集成样本 **51/1556（3.28%）**、**45 EQUAL / 6 DIFFERENT**（6 条均 R7）；G4 339 条 **0 proved / 339 open**；G6 24 条 local-bootstrap **20/24**、泄漏 0；`overall=BLOCKED`（G1/G2a/G2b/G2c/G3/G4/G6；G5 baseline_only）。证据 = `.trae/specs/attack-completeness-claims/rounds/round9/GATE_REPORT.md` + `rounds/round10/FINAL_REPORT.md`。
- **破口**：B163–B219 共 **57 项未封闭/定性挂账**；B142 由 B181 重新定性为形态级缺口（前规范「稀窝不升格」作废），B143 为归约级缺口。v9 新发现 4 个 fuzz 复现先映射 B203/B207/B210/B197+B202，未新开 B 号；J 样本 6 条 R7 DIFF 与 B199/B202 docstring 面同源，待去重。
- **文档同步**：总纲 §0/§2.2/§3（13→17 误解）/§5.5/§6（B163–B219 汇总）/§8.4/§9.1；`rules.md` §2.4/§6.2/§7.2/§8.1/§8.3；`overview`/`index`/`syntax-audit-ledger`/`branch-coverage` 全部改为双读数并标注 v9 BLOCKED。**禁止**把 128/128、51/1556 样本或 local-bootstrap canary 写成完备。
- **未做**：402/small34/quotation/pytest/IV.2 本轮未重跑；全量 J 语义差分、G2b/G2c、G3 全量、G4 traces、G6 独立保管均未建立；Task 10.1 的 B163+ 封闭为 0。终态只能表述为「形态基线达成（v8 口径）」。

## 2026-10-21（v3 attain-true-completeness 十轮终审：R8 全行对抗终审 + 三态落账 v8）

- **R8 终审**（commit `b6e634b7`，实录 = `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md` + `REVIEW2.md`）：25 行矩阵 34 探针 **257/257**（每行 ≥1 深层宿主探针 + 负对照 60/60；13 误解 13/13 自查零触犯）；组合级 25 号终表 + 另册 B52/B53/B11-R2 并入 = `r8combo2` **241/242**（唯一红 = `v_nest_fin_continue` 属地 **B142 稀窝**，不升格）；E 门禁终跑 402 八分片 **6617/6617 files_failure=0**（574s）、IV.2 全绿；7 组回归终读数 86/86、46/46、60/60、71/71、65/65、172/172、98/98。本轮机制 B153–B162（4 文件 +516/−25，全 `[Bn-V3R8]` 标记）：c04/m02 三层 try 配对（B155/B156）、for-iter 三元（B153/B154）、系列深宿主组合（B157–B160）、BUILD_\* 链式后继排除与 while-or 链链尾完成判据（B162），另册两项翻正后另册清空。
- **§8.2 复审六步（v8 落账）**：①fix 批落位确认——R1–R8 全批（rr-v3r01….rr-v3r08）均在 origin/main 祖先链；②grep 落地标记全表——`[Bn-V3Rn]` 标记族与 B129–B162 机制符号在树逐条核验（总纲 §6 B77+ 表 v8 终态列 + `round8/REVIEW.md`）；③台账 §5 全量更新——三态 **v8 = 完备 128 / 破口 0 / 零能力 0 ⇒ 100%**，§6 开放破口表全部封闭（v7 留档 + v8 终态列）、§8.1 口径史加 v8 行；④`tools/kb/syntax_coverage.py` 重跑 **128/128 = 100%**（sha256 `38003eb4…`，v7 为 `86539c44…`；JSON = `docs/refactor/syntax-coverage.json` denom/numer/pct 三读一致）；⑤占比重算同步五页——总纲/branch-coverage/syntax-audit-ledger 数字行更新，overview/index 无三态数字行（引用文本不涉改，核验一致）；⑥本条 log。
- **口径 v8 取代 v7**：v7 的 25 个破口行（表A 14 + 表B 6 + 表C 5）与组合级维持 16 全数封闭；v3 十轮按 25 行工作面推进（R2 If/BoolOp/IfExp、R3 Try/Raise/Assert/Import/Global、R4 Await/ListComp/await_expr/Yield、R5 Match/With、R6 Break/Continue/While、R7 Delete/AugAssign/Return/Slice、R8 终审），E 门禁每轮全量。稀窝属地 B142（嵌套 finally 副本归属）/B143（finalbody 内 break 派发）维持登记不升格。三维度禁互替不变：语料回归（402）与对抗矩阵分账记账。

## 2026-10-17（对抗规范 v2 Round 10：§8.2 六步全量重验 + 三态落账 v7）

- **六步全量重验**（HEAD `3e0d6905`；origin/main `0ad55951`；实录 = `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round10/WIKI_REVIEW.md`）：①round1–9 全批次提交在 origin/main 祖先链（13/13 核验）；②72 项落地标记 grep = **71 PASS / 1 异常**（`_graft_pending_operand` 在树）+ 36 项补充枚举；③台账全 128 三态落位：**完备 103 / 破口 25 / 零能力 0**（表A 14 + 表B 6 + 表C 5；round9 封闭 B104 族/B124/B125/B126 后自 101/27 升格 2 行：chained_comparison、for_else）；④`tools/kb/syntax_coverage.py` 重跑 128/128 = 100%，sha256 前后一致 `86539c44…`；⑤占比重算 **103/128 = 80.47%**，五页数字同步（总纲/overview/index/syntax-audit-ledger/branch-coverage）；⑥本条。
- **口径 v7 取代 v6**：v6「形式层 128/0/0 ⇒ 100%」为对抗分层前的未落账读数；对抗规范 v2 十轮实测 25 行破口（round3/round4 已预告降级方向）本轮统一落账。组合级挂账 25 号分层：**清零 9**（对抗规范 Round 1 批次 A/B/C 8 项 = B46 尾项/B48 残留变体/B74/B71/B73/B75/B76/B65 + B50 同链实证）/ **维持 16**（B42/B43/B44/B47/B49/B51/B56–B63/B69/B70；残余以 B78–B97 续接编号登记）；另册口径差 B52/B53/B11-R2 待归档统一。开放破口：B98/B122/B127/B128/Yield/B44（§6 B77+ 表 + §8.3 状态机）。
- **嫁接符号更正（只增不删）**：`_graft_pending_operand` 并非「树中零命中」——符号族在树（`core/cfg/region_ast_generator.py:43043/43180` + `_leading_operand`/`_cjb_skip_inline_if` 发射段 `:60503-60529`），随 `c53df077`（2026-09-30 harden round1 在途快照）引入；2026-10-04 条目所称「确证废弃」经本轮全量 grep 更正为「**路线废弃、符号未清理**」（历史条目保留原文）；B1 封闭判据不变（五臂算法）。

## 2026-10-04（对抗规范 Round 10 终审：B1 族升格 + 口径 v6）

- **B1 族升格「已封闭」**（§8.2 复审六步全量执行）：①fix 批归档落位（round10 FIX.md，B72/B48/B46 部分封闭 +7 单元）→ ②grep 落地标记在树确认（本轮 `[B48]`×5/`[B46]`×5/`[B71]`×2/`[B72]`；历史 B1 族 `[B1b fix]`/`[B1b fix-r2]` + `_sb_has_body` 十余处——round75 归档嫁接方案 `_graft_pending_operand` 确证废弃，改由 Round 1 五臂算法路线封闭）→ ③台账 §5/§6/§8.1 更新（完备 127→128、破口 1→0，B1a/B1b 状态改「已封闭（防回归监控）」）→ ④`tools/kb/syntax_coverage.py` 重跑 **128/128 = 100%** → ⑤占比重算同步五页（总纲/branch-coverage/syntax-audit-ledger/overview/index，overview 乱行修复）→ ⑥本条 log。
- **口径 v6（对抗分层）**：路径 100% / 形式层（路径 × 单形态不变式）128/0/0 ⇒ **100%**；对抗 10 轮（`harden-completed-forms-10rounds`）登记的**组合级挂账 25 号未清零**（B42–B51/B56–B65/B69–B71/B73–B76 内未封闭部分 + 残留单元 + 6 组零专攻形态组，权威清单 = spec rounds/round10/REVIEW.md 残留决策表 + REVIEW2.md）——透明挂账，不计入形式层分母，按 §8.3 状态机继续推进。终审全量验证零回退：402 = 6554/6617（99.05%）369/402、小测试集 34 = 1505/1568、quotation 152/153、tests 六套件 277 passed/2 failed（基线名单）——全与 Round 9 终态逐位持平。

## 2026-09-29（夜：总纲合并，消除散乱）

- **信息散乱收口**：完备性标准原拆在 branch-coverage（标准）/syntax-audit-ledger（台账）/branch-conditions（条件库）/rules.md（工程条款）/spec 三处，用户裁定"落实效果较差、信息散乱"⇒ 合并为单一权威文档 **[[decompile-invariant-completeness]]**（反编译迭代总纲：嵌套无感与语法完备）：§0 读数 / §1 C1-C2-C3 不变式+归纳 / §2 分母 128+三级判定 / §3 十三条误解 / §4 T1-T8 映射 / §5 128 形态台账全量 / §6 破口登记 B1a-B4 / §7 except\* 纠正 / §8 迭代机制（标记+六步+状态机）/ §9 口径演变史 v1-v5+正确性旁证+BOM / §10 可用资源索引（工具/数据/归档复现/页面/门禁全表）。旧两页降为转址页（含位置映射表，链接完整性保留）；index/overview/branch-conditions/cfg-anatomy/rules.md 全部活引用改指总纲；历史 log/spec 记录不改动。

## 2026-09-29（傍晚补：迭代机制操作化）

- **迭代机制操作化**（完备性支持的 KB 侧收口）：[[branch-coverage]] §7 重写为可执行程序——**落地标记表**（B1a 标记 = `_graft_pending_operand`，当前树 grep 零命中 = 已验证未落地；B2/B3/B4 标记已在树防回归）、**复审六步**（fix 批落位 → grep 标记 → 台账更新 → 路径层重测 → 占比重算 → log）、**破口状态机**（未定位→已定位(仅spec)→已落地→已复审，只有已复审才计入分子）。B1b 登记归档复现路径（`fix1/synth/neg75_jqcond2`：`if a and b or c:` → `if not (a and b):`，or 尾块整体丢失、两臂逐字节相同均失败、FACTS:267 确证未走 skip 分支）供 fix2 直接取用——**记录复现而非替 fix2 定位**（纠偏：定位属测试工程师职责，KB 只登记复现锚点与标记）。rules.md 7.2 同步（B1a/B1b 拆行 + 标记 + 状态机引用）；台账 BoolOp 行与标准 §6 同步。

## 2026-09-29（傍晚：BOM 读数纠正 + 判定条件库）

- **BOM 读数纠正（波及已发布数字）**：`region_ast_generator.py` 带 UTF-8 BOM（G0 保护特性），`program_cfg.py` 用裸 `utf-8` 读 → `compile()` 对 U+FEFF 报 SyntaxError → **51,751 行的最大模块整个缺失于旧读数**（旧 fail=1 静默）。改 `utf-8-sig` 重测：分支点 **51,518→60,933**（子分支 91.2%），code objects 5,664→6,923，模块 61→60（cleaned 已删除出清 8,941），**region_ast_generator 18,356 分支点独占 30.1% 成为最大分支巢**（旧"复杂度集中 78.9% 于识别侧"叙事纠正为 **82.1%**，生成侧比识别侧多 80%），最深 164 层定位 `ast_builder._process_instruction`。[[cfg-anatomy]] 全量重写，overview/index 同步；旧读数标注作废。
- **新增分支判定条件库**（`tools/kb/branch_conditions.py` → `docs/refactor/branch-conditions.json`）：程序自身**每一分支判断条件逐条入库 + 相似度比较**。7 类判定点（IF_TEST 30,996 / BOOLOP_OPERAND **逐操作数** 26,358 / IFEXP 2,124 / COMP_IF 1,302 / WHILE 509 / MATCH_GUARD **0** / ASSERT **0**——后两类零读数经精确 grep 核实为真实读数，程序自身不用 match/assert），合计 **61,289**；最深判定嵌套 143；结构归一化（Name→N/Attribute→A/Constant→C）+ 结构哈希同形簇 1,903 组（58,574 条重复）。命令：`similar`（结构全等 1.0 + SequenceMatcher 近邻，长度预过滤）、`dupes`（同形簇聚簇）。缺陷工作流：条件同形定位 → 定向回归集（替代"等语料撞上"）。修复过程自身 3 个 bug 入案：①module 字段被 visit_Module 置 None；②If/While/IfExp 条件内嵌 BoolOp 未递归（BOOLOP_OPERAND 1,965→17,456→26,358）；③BOM（上述）。[[branch-conditions]] 建页。
- 完备性标准与逐形态审计（推翻两初判）见上节。

## 2026-09-29（下午：完备性标准 + 逐形态审计，推翻两初判）

- **rules.md 清理更新**（根目录工程规范）：①修正失效锚点——`_identify_try_regions` 实为 `_identify_try_except_regions:7603`、R25 判据实为 `_check_elif_chain:18876`；②区域表补齐到 `RegionType` 19 类（补 MATCH/ASSERT/链式比较/TRY_FINALLY/SEQUENCE，锚点全核实）；③新增 1.5 嵌套无感不变式（C1/C2/C3+归纳论证）、2.4 完备性测量反模式禁令、3.5 except\* 规则（3.11 标记族）、6.4 修复验收标准（落地归档必须写明"代码已落地/仅归档 spec"——B1 教训）、7.2 破口登记（B1 开/B1b 未定位/B2-B4 已落地防回归）、8.1 完备性标准（128/128 路径 + 127/1/0 不变式 ⇒ 99.2%）；④§八"最终状态"ece3c91 时代快照降级为历史存档，当前门禁基线（41 靶/sstrict/battery/金丝雀）替换验证清单；"唯一缺口 except*"旧结论作废标注。
- **方法论重定义（用户指正后定稿）**：完备占比 = 程序能处理的 ÷ 完全反编译应能处理的，判据 = **三路径存在 ∧ 嵌套无感不变式成立**（C1 局部消费 L(A) / C2 子区域黑箱 / C3 非局部信息守卫封闭）；无感处理下任意深度由归纳得证，分母不随嵌套组合膨胀。[[branch-coverage]] 重写为标准本体（三级判定、**13 条误解清单**、T1-T8 理论→实现映射、迭代机制、证据规则）。
- **初判推翻 #1——except* 非零能力**：旧判"有节点类无识别逻辑"的根因 = 检测标准误用 `PRELOAD_RERAISE`（**3.12** 操作码）；3.11 的标记是 CHECK_EG_MATCH/PREP_RERAISE_STAR，审计确证全链已实现（`[Phase 3 adv17_try_except_star]` 标记族）：识别 `region_analyzer.py:9731/9813/12701-12709` + `exception_handler.py:93-276` → 归约 handler_type `'except_star'` `:8724/:9342` → 生成 `region_ast_generator.py:26839-26843` → 发射 `code_generator.py:702/2079`（`except_keyword='except*'`）。工具检测标准同步纠正（`is_except_star`/`PREP_RERAISE_STAR`），JSON 重测 128/128。
- **初判推翻 #2——B1 修复未落地**：当前树 `region_ast_generator.py:47629-47643` 仍为丢弃版（`_cjb_skip_inline_if` → extend pre_stmts → return，`_cjb_cond_expr` 丢失）；fix1 嫁接（`_graft_pending_operand`/`_leading_operand`/`_contains_identity`）**仅存归档 spec**（round75/batches/fix1/specs/jqop1.json，commit db9364bf 自述"除本归档外 repo 零写入"）；**B1b** 第二丢弃入口未定位（fix1 自述遗留，交 fix2+）。B2/B3/B4 守卫族确证**已落地**（continue `_loop_else_set:10423-10427`；共享尾 W14-C/fix3-T1T2T6/W23/R71-thenover；孤儿块 `:1593-1663`+`region_analyzer.py:1410-1424`），保留防回归登记。
- **产出**：[[branch-coverage]]（标准本体）+ [[syntax-audit-ledger]]（128 形态逐形态台账：识别/归约/生成三锚点 + 不变式判定 + 破口登记）；spec `.trae/specs/define-cfg-completeness-standard/`（spec/tasks/checklist 全勾）。
- **终判读数**：路径层 **128/128 = 100%**；不变式层 **完备 127 / 破口 1（BoolOp B1）/ 零能力 0 ⇒ 完备占比 99.2%**——与旧 99.2% 数值巧合、含义全异（旧数=节点词汇存在率"有过就算"；新数=路径 100% × 不变式扣减）。残留 sstrict 67 缺陷单元未归类守卫族，属 fix 批工作流，落位后按标准 §7 复审。程序文件零改动。

## 2026-09-29

- 建 patterns 层：`wiki/patterns/` 5 张缺陷模式页（P-1 if-continue 兄弟丢失 / P-2 IF 吸收循环后兄弟 / P-3 Loop 吸收外层条件 / P-4 elif 链尾随语句外提 / P-5 and 复合条件部分拆分），从 rules.md R23-R26 案例提炼，症状→区域类型→边界判据→原则→修复锚点→检索词；schema.md 增 `kind: pattern`。
- 补丁语义聚类：新增 `tools/kb/cluster_markers.py`，9,098 标记 → 16 主类（other 40.1%、if 18.8%、try 13.5%、loop 12.1%、with 6.3%…），产出 [[patch-semantic-clusters]] + `docs/refactor/patch-semantic-clusters.json`；发现三胞胎/v2/structured_analyzer 类分布同构、ast_builder 与 cleaned 逐类计数几乎相等（死副本独立证据）。
- Obsidian：新增 [[complexity-dashboard]]（补丁密度/god class/模式页三视角 Dataview）；根目录 `region-reduction-pipeline.canvas`（S1-S7 管线 + 模式页按修复阶段挂载）。
- Q4 闭环验证：症状查询"else 体内尾随循环被外提"命中 P-4 页（Score 57，Top-1）——修复前先查 wiki 成立。
- 向量检索：`llm_wiki_embed_page` 401（应用端 embedding 凭据未配置，tokenSource: none）；模式页检索词小节作为关键词检索的兜底。待应用端配置后重跑 embed。
- 数据校正：check_stale 发现 `parsers-ast-builder-cleaned.md` stale（仅 content_hash 变化）→ 重建；裁决 lineages/热点页 vs 模块页数字矛盾（以当前源码为准）：region_ast_generator 51,566→51,751、region_analyzer 28,337→28,371、ast_builder 26,959→30,264、cleaned 26,256→29,479（差 785）、ast_generator_v2 26,491→26,879、ast_builder_unified 166→185、control_flow 1,546→1,670；overview 计数表修正（模块 61/概念 4/热点 2/模式 5/查询 2）。
- 断链检查 0；check_stale 0。
- 入口可达性分析：新增 `tools/kb/reachability.py`（pycdc/pycdas BFS import 图）：61 模块中 16 个（37,972 行）从入口不可达，清单存 `docs/refactor/reachability.json`；仅作证据，源码零改动。
- 语法完备占比（分母纠正，两次）：① 首版循环论证——拿实现自身 `RegionType` 枚举当"全部可能分支"再测覆盖率；② 二版 34 形态仍是顶层构造的粗粒度清单（97.1% 虚高）。**正确分母 = Python 3.11 语言完整语法面**：以 `ast` 模块为权威取 97 个节点类型（剔除 3.8 前废弃别名 `Num/Str/Bytes/NameConstant/AugLoad/AugStore/ExtSlice` 与非语法面 `Interactive/Expression/FunctionType/Suite/TypeIgnore`）+ 31 个无独立 ast 节点的语句形态 = **128 项分母**；分子 = 程序可产出节点（`ast.<Node>` 构造引用 + `core/ast_nodes.py` 的 `AST*` 映射）= **127 项** ⇒ **完备占比 99.2%**（ast 节点 100%，扩展形态 96.8%）。工具 `tools/kb/syntax_coverage.py` → `docs/refactor/syntax-coverage.json`。**唯一缺口 = `except*` 异常组**：核实 `ASTTryStar` 节点类确实存在（`core/ast_nodes.py:6444`）且 `region_ast_generator.py:6728` 分发它，但 **`PRELOAD_RERAISE` 零引用**（except* 专有操作码）⇒ 属"有节点类、无识别逻辑"的半成品，故不计入分子。P0 两项：except* 补识别路径、match/case 补语料验正确性。
- 分支点枚举口径两次纠正：① 前版测"单元是否含某形态"（一层布尔），一个 500 行函数只记 1，低估数量级 → 改逐个分支点计数；② 用户指正后改为**分析程序自身**而非 pyc 语料实例。新增 `tools/kb/program_cfg.py`：编译 61 个白名单模块（5,664 个 code object）建 CFG，枚举每个分支点及全部层级子分支（支配深度）→ `docs/refactor/program-cfg.json`。读数：**51,518 分支点** = 顶层 4,096（7.9%）+ 子分支 **47,422（92.1%）**，最深支配深度 **164** 层，每单元均 9.10；形态 if 41,204（80.0%）/ for_iter 7,374 / boolop 1,352 / while 1,069 / 异常 519；深度每层仅衰减 ~8%（远慢于语料 pyc），>50 层仍 1,620 个；复杂度集中于 region_analyzer(10,131) + ast_builder(9,226) + ast_builder_cleaned(8,941) + ast_generator_v2(7,929) + structured_analyzer(4,358) = 78.9%。**关键结论：程序自身嵌套深度 164 层远超语料 pyc 的 32 层 ⇒ 反编译器比它反编译的代码更复杂**。[[cfg-anatomy]] 重写为此口径（语料 56,026 分支点降为对照附注）。
- content_hash 口径修正：12 张模块页原记录 LF 行尾 md5，git 检出为 CRLF（autocrlf）；md5 核验内容等价后同步为当前文件哈希，check_stale 回 0。

## 2026-09-28

- Project created
## [2026-09-28] external delete | _real/a.py

Deleted 1 source file and 0 wiki pages.


## 2026-10-24 rr-v5r01..r08（achieve-any-syntax-completeness）

- Task 0–3：测量口径修正、B142 嵌套 finally、x01 折叠行头族、B199 docstring（be256ae0 等）
- Task 4：四 fuzz 族封闭 + deephost 臂锚（7d3432a1，fuzz 24/24）
- Task 5：J 空间 c1/c2 补齐 + 1556 全量 C1–C5 + 三类清单（fa0bcd0a）
- B214 except* 闩：尝试→回退（4a5017d8，恢复 406 基线），登记 OPEN
- Task 6：G2b/G2c/G3样本/G4trace 实测读数（e6b603ee）
- Task 7：G5 本树复跑 + G6 ASSURANCE_BLOCKED + 比较器完整性（4a07f00c）
- Task 8：本双读数同步与终态归档

## 2026-10-25 rr-v5r09f→rr-v5r22 修复阶段：uncovered 归零

按族修复判定空间缺陷清单（每族：字节签名定位→窄谓词修复→strict R7 全等→全电池→J 刷新→提交推送）：
B214 try 尾自然回边（96）、B134-V3R4 混合链组边界（12）、E04a-e 三元族（12）、
B66c with 退出 return 链头（1）、R9-ELIDE-f while-1 壳 for 宿主（6）、B93d match 臂机制块（7）、
C404 match 三联（12）、G2B case 臂显式 return None（5）、G3B with 退出机制块（4）、
R811 match 尾拆分（2）。全部 22 个根因族修复后：

**covered_equal 281→395、uncovered 189→0、module_only 676→719、unjudgeable 442。**
判定空间 1556 条中全部 1114 条可判定条目 C4 均 EQUAL；402 语料零漂移、
pytest 406 基线逐字节一致、fuzz 24/24、16 探针 strict 全等。缺陷清单清零≠完备性宣称：
442 条 unjudgeable（424 环境依赖 + 18 超时）仍在判定外，product_complete 仍以运行时验证器判定为准。

## 2026-10-26 rr-v5r26：块中段 SWAP 多目标交换 + 常量折叠注解元组

- B220-V3R26 `core/cfg/region_ast_generator.py::_build_swap_multi_target_assign`：`self.a[i], self.a[j] = self.a[j], self.a[i]` 块中段整组归约。SWAP 属 SKIP_OPS 不进 `stmt_instrs`，块首解析器 `_swap_unpack_result` 因前导语句 STORE 失效，原先首个 STORE_SUBSCR 吞掉第二目标。判据全部取自块内指令序（SWAP(arg>=2) 回溯 + N 目标窗口前向解析 + 值段净栈效应 = N + 六种 STORE 白名单），六项 docstring + C1/C2/C3。
- B221-V3R26 `_build_function_def` 常量折叠注解：全常量注解元组被 CPython 折叠为 `LOAD_CONST ('return', None)`，表达式重建器产出 Constant 而非 Tuple，旧代码恒走 `.get('return')` → None。新增 Constant+tuple 分支还原 (name,type) 交替序列，`-> None` / `-> 'FastStack'` 恢复。
- 实测：G2c 子集 2 EQUAL → 4 EQUAL（REAL46-040 6 diffs→0、042 2→0、045 33→31）；A/B 24 个 stdlib pyc 零回归（24/24 sha 一致）；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 24/24；freeze_check 3/5（2 项为 LF/CRLF 口径与外部判据文件缺失）。
- 402 八分片 / small34 本沙箱不可达（pyc 缺失、index 为 Windows 绝对路径），如实登记；v9 overall 维持 BLOCKED，四桶 395/0/719/442 不变。

## 2026-10-26 rr-v5r27：scope 声明位于 docstring 之后 + for 前导区连续 STORE 整组归约

- B222-V3R26 `_build_function_def`：`scope_stmts` 原先无条件前置到 `body[0]`，把 docstring 挤到第二位，重编译后 docstring 退化为行 NOP、`__doc__` 变 None。改为按 `Expr(Constant(str))` 首节点结构判定，命中时插到索引 1。
- B223-V3R26 `_loop_extract_for_iter_pre_stmts`：for 循环前导块的多目标赋值 `a, b = e1, e2` 被逐 STORE 归约，首 STORE 吞掉全部值、次 STORE 无值可配。新增 N>=2 连续 STORE 段整组归约（值段禁 COPY/SWAP/UNPACK，栈深 >= N，目标反序），吸并段记 `_unpack_skip_remaining`。
- 实测：G2c 子集 4 EQUAL → **6 EQUAL / 1 DIFFERENT**（041、046 清零；仅剩 045 的 31 diffs，已定位为 report dict 整体丢失）；A/B 24 模块 5 处变化逐项核对全为改进（enum/shutil/functools/logging/tempfile），零回归；pytest 七套件名单逐位一致。

## 2026-10-26 rr-v5r28：BoolOp 尾部内联 if 的 IF_TRUE 极性

- B224-V3R26 `_generate_boolop_impl` R89 内联 if 提取：`POP_JUMP_FORWARD_IF_TRUE` 的语义是条件为真时跳转到跳转目标、fall-through 为假值路径。原实现把跳转目标当 then 臂，测试表达式重建后又经 `_if_negate_r89` 对 TRUE/NONE 取反一次 ⇒ 双重翻转，`if not f(x): sys.exit(...)` 后的 `tmp = ...` 被搬进 if 体。改为 IF_TRUE 分支 then 臂取 fall-through、else 臂取跳转目标；FALSE 与无极性路径逐位不变（C3）。
- 实测：G2c 子集维持 6 EQUAL / 1 DIFFERENT（045 仍 31 diffs，但 `cmd_single` 语义已恢复源码形态，残差收敛到「tuple 容器构造三元吞掉 print + 大 dict 字面量赋值丢失」第二族）；A/B `new3` vs `new4` 24/24 一致（零回归），`old2` vs `new4` 仍为 19 same / 5 diff 且 5 处全为 rr-v5r27 已核对的改进；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 24/24。
- 最小复现 `/tmp/mini7`：修复后与源码逐行一致（`sys.exit` 在 if 体内、`tmp = ...` 在 if 之后）。判定空间四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r29：容器字面量中兄弟推导式的 GET_ITER/MAKE_FUNCTION 误判

- B225-V3R29 分析层 `_identify_ternary_regions`：字典/集合字面量中紧跟三元项的兄弟推导式会先在汇合块前段执行 `LOAD_CONST <comp>; MAKE_FUNCTION; <iterable>; GET_ITER; CALL 0`，三元结果仍在栈底。原扫描只看 opcode 归属，把该 `GET_ITER` 误认成「三元作 for 迭代器」，汇合块被三元吞并。新增 `_mb_ternary_is_tos(target_instr)` 栈净值判据（从块起点累加 `_stack_effect` 净值，目标前净值 == 0 ⇔ 目标直接作用于三元结果），`GET_ITER/GET_AITER` 分支加该门；只否决、不改扫描顺序与块归属。
- B225-V3R29 生成层 `_generate_ternary`：同一 `MAKE_FUNCTION` 被误认成「三元作装饰器/默认值/注解的 FunctionDef」，产出 `@(ternary) def <target>` 伪函数并吞掉宿主容器赋值。MAKE_FUNCTION 分支加 `not _const_code_is_async_comprehension(_code_obj)` 守卫，推导式代码对象放行给下方 `initial_stack=[ternary]` 容器重建路径。
- 实测：G2c 子集维持 6 EQUAL / 1 DIFFERENT；REAL46-045 仍 31 diffs 但按维度统计为 `{'R7': 31}`（无结构维度，残差只剩 `cmd_selfcheck` 的 listcomp 调用被吞）；A/B `new4` vs `new5` 24/24 一致（零回归），`old2` vs `new5` 仍为 19 same / 5 diff 且 5 处全为 rr-v5r27 已核对的改进；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 24/24。
- 最小复现 `/tmp/mini16`（f1–f5）：修复后全部与源码语义一致。判定空间四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r30：try/finally 副本 ternary 预登记的循环变量复用误判

- B226-V3R30 现象：`try: <前导语句>; <三元赋值>` + `finally:` 的整个 try 臂退化为 `try: pass`（前导语句与三元赋值一起消失）。最小复现 `/tmp/mini22` 修复前即 `try: pass`。
- 根因：`filtered` 全局预标记段与 `_generate_try_body` 的「finally normal path 副本」预登记段都写成 `_sib = False` 后 `for _sib in children`，复用循环变量；循环未 `break` 结束时 `_sib` 残留为最后一个 child 对象（恒真值）⇒ 「存在 finally 结构副本」误判成立 ⇒ ternary 进 `_ids`（顶层 `if id(r) in _ids: continue`）且全部块进 `generated_blocks`（块走查 `continue`）⇒ 整臂蒸发。
- 判据（I.4 白名单：区域成员关系 + 块数事实）：`_has_copy` 只在真正命中「等块数 sibling ternary 的 entry ∈ 本域 `finally_blocks`」时置真，与循环变量解耦；仅换独立布尔量，命中条件与注册集合逐位不变（C3）。同文件第 36381 行的第三处 `for _sib in region.children` 在循环体内即 `_ids.add(id(child)); break`，无复用缺陷，未改动。
- 实测：G2c 子集维持 6 EQUAL / 1 DIFFERENT（`prod7`/`prod8`/`prod9` 三次重生成逐字节相同 ⇒ B226 对 402 语料零影响，属独立族；045 仍 31 diffs 全为 `{'R7': 31}`）；A/B `new5` vs `new6`、`new6` vs `new7` 均 24/24 一致，`old2` vs `new7` 仍 19 same / 5 diff 且 5 处全为 rr-v5r27 已核对的改进；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 24/24。
- 最小复现 `/tmp/mini22` 修复后恢复 `try: a = len(rows); rate = 1 if a else None`；`/tmp/mini21` 的 f1/f3 同步恢复。`return <name>` 仍丢失（`/tmp/mini24` 无 try 对照证明只在 try/finally 上下文），登记为下一族。判定空间四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r31：try/finally 体内三元赋值后的 return 丢失

- B227-V3R31 现象：`try: ...; x = <三元>; return x` + `finally: <含关键字实参的调用>` 中三元赋值恢复后 `return x` 整条丢失。
- 根因：CPython 3.11 把返回值在 merge 块压栈后穿越 finally 内联副本，由副本末尾 `RETURN_VALUE` 消费。该 merge 块已被 TernaryRegion 认领 ⇒ 既有 `_b34c_finally_deferred_return` 从未被调用；三元 A2 分支又以「后继块 RETURN_VALUE 前缀无 POP_TOP」为前提，finally 副本必然带 POP_TOP ⇒ 恒不命中。此外 `_DEFERRED_RET_CLEANUP_OPS` 缺 `KW_NAMES`（净效应 0 的关键字实参名登记），链分类被整体否决。
- 修复：白名单补 `KW_NAMES`；A2 残值分支在既有判据不命中后委托 `_b34c_finally_deferred_return(region.merge_block, emit_prefix=False)`；新增关键字参数让调用方跳过前缀语句（三元入口已发射过，重复会产出伪语句 `report = {}`）。返回 None 时逐位落回既有路径（C3）。
- 实测：G2c 维持 6 EQUAL / 1 DIFFERENT（`prod9` vs `prod10` 逐字节相同）；A/B `new7` vs `new8` 24/24 一致，`old2` vs `new8` 仍 19 same / 5 diff（全为 rr-v5r27 已核对的改进）；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 24/24；`/tmp/mini16`、`/tmp/mini24` 产物逐字节不变。
- 最小复现 `/tmp/mini22`、`/tmp/mini21`（f1–f4）修复后全部与源码语义一致。残差收敛到 `cmd_selfcheck` 内层 try 体语句丢失（下一族）。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r32：try 内嵌 for + 内层 try/except 的体语句丢失与续体错位

- B228-V3R32 现象：`try:` 内嵌 `for`、`for` 体内再嵌 `try/except`（外层可再带 `finally`）时，内层 try 体语句蒸发为 `try: pass`、try 之后的续体语句被搬进 `except` 体（`/tmp/mini25` f2、`/tmp/mini26` g1）。
- 修复①分析层 `_collect_finally_body_blocks`：副本登记判据 `is_try_exit_successor or block_in_any_range` 只要其一成立即登记；外层 try 块后继恰是同一保护跨度内的内层 try 体块 ⇒ 误登记为 finally 正常路径副本 ⇒ 生成层 `[B142]` 门整块抑制。新增 `nested_ranges`（异常表里 target 不属于本 finally handler 的跨度 = 内层结构保护区），块内任一指令落入即跳过。`finally_copy_blocks` 从 `{146:3,178:9,18:7,126:5}` 收敛为 `{146:3,178:9,126:5}`。
- 修复②生成层 `_loop_collect_child_regions`：`iter_setup_block` 原按 `header.predecessors` 集合遍历序取首个含 `GET_ITER/GET_AITER` 的前驱，回边块（实测 @152）先被取到 ⇒ `_loop_generate_body` 整块登记 generated 而不发射。改为优先读 `metadata['for_iter_setup']`，缺失时按起始偏移升序扫描（与 `_classify_loop_type` 同口径）。
- 修复③分析层 Pattern C：POP_EXCEPT 之后的块若同时处在 try 体正常流可达集内，它是 try 语句之后的续体，不是 handler 臂收尾。新增 `_try_flow_reach`（从 try 体入口沿正常边传播，剔除异常边与 handler/finally 块），worklist 入队前 `continue`。handler body 从 `['B3@70','B13@72','B14@76','B10@226','B15@126','B7@102']` 收敛为 `['B3@70','B13@72','B14@76']`。
- 修复④生成层 W13 嵌套重建：合并形态（finally region 吸收配对 except）中 try 体只有前缀属内层 try 体，其余是续体。分析层登记 `metadata['merged_except_try_range']`，`_generate_try_body` 按上界登记 `_w13_inner_body_len`，W13 拆 `_w13_inner + _w13_rest`；未登记该事实的 region 逐位不变（C3）。
- 实测：`/tmp/mini25/out12.py` f1/f2/f3 与源码逐行一致；`/tmp/mini26/out5.py` g1/g2/g3 与源码语义一致。G2c 子集维持 6 EQUAL / 1 DIFFERENT，REAL46-045 从 31 diffs 收敛到 29 diffs（全 `{'R7': 29}`），`try: pass` 恢复为 `res = compare_pyc(pyc, _compile(mutated, tmp, 'mut.pyc'))`；A/B `new8` vs `new9` 22/24 一致，2 处差异全为改进（logging/shutil 共四处 `try: pass` 恢复语句）；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 144/144。
- 新暴露残差：`/tmp/mini27` pc2（`else: return a` + `finally` 合并形态）把 `return None` 替换为 `os.getcwd()`——else 臂的 finally 内联副本 B14@134 被误并入 handler body，登记为下一族。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r33：except 臂 `return None` 被 finally 内联副本覆盖

- B229-V3R33 现象：`try: a = int(x)` + `except ValueError as e: print(e); return None` + `else: return a` + `finally: os.getcwd()` 中 `return None` 被替换为 `os.getcwd()`（pc1 无 as-var / 无 else 臂时正确，`/tmp/mini27`）。
- 根因：`_handler_arm_block_is_finally_copy` 的 `_b115_user_opcode_seq` 把块内**所有** `LOAD_CONST None` 一律当框架簿记滤除。臂块 B14@134（`LOAD_GLOBAL os; LOAD_ATTR getcwd; PRECALL 0; CALL 0; POP_TOP; LOAD_CONST None; RETURN_VALUE`）剥帧后用户序列 `[LOAD_GLOBAL, LOAD_ATTR, CALL]`，与本 region finally 异常副本体 B7@192（剥 `PUSH_EXC_INFO` 头与 `RERAISE` 尾后同序列）**等长** ⇒ 严格前缀判据 `len(arm) > len(body)` 恒不命中 ⇒ 臂降级为裸 Expr：finally 副本语句泄漏进 except 体、`return None` 丢失。
- 修复：`LOAD_CONST None` 的两种身份分开——紧跟 `STORE_*` 的是 except as-var 清理三元组（`LOAD_CONST None + STORE + DELETE`）的框架簿记；其余位置（尤其 `RETURN_VALUE` 之前）是 `return None` 的返回值装载，属臂自身终态 Return 的用户指令。只读块内指令序 + `_STORE_TARGET_OPS`（I.4 白名单），无名字/偏移/阈值判据。
- 实测：`/tmp/mini27/out3.py` pc1/pc2/g1 全部与源码语义一致（本轮用当前工作树重生成 `recheck.py` 逐字节复核一致）；G2c 子集维持 6 EQUAL / 1 DIFFERENT（`prod13` vs `prod12` 七条逐字节相同，045 仍 29 diffs 全 `{'R7': 29}`）；A/B `new10` vs `new11` 24/24 逐字节一致；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 150/150 failures=0。
- 残差：REAL46-045 的 29 diffs 全为 `$.metadata.code.co_consts.v[...]`（`from __future__ import annotations` 下注解存为字符串，产物渲染为裸名字），已定位全部注解发射点，登记为下一族「注解字符串化」。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r34：PEP 563 注解字符串化

- B230-V3R34 现象：`from __future__ import annotations` 的模块产物把注解多包一层引号（`def f(x: 'str', y: 'int'=3) -> 'str | None':`），重编译后 `co_consts` 存为带引号文本/类型对象，触发 REAL46-045 的 29 处 `$.metadata.code.co_consts.v[...]` 差异（`/tmp/mini28`）。
- 根因：PEP 563（`__future__.annotations.compiler_flag = 0x1000000`）生效时 CPython 在编译期把注解表达式字符串化存入 `co_consts`（`x: str` → `'str'`，`x: 'str'` → `"'str'"`）。生成器把注解节点当普通表达式发射，`Constant` 分支走 `repr(value)`、`_generate_expression` 对字符串常量同样加引号，于是重编译不再产生源码原文。
- 修复：`CodeGenerator.__init__` 新增 `future_annotations`（默认 `False` ⇒ 未启用该 future 的模块逐位不变，C3），由入口按 `co_flags & 0x1000000` 传入；新增纯查询 `_annotation_raw_text`（future 生效且注解节点为字符串常量时返回原文，否则 `None`）；8 处注解发射点（函数/参数/返回/kwonly/AnnAssign 的 dict 与 ASTNode 两条路径）加「原文优先、否则原路径」分支。判据只读 `co_flags` 的 future 位 + 注解节点类型与值（I.4 白名单）。
- 实测：`/tmp/mini28/out2.py` 恢复 `def f(x: str, y: int=3) -> str | None:`；G2c 子集维持 6 EQUAL / 1 DIFFERENT，REAL46-045 由 29 diffs 收敛到 4 diffs（3 条 `code_sha` + 1 条 `consts_len` 43 vs 42），`co_consts` 全部对齐；A/B `new11` vs `new12` 24/24 逐字节一致；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 148/148 failures=0。
- 残差：REAL46-045 剩余 4 条全在 `cmd_batch` code object——`BUILD_CONST_KEY_MAP` 多键字典首值为纯 LOAD 表达式、后续含三元/推导式时整体丢失（`/tmp/mini30`），登记 B231；`z: dict[str, int] = {}` 的 AnnAssign 注解在产物中仍丢失，需另查。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r35：三元 cond 预加载的二元运算未折叠

- B231-V3R35 现象：`BUILD_CONST_KEY_MAP` 多键字典首/次值均为纯 LOAD 表达式（`time.strftime(...)`、`round(time.time() - t0, 1)`）、后续含三元与推导式时，产物把前两个值渲染为 `round` 与 `time.time()(t0, 1)`，且 `co_consts` 少 1 项（`/tmp/mini30`）。
- 根因：`_generate_ternary` 的 cond_block 预加载折叠链缺**二元运算**分支。`BINARY_OP` 不折叠 ⇒ 预加载项停在操作数粒度 `[round, time.time(), t0, 1]` ⇒ 紧随的 `CALL 2` 弹 `1`/`t0` 作实参、把 `time.time()` 当 func ⇒ `round` 留作下一个字典值，`BUILD_CONST_KEY_MAP 11` 整体错位一格。`/tmp/probe_blocks31.py` 证明这些值的指令在 cond_block preload 区内（非 merge 块），排除 `_extract_dict_prefix_values` 路径。
- 修复：折叠链新增 `BINARY_OP`/`COMPARE_OP`/`IS_OP`/`CONTAINS_OP` 分支——弹「右项, 左项」按源序拼成分组指令列表、追加运算符指令，与既有 `BINARY_SUBSCR`（同为弹 2 压 1）完全同形；判据只读操作码类别与预加载项数（I.4 白名单）。
- 实测：`/tmp/mini30/out_fix.py` 第 31 行 11 键 11 值全部正确；G2c 子集维持 6 EQUAL / 1 DIFFERENT，REAL46-045 由 4 diffs 收敛到 3 diffs（`cmd_single`/`cmd_batch`/`cmd_compare` 三个嵌套 code object 的 `code_sha`）；A/B `new12` vs `new13` 24/24 逐字节一致；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 145/145 failures=0。
- 新暴露残差：`cmd_batch` 多发射一条 `JUMP_BACKWARD`（`elif i % 25 == 0:` 被渲染成 `if ...: else: continue`，登记 B232）；`cmd_single` 多 28 字节，`@832 JUMP_FORWARD` vs `RETURN_VALUE`；`cmd_compare` 的 `co_consts` 顺序差异与 `<genexpr>` 丢 `'%-14s'`。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r36：循环体末条 if/elif 的假边纯回边块被误认成 else 臂

- B232-V3R36 现象：`for ...: if cond: ... elif i % 25 == 0: ...`（源码无 else）的产物给每个 `elif` 臂补出伪 `else: continue`，重编译多一条 `JUMP_BACKWARD`（`cmd_batch` 整体 +2 字节，`/tmp/mini32`/`/tmp/mini33`）。
- 根因：`_if_generate_normal` 的 merge_block 假臂认领段（R40-A2）以 `not _mb_meaningful` 单独放行——merge 块剥噪后为空（纯 `JUMP_BACKWARD`→循环头）即被改认成 `else_blocks`，而它其实是循环的自然迭代回边。`/tmp/probe_b232.py` 实测 `IfRegion@entry=5`（elif 臂）的 `_if_false_path_is_loop_iteration` 为 True、外层 `IfRegion@entry=3` 为 False，谓词恰好只命中末条形态。
- 修复：认领门追加 `not self._if_false_path_is_loop_iteration(region)`（复用既有谓词 :29876，与 `[R3-Continue]` 补发段、`_process_if_blocks` 的 CONTINUE 角色抑制同源），谓词为真时保留 merge 角色、交给父循环按自然回边发射；判据只读条件入口的后继集合与「纯回边」结构事实（I.4 白名单）。
- 实测：`/tmp/mini32/out_fix.py` v1/v2/v3 与 `/tmp/mini33/out_fix.py` a/b/c/d 共 7 个函数用 `/tmp/cmpcodes.py` 逐指令 + `co_consts` 比对**全部 MATCH**；G2c 子集维持 6 EQUAL / 1 DIFFERENT，REAL46-045 由 3 diffs 收敛到 2 diffs（`cmd_batch` 的 `co_code` 已逐字节对齐）；A/B `new13` vs `new14` 零新增 CODE 差异且 `email__utils::_check_parenthesis` 一处 CODE 差异消失（净 -1）；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 145/145 failures=0。
- 新暴露残差：`cmd_single`（838 vs 866，首处 `@832 JUMP_FORWARD` vs `RETURN_VALUE`，登记 B233）与 `cmd_compare` + `<genexpr>`（`co_consts` 顺序差异 + 推导式丢 `'%-14s'`，登记 B234）。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r37：三元后继三元被升级成伪 if

- B233-V3R37 现象：`print('[single] status=%s ...' % (...))` 紧跟 `return 0 if row['status'] == 'success' else 1` 时，产物渲染为伪 `if row['status'] == 'success': return 0` + 重复的 `return 0 if ... else 1`（重复条件 + 重复 then 臂，`cmd_single` 838 vs 866 字节，`/tmp/mini34/v.py::g1`）。
- 根因：`_emit_post_extra_with_if_upgrade` 的 `_r59_claimable` 让位集合缺 `TernaryRegion`。外层三元（`entry=B1 merge=B4`）的 `post_extra` 只有 `Expr(Compare)`——正是内层三元（`entry=B4 merge=B7`）自身的条件表达式；merge 块 B4 末条的 `POP_JUMP_FORWARD_IF_FALSE` 属于内层三元，不是「三元消费语句之后的独立语句」。缺类 ⇒ 该条件被升级成伪 If，随后内层三元又发射完整 return。`/tmp/probe_postextra34b.py` 实测 `POST_EXTRA entry=1 merge=4 items=['Expr(Compare)']`，`/tmp/probe_bs34.py` 实测伪 If 由 `_emit_post_extra_with_if_upgrade.59095` 合成。
- 修复：让位集合补入 `TernaryRegion`，与既有 7 类同一收口（`results.extend(post_extra[:-1]); return`），末项条件由内层三元自身重建发射；判据只读「merge_block 是否为另一未生成区域的 entry」的区域身份事实（I.4 白名单）。
- 实测：`/tmp/mini34/out_fix.py` 的 `g1`/`g2`/`g3` 用 `/tmp/cmpcodes.py` 逐指令 + `co_consts` 比对 58/11/16 条指令**全部 MATCH**，`/tmp/mini10/out_r37.py` 的 `f1` 同步恢复；`/tmp/mini34/wout_fix.py` 与修复前 `wout.py` 逐字节相同（`h1` 属另一根因 B235）；G2c 子集维持 6 EQUAL / 1 DIFFERENT，REAL46-045 由 2 diffs 收敛到 **1 diff**（`cmd_single` 的 `code_sha` 已消失，仅剩 `cmd_compare`）；A/B `new14` vs `new15` 文本 24/24 逐字节相同、字节码问题集零差异；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 146/146 failures=0。
- 新暴露残差：REAL46-045 仅剩 `cmd_compare`（`co_consts` 顺序 + `<genexpr>` 丢 `'%-14s'`，B234）；`print('%s' % (ternary))` 的 merge 消费重建错误 `(cond)('-' % 'y')`（B235）；AnnAssign 注解丢失。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r38：三元 cond 前导区多目标赋值丢目标

- B234-V3R38 现象：`da, db = before['units_success'], after['units_success']` 与 `ta, tb = before['units_total'], after['units_total']` 位于某 TernaryRegion 的 `condition_block` 前导区，产物只保留 `db`/`tb`，`da`/`ta` 整条目标丢失并退化为未定义全局（`cmd_compare` 1986 vs 1994 字节，`/tmp/mini35`）。
- 根因：CPython 3.11 对纯名字多目标 `a, b = e1, e2` 生成 `LOAD e1; LOAD e2; STORE b; STORE a`（反源序连续 STORE，无 SWAP/UNPACK/COPY）。`_build_statements_from_instructions` 逐 STORE 独立重建：首 STORE 把整段值指令当单一 RHS、只弹栈顶，随后目标因 `_stmt_instrs` 已清空而无值可配 ⇒ `_build_store_statement` 返回 `None` ⇒ 整条目标静默丢弃。`[B223-V3R26]` 连续 STORE 段整组归约只覆盖 `for_iter_setup` 前导区，`Pattern SIG2` 只覆盖块首形态，均未覆盖三元 condition 前导区（`/tmp/probe_blocks35.py`、`/tmp/probe_skip35.py`、`/tmp/probe_caller35.py`、`/tmp/probe_dispatch35b.py`）。
- 修复：STORE 分支前新增 `[B234-V3R38]` 连续简单名 STORE 段整组归约——识别 N>=2 连续 `STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF`，要求值段无 `COPY/SWAP/UNPACK_SEQUENCE/UNPACK_EX` 且重建后栈深 >= N；整组归约为单一 `Assign(Tuple(源序目标), Tuple(压栈序值))`，被吸并次级 STORE 经 `_bsi_skip_until` 跳过。判据只读块内操作码序 + 值栈净效应（I.4 白名单），无名字/偏移/阈值特判；任一守卫不命中即逐位落回旧路径（C3）；模块根/类体/函数体/三元条件前导区共用本指令级归约（C1 局部消费、C2 同语义）。
- 实测：`/tmp/mini35/out_fix.py` 的 `g2`/`g3`/`g4` 用 `/tmp/cmpcodes.py` 逐指令 + `co_consts` 比对 27/13/13 条**全部 MATCH**（`g1` 尾随 `print` 蒸发属另一根因）；G2c 子集 **7/7 全 EQUAL**（REAL46-045 由 1 diff 收敛到 0 diff，`/tmp/disdiff2.py` 的 `@1582` 整段错位消失）；A/B `new16` vs `new15` 文本 24/24 逐字节相同、`/tmp/ab/bytecmp.py` 问题集零差异；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 146/146 failures=0。
- 新暴露残差：`cmd_compare` 的 `<genexpr>` 丢 `'%-14s'` 模板（`co_consts` 少一项，`FOR_ITER 158 vs 152`，登记 B236）；`/tmp/mini35/v.py::g1` 尾随 `print` 蒸发（Pattern C2 降级后未交回通用重建）；`print('%s' % (ternary))` merge 消费重建错误（B235）；AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r39：推导式元素位三元的「前导压栈项 + 汇合点后缀」丢失

- B236-V3R39 现象：元素位 `F % (A if c else B)` 的推导式产物只剩裸三元——格式串常量与尾部 `BINARY_OP %` 整段消失（`<genexpr>` 162 vs 156 字节，`co_consts` 少 `('str','%-14s')`，`FOR_ITER 158` vs `152`，`/tmp/mini36`、`/tmp/mini37`）。
- 根因：CPython 3.11 对元素位 `F % (A if c else B)` 发射「cond 块先 `LOAD_CONST F` 再求条件、merge 块 `BINARY_OP %` 消费三元值」。`ComprehensionGenerator._detect_comp_ternary` 的 `cond_instrs` 从目标存储之后切起，`reconstruct` 只返回栈顶（条件）⇒ 前缀 `F` 静默丢弃；merge 块后缀除 walrus 外从不重建 ⇒ 尾部运算整段丢失。`/tmp/probe_gen36b.py` 实测该 genexpr 内 `_generate_ternary` 从未被调用（不走区域生成器路径）。
- 修复：`_detect_comp_ternary` 末端新增「前导压栈项 + 汇合点后缀消费」整组归约——条件走单段整窗重建通道 ∧ `cond_instrs` 重建后非 PUSH_NULL 栈深 >= 2 ∧ merge 偏移到追加点之间后缀窗非空 ∧ 追加点非 `MAP_ADD` 时，以前导项 + 三元值作初栈逐条处理后缀指令，栈上唯一非 PUSH_NULL 项即整组结果。判据只读同层指令 opcode 与栈净效应（I.4 白名单）；任一守卫不命中即逐字返回原 IfExp（C3）；三元整体作为父节点的一个抽象子结点（C2）。
- 实测：`/tmp/mini36b/out.py` 的 h1–h5 指令条数 19/17/17/17/21 与原始逐位相同（仅 code object 地址差异）；`/tmp/mini37` 的 k1/k4/k5 恢复 `'%s!' % (...)` 形态，嵌套比对由 4 条 CODE-DIFF 收敛到 1 条（仅 k7）；G2c 子集 7/7 全 EQUAL，`/tmp/cmpnested45.py` 对 REAL46-045 **零 CODE-DIFF**（嵌套 code object 全部逐字节对齐）；A/B `new17` vs `new16` 文本 24/24 逐字节相同、问题集零差异；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 295/295 failures=0。
- 新暴露残差：推导式元素位 BoolOp（`and`/`or`）整族未归约——`[x or y ...]`→`[y ...]`、`[x and y ...]`→`[y ...]` 语义错，`x and x or 'e'` 的 `JUMP_IF_TRUE_OR_POP` 汇合点未被识别（`/tmp/mini38`、`/tmp/mini37::k7`），登记 B237；`m5` 另叠闭包丢帧。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r40：推导式元素位 and/or 短路丢左操作数

- B237-V3R40 现象：推导式元素位的 `and`/`or` 整族丢左操作数——`[x or y for x in xs]` → `[y ...]`、`[x and y for x in xs]` → `[y ...]`（`/tmp/mini38` 的 `m3`/`m4`，语义错）；融合形 `[x and y or 'e' ...]` → `[y if x else 'e']`（`y` 为假值时丢掉 `'e'`）；`'%s' % (x and y or 'e')` 另丢格式串前导与 `%` 后缀；嵌套形 `[x and y or 'e' if x else 'z' ...]` → `['e' if x else 'z']`；对照 `/tmp/mini37/v.py::k7`（`'%-14s' % (x and x or 'e')`）退化为三元且重编译 `JUMP_FORWARD` 与原始不一致。
- 根因：CPython 3.11 对「结果即表达式值」位置（推导式元素等）的 `A and B`/`A or B` 发射 `JUMP_IF_FALSE_OR_POP`/`JUMP_IF_TRUE_OR_POP`（短路时 A 自身即结果并保留在栈上、不短路时弹出 A 取 B）。`ExpressionReconstructor._process_instruction` 无该指令分支 ⇒ A 静默留在栈上、B 压顶，`reconstruct` 只取栈顶返回 B（`/tmp/probe_recbool.py` 实测 `m3` 整段返回 `Return(List([Name('y')]))`）。而 `A and B or C` 的融合形 `<A>; POP_JUMP_FORWARD_IF_FALSE <C>; <B>; JUMP_IF_TRUE_OR_POP <merge>; <C>` 又被既有三元通道当成普通分支跳转，产出 `B if A else C` 并把前导项 F 与 merge 后缀整段丢掉。
- 修复：① 表达式重建器新增 `_fold_boolop_keep_or_pop` 开关（默认关闭，既有调用路径逐位不变）与 keep-or-pop 栈机建模（弹左操作数 → 合并 Pending → `reconstruct` 末尾与右操作数合成单一 `BoolOp`，链式逐级左折叠），只由推导式元素窗显式开启；② `ComprehensionGenerator` 新增 `_b237_kop_window`：首个跳转为前向 IF_FALSE 型 ∧ 真值区终结于 `JUMP_IF_TRUE_OR_POP` ∧ 真值区无其它跳转 ∧ 追加点非 `MAP_ADD` 时，条件区取栈顶为 A（其余为前导项 F）、真值区重建 B、假值区重建 C，合成 `BoolOp(or, [BoolOp(and, [A, B]), C])`，有后缀则以 `F... + [值]` 作初栈逐条处理后缀（嵌套同族形态递归）；③ 外层三元的真值区自身含跳转时先走 `_b237_kop_window`（窗口含真值区终结跳转）。判据只读同层指令 opcode 与跳转目标（I.4 白名单），不命中返回 None 逐字回落既有通道（C3）。
- 实测：`/tmp/mini38d/out.py` 的 `m1`–`m5` 全部恢复源码形态，`/tmp/cmpnested38.py` **零 CODE-DIFF**（先前的 `MAKE_CELL`/`COPY_FREE_VARS` 丢帧随之消失）；`/tmp/mini37c2/out.py` 的 `k7` 恢复，`/tmp/cmpnested37.py` 由 1 条 CODE-DIFF 收敛到零输出；G2c 子集 7/7 全 EQUAL，`/tmp/cmpnested45.py` 对 REAL46-045 零 CODE-DIFF；A/B `new18` vs `new17` 文本 24/24 逐字节相同、问题集零差异；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 293/293 failures=0。
- 新暴露残差：更长的短路链（`A and B and C or D`、`A or B and C`）尚未纳入复现集，`BoolOpPending` 的左折叠只对 `A or B or C` 推导过；`/tmp/mini35/v.py::g1` 尾随 `print` 蒸发（Pattern C2 降级未交回通用重建）；B235 的 merge 消费重建错误、AnnAssign 注解丢失、三引号渲染仍在。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r41：`x is None` 条件三元未登记区域 + f-string 跨块被调对象误取实参

- B235-V3R41 现象：`print('%s' % ('-' if row['x'] is None else 'y'))` 的产物为 `(row['x'] is None)('-' % 'y')`（三元退化为裸条件、`print` 与 `'%s'` 前导蒸发）；f-string 形 `print(f"{row['a']!s} {'-' if row['x'] is None else 'y'!s}")` 的产物为 `row(f"...")`（宿主 `print` 被替换成第一个实参表达式里的 `row`）；两形态末尾都多出裸表达式语句 `row['status'] == 'success'`（紧随其后的三元条件被重复发射）。复现 `/tmp/mini10/v.py` 的 `f1`/`f2`/`f3`、`/tmp/mini34/v.py` 的 `h1`/`h2`/`h3`。
- 根因四处：① `ExpressionReconstructor._process_instruction` 的 `POP_JUMP_FORWARD_IF_NOT_NONE` 分支只压栈 `Compare(is)`、不登记三元区域（镜像的 `_IF_NONE` 分支有 `_open_ternary_region`）⇒ 汇合处 `[test, body, orelse]` 仍是三个独立栈项，被 `BINARY_OP` 当 `'-' % 'y'`、条件节点被 `CALL` 当函数对象；② `_generate_host_prefix_ternary_statement` 的 `tail_instrs` 段把同一极大直线块里**属于另一未生成区域**的下一三元条件一并物化；③ `_ternary_pending_callee` 把「独立 `PUSH_NULL` 指令」与「3.11 把空对象标记编进 `LOAD_GLOBAL` 操作数低位」两种编码混用同一「取下一指令为 callee」推导 ⇒ `LOAD_GLOBAL print(NULL) ; LOAD_FAST row` 把 `LOAD_FAST row` 当 callee；④ `_try_wrap_fstring_pending_call` 的 `_rest` 段同样物化了下一区域的条件测试。
- 修复：① 在压栈后按镜像补 `_open_ternary_region`（`fold_cond_jump_ternary=True` 门控，默认关闭 ⇒ 既有调用路径逐位不变）；② / ④ 增加区域归属守卫——尾段首指令所在块若是其它未生成区域的 `entry`/`condition_block` 则不物化，交回该区域自身发射；③ 新增 `_null_in_load_global` 区分两种编码，独立 `PUSH_NULL` 形态才走「下一指令为 callee」，低位标记形态交给既有 `[R63 Fix2a]` 段（callee 即该 `LOAD_GLOBAL` 自身）。所有判据只读同层 opcode / `arg & 1` 位 / 区域归属（I.4 白名单），不命中即逐位回落（C3）。
- 实测：`/tmp/mini10/b2/out.py` 的 `f1`/`f2`/`f3` 与 `/tmp/mini34/c2/out.py` 的 `g1`/`g2`/`g3` 经 `/tmp/cmpany.py` 全部 `total diffs = 0`（多余条件行同时消失）；对照族 `/tmp/mini37`/`min36`/`min30`/`min28`/`min27` 重生成后亦全部 `total diffs = 0`，`/tmp/mini38` 的 `/tmp/cmpnested38.py` 零输出；G2c 子集 7/7 全 EQUAL，`/tmp/cmpnested45.py` 对 REAL46-045 零 CODE-DIFF；A/B `new19` vs `new18` 文本 24/24 逐字节相同、问题集零差异；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 293/293 failures=0。
- 新暴露残差：`/tmp/mini35/v.py::g1` 多目标赋值后尾随 `print(da, db)` 整段蒸发（Pattern C2 无 SWAP 解包路径 `_ns_n = 0` 降级后未交回通用重建）；推导式元素位更长短路链（`A and B and C or D`、`A or B and C`）未纳入复现集；`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r42：无 SWAP 解包路径剩余段未按语句边界切分

- B238-V3R42 现象：`da, db = before['a'], after['a']` 紧跟 `print(da, db)` 时，产物只剩 `da, db = (before['a'], after['a'])`、`print` 整段蒸发并退化为隐式 `return None`（`/tmp/mini35/v.py::g1`，`orig=17 prod=11`）；同族 `g2`（两段多目标赋值 + 四参 `print`）与 `g4`（`x, y = 1, 2; print(x, y)`）同样受影响，`g3`（尾随 `return da, db`）不受影响。
- 根因：`_generate_block_statements_body` 的 Pattern C2 无 SWAP 解包路径本身识别正确（`_ns_n=2`），但末 STORE 之后的**剩余段**被整体当作 return 值交给 `reconstruct`——该段既含完整的兄弟语句（`LOAD_GLOBAL print; LOAD_FAST da; LOAD_FAST db; PRECALL 2; CALL 2; POP_TOP`）又含 `LOAD_CONST None; RETURN_VALUE`，`reconstruct` 只取栈顶 `Constant(None)`，前面的兄弟语句被静默丢弃（`/tmp/probe_ns41b.py` 实测 `66967 rv_instrs = [LOAD_GLOBAL print, LOAD_FAST da, LOAD_FAST db, PRECALL 2, CALL 2, LOAD_CONST None]`）。
- 修复：剩余段按语句边界切分——从 `RETURN_VALUE`/`RETURN_CONST` 之前回扫到最近一条语句终结指令（复用 `_B54_STMT_TERMINATOR_OPS`，块内 opcode 序、I.4 白名单），其前段交 `_build_statements_from_instructions` 重建为兄弟语句（含任何跳转指令则不切，避免把控制流当直线语句），其后段仅重建 return 值；不含终结指令的段不可能含语句边界 ⇒ 行为与旧实现逐位相同（C3）。
- 实测：`/tmp/mini35/r42/out.py` 的 `g1`/`g2`/`g3`/`g4` 与源码逐行一致，`/tmp/cmpany.py` `total diffs = 0`（修复前 `g1` 报 `first diff @34: LOAD_GLOBAL print vs LOAD_CONST None`）；21 个复现集（mini10/16/17/21/22/24/25/26/27/28/29/30/32/33/34/35/36/37/38）重生成后逐条 `total diffs = 0`，无回归；G2c 子集 7/7 全 EQUAL，`/tmp/cmpnested45.py` 对 REAL46-045 零 CODE-DIFF；A/B `new20` vs `new19` 文本 24/24 逐字节相同、问题集零差异；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 295/295 failures=0。
- 新暴露残差：推导式元素位更长短路链（`A and B and C or D`、`A or B and C`）未纳入复现集；`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r43：嵌套 finally 出口臂误建 match + J 空间 v3 备料

- B239-V3R43 现象：`v_nest_fin_continue`（`try: try: if r == 0: continue finally: out.append(1) finally: out.append(2)`）被反编译成 `match r: case 0: <空体>` + `case _: out.append(r)`，`continue` 整段丢失（`JS-IF-017` / `JS-IF-021`；`/tmp/cmpany.py` 报 `CODE-DIFF v_nest_fin_continue len 362 vs 220`、`first diff @10: FOR_ITER 358 vs FOR_ITER 216`）。
- 根因两处：① `_b142_arm_exits_via_finally_copy` 只查真臂块自身是否 finally 副本台账成员，而真臂在此形态下是纯噪声桩块 `B4@30=[NOP]`、副本在其唯一后继 `B14@32` 上（台账键集 `{32, 120}`）⇒ 守卫恒不命中；② `_identify_match_regions` 主扫描完全缺这条守卫（另两个扫描入口都有），`B13@18` 仅凭 `_is_match_subject_block` 的 `[B215-R5R10]` 无 COPY 分支入选即被建成 `MatchRegion`。
- 修复：① 新增 `_b142_walk_noise_stub`，沿「块内无有义指令（仅 `RESUME`/`NOP`/`CACHE`/`EXTENDED_ARG`）且正常后继唯一」的桩链穿越到首个有义块再查台账；visited 集合保证终止、不设深度常数，后继不唯一/环回返回 `None`（逐位回落）。② 主扫描补同一否决，但只对非结构型候选生效（`not _has_match_op and not _is_case_pattern_block`），结构型 match 与 case pattern 块零影响。
- 实测：`/tmp/b239/out.py` 的 `v_nest_fin_continue` 恢复逐行一致、`/tmp/cmpany.py` `total diffs = 0`，`JS-IF-021` 同；语义差分两条由 `DIFFERENT ['R7','R7','R1','R1','R1','R1']` 转为 **`EQUAL` covered_5tuple**；19 个最小复现集 `/tmp/mini_regress.py` `TOTAL ISSUES = 0`；G2c 7/7 EQUAL；A/B `new21` vs `new20` 文本 24/24 逐字节相同 + 问题集零差异；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 164/164 failures=0。
- J 空间 v3 备料（Task 5.5）：新建 `tools/completeness/jspace_v3_prepare.py`，J v2 的 1556 条 pyc 在本树内全部缺失 ⇒ 按 `UNCHECKED_HASH` 全部重编译成功；`calls` 空条目在安全闸下从源 AST 派生（real-package 宿主依赖缺失的 376 条不派生）⇒ `with_calls=1086 / without_calls=470`。产物落在 `rounds/round13/jspace_v3/`，全量 C1–C5 三片并行仍在跑。
- 新暴露残差：推导式元素位更长短路链（`A and B and C or D`、`A or B and C`）未纳入复现集；`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染；J v3 的 470 条空 calls 中 376 条卡在宿主依赖（`six`/`jsonpickle` 未安装）。四桶 v2 口径 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r44：Try 入口折叠宿主行头 NOP 补发 + J v3 三桶读数收尾

- B241-V3R44 现象：`x04_try_deep_hosts.py` 的 `try_in_if`（`if 1: try: if 1: try: ... finally: ... except ValueError: ...`）产物 NOP 少 1（74 vs 76，`first diff @8: NOP None vs LOAD_CONST 1`），`try_in_while` 产物 NOP 多 1（76 vs 74，`first diff @10: LOAD_CONST 1 vs NOP None`），严格 R7 红。
- 根因两处：① 函数入口块被 `TryExceptRegion` 整体认领、不进入 `_generate_block_statements`，其块首连续 NOP 游程（宿主折叠行头）又被 `_nop_structural_veto` 的 V-T（游程终点 == 异常表 start）全部否决 ⇒ 游程无任何发射点，宿主 `if 1:` 行标记丢失；② `_is_protected_statement_nop` 与 `_nop_structural_veto` 双重命中的 NOP（`try_in_while` 的 `B10@6`，异常表 `(6,8,38)` start=6、游程终点 8 同为 start）仍被发射包裹占位 ⇒ 多 1 条 NOP。
- 修复：新增 `_try_entry_folded_head_units(entry_block)`——收集块首连续 NOP 游程，按「try_blocks 首块偏移 == 游程终点」计数共享该起点的 `TryExceptRegion` 数 k，游程前 `len-k` 个 NOP 逐一发射裸 pass 并登记 `_x01_claimed_nops`（后 k 个归 Try 语句再生）；并在 `_generate_block_statements_body` 与 `_generate_try_body` 两处受保护 NOP 发射点补 `and not self._nop_structural_veto(...)` 门。CPython 3.11 实测协议：入口游程 = 宿主折叠行头 + 每个共享同一起点的 try 行各 1 条。
- 实测：`JS-TRY-008`（x04）`/tmp/cmpany.py` `total diffs = 0`；四个合成探针 `try_try`/`if_try`/`while_try`/`try_body_empty_fold` 全部 `total diffs = 0`；`JS-TRY-*.pyc` 108 个 `tools/bc_cmp.py` 19 个 FAIL 与基线清单逐位一致（非本轮引入）；pytest 七套件 2 failed/277 passed/2 xpassed（两个失败为基线既有）。
- Task 5.5 读数收尾：110 条 held-out 记录用 `--judge tools/completeness/semantic_diff.py` 重跑（两片各 55/55 EQUAL）并入 `semantic_v3_merged.json`（1556 条，EQUAL 1130 / ERROR 424 / DIFFERENT 2）；`coverage_checker` 新读数 `J_total=1556 covered_5tuple=1050 probe_only=0 unexecuted=0 n/a=0 inconclusive=36 excluded=470 uncovered=506 coverage=67.48%`，`green=1048`、`semantic_failures=2`（`JS-IF-017`/`JS-IF-021`），`judge_sha256` 统一后 `c5_judge_mismatch` 归零。
- 新暴露残差：36 条 `c4_error` inconclusive（Import/With/AnnAssign 各 12）待逐条查明；470 条空 calls 中 376 条卡在 real-package 宿主依赖（`six`/`jsonpickle` 未安装）；推导式元素位更长短路链（`A and B and C or D`、`A or B and C`）未纳入复现集；`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染。v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r45：推导式元素位更长短路链 keep-or-pop 归约

- B242-V3R45 现象：`[x or y and z ...]` → `[(x or y) and z ...]`（m3/n16）、`[(x and y) or (z and w) ...]` → `[x and y or w]`（m5）、`[x and (y or z) or w ...]` → `[x and y or w]`（m6）、`[x or y and z and w ...]` → `[(x or y) and z and w]`（m7）、`[(x or y) and (z or w) ...]` → `[(x or y) and w]`（m9）、`[x or y and z or w ...]` → `[z if y else w]`（n5）、`[x if c else y and z ...]` → `[x if c else z]`（n6）、`[x and y if c else z ...]` → `[y if c else z]`（n7）、`[bool(x or y and z and w) ...]` → 语法无效的 `[ for x in xs]`（n17）。
- 根因五处：① `BoolOpPending` 只携带 `(op, left)` 做逐跳左折叠，混合 `and`/`or` 链按扫描序左折必然错；② keep-or-pop 汇合点之后还有消费者（`bool(...)` 的 `PRECALL/CALL`）时 Pending 留在栈上被当被调对象；③ 扁平序列的结合序不能用布尔优先级（首版把 `x and y or z` 退化成 `x or z`）；④ `_b237_kop_window` 真值区只取到首个终结符、假值区/条件区重建未开同族归约、前导 keep-or-pop 被误当终结符；⑤ 三元真值臂/假值臂自身是 keep-or-pop 链时 `reconstruct` 只返回栈顶尾操作数。
- 修复：① keep-or-pop 分支改为扁平 `(ops, values)` 累积（每个跳转只追加一个「运算符—右操作数」边界，不做结合）；② `reconstruct` 扫描前收集窗内 keep-or-pop 的跳转目标偏移，到汇合点先 `_b242_flush_boolop_pending()` 归约成单一节点；③ 新增 `_b242_fold_boolop_pending`，按「纯 keep-or-pop 链只出现在右结合位置」自右向左结合、连续同运算符扁平合并，`len(values)!=len(ops)+1` 时返回 `None`；④ `_b237_kop_window` 首循环跳前导 keep-or-pop（作外链边界）、条件区栈建模开同族归约并把 `(Pending, A)` 记为外链、真值区取「条件跳转→假值区入口」整段并剥末尾边界跳转、三区重建全部 `fold=True`；⑤ `_detect_comp_ternary` 的 cond/真值/假值三处重建开启 `fold_boolop_keep_or_pop=True`。开关默认 `False`，既有调用路径逐字节不变（C3）。
- 实测：`/tmp/r45/w.py`（9 形态）`total diffs 8 → 0`；`/tmp/r45/w2.py`（17 形态）`15 → 3`（仅剩 dictcomp 键位 n9、过滤器回边 n12）；扩展对照 `/tmp/r45/w3.py` `13 → 7`（零新增）；`/tmp/r45/v.py`（rr-v5r44 残差第一条）`total diffs = 0`（已被 B238 覆盖）；A/B 24 个 stdlib pyc 文本 **24/24 逐字节相同**、`bytecmp` 问题集 **143 == 143 零差异**；`quotation.pyc` 151/152（唯一失败 `datetimeindex_astype.<lambda>` 基线既有，HEAD 同败）；pytest 七套件 2 failed/282 passed/2 xpassed 名单逐位一致；fuzz 286/286 failures=0。
- 新暴露残差：字典推导键位 keep-or-pop 链（`{k and y or z: v ...}` 先被三元通道截获，`_find_dict_kv_split_point` 亦未建模双路深度 ⇒ 键整体丢）；过滤器回边（`if not (x and z)` → `if x and not z`）；三元 test 位自身是 keep-or-pop 链；顶层 and 链中夹嵌套 or 后仍有 and（扁平序列无法表达层级）；三元臂内嵌推导式整段丢；AnnAssign 注解丢失、三引号渲染。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r46：字典推导式键位/值位 keep-or-pop 链归约

- B243-V3R46 现象：`{k and y or z: v for (k, v) in kv.items()}` → `{v: None for k, v in kv.items()}`（n9/q1/q5/q12，键整体丢弃、值错位）；`{k: y and k or z ...}` → `{k: z ...}`（q2/q4）；`{k or y and z: v ...}` → `{k: v ...}`（q3/q6/q10）；`{k: y or z ...}` → `{k: z ...}`（q7）；`{k: (y and z) or k ...}` → `{k: k ...}`（q11）。HEAD 基线 `/tmp/r45/x.py` `total diffs = 20`。
- 根因四处：① `_detect_comp_ternary` 以「Pending 三元」形态先截获键位链整窗（`probe_n9.py` 实测 `TERN: (PENDING(or,[y]) if k else v)`），未落到 `_split_dict_comp_kv`；② `_find_dict_kv_split_point` 的线性栈深模拟对 keep-or-pop 记 `delta=0`，键窗吞掉假值区首指令、切分点落入键中部；③ `_split_dict_comp_kv` 的键窗/值窗 `reconstruct` 把 keep-or-pop 当无操作、只返回栈顶尾项；④ rr-v5r45 的右结合折叠对「`or` 层内含 `and` 段」的混合链仍错。
- 修复：① `_detect_comp_ternary` 追加门——`MAP_ADD` 窗内含 keep-or-pop 且无任何无条件跳转 ⇒ 返回 `None` 交回 kv 切分（经典三元真分支必以 `JUMP_FORWARD` 直落假值区，`q8`/`q9` 实证，故「无无条件跳转」精确封闭三元通道）；② `_find_dict_kv_split_point` 对 keep-or-pop 记 `delta=-1`（不短路弹出「口径」，value 首条压栈恰落在 `depth==1→2` 边界）；③ 键窗/值窗先试 `_b237_kop_window`，未命中时按键位链「全部目标 < 追加点」/值位链「全部目标 == 追加点」开启同族归约，新增 `_is_value_kop_chain` / `_value_chain_key_split_point`（键边界取「净栈效应 +1 且不含跳转的最长前缀末尾」）；④ `_b242_fold_boolop_pending` 重写为布尔优先级递归下降（先解析 `or` 层，每个操作数再解析 `and` 段，连续同运算符扁平合并），`len(values)!=len(ops)+1` 时返回 `None`。
- 负结果登记：曾试在 `_process_instruction` 为 `POP_JUMP_FORWARD_IF_FALSE/IF_TRUE` 建假出口模型，`/tmp/r45/w3.py` 由 7 回归到 9（p4/p6/p9 退化）⇒ 已回退删除；元素位通道的 POP_JUMP 语义留作下一族在独立通道内处理。
- 实测：`/tmp/r45/w2.py` `3 → 2`（n9 恢复，仅剩 n12 过滤器回边与一处元素位 keep-or-pop）；`/tmp/r45/x.py`（12 形态）`20 → 1`（仅 q12）；`/tmp/r45/w.py`、`v.py` 均 `total diffs = 0`；`w3.py` 回退后恢复 7（与上一轮持平，零新增）；A/B 24 个 stdlib pyc 文本 **24/24 逐字节相同**、`bytecmp` 问题集 **143 == 143 零差异**；`quotation.pyc` 152 函数/151 完全匹配（唯一失败 `datetimeindex_astype.<lambda>` 基线既有）；pytest 七套件 2 failed/282 passed/2 xpassed；fuzz 288/288 failures=0。
- 新暴露残差：键位链首跳为假出口（`{(k or y) and (z or k) ...}`，`_b237_kop_window` 只收 IF_FALSE 型首跳 ⇒ 产物 `{y and z or k ...}`）；过滤器回边（n12）；三元 test 位自身是 keep-or-pop 链（p4）；顶层 and 链夹嵌套 or 后仍有 and（p5）；三元臂内嵌推导式（p9）；AnnAssign 注解丢失、三引号渲染。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。

## 2026-10-26 rr-v5r47：dict 推导式键/值位「假出口短路链」归约

- B244-V3R47 现象：`{(k or y) and (z or k): v ...}` → `{y and z or k: v ...}`（q12）；`{k: (y or z) and w ...}` → `{k: z and w ...}`（r1）；`{(k or y) and z: v ...}` → `{y and z: v ...}`（r3）；`{k: (y or z) and (w or k) ...}` → `{k: z and w or k ...}`（r5）；`{(k or y) and z and w: v ...}` → `{y and z and w: v ...}`（r7）；`{k: (y or z) and w and k ...}` → `{k: z and w and k ...}`（r8）。HEAD 基线 `/tmp/r47/y.py` `total diffs = 10`、`/tmp/r45/x.py` `1`。
- 根因三处：① 结果位置上的 `(X or A) and R` / `(X and A) or R` 在 X 已能决定内层结果时不保留 X（外层只看真值），CPython 发**弹跳**假出口 `POP_JUMP_FORWARD_IF_TRUE/_IF_FALSE` 直落 rest，而 `_b237_kop_window` 只收 IF_FALSE 型首跳、通用重建器只把 keep-or-pop 记成扁平链 ⇒ 首项 X 被丢弃；② 键位的汇合点是 value 起始而非 `MAP_ADD` 偏移，原 `_append_off` 与段末 keep-or-pop 的 `argval` 不等 ⇒ 通道恒不命中；③ 段窗以追加点收尾时 `_process_instruction` 留下 `(Pending, 右操作数)` 两项栈 ⇒ 段重建返回 None。
- 修复：新增 `_dict_shortcircuit_chain(instrs, merge_offset)`——首个弹跳假出口的极性给内层运算符（IF_TRUE ⇒ `or`、IF_FALSE ⇒ `and`），段末 keep-or-pop 的极性给外层（IF_FALSE_OR_POP ⇒ `and`、IF_TRUE_OR_POP ⇒ `or`），X/A/rest 三段各以新增的 `_single`（到 keep-or-pop 汇合点先 flush、结束再 flush、要求栈上恰一项）整组重建后合成 `(X <inner> A) <outer> rest`；`_split_dict_comp_kv` 键窗用 `filtered_instrs[best_key_end].offset` 作汇合点、值窗用追加点偏移，均在 `_b237_kop_window` 之后、`_key_chain`/`_value_chain` 之前接入（未命中回 `None`，C3）；`_key_chain` 判据仍用追加点偏移。
- 实测：`/tmp/r47/y.py`（8 形态）`10 → 2`（r1/r3/r4/r5/r7/r8 逐字一致，r2 仅为括号差异，仅 r6 仍退化）；`/tmp/r45/x.py`（12 形态）`1 → 0`（q12 恢复）；回归集 `w.py 0 / w2.py 2 / w3.py 7 / v.py 0` 与上轮逐项相同；A/B 24 个 stdlib pyc 文本 **24/24 逐字节相同**、`bytecmp` 问题集 **143 == 143 零差异**；`quotation.pyc` 152 函数/151 完全匹配；pytest 七套件 2 failed/282 passed/2 xpassed；fuzz 290/290 failures=0。
- 新暴露残差：段内多个假出口（r6 `(k or y or z) and w`，需按假出口递归解析或层级还原）；过滤器回边（n12）；三元 test 位自身是 keep-or-pop 链（p4）；顶层 and 链夹嵌套 or 后仍有 and（p5）；三元臂内嵌推导式（p9）；AnnAssign 注解丢失、三引号渲染。四桶 395/0/719/442 不变，v9 overall 维持 BLOCKED。
