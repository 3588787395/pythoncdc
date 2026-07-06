#!/usr/bin/env python3
"""测试 with 语句的各种变体"""

import sys
import os

# 添加 pythoncdc 目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
pythoncdc_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, pythoncdc_dir)

from tests.batch13.test_utils import test_bytecode_match

# 测试用例 1: 基本 with 语句
def test_basic_with():
    def func():
        with open('file.txt', 'r') as f:
            content = f.read()
        return content
    return func

# 测试用例 2: 多个 with 语句
def test_multiple_with():
    def func():
        with open('file1.txt', 'r') as f1:
            with open('file2.txt', 'r') as f2:
                content = f1.read() + f2.read()
        return content
    return func

# 测试用例 3: 复合 with 语句
def test_compound_with():
    def func():
        with open('file1.txt', 'r') as f1, open('file2.txt', 'r') as f2:
            content = f1.read() + f2.read()
        return content
    return func

# 测试用例 4: with 语句在 try 块中
def test_with_in_try():
    def func():
        try:
            with open('file.txt', 'r') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return None
    return func

# 测试用例 5: try-except 在 with 块中
def test_try_except_in_with():
    def func():
        with open('file.txt', 'r') as f:
            try:
                content = f.read()
                return content
            except IOError:
                return None
    return func

# 测试用例 6: with 语句在循环中
def test_with_in_loop():
    def func():
        for i in range(10):
            with open(f'file{i}.txt', 'r') as f:
                print(f.read())
    return func

# 测试用例 7: 循环在 with 块中
def test_loop_in_with():
    def func():
        with open('file.txt', 'r') as f:
            for line in f:
                print(line)
    return func

# 测试用例 8: 嵌套 with 语句
def test_nested_with():
    def func():
        with open('file1.txt', 'r') as f1:
            with open('file2.txt', 'r') as f2:
                with open('file3.txt', 'r') as f3:
                    content = f1.read() + f2.read() + f3.read()
        return content
    return func

# 测试用例 9: with 语句带 return
def test_with_with_return():
    def func():
        with open('file.txt', 'r') as f:
            return f.read()
    return func

# 测试用例 10: 复杂 with 场景
def test_complex_with():
    def func():
        try:
            with open('input.txt', 'r') as fin, open('output.txt', 'w') as fout:
                for line in fin:
                    if line.strip():
                        fout.write(line.upper())
        except IOError as e:
            print(f"IO错误: {e}")
    return func

if __name__ == '__main__':
    test_cases = [
        test_basic_with,
        test_multiple_with,
        test_compound_with,
        test_with_in_try,
        test_try_except_in_with,
        test_with_in_loop,
        test_loop_in_with,
        test_nested_with,
        test_with_with_return,
        test_complex_with,
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
