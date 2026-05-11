#!/usr/bin/env python3
"""测试综合复杂场景"""

import sys
import os

# 添加 pythoncdc 目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
pythoncdc_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, pythoncdc_dir)

from tests.batch14.test_utils import test_bytecode_match

# 测试用例 1: 复杂控制流
def test_complex_control_flow():
    def func():
        for i in range(100):
            if i % 2 == 0:
                if i % 3 == 0:
                    print(f"{i} 是6的倍数")
                else:
                    print(f"{i} 是2的倍数但不是3的倍数")
            elif i % 3 == 0:
                print(f"{i} 是3的倍数但不是2的倍数")
            else:
                print(f"{i} 既不是2的倍数也不是3的倍数")
    return func

# 测试用例 2: 嵌套循环和条件
def test_nested_loops_and_conditions():
    def func():
        for i in range(10):
            for j in range(10):
                if i == j:
                    continue
                if i + j == 10:
                    break
                print(f"i={i}, j={j}")
    return func

# 测试用例 3: 异常处理嵌套
def test_exception_nested():
    def func():
        try:
            for i in range(10):
                try:
                    if i == 5:
                        raise ValueError("i is 5")
                    print(i)
                except ValueError:
                    print(f"捕获值错误 at {i}")
        except Exception:
            print("捕获外层异常")
    return func

# 测试用例 4: with 语句和异常处理
def test_with_and_exception():
    def func():
        try:
            with open('input.txt', 'r') as fin:
                try:
                    content = fin.read()
                    if not content:
                        raise ValueError("文件为空")
                    return content
                except IOError:
                    return None
        except FileNotFoundError:
            return None
    return func

# 测试用例 5: 复杂表达式和条件
def test_complex_expressions_and_conditions():
    def func():
        result = (a + b) * (c - d) / (e % f)
        if 0 < result < 100 and result % 2 == 0:
            return result
        elif result < 0:
            return 0
        else:
            return 100
    return func

# 测试用例 6: 海象运算符和循环
def test_walrus_and_loops():
    def func():
        while (line := input()) != 'quit':
            if (n := len(line)) > 10:
                print(f"长行 ({n} 字符): {line}")
            else:
                print(f"短行 ({n} 字符): {line}")
    return func

# 测试用例 7: 复杂函数调用链
def test_complex_call_chain():
    def func():
        result = obj.method1(a, b).method2(c).method3(d, e, f)
        return result
    return func

# 测试用例 8: 列表推导式和条件
def test_list_comprehension_with_condition():
    def func():
        result = [x * 2 for x in range(100) if x % 2 == 0 if x % 3 == 0]
        return result
    return func

# 测试用例 9: 字典推导式
def test_dict_comprehension():
    def func():
        result = {k: v for k, v in zip(keys, values) if k.startswith('a')}
        return result
    return func

# 测试用例 10: 综合复杂场景
def test_comprehensive_complex():
    def func():
        try:
            with open('data.txt', 'r') as f:
                lines = f.readlines()
                
            result = []
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                try:
                    value = int(line.strip())
                    if 0 <= value <= 100:
                        if value % 2 == 0:
                            result.append(value * 2)
                        else:
                            result.append(value * 3)
                except ValueError:
                    print(f"行 {i}: 无法转换为整数")
                    
            return result
        except FileNotFoundError:
            return []
    return func

if __name__ == '__main__':
    test_cases = [
        test_complex_control_flow,
        test_nested_loops_and_conditions,
        test_exception_nested,
        test_with_and_exception,
        test_complex_expressions_and_conditions,
        test_walrus_and_loops,
        test_complex_call_chain,
        test_list_comprehension_with_condition,
        test_dict_comprehension,
        test_comprehensive_complex,
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
