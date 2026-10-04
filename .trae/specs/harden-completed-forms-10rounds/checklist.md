# Checklist

## 规范与基线
- [x] 新规范三件套已创建，对象 = 台账已判完备 127 形态的对抗评审与算法完善（round1 快照提交时一并入库）
- [x] 小测试集索引 `baseline/failing_index.json`（34 pyc）就位（round9 主代理实测 batch = 1505/1568）
- [x] 在途未评审变更已快照提交（一笔入库存证；round9 在途修复同理于 be58c97d 存证）

## 每轮纪律（round1–round10 逐轮核验；round9 实证记录）
- [x] 调用子代理前已本地提交（git log 可证，含阶段边界：round9 = d8246a8e 评审后 → be58c97d 在途存证 → 1624ef6d 修复后 → e337fdd9 复核后）
- [x] 独立文件夹 `rounds/round9/`（REVIEW.md、FIX.md、VERIFICATION.md、guard/fragment json）+ `test_repros/round9/`（12 探针组 + rv9_ 3 变体 + n9_01/n9_02 负对照全 MATCH）
- [x] 评审工程师：守卫族 B2/B3/B4 双向攻击（外推 9 + 收缩 1，10 探针 43 单元）+ 前八轮封闭破口复验（326/361 + 98/137 + 168/169 零漂移）+ 合规审计零容忍（在途变更/红线四项全过）
- [x] 修复工程师：B66/B67/B68 封闭限于区域归约算法（同层结构事实判据，评审 8/8 hunk 证实），docstring 三要素 + C1/C2/C3 条款同步，注释与代码一致
- [x] 评审复核结论 = 放行（REVIEW2.md；D-1 非阻塞偏差留档）
- [x] 主代理验证序：402 八分片 regen+batch+compare REGRESSIONS=0（6554/6617、369/402）→ 小测试集 34 = 1505/1568 REGRESSIONS=0 → quotation 152/153 零新增 → tests 六套件 277 passed/2 failed（基线名单）零新增
- [x] 本轮 ≥1 破口封闭或 ≥1 读数改善（B66/B67/B68 三封闭 + r9 攻击面 45/50→50/50 + 402 单元 +8 + 文件级 +1）
- [x] 成功率读数已汇报（单元级 6554/6617=99.05%、文件级 369/402、破口封闭 3、新登记 2）
- [x] 本轮已提交并 push 到 origin main（201234ab..94f8d95c）
- [x] 全程命令 ≤300s（分片 regen/verify/compare 三步驱动，verify 内部 290s 上限）

## 每轮纪律（round10 终审实证记录）
- [x] 调用子代理前已本地提交（72f46912 评审后 → b53d449c 修复后 → 0caea12b 复核后）
- [x] 独立文件夹 `rounds/round10/`（REVIEW.md、FIX.md、REVIEW2.md、VERIFICATION.md、r10_/f10_/rv10_ json）+ `test_repros/round10/`（17 探针组 + 3 变体 + n10 负对照 9/9）
- [x] 评审工程师：覆盖矩阵 41 组（35 覆盖/6 零专攻如实登记）+ 补攻击 61/72 + 残留 29 项决策 + B71–B75 登记；修复工程师：B72/B48/B46 部分封闭（同层结构事实判据，评审 6/6 hunk 证实），docstring 三要素 + C1/C2/C3 同步
- [x] 评审复核结论 = 放行（REVIEW2.md；哨兵口径裁决 114/114 = 漏跑 n6_01 口径缺口非造假，权威重跑 round6 115/115）
- [x] 主代理验证序：402 八分片 regen+batch+compare REGRESSIONS=0（6554/6617、369/402；shard7 触 290s 按纪律拆两半合并）→ 小测试集 34 = 1505/1568 REGRESSIONS=0 → quotation 152/153 零新增 → tests 六套件 277 passed/2 failed（基线名单）零新增
- [x] 本轮 ≥1 破口封闭或 ≥1 读数改善（B72/B48 封闭 + B46 部分 = 净 +7 单元；终审轮台账覆盖率提升：35/41 组覆盖 + 6 组如实登记；round7 面 +4、round8 面 +3 补强）
- [x] 成功率读数已汇报（单元级 6554/6617=99.05%、文件级 369/402、破口封闭 2 全 1 部分、新登记 B76 + 降级 2）
- [x] 本轮已提交并 push 到 origin main（见 git log 终归档链）
- [x] 全程命令 ≤300s（shard7 verify 超时 → verify7_split.py 拆两半 73s+30s 合并，compare 正常消费）

## 破口与台账
- [x] 新发现破口已登记 Bn 续接（锚点+机制+条款），状态机推进（round10：B72 封闭 + B48 封闭 + B46 部分封闭 + B76 登记；累计 B1a–B76）
- [x] B1a/B1b 与在途变更过审（round1 通过；round9 复验零漂移；round10 终审 grep 落地标记在树确证 + 台账升格「已封闭」）
- [x] wiki §8.2 复审六步按封闭情况执行（grep 落地标记→台账→syntax_coverage→占比→log）——round10 终审全量执行完毕（10.3）
- [x] 台账数字与 wiki 页面一致（禁手改）——round10 终审五页同步 v6 口径（syntax_coverage 重跑 128/128；组合级挂账 25 号透明分层，未清零如实呈现）

## 终态验收
- [ ] 台账 127 形态全部经对抗验证仍成立，破口清零 = 128/128（终审实测：形式层 128/0/0 = 100% 达成，但组合级挂账 25 号 + 6 组零专攻形态组未清零，诚实保持未勾；权威清单 = rounds/round10/REVIEW.md 残留决策表）
- [x] 402 全量无回退（compare REGRESSIONS=0）——round9/round10 两轮实测成立（6554/6617、369/402 逐位持平）
- [x] 主代理未执行修复/评审实现任务（仅调度 + 验证 + 勾选）——round1–round10 实证成立
- [x] 无用户既有变更被回滚（round1–round10 零回滚）
