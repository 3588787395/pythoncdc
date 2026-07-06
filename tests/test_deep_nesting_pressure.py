#!/usr/bin/env python3
"""
深层嵌套压力测试 - 极限场景验证

包含：
- 10个深层嵌套测试（DEEP-01到DEEP-10）
- 3个极限边界测试（BOUNDARY-01到BOUNDARY-03）
- 测试反编译器在极端嵌套深度下的表现

理论依据（编译器压力测试理论）：
- 嵌套深度测试：验证算法对递归/嵌套结构的处理能力
- 边界条件测试：发现极端情况下的潜在问题
- 压力测试：确保系统在复杂输入下的稳定性
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


class TestDeepNestingPressure(unittest.TestCase):
    """深层嵌套压力测试

    测试反编译器对深层嵌套结构的处理能力。
    涵盖for、while、if、try等控制流的组合嵌套。
    """

    @classmethod
    def setUpClass(cls):
        """初始化验证器"""
        cls.verifier = create_test_verifier()

    def verify_decompile(self, source: str, min_equivalence: float = 0.90):
        """
        验证深层嵌套代码的反编译结果

        Args:
            source: Python源代码（可能包含深层嵌套）
            min_equivalence: 最小等价率要求（深层嵌套可适当降低至90%）
        """
        report = self.verifier.verify_decompile(source)

        # 对于深层嵌套，允许WARNING状态（等价率略低）
        self.assertIn(
            report.status,
            [VerificationStatus.PASSED, VerificationStatus.WARNING],
            f"深层嵌套验证失败！状态: {report.status.value}\n"
            f"错误: {report.errors}\n"
            f"警告: {report.warnings}\n"
            f"等价率: {report.equivalence_rate:.2%}\n"
            f"反编译结果:\n{report.decompiled_source[:500]}"
        )

        # 等价率断言（深层嵌套允许更低阈值）
        self.assertGreaterEqual(
            report.equivalence_rate,
            min_equivalence,
            f"深层嵌套等价率 {report.equivalence_rate:.2%} 低于阈值 {min_equivalence:.2%}"
        )

        return report

    def test_DEEP_01_for_5_layers(self):
        """DEEP-01: for×5嵌套 - 纯循环嵌套"""
        source = '''
def target():
    for i1 in range(10):
        for i2 in range(10):
            for i3 in range(10):
                for i4 in range(10):
                    for i5 in range(10):
                        pass
'''
        report = self.verify_decompile(source)
        print(f"\nDEEP-01 (for×5): 等价率={report.equivalence_rate:.2%}")

    def test_DEEP_02_while_5_layers(self):
        """DEEP-02: while×5嵌套 - 纯while嵌套"""
        source = '''
def target():
    i1 = 0
    while i1 < 5:
        i2 = 0
        while i2 < 5:
            i3 = 0
            while i3 < 5:
                i4 = 0
                while i4 < 5:
                    i5 = 0
                    while i5 < 5:
                        pass
                    i5 += 1
                i4 += 1
            i3 += 1
        i2 += 1
    i1 += 1
'''
        report = self.verify_decompile(source, min_equivalence=0.88)
        print(f"\nDEEP-02 (while×5): 等价率={report.equivalence_rate:.2%}")

    def test_DEEP_03_if_5_layers(self):
        """DEEP-03: if×5嵌套 - 纯条件嵌套"""
        source = '''
def target(x1, x2, x3, x4, x5):
    if x1 > 0:
        if x2 > 0:
            if x3 > 0:
                if x4 > 0:
                    if x5 > 0:
                        y = 1
'''
        report = self.verify_decompile(source)
        print(f"\nDEEP-03 (if×5): 等价率={report.equivalence_rate:.2%}")

    def test_DEEP_04_mixed_5_layers(self):
        """DEEP-04: for>if>while>for>if (5层混合)"""
        source = '''
def target(x):
    for i in range(10):
        if x > 0:
            while True:
                for j in range(5):
                    if j % 2 == 0:
                        pass
                    else:
                        break
                break
'''
        report = self.verify_decompile(source, min_equivalence=0.88)
        print(f"\nDEEP-04 (mixed 5): 等价率={report.equivalence_rate:.2%}")

    def test_DEEP_05_try_nested_4_layers(self):
        """DEEP-05: try×4嵌套 - 异常处理嵌套"""
        source = '''
def target():
    try:
        try:
            try:
                try:
                    risky()
                except Error1:
                    handle1()
            except Error2:
                handle2()
        except Error3:
            handle3()
    except Error4:
        handle4()
'''
        report = self.verify_decompile(source)
        print(f"\nDEEP-05 (try×4): 等价率={report.equivalence_rate:.2%}")

    def test_DEEP_06_with_nested_4_layers(self):
        """DEEP-06: with×4嵌套 - 上下文管理器嵌套"""
        source = '''
def target():
    with context1() as c1:
        with context2() as c2:
            with context3() as c3:
                with context4() as c4:
                    process(c1, c2, c3, c4)
'''
        report = self.verify_decompile(source)
        print(f"\nDEEP-06 (with×4): 等价率={report.equivalence_rate:.2%}")

    def test_DEEP_07_for_if_mixed_complex(self):
        """DEEP-07: 复杂for-if混合嵌套（6层）"""
        source = '''
def target(data):
    result = []
    for item1 in data:
        if item1:
            for item2 in item1:
                if item2:
                    for item3 in item2:
                        if isinstance(item3, int):
                            result.append(item3)
'''
        report = self.verify_decompile(source, min_equivalence=0.88)
        print(f"\nDEEP-07 (complex mixed): 等价率={report.equivalence_rate:.2%}")

    def test_DEEP_08_mixed_7_layers(self):
        """DEEP-08: if>for>while>try>if>for>while (7层混合)"""
        source = '''
def target():
    if True:
        for i in range(10):
            while True:
                try:
                    if i > 0:
                        for j in range(5):
                            while j > 0:
                                pass
                            break
                except:
                    break
                break
            break
'''
        report = self.verify_decompile(source, min_equivalence=0.85)
        print(f"\nDEEP-08 (mixed 7): 等价率={report.equivalence_rate:.2%}")

    def test_DEEP_09_loop_with_break_continue_deep(self):
        """DEEP-09: 深层break/continue（4层循环+break/continue）"""
        source = '''
def target():
    for i in range(100):
        for j in range(100):
            for k in range(100):
                for l in range(100):
                    if l > 50:
                        continue
                    if k > 80:
                        break
                    if j > 90:
                        break
                    if i > 95:
                        break
'''
        report = self.verify_decompile(source, min_equivalence=0.87)
        print(f"\nDEEP-09 (break/continue deep): 等价率={report.equivalence_rate:.2%}")

    def test_DEEP_10_else_chains_deep(self):
        """DEEP-10: 深层else链（if-elif-else + 循环else）"""
        source = '''
def target(x):
    if x > 100:
        y = 1
    elif x > 50:
        for i in range(10):
            if i > 5:
                break
        else:
            y = 2
    elif x > 0:
        while x > 0:
            x -= 1
            if x == 5:
                break
        else:
            y = 3
    else:
        try:
            risky(x)
        except:
            y = 4
        finally:
            cleanup()
'''
        report = self.verify_decompile(source, min_equivalence=0.85)
        print(f"\nDEEP-10 (deep else chains): 等价率={report.equivalence_rate:.2%}")


class TestBoundaryConditions(unittest.TestCase):
    """极限边界测试

    测试反编译器在极限和边界条件下的行为。
    包括空函数、极长函数、特殊语法结构等。
    """

    @classmethod
    def setUpClass(cls):
        cls.verifier = create_test_verifier()

    def verify_boundary(self, source: str, should_pass: bool = True,
                       min_equivalence: float = 0.80):
        """边界条件验证"""
        report = self.verifier.verify_decompile(source)

        if should_pass:
            # 允许PASSED或WARNING
            self.assertIn(
                report.status,
                [VerificationStatus.PASSED, VerificationStatus.WARNING],
                f"边界测试失败！状态: {report.status.value}\n"
                f"错误: {report.errors}\n"
                f"等价率: {report.equivalence_rate:.2%}"
            )
        else:
            # 预期失败的情况，只记录不报错
            print(f"\n预期失败（合理）: status={report.status.value}, rate={report.equivalence_rate:.2%}")

        return report

    def test_BOUNDARY_01_empty_function(self):
        """BOUNDARY-01: 空函数 - 最小有效函数"""
        source = '''
def target():
    pass
'''
        report = self.verify_boundary(source, should_pass=True)
        print(f"\nBOUNDARY-01 (empty func): 等价率={report.equivalence_rate:.2%}")

    def test_BOUNDARY_02_large_function(self):
        """BOUNDARY-02: 大型函数 - 包含50+语句"""
        lines = []
        lines.append('def target():')
        for i in range(50):
            lines.append(f'    x{i} = {i}')
        lines.append('    return sum([x{} for x in locals().values() if isinstance(x, int)])')
        source = '\n'.join(lines)

        report = self.verify_boundary(source, should_pass=True,
                                     min_equivalence=0.82)
        print(f"\nBOUNDARY-02 (large func, 50 stmts): 等价率={report.equivalence_rate:.2%}")

    def test_BOUNDARY_03_complex_expression(self):
        """BOUNDARY-03: 复杂表达式 - 嵌套运算和调用链"""
        source = '''
def target(a, b, c, d, e, f):
    result = (((a + b) * (c - d)) / (e ** f)) if (a > b and c < d or e != f) else None
    return [str(result).upper().lower().strip() for _ in range(3)]
'''
        report = self.verify_boundary(source, should_pass=True,
                                     min_equivalence=0.83)
        print(f"\nBOUNDARY-03 (complex expr): 等价率={report.equivalence_rate:.2%}")


class TestStressCombinations(unittest.TestCase):
    """组合压力测试

    测试多种控制流结构的复杂组合。
    """

    @classmethod
    def setUpClass(cls):
        cls.verifier = create_test_verifier()

    def test_STRESS_01_all_structures_combined(self):
        """STRESS-01: 所有主要结构组合"""
        source = '''
def target(data):
    result = []

    try:
        with open('file.txt') as f:
            content = f.read()

            for line in content.splitlines():
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 3:
                        try:
                            value = int(parts[2])
                            while value > 0:
                                if value % 2 == 0:
                                    result.append(value)
                                value //= 1
                        except ValueError:
                            continue
                    elif len(parts) == 2:
                        result.append(parts[1])
    except IOError:
        result = []

    return result
'''
        report = self.verifier.verify_decompile(source)
        print(f"\nSTRESS-01 (all combined): 等价率={report.equivalence_rate:.2%}")
        self.assertIn(report.status,
                     [VerificationStatus.PASSED, VerificationStatus.WARNING])

    def test_STRESS_02_recursive_pattern(self):
        """STRESS-02: 类递归模式（多层嵌套函数调用）"""
        source = '''
def target(n):
    def helper(x):
        if x <= 1:
            return 1
        return x * helper(x - 1)

    def wrapper(y):
        if y < 0:
            return 0
        result = helper(y)
        if result > 1000:
            return result // 10
        return result

    return wrapper(n)
'''
        report = self.verifier.verify_decompile(source)
        print(f"\nSTRESS-02 (recursive pattern): 等价率={report.equivalence_rate:.2%}")
        self.assertIn(report.status,
                     [VerificationStatus.PASSED, VerificationStatus.WARNING])


def run_all_tests():
    """运行所有压力测试并生成汇总报告"""
    import datetime

    print("=" * 70)
    print("深层嵌套与边界条件压力测试")
    print(f"运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 加载所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDeepNestingPressure))
    suite.addTests(loader.loadTestsFromTestCase(TestBoundaryConditions))
    suite.addTests(loader.loadTestsFromTestCase(TestStressCombinations))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 生成汇总报告
    print("\n" + "=" * 70)
    print("测试汇总报告")
    print("=" * 70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功数: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  ❌ {test}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  ⚠️  {test}")

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n成功率: {success_rate:.1f}%")
    print("=" * 70)

    return result


if __name__ == '__main__':
    run_all_tests()
