#!/usr/bin/env python3
"""
边界情况测试 - 反编译器边界条件验证

包含5类共25个边界情况测试用例：
- Class 1: 空体边界 (BND-01到BND-05)
- Class 2: 单行边界 (BND-06到BND-10)
- Class 3: 深层边界 (BND-11到BND-15)
- Class 4: 复杂表达式边界 (BND-16到BND-20)
- Class 5: Python版本边界 (BND-21到BND-25)

理论依据（编译器边界测试理论）：
- 空体处理：验证编译器对最小有效结构的处理能力
- 单行优化：测试编译器对紧凑语法的支持
- 深层嵌套压力：发现递归/堆栈限制问题
- 复杂表达式：验证语法解析器的健壮性
- 版本兼容性：确保跨Python版本的稳定性
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.test_functional_verification import (
    DecompilationVerifier,
    VerificationStatus,
    create_test_verifier
)


class TestBoundaryCases:
    """边界情况测试类 - 覆盖反编译器的各类边界条件"""

    @classmethod
    def setup_class(cls):
        """初始化验证器"""
        cls.verifier = create_test_verifier()

    def verify_boundary(self, source: str, min_equivalence: float = 0.85):
        """
        边界条件验证辅助方法

        Args:
            source: Python源代码字符串
            min_equivalence: 最小等价率要求

        Returns:
            VerificationReport: 验证报告
        """
        report = self.verifier.verify_decompile(source)

        assert report.status in [VerificationStatus.PASSED, VerificationStatus.WARNING], (
            f"边界测试失败！状态: {report.status.value}\n"
            f"错误: {report.errors}\n"
            f"警告: {report.warnings}\n"
            f"等价率: {report.equivalence_rate:.2%}\n"
            f"反编译结果:\n{report.decompiled_source[:300]}"
        )

        assert report.equivalence_rate >= min_equivalence, (
            f"等价率 {report.equivalence_rate:.2%} 低于阈值 {min_equivalence:.2%}"
        )

        return report

    # ========================================================================
    # Class 1: 空体边界 (BND-01 到 BND-05)
    # ========================================================================

    def test_BND_01_empty_if_body(self):
        """BND-01: 空if体 - if True: pass

        边界类型：空控制流体
        目的：验证反编译器对仅包含pass语句的最小if体的处理能力
        测试要点：if语句结构保持、pass语句正确还原
        """
        source = '''
def target():
    if True:
        pass
'''
        report = self.verify_boundary(source)
        print(f"\nBND-01 (empty if): 等价率={report.equivalence_rate:.2%}")

    def test_BND_02_empty_for_body(self):
        """BND-02: 空for体 - for i in []: pass

        边界类型：空循环体
        目的：验证反编译器对空for循环的处理能力
        测试要点：for迭代器、空循环体、pass语句
        """
        source = '''
def target():
    for i in []:
        pass
'''
        report = self.verify_boundary(source)
        print(f"\nBND-02 (empty for): 等价率={report.equivalence_rate:.2%}")

    def test_BND_03_empty_while_body(self):
        """BND-03: 空while体 - while False: pass

        边界类型：空条件循环体
        目的：验证反编译器对永远不会执行的while循环的处理能力
        测试要点：while条件判断、空循环体
        """
        source = '''
def target():
    while False:
        pass
'''
        report = self.verify_boundary(source)
        print(f"\nBND-03 (empty while): 等价率={report.equivalence_rate:.2%}")

    def test_BND_04_empty_try_body(self):
        """BND-04: 空try体 - try: pass except: pass

        边界类型：空异常处理体
        目的：验证反编译器对最小try-except结构的处理能力
        测试要点：try-except结构、空的try和except块
        """
        source = '''
def target():
    try:
        pass
    except:
        pass
'''
        report = self.verify_boundary(source)
        print(f"\nBND-04 (empty try): 等价率={report.equivalence_rate:.2%}")

    def test_BND_05_empty_with_body(self):
        """BND-05: 空with体 - with open('/dev/null') as f: pass

        边界类型：空上下文管理器体
        目的：验证反编译器对空with语句块的处理能力
        测试要点：上下文管理器、as子句、空with体
        """
        source = '''
def target():
    with open('/dev/null') as f:
        pass
'''
        report = self.verify_boundary(source)
        print(f"\nBND-05 (empty with): 等价率={report.equivalence_rate:.2%}")

    # ========================================================================
    # Class 2: 单行边界 (BND-06 到 BND-10)
    # ========================================================================

    def test_BND_06_single_line_if(self):
        """BND-06: 单行if - if x: y = 1

        边界类型：单行复合语句
        目的：验证反编译器对单行if语句的处理能力
        测试要点：紧凑if语法、单行赋值
        """
        source = '''
def target(x):
    if x:
        y = 1
'''
        report = self.verify_boundary(source)
        print(f"\nBND-06 (single line if): 等价率={report.equivalence_rate:.2%}")

    def test_BND_07_single_line_for(self):
        """BND-07: 单行for - for i in range(3): print(i)

        边界类型：单行循环体
        目的：验证反编译器对单行for循环的处理能力
        测试要点：for循环、range函数调用、函数调用作为循环体
        """
        source = '''
def target():
    for i in range(3):
        print(i)
'''
        report = self.verify_boundary(source)
        print(f"\nBND-07 (single line for): 等价率={report.equivalence_rate:.2%}")

    def test_BND_08_single_line_while(self):
        """BND-08: 单行while - while count > 0: do_something()

        边界类型：单行条件循环
        目的：验证反编译器对单行while循环的处理能力
        测试要点：while条件、函数调用作为循环体
        """
        source = '''
def target(count):
    while count > 0:
        do_something()
'''
        report = self.verify_boundary(source)
        print(f"\nBND-08 (single line while): 等价率={report.equivalence_rate:.2%}")

    def test_BND_09_single_line_expression(self):
        """BND-09: 单行表达式 - result = x if condition else y

        边界类型：三元表达式
        目的：验证反编译器对条件表达式的处理能力
        测试要点：三元运算符、条件表达式求值
        """
        source = '''
def target(x, condition, y):
    result = x if condition else y
'''
        report = self.verify_boundary(source)
        print(f"\nBND-09 (ternary expression): 等价率={report.equivalence_rate:.2%}")

    def test_BND_10_compound_single_line(self):
        """BND-10: 复合单行 - if x: for i in range(3): print(i)

        边界类型：嵌套单行语句
        目的：验证反编译器对if内嵌套for的单行组合的处理能力
        测试要点：if-for嵌套结构、多层单行语句
        """
        source = '''
def target(x):
    if x:
        for i in range(3):
            print(i)
'''
        report = self.verify_boundary(source)
        print(f"\nBND-10 (compound single line): 等价率={report.equivalence_rate:.2%}")

    # ========================================================================
    # Class 3: 深层边界 (BND-11 到 BND-15)
    # ========================================================================

    def test_BND_11_eight_layer_for_nesting(self):
        """BND-11: 8层for嵌套 - 8层嵌套的for循环

        边界类型：深层同构嵌套
        目的：验证反编译器对8层纯for循环嵌套的处理能力
        测试要点：深层嵌套结构保持、缩进正确性、控制流完整性
        """
        source = '''
def target():
    for i1 in range(10):
        for i2 in range(10):
            for i3 in range(10):
                for i4 in range(10):
                    for i5 in range(10):
                        for i6 in range(10):
                            for i7 in range(10):
                                for i8 in range(10):
                                    pass
'''
        report = self.verify_boundary(source, min_equivalence=0.82)
        print(f"\nBND-11 (8-layer for): 等价率={report.equivalence_rate:.2%}")

    def test_BND_12_seven_layer_mixed_nesting(self):
        """BND-12: 7层混合嵌套 - if>for>while>try>if>for>while (7层混合)

        边界类型：深层异构嵌套
        目的：验证反编译器对多种控制流混合深层嵌套的处理能力
        测试要点：不同控制流类型的交替嵌套、复杂结构识别
        """
        source = '''
def target(x):
    if True:
        for i in range(10):
            while x > 0:
                try:
                    if i > 0:
                        for j in range(5):
                            while j > 0:
                                pass
                except:
                    pass
'''
        report = self.verify_boundary(source, min_equivalence=0.80)
        print(f"\nBND-12 (7-layer mixed): 等价率={report.equivalence_rate:.2%}")

    @pytest.mark.xfail(reason="接近Python递归限制")
    @pytest.mark.slow
    def test_BND_13_fifteen_layer_for_nesting(self):
        """BND-13: 接近递归限制(15层for) - 15层for循环

        边界类型：极端深度嵌套
        目的：测试反编译器在接近Python递归限制时的行为
        测试要点：极限嵌套深度、栈溢出防护、优雅降级
        注意：此测试可能因接近Python递归限制而失败，使用xfail标记
        """
        source = '''
def target():
    for i1 in range(5):
        for i2 in range(5):
            for i3 in range(5):
                for i4 in range(5):
                    for i5 in range(5):
                        for i6 in range(5):
                            for i7 in range(5):
                                for i8 in range(5):
                                    for i9 in range(5):
                                        for i10 in range(5):
                                            for i11 in range(5):
                                                for i12 in range(5):
                                                    for i13 in range(5):
                                                        for i14 in range(5):
                                                            for i15 in range(5):
                                                                pass
'''
        report = self.verify_boundary(source, min_equivalence=0.75)
        print(f"\nBND-13 (15-layer for): 等价率={report.equivalence_rate:.2%}")

    def test_BND_14_ten_layer_if_elif_else_chain(self):
        """BND-14: 10层if-elif-else链 - 长条件链

        边界类型：长条件链
        目的：验证反编译器对长if-elif-else链的处理能力
        测试要点：多分支条件链、elif结构保持、else终止
        """
        source = '''
def target(x):
    if x == 1:
        y = 1
    elif x == 2:
        y = 2
    elif x == 3:
        y = 3
    elif x == 4:
        y = 4
    elif x == 5:
        y = 5
    elif x == 6:
        y = 6
    elif x == 7:
        y = 7
    elif x == 8:
        y = 8
    elif x == 9:
        y = 9
    else:
        y = 10
'''
        report = self.verify_boundary(source)
        print(f"\nBND-14 (10-layer if-elif-else): 等价率={report.equivalence_rate:.2%}")

    def test_BND_15_six_layer_multi_statement_deep(self):
        """BND-15: 6层每层多语句 - 深层+复杂体

        边界类型：深层+复杂体组合
        目的：验证反编译器对深层嵌套且每层包含多个语句的处理能力
        测试要点：深层嵌套 + 多语句体 + 变量赋值 + 条件判断
        """
        source = '''
def target(data):
    result = []
    for item1 in data:
        if item1:
            temp1 = process(item1)
            for item2 in temp1:
                if item2:
                    temp2 = transform(item2)
                    for item3 in temp2:
                        if isinstance(item3, int):
                            result.append(item3 * 2)
                        else:
                            result.append(str(item3))
'''
        report = self.verify_boundary(source, min_equivalence=0.82)
        print(f"\nBND-15 (6-layer multi-stmt): 等价率={report.equivalence_rate:.2%}")

    # ========================================================================
    # Class 4: 复杂表达式边界 (BND-16 到 BND-20)
    # ========================================================================

    def test_BND_16_complex_condition_expression(self):
        """BND-16: 复杂条件表达式 - if (a and b) or (c and d):

        边界类型：复杂布尔表达式
        目的：验证反编译器对复杂布尔逻辑表达式的处理能力
        测试要点：and/or组合、括号优先级、短路求值语义保持
        """
        source = '''
def target(a, b, c, d):
    if (a and b) or (c and d):
        result = True
    else:
        result = False
'''
        report = self.verify_boundary(source)
        print(f"\nBND-16 (complex condition): 等价率={report.equivalence_rate:.2%}")

    def test_BND_17_multiple_exception_capture(self):
        """BND-17: 多重异常捕获 - except (ValueError, TypeError, KeyError) as e:

        边界类型：多重异常元组
        目的：验证反编译器对多重异常捕获的处理能力
        测试要点：异常元组语法、as绑定变量、异常类型匹配
        """
        source = '''
def target():
    try:
        risky_operation()
    except (ValueError, TypeError, KeyError) as e:
        handle_error(e)
'''
        report = self.verify_boundary(source)
        print(f"\nBND-17 (multi exception): 等价率={report.equivalence_rate:.2%}")

    def test_BND_18_nested_context_manager(self):
        """BND-18: 嵌套上下文管理器 - with a: with b: with c:

        边界类型：多层上下文管理器嵌套
        目的：验证反编译器对嵌套with语句的处理能力
        测试要点：多层with嵌套、上下文管理顺序、缩进层次
        """
        source = '''
def target():
    with context_a() as a:
        with context_b() as b:
            with context_c() as c:
                process(a, b, c)
'''
        report = self.verify_boundary(source)
        print(f"\nBND-18 (nested with): 等价率={report.equivalence_rate:.2%}")

    def test_BND_19_chained_comparison(self):
        """BND-19: 链式比较 - if 0 < x < 10 and y != z:

        边界类型：链式比较操作符
        目的：验证反编译器对Python链式比较语法的处理能力
        测试要点：链式比较、and组合、不等操作符
        """
        source = '''
def target(x, y, z):
    if 0 < x < 10 and y != z:
        result = valid
    else:
        result = invalid
'''
        report = self.verify_boundary(source)
        print(f"\nBND-19 (chained comparison): 等价率={report.equivalence_rate:.2%}")

    @pytest.mark.skipif(sys.version_info < (3, 8), reason="需要Python 3.8+支持海象运算符")
    def test_BND_20_walrus_operator_in_condition(self):
        """BND-20: 海象运算符(3.8+) - if (n := len(s)) > 0:

        边界类型：海象运算符（赋值表达式）
        目的：验证反编译器对Python 3.8+海象运算符的处理能力
        测试要点：:=运算符、表达式内赋值、变量作用域
        版本要求：Python 3.8+
        """
        source = '''
def target(s):
    if (n := len(s)) > 0:
        process(n)
    return n
'''
        report = self.verify_boundary(source)
        print(f"\nBND-20 (walrus operator): 等价率={report.equivalence_rate:.2%}")

    # ========================================================================
    # Class 5: Python版本边界 (BND-21 到 BND-25)
    # ========================================================================

    @pytest.mark.skipif(sys.version_info < (3, 8), reason="需要Python 3.8+")
    def test_BND_21_walrus_operator_comprehensive(self):
        """BND-21: walrus operator (3.8+) - 海象运算符综合测试

        版本边界：Python 3.8新特性
        目的：全面验证反编译器对海象运算符的支持
        测试要点：:=在while、列表推导式、if中的使用
        版本要求：Python 3.8+
        """
        source = '''
def target(data):
    results = []
    while (n := len(data)) > 0:
        results.append(n)
        data = data[:-1]
    return [y for x in results if (y := x * 2) > 5]
'''
        report = self.verify_boundary(source, min_equivalence=0.82)
        print(f"\nBND-21 (walrus comprehensive): 等价率={report.equivalence_rate:.2%}")

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+支持match/case")
    def test_BND_22_match_case_statement(self):
        """BND-22: match/case (3.10+) - 结构化模式匹配

        版本边界：Python 3.10新特性
        目的：验证反编译器对match/case语句的处理能力
        测试要点：match语句、case模式匹配、通配符、守卫条件
        版本要求：Python 3.10+
        """
        source = '''
def target(value):
    match value:
        case 0:
            result = "zero"
        case 1 | 2:
            result = "one or two"
        case [x, y]:
            result = f"pair {x}, {y}"
        case {"name": name}:
            result = f"named {name}"
        case _:
            result = "other"
    return result
'''
        report = self.verify_boundary(source, min_equivalence=0.82)
        print(f"\nBND-22 (match/case): 等价率={report.equivalence_rate:.2%}")

    @pytest.mark.skipif(sys.version_info < (3, 11), reason="需要Python 3.11+支持ExceptionGroup")
    def test_BND_23_exception_group_except_star(self):
        """BND-23: ExceptionGroup/except* (3.11+) - 异常组与except*

        版本边界：Python 3.11新特性
        目的：验证反编译器对ExceptionGroup和except*的处理能力
        测试要点：ExceptionGroup语法、except*异常组捕获
        版本要求：Python 3.11+
        """
        source = '''
def target():
    try:
        raise ExceptionGroup("group", [
            ValueError("bad value"),
            TypeError("bad type")
        ])
    except* ValueError as eg:
        handle_value_errors(eg)
    except* TypeError as eg:
        handle_type_errors(eg)
'''
        report = self.verify_boundary(source, min_equivalence=0.80)
        print(f"\nBND-23 (ExceptionGroup): 等价率={report.equivalence_rate:.2%}")

    def test_BND_24_position_only_parameters(self):
        """BND-24: position-only参数 - def f(a, /, b):

        版本边界：Python 3.8+（位置仅限参数）
        目的：验证反编译器对位置仅限参数语法的处理能力
        测试要点：/分隔符、位置仅限参数、关键字参数
        注意：此特性在3.8引入，但在低版本会报语法错误
        """
        if sys.version_info < (3, 8):
            pytest.skip("需要Python 3.8+支持位置仅限参数")

        source = '''
def f(a, /, b, *, c):
    return a + b + c

def g(x, /, y, z=10):
    return x * y + z
'''
        report = self.verify_boundary(source)
        print(f"\nBND-24 (position-only params): 等价率={report.equivalence_rate:.2%}")

    @pytest.mark.xfail(reason="反编译器对PEP 604联合类型语法(int|str)的支持尚不完善")
    def test_BND_25_type_hint_union_type(self):
        """BND-25: TypeHint联合类型 - x: int | str

        版本边界：Python 3.10+（新的联合类型语法）
        目的：验证反编译器对新式类型注解联合语法的处理能力
        测试要点：|联合类型操作符、PEP 604语法、类型注解保持
        注意：int | str是3.10+新语法，低版本需用Optional或Union
        已知限制：当前反编译器会丢失函数参数和返回值的类型注解，
                 仅保留模块级变量注解在__annotations__中
        """
        if sys.version_info < (3, 10):
            pytest.skip("需要Python 3.10+支持|联合类型语法")

        source = '''
from typing import Union

def process(value: int | str) -> int | str | None:
    if isinstance(value, int):
        return value * 2
    elif isinstance(value, str):
        return value.upper()
    return None

var: int | str | None = None
'''
        report = self.verify_boundary(source, min_equivalence=0.60)
        print(f"\nBND-25 (type hint union): 等价率={report.equivalence_rate:.2%}")


# ========================================================================
# 测试执行入口
# ========================================================================

def run_boundary_tests():
    """运行所有边界情况测试并生成汇总"""
    import datetime

    print("=" * 70)
    print("边界情况测试 - Boundary Cases Test Suite")
    print(f"Python版本: {sys.version}")
    print(f"运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("\n测试覆盖范围:")
    print("  Class 1: 空体边界 (BND-01 ~ BND-05) - 5个测试")
    print("  Class 2: 单行边界 (BND-06 ~ BND-10) - 5个测试")
    print("  Class 3: 深层边界 (BND-11 ~ BND-15) - 5个测试")
    print("  Class 4: 复杂表达式边界 (BND-16 ~ BND-20) - 5个测试")
    print("  Class 5: Python版本边界 (BND-21 ~ BND-25) - 5个测试")
    print("-" * 70)


if __name__ == '__main__':
    run_boundary_tests()
    pytest.main([__file__, '-v', '--tb=short'])
