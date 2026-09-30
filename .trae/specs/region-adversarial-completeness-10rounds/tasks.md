# Tasks

目标：site-packages 下 402 个 pyc 全部反编译 success（pyc_verify.py 单元全 Equal），同目录生成 `<name>OK.py`。
每轮（round76–round85）= 主代理本地提交 → 测试工程师（取 1 个 pyc → ≥10 最小复现 + 根因）→ 修复工程师（区域归约算法修复 + 注释三要素）→ 评审工程师（独立对抗审查，优先台账已判完备形态）→ 主代理验证（靶 pyc success → quotation.pyc → 批量回归 REGRESSIONS=0）→ 归档 → 提交并 push。
纪律：每轮至少解决 1 个 pyc，未解决禁止下一轮；所有命令 ≤300s；禁止手改 `*OK.py`；逐步进行禁止投机取巧。

- [ ] Task 0: 基线与规范就位（主代理，round76 启动前置）
  - [ ] SubTask 0.1: 创建 `.trae/specs/region-adversarial-completeness-10rounds/rounds/` 与 `baseline/` 目录；本地提交（调用子代理前必须提交）
  - [ ] SubTask 0.2: 用 `scripts/pyc_verify.py batch` 分片跑 402 基线（8 片 × ~50 文件，每片 ≤300s），产出基线报告与失败文件清单（= 小测试集索引 `baseline/failing_index.json`）
  - [ ] SubTask 0.3: 盘点 12 个 `_identify_*` 识别方法注释三要素（识别条件/归约方式/AST 映射）现状缺口表，存 `baseline/comment_gaps.md`

- [ ] Task 1: Round 76 — B1a 落地 + 靶 quote.pyc（当前最差 88.89%）
  - [ ] SubTask 1.1: 测试工程师：`pyc_verify.py single fly/data/quote.pyc` → 失败单元 dis 对照 → ≥10 最小复现 + ≥2 负对照（test_repros/round76/）→ ANALYSIS.md（根因 × C 条款归类）
  - [ ] SubTask 1.2: 修复工程师：落地 B1a 嫁接方案（jqop1.json：`_graft_pending_operand` + `_contains_identity`），触及方法注释同步三要素 + C1/C2/C3 声明；自测复现全 MATCH
  - [ ] SubTask 1.3: 评审工程师：对抗审查 BoolOp/If 路径 C1/C2/C3 合规 + 台账完备形态轮换抽查 ≥2（深层嵌套探针）；结论必须「通过」
  - [ ] SubTask 1.4: 主代理验证：quote.pyc 达 success（OK.py 程序生成）→ quotation.pyc 验证 → 批量回归分片 + compare REGRESSIONS=0 → 现有区域测试套件
  - [ ] SubTask 1.5: 归档 rounds/round76/ + 提交并 push（每轮必须）

- [ ] Task 2: Round 77 — B1b 定位封闭 + 当轮最差失败 pyc
  - [ ] SubTask 2.1: 测试工程师：neg75_jqcond2 复现扩展（≥10 复现）+ 当轮靶文件分析（失败清单最低一致率者）
  - [ ] SubTask 2.2: 修复工程师：定位并封闭语句上下文 or 臂第二丢弃入口（`_build_boolop_expression` 家族），注释同步
  - [ ] SubTask 2.3: 评审工程师：对抗审查（含 B1 双入口接回后的 jq_trans_module 65/65 保持验证）
  - [ ] SubTask 2.4: 主代理验证（靶 pyc success → quotation → 批量回归无回退）+ wiki §8.2 复审六步（B1 状态推进）
  - [ ] SubTask 2.5: 归档 rounds/round77/ + 提交并 push

- [ ] Task 3: Round 78 — 失败清单最差 pyc（参考 realtime_event_source.pyc 91.67%）
  - [ ] SubTask 3.1: 测试工程师（复现+根因）/ 修复工程师（算法修复+注释）/ 评审工程师（对抗审查+完备形态抽查）
  - [ ] SubTask 3.2: 主代理验证 + 归档 rounds/round78/ + 提交并 push

- [ ] Task 4: Round 79 — 失败清单最差 pyc（参考 order_api.pyc 94.12%）
  - [ ] SubTask 4.1: 三工程师同构流程（复现 ≥10 → 算法修复 → 对抗评审通过）
  - [ ] SubTask 4.2: 主代理验证 + 归档 rounds/round79/ + 提交并 push

- [ ] Task 5: Round 80 — 失败清单最差 pyc（参考 trade_live_broker.pyc 94.12%，13 残留单元）
  - [ ] SubTask 5.1: 三工程师同构流程
  - [ ] SubTask 5.2: 主代理验证 + 归档 rounds/round80/ + 提交并 push

- [ ] Task 6: Round 81 — 失败清单最差 pyc（参考 risk_calculation.pyc 94.29%）
  - [ ] SubTask 6.1: 三工程师同构流程
  - [ ] SubTask 6.2: 主代理验证 + 归档 rounds/round81/ + 提交并 push

- [ ] Task 7: Round 82 — 失败清单最差 pyc（参考 real_quote.pyc 95.45%，get_tick_direction 等）
  - [ ] SubTask 7.1: 三工程师同构流程
  - [ ] SubTask 7.2: 主代理验证 + 归档 rounds/round82/ + 提交并 push

- [ ] Task 8: Round 83 — 失败清单最差 pyc（参考 klinedata.pyc 95.56%）
  - [ ] SubTask 8.1: 三工程师同构流程
  - [ ] SubTask 8.2: 主代理验证 + 归档 rounds/round83/ + 提交并 push

- [ ] Task 9: Round 84 — 失败清单最差 pyc（参考 api_base.pyc 96.00%）+ 严格尺失败清单清零推进
  - [ ] SubTask 9.1: 三工程师同构流程
  - [ ] SubTask 9.2: 主代理验证 + 归档 rounds/round84/ + 提交并 push

- [ ] Task 10: Round 85 — 全量收敛与台账终审
  - [ ] SubTask 10.1: 三工程师流程处理剩余失败文件（可多靶，每靶同样 ≥10 复现门）
  - [ ] SubTask 10.2: 主代理全量终验：402/402 success 分片验证 + compare 无回退 + 现有区域测试全绿
  - [ ] SubTask 10.3: 台账复审六步全量执行（syntax_coverage.py 重跑、128/128 占比重算、wiki log）
  - [ ] SubTask 10.4: 归档 rounds/round85/ + 终提交并 push
  - [ ] SubTask 10.5: 若仍有失败文件，按同一规范续轮（round86+）直到 402/402（用户验收后续批准）

注：Task 3–9 靶文件按「每轮启动时失败清单中一致率最低者」动态确定（上述文件名为 round75 交接时参考序）；评审工程师每轮台账完备形态轮换抽查 ≥2 个，10 轮累计覆盖 ≥20 个形态。

# Task Dependencies
- Task 1–10 顺序依赖（前一轮门禁未过禁止开启下一轮）
- 每轮内：测试 → 修复 → 评审 → 验证 → 提交 push 串行
- SubTask 10.3 依赖 SubTask 10.2（终验通过才重算占比）
- 10 轮后未全量收敛时，Task 10.5 续轮依赖用户确认
