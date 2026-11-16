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
