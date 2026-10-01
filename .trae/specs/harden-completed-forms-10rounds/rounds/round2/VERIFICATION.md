# Round 2 主代理验证读数（VERIFICATION）

验证人：主代理（唯一判据 = `scripts/pyc_verify.py`；402 全量 = 8 分片重生成 OK.py + batch + compare，全部命令 ≤300s）

## 全量 402（当前树 vs 基线 a9ac63e3）

| 指标 | 基线 | Round 1 结束 | **Round 2 结束** |
|---|---|---|---|
| 单元级 success | 6546/6617（98.93%） | 6554（99.05%） | **6554/6617（99.05%）** |
| 文件级 success | 368/402 | 369 | **369/402** |
| Movement Matrix | — | REGRESSIONS=0 | **REGRESSIONS=0（8/8 片，文件级+单元级双查）** |
| 反编译/编译错误 | 0/0 | 0/0 | 0/0 |

单元级差异 vs 基线（仅改善）：jq_trans_module 63→65、trade_live_broker 115→118、quote 81→84。Round 2 的 B8/B9 修复在真身语料零新增增益/零回退（except* 语料不在 402 真身内，增益体现在合成对抗面）。

## 轮门禁判定

- **≥1 破口封闭：达成**——B8 封闭（except* 首 handler 类型表达式丢弃退化 Exception；4 复现 + rv2_01/02/03 新变体全 MATCH；台账 TryStar「完备」判定降格为「浅层完备」，复审定于 wiki 复审六步）；R2-O2 异常类型名白名单结构性移除
- **≥1 pyc 读数改善：达成**（存量 +8 保持；合成对抗面：r2_08 3/3、rv2_02 1/3→3/3、rv2_05 1/2→2/2 等改善 5 处）
- **无回退：达成**（402 全量、quotation 152/153、tests 零新增失败、哨兵 13/13）

## quotation.pyc / tests/

- `site-packages/fly/data/quotation.pyc`：152/153（99.35%），唯一失败 change_his_to_forward 基线既有，零新增
- tests/：test_algorithm_correctness 19+1（基线既有）、test_deep_nesting_pressure 14+1（基线既有）、test_complete_syntax_coverage 80 passed、test_control_flow_completeness_matrix 94 passed、test_ternary_combinations 27+3xpassed、test_boundary_cases 22+1（基线既有）——**零新增失败**（3 失败 = Round 1 已确证的基线既有）

## 本轮登记（交台账/后续轮）

- B8 已封闭（评审复核放行）；B9 装配层封闭、消费层四单元残留登记（r2_09.g/r2_10.f_while/f_ternary/r2_17.f）
- R2-NEW-1：except* 元组类型首 handler 后第二 handler 丢失（基线既有，rv2_01/04 证得）
- R2-NEW-2：B9 豁免未覆盖 WithRegion 属主（潜在扩展面）
- 基线既有独立缺陷立项：r2_04（幻影 else-try）、r2_06（try 体 continue 丢失，R76-D 族）、r2_14（finally 吞异常 break 丢失）、r2_07（match 模式降级，归 Round 4）
- DBG_OR env 钩子清理项（Round 67 基线既有，18 处）；D-1/D-2 docstring 瑕疵
- B7 维持登记（rv_03/05/09 各 1/2 持平）

## 产物

评审 `REVIEW.md`/`REVIEW2.md`；修复 `FIX.md`；复现 `test_repros/round2/`（r2_* 20 文件 + rv2_* 6 文件）；分片新报告复用 `rounds/round1/shard0..7_report_new.json`（本轮重跑覆盖）
