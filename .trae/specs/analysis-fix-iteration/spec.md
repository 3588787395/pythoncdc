# 分析修复迭代规范 (analysis-fix-iteration)

> 基于 `region-algorithm-deep-iteration` 规范，定义「架构工程师 + 修复工程师」
> 双角色迭代流程，对区域归约算法的全部 10 类区域进行 10 遍循环深度完善。

## Why

前置 `region-algorithm-deep-iteration` 规范已完成 Phase 0-2.7（基线建立、
算法反思、CPython peephole 模式库、禁止前缀重命名、测试框架修复），但 Phase 3-10
（每区域深度迭代 + 跨区域解耦 + 最终验证）尚未完成。剩余失败用例需要按区域类型
逐个深度修复，且必须遵守区域归约算法 4 原则。

用户要求采用「双工程师调度」模式：
- **架构工程师**：阅读现有代码，找出可能的问题点，完善算法通用性，强制符合算法原则
- **修复工程师**：将架构工程师分析结果，结合程序代码，依照区域归约算法完善程序，
  增强算法的通用性

以上为一轮。所有区域都过一轮为一遍，循环迭代 10 遍。

## What Changes

### A. 双工程师调度流程

每一轮（一个区域）的执行流程：

1. **架构工程师分析阶段**（由 search subagent 执行）
   - 阅读该区域的 `_identify_*_regions` 与 `_generate_*` 方法
   - 找出可能的问题点（识别顺序、归约边界、AST 映射、子区域抽象）
   - 评估算法通用性不足之处（特殊 case 处理、硬编码判据、启发式规则）
   - 强制符合算法 4 原则：自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 /
     父引用子入口
   - 输出「问题点 + 算法根因 + 修复策略」分析报告（写入该轮 test_findings.md）

2. **修复工程师实施阶段**（由 general_purpose_task subagent 执行）
   - 接收架构工程师的分析报告
   - 结合程序代码，依照区域归约算法完善程序
   - 增强算法的通用性（消除特例、统一判据、强化不变量）
   - 不引入新的跨区域特例 / 后处理补丁 / 启发式优先级覆盖
   - 输出「修复实施报告」（写入该轮 fix_report.md）

3. **回归测试**（在 300 秒内）
   - 运行该区域对应的测试集
   - 不退化（通过数不下降）

4. **提交并推送**（每轮强制 commit + push）
   - commit message 含「遍号/区域/轮号」标识
   - push 到 origin/main

### B. 10 类区域定义

每遍按以下顺序遍历 10 类区域：

1. **IF** — `tests/exhaustive/if_region/` + adv 测试
   - 识别方法：`_identify_conditional_regions`
   - 生成方法：`_generate_if`
2. **LOOP** — `tests/exhaustive/while_loop/` + `for_loop/`
   - 识别方法：`_identify_loop_regions`
   - 生成方法：`_generate_loop`
3. **TRY** — `tests/exhaustive/try_except/`
   - 识别方法：`_identify_try_except_regions`
   - 生成方法：`_generate_try`
4. **WITH** — `tests/exhaustive/with_region/`
   - 识别方法：`_identify_with_regions`
   - 生成方法：`_generate_with`
5. **MATCH** — `tests/exhaustive/match_region/`
   - 识别方法：`_identify_match_regions`
   - 生成方法：`_generate_match`
6. **ASSERT** — `tests/exhaustive/assert/`（如有）+ nook assert
   - 识别方法：`_identify_assert_regions`
   - 生成方法：`_generate_assert`
7. **BOOLOP** — `tests/exhaustive/bool_op/` + `boolop/`
   - 识别方法：`_identify_boolop_regions`
   - 生成方法：`_generate_boolop`
8. **TERNARY** — `tests/exhaustive/ternary/`
   - 识别方法：`_identify_ternary_regions`
   - 生成方法：`_generate_ternary`
9. **CHAINED_COMPARE** — 散布于 if/assert/boolop 测试
   - 识别方法：`_identify_chained_compare_regions`
   - 生成方法：`_build_chained_compare_from_region_data`
10. **SEQUENCE** — `tests/exhaustive/basic/` + L1_basic
    - 识别方法：`_identify_sequence_regions`
    - 生成方法：`_generate_basic_region`

### C. 算法 4 原则强化（每轮检查）

每轮修复后必须验证：
- **自底向上归约**：子区域先于父区域识别
- **每块唯一归属**：`block_to_region[block_id]` 每个块仅归属一个区域
- **嵌套即抽象节点**：子区域块不出现在父区域展开中
- **入口引用语义**：父区域仅引用子区域入口块

### D. 反模式禁止（每轮检查）

- 禁止跨区域跨层次的启发式规则
- 禁止后处理补丁（必须识别阶段一次正确）
- 禁止硬编码深度上限
- 禁止 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` /
  `_temp_` 前缀方法名

### E. 迭代产物归档

每轮产物归档至 `.trae/specs/analysis-fix-iteration/rounds/<region>/pass_<NN>/`：
- `test_findings.md` — 架构工程师分析报告
- `fix_report.md` — 修复工程师实施报告

## Impact

- **Affected specs**: `region-algorithm-deep-iteration`（前置，已完成 Phase 0-2.7）
- **Affected code**:
  - `core/cfg/region_analyzer.py`（~13000 行）— 主要修改
  - `core/cfg/region_ast_generator.py`（~15500 行）— 配合修改
  - `core/cfg/peephole_patterns.py` — 模式库扩展
  - 测试文件**不修改**
- **Algorithm compliance**: 持续 FULLY COMPLIANT（0 WARN，0 反模式）
- **Risk**: 双工程师迭代可能引入回归，需每轮回归测试

## ADDED Requirements

### Requirement: 双工程师迭代流程

系统 **SHALL** 对 10 类区域执行 10 遍「架构工程师 + 修复工程师」迭代流程，
每遍覆盖全部 10 类区域，共 100 轮。每轮：
1. 架构工程师分析（输出 test_findings.md）
2. 修复工程师实施（输出 fix_report.md）
3. 回归测试（不退化）
4. 提交并推送（强制）

#### Scenario: 一轮完成
- **WHEN** 第 N 遍的第 R 区域的迭代完成
- **THEN** 该区域的 test_findings.md 与 fix_report.md 已生成
- **AND** 该区域测试集无退化
- **AND** 已 commit + push 到 origin/main

#### Scenario: 一遍完成
- **WHEN** 第 N 遍的全部 10 个区域迭代完成
- **THEN** 共 10 轮 commit + push 完成
- **AND** 全测试集无退化

### Requirement: 算法 4 原则持续合规

每轮修复后 **SHALL** 保持算法 4 原则 FULLY COMPLIANT：
- 无新跨区域特例
- 无新后处理补丁
- 无新硬编码深度上限
- 无禁止前缀方法名

#### Scenario: 原则合规
- **WHEN** 检查任意一轮的代码变更
- **THEN** 无 `_fix_` / `_merge_` / `_patch_` 等禁止前缀
- **AND** 无 `depth > N` 硬编码
- **AND** 该区域测试集通过数不下降

## MODIFIED Requirements

### Requirement: 区域识别算法（持续强化）

在 `region-algorithm-deep-iteration` 已完成的基础上，每轮迭代继续强化：
- 消除该区域剩余的特殊 case 处理
- 统一判据（基于结构模式而非指令模式）
- 强化子区域抽象节点不变量
- 完善方法 docstring（6 节 / 4 节模板）

## REMOVED Requirements

### Requirement: 仅由单一执行者完成修复

**Reason**: 用户明确要求双工程师调度模式（架构工程师分析 + 修复工程师实施），
而非单一执行者。这分离了「找问题」与「改代码」两个职责，提升修复质量。

**Migration**: 改用双工程师迭代流程（见 ADDED Requirement: 双工程师迭代流程）。
