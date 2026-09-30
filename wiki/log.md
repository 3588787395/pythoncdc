# Research Log

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
