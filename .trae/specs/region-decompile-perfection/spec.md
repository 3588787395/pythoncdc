# 区域模式反编译逻辑完善规范

## Why
当前反编译器各区域类型的测试成功率差异巨大（if_region 68.5%, try_except 24.5%, with_region 0%, match_region 17.7%, for_loop 47.2%, while_loop 42.5%, bool_op ~5%, ternary 48.3%），大量测试用例因区域识别错误或AST生成缺陷导致反编译失败或字节码不一致。需要系统性地分析每种区域模式的字节码特征，将反编译逻辑以注释形式写入识别方法，并迭代修正直到所有区域测试100%通过且字节码完全匹配。

## What Changes
- 为 `RegionAnalyzer` 中每个 `_identify_*` 方法添加详细的反编译逻辑注释，描述字节码模式、识别算法、边界条件和区域归约算法符合度
- 为 `RegionASTGenerator` 中每个 `_generate_*` 方法添加详细的AST生成逻辑注释，描述从区域到AST的映射规则
- 修正各区域识别方法中的识别错误，确保区域归约算法正确性
- 修正各AST生成方法中的生成缺陷，确保反编译输出语法正确且字节码等价
- 迭代测试-修正循环，直到所有区域测试100%通过

## Impact
- Affected specs: 所有区域类型的识别与生成逻辑
- Affected code:
  - `core/cfg/region_analyzer.py` - 10个识别方法 + 辅助方法
  - `core/cfg/region_ast_generator.py` - 9个生成方法 + 辅助方法
  - 测试文件: `tests/exhaustive/` 下8个区域子目录

## ADDED Requirements

### Requirement: 反编译逻辑注释规范
每个区域识别方法 `_identify_*` 的注释 SHALL 包含以下结构化信息：
1. **字节码模式** - 该区域类型在CPython字节码中的特征指令序列
2. **识别算法** - 从字节码到区域结构的映射步骤
3. **边界条件** - 需要特殊处理的边缘情况
4. **区域归约算法符合度** - 该方法如何符合区域归约理论

每个AST生成方法 `_generate_*` 的注释 SHALL 包含：
1. **区域到AST映射** - 区域属性到AST节点的对应关系
2. **表达式重建** - 如何从指令序列重建复杂表达式
3. **嵌套处理** - 如何处理嵌套的区域结构
4. **字节码等价保证** - 如何确保反编译输出重编译后字节码一致

### Requirement: 循环区域（for/while）100%通过
系统 SHALL 正确识别和生成所有循环区域模式：
- **WHEN** 输入包含 for/while 循环的字节码
- **THEN** 反编译输出语法正确，重编译后字节码与原始一致
- 覆盖：基本循环、嵌套循环、break/continue、循环else、while True、异步for、yield from

### Requirement: 异常处理区域（try/except/finally）100%通过
系统 SHALL 正确识别和生成所有异常处理区域模式：
- **WHEN** 输入包含 try/except/finally 的字节码
- **THEN** 反编译输出语法正确，重编译后字节码与原始一致
- 覆盖：基本try-except、多except、except as、bare except、try-finally、try-except-finally、嵌套try、try中return/break/continue

### Requirement: With区域100%通过
系统 SHALL 正确识别和生成所有with区域模式：
- **WHEN** 输入包含 with 语句的字节码
- **THEN** 反编译输出语法正确，重编译后字节码与原始一致
- 覆盖：基本with、with as、多with、嵌套with、async with、with内控制流

### Requirement: Match区域100%通过
系统 SHALL 正确识别和生成所有match区域模式：
- **WHEN** 输入包含 match-case 的字节码（Python 3.10+）
- **THEN** 反编译输出语法正确，重编译后字节码与原始一致
- 覆盖：字面量模式、捕获模式、序列模式、映射模式、类模式、OR模式、守卫条件

### Requirement: 条件区域（if/elif/else）100%通过
系统 SHALL 正确识别和生成所有条件区域模式：
- **WHEN** 输入包含 if/elif/else 的字节码
- **THEN** 反编译输出语法正确，重编译后字节码与原始一致
- 覆盖：if-then、if-then-else、elif链、嵌套if、if中包含循环/try/with

### Requirement: BoolOp区域100%通过
系统 SHALL 正确识别和生成所有布尔运算区域模式：
- **WHEN** 输入包含 and/or 短路求值的字节码
- **THEN** 反编译输出语法正确，重编译后字节码与原始一致
- 覆盖：and链、or链、混合and/or、not运算、在条件/赋值/返回中的布尔运算

### Requirement: Ternary区域100%通过
系统 SHALL 正确识别和生成所有三元表达式区域模式：
- **WHEN** 输入包含条件表达式的字节码
- **THEN** 反编译输出语法正确，重编译后字节码与原始一致
- 覆盖：基本三元、嵌套三元、在赋值/返回/调用参数/列表/字典中的三元

### Requirement: 链式比较区域100%通过
系统 SHALL 正确识别和生成所有链式比较区域模式：
- **WHEN** 输入包含链式比较的字节码（如 a < b < c）
- **THEN** 反编译输出语法正确，重编译后字节码与原始一致

### Requirement: Assert区域100%通过
系统 SHALL 正确识别和生成所有assert区域模式：
- **WHEN** 输入包含 assert 语句的字节码
- **THEN** 反编译输出语法正确，重编译后字节码与原始一致

## MODIFIED Requirements

### Requirement: 区域归约算法一致性
所有区域识别方法 SHALL 严格遵循区域归约算法：
1. Phase 1（低层）：TRY > LOOP > WITH/MATCH/ASSERT，按优先级识别，互不依赖
2. Phase 2（高层）：CHAIN_CMP > BOOLOP > TERNARY > CONDITIONAL，可依赖Phase 1结果
3. Phase 3（底层）：SEQUENCE，覆盖所有未归约块
4. 区域不重叠原则：每个基本块只属于一个区域
5. 自底向上归约：内层区域先识别，外层区域后识别

## REMOVED Requirements
（无移除需求）
