# Tasks

> 目标：对 10 类区域执行 10 遍「架构工程师 + 修复工程师」迭代，共 100 轮。
> 每轮：架构分析 → 修复实施 → 回归测试 → commit + push。
> 所有命令执行不得超过 300 秒。
> 每轮必须提交并 push 到远程。

## 区域顺序（每遍）

1. IF — `tests/exhaustive/if_region/`
2. LOOP — `tests/exhaustive/while_loop/` + `for_loop/`
3. TRY — `tests/exhaustive/try_except/`
4. WITH — `tests/exhaustive/with_region/`
5. MATCH — `tests/exhaustive/match_region/`
6. ASSERT — `tests/exhaustive/assert/` + nook assert
7. BOOLOP — `tests/exhaustive/bool_op/` + `boolop/`
8. TERNARY — `tests/exhaustive/ternary/`
9. CHAINED_COMPARE — 散布于 if/assert/boolop
10. SEQUENCE — `tests/exhaustive/basic/` + L1_basic

## 每轮任务模板

- [ ] T1: 架构工程师分析该区域代码（输出 test_findings.md）
  - 阅读 `_identify_*_regions` 与 `_generate_*` 方法
  - 找出问题点 + 算法根因 + 修复策略
- [ ] T2: 修复工程师实施修复（输出 fix_report.md）
  - 依照区域归约算法完善程序，增强通用性
  - 不引入反模式
- [ ] T3: 回归测试（300s 内，不退化）
- [ ] T4: commit + push 到 origin/main

## 遍 1 (Pass 1)

- [x] Pass1-IF: 第 1 遍 IF 区域（轮 1）— T1/T2/T3 完成（test_findings.md + fix_report.md 已生成，IF/BOOLOP/TERNARY 三区域回归无退化）；T4 commit+push 待用户指令
- [x] Pass1-LOOP: 第 1 遍 LOOP 区域（轮 2）— T1/T2/T3 完成（test_findings.md + fix_report.md 已生成；删除死代码 + 新增 `_is_owned_by_other_region`/`_is_continue_recheck_fake_loop` 守卫并消除 3 个后处理补丁；LOOP 79p/0f/79、TRY 80p/0f/80、IF 79p/1f/80 三区域回归无退化；反模式自检通过）；T4 commit+push 待用户指令
- [ ] Pass1-TRY: 第 1 遍 TRY 区域（轮 3）
- [x] Pass1-WITH: 第 1 遍 WITH 区域（轮 4）— T1/T2/T3 完成（test_findings.md + fix_report.md 已生成；3 项反模式消除完成；WITH 80p/0f/80、LOOP 79p/0f/79、TRY 80p/0f/80 三区域回归无退化；反模式自检通过）；T4 commit+push 待用户指令
- [ ] Pass1-MATCH: 第 1 遍 MATCH 区域（轮 5）
- [ ] Pass1-ASSERT: 第 1 遍 ASSERT 区域（轮 6）
- [ ] Pass1-BOOLOP: 第 1 遍 BOOLOP 区域（轮 7）
- [ ] Pass1-TERNARY: 第 1 遍 TERNARY 区域（轮 8）
- [ ] Pass1-CC: 第 1 遍 CHAINED_COMPARE 区域（轮 9）
- [ ] Pass1-SEQ: 第 1 遍 SEQUENCE 区域（轮 10）

## 遍 2-10 (Pass 2-10)

结构与遍 1 相同，每遍覆盖 10 个区域。共 9 遍 × 10 区域 = 90 轮。

## 验证标准

每轮完成时必须满足：
1. test_findings.md 与 fix_report.md 已生成
2. 该区域测试集无退化（通过数不下降）
3. 已 commit + push 到 origin/main
4. 无反模式（_fix_/_merge_/_patch_ 等前缀、硬编码深度上限）

每遍完成时必须满足：
1. 10 个区域全部完成
2. 共 10 次 commit + push
3. 全测试集无退化

10 遍全部完成时必须满足：
1. 共 100 次 commit + push
2. 全测试集通过率 ≥ 起始基线
3. 算法 4 原则持续 FULLY COMPLIANT
