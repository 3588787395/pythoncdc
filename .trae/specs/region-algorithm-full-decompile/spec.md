# 区域归约算法全面反编译迭代完善 Spec

## Why
当前 402 个 pyc 文件中有 54 个为 partial 状态（字节码匹配率 70%~95.8%），整体函数级匹配率 96.7%。需要通过迭代式测试-修复流程，将区域归约算法完善至所有 pyc 文件 100% 字节码匹配，达到完全反编译成功。

## What Changes
- 对 54 个 partial pyc 文件逐一分析字节码不一致原因
- 将反编译逻辑写入识别方法的注释中（区域归约算法注释增强）
- 修复区域识别、AST 生成中的通用性缺陷
- 增强 elif 链合并、for-else/while-else、try-except-finally、嵌套循环 break/continue 等区域模式
- 每轮至少解决一个 pyc 文件（从 partial 变为 ok）
- 每轮验证 quotation.pyc + 批量回归，确保无退化
- 每轮提交并 push 到远程

## Impact
- Affected specs: core/cfg/region_analyzer.py, core/cfg/region_ast_generator.py
- Affected code: 核心区域识别与 AST 生成管线
- pyc_index.json: 54 个 partial 条目需逐步变为 ok

## ADDED Requirements

### Requirement: 迭代式测试-修复流程
The system SHALL implement a dual-engineer iteration process:
- Test Engineer: 反编译 pyc 文件，验证字节码一致性，分析不一致原因，创建最小复现实例（10+个/轮）
- Repair Engineer: 根据测试工程师分析结果，按区域归约算法完善程序，增强算法通用性
- 每轮独立文件夹，记录测试报告与修复报告

#### Scenario: 单轮迭代流程
- **WHEN** 开始一轮迭代
- **THEN** Test Engineer 取一个 pyc 文件，验证字节码一致性，分析不一致函数，创建最小复现实例
- **THEN** Repair Engineer 根据分析结果修复代码
- **THEN** 验证 quotation.pyc 仍然 ok
- **THEN** 批量回归验证（pyc_batch_verify.py batch）
- **THEN** 至少一个 pyc 从 partial 变为 ok
- **THEN** 提交并 push 到远程

### Requirement: 区域归约算法注释增强
The system SHALL 在区域识别方法中写入反编译逻辑注释，说明每种区域类型的识别规则、边界判定、AST 映射逻辑。

#### Scenario: 注释写入
- **WHEN** 修复一个区域识别缺陷
- **THEN** 在对应方法中添加注释说明反编译逻辑与修复原因

### Requirement: 100% 字节码匹配目标
The system SHALL 使所有 pyc_index.json 中的 pyc 文件达到 decompile_status='ok'（bytecode_match_rate=1.0）。

#### Scenario: 最终目标
- **WHEN** 所有 54 个 partial pyc 文件变为 ok
- **THEN** 累计匹配率 = 100%，所有 pyc 同目录生成同名+OK 的 py 文件

## MODIFIED Requirements

### Requirement: 区域归约算法
在现有区域归约算法基础上，增加以下通用性修复方向：
1. elif 链合并：正确识别 IF_ELIF_CHAIN 区域，合并 then-block 到 elif 链
2. for-else/while-else：正确识别 loop-else 区域，处理 else 分支
3. try-except-finally：正确识别嵌套异常处理区域
4. 嵌套 break/continue：正确处理嵌套循环中的 break/continue 语义
5. 条件表达式（ternary）：正确识别 IF_THEN_ELSE 与 ternary 的区别
6. with 语句：正确识别 WITH 区域的 entry/body/exit
7. match-case：正确识别 MATCH 区域
