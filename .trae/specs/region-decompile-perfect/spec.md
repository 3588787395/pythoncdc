# 区域归约算法完善与全量pyc反编译验证 Spec

## Why
55个partial pyc（273个不一致函数），96.53%累计匹配率。3个根本原因覆盖76%不一致函数。

## What Changes
- 修复 for/while-else 识别（影响35%函数，96个）
- 修复 try-except-finally 块边界（影响28%函数，76个）
- 修复 SWAP 指令处理（影响12%函数，32个）
- 修复条件跳转反转、类默认值元组、UNPACK_SEQUENCE等次要问题
- 禁止修改反编译生成的 OK.py 文件
- 使用 scripts/pyc_batch_verify.py 验证
- 每轮提交 push，命令不超300秒

## Impact
- Affected code: core/cfg/region_analyzer.py, region_ast_generator.py, code_generator.py, dominator_analyzer.py

## ADDED Requirements

### Requirement: for/while-else 正确识别
系统 SHALL 正确识别 for-else / while-else 结构

#### Scenario: for-else 识别
- **WHEN** FOR_ITER 后的循环体末尾有 JUMP_FORWARD 跳回 FOR_ITER（回边），且 FOR_ITER 的 fall-through 目标不是紧跟循环的代码
- **THEN** 识别为 for-else 结构，fall-through 目标为 else 块
- **THEN** 循环体末尾不生成 return/continue，else 块正确生成

#### Scenario: while-else 识别
- **WHEN** while 循环条件跳转的 fall-through 目标不是循环后代码
- **THEN** 识别为 while-else 结构

### Requirement: try-except-finally 块边界正确
系统 SHALL 正确处理 except 块结尾的跳转

#### Scenario: except 正常结束
- **WHEN** except 块末尾为 POP_EXCEPT → JUMP_FORWARD（跳过 RERAISE 处理器）
- **THEN** 生成正确的 except 块，不生成多余的 return None
- **THEN** JUMP_FORWARD 目标正确跳到 try 块后的代码

#### Scenario: try-else 识别
- **WHEN** try 块正常出口跳过所有 handler 到达 else 块
- **THEN** 正确识别 try-else 结构

### Requirement: SWAP 指令正确处理
系统 SHALL 正确处理 Python 3.11+ 的 SWAP 指令

#### Scenario: with-as SWAP 绑定
- **WHEN** with-as 语句中 SWAP(2) 用于绑定 as 变量
- **THEN** 正确生成 `with ctx as var` 语法

#### Scenario: 比较链 SWAP
- **WHEN** SWAP+COPY 组合用于比较链
- **THEN** 正确生成链式比较表达式

### Requirement: 迭代验证流程
系统 SHALL 按共性模式修复，每轮验证

#### Scenario: 修复一轮
- **WHEN** 修复一个共性模式
- **THEN** 对受影响的 pyc 文件运行 single 验证
- **THEN** 运行 quotation.pyc 验证无回归
- **THEN** 批量回归验证
- **THEN** 提交并 push
