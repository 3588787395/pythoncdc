#!/usr/bin/env python3
"""
功能验证测试套件 - 核心用例验证

包含：
- 39+核心用例的功能验证版本
- 使用DecompilationVerifier进行完整的反编译→再编译→字节码对比
- 覆盖基本语句、条件、循环、异常等核心结构

理论依据（编译器测试理论）：
- 回归测试：确保修改不破坏已有功能
- 功能等价性：反编译结果在功能上与原始代码等价
- 字节码一致性：关键操作序列保持一致
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.test_functional_verification import (
    DecompilationVerifier,
    VerificationStatus,
    create_test_verifier
)


class TestFunctionalVerification(unittest.TestCase):
    """功能验证测试基类"""

    @classmethod
    def setUpClass(cls):
        """初始化验证器"""
        cls.verifier = create_test_verifier()

    def verify_decompile(self, source: str, min_equivalence: float = 0.95):
        """验证反编译结果的功能等价性

        Args:
            source: Python源代码
            min_equivalence: 最小等价率要求（默认95%）
        """
        report = self.verifier.verify_decompile(source)

        # 基本断言
        self.assertEqual(
            report.status,
            VerificationStatus.PASSED,
            f"验证失败！状态: {report.status.value}\n"
            f"错误: {report.errors}\n"
            f"警告: {report.warnings}\n"
            f"反编译结果:\n{report.decompiled_source}"
        )

        # 等价率断言
        self.assertGreaterEqual(
            report.equivalence_rate,
            min_equivalence,
            f"等价率 {report.equivalence_rate:.2%} 低于阈值 {min_equivalence:.2%}"
        )

        return report


class TestBasicStatements(TestFunctionalVerification):
    """B系列：基本语句功能验证"""

    def test_B01_simple_assignment_func_verif(self):
        """B01功能验证：简单赋值"""
        source = '''
def target():
    x = 10
'''
        self.verify_decompile(source)

    def test_B02_augmented_assignment_func_verif(self):
        """B02功能验证：增强赋值"""
        source = '''
def target():
    x = 10
    x += 5
    x -= 3
'''
        self.verify_decompile(source)

    def test_B03_expression_statement_func_verif(self):
        """B03功能验证：表达式语句"""
        source = '''
def target():
    x = 1 + 2 * 3
'''
        self.verify_decompile(source)

    def test_B04_multiple_assignment_func_verif(self):
        """B04功能验证：多重赋值"""
        source = '''
def target():
    a, b = 1, 2
'''
        self.verify_decompile(source)

    def test_B05_return_value_func_verif(self):
        """B05功能验证：返回值"""
        source = '''
def target():
    return 42
'''
        self.verify_decompile(source)

    def test_B06_return_none_func_verif(self):
        """B06功能验证：返回None"""
        source = '''
def target():
    return None
'''
        self.verify_decompile(source)

    def test_B07_pass_func_verif(self):
        """B07功能验证：pass语句"""
        source = '''
def target():
    pass
'''
        self.verify_decompile(source)

    def test_B08_delete_func_verif(self):
        """B08功能验证：删除语句"""
        source = '''
def target():
    x = 10
    del x
'''
        self.verify_decompile(source)


class TestConditionalStatements(TestFunctionalVerification):
    """C系列：条件语句功能验证"""

    def test_C01_if_then_func_verif(self):
        """C01功能验证：if-then"""
        source = '''
def target(x):
    if x > 0:
        y = x * 2
'''
        self.verify_decompile(source)

    def test_C02_if_else_func_verif(self):
        """C02功能验证：if-else"""
        source = '''
def target(x):
    if x > 0:
        y = x * 2
    else:
        y = x + 1
'''
        self.verify_decompile(source)

    def test_C03_if_elif_func_verif(self):
        """C03功能验证：if-elif"""
        source = '''
def target(x):
    if x > 0:
        y = 1
    elif x < 0:
        y = -1
    else:
        y = 0
'''
        self.verify_decompile(source)

    def test_C04_nested_if_func_verif(self):
        """C04功能验证：嵌套if"""
        source = '''
def target(x, y):
    if x > 0:
        if y > 0:
            z = 1
        else:
            z = 2
'''
        self.verify_decompile(source)

    def test_C05_if_with_return_func_verif(self):
        """C05功能验证：带return的if"""
        source = '''
def target(x):
    if x > 0:
        return x
    return -x
'''
        self.verify_decompile(source)

    def test_C06_chained_compare_func_verif(self):
        """C06功能验证：链式比较"""
        source = '''
def target(x):
    if 0 < x < 10:
        y = 1
'''
        self.verify_decompile(source)

    def test_C07_ternary_func_verif(self):
        """C07功能验证：三元表达式"""
        source = '''
def target(x):
    y = 1 if x > 0 else -1
'''
        self.verify_decompile(source)


class TestLoopStatements(TestFunctionalVerification):
    """L系列：循环语句功能验证"""

    def test_L01_for_loop_func_verif(self):
        """L01功能验证：for循环"""
        source = '''
def target():
    for i in range(10):
        pass
'''
        self.verify_decompile(source)

    def test_L02_for_loop_else_func_verif(self):
        """L02功能验证：for-else"""
        source = '''
def target():
    for i in range(10):
        if i == 5:
            break
    else:
        x = 1
'''
        self.verify_decompile(source)

    def test_L03_while_loop_func_verif(self):
        """L03功能验证：while循环"""
        source = '''
def target():
    x = 0
    while x < 10:
        x += 1
'''
        self.verify_decompile(source)

    def test_L04_while_loop_else_func_verif(self):
        """L04功能验证：while-else"""
        source = '''
def target():
    x = 0
    while x < 10:
        x += 1
        if x == 5:
            break
    else:
        y = 1
'''
        self.verify_decompile(source)

    def test_L05_for_break_func_verif(self):
        """L05功能验证：for-break"""
        source = '''
def target():
    for i in range(100):
        if i > 10:
            break
'''
        self.verify_decompile(source)

    def test_L06_for_continue_func_verif(self):
        """L06功能验证：for-continue"""
        source = '''
def target():
    for i in range(10):
        if i % 2 == 0:
            continue
        pass
'''
        self.verify_decompile(source)

    def test_L07_nested_for_func_verif(self):
        """L07功能验证：嵌套for循环"""
        source = '''
def target():
    for i in range(5):
        for j in range(5):
            pass
'''
        self.verify_decompile(source)

    def test_L08_for_range_func_verif(self):
        """L08功能验证：range()函数"""
        source = '''
def target():
    for i in range(1, 10, 2):
        pass
'''
        self.verify_decompile(source)

    def test_L09_while_break_func_verif(self):
        """L09功能验证：while-break"""
        source = '''
def target():
    x = 0
    while True:
        x += 1
        if x >= 10:
            break
'''
        self.verify_decompile(source)

    def test_L10_loop_with_if_func_verif(self):
        """L10功能验证：循环内含if"""
        source = '''
def target():
    for i in range(10):
        if i % 2 == 0:
            x = i
'''
        self.verify_decompile(source)


class TestExceptionHandling(TestFunctionalVerification):
    """E系列：异常处理功能验证"""

    def test_E01_try_except_func_verif(self):
        """E01功能验证：try-except"""
        source = '''
def target():
    try:
        x = 1 / 0
    except ZeroDivisionError:
        x = 0
'''
        self.verify_decompile(source)

    def test_E02_try_finally_func_verif(self):
        """E02功能验证：try-finally"""
        source = '''
def target():
    try:
        x = 1
    finally:
        x = 0
'''
        self.verify_decompile(source)

    def test_E03_try_except_finally_func_verif(self):
        """E03功能验证：try-except-finally"""
        source = '''
def target():
    try:
        x = 1 / 0
    except ZeroDivisionError:
        x = 0
    finally:
        cleanup()
'''

    def test_E04_multiple_except_func_verif(self):
        """E04功能验证：多except"""
        source = '''
def target():
    try:
        risky_operation()
    except ValueError:
        handle_value()
    except TypeError:
        handle_type()
'''
        self.verify_decompile(source)

    def test_E05_nested_try_func_verif(self):
        """E05功能验证：嵌套try"""
        source = '''
def target():
    try:
        try:
            inner()
        except ValueError:
            pass
    except TypeError:
        pass
'''
        self.verify_decompile(source)


class TestWithStatement(TestFunctionalVerification):
    """W系列：with语句功能验证"""

    def test_W01_basic_with_func_verif(self):
        """W01功能验证：基本with"""
        source = '''
def target():
    with open('file.txt') as f:
        content = f.read()
'''
        self.verify_decompile(source)

    def test_W02_nested_with_func_verif(self):
        """W02功能验证：嵌套with"""
        source = '''
def target():
    with open('f1.txt') as f1:
        with open('f2.txt') as f2:
            data = f1.read() + f2.read()
'''
        self.verify_decompile(source)

    def test_W03_multi_with_func_verif(self):
        """W03功能验证：多个with"""
        source = '''
def target():
    with open('f1.txt') as f1, open('f2.txt') as f2:
        data = f1.read() + f2.read()
'''
        self.verify_decompile(source)


class TestBooleanOperations(TestFunctionalVerification):
    """BO系列：布尔操作功能验证"""

    def test_BO01_and_op_func_verif(self):
        """BO01功能验证：and操作"""
        source = '''
def target(a, b):
    if a and b:
        c = 1
'''
        self.verify_decompile(source)

    def test_BO02_or_op_func_verif(self):
        """BO02功能验证：or操作"""
        source = '''
def target(a, b):
    if a or b:
        c = 1
'''
        self.verify_decompile(source)

    def test_BO03_not_op_func_verif(self):
        """BO03功能验证：not操作"""
        source = '''
def target(a):
    if not a:
        c = 1
'''
        self.verify_decompile(source)

    def test_BO04_complex_bool_func_verif(self):
        """BO04功能验证：复杂布尔表达式"""
        source = '''
def target(a, b, c):
    if (a and b) or (c and not a):
        d = 1
'''
        self.verify_decompile(source)


class TestFunctionFeatures(TestFunctionalVerification):
    """F系列：函数特性功能验证"""

    def test_F01_default_args_func_verif(self):
        """F01功能验证：默认参数"""
        source = '''
def target(x=10, y=20):
    return x + y
'''
        self.verify_decompile(source)

    def test_F02_varargs_func_verif(self):
        """F02功能验证：可变参数"""
        source = '''
def target(*args):
    return sum(args)
'''
        self.verify_decompile(source)

    def test_F03_kwargs_func_verif(self):
        """F03功能验证：关键字参数"""
        source = '''
def target(**kwargs):
    return kwargs
'''
        self.verify_decompile(source)

    def test_F04_yield_func_verif(self):
        """F04功能验证：yield生成器"""
        source = '''
def target(n):
    for i in range(n):
        yield i
'''
        self.verify_decompile(source)

    def test_F05_lambda_func_verif(self):
        """F05功能验证：lambda表达式"""
        source = '''
def target():
    f = lambda x: x * 2
    return f(5)
'''
        self.verify_decompile(source)


class TestComplexPatterns(TestFunctionalVerification):
    """CP系列：复杂模式功能验证"""

    def test_CP01_list_comprehension_func_verif(self):
        """CP01功能验证：列表推导式"""
        source = '''
def target():
    return [x*2 for x in range(10)]
'''
        self.verify_decompile(source)

    def test_CP02_dict_comprehension_func_verif(self):
        """CP02功能验证：字典推导式"""
        source = '''
def target():
    return {x: x*2 for x in range(10)}
'''
        self.verify_decompile(source)

    def test_CP03_generator_expression_func_verif(self):
        """CP03功能验证：生成器表达式"""
        source = '''
def target():
    return sum(x*2 for x in range(10))
'''
        self.verify_decompile(source)

    def test_CP04_class_definition_func_verif(self):
        """CP04功能验证：类定义"""
        source = '''
def target():
    class MyClass:
        def __init__(self):
            self.x = 1
    return MyClass
'''
        self.verify_decompile(source)

    def test_CP05_import_statement_func_verif(self):
        """CP05功能验证：import语句"""
        source = '''
import os
import sys

def target():
    return os.path.join(sys.prefix, 'lib')
'''
        self.verify_decompile(source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
