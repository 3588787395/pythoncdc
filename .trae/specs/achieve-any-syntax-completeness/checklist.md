# Checklist

## 可达性表（Task 0）
- [x] `REACHABILITY.md` 已创建
- [x] 表含五行：J 空间（五个维度）、语义差分、变异测试、规则覆盖、G5 回归
- [x] 五个组成部分的命令面已在 `REACHABILITY.md` 逐行复述
- [x] 术语区分明确：J 五个维度 ≠ J 记录五个字段 ≠ 产品完备五个组成部分
- [x] J 记录最低五字段与审计辅助字段区分清楚
- [x] 每行四项齐全：有限输入来源、生成/执行方式、验收命令、阈值
- [x] 表中无 `TBD` / `待定` / `UNKNOWN`
- [x] J 行输入为 CPython 3.11 语法产生式，执行方式为 `jspace_generator.py`
- [x] 语义差分行输入为 J 空间（五个维度） + 402 语料 + 46 真实 pyc，执行方式为 `semantic_runner.py` + `semantic_diff.py`
- [x] 变异行输入为 J 空间（五个维度） + 402 语料，执行方式为 `mutation_test.py`
- [x] 规则行输入为 339 条规则，执行方式为 `rule_manifest.json` + witness/trace 映射
- [x] G5 行输入为 402 八分片 / small34 / quotation / IV.2，执行方式为既有回归脚本
- [x] 五行全部可达，缺任一行即 `NOT READY`

## 基本比较器冻结（Task 0）
- [x] `scripts/pyc_verify.py` SHA256 = `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4`，本规范期间未变化
- [x] 外部 `pylingual/equivalence_check.py` SHA256 = `9C7567BD6776B36B6AF1991AF222CF79E48412335CA01CBB07146F9ED50045A6`，未变化
- [x] `git diff -- scripts/pyc_verify.py` 为空
- [x] 未添加会改变基本比较器 verdict/tolerance 的包装
- [x] `tests/` 基线零改动
- [x] 基线 commit `e755d773` 与 before 读数已落盘

## 测量口径（Task 1）
- [x] `semantic_runner` 已传递 `input_model.calls`
- [x] 无 calls 的条目记 `INCONCLUSIVE/module_only`，不进入覆盖分子
- [x] R7 的 `co_code` / `co_consts` / `co_exceptiontable` 差异默认判 `DIFFERENT`
- [x] R7 tolerance 有书面登记，无未登记忽略
- [x] 超时记 `INCONCLUSIVE`，不记 EQUAL/DIFFERENT
- [x] J 样本中 B142 五条至少出现 R1，而不是仅 R7
- [x] `JS-IF-076` 出现函数体差异，不再被 module-only 掩盖
- [x] 四项口径自测（module-only / calls / R7 / timeout）全部通过

## B142（Task 2）
- [x] `v_nest_fin_continue([[0,1]])` 原件/产物返回序列逐项相等（R1_RESULT=EQUAL，8 组输入全 PASS）
- [x] `v_nest_fin_continue([[1,2]])` 原件/产物返回序列逐项相等
- [x] 内层 finally 正常路径副本归属内层，外层不重复认领（副本谱系签名 + 台账优先重建；冻结比较器 v_b71_face 4/4）
- [x] 内层 finally 异常路径顺序为内层→外层→传播（G1 探针 p_g1_fin_paths 3/3 字节级 PASS）
- [x] continue 回边保留，无双发/丢失/错层（fc 出口物化 + 循环指定回边排除）
- [ ] B142 合成探针（双层 finally + continue/break）通过 —— 部分：G1 3/3、G2 continue 形 g2_cont 绿、G3 双层 g3_two_fin 绿；break 出口臂（g2_brk）与三层（g3_three_fin）变体挂账（见 rounds/round12/probes_b142/README 影响面；break 需条件识别支持一分支纯循环出口终结，上游 [R13-A3] 扩展 TEMP-DISABLED）
- [x] B142 邻域与 402/small34 定向回归无回退（最终代码全量复跑：402 八分片 6617/6617、small34 1568/1568、quotation 153/153、pytest 277 passed + 2 失败为基线既有（stash 对比同败）；`_b142_final_regression.txt`）
- [x] B142 状态更新为已修复，附 I.4 判据（BREACH_REGISTRY §4 B142 / B181、BREACH_TRIAGE Headline）

## x01 / docstring / B200（Task 3）
- [x] `JS-IF-076` 的 `if_in_while` 中 `break`：原件字节码中该 `break` 已被 CPython 优化器作为不可达代码删除（内层 `while 1` 无出口）——字节级还原（R7 EQUAL、pyc_verify 7/7）不含 `break` 即为上限；源码级 `break` 语句属编译时销毁信息，挂账为不可恢复，不虚构
- [x] `if_in_while` / `if_in_try` / `if_shallow` 的 5 条 R7 清零（semantic_diff fresh **EQUAL** 0 diff；归档基线保持 R7×5+R1×1 作为修复前证据）
- [x] B199 函数 docstring 保留，module docstring 恢复为字符串字面量，`__doc__` 值一致（p5_docstring 4/4；x01 模块 docstring 字面量；两形态重编译逐字节相同）
- [x] docstring 修复单独验证，未与 B142 混记（独立探针 p5_docstring.pyc；B199 台账单独登记已修复）
- [x] 四类调用级探针通过（`case_js_if_076_fresh.json` call_exprs 4 条 EQUAL + `probes_x01/case_p_x01_variants.json` call_exprs 6 条 EQUAL；`if_in_while()` 源码死循环按 Task 1.3 口径单列）
- [x] B200 台账截断已修复，编号/字段完整（Task 0.6，注册表行 6/83）

## fuzz 封闭（Task 4）
- [x] `FZ-raresyntax-015` starred-unpack 已修复并有通用判据（607089e8 值段切分 + 1ff5d40a dict `**` 配对）
- [x] `FZ-semantictrap-020` generator-send 已修复并有通用判据（0df50457 send 值绑定）
- [x] `FZ-raresyntax-021` annotations-posonly 已修复并有通用判据（6d60cba0 `/` 签名链）
- [x] `FZ-semantictrap-023` finally-return 已修复并有通用判据（280d2c59 + 1ff5d40a 条件臂变体）
- [x] 四个发现均有最小复现、合成变体、I.4 白名单证据（probes_fz/p_fz_families.py 7/7 + semantic EQUAL；TASK4_6_CLOSURE.md）
- [x] 去重后 B 编号/登记正确，未把“已去重”写成“已封闭”（B199→已修复；023/015/deephost 残余不新增编号，维持 B203/B210/B197-B202/B207-B142）
- [x] 24 条 fuzz 达到 24/24 EQUAL（fuzz_summary.json EQUAL=24 failures=0；唯一结构残差 deephost-001 臂锚由 R12-MATCHANCHOR 剥离归约）

## J 空间（Task 5）
- [x] 388 条缺 source 已恢复/生成或登记 `unjudgeable`（12 PEP604 生成 + 376 等价源；`c1_source_missing=0`）
- [x] 12 条缺 pyc 已恢复/生成或登记 `unjudgeable`（PEP604 探针 pyc；`c2_pyc_missing=0`）
- [x] 所有条目有 `input_model.calls`（449 非空 + 1107 显式降级空表并注明原因；`calls_missing=0` 按显式决定口径）
- [x] 全量 J（1556 条 J v3）C1–C5 已跑完（8 分片合并 `semantic_j_sample.json`；judge=semantic_diff.py 哈希链 C5 全通）
- [x] **Fresh J v3 复算（rr-v5r73，2026-10-27）**：当前 Windows 树重跑 3 分片 + 合并；基线 `covered_5tuple=1050/1556`、`inconclusive=36`、`excluded=470`、`semantic_failures=0`、`coverage=67.48%`；与历史 1050 读数逐项一致，且历史 2 条 `DIFFERENT`（JS-IF-017/021）已因 B142 修复转为 `EQUAL`。证据：`rounds/round13/jspace_v3/fresh/COVERAGE_V3_FRESH.md`
- [x] **36 条 `c4_error` 已定位为 3 个 load-invalid 探针**（`c4_15_star_import.py` 缺 `path`、`c05_class_with.py` 缺 `_CM`、`c01_class_assign.py` lambda 读类体 `B`），非反编译缺陷；最小修复后 36/36 `EQUAL`，`inconclusive=0`。证据：`fresh/REPAIR.md`、`fresh/coverage_v3r.json`
- [x] **62 条 async-only 已闭合（rr-v5r74）**：`close_async_family.py` 为每个 async 入口生成自包含 `asyncio.run(...)` 驱动（async 生成器用 `_consume` 消费），驱动源哈希绑定在 `call_static`；62/62 `EQUAL`，`covered_5tuple 1086→1148`、`excluded 470→408`、`coverage 69.79%→73.78%`。证据：`fresh/ASYNC_DRIVER.md`、`semantic_async.json`、`COVERAGE_V3A.md`
- [x] **module-level 家族已判定（rr-v5r74）**：`close_module_family.py` 用原始 module code object 作可调用入口（`types.FunctionType(__loader__.get_code(__name__), globals())()`），m06/m08 20/20 `EQUAL`；m04 12 条先最小修复 `_CM()`，再判定为 R7-only `DIFFERENT`（产物多一层 `try`，`co_code` 300 vs 298），按 R7 阻断显式 `excluded`，不计入分子。`covered_5tuple 1148→1168`、`excluded 408→388`、`coverage 73.78%→75.06%`。证据：`fresh/MODULE_WITNESS.md`、`semantic_module.json`、`COVERAGE_V3M.md`
- [x] **B275 已修复（rr-v5r75）**：`_region_has_outer_handler_over_finally_copy` 在 `finally_copy_blocks` 为空时回退到 `finally_blocks`，且回退台账只接受 `region.blocks` 之外的 handler，避免把 finally 体内嵌套 `try` 误判为外层包裹。m04 产物 `co_code` 298 == 298、`co_exceptiontable` 129 == 129 相等；`b275_regression.py` 的 `m04_module_try`/`c04_CTryNest`/`control_flat` 全 `EQUAL`。全量 1556 基线重跑 **0 verdict 变化**、12 条 m04 产物 SHA 变化（预期）；module manifest 32/32 `EQUAL`。`covered_5tuple 1168→1180`、`excluded 388→376`、`coverage 75.06%→75.84%`。证据：`fresh/B275_FIX.md`、`semantic_module_b275.json`、`COVERAGE_V3M_B275.md`
- [x] **376 条 real-package 已审计（rr-v5r76）**：7 个 pyc 中 6 个在 `IQCommon.data.TickDataCache`（Linux x86_64 `.so`）处 `ModuleNotFoundError`，仅 `aes_encrypt.pyc` 可执行；10 条 module-level 中 9 条 `p_j` 含 claimed host 但被 `.so` 阻断，`JS-DECORATOR-009` 的 `p_j` 无类装饰器（仅方法级 `@staticmethod`）；366 条非 module-level 需 host-specific calls（355 条被 `.so` 阻断、11 条 `aes_encrypt` 无专属探针）。**0 条可诚实闭合**，读数不变。证据：`fresh/REAL_PACKAGE_AUDIT.md`、`REAL_PACKAGE_AUDIT.json`
- [ ] `uncovered = 0`（当前 376 = 376 real-package 安全闸；12 m04 B275 已闭合。rr-v5r76 审计确认 0 条可诚实闭合：9 条 module-level 被 Linux `.so` 阻断、`JS-DECORATOR-009` 无类装饰器、366 条需 host-specific calls。逐条挂账 `TASK5_THREE_LISTS.md`，未宣称完备）
- [ ] `module_only = 0`（当前 376：全部 `unsafe_host_module: real-package module`；62 async-only、20 m06/m08 module-level、12 m04 B275 均已进入分子；rr-v5r76 审计见 `fresh/REAL_PACKAGE_AUDIT.md`）
- [ ] `unjudgeable = 0`（fresh 基线 36 `c4_error` 已全部修复为 0；无其它 unjudgeable；但 excluded 376 仍使 G1 不可 PASS；rr-v5r76 审计确认无新增可闭合项）

## 门禁（Task 6–7）
- [x] G2b 402 语料语义差分完成并留逐样本证据（FAIL 如实：3 DIFF + 342 环境不可执行逐条在案）
- [x] G2c 46 个真实 pyc 语义差分完成（FAIL 如实：24 DIFF 含 5 行为差逐条在案）
- [ ] G3 变异测试完成，漏检 = 0（样本读数 missed 602/634；全量总体与调用模型补齐挂账）
- [ ] G4 规则 witness/trace 完成，`open = 0`（**2026-11-17 v3「谓词感知」口径（当前权威）**：universe 344 规则 / 5896 occurrences；predicate-aware trace 131 运行 / 1556 条目 / 0 失败、谓词求值 1,920,617 次而**为真仅 6,375（0.33%）**；`rules_hit_true` **156**、`empty_cov_true` **188**（v2 的「锚点命中 244 / empty_cov 100」是假命中：12,769 个 (run,rule) 锚点到达但谓词为假；(entry,rule) 231,827 命中中仅 77,199=33.3% 为真）；v1 定义下 **proved 127 / open 217**（无真发生点 100 / 谓词恒假 88 / 负 witness 缺失 29）；预演 `rule_manifest --check`：`empty_cov=188`、`ready 127/344`、**G4=FAIL(mapping_or_proof_gap)**，其余 unmapped/orphan/anchor_orphan/not_ready/witness_err/domain_err 全 0。**结构性阻塞（三重，均实证）**：①定义层——`rule_manifest.py:157-195` 要求 witness+domain+proof_id+composition 四项齐备，仓库原无 composition 理论，现已有「需评审的 v1 定义」（`fresh/gate_g4/G4_PROOF_THEORY.md`，明确声明只证「谓词在发生点成立」、非语义正确性）；②可达层——188 条无真发生点分三档：D1 15（无 importer，全 isinstance_ast：objective_patch_detector 11 + patch_detector 4）、D2 60（类/函数从不构造执行：ASTGeneratorV2 27、`_generate_dict_node` 16、StructuredAnalyzer 7、其余 10）、D3 113（88 条行到达但谓词恒假 + 25 条分支未走到，需新探针或改锚点语义）；③工具层——`rule_universe.py` 无排除机制，若评审决定排除 D1/D2 需先改工具。证据 `fresh/gate_g4/{universe_v3,traces_v3,proof_records_v2,manifest_proved_v2,G4_V2_TRIAGE,G4_V3_READINGS}.json|md`）
- [x] G1/G2a/G2b/G2c/G3/G4 复跑并更新 gate_report（GATE_REPORT_V5R06：overall BLOCKED，全部实测读数；G4 当前读数见 rr-v5r77）
- [x] G5：402 八分片 6617/6617、small34 1568/1568、quotation 153/153、pytest 基线、IV.2 全绿（rr-v5r77 当前树复跑，`gate_report.gate_g5` = PASS；证据 `fresh/g5_rerun/G5_RERUN.md`）
- [x] 基本比较器独立复跑，读数与基线一致（rr-v5r77 G5 全量由冻结 `scripts/pyc_verify.py` 与 `pylingual/equivalence_check.py` 产生，未改一字节）
- [ ] G6 使用独立 custody；24/24 EQUAL、0 leak、轮换记录齐全
- [ ] 无独立 custody 时 G6 记 `ASSURANCE_BLOCKED`，未用 local canary 冒充 PASS
- [ ] 完整 G1–G5 `product_complete = PASS`；G6 状态单列
- [x] **rr-v5r111 已实证**：REAL46-036 整案 `semantic_diff` EQUAL（diffs=[]，DIFFERENT→EQUAL）、REAL46-004 维持 EQUAL；1556 J 空间三分片全量闸门 **0 实质回归**（EQUAL 1180 不变，5 个 2 核并发超时抖动案单案复跑与基线逐字一致，抖动校正后 EQUAL 1180 / ERROR 376）；46 sweep 12 DIFFERENT / 16 EQUAL / 17 ERROR + skip1，唯一变化 REAL46-036；比较器与 `tests/` 零改动。证据 `fresh/orandchain_if/GATE_V5R111.md`。**不宣称 G1/G2c/G3/G4/G6 通过，product_complete 仍 NOT PASS**
- [x] **rr-v5r112 已实证**：REAL46-001 整案 `semantic_diff` EQUAL（diffs=[]，DIFFERENT→EQUAL，两叶 v[47]/v[69] 全消）、REAL46-004/036 维持 EQUAL；1556 J 空间三分片全量闸门 **0 实质回归**（抖动校正后 EQUAL 1180 / ERROR 376 逐案与基线一致；10 个并发抖动案 10/10 单案复跑证明与基线/校正基线逐字一致）；46 sweep 11 DIFFERENT / 17 EQUAL / 17 ERROR + skip1，唯一变化 REAL46-001；比较器与 `tests/` 零改动。证据 `fresh/notboolop_orand/GATE_V5R112.md`。**不宣称 G1/G2c/G3/G4/G6 通过，product_complete 仍 NOT PASS**
- [x] **rr-v5r113 已实证**：REAL46-019 整案 `semantic_diff` EQUAL（diffs=[]，DIFFERENT→EQUAL，唯一 R7 `v[19].code_sha` 全消）、REAL46-001/004/036 维持 EQUAL；1556 J 空间三分片全量闸门 **0 真实回归**（校正后 EQUAL 1180 / ERROR 376 逐案与基线一致；5 个并发/超时抖动案 5/5 单案复跑与校正基线逐字一致；原本能生成的产品文本零漂移）；46 sweep 10 DIFFERENT / 18 EQUAL / 17 ERROR + skip1，唯一变化 REAL46-019；比较器与 `tests/` 零改动。证据 `fresh/whileyield_break/GATE_V5R113.md`。**不宣称 G1/G2c/G3/G4/G6 通过，product_complete 仍 NOT PASS**

## 终态与不变式（Task 8）
- [ ] 双读数已更新到 `rules.md` 与 `wiki/` 台账
- [ ] `rounds/round11/` 已归档
- [ ] 终态报告列出 J 空间（五个维度）、语义差分、变异、规则覆盖、G5、G6/`ASSURANCE_BLOCKED`、缺陷关闭状态
- [ ] 未把 v8 128/128 写成完备
- [ ] 无用户既有变更被回滚
- [ ] 根目录 scratch / `_scratch_m4` / `.canary-private/` 未入库
- [ ] 提交已 push 到 `origin/main`

## 现状快照（2026-11-16，截至 4753cc05 / rr-v5r181；详见 rounds/round13/jspace_v3/fresh/final_state/REPORT.md）

- 语料判官（**上界口径**）：request 194/194、difflib 62/62、tarfile 156/160、cookiejar 103/105、subprocess 75/78 ⇒ 合计 **590/599 = 98.50%**；保守口径按函数级另算（Task 91：437/447 = 97.76%，不可与上界混算）。
- 已落地 24 个根因族（20 个提交），另有 1 轮 BLOCKED 已整体回退（rr-v5r179 `_wait`）。
- 门禁：G5 pytest 冻结基线 PASS（2F/282P/2XP，validator 14/6）；**G1 未 PASS**（uncovered=376，审计结论 0 条可诚实闭合）；**G3 未 PASS**（missed 602/634）；**G4 未 PASS**（proved 0 / open 342）；**G6 未 PASS**（无独立 custody，应记 `ASSURANCE_BLOCKED`）；`product_complete` 未达成。
- 测量限定：判官 EQUAL ≠ 文本保真（恶性盲区 45.8% 构造样本）；已常态接入 S1 签名闸门（594/594 一致、0 未配对）与 AST 剪枝检查（`ast.If`/语句数/`Pass` 前后对比）。
- 本快照不改变上列任何勾选项的判定；勾选仍以对应门禁证据为准。

## 合规修复记录（2026-11-16，均已有单提交 + push）

- **BOM 回归（rr-v5r165 引入，76df99d1 修复）**：`a1de8c5f` 的补丁脚本以 utf-8（无 sig）重写
  `core/cfg/region_analyzer.py` 与 `region_ast_generator.py`，剥掉两文件的 UTF-8 BOM；此后 20 轮
  G5 的 IV.2 一直报 BOM 红（功能四项正常，故未暴露）。已按字节恢复 BOM（numstat 1/1、1/1），
  IV.2 复跑 `efbbbf single-head ×2`，五语料产物逐字节不变。
- **硬编码上限（rules.md §2.2，50411c65 修复）**：本战役新增的三处上限已移除，终止性改由结构
  保证——`len(members) <= 64`（已有 seen）、`for _ in range(4)`（改 while True + seen）、
  `_v173_depth < 16`（AST body 严格下降 ⇒ 树有限）。改后五语料产物与判官读数逐字节不变，
  `iv2_recheck` 的 `G4_suspect_lines` 中本战役项清零（12 条均为既有代码）。
- **R7 口径**：`TarFile.next` 等「判官 EQUAL」单元仍可能有 `co_consts` 顺序差异（见
  `fresh/final_state/R7_FINDING.md`）；**judge-EQUAL ≠ R7-clean**，语料百分比不得当作
  J 空间覆盖或完备的证据。
- **命令面缺陷（非代码）**：402 索引内 `path` 为陈旧绝对路径需重映射；`spec.md` 第 124 行
  pytest 命令漏 `tests/` 前缀；`quotation` 在 gate 输出里显示 0 而 payload 实为 153/153
  （字段命名不一致，不影响 PASS 判定）。

## G4/G3 结构性结论（2026-11-17，证据见 fresh/gate_gap/）

- **G4 当前口径（权威）**：universe 344 条 / 5894 occurrences；trace 1556 entries、failed=0；rules_hit **244**、empty_cov **100**；unmapped/orphan/anchor_orphans 全 0；**proved 0 / open 344 ⇒ FAIL**。
- **G4 缺的不是复跑，是理论**：`rule_manifest.py` 要求每条规则同时具备「J 内正/反 witness + semantic_domain + proof.proof_id + 非空 composition」才可 `proved`，而 `--generate` 四项全空、仓库无 composition 理论 ⇒ 在不设计 proof/composition 的前提下，G4 数学上不可能 PASS；填假值即违反 `rules.md` §2.4。
- **100 条 empty_cov 的真实构成**：D1 23 条（模块永不执行、无 importer）／D2 56 条（模块 live、函数 0 行）／D3 21 条（函数已执行、分支未进）。两条路线（扩 tracer / 评审排除）均已实测：**都不能使 G4 PASS**。
- **G3 当前口径**：missed **602/635 = 94.8%**（明细在 `round9/g3_mutation/` 30 案，缺聚合器与全量总体）；按 operator：if 69/69、while 5/5、augassign 24/24、compare 9/9、unaryop 4/4、return 243/248、constant 206/229；30 案中 19 案零 kill；抽样归因＝调用域/分支不可达 7 + 判据盲区 2 + 「反编译错被归一化」0（该实验反编译器不在环内）。**前提是先扩判据观测域**（class-body 属性/未调用函数/闭包返回/局部值），否则 missed=0 不可达；另有 1 条 ERROR 单独卡死 errors==0。
- **结论**：G4 需「proof/composition 理论 + 344 条人工证明记录 + 100 条可达性裁决」；G3 需「判据观测域扩容 + 3–5 万 mutant 复跑」。二者都不是脚本重跑能解决的问题。

## G1 当前口径与 82 条真缺陷（2026-11-17，rr-v5r187 后）

- `covered_5tuple` **1174/1556（75.45%）**、`uncovered` **382** = 376 条 `real-package`（`.so` 环境阻塞）
  + **6 条 R7-only**。rr-v5r187 的死常量族修复使 1151→1174（23 站点 DIFFERENT→EQUAL）。
- **新发现：82 条真缺陷**（`fresh/gate_drift/DRIFT_109.md`）。G3 快照的 1151 产品集在当前树已漂移
  109 条，逐条定性：**82 条真缺陷 + 27 条尺子效应 + 0 条环境伪差**。
  - 行为维（R1）40 条 = **3 个根因**：`_generate_if` 的 BoolOp 条件摊平（20 条，含死循环
    `f_b98_while_cond_pos(1,1,1)`）、`_generate_try` 嵌套 finally 对调（19 条）、`_generate_with`
    continue 退化为 pass（1 条）。
  - 潜伏 42 条（表面仅 R7，定向真跑证实行为已错）：`a or (b and c)`→`not a and b and c` 的 De Morgan
    反转（18 条）、`while a and b or c` 条件被截断（12 条）、`keep(x)` 成死代码（12 条）。
  - **69 条 R7-only 与 r187 常量族无关**：`co_consts` 逐字节一致，差异只在嵌套
    `co_code`(93)/`co_stacksize`(18)/`co_exceptiontable`(9) ⇒ **「R7-only」不等于等价**。
- 引入点审计：正在用冻结树 bisect（`fresh/gate_drift/BISECT.md`），判定这 82 条是回归还是从未正确；
  在 bisect 出结果前，不把 r186/r187 视为已排除嫌疑。

## 按 REACHABILITY 表逐行对齐（2026-11-20，口径纠正）

此前把「J 空间行」的阈值读成 `covered_5tuple`（1174/1556），**这是口径错误**。表（L28–L32）写的是：

| 行 | 表内阈值 | 当前实测 | 状态 |
|---|---|---|---|
| J 空间 | 1556 全量 + `source_missing=0` `pyc_missing=0` `calls_missing=0` | 1556；`source_missing_non_excluded` **12→0**；`pyc_missing` **0**；`pyc_loadable` **1556/1556**（此前字段为 `null`，从未测过）；`calls_missing_non_excluded` **0**（449 非排除条目全有 calls；1107 排除条目无 calls 与 `excluded` 一一对应） | **达成**（376 条 excluded 无源码属客观 pyc-only 分布，如实标注，未计入分子） |
| 语义差分 | `unresolved=0`；C1–C5 齐全；R1–R7 无未裁决失败 | 全量 1556 四轮跑满（`round13/rows/SEMANTIC_J_FULL.md`）：**t33 权威（v2 judge 2110b736，2026-11-26）：EQUAL 1144 / DIFFERENT 0 / MIRRORED_EXCEPTION 412 / ERROR 0 / INCONCLUSIVE 0 / NO_C4 0；covered_5tuple 413、module_only 731；严格口径未解决 412、镜像口径 0**（t32 历史权威：EQUAL 1096 / DIFFERENT 30 / MIRRORED 364 / ERROR 48 / INCONCLUSIVE 18，严格 430、镜像 66）。t31→t32 迁移通道恰 5 条零意外：364 site-pkg 墙类全量翻镜像（镜像率 100%，两侧同 TickDataCache，G6 镜像块零违规）；48 探针族 TypeError/NameError 非 ImportError 族维持 ERROR；EQUAL/DIFFERENT/INCONCLUSIVE 1544 条逐字节同判；coverage_checker 零膨胀（t31/t32 输出逐位恒同，covered_5tuple 395 恒同） | **镜像口径 MET@t33；严格口径未达成**（→~~122.19 镜像 v2 族扩展裁决~~**已落地 r205**（48/48 定向翻镜像零真分歧，镜像裁决口径 66→18）→~~122.20 探针终止性修复~~**已完成 r206**（18/18 可判定：EQUAL 7＋DIFFERENT 11，INCONCLUSIVE 18→0；11 条单根因入 122.21 修复队列）→~~Task 124 Starred 12~~**已消解 r207**（同谱系单修复 12× 翻 EQUAL）→~~Task 123 for_in_try 签名~~**已消解 r208**（R7 三元组全消、census +9）→~~122.22 x02 pass 残留 6~~**已消解 r209**（A/B 同判官 6× 全翻 EQUAL、R7 归零、co_code strict-equal 回归）→~~122.21 x04 重建边界 11~~**已消解 r210**（V1 全形态重建 +143 纯插入，18/18 复测全 EQUAL、R7 归零、et 字节级全等、census 0 回退）→~~x05 背书 With 6~~**已消解 r211**（[R9-ELIDE-f3] 发射侧守卫 +16/−0：with 宿主发射序反转致 f2 登记无消费点；6/6 全翻 EQUAL、R7 归零、census changed=6 全族 0 回退）→~~Break 5＋While 1~~**已消解 r212**（6 条同源 c13 boom()、两独立根因同批修：B continue/break 目标归属＋A falsy 折叠死码 if 0: raise 重建；6/6 全翻 EQUAL、census changed=92 全 0 回退、x01 纯改善）→**30 原族 DIFFERENT 镜像口径归零**（Starred 12＋x02 6＋x04 11＋x05 6＋Break/While 6 共 41 条已翻 EQUAL）→**t33 全量终局读数（2026-11-26，权威从 t32 转移）：EQUAL 1144、MIRRORED_EXCEPTION 412、DIFFERENT 0、INCONCLUSIVE 0、ERROR 0；t32→t33 迁移矩阵零无主（1144=1096+30+18、412=364+48；t32 EQUAL 1096 新判官下零翻转）；covered_5tuple 413；严格口径 412 条 MIRRORED import-wall 待 Linux host B（既有结论不动）**——镜像口径 MET@t33 |
| 变异测试 | `missed=0` | G3 全量 912 案 **17 284 KILLED / 0 MISSED** | **达成** |
| 规则覆盖 | `open=0` | 证据门控 universe_v6：282 保留/62 排除（并集 344 守恒）；v8_b1（裁决二落定：B1 已工具强制，`--counting b1 --also-legacy`，2026-11-23）proved 126 / open 156 为历史基线；**2026-11-26 裁决三落定（采纳 `--structural-negative`）：行 4 工作基线 v8_b1+SN proved 144 / open 138**（guard_only 21 / neg 26 / no_occ 65 / false 26）；122.9 阶段一 no_occ 65 全定性闭合（(a)15 工具路径＋(b)19 死码＋(c)31 J 未覆盖形态，499 unmapped＝排除组精确镜像无需动作）；四项裁定：①SN 采纳；②(a)15 随 universe 刷新证据排除；③(b)19 修死优先/删除次之/排除兜底（agv2 集合守卫解遮蔽＋EXCEPTSTAR 96 复测；dict 兼容 17＋is_conditional 删除、census 门控）；④(c)31 扩 jspace 补形态；门禁 `rule_coverage_v8_b1.json` 历史读数 G4=FAIL（empty_cov 100）（`round13/rows/ROW4_RULE_COVERAGE.md`） | **未达成**（裁定后目标：分母 282→248、open 104（guard 21 / neg 26 / no_occ 31 / false 26）；先 core 修复批，再 jspace 扩形态，终局字面命令对齐） |
| G5 回归 | 全绿 | 402 分片 6617/6617、small34 1568/1568、quotation 153/153、pytest 2F/282P/2XP、IV.2 绿 | **达成** |

**教训**：`covered_5tuple`（J 行之外的覆盖率指标）与 J 行的四项存在性阈值是**两回事**。用前者代替后者
报「G1 FAIL」，等于用错的尺子量错了对象，并把可达性当成失败理由。

## 语义行与规则行读数落库（2026-11-22）

- **语义差分全量两轮**（`round13/rows/SEMANTIC_J_FULL.md`）：t5 与 t30（offset 0/778 两块）
  判定迁移交叉表**逐条稳定**（EQUAL 1083/1084、DIFFERENT 30/30）；t30 权威读数未解决 442。
  - **374 ERROR 根因四层（vendor 收口后终版）**：①runner 从未传 `package_root`（测量
    布线缺口）——**已修**：`semantic_runner.py` v1.1.0 `--package-root auto|off|<path>`
    默认 auto，37 条样本四项守卫断言全 PASS：守卫探针全 EQUAL 且无 package_root 字段、
    c3 产物 sha 37 条全与 t30 一致、`--package-root off` 复现旧 ERROR、全空间
    `--limit 3` 结构完好；②第三方 **logbook/tornado** 缺失——**已 vendor**
    （r197：logbook 1.10.1＋tornado 6.6.1，溯源 `rows/VENDOR_DEPS.md`；样本 5 条
    翻转 EQUAL＝JS-DECORATOR-001/002/005/006/007 fly/aes_encrypt 家族，链止于
    logbook）；③第三方 **zmq** 缺失——**已 vendor**（r198：pyzmq 27.3.0＋
    typing_extensions 4.16.0，`_zmq.pyd` add -f；布线 probe 27/27 越过 zmq 层）；
    ④**第四层墙**：`IQCommon.data.TickDataCache` 公司内部 Cython 扩展，语料唯一制品
    `TickDataCache.cpython-311-x86_64-linux-gnu.so`（Linux ELF，2,753,976 B），Windows
    CPython `EXTENSION_SUFFIXES` 不含 `.so` ⇒ 不可装载，非 PyPI 可 vendor（语料同类
    Linux `.so` 共 9 个）⇒ **vendor 路线收口**；37 样本 v3 复测 EQUAL 10/ERROR 27、
    零翻转零回退零 DIFFERENT、守卫四断言全 PASS（sample_out_v3.json）。残留处置
    →122.14「镜像异常等价」裁决；全量 t31 →122.15。IQData 在 J 中
    实际 0 条（此前推断有误）。2 条 t30-NO_C4（JS-IMPORT-015/JS-WHILE-037）样本
    三轮反编译成功未复现超时（30 s 边缘方差，暂态如实记录）。
  - t5 的 161 NO_C4 是 `--timeout 5` 对大体量真实模块太紧，t30 解开 159 条后暴露同一导入族。
  - **30 DIFFERENT 两轮完全稳定**＝真实语义差异，待逐族修复；18 INCONCLUSIVE 为超时口径。
- **规则覆盖证据门控链条落库**（`round13/rows/ROW4_RULE_COVERAGE.md`）：
  universe_v4 344 → v6 **282 保留/62 排除**（双门槛＝opcode-set 成员全部不在
  CPython 3.11 `dis.opmap` 且 `symbol_observed=False`；7 条被观察证据救回；并集守恒）；
  proof v6 **proved 136 / open 146** → v7（`--also-legacy`，2026-11-22）**proved 144 /
  open 138**（no_occ 65 / false_at_site 26 / neg_missing 47；9 翻正 ＋ 1 回退净 +8；
  legacy_v2 管线实测缺陷 2 例：m06 `chain_assign_state` UnboundLocalError、m08
  `_get_compare_op` AttributeError）。
  **proved 口径更正（2026-11-22 复核）**：`guard_only`（`symbol_observed=False`）规则
  被工具**计入** proved（B2 宽松式）；`G4_REVIEW_PACKET` 裁决二推荐的 B1 保守口径
  **已于 2026-11-23 落定并在工具强制**：`rule_proof_check.py` v1.2.0 `--counting
  {b1,b2}` 默认 b1——proved 额外要求 symbol_observed=True，guard-only 降级为 open
  （新码 `guard_only_symbol_not_observed`＋b1_downgrade 诊断，proof/witnesses 保留）。
  **v8 权威读数（对外报告基准）：proved 126 / open 156**（guard 降级 18 / no_occ 65 /
  false 26 / neg 47）；region-only 交叉 114/168 与 v6 事后推算逐位一致；三组回归
  guard 全 PASS（b2 全量复测 vs v7 逐规则 diff 空、282/282；b1 与事后推算逐位一致；
  降级集恰 18 条、12 条 guard_only-open 不变）。新 reason code 无封闭枚举校验消费者
  （下游影响清单已核查）。门禁 `rule_coverage_v8_b1.json`：G4=FAIL（empty_cov 100
  为主因）。**输入陷阱留档**：`rule_manifest.py --check`
  缺 `--traces` 读 339 open=proved 0；universe/manifest 不同域会把 62 排除规则算成
  orphan（open 虚高 208），须用 `manifest_proved_v8_b1_scoped.json` 配对。
- **工具入库**：`rule_proof_check.py` v1.1.0 增两个默认关闭开关（`--also-legacy`、
  `--structural-negative`，关闭时与旧口径逐字节一致）→ **v1.2.0 增 `--counting
  {b1,b2}` 默认 b1（裁决二强制，b2 显式复现 1.1.0）**；`rule_universe.py` v1.1.1 增
  `--opcode-scope`（默认 `any` 不变）。

## 语义行 t31 权威读数落库（2026-11-23）

- **t31 全量重跑完成（122.15）**：两块串行（前次并行尝试因子代理失活后台作业被杀，
  复盘后改串行＋跑批全程保持活跃），1556 条跑满，exit 3＝有 ERROR 判定预期非崩溃。
  **t31 联合读数＝EQUAL 1096 / DIFFERENT 30 / ERROR 412 / INCONCLUSIVE 18 /
  NO_C4 0；未解决 430**。judge 冻结 sha=d31948b3… 与 t30 一致（per-record c5
  失配 0）；runner v1.1.0 布线 auto。
- **t30→t31 迁移交叉表（1556 aligned）**：EQUAL→EQUAL 1084、DIFFERENT→DIFFERENT
  30、INCONCLUSIVE→INCONCLUSIVE 18、ERROR→ERROR 410 稳定；`ERROR→EQUAL` 12 条
  全部＝fly/common/aes_encrypt.pyc（JS-DECORATOR-001/002/005/006/007/008/009/
  010/011/012/015/016——不依赖 TickDataCache，布线＋vendor 后全程执行成功）；
  `NO_C4→ERROR` 2 条＝时序翻转集 {JS-IMPORT-015, JS-WHILE-037}（trade_live_broker
  ~30 s 边缘逐次运行随机落点，本轮 42 条全部反编译成功）。kept 人口学 449 逐类
  两轮恒同；covered_5tuple 395 恒同；module_only 719→731。
- **守卫**：G0 完整性 PASS；G1 冻结 PASS；G3 零漂移 PASS（两轮都出 c3/c1/c2 的
  记录 SHA 逐位一致、失配 0；git 漂移恰 2 文件＝时序翻转集，已复原 tracked 态）；
  G4 DIFFERENT 集合恒同 PASS；G5 守卫探针＋布线 PASS；G7 INCONCLUSIVE 18 逐条
  复现 PASS（零新增）；G6/G8 根因分解与结构计数落库。
- **根因终局（双侧探针实测）**：残余 364 条 site-packages ERROR 的 6 distinct pyc
  布线态探针 6/6 统一死于 `No module named 'IQCommon.data.TickDataCache'`；
  未布线态对照逐 pyc 死于首导入层——死亡层前进链条闭合。48 条探针 ERROR＝
  4 族探针源码自身确定性模块级崩溃（TypeError `with (CFG if 0 else json) as j`、
  NameError path/_CM/B 各一），48/48 根因逐字不变，非 ImportError 族（镜像 v1
  不覆盖，如实保持 ERROR）。
- **下一步**：122.14 镜像异常等价裁决实施（方案 D 已裁决；MIRRORED_EXCEPTION→
  37 样本验证（唯一允许翻转 27 ERROR→MIRRORED）→全量 t32 隔离 judge 变量）；
  修复轮次（30 DIFFERENT 逐族＋Task 123/124）在 t32 落地后启动（core 冻结期间
  不动本体），终局以全量 t33 收读数。

## 语义行 t32 权威读数落库（2026-11-24）

- **122.17 镜像裁决实施完成＋122.18 t32 全量完成**：r203 落地
  `MIRRORED_EXCEPTION`（semantic_diff v1.1.0／semantic_runner v1.2.0／
  coverage_checker v2.1.0），37 样本验证 a–g 全过（27/27 ERROR→MIRRORED、10
  EQUAL 不变、exit 4、布线守卫判别力得证）；t32 全量两块串行（a 56m13s、b
  44m56s，均 exit 3，总 101m8.5s），1556 跑满。
- **t32 联合读数**：EQUAL 1096 / DIFFERENT 30 / MIRRORED_EXCEPTION 364 /
  ERROR 48 / INCONCLUSIVE 18 / NO_C4 0。judge sha=8b6e6a61…b83004a（换代
  预期）；严格口径未解决 430、镜像裁决口径 66。
- **t31→t32 迁移交叉表（1556 aligned）**：通道恰 5 条零意外——ERROR→
  MIRRORED 364（site-pkg 墙类全量，**镜像率 100%**，两侧同 TickDataCache
  消息，第一层 0，谓词零漏捕零误捕）；ERROR→ERROR 48（4 探针族×12，
  TypeError/NameError 非 ImportError 族）；EQUAL→EQUAL 1096；
  DIFFERENT→DIFFERENT 30；INCONCLUSIVE→INCONCLUSIVE 18。形式不变式兑现
  （旧判 1544 条逐字节同判，仅 c5 代际域漂移）。
- **守卫 G0–G8 全过**：G1 换代一致逐记录 0 失配；G3 零漂移（1556 条 c1/c2/c3
  bitwise 失配 0；git 漂移恰方差集 2 文件已复原）；G6 镜像块 364 条零违规
  （七键齐全、两侧 canonical 全等、exit_code=4、unexecuted/mirror_exception、
  package_root=site-packages 364/364）；G8 coverage_checker v2.1.0 对 t31/t32
  证据实跑**输出逐位恒同**（covered_5tuple 365＋r7_only 30＝395、inconclusive
  54、excluded 1107、coverage 23.46%）——**全量零膨胀断言过**，MIRRORED 364
  全部 excluded 入口入分子 0；G7 残余 ERROR 48 全部 test_repros（ANNASSIGN/
  WITH/TRY/IMPORT 各 12），site-pkg 残留 0。
- **方差集占位债收编（r204）**：JS-IMPORT-015/JS-WHILE-037 两产物在 t30 提交
  内为 0 字节占位（超时态），与两轮记录 c3 sha（5999726a…）不符、每轮漂移；
  r204 起提交真实反编译产物（178,804 B，sha 逐位一致），checker 交叉验证该
  2 行恢复在盘校验（verdict null→MIRRORED_EXCEPTION），totals 逐位不变。
- **下一步**：122.19 镜像 v2 族扩展裁决（48 探针源码崩溃纳入谓词，接受则镜像
  口径 66→18）→ 30 DIFFERENT 修复轮次＋Task 123/124（core 解冻）→ 18 超时
  收敛 → t33 终局。

## 语义行 122.19 镜像 v2 落地（2026-11-24，r205）

- **裁决**（父代理，tasks.md 122.19 全文）：接受 v2——族白名单
  {ImportError, ModuleNotFoundError, ZipImportError, **NameError, TypeError**}
  （48 条残余 ERROR 全部实测族：TypeError×1 m04_module_try＋NameError×3
  c01_class_assign/c05_class_with/c4_15_star_import，各 12 条）；其余谓词
  逐字不变；进程控制类经 worker harness 白名单结构性排除（SystemExit 等
  harness_error=True 不入谓词）；exception_info 无位置敏感字段（L270–284）
  故 canonical 等价可判；mirror 块 exception_family 改实测族名（364 条 v1
  镜像实际类型＝builtins.ModuleNotFoundError，标注改进非回退）。
- **实施**（子代理 ec485c94，单文件 +42/−23）：semantic_diff v1.1.0→v1.2.0；
  新 judge_sha256 `2110b7367bb1f479f03892d62f0211e42e84711442e56cd618d2af7634ab9fdb`
  （t32 基线 8b6e6a61… 失效，下游审计一律新值）；semantic_diff_selftest
  26/26×2。
- **61 条定向验证全过**：**48/48 翻 MIRRORED 零真分歧**（逐族 12/12，墙钟
  170.4s）；3 site-pkg 镜像控制保持（族实测 ModuleNotFoundError）；5 守卫
  EQUAL 无 package_root；5 EQUAL kept 零行为变化；镜像块完整性 G6 式 51 条
  零违规；c1/c2/c3 零漂移＋products git 0 行；covered/module_only 切片不变。
  **镜像裁决口径未解决 66→18**（权威仍 t32，t33 v2 judge 转权威）。
- **附属诊断（18 条 INCONCLUSIVE，--timeout 120 定向复测，墙钟 4347.9s）**：
  18/18 两侧仍全挂（orig/prod 最长 120.34s/120.53s，零新信号）⇒ 墙钟不收敛
  ＝结构性挂起；**根因立案 122.20**：18 条全部见证自 round2 x01_if_deep_hosts
  （7）/x04_try_deep_hosts（11）两探针源（恰为两 pyc 全部条目），其
  `*_in_while()` 内层 `while 1:` 无 break、外层 break 不可达＝被调用即死循环；
  Task 5.3 input_model 派生源内全部零参可调用 ⇒ 全条目挂死。修复路线＝探针
  源最小终止修复（保 label/d3plus）＋pyc 重建＋空间 18 条更新（r8fix 先例）
  ＋定向复测收真实判定（worker calls 期逐调用异常记录已核实，非致命中止）。
- 产物：D:\temp\opencode\cl_layout\g4d\route2v2\（REPORT_12219_v2.md、
  v2_scoped_out.json、inc18_out.json、inc18_timings.json、scoped61_space.json
  等）。

## 语义行 122.20 探针终止性修复（2026-11-24，r206）

- **最小终止修复**：两源各恰 ＋1 行 16sp `break`（x01 L17＝if_in_while 内层
  while 体、x04 L36＝try_in_while 内层 while 体 try/finally 后），其余零 diff；
  AST 剥离 Break 后新旧 dump 逐字节同；p_j_sha256→c0b41f43…（58 行）/
  824e1480…（78 行）；12/12 函数 30s 上限零挂死。
- **pyc 同版重建**：x01→d574158f…、x04→418449ac…（D:/Python 3.11.7
  py_compile；`*.pyc` gitignore 惯例不入库）。
- **空间＋登记**：恰 18 条 × 4 字段（p_j_sha256/pyc_sha256/p_j_lines/note
  括号内登记续接），其余 1538 条逐字节不变；登记矩阵
  `rounds/round13/rec1_probe_repair_12220.json`（仿 r8fix 全字段含
  retest_verdict）；18 产品再生成。
- **定向复测（v2 judge 2110b736…）**：**18/18 可判定、零 INCONCLUSIVE/
  零 ERROR——EQUAL 7（x01 全部）＋DIFFERENT 11（x04 全部）**；per-call 双侧
  全等（1/2/3/NameError/5/0）。
- **11 条 DIFFERENT 未掩蔽**：单函数（try_in_while）单 R7 diff
  （co_exceptiontable）：pycdc 将内层 while 1:（尾随无条件 break）折叠为
  if 1:、并将外层 try 体内尾随 break 重定位至不受保护的 else 子句 ⇒
  保护域边界差 2 code unit（原 `28 to 34 -> 38 [0]` vs `28 to 32 -> 38
  [0]`）；co_code/co_consts/co_flags 与行为全等；x01 同类折叠回编恒等
  （EQUAL 对照）⇒ **122.21 立案**（与 30 原族零重叠，DIFFERENT 总量
  30→41；FIXTEST＝x04 新 pyc 418449ac… unit `***<module>.try_in_while`）。
- **镜像裁决口径**：INCONCLUSIVE 18→**0**（pending t33 权威）；未解决
  ＝DIFFERENT 41 修复队列（122.21＋122.8）。
- **登记债**：round13/jspace_v3/judgment_space_v3.json 18 条仍登记修复前
  源（stale 簿记，runner 不校验 sha 非运行阻断）——v3 流程复跑/定稿时须
  先重建该 18 条；历史审计快照不回写。

## 语义行 Task 124 c4_12 kwargs 折叠修复＋Starred 12 消解（2026-11-24，r207）

- **修复**：`core/cfg/ast_generator_v2.py` 单 hunk L547（+19/−1，
  `ExpressionReconstructor._flatten_dict_merge_to_kwargs`）——d2 分支前置
  守卫：d1 空字面量 Dict（BUILD_MAP 0 基座）＋d2 字面量 Dict ＝ 形式 (b)
  `**` 解包 dict 字面量 ⇒ 追加 `KeywordStarred`（保留 `**({...})`），
  不进 v154 展开；关键字对/变量解包/关键字基座均不进新分支（变化面 ⊂
  v154 引入轮）。core sha256 `b8fe4ff39470a156…`（BOM 完好，父代理抽查
  逐字符一致）。
- **验收链全过**：FIXTEST 12/13→**13/13**（e04_deep 转成功）；in-place
  OK.py 一步刷新 13/13；五案门 5/5 SAME＋judge OK（e01/v_b71/e02/r9_02/g4b
  良品 sha16 全同）；census 2510 pyc changed=3、**0 回退、纯改善 +5 单元**
  （c4_12 +1、r5v5_07 +2、REAL46-014 +2，后两者形式 (b) 同族——修复整体
  生效非特例）。
- **跨轮 J 快照（t32_b 基线 A/B 同判官）**：12 条 JS-STARRED
  **DIFFERENT→EQUAL 全翻**（A 与冻结 t32_b 逐字节一致＝基线复现；overlay
  EQUAL 589→601、DIFFERENT 19→7、covered_5tuple 257→257 不减）。判官
  漂移双口径如实（v2 r205 换代 245 条 c5_judge_mismatch 两侧同现伪影）。
- **Starred 谱系判定：同谱系**——12 条＝同一探针 c4_12 的 12 次分类学探针
  （src/pyc/product/diffs/输入模型五元全同），溯源唯一根因＝e04 kwargs
  折叠；单修复全翻。**DIFFERENT 待修 41→29**（With 9＋Break 5＋4 单例＝
  18 原族余量＋122.21 x04 重建边界 11；pending t33 权威）。
- **登记**：残留 v154 限制（变量解包后位空字面量 `f(*xs, **d, **{})` 静默
  丢弃，census 现网 0 受影响产物）低优先级入读数；方法论事故入簿（pwsh
  管道重定向破坏 git show 字节 → git 内容落盘一律 `cmd /c` 字节忠实重定向）。
- 工件：`D:\temp\opencode\cl_layout\g4d\p124\`（census×2 树、A/B 语义记录、
  overlay、覆盖检查）。

## 语义行 Task 123 x02 finally 消隐修复（2026-11-24，r208）

- **根因（probe123 实证）**：try/finally 为循环体末语句时 CPython 3.11 把
  finally 异常路径副本（蹦床块）发射在环回边块之后，容器 try 全区间
  (38,96) 越出宿主环区间 (4,82)，`_build_region_hierarchy`「容器区间 ⊆ 环
  区间」裁决失配，退化通用优先级 max（环 5＞try 3）⇒ for-j 误挂宿主环、
  finally 消隐、异常表 7→3；block_to_region 结构事实（for-j 三块 canonical
  owner 均为内层 try）支持 try 为父。
- **修复**：`core/cfg/region_analyzer.py` `_build_region_hierarchy` L38843
  单 hunk +31/−4（[v208-FINSPAN]）：通用回退前补充裁决——容器 TryExceptRegion
  声明保护跨度（try_offset_start…end）嵌于环区间且 child 各块 canonical
  owner 全为容器 ⇒ 容器为父；只读区域/块数据、不命中逐位不变。BOM/LF/
  ast.parse 完好，sha256 `323c03e0…`（父代理抽查逐字符一致）。
- **验收链全过**：FIXTEST 6/7→**7/7**（for_in_try 转成功）；in-place OK.py
  一步刷新（旧 `6D6B3556…`→新 `00D5EF34…`＝产物逐字节，就地 7/7）；五案门
  5/5 SAME＋judge OK；census 2510 changed=9 全 IMPROVED、**0 回退、纯改善
  +9 单元**（x02 正主＋7×rec1_x02 拷贝 6/7→7/7＋b87c/b87d 1/2→2/2，全部
  try/finally-环尾同族无意外扩散）。
- **J 快照（t32 权威，A/B 同判官 2110b736）**：受影响 6 条全 x02 pyc
  （t32_a 5：JS-IF-115、JS-TRY-077、JS-WITH-034/064/076；t32_b 1：
  JS-CONTINUE-025）；A 与冻结逐字节一致（e8e95f95 基线复现）；B 仍
  DIFFERENT×6 但 **R7 深度 4→1**——for_in_try 缺陷签名（co_code/
  co_exceptiontable/co_stacksize 三元组）全消；唯一残留＝for_in_while.
  co_code ＝**新谱系：环出口 pass 残留**（产物 while-1 出口函数级多发一条
  `pass`，重编译 co_code 88→90B 多 2B NOP；pyc_verify NOP 容差故 FIXTEST
  不扰；改前即存在属 region_ast_generator 环出口渲染独立旧谱系）——
  **122.22 立案**（6 条翻 EQUAL 唯一阻塞；良品＝2026-10-25 OK.py 快照
  for_in_while 渲染无残留 ⇒ 表示级回归，bisect 窗口待收）。
- **根因族重分组（余 18 条）**：x02 pass 残留 6（→122.22）＋x05 背书 With
  6（JS-WITH-017/020/033/047/054/075，诊断待做）＋Break 5＋While 1
  （JS-BREAK-001/011/023/027/030、JS-WHILE-040，pyc/根因待诊断）。
- 工件：`D:\temp\opencode\cl_layout\g4d\p123\`（probe123 根因证据、census
  全量、A/B 判官 9×2、J 复判 mini_space、R7 路径分解）；基树 D:\bt123
  （HEAD 提取 1.2GB 保留抽查）。

## 语义行 122.22 x02 环出口 pass 残留修复（2026-11-24，r209）

- **修复**：`core/cfg/region_ast_generator.py` 4 处编辑（+48/−2，设计
  [R9-ELIDE-f2] 无偏离）——trivial 路径 pass 占位符登记 (placeholder,
  offset)（L70712）、while-1 shell 成功记尾 NOP 偏移（L3442）、`_generate_loop`
  分派按**对象身份**从尾随语句剔除被壳消费的占位（L7991，无登记/不匹配逐位
  旧行为）、__init__ 初始化（L624）。机制＝同一尾 NOP 双重表示（占位 pass
  ＋壳 break 重编译）→ 身份去重。实例同一性经探针实证。BOM/LF/ast.parse
  完好，sha256 `2e453a19…`（父代理抽查逐字符一致）。
- **验收链全过**：FIXTEST 7/7 维持；**for_in_while co_code strict-equal
  回归**（`d8381219…`/90B → `de415811fb4a3811`/88B＝orig，+2B NOP 消除）；
  in-place OK.py 一步刷新（旧 `00D5EF34…`→新 `1DE52821…`＝产物逐字节，
  −1 行函数级 pass，就地 7/7）；五案门 **5/5 SAME**（r9_02 双 continue 同形
  未变）；census 2510（基树＝HEAD a8cf8e57 全新 git archive）changed=7 全
  x02 缺陷族、**0 回退**（7× SAME_UNITS 7/7→7/7）。
- **J frozen6 A/B 同判官 2110b736**：A 6× DIFFERENT（diffs=[R7]，产物
  00d5ef34 残差复现）→ **B 6× EQUAL（diffs=[]，产物 1de52821）——6 条全翻、
  R7 归零**；covered_5tuple 两侧 6、判官同一。**DIFFERENT 待修 29→23**
  （12 原族余量＋11 x04；pending t33 权威）。
- **良品考古定论（修正立案文本）**：r13 权威 strict-equal 工件＝J 产物
  （blob `6caeaf8d`）而非旧 OK.py（其 for_in_while 停留 if-1 陈旧中间态
  86B 非 strict-equal）；本修复产物与 r13 J 产物全文件 LF 逐字节一致
  （`611e46e0…`）＝恢复历史判 strict-equal 权威形态，严格优于旧 OK.py。
- **注意在簿**：编辑工具写盘剥 BOM——region_ast_generator.py 每次编辑后
  须字节前缀恢复；旧判官→新判官 R7 收紧是 6 条阻塞直接成因（t32 快照口径
  与新判官读数不可混算）；fivecase.py 工具 g4b 路径 round3→round5 笔误。
- 接力过程如实：前任子代理 cb8ef731 诊断定稿后实现前崩溃（零文件改动），
  设计无损移交接力子代理 b414e496 完成。
- 工件：`D:\temp\opencode\cl_layout\g4d\p123\p12222\`（f22_ 前缀全套）；基树
  `D:\f22bt_a8cf`（留抽查）。

## 语义行 122.21 x04 try_in_while 重建边界修复（2026-11-24，r210）

- **修复**：`core/cfg/region_ast_generator.py` 纯 +143 行（0 删改）——新增
  helper `_r12221_try_body_while_shell_rebuild`（识别：body_stmts 恰两条折叠
  占位＋Try、else 候选恰一块单条 JUMP_FORWARD 逃逸宿主 LoopRegion、
  try_blocks≥3 NOP 首尾结构）＋`_generate_try` 一处接线；命中整体重建为
  `[While(test, body=[inner, Break]), Break]`（**V1 全形态**＝内层 while-1
  壳＋try 体尾随 break），不中逐位保持。识别纯字节码结构链，无特判。
  BOM/LF/ast.parse 完好，sha256 `6b576ae6…`（父代理抽查逐字符一致）。
- **根因定稿（含草案订正，实证）**：CPython 3.11 else 子句位于 try 体与首个
  handler**之间**（3 次受控编译证实，订正立案草案「handler 之后」）；HYBRID
  与 V3 形态证伪——**读 else 结构永远修不了异常表**；受保护区终点＝try 体
  最后出口跳转，被消跳的内层 break NOP 在区内则受保护；唯 V1 全形态字节级
  与 ORIG 全等（co_code 80B、et `(28,36)→38` 字节 13＝0x04、全 7 条目）。
- **验收链全过**：FIXTEST x04 7/7（父代理复验 success）；**18/18 复测全
  EQUAL**（11 x04 全翻＋7 x01 控制组保持；判官 2110b736）；x01 产物 pre/post
  逐字节一致（回编恒等不变式）；五案门 **5/5 SAME**；census 2510（基树＝
  HEAD a817baa3 全新 worktree）**CHANGED=2 零回退**（297s）；5 守卫近失形态
  A/B 逐字节一致全不误触。
- **漂移 13 文件**＝core＋x04 OK.py（一步刷新，blob `38762db6` 与 11 份
  B 侧产物同源 sha `f13e2a06…`）＋11 份 semantic_products 原地再生（B 侧
  产物入库遵循 item 8 政策）。**housekeeping**：x01 OK.py 陈旧快照（HEAD
  即陈旧、与本修复无关）父代理一步刷新 `0D12595B…`→`AD3523CD…` 就地 7/7。
- **DIFFERENT 待修 23→12**（全为原族余量：x05 With 6＋Break 5＋While 1；
  Starred 12＋x02 6＋x04 11 共 29 已翻 EQUAL pending t33 权威）。
- 续用子代理 b414e496（用户指令：不新开）。工件：
  `D:\temp\opencode\cl_layout\g4d\p12221\`（f21_ 前缀全套）；A 侧基树 worktree
  `D:\f21wt_a817` 留复核。

## 语义行 x05 背书 With 6 条修复（2026-11-24，r211）

- **对象**：JS-WITH-017/020/033/047/054/075（t32 两轮稳定 DIFFERENT，全背书
  `test_repros/round2/x05_with_deep_hosts.pyc`，sha256 前缀 `CEF190C31F341686`，
  3578B）。现判官基线（HEAD 98cf5a17，2110b736，--timeout 30）：6/6 DIFFERENT
  全 R7，共享产物 sha16 `7c11d521e6d3d015`。
- **根因（单根因，受控证伪确认）**：源 `while 1: with _A() as a,...: R=...;
  break`＋尾部 return——`_generate_with`（L48680）调 `_r9_loopless_while1_shell`
  成功建壳并记尾 NOP 偏移 164；随后外层 trivial 路径发射**裸 pass 占位并登记
  (ph,164)**——但 [R9-ELIDE-f2] 唯一消费点在 `_generate_loop` 分派（for 宿主
  序：发射→壳→消费）；**with 宿主序相反（壳先建、占位后发射）→ 登记无消费
  者 → 游离 pass → 重编译 +1 NOP（172B vs orig 170B）→ R7 全 DIFFERENT**。
  证伪（px05w6/x05_falsify.py）：产物仅删该游离 pass → with_in_while 全字段
  逐字节相等（co_code 170B==170B）→ 唯一可行形态。仪器化确认 While 节点由
  `_r9_loopless_while1_shell` 产生（x05 CFG 无 LoopRegion，b70j 路径不适用）。
- **修复**：`core/cfg/region_ast_generator.py` [R9-ELIDE-f3] 发射侧守卫
  **+16/−0**——trivial 路径 NOP 处理 else 分支发射点：壳已认领该 NOP 为尾
  break 标记（`_r9_shell_tail_nop_offset` 运行时记录＝本 code object 实际尾
  NOP 偏移，无函数名/硬编码偏移特判）时跳过发射与登记。`_pop_head_const()`
  队列游标语义逐位不变；falsy 分支不动。次序安全：for 宿主（x02::for_in_while）
  发射先于壳 → 寄存器未置 → 守卫不命中 → f2 登记＋分派消费逐位不变。BOM
  EF BB BF 已恢复，sha256 `a9b630f1…`（父代理抽查逐字符一致）。
- **验收链全绿**：6/6 B 侧全翻 EQUAL（per-call，diffs=[]，产物
  `c5c6f2a3b1f7c471`＝OK.py 逐字节，父代理复验 BYTE-IDENTICAL＋7/7）；五案门
  5/5（产物与 r210 全等）；守卫：8 姊妹族（x01–x09 整 pyc）逐字节一致、
  x05 阳性对照 A≠B、4 合成守卫（G_FORHOST/G_B70J/G_REALLOOP/G_CONDFLOOP）
  A/B 逐字节一致；census 2510（基树 98cf5a17 全新 worktree）CHANGED=6 全
  x05 家族、**0 回退**；changed 6 逐个 A/B 判官 6/6 DIFFERENT→EQUAL；
  OK.py 刷新前后字节相同（本就正确形态，仍按规程执行）。
- **漂移恰 1 文件**（core +16/−0）。锚点复核全过（判官 2110b736、pyc_verify
  FE1902A90CEBD4A15、外检 9C7567BD6776B36B、x05 pyc CEF190C31F341686）。
- **开放问题登记（另立任务评估）**：G_WHILEFALSE 形态（`while 0: pass` 残差
  与 while-1 消隐壳同函数）——falsy 分支发射次序既有形态问题（基线即如此、
  A==B 无回归、不在本 6 条 J 判据内）；产物 co_code 92B==92B 内容差（残差
  节点在壳后发射、NOP 次序与真值相反）。**工具教训（在簿）**：r7 深比较器
  ——Python code object 无值相等（co_consts 元组含 code object 恒不等），必须
  逐元素递归比较（初版探针受此误导，已修正）。
- **DIFFERENT 待修 12→6**（Break 5＋While 1 最后一族；Starred 12＋x02 6＋
  x04 11＋x05 6 共 35 已翻 EQUAL pending t33 权威）。
- 续用子代理 b414e496（用户指令：不新开）。工件：
  `D:\temp\opencode\cl_layout\g4d\px05w6\`（x05_ 前缀全套）；A 侧基树
  worktree `D:\f21wt_b17` 留复核。

## 语义行 Break 5＋While 1 条修复（2026-11-25，r212）

- **对象**：JS-BREAK-001/011/023/027/030＋JS-WHILE-040（t32 两轮稳定
  DIFFERENT）。诊断结论：6/6 同源 `test_repros/round2/c13_class_misc.pyc`
  （sha256 `78eea14c…5915`）boom() 单函数 R7 差异；**两独立根因 A/B 同批修**
  （父代理裁决：同 pyc 同函数、R7 逐字节判据须同批才翻面；实施序 B→A，
  中间归因检查点——B 后 pyc_verify 3/3 但 6 条仍 DIFFERENT（A 残留
  NOP@2/'x'/ValueError），归因成立后实施 A）。
- **根因 B（continue/break 目标归属）**：B-1——`_if_generate_normal`
  [R68-diag3] `_has_explicit_continue` 只查 opname 不查跳转目标，把嵌套
  while 的 `else: continue` 回边（JUMP_BACKWARD→while 头@50）误判为本
  for 循环（头@34）显式 continue → for 体尾追加假 Continue；修复加目标
  校验（trailing JUMP_BACKWARD argval ∈ 本循环 header/条件偏移集；
  `_current_loop` None 时回落旧 opname-only 扫描）。B-2——
  `_loop_extract_self_loop_stmts` while-1 头内联 if(i) 生成时
  `_jump_to_continue=True` 但 else 臂硬编码 `orelse:[]` → @58 蒸发；修复
  在 `_loop_handle_header_no_condition` else 分支按「纯 JUMP_BACKWARD→
  本循环头」判别式发射 `[Continue]`（不命中维持 `orelse:[]` 旧行为）。
  falsification：block_roles 全角色 patch 5 变体输出逐字节不变（排除
  role 驱动）＋插桩逐级定位＋V-variant 矩阵（V1/V2 True，V3/V4 False）。
- **根因 A（falsy 折叠死码不重建）**：CPython 3.11 把 `if 0: raise
  ValueError('x')` 折叠为入口序言 NOP@2 行标记，'x'/'ValueError' 残留进
  co_consts/co_names；pycdc 现有机制只覆盖无引用数值常量。修复＝
  `_build_function_def` 三证据合取保守触发（入口序言 NOP（RESUME 后、
  首实质指令前）＋co_consts 恰一个未引用 str 常量＋co_names 恰一个未
  引用 name，缺一回落），重建 `if 0: raise <Name>(<Const>)` 插 body[0]；
  co_consts `(None,0,'x',2)`/co_names `('ValueError','range')` 自然落出
  无手工排序；幂等护栏 `_r212_dead_code` 标记防函数级＋宿主级双插。
  实现坑（在簿）：`func_obj` 是 dict，真 code 对象是局部 `code_obj`——
  v1 读错静默不触发，改 `locals().get('code_obj')`。
- **core 累计**：`region_ast_generator.py` 5 处编辑 +113 行，sha256
  `84c8c0da4023742f…`（父代理抽查逐字符一致，BOM efbbbf，ast.parse OK）。
- **验收链全绿**：FIXTEST c13 3/3 success；OK.py 一步刷新
  `5ed47ffb…`→`25e118d3…`（567B＝最终产物，父代理复验 BYTE-IDENTICAL）；
  6/6 B 侧 per-call 全翻 EQUAL（ba_judge.json：verdict EQUAL、diffs=[]、
  covered_5tuple=6、judge 2110b736）；五案门 5/5；census 2510（基树＝HEAD
  fefaf998 git archive 全新提取）changed=92 逐个 A/B pyc_verify 判定
  **file_regressions=0、unit_regressions=0**（92 全双侧同 status 同 units；
  failure×5/compile_error×1/error×4 预存在双侧同）——**B-1 修复广泛
  去除 corpus 假 continue（92 个 pyc 产物文本变化但字节码不变）**；
  守卫负例 A/B 逐字节一致（B-1 负例双层 for 内层 continue 不误插；A 负例
  入口 NOP 无 str/name 证据不触发）；x01–x09 姊妹族整 pyc A/B：x02–x09
  8 个 IDENTICAL、**x01 DIFFERENT＝纯改善**（B-1 正例：base 假 continue
  移除，双方 compiles OK、pyc_verify 双 7/7）。
- **漂移恰 2 文件**（core +113、OK.py 刷新）＋父代理按 item 8 政策刷新
  6 份 semantic_products（JS-BREAK-001/011/023/027/030.py、JS-WHILE-040.py
  旧 `43D02194`→新 `25E118D3` 全符）。
- **事故记录（如实）**：census 首轮后台 job 被会话重启杀掉（0 shard 落
  盘），前台重跑 16/16 完整；corpus_census.py 默认 shard glob 误吞
  *_report.json 致 TypeError（工具既有坑，未改仓库工具，8 个显式 --index
  绕过：A=402 对齐 A_delta=0、products_ok 402/402、missing 0）；changed
  判定脚本首版正则漏 success_rate=- 形态 5 条误归 NO-PARSE，核实实为
  error/compile_error 双侧同状态，已如实归类。
- **DIFFERENT 待修 6→0**（镜像口径；30 原族全消解，41 条已翻 EQUAL
  pending t33 权威）。
- 续用子代理 b414e496（用户指令：不新开）。工件：
  `D:\temp\opencode\cl_layout\g4d\pbrw1\`（全套 ba_/b_mid_/census_*/ab_
  guard 脚本与读数 JSON、base_r212_tree/、base_r212.zip）。

## 语义行 t33 全量终局读数（2026-11-26）

- **1556/1556 全读出：EQUAL 1144、MIRRORED_EXCEPTION 412、DIFFERENT 0、
  INCONCLUSIVE 0、ERROR 0**；covered_5tuple 413、module_only 731。行 2 权威从
  t32 转移至 t33（v2 judge `2110b736`；HEAD `0610e563`＝r212）。
- t32→t33 逐条迁移矩阵（`rows/t33_vs_t32_matrix.json`）零无主条目：t32
  DIFFERENT 30 全 EQUAL、INCONCLUSIVE 18 全 EQUAL、ERROR 48 全 MIRRORED
  迁移、EQUAL 1096 零翻转、MIRRORED 364 稳定；对账恒等式 1144=1096+30+18、
  412=364+48。**新判官未把任何旧 EQUAL 翻负**；41 条修复链（Starred 12
  r207＋x02 6 r209＋x04 11 r210＋x05 6 r211＋Break/While 6 r212）全部经
  权威运行复核为真。
- **行 2 镜像口径 MET@t33**（unresolved=0 且 DIFFERENT=0）；严格口径 412 条
  MIRRORED_EXCEPTION（site-packages import-wall 执行差）待 Linux host B，
  既有结论不动，诚实双读数。
- 执行：26 段前台分段循环＋断点续跑（子代理 b414e496 续用）；6 条高负载噪声
  读数单条重试全恢复（JS-WHILE-019/JS-DECORATOR-003/JS-FSTRING-017 pycdc
  超时、JS-DECORATOR-001/002 判官超时、JS-FSTRING-015 original worker error；
  重试 MIRROR×4、EQUAL×2 与 t32 同判）；纯跑 2h08m41s（a 2902s＋b 4819s）＋
  retry 41s。首段后曾因后台 job 随 turn 结束被杀空转 22 分钟——教训入册：
  子代理长跑一律 turn 内前台分段循环，禁后台 job 托管。
- 产品目录 t33 全量再生（103 份 semantic_products 刷新一并入库）；工件
  `D:\temp\opencode\cl_layout\g4d\t33\`（parts/ 26 段原始落盘、retry_log.json、
  t33_run.py/t33_retry.py/t33_vs_t32.py）；入库 `rows/semantic_j_full_t33_
  {a,b}.json`、`rows/t33_vs_t32_matrix.json`。
- t33 后开放面：严格口径 host B 执行（低边际价值）；jspace_v3 18 条陈旧登记
  刷新；G_WHILEFALSE 另立任务评估（r212 已实证与 Break/While 族无关）。
