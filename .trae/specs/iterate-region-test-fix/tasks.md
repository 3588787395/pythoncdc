# Tasks

> 目标：10 类区域 × 20 轮 = 200 轮对抗性测试修复迭代
> **严格协议（用户强调）**：每轮必须 测试+修复+commit+**PUSH**，禁止只测试不修复，禁止只 commit 不 push。
> 每轮修复完毕立即 git add + git commit + git push。基线 100% 不可退化，每步回归验证。

## Phase 0: 框架初始化
- [x] Task 0.1: 建立 spec 目录 + 工作分支
- [ ] Task 0.2: 验证 push 可用
- [ ] Task 0.3: 确认起点基线

## Phase 1: IF 区域（20 轮）
- [ ] Task 1.1 ~ 1.20: IF round_01 ~ round_20

## Phase 2: LOOP 区域（20 轮）
- [ ] Task 2.1 ~ 2.20

## Phase 3-10: 其他 8 区域（各 20 轮）
- [ ] Task 3.1 ~ 10.20

## Phase 11: 跨区域解耦与最终验证
- [ ] Task 11.1 ~ 11.5

# 执行协议（每轮，严格）
1. 调度测试工程师 sub-agent → 产 test_findings.md（10+错误）
2. 调度修复工程师 sub-agent → 修复全部错误 → 每步全量回归 → 产 fix_report.md
3. 修复工程师 git add + git commit
4. **主代理 git push 到远程**（关键！不可省略）
5. 主代理验证全量回归 = 100%
6. 勾选 tasks.md，更新 checklist.md

# 关键约束
- 基线 100% 不可退化，每步回归，退化则回滚换方案
- 修复依归约算法 4 原则，禁止后处理补丁/跨区域特例/硬编码深度上限
- **每轮必须 push**（血泪教训：Round 1-6 因未 push 全部丢失）
