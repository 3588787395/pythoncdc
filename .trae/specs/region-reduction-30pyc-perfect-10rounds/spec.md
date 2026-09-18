# 区域归约算法完善 — 30个partial pyc文件100%反编译成功

## Why
当前402个pyc文件中30个处于partial状态（字节码不完全匹配），成功率为92.5%。需要基于区域归约算法的根本性完善，使所有pyc文件达到100%字节码匹配。

## What Changes
- 修复try/except区域边界识别（POP_EXCEPT vs LOAD_CONST模式，占9%失败）
- 修复控制流结构错误（JUMP_FORWARD位置错误导致指令序列偏移，占52%失败）
- 修复变量作用域解析（LOAD_GLOBAL vs LOAD_FAST，占10%失败）
- 修复条件反转（POP_JUMP_IF_TRUE vs IF_FALSE，占5%失败）
- 修复循环结构（JUMP_BACKWARD vs JUMP_FORWARD，占3%失败）
- 修复栈操作重建（RETURN_VALUE vs POP_TOP，占6%失败）
- 修复变量/常量混淆（LOAD_FAST vs LOAD_CONST，占7%失败）

## Impact
- Affected specs: region_analyzer.py (区域识别), region_ast_generator.py (AST生成), cfg_builder.py (CFG构建)
- Affected code: core/cfg/region_analyzer.py, core/cfg/region_ast_generator.py, core/cfg/dominator_analyzer.py

## ADDED Requirements

### Requirement: try/except区域边界精确识别
系统应精确识别try/except区域的边界，确保：
- POP_EXCEPT指令在正确位置生成
- try体与except处理器的连接块正确归约
- finally块的异常清理序列正确重建

#### Scenario: try/except with POP_EXCEPT boundary
- **WHEN** 反编译包含try/except结构的函数
- **THEN** 生成的字节码中POP_EXCEPT应出现在与原始字节码相同的位置

### Requirement: 控制流结构精确归约
系统应正确归约if/elif/else和循环控制流，确保：
- JUMP_FORWARD指令在正确的块边界位置生成
- 嵌套区域的归约不导致指令序列偏移
- 循环的then/else/continue/break块正确连接

#### Scenario: nested if/elif/else in try block
- **WHEN** 反编译在try块中包含if/elif/else的函数
- **THEN** 生成的字节码中JUMP_FORWARD应在与原始字节码相同的位置

### Requirement: 变量作用域正确解析
系统应正确解析变量是局部变量还是全局变量：
- LOAD_GLOBAL vs LOAD_FAST 正确区分
- 闭包变量 STORE_DEREF vs STORE_FAST 正确处理

#### Scenario: global variable in function
- **WHEN** 反编译使用全局变量的函数
- **THEN** 生成的字节码应使用LOAD_GLOBAL而非LOAD_FAST

### Requirement: 条件跳转方向正确
系统应正确生成条件跳转指令的极性：
- POP_JUMP_IF_TRUE vs POP_JUMP_IF_FALSE 不应反转
- None检查跳转（IF_NONE/IF_NOT_NONE）极性正确

#### Scenario: inverted condition in if statement
- **WHEN** 反编译 `if not x:` 形式的条件
- **THEN** 应生成正确的组合（如POP_JUMP_IF_TRUE配合原始比较）

### Requirement: 循环结构正确归约
系统应正确归约while/for循环：
- JUMP_BACKWARD应在循环底部而非使用JUMP_FORWARD
- 循环else子句正确连接
- continue/break目标正确

#### Scenario: while loop with continue
- **WHEN** 反编译包含continue的while循环
- **THEN** JUMP_BACKWARD应指向循环头部而非循环外

### Requirement: 栈操作精确重建
系统应精确重建栈操作：
- RETURN_VALUE vs POP_TOP正确区分
- COPY/SWAP在多目标赋值中正确生成
- 异常处理中的栈操作（PUSH_EXC_INFO/SWAP）正确

#### Scenario: return value in try block
- **WHEN** 反编译try块中的return语句
- **THEN** 应生成RETURN_VALUE而非POP_TOP

## MODIFIED Requirements
无修改的已有需求，所有变更均为新增。

## REMOVED Requirements
无移除需求。
