# Round 9 主代理验证报告（VERIFICATION.md）

- 验证人：主代理（不执行实现任务，仅验证 + 归档）
- 日期：2026-10-04
- 树状态：HEAD = `e337fdd9`（评审批次二归档）；被验算法树 = 修复批次 `1624ef6d`（BOM 单头恢复后）
- 判据唯一：`scripts/pyc_verify.py`（batch/compare，pylingual compare_pyc，Python 3.11.7）；全部命令 ≤300s
- 驱动：`rounds/round9/verify_driver.py`（regen/verify/compare 三步，输出落 round9 目录）

## 1. 402 全量八分片重生成 + batch + compare

| 分片 | 文件 | units（基线→本轮） | 文件 success | 判定 |
|---|---|---|---|---|
| shard0 | 51 | 775/786 → **777/786**（+2） | 45 → **46**（jq_trans_module failure→success） | REGRESSIONS=0 IMPROVED=1 |
| shard1 | 51 | 462/469 → 462/469 | 48 → 48 | REGRESSIONS=0 |
| shard2 | 51 | 537/538 → 537/538 | 50 → 50 | REGRESSIONS=0 |
| shard3 | 51 | 883/887 → 883/887 | 48 → 48 | REGRESSIONS=0 |
| shard4 | 51 | 848/855 → 848/855 | 46 → 46 | REGRESSIONS=0 |
| shard5 | 51 | 993/999 → 993/999 | 46 → 46 | REGRESSIONS=0 |
| shard6 | 51 | 786/801 → **789/801**（+3） | 48 → 48 | REGRESSIONS=0 |
| shard7 | 45 | 1262/1282 → **1265/1282**（+3） | 37 → 37 | REGRESSIONS=0 |
| **合计** | **402** | **6546/6617 → 6554/6617（99.05%，+8）** | **369/402** | **REGRESSIONS=0** |

- regen 402/402 成功零失败（regen_shard0..7.json 全零）
- 终态 6554/6617、369/402 与 Round 5–8 报告终态逐位持平；本轮额外 +8 单元增益（shard0/6/7）与 shard0 文件级 +1（jq_trans_module，B66/B67/B68 修复真身增益），全为 IMPROVED 方向

## 2. 小测试集 34（baseline/failing_index.json）

- 实测 **1505/1568**（95.98%），1 success / 33 failure
- compare（round8/small34_report_new.json → round9/small34_new.json）：**REGRESSIONS=0 IMPROVED=0**，文件与单元逐位持平

## 3. quotation.pyc（基线路径口径）

- `site-packages/fly/data/quotation.pyc`：**152/153**，唯一失败 `change_his_to_forward`（Different control flow）= Round 8 VERIFICATION 逐字一致，零新增失败

## 4. tests/ 六套件

- `test_algorithm_correctness + test_deep_nesting_pressure + test_control_flow_completeness_matrix + test_complete_syntax_coverage + test_boundary_cases + test_core_functional`
- 实测 **277 passed / 2 failed / 2 xpassed**
- 2 failed = `test_B01_simple_if_then_else_merge` + `test_BOUNDARY_02_large_function`，与 Round 7/8 登记基线失败名单逐字一致，**零新增失败**
- 口径注记（诚实记录）：历史 VERIFICATION 记 257/2/5；本轮 277 passed（套件累计用例数随轮次增加）/ 2 xpassed（xpassed 差异源于套件组合口径），失败名单口径一致零新增，门禁判据为「零新增失败」达成

## 5. 修复面哨兵（修复工程师自测 + 评审批次二独立复跑）

- r9 攻击面 12 pyc：修复自测 50/50（r9_fix1.json）∧ 评审独立复跑 50/50（rv9_r9face.json）
- round6 全量 16 pyc：**115/115**（双跑一致）
- round7 全量：**104/128**（24 失败单元名单与 r9_regress.json §2.1 逐位一致）
- round8 全量：**107/118**；rv8 变体面 **18/20**（失败 = B65/B63 登记面持平）
- 六哨兵 + option_account + quotation：**302/308**（trade_info_utils 失败 5 名单、quotation 152/153 均基线）

## 6. 轮门禁判定

- **≥1 破口封闭：达成**——B66/B67/B68 三破口封闭（评审放行 8/8 hunk）；B68 3 单元 + B66 1 单元 + B67 1 单元转 MATCH
- **读数改善：达成**——r9 攻击面 45/50 → 50/50（+5）；变体面 +2 补强；402 单元级 +8；文件级 +1（jq_trans_module）
- **无回退：达成**——402 八分片 REGRESSIONS=0、34 小集 REGRESSIONS=0、quotation 零新增、tests 零新增失败
- **红线核验：通过**——单 BOM（`efbbbf 222222` 双文件字节级验证）；core/ 插桩 grep 零命中；site-packages 既有 *OK.py 零手改（本轮仅 shard 重生成流程）；git worktree 归因残留清零（遗留 pcdc_r0/pcdc_wt/pcdc_r8wt 为前轮产物，已登记建议清理）

## 7. 残留交接（交 Round 10 终审）

- 本轮新登记：**B69**（if 宿主臂内空 try/finally 吞臂内 return + 嵌套倒置，B63/B64 族变体）、**B70**（`while True: with: pass` 幻影 break）——均 pre-fix 逐字节同败，既有缺口
- 沿袭残留：B42×3/B43/B44/B46–B51/B56–B62/B63/B64/B65/B69/B70 + round7 残留 81/117 名单 + r4_or4_and2 1/2（B11-R2）
- 观察项：R-1（`finally: continue/break` 理论落入门控 machinery 集风险，无测试面）；quotation 哨兵双口径统一建议

## 8. 流程记录

1. 评审批次一（d8246a8e，任务 9.1）：守卫族双向攻击 10 探针 43 单元 38/43 + 前八轮复验 326/361 + 98/137 + 168/169 零漂移；登记 B66/B67/B68
2. 修复在途快照（be58c97d）：主代理存证（含双 BOM 损坏诚实记录）
3. 修复批次（1624ef6d，任务 9.2）：BOM 恢复单头 + 全哨兵重验 + docstring C 条款补齐 + FIX.md
4. 评审批次二（e337fdd9，任务 9.3）：终判放行 + B69/B70 登记 + rv9_ 独立读数
5. 主代理验证（本报告）：402 八分片 + 34 小集 + quotation + tests 六套件全过门禁
