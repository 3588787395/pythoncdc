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
- [ ] G4 339 条规则 witness/trace 完成，`open = 0`
- [x] G1/G2a/G2b/G2c/G3/G4 复跑并更新 gate_report（GATE_REPORT_V5R06：overall BLOCKED，全部实测读数）
- [ ] G5：402 八分片 6617/6617、small34 1568/1568、quotation 153/153、pytest 基线、IV.2 全绿
- [ ] 基本比较器独立复跑，读数与基线一致
- [ ] G6 使用独立 custody；24/24 EQUAL、0 leak、轮换记录齐全
- [ ] 无独立 custody 时 G6 记 `ASSURANCE_BLOCKED`，未用 local canary 冒充 PASS
- [ ] 完整 G1–G5 `product_complete = PASS`；G6 状态单列

## 终态与不变式（Task 8）
- [ ] 双读数已更新到 `rules.md` 与 `wiki/` 台账
- [ ] `rounds/round11/` 已归档
- [ ] 终态报告列出 J 空间（五个维度）、语义差分、变异、规则覆盖、G5、G6/`ASSURANCE_BLOCKED`、缺陷关闭状态
- [ ] 未把 v8 128/128 写成完备
- [ ] 无用户既有变更被回滚
- [ ] 根目录 scratch / `_scratch_m4` / `.canary-private/` 未入库
- [ ] 提交已 push 到 `origin/main`
