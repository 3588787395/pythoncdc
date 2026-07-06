# PyCDC-Python 控制流反编译文档

## 项目概述

本项目致力于完善Python多层多种类循环嵌套控制流的反编译，目标是达到100%通过率。

## 当前状态

- **总通过率**: 25.25% (25/99)
- **基础案例**: 17/20 (85%)
- **两层嵌套**: 6/40 (15%)
- **三层嵌套**: 2/29 (6.9%)
- **复杂案例**: 0/10 (0%)

## 文档结构

```
docs/
├── README.md                          # 本文档
├── patterns/
│   ├── control_flow_patterns.md       # 控制流模式详细说明
│   ├── control_flow_params_table.md   # 参量对照表
│   └── quick_reference.md             # 快速参考卡片
└── fixes/
    └── fix_registry.md                # 修复记录注册表
```

## 快速开始

### 1. 运行测试
```bash
python scripts/run_full_test_suite.py
```

### 2. 分析失败案例
```bash
python scripts/analyze_failures.py test_reports/test_report_*.json
```

### 3. 查看文档
- [控制流模式](patterns/control_flow_patterns.md) - 详细模式说明
- [参量对照表](patterns/control_flow_params_table.md) - 参量表格
- [快速参考](patterns/quick_reference.md) - 速查卡片
- [修复记录](fixes/fix_registry.md) - 修复记录

## 核心概念

### 控制流模式分类

1. **基础模式**
   - if-elif-else
   - for / for-else
   - while / while-else
   - try-except / try-finally

2. **嵌套模式**
   - if-in-for / for-in-if
   - try-in-for / for-in-try
   - nested_if / nested_for / nested_while / nested_try

3. **复杂模式**
   - 条件表达式 (ternary operator)
   - break / continue / return
   - 链式赋值

### 关键参量

| 参量 | 说明 | 使用场景 |
|------|------|----------|
| body_start / body_end | 代码块范围 | 所有模式 |
| else_start / else_end | else分支范围 | if / for |
| current_offset | 当前指令偏移 | 所有处理函数 |
| _chain_assign_offset | 链式赋值偏移 | 链式赋值 |

### 核心函数

| 函数 | 用途 |
|------|------|
| `_emit` | 节点分发到正确块 |
| `_pop_jump_forward_if_false` | 处理if-elif-else |
| `_pop_jump_backward_if_true` | 处理while循环 |
| `_for_iter` | 处理for循环 |
| `_push_exc_info` | 处理try-except |
| `_store_fast` | 处理变量赋值 |

## 修复记录

已完成10个关键修复：

| 修复ID | 问题 | 通过率提升 |
|--------|------|------------|
| FIX-001 | 预try节点查找修复 | +1.01% |
| FIX-002 | 空except块处理 | +1.01% |
| FIX-003 | while循环体结束位置修复 | +1.01% |
| FIX-004 | current_block恢复修复 | +3.03% |
| FIX-005 | RETURN_VALUE不在else块中修复 | +0% |
| FIX-006 | 包含运算的条件表达式修复 | +0% |
| FIX-007 | NOP指令处理修复 | +0% |
| FIX-008 | else块内NOP处理修复 | +1.01% |
| FIX-009 | 空except块异常类型修复 | +2.02% |
| FIX-010 | 赋值偏移量修复 | 进行中 |
| FIX-011 | for循环current_block恢复修复 | +1.01% |

## 待修复问题

### 🔴 高优先级
1. instruction_count不匹配 (74个案例)
2. for-else结构问题
3. 跳转目标计算错误

### 🟡 中优先级
4. FOR_ITER参数错误
5. 复杂嵌套结构

### 🟢 低优先级
6. 语法错误优化
7. 代码格式化

## 测试-修复-记录流程

```
1. 运行测试 → 生成报告
2. 分析失败 → 定位问题
3. 实施修复 → 验证效果
4. 更新文档 → 记录修复
5. 循环测试 → 持续提升
```

## 贡献指南

### 添加新修复
1. 在 `docs/fixes/fix_registry.md` 中添加修复记录
2. 在 `docs/patterns/control_flow_patterns.md` 中更新相关模式
3. 在 `docs/patterns/control_flow_params_table.md` 中更新参量表

### 添加新模式
1. 在 `docs/patterns/control_flow_patterns.md` 中添加模式说明
2. 在 `docs/patterns/control_flow_params_table.md` 中添加参量
3. 创建测试用例

## 调试技巧

### 启用调试输出
```python
from parsers import ast_builder
ast_builder.DEBUG = True
ast_builder.DEBUG_FILTER = ["_emit", "_for_iter"]
```

### 查看字节码
```bash
python -m dis tests/control_flow_cases/basic/__pycache__/case_name.cpython-311.pyc
```

### 创建调试脚本
```python
from core.pyc_loader_v2 import load_pyc_file_v2
from parsers.ast_builder import ASTBuilder

module = load_pyc_file_v2('path/to/case.pyc')
builder = ASTBuilder(module, module.code.get())
ast = builder.build_from_code(module.code.get())
print(ast.to_code())
```

## 更新日志

### 2026-03-01
- 创建文档系统
- 完成10个关键修复
- 通过率: 24.24%
- 建立测试-修复-记录流程

---

*文档持续更新中...*
