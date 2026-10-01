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
- [ ] Task 2: Round 2 — Try/ExceptHandler/try-finally 形态对抗（含孤儿 finally 帧守卫）
- [ ] Task 3: Round 3 — For/While + for-else/while-else（`_find_loop_else` + clamp 守卫）形态对抗
- [ ] Task 4: Round 4 — Match + match_case 8 模式（value/singleton/sequence/mapping/class/or/capture/star）形态对抗
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
