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
  - [ ] 5.5 目标 G1：`uncovered = 0`、`module_only = 0`、`unjudgeable = 0`（若不为 0，必须逐条挂账且不得宣称完备）
  - [ ] 5.6 提交并 push（`rr-v5r05:`）

- [ ] Task 6: 完成语义、变异与规则覆盖门禁
  - [x] 6.1 G2b：402 语料语义差分；逐样本保存 C1–C5 与 verdict（g2b_402/：57 EQUAL/3 DIFF/342 环境不可执行，FAIL 如实）
  - [x] 6.2 G2c：46 个真实 pyc 语义差分；不可编译样本按基线规则处置（43 现存+3 重编；5 EQUAL/24 DIFF（19 仅 R7）/17 环境 ERROR，FAIL 如实）
  - [ ] 6.3 G3：完整变异总体未跑；本轮 30 案×≤25 mutants 样本读数 32 killed/602 missed（missed 主因调用覆盖不全，判据盲区在案）——全量总体挂账
  - [ ] 6.4 G4：行覆盖 trace 建立（187/339 命中并填 witness；152 never-hit 清单在案；proved=0——proof 须评审供给）；`open=339` 未达，挂账
  - [x] 6.5 重跑 G1/G2a/G2b/G2c/G3/G4，更新 `gate_report` 与双读数（GATE_REPORT_V5R06：overall BLOCKED，G1/G2a FAIL=189 diffs，G5 实质绿但旧字符串口径 FAIL，差异原因在案）
  - [x] 6.6 提交并 push（`rr-v5r06:`）

- [ ] Task 7: 完成 E 门禁与独立保证
  - [ ] 7.1 G5：402 八分片 6617/6617、small34 1568/1568、quotation 153/153、pytest 基线、IV.2 全绿（本轮树重跑）
  - [ ] 7.2 G6：尝试独立 custody 的 24 条 canary 24/24 EQUAL、0 leak、季度轮换记录；无独立 custody 则记 `ASSURANCE_BLOCKED`，不得记 PASS
  - [ ] 7.3 用未修改的 `scripts/pyc_verify.py` 独立复跑回归，确认基本比较器读数与基线一致
  - [ ] 7.4 跑完整 G1–G5，目标 `product_complete = PASS`；单独报告 G6 状态；任一失败进入修复任务，不得改比较器
  - [ ] 7.5 提交并 push（`rr-v5r07:`）

- [ ] Task 8: 终态台账与发布
  - [ ] 8.1 更新 `rules.md`、`wiki/concepts/decompile-invariant-completeness.md`、`syntax-audit-ledger.md`、`branch-coverage.md`、`overview.md`、`index.md`、`log.md` 双读数
  - [ ] 8.2 归档 `rounds/round11/`：VERIFICATION、GATE_REPORT、BREACH_TRIAGE、RELEASE_NOTES、REACHABILITY.md
  - [ ] 8.3 终态报告写清：J 空间（五个维度）、语义差分、变异、规则覆盖、G5、G6/`ASSURANCE_BLOCKED`、B142/JS-IF-076/fuzz 关闭状态
  - [ ] 8.4 最终检查：基本比较器 SHA 未变、tests 零改动、用户变更未回滚、scratch 未入库；无 B 编号/测试名专用分支
  - [ ] 8.5 提交并 push（`rr-v5r08:`）

# Task Dependencies

- Task 0 → Task 1：先有 `REACHABILITY.md` 和冻结基线，才能判断后续是否真实改善
- Task 1 → Task 2/3/4/5：C4 与 R7 口径修正前，任何“修好了”的读数都可能是假绿
- Task 2 → Task 4.4：finally-return 与 B142 共享 finally 谱系判据
- Task 2/3/4 串行推进：一次只开一个根因族；新失败先登记，不并行打补丁
- Task 5 依赖 Task 1；388 source/12 pyc 补齐可在产品修复族之间串行插入，但不得跳过当前族
- Task 6 依赖 Task 2/3/4/5：产品修复和全量 J 是语义/变异/规则门禁的输入
- Task 7 依赖 Task 6：产品 G1–G5 与独立 G6 分别验收
- Task 8 依赖 Task 7：只有产品 G1–G5 全绿才能发布“产品完备”；G6 状态单列
- 强约束：任何 Task 都不得修改 `scripts/pyc_verify.py`、外部 `pylingual/equivalence_check.py`、`tests/` 基线；违反即回退该 Task 并重做
