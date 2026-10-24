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
- [ ] `JS-IF-076` 的 `if_in_while` 中 `break` 保留
- [ ] `if_in_while` / `if_in_try` / `if_shallow` 的 5 条 R7 清零
- [ ] B199 函数 docstring 保留，module docstring 恢复为字符串字面量，`__doc__` 值一致
- [ ] docstring 修复单独验证，未与 B142 混记
- [ ] 四类调用级探针通过
- [ ] B200 台账截断已修复，编号/字段完整

## fuzz 封闭（Task 4）
- [ ] `FZ-raresyntax-015` starred-unpack 已修复并有通用判据
- [ ] `FZ-semantictrap-020` generator-send 已修复并有通用判据
- [ ] `FZ-raresyntax-021` annotations-posonly 已修复并有通用判据
- [ ] `FZ-semantictrap-023` finally-return 已修复并有通用判据
- [ ] 四个发现均有最小复现、合成变体、I.4 白名单证据
- [ ] 去重后 B 编号/登记正确，未把“已去重”写成“已封闭”
- [ ] 24 条 fuzz 达到 24/24 EQUAL

## J 空间（Task 5）
- [ ] 388 条缺 source 已恢复/生成或登记 `unjudgeable`
- [ ] 12 条缺 pyc 已恢复/生成或登记 `unjudgeable`
- [ ] 所有条目有 `input_model.calls`
- [ ] 全量 J（1556 或 J v3）C1–C5 已跑完
- [ ] `uncovered = 0`
- [ ] `module_only = 0`
- [ ] `unjudgeable = 0`；不为 0 时逐条挂账且不宣称完备

## 门禁（Task 6–7）
- [ ] G2b 402 语料语义差分完成并留逐样本证据
- [ ] G2c 46 个真实 pyc 语义差分完成
- [ ] G3 变异测试完成，漏检 = 0
- [ ] G4 339 条规则 witness/trace 完成，`open = 0`
- [ ] G1/G2a/G2b/G2c/G3/G4 复跑并更新 gate_report
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
