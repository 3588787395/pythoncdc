# 验证清单

> 目标：10 遍 × 10 区域 = 100 轮双工程师迭代，每轮 commit + push。
> 当前状态：待执行

## 通用约束（每轮检查）

- [ ] G1 命令执行时间 ≤ 300 秒
- [ ] G2 每轮 commit + push 到 origin/main
- [ ] G3 无反模式（_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_ 前缀）
- [ ] G4 无硬编码深度上限（`grep "depth > [0-9]"` 0 结果）
- [ ] G5 该区域测试集无退化
- [ ] G6 test_findings.md 与 fix_report.md 已生成

## 遍 1 (Pass 1)

- [x] P1-IF 第 1 遍 IF 区域完成 (commit c5f18b8)（test_findings.md + fix_report.md 已生成；IF/BOOLOP/TERNARY 回归无退化；无反模式；commit+push 待用户指令）
- [x] P1-LOOP 第 1 遍 LOOP 区域完成（test_findings.md + fix_report.md 已生成；编译通过；LOOP/TRY/IF 三区域回归无退化；3 个后处理补丁 + 死代码已消除；无禁止前缀新增、无硬编码深度上限；commit+push 待用户指令）
- [ ] P1-TRY 第 1 遍 TRY 区域完成
- [x] P1-WITH 第 1 遍 WITH 区域完成（test_findings.md + fix_report.md 已生成；编译通过；WITH 80p/0f/80、LOOP 79p/0f/79、TRY 80p/0f/80 三区域回归无退化；3 项反模式消除：magic number +1000 → 空块跳过、5 处 inline 5-元组 → ASYNC_WITH_SEND_LOOP_OPS 常量 + _is_async_with_send_loop 谓词、docstring 归约顺序修正；无禁止前缀新增、无硬编码深度上限；commit+push 待用户指令）
- [ ] P1-MATCH 第 1 遍 MATCH 区域完成
- [ ] P1-ASSERT 第 1 遍 ASSERT 区域完成
- [ ] P1-BOOLOP 第 1 遍 BOOLOP 区域完成
- [ ] P1-TERNARY 第 1 遍 TERNARY 区域完成
- [ ] P1-CC 第 1 遍 CHAINED_COMPARE 区域完成
- [ ] P1-SEQ 第 1 遍 SEQUENCE 区域完成

## 遍 2 (Pass 2)

- [ ] P2-IF / P2-LOOP / P2-TRY / P2-WITH / P2-MATCH
- [ ] P2-ASSERT / P2-BOOLOP / P2-TERNARY / P2-CC / P2-SEQ

## 遍 3-10 (Pass 3-10)

每遍 10 个区域，共 8 遍 × 10 区域 = 80 轮。

## 最终验证（10 遍完成后）

- [ ] F1 共 100 次 commit + push 完成
- [ ] F2 全测试集通过率 ≥ 起始基线
- [ ] F3 算法 4 原则 FULLY COMPLIANT
- [ ] F4 无反模式残留
- [ ] F5 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
