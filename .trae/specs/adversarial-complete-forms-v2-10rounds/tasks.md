# Tasks

目标：对 wiki 总纲 §5 台账已判"完备"的 127 形态完成终局对抗评审与算法完善；残余破口清零（B42×3/B43/B44/B46–B51/B56–B65/B69/B70 及新登记 B71+）；`_identify_*` 十族方法注释三要素全量过审；全量 402 无回退；台账 128/128 复审成立。
角色：主代理 = 调度 + 阶段提交 + 全量验证 + push（零实现）；评审工程师 = 对抗攻击 + 合规审计 + 复核（子代理，独立两批）；修复工程师 = 算法修复 + 注释三要素（子代理，1..m 位协同）。
纪律：每轮独立文件夹；调用子代理前必须本地提交；每轮 ≥1 破口封闭或 ≥1 读数改善，否则禁止下一轮；每轮提交并 push；所有命令 ≤300s；禁止手改 `*OK.py`；站桩回归每轮强制；主代理不代笔，子代理故障重试派发或如实上报。

- [ ] Task 0: 规范就位与基线快照（主代理）
  - [ ] 0.1 本规范三件套就位；小测试集沿用 `harden-completed-forms-10rounds/baseline/failing_index.json`（34 pyc）；本规范 `baseline/` 落盘承接基线快照（402 = 6554/6617、369/402；34 = 1505/1568；quotation 152/153；tests 基线名单 test_B01 + test_BOUNDARY_02；残余破口名单）
  - [ ] 0.2 本规范三件套 + 基线快照本地提交（round1 派发前置；工作树若存在用户在途变更一并存证，禁止回滚）
- [ ] Task 1: Round 1 — 承接终审（旧规范 Round 10 未竟项）
  - [ ] 1.1 评审工程师：残余破口登记面逐项复验（B42×3/B43/B44/B46–B51/B56–B65/B69/B70 重放登记探针，读数与 round9 终态持平）+ 台账 127 形态对抗覆盖盘点（产出「形态 × 已对抗轮次 × 覆盖深度」矩阵，空白格作为 Round 2–9 主题输入）+ 算法合规审计（在途变更/BOM/插桩）；REVIEW.md
  - [ ] 1.2 修复工程师（可多位协同）：残余破口中具备判据形态者优先封闭（判据 = 同层结构事实，docstring 三要素 + C1/C2/C3 同步）；自测 = 复现转 MATCH + 负对照 + 34 小测试集 + 站桩回归零回退；FIX.md
  - [ ] 1.3 评审工程师复核：逐 hunk 审查（零容忍打回）+ 读数独立复跑 + 变体攻击；REVIEW2.md
  - [ ] 1.4 主代理验证：34 小测试集 batch → 402 八分片 batch+compare REGRESSIONS=0 → quotation 152/153 零新增 → tests 零新增失败；VERIFICATION.md
  - [ ] 1.5 归档 rounds/round1/ + 提交并 push origin main
- [ ] Task 2: Round 2 — 表A 语句结构形态对抗（优先文档标榜完备：If/For/While/Try/With/Match/Assert/Return/Assign/Delete/Import 族 × 深层宿主）
  - [ ] 2.1 评审工程师：按覆盖矩阵空白格抽取表A 形态，每形态 ≥10 深层/交叉复现（深度 ≥3）+ ≥2 MATCH 负对照；站桩回归重放；合规审计；登记新破口（B71+ 续接）；REVIEW.md + test_repros/round2/
  - [ ] 2.2 修复工程师（≥2 族并行时多位协同）：封闭登记破口（同层结构事实判据 + 注释三要素 + C1/C2/C3）；自测零回退；FIX.md（可多份）
  - [ ] 2.3 评审工程师复核：逐 hunk + 读数复跑 + 变体攻击；通过/打回；REVIEW2.md
  - [ ] 2.4 主代理验证：验证序五步（34 → 402 八分片 compare REGRESSIONS=0 → quotation → tests → 读数汇报）；VERIFICATION.md
  - [ ] 2.5 归档 rounds/round2/ + 提交并 push origin main
- [ ] Task 3: Round 3 — 表B 表达式形态对抗（BoolOp/Ternary/链式比较/Lambda/推导式族/Call/JoinedStr/海象/Starred/Slice 等）
  - [ ] 3.1 评审工程师：同 2.1 攻击协议（覆盖矩阵空白格优先 + 站桩回归 + 合规审计 + Bn 登记）；REVIEW.md + test_repros/round3/
  - [ ] 3.2 修复工程师（可多位协同）：封闭登记破口；自测零回退；FIX.md
  - [ ] 3.3 评审工程师复核；REVIEW2.md
  - [ ] 3.4 主代理验证：验证序五步；VERIFICATION.md
  - [ ] 3.5 归档 rounds/round3/ + 提交并 push origin main
- [ ] Task 4: Round 4 — 表C 31 扩展形态对抗（elif 链/for-else/while-else/except\*/match 8 模式/多目标赋值/augassign/链式比较/海象/关键字实参/star args/相对导入/global-nonlocal/f-string 转换/多重 for 推导/try-finally-only/装饰器带参/async 五件套）
  - [ ] 4.1 评审工程师：同 2.1 攻击协议；REVIEW.md + test_repros/round4/
  - [ ] 4.2 修复工程师（可多位协同）：封闭登记破口；自测零回退；FIX.md
  - [ ] 4.3 评审工程师复核；REVIEW2.md
  - [ ] 4.4 主代理验证：验证序五步；VERIFICATION.md
  - [ ] 4.5 归档 rounds/round4/ + 提交并 push origin main
- [ ] Task 5: Round 5 — 深层嵌套交叉矩阵对抗（覆盖矩阵剩余空白格：形态 × 宿主区域组合，深度 ≥3，重点 = 台账"完备"声明从未被交叉攻击过的组合）
  - [ ] 5.1 评审工程师：交叉矩阵抽样攻击 + 站桩回归 + 合规审计 + Bn 登记；REVIEW.md + test_repros/round5/
  - [ ] 5.2 修复工程师（可多位协同）：封闭登记破口；自测零回退；FIX.md
  - [ ] 5.3 评审工程师复核；REVIEW2.md
  - [ ] 5.4 主代理验证：验证序五步；VERIFICATION.md
  - [ ] 5.5 归档 rounds/round5/ + 提交并 push origin main
- [ ] Task 6: Round 6 — `_identify_*` 十族方法注释三要素与算法一致性审计（识别条件/归约方式/AST 映射 + C1/C2/C3 逐方法对照代码行为；不一致即打回修复）
  - [ ] 6.1 评审工程师：十族识别方法（conditional/loop/try_except/with/match/assert/boolop/ternary/chained_compare/sequence）+ 对应生成方法逐方法审计（docstring 三要素齐全性 ∧ 与代码行为一致性 ∧ C1/C2/C3 条款声明）+ 站桩回归 + 合规审计；REVIEW.md
  - [ ] 6.2 修复工程师（可多位协同，按方法族分派）：注释与代码对齐修复（以代码真实算法为准修正注释，或以注释声明的正确算法为准修正代码——两者必居其一，禁止含糊）；FIX.md
  - [ ] 6.3 评审工程师复核：逐方法重审一致性；REVIEW2.md
  - [ ] 6.4 主代理验证：验证序五步；VERIFICATION.md
  - [ ] 6.5 归档 rounds/round6/ + 提交并 push origin main
- [ ] Task 7: Round 7 — 已封闭守卫族与 B1–B70 全量深度外推重放（站桩回归强化轮：外推变体 + 收缩变体双向攻击，守卫判据面重攻击）
  - [ ] 7.1 评审工程师：B2/B3/B4 守卫族 + B1a/B1b/B6–B40/B45/B54/B55/B66–B68 已封闭面双向攻击（守卫适用形态变体/边界外形态/互斥组合）+ 前六轮新封闭面重放；读数不得变差；REVIEW.md + test_repros/round7/
  - [ ] 7.2 修复工程师（可多位协同）：封闭攻击中暴露的守卫缺口（封闭守卫恢复无感，禁止个案补丁）；FIX.md
  - [ ] 7.3 评审工程师复核；REVIEW2.md
  - [ ] 7.4 主代理验证：验证序五步；VERIFICATION.md
  - [ ] 7.5 归档 rounds/round7/ + 提交并 push origin main
- [ ] Task 8: Round 8 — 残余破口清零冲刺（任何未封闭 B 项：定位→封闭→复审；不具备判据形态者按 wiki §8.3 证伪降级并记录机制）
  - [ ] 8.1 评审工程师：残余破口全量清单盘点 + 逐项判据形态评估（可封闭/需证伪）+ 站桩回归 + 合规审计；REVIEW.md
  - [ ] 8.2 修复工程师（可多位协同）：按清单封闭或配合证伪（判据 = 同层结构事实）；FIX.md
  - [ ] 8.3 评审工程师复核；REVIEW2.md
  - [ ] 8.4 主代理验证：验证序五步；VERIFICATION.md
  - [ ] 8.5 归档 rounds/round8/ + 提交并 push origin main
- [ ] Task 9: Round 9 — 全台账 128 形态终局对抗复验（表A/表B/表C 全形态各 ≥1 深层探针 + 负对照 + 站桩回归全重放）
  - [ ] 9.1 评审工程师：128 形态终局复验 + 站桩回归全重放 + 合规审计终审；新发现即登记并本轮封闭；REVIEW.md + test_repros/round9/
  - [ ] 9.2 修复工程师（可多位协同）：封闭终局复验发现；FIX.md
  - [ ] 9.3 评审工程师复核；REVIEW2.md
  - [ ] 9.4 主代理验证：验证序五步；VERIFICATION.md
  - [ ] 9.5 归档 rounds/round9/ + 提交并 push origin main
- [ ] Task 10: Round 10 — 终审与台账定稿
  - [ ] 10.1 wiki §8.2 复审六步全量执行：grep 全部落地标记 → 台账（§5）全量更新 → `tools/kb/syntax_coverage.py` 重跑 → 完备占比重算 → wiki 页面数字同步（禁手改、禁矛盾数字）→ log 记录（评审工程师执行，主代理验收）
  - [ ] 10.2 主代理全量终验：402 八分片 batch + compare REGRESSIONS=0 + quotation + tests + 34 小测试集；VERIFICATION.md
  - [ ] 10.3 终归档 + 提交并 push origin main；汇报终态读数（单元级/文件级/完备占比/破口状态/注释三要素过审面）

注：每轮内部流程同构 = 评审攻击 → 修复 → 评审复核 → 主代理验证 → 归档 push；轮主题可依 Round 1 覆盖矩阵盘点结果微调（空白格优先），但 10 轮总量、每轮门禁与验证序不变；轮与轮之间形态不重复（Round 7 回归重放除外）。

# Task Dependencies
- Task 0–10 严格顺序依赖（前一轮门禁未过禁止开启下一轮）
- 每轮内：评审 → 修复 → 复核 → 验证 → push 串行；单轮内多位修复工程师可并行（破口族不相交 ∧ 涉改文件不相交）
- Task 10.1 依赖 10.2 终验通过后定稿归档（先验后台账）
