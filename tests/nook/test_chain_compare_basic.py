#!/usr/bin/env python3
"""测试基本链式比较"""

import sys
import os

# 添加 pythoncdc 目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
pythoncdc_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, pythoncdc_dir)

from tests.batch10.test_utils import test_bytecode_match

# 测试用例 1: 基本链式比较
def test_basic_chain_compare():
    def func():
        if 0 < x < 10:
            return True
        return False
    return func

# 测试用例 2: 双向链式比较
def test_two_way_chain():
    def func():
        if a < b < c:
            return True
        return False
    return func

# 测试用例 3: 长链式比较
def test_long_chain():
    def func():
        if 0 < a < b < c < 100:
            return True
        return False
    return func

# 测试用例 4: 带等号的链式比较
def test_chain_with_equal():
    def func():
        if 0 <= x <= 10:
            return True
        return False
    return func

# 测试用例 5: 混合操作符链式比较
def test_mixed_chain():
    def func():
        if 0 < x <= 10 < y < 100:
            return True
        return False
    return func

# 测试用例 6: 链式比较与逻辑运算
def test_chain_with_logic():
    def func():
        if 0 < x < 10 and y > 5:
            return True
        return False
    return func

# 测试用例 7: 嵌套链式比较
def test_nested_chain():
    def func():
        if (0 < x < 10) and (5 < y < 20):
            return True
        return False
    return func

# 测试用例 8: 链式比较在循环中
def test_chain_in_loop():
    def func():
        for i in range(100):
            if 0 < i < 50:
                print(i)
    return func

# 测试用例 9: 链式比较在异常处理中
def test_chain_in_exception():
    def func():
        try:
            if 0 < x < 10:
                return True
        except:
            return False
    return func

# 测试用例 10: 复杂链式比较
def test_complex_chain():
    def func():
        if 0 < a < b <= c < d < 100:
            result = a + b + c + d
            return result
        return 0
    return func

if __name__ == '__main__':
    test_cases = [
        test_basic_chain_compare,
        test_two_way_chain,
        test_long_chain,
        test_chain_with_equal,
        test_mixed_chain,
        test_chain_with_logic,
        test_nested_chain,
        test_chain_in_loop,
        test_chain_in_exception,
        test_complex_chain,
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
