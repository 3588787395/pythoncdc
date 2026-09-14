# 区域归约算法完善：47个PYC文件100%反编译 Spec

## Why
当前反编译器对402个pyc文件中355个达到100%字节码匹配（ok），但仍有47个pyc文件为partial状态（匹配率73.3%~95.8%），总计156个函数未通过字节码一致性验证。需基于区域归约算法原理，系统性完善反编译逻辑，使所有pyc文件达到100%字节码匹配。

## What Changes
- 对47个partial pyc文件逐个分析字节码不一致的原因
- 将反编译逻辑写入region_analyzer.py和region_ast_generator.py的方法注释中
- 根据区域归约算法修正区域分类和AST生成逻辑
- 确保每个pyc反编译后生成同名+OK.py文件且字节码完全一致
- 10轮迭代测试-修复，每轮至少解决一个pyc文件

## Impact
- Affected specs: region_analyzer.py (区域分类逻辑), region_ast_generator.py (AST生成逻辑), ast_converter.py (AST转换), code_generator.py (代码生成)
- Affected code: core/cfg/region_analyzer.py, core/cfg/region_ast_generator.py, core/cfg/ast_converter.py, core/cfg/code_generator.py

## ADDED Requirements

### Requirement: Iterative Test-Fix Round Execution
系统 SHALL 按10轮迭代执行测试-修复流程：
1. 测试工程师：反编译索引中的pyc文件，每次取一个，验证字节码一致性，创建10+最小复现实例
2. 修复工程师：根据测试分析结果，依照区域归约算法完善程序
3. 每轮必须至少解决一个pyc文件（从partial升级为ok）
4. 每轮创建独立文件夹
5. 每轮必须提交并push到远程

#### Scenario: Round execution success
- **WHEN** 开始一轮迭代
- **THEN** 测试工程师分析partial pyc的字节码差异，修复工程师完善代码
- **AND** 该轮至少有一个pyc从partial变为ok
- **AND** 代码提交并push到远程

### Requirement: Bytecode Consistency Verification
系统 SHALL 使用 scripts/pyc_batch_verify.py 验证每个pyc文件的反编译结果，确保反编译前后字节码完全一致（match_rate=1.0）。

#### Scenario: Single pyc verification
- **WHEN** 反编译一个pyc文件
- **THEN** 在同目录下生成同名+OK.py文件
- **AND** 使用pyc_batch_verify.py验证字节码一致性
- **AND** match_rate必须为1.0才算通过

### Requirement: Region Reduction Algorithm Compliance
系统 SHALL 严格遵循区域归约算法原则：
- 从最内层到最外层识别区域（归约顺序）
- 每个块在任何层级只属于一个区域
- 嵌套区域在其父区域中作为单个抽象节点表示
- 归约后父区域的then/else列表引用子区域的入口
- 禁止跨区域跨层次的启发式规则
- 用算法替代模式匹配，用数学性质替代启发式规则

#### Scenario: Region classification correctness
- **WHEN** 分析CFG中的控制流结构
- **THEN** 每个结构在识别阶段就正确分类
- **AND** 不需要后处理修正
- **AND** 区域归约保证不重叠

### Requirement: Quotation.pyc Priority Verification
系统 SHALL 在修复工程师完成一轮修复后，先验证quotation.pyc的反编译成功率，再进行批量回归验证。

#### Scenario: Quotation verification flow
- **WHEN** 一轮修复完成
- **THEN** 先验证quotation.pyc反编译成功
- **AND** 再执行批量回归验证
- **AND** 确保不引入回归问题

## MODIFIED Requirements
无（本spec为新增需求）

## REMOVED Requirements
无
