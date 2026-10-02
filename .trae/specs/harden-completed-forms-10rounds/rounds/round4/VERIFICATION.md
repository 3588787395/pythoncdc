# Round 4 主代理验证读数（VERIFICATION）

验证人：主代理（唯一判据 = `scripts/pyc_verify.py`；402 全量 = 8 分片重生成 OK.py + batch + compare，全部命令 ≤300s；验证驱动复用 round1 流程，副本落 round4 目录）。当前树 = 2478b02a（评审二批复核后）。

## 全量 402（当前树 vs 基线 a9ac63e3）

| 指标 | 基线 | Round 3 结束 | **Round 4 结束** |
|---|---|---|---|
| 单元级 success | 6546/6617（98.93%） | 6554（99.05%） | **6554/6617（99.05%）** |
| 文件级 success | 368/402 | 369 | **369/402** |
| Movement Matrix | — | REGRESSIONS=0 | **REGRESSIONS=0（8/8 片零回退；IMPROVED 合计 +8 单元级/+1 文件级，均 Round 1 既有增益保持：shard0 jq_trans_module、shard6 tlb、shard7 +3）** |
| 反编译/编译错误 | 0/0 | 0/0 | **0/0（8 片 compile_error=0 error=0）** |

分片明细：shard0 777/786、shard1 462/469、shard2 537/538、shard3 883/887、shard4 848/855、shard5 993/999、shard6 789/801、shard7 1265/1282——8 片全部 REGRESSIONS=0。402 重生成 402/402 成功零失败。

Round 4 修复的真身增益体现于合成对抗面（round4 攻击面 48/96 → **94/96** 单元 MATCH，13/14 文件全 success），402 真身零新增增益、零回退——与 Round 2/3 模式一致（match 语料在 402 中占比极小）。

## 小测试集（baseline/failing_index.json，34 pyc）

- worse = **0**，improved = 0（Round 1 增益全部保持：quote 84/92、trade_live_broker 118/128、jq_trans_module 65/65）
- 汇总读数：1505/1568（95.98%），报告 `rounds/round4/small34_report_new.json`，与 Round 3 终态逐单元持平

## quotation.pyc / tests/

- `site-packages/fly/data/quotation.pyc`：**152/153（99.35%）**，唯一失败 change_his_to_forward 基线既有，零新增
- tests/（六套件）：`test_complete_syntax_coverage`+`test_control_flow_completeness_matrix` 174 passed；`test_algorithm_correctness`+`test_deep_nesting_pressure` 33 passed/2 failed；`test_ternary_combinations`+`test_boundary_cases` 49 passed/5 xpassed/1 failed → **256 passed / 3 failed**——3 失败（test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function、test_BND_21_walrus_operator_comprehensive）与 Round 1/2/3 确证基线逐一对应，**零新增失败**

## 轮门禁判定

- **≥1 破口封闭：达成（超额，7/8）**——B12（模式发射废料 compile_error×4 文件→3 文件 compile 全通过）、B13（尾通配 case 整体丢失，r4_03 7/7）、B14（捕获归属三判据，验收 4/4）、B15（前导吞失/尾 return 错归）、B16（循环×match 装配灾难，r4_12 0→7/7）、B17（try 包 match 壳丢失）、B18（类模式槽位 SWAP 栈模拟+guard）、B19（调用 subject 丢失）——7/7 封闭声明经评审复核放行（r4_04 余 2 单元如实登记未落地，需绝对栈深种子完整栈模拟，交后续批次）
- **攻击面读数改善：达成**——Match 攻击面 96 单元 48→94 MATCH（39.6%→97.9%），14 文件中 13 全 success
- **无回退：达成**（402 八片、34 小集、quotation 152/153、tests 零新增、哨兵全持平）

## 评审流程记录（对抗闭环）

1. 评审批次（01de7afa 前置提交）：Match+8 模式 14 文件 96 单元 48/58 success + 探针 3/3 + 负对照 7/7，wiki「Match 完备」声明证伪；登记 B12–B19
2. 修复一批次（bb8efb50）：B12/B13/B14 三破口封闭
3. 修复二批次（e0ad6f3b）：B15/B16/B17/B18/B19 五破口封闭；r4_04 余 2 如实登记
4. 评审批次二（2478b02a）：读数复跑 17 支零虚报、67 hunk 全审零白名单、变体攻击 8/8（4 过 4 揭新边界）、终判 7/7 放行零打回

## 本轮登记（交 Round 5 / 台账）

- **B12-R**（新边界）：or 交替拆独立 case 且体变 pass、or+as 捕获名丢失、跨交替同名捕获幻影化为字面量（rv4_12 1/4）
- **B13-R**（新边界）：同函数第二支 match(mapping+尾通配) 坍缩幻影 if 链、case 体内嵌套 match+尾通配内层整体丢失（rv4_13 2/4）
- **B16-R**（新边界）：while>match>match 内层降级 if 链、while>match 尾通配+break case 丢失（rv4_16 2/4）
- **B17-R**（新边界）：try/except/**else** 包 match 丢 else 子句、try/**finally** 包 match 首 case 体 pass 退化（rv4_17 2/4）
- **r4_04 余 2 单元**（match_map_nested/match_map_mixed_seq）：需绝对栈深种子的完整栈模拟（SWAP 链窗口起点依赖真深），原型可行、接线回归风险高，交后续批次
- **B10-R/B11-R2**（Round 3 挂账）维持未修：r3_34 1/2、r4_or4_and2 1/2 持平
- **R4-O1** 判据盲区观察点：pyc_verify 对尾 `return None` 差异归一化，语义破缺漏检
- **台账动作（wiki §8.2 复审六步，交维护批）**：Match/match_case 形态判定由「完备」**降格为「对抗修正：批次封闭 B12–B19，残留 B12-R/B13-R/B16-R/B17-R + r4_04 余 2」**；128 分子不计 Match 直至残留清零；For/While/Break/Continue「浅层/受限形态完备」标注（Round 3 遗留）一并执行
- 卫生观察项：core/ 存量 34 处 print 为历史轮遗留且环境变量门控（非本轮引入）

## 产物

评审 `REVIEW.md`/`REVIEW2.md`；修复 `FIX.md`（§批次一+§批次二）；复现 `test_repros/round4/`（probe、r4_01..r4_14、n4_01、r4_or4_and2、rv4_12..rv4_19 变体）；分片报告 `regen_shard0..7.json` + `shard0..7_report_new.json`；小测试集报告 `small34_report_new.json`
