# Tasks

目标：对 wiki 总纲 §5 台账已判"完备"的 127 形态完成对抗性评审与算法完善；破口清零（128/128）；树中一切变更（含在途未评审代码）过审；全量 402 无回退。
角色：主代理 = 调度 + 阶段提交 + 全量验证 + push（不执行实现任务）；评审工程师 = 对抗攻击 + 合规审计（子代理）；修复工程师 = 算法修复 + 注释三要素（子代理）。
纪律：每轮独立文件夹；调用子代理前必须本地提交；每轮 ≥1 破口封闭或 ≥1 读数改善，否则禁止下一轮；每轮提交并 push；所有命令 ≤300s；禁止手改 `*OK.py`。

- [ ] Task 0: 规范就位与快照提交（主代理）
  - [ ] 0.1 创建本规范三件套 + 小测试集索引 `baseline/failing_index.json`（34 pyc）
  - [ ] 0.2 快照提交：在途未评审变更（region_ast_generator.py +419 行、再生成的 OK.py 与 repro 产物）+ 本规范，一笔入库存证
- [ ] Task 1: Round 1 — BoolOp 破口族（B1）+ If 形态对抗
  - [ ] 1.1 评审工程师：审计在途变更 `[R76-A1/A2]`/`[R75 fix1]` 的 C1/C2/C3 与算法合规；攻击 BoolOp（含 B1a 嫁接、B1b or 臂第二丢弃入口）与 If 形态，≥10 复现 + ≥2 负对照，`test_repros/round1/` + `rounds/round1/REVIEW.md`
  - [ ] 1.2 修复工程师：按评审结论算法修复（含 B1b 定位封闭），注释三要素同步，自测复现全 MATCH + 小测试集无回退，`rounds/round1/FIX.md`
  - [ ] 1.3 评审工程师复核修复（通过/打回循环）
  - [ ] 1.4 主代理验证：小测试集 → 402 分片 + compare REGRESSIONS=0 → quotation.pyc → tests/ 相关测试；归档 + 提交并 push
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
