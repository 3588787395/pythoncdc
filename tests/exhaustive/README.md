# CFG反编译器完备性测试工具

自动化测试运行脚本和报告生成器，用于验证CFG反编译器的完备性。

## 📋 目录

- [功能特性](#功能特性)
- [安装依赖](#安装依赖)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
- [命令行参数](#命令行参数)
- [支持的测试类型](#支持的测试类型)
- [报告格式说明](#报告格式说明)
- [常见问题FAQ](#常见问题faq)

## 功能特性

✅ **自动发现测试** - 自动扫描所有测试目录中的测试用例
✅ **分类统计** - 按区域类型（basic, if_region, for_loop等）分类统计
✅ **目标对比** - 内置各类型的目标通过率，自动对比达成情况
✅ **多格式报告** - 支持文本和JSON两种报告格式
✅ **详细日志** - 可选的详细输出模式，显示每个测试的结果
✅ **错误追踪** - 记录失败/错误测试的详细信息

## 安装依赖

### 系统要求

- Python 3.8+
- unittest（Python标准库）

### 环境准备

确保项目结构正确：
```
pythoncdc/
├── tests/
│   └── exhaustive/
│       ├── base.py                    # 测试基类
│       ├── run_completeness_tests.py  # 本脚本
│       ├── basic/                     # 基础语句测试
│       ├── if_region/                 # 条件分支测试
│       ├── for_loop/                  # for循环测试
│       ├── while_loop/                # while循环测试
│       ├── try_except/                # 异常处理测试
│       ├── with_region/               # 上下文管理测试
│       ├── nested/                    # 嵌套结构测试
│       ├── match_region/              # 模式匹配测试
│       ├── boolop/                    # 布尔运算测试
│       └── ternary/                   # 三元表达式测试
```

## 快速开始

### 1. 运行所有测试

```bash
cd pythoncdc/tests/exhaustive
python run_completeness_tests.py
```

### 2. 查看报告

测试完成后会自动生成 `full_report_v5.txt` 报告文件。

## 使用方法

### 基本用法

```bash
# 运行所有类型的测试
python run_completeness_tests.py

# 只运行特定类型的测试
python run_completeness_tests.py --type if_region

# 显示详细的测试过程
python run_completeness_tests.py --verbose

# 自定义输出文件名
python run_completeness_tests.py --output my_report.txt

# 输出JSON格式报告
python run_completeness_tests.py --format json
```

### 高级用法

```bash
# 运行if_region测试，显示详情，保存为特定文件
python run_completeness_tests.py -t if_region -v -o if_test_report.txt

# 运行多个场景并生成JSON报告用于CI/CD
python run_completeness_tests.py -f json -o ci_report.json

# 只运行基础测试并查看是否达标
python run_completeness_tests.py -t basic -v
```

## 命令行参数

| 参数 | 缩写 | 默认值 | 说明 |
|------|------|--------|------|
| `--type` | `-t` | None | 指定要运行的测试类型（见下方支持的类型列表） |
| `--output` | `-o` | `full_report_v5.txt` | 输出报告的文件名 |
| `--verbose` | `-v` | False | 显示详细输出（每个测试的通过/失败信息） |
| `--format` | `-f` | `text` | 报告格式：`text` 或 `json` |

## 支持的测试类型

| 类型名称 | 描述 | 目标通过率 | 测试内容 |
|----------|------|------------|----------|
| `basic` | 基础语句 | ≥85% | 赋值、返回、导入、删除、全局/非局部变量 |
| `if_region` | 条件分支 | ≥97% | if/elif/else、嵌套if、比较运算符 |
| `for_loop` | for循环 | ≥85% | 简单for、for-else、break/continue、迭代器 |
| `while_loop` | while循环 | 100% | 简单while、while-else、嵌套while |
| `try_except` | 异常处理 | ≥75% | try/except/finally、多层异常、异常链 |
| `with_region` | 上下文管理 | ≥80% | with语句、嵌套with |
| `nested` | 嵌套结构 | ≥80% | 多层嵌套的控制流组合 |
| `match_region` | 模式匹配 | ≥85% | match/case语句（Python 3.10+） |
| `boolop` | 布尔运算 | ≥80% | and/or/not及其组合 |
| `ternary` | 三元表达式 | ≥85% | 条件表达式 |

## 报告格式说明

### 文本报告格式

生成的文本报告包含以下部分：

#### 1. 汇总统计表
```
📊 汇总统计
--------------------------------------------------------------------------------
区域类型              描述           总数     通过     失败     错误     跳过    通过率
--------------------------------------------------------------------------------
basic               基础语句        120      115       3       2       0      95.8%
if_region           条件分支         85       83       1       1       0      97.6%
...
总计                                850      800      30      20       0      94.1%
```

#### 2. 目标达成情况
```
🎯 目标达成情况
--------------------------------------------------------------------------------
区域类型              目标       实际       差距         状态
--------------------------------------------------------------------------------
basic                 85%      95.8%    +10.8%       ✅ 达成
if_region             97%      97.6%     +0.6%       ✅ 达成
...
目标达成率: 9/10 (90.0%)
```

#### 3. 失败/错误详情
列出前20个失败或出错的测试用例及其错误信息。

#### 4. 总体评估
```
📈 总体评估
--------------------------------------------------------------------------------
总体通过率: 94.12%
评估等级: ★★★★★ 优秀 (>=95%)  # 或其他等级
目标达成率: 90.0%
```

### JSON报告格式

JSON报告包含完整的结构化数据：

```json
{
  "metadata": {
    "version": "5.0",
    "timestamp": "2026-05-06T10:30:00",
    "duration": 125.45,
    "generator": "CompletenessTestRunner"
  },
  "summary": {
    "total_tests": 850,
    "passed": 800,
    "failed": 30,
    "errors": 20,
    "skipped": 0,
    "pass_rate": 94.12
  },
  "targets": {
    "basic": {
      "target": 85,
      "actual": 95.8,
      "achieved": true,
      "description": "基础语句"
    }
  },
  "by_region_type": {
    "basic": {
      "total": 120,
      "passed": 115,
      "failed": 3,
      "errors": 2,
      "skipped": 0,
      "pass_rate": 95.8,
      "test_details": [...]
    }
  },
  "errors": [
    {
      "region_type": "basic",
      "test": "test_b01simpleassign_x_0.py",
      "error": "AssertionError: ..."
    }
  ]
}
```

**字段说明：**

- `metadata`: 报告元数据（版本、时间戳、耗时）
- `summary`: 总体统计摘要
- `targets`: 各类型的目标对比结果
- `by_region_type`: 各区域类型的详细统计
- `errors`: 所有失败的测试及错误信息

## 常见问题FAQ

### Q1: 运行时提示"未找到测试文件"怎么办？

**A:** 确保测试文件已经生成。如果测试目录为空，需要先运行测试生成脚本：
```bash
python generate_tests.py --type all
```

### Q2: 如何只运行某个特定的测试文件？

**A:** 当前版本不支持单个文件运行。建议使用 `--type` 参数按类型筛选，或者直接使用unittest：
```bash
python -m unittest tests.exhaustive.basic.test_b01simpleassign_a_3
```

### Q3: 报告中的"目标通过率"是什么意思？

**A:** 这是根据反编译器对不同代码结构的处理能力设定的预期目标。例如：
- `if_region` 目标 97%，因为条件分支是核心功能，应该高度可靠
- `try_except` 目标 75%，因为异常处理的边界情况较多

如果某类型未达到目标，说明该区域的反编译逻辑可能存在问题。

### Q4: 如何在CI/CD中集成？

**A:** 推荐使用JSON格式输出：
```yaml
# GitHub Actions示例
- name: Run Completeness Tests
  run: |
    cd pythoncdc/tests/exhaustive
    python run_completeness_tests.py -f json -o report.json
    
- name: Check Results
  run: |
    python -c "
    import json
    with open('report.json') as f:
        data = json.load(f)
    rate = data['summary']['pass_rate']
    print(f'Pass rate: {rate}%')
    if rate < 85:
        exit(1)
    "
```

### Q5: 测试运行很慢怎么办？

**A:** 可以尝试：
1. 使用 `--type` 参数只运行特定类型
2. 避免使用 `--verbose` 参数（会降低I/O开销）
3. 确保没有不必要的调试输出

### Q6: 如何添加新的测试类型？

**A:** 
1. 在 `tests/exhaustive/` 下创建新目录（如 `new_type/`）
2. 在 `run_completeness_tests.py` 的 `TEST_DIRS` 字典中添加映射
3. 在 `TARGETS` 字典中设定目标通过率
4. 创建继承自 `ExhaustiveTestCase` 的测试文件

示例：
```python
# 在 run_completeness_tests.py 中添加
TEST_DIRS['new_type'] = 'tests/exhaustive/new_type/'
TARGETS['new_type'] = {'target': 90, 'description': '新类型描述'}
```

### Q7: 报告文件太大怎么办？

**A:** 文本报告默认只显示前20个错误。如果需要完整错误列表，可以：
1. 使用JSON格式获取所有错误数据
2. 或者修改脚本中的 `all_errors[:20]` 为更大的数字

### Q8: Python版本兼容性？

**A:** 脚本要求 Python 3.8+，主要使用了：
- `typing` 模块的类型注解
- f-string格式化
- `dataclass`（可选）

对于Python 3.7及以下版本，需要进行少量修改。

## 相关文件

- [`base.py`](./base.py) - 测试基类定义
- [`run_tests.py`](./run_tests.py) - 旧版测试运行器
- [`generate_tests.py`](./generate_tests.py) - 测试用例生成器

## 版本历史

- **V5.0** (2026-05-06): 初始版本
  - 完整的测试发现和运行机制
  - 目标对比分析
  - 文本和JSON双格式报告
  - 详细的命令行接口

---

**提示**: 如有问题或建议，请检查测试基类 [`base.py`](./base.py) 的实现，确保理解测试框架的工作原理。
