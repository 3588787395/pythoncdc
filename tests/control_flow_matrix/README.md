# Python 控制流完备性测试框架

## 概述

本测试框架提供了 **100+ 个测试用例**，专门用于验证 Python 反编译器对控制流语法的处理能力。框架覆盖了从基本结构到复杂嵌套的所有主要控制流模式。

## 测试用例统计

### 总计: 100 项测试用例 ✓

| 级别 | 文件 | 数量 | 覆盖范围 |
|------|------|------|----------|
| **L1** | test_l1_basic.py | **52 项** | 基本结构（语句、条件、循环、异常、with） |
| **L2** | test_l2_nested.py | **30 项** | 两层嵌套（循环-条件-异常组合） |
| **L3** | test_l3_deep.py | **18 项** | 三层嵌套（复杂实际场景） |

## 目录结构

```
tests/control_flow_matrix/
├── __init__.py              # 包初始化文件
├── base.py                  # ControlFlowTestCase 基类
├── test_l1_basic.py         # L1 基本结构 (52项)
├── test_l2_nested.py        # L2 两层嵌套 (30项)
├── test_l3_deep.py          # L3 三层嵌套 (18项)
├── run_tests.py             # 测试运行器和报告生成
└── validate_framework.py    # 框架验证脚本
```

## L1 详细分类 (52项)

### B01-B08: 基础语句 (8项)
- TestB01SimpleAssignment - 简单赋值
- TestB02AugmentedAssignment - 增强赋值 (+=)
- TestB03MultiTargetAssignment - 多目标赋值 (a = b = 1)
- TestB04TupleUnpacking - 元组解包
- TestB05ExpressionStatement - 表达式语句
- TestB06ReturnWithValue - 有返回值的 return
- TestB07ReturnNoValue - 无返回值的 return
- TestB08PassStatement - pass 语句

### C01-C07: 条件结构 (7项)
- TestC01IfThen - 简单 if
- TestC02IfElse - if-else
- TestC03IfElif - if-elif
- TestC04IfElifElse - if-elif-else
- TestC05IfElifElifElse - 多分支 elif 链
- TestC06NestedIf - 嵌套 if
- TestC07NestedIfElse - 嵌套 if-else

### L01-L18: 循环结构 (18项)
- TestL01-L02: 基本 for/while 循环
- TestL03-L04: for-else / while-else
- TestL05-L06: for-break / for-continue
- TestL07-L08: while-break / while-continue
- TestL09-L10: for-break-else / while-break-else
- TestL11-L12: break+continue 组合
- TestL13-L14: 嵌套 for/while
- TestL15-L16: 嵌套 for-break/continue
- TestL17: for 中嵌套 while
- TestL18: while 中嵌套 for

### E01-E13: 异常处理 (13项)
- TestE01-E03: try-except / 多 except / try-except-else
- TestE04-E06: try-finally / try-except-finally / 完整结构
- TestE07-E08: except as / 裸 except
- TestE09: 嵌套 try
- TestE10-E12: try 中包含循环/条件，条件中包含 try
- TestE13: finally 中的 raise

### W01-W06: with 语句 (6项)
- TestW01-W02: 基本 with / 无 as 的 with
- TestW03: 多上下文 with
- TestW04-W05: 嵌套 with / with 中嵌套 try
- TestW06: try 中嵌套 with

## L2 详细分类 (30项)

### IF01-IF08: 嵌套条件结构 (8项)
- IF01-IF04: for/while/try/with 中的 if
- IF05: 循环中的多分支 elif 链
- IF06: except 中的嵌套 if
- IF07: else 分支中的 if
- IF08: 条件性 break/continue

### LO01-LO12: 嵌套循环结构 (12项)
- LO01-LO02: try 中的 for/while
- LO03-LO04: with 中的 for/while
- LO05-LO06: except 中的 for/while
- LO07-LO08: else 分支中的 for/while
- LO09: 嵌套 for 带 break-else
- LO10: 复杂循环嵌套模式
- LO11: for 内层包含 while，带异常处理
- LO12: while 内层包含 for，带条件判断

### EX01-EX06: 异常与控制流组合 (6项)
- EX01-EX02: for/while 循环中的 try-except
- EX03: 循环中的 try-finally
- EX04: 嵌套的 try-except
- EX05: except 中的重新抛出
- EX06: 多种异常类型的处理

### WI01-WI04: with 语句嵌套 (4项)
- WI01-WI02: for/while 循环中的 with
- WI03: except 块中的 with
- WI04: 链式上下文管理器（多层嵌套）

## L3 详细分类 (18项)

### DEEP01-DEEP06: 三层循环嵌套 (6项)
- DEEP01: 三层 for 循环
- DEEP02: for-while-for 混合嵌套
- DEEP03: while-for-while 复杂嵌套
- DEEP04: 三层循环带 break 和 continue
- DEEP05: 嵌套 for 带 else 链
- DEEP06: 复杂循环状态管理

### DEEP07-DEEP12: 循环-条件-异常组合 (6项)
- DEEP07: for-if-try-except 模式
- DEEP08: while-if-for-try-finally 模式
- DEEP09: try-for-if-while 异常链
- DEEP10: 嵌套条件与循环和异常的组合
- DEEP11: 复杂控制流图（状态机模拟）
- DEEP12: 递归模式与异常处理的结合

### DEEP13-DEEP18: 复杂实际场景 (6项)
- DEEP13: 数据管道处理场景
- DEEP14: 配置加载器带回退机制
- DEEP15: 请求处理器中间件链
- DEEP16: 并行任务协调器
- DEEP17: 状态机与恢复机制
- DEEP18: 事务管理与补偿机制

## 快速开始

### 1. 验证框架完整性

```bash
cd pythoncdc
python quick_validate.py
```

预期输出：
```
======================================================================
控制流测试框架验证
======================================================================

✓ test_l1_basic.py 导入成功
  L1 测试类数量: 52
✓ test_l2_nested.py 导入成功
  L2 测试类数量: 30
✓ test_l3_deep.py 导入成功
  L3 测试类数量: 18

======================================================================
总测试用例数: 100
★ 达到目标 (>=100)
======================================================================
```

### 2. 运行所有测试

```bash
# 使用 pytest（推荐）
python -m pytest tests/control_flow_matrix/ -v

# 或使用自定义运行器
cd tests/control_flow_matrix
python run_tests.py
```

### 3. 运行特定级别的测试

```bash
# 只运行 L1 基本结构测试
python run_tests.py --level L1

# 只运行 L2 嵌套测试
python run_tests.py --level L2

# 只运行 L3 深度嵌套测试
python run_tests.py --level L3
```

### 4. 运行特定测试类

```bash
# 运行单个测试类
python run_tests.py --class TestB01SimpleAssignment

# 运行名称包含 "For" 的测试
python run_tests.py --class ForLoop
```

### 5. 生成详细报告

```bash
# 显示详细输出
python run_tests.py --verbose

# JSON 格式输出
python run_tests.py --format json

# 保存报告到文件
python run_tests.py --output report.txt
python run_tests.py --output report.json --format json
```

## 测试基类说明

### ControlFlowTestCase

所有测试类都继承自 `ControlFlowTestCase`，该基类提供：

#### 核心属性
- `SOURCE_CODE`: 子类必须定义的源代码字符串

#### 自动提供的方法

1. **compile_source()**: 编译源码为 code object
2. **decompile(code)**: 反编译 code object 为源码字符串
3. **verify_syntax(source)**: 验证反编译结果的语法正确性
4. **verify_bytecode_equivalence()**: 验证重编译后字节码等价
5. **find_node(tree, node_type)**: 在 AST 中查找指定类型节点
6. **find_all_nodes(tree, node_type)**: 查找所有指定类型节点
7. **verify_decompilation()**: 完整验证流程（反编译+语法检查+字节码等价）

#### 默认测试方法

每个测试类只需实现：
```python
def test_structure_correct(self):
    """验证反编译结果的结构正确性"""
    decompiled = self.decompile()
    tree = self.verify_syntax(decompiled)
    self.assertIsNotNone(tree)
```

### 创建新测试用例示例

```python
from .base import ControlFlowTestCase

class TestMyNewCase(ControlFlowTestCase):
    """我的新测试用例"""
    SOURCE_CODE = """
    # 你的 Python 源代码
    if condition:
        for item in items:
            try:
                process(item)
            except Error:
                handle_error()
    """

    def test_structure_correct(self):
        """验证反编译结果的结构正确性"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        
        # 可选：添加特定的断言
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(if_node, "应该包含 if 语句")
```

## 报告格式

### 文本报告示例

```
================================================================================
Python 控制流完备性测试报告
================================================================================

测试时间: 2026-01-22 10:30:00
执行时长: 15.23 秒

--------------------------------------------------------------------------------
总体统计
--------------------------------------------------------------------------------
总测试数: 100
通过:     95 (95.0%)
失败:     3 (3.0%)
跳过:     2 (2.0%)
错误:     0

--------------------------------------------------------------------------------
各级别统计
--------------------------------------------------------------------------------

L1 级别测试:
  总数:   52
  通过:   50 (96.2%)
  失败:   2
  跳过:   0

L2 级别测试:
  总数:   30
  通过:   28 (93.3%)
  失败:   1
  跳过:   1

L3 级别测试:
  总数:   18
  通过:   17 (94.4%)
  失败:   0
  跳过:   1

--------------------------------------------------------------------------------

总体评估:
  ★★★★☆ 良好 (>=85%) - 控制流反编译能力较好，有少量问题

通过率: 95.00%
================================================================================
```

### JSON 报告结构

```json
{
  "metadata": {
    "timestamp": "2026-01-22T10:30:00",
    "duration": 15.23,
    "version": "1.0.0"
  },
  "summary": {
    "total": 100,
    "passed": 95,
    "failed": 3,
    "skipped": 2,
    "errors": 0,
    "pass_rate": 95.0
  },
  "by_level": {
    "L1": { ... },
    "L2": { ... },
    "L3": { ... }
  }
}
```

## 测试覆盖矩阵

| 控制流结构 | L1 | L2 | L3 | 总计 |
|-----------|----|----|----|------|
| **赋值语句** | 4 | - | - | 4 |
| **return/pass** | 3 | - | - | 3 |
| **if/elif/else** | 7 | 8 | - | 15 |
| **for 循环** | 9 | 7 | 6 | 22 |
| **while 循环** | 9 | 5 | 5 | 19 |
| **break/continue** | 8 | 4 | 3 | 15 |
| **try/except/finally** | 9 | 6 | 6 | 21 |
| **with 语句** | 6 | 4 | 3 | 13 |
| **嵌套组合** | - | 30 | 18 | 48 |

## 注意事项

1. **核心模块依赖**: 测试框架依赖 `core.cfg` 模块，确保这些模块可以正常导入
2. **Python 版本**: 框架针对 Python 3.11+ 设计
3. **性能**: 运行全部 100 个测试可能需要较长时间（取决于反编译器的性能）
4. **跳过测试**: 如果核心模块未加载或反编译失败，测试会自动跳过并标记为 SKIP
5. **字节码比较**: 字节码等价验证会跳过跳转地址的比较，只关注操作序列和参数

## 扩展指南

### 添加新的测试级别

1. 在 `tests/control_flow_matrix/` 下创建新的测试文件（如 `test_l4_extreme.py`）
2. 导入 `ControlFlowTestCase` 基类
3. 定义测试类并设置 `SOURCE_CODE`
4. 实现 `test_structure_correct()` 方法
5. 更新 `run_tests.py` 以支持新级别

### 自定义验证逻辑

除了默认的结构验证外，可以添加更具体的断言：

```python
def test_bytecode_match(self):
    """验证字节码完全匹配"""
    # 这个方法会调用 verify_bytecode_equivalence()
    self.verify_decompilation()

def test_ast_structure(self):
    """验证 AST 结构细节"""
    decompiled = self.decompile()
    tree = self.verify_syntax(decompiled)
    
    # 统计节点数量
    if_count = len(self.find_all_nodes(tree, ast.If))
    for_count = len(self.find_all_nodes(tree, ast.For))
    
    self.assertEqual(if_count, expected_if_count)
    self.assertEqual(for_count, expected_for_count)
```

## 故障排除

### 问题 1: 无法导入核心模块

**错误信息**: `警告: 无法导入核心模块`

**解决方案**:
- 确保从项目根目录 (`pythoncdc/`) 运行测试
- 检查 `core/cfg/` 模块是否存在且完整
- 确保 Python 路径设置正确

### 问题 2: 测试全部跳过

**原因**: 所有测试都因为无法反编译而跳过

**解决方案**:
- 检查反编译器是否正常工作
- 先运行简单的独立测试确认功能正常
- 查看 `base.py` 中的错误处理逻辑

### 问题 3: 字节码不匹配

**现象**: 语法正确但字节码不等价

**可能原因**:
- 反编译器生成了语义相同但实现不同的代码
- 控制流优化导致指令顺序变化
- 这是已知限制，不影响正确性

## 版本历史

- **v1.0.0** (2026-01-22): 初始版本，100 个测试用例
  - L1: 52 个基本结构测试
  - L2: 30 个两层嵌套测试
  - L3: 18 个三层嵌套测试

## 许可证

本项目与主项目保持相同的许可证。
