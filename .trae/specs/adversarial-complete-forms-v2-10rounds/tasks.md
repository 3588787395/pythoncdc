# Tasks

目标：对 wiki 总纲 §5 台账已判"完备"的 127+1 形态（spec III.2–III.4 全名单，v6 口径形式层 128/128）完成终局对抗评审与算法完善；残余破口清零（III.5 名单及 B77+）；`_identify_*` 十族方法注释六项模板（spec I.7）全量过审；全量 402 无回退；台账 128/128 终局复验成立（spec II.1 口径，形式层 + 组合级挂账如实分层）。
理论依据：spec 理论基准 I（设计原则：四原则/C1-C2-C3/判据白名单/禁止事项/修复语义/注释合规）+ II（完备预期：128 分母/三级判定/三路径/13 误解）+ III（对抗目标台账与锚点）+ IV（字节码口径与门禁）。修复与评审的一切结论必须引用条款编号。
角色：主代理 = 调度 + 阶段提交 + 全量验证 + push（零实现）；评审工程师 = 对抗攻击 + 合规审计 + 复核（子代理，独立两批）；修复工程师 = 算法修复 + 注释合规（子代理，1..m 位协同）。
纪律：每轮独立文件夹；调用子代理前必须本地提交；每轮 ≥1 破口封闭或 ≥1 读数改善，否则禁止下一轮；每轮提交并 push（前缀 `rr-v2rNN:`）；所有命令 ≤300s；禁止手改 `*OK.py`；站桩回归每轮强制；主代理不代笔，子代理故障重试派发或如实上报。

- [x] Task 0: 规范就位与基线快照（主代理）
  - [x] 0.1 本规范三件套就位；小测试集沿用 `harden-completed-forms-10rounds/baseline/failing_index.json`（34 pyc）；本规范 `baseline/` 落盘承接基线快照（spec II.6 全表：402 = 6554/6617、369/402；34 = 1505/1568；quotation 152/153；tests 基线名单；残余破口承接名单 III.5）
  - [x] 0.2 本规范三件套 + 基线快照本地提交（round1 派发前置；工作树若存在用户在途变更一并存证，禁止回滚）
- [x] Task 1: Round 1 — round10 终态承接复验（旧规范 Round 10 已完成归档、唯 push 未竟；本轮核对 v6 口径 + 残余名单实测 + 覆盖矩阵盘点）
  - [x] 1.1 评审工程师：v6 口径核对（wiki 五页 v6 数字 + syntax-coverage.json 128/128 + 台账 §5 形式层 128/0/0 与树内代码一致性抽查）+ 残余破口登记面逐项复验（III.5 名单：沿袭残留 B42×3/B43/B44/B47/B49/B50/B51/B56–B62/B65/B69/B70/B11-R2 + round10 新登记 B71/B73–B76/B48 残留变体/B46 尾项，重放登记探针，读数与 round10 终态持平，确认承接名单实测口径；权威清单 = 旧规范 rounds/round10/REVIEW.md §4 + REVIEW2.md）+ 台账 128 形态对抗覆盖盘点（以旧 round10 覆盖矩阵 41 组为起点：35 组已覆盖 + 6 组零专攻如实登记，产出「形态 × 已对抗轮次 × 覆盖深度」矩阵，以 III.2–III.4 全名单为行，零专攻组与空白格作为 Round 2–9 主题输入）+ 算法合规审计（I.4 黑名单五项 + BOM/插桩/在途变更，锚点+条款+机制格式打回）；REVIEW.md
  - [x] 1.2 修复工程师（可多位协同，破口族/涉改文件不相交时并行）：残余破口中具备判据形态者优先封闭（判据只取 I.4 白名单；修复语义 = I.3/I.6 封闭守卫恢复 C1/C2/C3；触及方法 docstring 按 I.7 六项模板 + C 条款）；自测 = 复现转 MATCH + 负对照 + 34 小测试集 + 站桩回归 + IV.2 门禁自检清单；FIX.md 含「代码已落地」声明
  - [x] 1.3 评审工程师复核：逐 hunk 审查（对照 I.1–I.7 逐条款，零容忍打回）+ 读数独立复跑（防虚报）+ 变体攻击；REVIEW2.md
  - [x] 1.4 主代理验证：验证序六步（spec「主代理无回退验证」：34 batch → 402 八分片 batch+compare REGRESSIONS=0 → quotation 152/153 零新增 → tests 零新增失败 → IV.2 门禁自检 → 读数汇报）；VERIFICATION.md
  - [x] 1.5 归档 rounds/round1/ + 提交并 push origin main
- [x] Task 2: Round 2 — 表A 语句结构形态对抗（III.2 全名单：If/For/While/Try/TryStar/With/Match/Assert/Raise/Return/Assign/Delete/Import/Global/FunctionDef/ExceptHandler × 深层宿主，优先文档标榜完备者与覆盖矩阵空白格）
  - [x] 2.1 评审工程师：每形态 ≥10 深层/交叉复现（深度 ≥3）+ ≥2 MATCH 负对照，实测深层与浅层产物结构一致（C2 判据）；宣告完备前逐条自查 13 误解（II.7）；站桩回归重放；合规审计；登记新破口（B71+ 续接，锚点+机制+违反条款）；REVIEW.md + test_repros/round2/
  - [x] 2.2 修复工程师（≥2 个不相交破口族时多位并行）：封闭登记破口（I.4 白名单判据 + I.3 推论修复方向 + I.7 注释）；自测 = IV.2 门禁自检清单全过；FIX.md（可多份）
  - [x] 2.3 评审工程师复核：逐 hunk + 读数独立复跑 + 变体攻击；通过/打回；REVIEW2.md
  - [x] 2.4 主代理验证：验证序六步；VERIFICATION.md
  - [x] 2.5 归档 rounds/round2/ + 提交并 push origin main
- [x] Task 3: Round 3 — 表B 表达式形态对抗（III.3 全名单：BoolOp/IfExp/Compare 链/BinOp/UnaryOp/Lambda/推导式族/Call/JoinedStr/Await/Yield/NamedExpr/操作符叶子 32 个 × 嵌套宿主，B1 台账口径重点复核）
  - [x] 3.1 评审工程师：同 2.1 攻击协议（II.7 自查 + 站桩回归 + 合规审计 + Bn 登记）；REVIEW.md + test_repros/round3/（28 探针 241/305、COMPILE_ERROR 3；新登记 B98 分组 boolop 保真 / B99 for 宿主 BoolOp 蒸发；BoolOp 由「完备」降「破口」）
  - [x] 3.2 修复工程师（可多位协同）：封闭登记破口（I.4/I.3/I.7 约束）；自测 = IV.2 门禁自检清单全过；FIX_P1/FIX_P2（B98+B1b 守卫域扩展落 `region_ast_generator.py`、B99 落 `region_analyzer.py`；28 探针 244→248/305，NEWFAIL=0）
  - [x] 3.3 评审工程师复核；REVIEW2.md（打回项 A/B 文档级 → 整改 `3b098f99` 纯文档（AST 恒等）→ §5.5 终审放行；新变体 5 探针 HEAD 46/63 vs 旧码 37/63 零误伤）
  - [x] 3.4 主代理验证：验证序六步；VERIFICATION.md（402 全量 6554/6617、369/402 与基线逐位一致；8 片 compare REGRESSIONS=0；34 集 1505/1568；quotation 152/153；tests 277 passed/2 failed/2 xpassed；IV.2 全过）
  - [x] 3.5 归档 rounds/round3/ + 提交并 push origin main
- [x] Task 4: Round 4 — 表C 31 扩展形态对抗（III.4 全名单：elif 链/for-else/while-else/except\*/match+守卫+8 模式/多上下文 with/try-finally-only/multi_target/augassign/chained_comparison/walrus/keyword_args/star_args/slice/relative_import/star_import/global_nonlocal/fstring_conversion/nested_comprehension/decorator_with_args/async 五件套）
  - [x] 4.1 评审工程师：同 2.1 攻击协议；except\* 检测标准对准 3.11 标记（II.7 第 12 条：CHECK_EG_MATCH/PREP_RERAISE_STAR/is_except_star）；REVIEW.md + test_repros/round4/（20 形态族：13 破口 / 7 完备；新登记 B100–B113；探针 301/338；站桩 6 面 WORSE=0）
  - [x] 4.2 修复工程师（可多位协同）：封闭登记破口；自测 = IV.2 门禁自检清单全过；FIX_G/FIX_R.md（位1 生成层封闭 B100 相对导入层级 + B101 star 导入；位2 识别层封闭 B102 except\* 多 handler + B109 while-else + B103 match 守卫部分）
  - [x] 4.3 评审工程师复核；REVIEW2.md（逐 hunk 合规 PASS、独立复跑 NEWFAIL=0、站桩 WORSE=0、新变体误伤 0、B113 驳回证伪降级维持破口；终审放行）
  - [x] 4.4 主代理验证：验证序六步；VERIFICATION.md（首跑 shard4 回退 → B109 守卫收紧整改 `3eb329d1` → 复跑 402 全量 6554/6617、369/402 与基线逐位一致；8 片 REGRESSIONS=0；34 集 1505/1568；quotation 152/153；tests 277/2/2；IV.2 全过）
  - [x] 4.5 归档 rounds/round4/ + 提交并 push origin main（归档提交 `44d77e72` 已完成；push 已于 round5 归档时补推成功 origin/main → `ae1b06bf`）
- [x] Task 5: Round 5 — 深层嵌套交叉矩阵对抗（覆盖矩阵剩余空白格：形态 × 宿主区域组合，深度 ≥3；重点 = 台账"完备"声明从未被交叉攻击过的组合；C1/C2/C3 逐条款攻击设计）
  - [x] 5.1 评审工程师：交叉矩阵抽样攻击（每空白格 ≥3 探针）+ 站桩回归 + 合规审计 + Bn 登记；REVIEW.md + test_repros/round5/（20 组探针 187/208，attack 165/186、neg 22/22；新登记 B114 模块根未别名点号 import × 序列赋值→幻影 import a.b as a / B115 外层 if 体首 while→条件融合 / B116 函数内裸注解丢弃→局部名退化 LOAD_GLOBAL；同 Bn 存量 5 项；站桩 6 面 WORSE=0；合规全 PASS 新增 0）
  - [x] 5.2 修复工程师（可多位协同）：封闭登记破口（深层才错 = C 条款破坏，按 I.3 推论封闭守卫）；自测 = IV.2 门禁自检清单全过；FIX.md（三破口全封闭：B116 region_ast_generator L2486-2503、B114 三条 import 归约路径、B115 region_analyzer L18196/L19074/L28495/L28899 回边重检收窄判据；三最小复现转 MATCH；34 集 1505/1568 NEWFAIL=0；站桩 WORSE=0）
  - [x] 5.3 评审工程师复核；REVIEW2.md（逐 hunk 合规 PASS、独立复跑一致、变体 32 文件/58 单元 51/58 NEWFAIL=0；终审=有条件放行，B114 path3 else 分支打回 1 项 → 整改 `711dc506`（else 改发 {name:_gi_imp_module,asname:None} + while 宿主同机制修复，r5v5r_b114_in_for/in_while 0/1→1/1 转 MATCH）→ 终审放行、无新残余）
  - [x] 5.4 主代理验证：验证序六步；VERIFICATION.md（402 全量 6554/6617、369/402 与基线逐位一致；8 片 compare REGRESSIONS=0；34 集 1505/1568；quotation 152/153；tests 277 passed/2 failed/2 xpassed；IV.2 全过；落地标记 10 处）
  - [x] 5.5 归档 rounds/round5/ + 提交并 push origin main（归档提交 `ae1b06bf`；push 已补推成功 origin/main → `ae1b06bf`，含 round4/round5 累积提交）
- [x] Task 6: Round 6 — `_identify_*` 十族方法注释合规与算法一致性审计（III.1 锚点逐方法：docstring 六项模板齐全性（I.7）∧ 与代码行为一致性 ∧ C1/C2/C3 条款声明；不一致即打回）
  - [x] 6.1 评审工程师：十族识别方法 + 对应生成方法逐方法审计（六项模板逐项对照代码真实行为；③唯一归属判定/④嵌套处理/⑤入口引用语义与四原则 I.1 对照）+ 站桩回归 + 合规审计；REVIEW.md（识别方法 合规0/打回10——六项齐全但均未声明 C1/C2/C3 条款，以 I.1 四原则收尾；生成方法 合规6/打回9——旧格式缺六项标号+C条款；合计打回19 R6-D1..D10 全属 I.7 形式层；注释↔代码一致性抽查无实质矛盾；站桩 6 面 WORSE=0 与 round5 逐位一致；合规审计新增违反 0；新破口 Bn=0；r6v6_* 证据 + 前缀偏差登记 r6_*→r6v6_*）
  - [x] 6.2 修复工程师（可多位协同，按方法族分派）：注释与代码对齐（以代码真实算法为准修正注释，或以注释声明的正确算法为准修正代码——两者必居其一，禁止含糊；代码修正同样受 I.4 白名单约束）；FIX_A/FIX_B.md（两位并行、涉改文件不相交：识别层 region_analyzer.py 10 方法各增补独立 C1/C2/C3 条款声明 +70；生成层 region_ast_generator.py 9 方法改建为 I.7 六项标号①-⑥ + 独立 C 条款行 +255/-9；纯 docstring，剥 docstring 后两文件 AST_EQUAL 零可执行代码变更；BOM 单头保持；r6v6fixa_*/r6v6fixb_* 证据）
  - [x] 6.3 评审工程师复核：逐方法重审一致性 + 读数复跑；REVIEW2.md（19/19 通过；对抗性核对 6 个跨族攻击点无反例、C 条款声明均经代码实证；独立 AST_EQUAL 两文件 ALL_OK；站桩 6 面 WORSE=0 全 same；合规新增 0；终审放行；r6v6r_* 证据）
  - [x] 6.4 主代理验证：验证序六步；VERIFICATION.md（402 全量 6554/6617、369/402 与基线逐位一致；8 分片 compare REGRESSIONS=0；34 集 1505/1568；quotation 152/153；tests 277 passed/2 failed/2 xpassed；IV.2 全过；落地标记 analyzer 10 + generator 23）
  - [x] 6.5 归档 rounds/round6/ + 提交并 push origin main
- [x] Task 7: Round 7 — 已封闭守卫族与已复审破口全量深度外推重放（站桩回归强化轮：B2/B3/B4 守卫族 + B1b/B6–B40/B45/B54/B55/B66–B68 已封闭面，外推变体 + 收缩变体双向攻击）
  - [x] 7.1 评审工程师：守卫判据面重攻击（三方向 47 探针 attack 114/122 + neg 18/18 全 MATCH；站桩 6 面 WORSE=0 持平 round6；登记守卫缺口型新破口 4 项 B117–B120——编号勘误：初稿误用 B77–B80 与台账冲突，已按最高号 B116 续接重编号；B3 族三方向封闭成立；合规新增违反 0）；REVIEW.md + test_repros/round7/ r7v7_*/n7v7_*（零覆盖既有 61 tracked）
  - [x] 7.2 修复工程师（单位续作——前任配额中断，四守卫已在途，续作核实并收紧 3 处过火守卫）：四破口全封闭（唯 core 改动 region_ast_generator.py +516/-6：B117 then 臂吸收守卫+else-continue 尾区域前置守卫+新谓词 _if_region_is_loop_body_tail、B118 else-break 出口边显式认领 orelse=[Break]、B119 try 体镜像守卫+回边释放用户语句载体判据+帧尾释放封闭、B120 祖先汇合块守卫）；7 复现全 MATCH；攻击面 122/122(+8)；站桩 6 面 WORSE=0 且 round2face 235/251(+1)、residual 418/446(+1)；34 集 1505/1568 NEWFAIL=0；IV.2 全过；FIX.md 代码已落地
  - [x] 7.3 评审工程师复核；REVIEW2.md（终判通过打回 0：逐 hunk 19 处判据全 I.4 白名单、落地锚点 20/20 grep 实证、读数独立复跑一致、变体 r7v7r_* B118 7/7·B120 7/7·B119 9/9 不误伤、B117 6/7 浅层 while 宿主基线 FAIL 转 MATCH 正向生效；新登记 B121 while 头形成误归约——基线同败确证存量缺口非本批回归，移交 Round 8）
  - [x] 7.4 主代理验证：验证序六步；VERIFICATION.md（402 全量 6554/6617、369/402 与基线逐位一致；8 分片 compare REGRESSIONS=0 IMPROVED=0；34 集 1505/1568；quotation 152/153；tests 277/2/2 基线名单；IV.2 全过 R7FIXDBG 清零/落地标记 analyzer10+generator24；轮门禁达成=4 破口封闭+3 读数改善）
  - [x] 7.5 归档 rounds/round7/ + 提交并 push origin main
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
