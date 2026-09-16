# 区域归约算法完善 - 39个Partial PYC文件100%反编译成功

## Why
当前402个pyc文件中39个为partial状态（字节码匹配率73%-96%），120个函数的字节码不一致。需要基于区域归约算法系统性完善反编译逻辑，使所有pyc文件达到100%字节码一致。

## What Changes
- 对39个partial pyc文件逐一分析反编译前后字节码差异
- 将差异归类为有限的区域模式（if/loop/try/with/match/assert/boolop/ternary等）
- 按区域归约算法原则完善region_analyzer.py和region_ast_generator.py中的区域识别与AST映射逻辑
- 禁止跨区域跨层次的启发式规则，禁止破坏算法对嵌套的天然支持
- 每轮至少解决1个pyc文件（从partial变为ok），10轮迭代

## Impact
- Affected specs: 区域归约算法的核心区域类型识别与归约
- Affected code: core/cfg/region_analyzer.py, core/cfg/region_ast_generator.py, core/cfg/dominator_analyzer.py

## ADDED Requirements
### Requirement: 区域归约算法完善
The system SHALL 对每个partial pyc文件的反编译失败函数，按区域归约算法分析其CFG区域结构，将正确的反编译逻辑写入识别方法的注释中，并完善代码使字节码100%一致。

#### Scenario: Partial pyc变为ok
- **WHEN** 对一个partial pyc文件执行反编译+字节码验证
- **THEN** bytecode_match_rate达到1.0，decompile_status变为ok，同目录生成同名OK.py

#### Scenario: 10轮迭代持续改进
- **WHEN** 执行一轮测试-修复迭代
- **THEN** 至少1个partial pyc变为ok，禁止0进度的轮次

### Requirement: 测试工程师与修复工程师协作
The system SHALL 调度两位工程师：
1. 测试工程师：反编译pyc文件，验证字节码一致性，创建最小复现实例（10+可复现实例）
2. 修复工程师：根据测试工程师分析结果，依照区域归约算法完善程序

### Requirement: 每轮提交与push
The system SHALL 每轮完成后git commit并push到远程仓库。

### Requirement: 禁止修改反编译生成的文件
The system SHALL NOT 修改任何反编译生成的OK.py文件。

### Requirement: 统一验证脚本
The system SHALL 使用scripts/pyc_batch_verify.py进行所有验证。
