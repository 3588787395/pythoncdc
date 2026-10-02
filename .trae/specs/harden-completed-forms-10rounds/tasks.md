# Tasks

目标：对 wiki 总纲 §5 台账已判"完备"的 127 形态完成对抗性评审与算法完善；破口清零（128/128）；树中一切变更（含在途未评审代码）过审；全量 402 无回退。
角色：主代理 = 调度 + 阶段提交 + 全量验证 + push（不执行实现任务）；评审工程师 = 对抗攻击 + 合规审计（子代理）；修复工程师 = 算法修复 + 注释三要素（子代理）。
纪律：每轮独立文件夹；调用子代理前必须本地提交；每轮 ≥1 破口封闭或 ≥1 读数改善，否则禁止下一轮；每轮提交并 push；所有命令 ≤300s；禁止手改 `*OK.py`。

- [ ] Task 0: 规范就位与快照提交（主代理）
  - [ ] 0.1 创建本规范三件套 + 小测试集索引 `baseline/failing_index.json`（34 pyc）
  - [ ] 0.2 快照提交：在途未评审变更（region_ast_generator.py +419 行、再生成的 OK.py 与 repro 产物）+ 本规范，一笔入库存证
- [x] Task 1: Round 1 — BoolOp 破口族（B1）+ If 形态对抗
  - [x] 1.1 评审工程师：审计在途变更 `[R76-A1/A2]`/`[R75 fix1]` 的 C1/C2/C3 与算法合规（5/5 通过）；攻击 BoolOp/If 形态：22 攻击目标 = 14 MISMATCH + 11 MATCH（含 3 负对照），`test_repros/round1/` 102 文件 + `rounds/round1/REVIEW.md`
  - [x] 1.2 修复工程师一：B1b 核心封闭（region_analyzer.py 五臂 A/B/B2/C/D/E，or 裸尾续接判据）；修复工程师二：B6 四上下文封闭（3 文件 7 处）；注释三要素同步；自测复现全 MATCH + 小测试集无回退；FIX.md/FIX_B6.md
  - [x] 1.3 评审工程师复核：两批放行（B6 限定表述=浅层封闭）；新破口 B7 登记（基线既有，交 Round 2）；rv_01..10 深嵌套探针 7 MATCH/3 MISMATCH（均基线既有）；REVIEW2.md
  - [x] 1.4 主代理验证：402 全量 8 分片重生成+batch+compare = **6554/6617（99.05%，+8）文件 369/402（+1）REGRESSIONS=0**；回退拦截 1 单元（risk_calculation get_daily_summary，根因=c53df077 在途 R76 剥离误触发，修复归零后 8 片复跑）；quotation 152/153 零新增；tests/ 零新增失败（3 失败基线既有）；小测试集 34 文件 worse=0 improved=3；VERIFICATION.md
  - [x] 1.5 归档 rounds/round1/ + 提交并 push（每轮必须）
- [x] Task 2: Round 2 — Try/ExceptHandler/try-finally/except* 形态对抗（含孤儿 finally 帧守卫）
  - [x] 2.1 评审：Round1 修复守卫在异常语料 5/5 通过零回退；攻击 12 MISMATCH/8 MATCH 全合成命中；B8 登记（except* 首 handler 类型丢弃，负对照翻案，台账 TryStar 判定降格）+ B9（异常区域包裹混合链）+ R2-O2 白名单违规；REVIEW.md
  - [x] 2.2 修复：B8 封闭（帧前缀剔除 4/4 MATCH）+ R2-O2 结构性移除（_find_handler_type_load）+ B9 装配层豁免（r2_08 3/3）；消费层四单元/r2_04/06/14/B7 登记立项；FIX.md
  - [x] 2.3 评审复核：放行无打回（帧前缀不可伪造实证 0/35、零回退抽验 13/13）；R2-NEW-1/2 登记；REVIEW2.md
  - [x] 2.4 主代理验证：8 片 REGRESSIONS=0、units 6554/6617（99.05%）文件 369/402 持平（B8/B9 真身零增益零回退、增益在合成对抗面 5 处改善）；quotation 152/153；tests 零新增失败；VERIFICATION.md
  - [x] 2.5 归档 rounds/round2/ + 提交并 push
- [x] Task 3: Round 3 — For/While + for-else/while-else（`_find_loop_else` + clamp 守卫）形态对抗
  - [x] 3.1 评审：任务A 5 项审计（2 通过/1 有条件/2 打回）；对抗 14 探针 77 单元 56/77（21 MISMATCH/8 文件）+ 负对照 n3_01/n3_02 各 5/5；B10 登记（loop-else×break 证据链失效族 15 单元/6 文件）+ B11 登记（while 混合链非名操作数装配灾难 4 单元浅层即败，B6/B7 声明降格）+ B1b 扩充 r3_31 + R3-O1/O2 观察；登记项复验 8/8 持平零回退；REVIEW.md
  - [x] 3.2 修复一批次（5f26202c）：B10 收尾 5/5 单元 = FIX-1 for_iter_exit 前驱扫描补 break 证据 + FIX-3 纯跳转 else 判定收窄 + FIX-2a/2b 落点放行（判据=_post_break_blocks 搁置台账）+ FIX-4 双 Break 守卫 + FIX-5 else 桩→Continue + FIX-6 祖先循环落点子区域抑制；quotation 回归自纠（152→151→152/153）；R3DBG 插桩清零；FIX.md
  - [x] 3.3 修复二批次（95046711）：B11 4/4（跨类调用 AttributeError 改调 + 祖先循环所有权判据 + or 尾多成员续接 + 残链超越替换集合判据 + or-前缀 or_left 续接）+ B1b 2/2（loop-else 认领豁免 :27827）；B6/B7 降格表述落实；FIX2.md
  - [x] 3.4 评审复核 REVIEW2.md：21 单元复验 72/72 全 MATCH 属实；打回 3 项（R2-1 BOM 剥离、R2-2 守卫面宽于声明、B11-R/B10-R 残留）
  - [x] 3.5 打回修复（b81a0046）：R2-1 BOM 字节级恢复 efbbbf + R2-2 仅 LoopRegion 祖先豁免收窄对齐声明 + B11-R 封闭（r3_33 4/4，FIX-B11c-3 fall-through 前驱反向收集）+ B10-R 精确登记（机制勘误 :18370 内联面，折叠面守卫 :4573-4602）；评审复验 §6 四项全通过放行
  - [x] 3.6 主代理验证：8 片 REGRESSIONS=0，units 6554/6617（99.05%）文件 369/402；小测试集 34 worse=0 improved=3；quotation 152/153 零新增；tests 256 passed/3 failed 基线既有零新增；VERIFICATION.md
  - [x] 3.7 归档 rounds/round3/ + 提交并 push
- [ ] Task 4: Round 4 — Match + match_case 8 模式（value/singleton/sequence/mapping/class/or/capture/star）形态对抗
  - [ ] 4.1 评审工程师：Match 区域全链对抗 = 8 模式 × 组合面（多 case、守卫、通配 `_`、or 模式、star、嵌套 match/loop/try 内 match）+ 负对照；Round 3 残留复验（B10-R r3_34 1/2、B11-R2 or4_and2 MISMATCH 登记读数不变差）；登记新破口；REVIEW.md + test_repros/round4/
  - [ ] 4.2 修复工程师：按区域归约算法封闭登记破口（docstring 三要素 + C1/C2/C3 同步）；B10-R/B11-R2 若具备判据形态一并处理；自测零回退（哨兵 = quotation/jq/quote/tlb/risk + round1-3 抽验）；FIX.md
  - [ ] 4.3 评审工程师复核：逐 hunk 审查守卫判据合规（算法驱动/嵌套无感/完备精简，零容忍打回）；REVIEW2.md
  - [ ] 4.4 主代理验证：402 全量 8 分片重生成+batch+compare = REGRESSIONS=0；小测试集 34 worse=0；quotation 152/153；tests/ 零新增失败；VERIFICATION.md
  - [ ] 4.5 归档 rounds/round4/ + 提交并 push
- [ ] Task 5: Round 5 — 推导式族（List/Set/Dict/GenExp + 多重 for 嵌套推导）形态对抗
- [ ] Task 6: Round 6 — With/AsyncWith + async 五件套（def/for/with/await/yield from）形态对抗
- [ ] Task 7: Round 7 — Ternary + 链式比较 + 表达式面 BoolOp 组合形态对抗
- [ ] Task 8: Round 8 — 表A 结构形态扫尾（Return/Pass/Delete/Assign 族、Assert、Raise）+ sstrict 缺陷单元对抗抽样
- [ ] Task 9: Round 9 — B2/B3/B4 守卫族回归攻击 + 前八轮已封闭破口复验（防回归）
- [ ] Task 10: Round 10 — 终审
  - [ ] 10.1 全台账 127 形态对抗覆盖汇总 + 残留破口处理
  - [ ] 10.2 主代理全量终验（402 分片 + compare + quotation + tests/）
  - [ ] 10.3 wiki §8.2 复审六步全量执行：syntax_coverage.py 重跑、占比重算、log 记录
  - [ ] 10.4 终归档 + 提交并 push

注：每轮内部流程同构 = 评审攻击 → 修复 → 评审复核 → 主代理验证 → 归档 push；轮与轮之间形态不重复（round9 回归攻击除外）。

# Task Dependencies
- Task 1–10 严格顺序依赖（前一轮门禁未过禁止开启下一轮）
- 每轮内：评审 → 修复 → 复核 → 验证 → push 串行
- Task 10.3 依赖 10.2 终验通过
