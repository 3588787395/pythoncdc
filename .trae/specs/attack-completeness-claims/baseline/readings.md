# 基线读数快照（v8 三态 / 门禁 / 探针 stamps / 残余登记 / 提交链）

- 快照日期：2026-10-21（工作树 HEAD = `f5f2c110` = rr-v3r11）
- 取证方式：**只读复读**。本文每个数字都给出源文件路径（代码事实另给行号）；凡无法复核者显式写「未核实」，不猜。
- 适用范围：本规范（`attack-completeness-claims`）全部攻击层 L0–L6 的对照基线；旧口径一律标注为历史。

---

## 1. 形式层三态 v8（被攻击对象的主张）

| 态 | v8 读数 | 源 |
|---|---|---|
| 完备 | **128** | `wiki/concepts/decompile-invariant-completeness.md:38`（§0 读数表「嵌套无感不变式（形式层）」行）、`:197`（§5.5 判定汇总「完备 128」行） |
| 破口 | **0** | 同上 `:38`、`:198`（§5.5「破口 0（v3 R8 终值；存量稀窝 B142/B143 属地登记，不构成形项破口）」） |
| 零能力 | **0** | 同上 `:38`、`:199` |
| 完备占比 | **128/128 = 100%** | 同上 `:37`（路径存在 128/128）、`:40`、`:196`、`:200`（II.1 口径：完备形态数 ÷ 128，破口不计分子） |
| 历史口径 v7 | 完备 103 / 破口 25 / 零能力 0 ⇒ 80.47% | 同上 `:42`；`.trae/specs/attain-true-completeness/rounds/round8/REVIEW2.md:29-34`（v7/v8 对照表） |

- 三态终表的**论证原文**（128/0/0 的四条支撑）：`.trae/specs/attain-true-completeness/rounds/round8/REVIEW2.md:36-42`（完备案=25 行的映射 / 每行统一终审标准 / 破口态=0 的封闭清单 / 零能力=0 的工具依据）。
- 终验复核：`.trae/specs/attain-true-completeness/rounds/round10/VERIFICATION.md:19`（"三态 v8（形式层）：完备 128 / 破口 0 / 零能力 0 ⇒ 100%（分母 128 = 97 ast 节点 + 31 扩展形态；工具 `tools/kb/syntax_coverage.py` 重跑 sha256 `38003eb46f2bdd6a`）"）。
- **分母 128 的构成（本次实测复读）**：`docs/refactor/syntax-coverage.json` → `denominator = {ast_node_types: 97, extra_syntax_forms: 31, total: 128}`；`numerator = {97, 31, 128}`；`coverage_pct = {ast_nodes: 100.0, extra_forms: 100.0, overall: 100.0}`；`uncovered_ast_nodes = []`、`uncovered_extra_forms = []`。写出逻辑见 `tools/kb/syntax_coverage.py:92-107`（分母）、`:113-142`（分子）、`:144-184`（31 扩展形态判定）、`:196-221`（输出）。

---

## 2. 门禁基线读数（round8 终跑；E 门禁全量）

| 门禁项 | 读数 | 源 |
|---|---|---|
| 402 语料八分片 | **6617/6617 单元，files_failure = 0**，compile_error/error/failure 全 0，elapsed **574.4s** | `.trae/specs/attain-true-completeness/rounds/round8/final_verify_summary.json:139-144`（total）、`:49-138`（8 分片明细） |
| 分片单元明细 | shard0 786 / shard1 469 / shard2 538 / shard3 887 / shard4 855 / shard5 999 / shard6 801 / shard7 1282 | 同上 `:50-137`；**本次复算 Σ = 6617 ✓**（REVIEW2.md:24 记同一加法） |
| small34 | **1568/1568 单元，34/34 文件 success**（compile_error/error/failure = 0） | `final_verify_summary.json:2-11`；`rounds/round8/small34_report_new.json`（本次复读 files_total=34 / units_total=1568 / units_success=1568）；半集 A/B 各 rc=0：`rounds/round8/final_verify_log.txt:358`、`:397` |
| quotation 单验 | **153/153 success，success_rate 100.00%，rc = 0** | `final_verify_summary.json:12-15`；`final_verify_log.txt:504-508` |
| pytest 七套件 | **2 failed / 282 passed / 2 xpassed in 10.84s（rc = 1）** | `final_verify_summary.json:16-19`；`final_verify_log.txt:510-518` |
| tests 失败名单 | `tests/test_algorithm_correctness.py::TestDominanceFrontierIf::test_B01_simple_if_then_else_merge` + `tests/test_deep_nesting_pressure.py::TestBoundaryConditions::test_BOUNDARY_02_large_function` | `final_verify_log.txt:516-517`；七套件清单：`rounds/round8/final_verify_run_r8.py:19-27` |
| IV.2 导入/编译 | IMPORT_OK = true、COMPILE_OK = true | `final_verify_summary.json:21-22`；判定式 `final_verify_run_r8.py:100-112` |
| IV.2 BOM | `region_ast_generator.py` = "one"、`region_analyzer.py` = "one"（单头） | `final_verify_summary.json:23-24`；判定式 `final_verify_run_r8.py:113-119` |
| IV.2 插桩 | 4 文件 **code 命中 0**；in_string 3 处（`region_ast_generator.py` 行 22176 / 22911 / 55327） | `final_verify_summary.json:25-46`；判定式 `final_verify_run_r8.py:120-143` |
| IV.2 G3 | `G3_forbidden_prefix_new_defs = 0` | `final_verify_summary.json:47`；判定式 `final_verify_run_r8.py:145-152` |
| compare 零回退 | `REGRESSIONS=0 IMPROVED=0` × 8（402 八分片）；small34 compare `REGRESSIONS=0 IMPROVED=33` | `final_verify_log.txt:61,100,139,178,217,256,295,355`（8 次 COMPARE）；`:502` |
| 组合级对照 | 25 号终表 + 另册 3 号 = **28 项全数处置**，唯一属地残余 = B142 稀窝 | `rounds/round8/REVIEW.md:58-103`、`:139`；`rounds/round10/VERIFICATION.md:20` |
| 六步终读数汇总表 | 见 §1–§2 全表 | `rounds/round10/VERIFICATION.md:8-15` |

> 门禁编排脚本（读数产出路径）：`rounds/round8/final_verify_run_r8.py`（regen 0-7 → verify 0-6 + shard7 拆分 → compare×8 → small34 拆半 → quotation → pytest → IV.2 → summary），行号 `:49-57`、`:58-90`、`:91-94`、`:95-99`、`:100-153`、`:157-177`。

---

## 3. 探针 / 证据 stamps（本次逐件复读 JSON 求和，非采信文字转述）

| stamp（`.trae/specs/attain-true-completeness/rounds/round8/`） | 探针数 | 单元 | 状态 | 备注 |
|---|---|---|---|---|
| `rec1_probes_r8matrix1.json` | **34** | **257/257** | 全 success | Σ=197 深层 + 60 负对照（`REVIEW.md:54`） |
| `rec1_probes_r8combo2.json` | **33** | **241/242** | 32 success / 1 failure | 唯一红 = `B71_0` → `<module>.v_nest_fin_continue`（**Different control flow**） |
| `rec1_probes_r8combo1.json` | 33 | 239/242 | 30/3 | 红三项：`v_nest_fin_continue` / `dict3_nested_value`(B53) / `or4_and2`(B11-R2)，B162 修复前 |
| `rec1_probes_r8fin_neigh1.json` | 16 | **86/86** | 全 success | 邻域组 |
| `rec1_probes_r8fin_named1.json` | 8 | **46/46** | 全 success | 命名组 |
| `rec1_probes_r8fin_neg9_1.json` | 9 | **60/60** | 全 success | 负对照九件 |
| `rec1_probes_r8fin_r4prot1.json` | 5 | **71/71** | 全 success | R4 保护组 |
| `rec1_probes_r8fin_r5synth1.json` | 20 | **65/65** | 全 success | R5 合成组 |
| `rec1_probes_r8fin_real3.json` | 3 | **172/172** | 全 success | 三真实文件 |
| `rec1_probes_r8fin_r7main.json` | 15 | **98/98** | 全 success | R7 主集 |
| `rec1_probes_r8acc_neigh1.json` | 16 | 86/86 | 全 success | B153–B160 后验收复跑（`REVIEW2.md:10`） |
| `rec1_probes_r8acc2_r7main.json` | 15 | 98/98 | 全 success | R7 合成 pyc 复制至 round8 stage 后自跑（`REVIEW2.md:10`） |
| `rec1_probes_r8verify2.json` | 2 | 5/5 | 全 success | B162 独立抽验 b53 3/3 + b11 2/2（`REVIEW2.md:13`） |

- 回归组合计：**76 探针 / 602 单元 / 0 失败**（16+8+9+5+20+3+15 = 76；86+46+60+71+65+172+98 = 602），与 `REVIEW2.md:23` 记的同一加法一致。
- 矩阵/组合内部数目核对：25 行探针单元 197 + 负对照 60 = 257（`REVIEW2.md:21`）；组合 46+186+9 = 241 success，总 242 含 1 红（`REVIEW2.md:22`）。
- **唯一已知红**：`v_b71_face::v_nest_fin_continue` —— 判据层读数为 `Different control flow`（stamps 的 `failures` 字段原文），归属 **B142 稀窝**，R8 不升格（`REVIEW.md:139`）。

---

## 4. 残余登记（稀窝，不升格）

| 编号 | 残余单元 | 根因（原文口径） | 源 |
|---|---|---|---|
| **B142** | `v_b71_face::v_nest_fin_continue`（嵌套 try/finally 内的 continue） | analyzer 的 try 区域构造按异常表深度分层时把「正常路径 finally 副本」误纳为外层 try 的 try_blocks（副本签名检测未命中，finally_copy_blocks 为空），内层 try 体与外层 try 体错位，continue 路径的两级副本被重排成伪嵌套 try/finally | `rounds/round6/FIX.md:92`（登记为 park 不追）；`rounds/round8/REVIEW.md:139`（不升格，修复窗口=后续轮次，机制候选：副本谱系图 + 属地继承） |
| **B143** | `s_b140_break_in_finally_loop`（finally 体内的 break） | finally 体（副本序列）中的嵌套 IfRegion 条件块与 break 臂块在 finalbody 装配时线性发射，break 未落在 if 臂内；需 finalbody 装配按子区域派发（entry 身份）而非线性发射 | `rounds/round6/FIX.md:93`；`rounds/round8/REVIEW.md:140` |

- **本次实测**：`core/cfg/*.py` 内 `[B142-V3R*]` / `[B143-V3R*]` 标记数 = **0 / 0** ⇒ 二者是「登记残余、无落地机制」，不参与 `markers.md` 的机制族清单。
- 处置口径：三态破口仍记 0（`REVIEW2.md:39` 第 3 条），存留 B142/B143 为稀窝登记。

---

## 5. 提交链（rr-v3r00 … rr-v3r11）

| 标签 | hash | 主题（首行摘要） |
|---|---|---|
| rr-v3r00 | `e1c0aabe` | 新规范 attain-true-completeness 三件套 + 基线快照（gate 42 复读 6617/6617 + 34 集 1568/1568 + quotation 153/153 + tests 基线名单；wiki v7 103/25/0） |
| rr-v3r01 | `cb24db60` | Round 1 破口侦察证据重建（46 探针 10 run 全复现；真实破口 20 / 已封闭待复验 5 / 证据缺口 0） |
| rr-v3r02wip | `70ed1ec6` | R2 修复中断存证（续作基线） |
| rr-v3r02 | `ece1aab5` | Round 2 条件合并块族封闭（If/BoolOp/IfExp）；标记 `[Bn-V3R2]` 47 处；新登记 B129/B130（域外，裁决归 R8） |
| rr-v3r03 | `69132f55` | Round 3 try-raise-assert-宿主族封闭；标记 `[Bn-V3R3]` 25 处；新登记 B131–B136；park 2 项（c04/m02 = B132，归 R8） |
| rr-v3r04 | `71fda309` | Round 4 await-挂起链族封闭；标记 `[Bn-V3R4]`（提交说明记 25 行） |
| rr-v3r05 | `841e511e` | Round 5 match-with 幻影族封闭；标记 `[Bn-V3R5]` 27 处（提交说明口径） |
| rr-v3r05a | `774cd9cb` | R5 提交后复核（site-packages 两真实模块 OK 快照刷新，零新增行） |
| rr-v3r06 | `8c088ef7` | Round 6 循环控制族封闭；标记 `[Bn-V3R6]` 11 处（提交说明口径）；新破口自 B142 起 |
| rr-v3r07 | `63520cb4` | Round 7 赋值-删除-return-slice 族封闭；标记 `[Bn-V3R7]` 21 处；新破口 B144–B152 |
| rr-v3r08 | `b6e634b7` | R8 全行对抗终审：25 行矩阵 257/257、组合级 241/242、三态 v8 128/0/0、机制 B153–B162 |
| rr-v3r09 | `1c0ea037` | wiki 台账 v8 落账（工具重跑 sha 38003eb4；六步实录 `rounds/round8/WIKI_REVIEW.md`） |
| rr-v3r10 | `a1e34be0` | v3 终验与终归档（`rounds/round10/VERIFICATION.md` + `README.md`） |
| rr-v3r11 | `f5f2c110` | 规则文档同步 v8 终态（`rules.md` 锚点全表重核 + §6.2/§7.2/§8.1 更新） |

- 链序来源：`git log --oneline`（HEAD 祖先链，线性）；hash 全长：`e1c0aabe…`（rr-v3r00）、`cb24db60…`（r01）、`ece1aab5…`（r02）、`69132f55…`（r03）、`71fda309…`（r04）、`841e511e…`（r05）、`8c088ef7…`（r06）、`63520cb4…`（r07）、`b6e634b7…`（r08）、`1c0ea037…`（r09）、`a1e34be0…`（r10）、`f5f2c110…`（r11）。
- 祖先链复核：`rounds/round8/WIKI_REVIEW.md:9` 记 13/13 fix 批在 origin/main 祖先链。

---

## 6. 与台账不一致 / 未核实项（如实登记，不得沿用为基线）

1. **「标记 174 处」口径不可复现** —— 台账数 `R2:47 / R3:25 / R4:13 / R5:34 / R6:12 / R7:21 / R8:22`（`rounds/round8/WIKI_REVIEW.md:10`、`rounds/round10/VERIFICATION.md:21`、rr-v3r09/r10 提交说明）。
   - 本次实测（口径：`\[B\d+[A-Za-z]*-V3R\d+` 于 `core/cfg/*.py` 按出现次数计）：**R2:47 / R3:25 / R4:13 / R5:51 / R6:12 / R7:21 / R8:22 = 191**；六轮与台账逐位一致，**仅 R5 不符（51 vs 34）**。
   - R5 自报数：**27 处**（`rounds/round5/FIX.md:159`、`:206`；rr-v3r05 提交说明同）。
   - 算术重建：R5 = B70(19) + B93(1) + B122(7) + B61a–B61k(24) = **51**；51 − 24(B61a–B61k) = **27**（= R5 自报数）；27 + 7(B122 二次计入) = **34**（= 台账数）。故台账 174 与实测 191 差 **17** = 24 − 7。
   - 结论：**174 处不可作为基线事实**；后续 L3 攻击面以实测 191（口径见 `markers.md` §5）为准，并在本轮开一条口径勘误（自 B163 起的登记台账须改用可复算口径）。
2. **其余数字全部核实**：§1 三态、§2 门禁九项、§3 十三份 stamps、§4 两条残余、§5 提交链 14 个 hash —— 均可从上文所列源文件逐行复核。
3. **未核实项（本次未取证，不猜）**：
   - R9/R10/R11 三轮台账页与 `rules.md` §8.1 的 v8 数字是否与本文逐位一致 —— 本次未逐页比对（仅读 `rules.md` 章节标题结构）。
   - `tools/kb/syntax_coverage.py` 在**当前**工作树重跑的输出 sha256 是否仍为 `38003eb46f2bdd6a` —— 本次只复读了已落盘的 `docs/refactor/syntax-coverage.json`（其内容为 128/128/100.0），**未重跑工具**（避免污染工作树）。
   - 402 语料 regen 后的 402 个产物是否仍零字节差异 —— 本次只读到 `regen_shard0..7.json` 均为 2 字节空数组的记录，未复跑 regen。
