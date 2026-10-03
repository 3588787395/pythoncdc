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
- [x] Task 4: Round 4 — Match + match_case 8 模式（value/singleton/sequence/mapping/class/or/capture/star）形态对抗
  - [x] 4.1 评审工程师：Match 区域全链对抗 = 8 模式 × 组合面（多 case、守卫、通配 `_`、or 模式、star、嵌套 match/loop/try 内 match）+ 负对照；Round 3 残留复验（B10-R r3_34 1/2、B11-R2 or4_and2 MISMATCH 登记读数不变差）；登记新破口；REVIEW.md + test_repros/round4/
  - [x] 4.2 修复工程师：按区域归约算法封闭登记破口（docstring 三要素 + C1/C2/C3 同步）；B10-R/B11-R2 若具备判据形态一并处理；自测零回退（哨兵 = quotation/jq/quote/tlb/risk + round1-3 抽验）；FIX.md
  - [x] 4.3 评审工程师复核：逐 hunk 审查守卫判据合规（算法驱动/嵌套无感/完备精简，零容忍打回）；REVIEW2.md
  - [x] 4.4 主代理验证：402 全量 8 分片重生成+batch+compare = REGRESSIONS=0；小测试集 34 worse=0；quotation 152/153；tests/ 零新增失败；VERIFICATION.md
  - [x] 4.5 归档 rounds/round4/ + 提交并 push
- [x] Task 5: Round 5 — 推导式族（List/Set/Dict/GenExp + 多重 for 嵌套推导）形态对抗
  - [x] 5.1 评审工程师：推导式全链对抗 = 16 文件 192 单元 180 MATCH/12 MISMATCH（93.75%）+ r5_07 compile_error 11 单元不可比 + 负对照 n5_01 7/7，wiki「推导式完备」声明证伪；Round 4 残留五项复验全持平（rv4_12 1/4、rv4_13 2/4、rv4_16 2/4、rv4_17 2/4、r4_04 4/6）；登记 B20（跨 clause 过滤静默丢失）+ B21（解包 target 拍平/星号坍缩）+ B22（walrus 幻影迭代目标，P0）+ B23（async 组合坍缩）+ B24（try finally 包 return 推导式被剥除）+ B25（lambda 默认值丢失双杀，P0）；REVIEW.md + test_repros/round5/
  - [x] 5.2 修复工程师：批次一（7e09e36d）B20/B21/B22 同根名袋封闭（_parse_target_store_sequence 结构解析 + B20 clause 过滤窗 + 目标渲染统一委托）；批次二（45864cc5）B25（arguments dict 经 _args_dict 挂载 + flags 位重建）+ B23（闭包过滤状态机 + _find_async_clause_heads 协议块 + 统一 clause 装配 + PUSH_NULL 双槽补消费）+ B24（R9 收窄 + 栈深模拟三重判据）；docstring 三要素 + C1/C2/C3 同步；自测零回退（哨兵 round5 16 支 + site-packages 5 支 + round1-4 抽验）；FIX.md 两批次
  - [x] 5.3 评审工程师复核：终判放行 = 20 hunk 全合规（无白名单/阈值/跨层/self 状态/少发射）+ 读数复跑 21/21 支零虚报 + 变体攻击 6 探针 61 单元 57 MATCH（3 失败经修复前树证实为既有缺口非回归）；新破口 B26（async GenExp 作实参）/B27（嵌套 try 包 return 剥除）/B28（纯 vararg/kwarg lambda）登记；REVIEW2.md
  - [x] 5.4 主代理验证：402 全量 8 分片重生成+batch+compare = REGRESSIONS=0，units 6554/6617（99.05%）文件 369/402 持平；小测试集 34 REGRESSIONS=0（1505/1568）；quotation 152/153 零新增；tests 257 passed/2 failed——test_BND_21_walrus 由 failed 转 passed（B22 真身增益），零新增失败；VERIFICATION.md
  - [x] 5.5 归档 rounds/round5/ + 提交并 push
- [x] Task 6: Round 6 — With/AsyncWith + async 五件套（def/for/with/await/yield from）形态对抗
  - [x] 6.1 评审工程师：16 文件可比 95 单元 66/95（69.47%）+ 3 文件 compile_error，声明证伪；登记 B29–B35 七破口（P0×3/P1×2/P2×2）；Round 5 残留复验偏差 0；合规审计 10 项全过；REVIEW.md + test_repros/round6/
  - [x] 6.2 修复工程师：四批封闭 B29/B30/B32/B33/B34b/B34c/B35（fbfc2e7b/1c059d1b/4cd2a9f6/30468033），round6 全清 115/115；FIX.md
  - [x] 6.3 评审工程师复核：读数复跑 21/21 面零虚报但终判打回（A10 BOM 红线/A8 静默移除/A9 破损插桩/A7 四方法缺 C 条款）+ 变体攻击 7 探针 29 单元 18 MATCH 登记 B37–B41 五破口（11 单元，全归因既有缺口）；打回修复 4 项封闭（a6e33367：BOM 恢复/LOOP_BACK_EDGE 方案A 复位/插桩清零/条款补齐）；复验放行（REVIEW2.md §7/§8）
  - [x] 6.4 主代理验证：批次一 402 重生成 402/402 + 8 分片 compare = REGRESSIONS=4 回退拦截（strategy/commission/slippage/dockerspawner）→ 修复工程师三处算法内修复 R6-F1/F1b/F2（75ca08bd，with-in-try 协同占用可达性/多管理器抑制出口/await 链头资格）→ 终验全部 8 分片 REGRESSIONS=0，**6554/6617（99.05%）369/402 与 Round 5 终态逐位持平**；小测试集 34 = 1505/1568 REGRESSIONS=0；quotation 152/153 零新增；tests 257 passed/2 failed/5 xpassed 基线一致；VERIFICATION.md
  - [x] 6.5 归档 rounds/round6/ + 提交并 push
- [ ] Task 7: Round 7 — Ternary + 链式比较 + 表达式面 BoolOp 组合形态对抗
  - [x] 7.1 评审工程师：16 文件 128 单元 96 MATCH/32 MISMATCH（75%）伪完备证伪；登记 B42–B51 十族（32 单元，全归因既有缺口）+ R7-O1 打回项 + R7-O2 遗留插桩观察；Round 6 残留复验零漂移持平；REVIEW.md + 16 探针
  - [x] 7.2 修复工程师：批次一（c0ab03c1，子代理三次基础设施故障后主代理接管）= R7-O1 短路恢复 + R7-O2 插桩清零 + B45 封闭 2/2 + B42 封闭 6/9（段收集含最内层 cond 前缀/后向链扩展/全链标记/return 上下文放行/单链受限/全空段守卫）；r7 96→104/128；残留 B42 3 单元 + B43/B44/B46–B51 如实登记交 Round 8；FIX.md
  - [x] 7.3 评审工程师复核：终判放行 = 逐 hunk 14/14 PASS + 判据面与 FIX.md 逐条相符 + 读数复跑零虚报 + 变体攻击 4 探针 12/15 零回归；新登记 B52/B53（均 pre-fix worktree 证实既有缺口）；REVIEW2.md
  - [x] 7.4 主代理验证：402 全量 8 分片重生成+batch+compare = 6554/6617（99.05%）369/402 **REGRESSIONS=0**；小测试集 34 = 1505/1568 REGRESSIONS=0 IMPROVED=0；quotation 152/153 零新增；tests 257 passed/2 failed/5 xpassed 基线一致；VERIFICATION.md
  - [x] 7.5 归档 rounds/round7/ + 提交并 push（9fb15e5a 复核放行后归档推送）
- [ ] Task 8: Round 8 — 表A 结构形态扫尾（Return/Pass/Delete/Assign 族、Assert、Raise）+ sstrict 缺陷单元对抗抽样
  - [x] 8.1 评审工程师（0c0642ab）：表A 形态全链对抗 = Return 位形态（多 return/嵌套 return/生成器 return/finally return）× Pass/Delete（del 局部/下标/属性/切片）× Assign 族（链式赋值/多目标/解包/星号解包/augassign 全算子）× Assert（带消息/不带/优化 -O 形态）× Raise（裸 raise/reraise/异常实例/异常类+消息/from 语法）× 深层宿主（if/while/for/try/with/match 内）+ Round 7 残留复验（B42 残留 3 单元 + B43/B44/B46/B47/B48/B49/B50/B51 + B52/B53 登记读数不变差）+ 负对照 ≥2；算法合规审计（在途变更 = 零）；登记新破口（B54+）；REVIEW.md + test_repros/round8/
  - [x] 8.2 修复工程师（5aff0e32）:按区域归约算法封闭登记破口（判据 = 同层结构事实，docstring 三要素 + C1/C2/C3 同步，BOM 校验纳入自测）；Round 7 残留（B42 3 单元/B43/B44/B46–B53）若具备判据形态按交接单认领；自测零回退（哨兵 = round6 115/115 + round7 r7 面 104/128 + rv6/rv7 持平 + 六哨兵 + option_account 35/35）；FIX.md。主代理不得代笔实现，子代理故障时重试派发或如实上报
  - [x] 8.3 评审工程师复核（612cf0f2）：终判放行 10/10 hunk + 变体 +7 补强 + B63/B64/B65 登记；REVIEW2.md
  - [x] 8.4 主代理验证：402 全量 8 分片重生成+batch+compare = 6554/6617（99.05%）369/402 REGRESSIONS=0；小测试集 34 REGRESSIONS=0 IMPROVED=0；quotation 152/153；tests 257 passed/2 failed/5 xpassed 基线一致；VERIFICATION.md
  - [x] 8.5 归档 rounds/round8/ + 提交并 push
- [ ] Task 9: Round 9 — B2/B3/B4 守卫族回归攻击 + 前八轮已封闭破口复验（防回归）
  - [ ] 9.1 评审工程师：B2/B3/B4 守卫族（守卫判据面重攻击：守卫适用形态变体/守卫边界外形态/守卫互斥组合）+ 前八轮已封闭破口复验（B1b/B6/B8/B9/B10/B11/B20–B35/B54/B55 逐封闭声明重放登记探针，读数不得变差）+ Round 8 残留复验（B42×3/B43/B44/B46/B48/B56–B62/B63–B65 登记面持平）+ 负对照；算法合规审计；登记新破口（B66+）；REVIEW.md + test_repros/round9/
  - [ ] 9.2 修复工程师：封闭本轮登记破口与复验发现的回归（判据 = 同层结构事实，docstring 三要素 + C1/C2/C3 同步）；自测零回退（哨兵 = round6/round7/round8 攻击面全 MATCH 面禁变差 + 六哨兵 + option_account）；FIX.md
  - [ ] 9.3 评审工程师复核：逐 hunk 审查（零容忍打回）；REVIEW2.md
  - [ ] 9.4 主代理验证：402 全量 8 分片重生成+batch+compare = REGRESSIONS=0；小测试集 34；quotation 152/153；tests/；VERIFICATION.md
  - [ ] 9.5 归档 rounds/round9/ + 提交并 push
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
