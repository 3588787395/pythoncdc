## Why
基于区域归约算法的反编译方法有望大幅提升代码还原准确率，当前依赖启发式规则导致部分结构无法正确识别，影响Python字节码反编译整体成功率。区域归约理论成熟且具备数学完备性，适用于CFG结构化还原。

## What Changes
- 基于区域模式分析，规划每一区域的反编译逻辑
- 将分析和归约算法写入识别方法的注释
- 执行系列pyc文件区域化测试，验证字节码一致性和成功率
- 根据测试结果修正反编译算法并完善代码，持续迭代
- 每轮处理全部pyc文件，生成同名+OK的py源文件
- 保证所有区域的反编译算法完全归约

## Capabilities

### New Capabilities
- `region-based-decompilation`: 实现区域归约算法驱动的结构化反编译流程，支持CFG自动分解和归约为唯一AST节点。

### Modified Capabilities
- 无

## Impact
- 影响site-packages目录下所有pyc反编译流程与生成结果
- 涉及CFG结构分析核心方法、识别注释、反编译驱动主程序
- 依赖DominantAnalyzer、CFG类以及主反编译流程代码，覆盖项目主流程各层级
