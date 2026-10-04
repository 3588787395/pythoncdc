# Tasks

目标：对 wiki 总纲 §5 台账已判"完备"的 127+1 形态（spec III.2–III.4 全名单，v6 口径形式层 128/128）完成终局对抗评审与算法完善；残余破口清零（III.5 名单及 B77+）；`_identify_*` 十族方法注释六项模板（spec I.7）全量过审；全量 402 无回退；台账 128/128 终局复验成立（spec II.1 口径，形式层 + 组合级挂账如实分层）。
理论依据：spec 理论基准 I（设计原则：四原则/C1-C2-C3/判据白名单/禁止事项/修复语义/注释合规）+ II（完备预期：128 分母/三级判定/三路径/13 误解）+ III（对抗目标台账与锚点）+ IV（字节码口径与门禁）。修复与评审的一切结论必须引用条款编号。
角色：主代理 = 调度 + 阶段提交 + 全量验证 + push（零实现）；评审工程师 = 对抗攻击 + 合规审计 + 复核（子代理，独立两批）；修复工程师 = 算法修复 + 注释合规（子代理，1..m 位协同）。
纪律：每轮独立文件夹；调用子代理前必须本地提交；每轮 ≥1 破口封闭或 ≥1 读数改善，否则禁止下一轮；每轮提交并 push（前缀 `rr-v2rNN:`）；所有命令 ≤300s；禁止手改 `*OK.py`；站桩回归每轮强制；主代理不代笔，子代理故障重试派发或如实上报。

- [ ] Task 0: 规范就位与基线快照（主代理）
  - [ ] 0.1 本规范三件套就位；小测试集沿用 `harden-completed-forms-10rounds/baseline/failing_index.json`（34 pyc）；本规范 `baseline/` 落盘承接基线快照（spec II.6 全表：402 = 6554/6617、369/402；34 = 1505/1568；quotation 152/153；tests 基线名单；残余破口承接名单 III.5）
  - [ ] 0.2 本规范三件套 + 基线快照本地提交（round1 派发前置；工作树若存在用户在途变更一并存证，禁止回滚）
- [ ] Task 1: Round 1 — round10 终态承接复验（旧规范 Round 10 已完成归档、唯 push 未竟；本轮核对 v6 口径 + 残余名单实测 + 覆盖矩阵盘点）
  - [ ] 1.1 评审工程师：v6 口径核对（wiki 五页 v6 数字 + syntax-coverage.json 128/128 + 台账 §5 形式层 128/0/0 与树内代码一致性抽查）+ 残余破口登记面逐项复验（III.5 名单：沿袭残留 B42×3/B43/B44/B47/B49/B50/B51/B56–B62/B65/B69/B70/B11-R2 + round10 新登记 B71/B73–B76/B48 残留变体/B46 尾项，重放登记探针，读数与 round10 终态持平，确认承接名单实测口径；权威清单 = 旧规范 rounds/round10/REVIEW.md §4 + REVIEW2.md）+ 台账 128 形态对抗覆盖盘点（以旧 round10 覆盖矩阵 41 组为起点：35 组已覆盖 + 6 组零专攻如实登记，产出「形态 × 已对抗轮次 × 覆盖深度」矩阵，以 III.2–III.4 全名单为行，零专攻组与空白格作为 Round 2–9 主题输入）+ 算法合规审计（I.4 黑名单五项 + BOM/插桩/在途变更，锚点+条款+机制格式打回）；REVIEW.md
  - [ ] 1.2 修复工程师（可多位协同，破口族/涉改文件不相交时并行）：残余破口中具备判据形态者优先封闭（判据只取 I.4 白名单；修复语义 = I.3/I.6 封闭守卫恢复 C1/C2/C3；触及方法 docstring 按 I.7 六项模板 + C 条款）；自测 = 复现转 MATCH + 负对照 + 34 小测试集 + 站桩回归 + IV.2 门禁自检清单；FIX.md 含「代码已落地」声明
  - [ ] 1.3 评审工程师复核：逐 hunk 审查（对照 I.1–I.7 逐条款，零容忍打回）+ 读数独立复跑（防虚报）+ 变体攻击；REVIEW2.md
  - [ ] 1.4 主代理验证：验证序六步（spec「主代理无回退验证」：34 batch → 402 八分片 batch+compare REGRESSIONS=0 → quotation 152/153 零新增 → tests 零新增失败 → IV.2 门禁自检 → 读数汇报）；VERIFICATION.md
  - [ ] 1.5 归档 rounds/round1/ + 提交并 push origin main
- [ ] Task 2: Round 2 — 表A 语句结构形态对抗（III.2 全名单：If/For/While/Try/TryStar/With/Match/Assert/Raise/Return/Assign/Delete/Import/Global/FunctionDef/ExceptHandler × 深层宿主，优先文档标榜完备者与覆盖矩阵空白格）
  - [ ] 2.1 评审工程师：每形态 ≥10 深层/交叉复现（深度 ≥3）+ ≥2 MATCH 负对照，实测深层与浅层产物结构一致（C2 判据）；宣告完备前逐条自查 13 误解（II.7）；站桩回归重放；合规审计；登记新破口（B71+ 续接，锚点+机制+违反条款）；REVIEW.md + test_repros/round2/
  - [ ] 2.2 修复工程师（≥2 个不相交破口族时多位并行）：封闭登记破口（I.4 白名单判据 + I.3 推论修复方向 + I.7 注释）；自测 = IV.2 门禁自检清单全过；FIX.md（可多份）
  - [ ] 2.3 评审工程师复核：逐 hunk + 读数独立复跑 + 变体攻击；通过/打回；REVIEW2.md
  - [ ] 2.4 主代理验证：验证序六步；VERIFICATION.md
  - [ ] 2.5 归档 rounds/round2/ + 提交并 push origin main
- [ ] Task 3: Round 3 — 表B 表达式形态对抗（III.3 全名单：BoolOp/IfExp/Compare 链/BinOp/UnaryOp/Lambda/推导式族/Call/JoinedStr/Await/Yield/NamedExpr/操作符叶子 32 个 × 嵌套宿主，B1 台账口径重点复核）
  - [ ] 3.1 评审工程师：同 2.1 攻击协议（II.7 自查 + 站桩回归 + 合规审计 + Bn 登记）；REVIEW.md + test_repros/round3/
  - [ ] 3.2 修复工程师（可多位协同）：封闭登记破口（I.4/I.3/I.7 约束）；自测 = IV.2 门禁自检清单全过；FIX.md
  - [ ] 3.3 评审工程师复核；REVIEW2.md
  - [ ] 3.4 主代理验证：验证序六步；VERIFICATION.md
  - [ ] 3.5 归档 rounds/round3/ + 提交并 push origin main
- [ ] Task 4: Round 4 — 表C 31 扩展形态对抗（III.4 全名单：elif 链/for-else/while-else/except\*/match+守卫+8 模式/多上下文 with/try-finally-only/multi_target/augassign/chained_comparison/walrus/keyword_args/star_args/slice/relative_import/star_import/global_nonlocal/fstring_conversion/nested_comprehension/decorator_with_args/async 五件套）
  - [ ] 4.1 评审工程师：同 2.1 攻击协议；except\* 检测标准对准 3.11 标记（II.7 第 12 条：CHECK_EG_MATCH/PREP_RERAISE_STAR/is_except_star）；REVIEW.md + test_repros/round4/
  - [ ] 4.2 修复工程师（可多位协同）：封闭登记破口；自测 = IV.2 门禁自检清单全过；FIX.md
  - [ ] 4.3 评审工程师复核；REVIEW2.md
  - [ ] 4.4 主代理验证：验证序六步；VERIFICATION.md
  - [ ] 4.5 归档 rounds/round4/ + 提交并 push origin main
- [ ] Task 5: Round 5 — 深层嵌套交叉矩阵对抗（覆盖矩阵剩余空白格：形态 × 宿主区域组合，深度 ≥3；重点 = 台账"完备"声明从未被交叉攻击过的组合；C1/C2/C3 逐条款攻击设计）
  - [ ] 5.1 评审工程师：交叉矩阵抽样攻击（每空白格 ≥3 探针）+ 站桩回归 + 合规审计 + Bn 登记；REVIEW.md + test_repros/round5/
  - [ ] 5.2 修复工程师（可多位协同）：封闭登记破口（深层才错 = C 条款破坏，按 I.3 推论封闭守卫）；自测 = IV.2 门禁自检清单全过；FIX.md
  - [ ] 5.3 评审工程师复核；REVIEW2.md
  - [ ] 5.4 主代理验证：验证序六步；VERIFICATION.md
  - [ ] 5.5 归档 rounds/round5/ + 提交并 push origin main
- [ ] Task 6: Round 6 — `_identify_*` 十族方法注释合规与算法一致性审计（III.1 锚点逐方法：docstring 六项模板齐全性（I.7）∧ 与代码行为一致性 ∧ C1/C2/C3 条款声明；不一致即打回）
  - [ ] 6.1 评审工程师：十族识别方法 + 对应生成方法逐方法审计（六项模板逐项对照代码真实行为；③唯一归属判定/④嵌套处理/⑤入口引用语义与四原则 I.1 对照）+ 站桩回归 + 合规审计；REVIEW.md（逐方法结论表：合规/打回+条款）
  - [ ] 6.2 修复工程师（可多位协同，按方法族分派）：注释与代码对齐（以代码真实算法为准修正注释，或以注释声明的正确算法为准修正代码——两者必居其一，禁止含糊；代码修正同样受 I.4 白名单约束）；FIX.md
  - [ ] 6.3 评审工程师复核：逐方法重审一致性 + 读数复跑；REVIEW2.md
  - [ ] 6.4 主代理验证：验证序六步；VERIFICATION.md
  - [ ] 6.5 归档 rounds/round6/ + 提交并 push origin main
- [ ] Task 7: Round 7 — 已封闭守卫族与已复审破口全量深度外推重放（站桩回归强化轮：B2/B3/B4 守卫族 + B1b/B6–B40/B45/B54/B55/B66–B68 已封闭面，外推变体 + 收缩变体双向攻击）
  - [ ] 7.1 评审工程师：守卫判据面重攻击（守卫适用形态变体/守卫边界外形态/守卫互斥组合；外推验证守卫确实恢复无感而非窄门控）+ 前六轮新封闭面重放；读数不得变差；REVIEW.md + test_repros/round7/
  - [ ] 7.2 修复工程师（可多位协同）：封闭攻击暴露的守卫缺口（I.3 推论：封闭守卫恢复无感，禁止窄门控/个案补丁——窄门控 = I.4 黑名单「以少发射换全绿」变体，打回）；FIX.md
  - [ ] 7.3 评审工程师复核；REVIEW2.md
  - [ ] 7.4 主代理验证：验证序六步；VERIFICATION.md
  - [ ] 7.5 归档 rounds/round7/ + 提交并 push origin main
- [ ] Task 8: Round 8 — 残余破口清零冲刺（任何未封闭 B 项：定位→封闭→复审；不具备判据形态者按 wiki §8.3 证伪降级并记录机制）
  - [ ] 8.1 评审工程师：残余破口全量清单盘点 + 逐项判据形态评估（可封闭/需证伪；对每项给出 C1/C2/C3 违反条款归属）+ 站桩回归 + 合规审计；REVIEW.md
  - [ ] 8.2 修复工程师（可多位协同）：按清单封闭（I.4 白名单）或配合证伪归档；FIX.md
  - [ ] 8.3 评审工程师复核；REVIEW2.md
  - [ ] 8.4 主代理验证：验证序六步；VERIFICATION.md
  - [ ] 8.5 归档 rounds/round8/ + 提交并 push origin main
- [ ] Task 9: Round 9 — 全台账 128 形态终局对抗复验（III.2–III.4 全形态各 ≥1 深层探针 + 负对照 + 站桩回归全重放）
  - [ ] 9.1 评审工程师：128 形态终局复验（每形态结论 = 完备/破口/零能力三态之一，II.3 口径；完备宣告附 13 误解自查）+ 站桩回归全重放 + 合规审计终审；新发现即登记并本轮封闭；REVIEW.md + test_repros/round9/
  - [ ] 9.2 修复工程师（可多位协同）：封闭终局复验发现；FIX.md
  - [ ] 9.3 评审工程师复核；REVIEW2.md
  - [ ] 9.4 主代理验证：验证序六步；VERIFICATION.md
  - [ ] 9.5 归档 rounds/round9/ + 提交并 push origin main
- [ ] Task 10: Round 10 — 终审与台账定稿
  - [ ] 10.1 主代理全量终验：402 八分片 batch + compare REGRESSIONS=0 + quotation + tests + 34 小测试集 + IV.2 门禁自检；VERIFICATION.md
  - [ ] 10.2 wiki §8.2 复审六步全量重验与增量更新（评审工程师执行，主代理验收；旧 round10 已执行 v6 首跑，本轮为重验 + B77+ 增量）：grep 全部落地标记（含本规范各轮「代码已落地」声明核验，I.6）→ 台账（§5）全量更新（II.3 三态判定落位 + 组合级挂账分层）→ `tools/kb/syntax_coverage.py` 重跑 → 完备占比重算（II.1 口径）→ wiki 页面数字同步（禁手改、禁矛盾数字）→ log 记录
  - [ ] 10.3 终归档 + 提交并 push origin main；汇报终态读数（单元级/文件级/完备占比/破口状态/注释合规过审面/站桩回归终读数）

注：每轮内部流程同构 = 评审攻击 → 修复 → 评审复核 → 主代理验证 → 归档 push；轮主题可依 Round 1 覆盖矩阵盘点结果微调（空白格优先），但 10 轮总量、每轮门禁与验证序不变；轮与轮之间形态不重复（Round 7 回归重放除外）。

# Task Dependencies
- Task 0–10 严格顺序依赖（前一轮门禁未过禁止开启下一轮）
- 每轮内：评审 → 修复 → 复核 → 验证 → push 串行；单轮内多位修复工程师可并行（破口族不相交 ∧ 涉改文件不相交）
- Task 10.2 依赖 10.1 终验通过（先验后台账）
