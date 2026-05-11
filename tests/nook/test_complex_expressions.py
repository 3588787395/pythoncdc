#!/usr/bin/env python3
"""测试复杂表达式和运算符优先级"""

import sys
import os

# 添加 pythoncdc 目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
pythoncdc_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, pythoncdc_dir)

from tests.batch11.test_utils import test_bytecode_match

# 测试用例 1: 基本算术表达式
def test_basic_arithmetic():
    def func():
        result = a + b * c - d / e
        return result
    return func

# 测试用例 2: 复杂算术表达式
def test_complex_arithmetic():
    def func():
        result = (a + b) * (c - d) / (e % f)
        return result
    return func

# 测试用例 3: 幂运算
def test_power():
    def func():
        result = a ** b ** c
        return result
    return func

# 测试用例 4: 混合运算
def test_mixed_operations():
    def func():
        result = a + b * c ** d - e / f % g
        return result
    return func

# 测试用例 5: 位运算
def test_bitwise():
    def func():
        result = (a & b) | (c ^ d) << e >> f
        return result
    return func

# 测试用例 6: 比较表达式
def test_comparison():
    def func():
        result = a < b and c > d or e == f
        return result
    return func

# 测试用例 7: 条件表达式
def test_conditional():
    def func():
        result = true_value if condition else false_value
        return result
    return func

# 测试用例 8: 嵌套条件表达式
def test_nested_conditional():
    def func():
        result = a if x > 0 else b if x < 0 else c
        return result
    return func

# 测试用例 9: 海象运算符
def test_walrus():
    def func():
        if (n := len(data)) > 5:
            return n
        return 0
    return func

# 测试用例 10: 复杂海象运算符
def test_complex_walrus():
    def func():
        while (line := file.readline()):
            if (count := len(line)) > 10:
                print(count)
    return func

# 测试用例 11: 函数调用链
def test_call_chain():
    def func():
        result = obj.method1().method2().method3()
        return result
    return func

# 测试用例 12: 索引和切片
def test_indexing():
    def func():
        result = data[0] + data[1:5] + data[-1]
        return result
    return func

# 测试用例 13: 复杂索引
def test_complex_indexing():
    def func():
        result = matrix[i][j] + data[start:end:step]
        return result
    return func

# 测试用例 14: 字符串操作
def test_string_ops():
    def func():
        result = s1 + s2 * 3 + s3[1:5]
        return result
    return func

# 测试用例 15: 列表操作
def test_list_ops():
    def func():
        result = [x * 2 for x in items if x > 0]
        return result
    return func

if __name__ == '__main__':
    test_cases = [
        test_basic_arithmetic,
        test_complex_arithmetic,
        test_power,
        test_mixed_operations,
        test_bitwise,
        test_comparison,
        test_conditional,
        test_nested_conditional,
        test_walrus,
        test_complex_walrus,
        test_call_chain,
        test_indexing,
        test_complex_indexing,
        test_string_ops,
        test_list_ops,
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        try:
            func = test_case()
            if test_bytecode_match(func):
                print(f"✓ {test_case.__name__}")
                passed += 1
            else:
                print(f"✗ {test_case.__name__} - 字节码不匹配")
                failed += 1
        except Exception as e:
            print(f"✗ {test_case.__name__} - {e}")
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
