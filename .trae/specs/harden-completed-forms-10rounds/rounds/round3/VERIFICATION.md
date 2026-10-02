# Round 3 主代理验证读数（VERIFICATION）

验证人：主代理（唯一判据 = `scripts/pyc_verify.py`；402 全量 = 8 分片重生成 OK.py + batch + compare，全部命令 ≤300s；验证驱动复用 round1 `verify_driver.py` 副本落 round3 目录）

## 全量 402（当前树 b81a0046 vs 基线 a9ac63e3）

| 指标 | 基线 | Round 2 结束 | **Round 3 结束** |
|---|---|---|---|
| 单元级 success | 6546/6617（98.93%） | 6554（99.05%） | **6554/6617（99.05%）** |
| 文件级 success | 368/402 | 369 | **369/402** |
| Movement Matrix | — | REGRESSIONS=0 | **REGRESSIONS=0（8/8 片，IMPROVED 合计 +1 文件级 / +8 单元级，均 Round 1 既有增益保持）** |
| 反编译/编译错误 | 0/0 | 0/0 | 0/0 |

分片明细：shard0 777/786（jq_trans_module failure→success，基线增益保持）、shard1 462/469、shard2 537/538、shard3 883/887、shard4 848/855、shard5 993/999、shard6 789/801（tlb 115→118 基线增益保持）、shard7 1265/1282——8 片全部 REGRESSIONS=0。

Round 3 修复的真身增益体现于合成对抗面（round3 全组 72/72 + r3_33 4/4），402 真身零新增增益、零回退——与 Round 2 模式一致。

## 小测试集（baseline/failing_index.json，34 pyc）

- worse = **0**（无任何 success→failure 或单元数下降位移）
- improved = 3（quote 81→84、trade_live_broker 115→118、jq_trans_module 63→65，均 Round 1 既有增益保持）
- 汇总读数：1505/1568（95.98%），报告 `rounds/round3/small34_report_new.json`

## quotation.pyc / tests/

- `site-packages/fly/data/quotation.pyc`：152/153（99.35%），唯一失败 change_his_to_forward 基线既有，零新增
- tests/（六套件同 Round 2）：`test_algorithm_correctness` 19+1、`test_deep_nesting_pressure` 14+1、`test_complete_syntax_coverage` 80 passed、`test_control_flow_completeness_matrix` 94 passed、`test_ternary_combinations` 27+3xpassed、`test_boundary_cases` 22+1 → 256 passed / 3 failed——**3 失败与 Round 1/2 确证基线既有逐一对应（同三文件各 1 失败），零新增失败**

## 轮门禁判定

- **≥1 破口封闭：达成（超额）**——B10 封闭（loop-else×break 证据链失效族，15 单元/6 文件全 MATCH）+ B11 封闭（while 混合链非名操作数装配灾难，4 单元全 MATCH；B6/B7 封闭声明降格落实）+ B1b 扩充封闭（r3_31 两单元）+ B11-R 封闭（r3_33 or 三成员组前置，4/4）
- **≥1 pyc 读数改善：达成**（合成对抗面 21+1 单元 0→MATCH；402/34 小集无回退）
- **无回退：达成**（402 八片、quotation 152/153、tests 零新增、哨兵全持平）

## 评审流程记录（对抗闭环）

1. 评审 REVIEW.md（45dd88b7）：B10/B11 登记 + B1b 扩充 + R3-O1/O2 观察点
2. 修复一批次（5f26202c）：B10 收尾 5 单元，quotation 回归自纠 1 起
3. 修复二批次（95046711）：B11 4 单元 + B1b 2 单元
4. 评审复核 REVIEW2.md：读数全绿属实，打回 3 项（R2-1 BOM 剥离、R2-2 注释/代码不一致、B11-R/B10-R 残留）
5. 打回修复（b81a0046）：R2-1 BOM 字节级恢复、R2-2 守卫面收窄对齐声明、B11-R 封闭（r3_33 4/4）、B10-R 精确登记
6. 评审复验 §6 终判：四项全通过，放行归档

## 本轮登记（交 Round 4 / 台账）

- **B10-R**（已定位待修）：内层 for-else 体纯 if-break 跳外层 → 幻影 `return acc`；机制勘误 = 经 `_if_generate_normal`（region_ast_generator.py:18370）then 臂内联共享 RETURN 块而非折叠面；折叠面已加祖先退出路径守卫（:4573-4602）零回退；最小验收组 = r3_34（1/2，b10r_innerforelse_break）
- **B11-R2**（已定位待修）：or 组 × 双 and 尾组合（or4_and2 变体）MISMATCH；FIX-B11c-3（:24761-24853）判定为「登记形态封闭」，族封闭性未证
- R3-O1（跨循环 continue 身份守卫）、R3-O2（WHILE 分支无 clamp）观察点维持
- B9 消费层四单元 / B7 / r2_04/06/14 维持登记未修
- 台账动作（交 §8.2 复审六步）：For/AsyncFor、While、Break/Continue 三形态标注「浅层/受限形态完备」；B6/B7 封闭声明降格为「单名操作数浅层封闭」

## 产物

评审 `REVIEW.md`/`REVIEW2.md`；修复 `FIX.md`/`FIX2.md`；复现 `test_repros/round3/`（r3_20..r3_34 + n3_01/n3_02 负对照）；分片报告 `rounds/round3/regen_shard0..7.json` + `shard0..7_report_new.json`；小测试集报告 `small34_report_new.json`
