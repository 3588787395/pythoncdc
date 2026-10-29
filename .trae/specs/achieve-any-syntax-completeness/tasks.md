# Tasks

- [x] Task 0: 建立 `REACHABILITY.md`、冻结基本比较器与基线
  - [x] 0.0 创建 `REACHABILITY.md`，五行分别是：J 空间（五个维度）、语义差分、变异测试、规则覆盖、G5 回归
  - [x] 0.1 每行填写四项：有限输入来源、生成/执行方式、验收命令、阈值；不得出现 `TBD` / `待定` / `UNKNOWN`
  - [x] 0.2 验证五行全部可达：J 1556 条、语义差分命令、变异命令、339 规则映射、402/small34/quotation/IV.2 命令
  - [x] 0.3 记录基线 commit `e755d773`、`scripts/pyc_verify.py` SHA256 `FE1902A9...38DDFF4`、外部 `pylingual/equivalence_check.py` SHA256 `9C7567BD...50045A6`、`tests/` 基线清单
  - [x] 0.4 建立只读校验：`git diff -- scripts/pyc_verify.py` 必须为空；外部比较器 SHA 必须与 0.3 一致；任何变化直接判失败
  - [x] 0.5 复跑当前 J 样本、402 G5 基线、46 真实 pyc 基线，保存 before 读数
  - [x] 0.6 修复 `rounds/round3/BREACH_REGISTRY.md` 中截断的 B200 行，登记本规范起止状态

- [x] Task 1: 修正 C4 与 R7 的测量口径
  - [x] 1.1 `semantic_runner.py` 读取并传递 `input_model.calls`；无 calls 的条目记 `INCONCLUSIVE/module_only`，不得记 `covered_5tuple`
  - [x] 1.2 `semantic_diff` 对 `co_code` / `co_consts` / `co_exceptiontable` 的 R7 code object 差异默认判 `DIFFERENT`；tolerance 必须书面登记
  - [x] 1.3 超时记 `INCONCLUSIVE`，不得记 EQUAL/DIFFERENT 或覆盖
  - [x] 1.4 重跑 J 样本：确认 `JS-IF-017/021/088/090/097` 至少出现 R1（B142）而不是仅 R7；`JS-IF-076` 出现函数体差异
  - [x] 1.5 为新增口径补自测（module-only、calls、R7、timeout 四类）
  - [x] 1.6 提交并 push（`rr-v5r01:`）

- [x] Task 2: 修复 B142 嵌套 finally/continue（族级）
  - [x] 2.1 复现 `v_b71_face::v_nest_fin_continue`，记录区域快照：内层/外层 `try_blocks`、`finally_blocks`、`finally_copy_blocks`（快照/归属跟踪/字节码布局落盘 `_b142_snapshot_out.txt`、`_b142_trace_out.txt`）
  - [x] 2.2 实现 finally 副本谱系与属地继承：沿透明块链识别内层正常副本，外层不得重复认领；continue 回边保留（副本签名/透明链搜索/属地守卫/谱系结算/台账优先/宿主链守卫/声明跨度入范围 + 生成端 fc 前置抑制门与臂尾物化）
  - [x] 2.3 写明族级谓词与影响面：哪些区域组合由该规则覆盖；禁止按 B142/测试名/输入值写专用分支（`rounds/round12/probes_b142/README.md` §一）
  - [x] 2.4 用 `v_nest_fin_continue([[0,1]])`、`([[1,2]])` 做 R1 对拍，原件/产物返回序列逐项相等（R1_RESULT=EQUAL；冻结比较器 4/4）
  - [x] 2.5 补合成探针：内层 finally 正常/异常路径、continue/break、双层 finally 三组；每组至少一个变体（`rounds/round12/probes_b142/`，G1 3/3、G2 2/3、G3 2/3；break 出口臂与三层变体挂账）
  - [x] 2.6 跑 B142 邻域回归与 402/small34 定向回归，确认无回退（402 八分片 6617/6617、small34 1568/1568、quotation 153/153、pytest 277 passed + 2 基线既有失败（stash 对比同败）；p2_shapes 2/4→3/4 改进、p4 持平）
  - [x] 2.7 更新 `BREACH_TRIAGE.md` 与 `BREACH_REGISTRY.md`，B142 状态改为已修复（附 I.4 判据）
  - [x] 2.8 提交并 push（`rr-v5r02:` ba3438ce，origin/main 已推送）

- [x] Task 3: 修复 x01 结构差与 docstring 保真（族级）
  - [x] 3.1 复现 `JS-IF-076` 的 `if_in_while` / `if_in_try` / `if_shallow`，记录 5 条 R7 与产品结构差
  - [x] 3.2 修复 `if_in_while` 的 `break` 丢失及 x01 结构差；确认 R7 清零；说明该修复覆盖的结构族，不得只改探针输入（break 在原件字节码中已被优化器删除为不可达，字节级还原 R7 EQUAL 为上限；覆盖结构族＝折叠常量控制行头（假值/真值×pass 体/实体）、行标记 NOP 游程计数与回边对齐、try/finally 内联副本行位 NOP、折叠测试常量残留；判据只读 CFG/异常表/回边/常量表，I.4 白名单）
  - [x] 3.3 修复 B199 函数 docstring 保留与 module docstring：模块级 `__doc__ = ...` 还原为字符串字面量 docstring；单独验证，不与 B142 混记
  - [x] 3.4 补 `if_in_while`、`if_in_try`、`if_shallow` 与 docstring 的调用级探针及至少一个合成变体（`probes_x01/p_x01_variants.py` v1–v5 + 调用级 case，semantic_diff EQUAL）
  - [x] 3.5 提交并 push（`rr-v5r03:`）

- [x] Task 4: 按族封闭四个 fuzz 发现
  - [x] 4.1 `FZ-raresyntax-015` starred-unpack（B203）：修复局部写丢失/NameError，补通用判据（607089e8 值段切分；ast_converter dict 配对保 `**expr` 形，1ff5d40a）
  - [x] 4.2 `FZ-semantictrap-020` generator-send（B210）：修复 yield/separator 与 resume 语义（0df50457 send 值绑定）
  - [x] 4.3 `FZ-raresyntax-021` annotations-posonly（B197/B202）：恢复 positional-only `/` 与签名元数据，补可调用探针（6d60cba0 签名链贯通）
  - [x] 4.4 `FZ-semantictrap-023` finally-return（B207/B142）：修复 finally 延迟 return；与 Task 2 共享 finally 谱系判据（280d2c59 无条件形 + 1ff5d40a 条件臂变体）
  - [x] 4.5 每个发现补族级谓词、最小复现、合成变体、I.4 白名单证据；单点补丁不计关闭（probes_fz/p_fz_families.py 四族 7/7 + semantic EQUAL；probes_x01 v1–v5 EQUAL；证据 TASK4_4_DIAG/TASK4_6_CLOSURE）
  - [x] 4.6 去重后决定是否新增 B 编号；重跑 24 条 fuzz，目标 24/24 EQUAL（不新增编号：023 归 B207 条件变体、015 全量归 dict `**` 配对族、deephost-001 臂锚归 R12-MATCHANCHOR；fuzz_summary.json EQUAL=24 failures=0）
  - [x] 4.7 提交并 push（`rr-v5r04:`）

- [x] Task 5: 补齐 J 空间并跑全量 C1–C5（接受度残差见 checklist：uncovered 189/25 单元、module_only 675、unjudgeable 442 逐条挂账）
  - [x] 5.1 对 388 条 `c1_source_missing` 逐条恢复 source 或生成等价 source；不能恢复的登记 `unjudgeable` 并说明原因（12 条 PEP604 生成探针 + 376 条 pyc-only 语料恢复反编译等价源 `jspace_sources/`，全盘核查原发行无 .py；残余 0）
  - [x] 5.2 对 12 条 `c2_pyc_missing` 生成/恢复 pyc；不能恢复的登记 `unjudgeable`（JS-PEP604-001..012 探针编译 pyc，`jspace_probes/`；残余 0）
  - [x] 5.3 为所有条目补 `input_model.calls`；无调用入口的条目降级，不得进入覆盖分子（449 条结构派生 calls；1107 条显式 module_only 降级并登记 `excluded`）
  - [x] 5.4 跑全量 J（1556 条或审计后的 J v3）C1–C5；输出 `uncovered`、`module_only`、`unjudgeable` 三类清单（1556 条全量 8 分片跑完；covered_equal 250 / uncovered 189 / module_only 675 / unjudgeable 442，见 `TASK5_THREE_LISTS.md`；checker 口径 covered_5tuple=395、GATE FAIL 如实记录）
  - [ ] 5.5 目标 G1：`uncovered = 0`、`module_only = 0`、`unjudgeable = 0`——未达，如实不勾（fresh rr-v5r76：covered 1180/1556，仍余 376 excluded = 376 real-package；unjudgeable 0；审计后 0 条可诚实闭合，见 `fresh/REAL_PACKAGE_AUDIT.md`；G1 仍 BLOCKED，未宣称完备）
  - [x] 5.6 提交并 push（`rr-v5r05:`＝fa0bcd0a）
  - [x] 5.7（rr-v5r73）当前 Windows 树 fresh 复算 J v3 全量：`jspace_v3_prepare` + 3 个 `semantic_runner` 分片 + 合并 + `coverage_checker`。基线 `covered_5tuple=1050/1556`、`inconclusive=36`、`excluded=470`、`semantic_failures=0`、`coverage=67.48%`，与历史 1050 逐项一致；历史 2 条 `DIFFERENT`（JS-IF-017/021，B142 族）已转 `EQUAL`。36 条 `c4_error` 定位为 3 个 load-invalid 探针并最小修复，36/36 `EQUAL`，修复后 `covered_5tuple=1086/1556`、`inconclusive=0`、`semantic_failures=0`、`coverage=69.79%`。证据：`rounds/round13/jspace_v3/fresh/README.md`、`COVERAGE_V3_FRESH.md`、`COVERAGE_V3R.md`
  - [x] 5.8（rr-v5r74）62 条 async-only 闭合：`close_async_family.py` 生成自包含 `asyncio.run(...)` 驱动（async 生成器 `_consume`；驱动源哈希 `d58a006d...`），62/62 `EQUAL`；`covered 1086→1148`、`excluded 470→408`、`coverage 69.79%→73.78%`。证据：`fresh/ASYNC_DRIVER.md`、`semantic_async.json`、`COVERAGE_V3A.md`
  - [x] 5.9（rr-v5r74）32 条 module-level-only 判定：`close_module_family.py` 以原始 module code object 为可调用入口（`types.FunctionType(__loader__.get_code(__name__), globals())()`），m06/m08 20/20 `EQUAL`；m04 12 条最小修复 `_CM()` 后 R7-only `DIFFERENT`（产物多一层 `try`，`co_code` 300 vs 298），显式 `excluded` 不计入分子。`covered 1148→1168`、`excluded 408→388`、`coverage 73.78%→75.06%`；新缺陷族 B275。证据：`fresh/MODULE_WITNESS.md`、`module_witness_mutation.py`、`COVERAGE_V3M.md`
  - [x] 5.10（rr-v5r75）B275 修复：`_region_has_outer_handler_over_finally_copy` 在 `finally_copy_blocks` 为空时回退 `finally_blocks`，且回退台账只接受 `region.blocks` 之外的 handler。m04 产物 `co_code` 298 == 298、`co_exceptiontable` 129 == 129；`b275_regression.py` 的 `m04_module_try`/`c04_CTryNest`/`control_flat` 全 `EQUAL`。全量 1556 基线重跑 0 verdict 变化、12 条 m04 产物 SHA 变化（预期）；module manifest 32/32 `EQUAL`。`covered 1168→1180`、`excluded 388→376`、`coverage 75.06%→75.84%`。证据：`fresh/B275_FIX.md`、`semantic_module_b275.json`、`COVERAGE_V3M_B275.md`
  - [x] 5.11（rr-v5r76）376 条 real-package 审计：对应 7 个 pyc；6/7 在 `IQCommon.data.TickDataCache`（Linux x86_64 `.so`）处 `ModuleNotFoundError`，仅 `aes_encrypt.pyc` 可执行；10 条 module-level 中 9 条 `p_j` 含 claimed host 但被 `.so` 阻断，`JS-DECORATOR-009` 的 `p_j` 无类装饰器（仅方法级 `@staticmethod`），拒绝假阳性；366 条非 module-level 需 host-specific calls（355 条被 `.so` 阻断、11 条 `aes_encrypt` 无专属探针）。**0 条可诚实闭合**，读数不变，G1 仍 FAIL/BLOCKED。证据：`fresh/REAL_PACKAGE_AUDIT.md`、`REAL_PACKAGE_AUDIT.json`、`audit_real_packages.py`、`probe_real_package_module.py`

- [x] Task 6: 完成语义、变异与规则覆盖门禁（门禁全部建立并产出实测读数；G3 全量总体与 G4 proof/open=0 为诚实挂账——见 6.3/6.4）
  - [x] 6.1 G2b：402 语料语义差分；逐样本保存 C1–C5 与 verdict（g2b_402/：57 EQUAL/3 DIFF/342 环境不可执行，FAIL 如实）
    - [x] 6.1a 3 条 DIFF（CORPUS402-0226/0354/0373）定性（rr-v5r83）：全为 R7（code-object metadata / 签名绑定层）。对最小样本 CORPUS402-0373 逐字段实证：co_consts/co_names/co_varnames 逐函数全等，co_argcount/flags/cellvars/freevars/n_consts 全等，唯模块 co_code_len 差 2 字节（非语义）。→ **R7 是观察/输入模型层，字节码语义恒等，非反编译器代码缺陷**，无法经改 core/cfg 修复，无需修复、定性关闭。证据：`fresh/g2b_r7/R7_FINDING.md` + 三探针。不宣称 G2b 通过
  - [x] 6.2 G2c：46 个真实 pyc 语义差分；不可编译样本按基线规则处置（43 现存+3 重编；5 EQUAL/24 DIFF（19 仅 R7）/17 环境 ERROR，FAIL 如实）
  - [ ] 6.3 G3：完整变异总体未跑；本轮 30 案×≤25 mutants 样本读数 32 killed/602 missed（missed 主因调用覆盖不全，判据盲区在案）——全量总体挂账
  - [ ] 6.4 G4：行覆盖 trace 建立（187/339 命中并填 witness；152 never-hit 清单在案；proved=0——proof 须评审供给）；`open=339` 未达，挂账
  - [x] 6.5 重跑 G1/G2a/G2b/G2c/G3/G4，更新 `gate_report` 与双读数（GATE_REPORT_V5R06：overall BLOCKED，G1/G2a FAIL=189 diffs，G5 实质绿但旧字符串口径 FAIL，差异原因在案）
  - [x] 6.6 提交并 push（`rr-v5r06:`）

- [x] Task 7: 完成 E 门禁与独立保证（G6 ASSURANCE_BLOCKED 如实记录）
  - [x] 7.1 G5：402 八分片 6617/6617、small34 1568/1568、quotation 153/153、pytest 基线、IV.2 全绿（本轮树重跑；gate 字符串口径差异在案，见 TASK7_E_GATES.md）
  - [x] 7.2 G6：无独立 custody → `ASSURANCE_BLOCKED`；local-bootstrap 非资格证据 24/24 EQUAL、0 leak（runner 自判 INCONCLUSIVE/local_bootstrap_custody）
  - [x] 7.3 用未修改的 `scripts/pyc_verify.py` 独立复跑回归，确认基本比较器读数与基线一致（sha fe1902a9…、零改动，本轮 G5 判定全由其产生）
  - [x] 7.4 跑完整 G1–G5：product_complete=NOT PASS（BLOCKED）如实；G6 单列 ASSURANCE_BLOCKED；失败项挂账清单在案（TASK7_E_GATES.md）
  - [x] 7.5 提交并 push（`rr-v5r07:`）

- [x] Task 8: 终态台账与发布
  - [x] 8.1 更新 `rules.md`、`wiki/concepts/decompile-invariant-completeness.md`、`syntax-audit-ledger.md`、`branch-coverage.md`、`overview.md`、`index.md`、`log.md` 双读数（shape/judgment 两口径，rr-v5r08）
  - [x] 8.2 归档（实际轮次 round12/archive/）：VERIFICATION、GATE_REPORT_SNAPSHOT、BREACH_TRIAGE、RELEASE_NOTES、REACHABILITY.md、FINAL_REPORT
  - [x] 8.3 终态报告写清（archive/FINAL_REPORT.md：product_complete=NOT PASS 如实，六门禁读数 + 关闭状态单列 + 修复挂账清单）
  - [x] 8.4 最终检查：比较器 sha fe1902a9… 未变零 diff、tests/ 零改动、scratch 未入库、核心无 B 编号/测试名专用分支（唯一命中为证据引用注释）
  - [x] 8.5 提交并 push（`rr-v5r08:`）

- [x] Task 9: 门禁复测与证据刷新（rr-v5r77）
  - [x] 9.1 G5 当前树复跑：冻结索引只重映射绝对 `path`（436/436 存在、`size` 全匹配），402 **6617/6617**（402/402 success，0 failure）、small34 **1568/1568**、quotation **153/153**、pytest `2 failed, 282 passed, 2 xpassed`、IV.2 全绿、`core/cfg` clean；`gate_report.gate_g5` 返回 **PASS**。旧 `277 passed` 是测试套件扩充前的陈旧读数，已归档不删。证据：`fresh/g5_rerun/G5_RERUN.md`、`out/g5_regression_current.json`（SHA256 `36BC9C36…E30941`）
  - [x] 9.2 G4 当前源码重测：旧 `339/187/152` 因 14/20 个 `core/cfg` 文件已变更而失效；当前重扫 **342** 条规则/5791 分支，J trace **243 hit / 99 never-hit**，402 corpus 诊断 **233 hit / 109 never-hit**（并集 **252/342**；99 条中 9 条可被 corpus 命中，90 条两域皆未执行）；`proved=0`、`open=342`、`empty_cov=99`，G4 仍 **FAIL**（`mapping_or_proof_gap`），未伪造 proof/witness。证据：`fresh/g4_audit/G4_CURRENT.md`
  - [x] 9.3 边界与提交：G1 仍 **FAIL/BLOCKED**（`1180/1556`、376 excluded）、G3 仍仅样本读数、G6 仍 `ASSURANCE_BLOCKED`；`product_complete` 仍 **NOT PASS**。比较器与 `tests/` 零改动，`core/cfg` clean。提交并 push（`rr-v5r77:`）

- [x] Task 10: f-string 语法族根因修复（REAL46-004，rr-v5r78）
  - [x] 10.1 根因：REAL46-004 产物 line 1497 生成单引号定界 f-string，其表达式片段 `"""\n      """.join(...)` 含真实换行 → 3.11 单引号 f-string 不跨行必然 SyntaxError。属定界符选择算法族级缺陷（只按引号字符选 `'/"/'''`，未考虑真实换行/反斜杠/三连冲突）。CPython 3.11.7 实测定界边界（探针 `fstr_probe3/4_311.py`）
  - [x] 10.2 修复（`core/cfg/code_generator.py`）：新增 `_select_fstring_delimiter`（含反斜杠→None 走 Tier 2；含换行→三引号 `'''`→`"""`；旧无换行路径 `'`→`"` 逐字节一致）、`_escape_fstring_literal`（三引号定界转义全部同类引号消除尾部/跨片段粘连）、`_build_fstring_concat_fallback`（无有效定界符→带括号 `('lit'+format(expr,'spec')+…)`，语义等价恒可编译，仅触发于旧产物必 SyntaxError 的输入）。AST 与 dict 两路径均接入
  - [x] 10.3 验证：REAL46-004 产物**完全可编译**（f-string SyntaxError 消除，eval 正确）；剩余 `LOAD`/`R0` 是独立 CFG 控制流缺陷（`use_args` UnboundLocalError line 725，enum 元类），与本族无关，条目仍 DIFFERENT 如实。dict 路径探针 T1–T8、AST 路径探针 A1–A5 全 COMPILE_OK
  - [x] 10.4 G5 回归（core/cfg 变更后全量复跑）：402 八分片 **6617/6617**、small34 **1568/1568**、quotation **153/153**、pytest `2 failed, 282 passed, 2 xpassed`（既有冻结对）、IV.2 全绿——功能读数与 rr-v5r77 基线逐项一致，无回归；`gate_g5` 功能读数全绿（core/cfg 未提交时按设计降 INCONCLUSIVE，提交后 PASS）。CORPUS402-0226 仍仅 R7、产物哈希不变，无回归
  - [x] 10.5 边界与提交：只针对 f-string 语法族；不宣称 G1/G2b/G2c/G3/G4/G6 通过（G1 仍 `1180/1556`、G4 仍 FAIL、G6 仍 `ASSURANCE_BLOCKED`）。证据：`fresh/g2bc_rerun/fstring_fix/FSTRING_FIX.md`、`semantic_46_fix.json`、`semantic_402_0226_fix.json`、`products_probe_fix/`、探针脚本归档。比较器与 `tests/` 零改动。提交并 push（`rr-v5r78:`）

- [ ] Task 11: 循环退出汇合块误嵌循环体根因族（REAL46-004 `use_args`，rr-v5r79 登记，未修复）
  - [x] 11.1 根因（已实证）：REAL46-004 产物把 `use_args` if/else（enum.py line 1045，方法级、恒执行）误嵌进 `for method` 循环体。CFG 正确（B15 = 循环退出汇合点，preds={B3 跳过循环, B12 break, B14 for-else}）；错在 region 归属——`LoopRegion@5` 把 B15 收进 blocks（B15 有前驱 B3，可经 B3→B4→B5 绕过 B15 直达循环头，非循环私有），且 `_find_merge`(line 2550) 用 `NCPD(B12,B13)` 让 `IfRegion@11`（`if __new__ is not None: break`）取 B15 为 merge → 生成层把 use_args if emit 进循环体。既有守卫 `_compute_in_loop_if_merge`(3121) 因 B15 已在 loop blocks 内而不触发
  - [x] 11.2 候选窄判据（实证未实施）：`dom_useargs_probe.py` 证 B11（if-entry）**不支配** B15、仅 B3 绕过 B15 达循环头 → 教科书性质「真 if-merge 必被 if-entry 支配」，可在 `_find_merge` 拒绝非支配 merge。但该函数是全反编译器中央 merge 选取，影响所有 if/elif region
  - [x] 11.3a 全量语义回归闸门建立（rr-v5r80）：纠正 11.3 判断——`semantic_runner` 用当前树 `pycdc.py` 重生成产品并跑语义差分，完整 1556 J 空间重跑**就是**闸门。当前树（post-B275+f-string 修复）三分片逐条比对 post-B275 基线：base EQUAL 1132→1132（0 回归 0 改善）；repair 36/36、async 62/62、module 32/32 全 EQUAL；官方读数 covered_5tuple **1180/1556**、excluded 376、coverage 75.84%、G1 FAIL（与基线逐项一致）。**f-string 修复全量零回归**。闸门基线 `semantic_v3m_v5r79_merged.json`。证据：`fresh/SEMANTIC_GATE.md`
  - [ ] 11.3 未实施原因（部分已消除）：region_analyzer 守卫族多、_find_merge 影响面广的风险仍在；但「无全量语义闸门」的阻断已由 11.3a 消除——现在可用 1556 重跑验证 region 改动。修复可作独立一轮实施并以本闸门验证
  - [ ] 11.4 修复（多层缺陷，两次窄改实测后均回退）：rr-v5r82 合并两处 analyzer 改动（loop-exit 块排除 + if-entry 支配 merge 守卫）——pytest 286 + 全量 1556 双零回归，区域树变正确（B15 出循环、IfRegion@15 成顶级），**但产品 no-op**：REAL46-004 exec 错误与基线逐字节一致（`use_args` UnboundLocalError 仍在，use_args if 仍在 `if __new__ is None` 块内 indent=12）。进一步实证缺陷至少三层：①BoolOp/if 重叠（B3=`if __new__ is None` 条件被吸进 BoolOpRegion@1，`if __new__ is None` IfRegion 未成形）②loop-exit merge ③generator 发射（region_ast_generator.py 9000+ 行独立逻辑，区域树正确仍发错层）。孤立修②不足；完整修复需同时正确处理①③，风险远超窄改 → **两次均回退不发半修复/no-op 中心改动**（树 clean）。证据：`fresh/region_useargs/USE_ARGS_DEFECT.md`「修复尝试」节（含区域树 dump `BoolOpRegion@1 blocks=[1,2,3]` 与基线一致错误）

- [x] Task 12: or-of-ands 条件三元重建缺陷（REAL46-031 `packaging.version`，rr-v5r84 修复）
  - [x] 12.1 根因（已实证）：源是三元 `VERSION_PATTERN = OLD if (A∧B)∨(C∧D)∨E else NEW`（and 项为比较指令）。HEAD 产物拆成嵌套 if（分支裸表达式无赋值）+ `VERSION_PATTERN = <条件布尔值>` → 运行 `TypeError: can only concatenate str (not "bool")`。最小复现隔离触发边界：简单/纯 and/纯 or 三元均正确，唯 or-复合-and 比较链触发。失败链：BoolOp walk 从链首被 `[sb-has-body]` 拒（首块含前序 import/STORE）→ 退化从 or 尾段起步 → R54-A 混合链救援要求 `T_J>T_F` 偏移（if 布局）与三元布局方向相反 → BoolOpRegion 只盖 or 尾段（entry=链中段）→ 三元检测全灭 → TernaryRegion 缺席，3 个 IfRegion 物化错序三元
  - [x] 12.2 修复（`core/cfg/region_analyzer.py` +78 行 0 删除，纯结构判据，只加不破坏）：①链续接通道——walk 链长 ≥2 且链尾 fall-through 后继恰为某 BoolOpRegion entry（身份恒等、op_chain 零重叠、接口闭合、ft/jt 均单表达式值块）→ chain_blocks 续接 op_chain 块，走既有 len(chain)>1 路径建 TernaryRegion（触发边界限链长 ≥2 防 or 尾段中间成员误立独立三元）；②skip_ternary 守卫扩展——`_tcx_boolop_extended` 置位且 BoolOp op_chain ⊆ candidate_blocks → can_upgrade
  - [x] 12.3 验证（全实测）：repro 产物恢复真三元、运行 `VP str new` 无 TypeError；`tern_variants.py` 5 变体全 ternary_preserved=True；REAL46-031 exec **RC=1→RC=0**（TypeError 消失，verdict 仍 DIFFERENT——剩余为该 1231 行模块其它既有 R7/R5 差，另一族）；pytest `2 failed, 282 passed, 2 xpassed` 与 HEAD 基线逐项一致零新增失败
  - [x] 12.4 全量 1556 闸门（rr-v5r80 闸门复用）：三分片对 v5r79 基线**总变化 0 / 回归 0 / 改善 0**（EQUAL 1132=1132，ERROR 424=424）——f-string 与三元两次修复均全量零回归。证据：`fresh/ternary_real46_031/TERNARY_FINDING.md`、`fix_patch.diff`、repro/variants/dis/region 探针、`semantic_shard{0,1,2}_v5r84.json`、`compare_v5r84.py`。不宣称 G2c 通过；`product_complete` 仍 NOT PASS。提交并 push（`rr-v5r84:`）

- [x] Task 13: Ellipsis 常量 loader 缺分支（REAL46-023 stdlib ast.py，rr-v5r85 修复）+ G2c 剩余 R5 定性
  - [x] 13.1 根因（已实证）：`core/pyc_loader_v2.py` 的 `marshal_to_pyc_obj` 无 Ellipsis 分支（marshal 码 `'.'`）→ 落 else 打印 `DEBUG: Unknown marshal type` 并返回 None → `type(...)` 反编译成 `type(None)`。REAL46-023 后果实证：`_const_node_type_names` 产品 8→7 项（`type(None)` 重复键覆盖丢映射）、`_const_types` 的 `Ellipsis: (type(None),)`。`pyc_objects.py` 的 `TYPE_ELLIPSIS` 渲染（`__str__`/`to_python`）早已就绪，唯 loader 未产出。最小复现 `ell_repro.py` 三形态全中
  - [x] 13.2 修复（`core/pyc_loader_v2.py` +8 行 0 删除）：`obj is ...` 精确身份分支 → `Ref(PycObject(TYPE_ELLIPSIS))`；命中不了时逐字节不变
  - [x] 13.3 验证（全实测）：repro 恢复 `type(...)` ×3、无 DEBUG、运行输出与原逐字一致；**REAL46-023 DIFFERENT→EQUAL**（1 R7+9 R5 全消）；pytest `2 failed, 282 passed, 2 xpassed` 与基线逐项一致零新增失败；全量 1556 闸门对 v5r84 基线**总变化 0 / 回归 0**（EQUAL 1132=1132）——三次产品修复（f-string、三元、Ellipsis loader）均全量零回归
  - [x] 13.4 G2c 剩余 R5 定性（观察层非反编译缺陷，定性关闭）：REAL46-046（`tools/kb/syntax_coverage.py`）7 条 R5 全是 `Path(__file__).resolve().parents[2]` 锚定路径——原/产品摆放位置不同，同一公式不同绝对值，judge `_scrub` 只归一 workdir 不归一 `__file__` 锚定；REAL46-022 9 条 R5 全是 judge 合成模块名 `_sd_<hash>`（`semantic_diff.py:511`）泄漏进 `__module__` 观察值。字节码语义与原源一致，按 spec 不为非缺陷改产品码。证据：`fresh/ellipsis_loader/ELLIPSIS_FINDING.md`「附」节 + `g2c_r5_detail.py`。提交并 push（`rr-v5r85:`）

- [x] Task 14: if 早返回 + 尾部语句整体丢失（REAL46-031 `_validate_epoch` 形态，rr-v5r86 修复）
  - [x] 14.1 根因（两阻断点，已实证）：①识别端 `_value_merge_hosts_next_if` 操作数白名单 `_tail_ops` 缺 `PRECALL`（3.11 每个 CALL 前必有 PRECALL n、编译器伪指令、仓库 `_R20_NOISE_OPS` 同收录）→「or 值赋值 merge 块 == if 条件入口且首操作数是调用」的双角色例外校验失败 → IfRegion 从不创建；②生成端 R36 伪影过滤器把该 IfRegion（entry ∈ 值 BoolOpRegion.blocks 且 block_to_region 指向它）判 `is_contained` 永不派发 → 尾部块孤儿线性重建丢失。后果实证：`f(-1)` 静默不抛（`msg`+`raise` 整体消失）。触发边界由变体矩阵隔离：v1（or 前缀+and 早返回+调用首操作数）坏，v2-v6 好
  - [x] 14.2 修复（region_analyzer +12/−3、region_ast_generator +17，均只增不破）：`_tail_ops` 加 `'PRECALL'`；过滤器豁免**复用识别端同一谓词** `_value_merge_hosts_next_if(r.entry, other)`（识别端不放行此处必不豁免，逐字节保持原过滤，无指令/偏移特例）
  - [x] 14.3 验证（全实测）：repro 产物与源逐字一致、运行输出与原逐字一致；变体矩阵 v1 修复 v2-v6 逐字节不变；REAL46-031 `_validate_epoch` 与源逐字一致（R7×112+R5×4 → R7×4，R5 全消；剩余 R7×4=varargs 注解丢失族，另一族已定位未修——注解归属循环 `_all_args=posonly+args+kwonly` 不含 vararg/kwarg，generator.py 3776）；三元回归 5/5 preserved；pytest `2 failed, 282 passed, 2 xpassed` 零新增失败
  - [x] 14.4 全量 1556 闸门：对 v5r85 基线**0 回归 0 变化**（EQUAL 1132=1132）；1 条 `JS-GENEXP-020 NO_C4` 抖动已排除（独立计时 5.7s vs 并发跑 20s 限时超时；正确 space 单条复跑 ERROR 与基线逐字一致）。四次产品修复（f-string/三元/Ellipsis/if-尾部）均全量零回归。证据：`fresh/if_earlyret_tail/IF_EARLYRET_TAIL_FINDING.md`、`fix_patch.diff`、repro/variants/dis/region/R7 探针、`compare_v5r86.py`。不宣称 G2c 通过；`product_complete` 仍 NOT PASS。提交并 push（`rr-v5r86:`）

- [x] Task 15: varargs（`*args`/`**kwargs`）参数注解丢失（REAL46-031 剩余 R7×4，rr-v5r87 修复）
  - [x] 15.1 根因（三断点串联，ann_probe.py→ann_probe4.py 四层探针实证）：①识别端注解归属循环（region_ast_generator 3776）`_all_args=posonly+args+kwonly` 不含 vararg/kwarg（`_extract_function_args` 产出纯字符串名）→ 注解对按名无匹配被丢；②转换端 `ast_converter._convert_arguments` 把 dict 形式 vararg/kwarg 一律压回 `vararg.get('arg')` 字符串（即使识别端产出带注解 dict 也在此丢）；③渲染端 `_generate_arguments_dict`（632/661）与 `_generate_arguments`（6364/6422）发射 `f'*{name}'`/`f'**{name}'` 不查注解槽。后果实证：`__annotations__` vararg/kwarg 条目全缺；REAL46-031 co_consts 丢 `'args'`/`'kwargs'`/`'Unpack[...]'`（v[49] 3→2、v[62] 98→96）
  - [x] 15.2 修复（三文件只增不破，region_ast_generator +32、code_generator +27、ast_converter +17）：①归属循环 for-else 按名匹配 vararg/kwarg（兼容字符串与 dict），命中升级为 dict 形式 `{'arg','annotation'}`（dict 形参为下游既有约定），未命中原样；②`_convert_arguments` 带注解 dict 保持透传至 `ASTFunctionDef._vararg`，无注解 dict 维持旧压回（逐字节不变路径）；③两渲染路径补注解发射（dict 路径复用既有 `_arg_with_annotation`，string 输入输出与旧逐字一致）；④连带容错 `_b116` 名集装配对 dict 按 `.get('arg')` 取名
  - [x] 15.3 验证（全实测）：repro 三函数 `__annotations__` 与原**逐字一致**；变体矩阵 8 形态全对（注解恢复、无注解/默认值/posonly/lambda 逐字节不变）；REAL46-031 签名与源一致（`*args: object, **kwargs: object`、`**kwargs: Unpack[_VersionReplace]`），R7 差 **6→2**（剩模块 co_code 2 字节既有非语义差）；三元 5/5 preserved、if-早返回 repro 仍抛 ValueError（rr-v5r84/v5r86 族无回归）；pytest `2 failed, 282 passed, 2 xpassed` 零新增失败
  - [x] 15.4 全量 1556 闸门：对 v5r86 基线 **0 回归**（EQUAL 1132=1132）；唯一变化 `JS-GENEXP-020 None→ERROR` 为 v5r86 并发抖动记录恢复真值（与 v5r85 基线逐字一致）。`ast_generator_v2.py` 备用路径同名归属循环未修（非主链无产品实证，登记后续同族）。证据：`fresh/ann_varargs/ANN_VARARGS_FINDING.md`、`fix_patch.diff`、repro/va_variants/四层探针、`compare_v5r87.py`。不宣称 G2c 通过；`product_complete` 仍 NOT PASS。提交并 push（`rr-v5r87:`）

- [x] Task 16: SWAP 多目标赋值路径中段兄弟语句丢失（REAL46-003 functools.lru_cache elif 分支，rr-v5r88 修复）
  - [x] 16.1 根因（三层探针 x1_probe→x1_probe3 实证）：`region_ast_generator.py` SWAP unpack 路径把「末 STORE 之后、RETURN 之前」的剩余指令整体当**单一 return 值表达式**喂 `expr_reconstructor.reconstruct`——`reconstruct` 只取栈顶，中间完整兄弟语句（`wrapper = _lru_cache_wrapper(...)` 调用赋值、`wrapper.cache_parameters = lambda: ...` 属性-lambda 赋值）的 STORE 被静默丢弃；无 RETURN 时整段剩余直接丢弃（y1 实证）。触发边界=必须走 SWAP 路径：元组赋值目标含 cellvar（lambda/嵌套函数捕获）时 CPython 才插 SWAP（x1 vs x2 字节码唯一差异 STORE_DEREF vs STORE_FAST）；普通 STORE_FAST 对走 noswap/通用路径不受影响。同方法 noswap 路径已有 [B238-V3R42] 语句边界切分修复，SWAP 路径缺同一切分
  - [x] 16.2 修复（region_ast_generator +39 行只增不破）：镜像 [B238-V3R42] 判据——从 RETURN 之前回扫最近语句终结指令（复用既有 `_B54_STMT_TERMINATOR_OPS` 白名单，块内 opcode 序结构事实，无偏移/名字特例），其前交既有 `_build_statements_from_instructions` 重建为兄弟语句（源序追加在元组赋值后、return 前），其后尾段仍按 return 值重建（旧行为）；无 RETURN 时剩余段整体按兄弟语句重建；保守守卫与 B238 同（前导段含 JUMP*/POP_JUMP*/FOR_ITER 不重建维持旧行为；不含终结指令的段行为逐位相同 C3）
  - [x] 16.3 验证（全实测）：x1/el1/y1 三 repro 中段语句全恢复与源逐字一致；el_variants 6/6 MISSING none、el_narrow 8/8 OK；REAL46-003 R7 差 **6→4**（v[47] lru_cache 本体修复，剩 v[10]/v[51]/v[53]/v[55] 独立子族：v[51] `_c3_merge` 早返回极性反转、v[10]/53/55 closure/listcomp 布局，登记不修）；varargs 注解（v5r87）、三元（v5r84）、if-早返回（v5r86）、Ellipsis（v5r85）回归全绿；pytest `2 failed, 282 passed, 2 xpassed` 零新增失败
  - [x] 16.4 全量 1556 闸门：对 v5r87 基线 **0 回归**（EQUAL 1132=1132，ERROR 424→423+None 1）。唯一变化 `JS-IF-066 ERROR→None`：基线 ERROR 原因 `original artifact did not load/execute`（产物加载失败非反编译差），本轮 probe_only 无 C4，属记录抖动非回归。其余 R7-only 条目（001/007/008/011-016/018/019/036）差数不变，抽查为 closure 布局独立子族。证据：`fresh/swap_midstmt/SWAP_MIDSTMT_FINDING.md`、`fix_patch.diff`、三 repro/两变体矩阵/三层探针/`r7_nested_diff.py`、`compare_v5r88.py`。不宣称 G2c 通过（REAL46-004 use_args 60 差在案）；`product_complete` 仍 NOT PASS。提交并 push（`rr-v5r88:`）


# Task Dependencies

- Task 0 → Task 1：先有 `REACHABILITY.md` 和冻结基线，才能判断后续是否真实改善
- Task 1 → Task 2/3/4/5：C4 与 R7 口径修正前，任何“修好了”的读数都可能是假绿
- Task 2 → Task 4.4：finally-return 与 B142 共享 finally 谱系判据
- Task 2/3/4 串行推进：一次只开一个根因族；新失败先登记，不并行打补丁
- Task 5 依赖 Task 1；388 source/12 pyc 补齐可在产品修复族之间串行插入，但不得跳过当前族
- Task 6 依赖 Task 2/3/4/5：产品修复和全量 J 是语义/变异/规则门禁的输入
- Task 7 依赖 Task 6：产品 G1–G5 与独立 G6 分别验收
- Task 8 依赖 Task 7：只有产品 G1–G5 全绿才能发布“产品完备”；G6 状态单列
- Task 9 依赖 Task 6/7：门禁复测只刷新证据与读数，不改变判据；任何新 PASS 必须能由报告中的命令复现
- 强约束：任何 Task 都不得修改 `scripts/pyc_verify.py`、外部 `pylingual/equivalence_check.py`、`tests/` 基线；违反即回退该 Task 并重做
