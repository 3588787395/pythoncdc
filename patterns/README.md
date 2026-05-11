# Python 3.11+ 反编译模式识别系统

## 概述

本系统用于管理和改进 Python 3.11+ 字节码反编译器的模式识别能力。通过建立完整的模式文档、参量表格和修复历史，不断提高反编译的准确性和匹配度。

## 目录结构

```
patterns/
├── README.md                 # 本文件
├── pattern_registry.py       # 模式注册表
├── docs/                     # 模式文档目录
│   ├── if_pattern.md         # If-Elif-Else 模式
│   ├── try_except_pattern.md # Try-Except 模式
│   └── ...                   # 其他模式文档
├── code/                     # 模式实现代码（待创建）
└── tests/                    # 模式测试用例（待创建）
```

## 已完成的模式文档

### 1. If-Elif-Else 模式
- **文件**: `docs/if_pattern.md`
- **描述**: 识别 if、if-else、if-elif-else 条件分支结构
- **关键操作码**: POP_JUMP_FORWARD_IF_FALSE, POP_JUMP_FORWARD_IF_TRUE
- **修复历史**: if_body_end 计算错误修复

### 2. Try-Except-Else-Finally 模式
- **文件**: `docs/try_except_pattern.md`
- **描述**: 识别 try-except、try-except-else、try-finally 等异常处理结构
- **关键操作码**: PUSH_EXC_INFO, POP_EXCEPT, RERAISE
- **修复历史**: 
  - try_body_start/end 从异常表获取
  - for 循环内 try 节点处理
  - 预创建 try 节点使用
  - ASTAugAssign 在 if 中的处理

### 3. For-Else 循环模式
- **文件**: `docs/for_loop_pattern.md`
- **描述**: 识别 for 循环和 for-else 结构
- **关键操作码**: GET_ITER, FOR_ITER, JUMP_BACKWARD
- **修复历史**:
  - for 循环体范围计算
  - 嵌套 for 循环处理
  - for-else 结构识别

### 4. 复合赋值（AugAssign）模式
- **文件**: `docs/augassign_pattern.md`
- **描述**: 识别 +=、-=、*=、/= 等复合赋值操作
- **关键操作码**: BINARY_OP, STORE_FAST
- **修复历史**:
  - try-except 内的复合赋值处理
  - if body 范围扩展
  - 边界条件处理

### 5. While-Else 循环模式
- **文件**: `docs/while_loop_pattern.md`
- **描述**: 识别 while 循环和 while-else 结构
- **关键操作码**: POP_JUMP_FORWARD_IF_FALSE, JUMP_BACKWARD
- **修复历史**:
  - while 循环体范围计算
  - 无限循环识别
  - 与 if 语句的区分

### 6. 推导式（Comprehension）模式
- **文件**: `docs/comprehension_pattern.md`
- **描述**: 识别列表、字典、集合推导式
- **关键操作码**: BUILD_LIST, BUILD_MAP, BUILD_SET, LIST_APPEND, MAP_ADD, SET_ADD
- **修复历史**:
  - 容器类型识别
  - 条件推导式处理
  - 字典键值对识别

### 7. 函数定义（Function Definition）模式
- **文件**: `docs/function_def_pattern.md`
- **描述**: 识别函数定义，包括普通函数、嵌套函数、异步函数等
- **关键操作码**: LOAD_CONST, MAKE_FUNCTION, STORE_FAST
- **修复历史**:
  - 嵌套函数识别
  - 装饰器处理
  - 异步函数识别

### 8. 类定义（Class Definition）模式
- **文件**: `docs/class_def_pattern.md`
- **描述**: 识别类定义，包括普通类、继承类、带装饰器的类等
- **关键操作码**: LOAD_CONST, MAKE_FUNCTION, CALL_FUNCTION, STORE_NAME
- **修复历史**:
  - 基类识别（支持多继承）
  - 类装饰器处理
  - 类方法和属性提取

### 9. Break/Continue 模式
- **文件**: `docs/break_continue_pattern.md`
- **描述**: 识别循环中的 break 和 continue 语句
- **关键操作码**: JUMP_FORWARD, JUMP_BACKWARD

### 10. Return 模式
- **文件**: `docs/return_pattern.md`
- **描述**: 识别函数中的 return 语句
- **关键操作码**: RETURN_VALUE, RETURN_CONST

### 11. Lambda 表达式模式
- **文件**: `docs/lambda_pattern.md`
- **描述**: 识别 lambda 表达式
- **关键操作码**: LOAD_CONST, MAKE_FUNCTION

### 12. 装饰器模式
- **文件**: `docs/decorator_pattern.md`
- **描述**: 识别函数和类的装饰器
- **关键操作码**: LOAD_GLOBAL, CALL_FUNCTION

### 13. 导入模式
- **文件**: `docs/import_pattern.md`
- **描述**: 识别 import 语句
- **关键操作码**: IMPORT_NAME, IMPORT_FROM, IMPORT_STAR

### 14. 全局/非局部声明模式
- **文件**: `docs/global_nonlocal_pattern.md`
- **描述**: 识别 global 和 nonlocal 声明
- **关键操作码**: STORE_GLOBAL, STORE_DEREF

## 模式注册表

### 功能
- 统一管理所有模式
- 支持按类型、操作码、优先级索引
- 提供模式匹配接口
- 记录模式统计信息

### 使用示例
```python
from patterns.pattern_registry import register_pattern, get_pattern, match_pattern

# 注册模式
register_pattern(if_pattern)

# 获取模式
pattern = get_pattern("If-Elif-Else")

# 匹配模式
matched_pattern = match_pattern(instruction, context)
```

## 核心思想

### 循环测试-修复-记录流程

```
测试阶段 → 修复阶段 → 记录阶段 → 测试阶段 → ...
```

1. **测试阶段**: 运行测试用例，识别失败案例
2. **修复阶段**: 分析问题，实现修复
3. **记录阶段**: 更新模式文档，记录修复历史

### 模式文档模板

每个模式文档包含：
- 模式描述和适用场景
- 字节码特征和指令序列
- 识别参数表格
- 识别伪代码
- 测试用例
- 修复历史
- 相关模式链接

## 参量表格

### 通用参量
- **位置参量**: current_offset, start_offset, end_offset, jump_target
- **状态参量**: in_try_block, in_if_body, in_for_body, current_block
- **栈参量**: stack_depth, stack_items, block_stack

### 模式特定参量
- **If 模式**: if_body_start, if_body_end, has_else, else_body_start
- **Try 模式**: try_body_start, try_body_end, except_start, has_finally
- **For 模式**: for_body_start, for_body_end, loop_var, iter_obj

## 修复历史记录

| 日期 | 模式 | 问题描述 | 修复方案 | 状态 |
|------|------|----------|----------|------|
| 2026-03-01 | If | if_body_end 计算错误 | 使用 JUMP_FORWARD 目标 | 通过 |
| 2026-03-01 | Try-Except | try_body_start/end 为 -1 | 从异常表获取 | 通过 |
| 2026-03-01 | Try-Except | try 节点添加到 main_block | 检查 for 循环范围 | 通过 |
| 2026-03-01 | Try-Except | 创建重复 try 节点 | 使用预创建节点 | 通过 |
| 2026-03-01 | Try-Except | ASTAugAssign 位置错误 | 修改范围检查逻辑 | 通过 |

## 下一步工作

### 高优先级
- [ ] 创建 For 循环模式文档
- [ ] 创建复合赋值模式文档
- [ ] 创建 While 循环模式文档

### 中优先级
- [ ] 创建推导式模式文档
- [ ] 创建函数定义模式文档
- [ ] 创建类定义模式文档

### 低优先级
- [ ] 创建测试框架
- [ ] 实现模式自动识别
- [ ] 建立性能监控系统

## 使用指南

### 添加新模式

1. 在 `docs/` 目录下创建模式文档（使用模板）
2. 在 `pattern_registry.py` 中注册模式
3. 在 `code/` 目录下实现模式识别代码
4. 在 `tests/` 目录下添加测试用例
5. 更新本 README 文件

### 更新现有模式

1. 修改模式文档，添加修复历史
2. 更新参量表格（如有变化）
3. 更新 `pattern_registry.py` 中的模式定义
4. 运行测试验证修复
5. 更新修复历史记录

### 运行测试

```bash
# 运行所有测试
python comprehensive_test.py

# 运行特定模式测试
python patterns/tests/test_if_pattern.py
```

## 贡献指南

欢迎贡献新的模式或改进现有模式！请遵循以下步骤：

1. Fork 本仓库
2. 创建新模式文档
3. 实现模式识别代码
4. 添加测试用例
5. 提交 Pull Request

## 相关链接

- [Python 3.11 字节码文档](https://docs.python.org/3.11/library/dis.html)
- [If 模式文档](./docs/if_pattern.md)
- [Try-Except 模式文档](./docs/try_except_pattern.md)

## 维护者

- AI Assistant
- 最后更新: 2026-03-01
