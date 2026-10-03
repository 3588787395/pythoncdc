# Round 7 主代理验证归档（VERIFICATION.md）

- 验证人：主代理；验证树 = `c0ab03c1`（修复批次一）
- 判据唯一：`scripts/pyc_verify.py`（pylingual compare_pyc，Python 3.11.7）；全部命令 ≤300s

## 验证序与读数

### 1. 全量 402 八分片重生成 + batch + compare
- 重生成 **402/402**（8 分片 0 失败）
- 逐分片：shard0 777/786（46S，IMPROVED=1 jq_trans_module）、shard1 462/469（48S）、shard2 537/538（50S）、shard3 883/887（48S）、shard4 848/855（46S）、shard5 993/999（46S）、shard6 789/801（48S）、shard7 1265/1282（37S）
- **八分片全部 REGRESSIONS=0**
- **总计 6554/6617（99.05%）、文件 success 369/402** —— 与 Round 5/6 终态逐位持平；B42/B45 修复零回退、真身零新增增益（增益在合成对抗面）

### 2. 小测试集 34
- **1505/1568（95.98%）**，success 1 / failure 33
- Movement Matrix vs Round 6：**REGRESSIONS=0 IMPROVED=0** 逐文件持平

### 3. quotation.pyc
- **152/153（99.35%）**，唯一失败 change_his_to_forward 基线既有，零新增；OK 重生成零漂移

### 4. tests/ 六套件
- **257 passed / 2 failed / 5 xpassed**（test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function 基线既有）——零新增失败

### 5. 修复面哨兵（批次一自测 + 本轮复核）
- round6 全量 16 文件 **115/115**（r6_04 11/11、r6_10 6/6 重点盯）
- rv6 探针 **18/29** 持平（B37–B41 无变差）
- 六哨兵：tools 6/6、trade_schedule 6/6、mq_connector 13/13、strategy 2/2、scheduler 52/52、trade_info_utils 36/41（失败 5 名单 = 基线）
- option_account **35/35**
- BOM `efbbbf` 在位；`_R23N20_DEBUG`/`R23N21_DEBUG` grep = 0

## 本轮门禁判定
- **≥1 破口封闭：达成**——R7-O1（短路恢复）、R7-O2（插桩清除）、B45（2/2）、B42（6/9，残留 3 单元如实登记）
- **读数改善：达成**——r7 攻击面 96/128 → **104/128**（+8 单元；r7_02 容器面 5/8→8/8 文件转 success）
- **无回退：达成**——402 八分片、34 小集、quotation、tests 零位移
- 残留交 Round 8：B42 残留 3 单元（t_arg_multi_mixed 内层早返回路径 / t_compare_lhs_only 单链 return 形态 / listcomp filter 推导式子码路径）+ B43/B44/B46/B47/B48/B49/B50/B51（按 REVIEW.md 交接单）

## 流程记录
1. 评审批次（a4463b56）：表达式面伪完备证伪 96/128，登记 B42–B51 + R7-O1/O2
2. 修复批次一（c0ab03c1）：子代理三次基础设施故障（验证码超时）后主代理直接接管完成——R7-O1/R7-O2/B45/B42 修复
3. 复核批次：评审子代理进行中（REVIEW2.md 落盘后本归档随附）
4. push：归档提交后 `git push origin main`
