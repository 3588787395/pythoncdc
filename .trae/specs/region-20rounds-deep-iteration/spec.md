# 区域逐类 20 轮深度迭代 Spec

## Why

`region-comment-multi-pyc-iteration` 已迭代至 R13（pyc 轮询策略），跨多个 pyc 暴露了大量跨区域缺陷（Pattern T3/T2/A2/B/C/E/F/M2/G3/R 等），但这些缺陷的根因仍分散在 10 类区域识别/生成方法中。用户要求**按区域类型逐类深度迭代**：每个区域类型进行 20 轮「测试工程师 + 修复工程师」对抗，测试工程师专注阅读该区域识别/生成方法现有代码、找出可能的问题点并构造测试实例（累计 ≥ 10 个错误即停止本轮测试），修复工程师依据区域归约算法修复并确保同类问题不再出现。每区域每轮独立目录，每轮 commit + push。所有区域同等完善，所有方法必须符合区域归约算法。

本规范继承 `region-comment-multi-pyc-iteration` 的全部基础设施（pyc_index.json / pyc_batch_verify.py / 6 节与 4 节注释模板 / 算法 4 原则 / 反模式禁令），仅改变迭代粒度：**从 pyc 轮询改为区域类型轮询**，并对每区域固定 20 轮。

## What Changes

### A. 迭代策略变更：区域类型轮询（非 pyc 轮询）

- 迭代单元 = 区域类型（IF / LOOP / TRY / WITH / MATCH / ASSERT / BOOLOP / TERNARY / CHAINED_COMPARE / SEQUENCE，共 10 类）
- 每区域固定 **20 轮**（round_01..round_20），共 200 轮
- 区域处理顺序（由弱到强，参考 region_test_baseline.txt 94.88% 中 TERNARY/TRY 最弱）：
  1. TERNARY（基线最弱）
  2. TRY（Pattern T2/T3 残留最多）
  3. BOOLOP（Pattern B/E 残留）
  4. CHAINED_COMPARE（Pattern G3 残留）
  5. IF（Pattern A2/C/C2/D2 残留）
  6. LOOP（Pattern R 残留）
  7. WITH（Pattern F 残留）
  8. MATCH
  9. ASSERT
  10. SEQUENCE

### B. 双工程师工作流（每轮）

1. **测试工程师**（subagent）：
   - 阅读**本区域**的 `_identify_*_regions` 方法（6 节注释）+ 对应 `_generate_*` 方法（4 节注释）的现有代码
   - 找出可能的问题点（边界条件 / 归约语义 / AST 映射 / 已知失败模式）
   - 从 pyc_index.json 中选取**触发本区域**的 pyc/函数，构造测试实例（最小 .py 源码 → 编译 → 反编译 → 字节码 diff）
   - **累计 ≥ 10 个真实错误即停止本轮测试**（正确的不算；非本区域缺陷标注 CTRL 不计入）
   - 输出 `test_engineer/findings.md`（问题点清单 + 测试实例 + 错误清单）

2. **修复工程师**（subagent）：
   - 阅读 `findings.md`
   - 对每个错误，定位到本区域 `_identify_*_regions` / `_generate_*` 方法
   - 按「No More Gotos」+ 区域归约算法 4 原则修复（禁止补丁 / 禁止硬编码 / 禁止跨区域启发式）
   - 同步更新方法 docstring（6 节 / 4 节模板）
   - 运行回归测试（既有矩阵不退化，≤ 280s）
   - 验证本轮测试实例全部通过
   - 输出 `repair_engineer/fix_report.md`
   - **确保相似问题不再出现**（通过完善判据/入口条件，而非针对单个实例打补丁）

3. **commit + push**：commit 前缀 `r20-<REGION>-rNN:`（如 `r20-TERNARY-r01:`）

### C. 目录结构（每区域每轮独立）

```
.trae/specs/region-20rounds-deep-iteration/
  rounds/
    TERNARY/
      round_01/
        test_engineer/
          findings.md
          minimal_repros/        # ≥ 10 个最小复现实例
        repair_engineer/
          fix_report.md
      round_02/
        ...
      ... round_20/
    TRY/
      round_01/
        ...
    ... SEQUENCE/
```

### D. 交叉影响解耦

- 每轮聚焦单一区域，但修复时若发现交叉影响（如 IF 修复影响 TRY 嵌套），尽量一并解决并记录
- 修复必须符合区域归约算法，禁止跨区域启发式
- 修复后运行**全部 10 类区域**的既有测试矩阵（确保无跨区域回归）

### E. 算法 4 原则持续合规（继承）

- 自底向上归约：从最内层到最外层识别区域
- 每块唯一归属：任意 CFG 块在任何层级仅属于一个区域
- 嵌套即抽象节点：嵌套区域在父区域中作为单个抽象节点表示
- 入口引用语义：归约后父区域 then/else 列表引用子区域入口，而非子区域所有块

### F. 反模式禁令（继承）

- 禁止跨区域跨层次的启发式规则
- 禁止破坏算法对嵌套的天然支持
- 禁止后处理补丁（必须识别阶段一次正确）
- 禁止硬编码深度上限
- 禁止 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀方法名
- 禁止修改反编译生成的 `+OK.py` 文件
- 禁止任何投机取巧（如针对特定 pyc 的硬编码绕过）

### G. 命令预算

- 所有命令执行 ≤ 300 秒
- 每轮 commit + push ≤ 300 秒
- 单轮回归测试 ≤ 280 秒
- 反编译单个 pyc ≤ 60 秒
- 字节码 diff ≤ 60 秒

### H. 每轮 push 强制

- 每轮**必须** commit + push 到远程（commit 前缀 `r20-<REGION>-rNN:`）
- push 使用本机已配置的 git 凭据（credential helper / `gh auth login`），**禁止**在命令或文件中嵌入任何 token
- 若 push 失败（网络/DNS），记录为 push-pending 并在下一轮重试，但 commit 不得跳过

## Impact

- **Affected specs**：
  - `region-comment-multi-pyc-iteration`（继承其基础设施与注释模板；本规范改为区域类型轮询）
  - `analysis-fix-iteration`（继承 4 原则与反模式禁令）
  - `region-100pct-bytecode-match` / `region-algorithm-deep-iteration`（继承算法合规要求）
- **Affected code**：
  - `core/cfg/region_analyzer.py`（11 个 `_identify_*_regions` 方法注释 + 逻辑修正）
  - `core/cfg/region_ast_generator.py`（9+ 个 `_generate_*` 方法注释 + 逻辑修正）
  - `core/cfg/cfg_builder.py` / `ast_converter.py` / `pattern_parser.py` / `code_generator.py`（必要时）
  - 复用 `scripts/pyc_index_builder.py` / `scripts/pyc_batch_verify.py`
- **Affected tests**：每轮新增 ≥ 10 个最小复现实例归档到 `rounds/<REGION>/round_NN/test_engineer/minimal_repros/`
- **Algorithm compliance**：持续 FULLY COMPLIANT（0 反模式新增，0 硬编码深度上限）
- **Risk**：200 轮迭代周期长；跨区域交叉影响需谨慎解耦

## ADDED Requirements

### Requirement: 区域类型轮询迭代（每区域 20 轮）

系统 SHALL 按区域类型逐类迭代，每区域固定 20 轮，共 200 轮。区域处理顺序：TERNARY → TRY → BOOLOP → CHAINED_COMPARE → IF → LOOP → WITH → MATCH → ASSERT → SEQUENCE。

#### Scenario: 单区域 20 轮闭环
- **WHEN** 区域 `<REGION>` 的第 NN 轮（NN=01..20）完成
- **THEN** `rounds/<REGION>/round_NN/test_engineer/findings.md` 已生成
- **AND** `rounds/<REGION>/round_NN/test_engineer/minimal_repros/` 含 ≥ 10 个可独立复现实例（若该区域已 100% 一致则豁免）
- **AND** `rounds/<REGION>/round_NN/repair_engineer/fix_report.md` 已生成
- **AND** 该轮 ≥ 10 个测试实例全部通过
- **AND** 既有测试矩阵无退化
- **AND** 已 commit + push `r20-<REGION>-rNN:`

#### Scenario: 测试工程师停止条件
- **WHEN** 测试工程师累计发现 ≥ 10 个真实错误（非本区域缺陷标注 CTRL 不计入）
- **THEN** 停止本轮测试，输出 findings.md
- **AND** 将错误清单移交修复工程师

### Requirement: 双工程师对抗迭代

每轮 SHALL 执行「测试工程师 + 修复工程师」对抗：
1. 测试工程师：阅读本区域识别/生成方法代码 → 找问题点 → 构造测试实例 → 累计 ≥ 10 错误即停
2. 修复工程师：按区域归约算法修复 → 更新注释 → 回归测试 → 确保相似问题不再出现

#### Scenario: 测试工程师职责
- **WHEN** 测试工程师启动第 `<REGION>` round_NN
- **THEN** 阅读本区域 `_identify_*_regions` + `_generate_*` 方法现有代码
- **AND** 从 pyc_index.json 选取触发本区域的 pyc/函数
- **AND** 构造 ≥ 10 个最小复现实例（正确的不算错误）
- **AND** 累计 ≥ 10 真实错误即停止

#### Scenario: 修复工程师职责
- **WHEN** 修复工程师收到 findings.md
- **THEN** 对每个错误定位到本区域方法
- **AND** 按区域归约算法 4 原则修复（禁止补丁）
- **AND** 同步更新 docstring（6 节 / 4 节模板）
- **AND** 运行回归测试（≤ 280s，无退化）
- **AND** 验证 ≥ 10 测试实例全部通过
- **AND** 确保相似问题不再出现（完善判据/入口条件）

### Requirement: 每轮独立目录与 push

每轮 SHALL 创建独立目录 `rounds/<REGION>/round_NN/{test_engineer/, repair_engineer/}`，并 commit + push（前缀 `r20-<REGION>-rNN:`）。

#### Scenario: 目录独立
- **WHEN** 第 `<REGION>` round_NN 执行
- **THEN** `rounds/<REGION>/round_NN/` 目录已创建
- **AND** test_engineer/ 与 repair_engineer/ 子目录已创建
- **AND** 禁止跨轮合并产物

#### Scenario: 每轮 push
- **WHEN** 第 `<REGION>` round_NN 完成
- **THEN** 已 commit（前缀 `r20-<REGION>-rNN:`）
- **AND** 已 push 到 origin/main（使用本机已配置凭据，禁止嵌入 token）
- **AND** 若 push 失败，记录 push-pending 并下一轮重试

### Requirement: 交叉影响解耦

每轮聚焦单一区域，但若修复发现交叉影响，SHALL 尽量一并解决并记录，运行全部 10 类区域测试矩阵确保无跨区域回归。

#### Scenario: 交叉影响处理
- **WHEN** 修复本区域时发现影响其他区域
- **THEN** 一并解决并在 fix_report.md 记录
- **AND** 运行全部 10 类区域既有测试矩阵
- **AND** 确保无跨区域回归

### Requirement: 算法 4 原则持续合规（继承）

每轮修复后 SHALL 保持算法 4 原则 FULLY COMPLIANT：自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义。

#### Scenario: 原则合规
- **WHEN** 检查任意一轮的代码变更
- **THEN** 无 `_fix_` / `_merge_` / `_patch_` 等禁止前缀
- **AND** 无 `depth > N` 硬编码
- **AND** 该轮测试矩阵通过数不下降

## MODIFIED Requirements

### Requirement: 区域归约算法实现（逐区域深度强化）

继承 `region-comment-multi-pyc-iteration` 的算法 4 原则与注释模板，本规范过程中：
- 按区域类型逐类深度强化（每区域 20 轮）
- 消除每区域剩余的特殊 case 处理
- 统一判据（基于结构模式而非指令模式）
- 强化子区域抽象节点不变量
- 完善方法 docstring（6 节 / 4 节模板）
- 所有修复必须符合区域归约算法，禁止跨区域启发式 / 后处理补丁

## REMOVED Requirements

### Requirement: pyc 轮询迭代策略
**Reason**：用户要求改为区域类型轮询（每区域 20 轮），聚焦单一区域深度完善
**Migration**：迭代单元从 pyc 改为区域类型；测试工程师从 pyc_index.json 选取触发本区域的 pyc/函数构造实例

### Requirement: 不设固定轮数上限
**Reason**：用户要求每区域固定 20 轮
**Migration**：每区域 round_01..round_20，共 200 轮

## 双工程师工作流详述

### 测试工程师职责（每轮）
1. 阅读本区域 `_identify_*_regions` 方法（6 节注释）+ 对应 `_generate_*` 方法（4 节注释）现有代码
2. 找出可能的问题点（边界条件 / 归约语义 / AST 映射 / 已知失败模式）
3. 从 pyc_index.json 选取触发本区域的 pyc/函数
4. 构造最小复现实例（最小 .py 源码 → 编译 → 反编译 → 字节码 diff）
5. 累计 ≥ 10 个真实错误即停止（正确的不算；非本区域缺陷标注 CTRL）
6. 输出 `findings.md`（问题点清单 + 测试实例路径 + 错误清单 + 成功率）

### 修复工程师职责（每轮）
1. 阅读 `findings.md`
2. 对每个错误，定位到本区域 `_identify_*_regions` / `_generate_*` 方法
3. 按「No More Gotos」+ 区域归约算法 4 原则修复
4. 同步更新方法 docstring（6 节 / 4 节模板）
5. 运行回归测试（既有矩阵不退化，≤ 280s）
6. 验证本轮 ≥ 10 测试实例全部通过
7. 确保相似问题不再出现（完善判据/入口条件）
8. 输出 `fix_report.md`（修复点 + 算法依据 + 注释更新清单 + 回归结果 + 残留不一致数）
9. commit + push（前缀 `r20-<REGION>-rNN:`，≤ 300s）

### 退出条件（单区域）
- 该区域 20 轮全部完成
- 该区域相关 pyc/函数字节码一致率 ≥ 99%（或残留缺陷已记录为 final_residual）

### 退出条件（全部）
- 10 个区域各 20 轮全部完成
- 所有 pyc 文件字节码不一致函数数趋近 0
- 算法 4 原则 FULLY COMPLIANT
- 所有 `_identify_*_regions` / `_generate_*` 方法注释模板合规

## 区域与方法的对应关系

| 区域类型 | `_identify_*_regions` 方法 | 对应 `_generate_*` 方法 |
|---------|---------------------------|------------------------|
| LOOP | `_identify_loop_regions` | `_generate_loop` 等 |
| TRY | `_identify_try_except_regions` | `_generate_try` 等 |
| WITH | `_identify_with_regions` | `_generate_with` 等 |
| MATCH | `_identify_match_regions` + `_identify_nested_match_regions` | `_generate_match` 等 |
| ASSERT | `_identify_assert_regions` | `_generate_assert` 等 |
| CHAINED_COMPARE | `_identify_chained_compare_regions` | `_generate_chained_compare` 等 |
| IF | `_identify_conditional_regions` | `_generate_if` / `_process_if_blocks` 等 |
| TERNARY | `_identify_ternary_regions` | `_generate_ternary_assign` 等 |
| BOOLOP | `_identify_boolop_regions` | `_generate_boolop` 等 |
| SEQUENCE | `_identify_sequence_regions` | `_generate_block_statements` 等 |

## 安全约束

- **禁止**在命令、文件、commit message 中嵌入任何 GitHub token / 凭据
- git push 必须使用本机已配置的凭据（credential helper / `gh auth login`）
- 若用户在对话中暴露 token，立即提示撤销，不得使用
