# Round 5 主代理验证读数（VERIFICATION）

验证人：主代理（唯一判据 = `scripts/pyc_verify.py`；402 全量 = 8 分片重生成 OK.py + batch + compare，全部命令 ≤300s；验证驱动复用 round1 流程副本 `verify_driver.py`）。当前树 = 9ef4597a（评审批次二复核放行后）。

## 全量 402（当前树 vs 基线 a9ac63e3）

| 指标 | 基线 | Round 4 结束 | **Round 5 结束** |
|---|---|---|---|
| 单元级 success | 6546/6617（98.93%） | 6554（99.05%） | **6554/6617（99.05%）** |
| 文件级 success | 368/402 | 369 | **369/402** |
| Movement Matrix | — | REGRESSIONS=0 | **REGRESSIONS=0（8/8 片零回退）** |
| 反编译/编译错误 | 0/0 | 0/0 | **0/0（8 片 compile_error=0 error=0；402 重生成 402/402 零失败）** |

分片明细：shard0 777/786（IMPROVED=1：jq_trans_module 65/65 Round 1 既有增益保持）、shard1 462/469、shard2 537/538、shard3 883/887、shard4 848/855、shard5 993/999、shard6 789/801、shard7 1265/1282——8 片全部 REGRESSIONS=0。

Round 5 修复的真身增益体现于合成对抗面（round5 攻击面 16 文件 192 单元：评审批次 180 MATCH/12 MISMATCH + 11 compile_error → 修复后 r5_04 13/13、r5_06 13/13、r5_07 11/11、r5_09 12/12、r5_10 13/13、r5_11 19/19 全 success；复核变体面 61 单元 57 MATCH），402 真身零新增增益、零回退——与 Round 2/3/4 模式一致（推导式语料在 402 中占比极小）。

## 小测试集（baseline/failing_index.json，34 pyc）

- Movement Matrix（vs Round 4 终态）：**REGRESSIONS=0 IMPROVED=0**，逐文件逐状态持平（success 1 / failure 33）
- 汇总读数：1505/1568（95.98%），报告 `small34_report_new.json`

## quotation.pyc / tests/

- `site-packages/fly/data/quotation.pyc`：**152/153（99.35%）**，唯一失败 change_his_to_forward 基线既有，零新增
- tests/（六套件）：`test_complete_syntax_coverage`+`test_control_flow_completeness_matrix` 174 passed；`test_algorithm_correctness`+`test_deep_nesting_pressure` 33 passed/2 failed；`test_ternary_combinations`+`test_boundary_cases` 50 passed/5 xpassed → **257 passed / 2 failed / 5 xpassed**
- **对比 Round 4 终态（256 passed/3 failed）：test_BND_21_walrus_operator_comprehensive 由 failed 转 passed（B22 walrus 幻影迭代目标封闭的真身增益）**；其余 2 失败（test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function）与 Round 1–4 确证基线逐一对应，零新增失败

## 轮门禁判定

- **≥1 破口封闭：达成（超额，6/6）**——B20（跨 clause 过滤静默丢失，r5_04 12/13→13/13）、B21（解包 target 拍平/星号坍缩，r5_06 11/13→13/13）、B22（walrus 幻影迭代目标 P0，r5_07 compile_error 0/11→11/11）、B23（async 组合坍缩，r5_10 9/13→13/13）、B24（try/finally 包 return 推导式被剥除，r5_09 11/12→12/12）、B25（lambda 默认值丢失双杀 P0，r5_11 17/19→19/19 + probe_lam_default 4/6→6/6）——6/6 封闭声明经评审复核放行（B24 except-handler 内 return 值带 finally 如实登记未落地，属 handler 装配子系统辖域）
- **读数改善：达成**——tests/ 3 failed→2 failed（BND_21 walrus 转通过）；推导式攻击面 12 MISMATCH + 11 compile_error → 0
- **无回退：达成**（402 八片、34 小集、quotation 152/153、tests 零新增失败、哨兵全持平）

## 评审流程记录（对抗闭环）

1. 评审批次（eec7041a 前置提交）：推导式族 16 文件 192 单元 180 MATCH/12 MISMATCH（93.75%）+ r5_07 compile_error 11 单元 + 负对照 n5_01 7/7，wiki「推导式完备」声明证伪；登记 B20–B25
2. 修复一批次（7e09e36d）：B20/B21/B22 三破口封闭（同根名袋一并解决）
3. 修复二批次（45864cc5）：B25/B23/B24 三破口封闭（含 B24 触发分支实测更正）
4. 评审批次二（9ef4597a）：读数复跑 21/21 支零虚报、20 hunk 全审合规、变体攻击 6 探针 61 单元 57 MATCH、终判放行零打回

## 本轮登记（交 Round 6 / 台账）

- **B26**（新破口，修复前既有缺口）：async GenExp 作实参坍缩 `None(ait())`（rv5_23）
- **B27**（新破口，修复前既有缺口）：嵌套 try 包 return 值剥除，普通值即杀（rv5_24 + rv5_26_diag）
- **B28**（新破口，修复前既有缺口）：纯 vararg/kwarg lambda 形参丢失（rv5_25）
- **B24 残留**：except handler 内 `return <值>` 带 finally（handler 装配子系统辖域，修复前后失败签名一致）
- **B20 边界**：非最内层 clause 三元作过滤（Pattern B）未扩展，降级产物语法合法
- **Round 4 挂账维持**：B12-R/B13-R/B16-R/B17-R（rv4_12 1/4、rv4_13 2/4、rv4_16 2/4、rv4_17 2/4 复验持平）、r4_04 余 2、B10-R/B11-R2 持平
- **台账动作（wiki §8.2 复审六步，交维护批）**：推导式族（List/Set/Dict/GenExp/多 for 嵌套）判定由「完备」**升格为「对抗修正：封闭 B20–B25，残留 B26/B27/B28 + B24 handler 残留 + B20 Pattern B 边界」**；同步登记 B26–B28 进 §8.3 状态机

## 产物

评审 `REVIEW.md`/`REVIEW2.md`；修复 `FIX.md`（§批次一+§批次二）；复现 `test_repros/round5/`（probe、r5_01..r5_13、n5_01、probe_lam_default、rv5_20..rv5_26 变体）；分片报告 `regen_shard0..7.json` + `shard0..7_report_new.json`；小测试集报告 `small34_report_new.json`

## push 记录（网络故障登记）

- 待推送提交：`45864cc5`（修复二批次）→ `9ef4597a`（评审批次二）→ `4cd1c2e3`（归档与验证），均已本地提交
- push 结果：**失败（网络故障，6 次重试均败）**
- 错误详情：`fatal: unable to access 'https://github.com/3588787395/pythoncdc.git/': Failed to connect to github.com port 443: Couldn't connect to server` 与 `Recv failure: Connection was reset` 交替出现（21s 连接超时）
- 已尝试：`git push origin main`（×2）、显式 token URL（×2）、`-c http.version=HTTP/1.1`（×3）、间隔 10/20/45/60s
- 重试命令（Round 6 启动前必须首先执行）：
  `git -C f:\Downloads\pythoncdc-main -c http.version=HTTP/1.1 push https://3588787395:ghp_****@github.com/3588787395/pythoncdc.git main`
- 本故障与 Round 1–4 历史 push 网络故障同型（curl 28 Recv failure 族），非代码/凭据问题
