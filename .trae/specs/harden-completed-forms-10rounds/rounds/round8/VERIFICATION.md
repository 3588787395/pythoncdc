# Round 8 主代理验证归档（VERIFICATION.md）

- 验证人：主代理；验证树 = 5aff0e32（修复批次，612cf0f2 复核放行）
- 402 全量八分片重生成 402/402 + batch + compare：**全部 REGRESSIONS=0**，shard0 777/786（IMPROVED=1 jq_trans_module）、shard1 462/469、shard2 537/538、shard3 883/887、shard4 848/855、shard5 993/999、shard6 789/801、shard7 1265/1282 → **总计 6554/6617（99.05%）、369/402 文件**，与 Round 5/6/7 终态逐位持平（B54/B55 修复零回退、真身零新增增益，增益在合成对抗面 r8 101→107/118 + rv8 变体 +7）
- 小测试集 34：1505/1568（95.98%），Movement vs Round 7 **REGRESSIONS=0 IMPROVED=0**
- quotation.pyc：152/153，唯一失败 change_his_to_forward 基线既有，零新增
- tests 六套件：257 passed / 2 failed / 5 xpassed（基线一致零新增）
- 轮门禁：破口封闭达成（B54 4/4 + B55 3/2，经 8.3 复核放行 10/10 hunk）；读数改善达成（r8 101→107/118 + rv8 17/20）
- 残留交 Round 9：B42 残留 3 + B43/B44/B46/B48 + B56/B57/B58/B59/B60/B61/B62 + B63/B64/B65（复核新登记）+ Round 9 = B2/B3/B4 守卫族回归攻击 + 前八轮封闭破口复验（防回归）
- push：归档提交后 git push origin main
