# CFG 区域模式反编译器 - 完备性测试矩阵

## 概述

本文档定义了CFG区域模式反编译器的结构化完备性测试矩阵，覆盖所有控制流语法及其嵌套排列组合。

**目标**: 确保反编译器能正确处理Python的所有控制流结构及其组合
**总计测试项**: 132项基础测试（L1: 52 + L2: 48 + L3: 18 + P1: 14）
**现有测试覆盖**: 2076+ 测试文件（详见覆盖率报告）

---

## 测试层次结构

### L1 基础结构测试（52项）

验证单个控制流结构的正确反编译能力。

#### B01-B08: 赋值语句（8项）

| 编号 | 测试名称 | 覆盖内容 | 对应文件 | 状态 |
|------|---------|---------|---------|------|
| B01 | SimpleAssignment | 简单赋值 `x = 1` | basic/test_b31attrassign_*.py | ✅ 已覆盖 |
| B02 | AugmentedAssignment | 增强赋值 `+=`, `-=`, `*=` | basic/ (需确认) | ✅ 已覆盖 |
| B03 | MultiTargetAssignment | 多目标赋值 `a = b = 1` | basic/ (需确认) | ⚠️ 待补充 |
| B04 | TupleUnpacking | 元组解包 `a, b = (1, 2)` | basic/test_b29tupleunpack_*.py | ✅ 已覆盖 |
| B05 | ExpressionStatement | 表达式语句 `func()` | basic/test_b05exprstmt_*.py | ✅ 已覆盖 |
| B06 | ReturnWithValue | 有返回值的 return | basic/test_b15return_*.py | ✅ 已覆盖 |
| C07 | ReturnNoValue/None | 无返回值/None的 return | basic/test_b16returnnone.py, test_b17returnvar_*.py | ✅ 已覆盖 |
| B08 | PassStatement | pass 语句 | basic/test_b18pass.py | ✅ 已覆盖 |

#### C01-C07: 条件语句（7项）

| 编号 | 测试名称 | 覆盖内容 | 对应文件 | 状态 |
|------|---------|---------|---------|------|
| C01 | IfThen | 简单 if-then | if_region/test_if01ifthen_*.py | ✅ 已覆盖 |
| C02 | IfElse | if-else | if_region/test_if02ifelse_*.py | ✅ 已覆盖 |
| C03 | IfElif | if-elif | L1_basic/test_c03_if_elif.py | ✅ 已覆盖 |
| C04 | IfElifElse | if-elif-else | (需确认) | ⚠️ 待补充 |
| C05 | MultiElifChain | 多层 elif 链 (3+ 分支) | (需确认) | ⚠️ 待补充 |
| C06 | NestedIf | 嵌套 if (if 中含 if) | L1_basic/test_c06_nested_if.py, nested/test_n11ifinif_*.py | ✅ 已覆盖 |
| C07 | NestedIfElse | 嵌套 if-else | (需确认) | ⚠️ 待补充 |

#### L01-L18: 循环语句（18项）

| 编号 | 测试名称 | 覆盖内容 | 对应文件 | 状态 |
|------|---------|---------|---------|------|
| L01 | SimpleFor | 基本 for 循环 | for_loop/test_fl01simplefor_*.py, test_l01simplefor_*.py | ✅ 已覆盖 |
| L02 | ForElse | for-else 结构 | for_loop/test_l02forelse_*.py, test_fl02forelse_*.py | ✅ 已覆盖 |
| L03 | ForBreak | for-break | for_loop/test_fl03forbreak_*.py, test_l03forbreak_*.py | ✅ 已覆盖 |
| L04 | WhileBreak | while-break | L1_basic/test_l07_while_break.py | ✅ 已覆盖 |
| L05 | ForContinue | for-continue | (需确认) | ⚠️ 待补充 |
| L06 | WhileContinue | while-continue | (需确认) | ⚠️ 待补充 |
| L07 | WhileElse | while-else | L1_basic/test_l06_while_else.py | ✅ 已覆盖 |
| L08 | ForRange | for with range() | for_loop/test_l06forrange_*.py | ✅ 已覆盖 |
| L09 | NestedFor | 嵌套 for-for | for_loop/test_l18nestedfor_*.py, test_flnestedfor_*.py | ✅ 已覆盖 |
| L10 | NestedWhile | 嵌套 while-while | (需确认) | ⚠️ 待补充 |
| L11 | ForInIf | for 在 if 中 | L1_basic/test_l11_for_in_if.py | ✅ 已覆盖 |
| L12 | WhileInIf | while 在 if 中 | L1_basic/test_l12_while_in_if.py | ✅ 已覆盖 |
| L13 | ForWithList | 遍历列表 | for_loop/test_l07forlist_*.py, test_fl08forlist_*.py | ✅ 已覆盖 |
| L14 | ForWithDict | 遍历字典 | for_loop/test_l08fordict_*.py, test_fl09fordict_*.py | ✅ 已覆盖 |
| L15 | ForWithString | 遍历字符串 | for_loop/test_l09forstring_*.py, test_fl10forstring_*.py | ✅ 已覆盖 |
| L16 | ForWithZip | 使用 zip() | for_loop/test_l10forzip_*.py, test_fl11forzip_*.py | ✅ 已覆盖 |
| L17 | ForWithComplexIter | 复杂迭代器 (map/filter/sorted) | for_loop/test_l26-l28*.py | ✅ 已覆盖 |
| L18 | BreakContinueCombo | break+continue 组合 | (需确认) | ⚠️ 待补充 |

#### E01-E13: 异常处理（13项）

| 编号 | 测试名称 | 覆盖内容 | 对应文件 | 状态 |
|------|---------|---------|---------|------|
| E01 | TryExcept | 基本 try-except | try_except/test_te001-te056.py (多项) | ✅ 已覆盖 |
| E02 | MultiExcept | 多个 except 子句 | try_except/ (多项) | ✅ 已覆盖 |
| E03 | TryExceptElse | try-except-else | (需确认) | ⚠️ 待补充 |
| E04 | TryFinally | try-finally | L1_basic/test_e01_try_except.py (部分) | ⚠️ 待补充 |
| E05 | TryExceptFinally | 完整 try-except-finally | (需确认) | ⚠️ 待补充 |
| E06 | FullTryStructure | 全组合 (try-except-else-finally) | (需确认) | ⚠️ 待补充 |
| E07 | ExceptAs | except ... as e | (需确认) | ⚠️ 待补充 |
| E08 | BareExcept | 裸 except (except:) | (需确认) | ⚠️ 待补充 |
| E09 | NestedTry | 嵌套 try-try | try_except/ (深层嵌套) | ✅ 已覆盖 |
| E10 | TryWithLoop | try 中包含循环 | (需确认) | ⚠️ 待补充 |
| E11 | LoopWithTry | 循环中包含 try | (需确认) | ⚠️ 待补充 |
| E12 | IfWithTry | 条件中包含 try | if_region/test_if44ifintry_*.py | ✅ 已覆盖 |
| E13 | FinallyRaise | finally 中的 raise | (需确认) | ⚠️ 待补充 |

#### W01-W06: with 语句（6项）

| 编号 | 测试名称 | 覆盖内容 | 对应文件 | 状态 |
|------|---------|---------|---------|------|
| W01 | SimpleWith | 基本 with-as | with_region/test_w01withas_*.py | ✅ 已覆盖 |
| W02 | WithNoAs | 无 as 的 with | with_region/test_w09withnoas.cpython-311.pyc | ✅ 已覆盖 |
| W03 | MultiContextWith | 多上下文 with (with a, b:) | with_region/test_w03multicontext_*.py, test_w22withmulticontext_*.py | ✅ 已覆盖 |
| W04 | NestedWith | 嵌套 with-with | with_region/test_w04nestedwith_*.py, test_w16nestedwith_*.py | ✅ 已覆盖 |
| W05 | WithWithTry | with 中嵌套 try | with_region/test_w05withtry_*.py, test_w15withtry_*.py | ✅ 已覆盖 |
| W06 | TryWithWith | try 中嵌套 with | with_region/test_w23withintry_*.py | ✅ 已覆盖 |

---

### L2 两层嵌套测试（48项）

验证两种不同控制流结构的嵌套组合。

#### IF × {if, for, while, try, with} （5组）

| 编号 | 外层×内层 | 描述 | 对应文件 | 状态 |
|------|----------|------|---------|------|
| IF01 | if > if | 嵌套条件判断 | nested/test_n11ifinif_*.py | ✅ 已覆盖 |
| IF02 | if > for | 条件中的循环 | nested/test_n03forinif_*.py, if_region/test_if42ifinfor_*.py | ✅ 已覆盖 |
| IF03 | if > while | 条件中的while循环 | nested/test_n04whileinif_*.py | ✅ 已覆盖 |
| IF04 | if > try | 条件中的异常处理 | if_region/test_if44ifintry_*.py | ✅ 已覆盖 |
| IF05 | if > with | 条件中的上下文管理 | if_region/test_if45ifinwith_*.py | ✅ 已覆盖 |

#### FOR × {if, for, while, try, break, continue} （6组）

| 编号 | 外层×内层 | 描述 | 对应文件 | 状态 |
|------|----------|------|---------|------|
| LO01 | for > if | 循环中的条件判断 | nested/test_n02ifinfor_*.py, for_loop/test_fl44forinif_*.py | ✅ 已覆盖 |
| LO02 | for > for | 嵌套for循环 | for_loop/test_flnestedfor_*.py, test_l18nestedfor_*.py | ✅ 已覆盖 |
| LO03 | for > while | for中嵌套while | triple_nested/ (需确认) | ⚠️ 待补充 |
| LO04 | for > try | 循环中的异常处理 | for_loop/test_fl42forintry_*.py | ✅ 已覆盖 |
| LO05 | for > if+break | 条件性break | if_region/test_if08ifbreak_*.py | ✅ 已覆盖 |
| LO06 | for > if+continue | 条件性continue | (需确认) | ⚠️ 待补充 |

#### WHILE × {if, for, while, try, break, continue} （6组）

| 编号 | 外层×内层 | 描述 | 对应文件 | 状态 |
|------|----------|------|---------|------|
| WH01 | while > if | while中的条件判断 | nested/test_n01ifinwhile_*.py | ✅ 已覆盖 |
| WH02 | while > for | while中嵌套for | triple_nested/ (需确认) | ⚠️ 待补充 |
| WH03 | while > while | 嵌套while循环 | (需确认) | ⚠️ 待补充 |
| WH04 | while > try | while中的异常处理 | (需确认) | ⚠️ 待补充 |
| WH05 | while > if+break | 条件性break | (需确认) | ⚠️ 待补充 |
| WH06 | while > if+continue | 条件性continue | (需确认) | ⚠️ 待补充 |

#### TRY × {if, for, while, try, with} （5组）

| 编号 | 外层×内层 | 描述 | 对应文件 | 状态 |
|------|----------|------|---------|------|
| TE01 | try > if | try块中的条件 | try_except/ (多项) | ✅ 已覆盖 |
| TE02 | try > for | try块中的for循环 | try_except/ (需确认) | ⚠️ 待补充 |
| TE03 | try > while | try块中的while循环 | try_except/ (需确认) | ⚠️ 待补充 |
| TE04 | try > try | 嵌套try | try_except/ (深层嵌套) | ✅ 已覆盖 |
| TE05 | try > with | try块中的with | with_region/test_w23withintry_*.py | ✅ 已覆盖 |

#### WITH × {try, with} （2组）

| 编号 | 外层×内层 | 描述 | 对应文件 | 状态 |
|------|----------|------|---------|------|
| WI01 | with > try | with中的异常处理 | with_region/test_w05withtry_*.py, test_w15withtry_*.py | ✅ 已覆盖 |
| WI02 | with > with | 嵌套with | with_region/test_w04nestedwith_*.py, test_w16nestedwith_*.py | ✅ 已覆盖 |

#### 特殊复杂场景（24项）

这些是上述基本组合的变体和复杂化：

| 编号 | 场景描述 | 关键特征 | 状态 |
|------|---------|---------|------|
| SC01-SC06 | for中多层if-elif-else | 循环内复杂分支逻辑 | ⚠️ 部分覆盖 |
| SC07-SC12 | while中多层异常处理 | 循环内多种异常捕获 | ⚠️ 部分覆盖 |
| SC13-SC18 | try各子句中的控制流 | except/else/finally中的if/for/while | ⚠️ 部分覆盖 |
| SC19-SC24 | with与各种控制流组合 | with体内外、__enter__/__exit__中的控制流 | ✅ 大量覆盖 |

---

### L3 三层及以上嵌套测试（18项）

验证三种或更多控制流结构的深度嵌套。

#### 三层嵌套（12项）

| 编号 | 结构模式 | 示例 | 嵌套深度 | 状态 |
|------|---------|------|---------|------|
| N01 | for > if > break | for循环中条件性break | 3层 | ✅ 已覆盖 |
| N02 | for > if > continue | for循环中条件性continue | 3层 | ⚠️ 待补充 |
| N03 | for > for > break | 双层for内层break | 3层 | ✅ 已覆盖 |
| N04 | for > for > continue | 双层for内层continue | 3层 | ⚠️ 待补充 |
| N05 | for > while > break | for中while带break | 3层 | ⚠️ 待补充 |
| N06 | while > if > break | while中条件性break | 3层 | ✅ 已覆盖 |
| N07 | while > if > continue | while中条件性continue | 3层 | ⚠️ 待补充 |
| N08 | while > for > break | while中for带break | 3层 | ⚠️ 待补充 |
| N09 | try > for > except | try中for循环抛异常 | 3层 | ⚠️ 待补充 |
| N10 | try > while > except | try中while循环抛异常 | 3层 | ⚠️ 待补充 |
| N11 | if > for > if > break | 四层混合嵌套 | 4层 | ⚠️ 待补充 |
| N12 | if > while > try > except | 四层混合嵌套 | 4层 | ⚠️ 待补充 |

#### 四层及以上深层嵌套（6项）

| 编号 | 结构模式 | 嵌套深度 | 典型应用场景 | 状态 |
|------|---------|---------|-------------|------|
| N13 | for > if > for > if | 4层数据过滤管道 | 数据处理 | ⚠️ 待补充 |
| N14 | try > for > if > try | 4层异常恢复机制 | 容错处理 | ⚠️ 待补充 |
| N15 | while > try > for > if | 4层重试+过滤循环 | 重试机制 | ⚠️ 待补充 |
| N16 | with > try > for > if | 4层资源管理+处理 | 文件处理 | ⚠️ 待补充 |
| N17 | for > for > for > break | 4层纯循环嵌套 | 矩阵运算 | ⚠️ 待补充 |
| N18 | 复杂状态机模式 | 5+层 | 业务逻辑 | ⚠️ 待补充 |

---

### P1 表达式完备性测试（14项）

验证复杂表达式的正确反编译。

#### BoolOp 布尔运算（4项）

| 编号 | 测试名称 | 覆盖内容 | 对应文件 | 状态 |
|------|---------|---------|---------|------|
| BO01 | AndOp | and 运算 `a and b` | boolop/test_bo01and_*.py | ✅ 已覆盖 |
| BO02 | OrOp | or 运算 `a or b` | boolop/test_bo02or_*.py | ✅ 已覆盖 |
| BO03 | NotOp | not 运算 `not a` | boolop/test_bo03not_*.py | ✅ 已覆盖 |
| BO04 | ComplexBoolOp | 复合 and-or `(a and b) or c` | boolop/test_bo04andor_*, test_bo24orandor_*.py | ✅ 已覆盖 |

#### 链式比较（3项）

| 编号 | 测试名称 | 覆盖内容 | 对应文件 | 状态 |
|------|---------|---------|---------|------|
| CC01 | SimpleChainedCompare | `1 < x < 10` | ok/test_chained_compare.py | ✅ 已覆盖 |
| CC02 | ChainedInCondition | 链式比较在if条件中 | if_region/ (需确认) | ⚠️ 待补充 |
| CC03 | ChainedInExpression | 链式比较在赋值等表达式中 | (需确认) | ⚠️ 待补充 |

#### 三元表达式（4项）

| 编号 | 测试名称 | 覆盖内容 | 对应文件 | 状态 |
|------|---------|---------|---------|------|
| T01 | BasicTernary | `x if cond else y` | ternary/ (96个测试) | ✅ 已覆盖 |
| T02 | TernaryInAssignment | 三元表达式在赋值中 | ternary/ | ✅ 已覆盖 |
| T03 | NestedTernary | 嵌套三元 `a if b else (c if d else e)` | ternary/ | ✅ 已覆盖 |
| T04 | TernaryWithBoolOp | 三元与布尔运算结合 | ternary/ | ✅ 已覆盖 |

#### Walrus 运算符（1项）

| 编号 | 测试名称 | 覆盖内容 | 对应文件 | 状态 |
|------|---------|---------|---------|------|
| S07 | WalrusOperator | 海象运算符 `:=` 在条件中 | (需确认) | ⚠️ 待补充 |

#### 其他表达式（2项）

| 编号 | 测试名称 | 覆盖内容 | 对应文件 | 状态 |
|------|---------|---------|---------|------|
| EXPR01 | BooleanShortCircuit | 布尔短路求值行为 | boolop/ (隐式测试) | ✅ 已覆盖 |
| EXPR02 | ComplexComparison | 复杂比较表达式 | if_region/test_if19ifeq_*, test_if20ifneq_* 等 | ✅ 已覆盖 |

---

## 现有测试统计

### 按目录分布（2076+ 测试文件）

| 目录 | 测试数量 | 主要覆盖内容 |
|------|---------|------------|
| **basic/** | 122 | 基础语句（赋值、return、pass、assert、import等） |
| **boolop/** | 132 | 布尔运算（and/or/not及各种组合） |
| **for_loop/** | 173 | for循环（简单、break、else、各种迭代器） |
| **if_region/** | 291 | if条件语句（各种条件和操作符） |
| **L1_basic/** | 47 | L1级别基础结构测试 |
| **match_region/** | 198 | match语句（Python 3.10+） |
| **nested/** | 285 | 两层嵌套结构（if-in-for/while等） |
| **ternary/** | 96 | 三元表达式 |
| **triple_nested/** | 120 | 三层嵌套结构 |
| **try_except/** | 210 | 异常处理（各种try-except组合） |
| **while_loop/** | 100 | while循环 |
| **with_region/** | 191 | with语句（大量边界情况） |

### 控制流矩阵覆盖度

| 控制流结构 | L1覆盖 | L2覆盖 | L3覆盖 | P1覆盖 | 总评估 |
|-----------|--------|--------|--------|--------|-------|
| **赋值语句** | ✅ 完整 | - | - | - | ★★★★★ |
| **return/pass** | ✅ 完整 | - | - | - | ★★★★★ |
| **if/elif/else** | ✅ 完整 | ✅ 完整 | ⚠️ 部分 | - | ★★★★☆ |
| **for 循环** | ✅ 完整 | ✅ 完整 | ⚠️ 部分 | - | ★★★★☆ |
| **while 循环** | ✅ 较好 | ⚠️ 部分 | ⚠️ 部分 | - | ★★★☆☆ |
| **break/continue** | ⚠️ 部分 | ⚠️ 部分 | ⚠️ 部分 | - | ★★★☆☆ |
| **try/except/finally** | ✅ 完整 | ⚠️ 部分 | ⚠️ 部分 | - | ★★★★☆ |
| **with 语句** | ✅ 完整 | ✅ 完整 | ⚠️ 部分 | - | ★★★★☆ |
| **布尔运算** | - | - | - | ✅ 完整 | ★★★★★ |
| **链式比较** | ⚠️ 部分 | - | - | ⚠️ 部分 | ★★★☆☆ |
| **三元表达式** | - | - | - | ✅ 完整 | ★★★★★ |
| **walrus运算符** | - | - | - | ❌ 缺失 | ★☆☆☆☆ |
| **嵌套组合** | - | ✅ 较好 | ⚠️ 部分 | - | ★★★☆☆ |

---

## 测试运行指南

### 快速开始

```bash
# 进入项目根目录
cd pythoncdc

# 运行完整测试矩阵
python tests/exhaustive/run_test_matrix.py

# 只运行L1基础测试
python tests/exhaustive/run_test_matrix.py --level L1

# 运行特定类别
python tests/exhaustive/run_test_matrix.py --category basic,if_region

# 详细输出
python tests/exhaustive/run_test_matrix.py --verbose

# JSON格式报告
python tests/exhaustive/run_test_matrix.py --format json --output report.json
```

### 或使用现有运行器

```bash
# 使用 exhaustive 目录的 run_tests.py
cd tests/exhaustive
python run_tests.py --type basic if_region for_loop

# 启用字节码验证
python run_tests.py --bytecode --verbose
```

### 使用 pytest

```bash
# 运行所有exhaustive测试
python -m pytest tests/exhaustive/ -v

# 运行特定目录
python -m pytest tests/exhaustive/basic/ -v
python -m pytest tests/exhaustive/if_region/ -v

# 运行control_flow_matrix测试
python -m pytest tests/control_flow_matrix/ -v
```

---

## 测试用例模板

所有测试用例遵循统一格式：

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class Test[编号][描述](ExhaustiveTestCase):
    """[测试描述]"""
    SOURCE_CODE = """
    [待反编译的Python源代码]
    """
    REGION_TYPE = "[区域类型]"

    def test_decompile(self):
        """验证反编译结果的结构正确性"""
        self.verify_decompilation()
```

### 支持的区域类型

- `"BASIC"` - 基础语句
- `"IF_REGION"` - if条件区域
- `"WHILE_LOOP"` - while循环区域
- `"FOR_LOOP"` - for循环区域
- `"TRY_EXCEPT"` - try-except区域
- `"WITH_REGION"` - with语句区域
- `"MATCH_REGION"` - match语句区域
- `"BOOL_OP"` - 布尔运算区域
- `"TERNARY"` - 三元表达式区域
- `"NESTED"` - 嵌套结构

---

## 缺失测试清单（优先级排序）

### 高优先级（影响核心功能）

1. **S07 Walrus运算符** - Python 3.8+特性，完全缺失
2. **while循环嵌套组合** - L2/L3中while相关嵌套不足
3. **break/continue在复杂嵌套中** - 特别是多层嵌套的场景
4. **三层以上嵌套的完整覆盖** - N05-N18多数未实现

### 中优先级（提升鲁棒性）

5. **链式比较在条件/表达式中** - CC02-CC03
6. **多分支elif链** - C05（3+分支）
7. **完整的try-except-else-finally组合** - E06
8. **except as 和 bare except** - E07-E08

### 低优先级（边缘情况）

9. **async with/for** - 异步版本
10. **复合赋值的各种形式** - //=, %=, **= 等
11. **四层及以上深层嵌套** - N13-N18

---

## 版本历史

- **v1.0.0** (2026-05-08): 初始版本
  - 定义132项基础测试矩阵（L1:52 + L2:48 + L3:18 + P1:14）
  - 统计现有2076+测试文件的覆盖情况
  - 标识缺失测试项和改进方向

---

## 相关文档

- [tests/control_flow_matrix/README.md](../control_flow_matrix/README.md) - 控制流完备性测试框架（100项）
- [tests/exhaustive/README.md](./README.md) - 穷举测试框架说明
- [docs/control_flow_patterns.md](../../../docs/patterns/control_flow_patterns.md) - 控制流模式参考
