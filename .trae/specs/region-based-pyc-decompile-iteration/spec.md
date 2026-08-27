# 区域归约算法驱动的全量 PYC 反编译迭代完善 Spec

## Why

当前反编译器在 site-packages 的 402 个 pyc 文件中，291 个为 OK（72.4%），111 个仍为 partial。函数级字节码匹配率约 84.8%（419/494 在样本中），主要失败模式集中在：条件跳转（POP_JUMP_FORWARD_IF_FALSE/TRUE/NONE/NOT_NONE）指令差异、循环结构（FOR_ITER/JUMP_FORWARD）差异、异常处理差异。需要通过系统性的「测试工程师+修复工程师」迭代，以区域归约算法为核心，逐个修复 partial pyc，最终达到 100% 字节码匹配。

## What Changes

- 建立 pyc 索引并按 function_count 升序+match_rate 升序排列 partial 文件
- 每轮：测试工程师反编译 + 字节码 diff + ≥10 最小复现实例；修复工程师按区域归约算法修复 + 更新方法注释 + 回归测试
- 每个 pyc 反编译成功后在同目录下生成同名+OK 的 .py 文件（禁止修改已生成的 OK.py）
- 每轮 commit + push（前缀 `rbi-rNN:`）
- 成功率单调递增，每轮至少解决一个 pyc
- 所有修复符合区域归约算法 4 原则，禁止反模式

## Impact

- Affected specs: `site-packages-full-decompile-10rounds`, `region-100pct-bytecode-match`
- Affected code: `core/cfg/region_analyzer.py`（22682 行），`core/cfg/region_ast_generator.py`（40731 行），`pycdc.py`
- Algorithm compliance: 持续 FULLY COMPLIANT

## ADDED Requirements

### Requirement: 区域识别方法 6 节注释模板

所有 `_identify_*_regions` 方法 SHALL 在 docstring 中包含 6 节：区域类型 / 算法描述 / 字节码模式 / 边界条件 / 归约语义 / AST映射+已知失败模式。

#### Scenario: 注释模板合规
- **WHEN** 检查任意 `_identify_*_regions` 方法的 docstring
- **THEN** 6 节标题全部存在且内容非空
- **AND** 内容与本方法实际逻辑一致

### Requirement: 区域生成方法 4 节注释模板

所有 `_generate_*` 方法 SHALL 在 docstring 中包含 4 节：输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束。

#### Scenario: 注释模板合规
- **WHEN** 检查任意 `_generate_*` 方法的 docstring
- **THEN** 4 节标题全部存在且内容非空

### Requirement: 逐个 pyc 字节码一致性验证

系统 SHALL 使用 `--region` 模式逐个反编译 partial pyc，对比反编译产物重编译后的字节码与原 pyc 字节码（使用 `compare_bytecode_v2.py` 的规范化比较）。

#### Scenario: 单个 pyc 修复闭环
- **WHEN** 一个 partial pyc 被修复后
- **THEN** 反编译产物重编译后字节码与原 pyc 完全匹配（所有函数 100% match）
- **AND** 在同目录下生成同名+OK 的 .py 文件
- **AND** pyc_index.json 中该文件状态更新为 "ok"

### Requirement: 持续双工程师迭代（10 轮）

每轮：测试工程师取一个 partial pyc 反编译 + diff + ≥10 最小复现实例；修复工程师按区域归约算法修复 + 更新注释 + 回归测试 + commit + push。

#### Scenario: 单轮闭环
- **WHEN** 第 NN 轮迭代完成
- **THEN** `rounds/round_NN/test_engineer/` 含反编译报告 + ≥10 最小复现实例
- **AND** `rounds/round_NN/repair_engineer/` 含修复报告
- **AND** 该轮目标 pyc 反编译成功，字节码完全匹配
- **AND** 既有测试矩阵无退化
- **AND** 已 commit + push `rbi-rNN:`

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
- **THEN** 无 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 等禁止前缀
- **AND** 无 `depth > N` 硬编码
- **AND** 该轮测试矩阵通过数不下降

### Requirement: 命令预算

所有命令执行 <= 300 秒。每轮 commit + push <= 300 秒。单轮回归测试 <= 280 秒。反编译单个 pyc <= 60 秒。

### Requirement: 每轮强制 commit + push

每轮必须 commit + push 到远程仓库，禁止只 commit 不 push。

### Requirement: quotation.pyc 回归守卫

每轮修复后 MUST 验证 quotation.pyc 的函数级字节码匹配率不退化。

#### Scenario: quotation 回归
- **WHEN** 修复工程师完成修复
- **THEN** quotation.pyc 函数级匹配率 >= 上一轮值

## MODIFIED Requirements

### Requirement: 区域归约算法实现（持续强化）

继承 `region-100pct-bytecode-match` 的算法 4 原则，本规范过程中：
- 消除剩余特殊 case 处理
- 统一判据（基于结构模式而非指令模式）
- 强化子区域抽象节点不变量
- 完善方法 docstring（6 节 / 4 节模板）
