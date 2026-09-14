# 区域归约算法完善 — 43 个 pyc 10 轮迭代 Spec

## Why

当前反编译器在 `site-packages` 目录的 402 个 pyc 文件中，359 个已完全反编译成功（OK），42 个仍为 partial（匹配率 80%-97%），1 个 failed（replace_utils.pyc RuntimeError）。需要通过 10 轮「测试工程师 + 修复工程师」迭代，以区域归约算法为核心，逐个修复，将所有 partial/failed 转为 OK，最终达到 100% 成功率。

## What Changes

- 按 bytecode_match_rate 降序排列 partial 文件（先修最接近 OK 的），逐个修复
- 每轮：测试工程师反编译 1 个 pyc + 字节码 diff + 10+ 最小复现实例；修复工程师按区域归约算法修复 + 更新注释
- 每个 pyc 反编译成功后在同目录下生成同名 + OK 的 .py 文件（禁止修改已生成的 OK.py）
- 每轮 commit + push（前缀 `rr43-rNN:`）
- 成功率单调递增，每轮至少解决一个 pyc
- 所有修复符合区域归约算法 4 原则，禁止反模式
- 必须用相同脚本验证：scripts/pyc_batch_verify.py
- quotation.pyc 每轮回归验证，必须保持 100% 匹配
- 所有命令执行 <= 300 秒

## Impact

- Affected specs: `site-packages-region-10rounds`, `region-reduction-complete-decompile`
- Affected code: `core/cfg/region_analyzer.py`, `core/cfg/region_ast_generator.py`, `pycdc.py`
- Algorithm compliance: 持续 FULLY COMPLIANT

## ADDED Requirements

### Requirement: 逐个 pyc 字节码一致性验证

系统 SHALL 逐个反编译 partial/failed pyc，对比反编译产物重编译后的字节码与原 pyc 字节码。

#### Scenario: 单个 pyc 修复闭环
- **WHEN** 一个 partial pyc 被修复后
- **THEN** 反编译产物重编译后字节码与原 pyc 完全匹配
- **AND** 在同目录下生成同名 + OK 的 .py 文件
- **AND** pyc_index.json 中该文件状态更新为 "ok"

### Requirement: 持续双工程师迭代（10 轮）

每轮：测试工程师取一个 partial pyc 反编译 + diff + 10+ 复现实例；修复工程师按区域归约算法修复 + 更新注释 + 回归测试 + commit + push。

#### Scenario: 单轮闭环
- **WHEN** 第 NN 轮迭代完成
- **THEN** 该轮目标 pyc 反编译成功，字节码完全匹配
- **AND** 既有测试矩阵无退化
- **AND** 已 commit + push `rr43-rNN:`

#### Scenario: 成功率单调递增
- **WHEN** 比较第 NN 轮与第 NN-1 轮的 OK 数量
- **THEN** 第 NN 轮 >= 第 NN-1 轮

### Requirement: 每轮至少解决一个 pyc

每轮 MUST 至少将一个 partial pyc 完全修复为 OK，否则禁止进入下一轮。

#### Scenario: 每轮进度保证
- **WHEN** 第 NN 轮完成
- **THEN** 至少一个 partial pyc 的字节码匹配率达到 100%
- **AND** 该 pyc 在 pyc_index.json 中状态更新为 "ok"

### Requirement: 算法 4 原则持续合规

1. 自底向上归约：子区域先于父区域识别
2. 每块唯一归属：`block_to_region[block_id]` 每个块仅归属一个区域
3. 嵌套即抽象节点：子区域块不出现在父区域展开中
4. 入口引用语义：父区域仅引用子区域入口块

#### Scenario: 原则合规
- **WHEN** 检查任意一轮的代码变更
- **THEN** 无 `_fix_` / `_merge_` / `_patch_` 等禁止前缀
- **AND** 无 `depth > N` 硬编码

### Requirement: 命令预算

所有命令执行 <= 300 秒。每轮 commit + push <= 300 秒。

### Requirement: 每轮强制 commit + push

每轮必须 commit + push 到远程仓库。

### Requirement: quotation.pyc 回归验证

每轮修复后 MUST 验证 quotation.pyc 反编译仍然 100% 匹配，确保无回归。

### Requirement: 测试工程师与修复工程师分工

测试工程师职责：
1. 反编译目标 pyc，输出详细 diff
2. 提取 >=10 个最小复现实例（最小 .py 源码 → compile → 反编译 → 字节码 diff）
3. 识别涉及的区域类型与算法偏离点

修复工程师职责：
1. 对每个不一致定位到 `_identify_*_regions` 或 `_generate_*` 方法
2. 按区域归约算法 4 原则完善逻辑（禁止补丁）
3. 只修改 core/cfg/ 下源码，不修改 OK.py 文件
4. 回归测试：10+ 复现实例通过 + 目标 pyc 100% + quotation.pyc 无退化

## MODIFIED Requirements

### Requirement: 区域归约算法实现（持续强化）

继承已有规范的算法 4 原则，本规范过程中：
- 消除剩余特殊 case 处理
- 统一判据（基于结构模式而非指令模式）
- 强化子区域抽象节点不变量

## REMOVED Requirements

（无移除需求）
